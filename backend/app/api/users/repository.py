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
    def update_by_id(user_id: str, update_fields: dict) -> dict | None:
        """
        Actualiza solo los campos enviados (update parcial).
        Retorna el documento actualizado o None si no se encontró el usuario
        o si ocurrió un error de Mongo.
        """
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