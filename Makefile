SHELL := /bin/zsh

PYTHON := $(if $(wildcard venv/bin/python3),venv/bin/python3,python3)
RUN_DATE ?= $(shell date +%F)
WORKFLOW ?= mlo
INPUT_CSV ?= workspace/projects/mortgage-signals/test_input.csv
OUTPUT_DIR ?= workspace/projects/mortgage-signals/outputs
LIMIT ?= 5

.PHONY: test-live test-company show-results help

help:
	@echo "Targets:"
	@echo "  make test-live      # Run MLO workflow test with defaults"
	@echo "  make test-company   # Run company workflow test"
	@echo "  make show-results   # Show current run output files"
	@echo ""
	@echo "Overrides:"
	@echo "  make test-live INPUT_CSV=path/to/input.csv LIMIT=10 RUN_DATE=2026-02-26"

test-live:
	@if [ ! -f "$(INPUT_CSV)" ]; then \
		echo "Input CSV not found: $(INPUT_CSV)"; \
		echo "Set INPUT_CSV=/path/to/file.csv"; \
		exit 1; \
	fi
	@echo "Running MLO workflow"
	@echo "Python: $(PYTHON)"
	@echo "Input:  $(INPUT_CSV)"
	@echo "Date:   $(RUN_DATE)"
	$(PYTHON) -m workspace.agent.main \
		--workflow mlo \
		--input-csv "$(INPUT_CSV)" \
		--limit "$(LIMIT)" \
		--date "$(RUN_DATE)" \
		--output-dir "$(OUTPUT_DIR)"
	@$(MAKE) show-results RUN_DATE="$(RUN_DATE)" OUTPUT_DIR="$(OUTPUT_DIR)" WORKFLOW=mlo

test-company:
	@if [ ! -f "$(INPUT_CSV)" ]; then \
		echo "Input CSV not found: $(INPUT_CSV)"; \
		echo "Set INPUT_CSV=/path/to/file.csv"; \
		exit 1; \
	fi
	@echo "Running company workflow"
	$(PYTHON) -m workspace.agent.main \
		--workflow company \
		--input-csv "$(INPUT_CSV)" \
		--limit "$(LIMIT)" \
		--date "$(RUN_DATE)" \
		--output-dir "$(OUTPUT_DIR)"
	@$(MAKE) show-results RUN_DATE="$(RUN_DATE)" OUTPUT_DIR="$(OUTPUT_DIR)" WORKFLOW=company

show-results:
	@if [ "$(WORKFLOW)" = "company" ]; then \
		CSV_FILE="$(OUTPUT_DIR)/company_leads_$(RUN_DATE).csv"; \
	else \
		CSV_FILE="$(OUTPUT_DIR)/mlo_leads_$(RUN_DATE).csv"; \
	fi; \
	SUMMARY_FILE="$(OUTPUT_DIR)/daily_summary_$(RUN_DATE).md"; \
	echo "CSV:     $$CSV_FILE"; \
	echo "Summary: $$SUMMARY_FILE"; \
	ls -lh "$$CSV_FILE" "$$SUMMARY_FILE"

