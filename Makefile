.PHONY: up down build proto test

up:
	docker compose up --build

down:
	docker compose down

build:
	cd server && go build ./...
	cd tui && go build ./...

proto:
	buf lint proto/
	buf generate
	cd physics && uv run python -m grpc_tools.protoc \
		-I../proto \
		--python_out=../proto/gen/python \
		--grpc_python_out=../proto/gen/python \
		../proto/roboremote/arm/v1/arm.proto

test:
	cd server && go test ./...
	cd tui && go test ./...
