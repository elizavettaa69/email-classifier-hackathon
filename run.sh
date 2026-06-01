
echo "  Email Classifier - Hackathon 2026"

# существует ли inbox
if [ ! -d "inbox" ]; then
    echo " Ошибка: папка 'inbox' не найдена"
    exit 1
fi

# есть ли файлы в inbox
if [ -z "$(ls -A inbox 2>/dev/null)" ]; then
    echo "Ошибка: папка 'inbox' пуста"
    exit 1
fi

echo "Начинаю обработку писем..."
echo ""

# Запуск Python-приложения
python3 src/processor.py

# Проверка результата
if [ $? -eq 0 ]; then
    echo ""
    echo "Обработка завершена успешно"
    echo ""
    echo " Статистика:"
    ls -la processed/
else
    echo ""
    echo "Ошибка при выполнении"
    exit 1
fi