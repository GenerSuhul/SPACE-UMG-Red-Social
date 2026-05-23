# backend/app/api/chats/repository.py
from bson import ObjectId
from datetime import datetime, timezone
from backend.app.extensions import mongo

class ChatRepository:

    @staticmethod
    def find_chat_by_participants(participants: list[str]) -> dict | None:
        """Busca un chat que contenga exactamente los participantes especificados."""
        oids = [ObjectId(p) for p in participants]
        # Buscar chat que tenga exactamente estos dos participantes
        return mongo.db.chats.find_one({
            "participants": {"$all": oids, "$size": len(oids)}
        })

    @staticmethod
    def create_chat(participants: list[str]) -> str:
        """Crea un nuevo hilo de chat entre participantes."""
        oids = [ObjectId(p) for p in participants]
        doc = {
            "participants": oids,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_message": None
        }
        res = mongo.db.chats.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def find_chat_by_id(chat_id: str) -> dict | None:
        return mongo.db.chats.find_one({"_id": ObjectId(chat_id)})

    @staticmethod
    def list_chats_by_user(user_id: str) -> list[dict]:
        """Obtiene todos los chats en los que participa el usuario, ordenados por updated_at descendente."""
        return list(mongo.db.chats.find({
            "participants": ObjectId(user_id)
        }).sort("updated_at", -1))

    @staticmethod
    def update_chat_last_message(chat_id: str, message: dict) -> None:
        """Actualiza el último mensaje y la fecha de actualización de un chat."""
        mongo.db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$set": {
                    "updated_at": message["created_at"],
                    "last_message": {
                        "id": str(message["_id"]),
                        "sender_id": str(message["sender_id"]),
                        "content": message["content"] or "[Archivo adjunto]",
                        "media_url": message.get("media_url"),
                        "media_type": message.get("media_type"),
                        "created_at": message["created_at"]
                    }
                }
            }
        )

    @staticmethod
    def insert_message(chat_id: str, sender_id: str, content: str, media_url: str = None, media_type: str = None) -> dict:
        """Inserta un nuevo mensaje en el chat."""
        doc = {
            "chat_id": ObjectId(chat_id),
            "sender_id": ObjectId(sender_id),
            "content": content,
            "is_read": False,
            "media_url": media_url,
            "media_type": media_type,
            "created_at": datetime.now(timezone.utc)
        }
        res = mongo.db.messages.insert_one(doc)
        doc["_id"] = res.inserted_id
        
        # Actualizar chat principal
        ChatRepository.update_chat_last_message(chat_id, doc)
        return doc

    @staticmethod
    def list_messages(chat_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
        """Obtiene la lista de mensajes de un chat ordenados por fecha ascendente."""
        return list(mongo.db.messages.find({
            "chat_id": ObjectId(chat_id)
        }).sort("created_at", 1).skip(skip).limit(limit))

    @staticmethod
    def mark_messages_as_read(chat_id: str, reader_id: str) -> int:
        """Marca todos los mensajes recibidos por reader_id en este chat como leídos."""
        res = mongo.db.messages.update_many(
            {
                "chat_id": ObjectId(chat_id),
                "sender_id": {"$ne": ObjectId(reader_id)},
                "is_read": False
            },
            {
                "$set": {"is_read": True}
            }
        )
        return res.modified_count
