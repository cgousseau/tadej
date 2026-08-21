from typing import Any

import requests


def query_overpass_water(points: list[dict[str, float]], radius_m: int) -> list[dict[str, Any]]:
    clauses = [
        f'node["amenity"="drinking_water"](around:{radius_m},{point["lat"]},{point["lon"]});'
        for point in points
    ]
    query = "[out:json][timeout:60];(" + "".join(clauses) + ");out body;"
    response = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers={"User-Agent": "TadejAPI/0.1"},
        timeout=120,
    )
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
    return list({point["osm_id"]: point for point in water_points}.values())