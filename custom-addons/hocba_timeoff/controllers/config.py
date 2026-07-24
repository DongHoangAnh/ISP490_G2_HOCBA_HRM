# ============================================================
# JSON API cho SPA — khu CẤU HÌNH Time Off (chỉ Admin base.group_system).
# Tách khỏi main.py: đây là cấu hình hệ thống, không phải nghiệp vụ vận hành.
# Mọi endpoint gate has_group('base.group_system'); ghi qua sudo() sau cổng
# quyền (theo gotcha self-service của dự án). Hàm cấp module để test gọi trực
# tiếp với env(user=...). Owner: Nhật Anh.
# ============================================================
from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

VALIDATION_TYPES = ('no_validation', 'hr', 'manager', 'both')
REQUEST_UNITS = ('day', 'half_day')  # Học Bá không dùng 'hour'


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
