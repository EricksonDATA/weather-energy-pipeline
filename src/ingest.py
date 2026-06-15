import requests
import pandas as pd


def fetch_weather(latitude=14.5995, longitude=120.9842, past_days=7):
    """
    Fetch hourly weather data from Open-Meteo API.
    Default location: Manila, Philippines (closest major city).
    No API key required.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        past_days: How many past days of data to pull (max 92)

    Returns:
        pandas DataFrame with hourly weather data
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
        ],
        "past_days": past_days,
        "timezone": "Asia/Manila",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()  # Throws error if request fails

    data = response.json()

    # Build DataFrame from API response
    df = pd.DataFrame(
        {
            "timestamp": data["hourly"]["time"],
            "temperature_c": data["hourly"]["temperature_2m"],
            "humidity_pct": data["hourly"]["relative_humidity_2m"],
            "wind_speed_kmh": data["hourly"]["wind_speed_10m"],
            "precipitation_mm": data["hourly"]["precipitation"],
        }
    )

    # Convert timestamp string to datetime object
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print(f"Fetched {len(df)} rows from Open-Meteo API.")
    return df


if __name__ == "__main__":
    df = fetch_weather()
    print(df.head(10))
    print(f"\nShape: {df.shape}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
