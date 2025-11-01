FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir \
    quart==0.20.0 \
    jinja2==3.1.6 \
    aiohttp==3.13.2 \
    python-dotenv==1.0.0

COPY . .

CMD ["python", "main.py"]
