from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

from backend.app.image_utils import ALLOWED_IMAGE_MIMES


class UserPublicSchema(BaseModel):
    """Perfil público de un usuario — sin datos sensibles (email, is_active)."""
    id:            str
    username:      str
    first_name:    str
    last_name:     str
    age:           int
    biography:     str | None = None
    privacy:       str = "public"
    avatar_base64: str | None = None
    avatar_mime:   str | None = None
    avatar_url:    str | None = None
    cover_url:     str | None = None
    cover_base64:  str | None = None
    cover_mime:    str | None = None
    followers_count: int | None = 0
    following_count: int | None = 0


class UserSchema(BaseModel):
    _id:           str
    username:      str
    email:         EmailStr
    age:           int
    first_name:    str
    last_name:     str
    is_active:     bool
    biography:     str | None = None
    privacy:       str = "public"
    avatar_base64: str | None = None
    avatar_mime:   str | None = None
    avatar_url:    str | None = None
    cover_url:     str | None = None
    cover_base64:  str | None = None
    cover_mime:    str | None = None
    followers_count: int | None = 0
    following_count: int | None = 0


class UserUpdateSchema(BaseModel):
    """
    Schema para actualizar parcialmente un usuario.
    Todos los campos son opcionales: solo se actualizan los enviados.
    Campos protegidos como _id, password, is_active no se permiten aquí.
    """
    model_config = ConfigDict(extra="forbid")

    username:      str       | None = None
    email:         EmailStr  | None = None
    age:           int       | None = Field(default=None, ge=0, le=150)
    first_name:    str       | None = None
    last_name:     str       | None = None
    biography:     str       | None = None
    privacy:       str       | None = None
    is_active:     bool      | None = True
    avatar_base64: str       | None = None
    avatar_mime:   str       | None = None
    avatar_url:    str       | None = None
    cover_url:     str       | None = None
    cover_base64:  str       | None = None
    cover_mime:    str       | None = None

    @field_validator("privacy")
    @classmethod
    def validate_privacy(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().lower()
        if cleaned not in ("public", "friends", "private"):
            raise ValueError("La privacidad debe ser 'public', 'friends' o 'private'")
        return cleaned

    @field_validator("avatar_mime")
    @classmethod
    def validate_avatar_mime(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in ALLOWED_IMAGE_MIMES:
            raise ValueError(
                f"Tipo de imagen no permitido. Permitidos: {sorted(ALLOWED_IMAGE_MIMES)}"
            )
        return cleaned

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) < 3:
            raise ValueError("El username debe tener mínimo 3 caracteres")
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError("El username solo puede contener letras, números y _")
        return value.lower()

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_non_empty_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El campo no puede estar vacío")
        return cleaned