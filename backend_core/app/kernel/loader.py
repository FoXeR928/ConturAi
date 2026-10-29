import sys
import json
import importlib.util
import subprocess
from pathlib import Path
from loguru import logger
from sqlalchemy import update

from app.kernel import kernel
from app.db.session import async_session_factory
from app.db.models import Plugin
from app.core.config import settings

class PluginLoader:
    def __init__(self):
        # Берем путь из настроек (по умолчанию "./plugins", что в Docker станет "/app/plugins")
        self.plugins_dir = Path(settings.plugins_dir).resolve()

    def _setup_venv(self, plugin_dir: Path) -> Path | None:
        """Создает venv для плагина и ставит зависимости из requirements.txt."""
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
        subprocess.run([str(pip_path), "install", "-r", str(req_file)], check=True, stdout=subprocess.DEVNULL)

        site_packages = venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if not site_packages.exists():
            site_packages = venv_dir / "Lib" / "site-packages"
        return site_packages

    async def _disable_plugin_in_db(self, plugin_id: str, reason: str):
        """Отключает плагин в БД, если он упал при загрузке."""
        try:
            async with async_session_factory() as session:
                await session.execute(update(Plugin).where(Plugin.plugin_id == plugin_id).values(is_enabled=False))
                await session.commit()
                logger.warning(f"  [Disabled] Плагин '{plugin_id}' отключен в БД. Причина: {reason}")
        except Exception as e:
            logger.error(f"  Не удалось отключить плагин {plugin_id} в БД: {e}")

    async def load_all(self):
        from app.services import plugin_service
        from sqlalchemy.exc import ProgrammingError

        try:
            async with async_session_factory() as session:
                enabled_ids = await plugin_service.get_enabled_plugin_ids(session)
        except Exception as e:
            logger.warning(f"Не удалось прочитать таблицу плагинов (возможно, БД не инициализирована): {e}")
            enabled_ids = set()

        logger.info(f"Активные плагины из БД: {enabled_ids}")

        # Полная очистка реестра перед загрузкой
        kernel.registry.clear_all()
        loaded_plugins: set[str] = set()

        if not self.plugins_dir.exists():
            logger.warning(f"Папка {self.plugins_dir} не найдена, плагины не загружены.")
            return

        for folder in self.plugins_dir.iterdir():
            if not folder.is_dir(): continue

            manifest_path = folder / "manifest.json"
            main_path = folder / "main.py"

            if not manifest_path.exists() or not main_path.exists(): continue

            pid = folder.name
            try:
                meta = json.loads(manifest_path.read_text(encoding="utf-8"))
                pid = meta.get("id", folder.name)

                if pid not in enabled_ids:
                    logger.debug(f"  [Skip] {meta.get('name', pid)} (отключен в БД)")
                    continue

                if pid in loaded_plugins:
                    logger.warning(f"  [Skip] {pid} уже загружен, дубликат.")
                    continue

                logger.info(f"  Загрузка плагина: {pid}")

                # Настраиваем venv
                site_packages = self._setup_venv(folder)
                if site_packages and str(site_packages) not in sys.path:
                    sys.path.insert(0, str(site_packages))

                # Регистрация
                kernel.begin_plugin(pid)
                try:
                    spec = importlib.util.spec_from_file_location(f"plugin_{pid}", main_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                finally:
                    kernel.end_plugin()

                loaded_plugins.add(pid)
                logger.info(f"  [Loaded] {meta.get('name', pid)}")

            except Exception as e:
                kernel.end_plugin()
                logger.error(f"  [Error] Ошибка плагина {folder.name}: {e}")
                await self._disable_plugin_in_db(pid, str(e)[:100])

loader = PluginLoader()