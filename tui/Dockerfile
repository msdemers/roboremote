FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o tui ./cmd/tui

FROM debian:bookworm-slim
COPY --from=builder /app/tui /tui
ENTRYPOINT ["/tui"]
