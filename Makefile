.PHONY: install dev test build clean

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

dev:
	trap 'kill 0' EXIT; \
		cd backend && uvicorn app.main:app --reload --port 8000 & \
		cd frontend && npm run dev

test:
	cd backend && pytest -xvs
	cd frontend && npm test

build:
	cd frontend && npm run build

clean:
	rm -rf frontend/node_modules frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
