"""
UserRepository: User tablosu için tüm veritabanı işlemlerini içerir.

Tasarım kararları:
- Her metot dışarıdan enjekte edilen bir AsyncSession alır (dependency injection).
  Böylece test sırasında aynı session kolayca geçilebilir.
- Yazma metotları (create, update, delete) kendi transaction sınırını yönetir:
  başarıda commit, herhangi bir SQLAlchemyError'da rollback.
- Doğrudan ham SQL string kullanılmaz; select(), session.get(), session.add()
  gibi SQLAlchemy 2.0 ORM API'leri tercih edilir.
"""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models import User
from app.schemas import UserCreate, UserUpdate


class UserNotFoundError(Exception):
    """İstenen id'ye sahip kullanıcı bulunamadığında fırlatılır."""
    pass


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> Sequence[User]:
        """Tüm kullanıcıları id sırasıyla döner. Read-only; commit gerekmez."""
        stmt = select(User).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, user_id: int) -> User | None:
        """Tek bir kullanıcıyı id ile getirir. Bulunamazsa None döner."""
        return await self.session.get(User, user_id)

    async def create(self, data: UserCreate) -> User:
        """
        Yeni kullanıcı oluşturur ve veritabanına ekler.

        Transaction: ekleme başarılıysa commit, SQLAlchemyError olursa rollback.
        refresh() ile id, created_at gibi DB tarafından doldurulan alanlar alınır.
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
        Mevcut kullanıcıyı günceller.

        Transaction: değişiklikler atomik uygulanır. Hata olursa
        hiçbiri kalıcılaşmaz (rollback).
        Kullanıcı bulunamazsa UserNotFoundError fırlatılır.
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
        Kullanıcıyı siler.

        Kullanıcı bulunamazsa UserNotFoundError fırlatılır.
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
