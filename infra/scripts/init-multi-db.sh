#!/bin/bash
# infra/scripts/init-multi-db.sh
# PostgreSQL 컨테이너 초기화 시 여러 DB 자동 생성
# POSTGRES_MULTIPLE_DATABASES 환경변수에 쉼표로 DB명 지정

set -e

create_db() {
  local db=$1
  echo "DB 생성: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $db;
    GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
  for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
    create_db "$db"
  done
fi
