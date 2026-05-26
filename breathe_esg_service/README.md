# Breathe ESG — Backend

Multi-tenant carbon emissions ingestion and review platform.

**Stack:** Django 4.2 · DRF · PostgreSQL · SimpleJWT · python-decouple

---

## Setup

```bash
# 1. Clone & install
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your DB credentials and secrets

# 3. Run migrations
python manage.py migrate

# 4. Seed demo data
python manage.py seed_demo_data

# 5. Start server
python manage.py runserver
```

Demo credentials after seeding:
- **Analyst:** `analyst@acme.com` / `demo1234`
- **Admin:** `admin@acme.com` / `admin1234`

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login — returns access token + sets httpOnly refresh cookie |
| POST | `/api/auth/refresh/` | Refresh access token from cookie |

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingestion/utility/upload/` | Upload utility CSV (multipart, field: `file`) |
| POST | `/api/ingestion/travel/pull/` | Pull travel data from Concur API |
| POST | `/api/ingestion/travel/upload/` | Upload travel CSV (multipart, field: `file`) |
| GET | `/api/ingestion/jobs/{id}/` | Get ingestion job status |

### Records

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/records/` | List all records (merged utility + travel, sorted by recently updated/created) |
| PATCH | `/api/records/{id}/` | Edit allowed fields |
| POST | `/api/records/{id}/approve/` | Approve a record |
| POST | `/api/records/{id}/flag/` | Flag a record with a reason |
| **PATCH** | **`/api/records/{id}/lock/`** | **Lock or unlock a record (admin only)** |
| POST | `/api/records/bulk-approve/` | Bulk approve up to 100 records |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/` | View audit log (tenant-scoped) |

---

## Record ID Format

All record IDs are prefixed to encode the table:

- `utility_<uuid>` → `records_utilityrecord`
- `travel_<uuid>` → `records_travelrecord`

---

## Lock / Unlock Records

**`PATCH /api/records/{id}/lock/`**

- **Admin role required** — returns `403` for analysts
- Body: `{ "is_locked": true }` or `{ "is_locked": false }`
- Locking prevents edits, approvals, flags, and further locks by non-admins
- Every lock/unlock writes an `AuditLog` entry with `action=locked` or `action=unlocked`
- Returns the full record shape identical to `GET /api/records/`

Example:
```bash
curl -X PATCH http://localhost:8000/api/records/utility_<uuid>/lock/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_locked": true}'
```

---

## Default Ordering

All GET list responses return records **most recently updated or created first**:

1. `edited_at DESC` (NULL last — unedited records fall to bottom)
2. `created_at DESC` (tiebreaker)

This applies to:
- `GET /api/records/` — merged list, sorted in Python after merging
- `GET /api/audit/` — sorted by `timestamp DESC`
- `GET /api/ingestion/jobs/` — sorted by `created_at DESC`

---

## GET /api/records/ Query Params

| Param | Values | Description |
|-------|--------|-------------|
| `source` | `utility_electricity`, `travel_air`, `travel_hotel`, `travel_ground`, `travel_rail` | Filter by source |
| `status` | `pending`, `approved`, `flagged`, `failed` | Filter by status |
| `date_from` | `YYYY-MM-DD` | Filter `activity_date >=` |
| `date_to` | `YYYY-MM-DD` | Filter `activity_date <=` |
| `page` | integer | Page number (page_size=50) |

---

## Multi-Tenancy

- Every model has `tenant FK`
- `request.user.tenant` is set from JWT; never trusted from request body/params
- All views filter by `tenant` — zero cross-tenant data leakage

---

## Flag Rules

**Utility:**
- `normalized_value > 1,000,000` → "Usage over 1,000,000 kWh — possible unit error"
- Billing period duration `< 20` or `> 45` days → "Unusual billing period duration"

**Travel (air):** distance null → "Distance not computed — airport pair needs lookup"

**Travel (hotel):** nights `> 30` → "Hotel stay over 30 nights — verify"

**Travel (car/rail):** distance null → "Distance not provided by source"

**All:** `normalized_value <= 0` → "Zero or negative normalized value"

---

## CSV Column Schemas

**Utility CSV:**
```
Account Number, Service Address, Billing Period Start, Billing Period End,
Usage (kWh), Demand (kW), Amount
```

**Travel CSV:**
```
Trip ID, Traveler, Travel Type, Origin, Destination,
Departure Date, Arrival Date, Amount, Currency
```
