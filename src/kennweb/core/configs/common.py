from starlette.config import Config
from starlette.datastructures import Secret
from databases import DatabaseURL

config = Config(".env")

PROJECT_TITLE     = config("PROJECT_TITLE", cast=str)
APP_VERSION       = config("APP_VERSION", cast=str)
ENV               = config("ENV", cast=str)
ALLOWED_ORIGINS   = config("ALLOWED_ORIGINS", cast=list)

POSTGRES_USER       = "db" if ENV == "local" else config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD   = "db" if ENV == "local" else config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER     = "localhost" if ENV == "local" else config("POSTGRES_SERVER", cast=str)
POSTGRES_PORT       = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB         = "db" if ENV == "local" else config("POSTGRES_DB", cast=str)

if ENV == "local":
    postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    postgres_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=require"

DATABASE_URL = config(
    "DATABASE_URL",
    cast=DatabaseURL,
    default=postgres_url
)