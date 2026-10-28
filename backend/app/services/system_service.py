import os
import glob
import shutil
from pathlib import Path
import psutil
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message
from app.core.config import SYSTEM_LOGIN
from app.core.config import settings  # <-- ВАЖНО: добавлен пропущенный импорт

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ NVIDIA NVML (БИБЛИОТЕКА ДЛЯ ВИДЕОКАРТ NVIDIA)
# ==============================================================================

try:
    import pynvml
    pynvml.nvmlInit() # Инициализируем драйвер NVIDIA
    NVML_AVAILABLE = True
except Exception as e:
    # Если библиотеки нет или драйвер не установлен — просто пишем лог и продолжаем работу.
    # Система продолжит работать на CPU или AMD/Intel GPU.
    logger.info(f"NVIDIA NVML library not found or no NVIDIA GPU: {e}")
    NVML_AVAILABLE = False


# ==============================================================================
# БЛОК 2: СБОР ДАННЫХ С ВИДЕОКАРТ NVIDIA
# ==============================================================================

def get_nvidia_gpus() -> list[dict]:
    """Возвращает список метрик для всех найденных GPU NVIDIA."""
    gpus = []
    if not NVML_AVAILABLE:
        return gpus
    try:
        # Узнаем, сколько всего NVIDIA-карт в системе
        device_count = pynvml.nvmlDeviceGetCount()
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            # Получаем имя (например, "NVIDIA GeForce RTX 4090")
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes): 
                name = name.decode('utf-8')
            
            # Получаем информацию о памяти и загрузке
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Температура (оборачиваем в try, так как на некоторых серверных картах датчик может отсутствовать)
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = 0
                
            gpus.append({
                "vendor": "NVIDIA",
                "name": name,
                "mem_total": mem.total,
                "mem_used": mem.used,
                "mem_percent": round((mem.used / mem.total) * 100, 1) if mem.total else 0,
                "utilization": util.gpu, # Загрузка вычислительных ядер в %
                "temperature": temp
            })
    except Exception as e:
        logger.error(f"Error reading NVIDIA stats: {e}")
    return gpus


# ==============================================================================
# БЛОК 3: СБОР ДАННЫХ С ВИДЕОКАРТ AMD (ЧЕРЕЗ SYSFS LINUX)
# ==============================================================================

def get_amd_gpus() -> list[dict]:
    """
    Читает метрики AMD GPU напрямую из файловой системы Linux (/sys/class/drm/).
    Это стандартный способ, не требующий установки тяжелых SDK.
    """
    gpus = []
    # Ищем карты в sysfs (card0, card1 и т.д.)
    cards = glob.glob('/sys/class/drm/card[0-9]*/device/vendor')
    for card_path in cards:
        try:
            with open(card_path, 'r') as f:
                vendor_id = f.read().strip()
            
            # 0x1002 — официальный идентификатор вендора AMD в системе
            if vendor_id == '0x1002':
                base_dir = os.path.dirname(card_path)
                
                # Память (VRAM)
                mem_total = 0
                mem_used = 0
                try:
                    with open(f'{base_dir}/mem_info_vram_total', 'r') as f:
                        mem_total = int(f.read().strip())
                    with open(f'{base_dir}/mem_info_vram_used', 'r') as f:
                        mem_used = int(f.read().strip())
                except FileNotFoundError:
                    pass # Встроенная графика (APU) может не иметь выделенной VRAM
                
                # Загрузка ядер (%)
                util = 0
                try:
                    with open(f'{base_dir}/gpu_busy_percent', 'r') as f:
                        util = int(f.read().strip())
                except FileNotFoundError:
                    pass

                # Температура (ищем в hwmon)
                temp = 0
                hwmon_paths = glob.glob(f'{base_dir}/hwmon/hwmon*/temp1_input')
                if hwmon_paths:
                    try:
                        with open(hwmon_paths[0], 'r') as f:
                            temp = int(f.read().strip()) // 1000 # sysfs хранит миллиградусы, переводим в градусы
                    except:
                        pass

                # Имя устройства (опционально, часто пустое)
                name = "AMD GPU"
                try:
                    with open(f'{base_dir}/product_name', 'r') as f:
                        name = f.read().strip()
                except FileNotFoundError:
                    pass

                gpus.append({
                    "vendor": "AMD",
                    "name": name,
                    "mem_total": mem_total,
                    "mem_used": mem_used,
                    "mem_percent": round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0,
                    "utilization": util,
                    "temperature": temp
                })
        except Exception as e:
            logger.error(f"Error reading AMD sysfs at {card_path}: {e}")
            
    return gpus


# ==============================================================================
# БЛОК 4: СБОР ДАННЫХ С ВИДЕОКАРТ INTEL (ЧЕРЕЗ SYSFS LINUX)
# ==============================================================================

def get_intel_gpus() -> list[dict]:
    """Читает метрики встроенной графики Intel (iGPU)."""
    gpus = []
    cards = glob.glob('/sys/class/drm/card[0-9]*/device/vendor')
    for card_path in cards:
        try:
            with open(card_path, 'r') as f:
                vendor_id = f.read().strip()
            
            # 0x8086 — официальный идентификатор вендора Intel
            if vendor_id == '0x8086':
                base_dir = os.path.dirname(card_path)
                
                # Загрузка ядер (приблизительно по частоте)
                util = 0
                try:
                    # Частота текущая и максимальная
                    with open(f'{base_dir}/gt_cur_freq_mhz', 'r') as f:
                        cur_freq = int(f.read().strip())
                    with open(f'{base_dir}/gt_max_freq_mhz', 'r') as f:
                        max_freq = int(f.read().strip())
                    if max_freq > 0:
                        util = int((cur_freq / max_freq) * 100)
                except FileNotFoundError:
                    pass # Некоторые старые iGPU не имеют этих файлов

                # У Intel нет выделенной VRAM (она делит системную RAM)
                gpus.append({
                    "vendor": "INTEL",
                    "name": "Intel Graphics",
                    "mem_total": 0, # Показываем, что VRAM выделенной нет
                    "mem_used": 0,
                    "mem_percent": 0,
                    "utilization": min(util, 100),
                    "temperature": 0 # Датчиков температуры обычно нет в sysfs для iGPU
                })
        except Exception as e:
            logger.error(f"Error reading Intel sysfs at {card_path}: {e}")
            
    return gpus


# ==============================================================================
# БЛОК 5: СБОР ОБЩИХ СИСТЕМНЫХ МЕТРИК (CPU, RAM, ДИСКИ)
# ==============================================================================

def get_system_stats() -> dict:
    """
    Главная функция сбора "железных" метрик.
    Возвращает словарь с данными о CPU, RAM, дисках и видеокартах.
    """
    # 1. Процессор и память (через psutil)
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    
    # 2. Дисковое пространство
    data_path = Path(settings.data_dir).resolve()
    models_path = Path(settings.models_dir).resolve()
    
    # Защита, если папок еще нет (возвращаем корень, чтобы не упасть)
    if not data_path.exists(): data_path = Path("/")
    if not models_path.exists(): models_path = Path("/")

    disk_data = shutil.disk_usage(data_path)
    disk_models = shutil.disk_usage(models_path)

    # 3. Видеокарты (собираем все в один список)
    all_gpus = get_nvidia_gpus() + get_amd_gpus() + get_intel_gpus()

    return {
        "cpu": {"percent": cpu_percent, "cores": psutil.cpu_count()},
        "ram": {"total": ram.total, "used": ram.used, "percent": ram.percent},
        "disk_data": {"total": disk_data.total, "used": disk_data.used, "free": disk_data.free},
        "disk_models": {"total": disk_models.total, "used": disk_models.used, "free": disk_models.free},
        "gpus": all_gpus
    }


# ==============================================================================
# БЛОК 6: СБОР СТАТИСТИКИ НЕЙРОСЕТИ (LLM) ИЗ БАЗЫ ДАННЫХ
# ==============================================================================

async def get_llm_stats(session: AsyncSession) -> dict:
    """
    Агрегирует данные из таблицы messages.
    Считает общее количество запросов, токенов и среднюю скорость генерации.
    """
    # Считаем только сообщения ассистента (от SYSTEM_LOGIN)
    stmt = select(
        func.count(Message.id).label("requests"),
        func.sum(Message.prompt_tokens).label("total_prompt"),
        func.sum(Message.completion_tokens).label("total_completion"),
        func.sum(Message.duration_ms).label("total_duration")
    ).where(Message.user_login == SYSTEM_LOGIN)
    
    row = (await session.execute(stmt)).one()
    
    total_prompt = row.total_prompt or 0
    total_completion = row.total_completion or 0
    total_duration = row.total_duration or 0
    
    # Скорость: сколько токенов в секунду генерировалось в среднем.
    # duration_ms переводим в секунды, умножая на 1000.
    avg_speed = (total_completion / total_duration * 1000) if total_duration > 0 else 0.0
    
    return {
        "requests": row.requests or 0,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "avg_speed": round(avg_speed, 1)
    }