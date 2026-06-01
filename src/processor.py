"""
Главный скрипт для классификации email-писем.

Читает файлы из папки inbox/, для каждого файла:
1. Парсит содержимое (извлекает тему, отправителя, тело письма)
2. Классифицирует (важное/не важное/спам)
3. Перемещает в соответствующую папку (important/, not_important/, spam/)
4. Логирует все действия
"""

import os
import sys
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорт модулей проекта (будут созданы позже)
from src.parser import parse_email
from src.classifier import classify_email


# Настройка логирования
def setup_logging(log_file: str = "logs/processing.log") -> None:
    """
    Настройка системы логирования.
    
    Args:
        log_file: путь к файлу логов
    """
    # Создаем директорию для логов, если её нет
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка форматирования
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настройка обработчиков
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # Вывод в консоль
        ]
    )


# Работа с файлами
def ensure_directories() -> Dict[str, Path]:
    """
    Создает необходимые директории, если их нет.
    
    Returns:
        Dict[str, Path]: словарь с путями к директориям
    """
    base_dir = Path(__file__).parent.parent  # Корень проекта
    dirs = {
        "inbox": base_dir / "inbox",
        "important": base_dir / "important",
        "not_important": base_dir / "not_important",
        "spam": base_dir / "spam",
        "logs": base_dir / "logs",
        "processed": base_dir / "processed"  # для уже обработанных (опционально)
    }
    
    # Создаем все директории
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Директории проверены/созданы. Inbox: {dirs['inbox']}")
    return dirs


def move_email(file_path: Path, target_category: str, directories: Dict[str, Path]) -> bool:
    """
    Перемещает email-файл в соответствующую папку на основе категории.
    
    Args:
        file_path: путь к исходному файлу
        target_category: категория ('important', 'not_important', 'spam')
        directories: словарь с путями к директориям
    
    Returns:
        bool: True если перемещение успешно, иначе False
    """
    category_map = {
        "important": directories["important"],
        "not_important": directories["not_important"],
        "spam": directories["spam"]
    }
    
    if target_category not in category_map:
        logging.warning(f"Неизвестная категория '{target_category}' для файла {file_path.name}")
        return False
    
    target_dir = category_map[target_category]
    target_path = target_dir / file_path.name
    
    try:
        # Если файл с таким именем уже существует, добавляем timestamp
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            target_path = target_dir / new_name
            logging.warning(f"Файл {file_path.name} уже существует. Переименован в {new_name}")
        
        shutil.move(str(file_path), str(target_path))
        logging.info(f"✓ Перемещен: {file_path.name} → {target_category}/{target_path.name}")
        return True
        
    except Exception as e:
        logging.error(f"✗ Ошибка перемещения {file_path.name}: {e}")
        return False


# Основная обработка
def process_single_email(file_path: Path, directories: Dict[str, Path]) -> Tuple[bool, str]:
    """
    Обрабатывает один email-файл: парсинг, классификация, перемещение.
    
    Args:
        file_path: путь к файлу
        directories: словарь с путями к директориям
    
    Returns:
        Tuple[bool, str]: (успех_обработки, сообщение)
    """
    filename = file_path.name
    logging.info(f"\n{'='*50}")
    logging.info(f"Обработка: {filename}")
    
    # Шаг 1: Парсинг email
    try:
        parsed_email = parse_email(file_path)
        logging.info(f"  📧 Тема: {parsed_email.get('subject', 'Без темы')[:50]}")
        logging.info(f"  📬 От: {parsed_email.get('from', 'Неизвестно')}")
    except Exception as e:
        error_msg = f"Ошибка парсинга {filename}: {e}"
        logging.error(error_msg)
        return False, error_msg
    
    # Шаг 2: Классификация
    try:
        category, confidence = classify_email(parsed_email)
        logging.info(f"  🏷️  Категория: {category} (уверенность: {confidence:.2f})")
    except Exception as e:
        error_msg = f"Ошибка классификации {filename}: {e}"
        logging.error(error_msg)
        return False, error_msg
    
    # Шаг 3: Перемещение файла
    success = move_email(file_path, category, directories)
    
    if success:
        return True, f"Успешно обработан: {filename} → {category}"
    else:
        return False, f"Не удалось переместить: {filename}"


def process_inbox(directories: Dict[str, Path], move_on_error: bool = False) -> Dict[str, int]:
    """
    Обрабатывает все файлы из папки inbox.
    
    Args:
        directories: словарь с путями к директориям
        move_on_error: перемещать ли файлы с ошибками в spam (опционально)
    
    Returns:
        Dict[str, int]: статистика обработки
    """
    inbox_dir = directories["inbox"]
    
    # Получаем список всех файлов в inbox (исключая поддиректории)
    files = [f for f in inbox_dir.iterdir() if f.is_file()]
    
    if not files:
        logging.info("Папка inbox пуста. Нечего обрабатывать.")
        return {"total": 0, "success": 0, "error": 0}
    
    logging.info(f"\n🔍 Найдено файлов для обработки: {len(files)}")
    
    stats = {
        "total": len(files),
        "success": 0,
        "error": 0,
        "important": 0,
        "not_important": 0,
        "spam": 0
    }
    
    for file_path in files:
        success, message = process_single_email(file_path, directories)
        
        if success:
            stats["success"] += 1
            # Извлекаем категорию из сообщения
            if "important" in message.lower():
                stats["important"] += 1
            elif "not_important" in message.lower():
                stats["not_important"] += 1
            elif "spam" in message.lower():
                stats["spam"] += 1
        else:
            stats["error"] += 1
            # Опционально: перемещаем проблемные файлы в spam
            if move_on_error:
                spam_dir = directories["spam"]
                error_path = spam_dir / file_path.name
                shutil.move(str(file_path), str(error_path))
                logging.info(f"Проблемный файл перемещен в spam: {file_path.name}")
    
    return stats


def print_summary(stats: Dict[str, int], start_time: datetime) -> None:
    """
    Выводит итоговую статистику обработки.
    
    Args:
        stats: словарь со статистикой
        start_time: время начала обработки
    """
    elapsed = (datetime.now() - start_time).total_seconds()
    
    logging.info(f"\n{'='*50}")
    logging.info(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    logging.info(f"{'='*50}")
    logging.info(f"Всего файлов:      {stats['total']}")
    logging.info(f"✅ Успешно:         {stats['success']}")
    logging.info(f"❌ Ошибок:          {stats['error']}")
    logging.info(f"{'-'*30}")
    logging.info(f"📌 Важные:          {stats['important']}")
    logging.info(f"📌 Не важные:       {stats['not_important']}")
    logging.info(f"⚠️  Спам:           {stats['spam']}")
    logging.info(f"{'-'*30}")
    logging.info(f"⏱️  Время:           {elapsed:.2f} сек")
    
    if stats["error"] > 0:
        logging.warning(f"⚠️  Есть ошибки! Проверьте логи для деталей.")


# Командная строка
def parse_arguments():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Классификатор email-писем",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python src/processor.py                # Обычный запуск
  python src/processor.py --move-errors  # Перемещать ошибочные файлы в spam
  python src/processor.py --log logs/custom.log  # Свой файл логов
  python src/processor.py --dry-run      # Пробный запуск (только логирование, без перемещения)
        """
    )
    
    parser.add_argument(
        "--log", "-l",
        type=str,
        default="logs/processing.log",
        help="Путь к файлу логов (по умолчанию: logs/processing.log)"
    )
    
    parser.add_argument(
        "--move-errors",
        action="store_true",
        help="Перемещать файлы с ошибками в папку spam"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Пробный запуск: только логирование, без реального перемещения файлов"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод (DEBUG уровень логирования)"
    )
    
    return parser.parse_args()


# Точка входа
def main():
    """Главная функция."""
    # Парсим аргументы
    args = parse_arguments()
    
    # Настройка логирования
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(args.log, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    logging.info("🚀 Запуск email-классификатора")
    logging.info(f"📝 Лог-файл: {args.log}")
    logging.info(f"🎭 Dry-run режим: {'ВКЛЮЧЕН (файлы не перемещаются)' if args.dry_run else 'ВЫКЛЮЧЕН'}")
    
    start_time = datetime.now()
    
    try:
        # Создаем необходимые директории
        directories = ensure_directories()
        
        # Если dry-run, заменяем функцию move_email на заглушку
        if args.dry_run:
            global move_email
            original_move = move_email
            
            def dry_run_move(file_path, target_category, directories):
                logging.info(f"[DRY-RUN] Был бы перемещен: {file_path.name} → {target_category}")
                return True
            
            move_email = dry_run_move
        
        # Обрабатываем файлы
        stats = process_inbox(directories, move_on_error=args.move_errors)
        
        # Выводим статистику
        print_summary(stats, start_time)
        
        # Возвращаем код ошибки, если были проблемы
        return 1 if stats["error"] > 0 else 0
        
    except KeyboardInterrupt:
        logging.warning("\n⚠️  Обработка прервана пользователем")
        return 130
    except Exception as e:
        logging.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        return 1
    finally:
        logging.info("🏁 Завершение работы классификатора")


if __name__ == "__main__":
    sys.exit(main())
  
