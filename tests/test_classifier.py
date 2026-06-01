import pytest
import os
import tempfile
import shutil
from pathlib import Path

# импортируем то что тестируем
from src.classifier import EmailClassifier
from src.parser import parse_email


# фикстуры

@pytest.fixture
def classifier():
    # создаёт классификатор со стандартными правилами
    return EmailClassifier()


@pytest.fixture
def temp_dir():
    # создаёт временную папку для тестов
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def test_email_file(temp_dir):
    # создаёт тестовое письмо в файле
    content = """Subject: Тестовое письмо
From: test@company.ru

Это тело тестового письма
"""
    filepath = os.path.join(temp_dir, 'test_email.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath


# тесты классификатора

class TestEmailClassifier:
    # тесты для класса EmailClassifier
    
    def test_spam_detection(self, classifier):
        # проверяет что спам определяется
        category = classifier.classify(
            subject='Вы выиграли миллион!',
            from_addr='spam@fake.com',
            body='Получите ваш выигрыш прямо сейчас'
        )
        assert category == 'spam'
    
    def test_incident_detection(self, classifier):
        # проверяет что инциденты определяются
        category = classifier.classify(
            subject='Критичный сбой',
            from_addr='user@company.ru',
            body='Система не работает, ошибка 500'
        )
        assert category == 'incident'
    
    def test_hardware_detection(self, classifier):
        # проверяет что проблемы с оборудованием определяются
        category = classifier.classify(
            subject='Сломался принтер',
            from_addr='user@company.ru',
            body='Принтер не включается, нужна замена'
        )
        assert category == 'hardware'
    
    def test_software_detection(self, classifier):
        # проверяет что проблемы с ПО определяются
        category = classifier.classify(
            subject='Не работает Chrome',
            from_addr='user@company.ru',
            body='Браузер зависает после обновления'
        )
        assert category == 'software'
    
    def test_access_detection(self, classifier):
        # проверяет что запросы доступа определяются
        category = classifier.classify(
            subject='Нужен доступ к GitLab',
            from_addr='manager@company.ru',
            body='Выдать права новому сотруднику'
        )
        assert category == 'access'
    
    def test_finance_detection(self, classifier):
        # проверяет что финансовые письма определяются
        category = classifier.classify(
            subject='Счёт на оплату',
            from_addr='partner@vendor.ru',
            body='Высылаем акт и договор на оплату'
        )
        assert category == 'finance'
    
    def test_newsletters_detection(self, classifier):
        # проверяет что рассылки определяются
        category = classifier.classify(
            subject='Корпоративный дайджест',
            from_addr='news@company.ru',
            body='Итоги квартала и плановые работы'
        )
        assert category == 'newsletters'
    
    def test_unknown_category(self, classifier):
        # проверяет что неизвестные письма попадают в other
        category = classifier.classify(
            subject='Просто письмо',
            from_addr='friend@mail.ru',
            body='Привет, как дела?'
        )
        assert category == 'other'
    
    def test_empty_fields(self, classifier):
        # проверяет работу с пустыми полями
        category = classifier.classify(
            subject='',
            from_addr='',
            body=''
        )
        assert category == 'other'
        @pytest.mark.parametrize('subject,expected', [
        ('Вы выиграли приз', 'spam'),
        ('Критическая ошибка', 'incident'),
        ('Сломался сканер', 'hardware'),
        ('Не запускается Zoom', 'software'),
        ('Доступ к VPN', 'access'),
        ('Счёт №123', 'finance'),
        ('Дайджест #5', 'newsletters'),
        ('Привет', 'other'),
    ])
    def test_parametrized_classification(self, classifier, subject, expected):
        # параметризованный тест для разных категорий
        category = classifier.classify(
            subject=subject,
            from_addr='test@company.ru',
            body='тело письма'
        )
        assert category == expected


# тесты парсера

class TestParser:
    # тесты для функции parse_email
    
    def test_parse_text_email(self, test_email_file):
        # проверяет парсинг обычного текстового письма
        result = parse_email(test_email_file)
        
        assert result is not None
        assert result['subject'] == 'Тестовое письмо'
        assert result['from_addr'] == 'test@company.ru'
        assert 'тело тестового письма' in result['body'].lower()
    
    def test_parse_empty_file(self, temp_dir):
        # проверяет что пустой файл возвращает None
        filepath = os.path.join(temp_dir, 'empty.txt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('')
        
        result = parse_email(filepath)
        assert result is None
    
    def test_parse_json_email(self, temp_dir):
        # проверяет парсинг JSON письма
        content = '''{
            "subject": "JSON тест",
            "from": "json@test.ru",
            "body": "тело из json"
        }'''
        
        filepath = os.path.join(temp_dir, 'test.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = parse_email(filepath)
        
        assert result is not None
        assert result['subject'] == 'JSON тест'
        assert result['from_addr'] == 'json@test.ru'
        assert result['body'] == 'тело из json'
    
    def test_parse_invalid_json(self, temp_dir):
        # проверяет что невалидный JSON возвращает None
        content = '{invalid json}'
        
        filepath = os.path.join(temp_dir, 'invalid.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = parse_email(filepath)
        assert result is None
    
    def test_parse_file_without_headers(self, temp_dir):
        # проверяет письмо без заголовков
        content = """Просто текст письма
без полей subject и from
несколько строк
"""
        filepath = os.path.join(temp_dir, 'no_headers.txt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = parse_email(filepath)
        
        assert result is not None
        assert result['from_addr'] == 'unknown'
    
    def test_parse_nonexistent_file(self):
        # проверяет что несуществующий файл возвращает None
        result = parse_email('/nonexistent/path/file.txt')
        assert result is None


