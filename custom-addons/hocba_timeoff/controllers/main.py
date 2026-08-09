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
from odoo.tools import html2plaintext

from .workday_xlsx import (
    XLSX_MIME, WorkdayImportError, build_template, parse_workdays_xlsx,
)

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
    'hb_leave_type_teaching_off',
)

# Loại nghỉ riêng cho giáo viên — nghỉ theo BUỔI dạy (session-first), không trừ
# quỹ. KHÔNG hiện trong dropdown "nghỉ dài ngày"; chỉ dùng cho luồng nghỉ buổi.
TEACHING_OFF_XMLID = 'hb_leave_type_teaching_off'

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


# Ngưỡng cảnh báo "sắp hết phép" (Phase 1, bảng Quỹ phép). Số ngày còn lại
# <= ngưỡng này thì NV bị đếm vào kpi.lowBalance. Chốt cùng nhóm (open Q#3).
LOW_BALANCE_DAYS = 2.0

# Ngưỡng "còn nhiều Phép Năm chưa dùng" → cảnh báo sắp mất phép cuối năm
# (Phase 3, open Q#3). Còn >= ngưỡng này (tính riêng Phép Năm) thì at-risk.
AT_RISK_DAYS = 5.0

# Ngưỡng cảnh báo trùng lịch nghỉ (Phase 4, open Q#3). Ngày có >= ngưỡng này
# người CÙNG PHÒNG nghỉ thì coi là "quá tải" → FE tô đậm cảnh báo.
OVERLAP_WARN = 3

# "Quá hạn" trong module này CHỈ có một nghĩa: đơn còn chờ duyệt mà ngày BẮT
# ĐẦU nghỉ đã qua (xem _lapsed_info). SLA theo tuổi đơn kể từ ngày nộp (Phase 8)
# đã bỏ — hai khái niệm cùng tên "quá hạn" làm số liệu giữa các tab lệch nhau.
# Ngưỡng tô đậm dòng ở bảng "Đơn quá hạn duyệt" (dashboard).
OVERDUE_DEEP_DAYS = 3


def _carryover_expire_date(env, year):
    """Ngày hết hạn phép năm để hiển thị cảnh báo (Phase 3).

    Chưa có cấu hình carry-over trong hb.timeoff.policy.rule (open Q#4) → mặc
    định cuối năm đang xem. Khi nhóm thêm quy tắc chuyển/hết hạn phép, ĐỔI Ở ĐÂY."""
    return '%d-12-31' % year


# ---------------------------------------------------------------------------
# Helper cấp module (nhận env) — để controller dùng dưới request VÀ test gọi
# trực tiếp với self.env(user=...) theo quy ước test của repo (TransactionCase).
# Các method cùng tên trong controller chỉ là lớp mỏng ủy quyền xuống đây.
# ---------------------------------------------------------------------------
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


def _scope_for(env):
    """Phân quyền Nghỉ phép (xem docstring chi tiết ở HocBaTimeoff._scope)."""
    user = env.user
    see_all = (user.has_group('base.group_system')
               or user.has_group('hr.group_hr_manager')
               or user.has_group('hr.group_hr_user'))
    is_hr_manager = (user.has_group('base.group_system')
                     or user.has_group('hr.group_hr_manager'))
    is_giaovu = user.has_group('hocba_employees.group_hocba_giaovu')
    dept_ids = [] if see_all else _managed_department_ids(env, user.employee_id)
    is_role_account = see_all or is_giaovu or bool(dept_ids)
    return {
        'isHrManager': is_hr_manager,
        'isDeptManager': bool(dept_ids),
        'isGiaovu': is_giaovu,
        'isEmployee': not is_role_account,
        'canApprove': see_all or bool(dept_ids),
        'seeAll': see_all,
        'deptIds': dept_ids,
    }


def _dept_domain(scope):
    """Domain lọc phòng ban: HR/Admin = tất cả, Trưởng phòng = phòng được giao."""
    if scope['seeAll']:
        return []
    return [('department_id', 'in', scope['deptIds'])]


def _approvals_domain(scope):
    """Domain tab "Chờ duyệt" hợp nhất: đơn chờ duyệt MỚI + đơn validate có
    yêu cầu rút đang chờ (Phase 7), lọc theo phạm vi phòng ban.

    Dùng chung cho GET /approvals VÀ payload refresh của decision/withdraw-decide
    — 3 nơi lệch nhau là bảng + badge "Chờ duyệt" tạm mất các dòng yêu cầu rút
    sau khi duyệt một đơn thường (bug đã gặp: FE ghi thẳng payload này vào cache).
    """
    return ['|',
            '&', ('state', 'in', list(PENDING_STATES)),
                 ('x_withdraw_state', '=', 'none'),
            '&', ('state', '=', 'validate'),
                 ('x_withdraw_state', '=', 'pending')] + _dept_domain(scope)


def _refused_domain(scope, dept_id, start, end):
    """Domain KPI "Đã từ chối" (dashboard Tổng quan): đơn bị từ chối trong năm,
    theo phạm vi phòng ban.

    Gồm CẢ đơn bị từ chối do duyệt yêu cầu rút (Phase 7) — Odoo đưa đơn về
    state 'refuse' và quỹ được hoàn — đúng nghĩa "tổng số đơn đã bị từ chối".
    """
    return [('state', '=', 'refuse'),
            ('date_from', '>=', start), ('date_from', '<=', end)] \
        + ([('department_id', '=', dept_id)] if dept_id else []) \
        + _dept_domain(scope)


def _scoped_departments(env, scope):
    """Phòng ban cho dropdown lọc: HR/Admin = tất cả, Trưởng phòng = phòng mình."""
    Dept = env['hr.department'].sudo()
    if scope['seeAll']:
        return Dept.search([], order='name')
    return Dept.browse(scope['deptIds'])


def _hb_leave_type_ids(env):
    """ID các loại nghỉ Học Bá — lọc theo cờ DB x_hb_managed (thay cho lọc
    cứng theo xml_id): loại admin tạo mới tự xuất hiện, loại tắt (active=False)
    tự ẩn khỏi SPA. HB_LEAVE_TYPE_XMLIDS giữ lại làm tài liệu danh sách 8 loại
    chuẩn; không còn dùng để lọc (migration seed cờ bằng danh sách riêng)."""
    return env['hr.leave.type'].sudo().search(
        [('x_hb_managed', '=', True)], order='id').ids


def _teaching_off_type_id(env):
    """ID loại nghỉ 'Nghỉ Buổi Dạy' (hoặc False nếu chưa seed)."""
    rec = env.ref('hocba_timeoff.%s' % TEACHING_OFF_XMLID, raise_if_not_found=False)
    return rec.id if rec else False


def _employee_balance_row(employee, alloc_types, annual_type_id=False,
                          expire_date=None):
    """1 dòng số dư của 1 NV theo tập loại nghỉ cần phân bổ (đã lọc sẵn).

    Phase 3: nếu truyền annual_type_id → tính atRisk (còn >= AT_RISK_DAYS ngày
    Phép Năm chưa dùng) + expireDate (ngày hết hạn để hiển thị)."""
    types_ctx = alloc_types.with_context(employee_id=employee.id)
    balances = []
    t_alloc = t_taken = t_remain = 0.0
    annual_remaining = None
    for lt in types_ctx:
        allocated = round(lt.max_leaves, 2)
        taken = round(lt.leaves_taken, 2)
        remaining = round(lt.virtual_remaining_leaves, 2)
        balances.append({
            'leaveTypeId': lt.id,
            'leaveType': lt.name,
            'allocated': allocated,
            'taken': taken,
            'remaining': remaining,
            'kind': _balance_kind(remaining),
        })
        t_alloc += allocated
        t_taken += taken
        t_remain += remaining
        if annual_type_id and lt.id == annual_type_id:
            annual_remaining = remaining
    at_risk = bool(annual_type_id and annual_remaining is not None
                   and annual_remaining >= AT_RISK_DAYS)
    return {
        'employeeId': employee.id,
        'employee': employee.name,
        'department': employee.department_id.name or '—',
        'balances': balances,
        'totalAllocated': round(t_alloc, 2),
        'totalTaken': round(t_taken, 2),
        'totalRemaining': round(t_remain, 2),
        'atRisk': at_risk,
        'expireDate': expire_date,
    }


def _balances_table(env, scope, year, dept_id=False, type_filter=False,
                    filter_mode=False):
    """Bảng số dư phép toàn nhân viên trong phạm vi (Phase 1 + Phase 3).

    Tái dùng đúng cơ chế của _balances(): đọc max_leaves / leaves_taken /
    virtual_remaining_leaves của hr.leave.type qua context employee_id. Cột số
    dư = các loại HB cần phân bổ (requires_allocation). year được giữ để hiển
    thị/lọc tương lai; số dư tính theo trạng thái phân bổ hiện tại (như tab
    "Của tôi"). Lặp NV với context = N+1 đọc — chấp nhận được ở quy mô hiện tại
    (ghi chú tối ưu _read_group nếu >200 NV).

    Phase 3: mỗi dòng có atRisk (còn >= AT_RISK_DAYS ngày Phép Năm) + expireDate.
    filter_mode='expiring' → CHỈ trả dòng at-risk; KPI vẫn tính trên TOÀN phạm vi."""
    Employee = env['hr.employee'].sudo()
    emp_domain = _dept_domain(scope)
    if dept_id:
        emp_domain = emp_domain + [('department_id', '=', dept_id)]
    employees = Employee.search(emp_domain, order='name')

    LeaveType = env['hr.leave.type'].sudo()
    alloc_types = LeaveType.browse(_hb_leave_type_ids(env)).filtered('requires_allocation')
    if type_filter:
        alloc_types = alloc_types.filtered(lambda t: t.id == type_filter)

    annual = env.ref('hocba_timeoff.hb_leave_type_annual', raise_if_not_found=False)
    annual_id = annual.id if annual else False
    expire_date = _carryover_expire_date(env, year)

    rows = []
    total_remaining_all = 0.0
    low_balance = 0
    at_risk_count = 0
    for emp in employees:
        row = _employee_balance_row(emp, alloc_types, annual_id, expire_date)
        rows.append(row)
        total_remaining_all += row['totalRemaining']
        if row['totalRemaining'] <= LOW_BALANCE_DAYS:
            low_balance += 1
        if row['atRisk']:
            at_risk_count += 1

    # KPI tính trên toàn phạm vi; chỉ lọc danh sách trả về khi xem "sắp mất phép".
    out_rows = [r for r in rows if r['atRisk']] if filter_mode == 'expiring' else rows

    return {
        'year': year,
        'atRiskDays': AT_RISK_DAYS,
        'expireDate': expire_date,
        'rows': out_rows,
        'leaveTypes': [{'id': lt.id, 'name': lt.name} for lt in alloc_types],
        'allDepartments': [{'id': d.id, 'name': d.name}
                           for d in _scoped_departments(env, scope)],
        'kpi': {
            'employees': len(rows),
            'totalRemaining': round(total_remaining_all, 1),
            'lowBalance': low_balance,
            'atRisk': at_risk_count,
        },
    }


def _apply_quota_adjustment(env, employee, leave_type, delta, reason, year):
    """Áp 1 điều chỉnh quỹ phép thủ công (Phase 2) — trả về delta đã áp.

    Cấp thêm (delta > 0): tạo 1 allocation regular mới đã duyệt = delta ngày.
    Trừ bớt (delta < 0): KHÔNG tạo allocation âm (DB chặn regular ≤ 0) — thay
    vào đó giảm các allocation đã duyệt của NV: từ chối (action_refuse) allocation
    bị trừ trọn, hoặc giảm number_of_days (vẫn > 0) cho phần lẻ. Chặn trừ vượt số
    dư (không cho remaining âm). Ghi 1 dòng hb.leave.adjustment liên kết allocation
    bị tác động. Mọi thao tác sudo (vai trò HR mới không có group hr_holidays)."""
    delta = round(float(delta), 2)
    if not delta:
        raise ValidationError('Số ngày điều chỉnh phải khác 0.')
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError('Vui lòng nhập lý do điều chỉnh.')

    Alloc = env['hr.leave.allocation'].sudo()
    lt_ctx = (env['hr.leave.type'].sudo()
              .with_context(employee_id=employee.id).browse(leave_type.id))
    remaining = lt_ctx.virtual_remaining_leaves

    touched = Alloc.browse()
    if delta > 0:
        alloc = Alloc.create({
            'name': 'Điều chỉnh quỹ: %s' % employee.name,
            'holiday_status_id': leave_type.id,
            'employee_id': employee.id,
            'number_of_days': delta,
            'allocation_type': 'regular',
            'date_from': '%d-01-01' % year,
            'date_to': '%d-12-31' % year,
        })
        alloc._action_validate()
        touched = alloc
    else:
        need = -delta
        if need > remaining + 1e-6:
            raise ValidationError(
                'Không đủ phép để trừ: nhân viên chỉ còn %.2f ngày.' % remaining)
        allocs = Alloc.search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('state', '=', 'validate'),
        ], order='id desc')
        for a in allocs:
            if need <= 1e-6:
                break
            d = a.number_of_days
            if d <= 0:
                continue
            if not touched:
                touched = a
            if d <= need + 1e-6:
                a.action_refuse()              # trừ trọn allocation
                need -= d
            else:
                a.write({'number_of_days': round(d - need, 2)})  # trừ phần lẻ
                need = 0
        if need > 1e-6:
            raise ValidationError('Không thể trừ đủ số ngày yêu cầu.')

    env['hb.leave.adjustment'].sudo().create({
        'employee_id': employee.id,
        'leave_type_id': leave_type.id,
        'delta_days': delta,
        'reason': reason,
        'allocation_id': touched.id if touched else False,
        'applied_by': env.user.employee_id.id if env.user.employee_id else False,
    })
    # max_leaves / virtual_remaining_leaves là field tính KHÔNG lưu — phải xả &
    # xoá cache sau khi đổi allocation để lần đọc số dư sau (row trả về / FE)
    # tính lại từ DB, không trả giá trị cũ đã cache trước khi điều chỉnh.
    env.flush_all()
    env.invalidate_all()
    return delta


def _adjustment_history(env, scope, employee_id=False, leave_type_id=False):
    """Lịch sử điều chỉnh quỹ trong phạm vi xem được (HR = tất cả, Trưởng phòng
    = NV phòng mình). Lọc thêm theo NV / loại nghỉ nếu truyền."""
    domain = []
    if not scope['seeAll']:
        domain.append(('employee_id.department_id', 'in', scope['deptIds']))
    if employee_id:
        domain.append(('employee_id', '=', employee_id))
    if leave_type_id:
        domain.append(('leave_type_id', '=', leave_type_id))
    recs = env['hb.leave.adjustment'].sudo().search(domain, limit=200)
    return [{
        'id': r.id,
        'employeeId': r.employee_id.id,
        'employee': r.employee_id.name,
        'leaveTypeId': r.leave_type_id.id,
        'leaveType': r.leave_type_id.name,
        'deltaDays': round(r.delta_days, 2),
        'reason': r.reason or '',
        'appliedBy': r.applied_by.name or '',
        'appliedDate': _d(r.applied_date),
    } for r in recs]


def _period_request_vals(leave_type, date_from, period):
    """Phase 6 — vals bổ sung cho đơn NỬA NGÀY.

    `period` ∈ {'am','pm'} (sáng/chiều) và loại nghỉ phải hỗ trợ half_day.
    Khi hợp lệ: đơn co về đúng 1 ngày (date_to = date_from) và đặt cùng buổi
    sáng/chiều → Odoo tính number_of_days = 0.5. Mọi trường hợp khác (cả ngày,
    loại nghỉ theo ngày, period rỗng/sai) → trả {} để giữ luồng cũ.
    """
    if not leave_type or leave_type.request_unit != 'half_day':
        return {}
    if period not in ('am', 'pm'):
        return {}
    return {
        'request_date_to': date_from,            # nửa ngày = đúng 1 ngày
        'request_date_from_period': period,
        'request_date_to_period': period,
    }


def _half_day_label(leave):
    """Nhãn buổi nghỉ nửa ngày: '' (cả ngày) / 'Sáng' / 'Chiều'. (Phase 6)"""
    if not leave.request_unit_half:
        return ''
    if leave.request_date_from_period != leave.request_date_to_period:
        return ''   # sáng → chiều = trọn 1 ngày
    return 'Sáng' if leave.request_date_from_period == 'am' else 'Chiều'


def _leave_day_bounds(leave):
    """Khoảng NGÀY thực của 1 đơn nghỉ (ưu tiên request_date_*, fallback date_*)."""
    d0 = leave.request_date_from or (leave.date_from and leave.date_from.date())
    d1 = leave.request_date_to or (leave.date_to and leave.date_to.date())
    return d0, d1


def _overlap_count(env, leave):
    """Số người CÙNG PHÒNG đang nghỉ (đơn đã duyệt) trùng khoảng ngày của đơn này —
    KHÔNG tính chính đơn. Dùng cho badge ở modal duyệt (Phase 4)."""
    d0, d1 = _leave_day_bounds(leave)
    if not d0 or not d1 or not leave.department_id:
        return 0
    return env['hr.leave'].sudo().search_count([
        ('id', '!=', leave.id),
        ('state', '=', 'validate'),
        ('department_id', '=', leave.department_id.id),
        ('date_from', '<=', '%s 23:59:59' % d1),
        ('date_to', '>=', '%s 00:00:00' % d0),
    ])


def _coverage_table(env, scope, date_from, date_to, dept_id=False):
    """Mức độ trùng lịch nghỉ theo NGÀY trong khoảng [date_from, date_to] (Phase 4).

    Mỗi ngày có ít nhất 1 người nghỉ (đơn state='validate', đã lọc phòng ban theo
    scope) → {date, count, employees:[...]}. Ngày không ai nghỉ được BỎ QUA để
    payload gọn (FE tra theo map date). KPI: tổng số ngày 'quá tải' (>= OVERLAP_WARN).
    Mọi thao tác sudo (vai trò duyệt không có group hr_holidays)."""
    start = fields.Date.to_date(date_from)
    end = fields.Date.to_date(date_to)
    if not start or not end or end < start:
        return {'days': [], 'overlapWarn': OVERLAP_WARN, 'overloadedDays': 0}

    domain = [('state', '=', 'validate'),
              ('date_from', '<=', '%s 23:59:59' % end),
              ('date_to', '>=', '%s 00:00:00' % start)] + _dept_domain(scope)
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    leaves = env['hr.leave'].sudo().search(domain, order='date_from')

    spans = []
    for l in leaves:
        d0, d1 = _leave_day_bounds(l)
        if d0 and d1:
            spans.append((d0, d1, l))

    days = []
    overloaded = 0
    cur = start
    while cur <= end:
        emps = [{
            'employeeId': l.employee_id.id,
            'employee': l.employee_id.name,
            'department': l.department_id.name or '—',
            'leaveType': l.holiday_status_id.name,
        } for d0, d1, l in spans if d0 <= cur <= d1]
        if emps:
            if len(emps) >= OVERLAP_WARN:
                overloaded += 1
            days.append({'date': _d(cur), 'count': len(emps), 'employees': emps})
        cur += timedelta(days=1)

    return {'days': days, 'overlapWarn': OVERLAP_WARN, 'overloadedDays': overloaded}


# ---------------------------------------------------------------------------
# Phase 8 — SLA duyệt đơn. Tuổi đơn = số ngày làm việc giữa create_date và today.
# ---------------------------------------------------------------------------
def _public_holiday_dates_env(env, start, end):
    """Tập date các ngày lễ toàn cục giao [start, end]. Dùng được ngoài request."""
    rows = env['resource.calendar.leaves'].sudo().search([
        ('calendar_id', '=', False),
        ('resource_id', '=', False),
        ('time_type', '=', 'leave'),
        ('date_from', '<=', '%s 23:59:59' % end),
        ('date_to', '>=', '%s 00:00:00' % start),
    ])
    days = set()
    for r in rows:
        d0 = max(r.date_from.date(), start)
        d1 = min(r.date_to.date(), end)
        cur = d0
        while cur <= d1:
            days.add(cur)
            cur += timedelta(days=1)
    return days


def _count_working_days_env(env, start, end):
    """Số ngày làm việc (T2–T6 + workday HR đánh dấu, trừ ngày lễ) trong
    [start, end]. Delegate về _working_dates_env để một chỗ duy nhất định
    nghĩa 'ngày làm việc' (tránh drift). Dùng dưới request VÀ test gọi trực tiếp."""
    return len(_working_dates_env(env, start, end))


# ---------------------------------------------------------------------------
# Phase 12 — Đơn lỡ hạn duyệt. Spec:
# docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
# ---------------------------------------------------------------------------
def _working_dates_env(env, start, end):
    """Danh sách NGÀY LÀM VIỆC (T2–T6 + workday HR, trừ lễ) trong [start, end]."""
    if not start or not end or end < start:
        return []
    work_extra = set(env['hb.work.day'].sudo().search([
        ('date', '>=', start), ('date', '<=', end)]).mapped('date'))
    holidays = _public_holiday_dates_env(env, start, end)
    days, cur = [], start
    while cur <= end:
        if (cur.weekday() < 5 or cur in work_extra) and cur not in holidays:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def _lapsed_info(env, leave):
    """Thông tin 'lỡ hạn duyệt' của 1 đơn (BR-L01→L03) — None nếu chưa lỡ hạn.

    Lỡ hạn = còn chờ duyệt mà ngày BẮT ĐẦU nghỉ đã qua. Đối chiếu
    hocba.attendance từng ngày nghỉ ĐÃ QUA (đến hết hôm qua): tổng work_credit
    trong ngày >= 0.5 là 'vẫn đi làm'; đơn NỬA NGÀY cần >= 1.0 mới tính (nửa
    làm + nửa nghỉ là khớp đơn). Loại 'Nghỉ Buổi Dạy' miễn đối chiếu — GV có
    thể vẫn chấm công ở trung tâm dù nghỉ 1 buổi dạy. Attendance đọc qua sudo:
    người duyệt không có ACL hocba.attendance; quyền phạm vi kiểm ở tầng gọi."""
    if leave.state not in PENDING_STATES:
        return None
    d0, d1 = _leave_day_bounds(leave)
    today = fields.Date.context_today(env.user)
    if not d0 or d0 >= today:
        return None

    yesterday = today - timedelta(days=1)
    lapsed_days = _count_working_days_env(env, d0, yesterday)
    exempt = leave.holiday_status_id.id == _teaching_off_type_id(env)

    day_checks, worked = [], 0
    if not exempt:
        dates = _working_dates_env(env, d0, min(d1 or yesterday, yesterday))
        if dates:
            atts = env['hocba.attendance'].sudo().search([
                ('employee_id', '=', leave.employee_id.id),
                ('date', 'in', dates)])
            credit_by_day = {}
            for a in atts:
                credit_by_day[a.date] = credit_by_day.get(a.date, 0.0) + a.work_credit
            # 'Nửa ngày thật sự' theo convention module (_half_day_label):
            # request_unit_half CHỈ báo đơn vị loại nghỉ là nửa ngày (Phép Năm
            # seed half_day → luôn True), KHÔNG có nghĩa đơn này là nửa ngày.
            # Đơn nửa ngày cần đủ công (1.0) mới là mâu thuẫn; đơn nguyên ngày
            # chỉ cần >= 0.5.
            is_half = bool(_half_day_label(leave))
            threshold = 1.0 if is_half else 0.5
            for d in dates:
                credit = credit_by_day.get(d, 0.0)
                is_worked = credit >= threshold
                worked += 1 if is_worked else 0
                day_checks.append({'date': _d(d), 'worked': is_worked,
                                   'workCredit': round(credit, 1)})

    checked = len(day_checks)
    suggestion = None
    if checked:
        if worked == 0:
            suggestion = 'approve'
        elif worked == checked:
            suggestion = 'refuse'
    return {
        'isLapsed': True,
        'lapsedDays': lapsed_days,
        'dayChecks': day_checks,
        'workedCount': worked,
        'checkedCount': checked,
        'suggestion': suggestion,
        'exempt': exempt,
    }


def _lapsed_summary_label(info):
    """Chuỗi tóm tắt đối chiếu (dùng cả trong chatter và bảng giám sát FE)."""
    if info['exempt']:
        return 'nghỉ buổi dạy — không đối chiếu chấm công'
    if not info['checkedCount']:
        return 'chưa có ngày nghỉ nào qua để đối chiếu'
    return 'đi làm %d/%d ngày nghỉ đã qua' % (
        info['workedCount'], info['checkedCount'])


def _lapsed_table(env, scope, dept_id=False):
    """Dữ liệu màn 'Giám sát duyệt đơn' (BR-L06): KPI + bảng đơn lỡ hạn
    + đếm theo phòng. sudo + lọc phòng ban tường minh theo scope."""
    today = fields.Date.context_today(env.user)
    domain = [('state', 'in', list(PENDING_STATES)),
              ('request_date_from', '<', today)] + _dept_domain(scope)
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    leaves = env['hr.leave'].sudo().search(domain, order='request_date_from, id')

    items, by_dept = [], {}
    n_approve = n_refuse = n_review = oldest = 0
    for leave in leaves:
        info = _lapsed_info(env, leave)
        if not info:
            continue
        if info['suggestion'] == 'approve':
            n_approve += 1
        elif info['suggestion'] == 'refuse':
            n_refuse += 1
        else:
            n_review += 1
        oldest = max(oldest, info['lapsedDays'])
        dept = leave.department_id or leave.employee_id.department_id
        row = by_dept.setdefault(dept.id or 0, {
            'id': dept.id or False, 'name': dept.name or '—', 'count': 0})
        row['count'] += 1
        items.append({
            'requestId': leave.id,
            'employee': leave.employee_id.name,
            'department': dept.name or '—',
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'days': round(leave.number_of_days, 2),
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'submittedAt': _d(leave.create_date.date()
                              if leave.create_date else None),
            'isEmergency': leave.x_is_emergency,
            'lapsedDays': info['lapsedDays'],
            'summary': _lapsed_summary_label(info),
            'suggestion': info['suggestion'],
            'workedCount': info['workedCount'],
            'checkedCount': info['checkedCount'],
            'exempt': info['exempt'],
        })
    items.sort(key=lambda r: r['lapsedDays'], reverse=True)
    return {
        'kpi': {'total': len(items), 'suggestApprove': n_approve,
                'suggestRefuse': n_refuse, 'needsReview': n_review,
                'oldestLapsedDays': oldest},
        'items': items,
        'byDepartment': sorted(by_dept.values(),
                               key=lambda r: r['count'], reverse=True),
    }


def _post_lapsed_decision_note(env, leave, action, info):
    """BR-L04: ghi vết 'duyệt trễ / từ chối đơn lỡ hạn' vào chatter.
    `info` phải lấy TRƯỚC khi duyệt (sau khi duyệt state đổi → hết lỡ hạn)."""
    if not info or not info.get('isLapsed'):
        return
    head = 'Duyệt trễ' if action == 'approve' else 'Từ chối đơn quá hạn'
    leave.sudo().message_post(
        body='%s — đơn quá hạn %d ngày làm việc. Đối chiếu chấm công: %s.' % (
            head, info['lapsedDays'], _lapsed_summary_label(info)),
        subtype_xmlid='mail.mt_note',
    )


def _burnout_table(env, scope, dept_id=False):
    """Bảng cảnh báo burnout (Widget 5-6, BR-040): KPI theo nhóm lý do
    + bảng NV có cờ + đếm theo phòng. Đọc SQL view hb.timeoff.burnout.line
    (đã sắp burnout desc, sick desc). sudo + lọc phòng ban tường minh."""
    domain = [('burnout_risk', '=', True)] + _dept_domain(scope)
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    lines = env['hb.timeoff.burnout.line'].sudo().search(domain)

    items, by_dept = [], {}
    n_sick = n_absence = n_balance = 0
    for line in lines:
        reason = line.risk_reason or ''
        # view trả đúng 1 lý do chính/NV → 3 nhóm cộng lại = total
        if reason.startswith('Nghỉ ốm'):
            n_sick += 1
        elif reason.startswith('Vắng'):
            n_absence += 1
        else:
            n_balance += 1
        dept = line.department_id
        row = by_dept.setdefault(dept.id or 0, {
            'id': dept.id or False, 'name': dept.name or '—', 'count': 0})
        row['count'] += 1
        items.append({
            'employeeId': line.employee_id.id,
            'employee': line.employee_id.name,
            'departmentId': dept.id or False,
            'department': dept.name or '—',
            'sickCount3m': line.sick_leave_count_3m,
            'absenceDays3m': round(line.total_absence_days_3m, 2),
            'remainingBalance': round(line.remaining_leave_balance, 2),
            'riskReason': reason,
        })
    return {
        'kpi': {'total': len(items), 'sickFreq': n_sick,
                'highAbsence': n_absence, 'lowBalance': n_balance},
        'items': items,
        'byDepartment': sorted(by_dept.values(),
                               key=lambda r: r['count'], reverse=True),
    }


# ---------------------------------------------------------------------------
# Nghỉ phép giáo viên — dò xung đột lịch dạy + áp dụng cách xử lý từng buổi.
# Lịch dạy là nguồn chính trong Neon (hocba.teaching.session). Helper cấp module
# để controller dùng dưới request VÀ test gọi trực tiếp.
# ---------------------------------------------------------------------------
def _find_teaching_conflicts(env, employee, date_from, date_to):
    """Buổi dạy đang hoạt động của giáo viên trùng khoảng nghỉ [date_from, date_to].

    Chỉ áp dụng cho giáo viên (có x_cms_user_id). Lấy buổi 'planned' + 'substituted'
    của CHỦ HIỆN TẠI (gồm buổi đã nhận dạy thay), bỏ buổi 'cancelled'. Vì employee_id
    luôn = chủ hiện tại nên mỗi buổi chỉ khớp đúng 1 GV → không xử lý chồng chéo."""
    if not employee or not employee.x_cms_user_id:
        return env['hocba.teaching.session']
    return env['hocba.teaching.session'].sudo().search([
        ('employee_id', '=', employee.id),
        ('state', 'in', ['planned', 'substituted']),
        ('session_date', '>=', date_from),
        ('session_date', '<=', date_to),
    ], order='session_date, start_time')


def _conflict_row(session):
    """1 dòng buổi dạy xung đột trả cho SPA."""
    return {
        'sessionId': session.id,
        'className': session.class_name or '',
        'date': str(session.session_date) if session.session_date else '',
        'startTime': session.start_time or '',
        'endTime': session.end_time or '',
    }


def _upcoming_teaching_sessions(env, employee, days=28):
    """Buổi dạy đang hoạt động sắp tới của GV (hôm nay → +days), cho form nghỉ-theo-buổi.

    Gồm 'planned' + 'substituted' của chủ hiện tại (buổi đã nhận dạy thay cũng hiện
    để GV đó xin nghỉ / giao tiếp cho người khác). Bỏ buổi 'cancelled'."""
    if not employee or not employee.x_cms_user_id:
        return env['hocba.teaching.session']
    today = fields.Date.context_today(env.user)
    horizon = today + timedelta(days=days)
    return env['hocba.teaching.session'].sudo().search([
        ('employee_id', '=', employee.id),
        ('state', 'in', ['planned', 'substituted']),
        ('session_date', '>=', today),
        ('session_date', '<=', horizon),
    ], order='session_date, start_time')


def _apply_resolutions(env, leave, conflicts, resolutions):
    """Tạo dòng xử lý cho TỪNG buổi xung đột. Chặn nếu chưa phủ hết / sai loại.

    Mỗi buổi phải có 1 lựa chọn ('class_off' / 'substitute'). Ràng buộc GV thay
    (bắt buộc & khác người nghỉ) do model hocba.leave.session.resolution kiểm.
    Chạy sudo: chủ đơn (NV thường) không có ACL ghi trên model resolution."""
    conflict_ids = list(conflicts.ids)
    by_session = {}
    for r in (resolutions or []):
        try:
            sid = int(r.get('sessionId'))
        except (TypeError, ValueError):
            continue
        by_session[sid] = r

    missing = [sid for sid in conflict_ids if sid not in by_session]
    if missing:
        raise ValidationError(
            'Còn %d buổi dạy trong kỳ nghỉ chưa chọn cách xử lý '
            '(cả lớp nghỉ hoặc đổi giáo viên dạy thay).' % len(missing))

    Res = env['hocba.leave.session.resolution'].sudo()
    created = Res.browse()
    for sid in conflict_ids:
        r = by_session[sid]
        rtype = (r.get('type') or '').strip()
        if rtype not in ('class_off', 'substitute'):
            raise ValidationError('Cách xử lý buổi dạy không hợp lệ.')
        vals = {'leave_id': leave.id, 'session_id': sid, 'resolution': rtype}
        if rtype == 'substitute':
            vals['substitute_id'] = int(r.get('substituteId') or 0) or False
        row = Res.create(vals)
        if row.resolution == 'substitute':
            _notify_substitute_request(env, row)
        created |= row
    return created


def _notify_substitute_request(env, resolution):
    """Báo chuông cho GV thay khi nhận yêu cầu dạy thay."""
    sub_user = resolution.substitute_id.user_id
    if not sub_user:
        return
    leave = resolution.leave_id
    _push_notification(
        env, sub_user, leave, 'sub_request', 'Yêu cầu dạy thay',
        '%s nhờ bạn dạy thay buổi %s' % (
            leave.employee_id.name, resolution.session_id.display_name))


def _notify_substitute_decision(env, resolution, accept):
    """Báo chuông cho người xin nghỉ khi GV thay đồng ý/từ chối."""
    req_user = resolution.leave_id.employee_id.user_id
    if not req_user:
        return
    verb = 'đồng ý' if accept else 'từ chối'
    _push_notification(
        env, req_user, resolution.leave_id,
        'sub_accepted' if accept else 'sub_declined',
        'Giáo viên thay đã %s dạy thay' % verb,
        '%s đã %s dạy thay buổi %s' % (
            resolution.substitute_id.name, verb,
            resolution.session_id.display_name))


def _substitution_rows(env, employee):
    """Yêu cầu dạy thay gửi tới 1 giáo viên (mới nhất trước)."""
    if not employee:
        return []
    recs = env['hocba.leave.session.resolution'].sudo().search(
        [('substitute_id', '=', employee.id), ('resolution', '=', 'substitute')],
        order='id desc')
    rows = []
    for r in recs:
        s = r.session_id
        rows.append({
            'id': r.id,
            'requester': r.leave_id.employee_id.name,
            'leaveId': r.leave_id.id,
            'className': s.class_name or '',
            'date': str(s.session_date) if s.session_date else '',
            'startTime': s.start_time or '',
            'endTime': s.end_time or '',
            'state': r.state,
            'isOwner': s.employee_id.id == employee.id,
        })
    return rows


def _decide_substitution(env, res_id, employee, accept, reason=''):
    """GV thay đồng ý/từ chối 1 yêu cầu của mình. Trả record hoặc False.

    False khi: yêu cầu không tồn tại / không thuộc về employee / đã xử lý."""
    r = env['hocba.leave.session.resolution'].sudo().browse(res_id)
    if not r.exists() or r.substitute_id.id != (employee.id if employee else 0):
        return False
    if r.resolution != 'substitute' or r.state != 'pending':
        return False
    r.write({
        'state': 'accepted' if accept else 'declined',
        'decided_at': fields.Datetime.now(),
        'decline_reason': '' if accept else (reason or ''),
    })
    _notify_substitute_decision(env, r, accept)
    return r


def _sessions_requestable_error(env, employee, session_ids):
    """Kiểm buổi dạy có được đưa vào đơn nghỉ-theo-buổi MỚI của `employee` không.

    Trả `(sessions, None)` nếu hợp lệ, hoặc `(None, (error_code, message))` nếu không.

    Mô hình "không trả lại": chủ hiện tại của buổi (kể cả buổi đã nhận dạy thay,
    `state='substituted'`) tự xử lý tiến — hủy lớp hoặc nhờ GV khác. Vì vậy buổi
    hợp lệ khi `s.employee_id == employee` VÀ `s.state in ('planned','substituted')`.
    Chặn-trùng bỏ qua "mắt xích đang sở hữu" (`session.source_leave_id` — đơn đã đưa
    buổi cho employee): đó là link trước của chuỗi, không phải trùng."""
    Session = env['hocba.teaching.session'].sudo()
    Res = env['hocba.leave.session.resolution'].sudo()
    sessions = Session.browse(session_ids)
    for s in sessions:
        if (not s.exists() or s.employee_id.id != (employee.id if employee else 0)
                or s.state not in ('planned', 'substituted')):
            return None, ('invalid_session',
                          'Buổi dạy không hợp lệ hoặc đã được xử lý.')
        dup_dom = [
            ('session_id', '=', s.id),
            ('leave_id.state', 'in', ['confirm', 'validate1', 'validate']),
            ('state', 'in', ['pending', 'accepted']),
        ]
        if s.source_leave_id:
            dup_dom.append(('leave_id', '!=', s.source_leave_id.id))
        if Res.search(dup_dom, limit=1):
            return None, ('session_already_requested',
                          'Có buổi dạy bạn đã gửi đơn nghỉ trước đó.')
    return sessions, None


# ---------------------------------------------------------------------------
# Phase 5 — Thông báo in-app (chuông) + nhật ký thao tác đơn (audit).
# Chuông: dùng model hợp nhất hb.notification của module hocba_notify (list/
# read/read-all qua /hocba-hrm/api/notifications* của module đó). Vì sao KHÔNG
# dùng mail.message needaction: trong Odoo 19 res.users.notification_type là
# field computed/stored, mặc định 'email' (chỉ user thuộc group
# mail.group_mail_notification_type_inbox mới là 'inbox') → đa số tài khoản SPA
# có inbox needaction rỗng, chuông sẽ trống. Model thông báo riêng chủ động,
# robust, không phụ thuộc tuỳ chọn nhận thông báo của user.
# Audit: message_post chatter trên hr.leave.
# Helper cấp module để controller dùng dưới request VÀ test gọi trực tiếp.
# ---------------------------------------------------------------------------
def _approver_users(env, leave):
    """Tập res.users được duyệt đơn này (để báo khi có đơn mới chờ duyệt):
    trưởng phòng theo chuỗi phòng ban của NV (gồm phòng cha) + toàn bộ HR Manager.
    Loại chính chủ đơn ra (không tự báo cho mình)."""
    users = env['res.users']
    # Đọc cây phòng ban/quản lý qua sudo: NV thường không có quyền đọc field
    # riêng tư của hr.employee người khác (manager) — sẽ AccessError nếu non-sudo.
    emp = leave.employee_id.sudo()
    dept = emp.department_id
    seen = set()
    while dept and dept.id not in seen:
        seen.add(dept.id)
        mgr = dept.manager_id
        if mgr and mgr.user_id:
            users |= mgr.user_id
        dept = dept.parent_id
    hr_group = env.ref('hr.group_hr_manager', raise_if_not_found=False)
    if hr_group:
        users |= env['res.users'].sudo().search([
            ('all_group_ids', 'in', hr_group.id), ('active', '=', True),
        ])
    if emp.user_id:
        users -= emp.user_id
    return users


def _leave_span_label(leave):
    d0, d1 = _leave_day_bounds(leave)
    f = d0.strftime('%d/%m/%Y') if d0 else '?'
    t = d1.strftime('%d/%m/%Y') if d1 else '?'
    return f if f == t else '%s → %s' % (f, t)


_KIND_LEVEL = {
    'pending': 'warning', 'withdraw_pending': 'warning',
    'sub_request': 'warning',
    'approved': 'success', 'sub_accepted': 'success', 'withdraw_approved': 'success',
    'refused': 'danger', 'sub_declined': 'danger', 'sub_cancelled': 'danger',
    'withdraw_refused': 'danger', 'lapsed': 'danger',
}


def _push_notification(env, recipient, leave, kind, title, body):
    """Wrapper mỏng → hb.notification hợp nhất (giữ chữ ký cũ cho mọi caller)."""
    if not recipient:
        return
    env['hb.notification'].sudo()._notify(
        recipient, category='timeoff', kind=kind,
        level=_KIND_LEVEL.get(kind, 'info'), title=title, body=body,
        target_view='timeoff', target_ref=leave.id,
        target_tab='sub' if kind.startswith('sub_') else None)


def _notify_request_created(env, leave):
    """Đơn mới → báo người duyệt phạm vi + ghi chú audit vào chatter."""
    span = _leave_span_label(leave)
    title = 'Đơn nghỉ mới chờ duyệt'
    body = '%s — %s (%s)' % (
        leave.employee_id.name, leave.holiday_status_id.name, span)
    for user in _approver_users(env, leave):
        _push_notification(env, user, leave, 'pending', title, body)
    leave.sudo().message_post(
        body='Đơn nghỉ được tạo và gửi chờ duyệt bởi %s.' % leave.employee_id.name,
        subtype_xmlid='mail.mt_note',
    )


def _notify_decision(env, leave, action):
    """Duyệt/từ chối → báo chủ đơn + ghi chú audit vào chatter."""
    approved = action == 'approve'
    kind = 'approved' if approved else 'refused'
    span = _leave_span_label(leave)
    title = 'Đơn nghỉ đã được duyệt' if approved else 'Đơn nghỉ bị từ chối'
    actor = (env.user.employee_id.name if env.user.employee_id
             else env.user.name) or 'người duyệt'
    body = '%s (%s) — %s bởi %s' % (
        leave.holiday_status_id.name, span,
        'đã duyệt' if approved else 'bị từ chối', actor)
    _push_notification(env, leave.employee_id.user_id, leave, kind, title, body)
    leave.sudo().message_post(
        body='Đơn nghỉ %s bởi %s.' % ('được duyệt' if approved else 'bị từ chối', actor),
        subtype_xmlid='mail.mt_note',
    )


def _notify_withdraw_requested(env, leave):
    """Phase 7: chủ đơn gửi yêu cầu rút → báo người duyệt phạm vi + audit."""
    span = _leave_span_label(leave)
    title = 'Yêu cầu rút đơn nghỉ'
    body = '%s — %s (%s) — yêu cầu rút đơn đã duyệt' % (
        leave.employee_id.name, leave.holiday_status_id.name, span)
    for user in _approver_users(env, leave):
        _push_notification(env, user, leave, 'withdraw_pending', title, body)
    leave.sudo().message_post(
        body='Chủ đơn (%s) yêu cầu rút đơn nghỉ đã duyệt. Lý do: %s' % (
            leave.employee_id.name,
            (leave.x_withdraw_reason or '').strip() or '—'),
        subtype_xmlid='mail.mt_note',
    )


def _notify_withdraw_decision(env, leave, approved, note):
    """Phase 7: kết quả duyệt rút → báo chủ đơn + audit (chatter)."""
    kind = 'withdraw_approved' if approved else 'withdraw_refused'
    span = _leave_span_label(leave)
    title = ('Yêu cầu rút đơn đã được duyệt'
             if approved else 'Yêu cầu rút đơn bị từ chối')
    actor = (env.user.employee_id.name if env.user.employee_id
             else env.user.name) or 'người duyệt'
    body = '%s (%s) — %s bởi %s' % (
        leave.holiday_status_id.name, span,
        'duyệt rút' if approved else 'từ chối rút', actor)
    _push_notification(env, leave.employee_id.user_id, leave, kind, title, body)
    chatter = ('Yêu cầu rút đơn được %s bởi %s.' %
               ('duyệt — đơn chuyển sang TỪ CHỐI, quỹ phép được hoàn lại'
                if approved else 'TỪ CHỐI, đơn giữ nguyên ĐÃ DUYỆT', actor))
    if note:
        chatter += ' Ghi chú: %s' % note
    leave.sudo().message_post(body=chatter, subtype_xmlid='mail.mt_note')


def _request_history(env, scope, leave_id):
    """Dòng thời gian thao tác của 1 đơn (audit). Trả:
    - None nếu đơn không tồn tại (controller → 404).
    - False nếu ngoài phạm vi xem (controller → 403).
    - list[{date, author, body, type}] theo thứ tự thời gian tăng dần.
    Xem được nếu là chủ đơn HOẶC người duyệt trong phạm vi (HR mọi phòng /
    trưởng phòng phòng mình)."""
    leave = env['hr.leave'].sudo().browse(leave_id)
    if not leave.exists():
        return None
    emp = env.user.employee_id
    is_owner = bool(emp) and leave.employee_id.id == emp.id
    in_scope = scope['canApprove'] and (
        scope['seeAll'] or leave.department_id.id in scope['deptIds'])
    if not (is_owner or in_scope):
        return False
    rows = []
    for m in leave.sudo().message_ids.sorted('id'):
        text = html2plaintext(m.body or '').strip()
        if not text:
            continue  # bỏ các message tracking rỗng (chỉ đổi field)
        rows.append({
            'id': m.id,
            'date': _d(m.date),
            'author': m.author_id.name or '',
            'body': text,
            'type': m.message_type,
        })
    return rows


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

        "Tài khoản nhân viên" (isEmployee) = KHÔNG thuộc bất kỳ vai trò quản lý
        nào (Admin/HR Manager/HR User/Giáo vụ/Trưởng phòng) — khớp đúng
        isRoleAccount của Shell.jsx (họp #2). Chỉ tài khoản nhân viên mới được
        TẠO đơn nghỉ; các vai trò quản lý chỉ duyệt/theo dõi.

        Vì không dựa được vào record rule của hr.leave (gắn group hr_holidays /
        leave_manager_id), các endpoint quản lý dùng sudo + lọc phòng ban tường
        minh theo deptIds (xem _dept_domain).

        Logic thực nằm ở hàm cấp module _scope_for(env) để test gọi trực tiếp.
        """
        return _scope_for(request.env)

    def _managed_department_ids(self, emp):
        return _managed_department_ids(request.env, emp)

    def _scope_flags(self, scope):
        """Cờ trả cho SPA. isOfficer/isManager giữ tên cũ để tương thích frontend."""
        return {
            'isOfficer': scope['canApprove'],     # tab Chờ duyệt/Tổng hợp, lịch cả đội
            'isManager': scope['canApprove'],     # dashboard chế độ quản lý
            'isHrManager': scope['isHrManager'],  # override chứng từ y tế (BR-011)
            'isEmployee': scope['isEmployee'],    # chỉ NV thường mới tạo được đơn
            'seeAll': scope['seeAll'],            # HR/Admin: lọc được mọi phòng ban
        }

    def _dept_domain(self, scope):
        return _dept_domain(scope)

    def _approvals_domain(self, scope):
        return _approvals_domain(scope)

    def _scoped_departments(self, scope):
        return _scoped_departments(request.env, scope)

    def _hb_leave_type_ids(self):
        return _hb_leave_type_ids(request.env)

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
        """Loại nghỉ chọn được trong dropdown 'nghỉ dài ngày'. Loại trừ 'Nghỉ
        Buổi Dạy' (chỉ dùng cho luồng nghỉ-theo-buổi của giáo viên)."""
        off_id = _teaching_off_type_id(request.env)
        type_ids = [i for i in self._hb_leave_type_ids() if i != off_id]
        types = (request.env['hr.leave.type'].sudo()
                 .with_context(employee_id=employee.id).search([
                     ('id', 'in', type_ids),
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
        # Phase 7: chỉ rút được đơn đã duyệt, chưa có yêu cầu rút, và còn ngày
        # nghỉ trong tương lai (date_to >= hôm nay).
        today = fields.Date.context_today(request.env.user)
        can_withdraw = (
            leave.state == 'validate'
            and leave.x_withdraw_state == 'none'
            and bool(leave.request_date_to)
            and leave.request_date_to >= today
        )
        sub_names, sess_res = [], []
        if leave.holiday_status_id.id == _teaching_off_type_id(request.env):
            for r in leave.teaching_resolution_ids:
                s = r.session_id.sudo()
                if r.resolution == 'class_off':
                    pass  # 'Cả lớp nghỉ' — không thêm tên GV thay
                else:
                    name = r.substitute_id.sudo().name or '—'
                    if name not in sub_names:
                        sub_names.append(name)
                sess_res.append({
                    'date': _d(s.session_date),
                    'className': s.class_name or '',
                    'kind': r.resolution,
                    'substituteName': (r.substitute_id.sudo().name or ''
                                       if r.resolution == 'substitute' else ''),
                    'state': r.state,
                })
        return {
            'id': leave.id,
            'leaveTypeId': leave.holiday_status_id.id,
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'createdAt': _d(leave.create_date.date() if leave.create_date else None),
            'days': round(leave.number_of_days, 2),
            'halfDay': _half_day_label(leave),
            'isTeachingOff': leave.holiday_status_id.id == _teaching_off_type_id(request.env),
            'sessionCount': len(leave.teaching_resolution_ids),
            'substituteNames': ', '.join(sub_names) if sub_names else (
                'Cả lớp nghỉ' if sess_res else ''),
            'sessionResolutions': sess_res,
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'stateKind': STATE_KIND.get(leave.state, 'gray'),
            'reason': leave.sudo().private_name or '',
            'isEmergency': leave.x_is_emergency,
            'supportDocument': leave.holiday_status_id.support_document,
            'hasMedicalDoc': leave.x_has_medical_doc,
            'canCancel': leave.state in PENDING_STATES,
            'withdrawState': leave.x_withdraw_state,
            'withdrawReason': leave.x_withdraw_reason or '',
            'canWithdraw': can_withdraw,
        }

    def _approval_request(self, leave):
        return {
            'id': leave.id,
            'employeeId': leave.employee_id.id,
            'employee': leave.employee_id.name,
            'departmentId': leave.department_id.id or leave.employee_id.department_id.id or False,
            'department': leave.department_id.name or leave.employee_id.department_id.name or '—',
            'leaveType': leave.holiday_status_id.name,
            'from': _d(leave.request_date_from),
            'to': _d(leave.request_date_to),
            'createdAt': _d(leave.create_date.date() if leave.create_date else None),
            'days': round(leave.number_of_days, 2),
            'halfDay': _half_day_label(leave),
            'isTeachingOff': leave.holiday_status_id.id == _teaching_off_type_id(request.env),
            'sessionCount': len(leave.teaching_resolution_ids),
            'state': leave.state,
            'stateLabel': STATE_LABEL.get(leave.state, leave.state),
            'stateKind': STATE_KIND.get(leave.state, 'gray'),
            'reason': leave.sudo().private_name or '',
            'isEmergency': leave.x_is_emergency,
            'supportDocument': leave.holiday_status_id.support_document,
            'hasMedicalDoc': leave.x_has_medical_doc,
            # Phase 4: số người cùng phòng đã duyệt nghỉ trùng khoảng ngày này.
            'overlapCount': _overlap_count(request.env, leave),
            # Phase 7: yêu cầu rút đơn (FE hiện badge "Yêu cầu rút" + modal riêng).
            'withdrawState': leave.x_withdraw_state,
            'withdrawReason': leave.x_withdraw_reason or '',
            'submittedAt': _d(leave.create_date.date() if leave.create_date else None),
            # "Quá hạn duyệt": qua ngày bắt đầu nghỉ mà đơn vẫn chờ duyệt, kèm
            # đối chiếu chấm công (None nếu chưa quá hạn).
            'lapsed': _lapsed_info(request.env, leave),
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
                # GV (có x_cms_user_id) → bật bước xử lý buổi dạy + panel dạy thay.
                'isTeacher': bool(emp.x_cms_user_id),
            },
            # Loại nghỉ 'Nghỉ Buổi Dạy' cho luồng nghỉ-theo-buổi (FE chế độ A).
            'teachingOffTypeId': _teaching_off_type_id(request.env),
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
        # FE phân biệt đơn mới / yêu cầu rút bằng withdrawState + Badge riêng.
        leaves = request.env['hr.leave'].sudo().search(
            self._approvals_domain(scope),
            order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            **self._scope_flags(scope),
            # HR/Admin lọc theo phòng ban ngay trong thanh sắp xếp; Trưởng phòng
            # chỉ thấy phòng mình nên không cần (FE gate bằng seeAll).
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
            'requests': [self._approval_request(l) for l in leaves],
        })

    # ------------------------------------------------------------------
    # 3.2a. GET /pending-count — badge "Nghỉ phép" ở thanh menu (sidebar).
    # Chỉ đếm (search_count), KHÔNG dựng payload đơn như /approvals: gọi ở
    # mọi màn nên phải rẻ. Không có quyền duyệt → 200 + count 0 (badge ẩn),
    # để SPA khỏi phải bắt 403 cho một chi tiết trang trí.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/pending-count', auth='user',
                type='http', methods=['GET'])
    def api_pending_count(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'canApprove': False, 'count': 0})
        return request.make_json_response({
            'canApprove': True,
            # Cùng _approvals_domain với tab "Đơn chờ duyệt" → 2 badge không lệch.
            'count': request.env['hr.leave'].sudo().search_count(
                self._approvals_domain(scope)),
        })

    # ------------------------------------------------------------------
    # 3.2b. POST /teaching-conflicts — dò buổi dạy trùng kỳ nghỉ (giáo viên)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/teaching-conflicts', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_teaching_conflicts(self, **kw):
        """Trả buổi dạy trùng + danh sách GV có thể dạy thay. Dò trên Neon."""
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)

        payload = request.get_json_data()
        date_from = (payload.get('dateFrom') or '').strip()
        date_to = (payload.get('dateTo') or date_from).strip()
        if not date_from:
            return request.make_json_response({'error': 'bad_request'}, status=400)

        conflicts = _find_teaching_conflicts(request.env, emp, date_from, date_to)
        substitutes = []
        if conflicts:
            others = request.env['hr.employee'].sudo().search([
                ('x_cms_user_id', '!=', False), ('id', '!=', emp.id)],
                order='name')
            substitutes = [{'id': e.id, 'name': e.name} for e in others]
        return request.make_json_response({
            'conflicts': [_conflict_row(s) for s in conflicts],
            'substitutes': substitutes,
        })

    # ------------------------------------------------------------------
    # 3.2c. Yêu cầu dạy thay gửi tới giáo viên thay — liệt kê + quyết định
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/substitutions', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_substitutions(self, **kw):
        emp = request.env.user.employee_id
        return request.make_json_response(
            {'items': _substitution_rows(request.env, emp)})

    # ------------------------------------------------------------------
    # 3.2d. GET /my-teaching-sessions — buổi dạy sắp tới của GV (nghỉ-theo-buổi)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/my-teaching-sessions', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_my_teaching_sessions(self, **kw):
        emp = request.env.user.employee_id
        sessions = _upcoming_teaching_sessions(request.env, emp)
        substitutes = []
        if emp and emp.x_cms_user_id:
            others = request.env['hr.employee'].sudo().search(
                [('x_cms_user_id', '!=', False), ('id', '!=', emp.id)],
                order='name')
            substitutes = [{'id': e.id, 'name': e.name} for e in others]
        return request.make_json_response({
            'sessions': [_conflict_row(s) for s in sessions],
            'substitutes': substitutes,
        })

    @http.route('/hocba-hrm/api/timeoff/substitutions/<int:res_id>/decide',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_substitution_decide(self, res_id, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)
        payload = request.get_json_data() or {}
        accept = bool(payload.get('accept'))
        reason = (payload.get('reason') or '').strip()
        r = _decide_substitution(request.env, res_id, emp, accept, reason)
        if not r:
            return request.make_json_response(
                {'error': 'not_found_or_decided'}, status=400)
        return request.make_json_response(
            {'items': _substitution_rows(request.env, emp)})

    def _create_teaching_session_leave(self, emp, payload):
        """Chế độ A — GV nghỉ theo BUỔI dạy. resolutions xác định ĐÚNG tập buổi
        nghỉ; KHÔNG dò/ép phủ hết buổi trong khoảng (khác luồng nghỉ dài ngày).
        Loại nghỉ cố định 'Nghỉ Buổi Dạy' (không trừ quỹ). Ngày đơn suy từ buổi."""
        if not emp.x_cms_user_id:
            return request.make_json_response({'error': 'not_teacher'}, status=403)
        off_id = _teaching_off_type_id(request.env)
        if not off_id:
            return request.make_json_response(
                {'error': 'leave_type_not_found'}, status=404)

        resolutions = payload.get('resolutions') or []
        sess_ids = []
        for r in resolutions:
            try:
                sess_ids.append(int(r.get('sessionId')))
            except (TypeError, ValueError):
                continue
        sess_ids = list(dict.fromkeys(sess_ids))   # unique, giữ thứ tự
        if not sess_ids:
            return request.make_json_response({'error': 'no_sessions'}, status=400)

        # Chủ hiện tại của buổi (kể cả buổi đã nhận dạy thay 'substituted') được
        # tạo đơn mới để tự xử lý tiến (hủy lớp / nhờ GV khác) — mô hình không trả
        # lại. Guard + chặn-trùng gói trong helper để test gọi trực tiếp.
        sessions, err = _sessions_requestable_error(request.env, emp, sess_ids)
        if err:
            return request.make_json_response(
                {'error': err[0], 'message': err[1]}, status=400)

        dates = sessions.mapped('session_date')
        vals = {
            'holiday_status_id': off_id,
            'employee_id': emp.id,
            'request_date_from': min(dates),
            'request_date_to': max(dates),
        }
        reason = (payload.get('reason') or '').strip()
        if reason:
            vals['name'] = reason

        try:
            with request.env.cr.savepoint():
                leave = request.env['hr.leave'].create(vals)
                _apply_resolutions(request.env, leave, sessions, resolutions)
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)

        _notify_request_created(request.env, leave)
        return request.make_json_response(self._overview_payload())

    # ------------------------------------------------------------------
    # 3.3. POST /request — tạo đơn nghỉ cho chính mình
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_create(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)

        # Chỉ tài khoản NHÂN VIÊN mới được tạo đơn nghỉ. Các vai trò quản lý
        # (Admin/HR/Giáo vụ/Trưởng phòng) là tài khoản thuần quản lý, chỉ duyệt
        # đơn — dùng tài khoản nhân viên riêng cho nghỉ phép cá nhân (họp #2).
        if not self._scope()['isEmployee']:
            return request.make_json_response(
                {'error': 'not_employee',
                 'message': 'Tài khoản quản lý không thể tạo đơn nghỉ phép. '
                            'Vui lòng dùng tài khoản nhân viên cá nhân.'},
                status=403)

        payload = request.get_json_data() or {}

        # Chế độ A — giáo viên nghỉ theo BUỔI dạy (session-first): luồng riêng,
        # không nhập khoảng ngày / không trừ quỹ / không ép phủ hết buổi trong kỳ.
        if (payload.get('scope') or '').strip() == 'sessions':
            return self._create_teaching_session_leave(emp, payload)

        leave_type_id = payload.get('leaveTypeId')
        date_from = (payload.get('dateFrom') or '').strip()
        date_to = (payload.get('dateTo') or '').strip()
        period = (payload.get('period') or '').strip().lower()  # ''/'am'/'pm' (Phase 6)
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

        # Phase 6 — nửa ngày: nếu chọn buổi sáng/chiều, đơn co về đúng date_from.
        period_vals = _period_request_vals(leave_type, date_from, period)
        if period_vals:
            date_to = date_from   # số ngày làm việc kiểm trên đúng 1 ngày

        # Không cho xin nghỉ nếu cả kỳ rơi vào ngày không làm việc
        # (Thứ 7 / Chủ nhật / ngày lễ đã seed) — ngày đó vốn đã nghỉ.
        if self._count_working_days(date_from, date_to) == 0:
            return request.make_json_response(
                {'error': 'non_working_day',
                 'message': 'Khoảng ngày bạn chọn trùng hoàn toàn vào ngày '
                            'nghỉ (cuối tuần hoặc ngày lễ) — không cần xin '
                            'nghỉ phép cho những ngày này.'},
                status=400)

        # Chặn trùng đơn nghỉ đã tạo trước đó của chính nhân viên (chờ duyệt +
        # đã duyệt). Đơn đã `refuse`/`cancel` không tính. Khoảng ngày giao nhau
        # = date_from <= other.to AND date_to >= other.from.
        ACTIVE_STATES = ('confirm', 'validate1', 'validate')
        clash = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', 'in', list(ACTIVE_STATES)),
            ('request_date_from', '<=', date_to),
            ('request_date_to', '>=', date_from),
        ], limit=1)
        if clash:
            clash_label = STATE_LABEL.get(clash.state, clash.state)
            d0 = clash.request_date_from.strftime('%d/%m/%Y') if clash.request_date_from else ''
            d1 = clash.request_date_to.strftime('%d/%m/%Y') if clash.request_date_to else ''
            return request.make_json_response(
                {'error': 'overlap_self',
                 'message': 'Bạn đã có đơn nghỉ "%s" (%s) từ %s đến %s '
                            'trùng khoảng ngày này. Vui lòng kiểm tra lại '
                            'hoặc hủy đơn cũ trước.' % (
                                clash.holiday_status_id.name or '',
                                clash_label, d0, d1)},
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
        vals.update(period_vals)   # Phase 6 — nửa ngày (nếu có)
        if reason:
            vals['name'] = reason

        # Giáo viên: dò buổi dạy trùng kỳ nghỉ (trên Neon). Nếu có, phải xử lý
        # hết TỪNG buổi (cả lớp nghỉ / đổi GV thay) thì mới được tạo đơn.
        conflicts = _find_teaching_conflicts(request.env, emp, date_from, date_to)

        # KHÔNG sudo cho hr.leave: model áp domain employee + quyền tạo của user.
        # Bọc savepoint để khi xử lý buổi dạy lỗi thì KHÔNG để lại đơn mồ côi.
        try:
            with request.env.cr.savepoint():
                leave = request.env['hr.leave'].create(vals)
                if conflicts:
                    _apply_resolutions(
                        request.env, leave, conflicts,
                        payload.get('resolutions'))
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)

        if att_vals:
            att_vals['res_id'] = leave.id
            request.env['ir.attachment'].sudo().create(att_vals)
            leave.invalidate_recordset(['attachment_ids', 'x_has_medical_doc'])

        # Phase 5: báo người duyệt phạm vi + ghi chú audit (chatter).
        _notify_request_created(request.env, leave)

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
        # Rút đơn (self-service): model kiểm chủ đơn + trạng thái chờ duyệt rồi
        # xoá dưới sudo. Dùng sudo vì chặn core "không xoá đơn quá khứ" khiến
        # NV không rút được đơn ĐÃ QUÁ HẠN mà chưa được duyệt.
        # Lưu ý: hr.leave.action_cancel() chỉ mở wizard, không hủy trực tiếp.
        try:
            leave.action_timeoff_self_cancel(emp)
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

        # Phase 12: chụp trạng thái lỡ hạn TRƯỚC khi duyệt (duyệt xong state
        # đổi → _lapsed_info trả None) để ghi vết "duyệt trễ" chính xác.
        lapsed_before = _lapsed_info(request.env, leave)
        try:
            if action == 'refuse':
                leave.action_refuse()
            else:
                # Override chứng từ y tế (BR-011): chỉ HR/Admin mới được.
                write_vals = {}
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
            # Phase 5: báo chủ đơn kết quả + ghi chú audit (chatter).
            _notify_decision(request.env, leave, action)
            _post_lapsed_decision_note(request.env, leave, action, lapsed_before)
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)

        # Trả lại danh sách chờ duyệt đã refresh (cùng phạm vi phòng ban,
        # cùng domain với GET /approvals — gồm cả yêu cầu rút đang chờ).
        leaves = request.env['hr.leave'].sudo().search(
            self._approvals_domain(scope),
            order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            **self._scope_flags(scope),
            'requests': [self._approval_request(l) for l in leaves],
        })

    # ------------------------------------------------------------------
    # 3.6. POST /request/<id>/withdraw — Phase 7: chủ đơn gửi yêu cầu rút
    #      đơn đã duyệt. Đơn vào trạng thái "chờ duyệt rút" (x_withdraw_state).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request/<int:leave_id>/withdraw',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_request_withdraw(self, leave_id, **kw):
        emp = request.env.user.employee_id
        leave = request.env['hr.leave'].sudo().browse(leave_id)
        if not leave.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not emp or leave.employee_id.id != emp.id:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        # Chỉ rút được đơn đã duyệt; đơn chờ duyệt đã có nút Hủy (cancel) riêng.
        if leave.state != 'validate':
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Chỉ rút được đơn đã được duyệt.'}, status=403)
        if leave.x_withdraw_state == 'pending':
            return request.make_json_response(
                {'error': 'already_pending',
                 'message': 'Yêu cầu rút đã được gửi và đang chờ duyệt.'},
                status=400)
        # Không rút được nếu mọi ngày nghỉ đều đã trôi qua (không còn gì để rút).
        today = fields.Date.context_today(request.env.user)
        if leave.request_date_to and leave.request_date_to < today:
            return request.make_json_response(
                {'error': 'past_only',
                 'message': 'Đơn này đã kết thúc — không thể rút đơn '
                            'cho ngày đã qua.'}, status=400)

        payload = request.get_json_data() or {}
        reason = (payload.get('reason') or '').strip()
        if not reason:
            return request.make_json_response(
                {'error': 'reason_required',
                 'message': 'Vui lòng nhập lý do rút đơn.'}, status=400)

        leave.sudo().write({
            'x_withdraw_state': 'pending',
            'x_withdraw_reason': reason,
        })
        _notify_withdraw_requested(request.env, leave)
        return request.make_json_response(self._overview_payload())

    # ------------------------------------------------------------------
    # 3.7. POST /request/<id>/withdraw/decide — Phase 7: người duyệt phạm vi
    #      duyệt / từ chối yêu cầu rút. approve → action_refuse (hoàn quỹ).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request/<int:leave_id>/withdraw/decide',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_request_withdraw_decide(self, leave_id, **kw):
        payload = request.get_json_data() or {}
        approve = bool(payload.get('approve'))
        note = (payload.get('note') or '').strip()

        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)

        leave = request.env['hr.leave'].sudo().browse(leave_id)
        if not leave.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if leave.x_withdraw_state != 'pending':
            return request.make_json_response(
                {'error': 'not_pending',
                 'message': 'Đơn này không có yêu cầu rút đang chờ.'},
                status=400)
        # Trưởng phòng chỉ xử lý đơn thuộc phòng ban mình quản lý.
        if not scope['seeAll'] and leave.department_id.id not in scope['deptIds']:
            return request.make_json_response({'error': 'forbidden'}, status=403)

        try:
            if approve:
                # action_refuse trên đơn validate → leaves_taken không còn tính
                # đơn này → virtual_remaining_leaves tự cộng lại number_of_days.
                leave.action_refuse()
                # Giữ x_withdraw_state='pending' để FE phân biệt "hủy do rút"
                # với "từ chối ban đầu" qua state+x_withdraw_state.
            else:
                leave.write({'x_withdraw_state': 'none'})
            _notify_withdraw_decision(request.env, leave, approve, note)
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=403)

        # Trả lại danh sách chờ duyệt (gồm cả yêu cầu rút) đã refresh —
        # cùng domain với GET /approvals.
        leaves = request.env['hr.leave'].sudo().search(
            self._approvals_domain(scope),
            order='x_is_emergency desc, request_date_from, id')
        return request.make_json_response({
            **self._scope_flags(scope),
            'requests': [self._approval_request(l) for l in leaves],
        })

    # ------------------------------------------------------------------
    # 3.5b. Phase 5 — Nhật ký thao tác đơn (chuông đã chuyển sang API hợp
    # nhất /hocba-hrm/api/notifications* của module hocba_notify).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/request/<int:leave_id>/history',
                auth='user', type='http', methods=['GET'])
    def api_request_history(self, leave_id, **kw):
        """Dòng thời gian thao tác của 1 đơn (audit) — chủ đơn / người duyệt phạm vi."""
        scope = self._scope()
        history = _request_history(request.env, scope, leave_id)
        if history is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        if history is False:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        return request.make_json_response({'history': history})

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

    # ------------------------------------------------------------------
    # 3.6b. GET /lapsed-dashboard — màn "Giám sát duyệt đơn" (Phase 12).
    # Chỉ officer; HR/Admin mọi phòng, Trưởng phòng phòng mình (BR-L06).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/lapsed-dashboard', auth='user',
                type='http', methods=['GET'])
    def api_lapsed_dashboard(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        data = _lapsed_table(request.env, scope, dept_id)
        data.update({
            **self._scope_flags(scope),
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
        })
        return request.make_json_response(data)

    # ------------------------------------------------------------------
    # 3.6c. GET /burnout — tab "Sức khỏe NV" (Widget 5-6, BR-040).
    # Chỉ officer; HR/Admin mọi phòng, Trưởng phòng phòng mình.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/burnout', auth='user',
                type='http', methods=['GET'])
    def api_burnout(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        data = _burnout_table(request.env, scope, dept_id)
        data.update({
            **self._scope_flags(scope),
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
        })
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

        # "Đơn quá hạn duyệt" dùng CHUNG nguồn với tab "Kiểm duyệt phát sinh"
        # (_lapsed_table) — trước đây dashboard đếm theo SLA tuổi đơn nên hai
        # tab cùng nói "quá hạn" mà ra hai con số khác nhau.
        lapsed = _lapsed_table(request.env, scope, dept_id)

        kpi = {
            'total': Leave.search_count(year_dom + dept_dom),
            'pending': Leave.search_count(pending_dom),
            'approved': Leave.search_count(approved_dom),
            'approvedDays': round(approved_days, 1),
            'refused': Leave.search_count(
                _refused_domain(scope, dept_id, start, end)),
            'onLeaveToday': Leave.search_count([
                ('state', '=', 'validate'),
                ('date_from', '<=', '%s 23:59:59' % today),
                ('date_to', '>=', '%s 00:00:00' % today)] + dept_dom),
            # Quá hạn duyệt = qua ngày bắt đầu nghỉ mà đơn vẫn chờ duyệt.
            'overdue': lapsed['kpi']['total'],
            'oldestOverdueDays': lapsed['kpi']['oldestLapsedDays'],
            'deepOverdueDays': OVERDUE_DEEP_DAYS,   # ngưỡng FE tô đậm dòng
        }

        # _lapsed_table đã sắp giảm dần theo số ngày quá hạn.
        overdue_requests = [{
            'requestId': r['requestId'],
            'employee': r['employee'],
            'department': r['department'],
            'leaveType': r['leaveType'],
            'from': r['from'],
            'to': r['to'],
            'days': r['days'],
            'overdueDays': r['lapsedDays'],
            'submittedAt': r['submittedAt'],
            'state': r['state'],
            'stateLabel': r['stateLabel'],
            'isEmergency': r['isEmergency'],
        } for r in lapsed['items']]

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
            # Phase 8 — danh sách đơn quá hạn (sort age desc).
            'overdueRequests': overdue_requests,
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
        # Phạm vi lịch theo VAI TRÒ (đã bỏ toggle Của tôi/Cả đội):
        #  - NV/GV thường: chỉ lịch cá nhân.
        #  - Trưởng phòng: cả phòng mình quản lý (gồm phòng con).
        #  - HR/Admin: mọi phòng ban, lọc 1 phòng nếu chọn (?dept=<id>).
        start, end = self._year_bounds(year)
        overlap = [('date_from', '<=', end), ('date_to', '>=', start)]
        Leave = request.env['hr.leave'].sudo()
        dept_filter = False
        if not scope['canApprove']:
            emp = request.env.user.employee_id
            domain = ([('employee_id', '=', emp.id)] + overlap) if emp else [('id', '=', 0)]
        else:
            dept_dom = self._dept_domain(scope)
            if scope['seeAll']:
                try:
                    dept_filter = int(kw.get('dept') or 0) or False
                except (TypeError, ValueError):
                    dept_filter = False
                if dept_filter:
                    dept_dom = [('department_id', '=', dept_filter)]
            domain = overlap + dept_dom

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
            'dept': dept_filter,
            # Danh sách phòng ban cho HR chọn lọc (vai trò khác không cần).
            'allDepartments': ([{'id': d.id, 'name': d.name}
                                for d in self._scoped_departments(scope)]
                               if scope['seeAll'] else []),
            'leaveTypes': sorted(types.values(), key=lambda t: t['name']),
            'leaves': rows,
            'mandatoryDays': mdays,
            'workDays': self._work_days(year),
        })

    # ------------------------------------------------------------------
    # Lịch làm việc — Thứ 2..6 mặc định + các ngày đi làm thêm do HR thêm
    # ------------------------------------------------------------------
    def _work_days(self, year):
        """Ngày đi làm thêm trong năm. `locked` = ngày đã đến/đã qua → SPA khoá
        nút sửa/xoá (model hb.work.day mới là nơi chặn thật)."""
        days = request.env['hb.work.day'].sudo().search([
            ('date', '>=', '%d-01-01' % year),
            ('date', '<=', '%d-12-31' % year),
        ], order='date')
        return [{'id': d.id, 'date': _d(d.date), 'name': d.name or 'Ngày đi làm',
                 'locked': d.is_locked}
                for d in days]

    def _min_work_day(self):
        """Ngày sớm nhất HR còn được thêm/sửa lịch làm việc (= ngày mai)."""
        return _d(request.env['hb.work.day'].sudo()._first_editable_date())

    def _public_holiday_dates(self, start, end):
        """Tập NGÀY lễ toàn cục (resource.calendar.leaves) trong [start, end].
        Trừ khỏi số ngày làm việc để chặn xin nghỉ vào ngày đã là lễ."""
        rows = request.env['resource.calendar.leaves'].sudo().search([
            ('calendar_id', '=', False),
            ('resource_id', '=', False),
            ('time_type', '=', 'leave'),
            ('date_from', '<=', '%s 23:59:59' % end),
            ('date_to', '>=', '%s 00:00:00' % start),
        ])
        days = set()
        for r in rows:
            d0 = max(r.date_from.date(), start)
            d1 = min(r.date_to.date(), end)
            cur = d0
            while cur <= d1:
                days.add(cur)
                cur += timedelta(days=1)
        return days

    def _count_working_days(self, date_from, date_to):
        """Số ngày LÀM VIỆC trong [date_from, date_to]: Thứ 2–Thứ 6, cộng các
        ngày Thứ 7 do HR đánh dấu đi làm (hb.work.day), TRỪ các ngày lễ toàn
        cục (resource.calendar.leaves đã seed Phase 6). Chủ nhật / Thứ 7 thường
        / ngày lễ = ngày nghỉ, không tính."""
        start = fields.Date.to_date(date_from)
        end = fields.Date.to_date(date_to)
        if not start or not end:
            return 0
        work_extra = set(request.env['hb.work.day'].sudo().search([
            ('date', '>=', start), ('date', '<=', end)]).mapped('date'))
        holidays = self._public_holiday_dates(start, end)
        n, cur = 0, start
        while cur <= end:
            is_workday = cur.weekday() < 5 or cur in work_extra
            if is_workday and cur not in holidays:
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
            'canEdit': scope['isHrManager'],   # chỉ HR/Admin được thêm/sửa/xoá
            'year': year,
            'minDate': self._min_work_day(),   # ngày sớm nhất còn thao tác được
            'workDays': self._work_days(year),
        })

    @http.route('/hocba-hrm/api/timeoff/workdays/add', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_workdays_add(self, **kw):
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        name = (payload.get('name') or 'Ngày đi làm').strip() or 'Ngày đi làm'
        try:
            year = int(payload.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()

        # 2 dạng payload: `dates` (thêm tay — dùng chung 1 ghi chú `name`) hoặc
        # `items` [{date, name}] (nhập từ Excel — ghi chú riêng từng ngày).
        raw_items = payload.get('items')
        if raw_items is None:
            raw_items = [{'date': d} for d in (payload.get('dates') or [])]

        Model = request.env['hb.work.day'].sudo()
        limit = Model._first_editable_date()
        days = []
        for it in raw_items:
            if isinstance(it, dict):
                ds, it_name = it.get('date'), (it.get('name') or '').strip()
            else:
                ds, it_name = it, ''
            ds = (ds or '').strip()
            if not ds:
                continue
            try:
                day = fields.Date.to_date(ds)
            except (ValueError, TypeError):
                continue
            days.append((day, it_name or name))
        # Chặn TRƯỚC khi tạo: chỉ nhận ngày chưa đến. Báo lỗi cả lô (không tạo
        # một phần) để HR sửa lại danh sách rồi lưu lại — tránh trạng thái
        # "đã lưu 2/3 ngày" khó hiểu.
        past = sorted({d for d, _n in days if d < limit})
        if past:
            return request.make_json_response(
                {'error': 'past_workday',
                 'message': 'Không thêm được ngày đã đến hoặc đã qua: %s. '
                            'Ngày đã diễn ra thì chấm công và lương đã tính '
                            'theo lịch lúc đó. Chỉ thêm được từ ngày %s trở đi.'
                            % (', '.join(d.strftime('%d/%m/%Y') for d in past),
                               limit.strftime('%d/%m/%Y'))},
                status=400)
        for day, day_name in days:
            if not Model.search_count([('date', '=', day)]):
                Model.create({'date': day, 'name': day_name})
        return request.make_json_response({
            'canEdit': True, 'year': year, 'minDate': self._min_work_day(),
            'workDays': self._work_days(year),
        })

    # -- Nhập lịch làm việc bằng Excel (cách thêm thứ 2, cạnh thêm tay) -----
    @http.route('/hocba-hrm/api/timeoff/workdays/template', auth='user',
                type='http', methods=['GET'])
    def api_workdays_template(self, **kw):
        """Tải file .xlsx mẫu: liệt kê sẵn Thứ 7/Chủ nhật CHƯA ĐẾN của năm đó,
        HR chỉ tick 'x'. Khoá cột Ngày/Thứ nên không chọn nhầm ngày khác."""
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        min_date = request.env['hb.work.day'].sudo()._first_editable_date()
        try:
            content = build_template(year, min_date)
        except WorkdayImportError as ex:
            return request.make_json_response(
                {'error': ex.code, 'message': ex.message}, status=400)
        return request.make_response(content, headers=[
            ('Content-Type', XLSX_MIME),
            ('Content-Length', len(content)),
            ('Content-Disposition',
             content_disposition('mau-lich-lam-viec-%d.xlsx' % year)),
        ])

    @http.route('/hocba-hrm/api/timeoff/workdays/import', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_workdays_import(self, **kw):
        """Đọc + KIỂM file HR tải lên, KHÔNG ghi gì cả — trả danh sách ngày để
        SPA xem trước rồi mới bấm Lưu (dùng lại /workdays/add). Sai định dạng
        thì báo lỗi ngay kèm số dòng, không nhập một phần."""
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            year = int(kw.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()

        upload = kw.get('file')
        filename = getattr(upload, 'filename', '') or ''
        if not upload or not filename:
            return request.make_json_response(
                {'error': 'no_file', 'message': 'Chưa chọn file để tải lên.'},
                status=400)
        if not filename.lower().endswith('.xlsx'):
            return request.make_json_response(
                {'error': 'bad_ext',
                 'message': 'Chỉ nhận file Excel .xlsx (file bạn chọn: "%s"). '
                            'Nếu đang dùng .xls hoặc .csv, hãy mở bằng Excel '
                            'rồi "Lưu dưới dạng" .xlsx.' % filename},
                status=400)

        Model = request.env['hb.work.day'].sudo()
        existing = set(Model.search([
            ('date', '>=', '%d-01-01' % year),
            ('date', '<=', '%d-12-31' % year)]).mapped('date'))
        try:
            res = parse_workdays_xlsx(upload.read(), year,
                                      Model._first_editable_date(), existing)
        except WorkdayImportError as ex:
            return request.make_json_response(
                {'error': ex.code, 'message': ex.message,
                 'details': ex.details}, status=400)
        return request.make_json_response({'year': year, 'filename': filename, **res})

    @http.route('/hocba-hrm/api/timeoff/workdays/<int:day_id>/update',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_workdays_update(self, day_id, **kw):
        """Sửa 1 ngày đi làm (đổi ngày / ghi chú) — chỉ khi ngày CHƯA ĐẾN."""
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        try:
            year = int(payload.get('year') or self._this_year())
        except (TypeError, ValueError):
            year = self._this_year()
        rec = request.env['hb.work.day'].sudo().browse(day_id)
        if not rec.exists():
            return request.make_json_response(
                {'error': 'not_found',
                 'message': 'Ngày làm việc này không còn trong lịch.'},
                status=404)
        vals = {}
        if payload.get('date'):
            try:
                vals['date'] = fields.Date.to_date(payload['date'])
            except (ValueError, TypeError):
                return request.make_json_response(
                    {'error': 'bad_date', 'message': 'Ngày không hợp lệ.'},
                    status=400)
        if payload.get('name') is not None:
            vals['name'] = (payload.get('name') or '').strip() or 'Ngày đi làm'
        if vals:
            try:
                rec.write(vals)
            except (UserError, ValidationError) as ex:
                return request.make_json_response(
                    {'error': 'locked_workday', 'message': str(ex)}, status=400)
        return request.make_json_response({
            'canEdit': True, 'year': year, 'minDate': self._min_work_day(),
            'workDays': self._work_days(year),
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
            # Ngày đã diễn ra bị model chặn — trả 400 kèm lý do thay vì 500.
            try:
                rec.unlink()
            except (UserError, ValidationError) as ex:
                return request.make_json_response(
                    {'error': 'locked_workday', 'message': str(ex)}, status=400)
        return request.make_json_response({
            'canEdit': True, 'year': year, 'minDate': self._min_work_day(),
            'workDays': self._work_days(year),
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
            'createdAt': _d(l.create_date.date() if l.create_date else None),
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
            'createdAt': _d(l.create_date.date() if l.create_date else None),
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
    # 3.11. GET /balances — bảng Quỹ phép toàn nhân viên (Phase 1).
    #   Chỉ vai trò duyệt (HR/Admin = mọi phòng; Trưởng phòng = phòng được
    #   giao). NV thường → 403. Số dư mỗi loại HB cần phân bổ, theo cơ chế
    #   context employee_id (như _balances). Params: year, dept, type.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/balances', auth='user',
                type='http', methods=['GET'])
    def api_balances(self, **kw):
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
        try:
            type_filter = int(kw.get('type')) if kw.get('type') else False
        except (TypeError, ValueError):
            type_filter = False
        # Phase 3: filter=expiring → chỉ NV còn nhiều phép năm (sắp mất phép).
        filter_mode = kw.get('filter') if kw.get('filter') in ('expiring',) else False
        data = _balances_table(request.env, scope, year, dept_id, type_filter,
                               filter_mode)
        return request.make_json_response({**self._scope_flags(scope), **data})

    # ------------------------------------------------------------------
    # 3.12. POST /balances/adjust — điều chỉnh quỹ phép thủ công (Phase 2).
    #   Quyết định (open Q#1): CHỈ HR Manager/Admin được chỉnh quỹ; Trưởng
    #   phòng KHÔNG. Body: {employeeId, leaveTypeId, deltaDays, reason}.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/balances/adjust', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_balance_adjust(self, **kw):
        scope = self._scope()
        if not scope['isHrManager']:
            return request.make_json_response({'error': 'forbidden'}, status=403)

        payload = request.get_json_data()
        try:
            employee_id = int(payload.get('employeeId'))
            leave_type_id = int(payload.get('leaveTypeId'))
        except (TypeError, ValueError):
            return request.make_json_response({'error': 'bad_request'}, status=400)
        try:
            delta = float(payload.get('deltaDays'))
        except (TypeError, ValueError):
            return request.make_json_response({'error': 'bad_request'}, status=400)
        reason = (payload.get('reason') or '').strip()
        if not reason:
            return request.make_json_response(
                {'error': 'reason_required',
                 'message': 'Vui lòng nhập lý do điều chỉnh.'}, status=400)
        if not delta:
            return request.make_json_response(
                {'error': 'zero_delta',
                 'message': 'Số ngày điều chỉnh phải khác 0.'}, status=400)

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return request.make_json_response(
                {'error': 'employee_not_found'}, status=404)
        if leave_type_id not in _hb_leave_type_ids(request.env):
            return request.make_json_response(
                {'error': 'leave_type_not_found'}, status=404)
        leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
        if not leave_type.requires_allocation:
            return request.make_json_response(
                {'error': 'leave_type_no_allocation',
                 'message': 'Loại nghỉ này không dùng quỹ phép.'}, status=400)

        try:
            _apply_quota_adjustment(request.env, employee, leave_type,
                                    delta, reason, self._this_year())
        except (AccessError, ValidationError, UserError) as ex:
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)

        alloc_types = (request.env['hr.leave.type'].sudo()
                       .browse(_hb_leave_type_ids(request.env))
                       .filtered('requires_allocation'))
        row = _employee_balance_row(employee, alloc_types)
        return request.make_json_response({**self._scope_flags(scope), 'row': row})

    # ------------------------------------------------------------------
    # 3.13. GET /balances/history — nhật ký điều chỉnh quỹ (Phase 2).
    #   HR/Admin xem tất cả; Trưởng phòng chỉ NV phòng mình. Lọc theo
    #   employeeId / leaveTypeId (tùy chọn).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/balances/history', auth='user',
                type='http', methods=['GET'])
    def api_balance_history(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            employee_id = int(kw.get('employeeId')) if kw.get('employeeId') else False
        except (TypeError, ValueError):
            employee_id = False
        try:
            leave_type_id = int(kw.get('leaveTypeId')) if kw.get('leaveTypeId') else False
        except (TypeError, ValueError):
            leave_type_id = False
        history = _adjustment_history(request.env, scope, employee_id, leave_type_id)
        return request.make_json_response({
            **self._scope_flags(scope), 'history': history})

    # ------------------------------------------------------------------
    # 3.14. GET /coverage — mức độ trùng lịch nghỉ theo ngày (Phase 4).
    #   Chỉ vai trò duyệt (HR/Admin = mọi phòng; Trưởng phòng = phòng được
    #   giao). NV thường → 403. Params: from, to (YYYY-MM-DD), dept (lọc 1
    #   phòng ban). Thiếu from/to → mặc định cả năm hiện tại.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/timeoff/coverage', auth='user',
                type='http', methods=['GET'])
    def api_coverage(self, **kw):
        scope = self._scope()
        if not scope['canApprove']:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        year = self._this_year()
        date_from = (kw.get('from') or '').strip() or '%d-01-01' % year
        date_to = (kw.get('to') or '').strip() or '%d-12-31' % year
        try:
            dept_id = int(kw.get('dept')) if kw.get('dept') else False
        except (TypeError, ValueError):
            dept_id = False
        # Trưởng phòng chỉ lọc trong phạm vi phòng ban được giao.
        if dept_id and not scope['seeAll'] and dept_id not in scope['deptIds']:
            dept_id = False
        data = _coverage_table(request.env, scope, date_from, date_to, dept_id)
        return request.make_json_response({
            **self._scope_flags(scope),
            'allDepartments': [{'id': d.id, 'name': d.name}
                               for d in self._scoped_departments(scope)],
            **data,
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
