# app/config.py
import os
from dataclasses import dataclass, field

@dataclass
class BaseConfig:
    _username_db: str   = os.getenv("MONGO_DB_USERNAME", "default_user")
    _password_db: str   = os.getenv("MONGO_DB_PASSWORD", "default_pass")
    _name_db: str       = os.getenv("MONGO_DB_NAME", "default_db")
    _host_db: str       = os.getenv("MONGO_DB_HOST", "localhost")
    _port_db: str       = os.getenv("MONGO_DB_PORT", "27017")
    MONGO_URI: str      = f"mongodb://{_username_db}:{_password_db}@{_host_db}:{_port_db}/{_name_db}?authSource=admin"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    DEBUG: bool = False
    TESTING: bool = False

    # @classmethod
    # def vermongo(cls):
    #     print(f"MONGO_URI: {cls.MONGO_URI}")
    #     return cls.MONGO_URI

@dataclass
class DevelopmentConfig(BaseConfig):
    DEBUG: bool    = True

    # MONGO_URI: str = BaseConfig.vermongo()

@dataclass
class ProductionConfig(BaseConfig):
    MONGO_URI: str = os.getenv("MONGO_URI", None)
    # TODO cuando se despliegue agregar la url del frontent http://www.forntend.com

@dataclass
class TestingConfig(BaseConfig):
    TESTING: bool  = True
    MONGO_URI: str = "mongodb://localhost:27017/test_db"

config_by_name: dict[str, type] = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}