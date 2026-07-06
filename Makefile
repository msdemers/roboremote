.PHONY: up down build proto test run-physics

up:
	docker compose up --build

down:
	docker compose down

build:
	cd server && go build ./...
	cd tui && go build ./...

proto:
	cd proto && buf lint
	cd proto && buf generate
	cd physics && uv run python -m grpc_tools.protoc \
		-I../proto \
		--python_out=../proto/gen/python \
		--grpc_python_out=../proto/gen/python \
		../proto/roboremote/arm/v1/arm.proto

run-physics:
	cd physics && PYTHONPATH=../proto/gen/python uv run python main.py
test:
	cd server && go test ./...
	cd tui && go test ./...
	cd physics && uv run pytest
