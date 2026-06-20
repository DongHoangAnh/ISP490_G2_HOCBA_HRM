from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HbWorkDay(models.Model):
    """Ngày đi làm thêm ngoài lịch chuẩn (Thứ 2–Thứ 6).

    Công ty làm việc Thứ 2 → Thứ 6; HR thêm các ngày Thứ 7 (hoặc ngày khác)
    phải đi làm vào model này. Lịch SPA (tab "Lịch") đọc ra để hiển thị.
    """
    _name = 'hb.work.day'
    _description = 'Ngày làm việc thêm (Học Bá)'
    _order = 'date'
    _rec_name = 'date'

    name = fields.Char(string='Ghi chú', default='Ngày đi làm')
    date = fields.Date(string='Ngày', required=True, index=True)
    company_id = fields.Many2one(
        'res.company', string='Công ty',
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('uniq_work_day_date', 'unique(date, company_id)',
         'Ngày làm việc này đã có trong lịch.'),
    ]

    @api.constrains('date', 'company_id')
    def _check_unique_date(self):
        for rec in self:
            if rec.search_count([
                ('id', '!=', rec.id),
                ('date', '=', rec.date),
                ('company_id', '=', rec.company_id.id),
            ]):
                raise ValidationError(
                    _('Ngày làm việc %s đã có trong lịch.', rec.date))
