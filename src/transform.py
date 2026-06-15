import pandas as pd
import numpy as np


def transform_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich hourly weather data.

    Adds:
    - Time features: date, hour, day_of_week, is_weekend
    - Simulated energy demand based on temperature

    Args:
        df: Raw DataFrame from ingest.py

    Returns:
        Enriched DataFrame
    """
    df = df.copy()

    # --- Clean ---
    before = len(df)
    df = df.dropna(subset=["temperature_c"])  # Temperature is critical
    dropped = before - len(df)
    if dropped > 0:
        print(f"Dropped {dropped} rows with missing temperature.")

    # Fill minor missing values with median
    df["precipitation_mm"] = df["precipitation_mm"].fillna(0)
    df["humidity_pct"] = df["humidity_pct"].fillna(df["humidity_pct"].median())
    df["wind_speed_kmh"] = df["wind_speed_kmh"].fillna(df["wind_speed_kmh"].median())

    # --- Time features ---
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5  # 5=Sat, 6=Sun

    # --- Simulate energy demand ---
    # Logic: energy demand peaks when temp deviates from comfort zone (22°C)
    # Hot = more air conditioning. Humidity and wind also affect load.
    np.random.seed(42)  # So results are reproducible
    comfort_temp = 22.0

    df["energy_demand_mw"] = (
        500  # base load (MW)
        + (df["temperature_c"] - comfort_temp).abs() * 15  # temperature deviation
        + df["humidity_pct"] * 0.5  # humidity adds load
        - df["wind_speed_kmh"] * 0.3  # wind cools, reduces load
        + np.random.normal(0, 10, len(df))  # realistic noise
    ).round(2)

    # Clip to a realistic range
    df["energy_demand_mw"] = df["energy_demand_mw"].clip(lower=300, upper=1000)

    print(
        f"Transformed {len(df)} rows. "
        f"Energy demand range: {df['energy_demand_mw'].min():.0f}–"
        f"{df['energy_demand_mw'].max():.0f} MW"
    )
    return df


def transform_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly data into a daily summary.

    Args:
        df: Transformed hourly DataFrame from transform_weather()

    Returns:
        Daily summary DataFrame
    """
    daily = (
        df.groupby("date")
        .agg(
            avg_temp_c=("temperature_c", "mean"),
            max_temp_c=("temperature_c", "max"),
            min_temp_c=("temperature_c", "min"),
            avg_humidity=("humidity_pct", "mean"),
            total_precipitation_mm=("precipitation_mm", "sum"),
            avg_wind_speed_kmh=("wind_speed_kmh", "mean"),
            avg_energy_demand_mw=("energy_demand_mw", "mean"),
            peak_energy_demand_mw=("energy_demand_mw", "max"),
            total_energy_demand_mw=("energy_demand_mw", "sum"),
        )
        .reset_index()
    )

    # Round all numeric columns to 2 decimal places
    numeric_cols = daily.select_dtypes(include="number").columns
    daily[numeric_cols] = daily[numeric_cols].round(2)

    print(f"Daily summary: {len(daily)} days.")
    return daily


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))

    from ingest import fetch_weather

    raw = fetch_weather()
    hourly = transform_weather(raw)
    daily = transform_daily_summary(hourly)

    print("\n--- Hourly Sample ---")
    print(
        hourly[
            ["timestamp", "temperature_c", "energy_demand_mw", "hour", "is_weekend"]
        ].head(10)
    )

    print("\n--- Daily Summary ---")
    print(daily.head())
