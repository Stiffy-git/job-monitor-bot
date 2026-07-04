#!/bin/bash
# Bot runner - restarts if crashed
cd "$(dirname "$0")"

while true; do
    echo "$(date) Starting bot..."
    python3 main.py
    echo "$(date) Bot exited, restarting in 10s..."
    sleep 10
done
