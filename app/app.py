from fastapi import FastAPI
from trending import get_trending_movie, get_trending_show
from search import search_movie, search_show

app = FastAPI()

# Trending API
@app.get("/trend_movies/{limit}")
async def root(limit: int):
    return get_trending_movie(limit)

@app.get("/trend_shows/{limit}")
async def root(limit: int):
    return get_trending_show(limit)

# Search APIs
@app.get("/search_movies/{searches}")
async def root(searches: str):
    return search_movie(searches)

@app.get("/search_show/{searches}")
async def root(searches: str):
    return search_show(searches)