from tmdbv3api import TMDb, Movie, TV
from dotenv import load_dotenv
import os

load_dotenv()

tmdb = TMDb()
tmdb.api_key = os.getenv('API_Key')
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

# Use the Movie object to search
def search_movie(searches):
    movie = Movie()
    search_results = movie.search(searches)
    results = list(search_results)[:5]

    return {
        "results": [
        {
            "id": movie["id"],
            "title": movie["title"],
            "raing": movie["vote_average"],
            "poster": base_image_url + movie["poster_path"] if movie["poster_path"] else None
        }
        for movie in results
    ]
   }

# print(search_movie("batman"))

def search_show(searches):
    show = TV()
    search_results = show.search(searches)
    results = list(search_results)[:5]

    return {
        "results": [
        {
            "id": show["id"],
            "title": show["name"],
            "raing": show["vote_average"],
            "poster": base_image_url + show["poster_path"] if show["poster_path"] else None
        }
        for show in results
    ]
   }