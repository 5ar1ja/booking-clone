# Booking Clone — Team Backend Project (Django + DRF + PostgreSQL)

This repository contains our team backend project: a simplified booking service API.
The project is built for university practice and is organized as incremental modules
(properties, users/auth, bookings, reviews, logging).

Current branch focus: **City CRUD module**.

---

## 1. Project Goal

The goal of this project is to learn how to design a real backend service in stages:

- model domain entities in Django ORM
- expose REST API with Django REST Framework
- work with PostgreSQL as the main DB
- use team workflow with feature branches and pull requests

Think of the project as a constructor:

- models = "what data we store"
- serializers = "how data is transformed to/from JSON"
- viewsets = "what actions API supports"
- router/urls = "where endpoints are available"

---

## 2. Implemented Module in This Branch: City

### 2.1 Business requirement

Entity: `City`

Fields:

- `name` — `CharField`
- `country` — `CharField`
- `created_at` — `DateTimeField(auto_now_add=True)`

Constraint:

- pair `name + country` must be unique

### 2.2 Why this uniqueness rule is important

City names are not globally unique (`Paris` can exist in different countries),
but duplicate cities inside the same country should be blocked.

Examples:

- `Paris, France` + `Paris, USA` -> valid
- `Paris, France` + `Paris, France` -> invalid

---

## 3. Architecture of the City API

```
HTTP request
    |
    v
URL Router (/api/cities/...)
    |
    v
CityViewSet (CRUD actions)
    |
    v
CitySerializer (validation + JSON transform)
    |
    v
City model (ORM) <-> PostgreSQL
```

### Layer responsibilities

- **Model**: schema and DB constraints
- **Serializer**: input/output validation and representation
- **ViewSet**: REST actions (`list/create/retrieve/update/destroy`)
- **Router**: endpoint registration

---

## 4. Tech Stack

- Python 3.14+
- Django 6.0.2
- Django REST Framework 3.16.1
- PostgreSQL 14+
- `python-dotenv`, `python-decouple`
- `psycopg` (PostgreSQL driver)

---

## 5. Repository Structure

```text
booking-clone/
├── booking_clone/
│   ├── apps/
│   │   ├── properties/
│   │   │   ├── migrations/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── users/
│   │   ├── bookings/
│   │   └── reviews/
│   ├── settings/
│   │   ├── base.py
│   │   ├── conf.py
│   │   └── urls.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .example.env
└── README.md
```

---

## 6. Environment Setup (Step-by-Step)

### 6.1 Clone and enter project

```bash
git clone https://github.com/5ar1ja/booking-clone.git
cd booking-clone/booking_clone
```

### 6.2 Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6.3 Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install python-decouple "psycopg[binary]"
```

---

## 7. PostgreSQL Setup (macOS + Homebrew)

### 7.1 Start PostgreSQL service

```bash
brew services start postgresql@14
pg_isready -h localhost -p 5432
```

Expected result:

```text
localhost:5432 - accepting connections
```

### 7.2 Create DB role and database

```bash
psql -d postgres -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname='booking_user') THEN CREATE ROLE booking_user LOGIN PASSWORD 'booking_pass_123'; END IF; END \$\$;"

if ! psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='booking_clone_db'" | grep -q 1; then
  createdb -O booking_user booking_clone_db
fi

psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE booking_clone_db TO booking_user;"
```

### 7.3 Verify role and DB

```bash
psql -d postgres -c "\\du booking_user"
psql -d postgres -c "\\l booking_clone_db"
```

---

## 8. Environment Variables (`.env`)

Create `.env` from template:

```bash
cp .example.env .env
```

Set values:

```env
SECRET_KEY=dev-secret-key-123
DJANGORLAR_ENV_ID=local

DB_NAME=booking_clone_db
DB_USER=booking_user
DB_PASSWORD=booking_pass_123
DB_HOST=localhost
DB_PORT=5432
```

---

## 9. Run Project

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

App URLs:

- Admin: `http://127.0.0.1:8000/admin/`
- API root (City): `http://127.0.0.1:8000/api/cities/`

---

## 10. City API Documentation

Base URL: `/api/cities/`

### 10.1 Create city

`POST /api/cities/`

Request:

```json
{
  "name": "Almaty",
  "country": "Kazakhstan"
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "Almaty",
  "country": "Kazakhstan",
  "created_at": "2026-03-11T16:45:00.123456Z"
}
```

### 10.2 List cities

`GET /api/cities/`

Response `200`:

```json
[
  {
    "id": 1,
    "name": "Almaty",
    "country": "Kazakhstan",
    "created_at": "2026-03-11T16:45:00.123456Z"
  }
]
```

### 10.3 Retrieve city by id

`GET /api/cities/{id}/`

### 10.4 Update city

`PATCH /api/cities/{id}/`

Request:

```json
{
  "name": "Astana"
}
```

### 10.5 Delete city

`DELETE /api/cities/{id}/`

### 10.6 Validation behavior

If duplicate (`name`, `country`) is sent, DB unique constraint prevents insert/update.
API returns validation/DB error response (4xx).

---

## 11. Team Workflow (Git)

We use feature branches and pull requests.

Typical flow:

```bash
git checkout main
git pull origin main
git checkout -b feature/<task-name>
# code changes
# tests/checks
git add .
git commit -m "Meaningful commit message"
git push -u origin feature/<task-name>
```

Then open PR to `main` and request review.

---

## 12. Current Team Branches (Project Progress)

The repository includes separate branches for modules in progress:

- `feature/city-crud`
- `feature/auth-and-users`
- `feature/booking`
- `feature/reviews`
- `feature/loggers`
- `feature/apartment-model`

This branch contains the City CRUD implementation and documentation update.

---

## 13. Troubleshooting

### Problem: `AUTH_USER_MODEL refers to model 'auths.User'` / `'auths.CustomUser'`

Reason: app `auths` is not installed in current branch.

Fix for this branch:

```python
AUTH_USER_MODEL = "auth.User"
```

### Problem: `pg_isready` shows `no response`

Check service and logs:

```bash
brew services list | grep -i postgres
tail -n 80 /opt/homebrew/var/log/postgresql@14.log
```

If `postgresql.conf` is missing:

```bash
cp /opt/homebrew/var/postgresql@14/postgresql.conf.bak /opt/homebrew/var/postgresql@14/postgresql.conf
brew services restart postgresql@14
```

If syntax error near `log_t imezone`:

```bash
perl -pi -e 's/^log_t\s+imezone\s*=/log_timezone =/' /opt/homebrew/var/postgresql@14/postgresql.conf
brew services restart postgresql@14
```

---

## 14. Verification Checklist

Before creating PR:

- `python manage.py check` passes
- migrations are created and applied
- `/api/cities/` returns `200`
- create/update/delete city works
- duplicate `(name, country)` is rejected

---

## 15. Next Steps

Planned backend expansion:

- connect City to apartments/properties entities
- authentication and permissions per endpoint
- booking flow with status transitions
- reviews module with rating aggregation
- centralized logging and monitoring

---

## Team Note

This documentation is maintained by the team and updated per branch scope.
When a module is merged to `main`, README sections should be synchronized accordingly.
