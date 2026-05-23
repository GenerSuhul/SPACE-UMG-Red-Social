# backend/app/api/notifications/service.py
from .repository import NotificationRepository
from backend.app.api.users.repository import UserRepository
import re

class NotificationService:

    @staticmethod
    def list_notifications(user_id: str, limit: int = 20) -> dict:
        notifications = NotificationRepository.list_by_user(user_id, limit=limit)
        return {"ok": True, "notifications": notifications}

    @staticmethod
    def mark_all_read(user_id: str) -> dict:
        NotificationRepository.mark_all_as_read(user_id)
        return {"ok": True}

    @staticmethod
    def trigger_follow(sender_id: str, receiver_id: str) -> None:
        if str(sender_id) == str(receiver_id):
            return
        sender = UserRepository.find_by_id(sender_id)
        if not sender:
            return
        
        username = sender.get("username", "Un usuario")
        data = {
            "user_id": str(receiver_id),
            "sender_id": str(sender_id),
            "sender_username": username,
            "type": "follow",
            "text": f"@{username} comenzó a seguirte."
        }
        NotificationRepository.create(data)

    @staticmethod
    def trigger_like(sender_id: str, receiver_id: str, post_id: str) -> None:
        if str(sender_id) == str(receiver_id):
            return
        sender = UserRepository.find_by_id(sender_id)
        if not sender:
            return
        
        username = sender.get("username", "Un usuario")
        data = {
            "user_id": str(receiver_id),
            "sender_id": str(sender_id),
            "sender_username": username,
            "type": "like",
            "post_id": str(post_id),
            "text": f"A @{username} le gustó tu publicación."
        }
        NotificationRepository.create(data)

    @staticmethod
    def trigger_share(sender_id: str, receiver_id: str, post_id: str) -> None:
        if str(sender_id) == str(receiver_id):
            return
        sender = UserRepository.find_by_id(sender_id)
        if not sender:
            return
        
        username = sender.get("username", "Un usuario")
        data = {
            "user_id": str(receiver_id),
            "sender_id": str(sender_id),
            "sender_username": username,
            "type": "share",
            "post_id": str(post_id),
            "text": f"@{username} compartió tu publicación."
        }
        NotificationRepository.create(data)

    @staticmethod
    def trigger_comment(sender_id: str, receiver_id: str, post_id: str, comment_text: str) -> None:
        if str(sender_id) == str(receiver_id):
            return
        sender = UserRepository.find_by_id(sender_id)
        if not sender:
            return
        
        username = sender.get("username", "Un usuario")
        short_text = comment_text[:30] + "..." if len(comment_text) > 30 else comment_text
        data = {
            "user_id": str(receiver_id),
            "sender_id": str(sender_id),
            "sender_username": username,
            "type": "comment",
            "post_id": str(post_id),
            "text": f"@{username} comentó en tu publicación: \"{short_text}\""
        }
        NotificationRepository.create(data)

    @staticmethod
    def trigger_mentions(sender_id: str, text: str, post_id: str) -> None:
        """Busca menciones con formato @username en el texto y notifica a los usuarios mencionados."""
        sender = UserRepository.find_by_id(sender_id)
        if not sender:
            return
        
        sender_username = sender.get("username", "")
        # Encontrar palabras que inician con @
        usernames = re.findall(r"@([a-zA-Z0-9_]+)", text)
        
        # Eliminar duplicados y el propio emisor
        usernames = list(set(usernames))
        if sender_username in usernames:
            usernames.remove(sender_username)
            
        for username in usernames:
            user = UserRepository.find_by_username(username.lower())
            if user:
                data = {
                    "user_id": str(user["_id"]),
                    "sender_id": str(sender_id),
                    "sender_username": sender_username,
                    "type": "mention",
                    "post_id": str(post_id),
                    "text": f"@{sender_username} te mencionó en una publicación."
                }
                NotificationRepository.create(data)
