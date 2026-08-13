ifeq (,$(wildcard .env))
$(error .env not found — run: cp .env.example .env)
endif
include .env

ROBOREMOTE_MODEL_PATH := $(CURDIR)/$(ROBOREMOTE_MODEL_PATH)

export $(filter ROBOREMOTE_%,$(.VARIABLES))

.PHONY: up down build proto proto-check test run-physics

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
	cd proto && uv run --locked --project gen/python --group codegen \
		python -m grpc_tools.protoc \
		-I. \
		--python_out=gen/python \
		--grpc_python_out=gen/python \
		--pyi_out=gen/python \
		roboremote/arm/v1/arm.proto

proto-check: proto
	@out="$$(git status --porcelain proto/gen)"; \
	if [ -n "$$out" ]; then \
		echo "DRIFTED - generated proto changed and needs commit"; \
		echo "$$out"; \
		exit 1; \
	fi

run-physics:
	cd physics && uv run python main.py

test:
	cd server && go test ./...
	cd tui && go test ./...
	cd physics && uv run pytest
