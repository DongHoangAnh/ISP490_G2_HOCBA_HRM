# Offboarding Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây quy trình thôi việc thống nhất (`hocba.offboarding`) cho module `hocba_employees`: đơn nghỉ có state machine 2 cấp duyệt, đóng bảo mật (resigned + archive + khoá tài khoản), gộp luồng rớt thử việc, kèm API cho SPA.

**Architecture:** Model mới `hocba.offboarding` (kế thừa `mail.thread`) giữ vòng đời đơn nghỉ. Phân quyền qua ACL + record rules (NV=của mình, quản lý trực tiếp/giáo vụ=phạm vi mình, HR Manager=tất cả) + kiểm quyền theo state trong các `action_*`. Đóng hồ sơ tái dùng logic block-archive sẵn có. Controller `hocba_hrm` expose 3 endpoint JSON.

**Tech Stack:** Odoo 19, Python, PostgreSQL. Test bằng `odoo.tests.common.TransactionCase`. Spec gốc: `docs/superpowers/specs/2026-07-04-offboarding-design.md`.

**Phạm vi plan này:** Backend model + enforcement + security + view Odoo + API controller + test. **SPA (React) tách plan riêng** sau khi API verify (đúng "backend chắc trước, UI sau").

---

## File Structure

**Tạo mới:**
- `custom-addons/hocba_employees/models/hocba_offboarding.py` — model `hocba.offboarding` + state machine.
- `custom-addons/hocba_employees/data/hocba_offboarding_data.xml` — `ir.sequence` mã đơn `OFF/YYYY/NNNN`.
- `custom-addons/hocba_employees/security/hocba_offboarding_rules.xml` — record rules phạm vi.
- `custom-addons/hocba_employees/views/hocba_offboarding_views.xml` — form/list/action/menu backend.
- `custom-addons/hocba_employees/tests/test_offboarding.py` — test model + phân quyền + tích hợp thử việc.

**Sửa:**
- `custom-addons/hocba_employees/models/__init__.py` — import model mới.
- `custom-addons/hocba_employees/security/ir.model.access.csv` — 4 dòng ACL.
- `custom-addons/hocba_employees/models/hr_employee.py` — sửa `_hocba_start_offboarding` tạo bản ghi offboarding.
- `custom-addons/hocba_employees/__manifest__.py` — thêm 3 file data/security/view.
- `custom-addons/hocba_employees/tests/__init__.py` — import test mới.
- `custom-addons/hocba_hrm/controllers/main.py` — 3 endpoint API.

**Lệnh test chuẩn (chạy sau mỗi task backend):**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```
Kết quả cần thấy: `0 failed, 0 error(s) of N tests` với N > 0.

---

## Task 1: Model `hocba.offboarding` — khung + tạo mã tự sinh

**Files:**
- Create: `custom-addons/hocba_employees/models/hocba_offboarding.py`
- Create: `custom-addons/hocba_employees/data/hocba_offboarding_data.xml`
- Modify: `custom-addons/hocba_employees/models/__init__.py`
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv`
- Modify: `custom-addons/hocba_employees/__manifest__.py`
- Create/Modify: `custom-addons/hocba_employees/tests/test_offboarding.py`, `custom-addons/hocba_employees/tests/__init__.py`

- [ ] **Step 1: Viết test đỏ — tạo đơn sinh mã & mặc định state**

Tạo `custom-addons/hocba_employees/tests/test_offboarding.py`:
```python
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOffboardingModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Off Target',
            'identification_id': '012345678901',
        })

    def _make(self, **kw):
        vals = {
            'employee_id': self.emp.id,
            'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hocba.offboarding'].create(vals)

    def test_create_generates_code_and_draft(self):
        rec = self._make()
        self.assertNotIn(rec.name, ('/', False))
        self.assertTrue(rec.name.startswith('OFF/'))
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(rec.source, 'self')
```

Thêm vào `custom-addons/hocba_employees/tests/__init__.py`:
```python
from . import test_offboarding
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn (ở đầu plan).
Expected: FAIL — `KeyError` / `Model 'hocba.offboarding' does not exist`.

- [ ] **Step 3: Viết model tối thiểu**

Tạo `custom-addons/hocba_employees/models/hocba_offboarding.py`:
```python
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class HocbaOffboarding(models.Model):
    _name = 'hocba.offboarding'
    _description = 'Đơn / Quy trình thôi việc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'

    SOURCE_SEL = [
        ('self', 'NV tự nộp'),
        ('hr', 'HR khởi tạo'),
        ('probation', 'Rớt thử việc'),
    ]
    REASON_SEL = [
        ('voluntary', 'Tự nguyện'),
        ('performance', 'Không đạt'),
        ('contract_end', 'Hết hạn HĐ'),
        ('other', 'Khác'),
    ]
    STATE_SEL = [
        ('draft', 'Nháp'),
        ('submitted', 'Chờ quản lý duyệt'),
        ('mgr_approved', 'Chờ HR duyệt'),
        ('hr_approved', 'Chờ hoàn tất'),
        ('done', 'Đã nghỉ'),
        ('refused', 'Từ chối'),
        ('cancelled', 'Đã huỷ'),
    ]

    name = fields.Char(string='Mã đơn', readonly=True, copy=False, default='/')
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True, tracking=True)
    source = fields.Selection(
        SOURCE_SEL, string='Nguồn', default='self', required=True)
    reason_type = fields.Selection(
        REASON_SEL, string='Loại lý do', required=True, default='voluntary')
    reason = fields.Text(string='Lý do chi tiết')
    request_date = fields.Date(
        string='Ngày nộp đơn', default=fields.Date.context_today)
    expected_leave_date = fields.Date(string='Ngày nghỉ dự kiến', required=True)
    actual_leave_date = fields.Date(string='Ngày nghỉ thực tế', readonly=True)
    mgr_approved_by = fields.Many2one('res.users', string='Quản lý duyệt', readonly=True)
    mgr_approved_date = fields.Datetime(string='Ngày QL duyệt', readonly=True)
    hr_approved_by = fields.Many2one('res.users', string='HR duyệt', readonly=True)
    hr_approved_date = fields.Datetime(string='Ngày HR duyệt', readonly=True)
    chk_handover = fields.Boolean(string='Đã bàn giao công việc')
    chk_payroll = fields.Boolean(string='Đã chốt lương/công nợ')
    chk_documents = fields.Boolean(string='Đã lưu hồ sơ')
    asset_pending_count = fields.Integer(
        string='Tài sản chưa thu hồi', compute='_compute_asset_pending_count')
    state = fields.Selection(
        STATE_SEL, string='Trạng thái', default='draft',
        required=True, tracking=True, copy=False)
    prev_employment_status = fields.Char(readonly=True, copy=False)
    note = fields.Text(string='Ghi chú')

    @api.depends('employee_id.x_asset_ids.state')
    def _compute_asset_pending_count(self):
        for rec in self:
            rec.asset_pending_count = len(rec.employee_id.x_asset_ids.filtered(
                lambda a: a.state == 'assigned'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hocba.offboarding') or '/'
        return super().create(vals_list)
```

Tạo `custom-addons/hocba_employees/data/hocba_offboarding_data.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="seq_hocba_offboarding" model="ir.sequence">
            <field name="name">HOCBA Offboarding Code</field>
            <field name="code">hocba.offboarding</field>
            <field name="prefix">OFF/%(year)s/</field>
            <field name="padding">4</field>
            <field name="number_next">1</field>
            <field name="number_increment">1</field>
            <field name="implementation">standard</field>
        </record>
    </data>
</odoo>
```

Thêm dòng vào cuối `custom-addons/hocba_employees/models/__init__.py`:
```python
from . import hocba_offboarding
```

Thêm 4 dòng vào cuối `custom-addons/hocba_employees/security/ir.model.access.csv`:
```csv
access_hocba_offboarding_user,access.hocba.offboarding.user,model_hocba_offboarding,base.group_user,1,1,1,0
access_hocba_offboarding_hr,access.hocba.offboarding.hr,model_hocba_offboarding,hr.group_hr_user,1,1,1,0
access_hocba_offboarding_manager,access.hocba.offboarding.manager,model_hocba_offboarding,hr.group_hr_manager,1,1,1,1
access_hocba_offboarding_giaovu,access.hocba.offboarding.giaovu,model_hocba_offboarding,hocba_employees.group_hocba_giaovu,1,1,1,0
```

Trong `custom-addons/hocba_employees/__manifest__.py`, thêm `data/hocba_offboarding_data.xml` ngay sau dòng `'data/hr_employee_sequence.xml',`:
```python
        'data/hr_employee_sequence.xml',
        'data/hocba_offboarding_data.xml',
```

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test chuẩn.
Expected: PASS `test_create_generates_code_and_draft`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hocba_offboarding.py \
  custom-addons/hocba_employees/data/hocba_offboarding_data.xml \
  custom-addons/hocba_employees/models/__init__.py \
  custom-addons/hocba_employees/security/ir.model.access.csv \
  custom-addons/hocba_employees/__manifest__.py \
  custom-addons/hocba_employees/tests/test_offboarding.py \
  custom-addons/hocba_employees/tests/__init__.py
git commit -m "feat(offboarding): model hocba.offboarding + sequence mã đơn"
```

---

## Task 2: State machine — submit / mgr_approve / hr_approve

**Files:**
- Modify: `custom-addons/hocba_employees/models/hocba_offboarding.py`
- Test: `custom-addons/hocba_employees/tests/test_offboarding.py`

- [ ] **Step 1: Viết test đỏ — chuỗi duyệt hợp lệ**

Thêm vào class `TestOffboardingModel`:
```python
    def test_happy_path_states(self):
        rec = self._make()
        rec.action_submit()
        self.assertEqual(rec.state, 'submitted')
        # duyệt cấp quản lý + HR bằng sudo (kiểm quyền test ở class khác)
        rec.sudo().action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        self.assertTrue(rec.mgr_approved_by)
        rec.sudo().action_hr_approve()
        self.assertEqual(rec.state, 'hr_approved')
        self.assertTrue(rec.hr_approved_by)

    def test_submit_only_from_draft(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        with self.assertRaises(ValidationError):
            rec.action_submit()
```

Lưu ý: `self.emp` mặc định `x_employment_status='probation'`; sau mgr_approve phải thành `exiting`.

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn.
Expected: FAIL — `AttributeError: 'hocba.offboarding' object has no attribute 'action_submit'`.

- [ ] **Step 3: Viết các action + helper quyền**

Thêm vào cuối class trong `hocba_offboarding.py`:
```python
    def _ensure_manages(self):
        """Raise nếu user hiện tại không quản lý phạm vi của NV (và không HR/su)."""
        self.ensure_one()
        user = self.env.user
        if self.env.su or user.has_group('hr.group_hr_manager'):
            return
        emp = self.employee_id
        if emp._hocba_user_manages_dept(user):
            return
        if user.has_group('hocba_employees.group_hocba_giaovu') \
                and emp.x_employee_type_id.code == 'teacher':
            return
        raise AccessError(_(
            'Bạn không có quyền duyệt đơn nghỉ của nhân viên này.'))

    def _is_hr_manager(self):
        return self.env.su or self.env.user.has_group('hr.group_hr_manager')

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Chỉ đơn nháp mới được nộp.'))
            user = rec.env.user
            if not rec._is_hr_manager() and rec.employee_id != user.employee_id:
                raise AccessError(_('Chỉ được nộp đơn nghỉ của chính mình.'))
            rec.state = 'submitted'
            rec.message_post(body=_('📤 Đã nộp đơn nghỉ việc.'))

    def action_mgr_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(_('Đơn không ở trạng thái chờ quản lý duyệt.'))
            rec._ensure_manages()
            rec.mgr_approved_by = rec.env.user
            rec.mgr_approved_date = fields.Datetime.now()
            rec.prev_employment_status = rec.employee_id.x_employment_status
            rec.employee_id.sudo().with_context(
                hocba_gate_automation=True).write({'x_employment_status': 'exiting'})
            rec.state = 'mgr_approved'
            rec.message_post(body=_('✅ Quản lý đã duyệt đơn nghỉ.'))

    def action_hr_approve(self):
        for rec in self:
            if rec.state != 'mgr_approved':
                raise ValidationError(_('Đơn chưa được quản lý duyệt.'))
            if not rec._is_hr_manager():
                raise AccessError(_('Chỉ HR Manager được duyệt bước này.'))
            rec.hr_approved_by = rec.env.user
            rec.hr_approved_date = fields.Datetime.now()
            rec.state = 'hr_approved'
            rec.message_post(body=_(
                '✅ HR đã duyệt — chờ thu hồi tài sản & hoàn tất.'))
```

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test chuẩn.
Expected: PASS `test_happy_path_states`, `test_submit_only_from_draft`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hocba_offboarding.py \
  custom-addons/hocba_employees/tests/test_offboarding.py
git commit -m "feat(offboarding): state machine submit/mgr_approve/hr_approve"
```

---

## Task 3: `action_done` — đóng bảo mật + chặn tài sản

**Files:**
- Modify: `custom-addons/hocba_employees/models/hocba_offboarding.py`
- Test: `custom-addons/hocba_employees/tests/test_offboarding.py`

- [ ] **Step 1: Viết test đỏ — hoàn tất & chặn tài sản**

Thêm vào class `TestOffboardingModel`:
```python
    def _advance_to_hr_approved(self, rec):
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        rec.sudo().action_hr_approve()

    def test_done_closes_profile_and_locks_user(self):
        user = self.env['res.users'].create({
            'name': 'Leaver', 'login': 'off_leaver_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp.user_id = user
        rec = self._make()
        self._advance_to_hr_approved(rec)
        rec.sudo().action_done()
        self.assertEqual(rec.state, 'done')
        self.assertEqual(self.emp.x_employment_status, 'resigned')
        self.assertFalse(self.emp.active)
        self.assertFalse(user.active)
        self.assertEqual(rec.actual_leave_date, fields.Date.today())

    def test_done_blocked_when_asset_assigned(self):
        from odoo.exceptions import ValidationError
        atype = self.env['hocba.asset.type'].create({
            'name': 'Laptop Off', 'code': 'LAPOFF'})
        self.env['hr.employee.asset'].create({
            'employee_id': self.emp.id,
            'asset_type_id': atype.id,
            'asset_code': 'LAPOFF-1',
            'grant_date': fields.Date.today(),
            'condition_in': 'new',
        })
        rec = self._make()
        self._advance_to_hr_approved(rec)
        with self.assertRaises(ValidationError):
            rec.sudo().action_done()
        self.assertEqual(rec.state, 'hr_approved')
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn.
Expected: FAIL — `AttributeError: ... action_done`.

- [ ] **Step 3: Viết `action_done`**

Thêm vào class trong `hocba_offboarding.py`:
```python
    def action_done(self):
        for rec in self:
            if rec.state != 'hr_approved':
                raise ValidationError(_('Đơn chưa sẵn sàng hoàn tất.'))
            if not rec._is_hr_manager():
                raise AccessError(_('Chỉ HR Manager được hoàn tất đơn nghỉ.'))
            emp = rec.employee_id
            pending = emp.x_asset_ids.filtered(lambda a: a.state == 'assigned')
            if pending:
                raise ValidationError(_(
                    'Còn %(n)d tài sản chưa thu hồi: %(codes)s') % {
                        'n': len(pending),
                        'codes': ', '.join(pending.mapped('asset_code'))})
            rec.actual_leave_date = fields.Date.context_today(rec)
            emp.sudo().with_context(hocba_gate_automation=True).write({
                'x_employment_status': 'resigned', 'active': False})
            if emp.user_id:
                emp.user_id.sudo().write({'active': False})
            rec.state = 'done'
            rec.message_post(body=_('🏁 Hoàn tất nghỉ việc từ %s.') % rec.actual_leave_date)
```

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test chuẩn.
Expected: PASS `test_done_closes_profile_and_locks_user`, `test_done_blocked_when_asset_assigned`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hocba_offboarding.py \
  custom-addons/hocba_employees/tests/test_offboarding.py
git commit -m "feat(offboarding): action_done đóng bảo mật + chặn tài sản chưa thu"
```

---

## Task 4: refuse / cancel + hoàn nguyên trạng thái

**Files:**
- Modify: `custom-addons/hocba_employees/models/hocba_offboarding.py`
- Test: `custom-addons/hocba_employees/tests/test_offboarding.py`

- [ ] **Step 1: Viết test đỏ**

Thêm vào class `TestOffboardingModel`:
```python
    def test_refuse_after_mgr_restores_status(self):
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        rec.sudo().action_refuse()
        self.assertEqual(rec.state, 'refused')
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_cancel_only_before_approval(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        with self.assertRaises(ValidationError):
            rec.sudo().action_cancel()
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn.
Expected: FAIL — `AttributeError: ... action_refuse`.

- [ ] **Step 3: Viết `action_refuse` + `action_cancel`**

Thêm vào class trong `hocba_offboarding.py`:
```python
    def action_refuse(self):
        for rec in self:
            if rec.state not in ('submitted', 'mgr_approved'):
                raise ValidationError(_('Chỉ từ chối đơn đang chờ duyệt.'))
            if rec.state == 'mgr_approved':
                if not rec._is_hr_manager():
                    raise AccessError(_('Chỉ HR Manager từ chối bước này.'))
            else:
                rec._ensure_manages()
            if rec.prev_employment_status:
                rec.employee_id.sudo().with_context(
                    hocba_gate_automation=True).write(
                    {'x_employment_status': rec.prev_employment_status})
            rec.state = 'refused'
            rec.message_post(body=_('❌ Đơn nghỉ bị từ chối.'))

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'submitted'):
                raise ValidationError(_('Chỉ huỷ đơn nháp hoặc đang chờ duyệt.'))
            user = rec.env.user
            if not rec._is_hr_manager() and rec.employee_id != user.employee_id:
                raise AccessError(_('Chỉ được huỷ đơn nghỉ của chính mình.'))
            rec.state = 'cancelled'
            rec.message_post(body=_('🚫 Đã huỷ đơn nghỉ.'))
```

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test chuẩn.
Expected: PASS `test_refuse_after_mgr_restores_status`, `test_cancel_only_before_approval`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hocba_offboarding.py \
  custom-addons/hocba_employees/tests/test_offboarding.py
git commit -m "feat(offboarding): refuse/cancel + hoàn nguyên trạng thái NV"
```

---

## Task 5: Record rules + test phân quyền

**Files:**
- Create: `custom-addons/hocba_employees/security/hocba_offboarding_rules.xml`
- Modify: `custom-addons/hocba_employees/__manifest__.py`
- Test: `custom-addons/hocba_employees/tests/test_offboarding.py`

- [ ] **Step 1: Viết test đỏ — phạm vi duyệt**

Thêm class mới vào `test_offboarding.py`:
```python
@tagged('post_install', '-at_install')
class TestOffboardingAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        # Phòng A có trưởng phòng là mgrA
        self.mgrA_user = self.env['res.users'].create({
            'name': 'MgrA', 'login': 'off_mgra',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.mgrA = self.env['hr.employee'].create({
            'name': 'MgrA Emp', 'identification_id': '011111111101',
            'user_id': self.mgrA_user.id})
        self.deptA = self.env['hr.department'].create({
            'name': 'Dept A Off', 'manager_id': self.mgrA.id})
        # NV phòng A
        self.staffA_user = self.env['res.users'].create({
            'name': 'StaffA', 'login': 'off_staffa',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.staffA = self.env['hr.employee'].create({
            'name': 'StaffA Emp', 'identification_id': '011111111102',
            'department_id': self.deptA.id, 'user_id': self.staffA_user.id})
        # Giáo vụ + 1 giáo viên
        teacher_type = self.env['hocba.employee.type'].search(
            [('code', '=', 'teacher')], limit=1)
        self.gv_user = self.env['res.users'].create({
            'name': 'GiaoVu', 'login': 'off_gv',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        self.teacher = self.env['hr.employee'].create({
            'name': 'Teacher Off', 'identification_id': '011111111103',
            'x_employee_type_id': teacher_type.id if teacher_type else False})

    def _submit_for(self, emp, submitter_user):
        rec = self.env['hocba.offboarding'].with_user(submitter_user).create({
            'employee_id': emp.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec.action_submit()
        return rec

    def test_manager_approves_own_dept(self):
        rec = self._submit_for(self.staffA, self.staffA_user)
        rec.with_user(self.mgrA_user).action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')

    def test_manager_cannot_approve_other_dept(self):
        from odoo.exceptions import AccessError
        # NV phòng B, mgrA không quản lý
        staffB = self.env['hr.employee'].create({
            'name': 'StaffB', 'identification_id': '011111111104'})
        rec = self.env['hocba.offboarding'].sudo().create({
            'employee_id': staffB.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec.sudo().action_submit()
        with self.assertRaises(AccessError):
            rec.with_user(self.mgrA_user).action_mgr_approve()

    def test_giaovu_approves_teacher_not_office(self):
        from odoo.exceptions import AccessError
        rec_t = self.env['hocba.offboarding'].sudo().create({
            'employee_id': self.teacher.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec_t.sudo().action_submit()
        rec_t.with_user(self.gv_user).action_mgr_approve()
        self.assertEqual(rec_t.state, 'mgr_approved')
        # đơn của NV văn phòng (phòng A) → giáo vụ không duyệt được
        rec_o = self._submit_for(self.staffA, self.staffA_user)
        with self.assertRaises(AccessError):
            rec_o.with_user(self.gv_user).action_mgr_approve()

    def test_employee_cannot_self_approve(self):
        from odoo.exceptions import AccessError
        rec = self._submit_for(self.staffA, self.staffA_user)
        with self.assertRaises(AccessError):
            rec.with_user(self.staffA_user).action_mgr_approve()
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn.
Expected: FAIL — nhiều khả năng `AccessError` khi NV đọc đơn của người khác, hoặc mgr không đọc được đơn NV phòng mình (chưa có record rule) → khẳng định cần rule.

- [ ] **Step 3: Viết record rules + đăng ký manifest**

Tạo `custom-addons/hocba_employees/security/hocba_offboarding_rules.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- NV thường: thấy đơn của mình HOẶC đơn NV mà mình là trưởng phòng/quản lý trực tiếp -->
    <record id="hocba_rule_offboarding_own" model="ir.rule">
        <field name="name">Offboarding: của mình / cấp dưới trực tiếp</field>
        <field name="model_id" ref="model_hocba_offboarding"/>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
        <field name="domain_force">['|', '|',
            ('employee_id.user_id', '=', user.id),
            ('employee_id.department_id.manager_id.user_id', '=', user.id),
            ('employee_id.parent_id.user_id', '=', user.id)]</field>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="False"/>
    </record>

    <!-- Giáo vụ: thấy đơn của giáo viên -->
    <record id="hocba_rule_offboarding_giaovu" model="ir.rule">
        <field name="name">Offboarding: giáo vụ xem giáo viên</field>
        <field name="model_id" ref="model_hocba_offboarding"/>
        <field name="groups" eval="[(4, ref('group_hocba_giaovu'))]"/>
        <field name="domain_force">[('employee_id.x_employee_type_id.code', '=', 'teacher')]</field>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="False"/>
    </record>

    <!-- HR user/manager: thấy tất cả -->
    <record id="hocba_rule_offboarding_hr" model="ir.rule">
        <field name="name">Offboarding: HR xem tất cả</field>
        <field name="model_id" ref="model_hocba_offboarding"/>
        <field name="groups" eval="[(4, ref('hr.group_hr_user'))]"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="False"/>
    </record>
</odoo>
```

Trong `custom-addons/hocba_employees/__manifest__.py`, thêm ngay sau `'security/ir.model.access.csv',`:
```python
        'security/ir.model.access.csv',
        'security/hocba_offboarding_rules.xml',
```

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test chuẩn.
Expected: PASS cả 4 test trong `TestOffboardingAccess`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/security/hocba_offboarding_rules.xml \
  custom-addons/hocba_employees/__manifest__.py \
  custom-addons/hocba_employees/tests/test_offboarding.py
git commit -m "feat(offboarding): record rules phạm vi + test phân quyền"
```

---

## Task 6: Gộp luồng rớt thử việc vào `hocba.offboarding`

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py:688` (`_hocba_start_offboarding`)
- Test: `custom-addons/hocba_employees/tests/test_offboarding.py`

- [ ] **Step 1: Viết test đỏ — rớt cổng tạo đơn probation**

Thêm class mới vào `test_offboarding.py`:
```python
@tagged('post_install', '-at_install')
class TestOffboardingProbation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Probation Fail', 'identification_id': '013333333301',
            'x_employment_status': 'probation'})

    def test_gate_fail_creates_offboarding(self):
        self.emp._hocba_start_offboarding('tuần-2')
        rec = self.env['hocba.offboarding'].search(
            [('employee_id', '=', self.emp.id)])
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec.source, 'probation')
        self.assertEqual(rec.reason_type, 'performance')
        self.assertEqual(rec.state, 'hr_approved')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run lệnh test chuẩn.
Expected: FAIL — `search` trả 0 bản ghi (`_hocba_start_offboarding` chưa tạo đơn).

- [ ] **Step 3: Sửa `_hocba_start_offboarding`**

Trong `custom-addons/hocba_employees/models/hr_employee.py`, thay thân method `_hocba_start_offboarding` (hiện ở dòng ~688) bằng:
```python
    def _hocba_start_offboarding(self, gate_label):
        """Không đạt cổng → khởi động nghỉ thử việc (tạo đơn offboarding)."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        self.env['hocba.offboarding'].sudo().create({
            'employee_id': self.id,
            'source': 'probation',
            'reason_type': 'performance',
            'reason': _('Không đạt cổng thử việc %s') % gate_label,
            'request_date': today,
            'expected_leave_date': today,
            'prev_employment_status': self.x_employment_status,
            'state': 'hr_approved',
        })
        self.sudo().with_context(hocba_gate_automation=True).write(
            {'x_employment_status': 'exiting'})
        self._hocba_gate_activity(
            _('Offboarding nghỉ thử việc: %s') % self.name,
            today + timedelta(days=1))
        self.message_post(body=_(
            '❌ Cổng %s KHÔNG ĐẠT — khởi động nghỉ thử việc.') % gate_label)
```

- [ ] **Step 4: Chạy test — xác nhận xanh (và không vỡ test cũ)**

Run lệnh test chuẩn.
Expected: PASS `test_gate_fail_creates_offboarding`; toàn bộ test `hocba_employees` cũ vẫn `0 failed`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py \
  custom-addons/hocba_employees/tests/test_offboarding.py
git commit -m "feat(offboarding): rớt cổng thử việc tạo đơn offboarding thống nhất"
```

---

## Task 7: View backend Odoo (form/list/action/menu)

**Files:**
- Create: `custom-addons/hocba_employees/views/hocba_offboarding_views.xml`
- Modify: `custom-addons/hocba_employees/__manifest__.py`

> Task này không có unit test (view). Kiểm chứng bằng cách nạp module không lỗi.

- [ ] **Step 1: Viết view + action + menu**

Tạo `custom-addons/hocba_employees/views/hocba_offboarding_views.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_hocba_offboarding_form" model="ir.ui.view">
        <field name="name">hocba.offboarding.form</field>
        <field name="model">hocba.offboarding</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_submit" type="object" string="Nộp đơn"
                            class="btn-primary" invisible="state != 'draft'"/>
                    <button name="action_mgr_approve" type="object" string="Quản lý duyệt"
                            class="btn-primary" invisible="state != 'submitted'"/>
                    <button name="action_hr_approve" type="object" string="HR duyệt"
                            class="btn-primary" invisible="state != 'mgr_approved'"/>
                    <button name="action_done" type="object" string="Hoàn tất"
                            class="btn-primary" invisible="state != 'hr_approved'"/>
                    <button name="action_refuse" type="object" string="Từ chối"
                            invisible="state not in ('submitted','mgr_approved')"/>
                    <button name="action_cancel" type="object" string="Huỷ"
                            invisible="state not in ('draft','submitted')"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,submitted,mgr_approved,hr_approved,done"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name" readonly="1"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="employee_id"/>
                            <field name="source"/>
                            <field name="reason_type"/>
                            <field name="reason"/>
                        </group>
                        <group>
                            <field name="request_date"/>
                            <field name="expected_leave_date"/>
                            <field name="actual_leave_date"/>
                            <field name="asset_pending_count"/>
                        </group>
                    </group>
                    <group string="Duyệt">
                        <field name="mgr_approved_by"/>
                        <field name="hr_approved_by"/>
                    </group>
                    <group string="Checklist thôi việc">
                        <field name="chk_handover"/>
                        <field name="chk_payroll"/>
                        <field name="chk_documents"/>
                        <field name="note"/>
                    </group>
                </sheet>
                <chatter/>
            </form>
        </field>
    </record>

    <record id="view_hocba_offboarding_list" model="ir.ui.view">
        <field name="name">hocba.offboarding.list</field>
        <field name="model">hocba.offboarding</field>
        <field name="arch" type="xml">
            <list decoration-muted="state in ('done','cancelled','refused')">
                <field name="name"/>
                <field name="employee_id"/>
                <field name="reason_type"/>
                <field name="request_date"/>
                <field name="expected_leave_date"/>
                <field name="asset_pending_count"/>
                <field name="state" widget="badge"/>
            </list>
        </field>
    </record>

    <record id="action_hocba_offboarding" model="ir.actions.act_window">
        <field name="name">Đơn thôi việc</field>
        <field name="res_model">hocba.offboarding</field>
        <field name="view_mode">list,form</field>
    </record>

    <menuitem id="menu_hocba_offboarding"
              name="Thôi việc"
              parent="hr.menu_hr_root"
              action="action_hocba_offboarding"
              sequence="90"
              groups="hr.group_hr_user"/>
</odoo>
```

Trong `__manifest__.py`, thêm sau `'views/hr_promotion_history_views.xml',`:
```python
        'views/hr_promotion_history_views.xml',
        'views/hocba_offboarding_views.xml',
```

- [ ] **Step 2: Nạp module — xác nhận không lỗi view**

Run lệnh test chuẩn (nó `-u hocba_employees`, sẽ nạp view).
Expected: module nạp thành công, `0 failed, 0 error(s)`; không có `ParseError`/`Field ... does not exist`.

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_employees/views/hocba_offboarding_views.xml \
  custom-addons/hocba_employees/__manifest__.py
git commit -m "feat(offboarding): view backend form/list + menu HR"
```

---

## Task 8: API controller `/hocba-hrm/api/offboarding/*`

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Test: `custom-addons/hocba_hrm/tests/test_offboarding_api.py` (tạo mới)

> Endpoint dùng `type='http', csrf=False`, `request.get_json_data()`, `request.make_json_response(...)` theo pattern hiện có (xem `api_asset_return` ~dòng 2133).

- [ ] **Step 1: Viết test đỏ — submit + list + action qua ORM controller**

Tạo `custom-addons/hocba_hrm/tests/test_offboarding_api.py`:
```python
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.hocba_hrm.controllers.main import _emp_scope_domain


@tagged('post_install', '-at_install')
class TestOffboardingScope(TransactionCase):
    """Kiểm helper scope dùng cho endpoint list (endpoint HTTP test qua tour/manual)."""
    def setUp(self):
        super().setUp()
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Off', 'login': 'off_api_hr',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_manager').id])]})
        self.emp = self.env['hr.employee'].create({
            'name': 'API Off Emp', 'identification_id': '014444444401'})

    def test_hr_scope_sees_offboarding(self):
        rec = self.env['hocba.offboarding'].create({
            'employee_id': self.emp.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        env = self.env(user=self.hr_user)
        # HR Manager: _emp_scope_domain trả [] → thấy mọi nhân viên
        self.assertEqual(_emp_scope_domain(env), [])
        scope_emp_ids = env['hr.employee'].sudo().search(
            _emp_scope_domain(env)).ids
        found = env['hocba.offboarding'].sudo().search(
            [('employee_id', 'in', scope_emp_ids)])
        self.assertIn(rec.id, found.ids)
```

> Ghi chú: endpoint HTTP đầy đủ khó test bằng TransactionCase; test này khoá logic scope. Kiểm endpoint end-to-end ở bước verify thủ công + SPA plan.

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```
Expected: FAIL (import hoặc logic) hoặc PASS ngay nếu scope đã đúng — nếu PASS, vẫn tiếp Step 3 để thêm endpoint.

- [ ] **Step 3: Thêm 3 endpoint vào controller**

Trong `custom-addons/hocba_hrm/controllers/main.py`, thêm vào trong class controller chính (cùng chỗ các route `/hocba-hrm/api/...`, ví dụ sau `api_asset_transfer`):
```python
    # ------------------------------------------------------------------
    # Offboarding — đơn thôi việc (self-service + duyệt 2 cấp)
    # ------------------------------------------------------------------
    def _offb_json(self, rec):
        return {
            'id': rec.id, 'name': rec.name,
            'employeeId': rec.employee_id.id,
            'employeeName': rec.employee_id.name,
            'source': rec.source, 'reasonType': rec.reason_type,
            'reason': rec.reason or '',
            'requestDate': rec.request_date and str(rec.request_date) or '',
            'expectedLeaveDate': rec.expected_leave_date
                and str(rec.expected_leave_date) or '',
            'state': rec.state,
            'assetPending': rec.asset_pending_count,
        }

    @http.route('/hocba-hrm/api/offboarding/submit', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_offboarding_submit(self, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response(
                {'error': 'no_employee'}, status=400)
        payload = request.get_json_data() or {}
        try:
            rec = request.env['hocba.offboarding'].create({
                'employee_id': emp.id,
                'source': 'self',
                'reason_type': payload.get('reasonType') or 'voluntary',
                'reason': (payload.get('reason') or '').strip(),
                'expected_leave_date': payload.get('expectedLeaveDate')
                    or fields.Date.context_today(request.env.user),
            })
            rec.action_submit()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True, 'item': self._offb_json(rec)})

    @http.route('/hocba-hrm/api/offboarding/list', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_offboarding_list(self, **kw):
        env = request.env
        can_manage = _user_can_manage(env)
        if can_manage:
            # _emp_scope_domain: [] cho HR (mọi NV), domain phòng/giáo viên cho quản lý
            scope_emp_ids = env['hr.employee'].sudo().search(
                _emp_scope_domain(env)).ids
            recs = env['hocba.offboarding'].sudo().search(
                [('employee_id', 'in', scope_emp_ids)])
        else:
            emp = env.user.employee_id
            recs = env['hocba.offboarding'].sudo().search(
                [('employee_id', '=', emp.id if emp else -1)])
        return request.make_json_response({
            'canManage': can_manage,
            'items': [self._offb_json(r) for r in recs],
        })

    @http.route('/hocba-hrm/api/offboarding/action', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_offboarding_action(self, **kw):
        payload = request.get_json_data() or {}
        rec_id = self._conv_id(payload.get('id'))
        action = payload.get('action')
        allowed = {'submit', 'mgr_approve', 'hr_approve',
                   'refuse', 'cancel', 'done'}
        if not rec_id or action not in allowed:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        rec = request.env['hocba.offboarding'].browse(rec_id)
        if not rec.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            getattr(rec, 'action_%s' % action)()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True, 'item': self._offb_json(rec)})
```

> `_conv_id` và `_user_can_manage` / `_emp_scope_domain` đã có sẵn trong file. `fields`, `AccessError`, `ValidationError`, `UserError` đã import ở đầu file.

- [ ] **Step 4: Chạy test — xác nhận xanh**

Run lệnh test `-u hocba_hrm,hocba_employees --test-tags /hocba_hrm` (như Step 2).
Expected: PASS `test_hr_scope_sees_offboarding`; module nạp không lỗi route.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py \
  custom-addons/hocba_hrm/tests/test_offboarding_api.py
git commit -m "feat(offboarding): API submit/list/action cho SPA"
```

---

## Self-Review Notes (đã kiểm khi viết plan)

- **Spec coverage:** §3 model (Task 1), §4 state machine (Task 2,4), §5 action_done (Task 3), §6 tích hợp thử việc (Task 6), §7 phân quyền (Task 5), §8 API (Task 8). §8 SPA (React) → plan riêng sau khi API verify.
- **Type consistency:** method names `action_submit/mgr_approve/hr_approve/done/refuse/cancel`, helper `_ensure_manages`, `_is_hr_manager`, field `prev_employment_status`, `asset_pending_count` dùng nhất quán mọi task.
- **Điểm cần chú ý khi thực thi:**
  - `x_asset_ids` đã tồn tại trên `hr.employee` (dùng ở `hr_employee.py:592`).
  - `action_done` set `active=False` sẽ đi qua guard `write()` block-archive — đã check hết tài sản trước nên không vỡ; `hocba_gate_automation=True` để nhất quán automation.
  - Record rule `base.group_user` phủ direct dept manager + direct parent; nếu cây phòng ban sâu >1 cấp, quản lý phòng cha đọc đơn phòng cháu cần sudo ở controller (đã dùng `.sudo()` trong list endpoint).
  - Chạy test luôn kèm `MSYS_NO_PATHCONV=1` (thiếu → 0 test vẫn báo OK).

---

## Sau khi hoàn thành plan này

1. `superpowers:requesting-code-review` cho nhánh `feature/offboarding`.
2. `superpowers:verification-before-completion` — chạy full test + nạp module.
3. Viết **plan SPA** (form nộp đơn ở "Hồ sơ của tôi" + list quản lý "Đơn nghỉ việc") — brainstorm/plan riêng.
4. Cập nhật `docs/DB_TEST_DATA.md` nếu seed dữ liệu mẫu.
5. `superpowers:finishing-a-development-branch` — merge fast-forward về main.
