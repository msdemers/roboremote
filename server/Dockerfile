FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server ./cmd/server

FROM scratch
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
