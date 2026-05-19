# Wizard Flow — текущий vs целевой

Документ сравнивает реальный порядок шагов создания персонажа в боте
с порядком из плана `dnd2024-telegram-bot-architecture.md` (PHB 2024).

## Текущий порядок (как сейчас в `handlers/character_handlers.py`)

```
/start
  └─ Главное меню (BTN_CREATE_CHAR)
      │
      ▼
[1]  class_select               ← выбор класса
      │
      ├─ Друид ─→  druid_order_select   ─┐
      ├─ Жрец  ─→  cleric_order_select  ─┤
      ├─ Колдун→  warlock_pact_select   ─┤  (subclass/order/pact на 1-м уровне)
      │            ├─ Tome → tome_cantrips/rituals
      │            └─ → warlock_invocation_select
      └─ остальные ───────────────────────┘
                                          ▼
[2]  skills_select               ← навыки от класса
      │
      ├─ Плут → rogue_expertise_select
      │       → rogue_language_select
      │
      ▼
     [если класс заклинатель]
      spells_cantrips_category → list → detail → complete
      spells_level1_category → list → detail → complete
      │
     [если Воин / Паладин / Следопыт]
[3]  fighting_style_select
      │
     [если Следопыт]
      ranger_favored_enemy_select
      │
      ▼
[4]  class_equipment_select      ← выбор стартового набора (A/B)
      │
      ▼
[5]  background_select           ← выбор предыстории
      │
      ▼
[6]  background_equipment_select ← набор предыстории (A/B)
      │
      ▼
     calculate_and_show_stats    ← АВТО-генерация хар-к из CLASS_STARTING_STATS
                                    (без участия игрока — ⚠ расхождение с планом)
      │
      ▼
[7]  race_select                 ← выбор расы
      │
      ├─ если есть подрасы → subrace_select
      └─ Драконорождённый    → draconic_ancestry_select
      │
      ▼
[8]  name_input                  ← текстовый ввод имени
      │
      ▼
[9]  backstory_input             ← текстовый ввод истории (не в плане)
      │
      ▼
[10] alignment_select            ← мировоззрение
      │
      ▼
[11] personality_intro           ← ⚠ ЗАПЛАНИРОВАНО К УДАЛЕНИЮ
      ├─ personality_trait_input
      ├─ personality_ideal_input
      ├─ personality_bond_input
      └─ personality_flaw_input
      │
      ▼
[12] image_input                 ← загрузка картинки (не в плане)
      │
      ▼
     finalize_character          ← сохранение в БД + веб-лист + PDF
```

## Целевой порядок (по плану PHB 2024)

```
/start
  └─ Главное меню
      │
      ▼
[1]  class                       ← выбор класса
      │
      ├─ Жрец / Друид / Колдун / Чародей → subclass
      │     └─ Колдун → invocations (1 на 1-м уровне)
      │
      └─ Воин → fighting_style
      │
      ▼
[2]  background                  ← предыстория
      │
      ▼
[2а] origin_feat                 ← экран показа Origin Feat (новый шаг)
      │
      ▼
[2б] background_bonus            ← выбор раскладки бонусов (+2/+1 или 1/1/1)
      │
      ▼
[2в] species                     ← вид (раса)
      │
      └─ если есть подвиды → subrace
      │
      ▼
[2г] language                    ← общий выбор языков (новый шаг)
      │
      ▼
[3]  abilities                   ← ★ НОВЫЙ ШАГ: назначение
                                   стандартного массива [15,14,13,12,10,8]
                                   на 6 характеристик игроком
      │
      ▼
[4]  skills                      ← навыки (от класса + предыстории)
      │
      ▼
[5]  equipment                   ← пакет ИЛИ 50 GP (новая опция «50 GP»)
      │
      ▼
[6]  spells                      ← заклинания (для кастеров)
      │
      ▼
[6а] invocations                 ← Eldritch Invocations (Колдун)
      │
      ▼
[6б] weapon_mastery              ← мастерство оружия (физические)
      │
      ▼
[7]  details                     ← имя, мировоззрение, trinket (новый шаг)
                                   + опционально backstory, image (наши доп.)
      │
      ▼
[8]  summary                     ← финальный лист
                                   • веб-страница (оставляем)
                                   • PDF (оставляем)
                                   • 5 сообщений Telegram (новый)
```

## Карта расхождений

| # | Сейчас                                       | Должно быть                                          | Этап |
|---|----------------------------------------------|------------------------------------------------------|------|
| 1 | Хар-ки авто из `CLASS_STARTING_STATS`        | Игрок назначает стандартный массив инлайн-кнопками   | 2    |
| 2 | Skills сразу после класса                    | Skills после Species/Languages/Abilities             | 4    |
| 3 | Equipment до Background                      | Equipment после Skills                               | 4    |
| 4 | Background bonus распределяется автоматически| Игрок выбирает раскладку (+2/+1 или 1/1/1)           | 3.2/4|
| 5 | Нет шага языков (только для Плута)           | Отдельный шаг `language`                             | 3.1  |
| 6 | Нет Trinket                                  | Шаг `trinket` (roll / skip)                          | 3.2  |
| 7 | Origin Feat скрыт в БД                       | Отдельный экран `origin_feat` с описанием            | 3.3  |
| 8 | Equipment: только A/B наборы                 | Добавить «50 GP вместо набора»                       | 3.4  |
| 9 | Чародей без подкласса на 1-м                 | Sorcerous Origin на 1-м уровне                       | 3.5  |
| 10| Fighting Style: Воин/Паладин/Следопыт         | Только Воин (PHB 2024: Pal/Rng через черту на 2)     | 3.6  |
| 11| Personality (4 черты)                        | Удалить (по запросу владельца проекта)               | 1    |
| 12| Финальный лист — только web/PDF              | Добавить 5-сообщений в Telegram                      | 5    |

## Заметки для UX

- Каждый шаг должен иметь кнопку «◀️ Назад», кроме шага 1.
- Текущий выбор пишется в текст сообщения, а не только в кнопку
  («Выбрано: Воин» — даже если кнопки сменились).
- Выбранный вариант помечается ✅ в самой кнопке.
- Для списков > 6 пунктов — пагинация по 6 в страницу.
- Длинные тексты дробятся, лимит 4096 символов на сообщение.
- `answerCallbackQuery()` всегда первым делом — убирает спиннер.

## Заметки для рефакторинга

`ProgressionService` сейчас содержит лоскутные функции
(`go_to_spells`, `go_to_fighting_style`, `go_to_background`). По
завершении Этапа 4 он становится единой машиной переходов:

```python
class ProgressionService:
    @staticmethod
    def next_step(state_data: dict, current: WizardStep) -> WizardStep:
        # Возвращает следующий шаг с учётом класса, кастер/не-кастер,
        # подкласса, наличия подвидов и т.д.
        ...
```

Все вызовы `proceed_to_*` в `handlers/character_handlers.py` заменить
на `await ProgressionService.advance(callback, state)`.
