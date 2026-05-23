# backend/app/api/notifications/repository.py
from backend.app.extensions import mongo
from bson import ObjectId
from datetime import datetime, timezone

class NotificationRepository:

    @staticmethod
    def create(data: dict) -> str | None:
        try:
            data = {
                **data,
                "created_at": datetime.now(timezone.utc),
                "is_read": False
            }
            res = mongo.db.notifications.insert_one(data)
            return str(res.inserted_id)
        except Exception as ex:
            print(f"Error creating notification: {ex}")
            return None

    @staticmethod
    def list_by_user(user_id: str, limit: int = 20) -> list[dict]:
        try:
            cursor = mongo.db.notifications.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)
            
            notifications = []
            for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                if "created_at" in doc and doc["created_at"]:
                    if isinstance(doc["created_at"], datetime):
                        doc["created_at"] = doc["created_at"].isoformat()
                notifications.append(doc)
            return notifications
        except Exception as ex:
            print(f"Error listing notifications: {ex}")
            return []

    @staticmethod
    def mark_all_as_read(user_id: str) -> bool:
        try:
            mongo.db.notifications.update_many(
                {"user_id": user_id, "is_read": False},
                {"$set": {"is_read": True}}
            )
            return True
        except Exception as ex:
            print(f"Error marking notifications as read: {ex}")
            return False
