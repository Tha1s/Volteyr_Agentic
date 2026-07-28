.PHONY: all venv setup api streamlit dev test clean fclean

VENV := .venv

all: venv setup
	@echo "Tout prêt ! Lance 'make dev' pour démarrer."

venv:
	python3 -m venv $(VENV)

setup: venv
	$(VENV)/bin/pip install -r requirements.txt

api:
	$(VENV)/bin/uvicorn src.api.main:app --reload --port 8000

streamlit:
	$(VENV)/bin/streamlit run src/ui/app.py --server.port 8501

dev:
	@$(VENV)/bin/uvicorn src.api.main:app --port 8000 & \
	PID=$$!; trap 'kill $$PID 2>/dev/null' EXIT; \
	$(VENV)/bin/streamlit run src/ui/app.py --server.port 8501

test:
	$(VENV)/bin/python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf $(VENV)/lib/python*/site-packages/*.pyc 2>/dev/null; true

fclean: clean
	rm -rf $(VENV)
