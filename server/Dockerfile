FROM golang:1.26.4-bookworm AS builder
WORKDIR /app
COPY --parents ./go.work ./go.work.sum ./proto/gen/go ./server ./tui/go.mod ./tui/go.sum /app/
WORKDIR /app/server
RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/roboserver

FROM scratch
COPY --from=builder /app/server/roboserver /roboserver
ENTRYPOINT ["/roboserver"]
