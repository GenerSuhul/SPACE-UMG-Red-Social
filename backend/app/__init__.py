# app/__init__.py
from flask import Flask
from .config import config_by_name
from .extensions import mongo, jwt, swagger

# Configuración base del Swagger UI
SWAGGER_CONFIG = {
    "title": "Swagger Flask Api Doc, Red Social APIs",
    "version": "1.0.0",
    "description": "Backend para red social de proyecto final, python y mongodb",
    "uiversion": 3,
    "openapi": "3.0.2",
    "specs_route": "/docs/",
}

def create_app(config_name: str = "development") -> Flask:
    """
    Factory pattern: permite crear múltiples instancias de la app
    (ej. una para tests con config aislada, otra para producción).
    Evita el problema del circular import que ocurre con app global.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    app.config['SWAGGER'] = SWAGGER_CONFIG

    # 1. Inicializar extensiones con la app
    _init_extensions(app)

    # 2. Registrar blueprints (rutas)
    _register_blueprints(app)

    return app


def _init_extensions(app: Flask) -> None:
    """Separado para mantener create_app() legible."""
    mongo.init_app(app)
    jwt.init_app(app)
    swagger.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from .api.auth import auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")