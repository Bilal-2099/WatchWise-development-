from tmdbv3api import TMDb, Movie, TV, Person, Discover, Genre
from dotenv import load_dotenv
import os

load_dotenv()

tmdb_api = os.getenv('API_Key')
tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

# trending = Trending()
movie = Movie()
show = TV()
discover = Discover()
genre_api = Genre()


import requests

def get_content_by_platform(media_type: str, provider_id: int, api_key: str, region: str = "US"):
    """
    Fetches movies or TV shows available on a specific streaming platform.
    
    :param media_type: 'movie' or 'tv'
    :param provider_id: TMDB provider ID (e.g., 8 for Netflix, 9 for Amazon Prime, 337 for Disney+)
    :param api_key: Your TMDB API key
    :param region: Country code for availability (ISO 3166-1)
    :return: List of dictionaries containing title and release info
    """
    if media_type not in ["movie", "tv"]:
        raise ValueError("media_type must be either 'movie' or 'tv'")
        
    url = f"https://api.themoviedb.org/3/discover/{media_type}"
    
    headers = {
        "accept": "application/json"
    }
    
    params = {
        "api_key": api_key,
        "with_watch_providers": provider_id,
        "watch_region": region,
        "sort_by": "popularity.desc"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return []
        
    data = response.json()
    results = data.get("results", [])
    
    formatted_results = []
    for item in results:
        formatted_results.append({
            "id": item.get("id"),
            "title": item.get("title") if media_type == "movie" else item.get("name"),
            "release_date": item.get("release_date") if media_type == "movie" else item.get("first_air_date"),
            "vote_average": item.get("vote_average"),
            "poster_path": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None
        })
        
    return formatted_results

# --- Example Usage ---
if __name__ == "__main__":
    API_KEY = "YOUR_TMDB_API_KEY"
    
    # Provider mapping dictionary
    platforms = {
        "Netflix": 8,
        "Amazon Prime Video": 9,
        "Disney Plus": 337
    }
    
    # Fetching popular movies on Netflix in the US
    print("--- Popular Movies on Netflix ---")
    netflix_movies = get_content_by_platform("movie", platforms["Netflix"], API_KEY)
    for movie in netflix_movies[:5]: # Print top 5
        print(f"- {movie['title']} (Rating: {movie['vote_average']})")