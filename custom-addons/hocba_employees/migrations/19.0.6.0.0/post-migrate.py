# Migration 19.0.6.0.0 — vá lại việc 19.0.4.0.0 làm hụt.
# 19.0.4.0.0 tìm bước "Cấp thiết bị làm việc" bằng env.ref. Trên Neon tồn
# tại HAI cặp quy trình trùng tên (cặp 19/07 không XML-ID + cặp seed 25/07
# có XML-ID); cặp thắng khi gán NV lại là cặp không XML-ID, nên lệnh vá cũ
# trúng đúng bản không ai dùng. Lần này tìm theo TÊN, vá mọi bản.
# Idempotent — DB sạch (chỉ 1 cặp, đã vá) chạy lại là lệnh rỗng.
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    res = env['hb.onboarding.template']._hocba_sync_independent_equip()
    _logger.info(
        '19.0.6.0.0: vá %s bước mẫu, %s bước NV, mở %s bước đang chờ.',
        res['templateSteps'], res['steps'], res['opened'])
