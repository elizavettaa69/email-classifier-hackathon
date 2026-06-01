import logging
import os
from datetime import datetime

def setup_logger():
    # настраивает логгер для проекта
    # пишет в файл и в консоль
    
    # создаём папку для логов если нет
    os.makedirs('logs', exist_ok=True)
    
    # имя логгера
    logger = logging.getLogger('email_classifier')
    logger.setLevel(logging.DEBUG)
    
    # чистим старые хэндлеры чтобы не дублировать
    logger.handlers.clear()
    
    # формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # файл с логами пишем всё включая debug
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(
        f'logs/processing_{timestamp}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # консоль только важное
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # добавляем хэндлеры
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger