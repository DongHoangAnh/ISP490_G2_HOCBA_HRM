from odoo import fields, http
from odoo.http import request


def _d(dt):
    return fields.Datetime.to_string(dt) if dt else None


def _notif_row(rec):
    return {
        'id': rec.id,
        'category': rec.category,
        'kind': rec.kind,
        'level': rec.level,
        'title': rec.title,
        'body': rec.body or '',
        'targetView': rec.target_view or None,
        'targetRef': rec.target_ref or None,
        'targetTab': rec.target_tab or None,
        'isRead': rec.is_read,
        'createdAt': _d(rec.create_date),
    }


def _list_notifications(env, limit=20):
    """Thông báo của chính user (mới nhất trước) + số chưa đọc cho badge."""
    N = env['hb.notification'].sudo()
    base = [('recipient_id', '=', env.uid)]
    recs = N.search(base, limit=limit or 20)
    unread = N.search_count(base + [('is_read', '=', False)])
    return {'items': [_notif_row(r) for r in recs], 'unread': unread}


def _mark_read(env, notif_id):
    """Đánh dấu 1 thông báo đã đọc — chỉ khi thuộc về chính user. True/False."""
    rec = env['hb.notification'].sudo().browse(int(notif_id))
    if not rec.exists() or rec.recipient_id.id != env.uid:
        return False
    if not rec.is_read:
        rec.is_read = True
    return True


def _mark_all(env):
    """Đánh dấu tất cả của user là đã đọc — trả số dòng vừa đổi."""
    recs = env['hb.notification'].sudo().search(
        [('recipient_id', '=', env.uid), ('is_read', '=', False)])
    recs.write({'is_read': True})
    return len(recs)


class HocbaNotify(http.Controller):

    @http.route('/hocba-hrm/api/notifications', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_list(self, **kw):
        limit = int(kw.get('limit') or 20)
        return request.make_json_response(
            _list_notifications(request.env, limit))

    @http.route('/hocba-hrm/api/notifications/<int:notif_id>/read',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_read(self, notif_id, **kw):
        if not _mark_read(request.env, notif_id):
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(_list_notifications(request.env))

    @http.route('/hocba-hrm/api/notifications/read-all',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_read_all(self, **kw):
        _mark_all(request.env)
        return request.make_json_response(_list_notifications(request.env))
