"""
Pydantic giris semalari.

Bu semalar repository metodlarina veri gonderirken kullanilir.
ORM modelinden (models.py) ayri tutuluyor cunku:
- ORM modeli veritabanini temsil eder (id, created_at gibi alanlar var).
- Schema modeli kullanici girisini temsil eder (sadece isim, email).
Bu ayrim katmanlar arasi temizligi saglar.
"""
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Yeni kullanici olustururken kullanilir."""
    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    """Mevcut kullaniciyi guncellerken kullanilir. Tum alanlar opsiyonel."""
    name: str | None = None
    email: EmailStr | None = None