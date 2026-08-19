FROM python:3.12.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

WORKDIR /app
COPY ./proto/gen/python ./proto/gen/python
COPY ./viz/pyproject.toml ./viz/uv.lock ./viz/

WORKDIR /app/viz
RUN uv sync --locked

WORKDIR /app
COPY ./viz ./viz
COPY ./models ./models

WORKDIR /app/viz

ENV ROBOREMOTE_MODEL_PATH=/app/models/so101/so101_new_calib.urdf
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uv", "run", "python", "main.py"]