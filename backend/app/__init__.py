# app/__init__.py
from flask import Flask
from .config import config_by_name
from .extensions import mongo, jwt, swagger, cors

# Configuración base del Swagger UI
SWAGGER_CONFIG = {
    "title": "Swagger Flask Api Doc, Red Social APIs",
    "version": "1.0.0",
    "description": "Backend para red social de proyecto final, python y mongodb",
    "uiversion": 3,
    "swagger": "2.0",
    "specs_route": "/docs/",
    "consumes": ["application/json"],
    "produces": ["application/json"],

    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Formato: Bearer {token}"
        }
    }
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

    # Inicializar esquemas e índices en MongoDB dentro del contexto de Flask
    with app.app_context():
        from .db_setup import setup_database
        setup_database(mongo.db)

    cors.init_app(app, resources={
        r"/*": {
            "origins": app.config.get("CORS_ORIGINS", ["*",]),
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    _register_jwt_callbacks()


def _register_jwt_callbacks() -> None:
    """
    Registra los callbacks de flask-jwt-extended.
    Se llama en cada request — `mongo.db` ya está disponible vía
    el contexto de aplicación que provee Flask.
    """
    from .api.auth.repository import AuthRepository

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload) -> bool:
        """
        Devuelve True si el JTI del token está en la blocklist.
        flask-jwt-extended responderá 401 automáticamente en ese caso.
        """
        jti = jwt_payload["jti"]
        return AuthRepository.is_token_revoked(jti)


def _register_blueprints(app: Flask) -> None:
    from .api.auth import auth_bp
    from .api.users import user_bp
    from .api.posts import posts_bp
    from .api.notifications import notifications_bp
    from .api.chats import chats_bp
    from .api.lives import lives_bp
    from .api.upload_routes import upload_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(posts_bp, url_prefix="/api/posts")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(chats_bp, url_prefix="/api/chats")
    app.register_blueprint(lives_bp, url_prefix="/api/lives")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")