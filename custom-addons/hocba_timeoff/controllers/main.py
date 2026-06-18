# ============================================================
# JSON API cho SPA — domain Nghỉ phép (timeoff). Owner: Nhật Anh.
# Spec: docs/SPEC_API_TIMEOFF.md · Quy ước: docs/QUY_UOC_FRONTEND.md
#
# Dùng chung prefix /hocba-hrm/api/timeoff/* nhưng đặt trong module
# hocba_timeoff (mỗi domain tự quản controller của mình). Mọi thao tác GHI
# gọi KHÔNG sudo để ràng buộc của model hr.leave là nguồn chân lý về quyền
# (BR-011 chứng từ y tế, BR-031 ghi chú thay thế, quyền duyệt...).
# ============================================================
import base64
import binascii

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

# Chứng từ y tế (BR-012): chỉ chấp nhận PDF / JPG / PNG, tối đa 5MB.
ALLOWED_MIME = frozenset({'application/pdf', 'image/jpeg', 'image/png'})
MAX_SIZE_BYTES = 5 * 1024 * 1024

# Palette hex tương ứng color index 0..11 của Odoo (cho leave type / lịch).
COLOR_PALETTE = [
    '#6b7280', '#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981',
    '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e', '#78716c',
]


def _lt_color(leave_type):
    return COLOR_PALETTE[(leave_type.color or 0) % len(COLOR_PALETTE)]

STATE_LABEL = {
    'confirm': 'Chờ duyệt',
    'validate1': 'Chờ duyệt (cấp 2)',
    'validate': 'Đã duyệt',
    'refuse': 'Từ chối',
    'cancel': 'Đã hủy',
}
STATE_KIND = {
    'confirm': 'amber',
    'validate1': 'blue',
    'validate': 'green',
    'refuse': 'red',
    'cancel': 'gray',
}
# Trạng thái còn xử lý được (hủy / nằm trong danh sách chờ duyệt).
PENDING_STATES = ('confirm', 'validate1')


def _d(v):
    """date/datetime → ISO string (None-safe)."""
    return v.isoformat() if v else None


def _balance_kind(remaining):
    if remaining <= 0:
        return 'red'
    if remaining <= 2:
        return 'amber'
    return 'teal'


class HocBaTimeoff(http.Controller):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _flags(self):
        user = request.env.user
        return (user.has_group('hr_holidays.group_hr_holidays_user'),
                user.has_group('hr_holidays.group_hr_holidays_manager'))

    def _emp_type_label(self, employee):
        if not employee.x_hb_leave_emp_type:
            return ''
        sel = dict(employee._fields['x_hb_leave_emp_type']
                   ._description_selection(request.env))
        return sel.get(employee.x_hb_leave_emp_type, '')

    def _balances(self, employee):
        """Số dư phép theo từng loại nghỉ (chỉ loại có phân bổ hoặc đã dùng)."""
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=employee.id).search([]))
        rows = []
        for lt in types:
            if not lt.requires_allocation:
                continue
            if lt.max_leaves <= 0 and lt.leaves_taken <= 0:
                continue
            remaining = lt.virtual_remaining_leaves
            rows.append({
                'leaveTypeId': lt.id,
                'leaveType': lt.name,
                'allocated': round(lt.max_leaves, 2),
                'taken': round(lt.leaves_taken, 2),
                'remaining': round(remaining, 2),
                'requiresAllocation': lt.requires_allocation,
                'kind': _balance_kind(remaining),
            })
        return rows

    def _leave_types(self, employee):
        """Loại nghỉ employee được phép chọn khi tạo đơn (theo domain hr.leave)."""
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=employee.id).search([
                     '|', ('requires_allocation', '=', False),
                          ('has_valid_allocation', '=', True),
                 ]))
        return [{
            'id': lt.id,
            'name': lt.name,
            'requiresAllocation': lt.requires_allocation,
            'isEmergency': lt.x_is_emergency_type,
            'supportDocument': lt.support_document,
            'requestUnit': lt.request_unit,
        } for lt in types]

    def _my_request(self, leave):
        return {
            'id': leave.id,
            'leaveTypeId': leave.holiday_status_id.id,
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'days': round(leave.number_of_days, 2),
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'stateKind': STATE_KIND.get(leave.state, 'gray'),
            'reason': leave.name or '',
            'isEmergency': leave.x_is_emergency,
            'scheduleConflict': leave.x_schedule_conflict,
            'supportDocument': leave.holiday_status_id.support_document,
            'hasMedicalDoc': leave.x_has_medical_doc,
            'canCancel': leave.state in PENDING_STATES,
        }

    def _approval_request(self, leave):
        return {
            'id': leave.id,
            'employeeId': leave.employee_id.id,
            'employee': leave.employee_id.name,
            'department': leave.department_id.name or leave.employee_id.department_id.name or '—',
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'days': round(leave.number_of_days, 2),
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'stateKind': STATE_KIND.get(leave.state, 'gray'),
            'reason': leave.name or '',
            'isEmergency': leave.x_is_emergency,
            'scheduleConflict': leave.x_schedule_conflict,
            'conflictInfo': leave.x_conflict_info or '',
            'academicReviewRequired': leave.x_academic_review_required,
            'replacementNote': leave.x_replacement_note or '',
            'supportDocument': leave.holiday_status_id.support_document,
            'hasMedicalDoc': leave.x_has_medical_doc,
        }

    def _overview_payload(self):
        is_officer, is_manager = self._flags()
        emp = request.env.user.employee_id
        if not emp:
            return {'isOfficer': is_officer, 'isManager': is_manager,
                    'employee': None, 'balances': [], 'leaveTypes': [],
                    'requests': []}
        leaves = (request.env['hr.leave'].sudo()
                  .search([('employee_id', '=', emp.id)],
                          order='request_date_from desc, id desc'))
        return {
            'isOfficer': is_officer,
            'isManager': is_manager,
            'employee': {
                'id': emp.id,
                'name': emp.name,
                'empTypeKey': emp.x_hb_leave_emp_type or '',
                'empType': self._emp_type_label(emp),
            },
            'balances': self._balances(emp),
            'leaveTypes': self._leave_types(emp),
            'requests': [self._my_request(l) for l in leaves],
        }

    # ------------------------------------------------------------------
    # 3.1. GET /overview — tab "Của tôi"
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/overview', auth='user',
                type='http', methods=['GET'])
    def api_overview(self, **kw):
        return request.make_json_response(self._overview_payload())

    # ------------------------------------------------------------------
    # 3.2. GET /approvals — tab "Chờ duyệt" (officer)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/approvals', auth='user',
                type='http', methods=['GET'])
    def api_approvals(self, **kw):
        is_officer, is_manager = self._flags()
        if not is_officer:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        # KHÔNG sudo: record rule của hr.leave giới hạn đúng phạm vi officer duyệt.
        leaves = request.env['hr.leave'].search(
            [('state', 'in', list(PENDING_STATES))],
            order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            'isOfficer': is_officer,
            'isManager': is_manager,
            'requests': [self._approval_request(l) for l in leaves],
        })

    # ------------------------------------------------------------------
    # 3.3. POST /request — tạo đơn nghỉ cho chính mình
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_create(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)

        payload = request.get_json_data()
        leave_type_id = payload.get('leaveTypeId')
        date_from = (payload.get('dateFrom') or '').strip()
        date_to = (payload.get('dateTo') or '').strip()
        reason = (payload.get('reason') or '').strip()
        att = payload.get('attachment')

        if not leave_type_id or not date_from or not date_to:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        if date_to < date_from:
            return request.make_json_response({'error': 'bad_range'}, status=400)

        leave_type = request.env['hr.leave.type'].sudo().browse(int(leave_type_id))
        if not leave_type.exists():
            return request.make_json_response(
                {'error': 'leave_type_not_found'}, status=404)

        # Kiểm tra chứng từ ở controller (defense); model re-validate ở bước duyệt.
        att_vals = None
        if att and att.get('data'):
            mimetype = att.get('mimetype') or ''
            if mimetype not in ALLOWED_MIME:
                return request.make_json_response(
                    {'error': 'bad_file_type'}, status=400)
            try:
                raw = base64.b64decode(att['data'], validate=True)
            except (binascii.Error, ValueError):
                return request.make_json_response(
                    {'error': 'bad_file'}, status=400)
            if len(raw) > MAX_SIZE_BYTES:
                return request.make_json_response(
                    {'error': 'file_too_large'}, status=400)
            att_vals = {
                'name': att.get('filename') or 'chung-tu',
                'datas': att['data'],
                'mimetype': mimetype,
                'res_model': 'hr.leave',
            }

        vals = {
            'holiday_status_id': leave_type.id,
            'employee_id': emp.id,
            'request_date_from': date_from,
            'request_date_to': date_to,
        }
        if reason:
            vals['name'] = reason

        # KHÔNG sudo: model áp domain employee + quyền tạo của user.
        try:
            leave = request.env['hr.leave'].create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)

        if att_vals:
            att_vals['res_id'] = leave.id
            request.env['ir.attachment'].sudo().create(att_vals)
            leave.invalidate_recordset(['attachment_ids', 'x_has_medical_doc'])

        return request.make_json_response(self._overview_payload())

    # ------------------------------------------------------------------
    # 3.4. POST /request/<id>/cancel — chủ đơn hủy đơn chờ duyệt
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request/<int:leave_id>/cancel',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_request_cancel(self, leave_id, **kw):
        emp = request.env.user.employee_id
        leave = request.env['hr.leave'].sudo().browse(leave_id)
        if not leave.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not emp or leave.employee_id.id != emp.id:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        # Chỉ rút được đơn còn chờ duyệt. (Đơn đã duyệt phải qua wizard hủy
        # của Odoo — ngoài phạm vi self-service ở SPA.)
        if leave.state not in PENDING_STATES:
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Chỉ rút được đơn đang chờ duyệt.'}, status=403)
        # Rút đơn = unlink (không sudo) để model áp đủ ràng buộc/quyền của chủ đơn.
        # Lưu ý: hr.leave.action_cancel() chỉ mở wizard, không hủy trực tiếp.
        try:
            request.env['hr.leave'].browse(leave_id).unlink()
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)
        return request.make_json_response(self._overview_payload())

    # ------------------------------------------------------------------
    # 3.5. POST /request/<id>/decision — duyệt / từ chối (officer)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request/<int:leave_id>/decision',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_request_decision(self, leave_id, **kw):
        payload = request.get_json_data()
        action = payload.get('action')
        if action not in ('approve', 'refuse'):
            return request.make_json_response({'error': 'bad_request'}, status=400)

        # KHÔNG sudo: quyền duyệt do model hr.leave quyết định.
        leave = request.env['hr.leave'].browse(leave_id)
        if not leave.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)

        try:
            if action == 'refuse':
                leave.action_refuse()
            else:
                # Ghi ghi-chú thay thế / override chứng từ trước khi duyệt.
                write_vals = {}
                note = (payload.get('replacementNote') or '').strip()
                if note:
                    write_vals['x_replacement_note'] = note
                if payload.get('medicalOverride'):
                    write_vals['x_medical_override'] = True
                    write_vals['x_medical_override_reason'] = (
                        payload.get('medicalOverrideReason') or '').strip()
                if write_vals:
                    leave.write(write_vals)
                leave.action_approve()
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)

        # Trả lại danh sách chờ duyệt đã refresh.
        is_officer, is_manager = self._flags()
        leaves = request.env['hr.leave'].search(
            [('state', 'in', list(PENDING_STATES))],
            order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            'isOfficer': is_officer,
            'isManager': is_manager,
            'requests': [self._approval_request(l) for l in leaves],
        })

    # ------------------------------------------------------------------
    # Helpers cho Dashboard + Lịch
    # ------------------------------------------------------------------
    def _this_year(self):
        return fields.Date.context_today(request.env.user).year

    def _year_bounds(self, year):
        return ('%d-01-01 00:00:00' % year, '%d-12-31 23:59:59' % year)

    # ------------------------------------------------------------------
    # 3.6. GET /dashboard — tổng quan (Manager hoặc Nhân viên theo quyền)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/dashboard', auth='user',
                type='http', methods=['GET'])
    def api_dashboard(self, **kw):
        is_officer, is_manager = self._flags()
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        if is_manager:
            data = self._dashboard_manager(year, kw.get('dept'))
        else:
            data = self._dashboard_employee(year)
        data.update({'isOfficer': is_officer, 'isManager': is_manager, 'year': year})
        return request.make_json_response(data)

    def _dashboard_manager(self, year, dept_raw):
        Leave = request.env['hr.leave']  # không sudo: record rule giới hạn đúng quyền
        start, end = self._year_bounds(year)
        try:
            dept_id = int(dept_raw) if dept_raw else False
        except (TypeError, ValueError):
            dept_id = False
        dept_dom = [('department_id', '=', dept_id)] if dept_id else []
        year_dom = [('date_from', '>=', start), ('date_from', '<=', end)]
        approved_dom = [('state', '=', 'validate')] + year_dom + dept_dom
        pending_dom = [('state', 'in', list(PENDING_STATES))] + dept_dom
        today = fields.Date.context_today(request.env.user).isoformat()

        approved_days = sum(
            r[0] for r in Leave._read_group(approved_dom, [], ['number_of_days:sum']))
        kpi = {
            'total': Leave.search_count(year_dom + dept_dom),
            'pending': Leave.search_count(pending_dom),
            'approved': Leave.search_count(approved_dom),
            'approvedDays': round(approved_days, 1),
            'onLeaveToday': Leave.search_count([
                ('state', '=', 'validate'),
                ('date_from', '<=', '%s 23:59:59' % today),
                ('date_to', '>=', '%s 00:00:00' % today)] + dept_dom),
        }

        def _bars(groups, get_id, get_name):
            rows = []
            for g in groups:
                rec, days, count = g[0], g[1], g[2]
                if days <= 0:
                    continue
                rows.append({'id': get_id(rec), 'name': get_name(rec),
                             'days': round(days, 1), 'count': count})
            rows.sort(key=lambda r: r['days'], reverse=True)
            mx = max([r['days'] for r in rows] + [1])
            for i, r in enumerate(rows):
                r['pct'] = round(r['days'] / mx * 100)
                r['color'] = COLOR_PALETTE[(i % (len(COLOR_PALETTE) - 1)) + 1]
            return rows

        by_type = _bars(
            Leave._read_group(approved_dom, ['holiday_status_id'],
                              ['number_of_days:sum', '__count']),
            lambda r: r.id or False, lambda r: r.name or 'Không xác định')
        by_dept = _bars(
            Leave._read_group(approved_dom, ['department_id'],
                              ['number_of_days:sum', '__count']),
            lambda r: r.id or False, lambda r: r.name or 'Chưa có phòng ban')
        top_emp = _bars(
            Leave._read_group(approved_dom, ['employee_id'],
                              ['number_of_days:sum', '__count']),
            lambda r: r.id or False, lambda r: r.name or 'Không xác định')[:5]

        pending = Leave.search(pending_dom, limit=10, order='create_date desc')
        return {
            'kpi': kpi,
            'byType': by_type,
            'byDept': by_dept,
            'topEmployees': top_emp,
            'pending': [{
                'id': l.id,
                'employee': l.employee_id.name,
                'department': l.department_id.name or '—',
                'leaveType': l.holiday_status_id.name,
                'from': _d(l.request_date_from),
                'to': _d(l.request_date_to),
                'days': round(l.number_of_days, 2),
                'isEmergency': l.x_is_emergency,
            } for l in pending],
            'departments': [{'id': d.id, 'name': d.name}
                            for d in request.env['hr.department'].search([], order='name')],
        }

    def _dashboard_employee(self, year):
        emp = request.env.user.employee_id
        if not emp:
            return {'empMissing': True, 'employee': None, 'balances': [],
                    'totalRemaining': 0,
                    'empKpi': {'pending': 0, 'approved': 0, 'approvedDays': 0},
                    'myRequests': [], 'upcoming': []}
        start, end = self._year_bounds(year)
        Leave = request.env['hr.leave'].sudo()
        emp_dom = [('employee_id', '=', emp.id)]
        approved_year = emp_dom + [('state', '=', 'validate'),
                                   ('date_from', '>=', start), ('date_from', '<=', end)]
        today = fields.Date.context_today(request.env.user).isoformat()

        # Số dư theo loại nghỉ (chỉ loại có hoạt động)
        balances = []
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=emp.id).search([('requires_allocation', '=', True)]))
        for lt in types:
            if lt.max_leaves <= 0 and lt.leaves_taken <= 0:
                continue
            remaining = lt.virtual_remaining_leaves
            allocated = lt.max_leaves
            balances.append({
                'id': lt.id, 'name': lt.name,
                'allocated': round(allocated, 2),
                'taken': round(lt.leaves_taken, 2),
                'remaining': round(remaining, 2),
                'pct': round(min(100, lt.leaves_taken / allocated * 100)) if allocated > 0 else 0,
                'low': allocated > 0 and remaining <= 2,
                'color': _lt_color(lt),
            })

        approved_days = sum(
            r[0] for r in Leave._read_group(approved_year, [], ['number_of_days:sum']))
        my = Leave.search(emp_dom, limit=10, order='create_date desc')
        upcoming = Leave.search(
            emp_dom + [('state', '=', 'validate'), ('date_to', '>=', '%s 00:00:00' % today)],
            limit=5, order='date_from')
        return {
            'empMissing': False,
            'employee': {'id': emp.id, 'name': emp.name},
            'balances': balances,
            'totalRemaining': round(sum(b['remaining'] for b in balances), 1),
            'empKpi': {
                'pending': Leave.search_count(emp_dom + [('state', 'in', list(PENDING_STATES))]),
                'approved': Leave.search_count(approved_year),
                'approvedDays': round(approved_days, 1),
            },
            'myRequests': [{
                'id': l.id, 'leaveType': l.holiday_status_id.name,
                'from': _d(l.request_date_from), 'to': _d(l.request_date_to),
                'days': round(l.number_of_days, 2),
                'state': l.state, 'stateLabel': STATE_LABEL.get(l.state, l.state),
                'stateKind': STATE_KIND.get(l.state, 'gray'),
            } for l in my],
            'upcoming': [{
                'id': l.id, 'leaveType': l.holiday_status_id.name,
                'from': _d(l.request_date_from), 'to': _d(l.request_date_to),
                'days': round(l.number_of_days, 2),
            } for l in upcoming],
        }

    # ------------------------------------------------------------------
    # 3.7. GET /calendar — lịch nghỉ (năm/tháng), legend + ngày bắt buộc
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/calendar', auth='user',
                type='http', methods=['GET'])
    def api_calendar(self, **kw):
        is_officer, is_manager = self._flags()
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        # scope='all' chỉ cho officer; mặc định xem lịch của chính mình.
        scope = kw.get('scope') if kw.get('scope') in ('me', 'all') else 'me'
        if scope == 'all' and not is_officer:
            scope = 'me'

        start, end = self._year_bounds(year)
        overlap = [('date_from', '<=', end), ('date_to', '>=', start)]
        if scope == 'all':
            Leave = request.env['hr.leave']  # record rule giới hạn phạm vi officer
            domain = overlap
        else:
            emp = request.env.user.employee_id
            Leave = request.env['hr.leave'].sudo()
            domain = ([('employee_id', '=', emp.id)] + overlap) if emp else [('id', '=', 0)]

        leaves = Leave.search(domain, order='date_from')
        rows, types = [], {}
        for l in leaves:
            lt = l.holiday_status_id
            types[lt.id] = {'id': lt.id, 'name': lt.name, 'color': _lt_color(lt)}
            rows.append({
                'id': l.id,
                'employee': l.employee_id.name,
                'leaveTypeId': lt.id,
                'leaveType': lt.name,
                'color': _lt_color(lt),
                'from': _d(l.request_date_from or (l.date_from and l.date_from.date())),
                'to': _d(l.request_date_to or (l.date_to and l.date_to.date())),
                'state': l.state,
                'stateKind': STATE_KIND.get(l.state, 'gray'),
                'isEmergency': l.x_is_emergency,
            })

        mandatory = request.env['hr.leave.mandatory.day'].sudo().search([
            ('start_date', '<=', '%d-12-31' % year),
            ('end_date', '>=', '%d-01-01' % year),
        ], order='start_date')
        # Khử trùng lặp (DB hiện có nhiều mandatory day giống nhau).
        seen, mdays = set(), []
        for m in mandatory:
            key = (m.name, str(m.start_date), str(m.end_date))
            if key in seen:
                continue
            seen.add(key)
            mdays.append({'name': m.name, 'from': _d(m.start_date), 'to': _d(m.end_date),
                          'color': COLOR_PALETTE[(m.color or 1) % len(COLOR_PALETTE)]})

        return request.make_json_response({
            'isOfficer': is_officer,
            'isManager': is_manager,
            'year': year,
            'scope': scope,
            'leaveTypes': sorted(types.values(), key=lambda t: t['name']),
            'leaves': rows,
            'mandatoryDays': mdays,
        })

    # ------------------------------------------------------------------
    # 3.8. GET /summary — tổng hợp đơn nghỉ (mọi trạng thái) theo phòng ban
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/summary', auth='user',
                type='http', methods=['GET'])
    def api_summary(self, **kw):
        is_officer, is_manager = self._flags()
        if not is_officer:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False

        start, end = self._year_bounds(year)
        # KHÔNG sudo: record rule giới hạn đúng phạm vi officer được xem.
        Leave = request.env['hr.leave']
        domain = [('date_from', '>=', start), ('date_from', '<=', end)]
        if dept_id:
            domain.append(('department_id', '=', dept_id))
        leaves = Leave.search(domain, order='date_from desc, id desc')

        # --- Tổng quan ---
        by_state = {k: 0 for k in STATE_LABEL}
        approved_days = 0.0
        type_acc = {}  # id -> {name, color, count}
        depts = {}     # id -> dept bucket
        for l in leaves:
            by_state[l.state] = by_state.get(l.state, 0) + 1
            if l.state == 'validate':
                approved_days += l.number_of_days
            lt = l.holiday_status_id
            t = type_acc.setdefault(lt.id, {'id': lt.id, 'name': lt.name,
                                            'color': _lt_color(lt), 'count': 0})
            t['count'] += 1

            dep = l.department_id or l.employee_id.department_id
            dep_id = dep.id or 0
            bucket = depts.setdefault(dep_id, {
                'id': dep.id or False, 'name': dep.name or 'Chưa có phòng ban',
                'total': 0, 'pending': 0, 'approved': 0, 'days': 0.0, 'requests': []})
            bucket['total'] += 1
            if l.state in PENDING_STATES:
                bucket['pending'] += 1
            elif l.state == 'validate':
                bucket['approved'] += 1
                bucket['days'] += l.number_of_days
            bucket['requests'].append({
                'id': l.id,
                'employee': l.employee_id.name,
                'leaveType': lt.name,
                'from': _d(l.request_date_from),
                'to': _d(l.request_date_to),
                'days': round(l.number_of_days, 2),
                'state': l.state,
                'stateLabel': STATE_LABEL.get(l.state, l.state),
                'stateKind': STATE_KIND.get(l.state, 'gray'),
                'isEmergency': l.x_is_emergency,
            })

        by_type = sorted(type_acc.values(), key=lambda t: t['count'], reverse=True)
        mx = max([t['count'] for t in by_type] + [1])
        for t in by_type:
            t['pct'] = round(t['count'] / mx * 100)
        dept_list = sorted(depts.values(), key=lambda d: d['total'], reverse=True)
        for d in dept_list:
            d['days'] = round(d['days'], 1)

        return request.make_json_response({
            'isOfficer': is_officer,
            'isManager': is_manager,
            'year': year,
            'overview': {
                'total': len(leaves),
                'pending': by_state.get('confirm', 0) + by_state.get('validate1', 0),
                'approved': by_state.get('validate', 0),
                'refused': by_state.get('refuse', 0),
                'cancelled': by_state.get('cancel', 0),
                'approvedDays': round(approved_days, 1),
                'byType': by_type,
            },
            'departments': dept_list,
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in request.env['hr.department'].search([], order='name')],
        })
