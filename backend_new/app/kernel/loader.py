import sys
import json
import importlib.util
import subprocess
from pathlib import Path
from loguru import logger
from app.kernel import kernel
from app.db.session import async_session_factory

class PluginLoader:
    def __init__(self):
        # Теперь загрузчик смотрит в две папки:
        # 1. plugins - легкие плагины (чистый Python)
        # 2. plugins_sidecar - тонкие клиенты для тяжелых Docker-сервисов
        self.plugins_dirs = [
            Path("/app/plugins"),
            Path("/app/plugins_sidecar")
        ]

    def _setup_venv(self, plugin_dir: Path) -> Path | None:
        """
        Создает venv для плагина и ставит зависимости из requirements.txt.
        Возвращает путь к site-packages или None, если зависимостей нет.
        """
        req_file = plugin_dir / "requirements.txt"
        if not req_file.exists():
            return None

        venv_dir = plugin_dir / ".venv"
        if not venv_dir.exists():
            logger.info(f"    Создание изолированного venv для {plugin_dir.name}...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        # Определяем путь к pip (Linux / Windows)
        pip_path = venv_dir / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_dir / "Scripts" / "pip.exe"

        # Устанавливаем зависимости
        logger.info(f"    Установка зависимостей для {plugin_dir.name}...")
        subprocess.run(
            [str(pip_path), "install", "-r", str(req_file)], 
            check=True, 
            stdout=subprocess.DEVNULL
        )

        # Возвращаем путь к site-packages
        site_packages = venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        if not site_packages.exists():
            site_packages = venv_dir / "Lib" / "site-packages"
        
        return site_packages

    async def load_all(self):
        from app.services import plugin_service
        
        async with async_session_factory() as session:
            enabled_ids = await plugin_service.get_enabled_plugin_ids(session)

        logger.info(f"Активные плагины из БД: {enabled_ids}")

        # Очищаем реестр перед полной перезагрузкой
        kernel.registry.parsers.clear()
        kernel.registry.routers.clear()
        kernel.registry.hooks.clear()

        # Проходим по каждой директории с плагинами
        for plugins_dir in self.plugins_dirs:
            if not plugins_dir.exists():
                logger.debug(f"Папка {plugins_dir} не найдена, пропускаем.")
                continue

            logger.info(f"Сканирование: {plugins_dir}...")
            
            for folder in plugins_dir.iterdir():
                if not folder.is_dir(): 
                    continue

                manifest_path = folder / "manifest.json"
                main_path = folder / "main.py"

                if not manifest_path.exists() or not main_path.exists():
                    continue

                try:
                    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
                    pid = meta.get("id", folder.name)
                    
                    if pid not in enabled_ids:
                        logger.debug(f"  [Skip] {meta.get('name', pid)} (отключен в БД)")
                        continue

                    logger.info(f"  Загрузка плагина: {pid} (из {plugins_dir.name})")

                    # 1. Настраиваем venv (если есть requirements.txt)
                    site_packages = self._setup_venv(folder)
                    if site_packages:
                        if str(site_packages) not in sys.path:
                            sys.path.insert(0, str(site_packages))

                    # 2. Регистрация в ядре
                    kernel.begin_plugin(pid)
                    try:
                        spec = importlib.util.spec_from_file_location(f"plugin_{pid}", main_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    finally:
                        kernel.end_plugin()
                        
                    logger.info(f"  [Loaded] {meta.get('name', pid)}")

                except Exception as e:
                    kernel.end_plugin()
                    logger.error(f"  [Error] Ошибка плагина {folder.name}: {e}")

loader = PluginLoader()