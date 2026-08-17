PYTHON     ?= python3
LOGS_DIR   ?= ./logs
IMAGE      := jenkins-triage:latest

.PHONY: help run json test slack docker-build docker-run

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available targets:"
	@echo "  make run           Run triage.py against $(LOGS_DIR) (Markdown output)"
	@echo "  make json          Run triage.py against $(LOGS_DIR) (JSON output)"

run: ## Run triage.py with default Markdown output
	$(PYTHON) triage.py $(LOGS_DIR)

json: ## Run triage.py with JSON output
	$(PYTHON) triage.py $(LOGS_DIR) -f json