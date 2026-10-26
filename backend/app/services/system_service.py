import os
import glob
import shutil
from pathlib import Path
import psutil
from loguru import logger
from app.core.config import settings

# --- NVIDIA ---
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception as e:
    logger.info(f"NVIDIA NVML library not found or no NVIDIA GPU: {e}")
    NVML_AVAILABLE = False

def get_nvidia_gpus() -> list[dict]:
    gpus = []
    if not NVML_AVAILABLE:
        return gpus
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes): name = name.decode('utf-8')
            
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
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
                "utilization": util.gpu,
                "temperature": temp
            })
    except Exception as e:
        logger.error(f"Error reading NVIDIA stats: {e}")
    return gpus

# --- AMD (через Linux sysfs) ---
def get_amd_gpus() -> list[dict]:
    gpus = []
    # Ищем карты в sysfs
    cards = glob.glob('/sys/class/drm/card[0-9]*/device/vendor')
    for card_path in cards:
        try:
            with open(card_path, 'r') as f:
                vendor_id = f.read().strip()
            
            # 0x1002 — идентификатор AMD
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
                            temp = int(f.read().strip()) // 1000 # миллиградусы в градусы
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

# --- Сбор всех данных ---
def get_system_stats() -> dict:
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    
    data_path = Path(settings.data_dir).resolve()
    models_path = Path(settings.models_dir).resolve()
    
    if not data_path.exists(): data_path = Path("/")
    if not models_path.exists(): models_path = Path("/")

    disk_data = shutil.disk_usage(data_path)
    disk_models = shutil.disk_usage(models_path)

    # Собираем все видеокарты в один список
    all_gpus = get_nvidia_gpus() + get_amd_gpus()

    return {
        "cpu": {"percent": cpu_percent, "cores": psutil.cpu_count()},
        "ram": {"total": ram.total, "used": ram.used, "percent": ram.percent},
        "disk_data": {"total": disk_data.total, "used": disk_data.used, "free": disk_data.free},
        "disk_models": {"total": disk_models.total, "used": disk_models.used, "free": disk_models.free},
        "gpus": all_gpus
    }