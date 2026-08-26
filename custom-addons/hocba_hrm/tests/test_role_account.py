"""Tài khoản vai trò trưởng phòng — không phải hồ sơ nhân sự.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Tài khoản tạo từ form "Thêm phòng ban" là tài khoản QUẢN LÝ (tài khoản thứ hai
của một người đã có hồ sơ nhân viên riêng). Nó phải biến mất khỏi Nhận việc,
danh sách Nhân viên và thống kê, nhưng VẪN giữ nguyên quyền duyệt phòng mình và
VẪN hiện ở màn Tài khoản để HR đổi mật khẩu / khoá.

DB test dùng chung nên mọi assert so theo bản ghi do test tự tạo, không so số
tuyệt đối.
"""
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _dept_create, _dept_update, _emp_scope_domain, _account_list)


@tagged('post_install', '-at_install')
class TestRoleAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        gu = self.env.ref('base.group_user').id
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Role', 'login': 'hrm_role_acc',
            'group_ids': [(6, 0, [gu,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def _mgr_block(self, login='tp_role_1', name='TP Vai Tro'):
        return {'name': name, 'login': login,
                'password': 'Hocba@2026', 'password_confirm': 'Hocba@2026'}

    def _create_dept(self, name='Phong Vai Tro', login='tp_role_1'):
        """Tạo phòng ban kèm tài khoản vai trò, trả về (dept, emp).

        Lấy dept qua id trả về từ _dept_create, KHÔNG search theo tên — DB
        hocba_hrm dùng chung, một phòng trùng tên còn sót lại (seed thủ công,
        lần chạy trước crash không rollback) sẽ khiến search(limit=1) không
        order bắt nhầm phòng cũ."""
        env = self.env(user=self.hrm)
        out = _dept_create(env, {'name': name,
                                  'manager': self._mgr_block(login=login)})
        dept = env['hr.department'].sudo().browse(out['id'])
        return dept, dept.manager_id

    # ---- Task 1: cờ trên model ----
    def test_create_khong_ghi_moc_nhan_viec(self):
        """Tài khoản vai trò không sinh mốc thăng tiến 'join'."""
        emp = self.env['hr.employee'].create({
            'name': 'Chi La Tai Khoan', 'x_is_role_account': True})
        self.assertTrue(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertFalse(
            logs, 'Tài khoản vai trò không được có mốc "Nhận việc".')

    def test_nv_thuong_van_ghi_moc_nhan_viec(self):
        """Không làm hỏng đường đi của nhân viên thật."""
        emp = self.env['hr.employee'].create({'name': 'NV That Su'})
        self.assertFalse(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertTrue(logs, 'NV thật vẫn phải có mốc "Nhận việc".')

    # ---- Task 1 (code review): chặn onboarding trong _hocba_maybe_assign_onboarding ----
    def _ensure_matching_onboarding_template(self, position_type='staff',
                                              work_form='offline'):
        """Bảo đảm có ít nhất 1 template khớp (position_type, work_form).

        DB test dùng chung nên có thể đã có sẵn (vd onb_template_office từ
        data seed) — chỉ tạo thêm khi thực sự chưa có gì khớp, tránh vọc
        thêm dữ liệu ngoài phạm vi cần cho test này."""
        Template = self.env['hb.onboarding.template'].sudo()
        probe = self.env['hr.employee'].new({
            'x_position_type': position_type, 'x_work_form': work_form})
        if Template._match_for_employee(probe):
            return
        Template.create({
            'name': 'Test tpl %s/%s' % (position_type, work_form),
            'sequence': 1,
            'apply_position_types': position_type,
            'apply_work_form': work_form,
            'step_ids': [(0, 0, {'name': 'Buoc test', 'step_type': 'task'})],
        })

    def test_tai_khoan_vai_tro_khong_gan_onboarding(self):
        """Tài khoản vai trò thử việc + có ngày bắt đầu vẫn KHÔNG được gán
        quy trình nhận việc — đối chứng: NV thật cùng dữ liệu thì CÓ.

        Chốt điều kiện trong _hocba_maybe_assign_onboarding() thay vì chỉ
        lọc ở create(): cách này còn bảo vệ được write() và
        _hocba_migrate_legacy_gates() — cùng một chỗ, không lặp lại điều
        kiện ở nhiều nơi."""
        self._ensure_matching_onboarding_template()
        today = fields.Date.context_today(self.env['hr.employee'])
        role_emp = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Onb', 'x_is_role_account': True,
            'x_position_type': 'staff', 'x_work_form': 'offline',
            'x_probation_start': today})
        real_emp = self.env['hr.employee'].create({
            'name': 'NV That Onb', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'x_probation_start': today})
        self.assertFalse(
            role_emp.x_onboarding_step_ids,
            'Tài khoản vai trò không được gán quy trình nhận việc.')
        self.assertTrue(
            real_emp.x_onboarding_step_ids,
            'NV thật cùng dữ liệu phải được gán quy trình nhận việc '
            '(nếu assert này fail, kiểm tra template khớp trong DB test).')

    def test_batch_create_hon_hop_chi_nv_that_co_moc_join(self):
        """create() một lần với recordset hỗn hợp (vai trò + NV thật) —
        filtered() trong create() phải tách đúng từng bản ghi, không lẫn
        theo vị trí trong vals_list."""
        employees = self.env['hr.employee'].create([
            {'name': 'TK Vai Tro Batch', 'x_is_role_account': True},
            {'name': 'NV That Batch'},
        ])
        role_emp, real_emp = employees[0], employees[1]
        Promotion = self.env['hr.promotion.history'].sudo()
        self.assertFalse(
            Promotion.search([('employee_id', '=', role_emp.id)]),
            'Bản ghi vai trò trong batch không được có mốc "Nhận việc".')
        self.assertTrue(
            Promotion.search([('employee_id', '=', real_emp.id)]),
            'Bản ghi NV thật trong cùng batch vẫn phải có mốc "Nhận việc".')

    # ---- Task 1 (code review): không cấp mã nhân sự cho tài khoản vai trò ----
    def test_tai_khoan_vai_tro_khong_cap_ma_nhan_su(self):
        """Không ngốn số dãy HB.xx của HR. Tạo HAI tài khoản vai trò để
        chứng minh ràng buộc unique(x_employee_code) chấp nhận nhiều bản ghi
        cùng để trống (Postgres: NULL không so bằng NULL) — không suy luận
        suông, để Odoo tự flush và raise nếu sai."""
        role_emp_1 = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Ma 1', 'x_is_role_account': True})
        role_emp_2 = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Ma 2', 'x_is_role_account': True})
        real_emp = self.env['hr.employee'].create({'name': 'NV That Ma'})
        self.assertFalse(
            role_emp_1.x_employee_code,
            'Tài khoản vai trò không được cấp mã nhân sự.')
        self.assertFalse(
            role_emp_2.x_employee_code,
            'Tài khoản vai trò không được cấp mã nhân sự.')
        self.assertTrue(
            real_emp.x_employee_code, 'NV thật vẫn phải có mã nhân sự.')

    # ---- Task 2: form phòng ban bật cờ ----
    def test_tao_phong_ban_sinh_tai_khoan_vai_tro(self):
        """Trưởng phòng tạo cùng lúc với phòng ban mới phải là tài khoản
        vai trò, không phải hồ sơ nhân sự."""
        dept, emp = self._create_dept(login='tp_role_2')
        self.assertTrue(emp, 'Phòng ban mới phải có trưởng phòng.')
        self.assertTrue(
            emp.x_is_role_account,
            'Trưởng phòng tạo từ form phòng ban phải là tài khoản vai trò.')

    def test_tai_khoan_vai_tro_khong_o_trang_thai_thu_viec(self):
        """Tài khoản vai trò không đi làm nên không có tình trạng làm việc —
        đối chứng bằng NV thật để chốt cứng default 'probation' của field
        vẫn còn nguyên (không thì test này xanh giả, kể cả khi ai đó lỡ đổi
        default field sang False và làm vỡ cả hệ)."""
        _dept, emp = self._create_dept(name='Phong KTT', login='tp_role_3')
        self.assertFalse(
            emp.x_employment_status,
            'Tài khoản vai trò không có tình trạng làm việc — nó không đi làm.')
        that = self.env['hr.employee'].sudo().create({'name': 'NV That KTT'})
        self.assertEqual(that.x_employment_status, 'probation',
                          'NV thật vẫn phải mặc định Thử việc.')

    def test_dept_update_doi_truong_phong_bang_tai_khoan_moi_cung_bat_co(self):
        """Nhánh Sửa phòng ban: HR đổi trưởng phòng bằng cách tạo TÀI KHOẢN
        MỚI ngay trong form Sửa (body['manager']) — đi qua cùng
        _dept_new_manager như form Tạo, nên cũng phải bật cờ. Khóa nhánh này
        lại bằng test riêng, đừng chỉ dựa vào chỗ nó dùng chung helper."""
        dept, emp1 = self._create_dept(name='Phong Sua TP', login='tp_role_4')
        out = _dept_update(self.env(user=self.hrm), dept.id, {
            'name': dept.name,
            'manager': self._mgr_block(login='tp_role_5', name='TP Moi')})
        self.assertNotEqual(out['managerId'], emp1.id,
                             'Trưởng phòng phải đổi sang người mới.')
        new_mgr = self.env['hr.employee'].sudo().browse(out['managerId'])
        self.assertTrue(
            new_mgr.x_is_role_account,
            'Trưởng phòng mới tạo từ form Sửa phòng ban cũng phải là '
            'tài khoản vai trò.')

    # ---- Task 3: biến mất khỏi các màn nhân sự ----
    def test_khong_nam_trong_danh_sach_nhan_vien(self):
        _dept, emp = self._create_dept(name='Phong DS', login='tp_role_4')
        env = self.env(user=self.hrm)
        found = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertNotIn(
            emp, found, 'Tài khoản vai trò không được nằm trong danh sách NV.')

    def test_khong_nam_trong_hang_doi_nhan_viec(self):
        """api_onboarding lọc probation + _emp_scope_domain.

        Cố tình ghi lại x_employment_status='probation' lên tài khoản vai trò
        trước khi kiểm. Không ghi thì test này XANH GIẢ: Task 2 đã đặt trạng
        thái rỗng nên bản ghi rơi khỏi vế ('x_employment_status','=',
        'probation') chứ không phải nhờ bộ lọc của Task 3. Trạng thái
        'probation' bám lại là chuyện có thật — bản ghi cũ trước migration
        (vd NV #33107 trong DB local) và đường ghi ngược từ form Sửa nhân
        viên của FE đều để lại đúng giá trị này. Hai lớp chặn độc lập.
        """
        _dept, emp = self._create_dept(name='Phong NV', login='tp_role_5')
        emp.sudo().write({'x_employment_status': 'probation'})
        env = self.env(user=self.hrm)
        queue = env['hr.employee'].sudo().search(
            [('x_employment_status', '=', 'probation')]
            + _emp_scope_domain(env))
        self.assertNotIn(
            emp, queue, 'Tài khoản vai trò không được vào hàng đợi Nhận việc.')

    def test_nv_that_van_nam_trong_danh_sach(self):
        """Bộ lọc không được vơ đũa cả nắm."""
        env = self.env(user=self.hrm)
        that = env['hr.employee'].sudo().create({'name': 'NV That Trong DS'})
        found = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertIn(that, found)

    def test_tai_khoan_vai_tro_van_duyet_duoc_phong_minh(self):
        """Quyền đến từ _managed_department_ids (search trên hr.department),
        không từ việc bản thân nằm trong danh sách NV."""
        dept, emp = self._create_dept(name='Phong Quyen', login='tp_role_6')
        nv = self.env['hr.employee'].sudo().create({
            'name': 'NV Duoi Quyen', 'department_id': dept.id})
        env = self.env(user=emp.user_id)
        thay_duoc = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertIn(
            nv, thay_duoc,
            'Tài khoản vai trò phải vẫn thấy NV phòng mình.')
