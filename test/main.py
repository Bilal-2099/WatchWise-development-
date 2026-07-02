
from tmdbv3api import TMDb, Movie, TV, Person, Discover
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

def popular_movies(limit=20):
    popular_movies = movie.popular()

    popular_movies = list(popular_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": movie["id"],
            "title": movie["title"],
            "raing": movie["vote_average"],
            "poster": base_image_url + movie["poster_path"] if movie["poster_path"] else None,
        }
        for movie in popular_movies
    ]
    }


popular_shows = show.popular()
popular_shows = list(popular_shows["results"])[:1]
for show in popular_shows:
    print(show)

# print(popular_movies(1))