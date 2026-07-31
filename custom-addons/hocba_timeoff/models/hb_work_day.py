from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


def _fmt(day):
    """date → 'dd/mm/yyyy' cho thông báo lỗi (None-safe)."""
    return day.strftime('%d/%m/%Y') if day else ''


class HbWorkDay(models.Model):
    """Ngày đi làm thêm ngoài lịch chuẩn (Thứ 2–Thứ 6).

    Công ty làm việc Thứ 2 → Thứ 6; HR thêm các ngày Thứ 7 (hoặc ngày khác)
    phải đi làm vào model này. Lịch SPA (tab "Lịch") đọc ra để hiển thị.

    KHOÁ THEO NGÀY (`is_locked`): chỉ thao tác được với ngày CHƯA ĐẾN
    (date > hôm nay). Ngày hôm nay và các ngày đã qua bị đóng băng —
    không thêm, không sửa, không xoá. Lý do: `hocba.attendance.policy.is_workday`
    và `_count_working_days` (số ngày trừ quỹ phép) đọc bảng này làm nguồn chân
    lý; ngày đã diễn ra thì chấm công đã sinh bản ghi và lương đã tính theo lịch
    lúc đó. Xoá/đổi ngược lại sẽ khiến bản ghi chấm công + số ngày nghỉ đã trừ
    không còn khớp lịch — sai dữ liệu mà không ai phát hiện.
    Ngày hôm nay cũng khoá vì NV đã có thể chấm công từ sáng.
    Muốn đính chính lịch quá khứ → điều chỉnh bên chấm công, không sửa ở đây.
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
    is_locked = fields.Boolean(
        string='Đã chốt', compute='_compute_is_locked',
        help='Ngày đã đến hoặc đã qua → khoá, không sửa/xoá được nữa.')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint.
    # Khai bằng API cũ chỉ log WARNING rồi bỏ qua, Postgres không có constraint
    # nào cả → trùng ngày lọt qua, số ngày làm việc / SLA đọc bảng này bị lệch.
    _uniq_work_day_date = models.Constraint(
        'unique (date, company_id)',
        'Ngày làm việc này đã có trong lịch.',
    )

    # ------------------------------------------------------------------
    # Khoá theo ngày
    # ------------------------------------------------------------------
    @api.depends('date')
    def _compute_is_locked(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_locked = bool(rec.date and rec.date <= today)

    @api.model
    def _first_editable_date(self):
        """Ngày sớm nhất còn được thêm/sửa = ngày mai (theo tz người dùng)."""
        return fields.Date.add(fields.Date.context_today(self), days=1)

    # Lưới đỡ cho `_uniq_work_day_date`: thông báo rõ ngày nào bị trùng, và vẫn
    # chặn được nếu constraint chưa kịp tạo trên một DB nào đó.
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

    @api.model_create_multi
    def create(self, vals_list):
        limit = self._first_editable_date()
        for vals in vals_list:
            day = fields.Date.to_date(vals.get('date'))
            if day and day < limit:
                raise ValidationError(_(
                    'Không thêm được lịch làm việc cho ngày %(day)s: ngày này '
                    'đã đến hoặc đã qua. Chấm công và lương của ngày đã diễn '
                    'ra được tính theo lịch lúc đó, thêm ngược lại sẽ làm sai '
                    'dữ liệu. Chỉ thêm được từ ngày %(limit)s trở đi.',
                    day=_fmt(day), limit=_fmt(limit)))
        return super().create(vals_list)

    def write(self, vals):
        limit = self._first_editable_date()
        locked = self.filtered(lambda r: r.date and r.date < limit)
        if locked:
            raise ValidationError(_(
                'Ngày làm việc %(days)s đã diễn ra nên không sửa được nữa — '
                'chấm công và lương của ngày đó đã tính theo lịch này. Chỉ sửa '
                'được ngày chưa đến (từ %(limit)s trở đi).',
                days=', '.join(_fmt(r.date) for r in locked),
                limit=_fmt(limit)))
        if 'date' in vals:
            new_day = fields.Date.to_date(vals['date'])
            if new_day and new_day < limit:
                raise ValidationError(_(
                    'Không chuyển lịch làm việc sang ngày %(day)s: ngày này đã '
                    'đến hoặc đã qua. Chỉ chọn được từ ngày %(limit)s trở đi.',
                    day=_fmt(new_day), limit=_fmt(limit)))
        return super().write(vals)

    def unlink(self):
        limit = self._first_editable_date()
        locked = self.filtered(lambda r: r.date and r.date < limit)
        if locked:
            raise ValidationError(_(
                'Không xoá được ngày làm việc %(days)s vì ngày đó đã diễn ra: '
                'nhân viên có thể đã chấm công và lương đã tính theo lịch này. '
                'Chỉ xoá được ngày chưa đến (từ %(limit)s trở đi).',
                days=', '.join(_fmt(r.date) for r in locked),
                limit=_fmt(limit)))
        return super().unlink()
