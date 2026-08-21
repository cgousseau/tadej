from typing import Any

import requests


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation,precipitation_probability,wind_speed_10m,wind_direction_10m,weather_code",
            "timezone": "auto",
            "forecast_days": 2,
        },
        timeout=20,
    )
    response.raise_for_status()
    hourly = response.json()["hourly"]
    return {key: values[0] for key, values in hourly.items()}