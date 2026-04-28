from pydantic import BaseModel, EmailStr, field_validator
import re

class UserRegisterSchema(BaseModel):
    username:   str
    email:      str
    password:   str
    email:      EmailStr
    age:        int
    first_name: str
    last_name:  str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', value):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', value):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'[0-9]', value):
            raise ValueError('La contraseña debe contener al menos un número')
        return value
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if len(value) < 3:
            raise ValueError("El username debe tener mínimo 3 caracteres")
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError("El username solo puede contener letras, números y _")
        return value.lower()

class UserLoginSchema(BaseModel):
    username: str
    password: str