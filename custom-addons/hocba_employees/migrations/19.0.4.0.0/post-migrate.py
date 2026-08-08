# Migration 19.0.4.0.0 — bước "Cấp thiết bị làm việc" thành bước không ràng
# buộc thứ tự (khách 2026-08-07). Seed template khai noupdate="1" nên upgrade
# KHÔNG đè, phải sửa tay ở đây; và NV đang chạy dở cũng cần mở bước ra.
# Spec: docs/superpowers/specs/2026-08-08-account-lock-independent-onboarding-step-design.md
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

XMLID = 'hocba_employees.onb_tpl_vp_step2'


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    tpl_step = env.ref(XMLID, raise_if_not_found=False)
    if not tpl_step:
        # DB seed khác đi (admin đã xoá/dựng lại quy trình) — không có gì
        # để sửa, thoát êm chứ không chặn upgrade.
        _logger.info('19.0.4.0.0: không thấy %s, bỏ qua.', XMLID)
        return
    tpl_step.write({'is_independent': True, 'auto_action': 'none'})

    steps = env['hb.onboarding.step'].with_context(active_test=False).search([
        ('template_id', '=', tpl_step.template_id.id),
        ('name', '=', tpl_step.name)])
    if not steps:
        _logger.info('19.0.4.0.0: không có bước NV nào cần chuyển.')
        return
    steps.write({'is_independent': True, 'auto_action': 'none'})
    # Bước đang chờ tới lượt → mở ngay để HR cấp thiết bị được.
    # done/skipped giữ nguyên: đó là lịch sử.
    waiting = steps.filtered(lambda s: s.state == 'waiting')
    waiting.write({'state': 'open'})
    _logger.info(
        '19.0.4.0.0: %s bước "Cấp thiết bị" thành độc lập, mở %s bước.',
        len(steps), len(waiting))
