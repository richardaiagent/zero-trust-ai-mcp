# src/policy-engine/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/policy-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/policy-engine/app/ ./app/
COPY shared/ ./shared/

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
