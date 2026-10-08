from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from .services.trending import get_trending_movie, get_trending_show, popular_movies, popular_shows, top_rated_movies, top_rated_shows
from .services.search import get_rec_shows, get_recs_movies, get_show, get_movie, search_movie, search_show
from .services.genres import get_movie_genres, get_show_genres, get_movies_by_platform, get_shows_by_platform, get_shows_by_genre, get_movies_by_genre
from sqlmodel import Session
from app.auth.security import get_current_user

DiscoverRoutes = APIRouter()

# Trending APIs
@DiscoverRoutes.get("/trending/movies/")
async def trend_movies(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_trending_movie(page=page)

@DiscoverRoutes.get("/trending/shows/")
async def trend_shows(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_trending_show(page=page)

# Popular Apis
@DiscoverRoutes.get("/popular/movies/")
async def get_popular_movies(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return popular_movies(page=page)

@DiscoverRoutes.get("/popular/shows/")
async def get_popular_shows(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return popular_shows(page=page)

# Search APIs
@DiscoverRoutes.get("/search/movies/")
async def searches_movies(query: str = Query(..., min_length=1, description="Movie search query"), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return search_movie(query=query, page=page)

@DiscoverRoutes.get("/search/shows/")
async def searches_shows(query: str = Query(..., min_length=1, description="Movie search query"), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return search_show(query, page=page)

# Top Rated Apis
@DiscoverRoutes.get("/top_rated/movies/")
async def get_top_rated_movies(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return top_rated_movies(page=page)

@DiscoverRoutes.get("/top_rated/shows/")
async def get_top_rated_shows(page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return top_rated_shows(page=page)

# Movie/Show by ID
@DiscoverRoutes.get("/movie/{id}/")
async def movie(id: int= Path(..., description="Search the movie by id"), current_user: User = Depends(get_current_user)):
    return get_movie(id)

@DiscoverRoutes.get("/show/{id}/")
async def show(id: int= Path(..., description="Search the movie by id"), current_user: User = Depends(get_current_user)):
    return get_show(id)

# Recommendation APIs
@DiscoverRoutes.get("/movies/{movie_id}/recommendations/")
async def get_recommendation_movies(movie_id: int = Path(...), limit: int = Query(5, ge=1, le=50), current_user: User = Depends(get_current_user)):
    return get_recs_movies(movie_id, limit)

@DiscoverRoutes.get("/shows/{show_id}/recommendations/")
async def get_recommendation_shows(show_id: int = Path(...),  limit: int = Query(5, ge=1, le=50), current_user: User = Depends(get_current_user)):
    return get_rec_shows(show_id, limit)

# List Genre APIs
@DiscoverRoutes.get("/genres/movies/")
async def get_movie_genres_list(current_user: User = Depends(get_current_user)):
    return get_movie_genres()

@DiscoverRoutes.get("/genres/shows/")
async def get_show_genres_list(current_user: User = Depends(get_current_user)):
    return get_show_genres()

# Get Movies By Genre
@DiscoverRoutes.get("/genre/{genre_id}/movies/")
async def get_movies_by_genres(genre_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_movies_by_genre(genre_id, limit)

# Get Shows By Genre
@DiscoverRoutes.get("/genre/{genre_id}/shows/")
async def get_shows_by_genres(genre_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_shows_by_genre(genre_id, limit)

@DiscoverRoutes.get("/movies/providers/{provider_id}/")
async def movies_by_platform(provider_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_movies_by_platform(provider_id, page=page)

@DiscoverRoutes.get("/shows/providers/{provider_id}/")
async def shows_by_platform(provider_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_shows_by_platform(provider_id, page=page)