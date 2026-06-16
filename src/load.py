import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env file when running locally
# On GitHub Actions and Streamlit Cloud, DATABASE_URL is set as an environment variable
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")


def get_engine():
    """Return a SQLAlchemy engine connected to Supabase PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable not set. Check your .env file."
        )
    return create_engine(db_url)


def create_tables():
    """Create tables in Supabase if they don't exist yet."""
    engine = get_engine()

    with engine.connect() as con:
        con.execute(
            text("""
            CREATE TABLE IF NOT EXISTS hourly_weather (
                timestamp            TIMESTAMP PRIMARY KEY,
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
        )

        con.execute(
            text("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                date                   DATE PRIMARY KEY,
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
        )

        con.commit()

    print("Tables ready.")


def load_hourly(df: pd.DataFrame):
    """
    Load hourly data incrementally.
    Only inserts rows newer than the latest timestamp in the DB.
    """
    engine = get_engine()

    with engine.connect() as con:
        result = con.execute(
            text("SELECT MAX(timestamp) as max_ts FROM hourly_weather")
        )
        max_ts = result.fetchone()[0]

    if max_ts is not None:
        new_rows = df[df["timestamp"] > pd.to_datetime(max_ts)]
    else:
        new_rows = df

    if new_rows.empty:
        print("No new hourly rows to load.")
    else:
        new_rows.to_sql("hourly_weather", engine, if_exists="append", index=False)
        print(f"Loaded {len(new_rows)} new hourly rows.")


def load_daily(df: pd.DataFrame):
    """
    Load daily summary.
    Deletes existing rows for those dates then reinserts (upsert behavior).
    """
    engine = get_engine()

    dates_str = ", ".join(f"'{str(d)}'" for d in df["date"].tolist())

    with engine.connect() as con:
        con.execute(text(f"DELETE FROM daily_summary WHERE date IN ({dates_str})"))
        con.commit()

    df.to_sql("daily_summary", engine, if_exists="append", index=False)
    print(f"Loaded {len(df)} daily summary rows.")


def query(sql: str) -> pd.DataFrame:
    """
    Run any SQL query and return a DataFrame.
    Used by app.py for the dashboard.
    """
    engine = get_engine()
    return pd.read_sql(sql, engine)


if __name__ == "__main__":
    create_tables()
    print("Database initialized on Supabase.")
    print("Tables created: hourly_weather, daily_summary")
