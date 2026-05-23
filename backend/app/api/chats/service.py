# backend/app/api/chats/service.py
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from .repository import ChatRepository
from backend.app.api.users.repository import UserRepository

_TZ_LOCAL = timezone(timedelta(hours=-6))

def _iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TZ_LOCAL).isoformat()

class ChatService:

    @staticmethod
    def _is_valid_object_id(value: str) -> bool:
        try:
            ObjectId(value)
            return True
        except (InvalidId, TypeError):
            return False

    @staticmethod
    def get_or_create_chat(user_id: str, other_user_id: str) -> dict:
        """Obtiene o crea un chat entre el usuario actual y otro usuario."""
        if not ChatService._is_valid_object_id(other_user_id):
            return {"ok": False, "errors": [{"field": "other_user_id", "message": "Id de usuario destino inválido"}]}
        
        # Verificar que el usuario destino existe
        other_user = UserRepository.find_by_id(other_user_id)
        if not other_user:
            return {"ok": False, "errors": [{"field": "other_user", "message": "El usuario destino no existe"}]}
        
        if str(user_id) == str(other_user_id):
            return {"ok": False, "errors": [{"field": "other_user_id", "message": "No puedes crear un chat contigo mismo"}]}

        chat = ChatRepository.find_chat_by_participants([user_id, other_user_id])
        if not chat:
            chat_id = ChatRepository.create_chat([user_id, other_user_id])
            chat = ChatRepository.find_chat_by_id(chat_id)

        # Serializar el chat con los datos del otro participante
        return {"ok": True, "chat": ChatService._serialize_chat(chat, user_id)}

    @staticmethod
    def list_my_chats(user_id: str) -> dict:
        """Lista todos los hilos de chat del usuario actual, con información del otro participante."""
        chats = ChatRepository.list_chats_by_user(user_id)
        serialized_chats = [ChatService._serialize_chat(c, user_id) for c in chats]
        return {"ok": True, "chats": serialized_chats}

    @staticmethod
    def send_message(chat_id: str, sender_id: str, content: str, media_url: str = None, media_type: str = None) -> dict:
        """Envía un mensaje a un chat."""
        if not ChatService._is_valid_object_id(chat_id):
            return {"ok": False, "errors": [{"field": "chat_id", "message": "Id de chat inválido"}]}
        
        content = (content or "").strip()
        if not content and not media_url:
            return {"ok": False, "errors": [{"field": "content", "message": "El mensaje no puede estar vacío"}]}
        
        chat = ChatRepository.find_chat_by_id(chat_id)
        if not chat:
            return {"ok": False, "errors": [{"field": "chat", "message": "Chat no encontrado"}]}
        
        # Verificar que el remitente es participante
        participants_ids = [str(p) for p in chat["participants"]]
        if str(sender_id) not in participants_ids:
            return {"ok": False, "errors": [{"field": "auth", "message": "No tienes acceso a este chat"}]}

        msg = ChatRepository.insert_message(chat_id, sender_id, content, media_url=media_url, media_type=media_type)
        return {"ok": True, "message": ChatService._serialize_message(msg)}

    @staticmethod
    def get_messages(chat_id: str, user_id: str, limit: int = 50, page: int = 1) -> dict:
        """Obtiene la lista de mensajes de un chat, paginados."""
        if not ChatService._is_valid_object_id(chat_id):
            return {"ok": False, "errors": [{"field": "chat_id", "message": "Id de chat inválido"}]}
        
        chat = ChatRepository.find_chat_by_id(chat_id)
        if not chat:
            return {"ok": False, "errors": [{"field": "chat", "message": "Chat no encontrado"}]}
        
        participants_ids = [str(p) for p in chat["participants"]]
        if str(user_id) not in participants_ids:
            return {"ok": False, "errors": [{"field": "auth", "message": "No tienes acceso a este chat"}]}

        page = max(1, page)
        limit = max(1, min(200, limit))
        skip = (page - 1) * limit

        messages = ChatRepository.list_messages(chat_id, limit=limit, skip=skip)
        return {
            "ok": True, 
            "messages": [ChatService._serialize_message(m) for m in messages]
        }

    @staticmethod
    def mark_chat_read(chat_id: str, user_id: str) -> dict:
        """Marca todos los mensajes del chat como leídos por el usuario actual."""
        if not ChatService._is_valid_object_id(chat_id):
            return {"ok": False, "errors": [{"field": "chat_id", "message": "Id de chat inválido"}]}
        
        chat = ChatRepository.find_chat_by_id(chat_id)
        if not chat:
            return {"ok": False, "errors": [{"field": "chat", "message": "Chat no encontrado"}]}
        
        participants_ids = [str(p) for p in chat["participants"]]
        if str(user_id) not in participants_ids:
            return {"ok": False, "errors": [{"field": "auth", "message": "No tienes acceso a este chat"}]}

        modified = ChatRepository.mark_messages_as_read(chat_id, user_id)
        return {"ok": True, "marked_count": modified}

    @staticmethod
    def _serialize_chat(chat: dict, current_user_id: str) -> dict:
        """Serializa la información del chat e incluye los datos del otro participante."""
        chat_id = str(chat["_id"])
        
        # Encontrar el otro participante
        other_user_id = next(
            (str(p) for p in chat["participants"] if str(p) != str(current_user_id)),
            None
        )
        
        other_user_data = {}
        if other_user_id:
            other_user = UserRepository.find_by_id(other_user_id)
            if other_user:
                other_user_data = {
                    "id": str(other_user["_id"]),
                    "username": other_user.get("username", ""),
                    "first_name": other_user.get("first_name", ""),
                    "last_name": other_user.get("last_name", ""),
                    "avatar_base64": other_user.get("avatar_base64"),
                    "avatar_mime": other_user.get("avatar_mime"),
                    "avatar_url": other_user.get("avatar_url"),
                    "online_status": other_user.get("online_status", "offline")
                }
        
        last_msg = chat.get("last_message")
        if last_msg:
            last_msg["created_at"] = _iso(last_msg["created_at"])
            
        return {
            "id": chat_id,
            "participants": [str(p) for p in chat["participants"]],
            "other_participant": other_user_data,
            "created_at": _iso(chat.get("created_at")),
            "updated_at": _iso(chat.get("updated_at")),
            "last_message": last_msg
        }

    @staticmethod
    def _serialize_message(msg: dict) -> dict:
        return {
            "id": str(msg["_id"]),
            "chat_id": str(msg["chat_id"]),
            "sender_id": str(msg["sender_id"]),
            "content": msg.get("content", ""),
            "is_read": msg.get("is_read", False),
            "media_url": msg.get("media_url"),
            "media_type": msg.get("media_type"),
            "created_at": _iso(msg.get("created_at"))
        }
