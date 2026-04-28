from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    id:         int
    username:   str
    email:      EmailStr
    age:        int
    first_name: str
    last_name:  str