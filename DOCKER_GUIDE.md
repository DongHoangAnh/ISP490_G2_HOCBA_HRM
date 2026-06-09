# HOCBA HRM - Docker Setup Guide

## Prerequisites
- Docker installed
- Docker Compose installed

## Quick Start

### 1. Build & Run
```bash
cd "d:\bpmn for odod\ISP490_G2_HOCBA_HRM"
docker-compose up --build
```

### 2. Access ODOO
- **URL**: http://localhost:8069
- **Username**: admin
- **Password**: admin

### 3. First Login
1. Go to http://localhost:8069
2. Create new database: `hocba_hrm`
3. Fill form with demo data (optional)
4. Click "Create Database"

### 4. Install Custom Modules
1. Click **Apps**
2. Click **Update Apps List** (top menu)
3. Search for `hocba_attendance`
4. Click **Install**
5. Repeat for `hocba_users`

---

## Common Commands

### Start containers
```bash
docker-compose up
```

### Start in background
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f odoo
```

### Stop containers
```bash
docker-compose down
```

### Stop and remove volumes
```bash
docker-compose down -v
```

### Restart
```bash
docker-compose restart
```

### Access ODOO shell
```bash
docker-compose exec odoo odoo shell
```

### View database
```bash
docker-compose exec db psql -U odoo -d hocba_hrm
```

---

## Troubleshooting

### Issue: Port 8069 already in use
Change in `docker-compose.yml`:
```yaml
ports:
  - "8080:8069"  # Access at http://localhost:8080
```

### Issue: Database connection error
Wait 10-15 seconds for PostgreSQL to start before ODOO connects.

### Issue: Modules not showing
1. Stop: `docker-compose down`
2. Remove volume: `docker-compose down -v`
3. Rebuild: `docker-compose up --build`

### Issue: Want to reset everything
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

---

## File Structure
```
ISP490_G2_HOCBA_HRM/
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # ODOO image definition
├── custom-addons/          # Your custom modules
│   ├── hocba_attendance/
│   ├── hocba_users/
│   └── ...
└── addons/                 # ODOO data directory
```

---

## Environment Variables
- `HOST=db` - PostgreSQL host (container name)
- `PORT=5432` - PostgreSQL port
- `USER=odoo` - Database user
- `PASSWORD=odoo_password` - Database password
- `MASTER_PASSWORD=admin_password` - ODOO master password

---

## Performance Notes
- First run takes 2-3 minutes (download image, build, etc.)
- Database initialization takes 30-60 seconds
- Subsequent runs are much faster

---

**Ready? Run:** `docker-compose up`
