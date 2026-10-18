# Books to Scrape — парсер каталога книг

Учебный Python-проект для сбора данных из открытого демонстрационного каталога [Books to Scrape](https://books.toscrape.com/).

## Что умеет

- Загружает страницы каталога с помощью `requests`.
- Разбирает HTML через `BeautifulSoup`.
- Собирает название книги, цену, рейтинг от 1 до 5 и ссылку на книгу.
- Переходит по страницам каталога с ограничением количества страниц.
- Повторяет запрос до трёх раз при сетевой ошибке.
- Сохраняет результаты в `result.csv`.
- Проверяет основные функции с помощью `pytest`.

## Технологии

- Python
- requests
- Beautiful Soup 4
- csv из стандартной библиотеки
- pytest

## Установка

```bash
git clone https://github.com/Perdin10/website_parser.git
cd website_parser
python -m venv .venv
```

Активируйте виртуальное окружение:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

## Запуск парсера

```bash
python main.py
```

По умолчанию парсер обрабатывает до четырёх страниц. Результат сохраняется в `result.csv` в текущей рабочей директории.

## Запуск тестов

```bash
python -m pytest -v
```

## Структура проекта

```text
website_parser/
├── main.py
├── test_parser.py
├── requirements.txt
├── result.csv
└── README.md
```

## Примечание

Проект создан в учебных целях. Используется демонстрационный сайт Books to Scrape, предназначенный для практики парсинга.