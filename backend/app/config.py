# app/config.py
import os
from dataclasses import dataclass, field
from datetime import timedelta

@dataclass
class BaseConfig:
    _username_db: str   = os.getenv("MONGO_DB_USERNAME", "default_user")
    _password_db: str   = os.getenv("MONGO_DB_PASSWORD", "default_pass")
    _name_db: str       = os.getenv("MONGO_DB_NAME", "default_db")
    _host_db: str       = os.getenv("MONGO_DB_HOST", "localhost")
    _port_db: str       = os.getenv("MONGO_DB_PORT", "27017")
    MONGO_URI: str      = f"mongodb://{_username_db}:{_password_db}@{_host_db}:{_port_db}/{_name_db}?authSource=admin"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")

    # Token válido 24 h. El logout lo invalida antes de tiempo via blocklist
    # (callback token_in_blocklist_loader registrado en app/__init__.py).
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=24)

    DEBUG: bool = False
    TESTING: bool = False

    # @classmethod
    # def vermongo(cls):
    #     print(f"MONGO_URI: {cls.MONGO_URI}")
    #     return cls.MONGO_URI

@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool         = True
    CORS_ORIGINS: list  = field(default_factory=lambda: ["http://localhost:4200"])

@dataclass
class ProductionConfig(BaseConfig):
    MONGO_URI: str      = os.getenv("MONGO_URI", None)
    CORS_ORIGINS: list  = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("CORS_WHITE_LIST", "").split(",")
        if origin.strip()
    ])

@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool       = True
    MONGO_URI: str      = "mongodb://localhost:27017/test_db"
    CORS_ORIGINS: list  = field(default_factory=lambda: ["http://localhost:4200"])

config_by_name: dict[str, type] = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}