FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /app/requirements/
COPY requirements/development.txt /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/base.txt

COPY . /app/

RUN python manage.py collectstatic --noinput || true

RUN chmod +x /app/manage.py

EXPOSE 8000

CMD ["gunicorn", "config.asgi:application", "-b", "0.0.0.0:8000", "-w", "4"]
