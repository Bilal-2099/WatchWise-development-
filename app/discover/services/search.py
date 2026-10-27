from tmdbv3api import TMDb, Movie, TV, Discover
from app.config import tmdb_api, base_image_url
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
movie_api = Movie()
show_api = TV()
discover = Discover()

def _safe_get(obj, key, default=None):
    """Helper to safely get values from TMDb objects whether they act as dicts or attributes."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

# Search Movies
def search_movie(query: str, page: int = 1):
    try:
        if not isinstance(query, str) or not query.strip():
            return {"page": page, "results": []}

        search_results = movie_api.search(query.strip(), page=page)
        results = getattr(search_results, "results", [])

        formatted_results = []
        for item in results:
            release_date = _safe_get(item, "release_date")
            vote_average = _safe_get(item, "vote_average")
            poster_path = _safe_get(item, "poster_path")

            formatted_results.append({
                "id": _safe_get(item, "id"),
                "title": _safe_get(item, "title"),
                "year": release_date[:4] if release_date and len(release_date) >= 4 else None,
                "rating": vote_average if vote_average is not None else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "page": page,
            "results": formatted_results,
        }
    except Exception as e:
        logger.error(f"Error searching movies with query '{query}': {str(e)}")
        raise RuntimeError(f"Failed to search movies: {str(e)}")

# Search Shows
def search_show(query: str, page: int = 1):
    try:
        if not isinstance(query, str) or not query.strip():
            return {"page": page, "results": []}

        search_results = show_api.search(query.strip(), page=page)
        results = getattr(search_results, "results", [])

        formatted_results = []
        for item in results:
            first_air_date = _safe_get(item, "first_air_date")
            vote_average = _safe_get(item, "vote_average")
            poster_path = _safe_get(item, "poster_path")

            formatted_results.append({
                "id": _safe_get(item, "id"),
                "title": _safe_get(item, "name"),
                "year": first_air_date[:4] if first_air_date and len(first_air_date) >= 4 else None,
                "rating": vote_average if vote_average is not None else None,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None
            })

        return {
            "page": page,
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error searching shows with query '{query}': {str(e)}")
        raise RuntimeError(f"Failed to search shows: {str(e)}")

def get_movie(id):
    try:
        movie_detail = movie_api.details(id, append_to_response='watch/providers,credits,videos')
        
        providers_data = _safe_get(movie_detail, 'watch_providers') or _safe_get(movie_detail, 'watch/providers', {})
        providers_results = _safe_get(providers_data, 'results', {})
        us_providers = providers_results.get('US', {}) if isinstance(providers_results, dict) else getattr(providers_results, 'US', {})
        
        credits_data = _safe_get(movie_detail, 'credits', {})
        raw_crew = _safe_get(credits_data, 'crew', [])
        crew = list(raw_crew) if raw_crew else []
            
        director = None
        for person in crew:
            p_name = _safe_get(person, 'name')
            p_job = _safe_get(person, 'job')
            if p_job == 'Director':
                director = p_name
                break

        raw_cast = _safe_get(credits_data, 'cast', [])
        cast = list(raw_cast) if raw_cast else []

        top_cast = []
        for actor in cast[:5]:
            actor_name = _safe_get(actor, 'name')
            if actor_name:
                profile_path = _safe_get(actor, 'profile_path')
                top_cast.append({
                    "name": actor_name,
                    "character": _safe_get(actor, 'character'),
                    "profile_path": f"{base_image_url}{profile_path}" if profile_path else None
                })

        videos_data = _safe_get(movie_detail, 'videos', {})
        raw_results = _safe_get(videos_data, 'results', [])
        results = list(raw_results) if raw_results else []

        trailer_key = None
        for v in results:
            v_type = _safe_get(v, 'type')
            v_site = _safe_get(v, 'site')
            v_key = _safe_get(v, 'key')
            if v_type == 'Trailer' and v_site == 'YouTube':
                trailer_key = v_key
                break
                
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

        def get_provider_names(provider_type):
            p_list = us_providers.get(provider_type, []) if isinstance(us_providers, dict) else getattr(us_providers, provider_type, [])
            return [_safe_get(p, 'provider_name') for p in p_list if _safe_get(p, 'provider_name')]

        poster_path = _safe_get(movie_detail, 'poster_path')
        backdrop_path = _safe_get(movie_detail, 'backdrop_path')
        release_date = _safe_get(movie_detail, 'release_date')
        genres_raw = _safe_get(movie_detail, 'genres') or []

        return {
            "results": {
                "id": _safe_get(movie_detail, 'id'),
                "title": _safe_get(movie_detail, 'title'),
                "tagline": _safe_get(movie_detail, 'tagline'),
                "release_date": release_date if release_date else None,
                "rating": _safe_get(movie_detail, 'vote_average'),
                "genres": [_safe_get(genre, 'name') for genre in genres_raw if _safe_get(genre, 'name')],
                "runtime": _safe_get(movie_detail, 'runtime'),
                "description": _safe_get(movie_detail, 'overview'),
                "director": director,
                "cast": top_cast,
                "trailer_url": trailer_url,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
                "backdrop_pic": f"{base_image_url}{backdrop_path}" if backdrop_path else None,
                "watch_providers": {
                    "stream": get_provider_names('flatrate'),
                    "rent": get_provider_names('rent'),
                    "buy": get_provider_names('buy')
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching movie details for ID {id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch movie details: {str(e)}")

def get_show(id):
    try:
        show_detail = show_api.details(id, append_to_response='watch/providers,credits,videos')

        providers_data = _safe_get(show_detail, 'watch_providers') or _safe_get(show_detail, 'watch/providers', {})
        providers_results = _safe_get(providers_data, 'results', {})
        us_providers = providers_results.get('US', {}) if isinstance(providers_results, dict) else getattr(providers_results, 'US', {})
        
        credits_data = _safe_get(show_detail, 'credits', {})
        raw_creators = _safe_get(show_detail, 'created_by', [])
        creators = list(raw_creators) if raw_creators else []
        created_by_list = []
        for creator in creators:
            creator_name = _safe_get(creator, 'name')
            if creator_name:
                created_by_list.append(creator_name)

        raw_cast = _safe_get(credits_data, 'cast', [])
        cast = list(raw_cast) if raw_cast else []

        top_cast = []
        for actor in cast[:5]:
            actor_name = _safe_get(actor, 'name')
            if actor_name:
                profile_path = _safe_get(actor, 'profile_path')
                top_cast.append({
                    "name": actor_name,
                    "character": _safe_get(actor, 'character'),
                    "profile_path": f"{base_image_url}{profile_path}" if profile_path else None
                })

        videos_data = _safe_get(show_detail, 'videos', {})
        raw_results = _safe_get(videos_data, 'results', [])
        results = list(raw_results) if raw_results else []

        trailer_key = None
        for v in results:
            v_type = _safe_get(v, 'type')
            v_site = _safe_get(v, 'site')
            v_key = _safe_get(v, 'key')
            if v_type == 'Trailer' and v_site == 'YouTube':
                trailer_key = v_key
                break
                
        trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

        def get_provider_names(provider_type):
            p_list = us_providers.get(provider_type, []) if isinstance(us_providers, dict) else getattr(us_providers, provider_type, [])
            return [_safe_get(p, 'provider_name') for p in p_list if _safe_get(p, 'provider_name')]

        poster_path = _safe_get(show_detail, 'poster_path')
        backdrop_path = _safe_get(show_detail, 'backdrop_path')
        first_air_date = _safe_get(show_detail, 'first_air_date')
        raw_runtimes = _safe_get(show_detail, 'episode_run_time', [])
        episode_run_time = list(raw_runtimes) if raw_runtimes else []

        return {
            "results": {
                "id": _safe_get(show_detail, 'id'),
                "title": _safe_get(show_detail, 'name'),
                "tagline": _safe_get(show_detail, 'tagline'),
                "status": _safe_get(show_detail, 'status'),
                "episode_run_time": episode_run_time,
                "first_air_date": first_air_date if first_air_date else None,
                "rating": _safe_get(show_detail, 'vote_average'),
                "genres": [_safe_get(genre, 'name') for genre in (_safe_get(show_detail, 'genres') or []) if _safe_get(genre, 'name')],
                "description": _safe_get(show_detail, 'overview'),
                "total_episodes": _safe_get(show_detail, 'number_of_episodes'),
                "seasons": _safe_get(show_detail, 'number_of_seasons'),
                "created_by": created_by_list,
                "cast": top_cast,
                "trailer_url": trailer_url,
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
                "backdrop_pic": f"{base_image_url}{backdrop_path}" if backdrop_path else None,
                "watch_providers": {
                    "stream": get_provider_names('flatrate'),
                    "rent": get_provider_names('rent'),
                    "buy": get_provider_names('buy')
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching show details for ID {id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch show details: {str(e)}")

def get_recs_movies(movie_id, limit=10):
    try:
        recs_results = movie_api.recommendations(movie_id)
        recs_movies = list(getattr(recs_results, "results", []))[:limit]

        formatted_results = []
        for m in recs_movies:
            release_date = _safe_get(m, "release_date")
            poster_path = _safe_get(m, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(m, "id"),
                "title": _safe_get(m, "title"),
                "year": release_date[:4] if release_date and len(release_date) >= 4 else None,
                "rating": _safe_get(m, "vote_average", 0.0),
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching movie recommendations for ID {movie_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch movie recommendations: {str(e)}")

def get_rec_shows(show_id, limit=20):
    try:
        recs_results = show_api.recommendations(show_id)
        recs_shows = list(getattr(recs_results, "results", []))[:limit]

        formatted_results = []
        for s in recs_shows:
            first_air_date = _safe_get(s, "first_air_date")
            poster_path = _safe_get(s, "poster_path")
            
            formatted_results.append({
                "id": _safe_get(s, "id"),
                "title": _safe_get(s, "name"),
                "year": first_air_date[:4] if first_air_date and len(first_air_date) >= 4 else None,
                "rating": _safe_get(s, "vote_average", 0.0),
                "poster": f"{base_image_url}{poster_path}" if poster_path else None,
            })

        return {
            "results": formatted_results
        }
    except Exception as e:
        logger.error(f"Error fetching show recommendations for ID {show_id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch show recommendations: {str(e)}")

def get_movie_minor(id):
    try:
        movie_detail = movie_api.details(id)
        
        return {
            "results": {
                "id": _safe_get(movie_detail, 'id'),
                "title": _safe_get(movie_detail, 'title')
            }
        }
    except Exception as e:
        logger.error(f"Error fetching minor movie details for ID {id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch minor movie details: {str(e)}")

def get_show_minor(id):
    try:
        show_detail = show_api.details(id)
        
        return {
            "results": {
                "id": _safe_get(show_detail, 'id'),
                "title": _safe_get(show_detail, 'name')             
            }
        }
    except Exception as e:
        logger.error(f"Error fetching minor show details for ID {id}: {str(e)}")
        raise RuntimeError(f"Failed to fetch minor show details: {str(e)}")