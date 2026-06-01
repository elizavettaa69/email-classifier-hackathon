"""
Главный скрипт для классификации email-писем.
Читает файлы из папки inbox/, классифицирует и раскладывает по папкам.
"""

import shutil
from pathlib import Path
from src.parser import parse_email
from src.classifier import EmailClassifier

# Создаём классификатор:
classifier = EmailClassifier()

# Создаём папки для результатов:
categories = ['spam', 'newsletters', 'incident', 'hardware', 
              'software', 'access', 'finance', 'other']

for cat in categories:
    Path(f'processed/{cat}').mkdir(parents=True, exist_ok=True)

# Берём все файлы из папки inbox
inbox = Path('inbox')

if not inbox.exists():
    print('❌ Нет папки inbox!')
    exit()

files = list(inbox.iterdir())
print(f'📧 Найдено файлов: {len(files)}')

# Обрабатываем каждый файл
for file in files:
    print(f'\n📄 Обработка: {file.name}')
    
    # Читаем письмо
    email = parse_email(file)
    
    if email is None:
        print('  ⚠️ Не могу прочитать -> other')
        dest = f'processed/other/{file.name}'
        shutil.move(file, dest)
        continue
    
    # Определяем категорию:
    category = classifier.classify(
        email['subject'],
        email['from_addr'], 
        email['body']
    )
    
    print(f'  🏷️  Категория: {category}')
    
    # Перемещаем
    dest = f'processed/{category}/{file.name}'
    shutil.move(file, dest)
    print(f'  ✅ Перемещён!')

# Выводим результат
print('\n🎉 Готово!')
