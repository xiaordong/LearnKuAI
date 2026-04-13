import os

import dotenv
dotenv.load_dotenv()
API_KEY = os.getenv("ZHIPU_API_KEY")
BASE_URL = os.getenv("ZHIPU_URL")
MODEL = os.getenv("MODEL")
