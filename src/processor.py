""" 
главный скрипт для классификации email-писем 
читает файлы из папки inbox/, классифицирует и раскладывает по папкам
""" 

import shutil
from pathlib import Path
from src.parser import parse_email
from src.classifier import EmailClassifier

# создаём классификатор
classifier = EmailClassifier()

# создаём папки для результатов
categories = ['spam', 'newsletters', 'incident', 'hardware',
              'software', 'access', 'finance', 'other']

for cat in categories:
    Path(f'processed/{cat}').mkdir(parents=True, exist_ok=True)

# берём все файлы из папки inbox
inbox = Path('inbox')

if not inbox.exists():
    print("❌ Папка 'inbox' не найдена!")
    exit(1)

files = list(inbox.iterdir())
print(f"📧 Найдено файлов: {len(files)}")

# счётчики для статистики
stats = {cat: 0 for cat in categories}
errors = 0

# обрабатываем каждый файл
for file in files:
    print(f"Обработка: {file.name}")
    
    # читаем письмо
    email = parse_email(file)
    
    if email is None:
        print(f"  ⚠️ Не удалось прочитать, отправляем в 'other'")
        dest = f'processed/other/{file.name}'
        try:
            shutil.move(str(file), dest)
            stats['other'] += 1
        except Exception as e:
            print(f"  ❌ Ошибка перемещения: {e}")
            errors += 1
        continue
    
    # определяем категорию
    category = classifier.classify(
        email['subject'],
        email['from_addr'],
        email['body']
    )
    
    print(f"  📂 Категория: {category}")
    
    # перемещаем
    dest = f'processed/{category}/{file.name}'
    try:
        shutil.move(str(file), dest)
        stats[category] += 1
        print(f"  ✅ Перемещён в processed/{category}/")
    except Exception as e:
        print(f"  ❌ Ошибка перемещения: {e}")
        errors += 1

# выводим статистику
print("\n" + "="*40)
print("📊 СТАТИСТИКА ОБРАБОТКИ:")
for cat, count in stats.items():
    print(f"  {cat:15} : {count}")
print(f"  {'Ошибок':15} : {errors}")
print(f"  {'ВСЕГО':15} : {sum(stats.values())}")
print("="*40)
print("🎉 Готово!")
