# ============================================================
# JSON API cho SPA — khu CẤU HÌNH Time Off (chỉ Admin base.group_system).
# Tách khỏi main.py: đây là cấu hình hệ thống, không phải nghiệp vụ vận hành.
# Mọi endpoint gate has_group('base.group_system'); ghi qua sudo() sau cổng
# quyền (theo gotcha self-service của dự án). Hàm cấp module để test gọi trực
# tiếp với env(user=...). Owner: Nhật Anh.
# ============================================================
from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

VALIDATION_TYPES = ('no_validation', 'hr', 'manager', 'both')
REQUEST_UNITS = ('day', 'half_day')  # Học Bá không dùng 'hour'
ALLOCATION_MODES = ('accrual', 'fixed', 'none')


def _is_admin(env):
    return env.user.has_group('base.group_system')


def _leave_type_row(env, lt):
    in_use = env['hr.leave'].sudo().search_count(
        [('holiday_status_id', '=', lt.id)])
    return {
        'id': lt.id,
        'name': lt.name or '',
        'requiresAllocation': bool(lt.requires_allocation),
        'unpaid': bool(lt.unpaid),
        'validationType': lt.leave_validation_type or 'hr',
        'requestUnit': lt.request_unit or 'day',
        'supportDocument': bool(lt.support_document),
        'isEmergency': bool(lt.x_is_emergency_type),
        'color': lt.color or 0,
        'active': bool(lt.active),
        'inUseCount': in_use,
    }


def _config_list_leave_types(env):
    types = (env['hr.leave.type'].sudo()
             .with_context(active_test=False)
             .search([('x_hb_managed', '=', True)], order='active desc, id'))
    return [_leave_type_row(env, lt) for lt in types]


def _coerce_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError('%s không hợp lệ.' % label)


def _normalize_leave_type_vals(vals):
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên loại nghỉ không được để trống.')
    validation = vals.get('validationType') or 'hr'
    if validation not in VALIDATION_TYPES:
        raise ValidationError('Bậc duyệt không hợp lệ.')
    unit = vals.get('requestUnit') or 'day'
    if unit not in REQUEST_UNITS:
        raise ValidationError('Đơn vị nghỉ không hợp lệ (chỉ cả ngày / nửa ngày).')
    return {
        'name': name,
        'requires_allocation': bool(vals.get('requiresAllocation')),
        'unpaid': bool(vals.get('unpaid')),
        'leave_validation_type': validation,
        'request_unit': unit,
        'support_document': bool(vals.get('supportDocument')),
        'x_is_emergency_type': bool(vals.get('isEmergency')),
        'color': int(vals.get('color') or 0),
    }


def _assert_unique_flag(env, field, rec_id, is_active):
    """Bất biến Học Bá: trong các loại nghỉ HB ĐANG BẬT, tối đa MỘT loại
    requires_allocation=True và tối đa MỘT loại unpaid=True (màn quỹ/balance ở
    main.py giả định duy nhất một loại mỗi thứ). Chỉ kiểm khi loại đang lưu sẽ ở
    trạng thái active — loại đã tắt không ảnh hưởng các màn chỉ đọc loại active."""
    if not is_active:
        return
    conflict = env['hr.leave.type'].sudo().search([
        ('x_hb_managed', '=', True), ('active', '=', True),
        (field, '=', True), ('id', '!=', rec_id or 0),
    ], limit=1)
    if conflict:
        label = ('trừ vào quỹ phép' if field == 'requires_allocation'
                 else 'nghỉ không lương')
        raise ValidationError(
            'Chỉ được phép MỘT loại nghỉ bật "%s". Loại "%s" đang giữ thuộc '
            'tính này — hãy tắt ở loại đó trước.' % (label, conflict.name))


def _config_save_leave_type(env, vals):
    write_vals = _normalize_leave_type_vals(vals)
    Model = env['hr.leave.type'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        lt = Model.with_context(active_test=False).browse(int(rec_id))
        if not lt.exists() or not lt.x_hb_managed:
            raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
        is_active = lt.active
        if write_vals['requires_allocation']:
            _assert_unique_flag(env, 'requires_allocation', lt.id, is_active)
        if write_vals['unpaid']:
            _assert_unique_flag(env, 'unpaid', lt.id, is_active)
        lt.write(write_vals)
    else:
        write_vals['x_hb_managed'] = True
        if write_vals['requires_allocation']:
            _assert_unique_flag(env, 'requires_allocation', None, True)
        if write_vals['unpaid']:
            _assert_unique_flag(env, 'unpaid', None, True)
        lt = Model.create(write_vals)
    return _leave_type_row(env, lt)


def _config_toggle_leave_type(env, rec_id, active):
    lt = (env['hr.leave.type'].sudo()
          .with_context(active_test=False).browse(int(rec_id)))
    if not lt.exists() or not lt.x_hb_managed:
        raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
    if active:
        if lt.requires_allocation:
            _assert_unique_flag(env, 'requires_allocation', lt.id, True)
        if lt.unpaid:
            _assert_unique_flag(env, 'unpaid', lt.id, True)
    lt.active = bool(active)
    return _leave_type_row(env, lt)


def _policy_row(env, rule):
    labels = dict(rule._fields['employment_type'].selection)
    return {
        'id': rule.id,
        'name': rule.name or '',
        'employmentType': rule.employment_type,
        'employmentLabel': labels.get(rule.employment_type, rule.employment_type),
        'leaveTypeIds': rule.leave_type_ids.ids,
        'allocationMode': rule.allocation_mode,
        'accrualPlanId': rule.accrual_plan_id.id or False,
        'annualDays': rule.annual_days,
        'notes': rule.notes or '',
        'employeeCount': rule.employee_count,
    }


def _config_list_policies(env):
    rules = env['hb.timeoff.policy.rule'].sudo().search([], order='employment_type')
    managed = (env['hr.leave.type'].sudo()
               .search([('x_hb_managed', '=', True)], order='id'))
    plans = env['hr.leave.accrual.plan'].sudo().search([], order='name')
    return {
        'policies': [_policy_row(env, r) for r in rules],
        'leaveTypeChoices': [{'id': t.id, 'name': t.name} for t in managed],
        'accrualPlanChoices': [{'id': p.id, 'name': p.name} for p in plans],
        'allocationModes': [
            {'value': 'accrual', 'label': 'Tích lũy tự động'},
            {'value': 'fixed', 'label': 'Phân bổ cố định'},
            {'value': 'none', 'label': 'Không phân bổ'},
        ],
    }


def _config_save_policy(env, vals):
    rec_id = vals.get('id')
    if not rec_id:
        raise ValidationError(
            'Thiếu id chính sách — chỉ được sửa 6 chính sách có sẵn.')
    rule = env['hb.timeoff.policy.rule'].sudo().browse(
        _coerce_int(rec_id, 'ID chính sách'))
    if not rule.exists():
        raise ValidationError('Chính sách không tồn tại.')
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên chính sách không được để trống.')
    mode = vals.get('allocationMode') or 'none'
    if mode not in ALLOCATION_MODES:
        raise ValidationError('Chế độ phân bổ không hợp lệ.')
    try:
        annual = float(vals.get('annualDays') or 0)
    except (TypeError, ValueError):
        raise ValidationError('Số ngày phép năm không hợp lệ.')
    if annual < 0:
        raise ValidationError('Số ngày phép năm không được âm.')
    req_ids = [_coerce_int(x, 'Loại nghỉ') for x in (vals.get('leaveTypeIds') or [])]
    managed_ids = set(env['hr.leave.type'].sudo()
                      .search([('x_hb_managed', '=', True), ('id', 'in', req_ids)]).ids)
    valid_ids = [i for i in req_ids if i in managed_ids]
    plan_id = vals.get('accrualPlanId')
    plan_final = False
    if plan_id:
        pid = _coerce_int(plan_id, 'Kế hoạch tích lũy')
        if not env['hr.leave.accrual.plan'].sudo().browse(pid).exists():
            raise ValidationError('Kế hoạch tích lũy không tồn tại.')
        plan_final = pid
    # employment_type CỐ Ý không cho sửa (khoá UNIQUE, ánh xạ loại NV).
    rule.write({
        'name': name,
        'allocation_mode': mode,
        'annual_days': annual,
        'notes': vals.get('notes') or False,
        'leave_type_ids': [(6, 0, valid_ids)],
        'accrual_plan_id': plan_final,
    })
    return _policy_row(env, rule)


def _holiday_row(mday):
    return {
        'id': mday.id,
        'name': mday.name or '',
        'startDate': str(mday.start_date),
        'endDate': str(mday.end_date),
        'color': mday.color or 0,
    }


def _twin_calendar_leaves(env, start_date):
    """Bản resource.calendar.leaves 'twin' của ngày lễ — khớp theo NGÀY bắt đầu
    (ngày lễ Học Bá không chồng lấn nên đủ định danh). start_date: date."""
    day_start = fields.Datetime.to_datetime('%s 00:00:00' % start_date)
    day_end = fields.Datetime.to_datetime('%s 23:59:59' % start_date)
    return env['resource.calendar.leaves'].sudo().search([
        ('calendar_id', '=', False),
        ('resource_id', '=', False),
        ('time_type', '=', 'leave'),
        ('date_from', '>=', day_start),
        ('date_from', '<=', day_end),
    ])


def _calendar_leave_vals(name, start_date, end_date):
    return {
        'name': name,
        'date_from': fields.Datetime.to_datetime('%s 00:00:00' % start_date),
        'date_to': fields.Datetime.to_datetime('%s 23:59:59' % end_date),
        'time_type': 'leave',
        'calendar_id': False,
        'resource_id': False,
    }


def _validate_holiday_vals(vals):
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên ngày lễ không được để trống.')
    try:
        start = fields.Date.to_date(vals.get('startDate'))
        end = fields.Date.to_date(vals.get('endDate'))
    except (ValueError, TypeError):
        raise ValidationError('Ngày không hợp lệ.')
    if not start or not end:
        raise ValidationError('Thiếu ngày bắt đầu/kết thúc.')
    if end < start:
        raise ValidationError('Ngày kết thúc phải >= ngày bắt đầu.')
    return name, start, end


def _config_list_holidays(env, year):
    year = int(year)
    MDay = env['hr.leave.mandatory.day'].sudo()
    days = MDay.search([
        ('start_date', '>=', '%d-01-01' % year),
        ('start_date', '<=', '%d-12-31' % year),
    ], order='start_date')
    years = sorted({d.start_date.year for d in MDay.search([]) if d.start_date})
    return {
        'year': year,
        'holidays': [_holiday_row(d) for d in days],
        'years': years,
    }


def _config_save_holiday(env, vals):
    name, start, end = _validate_holiday_vals(vals)
    color = _coerce_int(vals.get('color') or 1, 'Màu')
    MDay = env['hr.leave.mandatory.day'].sudo()
    Cal = env['resource.calendar.leaves'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        mday = MDay.browse(_coerce_int(rec_id, 'ID ngày lễ'))
        if not mday.exists():
            raise ValidationError('Ngày lễ không tồn tại.')
        twin = _twin_calendar_leaves(env, mday.start_date)  # theo ngày CŨ
        mday.write({'name': name, 'start_date': start,
                    'end_date': end, 'color': color})
        if twin:
            twin.write(_calendar_leave_vals(name, start, end))
        else:
            Cal.create(_calendar_leave_vals(name, start, end))
    else:
        mday = MDay.create({'name': name, 'start_date': start,
                            'end_date': end, 'color': color})
        Cal.create(_calendar_leave_vals(name, start, end))
    return _holiday_row(mday)


def _config_delete_holiday(env, rec_id):
    MDay = env['hr.leave.mandatory.day'].sudo()
    hid = _coerce_int(rec_id, 'ID ngày lễ')
    mday = MDay.browse(hid)
    if not mday.exists():
        raise ValidationError('Ngày lễ không tồn tại.')
    _twin_calendar_leaves(env, mday.start_date).unlink()
    mday.unlink()
    return {'ok': True, 'id': hid}


class HocBaTimeoffConfig(http.Controller):

    def _guard(self):
        """Trả response 403 nếu không phải Admin; None nếu OK."""
        if not _is_admin(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        return None

    @http.route('/hocba-hrm/api/timeoff/config/leave-types',
                auth='user', type='http', methods=['GET'])
    def leave_types(self, **kw):
        block = self._guard()
        if block:
            return block
        return request.make_json_response(
            {'leaveTypes': _config_list_leave_types(request.env)})

    @http.route('/hocba-hrm/api/timeoff/config/leave-types/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def leave_type_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_leave_type(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'leaveType': row})

    @http.route('/hocba-hrm/api/timeoff/config/leave-types/toggle-active',
                auth='user', type='http', methods=['POST'], csrf=False)
    def leave_type_toggle(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_toggle_leave_type(
                request.env, payload.get('id'), payload.get('active'))
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'leaveType': row})

    @http.route('/hocba-hrm/api/timeoff/config/policies',
                auth='user', type='http', methods=['GET'])
    def policies(self, **kw):
        block = self._guard()
        if block:
            return block
        return request.make_json_response(_config_list_policies(request.env))

    @http.route('/hocba-hrm/api/timeoff/config/policies/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def policy_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_policy(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'policy': row})

    @http.route('/hocba-hrm/api/timeoff/config/holidays',
                auth='user', type='http', methods=['GET'])
    def holidays(self, **kw):
        block = self._guard()
        if block:
            return block
        try:
            year = int(kw.get('year') or fields.Date.today().year)
        except (TypeError, ValueError):
            year = fields.Date.today().year
        return request.make_json_response(
            _config_list_holidays(request.env, year))

    @http.route('/hocba-hrm/api/timeoff/config/holidays/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def holiday_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_holiday(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'holiday': row})

    @http.route('/hocba-hrm/api/timeoff/config/holidays/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def holiday_delete(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            _config_delete_holiday(request.env, payload.get('id'))
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'ok': True})
