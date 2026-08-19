FROM golang:1.26.4-bookworm AS builder
WORKDIR /app
COPY --parents ./go.work ./go.work.sum ./proto/gen/go ./tui ./server/go.mod ./server/go.sum /app/
WORKDIR /app/tui
RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/robotui

FROM debian:bookworm-slim
COPY --from=builder /app/tui/robotui /robotui
ENTRYPOINT ["/robotui"]
