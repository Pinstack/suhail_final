#!/bin/bash
# Auto-restart enrichment if it stops unexpectedly

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

echo "🔄 Auto-restart enrichment monitor started"
echo "📝 Checking every 10 minutes for unexpected stops"

while true; do
    STATUS_OUTPUT=$(./check_enrichment_status.sh 2>&1)

    PROCESS_STATUS=$(echo "$STATUS_OUTPUT" | grep "Process Status:" | awk '{print $4}')
    REMAINING=$(echo "$STATUS_OUTPUT" | grep "Remaining:" | awk -F'Remaining: ' '{print $2}' | awk -F' ' '{print $1}' | tr -d ',')

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if [[ "$PROCESS_STATUS" == "STOPPED" ]] && [[ "$REMAINING" -gt 0 ]]; then
        echo "[$TIMESTAMP] 🚨 Process stopped with $REMAINING parcels remaining - RESTARTING!"

        nohup bash -lc "cd '$ROOT' && uv run meshic-pipeline full-refresh --batch-size 200" >> logs/enrichment-full.log 2>&1 & echo $! > logs/enrichment-full.pid

        echo "[$TIMESTAMP] 🔄 Enrichment restarted with PID $(cat logs/enrichment-full.pid)" >> logs/auto_restart.log

        bash -lc "cd '$ROOT' && uv run python logs/enrichment_watcher.py" &

        echo "[$TIMESTAMP] ✅ Auto-restart completed"

    elif [[ "$REMAINING" -eq 0 ]]; then
        echo "[$TIMESTAMP] 🎉 ENRICHMENT COMPLETED! Auto-restart monitor stopping."
        break
    else
        echo "[$TIMESTAMP] ✅ Process running normally ($REMAINING remaining)"
    fi

    sleep 600
done

echo "🏁 Auto-restart monitor finished"
