import logging
import pytz
from datetime import datetime, time as dt_time

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Khung giờ khai lịch rảnh — CẤU HÌNH ĐƯỢC, mặc định 09:00–17:00 mỗi 30 phút.
# Spec: docs/superpowers/specs/2026-08-11-interview-hours-config-design.md
# Trung tâm dạy buổi tối cần khai slot sau 17:00; trước đây danh sách này là hằng
# số nên phải sửa code + upgrade module mới đổi được.
P_SLOT_OPEN = 'hocba_recruitments.slot_hour_open'
P_SLOT_CLOSE = 'hocba_recruitments.slot_hour_close'
P_SLOT_STEP = 'hocba_recruitments.slot_step_minutes'

SLOT_HOUR_OPEN_DEFAULT = 9.0
SLOT_HOUR_CLOSE_DEFAULT = 17.0
SLOT_STEP_DEFAULT = 30
SLOT_STEPS_ALLOWED = (15, 30, 60)


def _hour_label(value):
    """9.25 -> '09:15'. Làm tròn phút để 1/3 tiếng không ra 09:19.999."""
    hh = int(value)
    mm = int(round((value - hh) * 60))
    if mm == 60:            # 9.999 -> 10:00 chứ không phải 09:60
        hh, mm = hh + 1, 0
    return '%02d:%02d' % (hh, mm)


class HbInterviewSlot(models.Model):
    """Slot rảnh phỏng vấn — do TBP khai báo, BP tuyển dụng dùng để lên lịch."""
    _name = 'hb.interview.slot'
    _description = 'Lịch rảnh phỏng vấn'
    _order = 'start_datetime'

    # ── Khung giờ khai slot (cấu hình được) ─────────────────────────────────

    @api.model
    def _hb_slot_hour_config(self):
        """(open, close, step_minutes) đã làm sạch — luôn trả giá trị dùng được.

        Tham số hỏng (ai đó gõ tay vào ir.config_parameter, hoặc chuỗi rỗng do
        module data ghi đè) thì rơi về mặc định thay vì nổ lỗi giữa lúc TBP đang
        khai lịch. Cấu hình sai là việc của màn cấu hình, không phải của form.
        """
        ICP = self.env['ir.config_parameter'].sudo()

        def _f(key, fallback):
            try:
                return float(ICP.get_param(key) or fallback)
            except (TypeError, ValueError):
                return fallback

        open_h = _f(P_SLOT_OPEN, SLOT_HOUR_OPEN_DEFAULT)
        close_h = _f(P_SLOT_CLOSE, SLOT_HOUR_CLOSE_DEFAULT)
        step = int(_f(P_SLOT_STEP, SLOT_STEP_DEFAULT))
        if step not in SLOT_STEPS_ALLOWED:
            step = SLOT_STEP_DEFAULT
        if not (0 <= open_h < close_h <= 24):
            open_h, close_h = SLOT_HOUR_OPEN_DEFAULT, SLOT_HOUR_CLOSE_DEFAULT
        return open_h, close_h, step

    @api.model
    def _hb_hour_slots(self):
        """[(9.0, '09:00'), (9.5, '09:30'), …] theo cấu hình hiện hành."""
        open_h, close_h, step = self._hb_slot_hour_config()
        inc = step / 60.0
        out, cur = [], open_h
        # Cộng dồn theo chỉ số thay vì cur += inc: cộng float 121 lần thì 17.0
        # thành 16.999999 và mốc cuối biến mất khỏi danh sách.
        i = 0
        while cur <= close_h + 1e-9:
            out.append((round(cur, 4), _hour_label(cur)))
            i += 1
            cur = open_h + i * inc
        return out

    @api.model
    def _hb_hour_selection(self):
        """Selection cho wizard — string float để Odoo lưu được."""
        return [(str(v), lbl) for v, lbl in self._hb_hour_slots()]

    @api.model
    def _hb_hour_selection_start(self):
        return self._hb_hour_selection()[:-1]

    @api.model
    def _hb_hour_selection_end(self):
        return self._hb_hour_selection()[1:]

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

    # ── Tự chuyển bước theo lịch phỏng vấn ───────────────────────────────────
    # Đặt ở tầng model (không phải controller) để form backend, import và SPA
    # cùng chạy một luật. Bám xmlid bước qua _hb_advance_stage() nên admin đổi
    # tên bước trên màn Cấu hình không làm chết tự động hoá.

    def _slot_label(self):
        """'20/08 lúc 10:00' theo giờ VN — để ghi chatter.

        Fallback Asia/Ho_Chi_Minh chứ không dùng thẳng context_timestamp: cron
        chạy dưới OdooBot (tz rỗng) ⇒ ghi chú sẽ lệch 7 tiếng so với giờ hẹn mà
        HR nhìn thấy trên lịch.
        """
        self.ensure_one()
        tz = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        local_dt = pytz.utc.localize(self.start_datetime).astimezone(tz)
        return local_dt.strftime('%d/%m lúc %H:%M')

    def _hb_advance_booked(self, applicants):
        """Xếp ứng viên vào slot ⇒ Hẹn & mời phỏng vấn → Phỏng vấn.

        CHỈ đẩy từ bước "Hẹn & mời phỏng vấn". Ứng viên còn ở "Lên lịch phỏng
        vấn" mà được xếp slot thì dừng lại ở "Hẹn & mời phỏng vấn" (controller
        ghi interview_date sau khi book ⇒ luật cũ đẩy schedule → invite), vì
        khâu mời vẫn phải gửi thư cho ứng viên chứ không được nhảy cóc.
        """
        self.ensure_one()
        if applicants:
            applicants._hb_advance_stage(
                'hb_stage_invite', 'hb_stage_interview',
                'Do đã được xếp lịch phỏng vấn %s (người PV: %s).' % (
                    self._slot_label(), self.user_id.name or '—'))

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            rec._hb_advance_booked(rec.applicant_ids)
        return recs

    def write(self, vals):
        # Chỉ ứng viên MỚI được thêm mới bị đẩy bước — gỡ ứng viên (unbook) hay
        # sửa giờ slot thì không đụng tới bước của ai.
        before = {rec.id: rec.applicant_ids for rec in self} if 'applicant_ids' in vals else {}
        res = super().write(vals)
        for rec in self:
            added = rec.applicant_ids - before.get(rec.id, rec.applicant_ids.browse())
            if added:
                rec._hb_advance_booked(added)
        return res

    @api.model
    def _cron_advance_past_interviews(self):
        """CRON-REC-002: qua giờ phỏng vấn ⇒ Phỏng vấn → Kết quả phỏng vấn.

        Chạy mỗi 30 phút (bằng đúng độ dài 1 slot). Chỉ đụng ứng viên CÒN ở
        bước "Phỏng vấn": ai đã được điền kết quả và đi tiếp (Pass → Gửi Offer)
        hoặc bị HR kéo đi bước khác thì bỏ qua — _hb_advance_stage() không kéo lùi.

        Không lọc theo "Tham gia PV": ứng viên vắng mặt vẫn cần vào bước Kết quả
        để HR ghi nhận (fail / hẹn lại), chứ không phải kẹt ở bước Phỏng vấn.
        """
        st_interview = self.env.ref(
            'hocba_recruitments.hb_stage_interview', raise_if_not_found=False)
        if not st_interview:
            return 0
        now = fields.Datetime.now()
        slots = self.sudo().search([
            ('stop_datetime', '<', now),
            ('applicant_ids', '!=', False),
        ])
        moved = 0
        for slot in slots:
            todo = slot.applicant_ids.filtered(
                lambda a: a.stage_id == st_interview)
            if not todo:
                continue
            todo._hb_advance_stage(
                'hb_stage_interview', 'hb_stage_result',
                'Do đã qua khung giờ phỏng vấn %s.' % slot._slot_label())
            moved += len(todo)
        if moved:
            _logger.info('CRON-REC-002: %s ứng viên chuyển sang bước Kết quả phỏng vấn.', moved)
        return moved


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
    # Callable chứ không phải list: list bị đóng băng lúc load module, đổi cấu
    # hình phải restart Odoo mới thấy. Callable đọc lại mỗi lần dựng form.
    start_hour = fields.Selection(
        selection=lambda self: self.env['hb.interview.slot']._hb_hour_selection_start(),
        string='Bắt đầu', required=True,
    )
    end_hour = fields.Selection(
        selection=lambda self: self.env['hb.interview.slot']._hb_hour_selection_end(),
        string='Kết thúc', required=True,
    )
