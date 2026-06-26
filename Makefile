.PHONY: install dev dev-backend dev-frontend test build clean

FRONTEND_DIR=web_app/frontend
BACKEND_DIR=web_app/backend

install:
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && pip install -r requirements.txt

dev-backend:
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

dev:
ifeq ($(OS),Windows_NT)
	start /b cmd /c "cd $(BACKEND_DIR) && uvicorn app.main:app --reload --port 8000"
	start /b cmd /c "cd $(FRONTEND_DIR) && npm run dev"
else
	trap 'kill 0' EXIT; \
		$(MAKE) dev-backend & \
		$(MAKE) dev-frontend
endif

test:
	cd $(BACKEND_DIR) && python -m pytest -xvs

build:
	cd $(FRONTEND_DIR) && npm run build

clean:
ifeq ($(OS),Windows_NT)
	@if exist "$(FRONTEND_DIR)\node_modules" rmdir /s /q "$(FRONTEND_DIR)\node_modules"
	@if exist "$(FRONTEND_DIR)\.next" rmdir /s /q "$(FRONTEND_DIR)\.next"
	@for /d /r "$(BACKEND_DIR)" %i in (__pycache__) do @if exist "%i" rmdir /s /q "%i" 2>nul
else
	$(RM) -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/.next
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
endif
