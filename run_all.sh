#!/bin/bash
# Start broker (docker-compose)
set -e
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Mosquitto broker via docker-compose..."
cd "$BASE_DIR"
docker-compose up -d

# Run subscriber in background
python3 subscriber/subscriber.py --outdir reports &
SUB_PID=$!

echo "Subscriber started (pid $SUB_PID). Publishing sample data..."
# Publish each CSV
python3 publishers/publish.py --file data/Shasta_WML_sample.csv --reservoir SHASTA
python3 publishers/publish.py --file data/Oroville_WML_sample.csv --reservoir OROVILLE
python3 publishers/publish.py --file data/Sonoma_WML_sample.csv --reservoir SONOMA

# Allow messages to be processed
sleep 1

# Stop subscriber
kill $SUB_PID || true

echo "Done. Reports are in ./reports"
