#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh script seed Odoo để tạo tài khoản đăng nhập HRM cho giáo viên CMS.

Đọc file JSON giáo viên mới nhất ở tools/cms/exports/ → ghi ra
_demo_seed/import_cms_teachers.py (dữ liệu nhúng sẵn) để chạy qua `odoo shell`.

    python tools/cms/build_teacher_seed.py

Sau đó chạy (DRY-RUN trước — chỉ đọc, không ghi):
    docker compose -f docker-compose.yml run --rm --no-deps -T odoo \\
      odoo shell -d neondb --addons-path=/mnt/extra-addons --no-http \\
      < _demo_seed/import_cms_teachers.py
Khi ưng, đổi DRY_RUN=False ở đầu file sinh ra rồi chạy lại để ghi thật.
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def main():
    files = sorted(glob.glob(os.path.join(HERE, "exports", "teachers_*.json")))
    if not files:
        raise SystemExit("Chưa có file export. Chạy export_teachers.py trước.")
    src = files[-1]
    with open(src, encoding="utf-8") as f:
        rows = json.load(f)

    # Chỉ giữ trường cần cho HRM, bỏ avatar/desc dài.
    teachers = [{
        "full_name": r.get("full_name") or "",
        "email": (r.get("email") or "").strip(),
        "phone": r.get("phone_number") or "",
        "code": r.get("unique_code") or "",
    } for r in rows if (r.get("email") or "").strip()]

    out_dir = os.path.join(ROOT, "_demo_seed")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "import_cms_teachers.py")
    data_literal = json.dumps(teachers, ensure_ascii=False, indent=2)

    with open(out, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE.replace("__DATA__", data_literal)
                         .replace("__SRC__", os.path.basename(src)))
    print("Đã sinh:", out)
    print("Số giáo viên:", len(teachers), "(nguồn:", os.path.basename(src) + ")")
    print("Mặc định DRY_RUN=True — chạy qua odoo shell để xem trước.")


# Script chạy BÊN TRONG odoo shell (đã có sẵn biến `env`).
_TEMPLATE = '''# -*- coding: utf-8 -*-
# TỰ SINH từ tools/cms/build_teacher_seed.py (nguồn: __SRC__). Đừng sửa tay.
# Tạo tài khoản đăng nhập HRM (self-service) cho giáo viên import từ CMS.
# Chạy: odoo shell -d <db> ... < _demo_seed/import_cms_teachers.py

DRY_RUN = True              # True = chỉ đếm, KHÔNG ghi. Đổi False để ghi thật.
DEFAULT_PASSWORD = "Hocba@2026"

TEACHERS = __DATA__

Employee = env["hr.employee"].sudo()
Users = env["res.users"].sudo().with_context(active_test=False)
teacher_type = env.ref("hocba_employees.employee_type_teacher")
base_user_group = env.ref("base.group_user")

created_emp = created_user = linked = skipped = 0
for t in TEACHERS:
    email = t["email"].strip()
    if not email:
        continue
    emp = Employee.search([("work_email", "=", email)], limit=1)
    usr = Users.search([("login", "=", email)], limit=1)

    if emp and usr and emp.user_id.id == usr.id:
        skipped += 1
        continue

    print(("[DRY] " if DRY_RUN else "") + "xu ly: %-40s emp=%s user=%s" % (
        email, bool(emp), bool(usr)))
    if DRY_RUN:
        if not emp:
            created_emp += 1
        if not usr:
            created_user += 1
        continue

    if not emp:
        emp = Employee.create({
            "name": t["full_name"] or email,
            "work_email": email,
            "work_phone": t["phone"] or False,
            "x_employee_type_id": teacher_type.id,
            "x_employment_status": "parttime",   # tránh ràng buộc BR-010 (official)
        })
        created_emp += 1
    if not usr:
        usr = Users.create({
            "name": t["full_name"] or email,
            "login": email,
            "password": DEFAULT_PASSWORD,
            "group_ids": [(6, 0, [base_user_group.id])],  # Odoo 19: group_ids
        })
        created_user += 1
    if emp.user_id.id != usr.id:
        emp.user_id = usr.id
        linked += 1

print("=" * 60)
print("DRY_RUN =", DRY_RUN)
print("Tong giao vien dau vao:", len(TEACHERS))
print("Se tao / da tao  hr.employee:", created_emp)
print("Se tao / da tao  res.users  :", created_user)
print("Lien ket emp<->user:", linked, "| Bo qua (da co):", skipped)
if not DRY_RUN:
    env.cr.commit()
    print(">>> DA COMMIT vao DB.")
else:
    print(">>> DRY-RUN: khong ghi gi. Doi DRY_RUN=False de chay that.")
'''


if __name__ == "__main__":
    main()
