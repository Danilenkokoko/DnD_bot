# Makefile
# Утилиты для тестирования и coverage

.PHONY: help test test-unit test-integration test-all coverage coverage-html clean

help:
	@echo "Доступные команды:"
	@echo "  make test           - Запустить все быстрые тесты"
	@echo "  make test-unit      - Запустить unit-тесты"
	@echo "  make test-integration - Запустить интеграционные тесты"
	@echo "  make test-all       - Запустить все тесты (включая медленные)"
	@echo "  make coverage       - Запустить тесты с coverage (консоль)"
	@echo "  make coverage-html  - Запустить тесты с HTML отчётом"
	@echo "  make clean          - Очистить временные файлы"

test:
	pytest tests/ -v -m "not slow" --tb=short

test-unit:
	pytest tests/engine/ tests/services/ -v -m "unit" --tb=short

test-integration:
	pytest tests/integration/ -v -m "integration" --tb=short

test-all:
	pytest tests/ -v --tb=short

coverage:
	pytest tests/ \
		--cov=engine \
		--cov=services \
		--cov=handlers \
		--cov-report=term-missing \
		--cov-config=.coveragerc \
		-v -m "not slow"

coverage-html:
	pytest tests/ \
		--cov=engine \
		--cov=services \
		--cov=handlers \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--cov-config=.coveragerc \
		-v
	@echo "HTML отчёт создан в директории htmlcov/"
	@echo "Откройте htmlcov/index.html в браузере"

clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete