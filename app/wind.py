import math
from typing import Any, Iterable, List


def _angle_diff(a: float, b: float) -> float:
    """Minimal difference between two angles in degrees (0..180)."""
    diff = abs((a - b + 180) % 360 - 180)
    return diff


def compute_impact_score(bearing_deg: float, wind_speed: float, wind_from_deg: float) -> dict[str, float]:
    """Compute wind impact on a travel segment.

    - `bearing_deg`: travel direction in degrees (0..360), where 0 is north.
    - `wind_from_deg`: meteorological wind direction (wind coming from this heading).
    - `wind_speed`: scalar speed (m/s or km/h depending on source).

    Returns a dict with:
    - `angle_between`: angle between wind (towards) and travel direction (deg, 0..180)
    - `component`: signed projection of wind along travel direction (positive => tailwind)
    - `impact`: negative of component (positive => headwind severity)
    """
    wind_towards = (wind_from_deg + 180) % 360
    angle_between = _angle_diff(wind_towards, bearing_deg)
    component = wind_speed * math.cos(math.radians(angle_between))
    impact = -component
    return {
        "angle_between": angle_between,
        "component": component,
        "impact": impact,
    }


def classify_color(impact: float, wind_speed: float) -> str:
    """Return a simple color for the segment: red for headwind, green for tailwind.

    We use the relative impact (impact / wind_speed) to choose intensity when possible.
    """
    if wind_speed <= 0 or abs(impact) == 0:
        return "#999999"
    rel = max(-1.0, min(1.0, impact / wind_speed))  # impact positive = headwind
    # headwind -> red shades, tailwind -> green shades
    if rel > 0:
        intensity = int(50 + 205 * min(1.0, rel))
        return f"#{intensity:02x}0000"
    else:
        intensity = int(50 + 205 * min(1.0, -rel))
        return f"#00{intensity:02x}00"


def compute_route_impacts(sampled_orientations: Iterable[dict[str, Any]], max_wind_speed: float | None = None) -> List[dict[str, Any]]:
    """Given sampled orientations each containing `lat`, `lon`, `bearing_deg` and `weather`,
    compute wind impact and color for each segment point.

    Returns a list of dicts with the original keys plus `impact`, `component`, `angle_between`, `color`.
    """
    results: List[dict[str, Any]] = []
    for item in sampled_orientations:
        bearing = float(item.get("bearing_deg", 0.0))
        weather = item.get("weather") or {}
        wind_speed = float(weather.get("wind_speed_10m", 0.0))
        wind_from = float(weather.get("wind_direction_10m", 0.0))
        impact_info = compute_impact_score(bearing, wind_speed, wind_from)
        color = classify_color(impact_info["impact"], wind_speed)
        out = dict(item)
        out.update(impact_info)
        out["color"] = color
        results.append(out)
    return results
