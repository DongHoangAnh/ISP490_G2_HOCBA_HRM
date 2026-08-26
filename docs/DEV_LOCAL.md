# Chạy môi trường dev

Repo hỗ trợ 2 cách chạy. **Khuyến nghị: dev hằng ngày dùng db LOCAL, demo/tích hợp dùng Neon.**

## 1. Db local (Postgres trong Docker) — khuyến nghị khi dev

```bash
# Lần đầu: cần file .env tồn tại (giá trị không dùng tới khi chạy local)
cp .env.example .env

docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

- Db: `hocba_hrm`, user/pass: `odoo` / `odoo_password`, port 5432.
- PostgreSQL local dùng major version 15 để tương thích với volume dữ liệu
  offline hiện hữu. Không đổi trực tiếp image sang major version khác; phải
  dump/restore hoặc `pg_upgrade` để tránh DB không khởi động.
- `docker-compose.local.yml` đã bật `--update` toàn bộ module → sau khi `git pull`
  chỉ cần restart container là schema tự nâng (không bị lỗi "Model ... has no table").
- Dữ liệu nằm trong volume `postgres_data`, không mất khi recreate container.

## 2. Neon cloud (mặc định của `docker-compose.yml`)

```bash
cp .env.example .env   # rồi điền connection string branch Neon CỦA BẠN
docker compose up -d
```

- Mỗi người dùng **branch Neon riêng** (lấy từ console.neon.tech) — đừng trỏ chung
  một branch khi dev, vì `--init`/upgrade của người này sẽ đè môi trường người kia.

## Lưu ý chung

- Khi có module mới: thêm vào `--init` ở **cả hai** file compose.
- Test nhanh db đang là cái nào: mở `http://localhost:8069/web/database/list`.
- Một máy có thể có Odoo native Windows chiếm port 8069 — nếu thấy db lạ,
  truy cập bằng `http://[::1]:8069` để chắc chắn vào Docker.
