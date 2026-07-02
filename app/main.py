from fastapi import FastAPI
from app.services.trending import *
from app.services.search import *
from app.services.genres import *

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

# Top Rated Apis
@app.get("/top_rated/movies/{limit}")
async def get_top_rated_movies(limit: int):
    return top_rated_movies(limit)

@app.get("/top_rated/shows/{limit}")
async def get_top_rated_shows(limit: int):
    return top_rated_shows(limit)

# Get APIs
@app.get("/movie/{id}")
async def movie(id: int):
    return get_movie(id)

@app.get("/show/{id}")
async def show(id: int):
    return get_show(id)

# Recommendation APIs
@app.get("/rec/movies/{movie_id}/{limit}")
async def get_recommendation_movies(movie_id: int, limit: int):
    return get_recs_movies(movie_id, 5)

@app.get("/rec/shows/{show_id}/{limit}")
async def get_recommendation_shows(show_id: int, limit: int):
    return get_rec_shows(show_id, 5)

# List Genre APIs
@app.get("/genres/movies/")
async def get_movie_genres():
    return get_movie_genres()

@app.get("/genres/shows/")
async def get_show_genres():
    return get_show_genres()

# Get Movies By Genre
@app.get("/movies/{genre_id}/{limit}")
async def get_movies_by_genre(genre_id: int, limit: int):
    return get_movies_by_genre(genre_id, limit)

# Get Shows By Genre
@app.get("/shows/{genre_id}/{limit}")
async def get_shows_by_genre(genre_id: int, limit: int):
    return get_shows_by_genre(genre_id, limit)