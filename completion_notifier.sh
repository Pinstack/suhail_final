#!/bin/bash
# Simple completion notifier - checks every 30 minutes and announces when done

echo "🔔 ENRICHMENT COMPLETION NOTIFIER STARTED"
echo "⏰ Will check every 30 minutes until completion"
echo "📁 Results will be logged to logs/completion_notification.log"
echo ""

LOG_FILE="logs/completion_notification.log"
touch "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Run status check and capture output
    STATUS_OUTPUT=$(./check_enrichment_status.sh 2>&1)
    
    # Log the check
    echo "[$TIMESTAMP] Checking enrichment status..." >> "$LOG_FILE"
    
    # Check if completed (look for "ENRICHMENT COMPLETE" in output)
    if echo "$STATUS_OUTPUT" | grep -q "ENRICHMENT COMPLETE"; then
        echo "[$TIMESTAMP] 🎉 ENRICHMENT COMPLETED!" >> "$LOG_FILE"
        echo "📧 Final status:" >> "$LOG_FILE"
        echo "$STATUS_OUTPUT" >> "$LOG_FILE"
        
        # Display completion message
        echo ""
        echo "🎉🎉🎉 ENRICHMENT PIPELINE COMPLETED! 🎉🎉🎉"
        echo "📅 Completion detected at: $TIMESTAMP"
        echo "📊 All 2.3M parcels have been enriched!"
        echo "📁 Check logs/completion_notification.log for details"
        echo "🚀 Database is ready for analysis and export!"
        echo ""
        
        break
    else
        # Just log progress quietly
        PROGRESS=$(echo "$STATUS_OUTPUT" | grep "Progress:" | tail -1)
        echo "[$TIMESTAMP] $PROGRESS" >> "$LOG_FILE"
    fi
    
    # Wait 30 minutes before next check
    sleep 1800
done

echo "🏁 Completion notifier finished"
