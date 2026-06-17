# Система управления заказами «Быстрая доставка»

## Описание проекта

Внутреннее приложение для учёта заказов доставки, управления клиентской базой и построения аналитики. Приложение предоставляет два интерфейса: 
- графический (GUI) для повседневной работы менеджеров,
- консольный (CLI)для административных задач и автоматизации.



## Как работает приложение

### Архитектура

Приложение построено по многослойной архитектуре с чётким разделением ответственности:
─────────────────────────────────────────┐
│ Presentation Layer │
│ (main_gui.py, main_cli.py) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ Business Logic Layer │
│ (database.py, data_export.py) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ Data Layer │
│ (models.py, SQLite database) │
└─────────────────────────────────────────┘

### Поток данных

#### 1. Работа с клиентами

Добавление клиента:
Пользователь вводит данные в GUI
↓
Создаётся объект Customer (models.py)
↓
DatabaseManager.add_customer() (database.py)
↓
SQL INSERT INTO customers
↓
Запись в лог: "Добавлен клиент: {name}"

Редактирование клиента: 
Пользователь выбирает клиента из списка
↓
Открывается форма с предзаполненными данными
↓
Пользователь изменяет данные
↓
DatabaseManager выполняет SQL UPDATE
↓
Проверка на дубликаты имён

Удаление клиента:
Пользователь выбирает клиента
↓
Проверка наличия заказов (SELECT FROM orders WHERE customer_id=?)
↓
Если заказы есть → SQLite IntegrityError → Ошибка удаления
Если заказов нет → SQL DELETE → Успех

#### 2. Работа с заказами

Создание заказа:
Пользователь выбирает клиента из ComboBox
↓
Вводит товары в формате: "Название, Количество, Цена"
↓
Система парсит строки и рассчитывает total = Σ(quantity × price)
↓
Начинается транзакция:
INSERT INTO orders (возвращается order_id)
INSERT INTO order_items для каждого товара
↓
Коммит транзакции

Фильтрация заказов:
Пользователь выбирает статус в ComboBox
↓
Событие <<ComboboxSelected>>
↓
SQL SELECT с WHERE status = ?
↓
Обновление Treeview в GUI

#### 3. Экспорт и импорт данных

Экспорт:
db.get_orders() → получение всех заказов
↓
Преобразование в словари (JSON) или XML-элементы
↓
Запись в файл

Импорт:
Чтение файла (JSON/XML)
↓
Парсинг структуры
↓
Валидация обязательных полей
↓
Создание объектов Order и OrderItem
↓
db.add_order() для каждой записи


#### 4. Отчёты и аналитика

SQL-запросы:
- Количество заказов по статусам: `SELECT status, COUNT(*) FROM orders GROUP BY status`
- Топ-3 клиента: `SELECT c.name, SUM(o.total) FROM orders JOIN customers ... ORDER BY total_sum DESC LIMIT 3`
- Выручка за период: `SELECT SUM(total) FROM orders WHERE order_date >= ?`



## Структура кода
delivery_system/
│
├── main_gui.py # Графический интерфейс (Tkinter)
│ ├── Класс DeliveryApp
│ │ ├── init() - инициализация окна и БД
│ │ ├── _create_widgets() - создание кнопок и таблицы
│ │ ├── _load_orders() - загрузка заказов в таблицу
│ │ │
│ │ ├── Методы управления клиентами:
│ │ │ ├── _add_customer_dialog() - диалог добавления
│ │ │ ├── _edit_customer_dialog() - выбор клиента для редактирования
│ │ │ ├── _open_edit_customer_form() - форма редактирования
│ │ │ └── _delete_customer_dialog() - диалог удаления
│ │ │
│ │ └── Методы управления заказами:
│ │ ├── _add_order() - диалог добавления заказа
│ │ ├── _edit_order() - редактирование выбранного заказа
│ │ ├── _delete_order() - удаление заказа
│ │ ├── _open_order_dialog() - форма заказа
│ │ └── _show_report() - окно отчёта
│ │
├── main_cli.py # Консольный интерфейс (argparse)
│ ├── Функция main()
│ │ ├── Парсинг аргументов командной строки
│ │ ├── Обработка команд:
│ │ │ ├── report --period [day|week|month]
│ │ │ ├── export --file <filename>
│ │ │ ├── import --file <filename>
│ │ │ ├── add-customer --name --phone --address
│ │ │ └── delete-customer --id
│ │ └── Вывод результатов в консоль
│ │
├── database.py # Слой работы с базой данных
│ ├── Класс DatabaseManager
│ │ ├── init() - инициализация БД, создание таблиц
│ │ ├── _get_connection() - получение соединения с БД
│ │ ├── _init_db() - создание таблиц customers, orders, order_items
│ │ │
│ │ ├── Методы для клиентов:
│ │ │ ├── add_customer() - INSERT
│ │ │ ├── get_customers() - SELECT всех клиентов
│ │ │ ── delete_customer() - DELETE с обработкой IntegrityError
│ │ │
│ │ ├── Методы для заказов:
│ │ │ ├── add_order() - INSERT в orders и order_items (транзакция)
│ │ │ ├── update_order() - UPDATE orders, DELETE+INSERT order_items
│ │ │ ├── delete_order() - DELETE из orders (CASCADE для items)
│ │ │ └── get_orders() - SELECT с JOIN и фильтрацией
│ │ │
│ │ └── Методы для отчётов:
│ │ └── get_report() - агрегатные запросы (COUNT, SUM, GROUP BY)
│ │
├── models.py # Модели данных
│ ├── @dataclass Customer
│ │ ├── id: int
│ │ ├── name: str
│ │ ├── phone: str
│ │ └── address: str
│ │
│ ├── @dataclass OrderItem
│ │ ├── id: int
│ │ ├── order_id: int
│ │ ├── product_name: str
│ │ ├── quantity: int
│ │ ── price: float
│ │
│ └── @dataclass Order
│ ├── id: int
│ ├── customer_id: int
│ ├── order_date: str
│ ├── status: str
│ ├── total: float
│ ├── items: List[OrderItem]
│ └── customer_name: str
│ │
├── data_export.py # Экспорт и импорт данных
│ ├── Класс DataExporter
│ │ ├── export_json() - сериализация в JSON
│ │ ├── import_json() - десериализация из JSON с валидацией
│ │ ├── export_xml() - создание XML-дерева
│ │ ── import_xml() - парсинг XML и создание объектов
│ │
├── logger_config.py # Настройка логирования
│ ├── Функция setup_logger()
│ │ ├── Создание FileHandler (logs/app.log)
│ │ ├── Создание StreamHandler (консоль)
│ │ └── Настройка формата: [время] - [модуль] - [уровень] - [сообщение]
│ │
├── requirements.txt # Зависимости проекта
│ └── pytest>=7.0.0
│ │
├── tests/ # Модульные тесты
│ ├── test_database.py
│ │ ├── Тесты добавления/получения клиентов
│ │ ├── Тесты добавления/получения заказов
│ │ └── Тест ON DELETE RESTRICT
│ │
│ ├── test_export.py
│ │ ├── Тест экспорта/импорта JSON
│ │ └── Тест экспорта/импорта XML
│ │
│ └── test_models.py
│ └── Тесты создания моделей
│ │
├── logs/ # Папка для логов (создаётся автоматически)
│ └── app.log
│ │
└── data/ # Папка для базы данных (создаётся автоматически)
└── delivery.db

#### Установка и запуск
Требования:
* Python 3.8 или выше
* pip

cd delivery_system
pip install -r requirements.txt

Запуск
Графический интерфейс:
- python main_gui.py

Консольный интерфейс:
- python main_cli.py


#### Примеры использования
* GUI: Работа менеджера
- Добавить клиента:
Кнопка «Добавить клиента»
↓
Ввести имя, телефон, адрес
↓
Сохранить

- Создать заказ:
Кнопка «Добавить заказ»
↓
Выбрать клиента
↓
Ввести товары: Ноутбук, 1, 45000.00
↓
Сохранить

- Посмотреть отчёт:
Кнопка «Показать отчёт»
↓
Увидеть выручку и топ клиентов

* CLI: Административные задачи
* 
# Отчёт за месяц
python main_cli.py report --period month

# Добавить клиента
python main_cli.py add-customer --name "Иванов И." --phone "+79991234567"

# Экспорт данных
python main_cli.py export --file backup.json

# Импорт данных
python main_cli.py import --file backup.json

#### Тестирование
pytest tests/ -v
* Тесты используют изолированные базы данных (в памяти), не затрагивая основную БД.

#### Логирование
Все операции записываются в logs/app.log:
Создание/редактирование/удаление клиентов и заказов
Ошибки импорта/экспорта
Попытки нарушения целостности данных

#### Ключевые особенности
Защита данных: Невозможно удалить клиента с заказами (ON DELETE RESTRICT)
Транзакции: Все операции с заказами атомарны
Валидация: Проверка формата товаров и обязательных полей
Два формата: Поддержка JSON и XML для экспорта/импорта
Модульность: Чёткое разделение слоёв приложения
