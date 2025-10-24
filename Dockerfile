FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput || echo "Static files already collected" && \
    exec gunicorn --bind :8080 --workers 2 --threads 4 --timeout 0 jarvis.wsgi:application

