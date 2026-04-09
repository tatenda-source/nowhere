.PHONY: build deploy logs restart status stop clean

build:
	cd app && npm run build:web

deploy: build
	docker compose up -d --build

logs:
	docker compose logs -f

restart:
	docker compose restart

status:
	docker compose ps
	@echo ""
	@curl -sf http://localhost:8000/health || echo "API not reachable"

stop:
	docker compose down

clean:
	docker compose down --volumes --remove-orphans
