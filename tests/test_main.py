import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a temporary database for testing.
    test_db = tmp_path / "test_movies.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)

    with TestClient(main.app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "movie-catalog",
        "status": "ok"
    }


def test_list_movies(client):
    response = client.get("/movies")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 5


def test_get_existing_movie(client):
    response = client.get("/movies/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Interstellar"


def test_get_nonexistent_movie(client):
    response = client.get("/movies/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


def test_create_movie(client):
    movie = {
        "title": "CI CD Test Movie",
        "genre": "Action",
        "release_year": 2025
    }

    response = client.post("/movies", json=movie)

    assert response.status_code == 201
    assert response.json()["title"] == movie["title"]
    assert response.json()["genre"] == movie["genre"]
    assert response.json()["release_year"] == movie["release_year"]


def test_create_movie_with_invalid_year(client):
    movie = {
        "title": "Invalid Movie",
        "genre": "Drama",
        "release_year": 1800
    }

    response = client.post("/movies", json=movie)

    assert response.status_code == 422
