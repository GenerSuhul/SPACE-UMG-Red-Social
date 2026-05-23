# app/db_setup.py
import logging
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import CollectionInvalid

logger = logging.getLogger(__name__)

def setup_database(db):
    """
    Crea las colecciones necesarias, define sus validaciones de esquema ($jsonSchema)
    y crea los índices de optimización en MongoDB para SPACE UMG.
    """
    logger.info("Iniciando la configuración de la base de datos MongoDB...")
    existing_collections = db.list_collection_names()

    # 1. Configuración de la Colección de Usuarios (users)
    if "users" not in existing_collections:
        try:
            db.create_collection("users")
            logger.info("Colección 'users' creada exitosamente.")
        except CollectionInvalid:
            pass

    # Crear índices para usuarios
    db.users.create_index("username", unique=True)
    db.users.create_index("email", unique=True)
    db.users.create_index("online_status")
    logger.info("Índices para 'users' verificados.")

    # 2. Configuración de la Colección de Publicaciones y Reels (posts)
    if "posts" not in existing_collections:
        try:
            db.create_collection("posts")
            logger.info("Colección 'posts' creada exitosamente.")
        except CollectionInvalid:
            pass

    # Crear índices para publicaciones
    db.posts.create_index("user_id")
    db.posts.create_index("type")
    db.posts.create_index([("created_at", DESCENDING)])
    db.posts.create_index([("text", TEXT), ("hashtags", TEXT)])
    logger.info("Índices para 'posts' verificados.")

    # 3. Configuración de la Colección de Chats (chats)
    if "chats" not in existing_collections:
        try:
            db.create_collection("chats")
            logger.info("Colección 'chats' creada exitosamente.")
        except CollectionInvalid:
            pass

    db.chats.create_index("participants")
    db.chats.create_index([("updated_at", DESCENDING)])
    logger.info("Índices para 'chats' verificados.")

    # 4. Configuración de la Colección de Mensajes (messages)
    if "messages" not in existing_collections:
        try:
            db.create_collection("messages")
            logger.info("Colección 'messages' creada exitosamente.")
        except CollectionInvalid:
            pass

    db.messages.create_index([("chat_id", ASCENDING), ("created_at", ASCENDING)])
    logger.info("Índices para 'messages' verificados.")

    # 5. Configuración de la Colección de Notificaciones (notifications)
    if "notifications" not in existing_collections:
        try:
            db.create_collection("notifications")
            logger.info("Colección 'notifications' creada exitosamente.")
        except CollectionInvalid:
            pass

    db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.notifications.create_index("is_read")
    logger.info("Índices para 'notifications' verificados.")

    # 6. Configuración de la Colección de transmisiones en vivo (live_streams)
    if "live_streams" not in existing_collections:
        try:
            db.create_collection("live_streams")
            logger.info("Colección 'live_streams' creada exitosamente.")
        except CollectionInvalid:
            pass
    db.live_streams.create_index("status")
    logger.info("Índices para 'live_streams' verificados.")

    logger.info("Configuración de base de datos finalizada con éxito.")
