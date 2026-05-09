FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh

RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["/app/start.sh"]