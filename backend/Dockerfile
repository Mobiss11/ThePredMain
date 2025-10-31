FROM python:3.13-slim

WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.32.1 \
    pydantic==2.11.10 \
    pydantic-settings==2.7.0 \
    sqlalchemy==2.0.36 \
    asyncpg==0.30.0 \
    alembic==1.14.0 \
    redis==5.0.1 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6 \
    aiohttp==3.13.2 \
    sentry-sdk==1.39.2 \
    prometheus-client==0.19.0 \
    python-dotenv==1.0.0

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
