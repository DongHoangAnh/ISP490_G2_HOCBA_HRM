#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đồng bộ **branding website công khai** (trang /jobs, header, footer, trang chủ)
từ DB nguồn sang DB đích.

    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose \
        -f docker-compose.yml -f docker-compose.local.yml -f <file port> \
        run --rm --no-deps -v "$PWD/tools:/tools" odoo python3 /tools/sync_website_branding.py

Env:
    SRC_DB      DB nguồn (mặc định neondb — bản restore nằm cùng Postgres local)
    DST_DB      DB đích  (mặc định hocba_demo)
    WEBSITE_ID  id bản ghi website ở CẢ HAI DB (mặc định 1)

VÌ SAO CẦN SCRIPT NÀY: phần rebrand trang tuyển dụng công khai được làm bằng
trình soạn website của Odoo, tức là nằm trong bảng `ir_ui_view` của riêng DB đó,
KHÔNG có dòng nào trong repo. DB mới cài `website` sẽ ra bộ mặc định của Odoo
("My Website" / "Your Logo" / +1 555-555-5556).

Chép 3 nhóm:
  · website (id=WEBSITE_ID)  — tên site, social, custom_code_head (CSS màu brand)
  · res_company (công ty 1)  — điện thoại, email hiển thị ở footer
  · ir_ui_view website_id=WEBSITE_ID — toàn bộ view riêng của site: bản đã sửa
    tay (header/footer/trang chủ/trang chi tiết tin tuyển dụng) LẪN bản chỉ bật
    tắt tuỳ chọn (`active`), vì Odoo bật/tắt tuỳ chọn giao diện bằng cách bật
    tắt view.

Cách ghi: viết vào `arch_base` KÈM context website_id → Odoo tự chạy cơ chế COW
(website/models/ir_ui_view.py::write) để sinh bản riêng cho site, thay vì sửa
view gốc của module. View do trình soạn tự sinh (`website.key_xxxxxx`) không có
bản gốc để COW nên được tạo mới.

⚠️ `arch_updated` được đồng bộ theo đúng bản nguồn: container đang chạy `--dev=xml`,
view nào `arch_updated=False` sẽ bị Odoo nạp đè lại từ file XML của module
(ir_ui_view.py:225) — ghi arch xong mà không giữ cờ này thì đổi lại như cũ.

Chạy lại được nhiều lần. KHÔNG đụng dữ liệu nghiệp vụ (nhân sự, tuyển dụng, lương…).
"""

import logging
import os
import sys

import psycopg2
import psycopg2.extras

import odoo
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

_log = logging.getLogger('sync_web')
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

SRC_DB = os.environ.get('SRC_DB', 'neondb')
DST_DB = os.environ.get('DST_DB', 'hocba_demo')
WEBSITE_ID = int(os.environ.get('WEBSITE_ID', '1'))

DB_HOST = os.environ.get('HOST', 'db')
DB_PORT = os.environ.get('PORT', '5432')
DB_USER = os.environ.get('USER', 'odoo')
DB_PASS = os.environ.get('PASSWORD', 'odoo_password')

# Trường branding trên bản ghi website. KHÔNG chép: domain (khác môi trường),
# company_id/user_id/default_lang_id (id có thể lệch), cdn_* (hạ tầng riêng).
SITE_FIELDS = [
    'name', 'social_facebook', 'social_twitter', 'social_linkedin',
    'social_youtube', 'social_instagram', 'social_tiktok', 'social_github',
    'social_discord', 'custom_code_head', 'custom_code_footer', 'cookies_bar',
    'homepage_url', 'robots_txt',
]
COMPANY_FIELDS = ['phone', 'email']


def _txt(val):
    """arch_db/name là jsonb đa ngữ — lấy bản en_US (Odoo dùng làm bản gốc)."""
    if isinstance(val, dict):
        return val.get('en_US') or next(iter(val.values()), None)
    return val


def fetch_source():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                            password=DB_PASS, dbname=SRC_DB)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM website WHERE id = %s", (WEBSITE_ID,))
        site = cur.fetchone()
        if not site:
            raise SystemExit('DB nguồn %s không có website id=%s' % (SRC_DB, WEBSITE_ID))
        cur.execute("SELECT phone, email FROM res_company ORDER BY id LIMIT 1")
        company = cur.fetchone()
        # Sắp xếp: view không kế thừa trước, view kế thừa sau — để khi tạo mới
        # thì view cha đã tồn tại mà trỏ inherit_id vào.
        # CHỈ lấy view qweb (giao diện web). Bản nguồn còn 4 view `form` của
        # res.company mang key `website.key_xxxxxx` — đó là bản COW Odoo tự sinh
        # khi sửa thông tin công ty trong Cài đặt Website, không chứa branding.
        # Chép sang sẽ tạo view form thiếu `model` → ValidationError
        # "Model not found: False" ngay lúc ghi.
        cur.execute("""
            SELECT v.key, v.name, v.arch_db, v.active, v.priority, v.mode,
                   v.type, v.model, v.customize_show, v.arch_updated, v.visibility,
                   p.key AS inherit_key
              FROM ir_ui_view v
              LEFT JOIN ir_ui_view p ON p.id = v.inherit_id
             WHERE v.website_id = %s AND v.type = 'qweb'
             ORDER BY (v.inherit_id IS NOT NULL), v.id
        """, (WEBSITE_ID,))
        views = cur.fetchall()
        return site, company, views
    finally:
        conn.close()


def sync_site(env, site, company):
    vals = {f: site[f] for f in SITE_FIELDS if site.get(f) is not None}
    web = env['website'].browse(WEBSITE_ID)
    if not web.exists():
        raise SystemExit('DB đích %s không có website id=%s — cài module '
                         'website trước.' % (DST_DB, WEBSITE_ID))
    web.write(vals)
    _log.info('Website: name=%r · facebook=%r · custom_code_head=%s ký tự',
              vals.get('name'), vals.get('social_facebook') or '',
              len(vals.get('custom_code_head') or ''))

    comp_vals = {f: company[f] for f in COMPANY_FIELDS if company.get(f)}
    if comp_vals:
        env['res.company'].browse(web.company_id.id).write(comp_vals)
        _log.info('Công ty: %s', ' · '.join('%s=%s' % kv for kv in comp_vals.items()))


def sync_views(env, views):
    View = env['ir.ui.view'].sudo().with_context(active_test=False)
    created = updated = skipped = 0
    arch_flags = []          # (key, arch_updated) — ép lại sau khi ghi xong

    for src in views:
        key, arch = src['key'], _txt(src['arch_db'])
        if not arch:
            _log.warning('  ! %s: arch rỗng ở nguồn, bỏ qua', key)
            skipped += 1
            continue
        vals = {
            'arch_base': arch,
            'active': src['active'],
            'priority': src['priority'],
            'customize_show': src['customize_show'],
        }
        specific = View.search([('key', '=', key), ('website_id', '=', WEBSITE_ID)], limit=1)
        if specific:
            specific.write(vals)
            updated += 1
            _log.info('  ~ %s', key)
            arch_flags.append((key, src['arch_updated']))
            continue

        generic = View.search([('key', '=', key), ('website_id', '=', False)], limit=1)
        if generic:
            # Ghi kèm context website_id → Odoo tự tạo bản riêng (COW) thay vì
            # sửa view gốc của module.
            generic.with_context(website_id=WEBSITE_ID).write(vals)
            updated += 1
            _log.info('  + %s (COW)', key)
            arch_flags.append((key, src['arch_updated']))
            continue

        # View do trình soạn website tự sinh (website.key_xxxxxx): không có bản
        # gốc để COW → tạo mới hẳn.
        inherit_id = False
        if src['inherit_key']:
            parent = View.search([('key', '=', src['inherit_key']),
                                  ('website_id', '=', WEBSITE_ID)], limit=1)
            parent = parent or View.search([('key', '=', src['inherit_key']),
                                            ('website_id', '=', False)], limit=1)
            if not parent:
                _log.warning('  ! %s: không tìm thấy view cha %s, bỏ qua',
                             key, src['inherit_key'])
                skipped += 1
                continue
            inherit_id = parent.id
        View.create(dict(vals,
                         key=key,
                         name=_txt(src['name']) or key,
                         type=src['type'],
                         model=src['model'] or False,
                         mode=src['mode'],
                         inherit_id=inherit_id,
                         website_id=WEBSITE_ID))
        created += 1
        _log.info('  * %s (tạo mới)', key)
        arch_flags.append((key, src['arch_updated']))

    # Ép cờ arch_updated đúng như nguồn. Ghi `arch_base` luôn bật cờ này
    # (ir_ui_view.py:647), nhưng ở nguồn có 71 view chỉ bật/tắt chứ không sửa
    # arch — để cờ sai thì `--dev=xml` KHÔNG nạp lại được bản vá từ file nữa.
    for key, flag in arch_flags:
        env.cr.execute(
            "UPDATE ir_ui_view SET arch_updated = %s WHERE key = %s AND website_id = %s",
            (flag, key, WEBSITE_ID))
    return created, updated, skipped


def main():
    odoo.tools.config.parse_config([
        '-c', '/etc/odoo/odoo.conf', '-d', DST_DB,
        '--addons-path=/mnt/extra-addons',
        '--db_host=%s' % DB_HOST, '--db_port=%s' % DB_PORT,
        '--db_user=%s' % DB_USER, '--db_password=%s' % DB_PASS,
    ])
    site, company, views = fetch_source()
    _log.info('Nguồn %s: website %r · %s view riêng của site',
              SRC_DB, _txt(site['name']), len(views))

    reg = Registry(DST_DB)
    with reg.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {'lang': 'en_US'})
        if not env['ir.module.module'].search_count(
                [('name', '=', 'website_hr_recruitment'), ('state', '=', 'installed')]):
            _log.error('DB đích chưa cài website_hr_recruitment — dừng.')
            return 1
        sync_site(env, site, company)
        created, updated, skipped = sync_views(env, views)
        cr.commit()

    _log.info('\n✅ Xong: %s view tạo mới · %s view cập nhật · %s bỏ qua.\n'
              'Nhớ restart container serving để xoá cache view/asset.',
              created, updated, skipped)
    return 0


if __name__ == '__main__':
    sys.exit(main())
