#!/usr/bin/env python3
"""
Generate Riyadh Recent Transactions Report

This script queries the database for all parcels that have transactions in the last 6 months
and generates a comprehensive report with transaction details, parcel information, and analytics.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import json

# Add the src directory to the Python path
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from meshic_pipeline.config import Settings
from meshic_pipeline.persistence.models import Parcel, Transaction, Neighborhood, Province


def get_database_connection():
    """Create database connection using project settings."""
    settings = Settings()
    engine = create_engine(str(settings.database_url))
    return engine


def query_recent_transactions(engine, months_back=6):
    """
    Query parcels with transactions in the last N months.
    
    Args:
        engine: SQLAlchemy engine
        months_back: Number of months to look back (default: 6)
    
    Returns:
        DataFrame with transaction and parcel data
    """
    # Calculate the cutoff date
    cutoff_date = datetime.now() - timedelta(days=months_back * 30)
    
    query = text("""
        SELECT 
            p.parcel_objectid,
            p.parcel_no,
            p.parcel_id,
            p.subdivision_no,
            p.block_no,
            p.landuseagroup,
            p.landuseadetailed,
            p.shape_area,
            p.transaction_price as parcel_transaction_price,
            p.price_of_meter as parcel_price_per_meter,
            p.zoning_id,
            p.zoning_color,
            p.ruleid,
            p.neighborhood_ar,
            p.municipality_ar,
            p.created_at as parcel_created_at,
            p.enriched_at as parcel_enriched_at,
            
            t.transaction_id,
            t.transaction_price,
            t.price_of_meter,
            t.transaction_date,
            t.area as transaction_area,
            t.raw_data as transaction_raw_data,
            
            n.neighborhood_name,
            n.neighborhood_ar as neighborhood_ar_full,
            n.price_of_meter as neighborhood_price_per_meter,
            n.transaction_price as neighborhood_transaction_price,
            
            pr.province_name,
            
            -- Calculate days since transaction
            EXTRACT(DAYS FROM (NOW() - t.transaction_date)) as days_since_transaction,
            
            -- Calculate price difference from neighborhood average
            (t.price_of_meter - n.price_of_meter) as price_diff_from_neighborhood,
            
            -- Calculate percentage difference
            CASE 
                WHEN n.price_of_meter > 0 
                THEN ((t.price_of_meter - n.price_of_meter) / n.price_of_meter) * 100
                ELSE NULL 
            END as price_percentage_diff
            
        FROM parcels p
        INNER JOIN transactions t ON p.parcel_objectid = t.parcel_objectid
        LEFT JOIN neighborhoods n ON p.neighborhood_id = n.neighborhood_id
        LEFT JOIN provinces pr ON p.province_id = pr.province_id
        
        WHERE t.transaction_date >= :cutoff_date
        AND t.transaction_date IS NOT NULL
        
        ORDER BY t.transaction_date DESC, t.transaction_price DESC
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={'cutoff_date': cutoff_date})
    
    return df


def generate_summary_statistics(df):
    """Generate summary statistics for the report."""
    if df.empty:
        return {}
    
    stats = {
        'total_transactions': len(df),
        'unique_parcels': df['parcel_objectid'].nunique(),
        'date_range': {
            'earliest_transaction': df['transaction_date'].min().strftime('%Y-%m-%d'),
            'latest_transaction': df['transaction_date'].max().strftime('%Y-%m-%d'),
            'days_span': (df['transaction_date'].max() - df['transaction_date'].min()).days
        },
        'price_statistics': {
            'total_transaction_value': df['transaction_price'].sum(),
            'average_transaction_price': df['transaction_price'].mean(),
            'median_transaction_price': df['transaction_price'].median(),
            'min_transaction_price': df['transaction_price'].min(),
            'max_transaction_price': df['transaction_price'].max(),
            'average_price_per_meter': df['price_of_meter'].mean(),
            'median_price_per_meter': df['price_of_meter'].median()
        },
        'area_statistics': {
            'total_area_transacted': df['transaction_area'].sum(),
            'average_area': df['transaction_area'].mean(),
            'median_area': df['transaction_area'].median()
        },
        'land_use_distribution': df['landuseagroup'].value_counts().to_dict(),
        'neighborhood_distribution': df['neighborhood_ar'].value_counts().head(10).to_dict(),
        'recent_activity': {
            'transactions_last_30_days': len(df[df['days_since_transaction'] <= 30]),
            'transactions_last_7_days': len(df[df['days_since_transaction'] <= 7]),
            'transactions_today': len(df[df['days_since_transaction'] == 0])
        }
    }
    
    return stats


def generate_markdown_report(df, stats, output_path):
    """Generate a comprehensive markdown report."""
    
    report_content = f"""# Riyadh Recent Transactions Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Report Period:** Last 6 months  
**Data Source:** Meshic Pipeline Database

## Executive Summary

This report analyzes all real estate transactions in Riyadh over the past 6 months, providing insights into market activity, pricing trends, and geographic distribution.

### Key Metrics

- **Total Transactions:** {stats['total_transactions']:,}
- **Unique Parcels:** {stats['unique_parcels']:,}
- **Total Transaction Value:** SAR {stats['price_statistics']['total_transaction_value']:,.2f}
- **Average Transaction Price:** SAR {stats['price_statistics']['average_transaction_price']:,.2f}
- **Average Price per Square Meter:** SAR {stats['price_statistics']['average_price_per_meter']:,.2f}

### Time Period Analysis

- **Date Range:** {stats['date_range']['earliest_transaction']} to {stats['date_range']['latest_transaction']}
- **Span:** {stats['date_range']['days_span']} days
- **Recent Activity (Last 30 days):** {stats['recent_activity']['transactions_last_30_days']} transactions
- **Recent Activity (Last 7 days):** {stats['recent_activity']['transactions_last_7_days']} transactions

## Price Analysis

### Transaction Price Distribution

- **Minimum:** SAR {stats['price_statistics']['min_transaction_price']:,.2f}
- **Median:** SAR {stats['price_statistics']['median_transaction_price']:,.2f}
- **Average:** SAR {stats['price_statistics']['average_transaction_price']:,.2f}
- **Maximum:** SAR {stats['price_statistics']['max_transaction_price']:,.2f}

### Price per Square Meter

- **Median:** SAR {stats['price_statistics']['median_price_per_meter']:,.2f}
- **Average:** SAR {stats['price_statistics']['average_price_per_meter']:,.2f}

## Geographic Distribution

### Top Neighborhoods by Transaction Volume

"""
    
    # Add neighborhood distribution
    for neighborhood, count in list(stats['neighborhood_distribution'].items())[:10]:
        report_content += f"- **{neighborhood}:** {count} transactions\n"
    
    report_content += """
### Land Use Distribution

"""
    
    # Add land use distribution
    for land_use, count in stats['land_use_distribution'].items():
        percentage = (count / stats['total_transactions']) * 100
        report_content += f"- **{land_use}:** {count} transactions ({percentage:.1f}%)\n"
    
    report_content += f"""
## Area Analysis

- **Total Area Transacted:** {stats['area_statistics']['total_area_transacted']:,.2f} sq meters
- **Average Parcel Area:** {stats['area_statistics']['average_area']:,.2f} sq meters
- **Median Parcel Area:** {stats['area_statistics']['median_area']:,.2f} sq meters

## Recent Transactions (Last 30 Days)

"""
    
    # Get recent transactions
    recent_df = df[df['days_since_transaction'] <= 30].head(20)
    if not recent_df.empty:
        report_content += "| Date | Parcel ID | Neighborhood | Price (SAR) | Price/m² | Area (m²) |\n"
        report_content += "|------|-----------|--------------|-------------|----------|-----------|\n"
        
        for _, row in recent_df.iterrows():
            date_str = row['transaction_date'].strftime('%Y-%m-%d')
            report_content += f"| {date_str} | {row['parcel_no'] or 'N/A'} | {row['neighborhood_ar'] or 'N/A'} | {row['transaction_price']:,.0f} | {row['price_of_meter']:,.0f} | {row['transaction_area']:,.0f} |\n"
    else:
        report_content += "No transactions in the last 30 days.\n"
    
    report_content += f"""
## High-Value Transactions (Top 10)

"""
    
    # Get top 10 transactions by price
    top_transactions = df.nlargest(10, 'transaction_price')
    if not top_transactions.empty:
        report_content += "| Rank | Parcel ID | Neighborhood | Price (SAR) | Price/m² | Date |\n"
        report_content += "|------|-----------|--------------|-------------|----------|------|\n"
        
        for i, (_, row) in enumerate(top_transactions.iterrows(), 1):
            date_str = row['transaction_date'].strftime('%Y-%m-%d')
            report_content += f"| {i} | {row['parcel_no'] or 'N/A'} | {row['neighborhood_ar'] or 'N/A'} | {row['transaction_price']:,.0f} | {row['price_of_meter']:,.0f} | {date_str} |\n"
    
    report_content += f"""
## Data Quality Notes

- **Total Records Processed:** {len(df):,}
- **Records with Missing Neighborhood Data:** {df['neighborhood_ar'].isna().sum():,}
- **Records with Missing Land Use Data:** {df['landuseagroup'].isna().sum():,}
- **Records with Missing Area Data:** {df['transaction_area'].isna().sum():,}

## Methodology

This report is generated from the Meshic Pipeline database, which captures real estate data from official sources and enriches it with additional market information. The analysis includes:

1. **Data Source:** Direct database queries from the `parcels` and `transactions` tables
2. **Time Period:** Last 6 months from the report generation date
3. **Geographic Scope:** All transactions within Riyadh province
4. **Data Enrichment:** Neighborhood and province information from related tables

## Technical Details

- **Database:** PostgreSQL with PostGIS spatial extensions
- **Query Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Report Format:** Markdown
- **Data Export:** CSV format available in companion file

---
*Report generated by Meshic Pipeline Analytics System*
"""
    
    # Write the report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Markdown report generated: {output_path}")


def generate_csv_export(df, output_path):
    """Generate CSV export of the transaction data."""
    # Select relevant columns for export
    export_columns = [
        'parcel_objectid', 'parcel_no', 'parcel_id', 'subdivision_no', 'block_no',
        'landuseagroup', 'landuseadetailed', 'shape_area', 'zoning_id', 'zoning_color',
        'neighborhood_ar', 'municipality_ar', 'transaction_id', 'transaction_price',
        'price_of_meter', 'transaction_date', 'transaction_area', 'days_since_transaction',
        'neighborhood_name', 'neighborhood_ar_full', 'province_name'
    ]
    
    # Filter to columns that exist in the dataframe
    available_columns = [col for col in export_columns if col in df.columns]
    export_df = df[available_columns].copy()
    
    # Export to CSV
    export_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"CSV export generated: {output_path}")


def main():
    """Main function to generate the Riyadh transactions report."""
    print("Generating Riyadh Recent Transactions Report...")
    
    try:
        # Create database connection
        engine = get_database_connection()
        print("✓ Database connection established")
        
        # Query recent transactions
        print("Querying recent transactions...")
        df = query_recent_transactions(engine, months_back=6)
        print(f"✓ Found {len(df):,} transactions in the last 6 months")
        
        if df.empty:
            print("No transactions found in the specified time period.")
            return
        
        # Generate statistics
        print("Generating summary statistics...")
        stats = generate_summary_statistics(df)
        print("✓ Statistics calculated")
        
        # Create output directory
        reports_dir = Path("Reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"Riyadh_recent_transactions_{timestamp}"
        
        # Generate markdown report
        md_path = reports_dir / f"{report_name}.md"
        generate_markdown_report(df, stats, md_path)
        
        # Generate CSV export
        csv_path = reports_dir / f"{report_name}.csv"
        generate_csv_export(df, csv_path)
        
        # Generate JSON summary
        json_path = reports_dir / f"{report_name}_summary.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"JSON summary generated: {json_path}")
        
        print(f"\n🎉 Report generation complete!")
        print(f"📊 Markdown Report: {md_path}")
        print(f"📋 CSV Export: {csv_path}")
        print(f"📈 JSON Summary: {json_path}")
        
        # Print key metrics
        print(f"\n📈 Key Metrics:")
        print(f"   • Total Transactions: {stats['total_transactions']:,}")
        print(f"   • Unique Parcels: {stats['unique_parcels']:,}")
        print(f"   • Total Value: SAR {stats['price_statistics']['total_transaction_value']:,.2f}")
        print(f"   • Average Price: SAR {stats['price_statistics']['average_transaction_price']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 