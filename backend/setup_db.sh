#!/usr/bin/env bash
# Provisions the PostgreSQL role + database this project expects.
# Reads credentials straight from backend/.env so the two can never drift.
set -euo pipefail

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
[ -f "$ENV_FILE" ] || { echo "No .env at $ENV_FILE"; exit 1; }

get() { sed -n "s/^$1=//p" "$ENV_FILE" | head -1; }

DB_NAME="$(get DATABASE_NAME)"
DB_USER="$(get DATABASE_USER)"
DB_PASS="$(get DATABASE_PASSWORD)"
DB_PORT="$(get DATABASE_PORT)"

: "${DB_NAME:?DATABASE_NAME missing in .env}"
: "${DB_USER:?DATABASE_USER missing in .env}"
: "${DB_PASS:?DATABASE_PASSWORD missing in .env}"
: "${DB_PORT:=5432}"

echo "Provisioning role '$DB_USER' and database '$DB_NAME' on port $DB_PORT ..."

# Role: create if missing, otherwise reset the password to match .env.
sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 \
     -v usr="$DB_USER" -v pw="$DB_PASS" <<'PSQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'usr', :'pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'usr') \gexec

SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'usr', :'pw')
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'usr') \gexec

-- Needed so this role can run the test-database suite.
SELECT format('ALTER ROLE %I CREATEDB', :'usr') \gexec
PSQL

# Database: create only if absent (CREATE DATABASE can't run inside a block).
if ! sudo -u postgres psql -p "$DB_PORT" -tAc \
      "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  sudo -u postgres createdb -p "$DB_PORT" -O "$DB_USER" "$DB_NAME"
  echo "Created database $DB_NAME."
else
  echo "Database $DB_NAME already exists; leaving its data untouched."
  sudo -u postgres psql -p "$DB_PORT" -v ON_ERROR_STOP=1 \
       -c "ALTER DATABASE \"$DB_NAME\" OWNER TO \"$DB_USER\";"
fi

# Django needs to create tables in the public schema (PG15+ locks this down).
sudo -u postgres psql -p "$DB_PORT" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
     -c "GRANT ALL ON SCHEMA public TO \"$DB_USER\";" \
     -c "ALTER SCHEMA public OWNER TO \"$DB_USER\";"

echo
echo "Verifying login as $DB_USER ..."
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
     -tAc "SELECT 'connected as ' || current_user || ' to ' || current_database();"
