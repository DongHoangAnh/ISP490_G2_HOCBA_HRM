# ============================================================
# Nền chung cho test module Dịch vụ Nhân sự (SPEC SVC §9).
# Owner: Nhật Anh.
#
# Nguyên tắc: setUp TỰ TẠO phòng ban + NV + set tường minh 2 ir.config_parameter.
# DB test thật có phòng < 5 NV (§2.2) nên test nào đọc ngưỡng từ DB sẽ xanh/đỏ
# ngẫu nhiên theo môi trường (local vs Neon).
# ============================================================
from odoo.tests.common import TransactionCase

from odoo.addons.hocba_service.models.hocba_hr_request import (
    PARAM_ANON_DAILY, PARAM_MIN_ANON_DEPT,
)


class ServiceCase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Request = self.env['hocba.hr.request']
        self.Sender = self.env['hocba.hr.request.sender']
        self.Param = self.env['ir.config_parameter'].sudo()

        # Ngưỡng cố định, không phụ thuộc dữ liệu DB.
        self.Param.set_param(PARAM_MIN_ANON_DEPT, '5')
        self.Param.set_param(PARAM_ANON_DAILY, '3')

        Dept = self.env['hr.department']
        # dept_big: đủ ≥5 NV → cho gửi ẩn danh tới trưởng phòng.
        self.dept_big = Dept.create({'name': 'Khối Lớn (svc)'})
        # dept_small: 3 NV → phải bị chặn ẩn danh (BR-SVC-03).
        self.dept_small = Dept.create({'name': 'Khối Nhỏ (svc)'})
        self.dept_other = Dept.create({'name': 'Khối Khác (svc)'})

        cccd = self._cccd_gen()
        self.emp_mgr_big = self._mk_emp('TP Lớn svc', next(cccd), self.dept_big)
        self.emp_sender = self._mk_emp('NV Gửi svc', next(cccd), self.dept_big)
        self.emp_big_3 = self._mk_emp('NV Lớn3 svc', next(cccd), self.dept_big)
        self.emp_big_4 = self._mk_emp('NV Lớn4 svc', next(cccd), self.dept_big)
        self.emp_big_5 = self._mk_emp('NV Lớn5 svc', next(cccd), self.dept_big)
        self.emp_big_6 = self._mk_emp('NV Lớn6 svc', next(cccd), self.dept_big)

        self.emp_mgr_small = self._mk_emp('TP Nhỏ svc', next(cccd), self.dept_small)
        self.emp_small_2 = self._mk_emp('NV Nhỏ2 svc', next(cccd), self.dept_small)
        self.emp_small_3 = self._mk_emp('NV Nhỏ3 svc', next(cccd), self.dept_small)

        self.emp_mgr_other = self._mk_emp('TP Khác svc', next(cccd), self.dept_other)

        self.dept_big.manager_id = self.emp_mgr_big.id
        self.dept_small.manager_id = self.emp_mgr_small.id
        self.dept_other.manager_id = self.emp_mgr_other.id

        # --- Tài khoản ---
        self.user_sender = self._mk_user('svc_sender', self.emp_sender)
        self.user_mgr_big = self._mk_user('svc_mgr_big', self.emp_mgr_big)
        self.user_mgr_other = self._mk_user('svc_mgr_other', self.emp_mgr_other)
        self.user_small = self._mk_user('svc_small', self.emp_small_2)
        self.user_mgr_small = self._mk_user('svc_mgr_small', self.emp_mgr_small)
        self.user_hr = self._mk_user(
            'svc_hr', groups=['hr.group_hr_user'])
        self.user_hr_mgr = self._mk_user(
            'svc_hr_mgr', groups=['hr.group_hr_manager'])

        # --- Loại yêu cầu (seed) ---
        ref = self.env.ref
        self.type_confirm_work = ref('hocba_service.type_confirm_work')
        self.type_feedback = ref('hocba_service.type_feedback')
        self.type_complaint = ref('hocba_service.type_complaint_mgr')
        self.type_proposal = ref('hocba_service.type_work_proposal')

    # ----------------------------------------------------------- helpers

    def _cccd_gen(self):
        """CCCD 12 số, mỗi NV một giá trị — BR-010 bắt buộc với NV chính thức."""
        n = 130000000000
        while True:
            n += 1
            yield str(n)

    def _mk_emp(self, name, cccd, dept):
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10]})

    def _mk_user(self, login, employee=None, groups=None):
        group_ids = [self.env.ref('base.group_user').id]
        for xmlid in (groups or []):
            group_ids.append(self.env.ref(xmlid).id)
        user = self.env['res.users'].create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, group_ids)]})
        if employee:
            employee.user_id = user.id
        return user

    def _send(self, user, **vals):
        """Gửi đơn với tư cách `user`."""
        vals.setdefault('subject', 'Tiêu đề test')
        vals.setdefault('body', 'Nội dung test')
        return self.Request.with_user(user).create_request(vals)

    def _send_feedback_anon(self, user=None, **vals):
        vals.setdefault('type_id', self.type_feedback.id)
        vals.setdefault('is_anonymous', True)
        vals.setdefault('recipient_scope', 'hr')
        return self._send(user or self.user_sender, **vals)
