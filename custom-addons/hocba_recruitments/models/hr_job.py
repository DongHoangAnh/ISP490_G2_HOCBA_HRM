from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Gợi ý trình độ cho ô "Trình độ" của vị trí tuyển dụng. Đây chỉ là DANH SÁCH
# GỢI Ý (field là Char, không phải Selection) — trung tâm gặp chứng chỉ lạ thì
# gõ thẳng, không phải chờ sửa code. Gồm đủ các cấp đang lưu hành trên thị
# trường: HSK 2.0 (1–6), HSK 3.0 cấp cao (7–9), HSKK khẩu ngữ và TOCFL.
HB_TEACHING_LEVELS = [
    'HSK1', 'HSK2', 'HSK3', 'HSK4', 'HSK5', 'HSK6',
    'HSK7', 'HSK8', 'HSK9', 'HSK7-9',
    'HSKK Sơ cấp', 'HSKK Trung cấp', 'HSKK Cao cấp',
    'TOCFL Band A', 'TOCFL Band B', 'TOCFL Band C', 'TOCFL',
]


class HrJobHocBaExt(models.Model):
    _inherit = 'hr.job'

    x_published = fields.Boolean(
        string='Đăng tuyển',
        default=False,
        tracking=True,
        help='Đánh dấu vị trí đang được đăng tuyển. Hiển thị badge PUBLISHED xanh trên Kanban.',
    )
    recruitment_status = fields.Selection(
        selection=[
            ('recruiting', 'Đang tuyển'),
            ('stopped', 'Dừng tuyển'),
        ],
        string='Trạng thái tuyển',
        default='recruiting',
        tracking=True,
    )
    jd_google_link = fields.Char(
        string='Link JD',
        help='Google Docs / Drive link chứa Job Description.',
    )
    # TUỲ CHỌN, không có ràng buộc bắt buộc — xem ghi chú "Vì sao bỏ ràng buộc
    # trình độ" ở cuối file trước khi định thêm lại @api.constrains vào đây.
    x_teaching_level = fields.Char(
        string='Trình độ',
        help='Yêu cầu trình độ tiếng Trung của vị trí (nếu có). Chọn trong '
             'danh sách gợi ý hoặc gõ trình độ khác. Để trống = không yêu cầu.',
    )
    x_required_sessions_per_week = fields.Integer(
        string='Số buổi/tuần tối thiểu',
        default=0,
    )

    def action_toggle_published(self):
        for rec in self:
            rec.x_published = not rec.x_published

    def _hb_resume_recruiting(self):
        """Mở lại Đang tuyển. Trả về các vị trí THỰC SỰ đổi (idempotent).

        KHÔNG bật cờ đăng tin: đăng tuyển là quyết định của HR ở tab Theo dõi
        tuyển dụng, cùng luật với `action_approve` của phiếu yêu cầu. Ghi mỗi
        `recruitment_status` nên `write()` bên dưới không soi gương publish.
        """
        changed = self.browse()
        for job in self:
            if job.recruitment_status == 'recruiting':
                continue
            job.sudo().write({'recruitment_status': 'recruiting'})
            changed |= job
        return changed

    def _hb_stop_recruiting(self):
        """Hạ vị trí về Dừng tuyển + gỡ tin đăng. Trả về các vị trí THỰC SỰ đổi.

        Một chỗ duy nhất cho "ngừng tuyển", vì có 2 đường gọi tới:
        tuyển đủ chỉ tiêu (hr_applicant._hb_auto_close_if_filled) và đóng phiếu
        cuối cùng của vị trí (hb_recruitment_request.write). Idempotent — gọi
        lại trên vị trí đã dừng thì không ghi và không đổi gì, để bên gọi khỏi
        post chatter trùng.

        `is_published` là field của `website_hr_recruitment` (module không
        depends, xem tests/test_job_publish.py) nên chỉ ghi khi field tồn tại.
        """
        changed = self.browse()
        for job in self:
            vals = {}
            if job.recruitment_status != 'stopped':
                vals['recruitment_status'] = 'stopped'
            if job.x_published:
                vals['x_published'] = False
                if 'is_published' in job._fields:
                    vals['is_published'] = False
            if not vals:
                continue
            job.sudo().write(vals)
            changed |= job
        return changed

    # ── Đồng bộ publish ↔ trạng thái tuyển (mọi cửa ghi) ─────────────────────
    # Đổi cờ publish từ BẤT KỲ đâu (SPA, backend, công tắc Publish trên
    # website) → gương 2 cờ is_published/x_published với nhau và khớp
    # trạng thái: đăng → Đang tuyển, ngừng đăng → Dừng tuyển.
    # Trạng thái truyền tường minh trong cùng write vẫn được tôn trọng.
    def write(self, vals):
        pub = None
        if 'is_published' in vals:
            pub = bool(vals['is_published'])
        elif 'x_published' in vals:
            pub = bool(vals['x_published'])
        if pub is not None:
            vals = dict(vals, x_published=pub)
            if 'is_published' in self._fields:
                vals['is_published'] = pub
            vals.setdefault('recruitment_status',
                            'recruiting' if pub else 'stopped')
        return super().write(vals)

    # ── Logic 2: Kiểm tra trùng lặp tên vị trí trong cùng phòng ban ──────────
    @api.constrains('name', 'department_id', 'active')
    def _check_duplicate_position(self):
        for rec in self:
            if not rec.active:
                continue
            domain = [
                ('name', '=', rec.name),
                ('department_id', '=', rec.department_id.id),
                ('id', '!=', rec.id),
                ('active', '=', True),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    'Vị trí "%s" đã tồn tại trong phòng ban "%s". Vui lòng kiểm tra lại.' % (
                        rec.name, rec.department_id.name or '',
                    )
                )

    # ── Vì sao KHÔNG có ràng buộc "bắt buộc điền Trình độ" ───────────────────
    # Bỏ ngày 2026-08-07 sau khi đối chiếu file quy trình gốc của khách
    # ("Học bá education.xlsx", 59 sheet):
    #
    #  · Cụm 7.x (tuyển dụng) KHÔNG có cột trình độ ở bất kỳ sheet nào.
    #    "7.8 Danh sách vị trí JD" chỉ gồm 4 cột: Vị trí | Trạng thái |
    #    Số lượng | JD công việc. "7.2 Phiếu yêu cầu tuyển dụng" cũng không có.
    #  · "Trình độ tiếng Trung" chỉ tồn tại ở sheet "2.1 Quản lý nhân sự"
    #    (HỒ SƠ NHÂN VIÊN, không phải vị trí tuyển dụng) và 165/168 nhân sự
    #    để trống; trong 29 người làm nghề dạy/đào tạo chỉ 2 người có điền,
    #    còn người duy nhất mang chức danh "Giáo viên" thì bỏ trống.
    #  · Mọi chỗ HSK còn lại trong file là trình độ của HỌC VIÊN (test đầu vào,
    #    học thử, kịch bản bán hàng), không liên quan tuyển dụng.
    #
    # ⇒ Bắt buộc trường này là tự nhóm nghĩ ra, và nó chặn HR lưu vị trí vì một
    # dữ liệu mà chính khách không thu thập. Ràng buộc cũ còn so TÊN phòng ban
    # ('Giảng viên'/'Trợ giảng') — hai phòng không tồn tại trong 6 phòng chuẩn,
    # nên nó chưa từng chạy trên dữ liệu thật (QA 2026-08-07, vấn đề #1).
    # Muốn theo dõi trình độ tiếng Trung thì chỗ đúng là hồ sơ nhân viên
    # (hocba_employees), và nên hỏi khách trước vì dữ liệu gần như trống.
