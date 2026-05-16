FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOOKING_ENV_ID=prod

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gettext \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

COPY requirements/ /app/requirements/

RUN pip install --upgrade pip && pip install -r /app/requirements/prod.txt

COPY . /app/

RUN chmod +x /app/scripts/entrypoint.sh \
    && mkdir -p /app/booking_clone/staticfiles /app/booking_clone/mediafiles /app/data \
    && chown -R appuser:appuser /app

WORKDIR /app/booking_clone

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "settings.asgi:application"]
