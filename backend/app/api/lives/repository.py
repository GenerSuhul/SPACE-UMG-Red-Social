# backend/app/api/lives/repository.py
from bson import ObjectId
from datetime import datetime, timezone
from backend.app.extensions import mongo
from pymongo import ReturnDocument

class LiveRepository:

    @staticmethod
    def create_stream(creator_id: str, title: str) -> dict:
        creator = mongo.db.users.find_one({"_id": ObjectId(creator_id)})
        username = creator.get("username", "Usuario UMG") if creator else "Usuario UMG"
        avatar_b64 = creator.get("avatar_base64") if creator else None
        avatar_mime = creator.get("avatar_mime") if creator else None
        
        doc = {
            "creator_id": ObjectId(creator_id),
            "creator_username": username,
            "creator_avatar_base64": avatar_b64,
            "creator_avatar_mime": avatar_mime,
            "title": title,
            "status": "live",
            "viewers_count": 1,
            "created_at": datetime.now(timezone.utc),
            "ended_at": None
        }
        res = mongo.db.live_streams.insert_one(doc)
        doc["_id"] = res.inserted_id
        return doc

    @staticmethod
    def find_stream_by_id(stream_id: str) -> dict | None:
        return mongo.db.live_streams.find_one({"_id": ObjectId(stream_id)})

    @staticmethod
    def list_active_streams() -> list[dict]:
        return list(mongo.db.live_streams.find({"status": "live"}).sort("created_at", -1))

    @staticmethod
    def end_stream(stream_id: str, creator_id: str) -> dict | None:
        return mongo.db.live_streams.find_one_and_update(
            {"_id": ObjectId(stream_id), "creator_id": ObjectId(creator_id)},
            {"$set": {"status": "ended", "ended_at": datetime.now(timezone.utc), "viewers_count": 0}},
            return_document=ReturnDocument.AFTER
        )

    @staticmethod
    def update_viewers(stream_id: str, viewers_delta: int) -> dict | None:
        # Asegurarse de que no baje de 0 viewers
        stream = LiveRepository.find_stream_by_id(stream_id)
        if not stream or stream.get("status") == "ended":
            return None
            
        current = stream.get("viewers_count", 0)
        new_count = max(0, current + viewers_delta)
        
        return mongo.db.live_streams.find_one_and_update(
            {"_id": ObjectId(stream_id), "status": "live"},
            {"$set": {"viewers_count": new_count}},
            return_document=ReturnDocument.AFTER
        )
