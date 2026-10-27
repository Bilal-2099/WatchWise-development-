from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from .services.trending import get_trending_movie, get_trending_show, popular_movies, popular_shows, top_rated_movies, top_rated_shows
from .services.search import get_rec_shows, get_recs_movies, get_show, get_movie, search_movie, search_show
from .services.genres import get_movie_genres, get_show_genres, get_movies_by_platform, get_shows_by_platform, get_shows_by_genre, get_movies_by_genre
from sqlmodel import Session
from app.auth.security import get_current_user
from tmdbv3api import TMDb, Movie, TV, Discover
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
movie_api = Movie()
show_api = TV()
discover = Discover()

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
    return get_movies_by_genre(genre_id, page=page)

# Get Shows By Genre
@DiscoverRoutes.get("/genre/{genre_id}/shows/")
async def get_shows_by_genres(genre_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_shows_by_genre(genre_id, page=page)

@DiscoverRoutes.get("/movies/providers/{provider_id}/")
async def movies_by_platform(provider_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_movies_by_platform(provider_id, page=page)

@DiscoverRoutes.get("/shows/providers/{provider_id}/")
async def shows_by_platform(provider_id: int = Path(...), page: int = Query(1, ge=1, description="TMDB page number"), current_user: User = Depends(get_current_user)):
    return get_shows_by_platform(provider_id, page=page)


# Helper function to safely extract attributes whether TMDB returns dict or object
def _parse_tmdb_item(item, media_type: str, base_image_url: str):
    is_movie = media_type == "movie"
    
    # Handle dict vs object inconsistency safely
    get_val = lambda obj, key, default=None: obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
    
    item_id = get_val(item, "id")
    title = get_val(item, "title" if is_movie else "name")
    
    date_field = "release_date" if is_movie else "first_air_date"
    raw_date = get_val(item, date_field)
    year = raw_date[:4] if raw_date and len(raw_date) >= 4 else None
    
    rating = get_val(item, "vote_average")
    poster_path = get_val(item, "poster_path")
    poster = f"{base_image_url}{poster_path}" if poster_path else None
    
    return {
        "id": item_id,
        "title": title,
        "media_type": media_type,
        "year": year,
        "rating": rating,
        "poster": poster,
    }

@DiscoverRoutes.get("/search/all")
def search_media(
    query: str | None = Query(None, description="Free text search query"),
    media_type: str = Query("movie", pattern="^(movie|tv)$", description="Media type: 'movie' or 'tv'"),
    genres: str | None = Query(None, description="Comma-separated genre IDs, e.g., '28,12' for Action & Adventure"),
    provider_id: int | None = Query(None, description="TMDB Watch Provider ID"),
    year: int | None = Query(None, description="Release or air year"),
    sort_by: str = Query("popularity.desc", description="Sort option"),
    page: int = Query(1, ge=1),
    region: str = Query("US", description="Region code for providers")
):
    """
    Unified Search & Discover endpoint supporting multiple genres.
    """
    # 1. Text Search mode
    if query and query.strip():
        search_results = (
            movie_api.search(query.strip(), page=page) 
            if media_type == "movie" 
            else show_api.search(query.strip(), page=page)
        )
        items = getattr(search_results, "results", [])
        formatted = [_parse_tmdb_item(item, media_type, base_image_url) for item in items]
        
        if year is not None:
            formatted = [item for item in formatted if item["year"] == str(year)]

        return {"page": page, "results": formatted}

    # 2. Discover & Filter mode
    filters = {
        "sort_by": sort_by,
        "page": page,
    }
    
    # Pass multiple genres directly (TMDB handles comma-separated strings natively)
    if genres:
        filters["with_genres"] = genres
        
    if provider_id is not None:
        filters["with_watch_providers"] = provider_id
        filters["watch_region"] = region
        
    if media_type == "movie":
        if year is not None:
            filters["primary_release_year"] = year
        discover_results = discover.discover_movies(filters)
    else:
        if year is not None:
            filters["first_air_date_year"] = year
        discover_results = discover.discover_tv_shows(filters)

    items = getattr(discover_results, "results", [])
    return {"page": page, "results": [_parse_tmdb_item(item, media_type, base_image_url) for item in items]}