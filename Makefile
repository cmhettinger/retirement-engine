.PHONY: bootstrap format lint test template validate-workbook summarize-workbook clean

CONFIG ?= env/config.yml
VALIDATION_OUTPUT ?= build/workbook-validation.json
SUMMARY_FORMAT ?= text
SUMMARY_OUTPUT ?=
WORKBOOK ?=

bootstrap:
	poetry install

format:
	poetry run ruff format src tests tools

lint:
	poetry run ruff check src tests tools

test:
	poetry run pytest || test $$? -eq 5

template:
	poetry run python tools/generate_template.py

validate-workbook:
	poetry run python -m retirement_engine --config $(CONFIG) validate --format json --output $(VALIDATION_OUTPUT) $(WORKBOOK)

summarize-workbook:
	poetry run python -m retirement_engine --config $(CONFIG) summary --format $(SUMMARY_FORMAT) $(if $(SUMMARY_OUTPUT),--output $(SUMMARY_OUTPUT)) $(WORKBOOK)

clean:
	mkdir -p build
	find build -mindepth 1 -maxdepth 1 ! -name .gitkeep -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist
