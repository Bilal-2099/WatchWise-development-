from tmdbv3api import TMDb, Movie, TV, Person, Discover, Genre
from dotenv import load_dotenv
import os

load_dotenv()
discover = Discover()
genre_api = Genre()
tv = TV()
tmdb_api = os.getenv('API_Key')
tmdb = TMDb()
movie = Movie()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

def search_shows_by_platform(query, provider_id, limit=10, region="US"):

    search_results = show_api.search(query)
    
    # Filter search results to only include those matching the provider
    filtered_items = []
    for item in search_results:
        # Check providers using TMDB's movie details/watch providers or check 
        # if the item has the provider in its data if returned by the search wrapper.
        # Alternatively, using discover with a keyword search if supported:
        pass

    # A cleaner approach using discover filters with a search query:
    filters = {
        "query": query,
        "with_watch_providers": provider_id,
        "watch_region": region,
        "sort_by": "popularity.desc"
    }
    
    results = discover.discover_tv_shows(filters)
        
    items = list(results)[:limit]
    
    return {
        "results": [
            {
                "id": item["id"],
                "title": item["name"],
                "rating": item["vote_average"],
                "poster": base_image_url + item["poster_path"] if item["poster_path"] else None,
            }
            for item in items
        ]
    }