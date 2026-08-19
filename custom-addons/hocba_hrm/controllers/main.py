import calendar
import hashlib
import json
import re
from datetime import date, datetime, time, timedelta

from psycopg2 import IntegrityError
from pytz import timezone, utc

from odoo import http, fields, SUPERUSER_ID
from odoo.exceptions import (
    AccessDenied, AccessError, UserError, ValidationError)
from odoo.fields import Domain
from odoo.http import request, Response
from odoo.tools import file_open

from odoo.addons.hocba_attendance.utils.cms_connector import (
    get_sessions_for_tutor, get_sessions_for_week, session_to_dict
)

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
    # Loại nhân sự (tag NV văn phòng / Giáo viên / CTV). Cùng tầng 'core' với
    # depId/status: quyền ghi đã chặn ở _can_edit_emp_record + _emp_in_scope.
    'empTypeId': ('x_employee_type_id', 'core'),
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
    'bankAccountNo': ('x_bank_account_no', 'mgr'),
    'bankCode': ('x_bank_code', 'mgr'),
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


def _bank_options(env):
    """Danh sách ngân hàng cho dropdown form NV — đọc từ cấu hình payroll
    (hb.bank.format). Trả [] nếu module payroll chưa cài (loose coupling)."""
    if 'hb.bank.format' not in env:
        return []
    return [{'code': b.code, 'name': b.name}
            for b in env['hb.bank.format'].sudo().search(
                [('active', '=', True)], order='sequence, name')]


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
        'geofenceOn': p.has_geofence,
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
        'notes': rec.notes or '',
    }


# ── Teaching schedule helpers ────────────────────────────────────────────────

def _teaching_session_row(session_dict, att_rec, policy, now_utc):
    """Chuẩn hóa 1 buổi dạy thành dict trả về API."""
    window = policy.shift_window_minutes or 15

    def _utc_from_local_time(d, t_str):
        """Parse 'HH:MM' (ICT) → UTC datetime."""
        if not d or not t_str:
            return None
        try:
            h, m = map(int, t_str.split(':')[:2])
            return datetime(d.year, d.month, d.day, h, m) - timedelta(hours=7)
        except Exception:
            return None

    d = session_dict['_date_raw']
    start_utc = _utc_from_local_time(d, session_dict['startTime'])
    end_utc = _utc_from_local_time(d, session_dict['endTime'])

    check_in_open = (start_utc and
                     abs((now_utc - start_utc).total_seconds()) <= window * 60)
    check_out_open = (end_utc and att_rec and att_rec.check_in and
                      abs((now_utc - end_utc).total_seconds()) <= window * 60)

    return {
        'id': session_dict['id'],
        'classId': session_dict['classId'],
        'className': session_dict['className'],
        'date': session_dict['date'],
        'startTime': session_dict['startTime'],
        'endTime': session_dict['endTime'],
        'status': session_dict['status'],
        'roleType': session_dict['roleType'],
        'checkIn': _dt_local(att_rec, att_rec.check_in) if att_rec else None,
        'checkOut': _dt_local(att_rec, att_rec.check_out) if att_rec else None,
        'workedHours': att_rec.worked_hours if att_rec else 0.0,
        'faceSuspect': att_rec.face_suspect if att_rec else False,
        'outOfZone': att_rec.out_of_zone if att_rec else False,
        'outOfWindow': att_rec.out_of_window if att_rec else False,
        'checkInOpen': bool(check_in_open),
        'checkOutOpen': bool(check_out_open),
    }


def _teaching_today_rows(env, emp, today, policy):
    """Buổi dạy hôm nay của giáo viên. Trả về [] nếu không có x_cms_user_id."""
    if not emp.x_cms_user_id:
        return []
    sessions_raw = get_sessions_for_tutor(emp.x_cms_user_id, today)
    if not sessions_raw:
        return []

    session_ids = [r['id'] for r in sessions_raw]
    att_map = {}
    for att in env['hocba.teaching.attendance'].sudo().search(
            [('cms_session_id', 'in', session_ids), ('employee_id', '=', emp.id)]):
        att_map[att.cms_session_id] = att

    now_utc = fields.Datetime.now()
    rows = []
    for raw in sessions_raw:
        sd = session_to_dict(raw)
        att = att_map.get(sd['id'])
        rows.append(_teaching_session_row(sd, att, policy, now_utc))
    return rows


def _teaching_week_rows(env, emp, monday, policy):
    """Buổi dạy của giáo viên trong tuần."""
    if not emp.x_cms_user_id:
        return []
    sessions_raw = get_sessions_for_week(emp.x_cms_user_id, monday)
    if not sessions_raw:
        return []

    session_ids = [r['id'] for r in sessions_raw]
    att_map = {}
    for att in env['hocba.teaching.attendance'].sudo().search(
            [('cms_session_id', 'in', session_ids), ('employee_id', '=', emp.id)]):
        att_map[att.cms_session_id] = att

    now_utc = fields.Datetime.now()
    rows = []
    for raw in sessions_raw:
        sd = session_to_dict(raw)
        att = att_map.get(sd['id'])
        rows.append(_teaching_session_row(sd, att, policy, now_utc))
    return rows


def _teaching_days_payload(env, from_str, to_str):
    """Payload cho /api/teaching/days. Trả (dict, http_status).

    Nguồn dữ liệu: model `hocba.teaching.session` trong Neon (KHÔNG đọc CMS).
    - Không phải GV (không có x_cms_user_id) → ({isTeacher:False, days:[]}, 200)
    - from/to thiếu hoặc sai định dạng → ({error:'invalid_date'}, 400)
    - to < from hoặc khoảng > 366 ngày → ({error:'invalid_range'}, 400)
    - Hợp lệ → ({isTeacher:True, days:[{date,count}]}, 200)
      Đếm số buổi/ngày mà GV đang phụ trách (bỏ buổi đã hủy cả lớp).
    """
    emp = env.user.employee_id
    if not emp or not emp.x_cms_user_id:
        return {'isTeacher': False, 'days': []}, 200
    try:
        d_from = datetime.strptime(from_str or '', '%Y-%m-%d').date()
        d_to = datetime.strptime(to_str or '', '%Y-%m-%d').date()
    except ValueError:
        return {'error': 'invalid_date'}, 400
    if d_to < d_from or (d_to - d_from).days > 366:
        return {'error': 'invalid_range'}, 400
    # User thường không có ACL trên hocba.teaching.session → sudo SAU khi đã ghim
    # employee_id của chính mình (self-service an toàn).
    sessions = env['hocba.teaching.session'].sudo().search_read(
        [('employee_id', '=', emp.id),
         ('state', '!=', 'cancelled'),
         ('session_date', '>=', d_from),
         ('session_date', '<=', d_to)],
        ['session_date'])
    counts = {}
    for s in sessions:
        key = str(s['session_date'])
        counts[key] = counts.get(key, 0) + 1
    days = [{'date': d, 'count': c} for d, c in sorted(counts.items())]
    return {'isTeacher': True, 'days': days}, 200


def _att_pending_count(env):
    """Tổng số đơn và ca chờ duyệt trong phạm vi quản lý."""
    if not _user_can_manage(env):
        return 0
    # Đơn sửa chấm công
    req_dom = [('state', '=', 'pending')]
    for field, op, val in _emp_scope_domain(env):
        if field == 'id':
            req_dom.append(('employee_id', op, val))
        else:
            req_dom.append(('employee_id.%s' % field, op, val))
    req_count = env['hocba.attendance.request'].sudo().search_count(req_dom)

    # Ca làm việc
    shift_dom = [('state', '=', 'pending')] + _shift_scope_domain(env)
    shift_count = env['hocba.work_shift'].sudo().search_count(shift_dom)

    return req_count + shift_count


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
            'lateMinutes', 'faceSuspect', 'outOfZone', 'outOfWindow', 'notes')}
    info['shiftToday'] = None
    if not info['isOfficial']:
        window = policy.shift_window_minutes or 15
        now_local = fields.Datetime.context_timestamp(
            env.user, fields.Datetime.now()).replace(tzinfo=None)
        shifts = env['hocba.attendance']._todays_approved_shifts(
            emp, now_local.date())
        if shifts:
            s = shifts[0]
            ci = fields.Datetime.context_timestamp(s, s.start).replace(tzinfo=None)
            co = fields.Datetime.context_timestamp(s, s.end).replace(tzinfo=None)
            info['shiftToday'] = {
                'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
                'shiftType': s.shift_type, 'rate': s.rate,
                'checkInOpen': abs((now_local - ci).total_seconds()) <= window * 60,
                'checkOutOpen': abs((now_local - co).total_seconds()) <= window * 60,
            }
    info['shiftsToday'] = _shift_today_rows(env, emp)
    # Lịch dạy giáo viên từ CMS (chỉ khi employee có x_cms_user_id)
    info['teachingToday'] = _teaching_today_rows(env, emp, today, policy)
    info['isTeacher'] = bool(emp.x_cms_user_id)
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


def _ot_row(env, s):
    """Một ca OT cho SPA (camelCase) + công ca theo giờ chấm THỰC TẾ (hocba.shift.attendance).
    counted = ca đã check-in; congCa = giờ_chấm/8 × hệ số (0 nếu chưa chấm)."""
    att = env['hocba.shift.attendance'].sudo().search([('shift_id', '=', s.id)], limit=1)
    hours = att.worked_hours if att else 0.0
    counted = bool(att and att.check_in)
    d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
    emp = s.employee_id
    return {
        'id': s.id, 'empId': emp.id, 'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'date': _d(d) if d else None,
        'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
        'shiftType': s.shift_type, 'otLevel': s.ot_level, 'rate': s.rate,
        'hours': round(hours, 2), 'counted': counted,
        'congCa': round((hours / 8.0) * s.rate, 2) if counted else 0.0,
        'state': s.state,
    }


def _ot_for_employee(env, emp, first, last):
    """Tổng OT của 1 NV trong [first,last] (ca approved, start trong tháng,
    chỉ cộng ca counted). Trả {otHours, otCong}."""
    shifts = env['hocba.work_shift'].sudo().search([
        ('employee_id', '=', emp.id), ('state', '=', 'approved')])
    rows = []
    for s in shifts:
        d = fields.Datetime.context_timestamp(s, s.start).date()
        if first <= d <= last:
            rows.append(_ot_row(env, s))
    return {
        'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
        'otCong': round(sum(r['congCa'] for r in rows), 2),
    }


def _ot_table(env, month_str, date_from=None, date_to=None):
    """Bảng ca OT approved theo tháng + phạm vi vai trò (giống _att_day_table).
    rows=mọi ca approved trong tháng; totals cộng ca counted. canManage."""
    user = env.user
    if date_from and date_to:
        first = fields.Date.from_string(date_from)
        last = fields.Date.from_string(date_to)
        y, m = first.year, first.month
    else:
        if month_str:
            y, m = (int(x) for x in month_str.split('-'))
        else:
            today = fields.Date.context_today(user)
            y, m = today.year, today.month
        first, last = _get_month_range(env, y, m)

    tz = timezone(user.tz or 'UTC')
    start_dt_local = tz.localize(datetime.combine(first, time.min))
    end_dt_local = tz.localize(datetime.combine(last, time.max))
    start_utc = start_dt_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_dt_local.astimezone(utc).replace(tzinfo=None)
    domain = [('state', '=', 'approved'),
              ('start', '>=', start_utc), ('start', '<=', end_utc)]
    if _user_can_manage(env):
        for field, op, val in _emp_scope_domain(env):
            if field == 'id':
                domain.append(('employee_id', op, val))
            else:
                domain.append(('employee_id.%s' % field, op, val))
    else:
        emp = user.employee_id
        domain.append(('employee_id', '=', emp.id if emp else -1))
    recs = env['hocba.work_shift'].sudo().search(domain, order='start')
    rows = [_ot_row(env, s) for s in recs]
    return {
        'month': '%04d-%02d' % (y, m),
        'canManage': _user_can_manage(env),
        'rows': rows,
        'totals': {
            'otHours': round(sum(r['hours'] for r in rows if r['counted']), 2),
            'otCong': round(sum(r['congCa'] for r in rows), 2),
            'count': len(rows),
            'countedCount': sum(1 for r in rows if r['counted']),
        },
    }


def _shift_history_row(env, s, att, row_type):
    """Một dòng ca OT/CTV cho history-full (unified row format như _att_row).
    s = hocba.work_shift, att = hocba.shift.attendance (có thể None/empty)."""
    emp = s.employee_id
    d = fields.Datetime.context_timestamp(s, s.start).date() if s.start else None
    start_local = fields.Datetime.context_timestamp(s, s.start) if s.start else None
    end_local = fields.Datetime.context_timestamp(s, s.end) if s.end else None

    checked_in = bool(att and att.check_in)
    hours = att.worked_hours if att else 0.0
    worked_min = int(hours * 60)

    # Shift duration (minutes)
    shift_min = 0
    if s.start and s.end:
        shift_min = int((s.end - s.start).total_seconds() / 60)

    # Late = check_in vượt quá shift.start
    late_min = 0
    if checked_in and s.start:
        diff = (att.check_in - s.start).total_seconds()
        late_min = max(0, int(diff / 60))

    # Early leave = check_out trước shift.end
    early_min = 0
    if att and att.check_out and s.end:
        diff = (s.end - att.check_out).total_seconds()
        early_min = max(0, int(diff / 60))

    # Missing = shift duration - worked (nếu đã check in)
    missing_min = max(0, shift_min - worked_min) if checked_in else 0

    # workCredit = congCa
    cong_ca = round((hours / 8.0) * (s.rate or 1.0), 2) if checked_in else 0.0

    # statusKey
    if not checked_in:
        status_key = 'none'
    elif late_min > 0:
        status_key = 'late'
    else:
        status_key = 'on_time'

    # shiftLabel  e.g. "OT 150% · 08:00–12:00" hoặc "CTV · 08:00–12:00"
    t_start = start_local.strftime('%H:%M') if start_local else '?'
    t_end = end_local.strftime('%H:%M') if end_local else '?'
    if row_type == 'ot':
        level_label = '%s%%' % (s.ot_level,) if s.ot_level else '100%'
        shift_label = 'OT %s · %s–%s' % (level_label, t_start, t_end)
    else:
        shift_label = 'CTV · %s–%s' % (t_start, t_end)

    return {
        'id': s.id,
        'empId': emp.id,
        'code': emp.x_employee_code or '—',
        'name': emp.name,
        'depName': emp.department_id.name or 'Chưa gán',
        'hasImg': bool(att and att.check_in_photo),
        'hasCheckOutImg': bool(att and att.check_out_photo),
        'date': _d(d) if d else None,
        'checkIn': _dt_local(att, att.check_in) if att and att.check_in else None,
        'checkOut': _dt_local(att, att.check_out) if att and att.check_out else None,
        'workingHours': round(hours, 2),
        'statusKey': status_key,
        'lateMinutes': late_min,
        'earlyLeaveMinutes': early_min,
        'missingMinutes': missing_min,
        'workCredit': cong_ca,
        'morningCredit': 0.0,
        'afternoonCredit': 0.0,
        'expectedCheckOut': _dt_local(s, s.end) if s.end else None,
        'faceSuspect': att.face_suspect if att else False,
        'outOfZone': att.out_of_zone if att else False,
        'outOfWindow': att.out_of_window if att else False,
        'needsReview': bool(att and (att.face_suspect or att.out_of_zone or att.out_of_window)),
        'checkInMapUrl': (
            'https://www.google.com/maps/search/?api=1&query=%s,%s'
            % (att.check_in_lat, att.check_in_lng)
            if att and att.check_in_lat and att.check_in_lng else None),
        'checkOutMapUrl': (
            'https://www.google.com/maps/search/?api=1&query=%s,%s'
            % (att.check_out_lat, att.check_out_lng)
            if att and att.check_out_lat and att.check_out_lng else None),
        'rowType': row_type,
        'shiftLabel': shift_label,
        'notes': att.notes if att else '',
        'attId': att.id if att else None,
    }


def _get_month_range(env, y, m):
    """Xác định khoảng [first, last] của tháng (y, m) dựa trên lịch sử cấu hình.
    Logic chống trùng lặp: last = (ngày bắt đầu của tháng sau) - 1 ngày."""
    ref_date = date(y, m, 1)
    # Tìm cấu hình áp dụng tại thời điểm đầu tháng đó
    history = env['hocba.attendance.period.history'].sudo().search([
        ('apply_from', '<=', ref_date)
    ], order='apply_from desc', limit=1)

    policy = env['hocba.attendance.policy'].sudo().get_policy()
    start_day = history.period_start_day if history else (policy.period_start_day or 1)

    # Tính ngày bắt đầu của tháng hiện tại (first)
    days_in_m = calendar.monthrange(y, m)[1]
    first = date(y, m, min(start_day, days_in_m))

    # Tính ngày bắt đầu của tháng tiếp theo để suy ra ngày kết thúc tháng này
    if m == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, m + 1

    days_in_nm = calendar.monthrange(ny, nm)[1]
    next_first = date(ny, nm, min(start_day, days_in_nm))

    # Ngày cuối cùng = Ngày đầu tháng sau - 1 ngày
    last = next_first - timedelta(days=1)

    return first, last


def _att_me_history(env, month_str, date_from=None, date_to=None):
    """Lịch sử chấm công của chính user theo tháng. None nếu chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    policy = env['hocba.attendance.policy'].sudo().get_policy()

    if date_from and date_to:
        first = fields.Date.from_string(date_from)
        last = fields.Date.from_string(date_to)
        y, m = first.year, first.month
    else:
        if month_str:
            y, m = (int(x) for x in month_str.split('-'))
        else:
            today = fields.Date.context_today(env.user)
            y, m = today.year, today.month
        first, last = _get_month_range(env, y, m)

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
    ot = _ot_for_employee(env, emp, first, last)
    summary = {
        'onTime': sum(1 for r in rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in rows if r['needsReview']),
        'daysPresent': len(rows),
        'totalHours': round(sum(r['workingHours'] for r in rows), 2),
        'totalCredit': round(total_credit + ot['otCong'], 2),
        'deficitCredit': deficit_credit,
        'netCredit': round(total_credit + ot['otCong'] - deficit_credit, 2),
        'violationDays': len(violations),
        'congOt': ot['otCong'],
        'otHours': ot['otHours'],
    }
    return {'month': '%04d-%02d' % (y, m), 'summary': summary, 'rows': rows}


def _att_me_history_full(env, month_str, att_type, date_from=None, date_to=None):
    """Lịch sử chấm công đầy đủ (thường + OT + CTV) theo filter.
    att_type: 'all' | 'regular' | 'ot' | 'ctv'. None nếu chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    policy = env['hocba.attendance.policy'].sudo().get_policy()

    if date_from and date_to:
        first = fields.Date.from_string(date_from)
        last = fields.Date.from_string(date_to)
        y, m = first.year, first.month
    else:
        if month_str:
            y, m = (int(x) for x in month_str.split('-'))
        else:
            today = fields.Date.context_today(env.user)
            y, m = today.year, today.month
        first, last = _get_month_range(env, y, m)

    # UTC bounds for shift searches
    tz = timezone(env.user.tz or 'UTC')
    start_dt_local = tz.localize(datetime.combine(first, time.min))
    end_dt_local = tz.localize(datetime.combine(last, time.max))
    start_utc = start_dt_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_dt_local.astimezone(utc).replace(tzinfo=None)

    # --- Regular rows ---
    regular_rows = []
    if att_type in ('regular', 'all'):
        recs = env['hocba.attendance'].sudo().search([
            ('employee_id', '=', emp.id),
            ('date', '>=', first), ('date', '<=', last),
        ], order='date desc')
        for r in recs:
            row = _att_row(r, policy)
            row['rowType'] = 'regular'
            row['shiftLabel'] = None
            regular_rows.append(row)

    # --- Shift rows (OT / CTV) ---
    ot_rows = []
    ctv_rows = []
    if att_type in ('ot', 'all'):
        shifts = env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'approved'),
            ('shift_type', '=', 'ot'),
            ('start', '>=', start_utc), ('start', '<', end_utc),
        ])
        for s in shifts:
            att = env['hocba.shift.attendance'].sudo().search(
                [('shift_id', '=', s.id)], limit=1)
            ot_rows.append(_shift_history_row(env, s, att or None, 'ot'))
    if att_type in ('ctv', 'all'):
        shifts = env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'approved'),
            ('shift_type', '=', 'ctv'),
            ('start', '>=', start_utc), ('start', '<', end_utc),
        ])
        for s in shifts:
            att = env['hocba.shift.attendance'].sudo().search(
                [('shift_id', '=', s.id)], limit=1)
            ctv_rows.append(_shift_history_row(env, s, att or None, 'ctv'))

    all_rows = sorted(
        regular_rows + ot_rows + ctv_rows,
        key=lambda r: r['date'] or '', reverse=True)

    # --- Summary ---
    total_credit = sum(r['workCredit'] for r in regular_rows)
    violations = sorted(
        [r for r in regular_rows if r['missingMinutes'] > 0],
        key=lambda r: r['date'])
    counted = violations[policy.violation_free_days:]
    std = policy.std_work_hours or 8.0
    deficit_credit = round(
        (sum(r['missingMinutes'] for r in counted) / 60.0) / std, 2)
    ot_hours = round(sum(r['workingHours'] for r in ot_rows if r['statusKey'] != 'none'), 2)
    cong_ot = round(sum(r['workCredit'] for r in ot_rows), 2)
    ctv_hours = round(sum(r['workingHours'] for r in ctv_rows if r['statusKey'] != 'none'), 2)
    cong_ctv = round(sum(r['workCredit'] for r in ctv_rows), 2)

    summary = {
        'daysPresent': len(regular_rows),
        'totalHours': round(sum(r['workingHours'] for r in regular_rows), 2),
        'totalCredit': round(total_credit, 2),
        'deficitCredit': deficit_credit,
        'netCredit': round(total_credit - deficit_credit, 2),
        'onTime': sum(1 for r in regular_rows if r['statusKey'] == 'on_time'),
        'late': sum(1 for r in regular_rows if r['statusKey'] == 'late'),
        'needsReview': sum(1 for r in regular_rows if r['needsReview']),
        'otHours': ot_hours,
        'congOt': cong_ot,
        'ctvHours': ctv_hours,
        'congCtv': cong_ctv,
    }
    return {
        'month': '%04d-%02d' % (y, m),
        'employmentStatus': emp.x_employment_status or 'official',
        'summary': summary,
        'rows': all_rows,
    }


def _att_manager_summary(env, month_str, date_from=None, date_to=None, role=None):
    """Tổng hợp chấm công theo tháng cho manager: 1 dòng/NV trong phạm vi quản lý.
    Cột: tổng công thường, OT, thiếu, tổng tháng.
    role: 'official' | 'teacher' | 'ctv' | 'all'."""
    if not _user_can_manage(env):
        raise AccessError('Không có quyền')

    if date_from and date_to:
        first = fields.Date.from_string(date_from)
        last = fields.Date.from_string(date_to)
        y, m = first.year, first.month
    else:
        if month_str:
            y, m = (int(x) for x in month_str.split('-'))
        else:
            today = fields.Date.context_today(env.user)
            y, m = today.year, today.month
        first, last = _get_month_range(env, y, m)

    tz = timezone(env.user.tz or 'UTC')
    start_dt_local = tz.localize(datetime.combine(first, time.min))
    end_dt_local = tz.localize(datetime.combine(last, time.max))
    start_utc = start_dt_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_dt_local.astimezone(utc).replace(tzinfo=None)

    policy = env['hocba.attendance.policy'].sudo().get_policy()
    emp_domain = _emp_scope_domain(env)

    if role == 'official':
        emp_domain.append(('x_employment_status', '=', 'official'))
    elif role == 'teacher':
        emp_domain.append(('x_cms_user_id', '!=', False))
    elif role == 'ctv':
        # CTV: không phải official và không phải teacher
        emp_domain.append(('x_employment_status', '!=', 'official'))
        emp_domain.append(('x_cms_user_id', '=', False))

    employees = env['hr.employee'].sudo().search(
        emp_domain, order='department_id, name')

    rows = []
    for emp in employees:
        att_recs = env['hocba.attendance'].sudo().search([
            ('employee_id', '=', emp.id),
            ('date', '>=', first), ('date', '<=', last),
        ])
        att_rows = [_att_row(r, policy) for r in att_recs]
        total_regular = round(sum(r['workCredit'] for r in att_rows), 2)

        violations = sorted(
            [r for r in att_rows if r['missingMinutes'] > 0],
            key=lambda r: r['date'])
        counted_v = violations[policy.violation_free_days:]
        std = policy.std_work_hours or 8.0
        deficit = round(
            (sum(r['missingMinutes'] for r in counted_v) / 60.0) / std, 2)

        ot = _ot_for_employee(env, emp, first, last)

        # CTV cong
        ctv_shifts = env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'approved'),
            ('shift_type', '=', 'ctv'),
            ('start', '>=', start_utc), ('start', '<', end_utc),
        ])
        ctv_cong = 0.0
        for s in ctv_shifts:
            att_s = env['hocba.shift.attendance'].sudo().search(
                [('shift_id', '=', s.id)], limit=1)
            if att_s and att_s.check_in:
                hours = att_s.worked_hours or 0.0
                ctv_cong += round((hours / 8.0) * (s.rate or 1.0), 2)
        ctv_cong = round(ctv_cong, 2)

        rows.append({
            'empId': emp.id,
            'empName': emp.name,
            'code': emp.x_employee_code or '—',
            'depId': emp.department_id.id if emp.department_id else None,
            'depName': emp.department_id.name or 'Chưa gán',
            'totalRegular': total_regular,
            'totalOt': ot['otCong'],
            'totalCtv': ctv_cong,
            'totalMissing': deficit,
            'totalMonth': round(total_regular + ot['otCong'] + ctv_cong, 2),
        })

    return {
        'month': '%04d-%02d' % (y, m),
        'rows': rows,
    }


def _att_emp_history(env, emp_id, month_str, att_type, date_from=None, date_to=None):
    """Lịch sử chấm công đầy đủ cho 1 NV cụ thể (manager xem/sửa).
    att_type: 'all' | 'regular' | 'ot' | 'ctv'. Kiểm tra phạm vi quản lý."""
    if not _user_can_manage(env):
        raise AccessError('Không có quyền')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists():
        raise UserError('Nhân viên không tồn tại')
    if not _emp_in_scope(env, emp):
        raise AccessError('Ngoài phạm vi quản lý')

    policy = env['hocba.attendance.policy'].sudo().get_policy()

    if date_from and date_to:
        first = fields.Date.from_string(date_from)
        last = fields.Date.from_string(date_to)
        y, m = first.year, first.month # fallbacks for legacy datetime calculations below
    else:
        if month_str:
            y, m = (int(x) for x in month_str.split('-'))
        else:
            today = fields.Date.context_today(env.user)
            y, m = today.year, today.month
        first = date(y, m, 1)
        last = date(y, m, calendar.monthrange(y, m)[1])

    tz = timezone(env.user.tz or 'UTC')
    start_local = tz.localize(datetime(first.year, first.month, first.day))
    end_local = tz.localize(datetime(last.year, last.month, last.day, 23, 59, 59))
    start_utc = start_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(utc).replace(tzinfo=None)

    regular_rows = []
    if att_type in ('regular', 'all'):
        recs = env['hocba.attendance'].sudo().search([
            ('employee_id', '=', emp.id),
            ('date', '>=', first), ('date', '<=', last),
        ], order='date desc')
        for r in recs:
            row = _att_row(r, policy)
            row['rowType'] = 'regular'
            row['shiftLabel'] = None
            regular_rows.append(row)

    ot_rows = []
    if att_type in ('ot', 'all'):
        shifts = env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'approved'),
            ('shift_type', '=', 'ot'),
            ('start', '>=', start_utc), ('start', '<', end_utc),
        ])
        for s in shifts:
            att = env['hocba.shift.attendance'].sudo().search(
                [('shift_id', '=', s.id)], limit=1)
            ot_rows.append(_shift_history_row(env, s, att or None, 'ot'))

    ctv_rows = []
    if att_type in ('ctv', 'all'):
        shifts = env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'approved'),
            ('shift_type', '=', 'ctv'),
            ('start', '>=', start_utc), ('start', '<', end_utc),
        ])
        for s in shifts:
            att = env['hocba.shift.attendance'].sudo().search(
                [('shift_id', '=', s.id)], limit=1)
            ctv_rows.append(_shift_history_row(env, s, att or None, 'ctv'))

    all_rows = sorted(
        regular_rows + ot_rows + ctv_rows,
        key=lambda r: r['date'] or '', reverse=True)

    total_credit = sum(r['workCredit'] for r in regular_rows)
    violations = sorted(
        [r for r in regular_rows if r['missingMinutes'] > 0],
        key=lambda r: r['date'])
    counted_v = violations[policy.violation_free_days:]
    std = policy.std_work_hours or 8.0
    deficit = round(
        (sum(r['missingMinutes'] for r in counted_v) / 60.0) / std, 2)
    ot_hours = round(sum(r['workingHours'] for r in ot_rows if r['statusKey'] != 'none'), 2)
    cong_ot = round(sum(r['workCredit'] for r in ot_rows), 2)
    ctv_hours = round(sum(r['workingHours'] for r in ctv_rows if r['statusKey'] != 'none'), 2)
    cong_ctv = round(sum(r['workCredit'] for r in ctv_rows), 2)

    summary = {
        'daysPresent': len(regular_rows),
        'totalHours': round(sum(r['workingHours'] for r in regular_rows), 2),
        'totalCredit': round(total_credit, 2),
        'deficitCredit': deficit,
        'netCredit': round(total_credit - deficit, 2),
        'otHours': ot_hours,
        'congOt': cong_ot,
        'ctvHours': ctv_hours,
        'congCtv': cong_ctv,
    }
    return {
        'month': '%04d-%02d' % (y, m),
        'emp': {
            'id': emp.id, 'name': emp.name,
            'code': emp.x_employee_code or '—',
            'depName': emp.department_id.name or 'Chưa gán',
        },
        'summary': summary,
        'rows': all_rows,
    }


def _req_row(req):
    """Một đơn chấm công cho SPA (wire format camelCase)."""
    emp = req.employee_id
    return {
        'id': req.id,
        'empId': emp.id,
        'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'requestDate': _d(req.request_date),
        'attendanceId': req.attendance_id.id or None,
        'checkIn': _dt_local(req, req.proposed_check_in),
        'checkOut': _dt_local(req, req.proposed_check_out),
        'reason': req.reason or '',
        'state': req.state,
        'reviewer': req.reviewer_id.name or None,
        'reviewNote': req.review_note or None,
        'decisionDate': _dt_local(req, req.decision_date),
    }


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


def _request_apply(env, req, check_in_utc, check_out_utc):
    """Áp đơn đã duyệt vào bản ghi chấm công (Gói 3). Trả bản ghi.
    check_in_utc/check_out_utc: Datetime UTC naive, hoặc None để bỏ qua (giờ đó
    giữ nguyên). Người gọi (_request_decide) chuẩn hóa False -> None trước khi
    truyền, nên None là giá trị "không cung cấp" chính thức.
    - Có attendance_id (hoặc tìm thấy bản ghi cùng ngày): chỉ ghi giờ khác None.
    - Ngày thiếu (không bản ghi): cần check_in_utc để tạo; thiếu -> ValidationError."""
    Att = env['hocba.attendance'].sudo()
    rec = req.attendance_id
    if not rec:
        rec = Att.search([
            ('employee_id', '=', req.employee_id.id),
            ('date', '=', req.request_date),
        ], limit=1)
    if rec:
        vals = {}
        if check_in_utc is not None:
            vals['check_in'] = check_in_utc
        if check_out_utc is not None:
            vals['check_out'] = check_out_utc
        if vals:
            rec.write(vals)
    else:
        if not check_in_utc:
            raise ValidationError('Cần giờ check-in để tạo bản ghi.')
        rec = Att.create({
            'employee_id': req.employee_id.id,
            'check_in': check_in_utc,
            'check_out': check_out_utc or False,
        })
    req.attendance_id = rec
    return rec


def _request_create(env, body):
    """User tạo đơn chấm công cho CHÍNH MÌNH (pin employee, chống giả mạo).
    Trả _req_row; None nếu user chưa có hồ sơ NV; ValidationError nếu thiếu lý
    do / bản ghi đính kèm không thuộc về user."""
    emp = env.user.employee_id
    if not emp:
        return None
    reason = (body.get('reason') or '').strip()
    if not reason:
        raise ValidationError('Cần lý do.')
    Att = env['hocba.attendance'].sudo()
    att_id = body.get('attendanceId') or None
    attendance = Att.browse(int(att_id)) if att_id else Att.browse()
    if not att_id or not attendance.exists() or attendance.employee_id != emp:
        raise ValidationError('Bản ghi không hợp lệ.')
    # --- Auto-approve first 2 requests per month ---
    today = fields.Date.context_today(env.user)
    first_of_month = today.replace(day=1)
    last_of_month = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    # Count requests created by this employee in the current month
    request_count = env['hocba.attendance.request'].sudo().search_count([
        ('employee_id', '=', emp.id),
        ('create_date', '>=', fields.Datetime.to_string(datetime.combine(first_of_month, time.min))),
        ('create_date', '<=', fields.Datetime.to_string(datetime.combine(last_of_month, time.max))),
    ])

    req_vals = {
        'employee_id': emp.id,
        'request_date': attendance.date,
        'attendance_id': attendance.id,
        'proposed_check_in': _to_utc(env, body.get('checkIn')),
        'proposed_check_out': _to_utc(env, body.get('checkOut')),
        'reason': reason,
    }

    if request_count < 2:
        # Auto-approve
        req_vals.update({
            'state': 'approved',
            'review_note': 'Hệ thống tự động duyệt (2 lần đầu trong tháng).',
            'decision_date': fields.Datetime.now(),
        })
        req = env['hocba.attendance.request'].sudo().create(req_vals)
        # Apply the changes to attendance record
        _request_apply(env, req, req.proposed_check_in, req.proposed_check_out)
    else:
        req = env['hocba.attendance.request'].sudo().create(req_vals)

    return _req_row(req)


def _request_decide(env, req_id, approve, body):
    """Manager duyệt/từ chối 1 đơn trong phạm vi (Gói 3).
    Trả _req_row; None nếu không tồn tại; AccessError nếu vượt quyền;
    UserError('already_decided') nếu đơn đã quyết định.
    Khi duyệt: giờ áp dụng = body override (nếu gửi) ELSE proposed_* của đơn."""
    req = env['hocba.attendance.request'].sudo().browse(req_id)
    if not req.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, req.employee_id)):
        raise AccessError('forbidden')
    if req.state != 'pending':
        raise UserError('already_decided')
    vals = {
        'reviewer_id': env.user.id,
        'decision_date': fields.Datetime.now(),
        'review_note': (body.get('reviewNote') or '').strip() or False,
    }
    if approve:
        ci = _to_utc(env, body['checkIn']) if 'checkIn' in body else req.proposed_check_in
        co = _to_utc(env, body['checkOut']) if 'checkOut' in body else req.proposed_check_out
        _request_apply(env, req, ci or None, co or None)
        vals['state'] = 'approved'
    else:
        vals['state'] = 'rejected'
    req.write(vals)
    return _req_row(req)


def _request_preview(env, req_id, body):
    """Tính thử (dry-run) các trường công khi áp giờ đề xuất, KHÔNG lưu.
    Manager xem trước khi duyệt. AccessError nếu vượt quyền; None nếu không tồn tại."""
    req = env['hocba.attendance.request'].sudo().browse(req_id)
    if not req.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, req.employee_id)):
        raise AccessError('forbidden')
    ci = _to_utc(env, body['checkIn']) if 'checkIn' in body else req.proposed_check_in
    co = _to_utc(env, body['checkOut']) if 'checkOut' in body else req.proposed_check_out
    draft = env['hocba.attendance'].sudo().new({
        'employee_id': req.employee_id.id,
        'check_in': ci or False,
        'check_out': co or False,
    })
    return {
        'workingHours': round(draft.working_hours, 2),
        'workCredit': draft.work_credit,
        'expectedCheckOut': _dt_local(draft, draft.expected_check_out),
        'earlyLeaveMinutes': draft.early_leave_minutes,
        'missingMinutes': draft.missing_minutes,
        'lateMinutes': draft.late_minutes,
        'needsReview': draft.needs_review,
    }


def _att_requests_mine(env):
    """Đơn chấm công của chính user (mọi state), mới nhất trước.
    None nếu user chưa có hồ sơ NV."""
    emp = env.user.employee_id
    if not emp:
        return None
    reqs = env['hocba.attendance.request'].sudo().search(
        [('employee_id', '=', emp.id)])
    return [_req_row(r) for r in reqs]


def _att_requests_pending(env):
    """Đơn đang chờ duyệt trong phạm vi vai trò của manager. [] nếu không phải
    manager. Áp _emp_scope_domain lên employee_id (prefix như bảng ngày Gói 2)."""
    if not _user_can_manage(env):
        return []
    domain = [('state', '=', 'pending')]
    for field, op, val in _emp_scope_domain(env):
        if field == 'id':            # ('id','=',0): không thuộc nhóm nào
            domain.append(('employee_id', op, val))
        else:
            domain.append(('employee_id.%s' % field, op, val))
    reqs = env['hocba.attendance.request'].sudo().search(domain)
    return [_req_row(r) for r in reqs]


def _employee_search(env, q):
    """Tìm NV theo mã (x_employee_code) hoặc tên cho manager (add-for-anyone).
    [] nếu không phải manager hoặc query rỗng. Giới hạn theo phạm vi vai trò."""
    if not _user_can_manage(env):
        return []
    q = (q or '').strip()
    if not q:
        return []
    domain = ['|', ('x_employee_code', 'ilike', q), ('name', 'ilike', q)]
    domain += _emp_scope_domain(env)
    emps = env['hr.employee'].sudo().search(domain, limit=20)
    return [{
        'id': e.id,
        'code': e.x_employee_code or '—',
        'name': e.name,
        'employmentStatus': e.x_employment_status or '',
    } for e in emps]


def _shift_scope_domain(env, type_filter=None):
    """Domain trên hocba.work_shift theo người xem (Section 2 spec).
    - Manager: theo _emp_scope_domain (dịch sang employee_id.*) + lọc loại nếu gửi.
    - CTV (x_employment_status='ctv'): chỉ thấy ca CTV (của mọi người).
    - NV thường: chỉ thấy ca OT (của mọi người)."""
    if _user_can_manage(env):
        dom = []
        for field, op, val in _emp_scope_domain(env):
            if field == 'id':
                dom.append(('employee_id', op, val))
            else:
                dom.append(('employee_id.%s' % field, op, val))
        if type_filter in ('ot', 'ctv'):
            dom.append(('shift_type', '=', type_filter))
        return dom
    emp = env.user.employee_id
    is_official = bool(emp) and emp.x_employment_status == 'official'
    return [('shift_type', '=', 'ot' if is_official else 'ctv')]


def _shift_row(s):
    """Một ca làm việc cho SPA (wire format camelCase)."""
    emp = s.employee_id
    return {
        'id': s.id,
        'empId': emp.id,
        'empName': emp.name,
        'code': emp.x_employee_code or '—',
        'depName': emp.department_id.name or 'Chưa gán',
        'start': _dt_local(s, s.start),
        'end': _dt_local(s, s.end),
        'shiftType': s.shift_type,
        'shiftTypeLabel': 'CTV' if s.shift_type == 'ctv' else 'OT',
        'deadline': _dt_local(s, s.deadline),
        'locked': bool(s.deadline) and fields.Datetime.now() >= s.deadline,
        'mine': bool(s.env.user.employee_id) and s.employee_id.id == s.env.user.employee_id.id,
        'otLevel': s.ot_level,
        'rate': s.rate,
        'state': s.state,
        'reason': s.reason or '',
        'reviewer': s.reviewer_id.name or None,
        'reviewNote': s.review_note or None,
        'decisionDate': _dt_local(s, s.decision_date),
        'checkIn': _dt_local(s, s.attendance_id[0].check_in) if s.attendance_id else None,
        'checkOut': _dt_local(s, s.attendance_id[0].check_out) if s.attendance_id else None,
        'notes': s.attendance_id[0].notes if s.attendance_id else None,
    }


def _shift_create(env, body):
    """Đăng ký ca. Mặc định pin về user (state=pending). Nếu người gọi là
    manager và gửi empId thuộc phạm vi → tạo hộ NV đó (state=approved).
    Trả _shift_row; None nếu user chưa có hồ sơ NV; ValidationError nếu dữ liệu sai."""
    Shift = env['hocba.work_shift'].sudo()
    emp_id = body.get('empId')
    as_manager = bool(emp_id) and _user_can_manage(env)
    if as_manager:
        emp = env['hr.employee'].sudo().browse(int(emp_id))
        if not emp.exists() or not _emp_in_scope(env, emp):
            raise ValidationError('Nhân viên ngoài phạm vi.')
    else:
        emp = env.user.employee_id
        if not emp:
            return None
    shift_type = body.get('shiftType')
    if shift_type not in ('ctv', 'ot'):
        raise ValidationError('Loại ca không hợp lệ.')
    level = body.get('otLevel') or '100'
    if level not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    if shift_type == 'ctv':
        level = '100'   # CTV cố định 100%, bỏ qua giá trị client gửi
    start = _to_utc(env, body.get('start'))
    end = _to_utc(env, body.get('end'))
    if not start or not end:
        raise ValidationError('Cần giờ bắt đầu và kết thúc.')
    vals = {
        'employee_id': emp.id,
        'start': start, 'end': end,
        'shift_type': shift_type,
        'ot_level': level,
        'reason': (body.get('reason') or '').strip() or False,
    }
    if as_manager:
        vals.update({'state': 'approved', 'reviewer_id': env.user.id,
                     'decision_date': fields.Datetime.now()})
    shift = Shift.create(vals)
    return _shift_row(shift)


def _shifts_week(env, monday_str, type_filter=None):
    """Dữ liệu lịch tuần (T2→CN của tuần chứa monday_str; rỗng = tuần hiện tại).
    Visibility theo loại ca: NV thường thấy ca OT của mọi người; CTV thấy ca CTV;
    Manager thấy ca theo phạm vi + filter loại tuỳ chọn."""
    user = env.user
    d = fields.Date.from_string(monday_str) if monday_str else fields.Date.context_today(user)
    monday = d - timedelta(days=d.weekday())
    tz = timezone(user.tz or 'UTC')
    start_local = tz.localize(datetime(monday.year, monday.month, monday.day))
    end_local = start_local + timedelta(days=7)
    start_utc = start_local.astimezone(utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(utc).replace(tzinfo=None)
    can_manage = _user_can_manage(env)
    scope = _shift_scope_domain(env, type_filter)
    env['hocba.work_shift'].sudo()._auto_reject_expired(scope)  # lazy backstop (Section 3)
    me = user.employee_id
    if can_manage:
        visible = scope
    else:
        # NV thường/CTV: CHỈ thấy ca của chính mình (thuộc loại ca tương ứng)
        visible = scope + [('employee_id', '=', me.id if me else -1)]
    domain = [('start', '>=', start_utc), ('start', '<', end_utc)] + visible
    recs = env['hocba.work_shift'].sudo().search(domain)
    by_day = {}
    for s in recs:
        local = fields.Datetime.context_timestamp(s, s.start)
        by_day.setdefault(local.date(), []).append(_shift_row(s))
    weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
    days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        days.append({'date': _d(day), 'weekday': weekdays[i],
                     'shifts': by_day.get(day, [])})
    return {'weekStart': _d(monday), 'canManage': can_manage, 'days': days}


def _shift_decide(env, shift_id, approve, body):
    """Manager duyệt/từ chối 1 ca trong phạm vi (Gói 4A). Khi duyệt: override
    được start/end/shiftType/rate (nếu body gửi). Trả _shift_row; None nếu không
    tồn tại; AccessError nếu vượt quyền; UserError('already_decided') nếu đã quyết định."""
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)):
        raise AccessError('forbidden')
    if shift.state == 'rejected':
        raise UserError('already_decided')
    shift._assert_actionable()
    vals = {
        'reviewer_id': env.user.id,
        'decision_date': fields.Datetime.now(),
        'review_note': (body.get('reviewNote') or '').strip() or False,
    }
    if approve:
        if 'start' in body:
            vals['start'] = _to_utc(env, body['start'])
        if 'end' in body:
            vals['end'] = _to_utc(env, body['end'])
        if 'shiftType' in body:
            if body['shiftType'] not in ('ctv', 'ot'):
                raise ValidationError('Loại ca không hợp lệ.')
            vals['shift_type'] = body['shiftType']
        if 'otLevel' in body:
            if body['otLevel'] not in ('100', '150', '300'):
                raise ValidationError('Mức hệ số không hợp lệ.')
            vals['ot_level'] = body['otLevel']
        vals['state'] = 'approved'
    else:
        vals['state'] = 'rejected'
    shift.write(vals)
    return _shift_row(shift)


def _shift_set_level(env, shift_id, level):
    """Manager (trong phạm vi) đổi mốc hệ số 1 ca approved (màn Chấm công OT).
    Trả _shift_row; None nếu không tồn tại; AccessError nếu vượt quyền;
    ValidationError nếu mốc sai / ca không ở trạng thái approved."""
    if level not in ('100', '150', '300'):
        raise ValidationError('Mức hệ số không hợp lệ.')
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id)):
        raise AccessError('forbidden')
    shift._assert_actionable()
    if shift.state != 'approved':
        raise ValidationError('Chỉ đổi mức cho ca đã duyệt.')
    if shift.shift_type == 'ctv':
        raise ValidationError('Ca CTV cố định hệ số 100%.')
    shift.write({'ot_level': level})
    return _shift_row(shift)


def _shift_cancel(env, shift_id):
    """Hủy ca PENDING. Quyền: owner của ca hoặc manager trong phạm vi.
    Trả {'ok':True}; None nếu không tồn tại; AccessError nếu vượt quyền;
    UserError('only_pending') nếu ca không còn pending."""
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        return None
    me = env.user.employee_id
    is_owner = bool(me) and shift.employee_id == me
    if not (is_owner or (_user_can_manage(env) and _emp_in_scope(env, shift.employee_id))):
        raise AccessError('forbidden')
    shift._assert_actionable()
    if shift.state != 'pending':
        raise UserError('only_pending')
    shift.unlink()
    return {'ok': True}


def _shift_today_rows(env, emp):
    """Ca approved hôm nay của emp (local) + trạng thái chấm cho màn chấm công ca."""
    policy = env['hocba.attendance.policy'].sudo().get_policy()
    window = policy.shift_window_minutes or 15
    now_local = fields.Datetime.context_timestamp(
        env.user, fields.Datetime.now()).replace(tzinfo=None)
    today = now_local.date()
    shifts = env['hocba.attendance']._todays_approved_shifts(emp, today)
    rows = []
    for s in shifts:
        att = env['hocba.shift.attendance'].sudo().search(
            [('shift_id', '=', s.id)], limit=1)
        ci_anchor = fields.Datetime.context_timestamp(s, s.start).replace(tzinfo=None)
        co_anchor = fields.Datetime.context_timestamp(s, s.end).replace(tzinfo=None)
        has_in = bool(att and att.check_in)
        has_out = bool(att and att.check_out)
        rows.append({
            'id': s.id,
            'start': _dt_local(s, s.start), 'end': _dt_local(s, s.end),
            'shiftType': s.shift_type, 'otLevel': s.ot_level, 'rate': s.rate,
            'checkIn': _dt_local(att, att.check_in) if has_in else None,
            'checkOut': _dt_local(att, att.check_out) if has_out else None,
            'checkInOpen': not has_in,
            'checkOutOpen': has_in and not has_out,
            'faceSuspect': att.face_suspect if att else False,
            'outOfZone': att.out_of_zone if att else False,
            'outOfWindow': att.out_of_window if att else False,
            'notes': att.notes if att else None,
        })
    return rows


def _shift_check(env, shift_id, kind, payload):
    """Chấm công 1 ca cho user hiện tại. Raise AccessError nếu ca không thuộc user."""
    emp = env.user.employee_id
    shift = env['hocba.work_shift'].sudo().browse(shift_id)
    if not shift.exists():
        raise UserError('no_shift')
    if not emp or shift.employee_id.id != emp.id:
        raise AccessError('forbidden')
    SA = env['hocba.shift.attendance'].sudo()
    SA._assert_allowed(shift, kind, has_note=bool(payload.get('note')))
    rec = SA._do_check(shift, payload, kind)
    return {
        'recordId': rec.id, 'kind': kind,
        'faceSuspect': rec.face_suspect, 'outOfZone': rec.out_of_zone,
        'outOfWindow': rec.out_of_window,
        'faceScore': (rec.check_in_face_score if kind == 'in'
                      else rec.check_out_face_score),
    }


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


def _cap_edit_emp(env):
    """Được tạo/sửa/xoá hồ sơ NV + hồ sơ con (trong phạm vi). = tập quản lý:
    Admin | HR | HR-Mgr | Giáo vụ | Trưởng phòng."""
    return _user_can_manage(env)


def _cap_see_salary(env):
    """Được XEM lương cơ bản: Admin | HR-Mgr | Giáo vụ | Trưởng phòng.
    (HR officer KHÔNG xem lương — giữ nguyên.)"""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager')
            or user.has_group('hocba_employees.group_hocba_giaovu')
            or _is_dept_manager(env, user.employee_id))


def _cap_edit_salary(env):
    """Được SỬA mức lương: Admin | HR-Mgr."""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager'))


def _cap_manage_account(env):
    """Quản lý tài khoản đăng nhập: Admin | HR | HR-Mgr."""
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_user')
            or user.has_group('hr.group_hr_manager'))


def _cap_edit_dept(env):
    """Được THÊM/SỬA/LƯU TRỮ phòng ban: Admin | HR-Mgr. HR officer chỉ XEM.

    Chốt 2026-08-15: sửa phòng ban là đổi cơ cấu tổ chức, kèm theo đó là đổi
    manager_id — tức nguồn quyền "trưởng phòng" của cả hệ (_emp_scope_domain).
    Việc đó vượt tầm HR officer.

    Lưu ý khi đọc: KHÔNG chặn bằng cách gỡ hr.group_hr_user, vì HR Manager
    cũng mang nhóm đó (Odoo chuẩn: group_hr_manager implies group_hr_user) —
    gỡ là chặn nhầm cả HR Manager. Phải kiểm ở tầng cao hơn như dưới đây.
    """
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager'))


def _cap_view_dept(env):
    """Được XEM danh sách phòng ban: HR officer trở lên, + Admin.

    Admin phải kể riêng: tài khoản admin "thuần" (base.group_system, không kèm
    nhóm HR nào — đúng dạng test_admin@hocba.vn trong DB) không có
    hr.group_hr_user, trong khi nav vẫn bày menu Phòng ban cho Admin
    (Shell.jsx: need 'hr' = isHrUser | isHrManager | isAdmin) → chặn ở đây là
    403 giữa mặt.
    """
    return _is_hr(env) or _cap_edit_dept(env)


# --- Quản lý tài khoản đăng nhập (account management) --------------------
ACCOUNT_ROLES = ('employee', 'giaovu', 'truongphong')
MIN_PASSWORD_LEN = 8


def _account_payload(emp):
    """Khối trạng thái tài khoản đăng nhập cho hồ sơ NV."""
    u = emp.user_id
    if not u:
        return {'hasAccount': False}
    return {'hasAccount': True, 'login': u.login, 'active': u.active}


def _is_hr(env):
    return env.user.has_group('hr.group_hr_user')


def _validate_password(body):
    pw = body.get('password') or ''
    pw2 = body.get('password_confirm') or ''
    if len(pw) < MIN_PASSWORD_LEN:
        raise ValidationError(
            'Mật khẩu phải có ít nhất %d ký tự.' % MIN_PASSWORD_LEN)
    if pw != pw2:
        raise ValidationError('Xác nhận mật khẩu không khớp.')
    return pw


def _account_create(env, emp_id, body):
    """HR/Admin cấp tài khoản đăng nhập cho 1 nhân viên.
    AccessError nếu không phải HR; ValidationError nếu dữ liệu sai;
    UserError nếu trưởng phòng cần xác nhận ghi đè."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được cấp tài khoản.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists():
        raise ValidationError('Không tìm thấy nhân viên.')
    if emp.user_id:
        raise ValidationError('Nhân viên đã có tài khoản. Dùng cấp lại mật khẩu.')
    login = (body.get('login') or '').strip()
    if not login:
        raise ValidationError('Vui lòng nhập tên đăng nhập.')
    if env['res.users'].sudo().with_context(active_test=False).search_count(
            [('login', '=', login)]):
        raise ValidationError('Tên đăng nhập đã tồn tại.')
    password = _validate_password(body)
    role = body.get('role') or 'employee'
    if role not in ACCOUNT_ROLES:
        raise ValidationError('Loại tài khoản không hợp lệ.')

    group_ids = [env.ref('base.group_user').id]
    if role == 'giaovu':
        group_ids.append(env.ref('hocba_employees.group_hocba_giaovu').id)

    dept = None
    if role == 'truongphong':
        dept_id = body.get('department_id')
        if not dept_id:
            raise ValidationError('Trưởng phòng cần chọn phòng ban.')
        dept = env['hr.department'].sudo().browse(int(dept_id))
        if not dept.exists():
            raise ValidationError('Phòng ban không hợp lệ.')
        if (dept.manager_id and dept.manager_id != emp
                and not body.get('confirm_overwrite')):
            raise UserError(
                'Phòng "%s" đã có trưởng phòng (%s). Xác nhận để ghi đè.'
                % (dept.name, dept.manager_id.name))

    user = env['res.users'].sudo().create({
        'name': emp.name, 'login': login, 'password': password,
        'group_ids': [(6, 0, group_ids)],
    })
    emp.sudo().user_id = user.id
    if dept is not None:
        dept.manager_id = emp.id
    return _account_payload(emp)


def _account_reset(env, emp_id, body):
    """HR/Admin cấp lại mật khẩu cho nhân viên đã có tài khoản."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được cấp lại mật khẩu.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists() or not emp.user_id:
        raise ValidationError('Nhân viên chưa có tài khoản.')
    password = _validate_password(body)
    emp.user_id.sudo().write({'password': password})
    return _account_payload(emp)


def _me_change_password(env, body):
    """Người đang đăng nhập TỰ đổi mật khẩu (mọi vai trò, kể cả HR/Admin).

    Bắt nhập mật khẩu hiện tại: không có nó thì bất kỳ ai mượn được phiên đăng
    nhập đang mở đều đổi được mật khẩu và chiếm luôn tài khoản. Đường HR cấp
    lại (_account_reset) vẫn giữ riêng — chỉ dùng khi nhân viên QUÊN mật khẩu.

    Lưu ý: đổi mật khẩu làm session_token của Odoo đổi theo → phiên hiện tại
    hết hiệu lực. FE phải đá người dùng về màn đăng nhập sau khi gọi hàm này.
    """
    current = body.get('currentPassword') or ''
    if not current:
        raise ValidationError('Vui lòng nhập mật khẩu hiện tại.')
    password = _validate_password(body)
    if password == current:
        raise ValidationError('Mật khẩu mới phải khác mật khẩu hiện tại.')
    try:
        # change_password tự kiểm mật khẩu cũ (AccessDenied nếu sai) rồi ghi
        # mật khẩu mới cho chính env.user — không sudo, không nhận uid từ body.
        env['res.users'].change_password(current, password)
    except AccessDenied:
        raise ValidationError('Mật khẩu hiện tại không đúng.')
    return {'ok': True, 'relogin': True}


def _account_set_active(env, emp_id, active):
    """HR/Admin khóa (active=False) / mở khóa tài khoản đăng nhập.

    Dùng thẳng res.users.active — Odoo tự chặn đăng nhập, và offboarding
    cũng ghi vào đúng field này khi hoàn tất nghỉ việc. browse()/exists()
    vốn đã thấy được cả bản ghi archived (chỉ search() mới cần
    active_test=False), nên không cần set context riêng ở đây."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được khóa/mở tài khoản.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists():
        raise ValidationError('Không tìm thấy nhân viên.')
    if not emp.user_id:
        raise ValidationError('Nhân viên chưa có tài khoản.')
    user = emp.user_id
    if user.id == env.user.id:
        raise ValidationError(
            'Không thể khóa tài khoản của chính bạn.')
    if user.id == SUPERUSER_ID or user.sudo().has_group('base.group_system'):
        raise ValidationError(
            'Tài khoản quản trị hệ thống không quản lý được từ đây.')
    if active and not emp.active:
        raise ValidationError(
            'Nhân viên đã nghỉ việc — không mở lại tài khoản từ đây. '
            'Nếu tuyển lại, khôi phục hồ sơ nhân viên trước.')
    if user.active != bool(active):
        user.sudo().write({'active': bool(active)})
        emp.sudo().message_post(
            body=('🔓 %s đã mở khóa tài khoản đăng nhập.' if active
                  else '🔒 %s đã khóa tài khoản đăng nhập.') % env.user.name,
            subtype_xmlid='mail.mt_note')
    return _account_payload(emp)


def _account_list(env):
    """Danh sách NV đã có tài khoản + danh mục phòng ban (cho form). Chỉ HR."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được xem danh sách tài khoản.')
    Dept = env['hr.department'].sudo()
    # active_test=False: NV đã nghỉ bị archive nhưng tài khoản của họ vẫn
    # phải rà soát được (nhóm bị khóa đông nhất).
    emps = env['hr.employee'].sudo().with_context(active_test=False).search(
        [('user_id', '!=', False)], order='x_employee_code, id')
    # Lấy 1 lần, dùng lại cho cả role (trưởng phòng?) lẫn danh mục trả về —
    # tránh N+1 search_count trên mỗi nhân viên (DB Neon: mỗi round-trip
    # ~10-30ms). Chỉ tính phòng ban đang active, giữ đúng ngữ nghĩa cũ của
    # Dept.search_count/Dept.search([]).
    all_depts = Dept.search([], order='name')
    manager_emp_ids = set(all_depts.mapped('manager_id').ids)
    rows = []
    for e in emps:
        u = e.user_id
        is_tp = e.id in manager_emp_ids
        is_gv = u.has_group('hocba_employees.group_hocba_giaovu')
        role = 'truongphong' if is_tp else ('giaovu' if is_gv else 'employee')
        rows.append({
            'employeeId': e.id, 'name': e.name,
            'code': e.x_employee_code or '',
            'depId': e.department_id.id or 0,
            'depName': e.department_id.name or '',
            'login': u.login, 'active': u.active, 'role': role,
            'empActive': e.active,
            # _account_set_active từ chối đụng tài khoản quản trị hệ thống →
            # FE ẩn nút thay vì bày ra chỉ để báo lỗi.
            'isSystem': u.id == SUPERUSER_ID or u.has_group(
                'base.group_system'),
        })
    depts = [{'id': d.id, 'name': d.name} for d in all_depts]
    return {'accounts': rows, 'departments': depts}


# ----------------------------------------------------------------------
# Trang Lộ trình sự nghiệp (ý C họp 2026-08-07) — khách: "dashboard thống
# kê cho từng người… đầy đủ thông tin, cả nhận xét… chứ không phải là theo
# kiểu phải click nhiều". Gộp 4 nguồn có sẵn thành MỘT dòng thời gian.
# Spec: docs/superpowers/specs/
# 2026-08-09-career-dashboard-honor-board-design.md §4
# ----------------------------------------------------------------------
VERDICT_LABELS = {'qualified': 'Đủ điều kiện', 'consider': 'Cân nhắc',
                  'not_yet': 'Chưa đủ'}
ONB_RESULT_LABELS = {'pass': 'Đạt', 'extend': 'Gia hạn', 'fail': 'Không đạt'}


def _career_resolve(env, emp_id):
    """Trả (emp, is_self) sau khi kiểm quyền. emp_id=0 → chính mình."""
    me = env.user.employee_id
    if not emp_id:
        if not me:
            raise ValidationError(
                'Tài khoản của bạn chưa được gắn với hồ sơ nhân viên nào.')
        return me.sudo(), True
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp.exists():
        raise ValidationError('Không tìm thấy nhân viên.')
    if me and emp.id == me.id:
        return emp, True
    if not _emp_in_scope(env, emp):
        raise AccessError('Bạn không có quyền xem lộ trình của nhân viên này.')
    return emp, False


STALE_PROMO_MONTHS = 12


def _career_insights(evaluations, criteria_radar, months_since, onb):
    """Vài câu đọc-là-hiểu rút từ chính dữ liệu trên trang.

    KHÔNG nhắc tới lương ở đây: insight hiện cho mọi người xem được trang,
    trong đó có vai trò không được xem lương (_cap_see_salary)."""
    out = []
    # 'published' là trạng thái chốt của phiếu hocba_reviews; đợt cũ dừng ở
    # 'confirmed'. Cả hai đều là kết quả đã chốt.
    confirmed = [e for e in evaluations
                 if e['state'] in ('confirmed', 'published')]
    if not confirmed:
        out.append({'kind': 'info', 'text': 'Chưa có đợt đánh giá nào được '
                                            'xác nhận.'})
    else:
        last = confirmed[-1]
        if len(confirmed) > 1:
            delta = round(last['totalScore'] - confirmed[-2]['totalScore'], 1)
            if delta > 0:
                out.append({'kind': 'up', 'text':
                            'Điểm đánh giá tăng %s điểm so với đợt trước '
                            '(%s%%).' % (delta, last['totalScore'])})
            elif delta < 0:
                out.append({'kind': 'down', 'text':
                            'Điểm đánh giá giảm %s điểm so với đợt trước '
                            '(%s%%).' % (abs(delta), last['totalScore'])})
            else:
                out.append({'kind': 'info', 'text':
                            'Điểm đánh giá đi ngang ở %s%%.'
                            % last['totalScore']})
        else:
            out.append({'kind': 'info', 'text':
                        'Đợt đánh giá đầu tiên: %s%%.' % last['totalScore']})
        scored = [c for c in criteria_radar if c['maxScore']]
        if len(scored) > 1:
            ratio = lambda c: c['score'] / c['maxScore']   # noqa: E731
            weakest = min(scored, key=ratio)
            strongest = max(scored, key=ratio)
            # Hoà điểm hết thì weakest is strongest → in "thấp nhất X" ngay
            # cạnh "cao nhất X", đọc như lỗi. Nói thẳng là đều nhau.
            if ratio(weakest) == ratio(strongest):
                out.append({'kind': 'info', 'text':
                            'Các tiêu chí đều nhau (%s/%s).'
                            % (weakest['score'], weakest['maxScore'])})
            else:
                out.append({'kind': 'warn', 'text': 'Tiêu chí thấp nhất: %s '
                            '(%s/%s).' % (weakest['name'], weakest['score'],
                                          weakest['maxScore'])})
                out.append({'kind': 'up', 'text': 'Tiêu chí cao nhất: %s '
                            '(%s/%s).' % (strongest['name'],
                                          strongest['score'],
                                          strongest['maxScore'])})
    if months_since is not None and months_since >= STALE_PROMO_MONTHS:
        out.append({'kind': 'warn', 'text':
                    'Đã %s tháng chưa có thay đổi chức vụ.' % months_since})
    if onb['total'] and onb['done'] + onb['skipped'] < onb['total']:
        out.append({'kind': 'info', 'text':
                    'Quy trình nhận việc: %s/%s bước đã xong.'
                    % (onb['done'] + onb['skipped'], onb['total'])})
    return out


def _career_payload(env, emp_id):
    """Toàn bộ "album của đời" một nhân viên: mốc thăng tiến, đợt đánh giá
    (điểm + nhận xét), kết quả từng bước thử việc, và các lần được vinh danh."""
    emp, is_self = _career_resolve(env, emp_id)
    can_manage = _user_can_manage(env)
    # Tự xem lương của chính mình vốn đã mở ở /api/me — giữ nhất quán, đừng
    # để trang mới chặt hơn trang cũ với cùng một dữ liệu.
    see_salary = is_self or _cap_see_salary(env)

    timeline = []

    # 1. Mốc thăng tiến / biến động hồ sơ
    change_labels = dict(
        env['hr.promotion.history']._fields['x_change_type'].selection)
    promos = env['hr.promotion.history'].sudo().search(
        [('employee_id', '=', emp.id)], order='date_effective, id')

    # 2. Vào làm việc — để NV mới toanh vẫn thấy một mốc. hr.employee.create
    # đã tự ghi snapshot 'join' vào hr.promotion.history, nên chỉ dựng mốc
    # tổng hợp khi snapshot đó KHÔNG có (hồ sơ cũ, hoặc tạo với
    # hocba_no_join_log) — nếu không dòng thời gian sẽ có 2 mốc nhận việc.
    start = emp.x_probation_start or (
        emp.create_date and emp.create_date.date())
    if start and not any(p.x_change_type == 'join' for p in promos):
        timeline.append({
            'kind': 'join', 'date': _d(start), 'sort': 0,
            'title': 'Vào làm việc',
            'detail': emp.job_id.name or '',
            'badge': '', 'badgeKind': 'gray'})
    salary_journey = []
    for p in promos:
        bits = []
        if p.reason:
            bits.append(p.reason)
        if p.decision_ref:
            bits.append('QĐ: %s' % p.decision_ref)
        # Snapshot 'join' chưa có chức vụ trước/sau → "— → —" vô nghĩa với
        # người đọc; dòng đó chính là mốc vào làm.
        is_join = p.x_change_type == 'join'
        if is_join:
            title = 'Vào làm việc'
            if p.to_job_id:
                bits.insert(0, p.to_job_id.name)
        else:
            title = '%s → %s' % (p.from_job_id.name or '—',
                                 p.to_job_id.name or '—')
        # Snapshot 'join' KHÔNG mang kind 'promotion': bộ lọc dòng thời gian
        # đếm theo kind, nên người chưa từng thăng chức sẽ thấy chip
        # "Thăng tiến (1)" ngay cạnh ô "Lần thăng chức: 0" — cùng một mâu
        # thuẫn đã sửa ở stats (promoCount/monthsSincePromo).
        item = {
            'kind': 'join' if is_join else 'promotion',
            'date': _d(p.date_effective), 'sort': 0 if is_join else 1,
            'title': title,
            'detail': ' · '.join(bits),
            'badge': change_labels.get(p.x_change_type, ''),
            'badgeKind': 'gold' if p.x_change_type == 'promotion' else 'gray',
            'dep': p.to_department_id.name or ''}
        if see_salary:
            item['fromWage'] = p.from_wage or 0
            item['toWage'] = p.to_wage or 0
            if p.to_wage:
                salary_journey.append({
                    'date': _d(p.date_effective), 'wage': p.to_wage,
                    'label': p.to_job_id.name or ''})
        timeline.append(item)

    # 3. Đợt đánh giá thăng tiến — bản nháp chỉ người quản lý thấy.
    # 3a. Đợt đánh giá thăng tiến CŨ (hr.promotion.evaluation) — chỉ còn là
    # lịch sử: từ 2026-08-12 nhập liệu chuyển hẳn sang phiếu của hocba_reviews
    # và hệ thống chỉ giữ MỘT bộ tiêu chí (hb.review.criteria). Vì vậy mốc cũ
    # KHÔNG mang 'lines': bày điểm của bộ tiêu chí đã ngừng dùng cạnh bộ mới
    # đúng là chỗ gây loạn mà khách bảo bỏ.
    ev_domain = [('employee_id', '=', emp.id)]
    if not can_manage:
        ev_domain.append(('state', '=', 'confirmed'))
    evals = env['hr.promotion.evaluation'].sudo().search(
        ev_domain, order='eval_date, id')
    evaluations = []
    score_trend = []
    for ev in evals:
        verdict = ev.verdict_final or ev.verdict_auto or ''
        evaluations.append({
            'id': ev.id, 'date': _d(ev.eval_date), 'source': 'legacy',
            'evaluator': ev.evaluator_id.name or '',
            'state': ev.state, 'totalScore': round(ev.total_score, 1),
            'verdictFinal': verdict,
            'verdictLabel': VERDICT_LABELS.get(verdict, ''),
            'note': ev.conclusion_note or '', 'lines': []})
        score_trend.append({'date': _d(ev.eval_date),
                            'score': round(ev.total_score, 1),
                            'verdict': verdict, 'source': 'legacy'})
        timeline.append({
            'kind': 'evaluation', 'date': _d(ev.eval_date), 'sort': 2,
            'title': 'Đợt đánh giá (bộ tiêu chí cũ) — %.0f%%' % ev.total_score,
            'detail': ev.conclusion_note or '',
            'badge': (VERDICT_LABELS.get(verdict, '') if ev.state == 'confirmed'
                      else 'Nháp'),
            'badgeKind': ('green' if verdict == 'qualified'
                          else 'amber' if verdict == 'consider' else 'gray'),
            'lines': []})

    # 3b. Phiếu đánh giá định kỳ (hocba_reviews) — nguồn CHÍNH từ 2026-08-12.
    # Người tự xem hồ sơ mình chỉ thấy phiếu ĐÃ CÔNG BỐ: hocba_reviews chỉ báo
    # nhân viên ở bước publish, cho xem phiếu vừa chốt là lộ kết quả trước khi
    # HR công bố. Vai trò quản lý thì thấy cả phiếu đã chốt.
    rv_states = ['confirmed', 'published'] if can_manage else ['published']
    reviews = env['hb.performance.review'].sudo().search(
        [('employee_id', '=', emp.id), ('state', 'in', rv_states)],
        order='date_from, id')
    grade_labels = dict(
        env['hb.performance.review']._fields['grade']._description_selection(env))
    for rv in reviews:
        lines = [{'name': l.criteria_id.name, 'score': l.score,
                  'maxScore': l.max_score, 'weight': l.weight,
                  'note': l.note or ''} for l in rv.line_ids]
        grade = rv.grade or ''
        evaluations.append({
            'id': rv.id, 'date': _d(rv.date_to), 'source': 'review',
            'evaluator': rv.evaluator_id.name or '',
            'state': rv.state, 'totalScore': round(rv.total_score, 1),
            'periodLabel': rv.period_label or '',
            'grade': grade, 'gradeLabel': grade_labels.get(grade, ''),
            'note': rv.manager_note or '', 'lines': lines})
        score_trend.append({'date': _d(rv.date_to),
                            'score': round(rv.total_score, 1),
                            'grade': grade, 'source': 'review'})
        timeline.append({
            'kind': 'evaluation', 'date': _d(rv.date_to), 'sort': 2,
            'title': 'Đánh giá %s — %.0f điểm' % (rv.period_label or '',
                                                  rv.total_score),
            'detail': rv.manager_note or '',
            'badge': grade_labels.get(grade, ''),
            'badgeKind': ('green' if grade == 'a' else 'teal' if grade == 'b'
                          else 'amber' if grade == 'c' else 'gray'),
            'lines': lines})

    # Sắp lại theo ngày: 2 nguồn ghép vào cùng một danh sách nên thứ tự create
    # không còn là thứ tự thời gian — mọi thứ tính "đợt gần nhất/liền trước"
    # bên dưới đều dựa vào đây.
    evaluations.sort(key=lambda x: x['date'] or '')
    score_trend.sort(key=lambda x: x['date'] or '')

    # Radar tiêu chí: CHỈ dựng từ phiếu đánh giá định kỳ — hệ thống giờ chỉ
    # còn một bộ tiêu chí. Lấy phiếu gần nhất, kèm điểm phiếu LIỀN TRƯỚC của
    # cùng tiêu chí để nhìn ra tiến bộ/thụt lùi từng mặt; thiếu thì để None,
    # không bịa 0 — 0 điểm và "chưa từng chấm" là hai chuyện khác nhau.
    criteria_radar = []
    scored = [e for e in evaluations if e['source'] == 'review' and e['lines']]
    if scored:
        prev_by_name = {}
        if len(scored) > 1:
            prev_by_name = {l['name']: l['score'] for l in scored[-2]['lines']}
        for l in scored[-1]['lines']:
            criteria_radar.append({
                'name': l['name'], 'score': l['score'],
                'maxScore': l['maxScore'],
                'previous': prev_by_name.get(l['name']),
            })

    # 4. Kết quả từng bước thử việc — đây là "nhận xét" khách đòi nhìn thấy.
    # Đếm tiến độ trên TOÀN BỘ bước (kể cả chưa tới lượt) cho biểu đồ tiến độ.
    all_steps = env['hb.onboarding.step'].sudo().search(
        [('employee_id', '=', emp.id)])
    onb_progress = {
        'done': len(all_steps.filtered(lambda s: s.state == 'done')),
        'skipped': len(all_steps.filtered(lambda s: s.state == 'skipped')),
        'open': len(all_steps.filtered(lambda s: s.state == 'open')),
        'waiting': len(all_steps.filtered(lambda s: s.state == 'waiting')),
        'total': len(all_steps),
    }
    steps = all_steps.filtered(
        lambda s: s.state in ('done', 'skipped')).sorted(
            key=lambda s: (s.done_date or date.min, s.sequence, s.id))
    for s in steps:
        timeline.append({
            'kind': 'onboarding', 'date': _d(s.done_date), 'sort': 3,
            'title': s.name,
            'detail': s.result_note or '',
            'badge': (ONB_RESULT_LABELS.get(s.result, '')
                      or ('Bỏ qua' if s.state == 'skipped' else 'Hoàn thành')),
            'badgeKind': ('green' if s.result == 'pass'
                          else 'amber' if s.result == 'extend'
                          else 'red' if s.result == 'fail' else 'gray')})

    # 5. Vinh danh
    honor_labels = dict(
        env['hb.honor.entry']._fields['category']._description_selection(env))
    honors = env['hb.honor.entry'].sudo().search(
        [('employee_id', '=', emp.id)], order='date_awarded, id')
    for h in honors:
        timeline.append({
            'kind': 'honor', 'date': _d(h.date_awarded), 'sort': 4,
            'title': h.title, 'detail': h.description or '',
            'badge': honor_labels.get(h.category, ''), 'badgeKind': 'gold'})

    # Mới nhất trên cùng; cùng ngày thì theo sort/kind để kết quả ổn định.
    timeline.sort(key=lambda t: (t['date'] or '', t['sort']), reverse=True)

    scores = [e['totalScore'] for e in evaluations
              if e['state'] in ('confirmed', 'published')]
    # KHÔNG dùng emp._promo_auto_metrics(): nó kéo thêm tổng hợp chấm công 90
    # ngày (module khác) mà trang này không dùng, và tính "tháng từ thăng
    # tiến" theo bản ghi gần nhất BẤT KỲ LOẠI — hồ sơ nào cũng có snapshot
    # 'join' nên người chưa từng thăng chức vẫn hiện một con số, chửi nhau với
    # ô "Lần thăng chức: 0" ngay cạnh.
    today = fields.Date.context_today(emp)
    tenure_months = round((today - start).days / 30.44, 1) if start else 0
    real_promos = promos.filtered(lambda p: p.x_change_type == 'promotion')
    months_since = None
    if real_promos:
        last = max(real_promos, key=lambda p: p.date_effective)
        months_since = round((today - last.date_effective).days / 30.44, 1)

    insights = _career_insights(evaluations, criteria_radar, months_since,
                                onb_progress)
    status_labels = dict(
        env['hr.employee']._fields['x_employment_status']
        ._description_selection(env))
    return {
        'employee': {
            'id': emp.id, 'name': emp.name,
            'code': emp.x_employee_code or '',
            'jobTitle': emp.job_id.name or '—',
            'depName': emp.department_id.name or '—',
            'hasImg': bool(emp.image_128),
            'start': _d(start),
            'status': status_labels.get(emp.x_employment_status, ''),
            'statusKey': emp.x_employment_status or '',
        },
        'isSelf': is_self,
        'canManage': can_manage,
        'canSeeSalary': see_salary,
        'stats': {
            'tenureMonths': tenure_months,
            'monthsSincePromo': months_since,
            # Chỉ thăng chức thật: hồ sơ nào cũng có snapshot 'join', đếm cả
            # nó thì ai vừa vào làm cũng thành "đã có 1 mốc thăng tiến".
            'promoCount': len(real_promos),
            'evalCount': len(evaluations),
            'honorCount': len(honors),
            'avgScore': round(sum(scores) / len(scores), 1) if scores else None,
            'lastScore': scores[-1] if scores else None,
        },
        'insights': insights,
        'timeline': timeline,
        'salaryJourney': salary_journey,
        'scoreTrend': score_trend,
        'criteriaRadar': criteria_radar,
        'onboardingProgress': onb_progress,
        'evaluations': evaluations,
        'honors': [{'id': h.id, 'date': _d(h.date_awarded),
                    'category': h.category, 'title': h.title,
                    'description': h.description or ''} for h in honors],
    }


# ----------------------------------------------------------------------
# Bảng vinh danh (ý D họp 2026-08-07) — khung "nhìn thấy đầu tiên" trên
# dashboard chung. Spec: docs/superpowers/specs/
# 2026-08-09-career-dashboard-honor-board-design.md §5.3
# ----------------------------------------------------------------------
HONOR_RANK_LIMIT = 5


def _honor_period_key(d):
    return '%04d-%02d' % (d.year, d.month)


def _honor_period_label(key):
    y, m = key.split('-')
    return 'Tháng %d/%s' % (int(m), y)


def _honor_row(e, labels):
    emp = e.employee_id
    return {
        'id': e.id,
        'empId': emp.id,
        'empName': emp.name,
        'empCode': emp.x_employee_code or '',
        'dep': emp.department_id.name or '',
        'hasImg': bool(emp.image_128),
        'category': e.category,
        'categoryLabel': labels.get(e.category, e.category),
        'title': e.title,
        'description': e.description or '',
        'date': _d(e.date_awarded),
        'rank': e.rank,
        'source': e.source,
    }


def _honor_board(env):
    """Bảng vinh danh của kỳ hiện tại — MỌI user đăng nhập đều đọc được.

    Kỳ = tháng. Nếu kỳ hiện tại chưa vinh danh ai thì lùi về kỳ gần nhất còn
    dữ liệu (isCurrent=False): khung này là thứ người dùng nhìn thấy đầu tiên,
    để trống ngay đầu tháng thì thành ô chết."""
    Honor = env['hb.honor.entry'].sudo()
    current = _honor_period_key(fields.Date.context_today(Honor))
    period = current
    if not Honor.search_count([('period_key', '=', current)]):
        newest = Honor.search([], order='date_awarded desc', limit=1)
        if newest:
            period = newest.period_key
    entries = Honor.search([('period_key', '=', period)])
    # rank=0 nghĩa là "không xếp hạng" → đẩy xuống cuối, không để nó leo lên
    # trên hạng 1 (lý do _order của model không đụng tới rank).
    entries = entries.sorted(
        key=lambda e: (e.rank == 0, e.rank, -(e.date_awarded.toordinal()), -e.id))
    labels = dict(Honor._fields['category']._description_selection(env))
    can_manage = _user_can_manage(env)

    # Lọc khoảng ngày ngay trong domain: kéo hết đợt đánh giá đã xác nhận về
    # rồi mới lọc bằng Python là đọc cả lịch sử nhiều năm cho một tháng.
    y, m = (int(x) for x in period.split('-'))
    first = date(y, m, 1)
    last_day = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
    evals = env['hr.promotion.evaluation'].sudo().search([
        ('state', '=', 'confirmed'),
        ('verdict_final', '=', 'qualified'),
        ('eval_date', '>=', first),
        ('eval_date', '<=', last_day),
    ])
    is_hr = _is_hr(env)
    ranking = []
    for ev in evals.sorted(key=lambda e: -e.total_score)[:HONOR_RANK_LIMIT]:
        emp = ev.employee_id
        row = {'empId': emp.id, 'empName': emp.name,
               'dep': emp.department_id.name or '',
               'hasImg': bool(emp.image_128)}
        # Điểm đánh giá cá nhân không bày cho toàn công ty — vinh danh là
        # nêu tên, không phải công bố bảng điểm. Bảng là dữ liệu chung nên
        # quản lý cũng chỉ thấy điểm của người TRONG phạm vi mình: cùng một
        # người đó, /api/career trả 403 cho trưởng phòng phòng khác.
        if is_hr or _emp_in_scope(env, emp):
            row['score'] = round(ev.total_score, 1)
        ranking.append(row)

    return {
        'period': period,
        'periodLabel': _honor_period_label(period),
        'isCurrent': period == current,
        'canManage': can_manage,
        # Thêm/gỡ mục vinh danh là quyền HR (_honor_create/_honor_archive).
        # FE bày nút theo cờ này, không theo canManage — bày cho trưởng phòng
        # là mời họ bấm vào một lỗi 403.
        'canEdit': is_hr,
        'entries': [_honor_row(e, labels) for e in entries],
        'ranking': ranking,
    }


def _honor_create(env, body):
    """HR thêm một mục vinh danh (khách: 'có cái vinh danh gì thì mình cho
    lên đấy thôi')."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được thêm mục vinh danh.')
    # Payload rác không được thành 500: int() trên chuỗi bậy ném ValueError,
    # mà route chỉ bắt AccessError/ValidationError/UserError.
    try:
        emp_id = int(body.get('employeeId') or 0)
        rank = int(body.get('rank') or 0)
    except (TypeError, ValueError):
        raise ValidationError('Dữ liệu gửi lên không hợp lệ.')
    emp = env['hr.employee'].sudo().browse(emp_id)
    if not emp_id or not emp.exists():
        raise ValidationError('Không tìm thấy nhân viên.')
    title = (body.get('title') or '').strip()
    if not title:
        raise ValidationError('Danh hiệu không được để trống.')
    category = body.get('category') or 'achievement'
    valid = dict(env['hb.honor.entry']._fields['category'].selection)
    if category not in valid:
        raise ValidationError('Nhóm vinh danh không hợp lệ.')
    env['hb.honor.entry'].sudo().create({
        'employee_id': emp.id,
        'category': category,
        'title': title,
        'description': (body.get('description') or '').strip() or False,
        'date_awarded': body.get('date') or fields.Date.context_today(emp),
        'rank': rank,
        'source': 'manual',
    })
    return _honor_board(env)


def _honor_archive(env, entry_id):
    """Gỡ khỏi bảng = archive, KHÔNG xoá — giữ vết ai từng được vinh danh."""
    if not _is_hr(env):
        raise AccessError('Chỉ HR/Admin được gỡ mục vinh danh.')
    entry = env['hb.honor.entry'].sudo().browse(entry_id)
    if not entry.exists():
        raise ValidationError('Không tìm thấy mục vinh danh.')
    entry.write({'active': False})
    return _honor_board(env)


def _dept_payload(dept):
    """Một dòng phòng ban cho SPA. employeeCount đếm trực tiếp member_ids
    (chắc chắn, không phụ thuộc tên field computed của Odoo)."""
    return {
        'id': dept.id,
        'name': dept.name,
        'functionDesc': dept.x_function_desc or '',
        'managerId': dept.manager_id.id or False,
        'managerName': dept.manager_id.name or '',
        'employeeCount': len(dept.member_ids),
        'active': dept.active,
    }


def _dept_list(env, archived=False):
    """Danh sách phòng ban + danh mục NV (cho dropdown trưởng phòng). Chỉ HR.
    archived=True → gồm cả phòng đã lưu trữ (active=False).

    Kèm cờ canEdit để FE ẩn nút Thêm/Sửa/Lưu trữ với HR officer (chỉ xem)."""
    if not _cap_view_dept(env):
        raise AccessError('Chỉ HR/Admin được xem danh sách phòng ban.')
    Dept = env['hr.department'].sudo().with_context(active_test=not archived)
    depts = Dept.search([], order='name')
    # Dropdown trưởng phòng CHỈ liệt kê NV đã có tài khoản đăng nhập (xem
    # _dept_update). Vẫn kèm trưởng phòng đương nhiệm dù chưa có tài khoản —
    # dữ liệu cũ có trường hợp đó, thiếu họ trong danh mục thì sửa tên phòng
    # sẽ vô tình gỡ mất người đang gán.
    emps = env['hr.employee'].sudo().search(
        ['|', ('user_id', '!=', False),
         ('id', 'in', depts.mapped('manager_id').ids)],
        order='x_employee_code, name')
    return {
        'departments': [_dept_payload(d) for d in depts],
        'employees': [{'id': e.id, 'name': e.name,
                       'code': e.x_employee_code or '',
                       'hasAccount': bool(e.user_id)} for e in emps],
        # Cho khối "tạo trưởng phòng mới" trong form phòng ban.
        'empTypes': [{'id': t.id, 'name': t.name, 'code': t.code or ''}
                     for t in env['hocba.employee.type'].sudo().search([])],
        'minPasswordLen': MIN_PASSWORD_LEN,
        'canEdit': _cap_edit_dept(env),
    }


def _dept_new_manager(env, dept, body):
    """Tạo hồ sơ NV + tài khoản đăng nhập MỚI rồi gán làm trưởng phòng của dept.

    Quyền trưởng phòng trong hệ này suy ra từ hr.department.manager_id (xem
    _emp_scope_domain), KHÔNG từ group riêng — nên chỉ cấp base.group_user,
    y như nhánh role='truongphong' của _account_create.
    """
    m = body.get('manager') or {}
    name = (m.get('name') or '').strip()
    if not name:
        raise ValidationError('Vui lòng nhập họ tên trưởng phòng.')
    login = (m.get('login') or '').strip()
    if not login:
        raise ValidationError('Vui lòng nhập tên đăng nhập cho trưởng phòng.')
    if env['res.users'].sudo().with_context(active_test=False).search_count(
            [('login', '=', login)]):
        raise ValidationError('Tên đăng nhập "%s" đã tồn tại.' % login)
    password = _validate_password(m)

    emp_vals = {
        'name': name,
        'department_id': dept.id,
        'work_email': (m.get('email') or '').strip() or False,
        'work_phone': (m.get('phone') or '').strip() or False,
    }
    code = (m.get('code') or '').strip()
    if code:
        emp_vals['x_employee_code'] = code
    if m.get('empTypeId'):
        emp_vals['x_employee_type_id'] = int(m['empTypeId'])
    emp = env['hr.employee'].sudo().create(emp_vals)
    user = env['res.users'].sudo().create({
        'name': emp.name, 'login': login, 'password': password,
        'group_ids': [(6, 0, [env.ref('base.group_user').id])],
    })
    emp.sudo().user_id = user.id
    dept.manager_id = emp.id
    return emp


def _dept_create(env, body):
    """HR Manager/Admin tạo phòng ban mới — BẮT BUỘC kèm trưởng phòng MỚI (hồ
    sơ NV + tài khoản đăng nhập), gửi trong body['manager'].

    Chốt với khách 2026-08-14: cho chọn NV có sẵn ở bước tạo phòng là sai phân
    quyền — manager_id chính là nguồn quyền "trưởng phòng", nên thao tác tưởng
    chỉ-là-gán-tên đó âm thầm nâng quyền một tài khoản vốn có vai trò khác
    (nhân viên thường, giáo vụ), hoặc gán cho người chưa có tài khoản nào.
    """
    if not _cap_edit_dept(env):
        raise AccessError('Chỉ HR Manager/Admin được tạo phòng ban.')
    name = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('Vui lòng nhập tên phòng ban.')
    if not (body.get('manager') or {}):
        raise ValidationError(
            'Phòng ban mới phải có trưởng phòng — nhập thông tin tài khoản '
            'trưởng phòng để tạo cùng lúc.')
    dept = env['hr.department'].sudo().create({
        'name': name,
        'x_function_desc': (body.get('functionDesc') or '').strip(),
    })
    _dept_new_manager(env, dept, body)
    return _dept_payload(dept)


def _dept_update(env, dept_id, body):
    """HR Manager/Admin sửa tên / chức năng / trưởng phòng.

    Đổi trưởng phòng theo 2 đường: chọn NV ĐÃ có tài khoản đăng nhập
    (managerId), hoặc gửi khối 'manager' để tạo trưởng phòng mới. NV chưa có
    tài khoản bị từ chối — làm trưởng phòng mà không đăng nhập được thì phòng
    coi như không có ai quản.
    """
    if not _cap_edit_dept(env):
        raise AccessError('Chỉ HR Manager/Admin được sửa phòng ban.')
    dept = env['hr.department'].sudo().with_context(
        active_test=False).browse(dept_id)
    if not dept.exists():
        raise ValidationError('Không tìm thấy phòng ban.')
    name = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('Vui lòng nhập tên phòng ban.')
    vals = {'name': name,
            'x_function_desc': (body.get('functionDesc') or '').strip()}

    if body.get('manager'):
        dept.write(vals)
        _dept_new_manager(env, dept, body)
        return _dept_payload(dept)

    manager_id = body.get('managerId')
    new_mgr = int(manager_id) if manager_id else False
    # Chỉ soi khi ĐỔI người: phòng cũ đang gán người chưa có tài khoản vẫn
    # phải sửa được tên/chức năng, không thì dữ liệu cũ kẹt cứng.
    if new_mgr and new_mgr != dept.manager_id.id:
        emp = env['hr.employee'].sudo().browse(new_mgr)
        if not emp.exists():
            raise ValidationError('Nhân viên không hợp lệ.')
        if not emp.user_id:
            raise ValidationError(
                'Nhân viên "%s" chưa có tài khoản đăng nhập nên không đặt làm '
                'trưởng phòng được. Cấp tài khoản ở màn Tài khoản, hoặc tạo '
                'trưởng phòng mới ngay tại đây.' % emp.name)
        if not emp.user_id.active:
            raise ValidationError(
                'Tài khoản đăng nhập của "%s" đang bị khóa.' % emp.name)
        # Giáo vụ + trưởng phòng là mâu thuẫn có thật, không phải cẩn thận thừa:
        # _emp_scope_domain xét nhánh giáo vụ TRƯỚC nhánh trưởng phòng, nên gán
        # xong người này vẫn chỉ thấy giáo viên chứ không thấy phòng mình.
        if emp.user_id.sudo().has_group('hocba_employees.group_hocba_giaovu'):
            raise ValidationError(
                'Tài khoản của "%s" đang là Giáo vụ — phạm vi giáo vụ (chỉ giáo '
                'viên) sẽ lấn át quyền trưởng phòng, người này vẫn không xem '
                'được phòng ban. Chọn người khác hoặc tạo trưởng phòng mới.'
                % emp.name)
    vals['manager_id'] = new_mgr
    dept.write(vals)
    return _dept_payload(dept)


def _dept_archive(env, dept_id, body):
    """HR Manager/Admin lưu trữ (active=False) / khôi phục (active=True) phòng
    ban. Đây là đường thay cho xóa cứng — xóa cứng bị chặn bởi ràng buộc model."""
    if not _cap_edit_dept(env):
        raise AccessError('Chỉ HR Manager/Admin được lưu trữ phòng ban.')
    dept = env['hr.department'].sudo().with_context(
        active_test=False).browse(dept_id)
    if not dept.exists():
        raise ValidationError('Không tìm thấy phòng ban.')
    dept.write({'active': bool(body.get('active'))})
    return _dept_payload(dept)


def _years_between(start, end):
    """Số năm tròn giữa 2 ngày; None nếu thiếu ngày hoặc start > end."""
    if not start or not end or start > end:
        return None
    return end.year - start.year - (
        (end.month, end.day) < (start.month, start.day))


def _last_months(n, today):
    """n cặp (year, month) gần nhất tính cả tháng hiện tại, tăng dần."""
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out[::-1]


def _m_label(y, m):
    return '%d/%d' % (m, y)


def _dash_scope_emp_ids(env):
    """Phạm vi NV cho tab Chấm công/Nghỉ phép: None = tất cả (HR/Admin);
    [] = không có quyền; list id = giới hạn theo vai trò (trưởng phòng/giáo vụ)."""
    dom = _emp_scope_domain(env)
    if not dom:
        return None
    if dom == [('id', '=', 0)]:
        return []
    return env['hr.employee'].sudo().with_context(
        active_test=False).search(dom).ids


def _dashboard_stats(env):
    """KPI + dữ liệu biểu đồ cho Dashboard (theo mẫu Lark HRM 6.1).
    Phạm vi theo vai trò như danh sách NV (_emp_scope_domain); search với
    active_test=False vì NV nghỉ việc bị archive nhưng vẫn phải đếm Offboard.
    Spec: docs/superpowers/specs/SPEC_DASHBOARD_HR_OVERVIEW.md"""
    today = fields.Date.today()
    all_emps = env['hr.employee'].sudo().with_context(
        active_test=False).search(_emp_scope_domain(env))
    resigned = all_emps.filtered(
        lambda e: e.x_employment_status == 'resigned')
    working = all_emps.filtered(
        lambda e: e.active and e.x_employment_status != 'resigned')

    ages, seniorities = [], []
    age_dist, sen_dist = {}, {}
    for e in working:
        age = _years_between(e.birthday, today)
        if age is not None:
            ages.append(age)
            age_dist[age] = age_dist.get(age, 0) + 1
        start = e.x_probation_start or (
            e.create_date and e.create_date.date())
        sen = _years_between(start, today)
        if sen is not None:
            seniorities.append(sen)
            sen_dist[sen] = sen_dist.get(sen, 0) + 1

    # Số NV lên chính thức theo tháng (mọi hồ sơ có mốc, kể cả đã nghỉ)
    by_month = {}
    for e in all_emps:
        if e.x_official_date:
            k = (e.x_official_date.year, e.x_official_date.month)
            by_month[k] = by_month.get(k, 0) + 1

    # Phân bổ phòng ban (NV đang làm)
    dep_cnt = {}
    for e in working:
        nm = e.department_id.name or 'Chưa gán'
        dep_cnt[nm] = dep_cnt.get(nm, 0) + 1
    by_department = [{'dep': k, 'count': dep_cnt[k]}
                     for k in sorted(dep_cnt, key=lambda k: -dep_cnt[k])]

    # Tỷ lệ nghỉ việc 12 tháng: tử = đơn offboarding done trong tháng,
    # mẫu = headcount cuối tháng (đã vào − đã nghỉ lũy kế, theo dữ liệu có ngày)
    months = _last_months(12, today)
    offs = env['hocba.offboarding'].sudo().search_read(
        [('state', '=', 'done'), ('actual_leave_date', '!=', False),
         ('employee_id', 'in', all_emps.ids)], ['actual_leave_date'])
    left_by_m = {}
    for o in offs:
        d = o['actual_leave_date']
        left_by_m[(d.year, d.month)] = left_by_m.get((d.year, d.month), 0) + 1
    starts = [e.x_probation_start or (e.create_date and e.create_date.date())
              for e in all_emps]
    turnover = []
    for (y, m) in months:
        month_end = date(y, m, calendar.monthrange(y, m)[1])
        joined = sum(1 for s in starts if s and s <= month_end)
        left_cum = sum(c for k, c in left_by_m.items() if k <= (y, m))
        headcount = joined - left_cum
        n = left_by_m.get((y, m), 0)
        turnover.append({
            'label': _m_label(y, m), 'count': n,
            'rate': round(n * 100.0 / headcount, 1) if headcount > 0 else 0.0,
        })

    # Cờ tab theo quyền — FE dựng thanh tab
    user = env.user
    is_hr = (user.has_group('base.group_system')
             or user.has_group('hr.group_hr_user')
             or user.has_group('hr.group_hr_manager'))
    scoped = _emp_scope_domain(env) != [('id', '=', 0)]

    return {
        'tabs': {
            'recruitment': is_hr,
            'attendance': scoped,
            'timeoff': scoped,
            'payroll': user.has_group('hr.group_hr_manager'),
        },
        'byDepartment': by_department,
        'turnoverByMonth': turnover,
        'kpi': {
            # total = onboard + offboard, KHÔNG phải len(all_emps).
            # Hồ sơ NV không xoá được qua ORM (BR-060: hr.promotion.history là
            # audit trail, FK restrict) nên mọi hồ sơ tạo nhầm/hồ sơ test chỉ
            # được archive và nằm lại vĩnh viễn trong all_emps. Chúng archived
            # nhưng x_employment_status vẫn 'probation'/'official' ⇒ không rơi
            # vào onboard lẫn offboard, khiến thẻ "Số nhân sự tính đến hiện tại"
            # phình lên và total ≠ onboard + offboard (đã gặp: 17 vs 6 + 1).
            'total': len(working) + len(resigned),
            'onboard': len(working),
            'offboard': len(resigned),
            'avgAge': round(sum(ages) / len(ages)) if ages else 0,
            'avgSeniority': (round(sum(seniorities) / len(seniorities))
                             if seniorities else 0),
        },
        'officialByMonth': [
            {'label': '%d/%d' % (m, y), 'count': by_month[(y, m)]}
            for (y, m) in sorted(by_month)],
        'byAge': [{'age': a, 'count': age_dist[a]}
                  for a in sorted(age_dist)],
        'bySeniority': [{'years': s, 'count': sen_dist[s]}
                        for s in sorted(sen_dist)],
    }


def _dashboard_recruitment(env):
    """Tab Tuyển dụng: phễu chuyển đổi, time-to-hire, nguồn CV, vị trí mở.
    Chỉ HR (route chặn) — dữ liệu tuyển dụng là toàn công ty.
    Guard model: hocba_hrm không depends hocba_recruitments."""
    if 'hr.applicant' not in env or 'hb.recruitment.request' not in env:
        return {'funnel': [], 'timeToHire': {'avgDays': 0, 'hired': 0,
                                             'totalCv': 0},
                'bySource': [], 'openByDept': []}
    Applicant = env['hr.applicant'].sudo().with_context(active_test=False)
    hired_ids = set(env['hr.recruitment.stage'].sudo().search(
        [('hired_stage', '=', True)]).ids)
    apps = Applicant.search_read(
        [], ['cv_filter_result', 'attendance_status', 'interview_result',
             'stage_id', 'start_date', 'date_received', 'source_id',
             'ctv_tuyen_dung'])
    hired = [a for a in apps
             if a['stage_id'] and a['stage_id'][0] in hired_ids]
    funnel = [
        {'stage': 'Nộp CV', 'count': len(apps)},
        {'stage': 'Pass lọc CV', 'count': sum(
            1 for a in apps if a['cv_filter_result'] == 'pass')},
        {'stage': 'Tham gia PV', 'count': sum(
            1 for a in apps if a['attendance_status'] == 'present')},
        {'stage': 'Pass PV', 'count': sum(
            1 for a in apps if a['interview_result'] == 'pass')},
        {'stage': 'Nhận việc', 'count': len(hired)},
    ]
    waits = [(a['start_date'] - a['date_received']).days
             for a in hired if a['start_date'] and a['date_received']
             and a['start_date'] >= a['date_received']]
    src_cnt = {}
    for a in apps:
        label = (a['source_id'][1] if a['source_id']
                 else ('CTV giới thiệu' if a['ctv_tuyen_dung'] else 'Khác'))
        src_cnt[label] = src_cnt.get(label, 0) + 1
    top_src = sorted(src_cnt.items(), key=lambda kv: -kv[1])
    by_source = [{'label': k, 'count': v} for k, v in top_src[:5]]
    rest = sum(v for _, v in top_src[5:])
    if rest:
        by_source.append({'label': 'Khác', 'count': rest})
    reqs = env['hb.recruitment.request'].sudo().search_read(
        [('state', '=', 'recruiting')], ['department_id', 'qty_expected'])
    open_cnt = {}
    for r in reqs:
        nm = r['department_id'][1] if r['department_id'] else 'Chưa gán'
        d = open_cnt.setdefault(nm, {'dep': nm, 'requests': 0, 'qty': 0})
        d['requests'] += 1
        d['qty'] += r['qty_expected'] or 0
    return {
        'funnel': funnel,
        'timeToHire': {
            'avgDays': round(sum(waits) / len(waits)) if waits else 0,
            'hired': len(hired),
            'totalCv': len(apps),
        },
        'bySource': by_source,
        'openByDept': sorted(open_cnt.values(), key=lambda d: -d['qty']),
    }


def _dashboard_attendance(env):
    """Tab Chấm công: % đi muộn / về sớm theo tháng, top đi muộn (3 tháng),
    giờ OT theo tháng phân theo mức hệ số. Scope NV theo vai trò."""
    today = fields.Date.today()
    months = _last_months(12, today)
    first = date(months[0][0], months[0][1], 1)
    emp_ids = _dash_scope_emp_ids(env)
    dom = [('date', '>=', first)]
    sdom = [('shift_type', '=', 'ot'), ('state', '=', 'approved'),
            ('start', '>=', datetime.combine(first, datetime.min.time()))]
    if emp_ids is not None:
        dom.append(('employee_id', 'in', emp_ids))
        sdom.append(('employee_id', 'in', emp_ids))
    rows = env['hocba.attendance'].sudo().search_read(
        dom, ['date', 'late_minutes', 'early_leave_minutes',
              'employee_id', 'department_id'])
    agg = {}
    for r in rows:
        k = (r['date'].year, r['date'].month)
        a = agg.setdefault(k, {'total': 0, 'late': 0, 'early': 0})
        a['total'] += 1
        if (r['late_minutes'] or 0) > 0:
            a['late'] += 1
        if (r['early_leave_minutes'] or 0) > 0:
            a['early'] += 1

    def pct(part, total):
        return round(part * 100.0 / total, 1) if total else 0.0

    rate_by_month = []
    for (y, m) in months:
        a = agg.get((y, m), {'total': 0, 'late': 0, 'early': 0})
        rate_by_month.append({
            'label': _m_label(y, m), 'records': a['total'],
            'latePct': pct(a['late'], a['total']),
            'earlyPct': pct(a['early'], a['total']),
        })
    # Top đi muộn 3 tháng gần nhất
    q_first = date(months[-3][0], months[-3][1], 1)
    top = {}
    for r in rows:
        if r['date'] < q_first or (r['late_minutes'] or 0) <= 0 \
                or not r['employee_id']:
            continue
        t = top.setdefault(r['employee_id'][0], {
            'name': r['employee_id'][1],
            'dep': r['department_id'][1] if r['department_id'] else 'Chưa gán',
            'count': 0, 'minutes': 0})
        t['count'] += 1
        t['minutes'] += r['late_minutes']
    top_late = sorted(top.values(),
                      key=lambda t: (-t['count'], -t['minutes']))[:7]
    # OT theo tháng × mức hệ số (giờ, gộp theo tháng UTC của ca)
    shifts = env['hocba.work_shift'].sudo().search_read(
        sdom, ['start', 'end', 'ot_level'])
    ot = {}
    for s in shifts:
        if not (s['start'] and s['end']):
            continue
        k = (s['start'].year, s['start'].month)
        h = max((s['end'] - s['start']).total_seconds() / 3600.0, 0)
        d = ot.setdefault(k, {'100': 0.0, '150': 0.0, '300': 0.0})
        d[s['ot_level'] or '100'] += h
    ot_by_month = []
    for (y, m) in months:
        d = ot.get((y, m), {})
        ot_by_month.append({
            'label': _m_label(y, m),
            'h100': round(d.get('100', 0.0), 1),
            'h150': round(d.get('150', 0.0), 1),
            'h300': round(d.get('300', 0.0), 1),
        })
    return {'rateByMonth': rate_by_month, 'topLate': top_late,
            'otByMonth': ot_by_month}


def _dashboard_timeoff(env):
    """Tab Nghỉ phép: pie lý do, xu hướng ngày nghỉ theo tháng, quỹ phép tồn.
    Chỉ đọc field cụ thể qua search_read (hr.leave có field lệch schema trên
    một số DB — tránh SELECT toàn bộ cột). Scope NV theo vai trò."""
    today = fields.Date.today()
    months = _last_months(12, today)
    if 'hr.leave' not in env:  # guard: DB không cài module nghỉ phép
        return {'byType': [], 'remaining': 0, 'takenDays': 0,
                'byMonth': [{'label': _m_label(y, m), 'days': 0}
                            for (y, m) in months]}
    first = date(months[0][0], months[0][1], 1)
    emp_ids = _dash_scope_emp_ids(env)
    scope = [] if emp_ids is None else [('employee_id', 'in', emp_ids)]
    leaves = env['hr.leave'].sudo().search_read(
        [('state', '=', 'validate'), ('request_date_from', '>=', first)]
        + scope,
        ['request_date_from', 'number_of_days', 'holiday_status_id'])
    by_type, by_m = {}, {}
    for lv in leaves:
        days = lv['number_of_days'] or 0
        nm = (lv['holiday_status_id'][1] if lv['holiday_status_id']
              else 'Khác')
        by_type[nm] = by_type.get(nm, 0) + days
        d = lv['request_date_from']
        if d:
            k = (d.year, d.month)
            by_m[k] = by_m.get(k, 0) + days
    top_types = sorted(by_type.items(), key=lambda kv: -kv[1])
    type_rows = [{'label': k, 'days': round(v, 1)} for k, v in top_types[:6]]
    rest = sum(v for _, v in top_types[6:])
    if rest:
        type_rows.append({'label': 'Khác', 'days': round(rest, 1)})
    allocs = env['hr.leave.allocation'].sudo().search_read(
        [('state', '=', 'validate')] + scope, ['number_of_days'])
    taken = env['hr.leave'].sudo().search_read(
        [('state', '=', 'validate')] + scope, ['number_of_days'])
    remaining = (sum(a['number_of_days'] or 0 for a in allocs)
                 - sum(t['number_of_days'] or 0 for t in taken))
    return {
        'byType': type_rows,
        'byMonth': [{'label': _m_label(y, m),
                     'days': round(by_m.get((y, m), 0), 1)}
                    for (y, m) in months],
        'remaining': round(max(remaining, 0.0), 1),
        'takenDays': round(sum(lv['number_of_days'] or 0 for lv in leaves), 1),
    }


def _dashboard_payroll(env):
    """Tab Lương (chỉ HR Manager — route chặn): quỹ lương theo tháng,
    chi phí theo phòng ban kỳ gần nhất, lương TB theo phân cấp."""
    today = fields.Date.today()
    months = _last_months(12, today)
    first = date(months[0][0], months[0][1], 1)
    slips = []
    if 'hb.payslip' in env:  # guard: DB không cài hocba_payroll
        slips = env['hb.payslip'].sudo().search_read(
            [('date_from', '>=', first), ('state', '!=', 'cancel')],
            ['date_from', 'net_amount', 'gross_amount', 'employee_id'])
    fund = {}
    for s in slips:
        k = (s['date_from'].year, s['date_from'].month)
        f = fund.setdefault(k, {'net': 0.0, 'gross': 0.0})
        f['net'] += s['net_amount'] or 0
        f['gross'] += s['gross_amount'] or 0
    fund_by_month = [{'label': _m_label(y, m),
                      'net': round(fund.get((y, m), {}).get('net', 0)),
                      'gross': round(fund.get((y, m), {}).get('gross', 0))}
                     for (y, m) in months]
    # Chi phí theo phòng ban — kỳ gần nhất có net > 0 (bỏ batch nháp
    # chưa tính lương, net = 0), fallback kỳ có gross
    by_dept, last_label = [], ''
    keys = ([k for k in fund if fund[k]['net'] > 0]
            or [k for k in fund if fund[k]['gross'] > 0])
    if keys:
        last_k = max(keys)
        last_label = _m_label(*last_k)
        cur = [s for s in slips
               if (s['date_from'].year, s['date_from'].month) == last_k
               and s['employee_id']]
        emps = env['hr.employee'].sudo().with_context(
            active_test=False).browse({s['employee_id'][0] for s in cur})
        dep_of = {e.id: e.department_id.name or 'Chưa gán' for e in emps}
        dep_sum = {}
        for s in cur:
            nm = dep_of.get(s['employee_id'][0], 'Chưa gán')
            dep_sum[nm] = dep_sum.get(nm, 0) + (s['net_amount'] or 0)
        by_dept = [{'dep': k, 'net': round(v)} for k, v in
                   sorted(dep_sum.items(), key=lambda kv: -kv[1])]
    # Lương TB theo phân cấp (wage hợp đồng hiện tại của NV đang làm)
    lvl_lbl = {'junior': 'Junior', 'middle': 'Middle', 'senior': 'Senior'}
    buckets = {}
    for e in env['hr.employee'].sudo().search(
            [('x_employment_status', '!=', 'resigned')]):
        v = e.version_id
        wage = (v.wage if v and 'wage' in v._fields else 0) or 0
        if wage <= 0:
            continue
        lbl = lvl_lbl.get(e.x_seniority_level, 'Chưa phân cấp')
        b = buckets.setdefault(lbl, [0.0, 0])
        b[0] += wage
        b[1] += 1
    order = ['Junior', 'Middle', 'Senior', 'Chưa phân cấp']
    avg_by_level = [
        {'label': k, 'avg': round(buckets[k][0] / buckets[k][1]),
         'count': buckets[k][1]}
        for k in order if k in buckets]
    return {'fundByMonth': fund_by_month, 'byDept': by_dept,
            'byDeptPeriod': last_label, 'avgByLevel': avg_by_level}


_CHECK_ERR_STATUS = {
    'not_workday': 403,
    'on_approved_leave': 403,
    'already_checked_in': 409,
    'not_checked_in': 409,
    'already_checked_out': 409,
    'no_shift_today': 403,
    'outside_shift_window': 403,
    'no_shift': 404,
    'shift_not_approved': 409,
}


class HocBaHRM(http.Controller):

    @http.route('/hocba-hrm', auth='public', type='http', csrf=False)
    def hrm_dashboard(self, **kw):
        if not SPA_ENABLED:
            return request.redirect('/odoo')
        try:
            with file_open('hocba_hrm/static/spa/index.html', 'r') as f:
                html = f.read()
            html = self._bust_asset_cache(html)
            html = self._inject_db_name(html)
        except (FileNotFoundError, OSError):
            html = ('<h3 style="font-family:sans-serif">SPA chưa được build.</h3>'
                    '<p style="font-family:sans-serif">Chạy: <code>cd frontend &amp;&amp; '
                    'npm install &amp;&amp; npm run build</code> rồi tải lại trang '
                    '(xem docs/QUY_UOC_FRONTEND.md §8).</p>')
        resp = Response(html, content_type='text/html; charset=utf-8')
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    @staticmethod
    def _inject_db_name(html):
        """Nhúng tên database đang phục vụ vào trang SPA.

        Form đăng nhập gọi /web/session/authenticate — route này BẮT BUỘC có
        tham số `db`. Trước đây SPA ghi cứng 'neondb' nên chạy trên bất kỳ DB
        nào khác (local, demo, DB của thành viên khác) là đăng nhập luôn sai
        mật khẩu dù mật khẩu đúng. Lấy tên DB từ chính cursor đang chạy để
        không phải sửa code mỗi lần đổi DB.
        """
        db = request.env.cr.dbname
        tag = '<script>window.__HB_DB__=%s;</script>' % json.dumps(db)
        if '</head>' in html:
            return html.replace('</head>', tag + '</head>', 1)
        return tag + html

    @staticmethod
    def _bust_asset_cache(html):
        """Chèn ?v=<hash nội dung> vào URL asset SPA trong index.html.

        Vite build với tên file cố định (assets/index.js, assets/index.css) để
        không sinh bundle mới mỗi lần build → tránh conflict git ở static/spa.
        Bù lại, tên cố định khiến trình duyệt cache bản cũ; ta thêm query
        ?v=<md5 8 ký tự của chính file> để bust cache khi nội dung đổi.
        """
        def repl(m):
            url = m.group(1)
            rel = url.split('/hocba_hrm/', 1)[1]  # static/spa/assets/index.js
            try:
                with file_open('hocba_hrm/' + rel, 'rb') as af:
                    digest = hashlib.md5(af.read()).hexdigest()[:8]
            except (FileNotFoundError, OSError):
                return m.group(0)
            return m.group(0).replace(url, '%s?v=%s' % (url, digest))

        return re.sub(r'(?:src|href)="(/hocba_hrm/static/spa/assets/[^"?]+)"',
                      repl, html)

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

    def _can_edit_emp_record(self, e):
        """Được sửa hồ sơ (con) của NV e: có quyền quản lý VÀ e trong phạm vi."""
        return _cap_edit_emp(request.env) and self._emp_in_scope(e)

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
            'asset_condition': sel(env['hr.employee.asset'], 'condition_in'),
            'relationship': sel(env['hr.employee.dependent'], 'relationship'),
        }

    def _emp_base(self, e, labels, see_salary):
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
            # Tag loại nhân sự: NV văn phòng / Giáo viên / CTV (hocba.employee.type)
            'empTypeId': e.x_employee_type_id.id or False,
            'empType': e.x_employee_type_id.name or '',
            'empTypeKey': e.x_employee_type_id.code or '',
            'probStart': _d(e.x_probation_start),
            'start': _d(e.x_probation_start) or _d(e.create_date and e.create_date.date()),
            'email': e.work_email or '',
            'phone': e.work_phone or '',
            'hasImg': bool(e.image_1920),
        }
        if see_salary:
            v = e.version_id
            data['wage'] = (v.wage if v and 'wage' in v._fields else 0) or 0
        return data

    @http.route('/hocba-hrm/api/employees', auth='user', type='http', methods=['GET'])
    def api_employees(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        see_salary = _cap_see_salary(request.env)
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
            rows.append(self._emp_base(e, labels, see_salary))
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
            'canEditEmp': _cap_edit_emp(request.env),
            'canSeeSalary': see_salary,
            'canManageAccount': _cap_manage_account(request.env),
            'departments': list(deps.values()),
            'employees': rows,
        })

    def _employee_detail(self, e, labels, is_hr, is_mgr, see_salary=None,
                         can_account=None):
        """Dựng dict hồ sơ chi tiết theo quyền — dùng chung cho
        /api/employee/<id> (HR/TP/GV xem trong phạm vi) và /api/me (tự xem).
        is_hr ở đây = 'được quản lý hồ sơ' (canEditEmp): mở pháp lý/NPT/chứng chỉ
        cho cả TP/Giáo vụ. can_account (mặc định = is_hr) gác riêng khối tài khoản
        cho HR/Admin. see_salary=None → mặc định theo is_mgr."""
        if see_salary is None:
            see_salary = is_mgr
        if can_account is None:
            can_account = is_hr
        data = self._emp_base(e, labels, see_salary)

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
        if see_salary:
            # Tên ngân hàng: tra từ list payroll (hb.bank.format) theo mã đã lưu;
            # guard nếu payroll chưa cài, fallback hiển thị mã.
            bank_name = e.x_bank_code or ''
            if e.x_bank_code and 'hb.bank.format' in e.env:
                bank = e.env['hb.bank.format'].sudo().search(
                    [('code', '=', e.x_bank_code)], limit=1)
                if bank:
                    bank_name = bank.name
            data.update({
                'pit': e.x_pit_code or '',
                'si': e.x_social_insurance_no or '',
                'bankCode': e.x_bank_code or '',
                'bankName': bank_name,
                'bankAccountNo': e.x_bank_account_no or '',
            })

        # --- Quy trình nhận việc bước động (thay 2 cổng + thử giảng cứng) ---
        data['onboarding'] = self._onb_emp_item(e)

        # --- Tài sản (F-006) ---
        data['assets'] = [{
            'id': a.id,
            'type': a.asset_type_id.name or '',
            'code': a.asset_code or '',
            'grant': _d(a.grant_date),
            'conditionLabel': labels['asset_condition'].get(
                a.condition_in, a.condition_in or ''),
        } for a in e.x_asset_ids.sorted('grant_date')]

        # --- Thăng tiến (F-007) ---
        promotions = []
        for p in e.x_promotion_ids.sorted('date_effective'):
            # Snapshot 'join' chưa có chức vụ trước/sau → tiêu đề dựng từ
            # fromJob/toJob thành "— → —" (hồ sơ nào cũng mở ra bằng dòng
            # đó). Trang Lộ trình đã bỏ; tab Thăng tiến dùng chung 'title'.
            is_join = p.x_change_type == 'join'
            item = {
                'id': p.id,
                'date': _d(p.date_effective),
                'changeType': p.x_change_type or '',
                'title': ('Vào làm việc' if is_join
                          else '%s → %s' % (p.from_job_id.name or '—',
                                            p.to_job_id.name or '—')),
                'fromJob': p.from_job_id.name or '—',
                'toJob': p.to_job_id.name or '—',
                'dept': p.to_department_id.name or '',
                'ref': p.decision_ref or '',
                'reason': p.reason or '',
            }
            if see_salary:
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

        if can_account:
            data['account'] = _account_payload(e)

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
            self._employee_detail(e, labels,
                                  _cap_edit_emp(request.env), is_mgr,
                                  _cap_see_salary(request.env),
                                  _cap_manage_account(request.env)))

    # ------------------------------------------------------------------
    # Quy trình nhận việc BƯỚC ĐỘNG (hb.onboarding.step) — thay route
    # /gate + /trial cũ. Kiểm phạm vi tại controller rồi with_user gọi
    # action model (model tự check + sudo ghi bên trong).
    # Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
    # ------------------------------------------------------------------
    def _onb_emp_item(self, e):
        """Payload 1 NV cho màn Onboarding + tab Thử việc (bước động)."""
        can_eval = self._can_eval_emp(e)
        user = request.env.user
        is_gv_teacher = (
            user.has_group('hocba_employees.group_hocba_giaovu')
            and e.x_employee_type_id.code == 'teacher')
        steps = []
        done = total = 0
        current = None
        for s in e.x_onboarding_step_ids.sorted(
                lambda x: (x.sequence, x.id)):
            total += 1
            if s.state in ('done', 'skipped'):
                done += 1
            can_act = (s.state == 'open') and (
                can_eval or (s.step_type == 'task' and is_gv_teacher))
            item = {
                'id': s.id, 'name': s.name, 'stepType': s.step_type,
                'state': s.state, 'result': s.result or '',
                'extendCount': s.extend_count,
                'dueDate': _d(s.due_date), 'doneDate': _d(s.done_date),
                'doneBy': s.done_by_id.name or '',
                'note': s.note or '', 'resultNote': s.result_note or '',
                'passCompletes': s.pass_completes,
                'isExtension': s.is_extension,
                'isIndependent': s.is_independent,
                'canAct': can_act,
            }
            # "Bước hiện tại" là bước của CHUỖI — bước độc lập luôn mở nên
            # nếu tính cả nó thì header lúc nào cũng hiện "Cấp thiết bị".
            if (s.state == 'open' and not s.is_independent
                    and current is None):
                current = item
            steps.append(item)
        return {
            'id': e.id, 'code': e.x_employee_code or '—', 'name': e.name,
            'depName': e.department_id.name or 'Chưa gán',
            'jobTitle': e.job_id.name or '—',
            'hasImg': bool(e.image_1920),
            'start': _d(e.x_probation_start),
            'officialDate': _d(e.x_official_date),
            'templateId': e.x_onboarding_template_id.id or 0,
            'templateName': e.x_onboarding_template_id.name or '',
            'steps': steps,
            'progress': {'done': done, 'total': total},
            'current': current,
            'canEval': can_eval,
            # Chuỗi hết bước mà không bước nào "Đạt → lên chính thức" thì
            # đây là đường DUY NHẤT để NV lên Chính thức. Chỉ HR Manager,
            # khớp guard hr_employee.write().
            'canFinalize': (
                user.has_group('hr.group_hr_manager')
                and e._hocba_onboarding_can_finalize()[0]),
        }

    def _onb_get_step(self, step_id):
        step = request.env['hb.onboarding.step'].sudo().browse(step_id)
        if not step.exists():
            return None, request.make_json_response(
                {'error': 'not_found'}, status=404)
        return step, None

    def _onb_can_act(self, step):
        e = step.employee_id
        if self._can_eval_emp(e):
            return True
        user = request.env.user
        return (step.step_type == 'task'
                and user.has_group('hocba_employees.group_hocba_giaovu')
                and e.x_employee_type_id.code == 'teacher')

    def _onb_step_response(self, step):
        return request.make_json_response(
            self._onb_emp_item(step.employee_id.sudo()))

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/complete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_complete(self, step_id, **kw):
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        if not self._onb_can_act(step):
            return request.make_json_response(
                {'error': 'forbidden',
                 'message': 'Bạn không có quyền xử lý bước này.'}, status=403)
        payload = request.get_json_data()
        try:
            step.with_user(request.env.user).action_complete(
                note=(payload.get('note') or '').strip() or None)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=422)
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/evaluate',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_evaluate(self, step_id, **kw):
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        if not self._can_eval_emp(step.employee_id):
            return request.make_json_response(
                {'error': 'forbidden',
                 'message': 'Bạn không có quyền đánh giá nhân viên này.'},
                status=403)
        payload = request.get_json_data()
        result = payload.get('result')
        if result not in ('pass', 'extend', 'fail'):
            return request.make_json_response({'error': 'bad_request'},
                                              status=400)
        try:
            step.with_user(request.env.user).action_evaluate(
                result, note=(payload.get('note') or '').strip() or None,
                eval_date=payload.get('date') or None)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=422)
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/due',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_due(self, step_id, **kw):
        # Sửa hạn tay từng ca: chỉ HR Manager
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        payload = request.get_json_data()
        step.write({'due_date': payload.get('dueDate') or False})
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/employees/<int:emp_id>/onboarding/assign',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_assign(self, emp_id, **kw):
        # Gán/đổi quy trình tay: chỉ HR Manager
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        payload = request.get_json_data()
        tpl = request.env['hb.onboarding.template'].sudo().browse(
            int(payload.get('templateId') or 0))
        if not tpl.exists():
            return request.make_json_response({'error': 'bad_request'},
                                              status=400)
        e._hocba_assign_onboarding(template=tpl)
        return request.make_json_response(self._onb_emp_item(e))

    @http.route('/hocba-hrm/api/employees/<int:emp_id>/onboarding/finalize',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_finalize(self, emp_id, **kw):
        """Chốt hoàn tất nhận việc → Chính thức. Chỉ HR Manager; model tự
        kiểm lại điều kiện chuỗi nên ẩn nút ở FE không phải là chốt chặn."""
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        try:
            e.with_user(request.env.user).action_hocba_finalize_onboarding()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=422)
        return request.make_json_response(self._onb_emp_item(e))

    # ---- Cấu hình template (chỉ HR Manager) ---------------------------
    def _onb_tpl_json(self, tpl):
        return {
            'id': tpl.id, 'name': tpl.name, 'sequence': tpl.sequence,
            'active': tpl.active,
            'applyPositionTypes': tpl.apply_position_types or '',
            'applyWorkForm': tpl.apply_work_form,
            'applyEmployeeTypeIds': tpl.apply_employee_type_ids.ids,
            'steps': [{
                'id': s.id, 'sequence': s.sequence, 'name': s.name,
                'stepType': s.step_type, 'dueDays': s.due_days,
                'passCompletes': s.pass_completes,
                'isExtension': s.is_extension,
                'isIndependent': s.is_independent,
                'autoAction': s.auto_action, 'note': s.note or '',
            } for s in tpl.step_ids.sorted(lambda x: (x.sequence, x.id))],
        }

    def _onb_step_vals(self, payload_steps):
        # FE gửi mảng steps theo thứ tự → replace-all (snapshot nên NV đang
        # chạy không ảnh hưởng)
        return [(0, 0, {
            'sequence': i + 1,
            'name': (s.get('name') or '').strip(),
            'step_type': s.get('stepType') or 'task',
            'due_days': int(s.get('dueDays') or 0),
            'pass_completes': bool(s.get('passCompletes')),
            'is_extension': bool(s.get('isExtension')),
            'is_independent': bool(s.get('isIndependent')),
            'auto_action': s.get('autoAction') or 'none',
            'note': (s.get('note') or '').strip() or False,
        }) for i, s in enumerate(payload_steps)]

    @http.route('/hocba-hrm/api/onboarding/templates', auth='user',
                type='http', methods=['GET', 'POST'], csrf=False)
    def api_onb_templates(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'},
                                              status=410)
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        Tpl = request.env['hb.onboarding.template'].sudo()
        if request.httprequest.method == 'GET':
            emp_types = request.env['hocba.employee.type'].sudo().search([])
            return request.make_json_response({
                'templates': [
                    self._onb_tpl_json(t) for t in
                    Tpl.with_context(active_test=False).search([])],
                'employeeTypes': [{'id': t.id, 'name': t.name}
                                  for t in emp_types],
            })
        payload = request.get_json_data()
        vals = {
            'name': (payload.get('name') or '').strip(),
            'apply_position_types':
                (payload.get('applyPositionTypes') or '').strip() or False,
            'apply_work_form': payload.get('applyWorkForm') or 'any',
            'apply_employee_type_ids':
                [(6, 0, payload.get('applyEmployeeTypeIds') or [])],
            'step_ids': self._onb_step_vals(payload.get('steps') or []),
        }
        # Không truyền sequence → model tự xếp CUỐI danh sách (max+10)
        if payload.get('sequence') is not None:
            vals['sequence'] = int(payload['sequence'])
        try:
            tpl = Tpl.create(vals)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._onb_tpl_json(tpl))

    @http.route('/hocba-hrm/api/onboarding/templates/<int:tpl_id>',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_template_update(self, tpl_id, **kw):
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        tpl = request.env['hb.onboarding.template'].sudo().with_context(
            active_test=False).browse(tpl_id)
        if not tpl.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        payload = request.get_json_data()
        vals = {}
        for key, field in (('name', 'name'), ('sequence', 'sequence'),
                           ('applyWorkForm', 'apply_work_form'),
                           ('active', 'active')):
            if key in payload:
                vals[field] = payload[key]
        if 'applyPositionTypes' in payload:
            vals['apply_position_types'] = \
                (payload['applyPositionTypes'] or '').strip() or False
        if 'applyEmployeeTypeIds' in payload:
            vals['apply_employee_type_ids'] = \
                [(6, 0, payload['applyEmployeeTypeIds'] or [])]
        if 'steps' in payload:
            vals['step_ids'] = [(5, 0, 0)] + self._onb_step_vals(
                payload['steps'] or [])
        try:
            tpl.write(vals)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._onb_tpl_json(tpl))

    @http.route('/hocba-hrm/api/onboarding/templates/reorder',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_reorder(self, **kw):
        """Kéo-thả thứ tự quy trình: nhận danh sách id theo thứ tự mới
        (trên → dưới), ghi lại sequence. Thứ tự = quyền ưu tiên khi trùng."""
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        ids = request.get_json_data().get('ids') or []
        try:
            request.env['hb.onboarding.template'].sudo().action_reorder(
                [int(i) for i in ids])
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True})

    @http.route('/hocba-hrm/api/onboarding/templates/assign-pending',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_assign_pending(self, **kw):
        """Gán quy trình cho mọi NV thử việc chưa có bước (tạo template
        xong bấm 1 nút thay vì vào từng hồ sơ gán tay)."""
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        res = request.env['hb.onboarding.template'].sudo(
            ).action_assign_pending()
        return request.make_json_response(res)

    # ------------------------------------------------------------------
    # Badge "Nhận việc" ở thanh menu. Đếm ĐÚNG bước mà user bấm được —
    # phạm vi bám sát _onb_can_act, đếm rộng hơn là mời người ta bấm vào
    # 403. Chỉ search_count (gọi ở mọi màn nên phải rẻ); không quyền thì
    # 200 + count 0, để SPA khỏi bắt 403 cho một chi tiết trang trí.
    # Spec: docs/superpowers/specs/
    # 2026-08-12-nav-badge-viec-can-xu-ly-design.md §3.1
    # ------------------------------------------------------------------
    def _onb_pending_count(self, env):
        user = env.user
        Step = env['hb.onboarding.step'].sudo()
        # Chỉ đếm bước của NV CÒN thử việc: màn "Nhận việc" chỉ liệt kê
        # x_employment_status='probation', nên bước treo lại trên NV đã lên
        # chính thức/nghỉ là việc không màn nào bấm được — badge trỏ vào đó
        # là mời người ta click rồi không thấy gì (23 vs 4 người).
        waiting = Domain([('state', '=', 'open'),
                          ('employee_id.x_employment_status', '=',
                           'probation')])
        if (user.has_group('base.group_system')
                or user.has_group('hr.group_hr_manager')):
            return {'canAct': True, 'count': Step.search_count(waiting)}
        scopes = []
        emp = user.employee_id
        dept_ids = _managed_department_ids(env, emp)
        if dept_ids:
            scopes.append(Domain([('employee_id.department_id', 'in',
                                   dept_ids)]))
        # child_ids: chỉ người THỰC SỰ có cấp dưới mới là quản lý trực tiếp.
        # Thiếu vế này thì mọi nhân viên có hồ sơ đều ra canAct=True/count=0 —
        # cờ nói "có quyền" trong khi họ không duyệt được gì.
        if emp and emp.child_ids:
            scopes.append(Domain([('employee_id.parent_id.user_id', '=',
                                   user.id)]))
        if user.has_group('hocba_employees.group_hocba_giaovu'):
            # Giáo vụ chỉ đụng bước việc-cần-làm của giáo viên, không chấm
            # bước đánh giá (_onb_can_act).
            scopes.append(Domain([
                ('step_type', '=', 'task'),
                ('employee_id.x_employee_type_id.code', '=', 'teacher')]))
        if not scopes:
            return {'canAct': False, 'count': 0}
        # OR chứ không cộng dồn: người kiêm 2 vai (trưởng phòng + giáo vụ)
        # có bước khớp cả hai nhánh, cộng lại sẽ ra số ảo.
        return {'canAct': True,
                'count': Step.search_count(waiting & Domain.OR(scopes))}

    @http.route('/hocba-hrm/api/onboarding/pending-count', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_onb_pending_count(self, **kw):
        return request.make_json_response(
            self._onb_pending_count(request.env))

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
            self._employee_detail(e.sudo(), self._labels(),
                                  _cap_edit_emp(request.env), is_mgr,
                                  _cap_see_salary(request.env),
                                  _cap_manage_account(request.env)))

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
        # Cho chính chủ tự thêm NPT của mình; hoặc người quản lý trong phạm vi.
        if not (e == request.env.user.employee_id or self._can_edit_emp_record(e)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
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
        if not (d.employee_id == request.env.user.employee_id
                or self._can_edit_emp_record(d.employee_id)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
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
        if not (d.employee_id == request.env.user.employee_id
                or self._can_edit_emp_record(d.employee_id)):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
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
    # KHÔNG có vòng đời: thu hồi = xoá dòng, bàn giao = xoá + cấp lại.
    # ------------------------------------------------------------------
    def _conv_id(self, v):
        return int(v) if v not in ('', None, False) else False

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/asset', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_create(self, emp_id, **kw):
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        vals = {'employee_id': emp_id}
        for key, field in ASSET_FIELDS.items():
            if key in payload:
                v = payload[key]
                if field == 'asset_type_id':
                    v = self._conv_id(v)
                vals[field] = v if v not in ('', None) else False
        try:
            request.env['hr.employee.asset'].sudo().create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    @http.route('/hocba-hrm/api/asset/<int:asset_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_delete(self, asset_id, **kw):
        """Gỡ tài sản khỏi hồ sơ (thu hồi/bàn giao = sửa danh sách)."""
        a = request.env['hr.employee.asset'].sudo().browse(asset_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        e = a.employee_id
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            a.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    # ------------------------------------------------------------------
    # Offboarding — đơn thôi việc (self-service + duyệt 2 cấp)
    # ------------------------------------------------------------------
    # Nhãn + màu badge theo trạng thái (SPA render trực tiếp, không hard-code FE)
    OFFB_STATE_UI = {
        'draft': ('Nháp', 'gray'),
        'submitted': ('Chờ quản lý duyệt', 'amber'),
        'mgr_approved': ('Chờ HR duyệt', 'blue'),
        'hr_approved': ('Chờ hoàn tất', 'violet'),
        'done': ('Đã nghỉ', 'gray'),
        'refused': ('Từ chối', 'red'),
        'cancelled': ('Đã huỷ', 'gray'),
    }

    def _offb_json(self, rec):
        # Quyền tính theo user của env gắn trên record (route browse dưới
        # request.env nên chính là user hiện tại; test truyền env(user=...)).
        user = rec.env.user
        is_hr_mgr = rec.env.su or user.has_group('hr.group_hr_manager')
        try:
            rec._ensure_manages()
            manages = True
        except AccessError:
            manages = False
        own = rec.employee_id == user.employee_id
        label, kind = self.OFFB_STATE_UI.get(rec.state, (rec.state, 'gray'))
        return {
            'id': rec.id, 'name': rec.name,
            'employeeId': rec.employee_id.id,
            'employeeName': rec.employee_id.name,
            'source': rec.source, 'reasonType': rec.reason_type,
            'reason': rec.reason or '',
            'requestDate': rec.request_date and str(rec.request_date) or '',
            'expectedLeaveDate': rec.expected_leave_date
                and str(rec.expected_leave_date) or '',
            'state': rec.state, 'stateLabel': label, 'stateKind': kind,
            'assetCount': rec.asset_count,
            'assetCodes': rec.asset_codes or '',
            'mgrApprovedBy': rec.mgr_approved_by.name or '',
            'hrApprovedBy': rec.hr_approved_by.name or '',
            'canMgrApprove': rec.state == 'submitted' and manages,
            'canHrApprove': rec.state == 'mgr_approved' and is_hr_mgr,
            'canDone': rec.state == 'hr_approved' and is_hr_mgr,
            'canRefuse': (rec.state == 'submitted' and manages)
                or (rec.state == 'mgr_approved' and is_hr_mgr),
            'canCancel': rec.state in ('draft', 'submitted')
                and (own or is_hr_mgr),
        }

    def _offb_managed_employee_ids(self, env):
        """Phạm vi NV mà user hiện tại được xử lý đơn nghỉ việc — KHỚP quyền
        duyệt của model (_ensure_manages): HR=tất cả; trưởng phòng=phòng mình;
        quản lý trực tiếp=cấp dưới parent_id; giáo vụ=giáo viên.
        Không dùng _emp_scope_domain (helper chung, thiếu parent_id)."""
        user = env.user
        Emp = env['hr.employee'].sudo()
        if (user.has_group('base.group_system')
                or user.has_group('hr.group_hr_user')
                or user.has_group('hr.group_hr_manager')):
            return Emp.search([]).ids
        ids = set()
        emp = user.employee_id
        dept_ids = _managed_department_ids(env, emp)
        if dept_ids:
            ids.update(Emp.search([('department_id', 'in', dept_ids)]).ids)
        if emp:
            ids.update(Emp.search([('parent_id', '=', emp.id)]).ids)
        if user.has_group('hocba_employees.group_hocba_giaovu'):
            ids.update(Emp.search(
                [('x_employee_type_id.code', '=', 'teacher')]).ids)
        ids.discard(emp.id if emp else -1)
        return list(ids)

    # ------------------------------------------------------------------
    # Badge "Nghỉ việc" ở thanh menu — đếm đơn user có NÚT bấm, khớp cờ
    # can* của _offb_json: submitted→quản lý duyệt, mgr_approved→HR duyệt,
    # hr_approved→HR hoàn tất (vẫn là việc phải bấm mới xong).
    # KHÔNG dùng _offb_managed_employee_ids: helper đó trả toàn bộ NV cho
    # cả HR officer, trong khi _ensure_manages KHÔNG cho HR officer duyệt
    # → badge sẽ đếm những đơn họ không bấm được.
    # Spec: docs/superpowers/specs/
    # 2026-08-12-nav-badge-viec-can-xu-ly-design.md §3.2
    # ------------------------------------------------------------------
    def _offb_pending_count(self, env):
        user = env.user
        Off = env['hocba.offboarding'].sudo()
        if (user.has_group('base.group_system')
                or user.has_group('hr.group_hr_manager')):
            return {'canAct': True, 'count': Off.search_count(
                [('state', 'in', ['submitted', 'mgr_approved',
                                  'hr_approved'])])}
        emp = user.employee_id
        emp_ids = set()
        dept_ids = _managed_department_ids(env, emp)
        if dept_ids:
            emp_ids.update(env['hr.employee'].sudo().search(
                [('department_id', 'in', dept_ids)]).ids)
        if emp:
            emp_ids.update(env['hr.employee'].sudo().search(
                [('parent_id', '=', emp.id)]).ids)
        if user.has_group('hocba_employees.group_hocba_giaovu'):
            emp_ids.update(env['hr.employee'].sudo().search(
                [('x_employee_type_id.code', '=', 'teacher')]).ids)
        # Đơn của chính mình là việc của người khác duyệt, không phải của mình.
        emp_ids.discard(emp.id if emp else -1)
        if not emp_ids:
            return {'canAct': False, 'count': 0}
        return {'canAct': True, 'count': Off.search_count(
            [('state', '=', 'submitted'),
             ('employee_id', 'in', list(emp_ids))])}

    @http.route('/hocba-hrm/api/offboarding/pending-count', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_offb_pending_count(self, **kw):
        return request.make_json_response(
            self._offb_pending_count(request.env))

    @http.route('/hocba-hrm/api/offboarding/submit', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_offboarding_submit(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response(
                {'error': 'no_employee'}, status=400)
        payload = request.get_json_data() or {}
        try:
            rec = request.env['hocba.offboarding'].create({
                'employee_id': emp.id,
                'source': 'self',
                'reason_type': payload.get('reasonType') or 'voluntary',
                'reason': (payload.get('reason') or '').strip(),
                'expected_leave_date': payload.get('expectedLeaveDate')
                    or fields.Date.context_today(request.env.user),
            })
            rec.action_submit()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True, 'item': self._offb_json(rec)})

    @http.route('/hocba-hrm/api/offboarding/list', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_offboarding_list(self, **kw):
        env = request.env
        is_officer = _user_can_manage(env)
        emp = env.user.employee_id
        Off = env['hocba.offboarding'].sudo()
        mine_ids = Off.search(
            [('employee_id', '=', emp.id if emp else -1)]).ids
        managed_ids = []
        if is_officer:
            managed_ids = Off.search([
                ('employee_id', 'in',
                 self._offb_managed_employee_ids(env))]).ids
        # _offb_json tính quyền từ rec.env.user → browse dưới env user thật.
        # Scope đã khớp record rule (own/dept/parent/teacher/HR) nên đọc không
        # vướng ACL; nếu AccessError tức scope lệch rule — phải sửa scope.
        Offu = env['hocba.offboarding']
        return request.make_json_response({
            'isOfficer': is_officer,
            'isEmployee': bool(emp) and not is_officer,
            'mine': [self._offb_json(r) for r in Offu.browse(mine_ids)],
            'managed': [self._offb_json(r) for r in Offu.browse(managed_ids)],
        })

    @http.route('/hocba-hrm/api/offboarding/action', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_offboarding_action(self, **kw):
        payload = request.get_json_data() or {}
        rec_id = self._conv_id(payload.get('id'))
        action = payload.get('action')
        allowed = {'submit', 'mgr_approve', 'hr_approve',
                   'refuse', 'cancel', 'done'}
        if not rec_id or action not in allowed:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        rec = request.env['hocba.offboarding'].browse(rec_id)
        if not rec.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            getattr(rec, 'action_%s' % action)()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True, 'item': self._offb_json(rec)})

    # ------------------------------------------------------------------
    # Thăng tiến (F-007) — thêm mốc thăng tiến inline (HR Manager). Tạo
    # bản ghi sẽ tự cập nhật chức vụ/phòng ban NV (model). KHÔNG xoá.
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Nhập liệu thăng tiến nay đi từ màn Đánh giá: phiếu là CĂN CỨ của quyết
    # định, nên 3 ràng buộc dưới phải ở server — FE gửi gì cũng không lách
    # được. Spec: docs/superpowers/specs/
    # 2026-08-12-gop-danh-gia-thang-tien-vao-reviews-design.md §3
    # ------------------------------------------------------------------
    def _promo_validate_review(self, env, emp_id, review_id):
        """Kiểm phiếu TRƯỚC khi tạo bản ghi thăng tiến, không phải sau.

        Phiếu vừa là căn cứ vừa là BẰNG CHỨNG đổi lương (_check_rules), nên
        review_id phải nằm ngay trong vals của create — gắn sau thì ràng buộc
        bằng chứng đã nổ mất rồi."""
        rv = env['hb.performance.review'].sudo().browse(review_id)
        if not rv.exists():
            raise ValidationError('Không tìm thấy phiếu đánh giá.')
        if rv.employee_id.id != emp_id:
            raise ValidationError(
                'Phiếu đánh giá không phải của nhân viên này.')
        if rv.state not in ('confirmed', 'published'):
            raise ValidationError(
                'Phiếu đánh giá còn ở trạng thái Nháp — chốt phiếu trước khi '
                'tạo thăng tiến.')
        if env['hr.promotion.history'].sudo().search_count(
                [('review_id', '=', rv.id)]):
            raise ValidationError(
                'Phiếu đánh giá này đã gắn với một quyết định thăng tiến.')
        return rv

    @http.route('/hocba-hrm/api/review/<int:review_id>/promotion',
                auth='user', type='http', methods=['GET'], csrf=False)
    def api_review_promotion(self, review_id, **kw):
        """Phiếu này đã dẫn tới quyết định thăng tiến nào chưa — để màn Đánh
        giá hiện liên kết thay vì mời bấm tạo lần hai. Đặt ở hocba_hrm chứ
        không thêm vào payload của hocba_reviews: review_id là trường của
        module này."""
        rv = request.env['hb.performance.review'].sudo().browse(review_id)
        if not rv.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        if not self._emp_in_scope(rv.employee_id):
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        promo = request.env['hr.promotion.history'].sudo().search(
            [('review_id', '=', rv.id)], limit=1)
        if not promo:
            return request.make_json_response({'promotion': None})
        return request.make_json_response({'promotion': {
            'id': promo.id,
            'date': _d(promo.date_effective),
            'toJob': promo.to_job_id.name or '',
            'decisionRef': promo.decision_ref or '',
        }})

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
            rv_id = self._conv_id(payload.get('reviewId'))
            if rv_id:
                self._promo_validate_review(request.env, emp_id, rv_id)
                vals['review_id'] = rv_id
            request.env['hr.promotion.history'].create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)

    # ------------------------------------------------------------------
    # Lộ trình sự nghiệp (ý C họp 2026-08-07). emp_id = 0 → chính mình.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/career/<int:emp_id>', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_career(self, emp_id, **kw):
        try:
            out = _career_payload(request.env, emp_id)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except (ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(out)

    # ------------------------------------------------------------------
    # Bảng vinh danh (ý D họp 2026-08-07) — đọc: mọi user; ghi: HR.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/honor/board', auth='user', type='http',
                methods=['GET'], csrf=False)
    def api_honor_board(self, **kw):
        return request.make_json_response(_honor_board(request.env))

    @http.route('/hocba-hrm/api/honor/entry', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_honor_create(self, **kw):
        try:
            out = _honor_create(request.env, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(out)

    @http.route('/hocba-hrm/api/honor/entry/<int:entry_id>/archive',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_honor_archive(self, entry_id, **kw):
        try:
            out = _honor_archive(request.env, entry_id)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(out)

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
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        vals = self._cert_vals(request.get_json_data())
        vals['employee_id'] = emp_id
        try:
            request.env['hr.employee.skill'].sudo().create(vals)
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
        c = request.env['hr.employee.skill'].sudo().browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(c.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
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
        c = request.env['hr.employee.skill'].sudo().browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(c.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
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
        c = request.env['hr.employee.skill'].sudo().browse(cert_id)
        if not c.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(c.employee_id):
            return request.make_json_response({'error': 'forbidden'}, status=403)
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

    def _dependent_meta(self, env):
        """Lựa chọn cho form Người phụ thuộc — khả dụng cho MỌI user đăng nhập
        (self-service NV tự khai NPT của mình). Chỉ trả selection, không lộ
        danh sách nhạy cảm như /api/form/meta."""
        return {'relationship': list(
            env['hr.employee.dependent']._fields['relationship']
            ._description_selection(env))}

    @http.route('/hocba-hrm/api/dependent/meta', auth='user',
                type='http', methods=['GET'])
    def api_dependent_meta(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        return request.make_json_response(self._dependent_meta(request.env))

    @http.route('/hocba-hrm/api/form/meta', auth='user', type='http', methods=['GET'])
    def api_form_meta(self, **kw):
        """Metadata cho form Thêm/Sửa nhân viên: phòng ban, chức danh, các lựa
        chọn (hình thức/tình trạng/loại vị trí). Cho phép cả TP/Giáo vụ
        (canEditEmp); phòng ban giới hạn theo phạm vi của Trưởng phòng."""
        _, is_mgr = self._hr_flags()
        if not _cap_edit_emp(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        env = request.env
        Emp = env['hr.employee']

        def opts(fname):
            return list(Emp._fields[fname]._description_selection(env))

        # Trưởng phòng chỉ chọn được phòng mình quản lý (gồm phòng con); HR/Admin/
        # Giáo vụ thấy mọi phòng (GV tạo giáo viên — phòng nào cũng hợp lệ).
        user = env.user
        is_hr_any = (user.has_group('base.group_system')
                     or user.has_group('hr.group_hr_user')
                     or user.has_group('hr.group_hr_manager'))
        if is_hr_any or user.has_group('hocba_employees.group_hocba_giaovu'):
            dep_domain = []
        else:
            managed = _managed_department_ids(env, user.employee_id)
            dep_domain = [('id', 'in', managed)] if managed else [('id', '=', 0)]

        # Giáo vụ "thuần" chỉ được chào đúng loại Giáo viên: phạm vi của họ là
        # x_employee_type_id.code == 'teacher', chọn loại khác thì hồ sơ rơi ra
        # ngoài phạm vi và bị chặn ở api_employee_create/update. Bày ra rồi từ
        # chối sau khi điền xong cả form là hành người dùng.
        type_domain = []
        if (user.has_group('hocba_employees.group_hocba_giaovu')
                and not is_hr_any):
            type_domain = [('code', '=', 'teacher')]

        return request.make_json_response({
            'departments': [{'id': d.id, 'name': d.name}
                            for d in env['hr.department'].sudo().search(dep_domain, order='name')],
            'jobs': [{'id': j.id, 'name': j.name, 'dep': j.department_id.id}
                     for j in env['hr.job'].sudo().search([], order='name')],
            'workForm': opts('x_work_form'),
            'status': opts('x_employment_status'),
            'position': opts('x_position_type'),
            # Tag loại nhân sự cho ô chọn ở form Thêm/Sửa nhân viên.
            'empTypes': [{'id': t.id, 'name': t.name, 'code': t.code or ''}
                         for t in env['hocba.employee.type'].sudo().search(
                             type_domain)],
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
            'banks': _bank_options(env),
        })

    def _split_form_payload(self, payload, is_hr, is_mgr):
        """Tách payload thành (vals hr.employee, vals hr.version) theo tầng quyền.
        Field ngoài whitelist hoặc vượt quyền sẽ bị bỏ qua (không ghi)."""
        def allowed(tier):
            return tier == 'core' or (tier == 'hr' and is_hr) or (tier == 'mgr' and is_mgr)

        def conv(field, val):
            if field in ('department_id', 'job_id', 'x_employee_type_id'):
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
        _, is_mgr = self._hr_flags()
        if not _cap_edit_emp(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        if not (emp_vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập họ tên.'}, status=400)
        # Giáo vụ (phạm vi = giáo viên): form CÓ ô "loại nhân sự" nhưng
        # api_form_meta chỉ chào đúng loại Giáo viên, và ô này được phép để
        # trống → chốt mặc định là giáo viên, không thì hồ sơ vừa tạo đã nằm
        # ngoài phạm vi và bị chặn ngay ở dưới.
        u = request.env.user
        if (u.has_group('hocba_employees.group_hocba_giaovu')
                and not u.has_group('base.group_system')
                and not u.has_group('hr.group_hr_user')
                and not u.has_group('hr.group_hr_manager')
                and not emp_vals.get('x_employee_type_id')):
            tt = request.env['hocba.employee.type'].sudo().search(
                [('code', '=', 'teacher')], limit=1)
            if tt:
                emp_vals['x_employee_type_id'] = tt.id
        try:
            # Ghi sudo sau khi đã kiểm quyền (TP/GV không có ACL Odoo trên hr.employee).
            e = request.env['hr.employee'].sudo().create(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
            # NV mới phải nằm trong phạm vi người tạo (TP: phòng mình; GV: giáo viên).
            if not self._emp_in_scope(e):
                request.env.cr.rollback()
                return request.make_json_response(
                    {'error': 'forbidden',
                     'message': 'Ngoài phạm vi quản lý của bạn.'}, status=403)
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
            self._employee_detail(e.sudo(), self._labels(),
                                  _cap_edit_emp(request.env), is_mgr,
                                  _cap_see_salary(request.env),
                                  _cap_manage_account(request.env)))

    @http.route('/hocba-hrm/api/employee/<int:emp_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_update(self, emp_id, **kw):
        """Cập nhật nhân viên từ SPA (POST cùng path với GET detail). Ghi KHÔNG
        sudo → model tự kiểm quyền + ràng buộc."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        _, is_mgr = self._hr_flags()
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        is_hr = _cap_edit_emp(request.env)
        payload = request.get_json_data()
        emp_vals, ver_vals = self._split_form_payload(payload, is_hr, is_mgr)
        try:
            if emp_vals:
                e.sudo().write(emp_vals)
            if ver_vals:
                e.version_id.sudo().write(ver_vals)
                if 'wage' in ver_vals and ver_vals['wage'] is not None:
                    contracts = request.env['hb.contract'].sudo().search([('employee_id', '=', e.id)])
                    if contracts:
                        contracts.write({'wage': ver_vals['wage']})
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự đã tồn tại. Vui lòng nhập mã khác.'}, status=400)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        # Kiểm phạm vi LẠI SAU khi ghi, y như đường tạo mới (api_employee_create).
        # _can_edit_emp_record ở trên chỉ soi hồ sơ TRƯỚC khi sửa, mà đúng hai
        # field quyết định phạm vi lại nằm trong form: "Loại nhân sự"
        # (x_employee_type_id — phạm vi Giáo vụ) và "Phòng ban" (department_id —
        # phạm vi Trưởng phòng). Thiếu bước này thì Giáo vụ đổi giáo viên thành
        # NV văn phòng là hồ sơ biến mất khỏi danh sách của chính họ, không ai
        # gọi lại được.
        if not self._emp_in_scope(e):
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'forbidden',
                 'message': 'Thay đổi này đẩy hồ sơ ra ngoài phạm vi quản lý '
                            'của bạn. Nhờ HR đổi giúp.'}, status=403)
        return request.make_json_response(
            self._employee_detail(e.sudo(), self._labels(),
                                  _cap_edit_emp(request.env), is_mgr,
                                  _cap_see_salary(request.env),
                                  _cap_manage_account(request.env)))

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_account_create(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_create(request.env, emp_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'needs_confirm', 'message': str(ex)}, status=409)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account/reset',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_account_reset(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_reset(request.env, emp_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/me/password', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_me_change_password(self, **kw):
        """Tự đổi mật khẩu — mọi vai trò, không gắn với hồ sơ NV nào (HR/Admin
        không có màn "Hồ sơ của tôi" nhưng vẫn phải đổi được mật khẩu)."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _me_change_password(request.env, request.get_json_data())
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/employee/<int:emp_id>/account/active',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_account_active(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            active = request.get_json_data().get('active')
            # Ép kiểu lỏng sẽ đảo ngược thao tác: bool('false') là True.
            # Từ chối thẳng thay vì đoán ý.
            if not isinstance(active, bool):
                raise ValidationError('Tham số "active" phải là true/false.')
            data = _account_set_active(request.env, emp_id, active)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except (ValidationError, UserError) as ex:
            # UserError: res.users.write('active') có luật riêng của Odoo lõi.
            # Các guard trong _account_set_active chặn trước hết những ca đã
            # biết, nhưng bắt ở đây để nếu Odoo nâng cấp thêm luật thì SPA
            # nhận 400 kèm thông điệp, thay vì 500 kèm traceback.
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/accounts', auth='user', type='http',
                methods=['GET'])
    def api_accounts(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _account_list(request.env)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/departments', auth='user', type='http',
                methods=['GET'])
    def api_departments(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        archived = kw.get('archived') in ('1', 'true', 'True')
        try:
            data = _dept_list(request.env, archived=archived)
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/department', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_department_create(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_create(request.env, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except IntegrityError:
            # Tạo phòng ban giờ kèm tạo NV + tài khoản → đụng unique mã NV /
            # login. Rollback cả cụm: không để lại phòng ban mồ côi.
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự hoặc tên đăng nhập đã tồn tại.'},
                status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/department/<int:dept_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_department_update(self, dept_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_update(request.env, dept_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự hoặc tên đăng nhập đã tồn tại.'},
                status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/department/<int:dept_id>/archive', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_department_archive(self, dept_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        try:
            data = _dept_archive(request.env, dept_id, request.get_json_data())
        except AccessError as ex:
            return request.make_json_response(
                {'error': 'forbidden', 'message': str(ex)}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(data)

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
        # Vai trò Tài chính (module hocba_finance có thể chưa cài → guard).
        def _has_group_safe(xmlid):
            try:
                return user.has_group(xmlid)
            except Exception:  # noqa: BLE001 - group/module chưa tồn tại
                return False
        is_finance = _has_group_safe('hocba_finance.group_finance_user')
        is_finance_mgr = _has_group_safe('hocba_finance.group_finance_manager')
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
        if is_finance_mgr:
            roles.append('Giám đốc Tài chính')
        elif is_finance:
            roles.append('Kế toán')
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
            'isFinance': is_finance,
            'isFinanceManager': is_finance_mgr,
            'canManage': can_manage,
            'canEditEmp': _cap_edit_emp(request.env),
            'canSeeSalary': _cap_see_salary(request.env),
            'canManageAccount': _cap_manage_account(request.env),
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

    @http.route('/hocba-hrm/api/dashboard/stats', auth='user',
                type='http', methods=['GET'])
    def api_dashboard_stats(self, **kw):
        """KPI + biểu đồ dashboard tổng quan nhân sự (mẫu Lark 6.1).
        Dữ liệu tổng hợp (không lộ hồ sơ lẻ), phạm vi vẫn theo vai trò."""
        if not SPA_ENABLED:
            return request.make_json_response(
                {'error': 'spa_disabled'}, status=410)
        return request.make_json_response(_dashboard_stats(request.env))

    @http.route('/hocba-hrm/api/dashboard/recruitment', auth='user',
                type='http', methods=['GET'])
    def api_dashboard_recruitment(self, **kw):
        """Tab Tuyển dụng — dữ liệu toàn công ty nên chỉ HR/Admin."""
        if not SPA_ENABLED:
            return request.make_json_response(
                {'error': 'spa_disabled'}, status=410)
        is_hr, _ = self._hr_flags()
        if not (is_hr or request.env.user.has_group('base.group_system')):
            return request.make_json_response(
                {'error': 'forbidden'}, status=403)
        return request.make_json_response(
            _dashboard_recruitment(request.env))

    @http.route('/hocba-hrm/api/dashboard/attendance', auth='user',
                type='http', methods=['GET'])
    def api_dashboard_attendance(self, **kw):
        """Tab Chấm công — HR thấy tất cả; trưởng phòng/giáo vụ theo scope."""
        if not SPA_ENABLED:
            return request.make_json_response(
                {'error': 'spa_disabled'}, status=410)
        if _dash_scope_emp_ids(request.env) == []:
            return request.make_json_response(
                {'error': 'forbidden'}, status=403)
        return request.make_json_response(
            _dashboard_attendance(request.env))

    @http.route('/hocba-hrm/api/dashboard/timeoff', auth='user',
                type='http', methods=['GET'])
    def api_dashboard_timeoff(self, **kw):
        """Tab Nghỉ phép — HR thấy tất cả; trưởng phòng/giáo vụ theo scope."""
        if not SPA_ENABLED:
            return request.make_json_response(
                {'error': 'spa_disabled'}, status=410)
        if _dash_scope_emp_ids(request.env) == []:
            return request.make_json_response(
                {'error': 'forbidden'}, status=403)
        return request.make_json_response(_dashboard_timeoff(request.env))

    @http.route('/hocba-hrm/api/dashboard/payroll', auth='user',
                type='http', methods=['GET'])
    def api_dashboard_payroll(self, **kw):
        """Tab Lương — thông tin nhạy cảm, chỉ HR Manager/Admin."""
        if not SPA_ENABLED:
            return request.make_json_response(
                {'error': 'spa_disabled'}, status=410)
        _, is_mgr = self._hr_flags()
        if not (is_mgr or request.env.user.has_group('base.group_system')):
            return request.make_json_response(
                {'error': 'forbidden'}, status=403)
        return request.make_json_response(_dashboard_payroll(request.env))

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
        """Bảng theo dõi nhập việc: NV đang thử việc + các BƯỚC ĐỘNG của
        quy trình nhận việc (hb.onboarding.step). FE suy tiến độ/quá hạn
        từ steps + current trả về."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        # Phạm vi theo vai trò (giống danh sách NV): Quản lý chỉ thấy phòng mình,
        # Giáo vụ chỉ giáo viên, HR/Admin thấy tất cả.
        emps = request.env['hr.employee'].sudo().search(
            [('x_employment_status', '=', 'probation')] + self._emp_scope_domain(),
            order='x_probation_start desc, id')
        return request.make_json_response({
            'isHr': is_hr, 'isHrManager': is_mgr,
            'items': [self._onb_emp_item(e) for e in emps]})

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
    def api_attendance_history(self, month=None, dateFrom=None, dateTo=None, **kw):
        data = _att_me_history(request.env, month, date_from=dateFrom, date_to=dateTo)
        if data is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/attendance/me/history-full', auth='user',
                type='http', methods=['GET'])
    def api_attendance_history_full(self, month=None, dateFrom=None, dateTo=None, type=None, **kw):
        att_type = type if type in ('regular', 'ot', 'ctv', 'all') else 'all'
        data = _att_me_history_full(request.env, month, att_type, date_from=dateFrom, date_to=dateTo)
        if data is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/attendance/pending-count', auth='user',
                type='http', methods=['GET'])
    def api_attendance_pending_count(self, **kw):
        return request.make_json_response({'count': _att_pending_count(request.env)})

    @http.route('/hocba-hrm/api/attendance/manager-summary', auth='user',
                type='http', methods=['GET'])
    def api_attendance_manager_summary(self, month=None, dateFrom=None, dateTo=None, role=None, **kw):
        try:
            data = _att_manager_summary(request.env, month, date_from=dateFrom, date_to=dateTo, role=role)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/attendance/emp-history', auth='user',
                type='http', methods=['GET'])
    def api_attendance_emp_history(self, empId=None, month=None, dateFrom=None, dateTo=None, type=None, **kw):
        if not empId:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        att_type = type if type in ('regular', 'ot', 'ctv', 'all') else 'all'
        try:
            data = _att_emp_history(request.env, int(empId), month, att_type, date_from=dateFrom, date_to=dateTo)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except (UserError, ValidationError) as ex:
            return request.make_json_response(
                {'error': 'not_found', 'message': str(ex)}, status=404)
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
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        Att = request.env['hocba.attendance'].sudo()
        has_note = payload.get('note') is not None
        try:
            if emp.x_employment_status == 'official':
                Att._assert_check_allowed(emp, kind, has_note=has_note)
            else:
                Att._assert_shift_check_allowed(emp, kind, has_note=has_note)
            res = Att._do_check({
                'employee_id': emp.id,
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
                'note': payload.get('note'),
            }, kind)
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

    @http.route(['/hocba-hrm/api/attendance/shift/<int:shift_id>/check-in',
                 '/hocba-hrm/api/attendance/shift/<int:shift_id>/check-out'],
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_shift_attendance_check(self, shift_id, **kw):
        if not request.env.user.employee_id:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        if _user_can_manage(request.env):
            return request.make_json_response({'error': 'manager_no_checkin'}, status=403)
        payload = request.get_json_data()
        kind = 'out' if request.httprequest.path.endswith('check-out') else 'in'
        try:
            res = _shift_check(request.env, shift_id, kind, {
                'photo': payload.get('photo'),
                'descriptor': payload.get('descriptor') or [],
                'latitude': payload.get('latitude') or 0.0,
                'longitude': payload.get('longitude') or 0.0,
                'note': payload.get('note'),
            })
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except UserError as ex:
            code = str(ex)
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': code}, status=_CHECK_ERR_STATUS.get(code, 400))
        return request.make_json_response(res)

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

    # ------------------------------------------------------------------
    # Đơn chấm công (Gói 3): user gửi đơn sửa/tạo bản ghi → manager duyệt
    # (chỉnh giờ được) & áp dụng, hoặc từ chối. Spec:
    # docs/superpowers/specs/2026-06-17-attendance-correction-request-design.md
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/attendance/requests', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_attendance_request_create(self, **kw):
        try:
            row = _request_create(request.env, request.get_json_data() or {})
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/requests/mine', auth='user',
                type='http', methods=['GET'])
    def api_attendance_requests_mine(self, **kw):
        rows = _att_requests_mine(request.env)
        if rows is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response({'rows': rows})

    @http.route('/hocba-hrm/api/attendance/requests/pending', auth='user',
                type='http', methods=['GET'])
    def api_attendance_requests_pending(self, **kw):
        return request.make_json_response(
            {'rows': _att_requests_pending(request.env)})

    def _decide_request(self, req_id, approve):
        try:
            row = _request_decide(request.env, req_id, approve,
                                  request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/approve',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_approve(self, req_id, **kw):
        return self._decide_request(req_id, True)

    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/reject',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_reject(self, req_id, **kw):
        return self._decide_request(req_id, False)

    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/preview',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_preview(self, req_id, **kw):
        try:
            row = _request_preview(request.env, req_id,
                                   request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    # ------------------------------------------------------------------
    # Ca làm việc CTV/OT (Gói 4A): user đăng ký ca → manager duyệt/chỉnh/từ chối
    # hoặc thêm ca hộ; lịch hiển thị theo tuần. Spec:
    # docs/superpowers/specs/2026-06-17-shift-registration-design.md
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/shifts', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_shift_create(self, **kw):
        try:
            row = _shift_create(request.env, request.get_json_data() or {})
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'no_employee'}, status=400)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/shifts/week', auth='user', type='http', methods=['GET'])
    def api_shifts_week(self, monday=None, type=None, **kw):
        return request.make_json_response(_shifts_week(request.env, monday, type))

    @http.route('/hocba-hrm/api/shifts/ot', auth='user', type='http', methods=['GET'])
    def api_shifts_ot(self, month=None, dateFrom=None, dateTo=None, **kw):
        return request.make_json_response(_ot_table(request.env, month, date_from=dateFrom, date_to=dateTo))

    def _decide_shift(self, shift_id, approve):
        try:
            row = _shift_decide(request.env, shift_id, approve,
                                request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except ValidationError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/approve', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_approve(self, shift_id, **kw):
        return self._decide_shift(shift_id, True)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/reject', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_reject(self, shift_id, **kw):
        return self._decide_shift(shift_id, False)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/cancel', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_cancel(self, shift_id, **kw):
        try:
            res = _shift_cancel(request.env, shift_id)
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except UserError as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': str(ex)}, status=400)
        if res is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(res)

    @http.route('/hocba-hrm/api/shifts/<int:shift_id>/level', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_shift_set_level(self, shift_id, **kw):
        try:
            row = _shift_set_level(request.env, shift_id,
                                   (request.get_json_data() or {}).get('otLevel'))
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)

    @http.route('/hocba-hrm/api/attendance/config', auth='user', type='http', methods=['GET'])
    def api_attendance_config_get(self, **kw):
        """Lấy cấu hình chấm công (Policy + History). Chỉ Admin."""
        if not request.env.user.has_group('base.group_system'):
            return request.make_json_response({'error': 'forbidden'}, status=403)

        policy = request.env['hocba.attendance.policy'].sudo().get_policy()
        histories = request.env['hocba.attendance.period.history'].sudo().search([], order='apply_from desc')

        return request.make_json_response({
            'periodStartDay': policy.period_start_day,
            'periodEndDay': policy.period_end_day,
            'morningStart': policy.morning_start,
            'morningEnd': policy.morning_end,
            'eveningStart': policy.evening_start,
            'eveningEnd': policy.evening_end,
            'officeLat': policy.office_lat,
            'officeLng': policy.office_lng,
            'officeRadiusM': policy.office_radius_m,
            'officeMapUrl': policy.office_map_url,
            'faceThreshold': policy.face_threshold,
            'lateCutoff': policy.late_cutoff,
            'morningCreditCutoff': policy.morning_credit_cutoff,
            'stdWorkHours': policy.std_work_hours,
            'afternoonMarginHours': policy.afternoon_margin_hours,
            'violationFreeDays': policy.violation_free_days,
            'shiftWindowMinutes': policy.shift_window_minutes,
            'history': [{
                'id': h.id,
                'applyFrom': h.apply_from.isoformat(),
                'periodStartDay': h.period_start_day
            } for h in histories]
        })

    @http.route('/hocba-hrm/api/attendance/config', auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_config_set(self, **kw):
        """Cập nhật cấu hình chấm công. Chỉ Admin."""
        if not request.env.user.has_group('base.group_system'):
            return request.make_json_response({'error': 'forbidden'}, status=403)

        payload = request.get_json_data()
        policy = request.env['hocba.attendance.policy'].sudo().get_policy()

        try:
            # Cập nhật các trường trên policy
            policy_fields = [
                'periodStartDay', 'periodEndDay', 'morningStart', 'morningEnd', 'eveningStart', 'eveningEnd',
                'officeLat', 'officeLng', 'officeRadiusM', 'officeMapUrl', 'faceThreshold', 'lateCutoff',
                'morningCreditCutoff', 'stdWorkHours', 'afternoonMarginHours',
                'violationFreeDays', 'shiftWindowMinutes'
            ]
            vals = {}
            for pf in policy_fields:
                if pf in payload:
                    # Chuyển camelCase sang snake_case
                    snake_f = re.sub(r'(?<!^)(?=[A-Z])', '_', pf).lower()
                    vals[snake_f] = payload[pf]

            if vals:
                policy.write(vals)

            # Cập nhật hoặc thêm lịch sử
            if 'history' in payload:
                History = request.env['hocba.attendance.period.history'].sudo()
                for h_data in payload['history']:
                    if h_data.get('id'):
                        History.browse(h_data['id']).write({
                            'apply_from': h_data['applyFrom'],
                            'period_start_day': int(h_data['periodStartDay'])
                        })
                    else:
                        History.create({
                            'apply_from': h_data['applyFrom'],
                            'period_start_day': int(h_data['periodStartDay'])
                        })

            # Xóa nếu có deleteIds
            if 'deleteHistoryIds' in payload:
                request.env['hocba.attendance.period.history'].sudo().browse(payload['deleteHistoryIds']).unlink()

        except (ValidationError, UserError, ValueError) as ex:
            request.env.cr.rollback()
            return request.make_json_response({'error': 'rejected', 'message': str(ex)}, status=400)

        return self.api_attendance_config_get()

    @http.route('/hocba-hrm/api/employees/search', auth='user',
                type='http', methods=['GET'])
    def api_employee_search(self, q=None, **kw):
        return request.make_json_response(
            {'rows': _employee_search(request.env, q)})

    # ── Teaching Schedule API ─────────────────────────────────────────────────

    @http.route('/hocba-hrm/api/teaching/schedule', auth='user',
                type='http', methods=['GET'])
    def api_teaching_schedule(self, date=None, monday=None, **kw):
        """Lịch dạy của giáo viên đang đăng nhập.
        ?date=YYYY-MM-DD  → buổi dạy trong ngày đó
        ?monday=YYYY-MM-DD → buổi dạy trong tuần (7 ngày)
        """
        env = request.env
        emp = env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)
        if not emp.x_cms_user_id:
            return request.make_json_response({'error': 'not_teacher', 'rows': []})

        policy = env['hocba.attendance.policy'].sudo().get_policy()

        if monday:
            try:
                mon = datetime.strptime(monday, '%Y-%m-%d').date()
            except ValueError:
                return request.make_json_response({'error': 'invalid_date'}, status=400)
            rows = _teaching_week_rows(env, emp, mon, policy)
            return request.make_json_response({'monday': monday, 'rows': rows})

        if date:
            try:
                target = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return request.make_json_response({'error': 'invalid_date'}, status=400)
        else:
            target = fields.Date.context_today(env.user)

        sessions_raw = get_sessions_for_tutor(emp.x_cms_user_id, target)
        session_ids = [r['id'] for r in sessions_raw]
        att_map = {}
        for att in env['hocba.teaching.attendance'].sudo().search(
                [('cms_session_id', 'in', session_ids), ('employee_id', '=', emp.id)]):
            att_map[att.cms_session_id] = att

        now_utc = fields.Datetime.now()
        rows = []
        for raw in sessions_raw:
            sd = session_to_dict(raw)
            att = att_map.get(sd['id'])
            rows.append(_teaching_session_row(sd, att, policy, now_utc))

        return request.make_json_response({'date': str(target), 'rows': rows})

    @http.route('/hocba-hrm/api/teaching/days', auth='user',
                type='http', methods=['GET'])
    def api_teaching_days(self, **kw):
        """Các ngày có lịch dạy của GV đang đăng nhập trong khoảng [from, to].
        Dùng để đánh dấu ngày dạy trên lịch năm/tháng (tab "Lịch").
        → { 'isTeacher': bool, 'days': [ { 'date': 'YYYY-MM-DD', 'count': N } ] }
        """
        payload, status = _teaching_days_payload(
            request.env, kw.get('from'), kw.get('to'))
        return request.make_json_response(payload, status=status)

    @http.route('/hocba-hrm/api/teaching/sessions/<string:session_id>/check-in',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_teaching_check_in(self, session_id, **kw):
        return self._teaching_do_check(session_id, 'in')

    @http.route('/hocba-hrm/api/teaching/sessions/<string:session_id>/check-out',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_teaching_check_out(self, session_id, **kw):
        return self._teaching_do_check(session_id, 'out')

    def _teaching_do_check(self, session_id, kind):
        env = request.env
        emp = env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)
        if not emp.x_cms_user_id:
            return request.make_json_response({'error': 'not_teacher'}, status=403)

        payload = request.get_json_data() or {}

        # Tìm buổi học trong CMS theo session_id (không phụ thuộc ngày)
        today = fields.Date.context_today(env.user)
        # Thử ngày hôm nay trước, nếu không có thì lấy từ attendance record đã có
        sessions_today = get_sessions_for_tutor(emp.x_cms_user_id, today)
        session_info = next((r for r in sessions_today if r['id'] == session_id), None)

        if not session_info:
            # Kiểm tra xem có attendance record không để lấy ngày
            att = env['hocba.teaching.attendance'].sudo().search(
                [('cms_session_id', '=', session_id), ('employee_id', '=', emp.id)], limit=1)
            if att and att.session_date:
                sessions_on_date = get_sessions_for_tutor(emp.x_cms_user_id, att.session_date)
                session_info = next((r for r in sessions_on_date if r['id'] == session_id), None)

        if not session_info:
            return request.make_json_response({'error': 'session_not_found'}, status=404)

        att_model = env['hocba.teaching.attendance']
        try:
            att_model.sudo()._assert_allowed(session_info, emp, kind)
        except UserError as ex:
            err = str(ex)
            status_map = {
                'outside_shift_window': 403,
                'already_checked_in': 409,
                'not_checked_in': 409,
                'already_checked_out': 409,
            }
            return request.make_json_response(
                {'error': err}, status=status_map.get(err, 400))

        rec = att_model.sudo()._do_check(session_info, emp, payload, kind)
        return request.make_json_response({
            'recordId': rec.id,
            'kind': kind,
            'faceSuspect': rec.face_suspect,
            'outOfZone': rec.out_of_zone,
            'outOfWindow': rec.out_of_window,
            'faceScore': rec.check_in_face_score if kind == 'in' else rec.check_out_face_score,
        })
