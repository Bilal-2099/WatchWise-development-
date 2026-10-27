from tmdbv3api import TMDb, Discover, Genre
from app.config import tmdb_api, base_image_url
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

discover = Discover()
genre_api = Genre()

def _safe_get(obj, key, default=None):
    """Helper to safely get values from TMDb objects whether they act as dicts or attributes."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

# Get Genres
def get_movie_genres():
    try:
        result = genre_api.movie_list()
        genres = getattr(result, "genres", [])
        
        return {
            "genres": [
                {
                    "id": _safe_get(genre, "id"),
                    "name": _safe_get(genre, "name"),
                }
                for genre in genres if genre
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching movie genres: {str(e)}")
        raise RuntimeError(f"Failed to fetch movie genres from TMDb: {str(e)}")

def get_show_genres():
    try:
        result = genre_api.tv_list()
        genres = getattr(result, "genres", [])

        return {
            "genres": [
                {
                    "id": _safe_get(genre, "id"),
                    "name": _safe_get(genre, "name"),
                }
                for genre in genres if genre
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching TV show genres: {str(e)}")
        raise RuntimeError(f"Failed to fetch TV show genres from TMDb: {str(e)}")

# Get Movies by Genre ID
def get_movies_by_genre(genre_id, page: int = 1):
    try:
        discover_results = discover.discover_movies({
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": page
        })
        
        results = getattr(discover_results, "results", [])

        formatted_results = []
        for m in results:
            release_date = _safe_get(m, "release_date")
            poster_path = _safe_get(m, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(m, "id"),
                "title": _safe_get(m, "title"),
                "rating": _safe_get(m, "vote_average", 0.0),
                "year": release_date[:4] if release_date and len(release_date) >= 4 else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "page": page,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching movies by genre {genre_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch movies by genre: {str(e)}")

# Get Shows by Genre ID
def get_shows_by_genre(genre_id, page: int = 1):
    try:
        discover_results = discover.discover_tv_shows({
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": page
        })
        
        results = getattr(discover_results, "results", [])

        formatted_results = []
        for s in results:
            first_air_date = _safe_get(s, "first_air_date")
            poster_path = _safe_get(s, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(s, "id"),
                "title": _safe_get(s, "name"),
                "rating": _safe_get(s, "vote_average", 0.0),
                "year": first_air_date[:4] if first_air_date and len(first_air_date) >= 4 else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "page": page,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching shows by genre {genre_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch shows by genre: {str(e)}")

# Movies by Provider ID
def get_movies_by_platform(provider_id, page: int = 1, region="US"):
    try:
        filters = {
            "with_watch_providers": provider_id,
            "watch_region": region,
            "sort_by": "popularity.desc",
            "page": page,
        }
        
        results = discover.discover_movies(filters)
        items = getattr(results, "results", [])
        
        formatted_results = []
        for item in items:
            release_date = _safe_get(item, "release_date")
            poster_path = _safe_get(item, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(item, "id"),
                "title": _safe_get(item, "title"),
                "rating": _safe_get(item, "vote_average", 0.0),
                "year": release_date[:4] if release_date and len(release_date) >= 4 else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "page": page,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching movies by platform {provider_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch movies by platform: {str(e)}")

# Shows by Provider ID
def get_shows_by_platform(provider_id, page: int = 1, region="US"):
    try:
        filters = {
            "with_watch_providers": provider_id,
            "watch_region": region,
            "sort_by": "popularity.desc",
            "page": page,
        }
        
        results = discover.discover_tv_shows(filters)
        items = getattr(results, "results", [])
        
        formatted_results = []
        for item in items:
            first_air_date = _safe_get(item, "first_air_date")
            poster_path = _safe_get(item, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(item, "id"),
                "title": _safe_get(item, "name"),
                "rating": _safe_get(item, "vote_average", 0.0),
                "year": first_air_date[:4] if first_air_date and len(first_air_date) >= 4 else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "page": page,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching shows by platform {provider_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch shows by platform: {str(e)}")