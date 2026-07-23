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


def _config_save_leave_type(env, vals):
    write_vals = _normalize_leave_type_vals(vals)
    Model = env['hr.leave.type'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        lt = Model.with_context(active_test=False).browse(int(rec_id))
        if not lt.exists() or not lt.x_hb_managed:
            raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
        lt.write(write_vals)
    else:
        write_vals['x_hb_managed'] = True
        lt = Model.create(write_vals)
    return _leave_type_row(env, lt)


def _config_toggle_leave_type(env, rec_id, active):
    lt = (env['hr.leave.type'].sudo()
          .with_context(active_test=False).browse(int(rec_id)))
    if not lt.exists() or not lt.x_hb_managed:
        raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
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
