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

# Get a Movie
def get_movie(id):
    movie_detail = movie_api.details(id, append_to_response='watch/providers,credits,videos')
    
    # 1. Watch Providers Extraction
    providers_data = getattr(movie_detail, 'watch_providers', None) or movie_detail.get('watch/providers', {})
    if hasattr(providers_data, 'results'):
        us_providers = providers_data.results.get('US', {})
    else:
        us_providers = providers_data.get('results', {}).get('US', {})
    
    # 2. Credits Extraction
    credits_data = getattr(movie_detail, 'credits', None) or movie_detail.get('credits', {})
    
    # Extract and force conversion to a standard Python list
    raw_crew = credits_data.get('crew', []) if hasattr(credits_data, 'get') else getattr(credits_data, 'crew', [])
    crew = list(raw_crew) if raw_crew else []
        
    director = None
    for person in crew:
        p_name = person.get('name') if isinstance(person, dict) else getattr(person, 'name', None)
        p_job = person.get('job') if isinstance(person, dict) else getattr(person, 'job', None)
        if p_job == 'Director':
            director = p_name
            break

    # Extract and force conversion to a standard Python list
    raw_cast = credits_data.get('cast', []) if hasattr(credits_data, 'get') else getattr(credits_data, 'cast', [])
    cast = list(raw_cast) if raw_cast else []

    top_cast = []
    for actor in cast[:5]:
        actor_name = actor.get('name') if isinstance(actor, dict) else getattr(actor, 'name', None)
        if actor_name:
            top_cast.append(actor_name)

    # 3. Videos / Trailer Extraction
    videos_data = getattr(movie_detail, 'videos', None) or movie_detail.get('videos', {})
    raw_results = videos_data.get('results', []) if hasattr(videos_data, 'get') else getattr(videos_data, 'results', [])
    results = list(raw_results) if raw_results else []

    trailer_key = None
    for v in results:
        v_type = v.get('type') if isinstance(v, dict) else getattr(v, 'type', None)
        v_site = v.get('site') if isinstance(v, dict) else getattr(v, 'site', None)
        v_key = v.get('key') if isinstance(v, dict) else getattr(v, 'key', None)
        if v_type == 'Trailer' and v_site == 'YouTube':
            trailer_key = v_key
            break
            
    trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

    return {
        "results": {
            "id": movie_detail.id,
            "title": movie_detail.title,
            "year": movie_detail.release_date[:4] if movie_detail.release_date else None,
            "rating": movie_detail.vote_average if movie_detail.vote_average else None,
            "genres": [genre['name'] for genre in movie_detail.genres] if movie_detail.genres else [],
            "runtime": getattr(movie_detail, 'runtime', None),
            "description": movie_detail.overview,
            "director": director,
            "cast": top_cast,
            "trailer_url": trailer_url,
            "release_date": movie_detail.release_date,
            "poster": base_image_url + movie_detail.poster_path if movie_detail.poster_path else None,
            "backdrop_pic": base_image_url + movie_detail.backdrop_path if movie_detail.backdrop_path else None,
            "watch_providers": {
                "stream": [p.get('provider_name') for p in us_providers.get('flatrate', [])],
                "rent": [p.get('provider_name') for p in us_providers.get('rent', [])],
                "buy": [p.get('provider_name') for p in us_providers.get('buy', [])]
            }
        }
   }

def get_show(id):
    show_detail = show_api.details(id, append_to_response='watch/providers,credits,videos')
    
    # 1. Watch Providers Extraction
    providers_data = getattr(show_detail, 'watch_providers', None) or show_detail.get('watch/providers', {})
    if hasattr(providers_data, 'results'):
        us_providers = providers_data.results.get('US', {})
    else:
        us_providers = providers_data.get('results', {}).get('US', {})
    
    # 2. Credits Extraction
    credits_data = getattr(show_detail, 'credits', None) or show_detail.get('credits', {})
    
    # Extract and force conversion to a standard Python list
    raw_crew = credits_data.get('crew', []) if hasattr(credits_data, 'get') else getattr(credits_data, 'crew', [])
    crew = list(raw_crew) if raw_crew else []
        
    director = None
    for person in crew:
        p_name = person.get('name') if isinstance(person, dict) else getattr(person, 'name', None)
        p_job = person.get('job') if isinstance(person, dict) else getattr(person, 'job', None)
        if p_job == 'Director':
            director = p_name
            break

    # Extract and force conversion to a standard Python list
    raw_cast = credits_data.get('cast', []) if hasattr(credits_data, 'get') else getattr(credits_data, 'cast', [])
    cast = list(raw_cast) if raw_cast else []

    top_cast = []
    for actor in cast[:5]:
        actor_name = actor.get('name') if isinstance(actor, dict) else getattr(actor, 'name', None)
        if actor_name:
            top_cast.append(actor_name)

    # 3. Videos / Trailer Extraction
    videos_data = getattr(show_detail, 'videos', None) or show_detail.get('videos', {})
    raw_results = videos_data.get('results', []) if hasattr(videos_data, 'get') else getattr(videos_data, 'results', [])
    results = list(raw_results) if raw_results else []

    trailer_key = None
    for v in results:
        v_type = v.get('type') if isinstance(v, dict) else getattr(v, 'type', None)
        v_site = v.get('site') if isinstance(v, dict) else getattr(v, 'site', None)
        v_key = v.get('key') if isinstance(v, dict) else getattr(v, 'key', None)
        if v_type == 'Trailer' and v_site == 'YouTube':
            trailer_key = v_key
            break
            
    trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None

    return {
        "results": {
            "id": show_detail.id,
            "title": show_detail.name,
            "year": show_detail.first_air_date[:4] if show_detail.first_air_date else None,
            "rating": show_detail.vote_average if show_detail.vote_average else None,
            "genres": [genre['name'] for genre in show_detail.genres] if show_detail.genres else [],
            "runtime": getattr(show_detail, 'runtime', None),
            "description": show_detail.overview,
            "director": director,
            "cast": top_cast,
            "trailer_url": trailer_url,
            "first_air_date": show_detail.first_air_date,
            "poster": base_image_url + show_detail.poster_path if show_detail.poster_path else None,
            "backdrop_pic": base_image_url + show_detail.backdrop_path if show_detail.backdrop_path else None,
            "watch_providers": {
                "stream": [p.get('provider_name') for p in us_providers.get('flatrate', [])],
                "rent": [p.get('provider_name') for p in us_providers.get('rent', [])],
                "buy": [p.get('provider_name') for p in us_providers.get('buy', [])]
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
