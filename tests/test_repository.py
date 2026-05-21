"""
UserRepository testleri.

Her test kendi seed verisini kendi içinde yükler (açık ve okunabilir kalsın diye
merkezi seed dosyası kullanılmadı). Fixture izolasyonu sayesinde testler
birbirinin verisini göremez; sıralama fark etmez.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.repository import UserRepository, UserNotFoundError
from app.schemas import UserCreate, UserUpdate


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_empty_on_fresh_db(session):
    """Temiz DB'de liste boş gelmelidir."""
    repo = UserRepository(session)
    users = await repo.list_all()
    assert users == []


@pytest.mark.asyncio
async def test_list_returns_all_created_users(session):
    """Oluşturulan tüm kullanıcılar listede görünmelidir."""
    repo = UserRepository(session)
    await repo.create(UserCreate(name="Esma", email="esma@test.com"))
    await repo.create(UserCreate(name="Dilara", email="dilara@test.com"))
    await repo.create(UserCreate(name="Ahmet", email="ahmet@test.com"))

    users = await repo.list_all()
    assert len(users) == 3
    emails = {u.email for u in users}
    assert emails == {"esma@test.com", "dilara@test.com", "ahmet@test.com"}


@pytest.mark.asyncio
async def test_list_ordered_by_id(session):
    """Kullanıcılar id sırasıyla gelmelidir."""
    repo = UserRepository(session)
    await repo.create(UserCreate(name="A", email="a@test.com"))
    await repo.create(UserCreate(name="B", email="b@test.com"))

    users = await repo.list_all()
    assert users[0].id < users[1].id


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_returns_user_with_id(session):
    """create() sonucu id alanı dolu olmalıdır."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Esma", email="esma@test.com"))
    assert user.id is not None
    assert user.name == "Esma"
    assert user.email == "esma@test.com"


@pytest.mark.asyncio
async def test_create_persists_to_db(session):
    """create() ile eklenen kullanıcı list_all()'da da görünmelidir."""
    repo = UserRepository(session)
    created = await repo.create(UserCreate(name="Dilara", email="dilara@test.com"))
    users = await repo.list_all()
    assert len(users) == 1
    assert users[0].id == created.id


@pytest.mark.asyncio
async def test_create_duplicate_email_raises_and_rolls_back(session):
    """
    Aynı e-posta ile ikinci kayıt eklemeye çalışılınca hata fırlamalı
    ve transaction rollback edilmeli — DB'de yalnızca ilk kayıt kalmalıdır.

    Bu test kabul kriteri 4'ü (transaction sınırları / rollback) doğrular.
    """
    repo = UserRepository(session)
    await repo.create(UserCreate(name="İlk", email="dup@test.com"))

    with pytest.raises((IntegrityError, Exception)):
        await repo.create(UserCreate(name="İkinci", email="dup@test.com"))

    users = await repo.list_all()
    assert len(users) == 1   # rollback → yalnızca ilki var


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_by_id_existing(session):
    """Var olan bir id için doğru kullanıcı dönmelidir."""
    repo = UserRepository(session)
    created = await repo.create(UserCreate(name="Ahmet", email="ahmet@test.com"))
    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert found.email == "ahmet@test.com"


@pytest.mark.asyncio
async def test_get_by_id_missing_returns_none(session):
    """Var olmayan id için None dönmelidir."""
    repo = UserRepository(session)
    result = await repo.get_by_id(9999)
    assert result is None


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_name_only(session):
    """Yalnızca isim güncellendiğinde e-posta değişmemeli."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Eski İsim", email="user@test.com"))
    updated = await repo.update(user.id, UserUpdate(name="Yeni İsim"))
    assert updated.name == "Yeni İsim"
    assert updated.email == "user@test.com"


@pytest.mark.asyncio
async def test_update_email_only(session):
    """Yalnızca e-posta güncellendiğinde isim değişmemeli."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Ad Soyad", email="eski@test.com"))
    updated = await repo.update(user.id, UserUpdate(email="yeni@test.com"))
    assert updated.email == "yeni@test.com"
    assert updated.name == "Ad Soyad"


@pytest.mark.asyncio
async def test_update_both_fields(session):
    """İsim ve e-posta aynı anda güncellenebilmelidir."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Eski", email="eski@test.com"))
    updated = await repo.update(user.id, UserUpdate(name="Yeni", email="yeni@test.com"))
    assert updated.name == "Yeni"
    assert updated.email == "yeni@test.com"


@pytest.mark.asyncio
async def test_update_missing_user_raises(session):
    """Var olmayan id güncellenmeye çalışılırsa UserNotFoundError fırlamalıdır."""
    repo = UserRepository(session)
    with pytest.raises(UserNotFoundError):
        await repo.update(9999, UserUpdate(name="Hayalet"))


@pytest.mark.asyncio
async def test_update_persists_after_list(session):
    """Güncelleme kalıcı olmalı; list_all() ile de doğrulanmalı."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Test", email="test@test.com"))
    await repo.update(user.id, UserUpdate(name="Kalıcı İsim"))
    users = await repo.list_all()
    assert users[0].name == "Kalıcı İsim"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_removes_user(session):
    """Silinen kullanıcı artık list_all()'da görünmemeli."""
    repo = UserRepository(session)
    user = await repo.create(UserCreate(name="Silinecek", email="del@test.com"))
    await repo.delete(user.id)
    users = await repo.list_all()
    assert len(users) == 0


@pytest.mark.asyncio
async def test_delete_only_target_user(session):
    """Yalnızca hedef kullanıcı silinmeli; diğerleri kalmalı."""
    repo = UserRepository(session)
    u1 = await repo.create(UserCreate(name="Kalacak", email="stay@test.com"))
    u2 = await repo.create(UserCreate(name="Gidecek", email="gone@test.com"))
    await repo.delete(u2.id)
    users = await repo.list_all()
    assert len(users) == 1
    assert users[0].id == u1.id


@pytest.mark.asyncio
async def test_delete_missing_user_raises(session):
    """Var olmayan id silinmeye çalışılırsa UserNotFoundError fırlamalıdır."""
    repo = UserRepository(session)
    with pytest.raises(UserNotFoundError):
        await repo.delete(9999)
