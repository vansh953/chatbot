FROM python:3.11-slim

WORKDIR /app

# System deps: libpq for psycopg2, tesseract for optional OCR on scanned reports
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
