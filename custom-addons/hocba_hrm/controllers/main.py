import calendar
from datetime import date, timedelta

from psycopg2 import IntegrityError
from pytz import timezone, utc

from odoo import http, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request, Response
from odoo.tools import file_open

# 13/06/2026: SPA là frontend chính thức (FE/BE tách riêng qua API).
# Dev:   cd frontend && npm run dev   (Vite :5173, proxy API về Odoo)
# Build: cd frontend && npm run build → static/spa/, route này serve bản build.
# (quy ước: docs/QUY_UOC_FRONTEND.md)
SPA_ENABLED = True


# Bảng màu gán cho phòng ban theo thứ tự id (SPA filter chips)
DEP_PALETTE = ['#C8102E', '#D9A400', '#0F766E', '#1D4ED8', '#6D28D9',
               '#BE185D', '#B45309', '#334155']

# Map field cho form Thêm/Sửa nhân viên (SPA). key payload camelCase ->
# (field Odoo, tầng quyền). tier: 'core' (mọi HR) | 'hr' (group_hr_user) |
# 'mgr' (group_hr_manager). Field nằm trên hr.employee.
EMP_FORM_FIELDS = {
    'name': ('name', 'core'),
    'code': ('x_employee_code', 'core'),
    'depId': ('department_id', 'core'),
    'jobId': ('job_id', 'core'),
    'workForm': ('x_work_form', 'core'),
    'status': ('x_employment_status', 'core'),
    'posType': ('x_position_type', 'core'),
    'email': ('work_email', 'core'),
    'phone': ('work_phone', 'core'),
    'probStart': ('x_probation_start', 'core'),
    'bday': ('birthday', 'hr'),
    'idIssue': ('x_id_date_issue', 'hr'),
    'idPlace': ('x_id_place_issue', 'hr'),
    'hi': ('x_health_insurance_no', 'hr'),
    'hiPlace': ('x_health_care_place', 'hr'),
    'pit': ('x_pit_code', 'mgr'),
    'si': ('x_social_insurance_no', 'mgr'),
}
# Field nằm trên hr.version (Odoo 19): CCCD + lương
EMP_FORM_VERSION_FIELDS = {
    'cccd': ('identification_id', 'hr'),
    'wage': ('wage', 'mgr'),
}

# Whitelist field nhân viên được TỰ SỬA trên hồ sơ của chính mình (self-service).
# Chỉ liên hệ + địa chỉ — KHÔNG có lương/trạng thái/pháp lý/phòng ban.
ME_SELF_FIELDS = {
    'phone': 'work_phone',
    'permStreet': 'x_permanent_street',
    'permWard': 'x_permanent_ward',
    'permState': 'x_permanent_state_id',
    'currentSame': 'x_current_same_as_permanent',
    'currStreet': 'x_current_street',
    'currWard': 'x_current_ward',
    'currState': 'x_current_state_id',
}

# Field người phụ thuộc (F-003) cho form NPT trong SPA.
DEP_FIELDS = {
    'name': 'name', 'relationship': 'relationship', 'birthday': 'birthday',
    'nationalId': 'national_id', 'dateStart': 'date_start',
    'dateEnd': 'date_end', 'notes': 'notes',
}

# Field cấp tài sản (F-006) cho form Tài sản trong SPA.
ASSET_FIELDS = {
    'assetTypeId': 'asset_type_id', 'assetCode': 'asset_code',
    'grantDate': 'grant_date', 'conditionIn': 'condition_in',
}

# Field thăng tiến (F-007) cho form Thăng tiến trong SPA.
PROMO_FIELDS = {
    'dateEffective': 'date_effective', 'toJobId': 'to_job_id',
    'toDepartmentId': 'to_department_id', 'toWage': 'to_wage',
    'allowanceNote': 'allowance_note', 'reason': 'reason',
    'decisionRef': 'decision_ref',
}

# Field chứng chỉ (F-008) cho form Chứng chỉ trong SPA (hr.employee.skill).
CERT_FIELDS = {
    'skillTypeId': 'skill_type_id', 'skillId': 'skill_id',
    'levelId': 'skill_level_id', 'certDate': 'x_cert_date',
    'certExpiry': 'x_cert_expiry', 'verified': 'x_cert_verified',
}


def _d(v):
    """date/datetime → chuỗi ISO (None-safe)."""
    return v.isoformat() if v else None


def _fmt_hm(hour_float):
    """8.5 -> '08:30' (giờ float local -> chuỗi HH:MM)."""
    h = int(hour_float)
    m = int(round((hour_float - h) * 60))
    return '%02d:%02d' % (h, m)


def _policy_dict(p):
    return {
        'checkInStart': _fmt_hm(p.morning_start),
        'checkInEnd': _fmt_hm(p.morning_end),
        'checkOutStart': _fmt_hm(p.evening_start),
        'checkOutEnd': _fmt_hm(p.evening_end),
        'geofenceOn': bool(p.office_lat and p.office_lng),
    }


def _att_policy_dict(env):
    return _policy_dict(env['hocba.attendance.policy'].sudo().get_policy())


def _dt_local(rec, dt):
    """Datetime UTC (stored) -> chuỗi ISO theo local tz của context."""
    if not dt:
        return None
    local = fields.Datetime.context_timestamp(rec, dt)
    return local.replace(tzinfo=None).isoformat()


def _att_row(rec, policy):
    """Một dòng chấm công cho SPA (wire format camelCase)."""
    return {
        'id': rec.id,
        'empId': rec.employee_id.id,
        'code': rec.employee_id.x_employee_code or '—',
        'name': rec.employee_id.name,
        'depName': rec.employee_id.department_id.name or 'Chưa gán',
        'hasImg': bool(rec.check_in_photo),
        'hasCheckOutImg': bool(rec.check_out_photo),
        'date': _d(rec.date),
        'checkIn': _dt_local(rec, rec.check_in),
        'checkOut': _dt_local(rec, rec.check_out),
        'workingHours': round(rec.working_hours, 2),
        'statusKey': rec.status_code or 'none',
        'lateMinutes': rec.late_minutes,
        'earlyLeaveMinutes': rec.early_leave_minutes,
        'missingMinutes': rec.missing_minutes,
        'workCredit': rec.work_credit,
        'morningCredit': rec.morning_credit,
        'afternoonCredit': rec.afternoon_credit,
        'expectedCheckOut': _dt_local(rec, rec.expected_check_out),
        'faceSuspect': rec.face_suspect,
        'outOfZone': rec.out_of_zone,
        'outOfWindow': rec.out_of_window,
        'needsReview': rec.needs_review,
        'checkInMapUrl': rec.check_in_map_url or None,
        'checkOutMapUrl': rec.check_out_map_url or None,
    }


def _att_me_info(env):
    """Thông tin cá nhân để dựng panel check-in. None nếu user chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    today = fields.Date.context_today(env.user)
    rec = env['hocba.attendance'].sudo().search(
        [('employee_id', '=', emp.id), ('date', '=', today)], limit=1)
    info = {
        'employeeId': emp.id,
        'name': emp.name,
        'enrolled': bool(emp.x_face_descriptor),
        'isOfficial': emp.x_employment_status == 'official',
        'isHr': env.user.has_group('hr.group_hr_user'),
        'isHrManager': env.user.has_group('hr.group_hr_manager'),
        'canManage': _user_can_manage(env),
        'isWorkdayToday': policy.is_workday(
            fields.Datetime.context_timestamp(
                env.user, fields.Datetime.now()).replace(tzinfo=None)),
        'policy': _policy_dict(policy),
        'today': None,
    }
    if rec:
        row = _att_row(rec, policy)
        info['today'] = {k: row[k] for k in (
            'checkIn', 'checkOut', 'workingHours', 'statusKey',
            'lateMinutes', 'faceSuspect', 'outOfZone', 'outOfWindow')}
    return info


def _att_day_table(env, date_str):
    """Bảng chấm công theo ngày. Phạm vi theo vai trò (giống danh sách NV):
    HR/Admin=tất cả; trưởng phòng=phòng mình; giáo vụ=giáo viên; NV thường=của mình."""
    is_hr = env.user.has_group('hr.group_hr_user')
    is_mgr = env.user.has_group('hr.group_hr_manager')
    can_manage = _user_can_manage(env)
    day = fields.Date.from_string(date_str) if date_str else fields.Date.context_today(env.user)
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    domain = [('date', '=', day)]
    if can_manage:
        for field, op, val in _emp_scope_domain(env):  # domain trên hr.employee
            if field == 'id':            # ('id','=',0): không thuộc nhóm nào
                domain.append(('employee_id', op, val))
            else:                         # department_id / x_employee_type_id.code
                domain.append(('employee_id.%s' % field, op, val))
    else:
        emp = env.user.employee_id
        domain.append(('employee_id', '=', emp.id if emp else -1))
    recs = env['hocba.attendance'].sudo().search(domain)
    rows = [_att_row(r, policy) for r in recs]
    counts = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'missing': 0,
        'totalCredit': round(sum(r['workCredit'] for r in rows), 2),
    }
    if (is_hr or is_mgr) and policy.is_workday(day):
        total = env['hr.employee'].sudo().search_count(
            [('x_employment_status', '=', 'official')])
        counts['missing'] = max(0, total - len(rows))
    return {
        'isHr': is_hr, 'isHrManager': is_mgr, 'canManage': can_manage,
        'date': _d(day),
        'policy': _policy_dict(policy),
        'counts': counts,
        'rows': rows,
    }


def _att_me_history(env, month_str):
    """Lịch sử chấm công của chính user theo tháng. None nếu chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    if month_str:
        y, m = (int(x) for x in month_str.split('-'))
    else:
        today = fields.Date.context_today(env.user)
        y, m = today.year, today.month
    first = date(y, m, 1)
    last = date(y, m, calendar.monthrange(y, m)[1])
    recs = env['hocba.attendance'].sudo().search([
        ('employee_id', '=', emp.id),
        ('date', '>=', first), ('date', '<=', last),
    ], order='date desc')
    rows = [_att_row(r, policy) for r in recs]
    total_credit = sum(r['workCredit'] for r in rows)
    # Công thiếu tính theo PHÚT thiếu so với giờ chuẩn (độc lập với work_credit
    # nửa-ngày): bỏ N ngày vi phạm đầu tháng, phần còn lại ÷60 ÷ giờ chuẩn.
    violations = sorted(
        [r for r in rows if r['missingMinutes'] > 0], key=lambda r: r['date'])
    counted = violations[policy.violation_free_days:]
    std = policy.std_work_hours or 8.0
    deficit_credit = round(
        (sum(r['missingMinutes'] for r in counted) / 60.0) / std, 2)
    summary = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'daysPresent': len(rows),
        'totalHours': round(sum(r['workingHours'] for r in rows), 2),
        'totalCredit': round(total_credit, 2),
        'deficitCredit': deficit_credit,
        'netCredit': round(total_credit - deficit_credit, 2),
        'violationDays': len(violations),
    }
    return {'month': '%04d-%02d' % (y, m), 'summary': summary, 'rows': rows}


def _to_utc(env, s):
    """Chuỗi datetime local ('YYYY-MM-DDTHH:MM[:SS]') -> Datetime UTC naive.
    None/'' -> False. Dùng tz của user."""
    if not s:
        return False
    s2 = s.replace('T', ' ')
    if len(s2) == 16:          # thiếu giây
        s2 += ':00'
    try:
        naive = fields.Datetime.to_datetime(s2)
    except (ValueError, TypeError):
        raise ValidationError('Định dạng thời gian không hợp lệ.')
    tz = timezone(env.user.tz or 'UTC')
    return tz.localize(naive).astimezone(utc).replace(tzinfo=None)


def _attendance_edit(env, rec_id, body):
    """Manager sửa check_in/check_out/notes của 1 bản ghi trong phạm vi.
    Trả row đã cập nhật; None nếu không tồn tại; raise AccessError nếu vượt quyền."""
    rec = env['hocba.attendance'].sudo().browse(rec_id)
    if not rec.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, rec.employee_id)):
        raise AccessError('forbidden')
    vals = {}
    if 'checkIn' in body:
        vals['check_in'] = _to_utc(env, body.get('checkIn'))
    if 'checkOut' in body:
        vals['check_out'] = _to_utc(env, body.get('checkOut'))
    if 'notes' in body:
        vals['notes'] = body.get('notes') or False
    if 'check_in' in vals and not vals['check_in']:
        raise ValidationError('Giờ check-in là bắt buộc.')
    rec.sudo().write(vals)
    return _att_row(rec, env['hocba.attendance.policy'].sudo().get_policy())


def _attendance_delete(env, rec_id):
    """Manager xóa 1 bản ghi trong phạm vi. {'ok':True}; None nếu không tồn tại;
    raise AccessError nếu vượt quyền."""
    rec = env['hocba.attendance'].sudo().browse(rec_id)
    if not rec.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, rec.employee_id)):
        raise AccessError('forbidden')
    rec.sudo().unlink()
    return {'ok': True}


def _managed_department_ids(env, emp):
    """Phòng ban (gồm phòng con) mà emp làm trưởng phòng (manager_id)."""
    if not emp:
        return []
    Dept = env['hr.department'].sudo()
    managed = Dept.search([('manager_id', '=', emp.id)])
    if not managed:
        return []
    result, frontier = set(managed.ids), managed
    while frontier:
        children = Dept.search([('parent_id', 'in', frontier.ids)])
        frontier = children.filtered(lambda d: d.id not in result)
        result.update(frontier.ids)
    return list(result)


def _emp_scope_domain(env):
    """Domain giới hạn NV theo vai trò: HR/Admin=tất cả; Giáo vụ=giáo viên;
    Trưởng phòng=phòng mình; còn lại=rỗng (id=0)."""
    user = env.user
    if (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager')):
        return []
    if user.has_group('hocba_employees.group_hocba_giaovu'):
        return [('x_employee_type_id.code', '=', 'teacher')]
    dept_ids = _managed_department_ids(env, user.employee_id)
    if dept_ids:
        return [('department_id', 'in', dept_ids)]
    return [('id', '=', 0)]


def _emp_in_scope(env, e):
    """User hiện tại có được xem/quản lý hồ sơ e không."""
    user = env.user
    if (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager')):
        return True
    if e == user.employee_id:
        return True
    return bool(env['hr.employee'].sudo().search_count(
        [('id', '=', e.id)] + _emp_scope_domain(env)))


def _is_dept_manager(env, emp):
    """True nếu emp là quản lý trực tiếp (có cấp dưới) hoặc trưởng phòng ban."""
    return bool(emp) and (
        bool(emp.child_ids)
        or bool(env['hr.department'].sudo().search_count(
            [('manager_id', '=', emp.id)])))


def _user_can_manage(env):
    """True nếu user thuộc bất kỳ nhóm quản lý nào (Admin/HR Mgr/HR/Giáo vụ/
    Trưởng phòng) — dùng để tách UI manager↔user và chặn manager check-in."""
    user = env.user
    emp = user.employee_id
    is_manager = _is_dept_manager(env, emp)
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hocba_employees.group_hocba_giaovu')
            or is_manager)


_CHECK_ERR_STATUS = {
    'not_workday': 403,
    'already_checked_in': 409,
    'not_checked_in': 409,
    'already_checked_out': 409,
}


class HocBaHRM(http.Controller):

    @http.route('/hocba-hrm', auth='user', type='http', csrf=False)
    def hrm_dashboard(self, **kw):
        if not SPA_ENABLED:
            return request.redirect('/odoo')
        try:
            with file_open('hocba_hrm/static/spa/index.html', 'r') as f:
                html = f.read()
        except (FileNotFoundError, OSError):
            html = ('<h3 style="font-family:sans-serif">SPA chưa được build.</h3>'
                    '<p style="font-family:sans-serif">Chạy: <code>cd frontend &amp;&amp; '
                    'npm install &amp;&amp; npm run build</code> rồi tải lại trang '
                    '(xem docs/QUY_UOC_FRONTEND.md §8).</p>')
        return Response(html, content_type='text/html; charset=utf-8')

    # ------------------------------------------------------------------
    # JSON API cho SPA — dữ liệu thật từ hocba_employees.
    # Trường nhạy cảm chỉ trả khi user thuộc nhóm HR tương ứng:
    #   hr.group_hr_user    → CCCD, ngày sinh, pháp lý cơ bản, NPT, chứng chỉ
    #   hr.group_hr_manager → MST TNCN, BHXH, lương (wage / from_wage / to_wage)
    # ------------------------------------------------------------------

    def _hr_flags(self):
        user = request.env.user
        return (user.has_group('hr.group_hr_user'),
                user.has_group('hr.group_hr_manager'))

    def _managed_department_ids(self, emp):
        """Phòng ban (gồm phòng con) mà emp làm trưởng phòng (manager_id)."""
        return _managed_department_ids(request.env, emp)

    def _emp_scope_domain(self):
        """Domain giới hạn danh sách NV theo vai trò (họp #2):
        HR/Admin = tất cả; Giáo vụ = giáo viên; Quản lý = phòng ban mình;
        còn lại = rỗng."""
        return _emp_scope_domain(request.env)

    def _emp_in_scope(self, e):
        """Người dùng hiện tại có được xem/quản lý hồ sơ e không."""
        return _emp_in_scope(request.env, e)

    def _can_eval_emp(self, e):
        """Người đang đăng nhập có quyền duyệt cổng thử việc của NV e không:
        HR Manager / quản lý trực tiếp (parent_id) / trưởng phòng ban của e."""
        user = request.env.user
        if user.has_group('hr.group_hr_manager'):
            return True
        if e.parent_id and e.parent_id.user_id == user:
            return True
        return bool(e.department_id
                    and e.department_id.id
                    in self._managed_department_ids(user.employee_id))

    def _labels(self):
        env = request.env
        Emp = env['hr.employee']

        def sel(model, fname):
            return dict(model._fields[fname]._description_selection(env))

        return {
            'status': sel(Emp, 'x_employment_status'),
            'work_form': sel(Emp, 'x_work_form'),
            'position': sel(Emp, 'x_position_type'),
            'asset_state': sel(env['hr.employee.asset'], 'state'),
            'relationship': sel(env['hr.employee.dependent'], 'relationship'),
        }

    def _emp_base(self, e, labels, is_mgr):
        status_key = e.x_employment_status or ''
        etype = ('CTV' if status_key == 'ctv'
                 else labels['work_form'].get(e.x_work_form, '—'))
        data = {
            'id': e.id,
            'code': e.x_employee_code or '—',
            'name': e.name,
            'dep': e.department_id.id or 0,
            'depName': e.department_id.name or 'Chưa gán',
            'jobTitle': e.job_id.name or '—',
            'jobId': e.job_id.id or False,
            'status': labels['status'].get(status_key, '—'),
            'statusKey': status_key,
            'type': etype,
            'workFormKey': e.x_work_form or '',
            'posType': labels['position'].get(e.x_position_type, ''),
            'posTypeKey': e.x_position_type or '',
            'probStart': _d(e.x_probation_start),
            'start': _d(e.x_probation_start) or _d(e.create_date and e.create_date.date()),
            'email': e.work_email or '',
            'phone': e.work_phone or '',
            'hasImg': bool(e.image_1920),
        }
        if is_mgr:
            v = e.version_id
            data['wage'] = (v.wage if v and 'wage' in v._fields else 0) or 0
        return data

    @http.route('/hocba-hrm/api/employees', auth='user', type='http', methods=['GET'])
    def api_employees(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        labels = self._labels()
        # Phạm vi theo vai trò (họp #2): HR/Admin = tất cả; Giáo vụ = giáo viên;
        # Quản lý = phòng ban mình. Domain áp tay vì api dùng sudo (bỏ record rule).
        domain = self._emp_scope_domain()
        emps = request.env['hr.employee'].sudo().search(
            domain, order='x_employee_code, id')

        deps = {}
        for i, d in enumerate(emps.mapped('department_id').sorted('id')):
            deps[d.id] = {'id': d.id, 'name': d.name, 'total': 0,
                          'official': 0, 'probation': 0,
                          'color': DEP_PALETTE[i % len(DEP_PALETTE)]}
        rows = []
        for e in emps:
            rows.append(self._emp_base(e, labels, is_mgr))
            dd = deps.get(e.department_id.id)
            if dd:
                dd['total'] += 1
                if e.x_employment_status == 'official':
                    dd['official'] += 1
                elif e.x_employment_status == 'probation':
                    dd['probation'] += 1

        return request.make_json_response({
            'isHr': is_hr,
            'isHrManager': is_mgr,
            'departments': list(deps.values()),
            'employees': rows,
        })

    def _employee_detail(self, e, labels, is_hr, is_mgr):
        """Dựng dict hồ sơ chi tiết theo quyền — dùng chung cho
        /api/employee/<id> (HR xem người khác) và /api/me (tự xem hồ sơ mình)."""
        data = self._emp_base(e, labels, is_mgr)

        # --- Pháp lý (F-002) + NPT (F-003): chỉ HR ---
        if is_hr:
            data.update({
                'bday': _d(e.birthday),
                'cccd': e.identification_id or '',
                'idIssue': _d(e.x_id_date_issue),
                'idPlace': e.x_id_place_issue or '',
                'hi': e.x_health_insurance_no or '',
                'hiPlace': e.x_health_care_place or '',
                'permanentAddr': ', '.join(p for p in (
                    e.x_permanent_street, e.x_permanent_ward,
                    e.x_permanent_state_id.name) if p),
                'currentAddr': ('Giống thường trú' if e.x_current_same_as_permanent
                                else ', '.join(p for p in (
                                    e.x_current_street, e.x_current_ward,
                                    e.x_current_state_id.name) if p)),
                'dependents': [{
                    'id': dp.id,
                    'name': dp.name,
                    'relationship': labels['relationship'].get(dp.relationship, ''),
                    'relationshipKey': dp.relationship or '',
                    'birthday': _d(dp.birthday),
                    'nationalId': dp.national_id or '',
                    'from': _d(dp.date_start),
                    'to': _d(dp.date_end),
                    'notes': dp.notes or '',
                } for dp in e.x_dependent_ids],
            })
        if is_mgr:
            data.update({
                'pit': e.x_pit_code or '',
                'si': e.x_social_insurance_no or '',
            })

        # --- Thử việc 2 cổng (F-004/005) — Nhóm B ---
        data['probation'] = {
            'isGroupB': (e.x_position_type in ('staff', 'manager')
                         and e.x_work_form == 'offline'),
            'canEval': self._can_eval_emp(e),
            'start': _d(e.x_probation_start),
            'd2wDue': _d(e.x_eval_2w_due),
            'd2wResult': e.x_eval_2w_result or 'draft',
            'd2wDate': _d(e.x_eval_2w_date),
            'd2wNote': e.x_eval_2w_note or '',
            'equipDate': _d(e.x_equip_grant_date),
            'd1mDue': _d(e.x_eval_1m_due),
            'd1mResult': e.x_eval_1m_result or 'draft',
            'd1mDate': _d(e.x_eval_1m_date),
            'd1mNote': e.x_eval_1m_note or '',
            'd2mDue': _d(e.x_eval_2m_due),
            'd2mResult': e.x_eval_2m_result or 'draft',
            'd2mDate': _d(e.x_eval_2m_date),
            'd2mNote': e.x_eval_2m_note or '',
            'officialDate': _d(e.x_official_date),
            'officialMonths': round(e.x_official_months or 0, 1),
        }

        # --- Thử giảng (F-008) — Nhóm A ---
        if (e.x_work_form == 'online'
                or e.x_employment_status in ('parttime', 'ctv', 'advisor')):
            data['trial'] = {
                'date': _d(e.x_trial_lesson_date),
                'class': e.x_trial_lesson_class or '',
                'scoreMethod': e.x_trial_score_method or 0,
                'scoreContent': e.x_trial_score_content or 0,
                'result': e.x_trial_lesson_result or 'draft',
                'note': e.x_trial_lesson_note or '',
            }

        # --- Tài sản (F-006) ---
        data['assets'] = [{
            'id': a.id,
            'type': a.asset_type_id.name or '',
            'code': a.asset_code or '',
            'grant': _d(a.grant_date),
            'state': a.state,
            'stateLabel': labels['asset_state'].get(a.state, a.state),
            'returnDate': _d(a.return_date),
        } for a in e.x_asset_ids.sorted('grant_date')]

        # --- Thăng tiến (F-007) ---
        promotions = []
        for p in e.x_promotion_ids.sorted('date_effective'):
            item = {
                'id': p.id,
                'date': _d(p.date_effective),
                'fromJob': p.from_job_id.name or '—',
                'toJob': p.to_job_id.name or '—',
                'dept': p.to_department_id.name or '',
                'ref': p.decision_ref or '',
                'reason': p.reason or '',
            }
            if is_mgr:
                item.update({'fromWage': p.from_wage or 0,
                             'toWage': p.to_wage or 0})
            promotions.append(item)
        data['promotions'] = promotions

        # --- Chứng chỉ (F-008/009): chỉ HR ---
        if is_hr:
            data['certs'] = [{
                'id': s.id,
                'skill': s.skill_id.name or '',
                'level': s.skill_level_id.name or '',
                'date': _d(s.x_cert_date),
                'expiry': _d(s.x_cert_expiry),
                'status': s.x_cert_status or 'none',
                'verified': s.x_cert_verified,
                'skillTypeId': s.skill_type_id.id or False,
                'skillId': s.skill_id.id or False,
                'levelId': s.skill_level_id.id or False,
            } for s in e.employee_skill_ids
                if s.x_cert_date or s.x_cert_expiry]

        return data

    @http.route('/hocba-hrm/api/employee/<int:emp_id>', auth='user',
                type='http', methods=['GET'])
    def api_employee_detail(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        labels = self._labels()
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._emp_in_scope(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        return request.make_json_response(
            self._employee_detail(e, labels, is_hr, is_mgr))

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/gate', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_gate(self, emp_id, **kw):
        """Đánh giá cổng thử việc (F-004/005) từ SPA: ghi kết quả tuần-2/tháng-2.
        Kiểm phạm vi TRONG CODE (HR Manager / quản lý trực tiếp / trưởng phòng
        ban) RỒI mới sudo ghi — nhờ vậy Quản lý không có nhóm HR vẫn duyệt được
        nhưng CHỈ nhân viên thuộc phòng ban mình. Chạy automation AUT-001/002."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        # Gác cổng tại controller: chỉ người có thẩm quyền với NV này mới được duyệt
        if not self._can_eval_emp(e):
            return request.make_json_response(
                {'error': 'forbidden',
                 'message': 'Bạn không có quyền duyệt nhân viên này.'}, status=403)

        payload = request.get_json_data()
        gate = payload.get('gate')
        result = payload.get('result')
        note = (payload.get('note') or '').strip()
        if gate not in ('2w', '1m', '2m') or result not in ('pass', 'fail', 'extend'):
            return request.make_json_response({'error': 'bad_request'}, status=400)

        today = fields.Date.context_today(request.env.user)
        vals = {
            'x_eval_%s_result' % gate: result,
            'x_eval_%s_date' % gate: today,
            'x_eval_%s_evaluator_id' % gate: request.env.user.id,
        }
        if note:
            vals['x_eval_%s_note' % gate] = note
        # Đã kiểm phạm vi ở trên → sudo để Quản lý không-HR vẫn ghi được; chỉ
        # ghi đúng các field cổng (vals), không mở rộng field khác.
        try:
            e.sudo().write(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)

        # Trả hồ sơ đã cập nhật (đọc sudo để dựng đầy đủ theo quyền hiện tại)
        is_hr, is_mgr = self._hr_flags()
        return request.make_json_response(
            self._employee_detail(e.sudo(), self._labels(), is_hr, is_mgr))

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/trial', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_trial(self, emp_id, **kw):
        """Đánh giá thử giảng (F-008) cho giảng viên Nhóm A từ SPA: ghi ngày,
        lớp, 2 điểm, kết quả, nhận xét. KHÔNG sudo — model áp ràng buộc (điểm
        1–10, ngày ≤ hôm nay, fail cần nhận xét) + activity nhắc HR."""
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)

        payload = request.get_json_data()
        result = payload.get('result')
        if result not in ('pass', 'fail'):
            return request.make_json_response({'error': 'bad_request'}, status=400)

        def num(v):
            return float(v) if v not in ('', None) else 0.0
        vals = {
            'x_trial_lesson_date': payload.get('date')
            or fields.Date.context_today(request.env.user),
            'x_trial_lesson_class': (payload.get('cls') or '').strip(),
            'x_trial_score_method': num(payload.get('scoreMethod')),
            'x_trial_score_content': num(payload.get('scoreContent')),
            'x_trial_lesson_note': (payload.get('note') or '').strip(),
            'x_trial_lesson_result': result,
        }
        try:
            e.write(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    # ------------------------------------------------------------------
    # Người phụ thuộc (F-003) — CRUD inline trong SPA (chỉ HR). Mỗi thao tác
    # trả về hồ sơ đã cập nhật để FE refresh tab Thông tin.
    # ------------------------------------------------------------------
    def _dep_vals(self, payload):
        vals = {}
        for key, field in DEP_FIELDS.items():
            if key in payload:
                v = payload[key]
                vals[field] = v if v not in ('', None) else False
        return vals

    def _detail_response(self, e):
        is_hr, is_mgr = self._hr_flags()
        return request.make_json_response(
            self._employee_detail(e.sudo(), self._labels(), is_hr, is_mgr))

    def _dep_response(self, e, is_hr):
        """Self (non-HR) cần payload đầy đủ kèm dependents → dùng _me_payload."""
        if not is_hr and e == request.env.user.employee_id:
            return request.make_json_response(self._me_payload(e.sudo()))
        return self._detail_response(e)

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/dependent', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_dependent_create(self, emp_id, **kw):
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        is_hr, _ = self._hr_flags()
        # Họp #2: cho chính chủ tự thêm NPT của mình (không cần HR duyệt).
        if not (is_hr or e == request.env.user.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        vals = self._dep_vals(request.get_json_data())
        vals['employee_id'] = emp_id
        try:
            request.env['hr.employee.dependent'].sudo().create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._dep_response(e, is_hr)

    @http.route('/hocba-hrm/api/dependent/<int:dep_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_dependent_update(self, dep_id, **kw):
        d = request.env['hr.employee.dependent'].sudo().browse(dep_id)
        if not d.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        is_hr, _ = self._hr_flags()
        if not (is_hr or d.employee_id == request.env.user.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            d.write(self._dep_vals(request.get_json_data()))
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._dep_response(d.employee_id, is_hr)

    @http.route('/hocba-hrm/api/dependent/<int:dep_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_dependent_delete(self, dep_id, **kw):
        d = request.env['hr.employee.dependent'].sudo().browse(dep_id)
        if not d.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        is_hr, _ = self._hr_flags()
        if not (is_hr or d.employee_id == request.env.user.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = d.employee_id
        try:
            d.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._dep_response(e, is_hr)

    # ------------------------------------------------------------------
    # Tài sản (F-006) — cấp / thu hồi / chuyển giao inline trong SPA (HR).
    # KHÔNG xoá (model chặn unlink); state đổi qua action của model.
    # ------------------------------------------------------------------
    def _conv_id(self, v):
        return int(v) if v not in ('', None, False) else False

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/asset', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_create(self, emp_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        payload = request.get_json_data()
        vals = {'employee_id': emp_id}
        for key, field in ASSET_FIELDS.items():
            if key in payload:
                v = payload[key]
                if field == 'asset_type_id':
                    v = self._conv_id(v)
                vals[field] = v if v not in ('', None) else False
        try:
            request.env['hr.employee.asset'].create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    @http.route('/hocba-hrm/api/asset/<int:asset_id>/return', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_return(self, asset_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.employee.asset'].browse(asset_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        e = a.employee_id
        payload = request.get_json_data() or {}
        try:
            a.write({
                'return_date': payload.get('returnDate') or fields.Date.context_today(a),
                'condition_out_note': (payload.get('note') or '').strip(),
            })
            a.action_mark_returned()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    @http.route('/hocba-hrm/api/asset/<int:asset_id>/transfer', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_transfer(self, asset_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.employee.asset'].browse(asset_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        e = a.employee_id
        payload = request.get_json_data() or {}
        target = self._conv_id(payload.get('transferTo'))
        if not target:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        try:
            a.write({
                'transferred_to': target,
                'return_date': payload.get('returnDate') or fields.Date.context_today(a),
            })
            a.action_mark_transferred()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    # ------------------------------------------------------------------
    # Thăng tiến (F-007) — thêm mốc thăng tiến inline (HR Manager). Tạo
    # bản ghi sẽ tự cập nhật chức vụ/phòng ban NV (model). KHÔNG xoá.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/employee/<int:emp_id>/promotion', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_promotion_create(self, emp_id, **kw):
        _, is_mgr = self._hr_flags()
        if not is_mgr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        payload = request.get_json_data()
        vals = {'employee_id': emp_id,
                'from_job_id': e.job_id.id or False,
                'from_wage': (e.version_id.wage if e.version_id
                              and 'wage' in e.version_id._fields else 0) or 0}
        for key, field in PROMO_FIELDS.items():
            if key in payload:
                v = payload[key]
                if field in ('to_job_id', 'to_department_id'):
                    v = self._conv_id(v)
                elif field == 'to_wage':
                    v = float(v) if v not in ('', None) else 0.0
                else:
                    v = v if v not in ('', None) else False
                vals[field] = v
        try:
            request.env['hr.promotion.history'].create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    # ------------------------------------------------------------------
    # Chứng chỉ (F-008) — thêm / sửa / xác minh / xoá inline (chỉ HR).
    # Bản ghi nằm trên hr.employee.skill (đã gắn x_cert_* của hocba).
    # ------------------------------------------------------------------
    def _cert_vals(self, payload):
        vals = {}
        for key, field in CERT_FIELDS.items():
            if key in payload:
                v = payload[key]
                if field in ('skill_type_id', 'skill_id', 'skill_level_id'):
                    v = self._conv_id(v)
                elif field == 'x_cert_verified':
                    v = bool(v)
                else:
                    v = v if v not in ('', None) else False
                vals[field] = v
        return vals

    def _cert_error(self, ex):
        """Đổi lỗi trùng kỹ năng (Odoo báo dài dòng tiếng Anh) thành thông
        điệp gọn tiếng Việt; còn lại giữ nguyên."""
        msg = str(ex)
        if 'overlap' in msg or 'match existing' in msg:
            msg = 'Nhân viên đã có chứng chỉ này.'
        request.env.cr.rollback()
        return request.make_json_response(
            {'error': 'rejected', 'message': msg}, status=400)

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/cert', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_cert_create(self, emp_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        vals = self._cert_vals(request.get_json_data())
        vals['employee_id'] = emp_id
        try:
            request.env['hr.employee.skill'].create(vals)
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Nhân viên đã có chứng chỉ này.'}, status=400)
        except (AccessError, ValidationError, UserError) as ex:
            return self._cert_error(ex)
        return self._detail_response(e)

    @http.route('/hocba-hrm/api/cert/<int:cert_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_cert_update(self, cert_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        c = request.env['hr.employee.skill'].browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            c.write(self._cert_vals(request.get_json_data()))
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Nhân viên đã có chứng chỉ này.'}, status=400)
        except (AccessError, ValidationError, UserError) as ex:
            return self._cert_error(ex)
        return self._detail_response(c.employee_id)

    @http.route('/hocba-hrm/api/cert/<int:cert_id>/verify', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_cert_verify(self, cert_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        c = request.env['hr.employee.skill'].browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        verified = bool((request.get_json_data() or {}).get('verified'))
        try:
            c.write({'x_cert_verified': verified})
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(c.employee_id)

    @http.route('/hocba-hrm/api/cert/<int:cert_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_cert_delete(self, cert_id, **kw):
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        c = request.env['hr.employee.skill'].browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        e = c.employee_id
        try:
            c.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    def _cert_skill_types(self, env):
        """Chỉ trả 2 loại kỹ năng của Học Bá (Tiếng Trung + Sư phạm) — ẩn
        skill type demo của Odoo (Languages/Soft Skills). Fallback: tất cả."""
        ids = []
        for xmlid in ('hocba_employees.skill_type_chinese',
                      'hocba_employees.skill_type_pedagogy'):
            rec = env.ref(xmlid, raise_if_not_found=False)
            if rec:
                ids.append(rec.id)
        domain = [('id', 'in', ids)] if ids else []
        return env['hr.skill.type'].sudo().search(domain, order='name')

    @http.route('/hocba-hrm/api/form/meta', auth='user', type='http', methods=['GET'])
    def api_form_meta(self, **kw):
        """Metadata cho form Thêm/Sửa nhân viên: phòng ban, chức danh, các lựa
        chọn (hình thức/tình trạng/loại vị trí). Chỉ HR."""
        is_hr, is_mgr = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        env = request.env
        Emp = env['hr.employee']

        def opts(fname):
            return list(Emp._fields[fname]._description_selection(env))

        return request.make_json_response({
            'departments': [{'id': d.id, 'name': d.name}
                            for d in env['hr.department'].sudo().search([], order='name')],
            'jobs': [{'id': j.id, 'name': j.name, 'dep': j.department_id.id}
                     for j in env['hr.job'].sudo().search([], order='name')],
            'workForm': opts('x_work_form'),
            'status': opts('x_employment_status'),
            'position': opts('x_position_type'),
            'relationship': list(env['hr.employee.dependent']._fields[
                'relationship']._description_selection(env)),
            'assetTypes': [{'id': t.id, 'name': t.name}
                           for t in env['hocba.asset.type'].sudo().search([], order='name')],
            'assetCondition': list(env['hr.employee.asset']._fields[
                'condition_in']._description_selection(env)),
            'employees': [{'id': em.id, 'name': em.name}
                          for em in env['hr.employee'].sudo().search(
                              [], order='name')],
            'skillTypes': [{
                'id': t.id, 'name': t.name,
                'skills': [{'id': sk.id, 'name': sk.name} for sk in t.skill_ids],
                'levels': [{'id': lv.id, 'name': lv.name} for lv in t.skill_level_ids],
            } for t in self._cert_skill_types(env)],
            'canManager': is_mgr,
        })

    def _split_form_payload(self, payload, is_hr, is_mgr):
        """Tách payload thành (vals hr.employee, vals hr.version) theo tầng quyền.
        Field ngoài whitelist hoặc vượt quyền sẽ bị bỏ qua (không ghi)."""
        def allowed(tier):
            return tier == 'core' or (tier == 'hr' and is_hr) or (tier == 'mgr' and is_mgr)

        def conv(field, val):
            if field in ('department_id', 'job_id'):
                return int(val) if val else False
            if field == 'wage':
                return float(val) if val not in ('', None) else 0.0
            return val if val not in ('', None) else False

        emp_vals, ver_vals = {}, {}
        for key, (field, tier) in EMP_FORM_FIELDS.items():
            if key in payload and allowed(tier):
                emp_vals[field] = conv(field, payload[key])
        for key, (field, tier) in EMP_FORM_VERSION_FIELDS.items():
            if key in payload and allowed(tier):
                ver_vals[field] = conv(field, payload[key])
        return emp_vals, ver_vals

    @http.route('/hocba-hrm/api/employees', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_employee_create(self, **kw):
        """Tạo nhân viên mới từ SPA. Ghi KHÔNG sudo → model tự kiểm quyền tạo
        + ràng buộc (CCCD 12 số, official cần MST/BHXH...)."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        if not (emp_vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập họ tên.'}, status=400)
        try:
            e = request.env['hr.employee'].create(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự đã tồn tại. Vui lòng nhập mã khác.'}, status=400)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(
            self._employee_detail(e.sudo(), self._labels(), is_hr, is_mgr))

    @http.route('/hocba-hrm/api/employee/<int:emp_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_update(self, emp_id, **kw):
        """Cập nhật nhân viên từ SPA (POST cùng path với GET detail). Ghi KHÔNG
        sudo → model tự kiểm quyền + ràng buộc."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        try:
            if emp_vals:
                e.write(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự đã tồn tại. Vui lòng nhập mã khác.'}, status=400)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(
            self._employee_detail(e.sudo(), self._labels(), is_hr, is_mgr))

    def _me_payload(self, e):
        """Dựng payload /api/me: hồ sơ đầy đủ (tự xem nên is_hr=is_mgr=True) +
        danh sách tỉnh/thành + giá trị thô của field tự-sửa (cho form self-edit)."""
        data = self._employee_detail(e.sudo(), self._labels(), True, True)
        data['hasEmployee'] = True
        states = request.env['res.country.state'].sudo().search(
            [('country_id.code', '=', 'VN')], order='name')
        data['provinces'] = [{'id': s.id, 'name': s.name} for s in states]
        data['editable'] = {
            'phone': e.work_phone or '',
            'permStreet': e.x_permanent_street or '',
            'permWard': e.x_permanent_ward or '',
            'permState': e.x_permanent_state_id.id or False,
            'currentSame': e.x_current_same_as_permanent,
            'currStreet': e.x_current_street or '',
            'currWard': e.x_current_ward or '',
            'currState': e.x_current_state_id.id or False,
        }
        return data

    @http.route('/hocba-hrm/api/me', auth='user', type='http', methods=['GET'])
    def api_me(self, **kw):
        """Hồ sơ self-service: user xem hồ sơ CỦA CHÍNH MÌNH (đầy đủ pháp lý/
        NPT/lương của bản thân)."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        e = request.env.user.employee_id
        if not e:
            return request.make_json_response({'hasEmployee': False})
        return request.make_json_response(self._me_payload(e.sudo()))

    def _role_payload(self):
        """Cờ vai trò để SPA dựng nav (tách tài khoản quản lý ↔ cá nhân — họp #2).
        Robust kể cả khi user chưa gắn hồ sơ nhân viên."""
        user = request.env.user
        emp = user.employee_id
        is_admin = user.has_group('base.group_system')
        is_hr_mgr = user.has_group('hr.group_hr_manager')
        is_hr_user = user.has_group('hr.group_hr_user')
        is_giaovu = user.has_group('hocba_employees.group_hocba_giaovu')
        is_manager = _is_dept_manager(request.env, emp)
        can_manage = _user_can_manage(request.env)
        roles = []
        if is_admin:
            roles.append('Admin')
        if is_hr_mgr:
            roles.append('HR Manager')
        elif is_hr_user:
            roles.append('HR')
        if is_giaovu:
            roles.append('Giáo vụ')
        if is_manager:
            roles.append('Quản lý')
        if not roles:
            roles.append('Nhân viên')
        return {
            'name': user.name,
            'login': user.login,
            'employeeId': emp.id if emp else False,
            'hasEmployee': bool(emp),
            'roleLabel': ' · '.join(roles),
            'isAdmin': is_admin,
            'isHrManager': is_hr_mgr,
            'isHrUser': is_hr_user,
            'isGiaovu': is_giaovu,
            'isManager': is_manager,
            'canManage': can_manage,
        }

    @http.route('/hocba-hrm/api/me/roles', auth='user', type='http',
                methods=['GET'])
    def api_me_roles(self, **kw):
        """Danh tính + cờ vai trò (nhẹ) để SPA quyết định menu/quyền hiển thị."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        return request.make_json_response(self._role_payload())

    @http.route('/hocba-hrm/api/me', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_me_update(self, **kw):
        """Nhân viên TỰ cập nhật liên hệ + địa chỉ của chính mình. Ghi sudo vào
        hồ sơ của bản thân nhưng CHỈ field trong ME_SELF_FIELDS (không leo thang
        sang lương/trạng thái/pháp lý)."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        e = request.env.user.employee_id
        if not e:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        payload = request.get_json_data()
        vals = {}
        for key, field in ME_SELF_FIELDS.items():
            if key not in payload:
                continue
            v = payload[key]
            if field.endswith('state_id'):
                v = int(v) if v else False
            elif field == 'x_current_same_as_permanent':
                v = bool(v)
            else:
                v = v if v not in ('', None) else False
            vals[field] = v
        # Nếu chọn "tạm trú giống thường trú" thì đồng bộ luôn (onchange không
        # chạy qua write) để dữ liệu nhất quán.
        if vals.get('x_current_same_as_permanent'):
            vals['x_current_state_id'] = vals.get('x_permanent_state_id', e.x_permanent_state_id.id)
            vals['x_current_ward'] = vals.get('x_permanent_ward', e.x_permanent_ward)
            vals['x_current_street'] = vals.get('x_permanent_street', e.x_permanent_street)
        try:
            e.sudo().write(vals)
        except (ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._me_payload(e.sudo()))

    @http.route('/hocba-hrm/api/me/photo', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_me_photo(self, **kw):
        """Nhân viên TỰ cập nhật ảnh đại diện của chính mình (image_1920).
        Nhận base64 (có/không tiền tố data:URI); gửi rỗng để xoá ảnh."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        e = request.env.user.employee_id
        if not e:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        img = (request.get_json_data() or {}).get('image') or ''
        if isinstance(img, str) and img.startswith('data:') and ',' in img:
            img = img.split(',', 1)[1]
        try:
            e.sudo().write({'image_1920': img or False})
        except (ValidationError, UserError, OSError, ValueError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': 'Ảnh không hợp lệ.'}, status=400)
        return request.make_json_response(self._me_payload(e.sudo()))

    @http.route('/hocba-hrm/api/employees/cert-alerts', auth='user',
                type='http', methods=['GET'])
    def api_cert_alerts(self, **kw):
        """F-009: chứng chỉ sắp/đã hết hạn — widget cảnh báo dashboard.
        Cert là dữ liệu HR → non-HR nhận danh sách rỗng (không phải 403) để
        dashboard tự ẩn widget."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'isHr': False, 'alerts': []})

        # Khớp đúng tập cảnh báo của CRON F-009 (_cron_cert_expiry_alerts):
        # chỉ cert ĐÃ XÁC MINH + nhân viên active; search trên x_cert_expiry
        # (stored) vì x_cert_status là computed non-stored, không search được.
        days = int(request.env['ir.config_parameter'].sudo().get_param(
            'hoc_ba.cert_alert_days', '60'))
        today = fields.Date.today()
        skills = request.env['hr.employee.skill'].sudo().search([
            ('x_cert_verified', '=', True),
            ('employee_id.active', '=', True),
            ('x_cert_expiry', '!=', False),
            ('x_cert_expiry', '<=', today + timedelta(days=days)),
        ])
        alerts = []
        for s in skills:
            e = s.employee_id
            alerts.append({
                'empId': e.id,
                'empName': e.name,
                'empCode': e.x_employee_code or '—',
                'dep': e.department_id.name or 'Chưa gán',
                'hasImg': bool(e.image_1920),
                'skill': s.skill_id.name or '',
                'level': s.skill_level_id.name or '',
                'expiry': _d(s.x_cert_expiry),
                'status': 'expired' if s.x_cert_expiry < today else 'expiring',
            })
        # sắp xếp: hết hạn trước, rồi theo ngày hết hạn gần nhất
        alerts.sort(key=lambda a: (a['status'] != 'expired', a['expiry'] or '9999'))
        return request.make_json_response({'isHr': True, 'alerts': alerts})

    @http.route('/hocba-hrm/api/employees/onboarding', auth='user',
                type='http', methods=['GET'])
    def api_onboarding(self, **kw):
        """Bảng theo dõi nhập việc: nhân viên đang thử việc + tình trạng 2 cổng
        (F-004/005) và thử giảng (F-008). Dữ liệu cổng không nhạy cảm → trả cho
        mọi user đăng nhập; FE tự suy ra phase/quá hạn từ ngày trả về."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        # Phạm vi theo vai trò (giống danh sách NV): Quản lý chỉ thấy phòng mình,
        # Giáo vụ chỉ giáo viên, HR/Admin thấy tất cả.
        emps = request.env['hr.employee'].sudo().search(
            [('x_employment_status', '=', 'probation')] + self._emp_scope_domain(),
            order='x_probation_start desc, id')
        items = []
        for e in emps:
            items.append({
                'id': e.id,
                'code': e.x_employee_code or '—',
                'name': e.name,
                'depName': e.department_id.name or 'Chưa gán',
                'jobTitle': e.job_id.name or '—',
                'hasImg': bool(e.image_1920),
                'start': _d(e.x_probation_start),
                'isGroupB': (e.x_position_type in ('staff', 'manager')
                             and e.x_work_form == 'offline'),
                # Cổng tuần-2 (cấp thiết bị)
                'g1Due': _d(e.x_eval_2w_due),
                'g1Result': e.x_eval_2w_result or 'draft',
                'g1Date': _d(e.x_eval_2w_date),
                'equipDate': _d(e.x_equip_grant_date),
                # Cổng tháng-1 (có thể lên chính thức sớm)
                'g1mDue': _d(e.x_eval_1m_due),
                'g1mResult': e.x_eval_1m_result or 'draft',
                'g1mDate': _d(e.x_eval_1m_date),
                # Cổng tháng-2 (lên chính thức)
                'g2Due': _d(e.x_eval_2m_due),
                'officialDate': _d(e.x_official_date),
                'g2Result': e.x_eval_2m_result or 'draft',
                'g2Date': _d(e.x_eval_2m_date),
                # Thử giảng (Nhóm A)
                'trialDate': _d(e.x_trial_lesson_date),
                'trialResult': e.x_trial_lesson_result or 'draft',
            })
        return request.make_json_response({
            'isHr': is_hr, 'isHrManager': is_mgr, 'items': items})

    # ------------------------------------------------------------------
    # JSON API Chấm công (Attendance) — owner FE: Hoàng Anh.
    # Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md
    # Logic face/geo tái dùng hocba.attendance._do_check / enroll_self_face.
    # ------------------------------------------------------------------

    @http.route('/hocba-hrm/api/attendance/me', auth='user',
                type='http', methods=['GET'])
    def api_attendance_me(self, **kw):
        info = _att_me_info(request.env)
        if info is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(info)

    @http.route('/hocba-hrm/api/attendance', auth='user',
                type='http', methods=['GET'])
    def api_attendance_day(self, date=None, **kw):
        return request.make_json_response(_att_day_table(request.env, date))

    @http.route('/hocba-hrm/api/attendance/me/history', auth='user',
                type='http', methods=['GET'])
    def api_attendance_history(self, month=None, **kw):
        data = _att_me_history(request.env, month)
        if data is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/attendance/enroll', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_enroll(self, **kw):
        if not request.env.user.employee_id:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        payload = request.get_json_data()
        request.env['hr.employee'].enroll_self_face({
            'photo': payload.get('photo'),
            'descriptor': payload.get('descriptor') or [],
        })
        return request.make_json_response({'ok': True})

    @http.route(['/hocba-hrm/api/attendance/check-in',
                 '/hocba-hrm/api/attendance/check-out'],
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_check(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if _user_can_manage(request.env):
            return request.make_json_response(
                {'error': 'manager_no_checkin'}, status=403)
        if emp.x_employment_status != 'official':
            return request.make_json_response({'error': 'not_official'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        method = 'action_check_out' if kind == 'out' else 'action_check_in'
        try:
            res = getattr(request.env['hocba.attendance'], method)({
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
            })
        except UserError as ex:
            code = str(ex)
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': code}, status=_CHECK_ERR_STATUS.get(code, 400))
        return request.make_json_response({
            'recordId': res['record_id'], 'kind': res['kind'],
            'faceSuspect': res['face_suspect'], 'outOfZone': res['out_of_zone'],
            'outOfWindow': res['out_of_window'], 'faceScore': res['face_score'],
        })

    @http.route('/hocba-hrm/api/attendance/<int:rec_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_edit(self, rec_id, **kw):
        try:
            row = _attendance_edit(request.env, rec_id,
                                   request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/<int:rec_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_delete(self, rec_id, **kw):
        try:
            res = _attendance_delete(request.env, rec_id)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        if res is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(res)
