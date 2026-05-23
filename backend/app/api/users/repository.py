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
                {"username": 1, "avatar_base64": 1, "avatar_mime": 1, "avatar_url": 1},
            )
            return {
                str(u["_id"]): {
                    "username":      u.get("username", ""),
                    # OPTIMIZATION: If avatar_url exists, omit transferring the heavy base64 avatar
                    "avatar_base64": None if u.get("avatar_url") else u.get("avatar_base64"),
                    "avatar_mime":   u.get("avatar_mime"),
                    "avatar_url":    u.get("avatar_url"),
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
                 "avatar_base64": 1, "avatar_mime": 1, "avatar_url": 1},
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

    @staticmethod
    def update_online_status(user_id: str, status: str) -> None:
        try:
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"online_status": status, "last_seen": datetime.now(timezone.utc)}}
            )
        except Exception as ex:
            print(f"Error updating online status: {ex}")

    @staticmethod
    def get_friend_recommendations(user_id: str, limit: int = 5) -> list[dict]:
        try:
            current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not current_user:
                return []
            
            already_following = [f["id"] for f in current_user.get("following", []) or []]
            already_following.append(str(current_user["_id"]))
            
            pipeline = [
                {"$match": {"_id": ObjectId(user_id)}},
                {"$unwind": "$following"},
                {"$lookup": {
                    "from": "users",
                    "let": {"followed_id": "$following.id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$followed_id"}]}}}
                    ],
                    "as": "friend_doc"
                }},
                {"$unwind": "$friend_doc"},
                {"$unwind": "$friend_doc.following"},
                {"$group": {
                    "_id": "$friend_doc.following.id",
                    "mutual_count": {"$sum": 1}
                }},
                {"$match": {"_id": {"$nin": already_following}}},
                {"$sort": {"mutual_count": -1}},
                {"$limit": limit},
                {"$lookup": {
                    "from": "users",
                    "let": {"rec_id": "$_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$rec_id"}]}}}
                    ],
                    "as": "user_info"
                }},
                {"$unwind": "$user_info"},
                {"$project": {
                    "id": {"$toString": "$user_info._id"},
                    "username": "$user_info.username",
                    "first_name": "$user_info.first_name",
                    "last_name": "$user_info.last_name",
                    "avatar_base64": "$user_info.avatar_base64",
                    "avatar_mime": "$user_info.avatar_mime",
                    "mutual_count": 1
                }}
            ]
            
            recs = list(mongo.db.users.aggregate(pipeline))
            
            if len(recs) < limit:
                needed = limit - len(recs)
                existing_ids = [r["id"] for r in recs] + already_following
                popular_cursor = mongo.db.users.find(
                    {"_id": {"$nin": [ObjectId(eid) for eid in existing_ids if ObjectId.is_valid(eid)]}},
                    {"username": 1, "first_name": 1, "last_name": 1, "avatar_base64": 1, "avatar_mime": 1}
                ).limit(needed)
                for u in popular_cursor:
                    recs.append({
                        "id": str(u["_id"]),
                        "username": u.get("username", ""),
                        "first_name": u.get("first_name", ""),
                        "last_name": u.get("last_name", ""),
                        "avatar_base64": u.get("avatar_base64"),
                        "avatar_mime": u.get("avatar_mime"),
                        "mutual_count": 0
                    })
            return recs
        except Exception as ex:
            print(f"Error getting recommendations: {ex}")
            try:
                current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
                already_following = [f["id"] for f in (current_user.get("following", []) or [])]
                already_following.append(str(user_id))
                oids = []
                for eid in already_following:
                    try:
                        oids.append(ObjectId(eid))
                    except:
                        pass
                popular = mongo.db.users.find(
                    {"_id": {"$nin": oids}},
                    {"username": 1, "first_name": 1, "last_name": 1, "avatar_base64": 1, "avatar_mime": 1}
                ).limit(limit)
                return [{
                    "id": str(u["_id"]),
                    "username": u.get("username", ""),
                    "first_name": u.get("first_name", ""),
                    "last_name": u.get("last_name", ""),
                    "avatar_base64": u.get("avatar_base64"),
                    "avatar_mime": u.get("avatar_mime"),
                    "mutual_count": 0
                } for u in popular]
            except Exception as inner_ex:
                print(f"Error in backup recommendations: {inner_ex}")
                return []