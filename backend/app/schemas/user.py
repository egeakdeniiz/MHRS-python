from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Kullanıcı oluştururken (Kayıt Olurken) dışarıdan alınacak veriler
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

# Kullanıcı verisini dışarıya dönerken şifreyi gizleyerek döndüğümüz model
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Giriş (Login) verisi için şema
class UserLogin(BaseModel):
    email: EmailStr
    password: str