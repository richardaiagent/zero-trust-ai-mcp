# src/audit-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/audit-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/audit-service/app/ ./app/
COPY shared/ ./shared/

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
