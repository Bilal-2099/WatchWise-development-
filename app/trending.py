from tmdbv3api import Trending, TMDb
from dotenv import load_dotenv
import os

load_dotenv()

tmdb = TMDb()
tmdb.api_key = os.getenv('API_Key')
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

trending = Trending()

def get_trending_movie(limit=20):
    trending_movies = trending.movie_week()

    movies = list(trending_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": movie["id"],
            "title": movie["title"],
            "description": movie["overview"],
            "raing": movie["vote_average"],
            "release_date": movie["release_date"],
            "poster": base_image_url + movie["poster_path"] if movie["poster_path"] else None,
            "backdrop_pic": base_image_url + movie["backdrop_path"] if movie["backdrop_path"] else None
        }
        for movie in movies
    ]
    }

# print(get_trending_movie(2))

def get_trending_show(limit=20):
    trending_shows = trending.tv_week()

    shows = list(trending_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": show["id"],
            "title": show["name"],
            "description": show["overview"],
            "poster": base_image_url + show["poster_path"] if show["poster_path"] else None,
        }
        for show in shows
    ]
    }
