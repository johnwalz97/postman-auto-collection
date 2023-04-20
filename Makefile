.PHONY: all test format lint

format:
	poetry run isort postman_docs_ai scripts
	poetry run black postman_docs_ai scripts

lint:
	poetry run ruff postman_docs_ai scripts

test:
	poetry run pytest --cov=postman_docs_ai --cov-report=term-missing tests
