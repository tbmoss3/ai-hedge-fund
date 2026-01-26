#!/bin/bash
# Quarterly scan trigger - called by Railway cron service
# Hits the backend API to trigger a full watchlist scan

BACKEND_URL="${BACKEND_URL:-https://backend-production-5221.up.railway.app}"

echo "$(date): Triggering quarterly watchlist scan..."
echo "Backend: $BACKEND_URL"

response=$(curl -s -X POST "$BACKEND_URL/api/watchlist/scan" \
  -H "Content-Type: application/json" \
  --max-time 1800)

echo "Response: $response"

# Check if successful
if echo "$response" | grep -q '"status"'; then
  echo "$(date): Scan triggered successfully"
  exit 0
else
  echo "$(date): Scan trigger failed"
  exit 1
fi
