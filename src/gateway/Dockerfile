# src/gateway/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/gateway/app/ ./app/
COPY shared/ ./shared/

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
