import logging
from datetime import datetime

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_current_time():
    """Возвращает текущее время в формате строки"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_get(data, keys, default=None):
    """Безопасно получает значение из словаря по цепочке ключей"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current