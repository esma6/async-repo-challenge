"""Iskelet kontrol script'i. Tablolar olusuyor mu?"""
import asyncio
from app.database import init_db, engine


async def main():
    print("init_db() cagriliyor...")
    await init_db()
    print("Tablolar olusturuldu.")
    await engine.dispose()
    print("Engine kapatildi.")


if __name__ == "__main__":
    asyncio.run(main())