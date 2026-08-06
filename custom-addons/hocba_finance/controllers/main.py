import logging
from datetime import date

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError, UserError

_logger = logging.getLogger(__name__)

_ACTION_METHODS = {
    'approve': 'action_approve',
    'post': 'action_post',
    'cancel': 'action_cancel',
    'reset': 'action_reset_draft',
}


def _month_domain(month):
    """month = 'YYYY-MM' → domain [start, next_month). Rỗng nếu không hợp lệ."""
    if not month:
        return []
    try:
        y, m = (int(x) for x in month.split('-'))
        start = date(y, m, 1)
        nxt = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    except (ValueError, TypeError):
        return []
    return [('voucher_date', '>=', start.isoformat()),
            ('voucher_date', '<', nxt.isoformat())]


def _voucher_json(v, is_finance):
    return {
        'id': v.id,
        'name': v.name,
        'type': v.voucher_type,
        'amount': v.amount,
        'date': v.voucher_date.isoformat() if v.voucher_date else None,
        'fundId': v.fund_id.id,
        'fundName': v.fund_id.name,
        'categoryId': v.category_id.id,
        'categoryName': v.category_id.name,
        'departmentId': v.department_id.id or None,
        'departmentName': v.department_id.name or None,
        'partnerName': v.partner_name or '',
        'partnerAddress': v.partner_address or '',
        'memo': v.memo or '',
        'attachmentCount': v.attachment_count or 0,
        'source': v.source,
        'state': v.state,
        'canApprove': is_finance and v.state == 'draft',
        'canPost': is_finance and v.state == 'approved',
        'canCancel': is_finance and v.state != 'cancel',
    }


class FinanceIngestController(http.Controller):
    """API nạp phiếu từ hệ thống ngoài (server-to-server).

    Xác thực header ``X-API-Key`` khớp ir.config_parameter
    ``hocba_finance.api_key``. Idempotent theo ``external_ref``.
    """

    @http.route('/hocba-hrm/api/finance/ingest', type='jsonrpc',
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


class FinanceSpaController(http.Controller):
    """API phục vụ màn Tài chính trong SPA (auth='user')."""

    # ── Helpers ──────────────────────────────────────────────────────────
    def _flags(self):
        user = request.env.user
        return (user.has_group('hocba_finance.group_finance_user'),
                user.has_group('hocba_finance.group_finance_manager'))

    def _check_finance(self):
        """Chặn non-finance user truy cập CRUD config."""
        if not request.env.user.has_group('hocba_finance.group_finance_user'):
            raise AccessError('Chỉ Kế toán / Ban giám đốc được cấu hình.')

    def _err(self, ex, code, status):
        request.env.cr.rollback()
        return request.make_json_response(
            {'error': code, 'message': str(ex)}, status=status)

    # ── Context (pick-lists + role flags) ────────────────────────────────
    @http.route('/hocba-hrm/api/finance/context', auth='user',
                type='http', methods=['GET'])
    def api_finance_context(self, **kw):
        is_fin, is_mgr = self._flags()
        env = request.env
        funds = env['hocba.fund'].sudo().search([('active', '=', True)])
        cats = env['hocba.fin.category'].sudo().search([('active', '=', True)])
        depts = env['hr.department'].sudo().search([])
        company = request.env.company
        return request.make_json_response({
            'isFinance': is_fin,
            'isFinanceManager': is_mgr,
            'company': {
                'name': company.name or '',
                'address': ' '.join(filter(None, [
                    company.street, company.street2, company.city,
                ])) or '',
                'phone': company.phone or '',
                'taxId': company.vat or '',
            },
            'funds': [{
                'id': f.id, 'name': f.name, 'code': f.code,
                'departmentId': f.department_id.id or None,
                'departmentName': f.department_id.name or None,
                'fundType': f.fund_type,
                'currentBalance': f.current_balance,
                'openingBalance': f.opening_balance,
            } for f in funds],
            'categories': {
                'income': [{'id': c.id, 'name': c.name, 'code': c.code}
                           for c in cats if c.category_type == 'income'],
                'expense': [{'id': c.id, 'name': c.name, 'code': c.code}
                            for c in cats if c.category_type == 'expense'],
            },
            'departments': [{'id': d.id, 'name': d.name} for d in depts],
        })

    # ── Danh sách phiếu ──────────────────────────────────────────────────
    @http.route('/hocba-hrm/api/finance/vouchers', auth='user',
                type='http', methods=['GET'])
    def api_finance_vouchers(self, **kw):
        is_fin, _ = self._flags()
        domain = []
        if kw.get('state'):
            domain.append(('state', '=', kw['state']))
        if kw.get('type') in ('income', 'expense'):
            domain.append(('voucher_type', '=', kw['type']))
        if kw.get('fundId'):
            try:
                domain.append(('fund_id', '=', int(kw['fundId'])))
            except ValueError:
                pass
        domain += _month_domain(kw.get('month'))
        vouchers = request.env['hocba.fin.voucher'].search(
            domain, limit=500, order='voucher_date desc, id desc')
        return request.make_json_response({
            'isFinance': is_fin,
            'vouchers': [_voucher_json(v, is_fin) for v in vouchers],
        })

    # ── Tạo phiếu (nháp) ─────────────────────────────────────────────────
    @http.route('/hocba-hrm/api/finance/voucher', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_finance_voucher_create(self, **kw):
        is_fin, _ = self._flags()
        body = request.get_json_data()
        vals = {
            'voucher_type': body.get('voucherType') or 'income',
            'amount': body.get('amount') or 0.0,
            'voucher_date': body.get('date') or date.today().isoformat(),
            'fund_id': body.get('fundId'),
            'category_id': body.get('categoryId'),
            'partner_name': body.get('partnerName') or False,
            'partner_address': body.get('partnerAddress') or False,
            'memo': body.get('memo') or False,
            'attachment_count': body.get('attachmentCount') or 0,
            'source': 'manual',
        }
        try:
            v = request.env['hocba.fin.voucher'].create(vals)
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)
        return request.make_json_response(_voucher_json(v, is_fin))

    # ── Hành động trạng thái ─────────────────────────────────────────────
    @http.route('/hocba-hrm/api/finance/voucher/<int:vid>/action', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_finance_voucher_action(self, vid, **kw):
        is_fin, _ = self._flags()
        body = request.get_json_data()
        method = _ACTION_METHODS.get(body.get('action'))
        if not method:
            return request.make_json_response(
                {'error': 'bad_action'}, status=400)
        v = request.env['hocba.fin.voucher'].browse(vid)
        if not v.exists():
            return request.make_json_response(
                {'error': 'not_found'}, status=404)
        try:
            getattr(v, method)()
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)
        return request.make_json_response(_voucher_json(v, is_fin))

    # ── Báo cáo tổng hợp ─────────────────────────────────────────────────
    @http.route('/hocba-hrm/api/finance/summary', auth='user',
                type='http', methods=['GET'])
    def api_finance_summary(self, **kw):
        Voucher = request.env['hocba.fin.voucher']
        domain = [('state', '=', 'posted')] + _month_domain(kw.get('month'))

        by_dept = Voucher._read_group(
            domain, ['department_id', 'voucher_type'], ['amount:sum'])
        by_cat = Voucher._read_group(
            domain, ['category_id', 'voucher_type'], ['amount:sum'])

        total_income = total_expense = 0.0
        dept_map = {}
        for dept, vtype, amt in by_dept:
            key = dept.id or 0
            row = dept_map.setdefault(key, {
                'name': dept.name if dept else 'Không phòng ban',
                'income': 0.0, 'expense': 0.0})
            if vtype == 'income':
                row['income'] += amt
                total_income += amt
            else:
                row['expense'] += amt
                total_expense += amt
        for row in dept_map.values():
            row['net'] = row['income'] - row['expense']

        categories = [{
            'name': cat.name if cat else 'Khác',
            'type': vtype,
            'amount': amt,
        } for cat, vtype, amt in by_cat]

        funds = request.env['hocba.fund'].sudo().search([('active', '=', True)])
        return request.make_json_response({
            'totalIncome': total_income,
            'totalExpense': total_expense,
            'net': total_income - total_expense,
            'byDepartment': sorted(
                dept_map.values(), key=lambda r: -r['net']),
            'byCategory': sorted(categories, key=lambda r: -r['amount']),
            'funds': [{'id': f.id, 'name': f.name,
                       'balance': f.current_balance} for f in funds],
        })

    # ══════════════════════════════════════════════════════════════════════
    # CRUD Quỹ (Fund) — chỉ Kế toán / BGĐ
    # ══════════════════════════════════════════════════════════════════════

    @http.route('/hocba-hrm/api/finance/fund', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_fund_create(self, **kw):
        try:
            self._check_finance()
            body = request.get_json_data()
            fund = request.env['hocba.fund'].create({
                'name': body.get('name', ''),
                'code': body.get('code', ''),
                'fund_type': body.get('fundType', 'cash'),
                'department_id': body.get('departmentId') or False,
                'opening_balance': body.get('openingBalance', 0),
            })
            return request.make_json_response(self._fund_json(fund))
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    @http.route('/hocba-hrm/api/finance/fund/<int:fid>', auth='user',
                type='http', methods=['PUT'], csrf=False)
    def api_fund_update(self, fid, **kw):
        try:
            self._check_finance()
            body = request.get_json_data()
            fund = request.env['hocba.fund'].browse(fid)
            if not fund.exists():
                return request.make_json_response(
                    {'error': 'not_found'}, status=404)
            vals = {}
            if 'name' in body:
                vals['name'] = body['name']
            if 'code' in body:
                vals['code'] = body['code']
            if 'fundType' in body:
                vals['fund_type'] = body['fundType']
            if 'departmentId' in body:
                vals['department_id'] = body['departmentId'] or False
            if 'openingBalance' in body:
                vals['opening_balance'] = body['openingBalance']
            if vals:
                fund.write(vals)
            return request.make_json_response(self._fund_json(fund))
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    @http.route('/hocba-hrm/api/finance/fund/<int:fid>', auth='user',
                type='http', methods=['DELETE'], csrf=False)
    def api_fund_delete(self, fid, **kw):
        try:
            self._check_finance()
            fund = request.env['hocba.fund'].browse(fid)
            if not fund.exists():
                return request.make_json_response(
                    {'error': 'not_found'}, status=404)
            # Archive thay vì xóa (có phiếu liên quan thì không xóa được)
            fund.write({'active': False})
            return request.make_json_response({'ok': True})
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    def _fund_json(self, f):
        return {
            'id': f.id, 'name': f.name, 'code': f.code,
            'fundType': f.fund_type,
            'departmentId': f.department_id.id or None,
            'departmentName': f.department_id.name or None,
            'openingBalance': f.opening_balance,
            'currentBalance': f.current_balance,
        }

    # ══════════════════════════════════════════════════════════════════════
    # CRUD Mục thu/chi (Category) — chỉ Kế toán / BGĐ
    # ══════════════════════════════════════════════════════════════════════

    @http.route('/hocba-hrm/api/finance/category', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_category_create(self, **kw):
        try:
            self._check_finance()
            body = request.get_json_data()
            cat = request.env['hocba.fin.category'].create({
                'name': body.get('name', ''),
                'code': body.get('code', ''),
                'category_type': body.get('categoryType', 'income'),
                'parent_id': body.get('parentId') or False,
            })
            return request.make_json_response(self._cat_json(cat))
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    @http.route('/hocba-hrm/api/finance/category/<int:cid>', auth='user',
                type='http', methods=['PUT'], csrf=False)
    def api_category_update(self, cid, **kw):
        try:
            self._check_finance()
            body = request.get_json_data()
            cat = request.env['hocba.fin.category'].browse(cid)
            if not cat.exists():
                return request.make_json_response(
                    {'error': 'not_found'}, status=404)
            vals = {}
            if 'name' in body:
                vals['name'] = body['name']
            if 'code' in body:
                vals['code'] = body['code']
            if 'categoryType' in body:
                vals['category_type'] = body['categoryType']
            if 'parentId' in body:
                vals['parent_id'] = body['parentId'] or False
            if vals:
                cat.write(vals)
            return request.make_json_response(self._cat_json(cat))
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    @http.route('/hocba-hrm/api/finance/category/<int:cid>', auth='user',
                type='http', methods=['DELETE'], csrf=False)
    def api_category_delete(self, cid, **kw):
        try:
            self._check_finance()
            cat = request.env['hocba.fin.category'].browse(cid)
            if not cat.exists():
                return request.make_json_response(
                    {'error': 'not_found'}, status=404)
            cat.write({'active': False})
            return request.make_json_response({'ok': True})
        except AccessError as ex:
            return self._err(ex, 'forbidden', 403)
        except (ValidationError, UserError) as ex:
            return self._err(ex, 'rejected', 400)

    def _cat_json(self, c):
        return {
            'id': c.id, 'name': c.name, 'code': c.code,
            'categoryType': c.category_type,
            'parentId': c.parent_id.id or None,
            'parentName': c.parent_id.name or None,
        }
