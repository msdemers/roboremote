.PHONY: up down build proto test

up:
	docker compose up --build

down:
	docker compose down

build:
	cd server && go build ./...
	cd tui && go build ./...

proto:
	@echo "TODO: buf generate proto/"

test:
	cd server && go test ./...
	cd tui && go test ./...
