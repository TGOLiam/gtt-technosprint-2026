.PHONY: install dev test build clean

FRONTEND_DIR=web_app/frontend
BACKEND_DIR=web_app/backend

install:
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && pip install -r requirements.txt

dev:
	trap 'kill 0' EXIT; \
		cd $(BACKEND_DIR) && uvicorn app.main:app --reload --port 8000 & \
		cd $(FRONTEND_DIR) && npm run dev

test:
	cd $(BACKEND_DIR) && pytest -xvs

build:
	cd $(FRONTEND_DIR) && npm run build

clean:
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/.next
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
