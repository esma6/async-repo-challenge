"""
Pytest fixture'ları.

Her test fonksiyonu birbirinden tam izole, temiz bir veritabanıyla başlar:
- In-memory SQLite kullanılır → disk dosyası oluşmaz, geliştirme DB'si kirlenmez.
- Her test için yeni bir engine + session açılır.
- Test bittikten sonra tablolar drop_all ile silinir, engine dispose edilir.
  Bu sayede testler arası durum taşınmaz; sıralama önemli değildir.
"""
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
from app import models  # noqa: F401 — modelleri Base.metadata'ya kayıt için


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """
    Her test fonksiyonu için izole bir AsyncSession üretir.

    Yaşam döngüsü:
      1. Yeni in-memory engine oluşturulur.
      2. Base.metadata.create_all ile tüm tablolar kurulur.
      3. Session açılır ve teste yield edilir.
      4. Test tamamlanır.
      5. Base.metadata.drop_all ile tablolar temizlenir.
      6. Engine dispose edilir.
    """
    engine = create_async_engine(TEST_DATABASE_URL, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with SessionLocal() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
