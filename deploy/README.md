# IntraStack CRM production deployment

This deployment uses Odoo 17 Community, PostgreSQL 15 and named volumes. The
custom module is bind-mounted read-only at `/mnt/extra-addons/intrastack_crm`.
Put Nginx/Traefik and TLS in front of the local Odoo ports. Route normal HTTP
traffic to `8069` and `/websocket` to `8072` so Discuss/live notifications work.

```bash
cd /opt/intrastack-crm/deploy
cp .env.example .env
chmod 600 .env
nano .env
docker compose pull
docker compose up -d db
./deploy.sh
docker compose ps
docker compose logs --tail=200 odoo
```

`deploy.sh` creates a compressed PostgreSQL dump and a filestore archive in
`deploy/backups/` before upgrading the module. It always uses
`--without-demo=all`; demo data must never be enabled on the production DB.

For an existing database, run the script during a maintenance window. If the
upgrade fails, keep the containers stopped, preserve the generated backup, and
restore only after verifying the exact database and filestore targets.

Before exposing the service publicly, configure TLS, SMTP, a catchall address,
reverse-proxy `proxy_mode`, websocket routing, firewall rules and an off-host
backup schedule. The compose file disables the database selector (`--no-database-list`)
and never enables demo data.

The values in `.env` are sourced by `deploy.sh`; quote values containing spaces,
`#`, `$`, backticks or shell metacharacters (for example,
`POSTGRES_PASSWORD='a-long-password-with-$-chars'`). Keep this file mode `600`.
