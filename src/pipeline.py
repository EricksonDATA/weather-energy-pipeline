import sys
import os

# Add src/ to Python's path so sibling imports work correctly
sys.path.insert(0, os.path.dirname(__file__))

from ingest import fetch_weather
from transform import transform_weather, transform_daily_summary
from load import create_tables, load_hourly, load_daily

from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


def run_pipeline():
    """Run the full ETL pipeline: Extract → Transform → Load."""
    print(f"\n{'=' * 50}")
    print(f"Pipeline started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}")

    try:
        # 1. Extract
        print("\n[1/3] Extracting from Open-Meteo API...")
        raw_df = fetch_weather(past_days=7)

        # 2. Transform
        print("\n[2/3] Transforming data...")
        hourly_df = transform_weather(raw_df)
        daily_df = transform_daily_summary(hourly_df)

        # 3. Load
        print("\n[3/3] Loading to DuckDB...")
        create_tables()
        load_hourly(hourly_df)
        load_daily(daily_df)

        print(f"\nPipeline complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        raise


def run_scheduled(interval_hours=6):
    """
    Run the pipeline on a recurring schedule.
    Runs immediately once, then every N hours.
    """
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        hours=interval_hours,
        next_run_time=datetime.now(),  # Run immediately on startup
    )

    print(f"Scheduler active. Pipeline runs every {interval_hours} hour(s).")
    print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Weather + Energy Pipeline")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a repeating schedule instead of once",
    )
    parser.add_argument(
        "--hours", type=int, default=6, help="Hours between scheduled runs (default: 6)"
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(args.hours)
    else:
        run_pipeline()
