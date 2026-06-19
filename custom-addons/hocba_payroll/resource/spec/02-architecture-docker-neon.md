# 02 — Kiến trúc, Docker & Kết nối Neon

## 1. Tổng quan kiến trúc

```
┌────────────────────┐        JSON-RPC / REST          ┌──────────────────────┐
│  ReactJS (sau)     │ ──────────────────────────────▶ │  Odoo 17 (container)  │
└────────────────────┘                                 │  + OCA payroll        │
                                                        │  + module hocba_payroll│
                                                        └───────────┬──────────┘
                                                                    │ psql (SSL)
                                                                    ▼
                                                        ┌──────────────────────┐
                                                        │  Neon PostgreSQL      │
                                                        │  (serverless, ap-SE-1)│
                                                        └──────────────────────┘
```

- Container **chỉ chạy Odoo web/worker**. **KHÔNG** chạy Postgres trong Docker — Odoo trỏ thẳng Neon.
- Neon yêu cầu **SSL**. Cần `sslmode=require`.
- Neon dùng **connection pooler** (host có hậu tố `-pooler`). Pooler là PgBouncer ở chế độ *transaction pooling* → có thể xung đột với một số thao tác Odoo dùng session/prepared statements.
  - **Khuyến nghị**: dùng **endpoint trực tiếp (non-pooler)** cho Odoo, hoặc nếu buộc dùng pooler thì để Odoo connpool nhỏ và test kỹ. (Xem mục 5.)

---

## 2. Biến môi trường (.env)

> ⚠️ KHÔNG commit `.env` thật. Dùng `.env.example` để chia sẻ. Rotate password sau khi lộ.

`.env.example`:
```dotenv
# ----- Neon PostgreSQL -----
DB_HOST=ep-xxxx-pooler.c-2.ap-southeast-1.aws.neon.tech   # hoặc endpoint non-pooler
DB_PORT=5432
DB_USER=neondb_owner
DB_PASSWORD=__REDACTED__
DB_NAME=neondb
DB_SSLMODE=require

# ----- Odoo -----
ODOO_ADMIN_PASSWD=change_me_master_password
ODOO_HTTP_PORT=8069
```

> Giá trị thật của khách (host/user/db) đã được cung cấp riêng — **điền vào `.env`**, đừng đưa vào repo.

---

## 3. Docker Compose

`docker-compose.yml`:
```yaml
services:
  odoo:
    image: odoo:17.0
    container_name: hocba_odoo
    depends_on: []          # KHÔNG có service db nội bộ — dùng Neon
    ports:
      - "${ODOO_HTTP_PORT:-8069}:8069"
    environment:
      HOST: ${DB_HOST}
      PORT: ${DB_PORT}
      USER: ${DB_USER}
      PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./addons:/mnt/extra-addons          # module custom + OCA payroll
      - ./config/odoo.conf:/etc/odoo/odoo.conf:ro
      - odoo-filestore:/var/lib/odoo
    command: ["odoo", "-c", "/etc/odoo/odoo.conf"]

volumes:
  odoo-filestore:
```

> Odoo image đọc `HOST/PORT/USER/PASSWORD` cho DB. Tuy nhiên để truyền `sslmode` và `dbname`
> cần cấu hình qua `odoo.conf` (image gốc không có env cho sslmode). Xem mục 4.

---

## 4. `config/odoo.conf`

```ini
[options]
admin_passwd = ${ODOO_ADMIN_PASSWD}
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
db_host = ep-xxxx.ap-southeast-1.aws.neon.tech      ; điền từ .env
db_port = 5432
db_user = neondb_owner
db_password = __REDACTED__
db_name = neondb                                     ; cố định 1 DB của Neon
db_sslmode = require
dbfilter = ^neondb$
list_db = False
limit_time_real = 600
workers = 0                                          ; dev: chế độ thread; prod tăng sau
log_level = info
```

> `db_sslmode = require` là tham số quan trọng để bắt tay SSL với Neon.
> Vì Neon là 1 database cố định, set `db_name` + `dbfilter` để Odoo không cố tạo/list DB khác.

---

## 5. Lưu ý đặc thù Neon (quan trọng cho AI/Dev)

1. **Init database**: lần đầu Odoo cần khởi tạo schema (`-i base`). Neon free có thể **auto-suspend** khi idle → lần connect đầu có độ trễ "cold start" vài giây; đặt timeout rộng.
2. **Pooler vs direct**:
   - Endpoint `*-pooler*` = PgBouncer transaction mode. Odoo đôi khi dùng `SET`/advisory locks/`LISTEN-NOTIFY` → nên dùng **direct endpoint** cho ổn định.
   - Nếu chỉ có pooler: tắt `LISTEN/NOTIFY` của Odoo (longpolling) ở dev, và để `db_maxconn` thấp.
3. **Quyền tạo extension**: Odoo cần `unaccent`/`pg_trgm` (tùy). Trên Neon, role owner thường tạo được `CREATE EXTENSION`. Nếu fail → cài extension thủ công qua Neon SQL editor: `CREATE EXTENSION IF NOT EXISTS unaccent;`
4. **Branch Neon**: dùng 1 branch riêng cho dev/test để có thể reset nhanh. Production tách branch khác.
5. **Timezone**: set DB/Odoo về `Asia/Ho_Chi_Minh` để period tháng đúng mốc.

---

## 6. Skeleton module `hocba_payroll`

```
addons/
├── payroll/                      # clone OCA/payroll branch 17.0 (nền salary rule)
└── hocba_payroll/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   ├── hr_employee.py        # field custom (mã NV, Lark, BH, thuế…)
    │   ├── hr_contract.py        # lương HĐ, lương đóng BH, phụ cấp định mức, NPT
    │   ├── hocba_sale_level.py   # bậc hoa hồng (Level→KPI→%COM→lương cứng)
    │   ├── hocba_sale_revenue.py # doanh thu sale theo tháng (input cho hoa hồng)
    │   └── hr_payslip.py         # override compute nếu cần helper VN
    ├── data/
    │   ├── salary_rule_categories.xml
    │   ├── salary_structure_offline.xml
    │   ├── salary_structure_online.xml
    │   ├── salary_rules_offline.xml
    │   ├── salary_rules_online.xml
    │   ├── pit_brackets_data.xml          # 7 bậc thuế (file 05)
    │   └── insurance_config_data.xml      # tỷ lệ BH (file 05)
    ├── security/
    │   └── ir.model.access.csv
    └── tests/
        └── test_payroll_hocba.py          # acceptance tests (file 07)
```

`__manifest__.py`:
```python
{
    "name": "Hoc Ba Education Payroll (VN)",
    "version": "17.0.1.0.0",
    "depends": ["payroll", "hr_contract", "hr"],   # 'payroll' = OCA backport
    "data": [
        "security/ir.model.access.csv",
        "data/salary_rule_categories.xml",
        "data/insurance_config_data.xml",
        "data/pit_brackets_data.xml",
        "data/salary_structure_offline.xml",
        "data/salary_structure_online.xml",
        "data/salary_rules_offline.xml",
        "data/salary_rules_online.xml",
    ],
    "license": "LGPL-3",
    "application": True,
}
```

---

## 7. Lệnh chạy & init

```bash
# 1. clone OCA payroll vào addons
git clone -b 17.0 https://github.com/OCA/payroll addons/payroll

# 2. đổ .env (điền thật) rồi up
docker compose --env-file .env up -d

# 3. init module lần đầu (chạy 1 lần)
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -d neondb -i payroll,hocba_payroll --stop-after-init

# 4. chạy lại bình thường
docker compose restart odoo

# 5. chạy test
docker compose exec odoo odoo -c /etc/odoo/odoo.conf \
    -d neondb -i hocba_payroll --test-enable --stop-after-init \
    --log-level=test
```

> ❓ Nếu OCA `payroll` chưa có branch 17.0 ổn định: fallback = dùng module `om_hr_payroll`
> (Odoo Mates) hoặc port rule sang Enterprise `hr_payroll`. Báo lại PM trước khi đổi nền.
