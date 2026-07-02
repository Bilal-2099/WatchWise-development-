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

def get_movie_genres():
    # Returns a list of genres like [{"id": 28, "name": "Action"}, ...]
    return genre_api.movie_list()

print(get_movie_genres())