#!/usr/bin/env python3
# check_bot_state.py
import os
import re

def check_duplicate_handler():
    file_path = "handlers/character_handlers.py"
    if not os.path.exists(file_path):
        return "Файл handlers/character_handlers.py не найден"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'@router\.message\(F\.text\s*==\s*"✅ Продолжить"\)'
    matches = re.findall(pattern, content)
    if matches:
        return f"❌ Найден дублирующий обработчик в {file_path}"
    else:
        return "✅ Дублирующий обработчик не найден"

def check_spell_router_in_bot():
    file_path = "bot.py"
    if not os.path.exists(file_path):
        return "Файл bot.py не найден"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import_pattern = r"from handlers\.spell_handlers import router as spell_router"
    include_pattern = r"dp\.include_router\(spell_router\)"
    if re.search(import_pattern, content) and re.search(include_pattern, content):
        return "✅ spell_router правильно подключён в bot.py"
    else:
        return "❌ spell_router не подключён или подключён неправильно"

def check_pycache():
    pycache_dirs = []
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_dirs.append(os.path.join(root, "__pycache__"))
    if pycache_dirs:
        return f"⚠️ Найдены папки __pycache__, возможно, старый код закэширован. Удалите их: {', '.join(pycache_dirs)}"
    else:
        return "✅ Папки __pycache__ не найдены"

def check_start_level1_selection():
    file_path = "services/spell_service.py"
    if not os.path.exists(file_path):
        return "Файл services/spell_service.py не найден"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if "async def start_level1_selection" in content:
        return "✅ Метод start_level1_selection существует"
    else:
        return "❌ Метод start_level1_selection отсутствует"

def check_state_setting():
    file_path = "services/spell_service.py"
    if not os.path.exists(file_path):
        return "Файл services/spell_service.py не найден"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if "CreateCharacter.spells_cantrips_complete" in content:
        return "✅ Состояние spells_cantrips_complete устанавливается"
    else:
        return "❌ Состояние spells_cantrips_complete не устанавливается"

def main():
    print("=== ДИАГНОСТИКА ПРОБЛЕМЫ КНОПКИ 'ПРОДОЛЖИТЬ' ===\n")
    print("1. Проверка дублирующего обработчика:", check_duplicate_handler())
    print("2. Проверка подключения spell_router в bot.py:", check_spell_router_in_bot())
    print("3. Проверка кэша Python:", check_pycache())
    print("4. Проверка наличия start_level1_selection:", check_start_level1_selection())
    print("5. Проверка установки состояния spells_cantrips_complete:", check_state_setting())
    print("\n=== РЕКОМЕНДАЦИИ ===")
    print("Если обнаружены дублирующие обработчики – удалите их.")
    print("Если есть папки __pycache__ – удалите их командой: find . -type d -name __pycache__ -exec rm -rf {} +")
    print("Убедитесь, что состояния FSM правильно устанавливаются при выборе последнего заговора.")
    print("После исправлений перезапустите бота и проверьте логи.")

if __name__ == "__main__":
    main()