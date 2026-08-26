import { patch } from "@web/core/utils/patch";
import { HrRecruitmentForm } from "@website_hr_recruitment/interactions/hr_recruitment_form";

/**
 * Bắt buộc nộp CV ở form ứng tuyển.
 *
 * Odoo mặc định cho phép "CV HOẶC hồ sơ LinkedIn": interaction gốc chỉ bật
 * `required` cho ô CV (#recruitment6) khi CẢ HAI đều trống, và bật ở lượt render
 * sau cú click — tức cú click đầu tiên vẫn lọt qua và đơn được gửi không CV.
 *
 * Học Bá đã bỏ hẳn ô LinkedIn (xem views/recruitment_branding_templates.xml),
 * nên ép `isIncomplete` luôn bằng True: ô CV `required` ngay từ lúc tải trang,
 * trình duyệt chặn gửi và hiện thông báo ngay trên ô CV.
 *
 * Đặt `required` thẳng trong XML thì vô tác dụng — interaction gắn
 * `t-att-required` nên nó ghi đè attribute ở mỗi lần render.
 */
patch(HrRecruitmentForm.prototype, {
    setup() {
        super.setup();
        this.isIncomplete = true;
    },

    onApplyButtonClick() {
        super.onApplyButtonClick();
        this.isIncomplete = true;
    },
});
