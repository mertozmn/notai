import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notai.db")