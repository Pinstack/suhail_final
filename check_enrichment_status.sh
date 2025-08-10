#!/bin/bash
# Quick enrichment status checker

source .venv/bin/activate

echo "🔍 ENRICHMENT STATUS CHECK"
echo "=========================="

# Check if process is running
if [ -f "logs/enrichment-full.pid" ]; then
    PID=$(cat logs/enrichment-full.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🟢 Process Status: RUNNING (PID: $PID)"
    else
        echo "🔴 Process Status: STOPPED"
    fi
else
    echo "❓ Process Status: NO PID FILE"
fi

# Check database status
python - <<EOF
from sqlalchemy import create_engine
from src.meshic_pipeline.config import settings
import time

engine = create_engine(str(settings.database_url))
with engine.connect() as conn:
    from sqlalchemy import text
    result = conn.execute(text('''
        SELECT 
            COUNT(*) as total,
            COUNT(enriched_at) as enriched,
            COUNT(*) - COUNT(enriched_at) as remaining
        FROM parcels
    ''')).fetchone()
    
    total, enriched, remaining = result
    progress = (enriched / total) * 100
    
    print(f"📊 Database Status:")
    print(f"   Total parcels: {total:,}")
    print(f"   Enriched: {enriched:,}")
    print(f"   Remaining: {remaining:,}")
    print(f"   Progress: {progress:.2f}%")
    
    if remaining == 0:
        print("🎉 ENRICHMENT COMPLETE!")
    else:
        print(f"⏳ Still processing...")
        
    print(f"🕐 Checked at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
EOF

# Check for completion flag
if [ -f "logs/enrichment_complete.txt" ]; then
    echo ""
    echo "🏁 COMPLETION DETECTED:"
    cat logs/enrichment_complete.txt
fi

echo "=========================="
