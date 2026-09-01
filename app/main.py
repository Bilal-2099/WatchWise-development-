from fastapi import FastAPI, Depends, Path, Query
from app.services.trending import *
from app.services.search import *
from typing import List, Optional
from app.services.genres import *
from contextlib import asynccontextmanager
from sqlmodel import Session
from app.database import init_db, get_session
from app.models import User, Watchlist, DiaryEntry

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/diary/log")
def log_media(entry: DiaryEntry, db: Session = Depends(get_session)):
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "data": entry}
    
# Trending APIs
@app.get("/trending/movies/")
async def trend_movies(limit: int = Query(10, ge=1, le=50, description="Number of Movies to return")):
    return get_trending_movie(limit)

@app.get("/trending/shows/")
async def trend_shows(limit: int = Query(10, ge=1, le=50, description="Number of Shows to return")):
    return get_trending_show(limit)

# Popular Apis
@app.get("/popular/movies/")
async def get_popular_movies(limit: int = Query(10, ge=1, le=50, description="Number of Movies to return")):
    return popular_movies(limit)

@app.get("/popular/shows/")
async def get_popular_shows(limit: int = Query(10, ge=1, le=50, description="Number of Shows to return")):
    return popular_shows(limit)

# Search APIs
@app.get("/search/movies/")
async def searches_movies(query: str = Query(..., min_length=1, description="Movie search query")):
    return search_movie(query)

@app.get("/search/shows/")
async def searches_shows(query: str = Query(..., min_length=1, description="Show search query")):
    return search_show(query)

# Top Rated Apis
@app.get("/top_rated/movies/")
async def get_top_rated_movies(limit: int = Query(10, ge=1, le=50, description="Number of Movies to return")):
    return top_rated_movies(limit)

@app.get("/top_rated/shows/")
async def get_top_rated_shows(limit: int = Query(10, ge=1, le=50, description="Number of Shows to return")):
    return top_rated_shows(limit)

# Movie/Show by ID
@app.get("/movie/{id}")
async def movie(id: int= Path(..., description="Search the movie by id")):
    return get_movie(id)

@app.get("/show/{id}")
async def show(id: int= Path(..., description="Search the movie by id")):
    return get_show(id)

# Recommendation APIs
@app.get("/movies/{movie_id}/recommendations")
async def get_recommendation_movies(movie_id: int = Path(...), limit: int = Query(10, ge=1, le=50)):
    return get_recs_movies(movie_id, limit)

@app.get("/shows/{show_id}/recommendations")
async def get_recommendation_shows(show_id: int = Path(...),  limit: int = Query(10, ge=1, le=50)):
    return get_rec_shows(show_id, limit)

# List Genre APIs
@app.get("/genres/movies/")
async def get_movie_genres_list():
    return get_movie_genres()

@app.get("/genres/shows/")
async def get_show_genres_list():
    return get_show_genres()

# Get Movies By Genre
@app.get("/movies/genre/{genre_id}")
async def get_movies_by_genres(genre_id: int = Path(...),  limit: int = Query(10, ge=1, le=50)):
    return get_movies_by_genre(genre_id, limit)

# Get Shows By Genre
@app.get("/shows/{genre_id}")
async def get_shows_by_genres(genre_id: int = Path(...), limit: int = Query(10, ge=1, le=50)):
    return get_shows_by_genre(genre_id, limit)

@app.get("/movies/providers/{provider_id}")
async def movies_by_platform(provider_id: int = Path(...), limit: int = Query(10, ge=1, le=50)):
    return get_movies_by_platform(provider_id, limit)

@app.get("/shows/providers/{provider_id}")
async def shows_by_platform(provider_id: int = Path(...), limit: int = Query(10, ge=1, le=50)):
    return get_shows_by_platform(provider_id, limit)