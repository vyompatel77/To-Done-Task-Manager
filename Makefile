# Makefile for Django Project

# Python and Django requirements
PYTHON = python3
PIP = pip
DJANGO_VERSION = 4.1
PORT = 8080

# Default target
.PHONY: help
help:
	@echo "Makefile for Django Project"
	@echo ""
	@echo "Usage:"
	@echo "  make setup        Install dependencies, apply migrations, and start the server"
	@echo "  make install      Install Django and dependencies"
	@echo "  make migrate      Apply migrations"
	@echo "  make test         Test the codebase"
	@echo "  make run          Start the Django development server"
	@echo ""

# Install Django and other dependencies
.PHONY: install
install:
	$(PIP) install -r requirements.txt
	$(PIP) install django==$(DJANGO_VERSION)

# Apply database migrations
.PHONY: migrate
migrate:
	$(PYTHON) manage.py migrate

# Start the Django server
.PHONY: run
run:
	$(PYTHON) manage.py runserver $(PORT)

# Install, migrate, and run server
.PHONY: setup
setup: install migrate run

# Test the codebase
.PHONY: test
test:
	$(PYTHON) manage.py test todo.tests.test_views todo.tests.test_export todo.tests.test_import
