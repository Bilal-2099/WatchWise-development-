from tmdbv3api import Trending, TMDb
from dotenv import load_dotenv
import os

load_dotenv()

tmdb = TMDb()
tmdb.api_key = os.getenv('API_Key')
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

trending = Trending()

# For Trending Movie of the week
trending_movies = trending.movie_week()

movies = list(trending_movies["results"])

# print("---- Movies ----")
# for movie in movies[:1]:
#     print(movie)
    # print(f"ID: {movie['id']}")
    # print(f"Title: {movie['title']}")
    # print(f"Description: {movie['overview']}")
    # print(f"Poster: {base_image_url + movie['poster_path']}")

# For Trending Show of the Week
trending_shows = trending.tv_week()

shows = list(trending_shows["results"])

print("---- Shows ----")
for show in shows[:5]:
    print(show)
    # print(f"ID: {show['id']}")
    # print(f"Title: {show['name']}")
    # print(f"Description: {show['overview']}")
    # print(f"Poster: {base_image_url + show['poster_path']}")