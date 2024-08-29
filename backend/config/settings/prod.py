from .base import *
import os
import dj_database_url
from dotenv import load_dotenv
load_dotenv()


DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': dj_database_url.config(
        default = os.getenv('DATABASE_URL')
    )
}
