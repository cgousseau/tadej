import math
from typing import Any

import gpxpy
from pydantic import BaseModel


class WaterPoint(BaseModel):
    osm_id: int
    lat: float
    lon: float
    name: str | None = None
    drinking_water: str | None = None
    fee: str | None = None
    access: str | None = None
    route_distance_km: float
    weather: dict[str, Any] | None = None


class RouteAnalysis(BaseModel):
    distance_km: float
    sampled_points: int
    water_points: list[WaterPoint]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    latitude_1, latitude_2 = math.radians(lat1), math.radians(lat2)
    delta_latitude = math.radians(lat2 - lat1)
    delta_longitude = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * earth_radius_km * math.asin(math.sqrt(value))


def load_route(gpx_content: bytes, max_distance_km: float | None) -> list[dict[str, float]]:
    gpx = gpxpy.parse(gpx_content.decode("utf-8"))
    points: list[dict[str, float]] = []
    distance_km = 0.0

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if points:
                    previous = points[-1]
                    distance_km += haversine_km(
                        previous["lat"], previous["lon"], point.latitude, point.longitude
                    )
                if max_distance_km is not None and distance_km > max_distance_km:
                    return points
                points.append({"lat": point.latitude, "lon": point.longitude, "distance_km": distance_km})

    if not points:
        raise ValueError("Aucun point GPS trouvé dans le GPX.")
    return points


def sample_route(route: list[dict[str, float]], every_km: float) -> list[dict[str, float]]:
    targets = range(0, math.ceil(route[-1]["distance_km"]) + 1, max(1, math.ceil(every_km)))
    sampled = []
    for target in targets:
        sampled.append(min(route, key=lambda point: abs(point["distance_km"] - target)))
    return list({id(point): point for point in sampled}.values())