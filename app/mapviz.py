from typing import Iterable, List
import folium


def _center(points: List[dict]) -> tuple[float, float]:
    lat = sum(p["lat"] for p in points) / len(points)
    lon = sum(p["lon"] for p in points) / len(points)
    return lat, lon


def create_wind_map(sampled_points: Iterable[dict], route_points: Iterable[dict] | None = None, zoom_start: int = 12) -> folium.Map:
    """Create a folium map showing the full route and colored segments according to wind impact.

    `sampled_points` should be an iterable of points that include `lat`, `lon`, and `color`.
    `route_points` (optional) can be the full route (list of dicts with `lat`,`lon`) to draw a faint background polyline.
    Returns the `folium.Map` object; call `get_root().render()` to obtain HTML string.
    """
    sampled = list(sampled_points)
    if not sampled:
        raise ValueError("No sampled points provided")
    center = _center(sampled if route_points is None else list(route_points))
    m = folium.Map(location=center, zoom_start=zoom_start)

    # Draw full route in light gray if provided
    if route_points:
        route_coords = [(p["lat"], p["lon"]) for p in route_points]
        folium.PolyLine(locations=route_coords, color="#888888", weight=3, opacity=0.6).add_to(m)

    # Draw colored segments between consecutive sampled points
    for a, b in zip(sampled[:-1], sampled[1:]):
        coords = [(a["lat"], a["lon"]), (b["lat"], b["lon"])]
        # prefer color from the start point
        color = a.get("color", "#ff0000")
        weight = 6
        folium.PolyLine(locations=coords, color=color, weight=weight, opacity=0.9).add_to(m)

    # Add markers with popup summary
    for pt in sampled:
        popup = folium.Popup(
            f"bearing: {pt.get('bearing_deg'):.1f}°<br/>wind_from: {pt.get('weather',{}).get('wind_direction_10m', 'n/a')}°<br/>speed: {pt.get('weather',{}).get('wind_speed_10m', 'n/a')}<br/>impact: {pt.get('impact', 0):.2f}",
            max_width=300,
        )
        folium.CircleMarker(location=(pt["lat"], pt["lon"]), radius=4, color=pt.get("color", "#000000"), fill=True, popup=popup).add_to(m)

    return m


def map_to_html(m: folium.Map) -> str:
    return m.get_root().render()
