from tmdbv3api import TMDb, Movie, TV, Discover
from dotenv import load_dotenv
import os

load_dotenv()
tmdb_api = os.getenv('API_Key')
base_image_url = os.getenv('base_tmdb_image_url')

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
movie_api = Movie()
show_api = TV()
discover = Discover()

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

# print("Print movie detail")
# print("------------------")
# print(get_movie(414906))

print("Print show detail")
print("------------------")
print(get_show(61889))

# import json

# class CustomEncoder(json.JSONEncoder):
#     def default(self, obj):
#         # Check if the object has a __dict__ attribute (meaning it's a custom class instance)
#         if hasattr(obj, '__dict__'):
#             return obj.__dict__
#         # Fallback for standard types
#         return super().default(obj)

# def get_all_movie(id):
#     movie_detail = movie_api.details(id)
#     with open("output.txt", "w") as file:
#         json.dump(movie_detail, file, cls=CustomEncoder, indent=4)
#     # print(movie_detail)

# get_all_movie(299534)