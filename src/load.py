import duckdb
import pandas as pd
from pathlib import Path


# Resolve DB path relative to this file's location
# This ensures it always points to project_root/data/ regardless of where you run the script
DB_PATH = Path(__file__).parent.parent / "data" / "weather_energy.duckdb"


def get_connection():
    """Return a DuckDB connection to the project database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # Create data/ folder if missing
    return duckdb.connect(str(DB_PATH))


def create_tables():
    """Create tables if they don't exist yet."""
    con = get_connection()

    con.execute("""
        CREATE TABLE IF NOT EXISTS hourly_weather (
            timestamp            TIMESTAMP,
            temperature_c        FLOAT,
            humidity_pct         FLOAT,
            wind_speed_kmh       FLOAT,
            precipitation_mm     FLOAT,
            date                 DATE,
            hour                 INTEGER,
            day_of_week          VARCHAR,
            is_weekend           BOOLEAN,
            energy_demand_mw     FLOAT
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date                   DATE,
            avg_temp_c             FLOAT,
            max_temp_c             FLOAT,
            min_temp_c             FLOAT,
            avg_humidity           FLOAT,
            total_precipitation_mm FLOAT,
            avg_wind_speed_kmh     FLOAT,
            avg_energy_demand_mw   FLOAT,
            peak_energy_demand_mw  FLOAT,
            total_energy_demand_mw FLOAT
        )
    """)

    con.close()
    print("Tables ready.")


def load_hourly(df: pd.DataFrame):
    """
    Load hourly data incrementally.
    Only inserts rows newer than the latest timestamp already in the DB.
    """
    con = get_connection()

    result = con.execute("SELECT MAX(timestamp) as max_ts FROM hourly_weather").df()

    max_ts = result["max_ts"].iloc[0]

    if pd.notna(max_ts):
        # Only load rows we haven't seen yet
        new_rows = df[df["timestamp"] > pd.to_datetime(max_ts)]
    else:
        # First run — load everything
        new_rows = df

    if new_rows.empty:
        print("No new hourly rows to load.")
    else:
        con.execute("INSERT INTO hourly_weather SELECT * FROM new_rows")
        print(f"Loaded {len(new_rows)} new hourly rows.")

    con.close()


def load_daily(df: pd.DataFrame):
    """
    Load daily summary.
    Replaces existing rows for the same dates (upsert behavior).
    """
    con = get_connection()

    # Build a quoted list of dates to delete before reinserting
    dates_str = ", ".join(f"'{str(d)}'" for d in df["date"].tolist())
    con.execute(f"DELETE FROM daily_summary WHERE date IN ({dates_str})")

    # Insert fresh rows
    con.execute("INSERT INTO daily_summary SELECT * FROM df")
    print(f"Loaded {len(df)} daily summary rows.")

    con.close()


def query(sql: str) -> pd.DataFrame:
    """
    Run any SQL query against the database and return a DataFrame.
    Used by app.py for the dashboard.
    """
    con = get_connection()
    result = con.execute(sql).df()
    con.close()
    return result


if __name__ == "__main__":
    create_tables()
    print(f"\nDatabase initialized at:\n{DB_PATH}")
    print("\nTables created: hourly_weather, daily_summary")
