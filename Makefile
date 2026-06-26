SHELL := cmd.exe
.SHELLFLAGS := /C

.PHONY: install dev test build clean

FRONTEND_DIR=web_app\frontend
BACKEND_DIR=web_app\backend

install:
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && pip install -r requirements.txt

dev:
	start "Backend" cmd /K "cd $(BACKEND_DIR) && python -m uvicorn app.main:app --reload --port 8000"
	timeout /t 2 >nul
	start "" http://localhost:3000
	cd $(FRONTEND_DIR) && npm run dev

test:
	cd $(BACKEND_DIR) && python -m pytest -xvs

build:
	cd $(FRONTEND_DIR) && npm run build

clean:
	if exist "$(FRONTEND_DIR)\node_modules" rmdir /s /q "$(FRONTEND_DIR)\node_modules"
	if exist "$(FRONTEND_DIR)\.next" rmdir /s /q "$(FRONTEND_DIR)\.next"
	powershell -NoProfile -Command "Get-ChildItem -Path '$(BACKEND_DIR)' -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"