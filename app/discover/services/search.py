from tmdbv3api import TMDb, Movie, TV, Discover
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
movie_api = Movie()
show_api = TV()
discover = Discover()

# Search Movies
def search_movie(query: str, page: int = 1):
    if not isinstance(query, str) or not query.strip():
        return {"page": page, "results": []}

    search_results = movie_api.search(query.strip(), page=page)
    results = getattr(search_results, "results", [])

    return {
        "page": page,
        "results": [
            {
                "id": item.id,
                "title": item.title,
                "year": (item.release_date[:4]
                    if getattr(item, "release_date", None) else None),
                "rating": (item.vote_average
                    if getattr(item, "vote_average", None) is not None else None),
                "poster": (
                    base_image_url + item.poster_path
                    if getattr(item, "poster_path", None) else None),}
            for item in results
        ],
    }

# Search Shows
def search_show(query: str, page: int = 1):
    if not isinstance(query, str) or not query.strip():
        return {"page": page, "results": []}

    search_results = show_api.search(query.strip(), page=page)
    results = getattr(search_results, "results", [])

    return {
        "page": page,
        "results": [
        {
            "id": item["id"],
            "title": item["name"],
            "year": item.first_air_date[:4] if item.first_air_date else None, # Added year
            "rating": item["vote_average"] if item["vote_average"] else None,
            "poster": base_image_url + item["poster_path"] if item["poster_path"] else None
        }
        for item in results
    ]
   }

def get_movie(id):
    movie_detail = movie_api.details(id, append_to_response='watch/providers,credits,videos')
    
    # Helper to safely fetch from objects or dictionaries
    def safe_get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # 1. Watch Providers Extraction
    providers_data = safe_get(movie_detail, 'watch_providers') or safe_get(movie_detail, 'watch/providers', {})
    providers_results = safe_get(providers_data, 'results', {})
    us_providers = providers_results.get('US', {}) if isinstance(providers_results, dict) else getattr(providers_results, 'US', {})
    
    # 2. Credits Extraction (Crew & Cast)
    credits_data = safe_get(movie_detail, 'credits', {})
    raw_crew = safe_get(credits_data, 'crew', [])
    crew = list(raw_crew) if raw_crew else []
        
    director = None
    for person in crew:
        p_name = safe_get(person, 'name')
        p_job = safe_get(person, 'job')
        if p_job == 'Director':
            director = p_name
            break

    raw_cast = safe_get(credits_data, 'cast', [])
    cast = list(raw_cast) if raw_cast else []

    top_cast = []
    for actor in cast[:5]:
        actor_name = safe_get(actor, 'name')
        if actor_name:
            profile_path = safe_get(actor, 'profile_path')
            top_cast.append({
                "name": actor_name,
                "character": safe_get(actor, 'character'),
                "profile_path": base_image_url + profile_path if profile_path else None
            })

    # 3. Videos / Trailer Extraction
    videos_data = safe_get(movie_detail, 'videos', {})
    raw_results = safe_get(videos_data, 'results', [])
    results = list(raw_results) if raw_results else []

    trailer_key = None
    for v in results:
        v_type = safe_get(v, 'type')
        v_site = safe_get(v, 'site')
        v_key = safe_get(v, 'key')
        if v_type == 'Trailer' and v_site == 'YouTube':
            trailer_key = v_key
            break
            
    trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

    # Helper for watch provider lists
    def get_provider_names(provider_type):
        p_list = us_providers.get(provider_type, []) if isinstance(us_providers, dict) else getattr(us_providers, provider_type, [])
        return [safe_get(p, 'provider_name') for p in p_list if safe_get(p, 'provider_name')]

    poster_path = safe_get(movie_detail, 'poster_path')
    backdrop_path = safe_get(movie_detail, 'backdrop_path')
    release_date = safe_get(movie_detail, 'release_date')
    genres_raw = safe_get(movie_detail, 'genres') or []

    return {
        "results": {
            "id": safe_get(movie_detail, 'id'),
            "title": safe_get(movie_detail, 'title'),
            "tagline": safe_get(movie_detail, 'tagline'),
            "release_date": release_date if release_date else None,
            "rating": safe_get(movie_detail, 'vote_average'),
            "genres": [safe_get(genre, 'name') for genre in genres_raw if safe_get(genre, 'name')],
            "runtime": safe_get(movie_detail, 'runtime'),
            "description": safe_get(movie_detail, 'overview'),
            "director": director,
            "cast": top_cast,
            "trailer_url": trailer_url,
            "poster": base_image_url + poster_path if poster_path else None,
            "backdrop_pic": base_image_url + backdrop_path if backdrop_path else None,
            "watch_providers": {
                "stream": get_provider_names('flatrate'),
                "rent": get_provider_names('rent'),
                "buy": get_provider_names('buy')
            }
        }
    }

def get_show(id):
    show_detail = show_api.details(id, append_to_response='watch/providers,credits,videos')
    
    # Helper to safely get attributes or dict keys
    def safe_get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # 1. Watch Providers Extraction
    providers_data = safe_get(show_detail, 'watch_providers') or safe_get(show_detail, 'watch/providers', {})
    providers_results = safe_get(providers_data, 'results', {})
    us_providers = providers_results.get('US', {}) if isinstance(providers_results, dict) else getattr(providers_results, 'US', {})
    
    # 2. Credits Extraction (Cast & Crew)
    credits_data = safe_get(show_detail, 'credits', {})
    raw_crew = safe_get(credits_data, 'crew', [])
    crew = list(raw_crew) if raw_crew else []
    raw_creators = safe_get(show_detail, 'created_by', [])
    creators = list(raw_creators) if raw_creators else []
    created_by_list = []
    for creator in creators:
        creator_name = safe_get(creator, 'name')
        if creator_name:
            created_by_list.append(creator_name)

    raw_cast = safe_get(credits_data, 'cast', [])
    cast = list(raw_cast) if raw_cast else []

    top_cast = []
    for actor in cast[:5]:
        actor_name = safe_get(actor, 'name')
        if actor_name:
            profile_path = safe_get(actor, 'profile_path')
            top_cast.append({
                "name": actor_name,
                "character": safe_get(actor, 'character'),
                "profile_path": base_image_url + profile_path if profile_path else None
            })

    # 3. Videos / Trailer Extraction
    videos_data = safe_get(show_detail, 'videos', {})
    raw_results = safe_get(videos_data, 'results', [])
    results = list(raw_results) if raw_results else []

    trailer_key = None
    for v in results:
        v_type = safe_get(v, 'type')
        v_site = safe_get(v, 'site')
        v_key = safe_get(v, 'key')
        if v_type == 'Trailer' and v_site == 'YouTube':
            trailer_key = v_key
            break
            
    trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

    # Helper for watch provider lists
    def get_provider_names(provider_type):
        p_list = us_providers.get(provider_type, []) if isinstance(us_providers, dict) else getattr(us_providers, provider_type, [])
        return [safe_get(p, 'provider_name') for p in p_list if safe_get(p, 'provider_name')]

    poster_path = safe_get(show_detail, 'poster_path')
    backdrop_path = safe_get(show_detail, 'backdrop_path')
    first_air_date = safe_get(show_detail, 'first_air_date')
    raw_runtimes = safe_get(show_detail, 'episode_run_time', [])
    episode_run_time = list(raw_runtimes) if raw_runtimes else []

    return {
        "results": {
            "id": safe_get(show_detail, 'id'),
            "title": safe_get(show_detail, 'name'),
            "tagline": safe_get(show_detail, 'tagline'),
            "status": safe_get(show_detail, 'status'),
            "episode_run_time": episode_run_time,
            "first_air_date": first_air_date if first_air_date else None,
            "rating": safe_get(show_detail, 'vote_average'),
            "genres": [genre.get('name') if isinstance(genre, dict) else getattr(genre, 'name', '') for genre in (safe_get(show_detail, 'genres') or [])],
            "description": safe_get(show_detail, 'overview'),
            "total_episodes": safe_get(show_detail, 'number_of_episodes'),
            "seasons": safe_get(show_detail, 'number_of_seasons'),
            "created_by": created_by_list,
            "cast": top_cast,
            "trailer_url": trailer_url,
            "poster": base_image_url + poster_path if poster_path else None,
            "backdrop_pic": base_image_url + backdrop_path if backdrop_path else None,
            "watch_providers": {
                "stream": get_provider_names('flatrate'),
                "rent": get_provider_names('rent'),
                "buy": get_provider_names('buy')
            }
        }
    }

# Recommendations Movies
def get_recs_movies(movie_id, limit=10, ):
    recs_movies = movie_api.recommendations(movie_id)

    recs_movies = list(recs_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": m["id"],
            "title": m["title"],
            "year": m.release_date[:4] if m.release_date else None, # Added year
            "rating": m["vote_average"],
            "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
        }
        for m in recs_movies
    ]
    }

# Recommendations Shows
def get_rec_shows(show_id,limit=20):
    recs_shows = show_api.recommendations(show_id)

    recs_shows = list(recs_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": s["id"],
            "title": s["name"],
            "year": s.first_air_date[:4] if s.first_air_date else None, # Added year
            "rating": s["vote_average"],
            "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
        }
        for s in recs_shows
    ]
    }
