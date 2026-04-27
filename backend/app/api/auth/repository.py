from backend.app.extensions import mongo
from datetime import datetime, timezone

class AuthRepository:

    @staticmethod
    def find_by_username(username: str) -> dict | None:
        try:
            user = mongo.db.users.find_one({"username": username})
            return user
        except Exception as e:
            print(f"Error finding user by username: {e}")
            return None
    
    @staticmethod
    def insert_user(user_data: dict) -> str:

        user_data["created_at"] = datetime.now(timezone.utc)
        try:
            result = mongo.db.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting user: {e}")
            return None