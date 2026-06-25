.PHONY: install dev test build clean

FRONTEND_DIR=frontend-nextjs

install:
	cd $(FRONTEND_DIR) && npm install
	cd backend && pip install -r requirements.txt

dev:
	trap 'kill 0' EXIT; \
		cd backend && uvicorn app.main:app --reload --port 8000 & \
		cd $(FRONTEND_DIR) && npm run dev

test:
	cd backend && pytest -xvs

build:
	cd $(FRONTEND_DIR) && npm run build

clean:
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/.next
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
