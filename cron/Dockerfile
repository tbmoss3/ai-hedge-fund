# Lightweight cron service to trigger quarterly scans
FROM alpine:latest

RUN apk add --no-cache curl bash

WORKDIR /app
COPY trigger_scan.sh .
RUN chmod +x trigger_scan.sh

CMD ["./trigger_scan.sh"]
