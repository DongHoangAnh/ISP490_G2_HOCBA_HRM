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
import threading
import concurrent.futures

import odoo
from odoo import http, fields, _
from odoo.http import request, Response
from odoo.exceptions import ValidationError, UserError
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)



def _run_async_batch_compute(db_name, batch_id, slip_ids):
    """Background worker thread for async batch payroll computation.

    Processes payslips in chunks (e.g. 50 per chunk), committing each chunk
    independently to prevent DB locks, long transactions, and socket timeouts.
    """
    registry = Registry(db_name)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        batch = env['hb.payslip.run'].browse(batch_id)
        if not batch.exists():
            return

        batch.write({
            'compute_status': 'processing',
            'computed_count': 0,
            'total_count': len(slip_ids),
            'compute_error': False,
        })
        cr.commit()

        try:
            rules = env['hb.salary.rule'].search([('active', '=', True)], order='sequence, id')
            CHUNK_SIZE = 50
            total_computed = 0

            for i in range(0, len(slip_ids), CHUNK_SIZE):
                chunk_ids = slip_ids[i:i + CHUNK_SIZE]
                slips = env['hb.payslip'].browse(chunk_ids).filtered(lambda s: s.state in ('draft', 'verify'))
                if slips:
                    res = slips.action_compute_batch(prefetched_rules=rules)
                    total_computed += res.get('computed', 0)

                batch.write({'computed_count': total_computed})
                cr.commit()

            batch.write({
                'compute_status': 'completed',
                'computed_count': total_computed,
            })
            cr.commit()
            _logger.info('Async batch payroll compute completed for batch %s (%s slips)', batch_id, total_computed)
        except Exception as e:
            _logger.exception('Async batch payroll compute error for batch %s: %s', batch_id, e)
            try:
                cr.rollback()
                batch.write({
                    'compute_status': 'failed',
                    'compute_error': str(e),
                })
                cr.commit()
            except Exception:
                pass


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
                'state': batch.state,
                'compute_status': batch.compute_status or 'idle',
                'computed_count': batch.computed_count or 0,
                'total_count': batch.total_count or len(slips),
                'compute_error': batch.compute_error or False,
                'payslips': slips,
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

            # 1) Find existing slip employee IDs to prevent duplicates
            existing_emp_ids = set(batch.slip_ids.mapped('employee_id.id'))

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
                if emp.id in seen_emp_ids or emp.id in existing_emp_ids:
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

            # 2) Trigger Async Background Batch Compute
            to_compute = request.env['hb.payslip'].sudo().search([
                ('payslip_run_id', '=', batch.id),
                ('state', 'in', ('draft', 'verify')),
            ])
            slip_ids = to_compute.ids
            if slip_ids:
                db_name = request.env.cr.dbname
                batch.write({
                    'compute_status': 'processing',
                    'computed_count': 0,
                    'total_count': len(slip_ids),
                    'compute_error': False,
                })
                request.env.cr.commit()

                worker = threading.Thread(
                    target=_run_async_batch_compute,
                    args=(db_name, batch.id, slip_ids),
                    daemon=True,
                )
                worker.start()

            return _success_response({
                'created': created,
                'total': len(slip_ids),
                'status': 'processing' if slip_ids else 'completed',
            }, message=f'Đã sinh {created} phiếu lương mới và đang tính toán ngầm.')
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

            # Only process payslips from draft/verify batches (not already closed)
            closed_batch_ids = env['hb.payslip.run'].sudo().search(
                [('state', '=', 'close')]).ids
            slip_domain = [
                ('date_from', '>=', date_start),
                ('date_from', '<', date_end),
                ('state', '!=', 'cancel'),
            ]
            if closed_batch_ids:
                slip_domain.append(('payslip_run_id', 'not in', closed_batch_ids))
            slips = env['hb.payslip'].sudo().search(slip_domain)

            if not slips:
                return _error_response('Không có phiếu lương trong kỳ này.')

            # Check all employees confirmed — auto-confirm expired first
            now = fields.Datetime.now()
            pending = slips.filtered(
                lambda s: s.x_employee_confirm != 'confirmed'
            )
            # Auto-confirm payslips that are past their deadline
            for s in pending:
                if (s.x_confirm_deadline and s.x_confirm_deadline <= now
                        and s.x_email_sent):
                    s.write({
                        'x_employee_confirm': 'confirmed',
                        'x_confirmed_date': now,
                    })
                    s.message_post(
                        body=_(
                            'Hệ thống tự động xác nhận phiếu lương '
                            '(nhân viên <b>%(name)s</b> không phản hồi '
                            'trong thời hạn — close-by-period).',
                            name=s.employee_id.name,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )

            # Re-check after auto-confirm
            not_confirmed = slips.filtered(
                lambda s: s.x_employee_confirm != 'confirmed'
            )
            if not_confirmed:
                rejected_slips = not_confirmed.filtered(lambda s: s.x_employee_confirm == 'rejected')
                if rejected_slips:
                    rej_names = ', '.join(rejected_slips.mapped('employee_id.name')[:5])
                    msg = f'Không thể chốt sổ đóng kỳ lương vì có {len(rejected_slips)} nhân viên đang khiếu nại chưa giải quyết ({rej_names}). Vui lòng kiểm tra và xử lý khiếu nại trước khi lưu lịch sử.'
                else:
                    names = ', '.join(not_confirmed.mapped('employee_id.name')[:5])
                    remain = len(not_confirmed) - 5
                    msg = f'Còn {len(not_confirmed)} nhân viên chưa xác nhận hoặc chưa gửi mail: {names}'
                    if remain > 0:
                        msg += f' và {remain} người khác'
                return _error_response(msg)

            # Close all related batches → payslips move to 'done', batch to 'close'
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

            # Đồng bộ lương cơ bản trên hợp đồng với phiên bản hồ sơ NV mới nhất
            for emp in employees:
                ver = emp.version_id
                if ver and hasattr(ver, 'wage') and ver.wage:
                    cnts = env['hb.contract'].sudo().search([('employee_id', '=', emp.id)])
                    if cnts:
                        cnts.filtered(lambda c: c.wage != ver.wage).write({'wage': ver.wage})

            # Gom vals rồi bulk INSERT 1 lần thay vì N+1 INSERT riêng lẻ
            slip_vals_list = []
            for emp in employees:
                contract = contract_map.get(emp.id)
                if emp.id in existing_emp_ids:
                    # Cập nhật contract_id mới nhất cho các phiếu đã tồn tại nếu chưa có
                    existing_s = Slip.search([('payslip_run_id', '=', batch.id), ('employee_id', '=', emp.id)], limit=1)
                    if existing_s and contract and existing_s.contract_id.id != contract.id:
                        existing_s.write({'contract_id': contract.id})
                    continue
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

            # 3) Async Daemon Worker Thread Execution
            # Computes all slips iteratively using 100% accurate single-employee logic (action_compute_sheet)
            to_compute = Slip.search([
                ('payslip_run_id', '=', batch.id),
                ('state', 'in', ('draft', 'verify')),
            ])

            if not to_compute:
                batch.write({
                    'compute_status': 'completed',
                    'computed_count': len(existing_emp_ids) + created,
                    'total_count': len(existing_emp_ids) + created,
                })
                request.env.cr.commit()
                return _success_response({
                    'batch_id': batch.id,
                    'status': 'completed',
                    'created': created,
                    'computed': 0,
                    'total': 0,
                }, message='Tất cả phiếu lương trong kỳ đã hoàn tất.')

            db_name = request.env.cr.dbname
            slip_ids = to_compute.ids

            # 🚀 Bulk delete ALL old lines upfront & reset slip status, committing immediately to DB
            # so reloading the page during compute displays clean blank/null state
            old_lines = env['hb.payslip.line'].sudo().search([('payslip_id', 'in', slip_ids)])
            if old_lines:
                old_lines.unlink()
            to_compute.write({
                'x_teaching_computed': False,
                'gross_amount': 0,
                'net_amount': 0,
            })

            batch.write({
                'compute_status': 'processing',
                'computed_count': 0,
                'total_count': len(slip_ids),
                'compute_error': False,
            })
            request.env.cr.commit()

            worker = threading.Thread(
                target=_run_async_batch_compute,
                args=(db_name, batch.id, slip_ids),
                daemon=True,
            )
            worker.start()

            return _success_response({
                'batch_id': batch.id,
                'status': 'processing',
                'created': created,
                'computed': 0,
                'total': len(slip_ids),
            }, message=f'🚀 Đã bắt đầu tính toán lương ngầm cho {len(slip_ids)} nhân viên!')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('compute_all_payslips error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/compute-status', type='http', auth='user',
                methods=['GET'], csrf=False)
    def compute_status(self, **kw):
        """Check progress of background payroll calculation directly from batch record."""
        try:
            month = int(kw.get('month', 0))
            year = int(kw.get('year', 0))
            batch_id = int(kw.get('batch_id', 0))

            env = request.env
            Batch = env['hb.payslip.run'].sudo()

            if batch_id:
                batch = Batch.browse(batch_id)
            elif month and year:
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                batch = Batch.search([
                    ('date_start', '=', f'{year}-{month:02d}-01'),
                    ('date_end', '=', f'{year}-{month:02d}-{last_day:02d}'),
                ], limit=1)
            else:
                return _error_response('batch_id or month/year is required.')

            if not batch or not batch.exists():
                return _success_response({'status': 'idle', 'computed': 0, 'total': 0})

            return _success_response({
                'batch_id': batch.id,
                'status': batch.compute_status or 'idle',
                'computed': batch.computed_count or 0,
                'total': batch.total_count or 0,
                'error': batch.compute_error or '',
            })
        except Exception as e:
            _logger.exception('compute_status error')
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

            # 2) Payslips trong kỳ — chỉ lấy từ batch draft/verify (chưa lưu lịch sử)
            #    Payslips từ batch close đã lưu lịch sử → hiển thị ở tab Lịch sử
            closed_batch_ids = env['hb.payslip.run'].sudo().search(
                [('state', '=', 'close')]).ids
            slip_domain = [
                ('date_from', '>=', date_start),
                ('date_from', '<', date_end),
                ('state', '!=', 'cancel'),
            ]
            if closed_batch_ids:
                slip_domain.append(('payslip_run_id', 'not in', closed_batch_ids))
            slips = env['hb.payslip'].sudo().search(
                slip_domain, order='date_from desc, id desc',
            )
            # Auto-confirm unconfirmed slips when past end_day deadline, or reset auto-confirmed if deadline extended
            ICP = env['ir.config_parameter'].sudo()
            end_day = int(ICP.get_param('hocba_payroll.confirm_end_day', '10'))
            today = fields.Date.today()
            if today.day > end_day:
                slips_to_autoconfirm = slips.filtered(
                    lambda s: s.x_employee_confirm in ('pending', 'rejected') or (s.x_confirm_deadline and fields.Datetime.now() > s.x_confirm_deadline)
                )
                if slips_to_autoconfirm:
                    write_vals = {
                        'x_employee_confirm': 'confirmed',
                        'x_confirmed_date': fields.Datetime.now(),
                    }
                    # Safely set x_auto_confirm if the column exists
                    try:
                        slips_to_autoconfirm.write({**write_vals, 'x_auto_confirm': True})
                    except Exception:
                        slips_to_autoconfirm.write(write_vals)
                    env.cr.commit()
            else:
                # Within deadline & deadline was extended:
                # ONLY reset slips that were auto-confirmed (x_auto_confirm=True).
                # Slips where x_auto_confirm=False (employee manually confirmed) are NEVER touched.
                auto_confirmed_slips = slips.filtered(
                    lambda s: s.x_employee_confirm == 'confirmed' and s.x_auto_confirm
                )
                if auto_confirmed_slips:
                    auto_confirmed_slips.write({
                        'x_employee_confirm': 'pending',
                        'x_auto_confirm': False,
                        'x_confirmed_date': False,
                    })
                    env.cr.commit()

            slip_map = {}  # employee_id → payslip (first = latest)
            for s in slips:
                if s.employee_id.id not in slip_map:
                    slip_map[s.employee_id.id] = s

            # 3) Active employees & prefetch line amounts in 1 DB query
            employees = env['hr.employee'].sudo().search(
                [('active', '=', True)],
                order='x_employee_code, id',
            )

            slip_line_map = {}
            if slip_map:
                valid_slip_ids = [s.id for s in slip_map.values()]
                all_lines = env['hb.payslip.line'].sudo().search([('payslip_id', 'in', valid_slip_ids)])
                for ln in all_lines:
                    slip_line_map.setdefault(ln.payslip_id.id, {})[ln.code] = ln.amount

            rows = []
            for emp in employees:
                slip = slip_map.get(emp.id)
                amounts = slip_line_map.get(slip.id, {}) if slip else {}
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
                    'auto_confirm': getattr(slip, 'x_auto_confirm', False) if slip else False,
                    'employee_feedback': slip.x_employee_feedback or '' if slip else '',
                    'email_sent': slip.x_email_sent if slip else False,
                    'gross_amount': slip.gross_amount if slip else 0,
                    'net_amount': slip.net_amount if slip else 0,
                    'access_token': slip.x_access_token if slip else None,
                    'confirm_deadline': str(slip.x_confirm_deadline) if slip and slip.x_confirm_deadline else None,
                    'amounts': amounts,
                })

            return _success_response({
                'month': month, 'year': year,
                'columns': columns, 'employees': rows,
            })
        except Exception as e:
            _logger.exception('employee_payroll_summary error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # SALARY HISTORY (lịch sử lương — chỉ lấy từ batch đã close)
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/salary-history', type='http', auth='user',
                methods=['GET'], csrf=False)
    def salary_history(self, **kw):
        """Lịch sử lương — trả danh sách NV kèm bảng lương từ batch đã close."""
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

            # 2) Payslips từ batch đã close (đã lưu lịch sử)
            closed_batch_ids = env['hb.payslip.run'].sudo().search(
                [('state', '=', 'close')]).ids
            if not closed_batch_ids:
                return _success_response({
                    'month': month, 'year': year,
                    'columns': columns, 'employees': [],
                })

            slips = env['hb.payslip'].sudo().search(
                [('date_from', '>=', date_start),
                 ('date_from', '<', date_end),
                 ('payslip_run_id', 'in', closed_batch_ids),
                 ('state', '!=', 'cancel')],
                order='employee_id, id desc',
            )
            slip_map = {}
            for s in slips:
                if s.employee_id.id not in slip_map:
                    slip_map[s.employee_id.id] = s

            slip_line_map = {}
            if slip_map:
                valid_slip_ids = [s.id for s in slip_map.values()]
                all_lines = env['hb.payslip.line'].sudo().search([('payslip_id', 'in', valid_slip_ids)])
                for ln in all_lines:
                    slip_line_map.setdefault(ln.payslip_id.id, {})[ln.code] = ln.amount

            rows = []
            for emp_id, slip in slip_map.items():
                emp = slip.employee_id
                amounts = slip_line_map.get(slip.id, {})
                rows.append({
                    'id': emp.id,
                    'code': emp.x_employee_code or '',
                    'name': emp.name or '',
                    'job_title': emp.job_id.name if emp.job_id else '',
                    'department': emp.department_id.name if emp.department_id else '',
                    'payslip_id': slip.id,
                    'payslip_state': slip.state,
                    'employee_confirm': slip.x_employee_confirm
                        if hasattr(slip, 'x_employee_confirm') else None,
                    'gross_amount': slip.gross_amount,
                    'net_amount': slip.net_amount,
                    'amounts': amounts,
                })

            # Sort by employee code
            rows.sort(key=lambda r: r.get('code', ''))

            return _success_response({
                'month': month, 'year': year,
                'columns': columns, 'employees': rows,
            })
        except Exception as e:
            _logger.exception('salary_history error')
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
    # ── Transfer list helpers ─────────────────────────────────────
    @staticmethod
    def _get_emp_bank(emp):
        """Get employee bank account — compatible with Community."""
        if hasattr(emp, 'bank_account_id') and emp.bank_account_id:
            return emp.bank_account_id
        partner = (
            getattr(emp, 'address_home_id', None)
            or getattr(emp, 'work_contact_id', None)
        )
        if partner and partner.bank_ids:
            return partner.bank_ids[0]
        return None

    @staticmethod
    def _build_bank_lookup(env):
        """Map bank format code → full name from hb.bank.format."""
        entries = env['hb.bank.format'].sudo().search([('active', '=', True)])
        lookup = {}
        for e in entries:
            if e.code:
                lookup[e.code.upper()] = e.name
        return lookup

    @staticmethod
    def _resolve_bank_name(bank_acc, bank_lookup):
        """Resolve employee bank account → format full name and code.

        Robust matching order:
        1. BIC code match: bic contains code or code contains bic
        2. Exact code match: bank name / code matches format code exactly
        3. Full name inclusion match: format name in bank name OR bank name in format name
        4. Substring / acronym match: code in bank name
        """
        if not bank_acc:
            return '', ''
        bank = bank_acc.bank_id
        if not bank:
            return '', ''
        bname = (bank.name or '').strip()
        bic = (bank.bic or '').strip().upper()
        bname_lower = bname.lower()

        for code, full in bank_lookup.items():
            code_upper = code.upper()
            code_lower = code.lower()
            full_lower = (full or '').lower()

            # 1. BIC match
            if bic and (code_upper in bic or bic in code_upper):
                return code_upper, full
            # 2. Exact code match in bank name or code
            if code_upper == bname.upper():
                return code_upper, full
            # 3. Full format name match
            if full_lower and (full_lower in bname_lower or bname_lower in full_lower):
                return code_upper, full
            # 4. Code substring / acronym match
            if code_lower and code_lower in bname_lower:
                return code_upper, full

        return '', bname

    def _build_transfer_rows(self, month, year, bank_codes_filter=None):
        """Build transfer rows from CLOSED batches only.

        bank_codes_filter: list of bank codes to include, or None/empty for all.
        Returns (rows, bank_formats_list).
        """
        import calendar
        try:
            env = request.env
        except Exception:
            env = getattr(self, 'env', None)
        last_day = calendar.monthrange(year, month)[1]
        date_start = f'{year}-{month:02d}-01'
        date_end = f'{year}-{month:02d}-{last_day}'

        bank_lookup = self._build_bank_lookup(env)
        all_codes = set(bank_lookup.keys())

        # Find CLOSED batches for this period
        batches = env['hb.payslip.run'].sudo().search([
            ('state', '=', 'close'),
            ('date_start', '>=', date_start),
            ('date_start', '<=', date_end),
        ])
        if not batches:
            return [], []

        # Payslips from closed batches
        slips = env['hb.payslip'].sudo().search([
            ('payslip_run_id', 'in', batches.ids),
            ('state', '=', 'done'),
        ])
        slip_map = {}
        for s in slips:
            if s.employee_id.id not in slip_map:
                slip_map[s.employee_id.id] = s

        # Active employees
        employees = env['hr.employee'].sudo().search(
            [('active', '=', True)], order='x_employee_code, id',
        )

        codes_upper = None
        if bank_codes_filter:
            cleaned = {c.strip().upper() for c in bank_codes_filter if c.strip()}
            if 'ALL' in cleaned or (all_codes and cleaned >= all_codes):
                codes_upper = None
            else:
                codes_upper = cleaned

        rows = []
        for emp in employees:
            slip = slip_map.get(emp.id)
            if not slip:
                continue
            net_line = slip.line_ids.filtered(lambda l: l.code == 'thuc_lanh')
            net = net_line[0].amount if net_line else 0.0

            bank_acc = self._get_emp_bank(emp)
            acc_number = (bank_acc.acc_number or '').strip() if bank_acc else ''
            code, bank_name = self._resolve_bank_name(bank_acc, bank_lookup)

            # Filter by bank codes
            if codes_upper and code.upper() not in codes_upper:
                continue

            rows.append({
                'employee_id': emp.id,
                'employee_code': getattr(emp, 'x_employee_code', '') or '',
                'name': emp.name or '',
                'bank_account': acc_number,
                'bank_code': code,
                'bank_name': bank_name,
                'net_amount': int(net),
                'payslip_state': slip.state,
                'employee_confirm': getattr(slip, 'x_employee_confirm', None),
            })

        # Bank formats for dropdown
        formats = env['hb.bank.format'].sudo().search(
            [('active', '=', True)], order='sequence, name')
        fmt_list = [{
            'id': f.id, 'name': f.name, 'code': f.code or '',
            'description_template': f.description_template or '',
        } for f in formats]

        return rows, fmt_list

    @http.route('/hocba-hrm/api/payroll/transfer-list', type='http', auth='user',
                methods=['GET'], csrf=False)
    def transfer_list(self, **kw):
        """Danh sách chuyển khoản lương — CHỈ từ lịch sử (closed batches)."""
        try:
            today = fields.Date.today()
            month = int(kw.get('month') or today.month)
            year = int(kw.get('year') or today.year)

            # Optional bank_codes filter (comma-separated)
            bank_codes_raw = kw.get('bank_codes', '')
            bank_codes = [
                c.strip() for c in bank_codes_raw.split(',') if c.strip()
            ] if bank_codes_raw else None

            # If file_id is given, load from that bank file record
            if kw.get('file_id'):
                bf = request.env['hb.bank.file'].sudo().browse(
                    int(kw['file_id']))
                if bf.exists():
                    ds = bf.batch_id.date_start
                    if ds:
                        month, year = ds.month, ds.year
                    if bf.bank_codes and bf.bank_codes != 'ALL':
                        bank_codes = [
                            c.strip()
                            for c in bf.bank_codes.split(',') if c.strip()
                        ]

            rows, fmt_list = self._build_transfer_rows(
                month, year, bank_codes)

            return _success_response({
                'month': month, 'year': year,
                'employees': rows,
                'bank_formats': fmt_list,
            })
        except Exception as e:
            _logger.exception('transfer_list error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/transfer-file', type='http',
                auth='user', methods=['POST'], csrf=False)
    def create_transfer_file(self, **kw):
        """Tạo file chuyển khoản từ lịch sử bảng lương (closed batches)."""
        try:
            body = _get_json_body()
            month = int(body.get('month', 0))
            year = int(body.get('year', 0))
            if not month or not year:
                return _error_response('month and year are required.')

            bank_codes = body.get('bank_codes', [])  # list of codes
            if isinstance(bank_codes, str):
                bank_codes = [c.strip() for c in bank_codes.split(',') if c.strip()]

            import calendar
            env = request.env
            last_day = calendar.monthrange(year, month)[1]
            date_start = f'{year}-{month:02d}-01'
            date_end = f'{year}-{month:02d}-{last_day}'

            # Must have a closed batch
            batch = env['hb.payslip.run'].sudo().search([
                ('state', '=', 'close'),
                ('date_start', '>=', date_start),
                ('date_start', '<=', date_end),
            ], limit=1)
            if not batch:
                return _error_response(
                    f'Không tìm thấy lịch sử lương cho tháng {month}/{year}. '
                    'Hãy lưu lịch sử bảng lương trước.'
                )

            rows, _ = self._build_transfer_rows(
                month, year, bank_codes or None)

            all_bank_lookup = self._build_bank_lookup(env)
            all_codes = set(all_bank_lookup.keys())
            req_codes = {c.strip().upper() for c in bank_codes} if bank_codes else set()

            if not bank_codes or 'ALL' in req_codes or (all_codes and req_codes >= all_codes):
                codes_str = 'ALL'
            else:
                codes_str = ','.join(c.strip().upper() for c in bank_codes if c.strip())

            bank_label = 'Tất cả NH' if codes_str == 'ALL' else codes_str
            filename = f'CK_T{month:02d}_{year}_{codes_str}'

            bf = env['hb.bank.file'].sudo().create({
                'name': filename,
                'batch_id': batch.id,
                'bank_codes': codes_str,
                'payment_date': fields.Date.today(),
                'total_amount': sum(r['net_amount'] for r in rows),
                'record_count': len(rows),
                'generated_by': env.uid,
                'generated_at': fields.Datetime.now(),
            })

            return _success_response(
                bf._to_api_dict(),
                message=f'Đã tạo file chuyển khoản: {len(rows)} nhân viên, '
                        f'ngân hàng: {bank_label}.',
            )
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_transfer_file error')
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
        """Return available lookup sources and their fields for the frontend.

        Gồm nguồn curated (Chấm công…) + MỌI model có liên kết hr.employee, mỗi
        model kèm các trường số. FE hiển thị dropdown có tìm kiếm cho nguồn/trường.
        """
        try:
            from odoo.addons.hocba_payroll.models.payslip import list_lookup_sources
            return _success_response(list_lookup_sources(request.env))
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
    #  Confirm Period Config
    # ══════════════════════════════════════════════════════════
    _CONFIRM_CFG_KEYS = {
        'confirm_period_days': 'hocba_payroll.confirm_period_days',
        'auto_send_mail':      'hocba_payroll.auto_send_mail',
    }

    @http.route('/hocba-hrm/api/payroll/confirm-config', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_confirm_config(self, **kw):
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            return _success_response({
                'confirm_start_day': int(
                    ICP.get_param('hocba_payroll.confirm_start_day', '5')
                ),
                'confirm_end_day': int(
                    ICP.get_param('hocba_payroll.confirm_end_day', '10')
                ),
                'confirm_period_days': int(
                    ICP.get_param('hocba_payroll.confirm_period_days', '5')
                ),
                'auto_send_mail': ICP.get_param(
                    'hocba_payroll.auto_send_mail', 'false'
                ) == 'true',
            })
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/confirm-config', type='http',
                auth='user', methods=['POST'], csrf=False)
    def save_confirm_config(self, **kw):
        try:
            body = _get_json_body()
            ICP = request.env['ir.config_parameter'].sudo()
            start_day = int(body.get('confirm_start_day', ICP.get_param('hocba_payroll.confirm_start_day', '5')))
            end_day = int(body.get('confirm_end_day', ICP.get_param('hocba_payroll.confirm_end_day', '10')))

            if end_day < start_day:
                return _error_response(
                    f'Ngày kết thúc phản hồi (ngày {end_day:02d}) không được nhỏ hơn Ngày bắt đầu gửi mail (ngày {start_day:02d}).',
                    status=400
                )

            ICP.set_param('hocba_payroll.confirm_start_day', str(start_day))
            ICP.set_param('hocba_payroll.confirm_end_day', str(end_day))

            if 'confirm_period_days' in body:
                days = max(1, min(int(body['confirm_period_days']), 90))
                ICP.set_param('hocba_payroll.confirm_period_days', str(days))
            if 'auto_send_mail' in body:
                ICP.set_param(
                    'hocba_payroll.auto_send_mail',
                    'true' if body['auto_send_mail'] else 'false',
                )

            # Re-evaluate slips when deadline is extended (today <= new end_day)
            # ONLY reset slips that were auto-confirmed by the system (x_auto_confirm=True).
            # Slips where x_auto_confirm=False (employee manually confirmed) are NEVER reset.
            today = fields.Date.today()
            if today.day <= end_day:
                closed_batches = request.env['hb.payslip.run'].sudo().search([('state', '=', 'close')]).ids
                domain = [
                    ('state', '!=', 'cancel'),
                    ('x_employee_confirm', '=', 'confirmed'),
                    ('x_auto_confirm', '=', True),
                ]
                if closed_batches:
                    domain.append(('payslip_run_id', 'not in', closed_batches))
                auto_slips = request.env['hb.payslip'].sudo().search(domain)
                if auto_slips:
                    auto_slips.write({
                        'x_employee_confirm': 'pending',
                        'x_auto_confirm': False,
                        'x_confirmed_date': False,
                    })
                    request.env.cr.commit()
            return _success_response({'saved': True},
                                     message='Đã lưu cấu hình khoảng thời gian gửi mail & phản hồi lương.')
        except Exception as e:
            return _error_response(str(e), status=500)

    # ══════════════════════════════════════════════════════════
    #  Unified Payroll Config Endpoint (High Performance Aggregation)
    # ══════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/config-all', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_payroll_config_all(self, **kw):
        """Unified endpoint returning rules, banks, emailjs config, and confirm config in 1 request."""
        try:
            # 1. Salary Rules
            rules = request.env['hb.salary.rule'].sudo().search([('active', '=', True)], order='sequence, id')
            rules_data = [{
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
            } for r in rules]

            # 2. Bank Formats
            formats = request.env['hb.bank.format'].sudo().search([('active', '=', True)], order='sequence, name')
            banks_data = [{
                'id': f.id, 'name': f.name, 'code': f.code or '',
                'sequence': f.sequence,
                'transfer_type': f.transfer_type or 'normal',
                'formatter_class': f.formatter_class or '',
            } for f in formats]

            # 3. EmailJS Config
            ICP = request.env['ir.config_parameter'].sudo()
            emailjs_data = {
                k: ICP.get_param(v, default='') for k, v in self._EMAILJS_KEYS.items()
            }

            # 4. Confirm Config
            confirm_data = {
                'confirm_start_day': int(ICP.get_param('hocba_payroll.confirm_start_day', '5')),
                'confirm_end_day': int(ICP.get_param('hocba_payroll.confirm_end_day', '10')),
                'confirm_period_days': int(ICP.get_param('hocba_payroll.confirm_period_days', '5')),
                'auto_send_mail': ICP.get_param('hocba_payroll.auto_send_mail', 'false') == 'true',
            }

            return _success_response({
                'rules': rules_data,
                'banks': banks_data,
                'emailjs_config': emailjs_data,
                'confirm_config': confirm_data,
            })
        except Exception as e:
            return _error_response(str(e), status=500)


    # ══════════════════════════════════════════════════════════
    #  Send payslips mail (Backend Odoo engine + Confirmation window)
    # ══════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip/send-mail', type='http',
                auth='user', methods=['POST'], csrf=False)
    def send_payslip_mail(self, **kw):
        """Send payslip emails via backend Odoo engine with window validation."""
        try:
            body = _get_json_body()
            ids = body.get('payslip_ids', [])
            if not ids:
                return _error_response('Missing payslip_ids.')

            ICP = request.env['ir.config_parameter'].sudo()
            start_day = int(ICP.get_param('hocba_payroll.confirm_start_day', '5'))
            end_day = int(ICP.get_param('hocba_payroll.confirm_end_day', '10'))
            today = fields.Date.today()
            current_day = today.day

            if current_day < start_day:
                return _error_response(
                    f'Chưa đến ngày gửi mail phiếu lương! Khoảng thời gian cho phép gửi mail là từ ngày {start_day:02d} đến ngày {end_day:02d} hàng tháng.',
                    status=400
                )
            if current_day > end_day:
                return _error_response(
                    f'Đã hết thời hạn gửi mail phiếu lương (Hạn chót ngày {end_day:02d} hàng tháng). Các phiếu lương đã tự động được xác nhận. Nếu muốn gửi lại mail, HR vui lòng nới rộng Ngày kết thúc trong tab Cấu hình lương!',
                    status=400
                )

            slips = request.env['hb.payslip'].sudo().browse(ids)
            now = fields.Datetime.now()
            confirm_days = max(1, end_day - start_day)
            from datetime import timedelta
            deadline = now + timedelta(days=confirm_days)

            sent_count = 0
            for slip in slips.filtered(lambda s: s.exists()):
                vals = {
                    'x_email_sent': True,
                    'x_email_sent_date': now,
                    'x_confirm_deadline': deadline,
                }
                if slip.x_employee_confirm == 'rejected':
                    vals['x_employee_confirm'] = 'pending'
                    vals['x_employee_feedback'] = False
                slip.write(vals)

                # Attempt sending via Odoo mail template if exists
                try:
                    if hasattr(slip, 'action_send_email'):
                        slip.action_send_email()
                except Exception:
                    pass

                month = slip.date_from.strftime('%m') if slip.date_from else ''
                year = slip.date_from.strftime('%Y') if slip.date_from else ''
                email_to = slip.employee_id.work_email or ''
                slip.message_post(
                    body=_(
                        'Đã phát hành email phiếu lương tháng %(m)s/%(y)s tới <b>%(email)s</b>. '
                        'Khung thời gian phản hồi đến %(dl)s.',
                        m=month, y=year, email=email_to,
                        dl=deadline.strftime('%d/%m/%Y %H:%M'),
                    ),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
                sent_count += 1

            return _success_response({
                'sent': sent_count,
                'confirm_deadline': deadline.strftime('%Y-%m-%d %H:%M:%S'),
            }, message=f'Đã gửi mail phát hành phiếu lương cho {sent_count} nhân viên.')
        except Exception as e:
            _logger.exception('send_payslip_mail error')
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
                # Calculate confirm deadline from config
                ICP = request.env['ir.config_parameter'].sudo()
                confirm_days = int(
                    ICP.get_param('hocba_payroll.confirm_period_days', '3')
                )
                from datetime import timedelta
                vals['x_confirm_deadline'] = now + timedelta(days=confirm_days)
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

    # ══════════════════════════════════════════════════════════
    # EMPLOYEE SELF-SERVICE PAYSLIPS (Authenticated)
    # ══════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/my-payslips', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_my_payslips(self, **kw):
        """Fetch payslips for the currently logged-in employee."""
        try:
            user = request.env.user
            employee = request.env['hr.employee'].sudo().search([
                '|', ('user_id', '=', user.id), ('work_email', '=ilike', user.partner_id.email or '')
            ], limit=1)

            if not employee:
                return _success_response({'employee': None, 'payslips': []})

            slips = request.env['hb.payslip'].sudo().search([
                ('employee_id', '=', employee.id)
            ], order='date_from desc')

            now = fields.Datetime.now()
            res = []
            for s in slips:
                lines = [{
                    'id': l.id,
                    'code': l.code,
                    'name': l.name,
                    'amount': l.amount,
                    'category_code': l.category_id.code if l.category_id else (l.code or ''),
                } for l in s.line_ids.sorted('sequence')]

                worked_recs = request.env['hb.payslip.worked_days'].sudo().search([('payslip_id', '=', s.id)])
                worked = [{
                    'id': w.id,
                    'code': w.code,
                    'name': w.name,
                    'number_of_days': w.number_of_days,
                    'number_of_hours': w.number_of_hours,
                    'amount': getattr(w, 'amount', 0),
                } for w in worked_recs]

                is_expired = bool(s.x_confirm_deadline and now > s.x_confirm_deadline)

                res.append({
                    'id': s.id,
                    'number': s.number or f'#{s.id}',
                    'month': s.date_from.strftime('%m') if s.date_from else '',
                    'year': s.date_from.strftime('%Y') if s.date_from else '',
                    'date_from': s.date_from.strftime('%Y-%m-%d') if s.date_from else '',
                    'date_to': s.date_to.strftime('%Y-%m-%d') if s.date_to else '',
                    'gross_amount': s.gross_amount,
                    'net_amount': s.net_amount,
                    'state': s.state,
                    'email_sent': s.x_email_sent,
                    'email_sent_date': s.x_email_sent_date.strftime('%Y-%m-%d %H:%M:%S') if s.x_email_sent_date else None,
                    'confirm_deadline': s.x_confirm_deadline.strftime('%Y-%m-%d %H:%M:%S') if s.x_confirm_deadline else None,
                    'employee_confirm': s.x_employee_confirm or 'pending',
                    'employee_feedback': s.x_employee_feedback or '',
                    'confirmed_date': s.x_confirmed_date.strftime('%Y-%m-%d %H:%M:%S') if s.x_confirmed_date else None,
                    'is_expired': is_expired,
                    'lines': lines,
                    'worked_days': worked,
                })

            return _success_response({
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'code': employee.x_employee_code or '',
                    'department': employee.department_id.name if employee.department_id else '',
                    'job_title': employee.job_id.name if employee.job_id else '',
                },
                'payslips': res,
            })
        except Exception as e:
            _logger.exception('get_my_payslips error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # EMPLOYEE SELF-CONFIRM (authenticated — requires login)
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>/employee-confirm',
                type='http', auth='user', methods=['POST'], csrf=False)
    def employee_confirm_payslip(self, slip_id, **kw):
        """Employee confirms/rejects their own payslip (must be logged in)."""
        try:
            body = _get_json_body()
            action = body.get('action')
            if action not in ('confirm', 'reject'):
                return _error_response('Invalid action.')

            # Current user → employee
            user = request.env.user
            employee = request.env['hr.employee'].sudo().search([
                '|', ('user_id', '=', user.id), ('work_email', '=ilike', user.partner_id.email or '')
            ], limit=1)
            if not employee:
                return _error_response(
                    'Không tìm thấy hồ sơ nhân viên của bạn.', status=403)

            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)

            # Verify ownership
            if slip.employee_id.id != employee.id:
                return _error_response(
                    'Bạn không có quyền xác nhận phiếu lương này.', status=403)

            now = fields.Datetime.now()
            if slip.x_confirm_deadline and now > slip.x_confirm_deadline:
                return _error_response('Đã hết thời hạn phản hồi phiếu lương.')

            if action == 'confirm':
                slip.write({
                    'x_employee_confirm': 'confirmed',
                    'x_auto_confirm': False,
                    'x_confirmed_date': now,
                })
                try:
                    slip.message_post(
                        body=_(
                            'Nhân viên <b>%(name)s</b> đã <b>xác nhận (đồng ý)</b> phiếu lương.',
                            name=employee.name,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception as msg_err:
                    _logger.warning('message_post note failed: %s', msg_err)
            else:
                feedback = (body.get('feedback') or '').strip()
                if not feedback:
                    return _error_response('Vui lòng nhập lý do từ chối.')
                slip.write({
                    'x_employee_confirm': 'rejected',
                    'x_auto_confirm': False,
                    'x_employee_feedback': feedback,
                    'x_confirmed_date': fields.Datetime.now(),
                })
                try:
                    slip.message_post(
                        body=_(
                            'Nhân viên <b>%(name)s</b> đã <b>từ chối</b> phiếu lương. '
                            'Lý do: %(fb)s',
                            name=employee.name, fb=feedback,
                        ),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                except Exception as msg_err:
                    _logger.warning('message_post note failed: %s', msg_err)

            return _success_response({
                'status': slip.x_employee_confirm,
            })
        except Exception as e:
            _logger.exception('employee_confirm_payslip error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/<int:slip_id>/reset-confirm',
                type='http', auth='user', methods=['POST'], csrf=False)
    def reset_payslip_confirm(self, slip_id, **kw):
        """HR resets employee confirmation back to pending.

        Allows HR to undo confirm/reject so salary can be recalculated
        and mail resent. Only works while batch is not yet closed.
        """
        try:
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            # Block if batch is already closed (history saved)
            if slip.payslip_run_id and slip.payslip_run_id.state == 'close':
                return _error_response(
                    'Batch đã lưu lịch sử, không thể reset xác nhận.')
            old_status = slip.x_employee_confirm
            slip.write({
                'x_employee_confirm': 'pending',
                'x_auto_confirm': False,
                'x_employee_feedback': False,
                'x_confirm_deadline': False,  # #6: clear deadline on reset
                'x_email_sent': False,
                'x_email_sent_date': False,
            })
            try:
                slip.message_post(
                    body=_(
                        'HR đã reset trạng thái xác nhận của %(name)s '
                        '(%(old)s → chờ xác nhận). Bởi: %(user)s',
                        name=slip.employee_id.name,
                        old=old_status,
                        user=request.env.user.name,
                    ),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
            except Exception:
                pass
            return _success_response({
                'status': 'pending',
            }, message='Đã reset xác nhận.')
        except Exception as e:
            _logger.exception('reset_payslip_confirm error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/payslip/bulk-reset-confirm',
                type='http', auth='user', methods=['POST'], csrf=False)
    def bulk_reset_payslip_confirm(self, **kw):
        """Bulk reset employee confirmation back to pending for specified payslips or all in batch.

        - Instant 1-query DB write for ultra-fast performance on 100+ employees.
        - Resets confirm status, feedback, deadline AND email sent flags back to 'Chưa gửi mail'.
        """
        try:
            body = _get_json_body()
            ids = body.get('payslip_ids', [])
            month = int(body.get('month', 0))
            year = int(body.get('year', 0))

            env = request.env
            if ids:
                slips = env['hb.payslip'].sudo().browse(ids)
            elif month and year:
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                date_start = f'{year}-{month:02d}-01'
                date_end = f'{year}-{month:02d}-{last_day:02d}'
                batch = env['hb.payslip.run'].sudo().search([
                    ('date_start', '=', date_start),
                    ('date_end', '=', date_end),
                    ('state', '=', 'draft'),
                ], limit=1)
                if not batch:
                    return _error_response('Không tìm thấy kỳ lương nháp.')
                slips = env['hb.payslip'].sudo().search([('payslip_run_id', '=', batch.id)])
            else:
                return _error_response('Missing payslip_ids or month/year.')

            valid_slips = slips.filtered(lambda s: s.exists() and (not s.payslip_run_id or s.payslip_run_id.state != 'close'))
            if not valid_slips:
                return _error_response('Không có phiếu lương hợp lệ để reset.')

            # ⚡ Bulk update 100% records in 1 single SQL trip (Ultra fast performance)
            valid_slips.write({
                'x_employee_confirm': 'pending',
                'x_employee_feedback': False,
                'x_confirm_deadline': False,
                'x_email_sent': False,
                'x_email_sent_date': False,
            })
            count = len(valid_slips)

            return _success_response({'count': count}, message=f'Đã reset trạng thái xác nhận và mail về Chưa gửi cho {count} phiếu lương.')
        except Exception as e:
            _logger.exception('bulk_reset_payslip_confirm error')
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # DEV / SEED — Tạo dữ liệu lương demo (XÓA KHI LÊN PRODUCTION)
    # ═════════════════════════════════════════════════════════
    @http.route('/hocba-hrm/api/payroll/seed-history', type='http',
                auth='user', methods=['POST'], csrf=False)
    def seed_salary_history(self, **kw):
        """[DEV] Seed lịch sử lương cho tháng bất kỳ.

        Body: { "month": 5, "year": 2026 }
        Lấy TẤT CẢ employee active trong DB + contract → tính lương →
        tạo batch + payslips → close batch ngay.
        Xóa batch cũ + bank file mồ côi nếu có.
        """
        try:
            body = _get_json_body()
            month = int(body.get('month', 5))
            year = int(body.get('year', 2026))

            import calendar
            import random
            random.seed(month * 100 + year)  # deterministic per month

            last_day = calendar.monthrange(year, month)[1]
            date_from = f'{year}-{month:02d}-01'
            date_end = f'{year}-{month:02d}-{last_day:02d}'

            env = request.env
            Batch = env['hb.payslip.run'].sudo()
            Slip = env['hb.payslip'].sudo()
            Employee = env['hr.employee'].sudo()
            Contract = env['hb.contract'].sudo()
            Structure = env['hb.salary.structure'].sudo()
            Rule = env['hb.salary.rule'].sudo()
            BankFile = env['hb.bank.file'].sudo()

            # ── Delete existing batch + orphan bank files for this period ──
            existing = Batch.search([
                ('date_start', '>=', date_from),
                ('date_start', '<=', date_end),
            ])
            for b in existing:
                # Delete bank files referencing this batch
                orphan_bf = BankFile.search([('batch_id', '=', b.id)])
                if orphan_bf:
                    orphan_bf.unlink()
                b.slip_ids.write({'state': 'draft'})
                b.write({'state': 'draft'})
                b.slip_ids.unlink()
                b.unlink()

            # Also clean up bank files with no valid batch
            all_bf = BankFile.search([])
            for bf in all_bf:
                if not bf.batch_id or not bf.batch_id.exists():
                    bf.unlink()

            # ── Create batch ──
            batch = Batch.create({
                'name': f'Lương Tháng {month:02d}/{year}',
                'date_start': date_from,
                'date_end': date_end,
                'state': 'draft',
            })

            # ── Find structure ──
            struct = Structure.search([('code', '=', 'STRUCT_OFFLINE')], limit=1)
            if not struct:
                return _error_response('STRUCT_OFFLINE not found.')

            # ── Build rule lookup ──
            rules = Rule.search([('structure_id', '=', struct.id)])
            rule_map = {}
            for r in rules:
                rule_map[r.code] = {
                    'rule_id': r.id,
                    'category_id': r.category_id.id if r.category_id else False,
                    'name': r.name,
                    'sequence': r.sequence,
                }

            # ── PIT calculator ──
            def calc_pit(w):
                if w <= 0:
                    return 0
                if w <= 10_000_000:
                    return round(w * 0.05)
                elif w <= 30_000_000:
                    return round(500_000 + (w - 10_000_000) * 0.10)
                elif w <= 60_000_000:
                    return round(2_500_000 + (w - 30_000_000) * 0.20)
                elif w <= 100_000_000:
                    return round(8_500_000 + (w - 60_000_000) * 0.30)
                else:
                    return round(20_500_000 + (w - 100_000_000) * 0.35)

            # ── Get ALL active employees ──
            employees = Employee.search(
                [('active', '=', True)], order='x_employee_code, id',
            )
            if not employees:
                return _error_response('Không có nhân viên active nào trong DB.')

            # ── Build contract map ──
            contracts = Contract.search([
                ('state', '=', 'open'),
                ('employee_id', 'in', employees.ids),
            ])
            contract_map = {}
            for c in contracts:
                if c.employee_id.id not in contract_map:
                    contract_map[c.employee_id.id] = c

            STANDARD_DAYS = 25
            created = 0
            no_contract = []
            slip_vals_list = []
            emp_details = []

            for emp in employees:
                contract = contract_map.get(emp.id)
                if not contract:
                    # Try any contract
                    contract = Contract.search([
                        ('employee_id', '=', emp.id),
                    ], order='id desc', limit=1)

                # Lương cơ bản: ưu tiên hr.version.wage (đúng nguồn form Nhân viên
                # hiển thị/HR chỉnh), fallback hb.contract.wage, rồi mặc định.
                ver = emp.version_id
                base = ((ver.wage if ver and 'wage' in ver._fields else 0)
                        or (contract.wage if contract else 0) or 5_700_000)

                # Randomize work days slightly for realism
                nctt_options = [STANDARD_DAYS, STANDARD_DAYS,
                                STANDARD_DAYS, STANDARD_DAYS - 1,
                                STANDARD_DAYS - 2, STANDARD_DAYS + 1]
                nctt = random.choice(nctt_options)
                nctt = max(18, min(nctt, 28))

                # Allowances from contract or defaults
                xangxe = (getattr(contract, 'x_pc_fuel', 0) or 0) if contract else 0
                dienthoai = (getattr(contract, 'x_sp_phone', 0) or 0) if contract else 0
                npt = (getattr(contract, 'x_dependent_count', 0) or 0) if contract else 0

                # Default allowances if contract has none
                if not xangxe:
                    xangxe = random.choice([500000, 800000, 1000000])
                if not dienthoai:
                    dienthoai = random.choice([400000, 500000, 800000, 1000000])

                # ── Compute salary ──
                F = base
                an_ca = round(50000 * nctt)
                tong_thu_nhap = round((an_ca + xangxe + dienthoai + F) / 25.0 * nctt) if nctt > 0 else 0
                tn_mien_thue = 730000
                tn_truoc_thue = tong_thu_nhap - tn_mien_thue
                giam_tru = 15500000 + int(npt) * 6200000
                bhxh_nv = round(F * 0.08)
                bhyt_nv = round(F * 0.015)
                bhtn_nv = round(F * 0.01)
                tn_tinh_thue = max(0, tn_truoc_thue - giam_tru - bhxh_nv - bhyt_nv - bhtn_nv)
                thue_tncn = calc_pit(tn_tinh_thue)
                thuc_lanh = round(tong_thu_nhap - bhxh_nv - bhyt_nv - bhtn_nv - thue_tncn)
                bhxh_ct = round(F * 0.175)
                bhyt_ct = round(F * 0.03)
                bhtn_ct = round(F * 0.01)

                amounts = {
                    'an_ca': an_ca, 'xang_xe': xangxe, 'dien_thoai': dienthoai,
                    'thuong_khac': 0, 'ho_tro_nuoi_con': 0,
                    'tong_thu_nhap': tong_thu_nhap, 'tn_mien_thue': tn_mien_thue,
                    'tn_truoc_thue': tn_truoc_thue, 'npt': npt, 'giam_tru': giam_tru,
                    'bhxh_8_nv': bhxh_nv, 'bhyt_1_5_nv': bhyt_nv, 'bhtn_1_nv': bhtn_nv,
                    'tn_tinh_thue': tn_tinh_thue, 'thue_tncn': thue_tncn,
                    'thuc_lanh': thuc_lanh,
                    'bhxh_17_5_ct': bhxh_ct, 'bhyt_3_ct': bhyt_ct, 'bhtn_1_ct': bhtn_ct,
                }

                # ── Build payslip lines ──
                line_vals = []
                for code, amt in amounts.items():
                    rm = rule_map.get(code)
                    if rm:
                        line_vals.append((0, 0, {
                            'rule_id': rm['rule_id'],
                            'category_id': rm['category_id'],
                            'code': code, 'name': rm['name'],
                            'sequence': rm['sequence'],
                            'quantity': 1.0, 'rate': amt, 'amount': amt,
                        }))

                # ── Worked days ──
                wd_vals = [
                    (0, 0, {'name': 'Ngày công chuẩn', 'code': 'STANDARD',
                            'sequence': 1, 'number_of_days': STANDARD_DAYS,
                            'number_of_hours': STANDARD_DAYS * 8}),
                    (0, 0, {'name': 'Ngày công thực tế', 'code': 'WORK100',
                            'sequence': 2, 'number_of_days': nctt,
                            'number_of_hours': nctt * 8}),
                ]

                slip_vals_list.append({
                    'employee_id': emp.id,
                    'contract_id': contract.id if contract else False,
                    'structure_id': struct.id,
                    'payslip_run_id': batch.id,
                    'date_from': date_from,
                    'date_to': date_end,
                    'state': 'done',
                    'x_employee_confirm': 'confirmed',
                    'line_ids': line_vals,
                    'worked_days_ids': wd_vals,
                })
                created += 1
                emp_details.append({
                    'code': emp.x_employee_code or '',
                    'name': emp.name or '',
                    'base': F,
                    'nctt': nctt,
                    'net': thuc_lanh,
                    'has_contract': bool(contract),
                })

            # Bulk create
            if slip_vals_list:
                Slip.create(slip_vals_list)

            # Close batch
            batch.write({'state': 'close'})

            return _success_response({
                'batch_id': batch.id,
                'batch_name': batch.name,
                'created': created,
                'no_contract': no_contract,
                'employees': emp_details,
                'month': month,
                'year': year,
            }, message=f'Đã seed {created} payslips cho tháng {month:02d}/{year}. '
                       f'Batch đã close → hiện trong lịch sử lương & chuyển khoản.')
        except Exception as e:
            _logger.exception('seed_salary_history error')
            return _error_response(str(e), status=500)



    # ── SALE SALARY LEVELS API ──────────────────────────────────────────────
    @http.route('/hocba-hrm/api/payroll/sale-salary-level', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_sale_salary_levels(self, **kw):
        """Get all configured Sale Salary Levels (or auto-seed defaults if empty)."""
        try:
            Model = request.env['hb.sale.salary.level'].sudo()
            Model.init_default_sale_levels()
            recs = Model.search([('active', '=', True)], order='sequence, id')
            res = [{
                'id': r.id,
                'levelCode': r.level_code,
                'name': r.name,
                'sequence': r.sequence,
                'kpiTarget': r.kpi_target,
                'baseWage': r.base_wage,
            } for r in recs]
            return _success_response(res)
        except Exception as e:
            _logger.exception('get_sale_salary_levels error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/sale-salary-level', type='http',
                auth='user', methods=['POST'], csrf=False)
    def create_sale_salary_level(self, **kw):
        """Create a new Sale Salary Level."""
        try:
            data = _get_json_body()
            vals = {
                'level_code': data.get('levelCode') or f"LEVEL_{data.get('sequence', 10)}",
                'name': data.get('name', 'Level mới'),
                'sequence': int(data.get('sequence', 10)),
                'kpi_target': float(data.get('kpiTarget', 1.0)),
                'base_wage': float(data.get('baseWage', 7000000.0)),
            }
            rec = request.env['hb.sale.salary.level'].sudo().create(vals)
            return _success_response({
                'id': rec.id,
                'levelCode': rec.level_code,
                'name': rec.name,
                'sequence': rec.sequence,
                'kpiTarget': rec.kpi_target,
                'baseWage': rec.base_wage,
            }, message='Đã thêm Level mới thành công.')
        except Exception as e:
            _logger.exception('create_sale_salary_level error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/sale-salary-level/<int:level_id>', type='http',
                auth='user', methods=['PUT', 'POST'], csrf=False)
    def update_sale_salary_level(self, level_id, **kw):
        """Update an existing Sale Salary Level."""
        try:
            rec = request.env['hb.sale.salary.level'].sudo().browse(level_id)
            if not rec.exists():
                return _error_response('Không tìm thấy Level.', status=404)
            data = _get_json_body()
            vals = {}
            if 'levelCode' in data: vals['level_code'] = data['levelCode']
            if 'name' in data: vals['name'] = data['name']
            if 'sequence' in data: vals['sequence'] = int(data['sequence'])
            if 'kpiTarget' in data: vals['kpi_target'] = float(data['kpiTarget'])
            if 'baseWage' in data: vals['base_wage'] = float(data['baseWage'])
            rec.write(vals)
            return _success_response({'id': rec.id}, message='Đã cập nhật Level thành công.')
        except Exception as e:
            _logger.exception('update_sale_salary_level error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/sale-salary-level/<int:level_id>/delete', type='http',
                auth='user', methods=['POST', 'DELETE'], csrf=False)
    def delete_sale_salary_level(self, level_id, **kw):
        """Delete / archive a Sale Salary Level."""
        try:
            rec = request.env['hb.sale.salary.level'].sudo().browse(level_id)
            if not rec.exists():
                return _error_response('Không tìm thấy Level.', status=404)
            rec.unlink()
            return _success_response({}, message='Đã xóa Level thành công.')
        except Exception as e:
            _logger.exception('delete_sale_salary_level error')
            return _error_response(str(e), status=500)

    # ── ROLE ALLOWANCE CONFIG API ───────────────────────────────────────────
    @http.route('/hocba-hrm/api/payroll/role-allowance-config', type='http',
                auth='user', methods=['GET'], csrf=False)
    def get_role_allowance_configs(self, **kw):
        """Get all Role & Department Allowance Configurations."""
        try:
            recs = request.env['hb.role.allowance.config'].sudo().search([('active', '=', True)], order='id desc')
            res = []
            for r in recs:
                j_ids = r.job_ids.ids if r.job_ids else ([r.job_id.id] if r.job_id else [])
                d_ids = r.department_ids.ids if r.department_ids else ([r.department_id.id] if r.department_id else [])
                j_name = ', '.join(r.job_ids.mapped('name')) if r.job_ids else (r.job_id.name if r.job_id else 'Tất cả chức vụ')
                d_name = ', '.join(r.department_ids.mapped('name')) if r.department_ids else (r.department_id.name if r.department_id else 'Tất cả phòng ban')
                res.append({
                    'id': r.id,
                    'name': r.name,
                    'jobId': r.job_id.id if r.job_id else None,
                    'jobIds': j_ids,
                    'jobName': j_name,
                    'departmentId': r.department_id.id if r.department_id else None,
                    'departmentIds': d_ids,
                    'departmentName': d_name,
                    'allowanceType': r.allowance_type,
                    'amount': r.amount,
                    'notes': r.notes or '',
                })
            return _success_response(res)
        except Exception as e:
            _logger.exception('get_role_allowance_configs error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/role-allowance-config', type='http',
                auth='user', methods=['POST'], csrf=False)
    def create_role_allowance_config(self, **kw):
        """Create or Update a Role & Department Allowance Config."""
        try:
            data = _get_json_body()
            cfg_id = data.get('id')
            raw_jids = data.get('jobIds') or ([data.get('jobId')] if data.get('jobId') else [])
            raw_dids = data.get('departmentIds') or ([data.get('departmentId')] if data.get('departmentId') else [])
            jids = [int(x) for x in raw_jids if x]
            dids = [int(x) for x in raw_dids if x]

            vals = {
                'name': data.get('name', 'Phụ cấp chức vụ'),
                'job_id': jids[0] if len(jids) == 1 else False,
                'department_id': dids[0] if len(dids) == 1 else False,
                'job_ids': [(6, 0, jids)],
                'department_ids': [(6, 0, dids)],
                'allowance_type': data.get('allowanceType', 'position_allowance'),
                'amount': float(data.get('amount', 0.0)),
                'notes': data.get('notes', ''),
            }
            if cfg_id:
                rec = request.env['hb.role.allowance.config'].sudo().browse(cfg_id)
                if rec.exists():
                    rec.write(vals)
                else:
                    rec = request.env['hb.role.allowance.config'].sudo().create(vals)
            else:
                rec = request.env['hb.role.allowance.config'].sudo().create(vals)
            return _success_response({'id': rec.id}, message='Đã lưu cấu hình thưởng/phụ cấp thành công.')
        except Exception as e:
            _logger.exception('create_role_allowance_config error')
            return _error_response(str(e), status=500)

    @http.route('/hocba-hrm/api/payroll/role-allowance-config/<int:cfg_id>/delete', type='http',
                auth='user', methods=['POST', 'DELETE'], csrf=False)
    def delete_role_allowance_config(self, cfg_id, **kw):
        """Delete a Role & Department Allowance Config."""
        try:
            rec = request.env['hb.role.allowance.config'].sudo().browse(cfg_id)
            if not rec.exists():
                return _error_response('Không tìm thấy cấu hình.', status=404)
            rec.unlink()
            return _success_response({}, message='Đã xóa cấu hình thành công.')
        except Exception as e:
            _logger.exception('delete_role_allowance_config error')
            return _error_response(str(e), status=500)

    # ── BULK BONUS & PENALTY WIZARD API ─────────────────────────────────────
    @http.route('/hocba-hrm/api/payroll/batch/<int:batch_id>/bulk-bonus-penalty', type='http',
                auth='user', methods=['POST'], csrf=False)
    def apply_bulk_bonus_penalty(self, batch_id, **kw):
        """Apply dynamic bonus and/or penalty to multiple payslips in a batch."""
        try:
            data = _get_json_body()
            payslip_ids = data.get('payslip_ids') or data.get('payslipIds') or []
            bonus_amount = float(data.get('bonusAmount', 0.0))
            bonus_reason = data.get('bonusReason', '')
            penalty_amount = float(data.get('penaltyAmount', 0.0))
            penalty_reason = data.get('penaltyReason', '')

            PayslipModel = request.env['hb.payslip'].sudo()

            if payslip_ids:
                slips = PayslipModel.browse(payslip_ids)
            else:
                slips = PayslipModel.search([('payslip_run_id', '=', batch_id)])

            if not slips:
                return _error_response('Không tìm thấy phiếu lương phù hợp.')

            vals = {}
            if bonus_amount >= 0:
                vals['x_bonus_extra'] = bonus_amount
                if bonus_reason:
                    vals['x_bonus_reason'] = bonus_reason
            if penalty_amount >= 0:
                vals['x_penalty_amount'] = penalty_amount
                if penalty_reason:
                    vals['x_penalty_reason'] = penalty_reason

            if vals:
                slips.write(vals)

            # Recompute payslips to update NET/GROSS amounts
            slips.action_compute_batch()

            return _success_response({
                'updatedCount': len(slips),
            }, message=f'🎉 Đã áp dụng thưởng/phạt thành công cho {len(slips)} nhân viên!')
        except Exception as e:
            _logger.exception('apply_bulk_bonus_penalty error')
            return _error_response(str(e), status=500)

