from tmdbv3api import TMDb, Movie, TV, Person, Discover, Genre
from dotenv import load_dotenv
import os
import json

load_dotenv()

tmdb_api = os.getenv('API_Key')
tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

# trending = Trending()
movie_api = Movie()
show_api = TV()
discover = Discover()
genre_api = Genre()

def obj_to_dict(obj):
  """Recursively converts custom AsObj objects, lists, and dicts into standard Python dictionaries."""
  if hasattr(obj, '__dict__'):
    return {k: obj_to_dict(v) for k, v in obj.__dict__.items()}
  elif isinstance(obj, list):
    return [obj_to_dict(item) for item in obj]
  elif isinstance(obj, dict):
    return {k: obj_to_dict(v) for k, v in obj.items()}
  else:
    return obj


def get_full_show(id):
  show_detail = show_api.details(
      id, append_to_response='watch/providers,credits,videos'
  )

  # Convert the custom AsObj structure into a regular dictionary
  show_dict = obj_to_dict(show_detail)

  # Define a dynamic filename using the show ID
  filename = f'show_{id}.json'

  # Save the dictionary to a JSON file
  with open(filename, 'w', encoding='utf-8') as f:
    json.dump(show_dict, f, ensure_ascii=False, indent=4)

  print(f'Successfully saved show details to {filename}')
  return show_detail

def get_full_movie(id):
    movie_detail = movie_api.details(id, append_to_response='watch/providers,credits,videos')

    movie_dict = obj_to_dict(movie_detail)

    filename = f'movie_{id}.json'

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(movie_dict, f, ensure_ascii=False, indent=4)

    print(f'Successfully saved movie details to {filename}')
    return movie_detail

get_full_show(133903)

get_full_movie(414906)