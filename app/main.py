from itertools import count
import logging
from time import perf_counter

import gpxpy
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app import geography
from app.services import water, weather


app = FastAPI(title="Tadej API", version="0.1.0")
logger = logging.getLogger(__name__)

task_ids = count(1)
tasks: dict[int, "Task"] = {}


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    completed: bool = False


class Task(TaskCreate):
    id: int


@app.post("/routes/analyze", response_model=geography.RouteAnalysis)
async def analyze_route(
    file: UploadFile = File(...),
    every_km: float = 5.0,
    radius_m: int = 1500,
    max_distance_km: float | None = 100.0,
) -> geography.RouteAnalysis:
    started_at = perf_counter()
    logger.info(
        "Route analysis started: filename=%s every_km=%s radius_m=%s max_distance_km=%s",
        file.filename,
        every_km,
        radius_m,
        max_distance_km,
    )
    if every_km <= 0 or radius_m <= 0 or (max_distance_km is not None and max_distance_km <= 0):
        logger.warning("Route analysis rejected: invalid numeric parameters")
        raise HTTPException(status_code=400, detail="Les paramètres numériques doivent être positifs")
    try:
        gpx_content = await file.read()
        logger.info("GPX uploaded: bytes=%d", len(gpx_content))
        route = geography.load_route(gpx_content, max_distance_km)
        logger.info("GPX parsed: route_points=%d distance_km=%.2f", len(route), route[-1]["distance_km"])
        sampled_route = geography.sample_route(route, every_km)
        logger.info("Route sampled: sampled_points=%d", len(sampled_route))
        water_points = water.query_overpass_water(sampled_route, radius_m)
        logger.info("Overpass completed: water_points=%d", len(water_points))
        for water_point in water_points:
            nearest = min(
                route,
                key=lambda point: (point["lat"] - water_point["lat"]) ** 2
                + (point["lon"] - water_point["lon"]) ** 2,
            )
            water_point["route_distance_km"] = nearest["distance_km"]
            try:
                water_point["weather"] = weather.get_weather(water_point["lat"], water_point["lon"])
            except requests.RequestException:
                logger.exception("Weather request failed: lat=%s lon=%s", water_point["lat"], water_point["lon"])
                water_point["weather"] = None
    except (UnicodeDecodeError, ValueError, gpxpy.gpx.GPXException) as error:
        logger.exception("GPX processing failed")
        raise HTTPException(status_code=400, detail=f"GPX invalide : {error}") from error
    except requests.RequestException as error:
        logger.exception("External cartographic request failed")
        raise HTTPException(status_code=502, detail="Un service cartographique est indisponible") from error

    logger.info(
        "Route analysis completed: water_points=%d duration_seconds=%.2f",
        len(water_points),
        perf_counter() - started_at,
    )
    return geography.RouteAnalysis(
        distance_km=route[-1]["distance_km"],
        sampled_points=len(sampled_route),
        water_points=water_points,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(tasks.values())


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate) -> Task:
    task = Task(id=next(task_ids), **task_data.model_dump())
    tasks[task.id] = task
    return task


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    if tasks.pop(task_id, None) is None:
        raise HTTPException(status_code=404, detail="Task not found")