FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    quart==0.20.0 \
    python-dotenv==1.0.0

COPY . .

CMD ["python", "main.py"]
