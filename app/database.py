"""
Veritabanı bağlantı yönetimi.

- engine: Tek bir tane, uygulama ömrü boyunca yaşar.
- AsyncSessionLocal: Her işlem için yeni bir AsyncSession üretir.
- Base: Tüm ORM modellerinin türeyeceği temel sınıf.
- init_db(): Geliştirme amaçlı tabloları oluşturur (production'da Alembic).
"""
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# .env dosyasini yukle
load_dotenv()

# Baglanti URL'i ortam degiskeninden okunur (kabul kriteri 1).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

# echo=True yaparsan SQLAlchemy'nin urettigi SQL'leri konsolda gorebilirsin.
# Debug icin faydali, production'da kapali olmali.
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# expire_on_commit=False: commit sonrasi ORM nesneleri kullanim disi olmasin.
# Async dunyada bu pratiktir; aksi halde her attribute erisimi yeni bir await ister.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Tum ORM modellerinin turetilecegi temel sinif."""
    pass


async def init_db() -> None:
    """
    Gelistirme amacli: Tablolari metadata'dan olusturur.
    Production'da bu yontem yerine Alembic migration'lari kullanilmalidir.
    """
    # Modelleri import et ki Base.metadata onlari tanisin
    from app import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)