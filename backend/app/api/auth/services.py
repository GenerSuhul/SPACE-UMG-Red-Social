import bcrypt
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from .schemas import UserRegisterSchema, UserLoginSchema
from .repository import AuthRepository

class AuthService:

    @staticmethod
    def register(data: dict) -> dict:
        # 1. Validación — Pydantic lanza ValidationError si algo falla
        try:
            validated = UserRegisterSchema(**data)
        except ValidationError as e:
            # Extraemos solo los mensajes limpios para la respuesta
            errors = [
                {"field": err["loc"][0], "message": err["msg"]}
                for err in e.errors()
            ]
            return {"ok": False, "errors": errors}

        # 2. Verificar duplicados
        exist_user = AuthRepository.find_by_username(validated.username)
        if exist_user:
            return {"ok": False, "errors": [{"field": "username", "message": "Username in use"}]}

        # 3. Encriptar contraseña con bcrypt
        # El salt_rounds=12 es el balance recomendado entre seguridad y rendimiento
        hashed_password = bcrypt.hashpw(
            validated.password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        )

        # 4. Construir documento para MongoDB
        user_doc = {
            "username":   validated.username,
            "email":      validated.email.lower(),
            "password":   hashed_password,
            "age":        validated.age,
            "first_name": validated.first_name,
            "last_name":  validated.last_name,
        }


        user_id = AuthRepository.insert_user(user_doc)
        if not user_id:
            return {"ok": False, "errors": [{"field": "database", "message": "Error saving user"}]}
        return {"ok": True, "user_id": user_id}


    @staticmethod
    def login(data: dict) -> dict:
        # 1. Validación básica de entrada
        try:
            validated = UserLoginSchema(**data)
        except ValidationError as e:
            errors = [
                {"field": err["loc"][0], "message": err["msg"]}
                for err in e.errors()
            ]
            return {"ok": False, "errors": errors}

        # 2. Buscar usuario
        user = AuthRepository.find_by_username(validated.username)
        if not user:
            # Mensaje genérico intencional — no revelar si el username existe
            return {"ok": False, "errors": [{"field": "credentials", "message": "Invalid Login"}]}

        # 3. Verificar contraseña
        password_matches = bcrypt.checkpw(
            validated.password.encode("utf-8"),
            user["password"]
        )
        if not password_matches:
            return {"ok": False, "errors": [{"field": "credentials", "message": "Invalid Login"}]}

        # 4. Generar JWT
        # identity es lo que podrás leer luego con get_jwt_identity()
        access_token = create_access_token(identity=str(user["_id"]))
        return {
            "ok": True,
            "access_token": access_token,
            "user": {
                "user_id":    str(user["_id"]),
                "username":   user["username"],
                "email":      user["email"],
                "first_name": user["first_name"],
                "last_name":  user["last_name"],
            }
        }


    @staticmethod
    def logout(jti: str, user_id: str | None = None) -> dict:
        """
        Revoca el token actual añadiendo su JTI a la blocklist.
        El JTI y user_id deben extraerse en la capa de routes con
        get_jwt() / get_jwt_identity() antes de invocar este método.
        """
        if not jti:
            return {"ok": False, "errors": [{"field": "token", "message": "JTI not found in token"}]}

        revoked = AuthRepository.revoke_token(jti, user_id)
        if not revoked:
            return {"ok": False, "errors": [{"field": "database", "message": "Error revoking token"}]}

        return {"ok": True}