from pydantic import ValidationError

from .repository import UserRepository
from .schemas import UserSchema, UserUpdateSchema
from backend.app.image_utils import normalize_base64_image, ImageError

class UserService:

    @staticmethod
    def find_by_id(id_user: str) -> dict | None:
        if not id_user:
            return {"ok": False, "errors": [{"field": "id", "message": "Id no valido"}]}

        user_found = UserRepository.find_by_id(id_user)

        if not user_found:
            return {"ok": False, "error": [{"field": "user", "message": "Usuario no encontrado"}]}

        user_found.setdefault("is_active", True)
        user_found.setdefault("avatar_base64", None)
        user_found.setdefault("avatar_mime", None)
        uesr_parsed = UserSchema(**user_found)

        return {"ok": True, "user": uesr_parsed.model_dump()}

    @staticmethod
    def update_user(id_user: str, data: dict | None) -> dict:
        """
        Actualiza parcialmente un usuario identificado por su _id (extraído del JWT).
        Solo modifica los campos enviados. Verifica unicidad de username y email
        cuando aplican.
        """
        # 1. Validar identity del token
        if not id_user:
            return {"ok": False, "errors": [{"field": "id", "message": "Id no enviado"}]}

        # 2. Validar que llegó un body con algo
        if not isinstance(data, dict) or not data:
            return {
                "ok": False,
                "errors": [{"field": "body", "message": "No se enviaron campos para actualizar"}],
            }

        # 3. Validar payload con Pydantic (extra="forbid" rechaza campos no permitidos)
        try:
            validated = UserUpdateSchema(**data)
        except ValidationError as e:
            errors = [
                {"field": err["loc"][0] if err["loc"] else "body", "message": err["msg"]}
                for err in e.errors()
            ]
            return {"ok": False, "errors": errors}

        # 4. Verificar que el usuario existe
        existing_user = UserRepository.find_by_id(id_user)
        if not existing_user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        # 5. Construir dict solo con campos enviados (exclude_unset descarta los None
        # que el cliente nunca envió, preservando la semántica de update parcial)
        update_fields = validated.model_dump(exclude_unset=True)
        if not update_fields:
            return {
                "ok": False,
                "errors": [{"field": "body", "message": "No se enviaron campos para actualizar"}],
            }

        # Validar y normalizar avatar si viene en el payload
        if "avatar_base64" in update_fields and update_fields["avatar_base64"]:
            try:
                clean_b64, clean_mime = normalize_base64_image(
                    update_fields["avatar_base64"],
                    update_fields.get("avatar_mime"),
                )
            except ImageError as ex:
                return {"ok": False, "errors": [{"field": "avatar", "message": str(ex)}]}
            update_fields["avatar_base64"] = clean_b64
            update_fields["avatar_mime"]   = clean_mime

        # Normalizar email a minúsculas (consistente con register)
        if "email" in update_fields and update_fields["email"]:
            update_fields["email"] = update_fields["email"].lower()

        # 6. Verificar unicidad de username (si cambia)
        if "username" in update_fields and update_fields["username"] != existing_user.get("username"):
            duplicate = UserRepository.find_by_username(update_fields["username"])
            if duplicate and str(duplicate["_id"]) != str(existing_user["_id"]):
                return {
                    "ok": False,
                    "errors": [{"field": "username", "message": "Username in use"}],
                }

        # 7. Verificar unicidad de email (si cambia)
        if "email" in update_fields and update_fields["email"] != existing_user.get("email"):
            duplicate = UserRepository.find_by_email(update_fields["email"])
            if duplicate and str(duplicate["_id"]) != str(existing_user["_id"]):
                return {
                    "ok": False,
                    "errors": [{"field": "email", "message": "Email in use"}],
                }

        # 8. Persistir
        updated_user = UserRepository.update_by_id(id_user, update_fields)
        if not updated_user:
            return {
                "ok": False,
                "errors": [{"field": "database", "message": "Error actualizando usuario"}],
            }

        # 9. Parsear con UserSchema (los campos no presentes podrían faltar; los
        # rellenamos para no romper la validación del schema de respuesta)
        updated_user.setdefault("is_active", True)
        updated_user.setdefault("avatar_base64", None)
        updated_user.setdefault("avatar_mime", None)
        user_parsed = UserSchema(**updated_user)
        return {"ok": True, "user": user_parsed.model_dump()}