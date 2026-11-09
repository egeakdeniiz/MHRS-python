from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import get_user_by_email, create_user
from app.core.security import verify_plain_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı oluşturur."""
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten bir hesap kayıtlı."
        )
    return create_user(db=db, user=user)

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi yapar ve JWT erişim token'ı üretir."""
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_plain_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta adresi veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Başarılı giriş sonrası JWT token üretimi
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}