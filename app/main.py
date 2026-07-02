from fastapi import FastAPI
from app.services.trending import *
from app.services.search import *

app = FastAPI()

# Trending APIs
@app.get("/trending/movies/{limit}")
async def trend_movies(limit: int):
    return get_trending_movie(limit)

@app.get("/trending/shows/{limit}")
async def trend_shows(limit: int):
    return get_trending_show(limit)

# Popular Apis
@app.get("/popular/movies/{limit}")
async def get_popular_movies(limit: int):
    return popular_movies(limit)

@app.get("/popular/shows/{limit}")
async def get_popular_shows(limit: int):
    return popular_shows(limit)

# Search APIs
@app.get("/search/movies/{query}")
async def searches_movies(query: str):
    return search_movie(query)

@app.get("/search/shows/{query}")
async def searches_shows(query: str):
    return search_show(query)

# Get APIs
@app.get("/movie/{id}")
async def movie(id: int):
    return get_movie(id)

@app.get("/show/{id}")
async def show(id: int):
    return get_show(id)