"""
Payroll REST API Controllers.
Full-flow endpoints for payroll management (test & FE integration).

Endpoints:
    ── Payslip Batch ──────────────────────────────
    POST   /hocba-hrm/api/payroll/batch                  Create batch
    GET    /hocba-hrm/api/payroll/batch                  List batches
    GET    /hocba-hrm/api/payroll/batch/<id>             Get batch detail
    POST   /hocba-hrm/api/payroll/batch/<id>/generate    Generate payslips for batch
    POST   /hocba-hrm/api/payroll/batch/<id>/close       Mark batch as done

    ── Payslip ────────────────────────────────────
    GET    /hocba-hrm/api/payroll/payslip                List payslips
    GET    /hocba-hrm/api/payroll/payslip/<id>           Get payslip detail
    POST   /hocba-hrm/api/payroll/payslip/<id>/compute   Compute teaching salary
    POST   /hocba-hrm/api/payroll/payslip/<id>/confirm   Confirm payslip
    POST   /hocba-hrm/api/payroll/payslip/<id>/reset     Reset to draft

    ── Work Entry ─────────────────────────────────
    POST   /hocba-hrm/api/payroll/work-entry             Create work entry
    GET    /hocba-hrm/api/payroll/work-entry             List work entries
    POST   /hocba-hrm/api/payroll/work-entry/<id>/validate  Validate work entry
    POST   /hocba-hrm/api/payroll/work-entry/bulk-create    Bulk create work entries

    ── Bank File ──────────────────────────────────
    POST   /hocba-hrm/api/payroll/bank-file/generate     Generate bank file
    GET    /hocba-hrm/api/payroll/bank-file              List bank files
    POST   /hocba-hrm/api/payroll/bank-file/<id>/upload  Mark as uploaded
    POST   /hocba-hrm/api/payroll/bank-file/<id>/confirm Mark as confirmed

    ── Config ─────────────────────────────────────
    GET    /hocba-hrm/api/payroll/bank-format             List bank formats
    POST   /hocba-hrm/api/payroll/bank-format             Create bank format
    POST   /hocba-hrm/api/payroll/bank-format/<id>        Update bank format
    POST   /hocba-hrm/api/payroll/bank-format/<id>/delete Delete (archive) bank format
    GET    /hocba-hrm/api/payroll/salary-rule-category    List/CRUD salary rule categories
    GET    /hocba-hrm/api/payroll/contract/<id>           Get contract detail
    GET    /hocba-hrm/api/payroll/contract/<id>/teaching  Get contract teaching config
    POST   /hocba-hrm/api/payroll/contract/<id>/teaching  Update contract teaching config
"""
import json
import logging

from odoo import http, fields, _
from odoo.http import request, Response
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


def _json_response(data, status=200):
    body = json.dumps(data, ensure_ascii=False, default=str)
    return Response(body, status=status, content_type='application/json; charset=utf-8')


def _error_response(message, status=400, code=None):
    payload = {'success': False, 'error': message}
    if code:
        payload['code'] = code
    return _json_response(payload, status=status)


def _success_response(data=None, message=None):
    payload = {'success': True}
    if data is not None:
        payload['data'] = data
    if message:
        payload['message'] = message
    return _json_response(payload)


def _get_json_body():
    try:
        return json.loads(request.httprequest.data or '{}')
    except (json.JSONDecodeError, TypeError):
        return {}


class PayrollAPI(http.Controller):

    # ═════════════════════════════════════════════════════════
    # PAYSLIP BATCH
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/batch', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_batch(self, **kw):
        try:
            body = _get_json_body()
            for f in ('name', 'date_start', 'date_end'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            batch = request.env['hb.payslip.run'].sudo().create({
                'name': body['name'],
                'date_start': body['date_start'],
                'date_end': body['date_end'],
            })
            return _success_response({
                'id': batch.id, 'name': batch.name, 'state': batch.state,
            }, message='Payslip batch created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_batch error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/batch', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_batches(self, **kw):
        try:
            batches = request.env['hb.payslip.run'].sudo().search(
                [], order='date_start desc', limit=int(kw.get('limit', 50)),
            )
            data = [{
                'id': b.id, 'name': b.name,
                'date_start': str(b.date_start) if b.date_start else None,
                'date_end': str(b.date_end) if b.date_end else None,
                'state': b.state, 'payslip_count': len(b.slip_ids),
            } for b in batches]
            return _success_response(data)
        except Exception as e:
            _logger.exception('list_batches error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/batch/<int:batch_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_batch(self, batch_id, **kw):
        try:
            batch = request.env['hb.payslip.run'].sudo().browse(batch_id)
            if not batch.exists():
                return _error_response('Batch not found.', status=404)
            slips = [{
                'id': s.id, 'number': s.number,
                'employee_name': s.employee_id.name,
                'state': s.state,
                'gross_amount': s.gross_amount,
                'net_amount': s.net_amount,
                'teaching_computed': s.x_teaching_computed,
            } for s in batch.slip_ids]
            return _success_response({
                'id': batch.id, 'name': batch.name,
                'date_start': str(batch.date_start),
                'date_end': str(batch.date_end),
                'state': batch.state, 'payslips': slips,
            })
        except Exception as e:
            _logger.exception('get_batch error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/batch/<int:batch_id>/generate', type='http',
                auth='user', methods=['POST'], csrf=False)
    def generate_payslips(self, batch_id, **kw):
        try:
            batch = request.env['hb.payslip.run'].sudo().browse(batch_id)
            if not batch.exists():
                return _error_response('Batch not found.', status=404)

            # Search open contracts first, then get unique employees
            contracts = request.env['hb.contract'].sudo().search([
                ('state', '=', 'open'),
                ('employee_id.active', '=', True),
                ('date_start', '<=', batch.date_end),
                '|', ('date_end', '=', False), ('date_end', '>=', batch.date_start),
            ])
            created = 0
            skipped = []
            seen_emp_ids = set()
            for contract in contracts:
                emp = contract.employee_id
                if emp.id in seen_emp_ids:
                    continue
                seen_emp_ids.add(emp.id)
                slip_vals = {
                    'employee_id': emp.id,
                    'contract_id': contract.id,
                    'date_from': batch.date_start,
                    'date_to': batch.date_end,
                    'payslip_run_id': batch.id,
                }
                struct = getattr(contract, 'x_structure_id', None)
                if struct:
                    slip_vals['structure_id'] = struct.id
                request.env['hb.payslip'].sudo().create(slip_vals)
                created += 1
            return _success_response({
                'created': created, 'skipped': skipped,
            }, message=f'{created} payslips generated.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('generate_payslips error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/batch/<int:batch_id>/close', type='http',
                auth='user', methods=['POST'], csrf=False)
    def close_batch(self, batch_id, **kw):
        try:
            batch = request.env['hb.payslip.run'].sudo().browse(batch_id)
            if not batch.exists():
                return _error_response('Batch not found.', status=404)
            batch.action_close()
            return _success_response({'state': batch.state}, message='Batch closed.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('close_batch error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/batch/close-by-period', type='http',
                auth='user', methods=['POST'], csrf=False)
    def close_batch_by_period(self, **kw):
        """Close all batches that have payslips in the given month/year.
        Only succeeds when every payslip employee has confirmed."""
        try:
            body = _get_json_body()
            month = int(body.get('month', 0))
            year = int(body.get('year', 0))
            if not month or not year:
                return _error_response('month and year are required.')

            nm = month + 1 if month < 12 else 1
            ny = year if month < 12 else year + 1
            date_start = f'{year}-{month:02d}-01'
            date_end = f'{ny}-{nm:02d}-01'

            env = request.env
            slips = env['hb.payslip'].sudo().search([
                ('date_from', '>=', date_start),
                ('date_from', '<', date_end),
                ('state', '!=', 'cancel'),
            ])

            if not slips:
                return _error_response('Không có phiếu lương trong kỳ này.')

            # Check all employees confirmed
            not_confirmed = slips.filtered(
                lambda s: s.x_employee_confirm != 'confirmed'
            )
            if not_confirmed:
                names = ', '.join(not_confirmed.mapped('employee_id.name')[:5])
                remain = len(not_confirmed) - 5
                msg = f'Còn {len(not_confirmed)} nhân viên chưa xác nhận: {names}'
                if remain > 0:
                    msg += f' và {remain} người khác'
                return _error_response(msg)

            # Close all related batches
            batch_ids = slips.mapped('payslip_run_id')
            closed = []
            for batch in batch_ids:
                if batch.state != 'close':
                    batch.action_close()
                closed.append({'id': batch.id, 'name': batch.name, 'state': batch.state})

            return _success_response({
                'closed_batches': closed,
                'payslip_count': len(slips),
            }, message=f'Đã lưu lịch sử lương tháng {month:02d}/{year}.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('close_batch_by_period error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/compute-all', type='http', auth='user',
                methods=['POST'], csrf=False)
    def compute_all_payslips(self, **kw):
        """One-click: find-or-create batch, generate payslips, compute all.

        Body: { "month": int, "year": int }
        """
        try:
            body = _get_json_body()
            month = int(body.get('month', 0))
            year = int(body.get('year', 0))
            if not month or not year:
                return _error_response('month and year are required.')

            import calendar
            last_day = calendar.monthrange(year, month)[1]
            date_start = f'{year}-{month:02d}-01'
            date_end = f'{year}-{month:02d}-{last_day:02d}'

            env = request.env
            Batch = env['hb.payslip.run'].sudo()
            Slip = env['hb.payslip'].sudo()

            # 1) Find or create batch for this period
            batch = Batch.search([
                ('date_start', '=', date_start),
                ('date_end', '=', date_end),
                ('state', '=', 'draft'),
            ], limit=1)
            if not batch:
                batch = Batch.create({
                    'name': f'Lương Tháng {month:02d}/{year}',
                    'date_start': date_start,
                    'date_end': date_end,
                })

            # 2) Generate payslips for employees who don't have one yet
            existing_emp_ids = set(
                Slip.search([
                    ('payslip_run_id', '=', batch.id),
                ]).mapped('employee_id.id')
            )
            # Build a map of open contracts (employee_id → contract) for the period
            contracts = env['hb.contract'].sudo().search([
                ('state', '=', 'open'),
                ('employee_id.active', '=', True),
                ('date_start', '<=', batch.date_end),
                '|', ('date_end', '=', False), ('date_end', '>=', batch.date_start),
            ])
            contract_map = {}
            for c in contracts:
                if c.employee_id.id not in contract_map:
                    contract_map[c.employee_id.id] = c

            # Create payslips for ALL active employees, with or without a contract
            employees = env['hr.employee'].sudo().search(
                [('active', '=', True)], order='id',
            )
            # Gom vals rồi bulk INSERT 1 lần thay vì N+1 INSERT riêng lẻ
            slip_vals_list = []
            for emp in employees:
                if emp.id in existing_emp_ids:
                    continue
                contract = contract_map.get(emp.id)
                vals = {
                    'employee_id': emp.id,
                    'date_from': batch.date_start,
                    'date_to': batch.date_end,
                    'payslip_run_id': batch.id,
                }
                if contract:
                    vals['contract_id'] = contract.id
                    if contract.x_structure_id:
                        vals['structure_id'] = contract.x_structure_id.id
                slip_vals_list.append(vals)
            if slip_vals_list:
                Slip.create(slip_vals_list)  # 1 DB trip duy nhất
            created = len(slip_vals_list)

            # 3) Compute all draft/verify payslips in the batch
            to_compute = Slip.search([
                ('payslip_run_id', '=', batch.id),
                ('state', 'in', ('draft', 'verify')),
            ])

            # Pre-fetch rules 1 lần duy nhất — tất cả NV dùng chung bộ rule
            # → bỏ qua O(E) lần resolve structure/rules per slip
            global_rules = env['hb.salary.rule'].sudo().search(
                [('active', '=', True)], order='sequence, id',
            )

            computed = 0
            errors = []
            for slip in to_compute:
                try:
                    slip.action_compute_sheet(prefetched_rules=global_rules)
                    computed += 1
                except Exception as e:
                    errors.append(f'{slip.employee_id.name}: {e}')

            return _success_response({
                'batch_id': batch.id,
                'created': created,
                'computed': computed,
                'errors': errors,
            }, message=f'Đã tính lương cho {computed} nhân viên.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('compute_all_payslips error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # PAYSLIP
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_payslips(self, **kw):
        try:
            domain = []
            if kw.get('batch_id'):
                domain.append(('payslip_run_id', '=', int(kw['batch_id'])))
            if kw.get('employee_id'):
                domain.append(('employee_id', '=', int(kw['employee_id'])))
            if kw.get('state'):
                domain.append(('state', '=', kw['state']))
            # ── month / year filter ──
            year = int(kw['year']) if kw.get('year') else None
            month = int(kw['month']) if kw.get('month') else None
            if year and month:
                nm = month + 1 if month < 12 else 1
                ny = year if month < 12 else year + 1
                domain.append(('date_from', '>=', f'{year}-{month:02d}-01'))
                domain.append(('date_from', '<', f'{ny}-{nm:02d}-01'))
            elif year:
                domain.append(('date_from', '>=', f'{year}-01-01'))
                domain.append(('date_from', '<', f'{year + 1}-01-01'))
            payslips = request.env['hb.payslip'].sudo().search(
                domain, order='employee_id, number', limit=int(kw.get('limit', 500)),
            )
            return _success_response([s._to_api_dict() for s in payslips])
        except Exception as e:
            _logger.exception('list_payslips error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # EMPLOYEE PAYROLL SUMMARY
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/employee-payroll', type='http', auth='user',
                methods=['GET'], csrf=False)
    def employee_payroll_summary(self, **kw):
        """Danh sách nhân viên kèm bảng lương mới nhất theo tháng/năm."""
        try:
            today = fields.Date.today()
            month = int(kw.get('month') or today.month)
            year = int(kw.get('year') or today.year)
            nm = month + 1 if month < 12 else 1
            ny = year if month < 12 else year + 1
            date_start = f'{year}-{month:02d}-01'
            date_end = f'{ny}-{nm:02d}-01'

            env = request.env

            # 1) Salary rules → dynamic columns
            rules = env['hb.salary.rule'].sudo().search(
                [('active', '=', True), ('appears_on_payslip', '=', True)],
                order='sequence, id',
            )
            columns = [{
                'id': r.id, 'code': r.code,
                'name': r.name, 'sequence': r.sequence,
            } for r in rules]

            # 2) Payslips trong kỳ (mới nhất mỗi NV)
            slips = env['hb.payslip'].sudo().search(
                [('date_from', '>=', date_start),
                 ('date_from', '<', date_end),
                 ('state', '!=', 'cancel')],
                order='date_from desc, id desc',
            )
            slip_map = {}  # employee_id → payslip (first = latest)
            for s in slips:
                if s.employee_id.id not in slip_map:
                    slip_map[s.employee_id.id] = s

            # 3) Active employees
            employees = env['hr.employee'].sudo().search(
                [('active', '=', True)],
                order='x_employee_code, id',
            )

            rows = []
            for emp in employees:
                slip = slip_map.get(emp.id)
                amounts = {}
                if slip:
                    for ln in slip.line_ids:
                        amounts[ln.code] = ln.amount
                rows.append({
                    'id': emp.id,
                    'code': emp.x_employee_code or '',
                    'name': emp.name or '',
                    'job_title': emp.job_id.name if emp.job_id else '',
                    'department': emp.department_id.name if emp.department_id else '',
                    'work_email': emp.work_email or '',
                    'payslip_id': slip.id if slip else None,
                    'payslip_state': slip.state if slip else None,
                    'employee_confirm': slip.x_employee_confirm if slip else None,
                    'employee_feedback': slip.x_employee_feedback or '' if slip else '',
                    'email_sent': slip.x_email_sent if slip else False,
                    'gross_amount': slip.gross_amount if slip else 0,
                    'net_amount': slip.net_amount if slip else 0,
                    'access_token': slip.x_access_token if slip else None,
                    'amounts': amounts,
                })

            return _success_response({
                'month': month, 'year': year,
                'columns': columns, 'employees': rows,
            })
        except Exception as e:
            _logger.exception('employee_payroll_summary error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_payslip(self, slip_id, **kw):
        try:
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            return _success_response(slip._to_api_dict())
        except Exception as e:
            _logger.exception('get_payslip error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>/compute', type='http',
                auth='user', methods=['POST'], csrf=False)
    def compute_payslip(self, slip_id, **kw):
        try:
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            slip.action_compute_sheet()
            return _success_response(slip._to_api_dict(), message='Payslip computed successfully.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('compute_payslip error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>/confirm', type='http',
                auth='user', methods=['POST'], csrf=False)
    def confirm_payslip(self, slip_id, **kw):
        try:
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            slip.action_payslip_done()
            return _success_response({'state': slip.state}, message='Payslip confirmed.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('confirm_payslip error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>/reset', type='http',
                auth='user', methods=['POST'], csrf=False)
    def reset_payslip(self, slip_id, **kw):
        try:
            body = _get_json_body()
            reason = body.get('reason')
            if not reason:
                return _error_response('Missing required field: reason')
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            slip.action_reset_to_draft(reason=reason)
            return _success_response({'state': slip.state}, message='Payslip reset to draft.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('reset_payslip error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # PAYSLIP MESSAGES (CHATTER)
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip/<int:payslip_id>/messages', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_payslip_messages(self, payslip_id, **kw):
        """Fetch chatter messages for a payslip."""
        try:
            slip = request.env['hb.payslip'].sudo().browse(payslip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            messages = request.env['mail.message'].sudo().search([
                ('model', '=', 'hb.payslip'),
                ('res_id', '=', payslip_id),
                ('message_type', 'in', ('comment', 'email')),
            ], order='date desc', limit=50)
            result = []
            for m in messages:
                author_name = m.author_id.name if m.author_id else 'Hệ thống'
                result.append({
                    'id': m.id,
                    'body': m.body or '',
                    'date': m.date.isoformat() if m.date else None,
                    'author': author_name,
                    'message_type': m.message_type,
                })
            return _success_response(result)
        except Exception as e:
            _logger.exception('get_payslip_messages error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # SEND PAYSLIP MAIL
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip/send-mail', type='http',
                auth='user', methods=['POST'], csrf=False)
    def send_payslip_mail(self, **kw):
        """Send payslip emails to selected employees."""
        try:
            body = _get_json_body()
            payslip_ids = body.get('payslip_ids', [])
            if not payslip_ids:
                return _error_response('Missing payslip_ids.')

            payslips = request.env['hb.payslip'].sudo().browse(payslip_ids)
            if not payslips.exists():
                return _error_response('No valid payslips found.', status=404)

            sent = 0
            skipped = []
            for slip in payslips:
                employee = slip.employee_id
                email_to = employee.work_email or getattr(employee, 'email', False)
                if not email_to:
                    skipped.append({
                        'employee_name': employee.name,
                        'reason': 'Không có email',
                    })
                    continue
                try:
                    slip.action_send_payslip_mail()
                    sent += 1
                except Exception as e:
                    skipped.append({
                        'employee_name': employee.name,
                        'reason': str(e),
                    })

            return _success_response({
                'sent': sent,
                'skipped': skipped,
            }, message=f'Đã gửi {sent} email thành công.')
        except Exception as e:
            _logger.exception('send_payslip_mail error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # WORK ENTRY
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/work-entry', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_work_entry(self, **kw):
        try:
            body = _get_json_body()
            for f in ('employee_id', 'work_entry_type_code', 'date_start', 'date_stop'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            we_type = request.env['hb.work.entry.type'].sudo().search(
                [('code', '=', body['work_entry_type_code'])], limit=1)
            if not we_type:
                return _error_response(f'Work entry type "{body["work_entry_type_code"]}" not found.')
            vals = {
                'employee_id': int(body['employee_id']),
                'work_entry_type_id': we_type.id,
                'date_start': body['date_start'],
                'date_stop': body['date_stop'],
                'x_class_level': body.get('class_level', 'basic'),
                'x_class_code': body.get('class_code', ''),
            }
            entry = request.env['hb.work.entry'].sudo().create(vals)
            return _success_response({
                'id': entry.id, 'name': entry.name,
                'duration': entry.duration, 'state': entry.state,
            }, message='Work entry created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_work_entry error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/work-entry', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_work_entries(self, **kw):
        try:
            domain = []
            if kw.get('employee_id'):
                domain.append(('employee_id', '=', int(kw['employee_id'])))
            if kw.get('state'):
                domain.append(('state', '=', kw['state']))
            if kw.get('type_code'):
                domain.append(('work_entry_type_id.code', '=', kw['type_code']))
            entries = request.env['hb.work.entry'].sudo().search(
                domain, order='date_start desc', limit=int(kw.get('limit', 200)),
            )
            data = [{
                'id': e.id, 'name': e.name,
                'employee_id': e.employee_id.id,
                'employee_name': e.employee_id.name,
                'type_code': e.work_entry_type_id.code,
                'date_start': str(e.date_start),
                'date_stop': str(e.date_stop),
                'duration': e.duration,
                'class_level': e.x_class_level,
                'class_code': e.x_class_code,
                'state': e.state,
            } for e in entries]
            return _success_response(data)
        except Exception as e:
            _logger.exception('list_work_entries error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/work-entry/<int:entry_id>/validate', type='http',
                auth='user', methods=['POST'], csrf=False)
    def validate_work_entry(self, entry_id, **kw):
        try:
            entry = request.env['hb.work.entry'].sudo().browse(entry_id)
            if not entry.exists():
                return _error_response('Work entry not found.', status=404)
            entry.action_validate()
            return _success_response({'state': entry.state})
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('validate_work_entry error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/work-entry/bulk-create', type='http', auth='user',
                methods=['POST'], csrf=False)
    def bulk_create_work_entries(self, **kw):
        """Bulk create + auto-validate work entries."""
        try:
            body = _get_json_body()
            entries_data = body.get('entries', [])
            if not entries_data:
                return _error_response('Missing entries array.')

            created_ids = []
            for item in entries_data:
                we_type = request.env['hb.work.entry.type'].sudo().search(
                    [('code', '=', item.get('work_entry_type_code', 'WORK200'))], limit=1)
                if not we_type:
                    continue
                entry = request.env['hb.work.entry'].sudo().create({
                    'employee_id': int(item['employee_id']),
                    'work_entry_type_id': we_type.id,
                    'date_start': item['date_start'],
                    'date_stop': item['date_stop'],
                    'x_class_level': item.get('class_level', 'basic'),
                    'x_class_code': item.get('class_code', ''),
                })
                if item.get('auto_validate', True):
                    entry.action_validate()
                created_ids.append(entry.id)

            return _success_response({
                'created_count': len(created_ids),
                'ids': created_ids,
            }, message=f'{len(created_ids)} work entries created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('bulk_create error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # TRANSFER LIST (danh sách chuyển khoản)
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/transfer-list', type='http', auth='user',
                methods=['GET'], csrf=False)
    def transfer_list(self, **kw):
        """Danh sách chuyển khoản lương — dùng để xuất file eMB_BulkPayment."""
        try:
            today = fields.Date.today()
            month = int(kw.get('month') or today.month)
            year = int(kw.get('year') or today.year)
            nm = month + 1 if month < 12 else 1
            ny = year if month < 12 else year + 1
            date_start = f'{year}-{month:02d}-01'
            date_end = f'{ny}-{nm:02d}-01'
            env = request.env

            # Build bank entry lookup: short_code → full name
            bank_entries = env['hb.bank.format'].sudo().search(
                [('active', '=', True)])
            bank_lookup = {}
            for entry in bank_entries:
                parts = entry.name.split(' - ', 1)
                if len(parts) == 2:
                    code = parts[0].strip().upper()
                    if code not in bank_lookup:
                        bank_lookup[code] = entry.name

            # Helper: resolve employee bank → MB bank name
            def _resolve_bank(bank_acc):
                if not bank_acc:
                    return ''
                bank = bank_acc.bank_id
                if not bank:
                    return ''
                bname = bank.name or ''
                bic = (bank.bic or '').upper()
                for code, full in bank_lookup.items():
                    if bic and code in bic:
                        return full
                    if code.lower() in bname.lower():
                        return full
                    if bname.lower() in full.lower():
                        return full
                return bname

            # Helper: get employee bank account
            def _get_bank(emp):
                if hasattr(emp, 'bank_account_id') and emp.bank_account_id:
                    return emp.bank_account_id
                partner = (
                    getattr(emp, 'address_home_id', None)
                    or getattr(emp, 'work_contact_id', None)
                )
                if partner and partner.bank_ids:
                    return partner.bank_ids[0]
                return None

            # Payslips in period
            slips = env['hb.payslip'].sudo().search(
                [('date_from', '>=', date_start),
                 ('date_from', '<', date_end),
                 ('state', 'in', ('done', 'close'))],
                order='date_from desc, id desc',
            )
            slip_map = {}
            for s in slips:
                if s.employee_id.id not in slip_map:
                    slip_map[s.employee_id.id] = s

            # Active employees
            employees = env['hr.employee'].sudo().search(
                [('active', '=', True)],
                order='x_employee_code, id',
            )

            rows = []
            for emp in employees:
                slip = slip_map.get(emp.id)
                if not slip:
                    continue  # No payslip this month → skip
                net_line = slip.line_ids.filtered(
                    lambda l: l.code == 'thuc_lanh')
                net = net_line[0].amount if net_line else 0.0

                bank_acc = _get_bank(emp)
                acc_number = (bank_acc.acc_number or '').strip() if bank_acc else ''
                bank_name = _resolve_bank(bank_acc)

                rows.append({
                    'employee_id': emp.id,
                    'employee_code': emp.x_employee_code or '',
                    'name': emp.name or '',
                    'bank_account': acc_number,
                    'bank_name': bank_name,
                    'net_amount': int(net),
                    'payslip_state': slip.state,
                    'employee_confirm': slip.x_employee_confirm
                        if hasattr(slip, 'x_employee_confirm') else None,
                })

            # Bank formats for dropdown
            formats = env['hb.bank.format'].sudo().search(
                [('active', '=', True)], order='sequence, name')
            fmt_list = [{
                'id': f.id, 'name': f.name, 'code': f.code,
                'description_template': f.description_template or '',
            } for f in formats]

            return _success_response({
                'month': month, 'year': year,
                'employees': rows,
                'bank_formats': fmt_list,
            })
        except Exception as e:
            _logger.exception('transfer_list error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # BANK FILE
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/bank-file/generate', type='http', auth='user',
                methods=['POST'], csrf=False)
    def generate_bank_file(self, **kw):
        try:
            body = _get_json_body()
            for f in ('batch_id', 'bank_format_id'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            payment_date = body.get('payment_date') or str(fields.Date.today())
            wiz_vals = {
                'payslip_batch_id': int(body['batch_id']),
                'bank_format_id': int(body['bank_format_id']),
                'payment_date': payment_date,
                'description': body.get('description', 'Luong T{month}/{year}'),
            }
            if body.get('company_bank_id'):
                wiz_vals['company_bank_id'] = int(body['company_bank_id'])
            wiz = request.env['hb.bank.file.wizard'].sudo().create(wiz_vals)
            wiz.action_generate()
            bank_file = request.env['hb.bank.file'].sudo().search([
                ('batch_id', '=', int(body['batch_id'])),
                ('bank_format_id', '=', int(body['bank_format_id'])),
            ], order='generated_at desc', limit=1)
            return _success_response(
                bank_file._to_api_dict() if bank_file else {},
                message='Bank file generated.',
            )
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('generate_bank_file error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-file', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_bank_files(self, **kw):
        try:
            domain = []
            if kw.get('batch_id'):
                domain.append(('batch_id', '=', int(kw['batch_id'])))
            files = request.env['hb.bank.file'].sudo().search(
                domain, order='generated_at desc', limit=int(kw.get('limit', 50)),
            )
            return _success_response([f._to_api_dict() for f in files])
        except Exception as e:
            _logger.exception('list_bank_files error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-file/<int:file_id>/upload', type='http',
                auth='user', methods=['POST'], csrf=False)
    def mark_bank_file_uploaded(self, file_id, **kw):
        try:
            bf = request.env['hb.bank.file'].sudo().browse(file_id)
            if not bf.exists():
                return _error_response('Bank file not found.', status=404)
            bf.action_mark_uploaded()
            return _success_response({'state': bf.state})
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-file/<int:file_id>/confirm', type='http',
                auth='user', methods=['POST'], csrf=False)
    def mark_bank_file_confirmed(self, file_id, **kw):
        try:
            bf = request.env['hb.bank.file'].sudo().browse(file_id)
            if not bf.exists():
                return _error_response('Bank file not found.', status=404)
            bf.action_mark_confirmed()
            return _success_response({'state': bf.state})
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # CONFIG
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/bank-format', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_bank_formats(self, **kw):
        try:
            formats = request.env['hb.bank.format'].sudo().search(
                [('active', '=', True)], order='sequence, name',
            )
            return _success_response([{
                'id': f.id, 'name': f.name, 'code': f.code or '',
                'sequence': f.sequence,
                'transfer_type': f.transfer_type or 'normal',
                'formatter_class': f.formatter_class or '',
            } for f in formats])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-format', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_bank_format(self, **kw):
        try:
            body = _get_json_body()
            if not body.get('name'):
                return _error_response('Missing required field: name')
            vals = {
                'name': body['name'],
                'code': body.get('code', ''),
                'transfer_type': body.get('transfer_type', 'normal'),
                'sequence': int(body.get('sequence', 10)),
            }
            rec = request.env['hb.bank.format'].sudo().create(vals)
            return _success_response({
                'id': rec.id, 'name': rec.name, 'code': rec.code,
            }, message='Bank format created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_bank_format error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-format/<int:fmt_id>', type='http',
                auth='user', methods=['POST'], csrf=False)
    def update_bank_format(self, fmt_id, **kw):
        try:
            body = _get_json_body()
            rec = request.env['hb.bank.format'].sudo().browse(fmt_id)
            if not rec.exists():
                return _error_response('Bank format not found.', status=404)
            vals = {}
            for f in ('name', 'code', 'transfer_type'):
                if f in body:
                    vals[f] = body[f]
            if 'sequence' in body:
                vals['sequence'] = int(body['sequence'])
            if vals:
                rec.write(vals)
            return _success_response({
                'id': rec.id, 'name': rec.name, 'code': rec.code,
            }, message='Bank format updated.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('update_bank_format error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/bank-format/<int:fmt_id>/delete', type='http',
                auth='user', methods=['POST'], csrf=False)
    def delete_bank_format(self, fmt_id, **kw):
        try:
            rec = request.env['hb.bank.format'].sudo().browse(fmt_id)
            if not rec.exists():
                return _error_response('Bank format not found.', status=404)
            rec.write({'active': False})
            return _success_response(message='Bank format archived.')
        except Exception as e:
            _logger.exception('delete_bank_format error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-structure', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_salary_structures(self, **kw):
        try:
            structs = request.env['hb.salary.structure'].sudo().search(
                [('active', '=', True)], order='code',
            )
            data = [{
                'id': s.id, 'name': s.name, 'code': s.code,
                'rule_count': s.rule_count,
            } for s in structs]
            return _success_response(data)
        except Exception as e:
            return _error_response(str(e), status=500)

    # ── Salary Rule Category ─────────────────────────────
    @http.route('/hocba-hrm/api/payroll/salary-rule-category', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_salary_rule_categories(self, **kw):
        try:
            cats = request.env['hb.salary.rule.category'].sudo().search([], order='sequence, id')
            return _success_response([{
                'id': c.id, 'name': c.name, 'code': c.code,
                'sequence': c.sequence, 'note': c.note or '',
            } for c in cats])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule-category', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_salary_rule_category(self, **kw):
        try:
            data = request.get_json_data()
            cat = request.env['hb.salary.rule.category'].sudo().create({
                'name': data.get('name', ''),
                'code': data.get('code', ''),
                'sequence': int(data.get('sequence', 10)),
                'note': data.get('note', ''),
            })
            return _success_response({'id': cat.id, 'name': cat.name, 'code': cat.code,
                                      'sequence': cat.sequence, 'note': cat.note or ''})
        except Exception as e:
            _logger.exception('create_salary_rule_category error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule-category/<int:cat_id>', type='http', auth='user',
                methods=['POST'], csrf=False)
    def update_salary_rule_category(self, cat_id, **kw):
        try:
            cat = request.env['hb.salary.rule.category'].sudo().browse(cat_id)
            if not cat.exists():
                return _error_response('Category not found.', status=404)
            data = request.get_json_data()
            vals = {}
            for f in ('name', 'code', 'note'):
                if f in data:
                    vals[f] = data[f]
            if 'sequence' in data:
                vals['sequence'] = int(data['sequence'])
            cat.write(vals)
            return _success_response({'id': cat.id, 'name': cat.name, 'code': cat.code,
                                      'sequence': cat.sequence, 'note': cat.note or ''})
        except Exception as e:
            _logger.exception('update_salary_rule_category error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule-category/<int:cat_id>/delete', type='http', auth='user',
                methods=['POST'], csrf=False)
    def delete_salary_rule_category(self, cat_id, **kw):
        try:
            cat = request.env['hb.salary.rule.category'].sudo().browse(cat_id)
            if not cat.exists():
                return _error_response('Category not found.', status=404)
            cat.unlink()
            return _success_response({'deleted': True})
        except Exception as e:
            _logger.exception('delete_salary_rule_category error')
            return _error_response(str(e), status=500)

    # ── Lookup Sources ─────────────────────────────────────
    @http.route('/hocba-hrm/api/payroll/lookup-sources', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_lookup_sources(self, **kw):
        """Return available lookup sources and their fields for the frontend."""
        try:
            from odoo.addons.hocba_payroll.models.payslip import LOOKUP_SOURCES
            data = {}
            for key, src in LOOKUP_SOURCES.items():
                data[key] = {
                    'label': src['label'],
                    'fields': {
                        fname: {'label': fdef['label'], 'agg': fdef.get('agg', 'sum')}
                        for fname, fdef in src['fields'].items()
                    },
                }
            return _success_response(data)
        except Exception as e:
            _logger.exception('list_lookup_sources error')
            return _error_response(str(e), status=500)

    # ── Salary Rule CRUD ──────────────────────────────────
    @http.route('/hocba-hrm/api/payroll/salary-rule', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_salary_rules(self, **kw):
        try:
            domain = [('active', '=', True)]
            if kw.get('structure_id'):
                domain.append(('structure_id', '=', int(kw['structure_id'])))
            rules = request.env['hb.salary.rule'].sudo().search(domain, order='sequence, id')
            return _success_response([{
                'id': r.id, 'name': r.name, 'code': r.code,
                'sequence': r.sequence,
                'structure_id': r.structure_id.id,
                'category_id': r.category_id.id,
                'category_code': r.category_id.code,
                'category_name': r.category_id.name,
                'amount_type': r.amount_type,
                'amount_fixed': r.amount_fixed,
                'amount_percentage': r.amount_percentage,
                'amount_percentage_base': r.amount_percentage_base or '',
                'amount_python_compute': r.amount_python_compute or '',
                'amount_formula': r.amount_formula or '',
                'lookup_source': r.lookup_source or '',
                'lookup_field': r.lookup_field or '',
                'condition_type': r.condition_type,
                'condition_python': r.condition_python or '',
                'appears_on_payslip': r.appears_on_payslip,
                'note': r.note or '',
            } for r in rules])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_salary_rule(self, **kw):
        try:
            body = _get_json_body()
            for f in ('name', 'code'):
                if not body.get(f):
                    return _error_response(f'Missing required field: {f}')
            # Auto-assign structure_id if not provided → first active structure
            structure_id = int(body['structure_id']) if body.get('structure_id') else None
            if not structure_id:
                first_struct = request.env['hb.salary.structure'].sudo().search(
                    [('active', '=', True)], limit=1, order='id')
                if not first_struct:
                    return _error_response('Chưa có cấu trúc lương. Tạo trước khi thêm rule.')
                structure_id = first_struct.id
            # Auto-assign category_id if not provided → first category
            category_id = int(body['category_id']) if body.get('category_id') else None
            if not category_id:
                first_cat = request.env['hb.salary.rule.category'].sudo().search(
                    [], limit=1, order='sequence, id')
                if not first_cat:
                    return _error_response('Chưa có danh mục rule. Tạo trước khi thêm rule.')
                category_id = first_cat.id
            vals = {
                'name': body['name'],
                'code': body['code'],
                'sequence': int(body.get('sequence', 10)),
                'structure_id': structure_id,
                'category_id': category_id,
                'amount_type': body.get('amount_type', 'fixed'),
                'appears_on_payslip': body.get('appears_on_payslip', True),
                'note': body.get('note', ''),
            }
            if vals['amount_type'] == 'fixed':
                vals['amount_fixed'] = float(body.get('amount_fixed', 0))
            elif vals['amount_type'] == 'percentage':
                vals['amount_percentage'] = float(body.get('amount_percentage', 0))
                vals['amount_percentage_base'] = body.get('amount_percentage_base', '')
            elif vals['amount_type'] == 'formula':
                vals['amount_formula'] = body.get('amount_formula', '')
            elif vals['amount_type'] == 'code':
                vals['amount_python_compute'] = body.get('amount_python_compute', '')
            elif vals['amount_type'] == 'lookup':
                vals['lookup_source'] = body.get('lookup_source', '')
                vals['lookup_field'] = body.get('lookup_field', '')
            if body.get('condition_type') == 'python':
                vals['condition_type'] = 'python'
                vals['condition_python'] = body.get('condition_python', '')
            rec = request.env['hb.salary.rule'].sudo().create(vals)
            return _success_response({'id': rec.id, 'name': rec.name, 'code': rec.code},
                                     message='Salary rule created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_salary_rule error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule/<int:rule_id>', type='http',
                auth='user', methods=['POST'], csrf=False)
    def update_salary_rule(self, rule_id, **kw):
        try:
            body = _get_json_body()
            rec = request.env['hb.salary.rule'].sudo().browse(rule_id)
            if not rec.exists():
                return _error_response('Salary rule not found.', status=404)
            vals = {}
            for f in ('name', 'code', 'note', 'amount_percentage_base',
                       'amount_python_compute', 'amount_formula', 'condition_python',
                       'lookup_source', 'lookup_field'):
                if f in body:
                    vals[f] = body[f]
            for f in ('sequence', 'category_id'):
                if f in body:
                    vals[f] = int(body[f])
            if 'amount_type' in body:
                vals['amount_type'] = body['amount_type']
            if 'amount_fixed' in body:
                vals['amount_fixed'] = float(body['amount_fixed'])
            if 'amount_percentage' in body:
                vals['amount_percentage'] = float(body['amount_percentage'])
            if 'condition_type' in body:
                vals['condition_type'] = body['condition_type']
            if 'appears_on_payslip' in body:
                vals['appears_on_payslip'] = bool(body['appears_on_payslip'])
            if vals:
                rec.write(vals)
            return _success_response({'id': rec.id, 'name': rec.name, 'code': rec.code},
                                     message='Salary rule updated.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule/<int:rule_id>/delete', type='http',
                auth='user', methods=['POST'], csrf=False)
    def delete_salary_rule(self, rule_id, **kw):
        try:
            rec = request.env['hb.salary.rule'].sudo().browse(rule_id)
            if not rec.exists():
                return _error_response('Salary rule not found.', status=404)
            rec.write({'active': False})
            return _success_response(message='Salary rule archived.')
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/salary-rule/reorder', type='http',
                auth='user', methods=['POST'], csrf=False)
    def reorder_salary_rules(self, **kw):
        """Batch update sequence for salary rules. Body: { "order": [id1, id2, ...] }"""
        try:
            body = json.loads(request.httprequest.data)
            order = body.get('order', [])
            if not order:
                return _error_response('Missing order list.', status=400)
            Rule = request.env['hb.salary.rule'].sudo()
            for idx, rule_id in enumerate(order):
                rec = Rule.browse(int(rule_id))
                if rec.exists():
                    rec.write({'sequence': (idx + 1) * 10})
            return _success_response({'updated': len(order)})
        except Exception as e:
            _logger.exception('reorder_salary_rules error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/contract/<int:contract_id>', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_contract_detail(self, contract_id, **kw):
        try:
            c = request.env['hb.contract'].sudo().browse(contract_id)
            if not c.exists():
                return _error_response('Contract not found.', status=404)
            return _success_response({
                'id': c.id, 'name': c.name,
                'employee_id': c.employee_id.id,
                'employee_name': c.employee_id.name,
                'state': c.state,
                'wage': c.wage,
                'date_start': str(c.date_start) if c.date_start else None,
                'date_end': str(c.date_end) if c.date_end else None,
                'structure_id': c.x_structure_id.id if c.x_structure_id else None,
                'structure_name': c.x_structure_id.name if c.x_structure_id else None,
                'x_insurance_base': c.x_insurance_base,
                'x_insurance_policy': c.x_insurance_policy,
                'x_dependent_count': c.x_dependent_count,
                'x_pc_seniority': c.x_pc_seniority,
                'x_pc_parking': c.x_pc_parking,
                'x_pc_fuel': c.x_pc_fuel,
                'x_pc_position': c.x_pc_position,
                'x_sp_transport': c.x_sp_transport,
                'x_sp_phone': c.x_sp_phone,
                'x_sp_meal': c.x_sp_meal,
                'x_sp_uniform': c.x_sp_uniform,
                'x_teaching_hourly_rate': c.x_teaching_hourly_rate,
                'x_rate_hsk_class': c.x_rate_hsk_class,
                'x_rate_advanced_class': c.x_rate_advanced_class,
            })
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/contract/<int:contract_id>/teaching', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_contract_teaching(self, contract_id, **kw):
        try:
            c = request.env['hb.contract'].sudo().browse(contract_id)
            if not c.exists():
                return _error_response('Contract not found.', status=404)
            return _success_response({
                'id': c.id, 'name': c.name,
                'employee_name': c.employee_id.name,
                'x_teaching_hourly_rate': c.x_teaching_hourly_rate,
                'x_rate_hsk_class': c.x_rate_hsk_class,
                'x_rate_advanced_class': c.x_rate_advanced_class,
                'x_standard_threshold': c.x_standard_threshold,
                'x_extra_rate': c.x_extra_rate,
                'x_effective_extra_rate': c.x_effective_extra_rate,
                'x_has_fixed_base': c.x_has_fixed_base,
                'x_fixed_base': c.x_fixed_base,
            })
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/contract/<int:contract_id>/teaching', type='http',
                auth='user', methods=['POST'], csrf=False)
    def update_contract_teaching(self, contract_id, **kw):
        try:
            body = _get_json_body()
            c = request.env['hb.contract'].sudo().browse(contract_id)
            if not c.exists():
                return _error_response('Contract not found.', status=404)
            allowed = [
                'x_teaching_hourly_rate', 'x_rate_hsk_class', 'x_rate_advanced_class',
                'x_standard_threshold', 'x_extra_rate', 'x_has_fixed_base', 'x_fixed_base',
            ]
            vals = {k: v for k, v in body.items() if k in allowed}
            if not vals:
                return _error_response('No valid fields to update.')
            c.write(vals)
            return _success_response({
                'id': c.id, 'updated_fields': list(vals.keys()),
            }, message='Contract teaching config updated.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    # ══════════════════════════════════════════════════════════
    #  Email Template Config
    # ══════════════════════════════════════════════════════════
    _MAIL_TPL_KEYS = {
        'subject': 'hocba_payroll.mail_subject',
        'body': 'hocba_payroll.mail_body',
    }
    _MAIL_TPL_DEFAULTS = {
        'subject': 'Bảng lương tháng {month}/{year} — {employee_name}',
        'body': (
            '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">'
            '<h2 style="color:#1f2937;">Bảng lương tháng {month}/{year}</h2>'
            '<p>Xin chào <strong>{employee_name}</strong>,</p>'
            '<p>Phiếu lương tháng {month}/{year} của bạn đã sẵn sàng.</p>'
            '<table style="width:100%;border-collapse:collapse;margin:16px 0;">'
            '<tr style="background:#f3f4f6;">'
            '<td style="padding:8px 12px;font-weight:600;">Tổng thu nhập</td>'
            '<td style="padding:8px 12px;text-align:right;">{gross} ₫</td>'
            '</tr>'
            '<tr style="background:#ecfdf5;">'
            '<td style="padding:8px 12px;font-weight:600;color:#065f46;">Thực lĩnh</td>'
            '<td style="padding:8px 12px;text-align:right;font-weight:700;color:#065f46;">{net} ₫</td>'
            '</tr>'
            '</table>'
            '<p>Vui lòng nhấn nút bên dưới để xem chi tiết và xác nhận:</p>'
            '<a href="{view_url}" '
            'style="display:inline-block;padding:12px 24px;background:#2563eb;'
            'color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">'
            'Xem phiếu lương</a>'
            '<hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;"/>'
            '<p style="font-size:12px;color:#9ca3af;">Email này được gửi tự động. Vui lòng không reply.</p>'
            '</div>'
        ),
    }

    @http.route('/hocba-hrm/api/payroll/mail-template', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_mail_template(self, **kw):
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            result = {}
            for key, param in self._MAIL_TPL_KEYS.items():
                val = ICP.get_param(param, default=False)
                result[key] = val if val else self._MAIL_TPL_DEFAULTS[key]
            return _success_response(result)
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/mail-template', type='http',
                auth='user', methods=['POST'], csrf=False)
    def save_mail_template(self, **kw):
        try:
            body = _get_json_body()
            ICP = request.env['ir.config_parameter'].sudo()
            for key, param in self._MAIL_TPL_KEYS.items():
                if key in body:
                    ICP.set_param(param, body[key])
            return _success_response({'saved': True}, message='Mail template saved.')
        except Exception as e:
            return _error_response(str(e), status=500)

    # ══════════════════════════════════════════════════════════
    #  EmailJS Config
    # ══════════════════════════════════════════════════════════
    _EMAILJS_KEYS = {
        'service_id':  'hocba_payroll.emailjs_service_id',
        'template_id': 'hocba_payroll.emailjs_template_id',
        'public_key':  'hocba_payroll.emailjs_public_key',
    }

    @http.route('/hocba-hrm/api/payroll/emailjs-config', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_emailjs_config(self, **kw):
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            return _success_response({
                k: ICP.get_param(v, default='') for k, v in self._EMAILJS_KEYS.items()
            })
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/emailjs-config', type='http',
                auth='user', methods=['POST'], csrf=False)
    def save_emailjs_config(self, **kw):
        try:
            body = _get_json_body()
            ICP = request.env['ir.config_parameter'].sudo()
            for key, param in self._EMAILJS_KEYS.items():
                if key in body:
                    ICP.set_param(param, body[key])
            return _success_response({'saved': True})
        except Exception as e:
            return _error_response(str(e), status=500)

    # ══════════════════════════════════════════════════════════
    #  Mark payslips as sent (used by frontend EmailJS flow)
    # ══════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip/mark-sent', type='http',
                auth='user', methods=['POST'], csrf=False)
    def mark_payslips_sent(self, **kw):
        """Mark payslips as email-sent and log chatter. Called by frontend after EmailJS send."""
        try:
            body = _get_json_body()
            ids = body.get('payslip_ids', [])
            if not ids:
                return _error_response('Missing payslip_ids.')
            slips = request.env['hb.payslip'].sudo().browse(ids)
            now = fields.Datetime.now()
            for slip in slips.filtered(lambda s: s.exists()):
                vals = {'x_email_sent': True, 'x_email_sent_date': now}
                # Reset rejected → pending so employee can re-confirm
                if slip.x_employee_confirm == 'rejected':
                    vals['x_employee_confirm'] = 'pending'
                    vals['x_employee_feedback'] = False
                slip.write(vals)
                month = slip.date_from.strftime('%m') if slip.date_from else ''
                year = slip.date_from.strftime('%Y') if slip.date_from else ''
                email_to = slip.employee_id.work_email or ''
                slip.message_post(
                    body=_(
                        'Đã gửi phiếu lương tháng %(m)s/%(y)s tới <b>%(email)s</b> (qua EmailJS).',
                        m=month, y=year, email=email_to,
                    ),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
            return _success_response({'marked': len(slips)})
        except Exception as e:
            _logger.exception('mark_payslips_sent error')
            return _error_response(str(e), status=500)
