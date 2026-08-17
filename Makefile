PYTHON     ?= python3
LOGS_DIR   ?= ./logs
IMAGE      := jenkins-triage:latest

.PHONY: help run json test slack docker-build docker-run

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available targets:"
	@echo "  make run           Run triage.py against $(LOGS_DIR) (Markdown output)"
	@echo "  make json          Run triage.py against $(LOGS_DIR) (JSON output)"
	@echo "  make test          Run unit tests (test_triage.py)"
	@echo "  make slack         Run triage.py and post the summary to Slack (needs SLACK_WEBHOOK_URL)"
	@echo "  make docker-build  Build the Docker image as $(IMAGE)"
	@echo "  make docker-run    Run the Docker image against $(LOGS_DIR)"

run: ## Run triage.py with default Markdown output
	$(PYTHON) triage.py $(LOGS_DIR)

json: ## Run triage.py with JSON output
	$(PYTHON) triage.py $(LOGS_DIR) -f json

test: ## Run the unit test suite
	$(PYTHON) -m unittest test_triage.py

slack: ## Run triage.py and send a Slack alert (requires SLACK_WEBHOOK_URL)
	$(PYTHON) triage.py $(LOGS_DIR) --slack-webhook "$(SLACK_WEBHOOK_URL)"