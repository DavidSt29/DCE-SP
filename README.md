# QR kód stopovačka (Semestrální práce DCE)

Webová aplikace pro generování, správu a ukládání QR kódů do relační databáze PostgreSQL (včetně ukládání vygenerovaných PNG obrázků v binárním formátu `BYTEA`).

## Architektura a technologie

Aplikace je třívrstvá a běží v Docker Compose:
- **Frontend:** Vue 3 (Vite), obsluhovaný přes webový server Nginx.
- **Backend:** REST API v Python Flask (Gunicorn WSGI, SQLAlchemy).
- **Databáze:** PostgreSQL 16 (perzistentní volume `qr_postgres_data`).

**Síť a porty:**
- Jediný veřejně dostupný port z hostitele je **`8080`** (`http://localhost:8080`), kde Nginx servíruje frontend a zároveň funguje jako reverzní proxy pro backendové API (`/api/*`).
- Backend (port 5000) a PostgreSQL (port 5432) **nejsou** vystaveny do hostitelského systému – komunikují pouze v interních Docker sítích (`frontend-network`, `db-network`).

## Spuštění aplikace

Předpoklad: nainstalovaný a spuštěný Docker.

1. **Spuštění:**
   ```bash
   docker compose up -d --build
   ```
2. **Přístup k aplikaci:**
   - Webové rozhraní: [http://localhost:8080](http://localhost:8080)
   - Kontrola stavu (Health Check): [http://localhost:8080/api/health](http://localhost:8080/api/health)

3. **Zastavení:**
   ```bash
   docker compose down
   ```
   *(Pro smazání uložených dat v databázi: `docker compose down -v`)*

## Struktura projektu

```
├── docker-compose.yml          # Definice služeb (frontend, backend, db) a sítí
├── README.md                   # Dokumentace
└── src/
    ├── frontend/               # SPA ve Vue 3 + Nginx (Dockerfile, nginx.conf, src/)
    └── backend/                # REST API ve Flasku (Dockerfile, app.py, models.py, qr_service.py)
```

## Databázové schéma (`qr_codes`)

| Sloupec | Typ | Popis |
|---|---|---|
| `id` | `INTEGER` (PK) | Identifikátor |
| `code_number` | `VARCHAR(100)` | Označení/číslo QR kódu |
| `description` | `TEXT` | Volitelný popis |
| `content` | `TEXT` | Zakódovaný text / URL |
| `image_data` | `BYTEA` | Binární data PNG obrázku |
| `created_at` | `TIMESTAMP` | Čas vytvoření |
| `updated_at` | `TIMESTAMP` | Čas poslední úpravy |

## REST API

Všechny požadavky směřují přes port 8080 na prefix `/api`:

| Metoda | Endpoint | Popis |
|---|---|---|
| `GET` | `/api/health` | Stav aplikace a spojení s databází |
| `GET` | `/api/qrcodes` | Seznam všech QR kódů (podpora `?search=`) |
| `POST` | `/api/qrcodes` | Vytvoření kódu, vygenerování PNG a uložení do DB |
| `GET` | `/api/qrcodes/<id>` | Detail konkrétního QR kódu |
| `GET` | `/api/qrcodes/<id>/image` | Stažení/zobrazení PNG obrázku (`?download=1`) |
| `POST` | `/api/qrcodes/preview` | Generování base64 náhledu pro formulář |
| `DELETE` | `/api/qrcodes/<id>` | Smazání QR kódu z databáze |
