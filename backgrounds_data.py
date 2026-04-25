# backgrounds_data.py
"""
D&D 5e Backgrounds Data Module
Модуль с данными о предысториях, загружаемыми из PostgreSQL
"""

from typing import Dict, Any, List, Tuple, Optional
from db import get_background_from_db, get_all_backgrounds_from_db, get_background_names

# Кэш для данных (чтобы не ходить в БД каждый раз)
_BACKGROUNDS_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOADED = False


def _load_backgrounds_cache():
    """Загружает все предыстории в кэш"""
    global _BACKGROUNDS_CACHE, _CACHE_LOADED

    if _CACHE_LOADED:
        return

    try:
        backgrounds = get_all_backgrounds_from_db()
        for bg in backgrounds:
            # Получаем полные данные для каждой предыстории
            full_data = get_background_from_db(bg["name"])
            if full_data:
                # Преобразуем JSONB данные обратно в списки
                data = dict(full_data)

                # Обрабатываем JSONB поля
                if isinstance(data.get("characteristics"), str):
                    import json
                    data["characteristics"] = json.loads(data["characteristics"])
                if isinstance(data.get("skills"), str):
                    import json
                    data["skills"] = json.loads(data["skills"])

                _BACKGROUNDS_CACHE[bg["name"]] = data

        _CACHE_LOADED = True
        print(f"✅ Загружено {len(_BACKGROUNDS_CACHE)} предысторий из PostgreSQL")

    except Exception as e:
        print(f"⚠️ Ошибка загрузки предысторий из БД: {e}")
        _BACKGROUNDS_CACHE = {}
        _CACHE_LOADED = True


def reload_cache():
    """Принудительная перезагрузка кэша"""
    global _CACHE_LOADED
    _CACHE_LOADED = False
    _load_backgrounds_cache()


def get_all_backgrounds() -> List[str]:
    """
    Возвращает список всех предысторий

    Returns:
        List[str]: Список названий предысторий
    """
    _load_backgrounds_cache()
    return list(_BACKGROUNDS_CACHE.keys())


def get_background_data(background_name: str) -> Dict[str, Any]:
    """
    Возвращает данные предыстории по имени

    Args:
        background_name: название предыстории

    Returns:
        Dict[str, Any]: словарь с данными предыстории
    """
    _load_backgrounds_cache()
    return _BACKGROUNDS_CACHE.get(background_name, {})


def get_background_characteristics(background_name: str) -> List[str]:
    """
    Возвращает характеристики, которые дает предыстория

    Args:
        background_name: название предыстории

    Returns:
        List[str]: список характеристик
    """
    data = get_background_data(background_name)
    return data.get("characteristics", [])


def get_background_trait(background_name: str) -> str:
    """
    Возвращает черту предыстории

    Args:
        background_name: название предыстории

    Returns:
        str: черта предыстории
    """
    data = get_background_data(background_name)
    return data.get("trait", "")


def get_background_skills(background_name: str) -> List[str]:
    """
    Возвращает навыки, которые дает предыстория

    Args:
        background_name: название предыстории

    Returns:
        List[str]: список навыков
    """
    data = get_background_data(background_name)
    return data.get("skills", [])


def get_background_tools(background_name: str) -> str:
    """
    Возвращает инструменты, которые дает предыстория

    Args:
        background_name: название предыстории

    Returns:
        str: инструменты
    """
    data = get_background_data(background_name)
    return data.get("tools", "")


def get_background_description(background_name: str) -> str:
    """
    Возвращает описание предыстории

    Args:
        background_name: название предыстории

    Returns:
        str: описание предыстории
    """
    data = get_background_data(background_name)
    return data.get("description", "")


def get_equipment_choice(background_name: str, choice: str = "A") -> str:
    """
    Возвращает снаряжение для предыстории в зависимости от выбора А или Б

    Args:
        background_name: название предыстории
        choice: выбор "A" или "B"

    Returns:
        str: описание снаряжения
    """
    data = get_background_data(background_name)
    if choice.upper() == "A":
        return data.get("equipment_a", "Нет данных")
    elif choice.upper() == "B":
        return data.get("equipment_b", "Нет данных")
    else:
        return "Неверный выбор"


def get_equipment_options(background_name: str) -> Tuple[str, str]:
    """
    Возвращает оба варианта снаряжения для предыстории

    Args:
        background_name: название предыстории

    Returns:
        Tuple[str, str]: (снаряжение А, снаряжение Б)
    """
    data = get_background_data(background_name)
    return data.get("equipment_a", ""), data.get("equipment_b", "")


def format_background_info(background_name: str) -> str:
    """
    Форматирует информацию о предыстории для отображения пользователю

    Args:
        background_name: название предыстории

    Returns:
        str: отформатированный текст
    """
    data = get_background_data(background_name)
    if not data:
        return f"❌ Предыстория '{background_name}' не найдена"

    info = f"📜 **{background_name}**\n\n"
    info += f"**Описание:** {data.get('description', 'Нет описания')[:200]}...\n\n"
    info += f"**Черта:** {data.get('trait', 'Нет')}\n"
    info += f"**Характеристики:** {', '.join(data.get('characteristics', []))}\n"
    info += f"**Навыки:** {', '.join(data.get('skills', []))}\n"
    info += f"**Инструменты:** {data.get('tools', 'Нет')}\n\n"
    info += f"**Снаряжение А:** {data.get('equipment_a', 'Нет')[:100]}...\n"
    info += f"**Снаряжение Б:** {data.get('equipment_b', 'Нет')[:100]}..."

    return info


def search_backgrounds(query: str) -> List[Dict[str, Any]]:
    """
    Поиск предысторий по названию или описанию

    Args:
        query: поисковый запрос

    Returns:
        List[Dict[str, Any]]: список найденных предысторий
    """
    _load_backgrounds_cache()
    query_lower = query.lower()
    results = []

    for name, data in _BACKGROUNDS_CACHE.items():
        if query_lower in name.lower() or query_lower in data.get("description", "").lower():
            results.append({
                "name": name,
                "description": data.get("description", "")[:150]
            })

    return results


def get_backgrounds_count() -> int:
    """
    Возвращает количество предысторий в базе

    Returns:
        int: количество предысторий
    """
    _load_backgrounds_cache()
    return len(_BACKGROUNDS_CACHE)


def validate_background(background_name: str) -> bool:
    """
    Проверяет существует ли предыстория

    Args:
        background_name: название предыстории

    Returns:
        bool: True если существует
    """
    _load_backgrounds_cache()
    return background_name in _BACKGROUNDS_CACHE


# Загружаем кэш при импорте модуля
_load_backgrounds_cache()


# Для совместимости со старым кодом
def get_background_info(background_name: str) -> Dict[str, Any]:
    """
    Алиас для get_background_data (для совместимости)
    """
    return get_background_data(background_name)


# ---------------- ТЕСТИРОВАНИЕ ----------------
if __name__ == "__main__":
    print("=== Тест предысторий (PostgreSQL) ===\n")

    # Проверяем соединение с БД
    try:
        from db import init_database

        init_database()
        print("✅ Подключение к БД установлено\n")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}\n")
        print("Убедитесь, что:")
        print("1. PostgreSQL запущен")
        print("2. Переменные окружения DB_NAME, DB_USER, DB_PASSWORD, DB_HOST заданы")
        print("3. База данных существует\n")
        exit(1)

    # Получаем список всех предысторий
    backgrounds = get_all_backgrounds()
    print(f"📚 Всего предысторий: {len(backgrounds)}")
    print(f"Список: {', '.join(backgrounds)}\n")

    # Проверяем каждую предысторию
    print("=" * 50)
    print("Детальная информация о предысториях:")
    print("=" * 50)

    for bg_name in backgrounds[:5]:  # Показываем первые 5 для примера
        print(f"\n📜 {bg_name}")
        print("-" * 40)

        data = get_background_data(bg_name)
        if data:
            print(f"  Характеристики: {', '.join(data.get('characteristics', []))}")
            print(f"  Черта: {data.get('trait', 'Нет')}")
            print(f"  Навыки: {', '.join(data.get('skills', []))}")
            print(f"  Инструменты: {data.get('tools', 'Нет')}")
            print(f"  Снаряжение А: {data.get('equipment_a', 'Нет')[:60]}...")
            print(f"  Снаряжение Б: {data.get('equipment_b', 'Нет')[:60]}...")
            print(f"  Описание: {data.get('description', 'Нет')[:100]}...")

    # Тестирование дополнительных функций
    print("\n" + "=" * 50)
    print("Тестирование дополнительных функций:")
    print("=" * 50)

    # Тест форматирования
    if backgrounds:
        print(f"\n📋 Форматированная информация о '{backgrounds[0]}':")
        print(get_background_info(backgrounds[0]))

    # Тест поиска
    print("\n🔍 Поиск предысторий по слову 'маг':")
    results = search_backgrounds("маг")
    for result in results:
        print(f"  - {result['name']}: {result['description']}...")

    # Тест валидации
    print(f"\n✅ Проверка существования 'Мудрец': {validate_background('Мудрец')}")
    print(f"❌ Проверка существования 'НесуществующаяПредыстория': {validate_background('НесуществующаяПредыстория')}")

    # Тест выбора снаряжения
    if backgrounds:
        print(f"\n🎒 Выбор снаряжения для '{backgrounds[0]}':")
        equip_a, equip_b = get_equipment_options(backgrounds[0])
        print(f"  Вариант А: {equip_a[:80]}...")
        print(f"  Вариант Б: {equip_b[:80]}...")

    print("\n" + "=" * 50)
    print("✅ Модуль предысторий успешно протестирован!")
    print("=" * 50)