Telegram бот, который помогает игрокам создать персонажа для игры в ДнД.
На выходе получается готовый персонаж первого уровня. Информация о персонаже сохраняется в базе данных.
Также после создание доступна возможность скачать лист персонажа в PDF формате.

Структура проекта:
dnd-bot/
│
├── bot.py                    # Точка входа, инициализация
│
├── handlers/                 # UI слой (Telegram)
│   ├── character_handlers.py # Создание персонажа
│   ├── spell_handlers.py     # Выбор заклинаний
│   ├── view_handlers.py      # Просмотр/удаление
│   └── __init__.py
│
├── keyboards/                # UI клавиатуры
│   ├── character_keyboards.py
│   ├── spell_keyboards.py
│   └── __init__.py
│
├── states/                   # FSM состояния
│   ├── character_states.py
│   └── __init__.py
│
├── services/                 # Прикладной слой
│   ├── character_service.py  # Расчёт характеристик
│   ├── spell_service.py      # Выбор заклинаний
│   ├── progression_service.py # Порядок шагов
│   └── __init__.py
│
├── engine/                   # Игровой движок (чистая логика)
│   ├── stats/                # Характеристики
│   │   ├── models.py
│   │   ├── validation.py
│   │   ├── distribution.py
│   │   └── __init__.py
│   ├── hp.py                 # Расчёт хитов
│   ├── ac.py                 # Расчёт КБ
│   ├── proficiency.py        # Бонус мастерства
│   ├── dice.py               # Броски кубов
│   ├── validators.py         # Общие валидаторы
│   └── __init__.py
│
├── repositories/             # Data слой (будущее)
│   ├── character_repository.py
│   ├── class_repository.py
│   └── __init__.py
│
├── db.py                     # Подключение к БД
├── dnd_logic.py              # Доступ к данным (legacy)
├── pdf_generator.py          # Генерация PDF
├── spell_selector.py         # Выбор заклинаний
│
├── tests/                    # Тесты
│   ├── engine/               # Тесты engine
│   ├── services/             # Тесты сервисов
│   ├── integration/          # Интеграционные тесты
│   ├── conftest.py           # Фикстуры
│   └── __init__.py
│
├── scripts/                  # Утилиты
│   ├── run_tests.sh
│   ├── load_initial_data.py
│   └── coverage_badge.py
│
├── images/                   # Изображения
│   ├── races/
│   └── classes/
│
├── .env                      # Переменные окружения
├── .coveragerc               # Конфигурация coverage
├── pytest.ini                # Конфигурация pytest
├── requirements.txt          # Зависимости
├── Makefile                  # Утилиты
└── README.md                 # Документация
