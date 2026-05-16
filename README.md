# Booking Clone — Team Backend Project (Django + DRF + Docker)

This repository contains our team backend project: a simplified booking service API.
The project is built for university practice and is organized as incremental modules
(properties, users/auth, bookings, reviews, notifications, logging, localization).

---

## 1. Project Goal

The goal of this project is to learn how to design a real backend service in stages:

- model domain entities in Django ORM
- expose REST API with Django REST Framework
- work with a production-like backend stack and supporting services
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
City model (ORM) <-> Database
```

### Layer responsibilities

- **Model**: schema and DB constraints
- **Serializer**: input/output validation and representation
- **ViewSet**: REST actions (`list/create/retrieve/update/destroy`)
- **Router**: endpoint registration

---

## 4. Tech Stack

- Python 3.12
- Django 5.1
- Django REST Framework 3.16
- SQLite
- Redis
- Celery + Celery Beat
- Daphne (ASGI)
- Nginx
- Flower
- Docker Compose

---

## 5. Repository Structure

```text
booking-clone/
├── Dockerfile
├── docker-compose.yml
├── booking_clone/
│   ├── apps/
│   │   ├── properties/
│   │   ├── users/
│   │   ├── bookings/
│   │   ├── reviews/
│   │   └── notifications/
│   ├── locale/
│   ├── settings/
│   │   ├── base.py
│   │   ├── conf.py
│   │   ├── env/
│   │   └── urls.py
│   ├── templates/
│   ├── .env
│   ├── .env.example
│   ├── manage.py
│   └── pytest.ini
├── nginx/
├── requirements/
├── scripts/
└── README.md
```

---

## 6. Run With Docker Compose

### 6.1 Clone and enter project

```bash
git clone https://github.com/5ar1ja/booking-clone.git
cd booking-clone
```

### 6.2 Prepare environment variables

Docker Compose reads environment variables from:

```text
booking_clone/.env
```

Create it from the template if needed:

```bash
cp booking_clone/.env.example booking_clone/.env
```

Recommended values for Docker:

```env
BOOKING_ENV_ID=dev
BOOKING_SECRET_KEY=your-secret-key-here
BOOKING_DEBUG=True
BOOKING_ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_HOST=redis
REDIS_PORT=6379
FLOWER_USER=admin
FLOWER_PASSWORD=change_me_in_production
```

### 6.3 Build and start all services

```bash
docker compose up --build -d
```

Services started by Compose:

- `redis`
- `web` (Django via Daphne)
- `celery_worker`
- `celery_beat`
- `flower`
- `nginx`

### 6.4 Verify that Compose started successfully

```bash
docker compose ps
```

Expected result:

- `redis` is `healthy`
- `web`, `celery_worker`, `celery_beat`, and `flower` are `Up`
- `nginx` is also `Up` if host port `80` is available

Useful log checks:

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 celery_worker
docker compose logs --tail=100 celery_beat
docker compose logs --tail=100 nginx
```

### 6.5 Access the running services

If `nginx` starts on port `80`:

- API root: `http://localhost/`
- Swagger docs: `http://localhost/api/docs/swagger/`
- ReDoc: `http://localhost/api/docs/redoc/`
- Flower: `http://localhost:5555/`

### 6.6 If port `80` is already in use

If `nginx` fails with `address already in use`, either free port `80` or change:

```yaml
ports:
  - "80:80"
```

to:

```yaml
ports:
  - "8080:80"
```

Then start again:

```bash
docker compose up --build -d
```

After that, open:

- `http://localhost:8080/`
- `http://localhost:8080/api/docs/swagger/`
- `http://localhost:8080/api/docs/redoc/`

### 6.7 Run without nginx

If you only want the application and worker containers:

```bash
docker compose up -d redis web celery_worker celery_beat flower
```

In this mode, Django is still running inside the `web` container, but it is not directly exposed to the host unless you add a port mapping or run `nginx`.

### 6.8 What starts automatically

When using Docker Compose, you do not need to run Django manually.
The `web` service starts the application automatically with:

```text
daphne -b 0.0.0.0 -p 8000 settings.asgi:application
```

Its entrypoint also:

- waits for Redis
- runs migrations
- collects static files
- compiles translations

### 6.9 Stop the stack

```bash
docker compose down
```

Remove containers and volumes:

```bash
docker compose down -v
```

---

## 7. Run Locally Without Docker

### 7.1 Enter the app directory

```bash
cd booking_clone
```

### 7.2 Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 7.3 Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r ../requirements/dev.txt
```

### 7.4 Prepare environment variables

```bash
cp .env.example .env
```

For local development:

```env
BOOKING_ENV_ID=dev
BOOKING_SECRET_KEY=your-secret-key-here
BOOKING_DEBUG=True
BOOKING_ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 7.5 Run the project

```bash
python manage.py check
python manage.py migrate
python manage.py runserver
```

App URLs:

- Admin: `http://127.0.0.1:8000/admin/`
- Swagger docs: `http://127.0.0.1:8000/api/docs/swagger/`
- ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`

---

## 10. City API Documentation

Base URL: `/api/cities/`

### 10.0 Available endpoints (quick list)

- `GET /api/cities/` - list cities
- `POST /api/cities/` - create city
- `GET /api/cities/{id}/` - retrieve city
- `PUT /api/cities/{id}/` - full update
- `PATCH /api/cities/{id}/` - partial update
- `DELETE /api/cities/{id}/` - delete city

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

## 12. All Team Branches and Endpoints (Combined Catalog)

The repository contains separate feature branches. Endpoints differ by branch because
not all modules are merged into `main` yet.

### 12.1 Branch list

- `main`
- `feature/city-crud`
- `feature/city-crud-z3sker`
- `feature/auth-and-users`
- `feature/apartment-model`
- `feature/booking`
- `feature/reviews`
- `feature/loggers`

### 12.2 Endpoint map by branch

#### `main`

- `GET /admin/` (Django admin)

#### `feature/city-crud`

- `GET /api/cities/`
- `POST /api/cities/`
- `GET /api/cities/{id}/`
- `PUT /api/cities/{id}/`
- `PATCH /api/cities/{id}/`
- `DELETE /api/cities/{id}/`

#### `feature/auth-and-users`

Base prefix: `/users/`

- `POST /users/register/`
- `POST /users/login/`
- `GET /users/personal-info/`
- `PATCH /users/update-profile/`
- `POST /users/token/refresh/`

#### `feature/apartment-model`

Includes user endpoints from `feature/auth-and-users`, plus property endpoints:

- `GET /properties/apartments/`
- `POST /properties/apartments/`
- `GET /properties/apartments/{id}/`
- `PUT /properties/apartments/{id}/`
- `PATCH /properties/apartments/{id}/`
- `DELETE /properties/apartments/{id}/`

#### `feature/booking`

Includes users + properties, plus booking endpoints:

- `GET /apps.bookings/bookings/`
- `POST /apps.bookings/bookings/`
- `GET /apps.bookings/bookings/{id}/`
- `PUT /apps.bookings/bookings/{id}/`
- `PATCH /apps.bookings/bookings/{id}/`
- `DELETE /apps.bookings/bookings/{id}/`
- `PATCH /apps.bookings/bookings/{id}/cancel/`
- `PATCH /apps.bookings/bookings/{id}/update-status/`

Note: in this branch URL prefix is literally `apps.bookings/` in `settings/urls.py`.

#### `feature/reviews` and `feature/loggers`

Includes users + properties + bookings + reviews:

Users:

- `POST /users/register/`
- `POST /users/login/`
- `GET /users/personal-info/`
- `PATCH /users/update-profile/`
- `POST /users/token/refresh/`

Properties:

- `GET /properties/apartments/`
- `POST /properties/apartments/`
- `GET /properties/apartments/{id}/`
- `PUT /properties/apartments/{id}/`
- `PATCH /properties/apartments/{id}/`
- `DELETE /properties/apartments/{id}/`
- `GET /properties/apartments/{id}/reviews/` (custom action)

Bookings:

- `GET /bookings/`
- `POST /bookings/`
- `GET /bookings/{id}/`
- `PUT /bookings/{id}/` (blocked with `405` in these branches)
- `PATCH /bookings/{id}/` (blocked with `405` in these branches)
- `DELETE /bookings/{id}/` (blocked with `405` in these branches)
- `PATCH /bookings/{id}/cancel/`
- `PATCH /bookings/{id}/update-status/`

Reviews:

- `GET /reviews/`
- `POST /reviews/`
- `GET /reviews/{id}/`
- `PUT /reviews/{id}/`
- `PATCH /reviews/{id}/`
- `DELETE /reviews/{id}/`

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
