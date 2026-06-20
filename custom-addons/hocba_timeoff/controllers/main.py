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
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import content_disposition, request

# Chứng từ y tế (BR-012): chỉ chấp nhận PDF / JPG / PNG, tối đa 5MB.
ALLOWED_MIME = frozenset({'application/pdf', 'image/jpeg', 'image/png'})
MAX_SIZE_BYTES = 5 * 1024 * 1024

# 7 loại nghỉ chuẩn của Học Bá (theo xml_id). SPA chỉ làm việc với các loại
# này — DB còn rất nhiều loại nghỉ demo/bản địa hoá của Odoo mà ta không muốn
# bày ra ở màn tự phục vụ. Lọc theo đây thay vì xoá/lưu trữ dữ liệu demo.
HB_LEAVE_TYPE_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
)

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
    def _scope(self):
        """Phân quyền Nghỉ phép — đồng bộ cách phân vai trò của SPA hocba_hrm.

        Hệ thống role mới KHÔNG gán group hr_holidays cho ai; quyền lấy từ:
        - Admin/HR : base.group_system / hr.group_hr_manager / hr.group_hr_user
                     → mọi phòng ban (HR Manager/Admin còn được override chứng từ).
        - Quản lý  : trưởng phòng ban qua hr.department.manager_id (gồm phòng con)
                     → chỉ phòng ban mình quản lý. Khớp _is_dept_manager của
                     hocba_hrm nên chắc chắn qua được cổng canManage của SPA.
        - Nhân viên: còn lại → chỉ dữ liệu cá nhân.

        Vì không dựa được vào record rule của hr.leave (gắn group hr_holidays /
        leave_manager_id), các endpoint quản lý dùng sudo + lọc phòng ban tường
        minh theo deptIds (xem _dept_domain).
        """
        user = request.env.user
        see_all = (user.has_group('base.group_system')
                   or user.has_group('hr.group_hr_manager')
                   or user.has_group('hr.group_hr_user'))
        is_hr_manager = (user.has_group('base.group_system')
                         or user.has_group('hr.group_hr_manager'))
        dept_ids = [] if see_all else self._managed_department_ids(user.employee_id)
        return {
            'isHrManager': is_hr_manager,      # HR/Admin: override chứng từ y tế
            'isDeptManager': bool(dept_ids),   # Trưởng phòng: theo phòng ban
            'canApprove': see_all or bool(dept_ids),
            'seeAll': see_all,
            'deptIds': dept_ids,
        }

    def _managed_department_ids(self, emp):
        """Phòng ban (gồm phòng con) mà emp làm trưởng phòng (manager_id).
        Nhân bản logic hocba_hrm._managed_department_ids để giữ nhất quán SPA."""
        if not emp:
            return []
        Dept = request.env['hr.department'].sudo()
        managed = Dept.search([('manager_id', '=', emp.id)])
        if not managed:
            return []
        result, frontier = set(managed.ids), managed
        while frontier:
            children = Dept.search([('parent_id', 'in', frontier.ids)])
            frontier = children.filtered(lambda d: d.id not in result)
            result.update(frontier.ids)
        return list(result)

    def _scope_flags(self, scope):
        """Cờ trả cho SPA. isOfficer/isManager giữ tên cũ để tương thích frontend."""
        return {
            'isOfficer': scope['canApprove'],     # tab Chờ duyệt/Tổng hợp, lịch cả đội
            'isManager': scope['canApprove'],     # dashboard chế độ quản lý
            'isHrManager': scope['isHrManager'],  # override chứng từ y tế (BR-011)
        }

    def _dept_domain(self, scope):
        """Domain lọc phòng ban: HR/Admin = tất cả, Trưởng phòng = phòng được giao."""
        if scope['seeAll']:
            return []
        # deptIds rỗng → ('department_id', 'in', []) khớp 0 bản ghi (an toàn).
        return [('department_id', 'in', scope['deptIds'])]

    def _scoped_departments(self, scope):
        """Phòng ban cho dropdown lọc: HR/Admin = tất cả, Trưởng phòng = phòng mình."""
        Dept = request.env['hr.department'].sudo()
        if scope['seeAll']:
            return Dept.search([], order='name')
        return Dept.browse(scope['deptIds'])

    def _hb_leave_type_ids(self):
        """ID của 7 loại nghỉ Học Bá (theo xml_id, bỏ qua loại thiếu)."""
        ids = []
        for xmlid in HB_LEAVE_TYPE_XMLIDS:
            rec = request.env.ref('hocba_timeoff.%s' % xmlid,
                                  raise_if_not_found=False)
            if rec:
                ids.append(rec.id)
        return ids

    def _emp_type_label(self, employee):
        if not employee.x_hb_leave_emp_type:
            return ''
        sel = dict(employee._fields['x_hb_leave_emp_type']
                   ._description_selection(request.env))
        return sel.get(employee.x_hb_leave_emp_type, '')

    def _balances(self, employee):
        """Số dư phép theo từng loại nghỉ (chỉ loại có phân bổ hoặc đã dùng)."""
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=employee.id)
                 .search([('id', 'in', self._hb_leave_type_ids())]))
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
                     ('id', 'in', self._hb_leave_type_ids()),
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
            'unpaid': lt.unpaid,            # True = không lương; hiển thị thẻ trên form
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
            'reason': leave.sudo().private_name or '',
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
            'reason': leave.sudo().private_name or '',
            'isEmergency': leave.x_is_emergency,
            'scheduleConflict': leave.x_schedule_conflict,
            'conflictInfo': leave.x_conflict_info or '',
            'academicReviewRequired': leave.x_academic_review_required,
            'replacementNote': leave.x_replacement_note or '',
            'supportDocument': leave.holiday_status_id.support_document,
            'hasMedicalDoc': leave.x_has_medical_doc,
        }

    def _approver_name(self, leave):
        """Tên người đã duyệt/từ chối đơn. Đơn duyệt qua SPA ghi đè
        first_approver_id = người đăng nhập thật (xem api_request_decision).
        Bỏ qua tên của OdooBot/superuser cho dữ liệu cũ duyệt dưới sudo."""
        # Ưu tiên first_approver_id vì decision endpoint luôn ghi đè field này
        # bằng người duyệt thật; second_approver_id có thể còn là OdooBot.
        emp = leave.first_approver_id or leave.second_approver_id
        if not emp:
            return ''
        root = request.env.ref('base.user_root', raise_if_not_found=False)
        if root and emp.user_id and emp.user_id.id == root.id:
            return ''
        return emp.name or ''

    def _leave_attachments(self, leave):
        """Danh sách chứng từ đính kèm (qua endpoint tải có kiểm quyền sudo)."""
        return [{
            'id': a.id,
            'name': a.name or 'chung-tu',
            'mimetype': a.mimetype or '',
            'url': '/hocba-hrm/api/timeoff/attachment/%d' % a.id,
        } for a in leave.attachment_ids]

    def _overview_payload(self):
        scope = self._scope()
        flags = self._scope_flags(scope)
        emp = request.env.user.employee_id
        if not emp:
            return {**flags, 'employee': None, 'balances': [],
                    'leaveTypes': [], 'requests': []}
        leaves = (request.env['hr.leave'].sudo()
                  .search([('employee_id', '=', emp.id)],
                          order='request_date_from desc, id desc'))
        return {
            **flags,
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
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        # sudo + lọc phòng ban: HR/Admin xem tất cả, Trưởng phòng chỉ phòng mình.
        domain = [('state', 'in', list(PENDING_STATES))] + self._dept_domain(scope)
        leaves = request.env['hr.leave'].sudo().search(
            domain, order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            **self._scope_flags(scope),
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
        if not leave_type.exists() or leave_type.id not in self._hb_leave_type_ids():
            return request.make_json_response(
                {'error': 'leave_type_not_found'}, status=404)

        # Không cho xin nghỉ nếu cả kỳ rơi vào ngày không làm việc
        # (Chủ nhật / Thứ 7 không phải ngày đi làm) — ngày đó vốn đã nghỉ.
        if self._count_working_days(date_from, date_to) == 0:
            return request.make_json_response(
                {'error': 'non_working_day',
                 'message': 'Ngày bạn chọn là ngày nghỉ (Thứ 7/Chủ nhật) — '
                            'không thể xin nghỉ phép vào ngày không làm việc.'},
                status=400)

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

        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)

        # sudo: người duyệt (HR/Admin/Trưởng phòng) không có group hr_holidays.
        leave = request.env['hr.leave'].sudo().browse(leave_id)
        if not leave.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        # Trưởng phòng chỉ xử lý đơn thuộc phòng ban mình quản lý.
        if not scope['seeAll'] and leave.department_id.id not in scope['deptIds']:
            return request.make_json_response({'error': 'forbidden'}, status=403)

        try:
            if action == 'refuse':
                leave.action_refuse()
            else:
                # Ghi ghi-chú thay thế / override chứng từ trước khi duyệt.
                write_vals = {}
                note = (payload.get('replacementNote') or '').strip()
                if note:
                    write_vals['x_replacement_note'] = note
                # Override chứng từ y tế (BR-011): chỉ HR/Admin mới được.
                if payload.get('medicalOverride') and scope['isHrManager']:
                    write_vals['x_medical_override'] = True
                    write_vals['x_medical_override_reason'] = (
                        payload.get('medicalOverrideReason') or '').strip()
                if write_vals:
                    leave.write(write_vals)
                leave.action_approve()
            # Vì duyệt chạy dưới sudo, Odoo ghi người duyệt = OdooBot. Ghi đè lại
            # bằng nhân viên đang đăng nhập (HR/Trưởng phòng) để hiển thị đúng.
            approver = request.env.user.employee_id
            if approver:
                leave.write({'first_approver_id': approver.id})
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)

        # Trả lại danh sách chờ duyệt đã refresh (cùng phạm vi phòng ban).
        domain = [('state', 'in', list(PENDING_STATES))] + self._dept_domain(scope)
        leaves = request.env['hr.leave'].sudo().search(
            domain, order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            **self._scope_flags(scope),
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
        scope = self._scope()
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        if scope['canApprove']:
            data = self._dashboard_manager(year, kw.get('dept'), scope)
        else:
            data = self._dashboard_employee(year)
        data.update({**self._scope_flags(scope), 'year': year})
        return request.make_json_response(data)

    def _dashboard_manager(self, year, dept_raw, scope):
        Leave = request.env['hr.leave'].sudo()  # sudo + lọc phòng ban tường minh
        start, end = self._year_bounds(year)
        try:
            dept_id = int(dept_raw) if dept_raw else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        dept_dom = ([('department_id', '=', dept_id)] if dept_id else []) \
            + self._dept_domain(scope)
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
                            for d in self._scoped_departments(scope)],
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
                 .with_context(employee_id=emp.id)
                 .search([('requires_allocation', '=', True),
                          ('id', 'in', self._hb_leave_type_ids())]))
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
        scope = self._scope()
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        # view='all' chỉ cho người duyệt; mặc định xem lịch của chính mình.
        view = kw.get('scope') if kw.get('scope') in ('me', 'all') else 'me'
        if view == 'all' and not scope['canApprove']:
            view = 'me'

        start, end = self._year_bounds(year)
        overlap = [('date_from', '<=', end), ('date_to', '>=', start)]
        Leave = request.env['hr.leave'].sudo()
        if view == 'all':
            # HR/Admin xem tất cả, Trưởng phòng chỉ phòng ban được giao.
            domain = overlap + self._dept_domain(scope)
        else:
            emp = request.env.user.employee_id
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
            **self._scope_flags(scope),
            'year': year,
            'scope': view,
            'leaveTypes': sorted(types.values(), key=lambda t: t['name']),
            'leaves': rows,
            'mandatoryDays': mdays,
            'workDays': self._work_days(year),
        })

    # ------------------------------------------------------------------
    # Lịch làm việc — Thứ 2..6 mặc định + các ngày đi làm thêm do HR thêm
    # ------------------------------------------------------------------
    def _work_days(self, year):
        days = request.env['hb.work.day'].sudo().search([
            ('date', '>=', '%d-01-01' % year),
            ('date', '<=', '%d-12-31' % year),
        ], order='date')
        return [{'id': d.id, 'date': _d(d.date), 'name': d.name or 'Ngày đi làm'}
                for d in days]

    def _count_working_days(self, date_from, date_to):
        """Số ngày LÀM VIỆC trong [date_from, date_to]: Thứ 2–Thứ 6, cộng các
        ngày Thứ 7 do HR đánh dấu đi làm (hb.work.day). Chủ nhật / Thứ 7 thường
        = ngày nghỉ, không tính."""
        start = fields.Date.to_date(date_from)
        end = fields.Date.to_date(date_to)
        if not start or not end:
            return 0
        work_extra = set(request.env['hb.work.day'].sudo().search([
            ('date', '>=', start), ('date', '<=', end)]).mapped('date'))
        n, cur = 0, start
        while cur <= end:
            if cur.weekday() < 5 or cur in work_extra:  # T2..T6 hoặc T7 đi làm
                n += 1
            cur += timedelta(days=1)
        return n

    @http.route('/hocba-hrm/api/timeoff/workdays', auth='user',
                type='http', methods=['GET'])
    def api_workdays(self, **kw):
        scope = self._scope()
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        return request.make_json_response({
            'canEdit': scope['isHrManager'],   # chỉ HR/Admin được thêm/xoá
            'year': year,
            'workDays': self._work_days(year),
        })

    @http.route('/hocba-hrm/api/timeoff/workdays/add', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_workdays_add(self, **kw):
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        raw_dates = payload.get('dates') or []
        name = (payload.get('name') or 'Ngày đi làm').strip() or 'Ngày đi làm'
        try:
            year = int(payload.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()

        Model = request.env['hb.work.day'].sudo()
        for ds in raw_dates:
            ds = (ds or '').strip()
            if not ds:
                continue
            try:
                day = fields.Date.to_date(ds)
            except (ValueError, TypeError):
                continue
            if not Model.search_count([('date', '=', day)]):
                Model.create({'date': day, 'name': name})
        return request.make_json_response({
            'canEdit': True, 'year': year, 'workDays': self._work_days(year),
        })

    @http.route('/hocba-hrm/api/timeoff/workdays/<int:day_id>/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_workdays_delete(self, day_id, **kw):
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        try:
            year = int(payload.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        rec = request.env['hb.work.day'].sudo().browse(day_id)
        if rec.exists():
            rec.unlink()
        return request.make_json_response({
            'canEdit': True, 'year': year, 'workDays': self._work_days(year),
        })

    # ------------------------------------------------------------------
    # 3.8. GET /summary — BÁO CÁO CÁ NHÂN của nhân viên đang đăng nhập
    #   (Tab "Tổng hợp" — chỉ hiển thị cho role Nhân viên ở SPA). Trả về
    #   thống kê nghỉ phép của CHÍNH user trong năm: quỹ phép năm, KPI,
    #   phân bổ theo loại nghỉ, theo tháng, và danh sách đơn.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/summary', auth='user',
                type='http', methods=['GET'])
    def api_summary(self, **kw):
        scope = self._scope()
        flags = self._scope_flags(scope)
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()

        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({
                **flags, 'year': year, 'empMissing': True,
            })

        start, end = self._year_bounds(year)
        Leave = request.env['hr.leave'].sudo()
        year_dom = [('employee_id', '=', emp.id),
                    ('date_from', '>=', start), ('date_from', '<=', end)]
        leaves = Leave.search(year_dom, order='date_from desc, id desc')

        # --- Quỹ phép năm (loại requires_allocation = quỹ 12 ngày cố định) ---
        annual = None
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=emp.id)
                 .search([('requires_allocation', '=', True),
                          ('id', 'in', self._hb_leave_type_ids())]))
        for lt in types:
            allocated = lt.max_leaves
            remaining = lt.virtual_remaining_leaves
            taken = lt.leaves_taken
            row = {
                'id': lt.id, 'name': lt.name, 'color': _lt_color(lt),
                'allocated': round(allocated, 2),
                'taken': round(taken, 2),
                'remaining': round(remaining, 2),
                'pct': round(min(100, taken / allocated * 100)) if allocated > 0 else 0,
                'low': allocated > 0 and remaining <= 2,
            }
            # Ưu tiên loại có phân bổ làm "quỹ phép năm" chính.
            if annual is None or allocated > annual['allocated']:
                annual = row

        # --- Tổng hợp theo trạng thái / loại nghỉ / tháng ---
        by_state = {k: 0 for k in STATE_LABEL}
        approved_days = paid_days = unpaid_days = 0.0
        type_acc = {}            # id -> {name, color, count, days, unpaid}
        by_month = [0.0] * 12    # ngày đã duyệt theo tháng
        for l in leaves:
            by_state[l.state] = by_state.get(l.state, 0) + 1
            lt = l.holiday_status_id
            t = type_acc.setdefault(lt.id, {
                'id': lt.id, 'name': lt.name, 'color': _lt_color(lt),
                'count': 0, 'days': 0.0, 'unpaid': lt.unpaid})
            t['count'] += 1
            if l.state == 'validate':
                approved_days += l.number_of_days
                t['days'] += l.number_of_days
                if lt.unpaid:
                    unpaid_days += l.number_of_days
                else:
                    paid_days += l.number_of_days
                if l.date_from:
                    by_month[l.date_from.month - 1] += l.number_of_days

        by_type = sorted(type_acc.values(), key=lambda t: t['count'], reverse=True)
        mx_t = max([t['count'] for t in by_type] + [1])
        for t in by_type:
            t['pct'] = round(t['count'] / mx_t * 100)
            t['days'] = round(t['days'], 1)

        mx_m = max(by_month + [1])
        months = [{
            'month': i + 1,
            'days': round(by_month[i], 1),
            'pct': round(by_month[i] / mx_m * 100),
        } for i in range(12)]

        requests = [{
            'id': l.id,
            'leaveTypeId': l.holiday_status_id.id,
            'leaveType': l.holiday_status_id.name,
            'color': _lt_color(l.holiday_status_id),
            'unpaid': l.holiday_status_id.unpaid,
            'from': _d(l.request_date_from),
            'to': _d(l.request_date_to),
            'days': round(l.number_of_days, 2),
            'reason': l.sudo().private_name or '',
            'state': l.state,
            'stateLabel': STATE_LABEL.get(l.state, l.state),
            'stateKind': STATE_KIND.get(l.state, 'gray'),
            'isEmergency': l.x_is_emergency,
        } for l in leaves]

        return request.make_json_response({
            **flags,
            'year': year,
            'empMissing': False,
            'employee': {'id': emp.id, 'name': emp.name,
                         'department': emp.department_id.name or '—'},
            'annual': annual,
            'kpi': {
                'total': len(leaves),
                'pending': by_state.get('confirm', 0) + by_state.get('validate1', 0),
                'approved': by_state.get('validate', 0),
                'refused': by_state.get('refuse', 0),
                'cancelled': by_state.get('cancel', 0),
                'approvedDays': round(approved_days, 1),
                'paidDays': round(paid_days, 1),
                'unpaidDays': round(unpaid_days, 1),
            },
            'byType': by_type,
            'byMonth': months,
            'requests': requests,
        })

    # ------------------------------------------------------------------
    # 3.9. GET /approved — danh sách đơn nghỉ ĐÃ XỬ LÝ (duyệt / từ chối)
    #   Trang quản lý: HR/Admin xem mọi phòng ban, Trưởng phòng chỉ phòng mình.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/approved', auth='user',
                type='http', methods=['GET'])
    def api_approved(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False

        start, end = self._year_bounds(year)
        Leave = request.env['hr.leave'].sudo()
        # Đơn đã xử lý = đã duyệt (validate) hoặc bị từ chối (refuse).
        domain = [('state', 'in', ['validate', 'refuse']),
                  ('date_from', '>=', start), ('date_from', '<=', end)] \
            + self._dept_domain(scope)
        if dept_id:
            domain.append(('department_id', '=', dept_id))
        leaves = Leave.search(domain, order='date_from desc, id desc')

        approved = leaves.filtered(lambda l: l.state == 'validate')
        refused = leaves.filtered(lambda l: l.state == 'refuse')
        rows = [{
            'id': l.id,
            'employee': l.employee_id.name,
            'department': l.department_id.name or l.employee_id.department_id.name or '—',
            'leaveType': l.holiday_status_id.name,
            'color': _lt_color(l.holiday_status_id),
            'unpaid': l.holiday_status_id.unpaid,
            'from': _d(l.request_date_from),
            'to': _d(l.request_date_to),
            'days': round(l.number_of_days, 2),
            'reason': l.sudo().private_name or '',
            'state': l.state,
            'stateLabel': STATE_LABEL.get(l.state, l.state),
            'stateKind': STATE_KIND.get(l.state, 'gray'),
            'isEmergency': l.x_is_emergency,
            'approver': self._approver_name(l),
            'supportDocument': l.holiday_status_id.support_document,
            'attachments': self._leave_attachments(l),
        } for l in leaves]

        return request.make_json_response({
            **self._scope_flags(scope),
            'year': year,
            'kpi': {
                'approved': len(approved),
                'refused': len(refused),
                'days': round(sum(approved.mapped('number_of_days')), 1),
            },
            'requests': rows,
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
        })

    # ------------------------------------------------------------------
    # 3.10. GET /attachment/<id> — tải chứng từ đính kèm của 1 đơn nghỉ.
    #   Vì role mới không có group hr_holidays, /web/content có thể chặn
    #   Trưởng phòng → phục vụ qua đây với sudo + kiểm quyền tường minh:
    #   chủ đơn, hoặc người duyệt trong phạm vi phòng ban được giao.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/attachment/<int:att_id>',
                auth='user', type='http', methods=['GET'])
    def api_attachment(self, att_id, **kw):
        att = request.env['ir.attachment'].sudo().browse(att_id)
        if not att.exists() or att.res_model != 'hr.leave':
            return request.not_found()
        leave = request.env['hr.leave'].sudo().browse(att.res_id)
        if not leave.exists():
            return request.not_found()
        scope = self._scope()
        emp = request.env.user.employee_id
        is_owner = bool(emp) and leave.employee_id.id == emp.id
        in_scope = scope['seeAll'] or (
            scope['canApprove'] and leave.department_id.id in scope['deptIds'])
        if not (is_owner or in_scope):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            data = base64.b64decode(att.datas or b'')
        except (binascii.Error, ValueError):
            return request.not_found()
        return request.make_response(data, headers=[
            ('Content-Type', att.mimetype or 'application/octet-stream'),
            ('Content-Length', len(data)),
            ('Content-Disposition',
             content_disposition(att.name or 'chung-tu')),
        ])
