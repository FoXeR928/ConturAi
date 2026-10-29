import sys
import json
import importlib.util
import subprocess
import os
import asyncio
from pathlib import Path
from loguru import logger
from sqlalchemy import update
import httpx

from app.kernel import kernel
from app.db.session import async_session_factory
from app.db.models import Plugin
from app.core.config import settings

# Docker SDK нужен только для remote-плагинов
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Модуль 'docker' не установлен — remote-плагины недоступны")


class PluginLoader:
    def __init__(self):
        self.plugins_dir = Path(settings.plugins_dir).resolve()
        self._docker_client = None

    # =========================================================================
    # Вспомогательные методы
    # =========================================================================

    def _setup_venv(self, plugin_dir: Path) -> Path | None:
        """Создает изолированное venv для плагина, если есть requirements.txt."""
        req_file = plugin_dir / "requirements.txt"
        if not req_file.exists():
            return None

        venv_dir = plugin_dir / ".venv"
        if not venv_dir.exists():
            logger.info(f"    Создание venv для {plugin_dir.name}...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        pip_path = venv_dir / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_dir / "Scripts" / "pip.exe"

        logger.info(f"    Установка зависимостей для {plugin_dir.name}...")
        subprocess.run(
            [str(pip_path), "install", "-r", str(req_file)],
            check=True, stdout=subprocess.DEVNULL
        )

        site = venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if not site.exists():
            site = venv_dir / "Lib" / "site-packages"
        return site

    async def _disable_plugin_in_db(self, plugin_id: str, reason: str):
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(Plugin).where(Plugin.plugin_id == plugin_id).values(is_enabled=False)
                )
                await session.commit()
            logger.warning(f"  [Disabled] Плагин '{plugin_id}' отключен в БД: {reason}")
        except Exception as e:
            logger.error(f"  Не удалось отключить плагин {plugin_id} в БД: {e}")

    def _get_docker(self):
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Модуль 'docker' не установлен в backend")
        if self._docker_client is None:
            self._docker_client = docker.from_env()
        return self._docker_client

    # =========================================================================
    # Запуск Docker-контейнера для remote-плагина
    # =========================================================================

    async def _ensure_remote_container(self, meta: dict) -> str:
        """Запускает контейнер. Возвращает базовый URL плагина."""
        client = self._get_docker()
        pid = meta["id"]
        container_name = meta.get("container_name", f"conturai_plugin_{pid}")

        loop = asyncio.get_running_loop()

        def _ensure():
            try:
                container = client.containers.get(container_name)
                if container.status != "running":
                    logger.info(f"    Запуск существующего контейнера {container_name}...")
                    container.start()
                else:
                    logger.info(f"    Контейнер {container_name} уже запущен.")
                return container
            except docker.errors.NotFound:
                logger.info(f"    Создание контейнера {container_name} ({meta['docker_image']})...")
                return client.containers.run(
                    image=meta["docker_image"],
                    name=container_name,
                    detach=True,
                    ports=meta.get("ports", {}),
                    environment=meta.get("environment", {}),
                    volumes=meta.get("volumes", []),
                    command=meta.get("command"),
                    device_requests=meta.get("device_requests"),
                    ipc_mode=meta.get("ipc_mode"),
                    restart_policy={"Name": "unless-stopped"},
                )

        await loop.run_in_executor(None, _ensure)

        # Ждем health-check
        port = meta.get("host_port", 8000)
        endpoint = meta.get("health_endpoint", "/health")
        url = f"http://127.0.0.1:{port}{endpoint}"

        logger.info(f"    Ожидание готовности {pid} ({url})...")
        for _ in range(60):  # до 2 минут
            try:
                async with httpx.AsyncClient(timeout=2.0) as c:
                    r = await c.get(url)
                    if r.status_code == 200:
                        logger.info(f"    {pid} готов к работе")
                        return f"http://127.0.0.1:{port}"
            except Exception:
                pass
            await asyncio.sleep(2)

        raise RuntimeError(f"Плагин {pid} не отвечает после 120 секунд")

    # =========================================================================
    # Основной цикл загрузки
    # =========================================================================

    async def load_all(self):
        from app.services import plugin_service

        try:
            async with async_session_factory() as session:
                enabled_ids = await plugin_service.get_enabled_plugin_ids(session)
        except Exception as e:
            logger.warning(f"Не удалось прочитать таблицу plugins: {e}")
            enabled_ids = set()

        logger.info(f"Активные плагины из БД: {enabled_ids}")
        kernel.registry.clear_all()

        if not self.plugins_dir.exists():
            logger.warning(f"Папка {self.plugins_dir} не найдена")
            return

        loaded: set[str] = set()

        for folder in sorted(self.plugins_dir.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue

            manifest_path = folder / "manifest.json"
            main_path = folder / "main.py"

            if not manifest_path.exists() or not main_path.exists():
                continue

            try:
                meta = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Ошибка манифеста {folder.name}: {e}")
                continue

            pid = meta.get("id", folder.name)
            if pid not in enabled_ids:
                logger.debug(f"  [Skip] {pid} (отключен)")
                continue
            if pid in loaded:
                continue

            ptype = meta.get("type", "local")
            logger.info(f"  Загрузка плагина: {pid} (type={ptype})")

            try:
                plugin_url = None

                # 1. Для remote — поднимаем контейнер
                if ptype == "remote":
                    plugin_url = await self._ensure_remote_container(meta)

                # 2. Настраиваем venv
                site = self._setup_venv(folder)
                if site and str(site) not in sys.path:
                    sys.path.insert(0, str(site))

                # 3. Импортируем main.py
                kernel.begin_plugin(pid)
                try:
                    if plugin_url:
                        os.environ["PLUGIN_URL"] = plugin_url
                        os.environ[f"PLUGIN_{pid.upper()}_URL"] = plugin_url

                    spec = importlib.util.spec_from_file_location(f"plugin_{pid}", main_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                finally:
                    kernel.end_plugin()

                loaded.add(pid)
                logger.info(f"  [OK] {meta.get('name', pid)}")

            except Exception as e:
                kernel.end_plugin()
                logger.error(f"  [ERROR] {folder.name}: {e}")
                await self._disable_plugin_in_db(pid, str(e)[:200])


loader = PluginLoader()