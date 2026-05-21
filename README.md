# Async Repository Challenge — YZTA Learn

SQLAlchemy 2.0 async ile bir `User` tablosu, repository katmanı ve
basit CRUD senaryoları. Bu proje YZTA 5.0 Learn Challenge kapsamında
geliştirilmiştir.

## Ekip

- Esma Fazilet Karagülle
- Dilara Şenay
- Ahmet Özdoğan

## Proje Yapısı
    async-repo-challenge/
    ├── app/
    │   ├── init.py
    │   ├── database.py        # Engine ve AsyncSession factory
    │   ├── models.py          # SQLAlchemy ORM modeli (User)
    │   ├── repository.py      # UserRepository sınıfı
    │   └── schemas.py         # Pydantic giriş şemaları
    ├── tests/
    │   ├── conftest.py        # Pytest fixture'ları (DB izolasyonu)
    │   └── test_repository.py # Repository testleri
    ├── demo.py                # Basit kullanım senaryosu
    ├── .env.example           # Örnek ortam değişkenleri
    ├── requirements.txt
    └── README.md

  ## Kurulum

```bash
git clone https://github.com/esma6/async-repo-challenge.git
cd async-repo-challenge
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env     # Linux/Mac: cp .env.example .env
```

## Yapılandırma — Ortam Değişkenleri

Bağlantı bilgisi `.env` dosyasından, `python-dotenv` ile yüklenir.
`app/database.py` içinde `os.getenv("DATABASE_URL")` çağrısıyla okunur.
Bu sayede:

- Şifre veya hassas bilgi kod tabanına gömülmez.
- Geliştirme ve production ortamları için farklı bağlantılar tanımlanabilir.
- `.env` dosyası `.gitignore` ile sürüm kontrolü dışında tutulur.

| Değişken | Açıklama | Örnek değer |
|---|---|---|
| `DATABASE_URL` | Async SQLAlchemy bağlantı URL'i | `sqlite+aiosqlite:///./dev.db` |

PostgreSQL kullanmak için `.env` dosyasında:
` DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb `
  
## Şema Oluşturma Yaklaşımı

Bu projede iki seçenek değerlendirildi:

### 1. `Base.metadata.create_all` (seçilen yöntem)

`app/database.py` içindeki `init_db()` fonksiyonu, SQLAlchemy modellerinden
tabloları doğrudan oluşturur. Tek komutla başlangıç için en hızlı yöntem.

**Artıları:**
- Kurulum gerekmez, ek dosya yok.
- Geliştirme ve eğitim odaklı projeler için yeterli.
- Challenge süresi (36 saat) için uygun bir başlangıç.

**Eksileri:**
- Şema değişikliklerini versiyonlamaz.
- Production'da kullanılmamalı (mevcut tabloları olduğu gibi bırakır, yeni
  alanları otomatik eklemez).

### 2. Alembic migrasyonları (production önerisi)

Şema değişikliklerini versiyonlayan, geri alınabilir migration'lar üretir.
Production-grade çözüm.

### Tercih edilen yaklaşım ve gerekçe

Bu challenge için **`create_all`** tercih edildi çünkü:

- Amaç, repository pattern ve async kullanımını öğrenmek; migration yönetimi
  bu projenin kapsamı dışında.
- 36 saatlik süre içinde Alembic kurulumu ek yük getirir.
- Production'a taşıma durumunda `alembic init alembic` ile geçiş kolay.

`requirements.txt` içinde Alembic bağımlılığı zaten mevcut; ileride genişletme
yapmak isteyen ekipler için hazır bırakıldı.

## Kullanım

Demo senaryosu (liste, oluştur, güncelle):

```bash
python demo.py
```

Bu komut:
1. Tabloları oluşturur (`init_db()`).
2. Üç kullanıcı ekler.
3. Tüm kullanıcıları listeler.
4. Birinin adını günceller.

## Repository Tasarımı

`UserRepository` sınıfı, `User` tablosu için tüm veritabanı işlemlerini
sağlar. API/iş mantığı katmanı doğrudan SQL veya ORM çağrısı yapmaz;
yalnızca repository metotlarını çağırır. Bu ayrım:

- İş mantığını veri erişiminden ayrıştırır.
- Test edilebilirliği artırır (repository mock'lanabilir).
- İleride farklı bir veritabanı kullanılması durumunda yalnızca
  repository katmanı değişir.

### Metotlar

| Metot | Açıklama |
|---|---|
| `list_all()` | Tüm kullanıcıları döner |
| `get_by_id(id)` | Tek kullanıcıyı id ile getirir |
| `create(data)` | Yeni kullanıcı oluşturur |
| `update(id, data)` | Mevcut kullanıcıyı günceller |
| `delete(id)` | Kullanıcıyı siler |

### Transaction Yönetimi

Her yazma metodu (`create`, `update`, `delete`) kendi transaction sınırını
yönetir:

- İşlem başarıyla tamamlanırsa `commit` çağrılır.
- Herhangi bir `SQLAlchemyError` durumunda `rollback` yapılır ve hata
  yukarıya iletilir.

Bu sayede üst katman, yarım kalmış bir güncellemeyi **göremez** — işlem
ya bütünüyle uygulanır, ya hiç uygulanmaz. Bu davranış
`tests/test_repository.py` içindeki `test_unique_email_rolled_back` testi
ile doğrulanmaktadır.

### Ham SQL Yerine ORM

Repository içinde ham SQL string'i kullanılmaz. Bunun yerine:

- Sorgular: `select(User).where(...)` gibi SQLAlchemy 2.0 ORM ifadeleri
- Tek kayıt erişimi: `session.get(User, id)`
- Ekleme: `session.add(user)`

Bu tercihin avantajları:

- **Tip güvenliği:** `Mapped[...]` tip ipuçlarıyla IDE desteği.
- **SQL injection koruması:** Parametreler otomatik bağlanır.
- **Refactor kolaylığı:** Sütun adı değiştiğinde tek noktada değişir.

## Testler

```bash
pytest -v
```

### Test Stratejisi

Her test fonksiyonu, **in-memory SQLite** veritabanı üzerinde **kendi
izole** oturumunu alır. `tests/conftest.py` içindeki `session` fixture
şu davranışı sergiler:

1. **Setup:** Yeni bir `AsyncEngine` oluşturulur, `Base.metadata.create_all`
   ile tüm tablolar kurulur, yeni bir `AsyncSession` açılır.
2. **Test çalışır.** Test kendi seed verisini metot içinde
   (`await repo.create(...)`) yükler. Bu yaklaşım, her testin neye bağlı
   olduğunu açıkça gösterir; merkezi bir seed dosyası kullanılmadı.
3. **Cleanup:** Test sonunda `Base.metadata.drop_all` ile tablolar silinir,
   engine `dispose` edilir.

Bu strateji şu garantileri sağlar:

- Testler birbirinden bağımsızdır; sıralama önemli değildir.
- Her test temiz bir durumdan başlar (önceki testin verisi taşmaz).
- Geliştirme veritabanı (`dev.db`) testlerden etkilenmez — testler bellekte
  çalışır.

## Tasarım Kararları ve Trade-off'lar

- **SQLite + aiosqlite:** Kurulum gerektirmez; challenge için yeterli.
  PostgreSQL'e geçiş tek satır `.env` değişikliği.
- **ORM tercih edildi:** Ham SQL kullanılmadı. Tip güvenliği ve refactor
  kolaylığı için.
- **Pydantic şemaları:** `UserCreate` ve `UserUpdate` ile giriş
  validasyonu. `EmailStr` ile format kontrolü otomatik.
- **`expire_on_commit=False`:** Async'te commit sonrası nesne erişimi
  pratikleştirmek için. Aksi halde her attribute erişimi yeni bir await
  gerektirir.
- **Repository sınıfı session enjekte alır:** Sınıf içinde kendi session'ını
  oluşturmaz; dışarıdan verilir (dependency injection). Bu yaklaşım test
  edilebilirliği artırır.

## Gereksinimler

- Python 3.10+
- SQLAlchemy 2.0+ (async desteği için)
- Bkz. `requirements.txt` tüm bağımlılıklar için.                                            

