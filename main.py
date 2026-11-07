
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path("/data/movies.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                release_year INTEGER NOT NULL
            )
        """)

        sample_movies = [
            ("Interstellar", "Science Fiction", 2014),
            ("Inception", "Science Fiction", 2010),
            ("The Dark Knight", "Action", 2008),
            ("The Matrix", "Science Fiction", 1999),
            ("The Shawshank Redemption", "Drama", 1994),
        ]

        for title, genre, year in sample_movies:
            existing = conn.execute(
                """
                SELECT id FROM movies
                WHERE title = ? AND release_year = ?
                """,
                (title, year),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO movies (title, genre, release_year)
                    VALUES (?, ?, ?)
                    """,
                    (title, genre, year),
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Movie Catalog Service",
    version="1.1.0",
    lifespan=lifespan,
)


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    genre: str = Field(min_length=1, max_length=100)
    release_year: int = Field(ge=1888, le=2100)


@app.get("/health")
def health():
    return {"service": "movie-catalog", "status": "ok"}


@app.post("/movies", status_code=201)
def create_movie(movie: MovieCreate):
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO movies (title, genre, release_year)
               VALUES (?, ?, ?)""",
            (movie.title, movie.genre, movie.release_year),
        )

        row = conn.execute(
            "SELECT * FROM movies WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return dict(row)


@app.get("/movies")
def list_movies():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM movies ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM movies WHERE id = ?",
            (movie_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Movie not found",
        )

    return dict(row)
