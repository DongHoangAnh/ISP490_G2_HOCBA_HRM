from odoo import api, fields, models


class HbNotification(models.Model):
    _name = 'hb.notification'
    _description = 'Thông báo in-app (chuông SPA) — dùng chung mọi module'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    recipient_id = fields.Many2one(
        'res.users', string='Người nhận',
        required=True, ondelete='cascade', index=True)
    title = fields.Char(required=True)
