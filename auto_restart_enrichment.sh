#!/bin/bash
# Auto-restart enrichment if it stops unexpectedly

echo "🔄 Auto-restart enrichment monitor started"
echo "📝 Checking every 10 minutes for unexpected stops"

while true; do
    # Check current status
    STATUS_OUTPUT=$(./check_enrichment_status.sh 2>&1)
    
    # Extract values using grep and awk
    PROCESS_STATUS=$(echo "$STATUS_OUTPUT" | grep "Process Status:" | awk '{print $4}')
    REMAINING=$(echo "$STATUS_OUTPUT" | grep "Remaining:" | awk -F'Remaining: ' '{print $2}' | awk -F' ' '{print $1}' | tr -d ',')
    
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check if process stopped but work remains
    if [[ "$PROCESS_STATUS" == "STOPPED" ]] && [[ "$REMAINING" -gt 0 ]]; then
        echo "[$TIMESTAMP] 🚨 Process stopped with $REMAINING parcels remaining - RESTARTING!"
        
        # Restart the enrichment
        nohup bash -lc 'source .venv/bin/activate && meshic-pipeline full-refresh --batch-size 200' >> logs/enrichment-full.log 2>&1 & echo $! > logs/enrichment-full.pid
        
        # Log the restart
        echo "[$TIMESTAMP] 🔄 Enrichment restarted with PID $(cat logs/enrichment-full.pid)" >> logs/auto_restart.log
        
        # Restart the watcher too
        bash -lc 'source .venv/bin/activate && python logs/enrichment_watcher.py' &
        
        echo "[$TIMESTAMP] ✅ Auto-restart completed"
        
    elif [[ "$REMAINING" -eq 0 ]]; then
        echo "[$TIMESTAMP] 🎉 ENRICHMENT COMPLETED! Auto-restart monitor stopping."
        break
    else
        echo "[$TIMESTAMP] ✅ Process running normally ($REMAINING remaining)"
    fi
    
    # Wait 10 minutes before next check
    sleep 600
done

echo "🏁 Auto-restart monitor finished"
