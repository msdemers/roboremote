FROM golang:1.26.4-bookworm AS builder
WORKDIR /app
COPY . .
WORKDIR /app/tui
RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/robotui

FROM debian:bookworm-slim
COPY --from=builder /app/tui/robotui /robotui
ENTRYPOINT ["/robotui"]
