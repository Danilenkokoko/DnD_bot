#!/bin/bash
# scripts/run_tests.sh
# Скрипт для запуска тестов с coverage

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}D&D Character Creator - Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Установка зависимостей для тестирования
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install pytest pytest-cov pytest-xdist pytest-timeout coverage 2>/dev/null || true

# Создание директории для отчётов
mkdir -p reports

# Функция для запуска тестов
run_tests() {
    local test_path=$1
    local test_name=$2

    echo -e "${GREEN}Running $test_name tests...${NC}"
    pytest $test_path \
        --cov-report=term-missing \
        --cov-report=html:reports/htmlcov_${test_name} \
        --cov-report=xml:reports/coverage_${test_name}.xml \
        --cov-report=json:reports/coverage_${test_name}.json \
        -m "not slow" \
        -v \
        --tb=short
}

# Запуск разных категорий тестов
run_tests "tests/engine/" "engine"
run_tests "tests/services/" "services"
run_tests "tests/integration/" "integration"

# Запуск всех тестов (включая медленные) с объединённым отчётом
echo -e "${GREEN}Running all tests with combined coverage...${NC}"
pytest tests/ \
    --cov=engine \
    --cov=services \
    --cov=handlers \
    --cov-report=term-missing \
    --cov-report=html:reports/htmlcov_full \
    --cov-report=xml:reports/coverage_full.xml \
    --cov-report=json:reports/coverage_full.json \
    --cov-config=.coveragerc \
    -v \
    --tb=short

# Проверка порога покрытия
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Coverage Summary${NC}"
echo -e "${BLUE}========================================${NC}"

# Извлечение процента покрытия из JSON отчёта
if [ -f "reports/coverage_full.json" ]; then
    COVERAGE_PERCENT=$(python -c "import json; data=json.load(open('reports/coverage_full.json')); print(data['totals']['percent_covered_display'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}Total coverage: ${COVERAGE_PERCENT}%${NC}"

    # Проверка порога
    THRESHOLD=70
    if (( $(echo "$COVERAGE_PERCENT < $THRESHOLD" | bc -l) )); then
        echo -e "${RED}❌ Coverage ${COVERAGE_PERCENT}% is below threshold ${THRESHOLD}%${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Coverage meets threshold (${THRESHOLD}%)${NC}"
    fi
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All tests completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Открыть HTML отчёт
if [ -f "reports/htmlcov_full/index.html" ]; then
    echo -e "${YELLOW}HTML report generated at: reports/htmlcov_full/index.html${NC}"

    # Попытка открыть в браузере
    if command -v xdg-open &> /dev/null; then
        xdg-open reports/htmlcov_full/index.html 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open reports/htmlcov_full/index.html 2>/dev/null || true
    fi
fi