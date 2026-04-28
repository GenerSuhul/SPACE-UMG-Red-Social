from backend.app.extensions import mongo
from bson import ObjectId
from datetime import datetime, timezone

class UserRepository:

    @staticmethod
    def find_by_id(user_id) -> dict | None:
        try:
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as ex:
            print(f"Error finding user by id: {ex}")
            return None