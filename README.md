# Booking Clone - Django REST Framework Backend

Booking Clone is a university backend project that implements a simplified
apartment booking platform. The current `develop` branch contains REST API
modules for users, apartments, bookings, reviews, notifications, API
documentation, localization, Redis caching, and Celery tasks.

## Project Goals

- Build a real backend service with Django and Django REST Framework.
- Use a custom user model with email-based authentication.
- Provide JWT authentication for protected API endpoints.
- Model apartments, locations, bookings, reviews, and notifications.
- Document API endpoints with Swagger and ReDoc.
- Demonstrate background processing, Redis usage, SSE, and localization.
- Keep the project organized for team development through feature branches.

## Tech Stack

- Python 3.14+
- Django 6.0.2
- Django REST Framework 3.16.1
- Simple JWT
- drf-spectacular
- django-filter
- django-redis
- Celery
- django-celery-beat
- Redis
- SQLite for local development
- PostgreSQL settings for production
- pytest / pytest-django
- Ruff

## Main Features

- Custom `CustomUser` model using `email` instead of `username`.
- User registration, login, profile view, and profile update with avatar upload.
- JWT access and refresh tokens.
- Apartment listing CRUD with landlord permissions.
- Country and city models for apartment locations.
- Booking workflow with `pending`, `confirmed`, `completed`, and `cancelled`
  statuses.
- Review workflow for users who completed a stay.
- Notification storage and notification API.
- Server-Sent Events endpoint for notification streaming.
- Redis cache support.
- Celery task for booking confirmation email.
- Celery Beat task for cleaning stale pending bookings.
- English and Russian localization.
- Swagger and ReDoc API documentation.
- Database seeding command.
- Centralized logging configuration.

## Repository Structure

```text
booking-clone/
├── booking_clone/
│   ├── apps/
│   │   ├── bookings/
│   │   ├── core/
│   │   ├── notifications/
│   │   ├── properties/
│   │   ├── reviews/
│   │   └── users/
│   ├── locale/
│   │   ├── en/
│   │   └── ru/
│   ├── logs/
│   ├── settings/
│   │   ├── env/
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── asgi.py
│   │   ├── base.py
│   │   ├── celery.py
│   │   ├── conf.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── templates/
│   ├── .env.example
│   ├── manage.py
│   └── pytest.ini
├── docs/
│   ├── ERD.png
│   └── localization_internationalization.md
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── pyproject.toml
└── README.md
```

## Domain Models

The main database entities are:

- `CustomUser` - email-based user model with landlord and renter roles,
  including an optional avatar image.
- `Country` - country used for apartment location.
- `City` - city linked to a country.
- `Apartment` - rental listing owned by a landlord.
- `Booking` - apartment reservation made by a renter.
- `Review` - rating and comment for an apartment.
- `Notification` - stored user notification, used by API and SSE streaming.

The ER diagram is stored in:

```text
docs/ERD.png
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/5ar1ja/booking-clone.git
cd booking-clone/booking_clone
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r ../requirements/dev.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Useful local values:

```env
BOOKING_ENV_ID=dev
BOOKING_SECRET_KEY=dev-secret-key
BOOKING_DEBUG=True
BOOKING_ALLOWED_HOSTS=localhost,127.0.0.1

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CELERY_DB=1
REDIS_DB=2
BOOKING_REDIS_URL=redis://localhost:6379/2
```

The development settings use SQLite by default:

```text
booking_clone/db.sqlite3
```

### 5. Start Redis

Redis is used for cache-related endpoints and Celery. Start a local Redis
server before running the full test suite or background workers.

Example with Homebrew:

```bash
brew services start redis
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Seed sample data

```bash
python manage.py seed_db
```

To clear existing sample data first:

```bash
python manage.py seed_db --clear
```

### 9. Run the development server

```bash
python manage.py runserver
```

Main local URLs:

- Admin: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/api/docs/swagger/`
- ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Localization demo: `http://127.0.0.1:8000/localization/`

## Authentication

The project uses JWT authentication.

Register:

```http
POST /users/register/
```

Login:

```http
POST /users/login/
```

Refresh token:

```http
POST /users/token/refresh/
```

Authenticated API requests should include the access token:

```http
Authorization: JWT <access_token>
```

The SSE notification stream accepts a token through the `Authorization` header
as `Bearer <access_token>` or through the `token` query parameter.

## API Endpoints

### Users

- `POST /users/register/`
- `POST /users/login/`
- `POST /users/token/refresh/`
- `GET /users/personal-info/`
- `PATCH /users/update-profile/`

User profiles include an optional `avatar` field. `GET /users/personal-info/`
returns the avatar URL when an image is uploaded. `PATCH /users/update-profile/`
accepts normal JSON updates for profile fields and `multipart/form-data` for
avatar uploads.

Example avatar update:

```http
PATCH /users/update-profile/
Authorization: JWT <access_token>
Content-Type: multipart/form-data

avatar=<image file>
```

Uploaded avatars are stored under the configured media root in the `avatars/`
directory. Local media settings are defined in `booking_clone/settings/base.py`.

### Apartments

- `GET /properties/apartments/`
- `POST /properties/apartments/`
- `GET /properties/apartments/{id}/`
- `PUT /properties/apartments/{id}/`
- `PATCH /properties/apartments/{id}/`
- `DELETE /properties/apartments/{id}/`
- `GET /properties/apartments/{id}/reviews/`
- `GET /properties/apartments/{id}/availability/`

Apartment list filters:

- `city`
- `country`
- `rooms`
- `min_price`
- `max_price`
- `check_in`
- `check_out`

### Bookings

- `GET /bookings/`
- `POST /bookings/`
- `GET /bookings/{id}/`
- `PATCH /bookings/{id}/cancel/`
- `PATCH /bookings/{id}/update-status/`

Full update, partial update, and delete are intentionally disabled for normal
booking records. Use the custom actions instead.

Booking statuses:

- `pending`
- `confirmed`
- `completed`
- `cancelled`

### Reviews

- `GET /reviews/`
- `POST /reviews/`
- `GET /reviews/{id}/`
- `PUT /reviews/{id}/`
- `PATCH /reviews/{id}/`
- `DELETE /reviews/{id}/`

Review list filters:

- `apartment`
- `author`
- `rating`
- `min_rating`
- `max_rating`

### Notifications

- `GET /notifications/`
- `GET /notifications/{id}/`
- `PATCH /notifications/{id}/mark-read/`
- `PATCH /notifications/mark-all-read/`
- `GET /notifications/stream/`

The stream endpoint uses Server-Sent Events and can replay missed events with
`Last-Event-ID` or `last_event_id`.

## Permissions

The project uses custom permissions for role-based behavior:

- Landlords can create and manage their own apartments.
- Renters can create bookings.
- Tenants can cancel their own bookings.
- Apartment owners can update booking status for their apartments.
- Review authors can update or delete their own reviews.
- Notifications are scoped to the authenticated user.

## Redis, Celery, and Background Work

Redis is used as:

- Django cache backend through `django-redis`.
- Celery broker/result backend for background tasks.

Celery tasks:

- `send_booking_confirmation_email`
- `cleanup_stale_bookings`

Celery Beat schedule:

- `cleanup-stale-bookings-every-hour`

Run a worker:

```bash
celery -A settings.celery worker -l info
```

Run Celery Beat:

```bash
celery -A settings.celery beat -l info
```

## Localization and Internationalization

Supported languages:

- English: `en`
- Russian: `ru`

Localization is configured in `booking_clone/settings/base.py`.

Language switching endpoint:

```text
/i18n/setlang/
```

Demo page:

```text
/localization/
```

Translation files:

```text
booking_clone/locale/en/LC_MESSAGES/django.po
booking_clone/locale/ru/LC_MESSAGES/django.po
```

Update translations:

```bash
python manage.py makemessages -l en -l ru
python manage.py compilemessages
```

More details are documented in:

```text
docs/localization_internationalization.md
```

## API Documentation

drf-spectacular generates OpenAPI documentation.

- Schema: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc: `/api/docs/redoc/`

The viewsets include schema descriptions, response serializers, request
serializers, permissions, and examples for important endpoints.

## Logging

Logging is configured in `booking_clone/settings/conf.py`.

Log files are written under:

```text
booking_clone/logs/
```

Configured log files:

- `app.log`
- `debug_requests.log`

## Quality Checks

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
python manage.py test
```

or:

```bash
pytest
```

Run Ruff:

```bash
ruff check .
ruff format --check .
```

## Team Workflow

Use separate branches for each task.

```bash
git switch develop
git pull origin develop
git switch -c feature/<task-name>

# make changes

git status
git add <changed-files>
git commit -m "clear commit message"
git push -u origin feature/<task-name>
```

Do not push directly to `develop`. Team admins review branches before merging.

## Notes

- The default remote branch is `develop`.
- The local development database is SQLite.
- Redis should be running for cache, Celery, and tests that touch cached
  endpoints.
- Docker-related work may exist in separate feature branches, but Docker files
  are not part of the current `develop` branch documentation.
