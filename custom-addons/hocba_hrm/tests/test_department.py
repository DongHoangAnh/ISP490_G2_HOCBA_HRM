from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.addons.hocba_hrm.controllers.main import (
    _dept_payload, _dept_list, _dept_create, _dept_update, _dept_archive,
    _cap_edit_dept, _emp_in_scope)


@tagged('post_install', '-at_install')
class TestDepartment(TransactionCase):

    def setUp(self):
        super().setUp()
        # HR officer: CHỈ được xem phòng ban (chốt 2026-08-15 — xem _cap_edit_dept).
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        # HR Manager: được thêm/sửa/lưu trữ.
        self.hrm = self.env['res.users'].create({
            'name': 'HR Manager', 'login': 'hrm_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        # Admin "thuần" — base.group_system, KHÔNG kèm nhóm HR nào. Tài khoản
        # test_admin@hocba.vn trong DB thật đúng dạng này.
        self.admin = self.env['res.users'].create({
            'name': 'Admin', 'login': 'admin_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('base.group_system').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV A', 'department_id': self.dept.id})
        # NV đã có tài khoản → hợp lệ để gán làm trưởng phòng (_dept_update).
        self.emp_user = self.env['hr.employee'].create({
            'name': 'NV Có TK', 'department_id': self.dept.id,
            'user_id': self.env['res.users'].create({
                'name': 'NV Có TK', 'login': 'nv_co_tk',
                'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
            }).id})

    def _env(self, user):
        return self.env(user=user)

    def _mgr_block(self, login='tp_moi', name='TP Mới'):
        """Khối 'manager' bắt buộc khi tạo phòng ban (trưởng phòng mới)."""
        return {'name': name, 'login': login,
                'password': 'Hocba@2026', 'password_confirm': 'Hocba@2026'}

    # ---- Ràng buộc xóa (Task 1) ----
    def test_unlink_blocked_when_has_members(self):
        with self.assertRaises(UserError):
            self.dept.unlink()

    def test_unlink_blocked_when_has_children(self):
        parent = self.env['hr.department'].create({'name': 'Cha'})
        self.env['hr.department'].create({'name': 'Con', 'parent_id': parent.id})
        with self.assertRaises(UserError):
            parent.unlink()

    def test_unlink_ok_when_empty(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        empty.unlink()
        self.assertFalse(empty.exists())

    # ---- _dept_list / _dept_payload (Task 2) ----
    def test_list_forbidden_for_plain(self):
        with self.assertRaises(AccessError):
            _dept_list(self._env(self.plain))

    def test_list_returns_departments_and_employees(self):
        out = _dept_list(self._env(self.hr))
        names = [d['name'] for d in out['departments']]
        self.assertIn('Phòng A', names)
        self.assertTrue(any(e['id'] == self.emp_user.id for e in out['employees']))

    def test_payload_employee_count(self):
        out = _dept_list(self._env(self.hr))
        row = next(d for d in out['departments'] if d['id'] == self.dept.id)
        self.assertEqual(row['employeeCount'], 2)
        self.assertTrue(row['active'])

    def test_list_excludes_archived_by_default(self):
        self.dept.active = False
        names = [d['name'] for d in _dept_list(self._env(self.hr))['departments']]
        self.assertNotIn('Phòng A', names)

    def test_list_includes_archived_when_requested(self):
        self.dept.active = False
        names = [d['name'] for d in
                 _dept_list(self._env(self.hr), archived=True)['departments']]
        self.assertIn('Phòng A', names)

    # ---- Cờ canEdit: FE ẩn nút Thêm/Sửa/Lưu trữ theo cờ này ----
    def test_list_can_edit_false_for_hr_officer(self):
        self.assertFalse(_dept_list(self._env(self.hr))['canEdit'])

    def test_list_can_edit_true_for_hr_manager(self):
        self.assertTrue(_dept_list(self._env(self.hrm))['canEdit'])

    def test_list_allowed_for_admin_without_hr_group(self):
        """Admin thuần (base.group_system) phải xem được — nav vẫn bày menu
        Phòng ban cho Admin, chặn ở đây là 403 giữa mặt."""
        out = _dept_list(self._env(self.admin))
        self.assertIn('Phòng A', [d['name'] for d in out['departments']])
        self.assertTrue(out['canEdit'])

    # ---- _dept_create (Task 3) ----
    def test_create_ok(self):
        out = _dept_create(self._env(self.hrm), {
            'name': 'Phòng Mới', 'functionDesc': 'Mô tả',
            'manager': self._mgr_block()})
        self.assertEqual(out['name'], 'Phòng Mới')
        self.assertEqual(out['functionDesc'], 'Mô tả')
        self.assertEqual(out['managerName'], 'TP Mới')
        self.assertTrue(out['active'])

    def test_create_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_create(self._env(self.hrm), {'name': '   '})

    def test_create_without_manager_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_create(self._env(self.hrm), {'name': 'Phòng Thiếu TP'})

    def test_create_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_create(self._env(self.plain), {'name': 'X'})

    def test_create_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_create(self._env(self.hr), {
                'name': 'Phòng HR tạo', 'manager': self._mgr_block()})

    # ---- Quyền của TÀI KHOẢN trưởng phòng vừa được tạo kèm phòng ban ----
    # Đây là chỗ dễ vượt quyền nhất của tính năng "tạo phòng kèm trưởng phòng":
    # tài khoản sinh ra ở đây chỉ được là nhân viên thường, quyền trưởng phòng
    # đến từ manager_id chứ không từ nhóm.
    def test_new_manager_account_gets_no_hr_group(self):
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng Quyền', 'manager': self._mgr_block(login='tp_quyen')})
        u = self.env['res.users'].search([('login', '=', 'tp_quyen')], limit=1)
        self.assertTrue(u, 'phải tạo được tài khoản đăng nhập')
        self.assertTrue(u.has_group('base.group_user'))
        for g in ('hr.group_hr_user', 'hr.group_hr_manager',
                  'base.group_system', 'hocba_employees.group_hocba_giaovu'):
            self.assertFalse(u.has_group(g), 'không được cấp nhóm %s' % g)

    def test_new_manager_scope_limited_to_own_department(self):
        """Trưởng phòng mới chỉ thấy phòng mình, không thấy NV phòng khác."""
        out = _dept_create(self._env(self.hrm), {
            'name': 'Phòng Riêng', 'manager': self._mgr_block(login='tp_rieng')})
        u = self.env['res.users'].search([('login', '=', 'tp_rieng')], limit=1)
        nguoi_phong_khac = self.emp          # thuộc 'Phòng A'
        nguoi_phong_minh = self.env['hr.employee'].create({
            'name': 'NV phòng riêng', 'department_id': out['id']})
        env_tp = self._env(u)
        self.assertTrue(_emp_in_scope(env_tp, nguoi_phong_minh))
        self.assertFalse(_emp_in_scope(env_tp, nguoi_phong_khac))
        # Và không được đụng vào màn phòng ban.
        self.assertFalse(_cap_edit_dept(env_tp))
        with self.assertRaises(AccessError):
            _dept_list(env_tp)

    # ---- _dept_update (Task 4) ----
    def test_update_changes_fields(self):
        out = _dept_update(self._env(self.hrm), self.dept.id, {
            'name': 'Phòng A2', 'functionDesc': 'Mới'})
        self.assertEqual(out['name'], 'Phòng A2')
        self.assertEqual(out['functionDesc'], 'Mới')

    def test_update_clears_manager(self):
        self.dept.manager_id = self.emp_user.id
        out = _dept_update(self._env(self.hrm), self.dept.id, {
            'name': 'Phòng A', 'managerId': False})
        self.assertFalse(out['managerId'])
        self.assertFalse(self.dept.manager_id)

    def test_update_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            _dept_update(self._env(self.hrm), self.dept.id, {'name': ''})

    # ---- Người đứng đầu = tài khoản vai trò (chốt 2026-08-27) ----
    def test_update_khong_gan_duoc_nv_co_san(self):
        """Gán một hồ sơ NV THẬT làm người đứng đầu là dựng lại mô hình kiêm
        nhiệm: manager_id là nguồn quyền, nên thao tác đó âm thầm nâng quyền
        tài khoản cá nhân của họ."""
        with self.assertRaisesRegex(ValidationError, 'tài khoản vai trò riêng'):
            _dept_update(self._env(self.hrm), self.dept.id, {
                'name': 'Phòng A', 'managerId': self.emp_user.id})
        self.assertFalse(self.dept.manager_id)

    def test_update_khong_gui_managerId_thi_giu_nguyen(self):
        """Ba ý định phân biệt bằng KHÓA CÓ MẶT, không bằng giá trị: thiếu khóa
        'managerId' là 'giữ nguyên', không phải 'gỡ'. Sửa mỗi tên phòng mà mất
        luôn người đứng đầu thì là mất dữ liệu thầm lặng."""
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng Giữ', 'manager': self._mgr_block(login='tp_giu')})
        dept = self.env['hr.department'].search([('name', '=', 'Phòng Giữ')])
        head = dept.manager_id
        self.assertTrue(head)
        _dept_update(self._env(self.hrm), dept.id, {'name': 'Phòng Giữ 2'})
        self.assertEqual(dept.manager_id, head)

    def test_update_tao_nguoi_dung_dau_moi_thay_nguoi_cu(self):
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng Thay', 'manager': self._mgr_block(login='tp_cu')})
        dept = self.env['hr.department'].search([('name', '=', 'Phòng Thay')])
        cu = dept.manager_id
        _dept_update(self._env(self.hrm), dept.id, {
            'name': 'Phòng Thay',
            'manager': self._mgr_block(login='tp_thay', name='TP Thay')})
        self.assertNotEqual(dept.manager_id, cu)
        self.assertEqual(dept.manager_id.name, 'TP Thay')
        self.assertTrue(dept.manager_id.x_is_role_account)

    def test_tao_giao_vu_lam_nguoi_dung_dau(self):
        """Giáo vụ ngang hàng trưởng phòng: cũng là tài khoản vai trò, cũng
        đứng tên manager_id, khác ở chỗ được cấp thêm nhóm giáo vụ."""
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng GV',
            'manager': dict(self._mgr_block(login='gv_head', name='GV Head'),
                            role='giaovu')})
        dept = self.env['hr.department'].search([('name', '=', 'Phòng GV')])
        head = dept.manager_id
        self.assertTrue(head.x_is_role_account)
        self.assertTrue(head.user_id.has_group(
            'hocba_employees.group_hocba_giaovu'))

    def test_truong_phong_khong_duoc_nhom_giao_vu(self):
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng TP', 'manager': self._mgr_block(login='tp_khong_gv')})
        dept = self.env['hr.department'].search([('name', '=', 'Phòng TP')])
        self.assertFalse(dept.manager_id.user_id.has_group(
            'hocba_employees.group_hocba_giaovu'))

    def test_vai_tro_la_bi_tu_choi(self):
        with self.assertRaisesRegex(ValidationError, 'Vai trò'):
            _dept_create(self._env(self.hrm), {
                'name': 'Phòng Lạ',
                'manager': dict(self._mgr_block(login='vai_tro_la'),
                                role='hieu_truong')})

    def test_danh_muc_dien_nhanh_bo_tai_khoan_vai_tro(self):
        """Danh mục này nuôi ô 'điền nhanh'. Tài khoản vai trò bị loại (lấy tên
        nó để tạo tài khoản vai trò khác là vô nghĩa); NV CHƯA có tài khoản thì
        vẫn phải có mặt — người được lấy tên không cần account nào."""
        _dept_create(self._env(self.hrm), {
            'name': 'Phòng Lọc', 'manager': self._mgr_block(login='tp_loc')})
        dept = self.env['hr.department'].search([('name', '=', 'Phòng Lọc')])
        ids = [e['id'] for e in _dept_list(self._env(self.hr))['employees']]
        self.assertNotIn(dept.manager_id.id, ids)
        self.assertIn(self.emp.id, ids, 'NV chưa có tài khoản vẫn phải liệt kê')
        self.assertIn(self.emp_user.id, ids)

    def test_danh_muc_dien_nhanh_kem_email_dien_thoai(self):
        self.emp.write({'work_email': 'a@hocba.vn', 'work_phone': '0900000001'})
        row = next(e for e in _dept_list(self._env(self.hr))['employees']
                   if e['id'] == self.emp.id)
        self.assertEqual(row['email'], 'a@hocba.vn')
        self.assertEqual(row['phone'], '0900000001')

    def test_update_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_update(self._env(self.plain), self.dept.id, {'name': 'X'})

    def test_update_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_update(self._env(self.hr), self.dept.id, {'name': 'X'})

    # ---- _dept_archive (Task 5) ----
    def test_archive_sets_inactive(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        out = _dept_archive(self._env(self.hrm), empty.id, {'active': False})
        self.assertFalse(out['active'])
        self.assertFalse(empty.active)

    def test_archive_restore(self):
        self.dept.active = False
        out = _dept_archive(self._env(self.hrm), self.dept.id, {'active': True})
        self.assertTrue(out['active'])
        self.assertTrue(self.dept.active)

    def test_archive_forbidden(self):
        with self.assertRaises(AccessError):
            _dept_archive(self._env(self.plain), self.dept.id, {'active': False})

    def test_archive_forbidden_for_hr_officer(self):
        with self.assertRaises(AccessError):
            _dept_archive(self._env(self.hr), self.dept.id, {'active': False})
