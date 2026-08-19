FROM python:3.12.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

WORKDIR /app
COPY ./proto/gen/python ./proto/gen/python
COPY ./physics/pyproject.toml ./physics/uv.lock ./physics/

WORKDIR /app/physics
RUN uv sync --locked

WORKDIR /app
COPY ./physics ./physics
COPY ./models ./models

WORKDIR /app/physics

ENV ROBOREMOTE_MODEL_PATH=/app/models/so101/so101_new_calib.urdf
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=2s --timeout=3s --start-period=10s --retries=3 \
    CMD ["uv", "run", "python", "healthcheck.py"]

CMD ["uv", "run", "python", "main.py"]