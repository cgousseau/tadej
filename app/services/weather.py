from typing import Any
import logging
from time import perf_counter

import requests


logger = logging.getLogger(__name__)


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    started_at = perf_counter()
    logger.info("Weather request started: lat=%s lon=%s", lat, lon)
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
    logger.info("Weather response: status=%d duration_seconds=%.2f", response.status_code, perf_counter() - started_at)
    response.raise_for_status()
    hourly = response.json()["hourly"]
    return {key: values[0] for key, values in hourly.items()}