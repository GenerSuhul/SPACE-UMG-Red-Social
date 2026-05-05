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

    # ---- Blocklist de tokens JWT ----------------------------------------

    @staticmethod
    def revoke_token(jti: str, user_id: str | None = None) -> bool:
        """
        Inserta el JTI del token en la colección `token_blocklist`.
        Devuelve True si la inserción fue exitosa.
        """
        try:
            mongo.db.token_blocklist.insert_one({
                "jti":        jti,
                "user_id":    user_id,
                "revoked_at": datetime.now(timezone.utc),
            })
            return True
        except Exception as e:
            print(f"Error revoking token: {e}")
            return False

    @staticmethod
    def is_token_revoked(jti: str) -> bool:
        """
        True si el JTI existe en la blocklist.
        Usado por el callback `token_in_blocklist_loader`.
        """
        try:
            return mongo.db.token_blocklist.find_one({"jti": jti}) is not None
        except Exception as e:
            print(f"Error checking token blocklist: {e}")
            # Por seguridad: si la consulta falla, tratamos el token como revocado
            # para no permitir accesos sin verificación.
            return True