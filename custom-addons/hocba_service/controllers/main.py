# ============================================================
# JSON API cho SPA — domain Dịch vụ Nhân sự (service). Owner: Nhật Anh.
# Spec: docs/superpowers/specs/2026-07-26-hr-service-request-design.md §6
#
# Dùng prefix /hocba-hrm/api/service/* nhưng đặt trong module hocba_service
# (mỗi domain tự quản controller của mình — tiền lệ hocba_timeoff).
#
# NGUYÊN TẮC LỚP NÀY: controller là lớp MỎNG. Toàn bộ business rule nằm ở
# model (hocba.hr.request.create_request / post_message / action_*) nên P1 test
# được nghiệp vụ khi chưa có API. Ở đây chỉ: parse JSON → gọi model → map
# exception sang HTTP. TUYỆT ĐỐI không tự dựng payload của đơn: mọi payload
# phải đi qua request.serialize() — đó là chốt cuối chống rò danh tính
# (SPEC §4.2 lớp L3).
# ============================================================
import base64
import binascii

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import content_disposition, request

from odoo.addons.hocba_service.models.hocba_hr_request import (
    DEFAULT_ANON_DAILY, DEFAULT_MIN_ANON_DEPT, OPEN_STATES,
    PARAM_ANON_DAILY, PARAM_MIN_ANON_DEPT, SvcError,
    _inbox_domain, _my_request_ids, _param_int, _svc_scope,
)

# Đính kèm (chỉ đơn KHÔNG ẩn danh — BR-SVC-02). Giới hạn giống chứng từ y tế
# của hocba_timeoff để hạ tầng lưu trữ hành xử nhất quán.
ALLOWED_MIME = frozenset({'application/pdf', 'image/jpeg', 'image/png'})
MAX_SIZE_BYTES = 5 * 1024 * 1024
MAX_FILES = 3

# Pseudo-state cho filter của SPA: gộp new + in_progress.
STATE_OPEN = 'open'


# ---------------------------------------------------------------------------
# Helper cấp module (nhận env) — controller dùng dưới request, test gọi trực
# tiếp với self.env(user=...) theo quy ước test của repo (không có HttpCase).
# ---------------------------------------------------------------------------

def _type_payload(rt):
    return {
        'id': rt.id,
        'code': rt.code,
        'name': rt.name,
        'defaultRecipient': rt.default_recipient,
        'forceHrOnly': rt.force_hr_only,
        'allowAnonymous': rt.allow_anonymous,
        'allowAttachment': rt.allow_attachment,
        'hasRating': rt.has_rating,
        'slaDays': rt.sla_days,
        'description': rt.description or '',
    }


def _meta_payload(env):
    """Danh mục loại + cờ vai trò + thông tin phòng để form tự chặn trước.

    Trả cả 2 ngưỡng cấu hình + số đơn ẩn danh đã dùng hôm nay để SPA cảnh báo
    tại chỗ (§7.3) thay vì để người dùng viết xong đơn mới ăn lỗi 400.
    """
    scope = _svc_scope(env)
    emp = env.user.sudo().employee_id
    dept = emp.sudo().department_id if emp else None
    types = env['hocba.hr.request.type'].sudo().search([('active', '=', True)])
    headcount = env['hocba.hr.request']._dept_headcount(dept) if dept else 0
    return {
        'isHr': scope['isHr'],
        'isHrManager': scope['isHrManager'],
        'isDeptManager': scope['isDeptManager'],
        'canHandle': scope['canHandle'],
        # Tab "Cấu hình" (P6) — chỉ HR Manager/Admin. Cùng một cờ với
        # _config_guard() ở model để SPA không đoán vai trò khác BE.
        'canConfig': scope['isHrManager'],
        'canSend': bool(emp),
        'types': [_type_payload(rt) for rt in types],
        'myDepartment': {
            'id': dept.id,
            'name': dept.name,
            'headcount': headcount,
            'hasManager': bool(dept.manager_id),
            # BR-SVC-04: TP tự gửi cho phòng mình sẽ bị đổi hướng về HR — nói
            # trước ở form thay vì để người dùng ngạc nhiên sau khi gửi.
            'iAmManager': bool(emp) and dept.manager_id.id == emp.id,
        } if dept else None,
        'minAnonDeptSize': _param_int(
            env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT),
        'anonDailyLimit': _param_int(
            env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY),
        'anonUsedToday': env['hocba.hr.request']._anon_count_today(),
    }


def _state_domain(state):
    """'open' → new + in_progress; còn lại là state thật; '' → không lọc."""
    key = (state or '').strip()
    if not key:
        return []
    if key == STATE_OPEN:
        return [('state', 'in', list(OPEN_STATES))]
    return [('state', '=', key)]


def _year_domain(year):
    try:
        y = int(year)
    except (TypeError, ValueError):
        return []
    return [('create_date', '>=', '%d-01-01 00:00:00' % y),
            ('create_date', '<=', '%d-12-31 23:59:59' % y)]


def _store_attachments(env, files):
    """Tạo ir.attachment từ danh sách base64 của SPA, trả list id.

    Chỉ dùng cho đơn KHÔNG ẩn danh. Route gọi hàm này TRONG savepoint: nếu
    create_request() phía sau bác đơn thì file vừa tạo bị rollback, không để lại
    attachment mồ côi.
    """
    if len(files) > MAX_FILES:
        raise SvcError('too_many_files', env._(
            'Mỗi đơn đính kèm tối đa %s tệp.', MAX_FILES))
    Att = env['ir.attachment'].sudo()
    ids = []
    for item in files:
        if not isinstance(item, dict):
            raise SvcError('bad_attachment', env._('Tệp đính kèm không hợp lệ.'))
        name = (item.get('name') or '').strip() or 'tep-dinh-kem'
        mimetype = (item.get('mimetype') or '').strip().lower()
        raw = item.get('data') or ''
        if mimetype not in ALLOWED_MIME:
            raise SvcError('bad_mimetype', env._(
                'Chỉ nhận tệp PDF, JPG hoặc PNG (tệp "%s").', name))
        try:
            decoded = base64.b64decode(raw, validate=True)
        except (binascii.Error, ValueError, TypeError):
            raise SvcError('bad_attachment', env._(
                'Không đọc được nội dung tệp "%s".', name))
        if not decoded:
            raise SvcError('bad_attachment', env._('Tệp "%s" rỗng.', name))
        if len(decoded) > MAX_SIZE_BYTES:
            raise SvcError('file_too_large', env._(
                'Tệp "%s" vượt quá 5MB.', name))
        ids.append(Att.create({
            'name': name,
            'datas': raw,
            'mimetype': mimetype,
            'res_model': 'hocba.hr.request',
            'res_id': 0,
        }).id)
    return ids


def _create_from_payload(env, payload):
    """Map payload camelCase của SPA → vals của create_request().

    ⚠️ CỐ TÌNH không nhận `attachmentIds` (danh sách id có sẵn) như bản nháp §6:
    client tự chọn id là lỗ hổng — gắn id attachment của người khác vào đơn của
    mình rồi tải về qua /service/attachment/<id>. Chỉ nhận nội dung base64 và
    tự tạo record (đúng cách hocba_timeoff nhận chứng từ y tế).
    """
    files = payload.get('attachments') or []
    if not isinstance(files, list):
        raise SvcError('bad_attachment', env._('Danh sách tệp không hợp lệ.'))
    att_ids = _store_attachments(env, files) if files else []
    vals = {
        'type_id': payload.get('typeId'),
        'subject': payload.get('subject'),
        'body': payload.get('body'),
        'recipient_scope': (payload.get('recipientScope') or '').strip() or None,
        'target_department_id': payload.get('targetDepartmentId') or False,
        'is_anonymous': bool(payload.get('isAnonymous')),
        'rating': (str(payload.get('rating')).strip()
                   if payload.get('rating') else False),
        'priority': (payload.get('priority') or '').strip() or 'normal',
        'attachment_ids': att_ids,
    }
    req = env['hocba.hr.request'].create_request(vals)
    if att_ids:
        # Gắn res_id sau khi có đơn để route tải file kiểm tra được nguồn gốc.
        env['ir.attachment'].sudo().browse(att_ids).write({'res_id': req.id})
    return req


def _my_requests_payload(env, state=None, year=None):
    """Đơn của tôi. Danh tính người gửi nằm ở bảng không ACL nên phải đi qua
    _my_request_ids() (pin uid TRƯỚC, sudo SAU)."""
    Request = env['hocba.hr.request']
    ids = _my_request_ids(env)
    if not ids:
        return {'requests': [], 'years': []}
    base = [('id', 'in', ids)]
    recs = Request.sudo().search(base + _state_domain(state) + _year_domain(year))
    years = sorted({r.create_date.year
                    for r in Request.sudo().browse(ids) if r.create_date},
                   reverse=True)
    return {
        'requests': [r.serialize(viewer_is_sender=True) for r in recs],
        'years': years,
    }


def _inbox_payload(env, state=None, overdue=False, type_id=None, q=None):
    """Hộp thư cần xử lý của HR / Trưởng phòng (BR-SVC-13 nằm trong
    _inbox_domain — HR Manager KHÔNG giám sát đơn của Trưởng phòng)."""
    scope = _svc_scope(env)
    if not scope['canHandle']:
        raise AccessError(env._('Bạn không có hộp thư xử lý yêu cầu dịch vụ.'))
    domain = _inbox_domain(scope) + _state_domain(state)
    if overdue:
        domain += [('is_overdue', '=', True)]
    if type_id:
        domain += [('type_id', '=', int(type_id))]
    keyword = (q or '').strip()
    if keyword:
        domain += ['|', '|', ('name', 'ilike', keyword),
                   ('subject', 'ilike', keyword), ('body', 'ilike', keyword)]
    recs = env['hocba.hr.request'].sudo().search(domain)
    return {
        'isHr': scope['isHr'],
        'isHrManager': scope['isHrManager'],
        'isDeptManager': scope['isDeptManager'],
        'canHandle': True,
        'requests': [r.serialize(viewer_is_sender=False) for r in recs],
    }


def _visible_request(env, rid):
    """(record, viewer_is_sender) nếu user được xem đơn.

    None → không tồn tại (route trả 404). AccessError → ngoài phạm vi (403).
    .sudo() ở đây an toàn cho việc xác định vai trò: Odoo 19 .sudo() KHÔNG đổi
    env.user nên _is_sender()/_can_handle() vẫn soi đúng user thật.
    """
    rec = env['hocba.hr.request'].sudo().browse(rid)
    if not rec.exists():
        return None, False
    if rec._is_sender():
        return rec, True
    if rec._can_handle():
        return rec, False
    raise AccessError(env._('Bạn không có quyền trên đơn này.'))


def _detail_payload(env, rid):
    rec, is_sender = _visible_request(env, rid)
    if rec is None:
        return None
    return rec.serialize(viewer_is_sender=is_sender, with_messages=True)


def _stats_payload(env):
    """KPI hộp thư của chính người xử lý (không phải KPI toàn hệ thống — HR
    Manager cũng chỉ thấy phạm vi mình đọc được, BR-SVC-13)."""
    scope = _svc_scope(env)
    if not scope['canHandle']:
        raise AccessError(env._('Bạn không có hộp thư xử lý yêu cầu dịch vụ.'))
    recs = env['hocba.hr.request'].sudo().search(_inbox_domain(scope))
    open_recs = recs.filtered(lambda r: r.state in OPEN_STATES)
    handled = recs.filtered(lambda r: r.answered_at and r.create_date)
    hours = [(r.answered_at - r.create_date).total_seconds() / 3600.0
             for r in handled]
    rated = recs.filtered(lambda r: r.rating)
    ratings = [int(r.rating) for r in rated]
    by_type = {}
    for rec in recs:
        row = by_type.setdefault(
            rec.type_id.id, {'typeId': rec.type_id.id,
                             'typeName': rec.type_id.name, 'count': 0})
        row['count'] += 1
    return {
        'total': len(recs),
        'open': len(open_recs),
        'overdue': len(recs.filtered(lambda r: r.is_overdue)),
        'anonymous': len(recs.filtered(lambda r: r.is_anonymous)),
        'avgHandleHours': round(sum(hours) / len(hours), 1) if hours else None,
        'avgRating': round(sum(ratings) / len(ratings), 2) if ratings else None,
        'ratedCount': len(ratings),
        'byType': sorted(by_type.values(), key=lambda r: -r['count']),
    }


def _config_payload(env):
    """Màn Cấu hình (P6): TẤT CẢ loại (kể cả đã tắt) + 2 ngưỡng + số đơn đã dùng.

    Khác _meta_payload ở 3 chỗ, đừng gộp: (a) lấy cả loại đã tắt, (b) chỉ HR
    Manager/Admin đọc được, (c) kèm usageCount/openCount để Admin biết mình sắp
    tắt một loại đang có đơn chạy dở.
    """
    Type = env['hocba.hr.request.type']
    Type._config_guard()
    types = Type.with_context(active_test=False).search([])
    Request = env['hocba.hr.request'].sudo()
    used = dict(Request._read_group(
        [('type_id', 'in', types.ids)], ['type_id'], ['__count']))
    open_used = dict(Request._read_group(
        [('type_id', 'in', types.ids), ('state', 'in', list(OPEN_STATES))],
        ['type_id'], ['__count']))
    rows = []
    for rt in types:
        row = _type_payload(rt)
        row.update({
            'sequence': rt.sequence,
            'active': rt.active,
            'usageCount': used.get(rt, 0),
            'openCount': open_used.get(rt, 0),
        })
        rows.append(row)
    return {
        'canConfig': True,
        'types': rows,
        'params': {
            'minAnonDeptSize': _param_int(
                env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT),
            'anonDailyLimit': _param_int(
                env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY),
        },
    }


def _attachment_owner(env, att):
    """Đơn chứa attachment này. Quan hệ là Many2many nên không tin res_id —
    tra ngược qua bảng nối."""
    return env['hocba.hr.request'].sudo().search(
        [('attachment_ids', 'in', att.id)], limit=1)


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _err(code, message=None, status=400):
    body = {'error': code}
    if message:
        body['message'] = message
    return request.make_json_response(body, status=status)


def _guarded(build):
    """Chạy build() trong savepoint rồi map exception nghiệp vụ sang HTTP.

    - Savepoint: vì controller BẮT exception và trả 400/403, Odoo sẽ commit
      transaction như một request thành công ⇒ không có savepoint thì các ghi
      trước chỗ lỗi (điển hình: ir.attachment vừa tạo) bị commit mồ côi.
    - Thứ tự except: SvcError kế thừa ValidationError nên phải bắt TRƯỚC, nếu
      không mã lỗi nghiệp vụ (anon_dept_too_small…) bị nuốt thành 'invalid'.
    """
    try:
        with request.env.cr.savepoint():
            data = build()
    except SvcError as e:
        return _err(e.code, str(e))
    except AccessError as e:
        return _err('forbidden', str(e), status=403)
    except (ValidationError, UserError) as e:
        return _err('invalid', str(e))
    if data is None:
        return _err('not_found', status=404)
    return request.make_json_response(data)


class HocBaService(http.Controller):
    """API màn "Yêu cầu dịch vụ nhân sự" của SPA (SPEC SVC §6)."""

    # ------------------------------------------------------------------
    # 1. GET /meta — danh mục loại + cờ vai trò (form + bật/tắt tab)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/meta', auth='user',
                type='http', methods=['GET'])
    def api_meta(self, **kw):
        return _guarded(lambda: _meta_payload(request.env))

    # ------------------------------------------------------------------
    # 2. POST /request — gửi đơn (mọi BR chốt ở model.create_request)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/request', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_create(self, **kw):
        payload = request.get_json_data() or {}

        def build():
            req = _create_from_payload(request.env, payload)
            return req.serialize(viewer_is_sender=True, with_messages=True)
        return _guarded(build)

    # ------------------------------------------------------------------
    # 3. GET /my-requests — tab "Đơn của tôi"
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/my-requests', auth='user',
                type='http', methods=['GET'])
    def api_my_requests(self, state=None, year=None, **kw):
        return _guarded(
            lambda: _my_requests_payload(request.env, state=state, year=year))

    # ------------------------------------------------------------------
    # 4. GET /inbox — tab "Cần xử lý" (HR / Trưởng phòng)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/inbox', auth='user',
                type='http', methods=['GET'])
    def api_inbox(self, state=None, overdue=None, typeId=None, q=None, **kw):
        overdue_flag = str(overdue or '').lower() in ('1', 'true', 'yes')
        return _guarded(lambda: _inbox_payload(
            request.env, state=state, overdue=overdue_flag,
            type_id=typeId or None, q=q))

    # ------------------------------------------------------------------
    # 5. GET /request/<id> — chi tiết + hội thoại
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/request/<int:rid>', auth='user',
                type='http', methods=['GET'])
    def api_request_detail(self, rid, **kw):
        return _guarded(lambda: _detail_payload(request.env, rid))

    # ------------------------------------------------------------------
    # 6. POST /request/<id>/reply — hội thoại 2 chiều (+ ghi chú nội bộ)
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/request/<int:rid>/reply', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_reply(self, rid, **kw):
        payload = request.get_json_data() or {}

        def build():
            rec, is_sender = _visible_request(request.env, rid)
            if rec is None:
                return None
            # post_message tự chốt vai trò + ép is_internal=False cho người gửi
            # (BR-SVC-07) — controller không được tự quyết.
            rec.post_message(payload.get('body') or '',
                             is_internal=bool(payload.get('isInternal')))
            return rec.serialize(viewer_is_sender=is_sender, with_messages=True)
        return _guarded(build)

    # ------------------------------------------------------------------
    # 7-10. POST /request/<id>/{claim,answer,close,cancel} — vòng đời
    # ------------------------------------------------------------------
    def _action(self, rid, run):
        def build():
            rec, is_sender = _visible_request(request.env, rid)
            if rec is None:
                return None
            run(rec)
            return rec.serialize(viewer_is_sender=is_sender, with_messages=True)
        return _guarded(build)

    @http.route('/hocba-hrm/api/service/request/<int:rid>/claim', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_claim(self, rid, **kw):
        return self._action(rid, lambda rec: rec.action_claim())

    @http.route('/hocba-hrm/api/service/request/<int:rid>/answer', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_answer(self, rid, **kw):
        return self._action(rid, lambda rec: rec.action_answer())

    @http.route('/hocba-hrm/api/service/request/<int:rid>/close', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_close(self, rid, **kw):
        payload = request.get_json_data() or {}
        reason = payload.get('closedReason') or ''
        return self._action(rid, lambda rec: rec.action_close(reason))

    @http.route('/hocba-hrm/api/service/request/<int:rid>/cancel', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_request_cancel(self, rid, **kw):
        return self._action(rid, lambda rec: rec.action_cancel())

    # ------------------------------------------------------------------
    # 11. GET /stats — KPI hộp thư
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/stats', auth='user',
                type='http', methods=['GET'])
    def api_stats(self, **kw):
        return _guarded(lambda: _stats_payload(request.env))

    # ------------------------------------------------------------------
    # 12. GET /attachment/<id> — tải tệp đính kèm.
    #   Trưởng phòng không có group hr nào ⇒ /web/content chặn. Phục vụ qua
    #   đây với sudo + kiểm phạm vi tường minh (pattern /timeoff/attachment).
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/attachment/<int:att_id>', auth='user',
                type='http', methods=['GET'])
    def api_attachment(self, att_id, **kw):
        env = request.env
        att = env['ir.attachment'].sudo().browse(att_id)
        if not att.exists():
            return request.not_found()
        req = _attachment_owner(env, att)
        if not req:
            return request.not_found()
        try:
            _visible_request(env, req.id)
        except AccessError as e:
            return _err('forbidden', str(e), status=403)
        try:
            data = base64.b64decode(att.datas or b'')
        except (binascii.Error, ValueError):
            return request.not_found()
        return request.make_response(data, headers=[
            ('Content-Type', att.mimetype or 'application/octet-stream'),
            ('Content-Length', len(data)),
            ('Content-Disposition', content_disposition(att.name or 'tep')),
        ])

    # ------------------------------------------------------------------
    # 13-16. Cấu hình (P6) — Admin / HR Manager. Toàn bộ luật ở model
    #   hocba.hr.request.type.config_*; ở đây chỉ parse JSON như mọi route khác.
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/service/config/types', auth='user',
                type='http', methods=['GET'])
    def api_config_types(self, **kw):
        return _guarded(lambda: _config_payload(request.env))

    @http.route('/hocba-hrm/api/service/config/types/save', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_config_type_save(self, **kw):
        payload = request.get_json_data() or {}

        def build():
            request.env['hocba.hr.request.type'].config_save(payload)
            # Trả lại nguyên bảng: sửa 1 loại có thể đổi thứ tự hiển thị, và
            # SPA khỏi phải gọi thêm 1 vòng để làm mới.
            return _config_payload(request.env)
        return _guarded(build)

    @http.route('/hocba-hrm/api/service/config/types/toggle-active',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_config_type_toggle(self, **kw):
        payload = request.get_json_data() or {}

        def build():
            request.env['hocba.hr.request.type'].config_toggle_active(
                payload.get('id'), payload.get('active'))
            return _config_payload(request.env)
        return _guarded(build)

    @http.route('/hocba-hrm/api/service/config/params', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_config_params(self, **kw):
        payload = request.get_json_data() or {}

        def build():
            request.env['hocba.hr.request.type'].config_set_params(payload)
            return _config_payload(request.env)
        return _guarded(build)
