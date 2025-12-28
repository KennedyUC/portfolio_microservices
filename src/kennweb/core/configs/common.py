from starlette.config import Config

config = Config(".env")

PROJECT_TITLE     = config("PROJECT_TITLE", cast=str)
APP_VERSION       = config("APP_VERSION", cast=str)
ENV               = config("ENV", cast=str)
ALLOWED_ORIGINS   = config("ALLOWED_ORIGINS", cast=list)