"""
Basit kullanım senaryosu: liste, oluştur, güncelle, sil.

Çalıştırmak için:
    python demo.py
"""
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.repository import UserRepository
from app.schemas import UserCreate, UserUpdate


async def main() -> None:
    # 1) Tabloları oluştur (geliştirme modu — production'da Alembic kullan)
    await init_db()
    print("✓ Tablolar hazır\n")

    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)

        # 2) Başlangıç listesi (boş)
        users = await repo.list_all()
        print(f"Başlangıç: {len(users)} kullanıcı")

        # 3) Üç kullanıcı oluştur
        esma = await repo.create(UserCreate(name="Esma Fazilet", email="esma@example.com"))
        dilara = await repo.create(UserCreate(name="Dilara Şenay", email="dilara@example.com"))
        ahmet = await repo.create(UserCreate(name="Ahmet Özdoğan", email="ahmet@example.com"))
        print(f"\n✓ 3 kullanıcı oluşturuldu:")
        print(f"  {esma}")
        print(f"  {dilara}")
        print(f"  {ahmet}")

        # 4) Tüm kullanıcıları listele
        users = await repo.list_all()
        print(f"\nMevcut kullanıcılar ({len(users)} kişi):")
        for u in users:
            print(f"  [{u.id}] {u.name} — {u.email}")

        # 5) id ile tek kullanıcı getir
        found = await repo.get_by_id(esma.id)
        print(f"\nget_by_id({esma.id}) → {found}")

        # 6) Güncelle (sadece isim)
        updated = await repo.update(esma.id, UserUpdate(name="Esma Fazilet Karagülle"))
        print(f"\nGüncellendi → {updated}")

        # 7) Sil
        await repo.delete(dilara.id)
        users = await repo.list_all()
        print(f"\nDilara silindi. Kalan: {len(users)} kullanıcı")
        for u in users:
            print(f"  [{u.id}] {u.name}")

        # 8) Olmayan kullanıcıyı güncelleme → hata yakalama
        from app.repository import UserNotFoundError
        try:
            await repo.update(9999, UserUpdate(name="Hayalet"))
        except UserNotFoundError as e:
            print(f"\n✓ Beklenen hata yakalandı: {e}")

    print("\nDemo tamamlandı.")


if __name__ == "__main__":
    asyncio.run(main())
