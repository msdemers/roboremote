FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/roboserver

FROM scratch
COPY --from=builder /app/roboserver /roboserver
ENTRYPOINT ["/roboserver"]
