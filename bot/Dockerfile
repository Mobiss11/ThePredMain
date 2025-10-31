FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir \
    aiogram==3.22.0 \
    asyncpg==0.30.0 \
    python-dotenv==1.0.0 \
    redis==5.0.1

COPY . .

CMD ["python", "main.py"]
