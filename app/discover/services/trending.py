from tmdbv3api import Trending, TMDb, Movie, TV
from app.config import tmdb_api, base_image_url
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

trending = Trending()
movie = Movie()
show_api = TV()

def _safe_get(obj, key, default=None):
    """Helper to safely get values from TMDb objects whether they act as dicts or attributes."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

# Get trending movies
def get_trending_movie(page: int = 1):
    try:
        trending_movies = trending.movie_week(page=page)
        movies = getattr(trending_movies, "results", [])

        formatted_results = []
        for m in movies:
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
        logger.error(f"Error fetching trending movies on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch trending movies: {str(e)}")

# Get trending shows
def get_trending_show(page: int = 1):
    try:
        trending_shows = trending.tv_week(page=page)
        shows = getattr(trending_shows, "results", [])

        formatted_results = []
        for s in shows:
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
        logger.error(f"Error fetching trending shows on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch trending shows: {str(e)}")

# Get popular movies
def popular_movies(page: int = 1):
    try:
        popular_movies_result = movie.popular(page=page)
        popular_movies_list = getattr(popular_movies_result, "results", [])

        formatted_results = []
        for m in popular_movies_list:
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
        logger.error(f"Error fetching popular movies on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch popular movies: {str(e)}")

# Get popular shows
def popular_shows(page: int = 1):
    try:
        popular_shows_result = show_api.popular(page=page)
        popular_shows_list = getattr(popular_shows_result, "results", [])

        formatted_results = []
        for s in popular_shows_list:
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
        logger.error(f"Error fetching popular shows on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch popular shows: {str(e)}")

# Get top rated movies
def top_rated_movies(page: int = 1):
    try:
        top_rated_movies_result = movie.top_rated(page=page)
        top_rated_movies_list = getattr(top_rated_movies_result, "results", [])

        formatted_results = []
        for m in top_rated_movies_list:
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
        logger.error(f"Error fetching top rated movies on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch top rated movies: {str(e)}")

# Get top rated shows
def top_rated_shows(page: int = 1):
    try:
        top_rated_shows_result = show_api.top_rated(page=page)
        top_rated_shows_list = getattr(top_rated_shows_result, "results", [])

        formatted_results = []
        for s in top_rated_shows_list:
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
        logger.error(f"Error fetching top rated shows on page {page}: {str(e)}")
        raise RuntimeError(f"Failed to fetch top rated shows: {str(e)}")