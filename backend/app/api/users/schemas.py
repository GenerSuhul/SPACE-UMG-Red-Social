from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

class UserSchema(BaseModel):
    _id:        str
    username:   str
    email:      EmailStr
    age:        int
    first_name: str
    last_name:  str
    is_active:  bool


class UserUpdateSchema(BaseModel):
    """
    Schema para actualizar parcialmente un usuario.
    Todos los campos son opcionales: solo se actualizan los enviados.
    Campos protegidos como _id, password, is_active no se permiten aquí.
    """
    model_config = ConfigDict(extra="forbid")

    username:   str       | None = None
    email:      EmailStr  | None = None
    age:        int       | None = Field(default=None, ge=0, le=150)
    first_name: str       | None = None
    last_name:  str       | None = None
    is_active:  bool      | None = True

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