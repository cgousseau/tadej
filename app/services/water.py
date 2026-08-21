import os
import logging
from time import perf_counter
from typing import Any

import requests


logger = logging.getLogger(__name__)


def query_overpass_water(points: list[dict[str, float]], radius_m: int) -> list[dict[str, Any]]:
    clauses = [
        f'node["amenity"="drinking_water"](around:{radius_m},{point["lat"]},{point["lon"]});'
        for point in points
    ]
    query = "[out:json][timeout:25];(" + "".join(clauses) + ");out body;"
    overpass_url = os.getenv(
        "OVERPASS_URL", "https://overpass.kumi.systems/api/interpreter"
    )
    started_at = perf_counter()
    logger.info("Overpass request started: points=%d radius_m=%d url=%s", len(points), radius_m, overpass_url)
    response = requests.post(
        overpass_url,
        data={"data": query},
        headers={"User-Agent": "TadejAPI/0.1"},
        timeout=30,
    )
    logger.info("Overpass response: status=%d duration_seconds=%.2f", response.status_code, perf_counter() - started_at)
    response.raise_for_status()

    water_points = []
    for element in response.json().get("elements", []):
        tags = element.get("tags", {})
        water_points.append(
            {
                "osm_id": element["id"],
                "lat": element["lat"],
                "lon": element["lon"],
                "name": tags.get("name"),
                "drinking_water": tags.get("drinking_water"),
                "fee": tags.get("fee"),
                "access": tags.get("access"),
            }
        )
    unique_water_points = list({point["osm_id"]: point for point in water_points}.values())
    logger.info("Overpass response parsed: elements=%d unique_water_points=%d", len(water_points), len(unique_water_points))
    return unique_water_points