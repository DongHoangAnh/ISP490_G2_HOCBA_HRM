"""
Payroll REST API Controllers.
Full-flow endpoints for payroll management (test & FE integration).

Endpoints:
    ── Payslip Batch ──────────────────────────────
    POST   /api/payroll/batch                  Create batch
    GET    /api/payroll/batch                  List batches
    GET    /api/payroll/batch/<id>             Get batch detail
    POST   /api/payroll/batch/<id>/generate    Generate payslips for batch
    POST   /api/payroll/batch/<id>/close       Mark batch as done

    ── Payslip ────────────────────────────────────
    GET    /api/payroll/payslip                List payslips
    GET    /api/payroll/payslip/<id>           Get payslip detail
    POST   /api/payroll/payslip/<id>/compute   Compute teaching salary
    POST   /api/payroll/payslip/<id>/confirm   Confirm payslip
    POST   /api/payroll/payslip/<id>/reset     Reset to draft

    ── Work Entry ─────────────────────────────────
    POST   /api/payroll/work-entry             Create work entry
    GET    /api/payroll/work-entry             List work entries
    POST   /api/payroll/work-entry/<id>/validate  Validate work entry
    POST   /api/payroll/work-entry/bulk-create    Bulk create work entries

    ── Bank File ──────────────────────────────────
    POST   /api/payroll/bank-file/generate     Generate bank file
    GET    /api/payroll/bank-file              List bank files
    POST   /api/payroll/bank-file/<id>/upload  Mark as uploaded
    POST   /api/payroll/bank-file/<id>/confirm Mark as confirmed

    ── BHXH Report ────────────────────────────────
    POST   /api/payroll/bhxh                   Create BHXH report
    GET    /api/payroll/bhxh                   List BHXH reports
    GET    /api/payroll/bhxh/<id>              Get BHXH detail
    POST   /api/payroll/bhxh/<id>/compute      Compute BHXH
    POST   /api/payroll/bhxh/<id>/submit       Mark submitted

    ── eTax Report ────────────────────────────────
    POST   /api/payroll/etax                   Create eTax report
    GET    /api/payroll/etax                   List eTax reports
    GET    /api/payroll/etax/<id>              Get eTax detail
    POST   /api/payroll/etax/<id>/compute      Compute eTax
    POST   /api/payroll/etax/<id>/submit       Mark submitted

    ── Config ─────────────────────────────────────
    GET    /api/payroll/bank-format             List bank formats
    GET    /api/payroll/contract/<id>/teaching  Get contract teaching config
    PUT    /api/payroll/contract/<id>/teaching  Update contract teaching config
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
    @http.route('/api/payroll/batch', type='http', auth='user',
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

    @http.route('/api/payroll/batch', type='http', auth='user',
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

    @http.route('/api/payroll/batch/<int:batch_id>', type='http', auth='user',
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
                'teaching_total_hours': s.x_teaching_total_hours,
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

    @http.route('/api/payroll/batch/<int:batch_id>/generate', type='http',
                auth='user', methods=['POST'], csrf=False)
    def generate_payslips(self, batch_id, **kw):
        try:
            batch = request.env['hb.payslip.run'].sudo().browse(batch_id)
            if not batch.exists():
                return _error_response('Batch not found.', status=404)

            employees = request.env['hr.employee'].sudo().search([
                ('active', '=', True),
                ('contract_ids.state', '=', 'open'),
            ])
            created = 0
            skipped = []
            for emp in employees:
                contract = emp.contract_ids.filtered(
                    lambda c: c.state == 'open'
                              and c.date_start <= batch.date_end
                              and (not c.date_end or c.date_end >= batch.date_start)
                )[:1]
                if not contract:
                    skipped.append(emp.name)
                    continue
                request.env['hb.payslip'].sudo().create({
                    'employee_id': emp.id,
                    'contract_id': contract.id,
                    'date_from': batch.date_start,
                    'date_to': batch.date_end,
                    'payslip_run_id': batch.id,
                })
                created += 1
            return _success_response({
                'created': created, 'skipped': skipped,
            }, message=f'{created} payslips generated.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('generate_payslips error')
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/batch/<int:batch_id>/close', type='http',
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

    # ═════════════════════════════════════════════════════════
    # PAYSLIP
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/payslip', type='http', auth='user',
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
            payslips = request.env['hb.payslip'].sudo().search(
                domain, order='number', limit=int(kw.get('limit', 100)),
            )
            return _success_response([s._to_api_dict() for s in payslips])
        except Exception as e:
            _logger.exception('list_payslips error')
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/payslip/<int:slip_id>', type='http', auth='user',
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

    @http.route('/api/payroll/payslip/<int:slip_id>/compute', type='http',
                auth='user', methods=['POST'], csrf=False)
    def compute_payslip(self, slip_id, **kw):
        try:
            slip = request.env['hb.payslip'].sudo().browse(slip_id)
            if not slip.exists():
                return _error_response('Payslip not found.', status=404)
            slip.action_compute_teaching_salary()
            return _success_response(slip._to_api_dict(), message='Payslip computed successfully.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('compute_payslip error')
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/payslip/<int:slip_id>/confirm', type='http',
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

    @http.route('/api/payroll/payslip/<int:slip_id>/reset', type='http',
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
    # WORK ENTRY
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/work-entry', type='http', auth='user',
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

    @http.route('/api/payroll/work-entry', type='http', auth='user',
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

    @http.route('/api/payroll/work-entry/<int:entry_id>/validate', type='http',
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

    @http.route('/api/payroll/work-entry/bulk-create', type='http', auth='user',
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
    # BANK FILE
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/bank-file/generate', type='http', auth='user',
                methods=['POST'], csrf=False)
    def generate_bank_file(self, **kw):
        try:
            body = _get_json_body()
            for f in ('batch_id', 'bank_format_id', 'payment_date'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            wiz = request.env['hb.bank.file.wizard'].sudo().create({
                'payslip_batch_id': int(body['batch_id']),
                'bank_format_id': int(body['bank_format_id']),
                'company_bank_id': int(body.get('company_bank_id', 0)) or False,
                'payment_date': body['payment_date'],
                'description': body.get('description', 'Luong T{month}/{year}'),
            })
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

    @http.route('/api/payroll/bank-file', type='http', auth='user',
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

    @http.route('/api/payroll/bank-file/<int:file_id>/upload', type='http',
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

    @http.route('/api/payroll/bank-file/<int:file_id>/confirm', type='http',
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
    # BHXH REPORT
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/bhxh', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_bhxh_report(self, **kw):
        try:
            body = _get_json_body()
            for f in ('period_month', 'period_year', 'batch_id'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            report = request.env['hb.bhxh.report'].sudo().create({
                'period_month': str(body['period_month']),
                'period_year': str(body['period_year']),
                'batch_id': int(body['batch_id']),
            })
            return _success_response(report._to_api_dict(), message='BHXH report created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_bhxh error')
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/bhxh', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_bhxh_reports(self, **kw):
        try:
            reports = request.env['hb.bhxh.report'].sudo().search(
                [], order='period_year desc, period_month desc',
                limit=int(kw.get('limit', 50)),
            )
            return _success_response([r._to_api_dict() for r in reports])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/bhxh/<int:report_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_bhxh_report(self, report_id, **kw):
        try:
            report = request.env['hb.bhxh.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('BHXH report not found.', status=404)
            return _success_response(report._to_api_dict())
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/bhxh/<int:report_id>/compute', type='http',
                auth='user', methods=['POST'], csrf=False)
    def compute_bhxh(self, report_id, **kw):
        try:
            report = request.env['hb.bhxh.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('BHXH report not found.', status=404)
            report.action_compute()
            return _success_response(report._to_api_dict(), message='BHXH report computed.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/bhxh/<int:report_id>/submit', type='http',
                auth='user', methods=['POST'], csrf=False)
    def submit_bhxh(self, report_id, **kw):
        try:
            report = request.env['hb.bhxh.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('BHXH report not found.', status=404)
            report.action_mark_submitted()
            return _success_response({'state': report.state})
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # ETAX REPORT
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/etax', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_etax_report(self, **kw):
        try:
            body = _get_json_body()
            for f in ('period_month', 'period_year', 'batch_id'):
                if f not in body:
                    return _error_response(f'Missing required field: {f}')
            report = request.env['hb.etax.report'].sudo().create({
                'period_month': str(body['period_month']),
                'period_year': str(body['period_year']),
                'batch_id': int(body['batch_id']),
            })
            return _success_response(report._to_api_dict(), message='eTax report created.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            _logger.exception('create_etax error')
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/etax', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_etax_reports(self, **kw):
        try:
            reports = request.env['hb.etax.report'].sudo().search(
                [], order='period_year desc, period_month desc',
                limit=int(kw.get('limit', 50)),
            )
            return _success_response([r._to_api_dict() for r in reports])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/etax/<int:report_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_etax_report(self, report_id, **kw):
        try:
            report = request.env['hb.etax.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('eTax report not found.', status=404)
            return _success_response(report._to_api_dict())
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/etax/<int:report_id>/compute', type='http',
                auth='user', methods=['POST'], csrf=False)
    def compute_etax(self, report_id, **kw):
        try:
            report = request.env['hb.etax.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('eTax report not found.', status=404)
            report.action_compute()
            return _success_response(report._to_api_dict(), message='eTax report computed.')
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/etax/<int:report_id>/submit', type='http',
                auth='user', methods=['POST'], csrf=False)
    def submit_etax(self, report_id, **kw):
        try:
            report = request.env['hb.etax.report'].sudo().browse(report_id)
            if not report.exists():
                return _error_response('eTax report not found.', status=404)
            report.action_mark_submitted()
            return _success_response({'state': report.state})
        except (ValidationError, UserError) as e:
            return _error_response(str(e))
        except Exception as e:
            return _error_response(str(e), status=500)

    # ═════════════════════════════════════════════════════════
    # CONFIG
    # ═════════════════════════════════════════════════════════
    @http.route('/api/payroll/bank-format', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_bank_formats(self, **kw):
        try:
            formats = request.env['hb.bank.format'].sudo().search([('active', '=', True)])
            return _success_response([{
                'id': f.id, 'name': f.name, 'code': f.code,
                'file_extension': f.file_extension,
            } for f in formats])
        except Exception as e:
            return _error_response(str(e), status=500)

    @http.route('/api/payroll/contract/<int:contract_id>/teaching', type='http',
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

    @http.route('/api/payroll/contract/<int:contract_id>/teaching', type='http',
                auth='user', methods=['PUT'], csrf=False)
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
