#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# IntraStack CRM Module — Auto Deploy Script
# Deploys the intrastack_crm module to Odoo 17 running in Docker
# ══════════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  IntraStack CRM Module — Deploy Script${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# ── Step 0: Detect Docker container ──────────────────────────────────────────
echo -e "${YELLOW}[1/5] Detecting Odoo Docker container...${NC}"

# Try to find the Odoo container automatically
ODOO_CONTAINER=$(sudo docker ps --filter "ancestor=odoo:17" --format "{{.Names}}" 2>/dev/null | head -1)

if [ -z "$ODOO_CONTAINER" ]; then
    # Try broader search
    ODOO_CONTAINER=$(sudo docker ps --format "{{.Names}}" 2>/dev/null | grep -i "odoo" | head -1)
fi

if [ -z "$ODOO_CONTAINER" ]; then
    echo -e "${RED}ERROR: Could not find Odoo Docker container.${NC}"
    echo "Available containers:"
    sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    echo ""
    echo "Please set the container name manually:"
    echo "  export ODOO_CONTAINER=your_container_name"
    echo "  bash deploy.sh"
    exit 1
fi

echo -e "${GREEN}  ✓ Found Odoo container: ${ODOO_CONTAINER}${NC}"

# ── Step 1: Detect addons path inside container ─────────────────────────────
echo -e "${YELLOW}[2/5] Detecting addons path...${NC}"

# Check common addons paths
ADDONS_PATH=""
for path in "/mnt/extra-addons" "/opt/odoo/custom-addons" "/opt/odoo/addons" "/var/lib/odoo/addons"; do
    if sudo docker exec "$ODOO_CONTAINER" test -d "$path" 2>/dev/null; then
        ADDONS_PATH="$path"
        break
    fi
done

if [ -z "$ADDONS_PATH" ]; then
    # Try to get from odoo.conf
    ADDONS_PATH=$(sudo docker exec "$ODOO_CONTAINER" grep -oP 'addons_path\s*=\s*\K.*' /etc/odoo/odoo.conf 2>/dev/null | tr ',' '\n' | grep -v '/usr/lib' | head -1 | tr -d '[:space:]')
fi

if [ -z "$ADDONS_PATH" ]; then
    ADDONS_PATH="/mnt/extra-addons"
    echo -e "${YELLOW}  ⚠ Could not detect addons path, using default: ${ADDONS_PATH}${NC}"
else
    echo -e "${GREEN}  ✓ Addons path: ${ADDONS_PATH}${NC}"
fi

# ── Step 2: Copy module to container ─────────────────────────────────────────
echo -e "${YELLOW}[3/5] Copying module to container...${NC}"

MODULE_DIR="$(cd "$(dirname "$0")/.." && pwd)/intrastack_crm"

if [ ! -d "$MODULE_DIR" ]; then
    # Try current directory
    MODULE_DIR="$(pwd)/intrastack_crm"
fi

if [ ! -d "$MODULE_DIR" ]; then
    echo -e "${RED}ERROR: Cannot find intrastack_crm module directory.${NC}"
    echo "Expected at: $MODULE_DIR"
    exit 1
fi

# Remove old version if exists
sudo docker exec "$ODOO_CONTAINER" rm -rf "${ADDONS_PATH}/intrastack_crm" 2>/dev/null || true

# Copy new version
sudo docker cp "$MODULE_DIR" "${ODOO_CONTAINER}:${ADDONS_PATH}/intrastack_crm"
echo -e "${GREEN}  ✓ Module copied to ${ADDONS_PATH}/intrastack_crm${NC}"

# ── Step 3: Set permissions ──────────────────────────────────────────────────
echo -e "${YELLOW}[4/5] Setting file permissions...${NC}"
sudo docker exec "$ODOO_CONTAINER" chown -R odoo:odoo "${ADDONS_PATH}/intrastack_crm" 2>/dev/null || true
echo -e "${GREEN}  ✓ Permissions set${NC}"

# ── Step 4: Restart Odoo ─────────────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Restarting Odoo container...${NC}"
sudo docker restart "$ODOO_CONTAINER"
echo -e "${GREEN}  ✓ Odoo restarted${NC}"

# Wait for Odoo to be ready
echo -e "${YELLOW}  Waiting for Odoo to start...${NC}"
sleep 10

# Check if Odoo is responding
for i in {1..12}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/ | grep -q "200\|303"; then
        echo -e "${GREEN}  ✓ Odoo is ready!${NC}"
        break
    fi
    if [ $i -eq 12 ]; then
        echo -e "${YELLOW}  ⚠ Odoo may still be starting. Check manually at http://crm.intrastack.com${NC}"
    fi
    sleep 5
done

echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deploy complete!${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Go to ${BLUE}https://crm.intrastack.com${NC}"
echo -e "  2. Login as admin"
echo -e "  3. Go to ${YELLOW}Settings → Activate Developer Mode${NC}"
echo -e "  4. Go to ${YELLOW}Apps → Update Apps List${NC} (top menu)"
echo -e "  5. Search for ${GREEN}\"IntraStack\"${NC}"
echo -e "  6. Click ${GREEN}Install${NC}"
echo -e ""
echo -e "  To install with demo data, make sure ${YELLOW}Demo Data${NC} is enabled"
echo -e "  in Settings → General Settings before installing the module."
echo ""
