.PHONY: bootstrap format lint test template clean

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

clean:
	mkdir -p build
	find build -mindepth 1 -maxdepth 1 ! -name .gitkeep -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist
