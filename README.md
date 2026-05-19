# D&D Character Creator Bot (5.5e / PHB 2024)

Telegram-бот для пошагового создания персонажа D&D первого уровня по
правилам **PHB 2024 (5.5e)**. Готовый персонаж сохраняется в PostgreSQL и
доступен в трёх форматах: текстовый лист в Telegram, веб-страница и PDF.

## Возможности

- **13 классов** — Артефактор, Бард, Варвар, Воин, Волшебник, Друид,
  Жрец, Колдун, Монах, Паладин, Плут, Следопыт, Чародей.
- **16 рас** + подрасы + 10 типов наследия Драконорождённого.
- **16 предысторий** с уникальными Origin Feat.
- **Стандартный массив** для назначения характеристик (15·14·13·12·10·8).
- **Подклассы на 1-м уровне** для Друида, Жреца, Колдуна и Чародея
  (Sorcerous Origin — PHB 2024).
- **Eldritch Invocations** для Колдуна; **Pact of the Tome** с выбором
  3 кантрипов и 2 ритуалов.
- **Боевой стиль** для Воина (PHB 2024 — Паладин/Следопыт получают на
  2/3 ур.).
- **Weapon Mastery** для физических классов (Воин 3, остальные 2).
- **Опция «50 GP вместо набора снаряжения»** на экранах снаряжения
  класса и предыстории.
- **Общий выбор языков** после расы — мультиселект до 2 языков с
  дефолтами от предыстории.
- **Безделушка (Trinket)** — пул из 30 нарративных вариантов с кубиком
  или пропуском.
- **Финальный лист в 5 сообщениях Telegram** параллельно с веб-страницей
  и PDF.

## Архитектура

```
bot.py                       — точка входа (aiogram 3, MemoryStorage)
webapp.py                    — встроенный веб-сервер (Flask + Jinja)
pdf_generator.py             — PDF-экспорт листа персонажа

handlers/                    — aiogram routers (FSM-обработчики)
  character_handlers.py
  spell_handlers.py

services/                    — бизнес-логика
  character_service.py
  progression_service.py     — WizardStep enum + state-machine
  spell_service.py
  auto_choices.py            — данные/хелперы (skills, languages,
                               sorcerer origins, trinkets, weapon mastery)
  telegram_sheet_service.py  — финальный лист в 5 Telegram-сообщений

engine/                      — pure-вычисления (без БД/aiogram)
  ac.py / hp.py / proficiency.py / spell_slots.py / dice.py
  stats/distribution.py      — распределитель бонусов предыстории

repositories/                — слой доступа к PostgreSQL
  character_repository.py
  background_repository.py / class_repository.py / race_repository.py
  equipment_repository.py / spell_repository.py

states/character_states.py   — FSM-состояния шагов wizard'а
keyboards/character_keyboards.py — inline-клавиатуры
strings.py                   — UI-строки на русском
db.py                        — пул соединений + миграции схемы
classes_data.py / races_data.py / backgrounds_data.py — справочные данные

tests/                       — pytest
  enfine/                    — edge-case unit-тесты движка (45 тестов)
  integration/               — full-flow + backward-compat (44 теста)
  repositories/              — тесты репозиториев (31 тест)
  services/                  — тесты сервисов (100 тестов)
```

## Wizard персонажа — порядок шагов

```
1. Класс
   └─ Подкласс (Друид/Жрец/Колдун/Чародей) или Sorcerous Origin
2. Навыки класса
3. Заклинания (для кастеров) + Invocations (Колдун) + Pact of the Tome
4. Боевой стиль (только Воин)
5. Снаряжение класса (пакет А/Б ИЛИ 50 GP)
6. Предыстория
   ├─ Origin Feat (отдельный экран показа)
   └─ Снаряжение предыстории (пакет А/Б ИЛИ 50 GP)
7. Назначение характеристик (стандартный массив)
8. Раса + подраса + драконье наследие
9. Языки (мультиселект до 2)
10. Имя + история + мировоззрение + Trinket + изображение
→ Финал: сохранение в БД + 5-сообщений Telegram + Web App + PDF
```

Подробная схема: [`docs/wizard-flow.md`](docs/wizard-flow.md).

## Команды бота

- `/start` — главное меню.
- `/menu` — вернуться в главное меню.
- `/help` — справка по созданию персонажа.

## Установка локально

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd D&D_bot

# 2. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env (в корне проекта)
# BOT_TOKEN=<токен от @BotFather>
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=dnd_bot
# DB_USER=postgres
# DB_PASSWORD=<пароль>

# 5. Запустить PostgreSQL (если ещё не запущен)

# 6. Запустить бота — он сам инициализирует БД при первом запуске
python bot.py
```

## Тесты

```bash
# Установить зависимости для тестов
pip install pytest pytest-mock pytest-asyncio

# Прогон всех тестов
pytest -q

# Только сервисный слой (100 тестов, без БД)
pytest tests/services -v

# С покрытием
pytest --cov=. --cov-report=html
```

## База данных и миграции

При старте бота `db.init_db()` создаёт все таблицы и `migrate_database_v2()`
добавляет недостающие колонки через идемпотентный `add_column_if_missing`.
Никаких внешних инструментов миграций не требуется.

**Опциональные SQL-скрипты** (запускаются вручную, если нужны):
- `migrations/0001_drop_personality_columns.sql` — удалить колонки
  `personality_trait/ideal/bond/flaw` из таблицы `characters` после
  Этапа 1 (деструктивно — сделать `pg_dump` перед запуском).

## Эволюция проекта

Проект приведён к плану PHB 2024 через 9 incremental-этапов
(см. [`docs/migration-notes.md`](docs/migration-notes.md)):

- **Этап 0** — журналы изменений.
- **Этап 1** — удалён шаг «4 черты личности».
- **Этап 2** — шаг назначения характеристик стандартным массивом.
- **Этап 3** — 6 недостающих шагов: Languages, Trinket, Origin Feat,
  Gold-опция, Sorcerous Origin, ограничение Fighting Style до Воина.
- **Этап 4** — WizardStep enum + state-machine + UX-индикатор «Шаг X из 10».
- **Этап 5** — финальный лист в 5 Telegram-сообщений.
- **Этап 8** — 100 unit-тестов на сервисный слой.
- **Этап 9** — cleanup orphan-кода, обновление документации.

## Технологии

- Python 3.10+
- [aiogram 3](https://docs.aiogram.dev/) — Telegram Bot API
- PostgreSQL + psycopg2 — хранилище
- Flask + Jinja2 — встроенный веб-сервер для просмотра листа
- pytest — тесты
- python-dotenv — переменные окружения

## Лицензия

Внутренний проект. Все права на правила D&D / PHB 2024 — Wizards of the Coast.
