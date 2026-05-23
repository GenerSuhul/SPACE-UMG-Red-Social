# app/config.py
import os
from dataclasses import dataclass, field
from datetime import timedelta


def _build_mongo_uri() -> str:
    uri_env = os.getenv("MONGO_URI")
    if uri_env:
        return uri_env

    username = os.getenv("MONGO_DB_USERNAME", "default_user")
    password = os.getenv("MONGO_DB_PASSWORD", "default_pass")
    name     = os.getenv("MONGO_DB_NAME",     "default_db")
    host     = os.getenv("MONGO_DB_HOST",     "localhost")
    port     = os.getenv("MONGO_DB_PORT",     "27017")
    return f"mongodb://{username}:{password}@{host}:{port}/{name}?authSource=admin"

@dataclass
class BaseConfig:
    MONGO_URI: str      = field(default_factory=_build_mongo_uri)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")

    # Token válido 24 h. El logout lo invalida antes de tiempo via blocklist
    # (callback token_in_blocklist_loader registrado en app/__init__.py).
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=24)

    DEBUG: bool = False
    TESTING: bool = False

    # Cota superior del body — aumentado para permitir reels de hasta 100MB
    MAX_CONTENT_LENGTH: int = 110 * 1024 * 1024

@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool         = True
    CORS_ORIGINS: list  = field(default_factory=lambda: ["http://localhost:4200", "https://space.umg.kyrosoftgs.com"])

@dataclass
class ProductionConfig(BaseConfig):
    # MONGO_URI lo hereda de BaseConfig (vía _build_mongo_uri).
    # En producción se asume que MONGO_URI viene del entorno (Atlas).
    CORS_ORIGINS: list  = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("CORS_WHITE_LIST", "http://localhost:4200,https://space.umg.kyrosoftgs.com").split(",")
        if origin.strip()
    ])

@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool       = True
    MONGO_URI: str      = "mongodb://localhost:27017/test_db"
    CORS_ORIGINS: list  = field(default_factory=lambda: ["http://localhost:4200", "https://space.umg.kyrosoftgs.com"])

config_by_name: dict[str, object] = {
    "development": DevelopmentConfig(),
    "production":  ProductionConfig(),
    "testing":     TestingConfig(),
}