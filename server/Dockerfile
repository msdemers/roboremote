FROM golang:1.26.4-bookworm AS builder
WORKDIR /app
COPY . .
WORKDIR /app/server
RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/roboserver

FROM scratch
COPY --from=builder /app/server/roboserver /roboserver
ENTRYPOINT ["/roboserver"]
