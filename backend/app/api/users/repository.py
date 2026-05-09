from backend.app.extensions import mongo
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import ReturnDocument

class UserRepository:

    @staticmethod
    def find_by_id(user_id) -> dict | None:
        try:
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as ex:
            print(f"Error finding user by id: {ex}")
            return None

    @staticmethod
    def find_by_username(username: str) -> dict | None:
        try:
            return mongo.db.users.find_one({"username": username})
        except Exception as ex:
            print(f"Error finding user by username: {ex}")
            return None

    @staticmethod
    def find_by_email(email: str) -> dict | None:
        try:
            return mongo.db.users.find_one({"email": email})
        except Exception as ex:
            print(f"Error finding user by email: {ex}")
            return None

    @staticmethod
    def find_many_usernames(user_ids: list) -> dict:
        try:
            oids = [ObjectId(uid) for uid in user_ids]
            cursor = mongo.db.users.find(
                {"_id": {"$in": oids}},
                {"username": 1, "avatar_base64": 1, "avatar_mime": 1},
            )
            return {
                str(u["_id"]): {
                    "username":      u.get("username", ""),
                    "avatar_base64": u.get("avatar_base64"),
                    "avatar_mime":   u.get("avatar_mime"),
                }
                for u in cursor
            }
        except Exception as ex:
            print(f"Error finding usernames by ids: {ex}")
            return {}

    @staticmethod
    def search_by_username(query: str, limit: int = 20) -> list[dict]:
        try:
            cursor = mongo.db.users.find(
                {"username": {"$regex": query, "$options": "i"}},
                {"username": 1, "first_name": 1, "last_name": 1, "age": 1,
                 "avatar_base64": 1, "avatar_mime": 1},
            ).limit(limit)
            return list(cursor)
        except Exception as ex:
            print(f"Error searching users by username: {ex}")
            return []

    @staticmethod
    def update_by_id(user_id: str, update_fields: dict) -> dict | None:
        if not update_fields:
            return None
        try:
            update_fields = {**update_fields, "updated_at": datetime.now(timezone.utc)}
            updated_user = mongo.db.users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields},
                return_document=ReturnDocument.AFTER,
            )
            return updated_user
        except Exception as ex:
            print(f"Error updating user by id: {ex}")
            return None

    @staticmethod
    def is_following(current_user_id: str, target_user_id: str) -> bool:
        try:
            doc = mongo.db.users.find_one(
                {
                    "_id": ObjectId(current_user_id),
                    "following.id": target_user_id,
                },
                {"_id": 1},
            )
            return doc is not None
        except Exception as ex:
            print(f"Error checking is_following: {ex}")
            return False

    @staticmethod
    def add_follow(
        current_user_id: str,
        current_user_info: dict,
        target_user_id: str,
        target_user_info: dict,
    ) -> bool:
        try:
            res_current = mongo.db.users.update_one(
                {"_id": ObjectId(current_user_id)},
                {
                    "$push": {"following": target_user_info},
                    "$set":  {"updated_at": datetime.now(timezone.utc)},
                },
            )
            res_target = mongo.db.users.update_one(
                {"_id": ObjectId(target_user_id)},
                {
                    "$push": {"followers": current_user_info},
                    "$set":  {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return res_current.matched_count > 0 and res_target.matched_count > 0
        except Exception as ex:
            print(f"Error adding follow: {ex}")
            return False

    @staticmethod
    def remove_follow(current_user_id: str, target_user_id: str) -> bool:
        try:
            res_current = mongo.db.users.update_one(
                {"_id": ObjectId(current_user_id)},
                {
                    "$pull": {"following": {"id": target_user_id}},
                    "$set":  {"updated_at": datetime.now(timezone.utc)},
                },
            )
            res_target = mongo.db.users.update_one(
                {"_id": ObjectId(target_user_id)},
                {
                    "$pull": {"followers": {"id": current_user_id}},
                    "$set":  {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return res_current.matched_count > 0 and res_target.matched_count > 0
        except Exception as ex:
            print(f"Error removing follow: {ex}")
            return False

    @staticmethod
    def get_follow_lists(user_id: str) -> dict | None:
        try:
            doc = mongo.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"followers": 1, "following": 1},
            )
            if not doc:
                return None
            return {
                "followers": doc.get("followers", []) or [],
                "following": doc.get("following", []) or [],
            }
        except Exception as ex:
            print(f"Error getting follow lists: {ex}")
            return None

    @staticmethod
    def get_follow_counts(user_id: str) -> dict:
        try:
            doc = mongo.db.users.find_one(
                {"_id": ObjectId(user_id)},
                {"followers": 1, "following": 1},
            )
            if not doc:
                return {"followers_count": 0, "following_count": 0}
            return {
                "followers_count": len(doc.get("followers", []) or []),
                "following_count": len(doc.get("following", []) or []),
            }
        except Exception as ex:
            print(f"Error getting follow counts: {ex}")
            return {"followers_count": 0, "following_count": 0}