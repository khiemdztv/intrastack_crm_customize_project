# IntraStack CRM Module — Deploy Guide

## Prerequisites
- SSH access to server (163.245.212.92)
- Odoo 17 running in Docker
- `sudo` access for Docker commands

## Quick Deploy (1 Command)

```bash
# SSH into server
ssh steve@163.245.212.92

# Clone/copy the module to server, then run:
cd /path/to/CRM-Customize-project
chmod +x deploy/deploy.sh
bash deploy/deploy.sh
```

## Manual Deploy (Step by Step)

### Step 1: Fix Docker Permission (if needed)
```bash
# Option A: Use sudo
sudo docker ps

# Option B: Add user to docker group (permanent fix)
sudo usermod -aG docker $USER
# Then logout and login again
```

### Step 2: Copy module to server
```bash
# From your local machine:
scp -r intrastack_crm steve@163.245.212.92:/tmp/

# On server:
ssh steve@163.245.212.92
```

### Step 3: Find Docker container name
```bash
sudo docker ps
# Look for the Odoo container (usually "odoo" or similar)
```

### Step 4: Copy module into container
```bash
# Replace CONTAINER_NAME with your actual container name
sudo docker cp /tmp/intrastack_crm CONTAINER_NAME:/mnt/extra-addons/intrastack_crm
sudo docker exec CONTAINER_NAME chown -R odoo:odoo /mnt/extra-addons/intrastack_crm
```

### Step 5: Restart Odoo
```bash
sudo docker restart CONTAINER_NAME
```

### Step 6: Install module in Odoo
1. Go to https://crm.intrastack.com
2. Login as admin
3. Go to **Settings** → **Activate Developer Mode**
4. Go to **Apps** → click **Update Apps List** (in the top menu)
5. Search for **"IntraStack"**
6. Click **Install**

### Step 7: Verify installation
After installation, verify:
- [ ] CRM → Configuration → Sales Teams → 4 pipelines visible
- [ ] CRM → Any opportunity → "IntraStack Deal Info" section with 6 fields
- [ ] Contacts → Configuration → Tags → 10 IntraStack tags
- [ ] Settings → Technical → Automated Actions → 4 rules (R1-R4)
- [ ] Project → 3 template projects
- [ ] Sales → Configuration → Quotation Templates → 3 templates

## Installing with Demo Data

To load demo data (sample contacts, opportunities, projects):

1. Before installing the module, go to **Settings** → **General Settings**
2. Enable **Demo Data** 
3. Then install the IntraStack CRM module
4. Demo data will be loaded automatically

> **Note:** If Demo Data was not enabled before installation, you can reinstall the module to load demo data.

## Troubleshooting

### Module not appearing in Apps list
```bash
# Make sure the module is in the correct addons path
sudo docker exec CONTAINER_NAME ls /mnt/extra-addons/intrastack_crm/
# Should show __manifest__.py and other files

# Check Odoo logs for errors
sudo docker logs CONTAINER_NAME --tail 50
```

### Module installation fails
```bash
# Check logs for specific errors
sudo docker logs CONTAINER_NAME --tail 100 2>&1 | grep -i "error\|traceback"

# Common fix: update module list via CLI
sudo docker exec CONTAINER_NAME odoo -d YOUR_DATABASE --update=intrastack_crm --stop-after-init
```

### Addons path not configured
```bash
# Check current config
sudo docker exec CONTAINER_NAME cat /etc/odoo/odoo.conf | grep addons

# If /mnt/extra-addons is not in the addons_path, add it:
sudo docker exec CONTAINER_NAME bash -c 'echo "addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons" >> /etc/odoo/odoo.conf'
sudo docker restart CONTAINER_NAME
```
