"""Tài khoản vai trò trưởng phòng — không phải hồ sơ nhân sự.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Tài khoản tạo từ form "Thêm phòng ban" là tài khoản QUẢN LÝ (tài khoản thứ hai
của một người đã có hồ sơ nhân viên riêng). Nó phải biến mất khỏi Nhận việc,
danh sách Nhân viên và thống kê, nhưng VẪN giữ nguyên quyền duyệt phòng mình và
VẪN hiện ở màn Tài khoản để HR đổi mật khẩu / khoá.

DB test dùng chung nên mọi assert so theo bản ghi do test tự tạo, không so số
tuyệt đối.
"""
import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import HttpCase, tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _dept_create, _dept_update, _emp_scope_domain, _account_list,
    _user_can_manage, _has_self_profile)

PWD = 'Hocba@2026'


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
                'password': PWD, 'password_confirm': PWD}

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

    def test_tai_khoan_vai_tro_van_quan_ly_duoc_phong_minh(self):
        """Chứng minh 3 điều cho tài khoản vai trò đăng nhập bằng chính nó:
        (1) vẫn thấy NV thật trong phòng mình — quyền đến từ
        _managed_department_ids (search trên hr.department), không từ việc
        bản thân nằm trong danh sách NV; (2) không thấy CHÍNH NÓ trong danh
        sách đó — _dept_new_manager gán department_id=dept.id cho tài khoản
        vai trò nên nó khớp vế ('department_id','in',dept_ids), thứ duy nhất
        loại nó ra là ROLE_ACCOUNT_EXCLUDED; (3) _user_can_manage (cổng thật
        sự mở hàng đợi duyệt, qua _is_dept_manager) không bị ăn theo domain
        danh sách NV — nó suy ra thẳng từ hr.department.manager_id."""
        dept, emp = self._create_dept(name='Phong Quyen', login='tp_role_6')
        nv = self.env['hr.employee'].sudo().create({
            'name': 'NV Duoi Quyen', 'department_id': dept.id})
        env = self.env(user=emp.user_id)
        thay_duoc = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertIn(
            nv, thay_duoc,
            'Tài khoản vai trò phải vẫn thấy NV phòng mình.')
        self.assertNotIn(emp, thay_duoc,
                         'Tài khoản vai trò không thấy chính nó trong danh sách phòng.')
        self.assertTrue(_user_can_manage(env), 'Quyền duyệt không được suy giảm.')

    def test_giao_vu_khong_thay_tai_khoan_vai_tro(self):
        """Nhánh giáo vụ của _emp_scope_domain nối thêm base (đã có
        ROLE_ACCOUNT_EXCLUDED) trước vế ('x_employee_type_id.code','=',
        'teacher') — hôm nay vế teacher đã tự loại tài khoản vai trò (nó
        không có x_employee_type_id), nên base ở nhánh này là phòng thủ
        chiều sâu. Test đối xứng: ép tài khoản vai trò MANG loại giáo viên,
        để nếu ai đó lỡ xoá ROLE_ACCOUNT_EXCLUDED khỏi base thì test này đỏ
        thay vì im lặng."""
        _dept, emp = self._create_dept(name='Phong GV', login='tp_role_7')
        teacher_type = self.env.ref('hocba_employees.employee_type_teacher')
        emp.sudo().write({'x_employee_type_id': teacher_type.id})
        gu = self.env.ref('base.group_user').id
        gv_user = self.env['res.users'].create({
            'name': 'GV Role Test', 'login': 'gv_role_test',
            'group_ids': [(6, 0, [
                gu, self.env.ref(
                    'hocba_employees.group_hocba_giaovu').id])]})
        env = self.env(user=gv_user)
        thay_duoc = env['hr.employee'].sudo().search(_emp_scope_domain(env))
        self.assertNotIn(
            emp, thay_duoc,
            'Giáo vụ không được thấy tài khoản vai trò dù nó mang loại '
            'giáo viên.')

    # ---- Task 4: màn Tài khoản cố tình KHÔNG lọc ----
    def test_van_hien_o_man_tai_khoan(self):
        """Đây là chỗ duy nhất HR đổi mật khẩu / khoá tài khoản vai trò.
        Lọc nó ở đây là biến tài khoản thành vô hình, không quản được.

        Kiểm cả 'có mặt' lẫn 'role' đúng, vì _account_list suy ra role
        bằng cách xem employee id có nằm trong manager_emp_ids (tập
        manager_id của mọi phòng ban active) hay không — nếu sau này ai
        đó lọc tài khoản vai trò ở tầng nào đó trước khi build set này
        (vd đổi search() thành có domain loại trừ), cột role trên màn
        Tài khoản sẽ âm thầm hiển thị sai thành 'employee' dù bản ghi
        vẫn còn trong danh sách — assertIn không bắt được lỗi đó."""
        _dept, emp = self._create_dept(name='Phong TK', login='tp_role_7')
        data = _account_list(self.env(user=self.hrm))
        rows = [r for r in data['accounts'] if r['employeeId'] == emp.id]
        self.assertTrue(
            rows,
            'Tài khoản vai trò phải hiện ở màn Tài khoản để HR quản lý.')
        self.assertEqual(
            rows[0]['role'], 'truongphong',
            'Tài khoản vai trò tạo từ form phòng ban phải mang role '
            "'truongphong' trên màn Tài khoản.")

    # ---- Task 5: không có "Hồ sơ của tôi" ----
    def test_dieu_kien_an_ho_so_ca_nhan(self):
        """hasEmployee phải False cho tài khoản vai trò. Test ở mức điều kiện
        (nhanh, không cần HTTP) cho _has_self_profile tự thân; hành vi HTTP
        thật của /api/me và /api/me/roles có test riêng ở
        TestRoleAccountFormWriteGuard (lớp đó đã dùng HttpCase nên không còn
        lý do né HTTP)."""
        _dept, emp = self._create_dept(name='Phong Me', login='tp_role_8')
        self.assertFalse(_has_self_profile(emp.user_id))
        nv_user = self.env['res.users'].create({
            'name': 'NV Co Ho So', 'login': 'nv_co_ho_so',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.env['hr.employee'].sudo().create({
            'name': 'NV Co Ho So', 'user_id': nv_user.id})
        self.assertTrue(_has_self_profile(nv_user))


@tagged('post_install', '-at_install')
class TestRoleAccountFormWriteGuard(HttpCase):
    """Bịt lỗ ghi ngược qua form Sửa nhân viên (phát hiện ở review Task 2).

    EmployeeForm.jsx gửi `status: emp?.statusKey || 'probation'` — tài khoản
    vai trò trả statusKey rỗng nên FE sẽ ghi ngược 'probation' nếu form này
    mở được cho nó. Nguy cơ thật KHÔNG phải "lọt lại vào hàng đợi Nhận việc":
    `api_onboarding` gọi `_emp_scope_domain` (đã có ROLE_ACCOUNT_EXCLUDED ở
    mọi nhánh) nên bản ghi lai vẫn bị chặn ở đó; còn `_hocba_maybe_assign_onboarding`
    (module hocba_employees, KHÔNG gọi `_emp_scope_domain` — vòng phụ thuộc
    không cho phép) tự chặn độc lập bằng điều kiện `not emp.x_is_role_account`
    ngay trong thân hàm (hr_employee.py:874). Nguy cơ thật là TOÀN VẸN DỮ
    LIỆU: bản ghi mang trạng thái nói dối (x_is_role_account=True nhưng thử
    việc), lộ ra ở filter "Thử việc" trên view Odoo backend, và sẽ ăn theo
    mốc thăng tiến/onboarding như NV thật nếu sau này ai đó gỡ cờ
    x_is_role_account.

    Đường tới được đây KHÔNG chỉ là "HR/Admin gọi ngoài UI" (Postman,
    script) — dù Task 3 đã lọc tài khoản vai trò khỏi mọi danh sách nên UI
    không còn đường mở form Sửa cho nó, _emp_in_scope vẫn trả True ngay cho
    HR/Admin (trước khi hỏi _emp_scope_domain) nên API vẫn nhận request POST
    thẳng bằng id. Nguy hiểm hơn: _emp_in_scope còn short-circuit
    `e == user.employee_id`, và _cap_edit_emp = _user_can_manage = True cho
    trưởng phòng — nghĩa là CHÍNH tài khoản vai trò trưởng phòng, đăng nhập
    bình thường (không cần Postman), cũng vượt được _can_edit_emp_record
    trên bản ghi CỦA CHÍNH NÓ, mà _role_payload vẫn trả 'employeeId': emp.id
    cho nó dùng. test_truong_phong_tu_sua_chinh_minh_van_bi_chan bên dưới
    khoá đúng đường này — đây mới là lý do chính guard tồn tại.

    Chặn thẳng ở backend, tại route api_employee_update: từ chối sửa tài
    khoản vai trò qua form nhân viên — HR quản nó ở màn Tài khoản, không
    phải form hồ sơ nhân sự.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_mgr = cls.env['res.users'].create({
            'name': 'HR Mgr Vai Tro WG', 'login': 'hrmgr_role_wg',
            'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_manager').id])]})
        # x_employment_status=False vì mô phỏng đúng đường thật
        # (_dept_new_manager) — create() không tự clear field này, chỉ mặc
        # định 'probation' như NV thường. Nếu không set, test sẽ không phân
        # biệt được "guard chặn ghi" với "chưa từng bị ghi gì".
        cls.role_emp = cls.env['hr.employee'].sudo().create({
            'name': 'TP Vai Tro WG', 'x_is_role_account': True,
            'x_employment_status': False})
        # Tài khoản vai trò THẬT (tạo qua _dept_create, có login/password) để
        # test được đường nguy hiểm nhất: chính nó tự đăng nhập rồi POST lên
        # id của chính mình. role_emp ở trên không có user_id nên không
        # đăng nhập được — không dùng lại được cho test này.
        dept_env = cls.env(user=cls.hr_mgr)
        out = _dept_create(dept_env, {
            'name': 'Phong WG Tu Sua',
            'manager': {'name': 'TP Tu Sua WG', 'login': 'tp_role_self_wg',
                        'password': PWD, 'password_confirm': PWD}})
        cls.self_role_emp = dept_env['hr.department'].sudo().browse(
            out['id']).manager_id

    def _post(self, emp, payload, login='hrmgr_role_wg'):
        """POST JSON tới api_employee_update, trả (status, body-dict) —
        cùng khuôn với test_me_password_scope.py để test đọc gọn bằng
        assertIn trên body['message']."""
        self.authenticate(login, PWD)
        resp = self.url_open(
            '/hocba-hrm/api/employee/%s' % emp.id, data=json.dumps(payload),
            headers={'Content-Type': 'application/json'})
        try:
            return resp.status_code, resp.json()
        except ValueError:
            return resp.status_code, {}

    def test_hr_khong_sua_duoc_tai_khoan_vai_tro_qua_form_nhan_vien(self):
        st, body = self._post(self.role_emp, {'status': 'probation'})
        self.assertEqual(st, 400, body)
        # Mã lỗi + nội dung message phải đúng — không chỉ status_code, không
        # thì đổi nhầm thành {'error':'forbidden'} hay bỏ message vẫn xanh
        # trong khi FE mất hẳn câu giải thích cho HR.
        self.assertEqual(
            body.get('error'), 'rejected',
            'Phải là "rejected" (lỗi nghiệp vụ) chứ không phải "forbidden" '
            '(lỗi quyền) — HR CÓ quyền sửa, chỉ là bản ghi này không sửa '
            'được bằng form này.')
        self.assertIn(
            'tài khoản vai trò', body.get('message', ''),
            'Mất câu giải thích thì HR không hiểu vì sao Lưu không được.')
        self.role_emp.invalidate_recordset()
        self.assertFalse(
            self.role_emp.x_employment_status,
            'Không được ghi ngược trạng thái thử việc lên tài khoản vai trò '
            '— dù request bị từ chối, phải chắc chắn hoàn toàn không ghi gì.')
        self.assertTrue(
            self.role_emp.x_is_role_account,
            'Cờ vai trò không được đổi trong lúc bị từ chối.')

    def test_truong_phong_tu_sua_chinh_minh_van_bi_chan(self):
        """Đường nguy hiểm nhất — xem docstring lớp: KHÔNG cần Postman của
        HR, chính trưởng phòng đăng nhập bình thường POST lên id của mình đã
        vượt được _can_edit_emp_record (e == user.employee_id +
        _user_can_manage). Guard tài khoản vai trò phải chặn độc lập với ai
        gọi."""
        st, body = self._post(self.self_role_emp, {'status': 'probation'},
                              login='tp_role_self_wg')
        self.assertEqual(st, 400, body)
        self.assertEqual(body.get('error'), 'rejected')
        self.assertIn('tài khoản vai trò', body.get('message', ''))
        self.self_role_emp.invalidate_recordset()
        self.assertFalse(
            self.self_role_emp.x_employment_status,
            'Trưởng phòng không được tự ghi trạng thái thử việc lên chính '
            'mình qua form nhân viên.')

    def test_nv_that_van_sua_binh_thuong(self):
        """Đối chứng: guard không được vơ đũa cả nắm sang NV thật."""
        real_emp = self.env['hr.employee'].sudo().create({'name': 'NV That WG'})
        st, body = self._post(real_emp, {'status': 'probation'})
        self.assertEqual(st, 200, body)
        real_emp.invalidate_recordset()
        self.assertEqual(real_emp.x_employment_status, 'probation')

    # ---- Task 5 (code review): hành vi HTTP thật của /api/me, /api/me/roles ----
    def test_api_me_an_ho_so_cho_tai_khoan_vai_tro(self):
        """GET /api/me phải trả hasEmployee=False cho tài khoản vai trò —
        hành vi HTTP thật, không chỉ điều kiện thuần (đối chứng với
        test_dieu_kien_an_ho_so_ca_nhan ở TestRoleAccount)."""
        self.authenticate('tp_role_self_wg', PWD)
        res = self.url_open('/hocba-hrm/api/me')
        self.assertEqual(res.status_code, 200, res.text[:300])
        self.assertFalse(res.json()['hasEmployee'])

    def test_api_me_roles_an_ho_so_cho_tai_khoan_vai_tro(self):
        """GET /api/me/roles (nguồn cho SPA dựng nav) cũng phải đồng nhất
        với /api/me — hai route dùng chung logic qua _has_self_profile."""
        self.authenticate('tp_role_self_wg', PWD)
        res = self.url_open('/hocba-hrm/api/me/roles')
        self.assertEqual(res.status_code, 200, res.text[:300])
        self.assertFalse(res.json()['hasEmployee'])


@tagged('post_install', '-at_install')
class TestRoleAccountIncompleteBadge(HttpCase):
    """Badge "cần hoàn thiện hồ sơ" (menu Nhân viên) không được đếm tài
    khoản vai trò (dọn từ review tổng thể trước khi gộp main).

    x_needs_profile_completion bật khi thiếu CCCD/MST/BHXH — tài khoản vai
    trò thiếu cả ba nên luôn True. Nếu badge đếm nó, HR bấm vào con số rồi mở
    danh sách (đã lọc _emp_scope_domain) sẽ không tìm ra ai tương ứng.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_mgr = cls.env['res.users'].create({
            'name': 'HR Mgr Badge WG', 'login': 'hrmgr_badge_wg',
            'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_manager').id])]})

    def _count(self):
        self.authenticate('hrmgr_badge_wg', PWD)
        res = self.url_open('/hocba-hrm/api/employees/incomplete-count')
        self.assertEqual(res.status_code, 200, res.text[:300])
        return res.json()['count']

    def test_tai_khoan_vai_tro_khong_tang_badge(self):
        """Đối chứng bằng NV thật: nếu tạo tài khoản vai trò không đổi số mà
        tạo NV thật thiếu giấy tờ cũng không đổi số, test này không phân
        biệt được 'lọc đúng' với 'endpoint hỏng luôn trả hằng số' — nên phải
        kiểm cả hai chiều."""
        before = self._count()
        self.env['hr.employee'].sudo().create({
            'name': 'TP Vai Tro Badge', 'x_is_role_account': True,
            'x_employment_status': False})
        after_role = self._count()
        self.assertEqual(
            after_role, before,
            'Tài khoản vai trò thiếu CCCD/MST/BHXH nhưng không phải hồ sơ '
            'nhân sự — không được cộng vào badge "cần hoàn thiện hồ sơ".')
        self.env['hr.employee'].sudo().create({'name': 'NV That Badge'})
        after_real = self._count()
        self.assertEqual(
            after_real, before + 1,
            'NV thật thiếu giấy tờ vẫn phải tăng badge — nếu không tăng, '
            'endpoint có thể đang luôn trả hằng số chứ không thật sự đếm.')
