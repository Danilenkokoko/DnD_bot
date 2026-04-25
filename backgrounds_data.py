# backgrounds_data.py
"""
D&D 5e Backgrounds Data Module
Модуль с данными о предысториях, загружаемыми из PostgreSQL
"""

from typing import Dict, Any, List, Tuple, Optional
from db import get_background_from_db, get_all_backgrounds_from_db

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
        if not backgrounds:
            print("⚠️ Предыстории не загружены (таблица пуста или не существует)")
            _CACHE_LOADED = True
            return

        for bg in backgrounds:
            full_data = get_background_from_db(bg["name"])
            if full_data:
                data = dict(full_data)
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
    """Возвращает список всех предысторий"""
    _load_backgrounds_cache()
    return list(_BACKGROUNDS_CACHE.keys())


def get_background_data(background_name: str) -> Dict[str, Any]:
    """Возвращает данные предыстории по имени"""
    _load_backgrounds_cache()
    return _BACKGROUNDS_CACHE.get(background_name, {})


def get_background_characteristics(background_name: str) -> List[str]:
    """Возвращает характеристики, которые дает предыстория"""
    data = get_background_data(background_name)
    return data.get("characteristics", [])


def get_background_trait(background_name: str) -> str:
    """Возвращает черту предыстории"""
    data = get_background_data(background_name)
    return data.get("trait", "")


def get_background_skills(background_name: str) -> List[str]:
    """Возвращает навыки, которые дает предыстория"""
    data = get_background_data(background_name)
    return data.get("skills", [])


def get_background_tools(background_name: str) -> str:
    """Возвращает инструменты, которые дает предыстория"""
    data = get_background_data(background_name)
    return data.get("tools", "")


def get_background_description(background_name: str) -> str:
    """Возвращает описание предыстории"""
    data = get_background_data(background_name)
    return data.get("description", "")


def get_equipment_choice(background_name: str, choice: str = "A") -> str:
    """Возвращает снаряжение для предыстории в зависимости от выбора А или Б"""
    data = get_background_data(background_name)
    if choice.upper() == "A":
        return data.get("equipment_a", "Нет данных")
    elif choice.upper() == "B":
        return data.get("equipment_b", "Нет данных")
    else:
        return "Неверный выбор"


def get_equipment_options(background_name: str) -> Tuple[str, str]:
    """Возвращает оба варианта снаряжения для предыстории"""
    data = get_background_data(background_name)
    return data.get("equipment_a", ""), data.get("equipment_b", "")


def format_background_info(background_name: str) -> str:
    """Форматирует информацию о предыстории для отображения пользователю"""
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
    """Поиск предысторий по названию или описанию"""
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
    """Возвращает количество предысторий в базе"""
    _load_backgrounds_cache()
    return len(_BACKGROUNDS_CACHE)


def validate_background(background_name: str) -> bool:
    """Проверяет существует ли предыстория"""
    _load_backgrounds_cache()
    return background_name in _BACKGROUNDS_CACHE


# Для совместимости со старым кодом
def get_background_info(background_name: str) -> Dict[str, Any]:
    """Алиас для get_background_data (для совместимости)"""
    return get_background_data(background_name)


# Не загружаем кэш автоматически при импорте, чтобы избежать ошибок до инициализации БД
# _load_backgrounds_cache()


# ---------------- ТЕСТИРОВАНИЕ ----------------
if __name__ == "__main__":
    print("=== Тест предысторий (PostgreSQL) ===\n")

    # Принудительно загружаем
    _load_backgrounds_cache()

    backgrounds = get_all_backgrounds()
    print(f"📚 Всего предысторий: {len(backgrounds)}")

    if backgrounds:
        print(f"Список: {', '.join(backgrounds[:5])}...")
    else:
        print("⚠️ Предыстории не загружены. Убедитесь, что база данных инициализирована.")

    print("\n✅ Модуль предысторий загружен")