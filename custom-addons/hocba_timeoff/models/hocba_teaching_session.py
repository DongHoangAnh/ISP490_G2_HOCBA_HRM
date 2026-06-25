# ============================================================
# Lịch dạy của giáo viên — NGUỒN CHÍNH trong Neon (không phải cache tạm).
#
# CMS MySQL chỉ dùng để IMPORT 1 LẦN làm dữ liệu mẫu (`_import_from_cms`).
# Sau import, luồng nghỉ phép KHÔNG đọc CMS nữa: dò xung đột, hủy buổi (cả lớp
# nghỉ) và đổi giáo viên dạy thay đều thực hiện & ghi thẳng vào model này.
# Khi gộp 2 dự án về 1 DB chung, đây trở thành bảng lịch dạy dùng chung.
# Owner: Nhật Anh. Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict.
# ============================================================
import logging
from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HocbaTeachingSession(models.Model):
    _name = 'hocba.teaching.session'
    _description = 'Buổi dạy của giáo viên (lịch dạy)'
    _order = 'session_date, start_time, id'

    cms_session_id = fields.Char(
        string='Mã buổi (CMS)', required=True, index=True, copy=False,
        help='Khóa buổi dạy lấy từ CMS — giữ để map khi gộp DB chung.',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Giáo viên phụ trách',
        required=True, index=True, ondelete='cascade',
        help='GV đang phụ trách buổi (bị đổi khi có dạy thay).',
    )
    original_employee_id = fields.Many2one(
        'hr.employee', string='Giáo viên gốc', ondelete='set null',
        help='GV gốc — dùng để revert khi hủy đơn nghỉ đã duyệt.',
    )
    class_id = fields.Char(string='Mã lớp')
    class_name = fields.Char(string='Tên lớp')
    session_date = fields.Date(string='Ngày dạy', required=True, index=True)
    start_time = fields.Char(string='Giờ bắt đầu', help='Định dạng HH:MM')
    end_time = fields.Char(string='Giờ kết thúc', help='Định dạng HH:MM')
    state = fields.Selection(
        [('planned', 'Theo kế hoạch'),
         ('substituted', 'Đã đổi GV dạy thay'),
         ('cancelled', 'Đã hủy (cả lớp nghỉ)')],
        string='Trạng thái', default='planned', required=True, index=True,
    )
    source_leave_id = fields.Many2one(
        'hr.leave', string='Đơn nghỉ liên quan', ondelete='set null', copy=False,
        help='Đơn nghỉ đã gây ra việc đổi GV / hủy buổi này.',
    )

    _cms_session_uniq = models.Constraint(
        'unique (cms_session_id)',
        'Mỗi buổi dạy (cms_session_id) chỉ được lưu một bản ghi.',
    )

    @api.depends('class_name', 'session_date', 'start_time', 'end_time')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.class_name or rec.cms_session_id or '?']
            if rec.session_date:
                parts.append(rec.session_date.strftime('%d/%m/%Y'))
            if rec.start_time:
                parts.append('%s-%s' % (rec.start_time, rec.end_time or ''))
            rec.display_name = ' — '.join(parts)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('original_employee_id') and vals.get('employee_id'):
                vals['original_employee_id'] = vals['employee_id']
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Import dữ liệu mẫu từ CMS (read-only) — CHẠY MỘT LẦN.
    # ------------------------------------------------------------------
    @api.model
    def _import_from_cms(self, date_from, date_to):
        """Import buổi dạy từ CMS MySQL vào Neon (upsert theo cms_session_id).

        Đọc read-only qua hocba_attendance.cms_connector; map tutor (CMS) →
        hr.employee qua x_cms_user_id. Idempotent: chạy lại không nhân đôi.
        Trả về recordset các buổi đã tạo/cập nhật.
        """
        # Import động: tránh phụ thuộc cứng khi load registry; cũng giúp test
        # patch hàm tại nguồn (odoo.addons.hocba_attendance.utils.cms_connector).
        from odoo.addons.hocba_attendance.utils import cms_connector

        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        teachers = self.env['hr.employee'].sudo().search(
            [('x_cms_user_id', '!=', False)])

        touched = self.browse()
        for emp in teachers:
            day = date_from
            while day <= date_to:
                for raw in cms_connector.get_sessions_for_tutor(
                        emp.x_cms_user_id, day):
                    sd = cms_connector.session_to_dict(raw)
                    touched |= self._upsert_session(emp, sd)
                day += timedelta(days=1)
        _logger.info('Import lịch dạy CMS: %s buổi (từ %s đến %s).',
                     len(touched), date_from, date_to)
        return touched

    def _upsert_session(self, emp, sd):
        """Tạo mới hoặc cập nhật 1 buổi theo cms_session_id.

        Bản ghi đã tồn tại: chỉ cập nhật thông tin mô tả (lớp/ngày/giờ), GIỮ
        nguyên employee_id/state/original (bảo toàn nếu đã đổi GV/hủy)."""
        cms_id = str(sd['id'])
        desc_vals = {
            'class_id': str(sd.get('classId') or ''),
            'class_name': sd.get('className') or '',
            'session_date': sd['date'],
            'start_time': sd.get('startTime') or '',
            'end_time': sd.get('endTime') or '',
        }
        existing = self.search([('cms_session_id', '=', cms_id)], limit=1)
        if existing:
            existing.write(desc_vals)
            return existing
        return self.create(dict(
            desc_vals,
            cms_session_id=cms_id,
            employee_id=emp.id,
            original_employee_id=emp.id,
        ))
