import pytz
from datetime import datetime, time as dt_time

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Khung giờ 09:00–17:00, mỗi 30 phút — giá trị là string float để Selection lưu được
_HOUR_SLOTS = [
    ('9.0',  '09:00'), ('9.5',  '09:30'),
    ('10.0', '10:00'), ('10.5', '10:30'),
    ('11.0', '11:00'), ('11.5', '11:30'),
    ('12.0', '12:00'), ('12.5', '12:30'),
    ('13.0', '13:00'), ('13.5', '13:30'),
    ('14.0', '14:00'), ('14.5', '14:30'),
    ('15.0', '15:00'), ('15.5', '15:30'),
    ('16.0', '16:00'), ('16.5', '16:30'),
    ('17.0', '17:00'),
]


class HbInterviewSlot(models.Model):
    """Slot rảnh phỏng vấn — do TBP khai báo, BP tuyển dụng dùng để lên lịch."""
    _name = 'hb.interview.slot'
    _description = 'Lịch rảnh phỏng vấn'
    _order = 'start_datetime'

    name = fields.Char(compute='_compute_name', store=True)
    start_datetime = fields.Datetime(string='Bắt đầu', required=True)
    stop_datetime = fields.Datetime(string='Kết thúc', required=True)
    user_id = fields.Many2one(
        'res.users', string='Người phỏng vấn',
        required=True, default=lambda self: self.env.user,
    )
    department_id = fields.Many2one(
        'hr.department', string='Phòng ban',
        compute='_compute_department', store=True,
    )
    # Một slot có thể phỏng vấn NHIỀU ứng viên cùng khung giờ (PV nhóm, hoặc
    # hội đồng gọi lần lượt trong 1 tiếng) ⇒ many2many chứ không phải 1 ứng viên.
    applicant_ids = fields.Many2many(
        'hr.applicant', 'hb_interview_slot_applicant_rel', 'slot_id', 'applicant_id',
        string='Ứng viên',
    )
    applicant_count = fields.Integer(
        string='Số ứng viên', compute='_compute_applicant_count', store=True,
    )
    # Trạng thái suy ra từ danh sách ứng viên — tránh 2 nguồn sự thật lệch nhau
    # khi ai đó sửa ứng viên thẳng trên form backend.
    state = fields.Selection([
        ('available', 'Còn trống'),
        ('booked',    'Đã đặt'),
    ], string='Trạng thái', compute='_compute_state', store=True, readonly=True)
    notes = fields.Text(string='Ghi chú')

    @api.depends('applicant_ids')
    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_count = len(rec.applicant_ids)

    @api.depends('applicant_ids')
    def _compute_state(self):
        for rec in self:
            rec.state = 'booked' if rec.applicant_ids else 'available'

    @api.depends('user_id', 'start_datetime')
    def _compute_name(self):
        for rec in self:
            if rec.user_id and rec.start_datetime:
                local_dt = fields.Datetime.context_timestamp(rec, rec.start_datetime)
                rec.name = f"{rec.user_id.name} — {local_dt.strftime('%d/%m %H:%M')}"
            else:
                rec.name = 'Slot mới'

    @api.depends('user_id')
    def _compute_department(self):
        Employee = self.env['hr.employee']
        for rec in self:
            emp = Employee.search([('user_id', '=', rec.user_id.id)], limit=1)
            rec.department_id = emp.department_id if emp else False

    @api.constrains('start_datetime', 'stop_datetime')
    def _check_datetime_order(self):
        for rec in self:
            if rec.stop_datetime <= rec.start_datetime:
                raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu.')

    def action_mark_available(self):
        """Trả slot về Còn trống = gỡ hết ứng viên (state tự tính lại)."""
        self.write({'applicant_ids': [(5, 0, 0)]})


class HbInterviewSlotWizard(models.TransientModel):
    """Wizard để TBP khai báo nhiều slot rảnh trong một lần."""
    _name = 'hb.interview.slot.wizard'
    _description = 'Khai báo lịch rảnh phỏng vấn'

    user_id = fields.Many2one(
        'res.users', string='Người phỏng vấn',
        required=True, default=lambda self: self.env.user,
    )
    line_ids = fields.One2many(
        'hb.interview.slot.wizard.line', 'wizard_id',
        string='Các slot rảnh',
    )

    def _to_utc(self, day, hour_str, tz):
        h = float(hour_str)
        local_dt = tz.localize(datetime.combine(day, dt_time(int(h), int(round((h % 1) * 60)))))
        return local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    def action_create_slots(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError('Vui lòng thêm ít nhất một slot rảnh.')
        tz = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        SlotModel = self.env['hb.interview.slot']
        for line in self.line_ids:
            SlotModel.create({
                'start_datetime': self._to_utc(line.date, line.start_hour, tz),
                'stop_datetime': self._to_utc(line.date, line.end_hour, tz),
                'user_id': self.user_id.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lịch rảnh phỏng vấn',
            'res_model': 'hb.interview.slot',
            'view_mode': 'calendar,list,form',
            'target': 'current',
            'context': {'search_default_filter_available': 1},
        }


class HbInterviewSlotWizardLine(models.TransientModel):
    _name = 'hb.interview.slot.wizard.line'
    _description = 'Dòng khai báo slot rảnh'
    _order = 'date, start_hour'

    wizard_id = fields.Many2one(
        'hb.interview.slot.wizard', required=True, ondelete='cascade',
    )
    date = fields.Date(string='Ngày', required=True)
    start_hour = fields.Selection(
        selection=_HOUR_SLOTS[:-1],
        string='Bắt đầu', required=True,
    )
    end_hour = fields.Selection(
        selection=_HOUR_SLOTS[1:],
        string='Kết thúc', required=True,
    )
