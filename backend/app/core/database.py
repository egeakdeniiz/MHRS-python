from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQL Server / Veritabanı bağlantı cümlesi (Proje gereksinimine göre güncellenecek)
SQLALCHEMY_DATABASE_URL = "sqlite:///./mhrs.db"  # Geliştirme için SQLite ile başlayabiliriz

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Her istekte veritabanı oturumu açar ve işlem bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()