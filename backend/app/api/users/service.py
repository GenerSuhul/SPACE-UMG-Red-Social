from pydantic import ValidationError

from .repository import UserRepository
from .schemas import UserSchema, UserUpdateSchema, UserPublicSchema
from bson import ObjectId
from bson.errors import InvalidId
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
        if not id_user:
            return {"ok": False, "errors": [{"field": "id", "message": "Id no enviado"}]}

        if not isinstance(data, dict) or not data:
            return {
                "ok": False,
                "errors": [{"field": "body", "message": "No se enviaron campos para actualizar"}],
            }

        try:
            validated = UserUpdateSchema(**data)
        except ValidationError as e:
            errors = [
                {"field": err["loc"][0] if err["loc"] else "body", "message": err["msg"]}
                for err in e.errors()
            ]
            return {"ok": False, "errors": errors}

        existing_user = UserRepository.find_by_id(id_user)
        if not existing_user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        update_fields = validated.model_dump(exclude_unset=True)
        if not update_fields:
            return {
                "ok": False,
                "errors": [{"field": "body", "message": "No se enviaron campos para actualizar"}],
            }

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

        if "email" in update_fields and update_fields["email"]:
            update_fields["email"] = update_fields["email"].lower()

        if "username" in update_fields and update_fields["username"] != existing_user.get("username"):
            duplicate = UserRepository.find_by_username(update_fields["username"])
            if duplicate and str(duplicate["_id"]) != str(existing_user["_id"]):
                return {
                    "ok": False,
                    "errors": [{"field": "username", "message": "Username in use"}],
                }

        if "email" in update_fields and update_fields["email"] != existing_user.get("email"):
            duplicate = UserRepository.find_by_email(update_fields["email"])
            if duplicate and str(duplicate["_id"]) != str(existing_user["_id"]):
                return {
                    "ok": False,
                    "errors": [{"field": "email", "message": "Email in use"}],
                }

        updated_user = UserRepository.update_by_id(id_user, update_fields)
        if not updated_user:
            return {
                "ok": False,
                "errors": [{"field": "database", "message": "Error actualizando usuario"}],
            }

        updated_user.setdefault("is_active", True)
        updated_user.setdefault("avatar_base64", None)
        updated_user.setdefault("avatar_mime", None)
        user_parsed = UserSchema(**updated_user)
        return {"ok": True, "user": user_parsed.model_dump()}

    @staticmethod
    def _is_valid_object_id(value: str) -> bool:
        try:
            ObjectId(value)
            return True
        except (InvalidId, TypeError):
            return False

    @staticmethod
    def _serialize_public(user: dict) -> dict:
        return {
            "id":            str(user["_id"]),
            "username":      user.get("username", ""),
            "first_name":    user.get("first_name", ""),
            "last_name":     user.get("last_name", ""),
            "age":           user.get("age", 0),
            "avatar_base64": user.get("avatar_base64"),
            "avatar_mime":   user.get("avatar_mime"),
        }

    @staticmethod
    def search_users(query: str, limit: int = 20) -> dict:
        query = (query or "").strip()
        if len(query) < 1:
            return {"ok": False, "errors": [{"field": "q", "message": "El término de búsqueda no puede estar vacío"}]}
        if len(query) > 50:
            return {"ok": False, "errors": [{"field": "q", "message": "El término de búsqueda es demasiado largo"}]}

        limit = max(1, min(50, limit))
        users = UserRepository.search_by_username(query, limit=limit)
        return {
            "ok":    True,
            "users": [UserService._serialize_public(u) for u in users],
            "total": len(users),
        }

    @staticmethod
    def get_public_profile(user_id: str, current_user_id: str | None = None) -> dict:
        if not user_id or not UserService._is_valid_object_id(user_id):
            return {"ok": False, "errors": [{"field": "user_id", "message": "Id de usuario inválido"}]}

        user = UserRepository.find_by_id(user_id)
        if not user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        is_following = (
            UserRepository.is_following(current_user_id, user_id)
            if current_user_id and current_user_id != user_id
            else False
        )

        profile = UserService._serialize_public(user)
        profile["is_following"] = is_following
        return {"ok": True, "user": profile}

    @staticmethod
    def _serialize_follow_info(user: dict) -> dict:
        return {
            "id":         str(user["_id"]),
            "username":   user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "last_name":  user.get("last_name", ""),
        }

    @staticmethod
    def get_my_follow_lists(user_id: str) -> dict:
        if not user_id or not UserService._is_valid_object_id(user_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id no válido"}]}

        lists = UserRepository.get_follow_lists(user_id)
        if lists is None:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        return {
            "ok":              True,
            "followers":       lists["followers"],
            "following":       lists["following"],
            "followers_count": len(lists["followers"]),
            "following_count": len(lists["following"]),
        }

    @staticmethod
    def toggle_follow(current_user_id: str, target_user_id: str) -> dict:
        if not current_user_id or not UserService._is_valid_object_id(current_user_id):
            return {"ok": False, "errors": [{"field": "current_user", "message": "Id del usuario autenticado inválido"}]}
        if not target_user_id or not UserService._is_valid_object_id(target_user_id):
            return {"ok": False, "errors": [{"field": "target_user_id", "message": "Id de usuario inválido"}]}

        if str(current_user_id) == str(target_user_id):
            return {"ok": False, "errors": [{"field": "target_user_id", "message": "No puedes seguirte a ti mismo"}]}

        target_user = UserRepository.find_by_id(target_user_id)
        if not target_user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        current_user = UserRepository.find_by_id(current_user_id)
        if not current_user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario autenticado no encontrado"}]}

        already_following = UserRepository.is_following(current_user_id, target_user_id)

        target_info  = UserService._serialize_follow_info(target_user)
        current_info = UserService._serialize_follow_info(current_user)

        if already_following:
            ok = UserRepository.remove_follow(current_user_id, target_user_id)
            action = "unfollowed"
        else:
            ok = UserRepository.add_follow(
                current_user_id, current_info, target_user_id, target_info
            )
            action = "followed"

        if not ok:
            return {
                "ok": False,
                "errors": [{"field": "database", "message": "Error actualizando follow"}],
            }

        counts = UserRepository.get_follow_counts(target_user_id)
        return {
            "ok":              True,
            "action":          action,
            "target_user":     target_info,
            "followers_count": counts["followers_count"],
            "following_count": counts["following_count"],
        }