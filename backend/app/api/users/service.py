from pydantic import ValidationError

from .repository import UserRepository
from .schemas import UserSchema

class UserService:

    @staticmethod
    def find_by_id(id_user: str) -> dict | None:
        if not id_user:
            return {"ok": False, "errors": [{"field": "id", "message": "Id no valido"}]}
        
        user_found = UserRepository.find_by_id(id_user)

        if not user_found:
            return {"ok": False, "error": [{"field": "user", "message": "Usuario no encontrado"}]}
        
        # parsear user
        uesr_parsed = UserSchema(**user_found)
        
        return {"ok": True, "user": uesr_parsed.model_dump()}