.DEFAULT_GOAL := help

PY := .venv/bin/python
PIP := .venv/bin/pip
PORT ?= 8000

.PHONY: help setup venv deps run test lint fix precommit-install clean-cache

help:
	@echo "Targets disponíveis:"
	@echo "  make setup               # Cria venv (--copies) e instala dependências"
	@echo "  make run [PORT=8000]     # Sobe a API com reload (python -m uvicorn)"
	@echo "  make test                # Roda testes (pytest -q)"
	@echo "  make lint                # Ruff check + Black --check"
	@echo "  make fix                 # Ruff --fix + Black format"
	@echo "  make precommit-install   # Instala pre-commit e registra hooks"
	@echo "  make clean-cache         # Limpa caches (.pytest_cache, __pycache__, .ruff_cache)"

setup: venv deps

venv:
	@[ -d .venv ] || python3 -m venv --copies .venv
	@$(PY) -m ensurepip --upgrade >/dev/null 2>&1 || true
	@$(PY) -m pip install --upgrade pip >/dev/null 2>&1

deps: venv
	@$(PIP) install -r requirements.txt

run: deps
	@$(PY) -m uvicorn app.main:app --reload --port $(PORT)

test: deps
	@$(PY) -m pytest -q

lint: deps
	@$(PY) -m ruff check .
	@$(PY) -m black --check .

fix: deps
	@$(PY) -m ruff check . --fix
	@$(PY) -m black .

precommit-install: deps
	@$(PIP) install pre-commit
	@$(PY) -m pre_commit install

clean-cache:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf .pytest_cache .ruff_cache
