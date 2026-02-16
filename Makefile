# .PHONY tells Make that these are commands, not files
.PHONY: help up down logs build test lint format clean

# Default command when you just run 'make'
help:
	@echo "Available commands:"
	@echo " make up 	 - Start the containers (detached mode)"
	@echo " make down 	 - Stop and remove the containers"
	@echo " make logs 	 - View logs from all containers"
	@echo " make build   - Rebuild the Docker images"
	@echo " make test    - Run tests inside the container"
	@echo " make lint    - Run ruff to check code style"
	@echo " make format  - Run ruff to format code"
	@echo " make clean   - Remove python cache files"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

build:
	docker-compose up -d --build

# Run tests inside 'web' container so they have access to the database
test:
	docker-compose exec web pytest

lint:
	docker-compose exec web ruff check .

format:
	docker-compose exec web ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete