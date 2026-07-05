from odoo import api, fields, models


class HbNotification(models.Model):
    _name = 'hb.notification'
    _description = 'Thông báo in-app (chuông SPA) — dùng chung mọi module'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    CATEGORY_SEL = [
        ('timeoff', 'Nghỉ phép'),
        ('offboarding', 'Nghỉ việc'),
        ('onboarding', 'Nhận việc / Thử việc'),
        ('hr_reminder', 'Nhắc hạn hồ sơ'),
    ]
    LEVEL_SEL = [
        ('info', 'Info'), ('success', 'Success'),
        ('warning', 'Warning'), ('danger', 'Danger'),
    ]

    recipient_id = fields.Many2one(
        'res.users', string='Người nhận',
        required=True, ondelete='cascade', index=True)
    category = fields.Selection(CATEGORY_SEL, string='Nhóm', required=True, index=True)
    kind = fields.Char(string='Loại', required=True)
    level = fields.Selection(LEVEL_SEL, string='Mức', default='info', required=True)
    title = fields.Char(string='Tiêu đề', required=True)
    body = fields.Text(string='Nội dung')
    target_view = fields.Char(string='View đích')
    target_ref = fields.Integer(string='ID đích')
    target_tab = fields.Char(string='Tab đích')
    dedup_key = fields.Char(string='Khoá chống trùng', index=True)
    is_read = fields.Boolean(string='Đã đọc', default=False, index=True)

    @api.model
    def _notify(self, recipients, category, kind, level, title, body=None,
                target_view=None, target_ref=None, target_tab=None,
                dedup_key=None):
        """Tạo 1 thông báo cho mỗi recipient (chạy sudo). Bỏ recipient rỗng/
        inactive. Nếu có dedup_key: bỏ qua khi đã có dòng CHƯA ĐỌC cùng
        (recipient, dedup_key). Trả về recordset đã tạo."""
        if recipients is None:
            return self.browse()
        if isinstance(recipients, models.BaseModel):
            users = recipients
        else:
            ids = recipients if isinstance(recipients, (list, tuple, set)) else [recipients]
            users = self.env['res.users'].browse([i for i in ids if i])
        created = self.browse()
        for user in users:
            # browse() never filters deleted/inactive ids regardless of context,
            # nên phải kiểm .exists() + .active tường minh. .exists() short-circuit
            # nên .active an toàn với record đã xoá.
            if not user.exists() or not user.active:
                continue
            if dedup_key and self.sudo().search_count([
                    ('recipient_id', '=', user.id),
                    ('dedup_key', '=', dedup_key),
                    ('is_read', '=', False)]):
                continue
            created |= self.sudo().create({
                'recipient_id': user.id, 'category': category, 'kind': kind,
                'level': level, 'title': title, 'body': body or False,
                'target_view': target_view or False,
                'target_ref': target_ref or 0,
                'target_tab': target_tab or False,
                'dedup_key': dedup_key or False,
            })
        return created
