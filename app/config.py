from dotenv import load_dotenv
import os

load_dotenv()

tmdb_api = os.getenv('API_Key')
base_image_url = "https://image.tmdb.org/t/p/w500"