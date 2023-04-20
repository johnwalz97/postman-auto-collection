.PHONY: all test format lint

format:
	poetry run isort postman_auto_collection tests
	poetry run black postman_auto_collection tests

lint:
	poetry run ruff postman_auto_collection tests

test:
	poetry run pytest --cov=postman_auto_collection --cov-report=term-missing tests
