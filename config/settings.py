import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

