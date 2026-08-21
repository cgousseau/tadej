from fastapi.testclient import TestClient

from app.main import app, tasks


client = TestClient(app)


def setup_function() -> None:
    tasks.clear()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_list_and_get_task() -> None:
    created = client.post("/tasks", json={"title": "Préparer l'API"})

    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "Préparer l'API"
    assert task["completed"] is False

    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert listed.json() == [task]

    fetched = client.get(f"/tasks/{task['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == task


def test_missing_task_returns_not_found() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_analyze_gpx(monkeypatch) -> None:
    gpx = b'''<?xml version="1.0"?><gpx version="1.1" creator="test">
    <trk><name>Test</name><trkseg>
    <trkpt lat="48.8566" lon="2.3522"/><trkpt lat="48.8570" lon="2.3530"/>
    </trkseg></trk></gpx>'''

    monkeypatch.setattr(
        "app.services.water.query_overpass_water",
        lambda points, radius_m: [{"osm_id": 42, "lat": 48.8568, "lon": 2.3526}],
    )
    monkeypatch.setattr(
        "app.services.weather.get_weather",
        lambda lat, lon: {"temperature_2m": 21},
    )

    response = client.post(
        "/routes/analyze?max_distance_km=100",
        files={"file": ("route.gpx", gpx, "application/gpx+xml")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["sampled_points"] == 1
    assert result["water_points"][0]["osm_id"] == 42
    assert result["water_points"][0]["weather"] == {"temperature_2m": 21}