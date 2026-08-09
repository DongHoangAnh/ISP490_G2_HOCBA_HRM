# Migration 19.0.5.0.0 — bảng vinh danh (khách 2026-08-07, ý D).
# Hook tự sinh chỉ chạy khi TẠO hr.promotion.history, nên các lần bổ nhiệm
# đã có trước khi cài không có mục vinh danh nào → bảng trống trơn ngay sau
# upgrade. Bù lại cho các lần bổ nhiệm gần đây.
# Spec: docs/superpowers/specs/2026-08-09-career-dashboard-honor-board-design.md
import logging

from odoo import api, fields, SUPERUSER_ID

_logger = logging.getLogger(__name__)

BACKFILL_DAYS = 90


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    since = fields.Date.subtract(fields.Date.today(), days=BACKFILL_DAYS)
    promos = env['hr.promotion.history'].search([
        ('x_change_type', '=', 'promotion'),
        ('date_effective', '>=', since),
        ('to_job_id', '!=', False),
    ])
    Honor = env['hb.honor.entry'].with_context(active_test=False)
    # Idempotent: chạy lại không tạo trùng (và unique(promotion_id) chặn nốt).
    done_ids = set(Honor.search(
        [('promotion_id', 'in', promos.ids)]).mapped('promotion_id').ids)
    created = 0
    for p in promos:
        if p.id in done_ids or p.to_job_id == p.from_job_id:
            continue
        Honor.create({
            'employee_id': p.employee_id.id,
            'category': 'promotion',
            'source': 'auto',
            'title': 'Bổ nhiệm %s' % p.to_job_id.name,
            'description': p.reason or False,
            'date_awarded': p.date_effective,
            'promotion_id': p.id,
        })
        created += 1
    _logger.info('19.0.5.0.0: bù %s mục vinh danh từ %s lần bổ nhiệm %s ngày '
                 'gần nhất.', created, len(promos), BACKFILL_DAYS)
