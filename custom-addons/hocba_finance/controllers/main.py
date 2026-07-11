import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FinanceApiController(http.Controller):
    """API nạp phiếu thu/chi từ hệ thống ngoài.

    Xác thực bằng header ``X-API-Key`` khớp ir.config_parameter
    ``hocba_finance.api_key``. Idempotent theo ``external_ref``.
    """

    @http.route('/hocba-hrm/api/finance/vouchers', type='jsonrpc',
                auth='public', methods=['POST'], csrf=False)
    def ingest_vouchers(self, vouchers=None, auto_post=False, **kw):
        key = request.httprequest.headers.get('X-API-Key')
        expected = request.env['ir.config_parameter'].sudo().get_param(
            'hocba_finance.api_key')
        if not expected or key != expected:
            return {'error': 'unauthorized',
                    'created': 0, 'skipped': 0, 'errors': []}
        if not isinstance(vouchers, list):
            return {'error': 'vouchers phải là danh sách',
                    'created': 0, 'skipped': 0, 'errors': []}
        return request.env['hocba.fin.voucher'].sudo()._ingest_from_api(
            vouchers, source='api', auto_post=bool(auto_post))
