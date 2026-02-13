.PHONY: up down db api web

up:
	docker compose up -d

down:
	docker compose down

db:
	docker compose up -d db

api:
	cd apps/api && python main.py

web:
	cd apps/web && pnpm dev
