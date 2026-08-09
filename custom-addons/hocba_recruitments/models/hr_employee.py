from odoo import models


class HrEmployeeRecruitmentStage(models.Model):
    """Nối kết quả thử việc bên Nhân sự về lại bước tuyển dụng.

    Ứng viên nhận việc (nút Onboard) đứng ở bước Onboarding cho tới khi hết thử
    việc. Người chốt "đạt thử việc" làm việc ở module Nhân sự chứ không mở tab
    Tuyển dụng, nên nếu không tự đẩy thì hồ sơ nằm mãi ở Onboarding và chỉ tiêu
    tuyển của vị trí không bao giờ được trừ.

    Đặt ở hocba_recruitments (đã depends hocba_employees) chứ không nhét ngược
    vào hocba_employees: tuyển dụng biết về nhân sự, chiều ngược lại thì không.
    """
    _inherit = 'hr.employee'

    def write(self, vals):
        res = super().write(vals)
        # Lên Chính thức = qua cổng đánh giá thử việc (_hocba_make_official) hoặc
        # HR Manager chốt tay — cả hai đều đi qua write nên bắt ở đây là đủ.
        if vals.get('x_employment_status') == 'official':
            self._hb_advance_applicant_to_handover()
        return res

    def _hb_advance_applicant_to_handover(self):
        """Onboarding → Bàn giao nhân sự cho ứng viên gắn với các NV này.

        Tra ngược qua hr.applicant.employee_id thay vì trường nghịch trên
        hr.employee: liên kết được đặt ở cả hai chiều lúc tạo hồ sơ (xem
        api_recruitment_create_employee) nhưng chiều applicant→employee mới là
        chiều chắc chắn có.

        active_test=False để ứng viên đã lưu trữ vẫn được đẩy bước — lưu trữ hồ
        sơ ứng viên sau khi nhận việc là chuyện bình thường.

        Bàn giao nhân sự là bước hired_stage ⇒ ứng viên vào đây sẽ trừ chỉ tiêu
        tuyển và có thể kích hoạt tự ngừng đăng tin (_hb_auto_close_if_filled) —
        đúng ý đồ, không phải tác dụng phụ ngoài ý muốn.
        """
        apps = self.env['hr.applicant'].sudo().with_context(
            active_test=False).search([('employee_id', 'in', self.ids)])
        if apps:
            apps._hb_advance_stage(
                'hb_stage_onboarding', 'hb_stage_hired',
                'Do nhân viên đã hoàn thành thử việc và lên Chính thức.')
