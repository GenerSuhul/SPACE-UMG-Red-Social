# app/config.py
import os
from dataclasses import dataclass

@dataclass
class BaseConfig:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/mydb")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    DEBUG: bool = False
    TESTING: bool = False

@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True

@dataclass
class ProductionConfig(BaseConfig):
    # En prod, MONGO_URI debe venir SIEMPRE del entorno
    MONGO_URI: str = os.environ["MONGO_URI"]  # falla duro si no existe ✓

@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool = True
    MONGO_URI: str = "mongodb://localhost:27017/test_db"

config_by_name: dict[str, type] = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}