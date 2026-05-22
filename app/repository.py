"""
UserRepository: User tablosu icin tum veritabani islemleri.
Tasarim kararlari:
- Her metot bir AsyncSession alir (dependency injection).
- Yazma metotlari try/except ile transaction sinirlarini net yonetir:
  hata olursa rollback, basari olursa commit.
- Dogrudan ham SQL kullanilmaz; SQLAlchemy ORM ve select() tercih edilir.
"""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models import User
from app.schemas import UserCreate, UserUpdate
class UserNotFoundError(Exception):
    """Belirtilen id'ye sahip kullanici bulunamadiginda firlatilir."""
    pass
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    async def list_all(self) -> Sequence[User]:
        """Tum kullanicilari id sirasiyla doner. Read-only, transaction gerekmiyor."""
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    async def get_by_id(self, user_id: int) -> User | None:
        """Tek bir kullaniciyi id ile getirir; yoksa None doner."""
        return await self.session.get(User, user_id)
    async def create(self, data: UserCreate) -> User:
        """
        Yeni kullanici olusturur.
        Transaction: ekleme basariliysa commit, hata olursa rollback.
        """
        user = User(name=data.name, email=data.email)
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except SQLAlchemyError:
            await self.session.rollback()
            raise
    async def update(self, user_id: int, data: UserUpdate) -> User:
        """
        Kullaniciyi gunceller.
        Transaction: degisiklikler atomik. Hata olursa hicbiri uygulanmaz.
        Kullanici bulunamazsa UserNotFoundError firlatir.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        try:
            if data.name is not None:
                user.name = data.name
            if data.email is not None:
                user.email = data.email
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except SQLAlchemyError:
            await self.session.rollback()
            raise
    async def delete(self, user_id: int) -> None:
        """
        Kullaniciyi siler.
        Kullanici bulunamazsa UserNotFoundError firlatir.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        try:
            await self.session.delete(user)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise