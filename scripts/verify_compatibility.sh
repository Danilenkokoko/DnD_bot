#!/bin/bash
# scripts/verify_compatibility.sh
# Скрипт для проверки обратной совместимости

set -e

echo "=========================================="
echo "Verifying Backward Compatibility"
echo "=========================================="

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Проверка импортов (никаких изменений в API)
echo -e "\n${YELLOW}1. Checking imports...${NC}"

# Список функций, которые должны остаться доступными
FUNCTIONS=(
    "get_race_list"
    "get_class_list"
    "get_background_list"
    "get_race_by_name"
    "get_class_by_name"
    "get_background_by_name"
    "get_class_starting_stats"
    "get_class_primary_stats"
    "get_background_characteristics"
    "validate_name"
    "validate_stats"
    "get_class_equipment"
)

for func in "${FUNCTIONS[@]}"; do
    if python -c "from dnd_logic import $func" 2>/dev/null; then
        echo -e "   ${GREEN}✅ $func available${NC}"
    else
        echo -e "   ${RED}❌ $func missing${NC}"
        exit 1
    fi
done

# 2. Проверка deprecated функций (должны работать с предупреждениями)
echo -e "\n${YELLOW}2. Checking deprecated functions...${NC}"

DEPRECATED_FUNCTIONS=(
    "modifier"
    "calculate_proficiency_bonus"
    "calc_hp"
    "calc_ac_with_armor"
)

for func in "${DEPRECATED_FUNCTIONS[@]}"; do
    if python -c "from dnd_logic import $func; import warnings; warnings.simplefilter('ignore'); $func(10 if '$func' != 'calc_hp' else 1)" 2>/dev/null; then
        echo -e "   ${GREEN}✅ $func works (with warning)${NC}"
    else
        echo -e "   ${RED}❌ $func failed${NC}"
        exit 1
    fi
done

# 3. Проверка тестов
echo -e "\n${YELLOW}3. Running compatibility tests...${NC}"

pytest tests/integration/test_backward_compatibility.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All backward compatibility tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some compatibility tests failed!${NC}"
    exit 1
fi

# 4. Проверка отсутствия критических изменений в API
echo -e "\n${YELLOW}4. Checking API stability...${NC}"

# Сравнение сигнатур функций (упрощённо)
python -c "
import inspect
from dnd_logic import get_race_list, get_class_list, get_background_list

# Функции не должны принимать обязательные аргументы
for func in [get_race_list, get_class_list, get_background_list]:
    sig = inspect.signature(func)
    params = sig.parameters
    # Если появились обязательные параметры - это проблема
    for name, param in params.items():
        if param.default == inspect.Parameter.empty:
            print(f'ERROR: {func.__name__} now requires {name}')
            exit(1)
print('API signatures unchanged')
"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ API signatures stable${NC}"
else
    echo -e "   ${RED}❌ API signatures changed!${NC}"
    exit 1
fi

# 5. Проверка формата возвращаемых данных
echo -e "\n${YELLOW}5. Checking return data formats...${NC}"

python -c "
from dnd_logic import get_race_list, get_class_list, get_background_list

# Проверка, что возвращаются списки
races = get_race_list()
if not isinstance(races, list):
    print(f'ERROR: get_race_list returned {type(races)}, expected list')
    exit(1)

classes = get_class_list()
if not isinstance(classes, list):
    print(f'ERROR: get_class_list returned {type(classes)}, expected list')
    exit(1)

backgrounds = get_background_list()
if not isinstance(backgrounds, list):
    print(f'ERROR: get_background_list returned {type(backgrounds)}, expected list')
    exit(1)

print('Return formats unchanged')
"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Return data formats stable${NC}"
else
    echo -e "   ${RED}❌ Return data formats changed!${NC}"
    exit 1
fi

echo -e "\n=========================================="
echo -e "${GREEN}✅ BACKWARD COMPATIBILITY VERIFIED${NC}"
echo -e "=========================================="