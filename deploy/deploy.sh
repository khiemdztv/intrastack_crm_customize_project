#!/usr/bin/env bash
set -Eeuo pipefail

ODOO_WAS_STOPPED=0
BACKUP_READY=0

# Invoked indirectly by the ERR trap below.
# shellcheck disable=SC2329
on_error() {
    local line="${1:-unknown}"
    echo "Deployment failed near line ${line}." >&2
    if [[ "${ODOO_WAS_STOPPED}" == "1" ]]; then
        echo "Odoo was left stopped to protect the database." >&2
    fi
    if [[ "${BACKUP_READY}" == "1" ]]; then
        echo "Restore from deploy/backups/ only after checking the target DB and filestore." >&2
    fi
}
trap 'on_error $LINENO' ERR

# Production-safe IntraStack CRM deployment.
# Run from deploy/ after copying .env.example to .env and editing secrets.
# The module is bind-mounted by docker-compose; this script never deletes the
# live addon directory and always takes a PostgreSQL + filestore backup first.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${ROOT_DIR}/deploy"
cd "${DEPLOY_DIR}"

if [[ ! -f .env ]]; then
    echo "Missing deploy/.env. Copy .env.example to .env and set production values." >&2
    exit 1
fi

# shellcheck disable=SC1091
source .env
: "${ODOO_DB:?ODOO_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${ODOO_MASTER_PASSWORD:?ODOO_MASTER_PASSWORD is required}"
if [[ ! "${ODOO_DB}" =~ ^[A-Za-z0-9_]+$ ]]; then
    echo "ODOO_DB may contain only letters, numbers and underscores." >&2
    exit 1
fi
if [[ "${POSTGRES_PASSWORD}" == replace-with-* || "${ODOO_MASTER_PASSWORD}" == replace-with-* ]]; then
    echo "Replace example secrets in deploy/.env before running deployment." >&2
    exit 1
fi

mkdir -p backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DB_BACKUP="backups/${ODOO_DB}_${STAMP}.dump"
FILESTORE_BACKUP="backups/${ODOO_DB}_${STAMP}_filestore.tar.gz"

echo "[1/6] Validating Docker Compose configuration"
docker compose config >/dev/null

echo "[2/6] Starting PostgreSQL"
docker compose up -d db
until docker compose exec -T db pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; do
    sleep 2
done

echo "[3/6] Backing up database and filestore"
docker compose stop odoo >/dev/null 2>&1 || true
ODOO_WAS_STOPPED=1
DB_EXISTS="$(docker compose exec -T db psql -U "${POSTGRES_USER}" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${ODOO_DB}'")"
if [[ "${DB_EXISTS}" == "1" ]]; then
    docker compose exec -T db pg_dump -Fc -U "${POSTGRES_USER}" "${ODOO_DB}" > "${DB_BACKUP}"
    if docker compose run --rm --no-deps --entrypoint sh odoo -c "test -d /var/lib/odoo/filestore/${ODOO_DB}"; then
        docker compose run --rm --no-deps --entrypoint sh odoo -c \
            "tar -C /var/lib/odoo/filestore -czf /backups/$(basename "${FILESTORE_BACKUP}") ${ODOO_DB}"
    fi
    chmod 600 "${DB_BACKUP}" "${FILESTORE_BACKUP}" 2>/dev/null || true
    BACKUP_READY=1
else
    docker compose exec -T db createdb -U "${POSTGRES_USER}" "${ODOO_DB}"
fi

MODULE_STATE="$(docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${ODOO_DB}" -tAc \
    "SELECT state FROM ir_module_module WHERE name='intrastack_crm'" 2>/dev/null || true)"
if [[ "${MODULE_STATE}" == *"installed"* ]]; then
    MODULE_ACTION="-u"
else
    MODULE_ACTION="-i"
fi

echo "[4/6] Installing or upgrading intrastack_crm without demo data"
docker compose run --rm --no-deps odoo odoo \
    -d "${ODOO_DB}" \
    "${MODULE_ACTION}" intrastack_crm \
    --without-demo=all \
    --stop-after-init \
    --log-level=info

echo "[5/6] Starting Odoo"
docker compose up -d odoo
ODOO_WAS_STOPPED=0

echo "[6/6] Waiting for health endpoint"
for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${ODOO_PORT:-8069}/web/health" >/dev/null 2>&1; then
        echo "Deployment complete: Odoo is healthy."
        exit 0
    fi
    sleep 3
done

echo "Odoo did not become healthy. Inspect: docker compose logs --tail=200 odoo" >&2
exit 1
