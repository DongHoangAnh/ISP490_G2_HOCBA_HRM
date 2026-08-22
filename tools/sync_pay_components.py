#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đồng bộ **Thành phần lương (Pay Components)** từ DB nguồn sang DB đích.

    docker compose -f docker-compose.yml -f docker-compose.local.yml \
        run --rm -v "$PWD/tools:/tools" odoo python3 /tools/sync_pay_components.py

Env:
    SRC_DB   DB nguồn  (mặc định neondb — bản restore nằm cùng Postgres local)
    DST_DB   DB đích   (mặc định hocba_demo)
    RECOMPUTE 1 = tính lại các phiếu lương nháp/verify sau khi đồng bộ (mặc định 1)

Chép NGUYÊN TRẠNG (kể cả cờ `active`) 3 nhóm cấu hình lương:
  · hb.salary.rule          — Thành phần lương
  · hb.role.allowance.config — Phụ cấp theo vai trò (công thức gross gọi
                               `role_allowance`, thiếu bảng này thì = 0)
  · hb.sale.salary.level     — Bậc lương theo KPI của sale

KHÔNG đụng tới bất kỳ dữ liệu nghiệp vụ nào khác (nhân sự, chấm công, tuyển
dụng, đánh giá…). Danh mục nhóm lương và cấu trúc lương ở hai DB đã trùng mã
nên chỉ **ánh xạ theo mã**, không chép đè — ID hai bên khác nhau (Neon 10–17,
demo 1–8) nên chép thẳng ID sẽ hỏng khoá ngoại.
"""
import logging
import os
import sys

import psycopg2
import psycopg2.extras

import odoo
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

_log = logging.getLogger('sync_pay')
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

SRC_DB = os.environ.get('SRC_DB', 'neondb')
DST_DB = os.environ.get('DST_DB', 'hocba_demo')
RECOMPUTE = os.environ.get('RECOMPUTE', '1') == '1'

DB_HOST = os.environ.get('HOST', 'db')
DB_PORT = os.environ.get('PORT', '5432')
DB_USER = os.environ.get('USER', 'odoo')
DB_PASS = os.environ.get('PASSWORD', 'odoo_password')

RULE_FIELDS = [
    'sequence', 'code', 'amount_type', 'amount_fixed', 'amount_percentage',
    'amount_percentage_base', 'amount_python_compute', 'amount_formula',
    'lookup_source', 'lookup_field', 'condition_type', 'condition_python',
    'appears_on_payslip', 'note', 'active',
]


def fetch_source():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                            password=DB_PASS, dbname=SRC_DB)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT r.*, r.name ->> 'en_US' AS name_text,
                   s.code AS struct_code, c.code AS categ_code,
                   d.module || '.' || d.name AS xmlid
              FROM hb_salary_rule r
              JOIN hb_salary_structure s ON s.id = r.structure_id
              JOIN hb_salary_rule_category c ON c.id = r.category_id
              LEFT JOIN ir_model_data d
                     ON d.model = 'hb.salary.rule' AND d.res_id = r.id
             ORDER BY s.code, r.sequence, r.id
        """)
        rules = cur.fetchall()
        cur.execute("SELECT * FROM hb_role_allowance_config ORDER BY id")
        allowances = cur.fetchall()
        cur.execute("SELECT * FROM hb_sale_salary_level ORDER BY sequence, id")
        levels = cur.fetchall()
        return rules, allowances, levels
    finally:
        conn.close()


def main():
    odoo.tools.config.parse_config([
        '-c', '/etc/odoo/odoo.conf', '-d', DST_DB,
        '--addons-path=/mnt/extra-addons',
        '--db_host=%s' % DB_HOST, '--db_port=%s' % DB_PORT,
        '--db_user=%s' % DB_USER, '--db_password=%s' % DB_PASS,
    ])
    rules, allowances, levels = fetch_source()
    _log.info('Nguồn %s: %s thành phần lương · %s phụ cấp vai trò · %s bậc lương sale',
              SRC_DB, len(rules), len(allowances), len(levels))

    reg = Registry(DST_DB)
    with reg.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {'lang': 'en_US'})
        Rule = env['hb.salary.rule'].sudo().with_context(active_test=False)
        structs = {s.code: s.id for s in
                   env['hb.salary.structure'].sudo().search([])}
        categs = {c.code: c.id for c in
                  env['hb.salary.rule.category'].sudo().with_context(
                      active_test=False).search([])}
        missing = {r['struct_code'] for r in rules} - set(structs)
        missing |= {r['categ_code'] for r in rules} - set(categs)
        if missing:
            _log.error('DB đích thiếu cấu trúc/nhóm lương: %s — dừng.', missing)
            return 1

        # 1. Xoá thành phần lương cũ. Dòng phiếu lương trỏ tới rule qua
        #    `rule_id` nên phải dọn trước; phiếu được tính lại ở bước 5.
        old = Rule.search([])
        if old:
            env.cr.execute(
                "DELETE FROM hb_payslip_line WHERE rule_id IN %s",
                (tuple(old.ids),))
            _log.info('Xoá %s dòng phiếu lương cũ', env.cr.rowcount)
            env.cr.execute(
                "DELETE FROM ir_model_data WHERE model = 'hb.salary.rule' "
                "AND res_id IN %s", (tuple(old.ids),))
            old.unlink()
            _log.info('Xoá %s thành phần lương cũ ở %s', len(old), DST_DB)

        # 2. Tạo lại theo đúng bản nguồn (giữ nguyên cờ active).
        xmlid_rows = []
        for src in rules:
            vals = {f: src[f] for f in RULE_FIELDS}
            vals['name'] = src['name_text']
            vals['structure_id'] = structs[src['struct_code']]
            vals['category_id'] = categs[src['categ_code']]
            rec = Rule.create(vals)
            if src['xmlid']:
                module, xid = src['xmlid'].split('.', 1)
                xmlid_rows.append((module, xid, rec.id))
            _log.info('  + %-16s %-14s %-9s %s', src['struct_code'], src['code'],
                      src['amount_type'], '' if src['active'] else '(đã ẩn)')

        # 3. Gắn lại XML-ID để lần `-u hocba_payroll` sau KHÔNG tạo bản trùng.
        #    noupdate=TRUE: upgrade sẽ không ghi đè giá trị vừa chép từ nguồn.
        for module, xid, res_id in xmlid_rows:
            env.cr.execute("""
                INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
                VALUES (%s, %s, 'hb.salary.rule', %s, TRUE)
                ON CONFLICT (module, name) DO UPDATE
                    SET res_id = EXCLUDED.res_id, noupdate = TRUE
            """, (module, xid, res_id))
        _log.info('Gắn lại %s XML-ID', len(xmlid_rows))

        # 4. Phụ cấp theo vai trò + bậc lương sale (chép nguyên trạng).
        for model, rows, skip in (
                ('hb.role.allowance.config', allowances, ('id', 'create_uid',
                                                          'write_uid',
                                                          'create_date',
                                                          'write_date')),
                ('hb.sale.salary.level', levels, ('id', 'create_uid',
                                                  'write_uid', 'create_date',
                                                  'write_date'))):
            Model = env[model].sudo().with_context(active_test=False)
            Model.search([]).unlink()
            for row in rows:
                vals = {k: v for k, v in row.items()
                        if k not in skip and k in Model._fields}
                Model.create(vals)
            _log.info('%s: chép %s dòng', model, len(rows))

        env.cr.commit()

        # 5. Tính lại phiếu lương chưa chốt để số tiền khớp bộ thành phần mới.
        if RECOMPUTE:
            slips = env['hb.payslip'].sudo().search(
                [('state', 'in', ('draft', 'verify'))])
            ok = 0
            for slip in slips:
                try:
                    with env.cr.savepoint():
                        slip.action_compute_sheet()
                        ok += 1
                except Exception as ex:                  # noqa: BLE001
                    _log.warning('  ! tính lại %s: %s', slip.employee_id.name,
                                 str(ex).strip()[:110])
            _log.info('Tính lại %s/%s phiếu lương', ok, len(slips))
            env.cr.commit()

        env.cr.execute("""
            SELECT s.code, count(*) FILTER (WHERE r.active) AS dang_dung,
                   count(*) FILTER (WHERE NOT r.active) AS da_an
              FROM hb_salary_rule r
              JOIN hb_salary_structure s ON s.id = r.structure_id
             GROUP BY s.code ORDER BY s.code
        """)
        for code, active, hidden in env.cr.fetchall():
            _log.info('KẾT QUẢ %-15s đang dùng %s · đã ẩn %s', code, active, hidden)
    _log.info('✅ Đồng bộ xong: %s → %s', SRC_DB, DST_DB)
    return 0


if __name__ == '__main__':
    sys.exit(main())
