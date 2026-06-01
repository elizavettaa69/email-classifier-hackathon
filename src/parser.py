"""
parser.py отвечает за чтение писем из папки inbox

что делает:
- Открывает файл любого формата
- Извлекает из него тему письма (subject), отправителя (from) и тело (body)
- Если файл не стандартный возвращает None
"""

import json      
import os        
import re        


def parse_email(filepath: str) -> dict | None:
    """
    Главная функция модуля. Принимает путь к файлу и возвращает словарь с ключами:
        'subject'   — тема письма
        'from_addr' — отправитель
        'body'      — тело 
    Если файл не является читаемым письмом, возвращает None.
    """
    
    # пробуем прочитать файл как текст 
    # письма могут быть в разных кодировках. мы пробуем UTF-8

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        # Если файл не читается как текст ,
        # то это не письмо. Печатаем ошибку в консоль и возвращаем None.
        print(f"Не удалось прочитать файл как текст: {filepath} — {e}")
        return None
    
    # Если файл пустой  — тоже не письмо
    if not content or not content.strip():
        print(f"Файл пуст: {filepath}")
        return None
    
    # 2. Определяем тип файла по расширению 
    # splitext разбивает имя файла на "основное имя" и "расширение"
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.json':
        # если расширение .json — используем специальный парсер JSON
        return _parse_json_email(content)
    else:
        # Для всех остальных используем парсер текстового письма
        return _parse_text_email(content)


def _parse_text_email(content: str) -> dict:
    """
    Парсит текстовое письмо 
    Ищет поля : Subject, From ,Всё остальное считает телом письма.
    """
    result = {
        'subject': '',
        'from_addr': '',
        'body': ''
    }
    
    # Разбиваем содержимое на строки
    lines = content.split('\n')
    
    # Флаги, чтобы понять, нашли ли мы уже тему и отправителя
    subject_found = False
    from_found = False
    body_lines = []   # сюда собираем строки тела
    
    # Перебираем строки по порядку
    for i, line in enumerate(lines):
        # Приводим строку к нижнему регистру 
        lower_line = line.lower()
        # Ищем тему, пока не нашли
        if not subject_found:
            # ищем в начале строки одно из слов, за которым может быть двоеточие или точка с запятой
            match = re.search(r'(subject|тема)\s*[:;]', lower_line)
            if match:
                # Если нашли — извлекаем всё, что идёт после двоеточия
                # разобиваем строку по двоеточию или точке с запятой, берем вторую часть
                parts = re.split(r'[:;]', line, maxsplit=1)
                if len(parts) > 1:
                    result['subject'] = parts[1].strip() 
                subject_found = True
                continue  # переходим к следующей строке
        
        # Поиск отправителя 
        if not from_found:
            # Возможные варианты: "From:", "От кого:", "От:"
            match = re.search(r'(from|от кого|от)\s*[:;]', lower_line)
            if match:
                parts = re.split(r'[:;]', line, maxsplit=1)
                if len(parts) > 1:
                    result['from_addr'] = parts[1].strip()
                from_found = True
                continue
        
        # Если тему и отправителя уже нашли, все остальные строки — тело
        if subject_found and from_found:
            # Добавляем строку в тело
            body_lines.append(line)
        else:
            # Если мы ещё не нашли заголовки, но прошло > 10,то, в файле нет заголовков 
            # Тогда считаем, что первая строка — тема,а всё остальное — тело.
            if i > 10 and not subject_found and not from_found:
                if not result['subject'] and lines:
                    result['subject'] = lines[0].strip()
                body_lines = lines[1:] if len(lines) > 1 else []
                break
    
    # Если тему так и не нашли, но есть хотя бы одна строка — берём её как тему
    if not result['subject'] and lines:
        # Берём первую строку, но не длиннее 100 символов, чтобы не захватывать всё письмо
        result['subject'] = lines[0].strip()[:100]
    
    # Если отправитель не найден — ставим "unknown"
    if not result['from_addr']:
        result['from_addr'] = 'unknown'
    
    # формируем тело, соединяем все собранные строки через 
    if body_lines:
        result['body'] = '\n'.join(body_lines).strip()
    elif len(lines) > 2:
        # Если тела нет, но строк больше двух — берём всё после первых двух строк
        result['body'] = '\n'.join(lines[2:]).strip()
    
    return result


def _parse_json_email(content: str) -> dict | None:
    """
    Парсит JSON-файл
    Ожидает, что в JSON есть поля: subject, from, body 
    Если JSON невалидный — возвращает None.
    """
    result = {
        'subject': '',
        'from_addr': '',
        'body': ''
    }
    
    # Пробуем распарсить строку как JSON
    try:
        data = json.loads(content)   # превращает JSON-строку в словарь Python
    except json.JSONDecodeError as e:
        # Невалидный JSON
        print(f"Ошибка парсинга JSON: {e}")
        return None
    
    # Извлекаем поля, пробуя разные варианты 
    # .get() возвращает значение по ключу, если ключа нет — возвращает пустую строку
    result['subject'] = data.get('subject') or data.get('Subject') or data.get('тема') or ''
    result['from_addr'] = data.get('from') or data.get('From') or data.get('отправитель') or ''
    result['body'] = data.get('body') or data.get('Body') or data.get('текст') or ''
    
    return result