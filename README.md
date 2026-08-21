# Tadej API

API REST minimale construite avec Python et FastAPI.

## Organisation

```text
app/
	main.py                 # Routes FastAPI et orchestration
	geography.py            # Modèles et fonctions de traitement géographique
	services/
		water.py              # Recherche des points d'eau via Overpass
		weather.py            # Prévisions météo via Open-Meteo
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer l'API

```bash
uvicorn app.main:app --reload
```

L'API est disponible sur http://127.0.0.1:8000. La documentation interactive est sur http://127.0.0.1:8000/docs.

## Routes

- `GET /health` : vérifier que l'API fonctionne
- `GET /tasks` : lister les tâches
- `POST /tasks` : créer une tâche avec `{"title": "Ma tâche"}`
- `GET /tasks/{task_id}` : récupérer une tâche
- `DELETE /tasks/{task_id}` : supprimer une tâche
- `POST /routes/analyze` : analyser un fichier GPX, trouver les points d'eau et obtenir la météo

Exemple avec `curl` :

```bash
curl -X POST "http://127.0.0.1:8000/routes/analyze?every_km=5&radius_m=1500&max_distance_km=100" \
	-F "file=@route.gpx"
```

L'endpoint appelle Overpass pour les points d'eau et Open-Meteo pour la météo. Ces services externes doivent être accessibles depuis l'environnement d'exécution.

## Tests

```bash
pytest
```