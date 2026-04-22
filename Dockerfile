FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir "fastapi>=0.111.0" "uvicorn[standard]>=0.29.0" "sqlalchemy>=2.0" "alembic>=1.13.0" "google-cloud-bigquery>=3.20.0" "pydantic-settings>=2.2.0" "httpx>=0.27.0" "psycopg2-binary>=2.9.0"

COPY src/ ./src/
COPY main.py .
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY start.sh .

EXPOSE 8080

CMD ["./start.sh"]
