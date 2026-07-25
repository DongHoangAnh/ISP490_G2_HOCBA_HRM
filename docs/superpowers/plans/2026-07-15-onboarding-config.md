# Onboarding Config (bước động) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admin (HR Manager) cấu hình được các bước nhận việc/thử việc (template bước động, snapshot per-NV) thay cho 3 cổng + thử giảng hard-code.

**Architecture:** 3 model mới `hb.onboarding.template` / `.template.step` / `.step` (instance snapshot) trong `hocba_employees`; engine máy trạng thái trên instance tái dùng các helper automation sẵn có (`_hocba_make_official`, `_hocba_start_offboarding`, `_hocba_grant_default_assets`, `_hocba_notify_probation`); API JSON trong `hocba_hrm/controllers/main.py`; SPA React màn config + viết lại màn Onboarding + tab Thử việc.

**Tech Stack:** Odoo 19 (custom-addons), React 18 + Vite (frontend/), test TransactionCase chạy Docker local.

**Spec:** `docs/superpowers/specs/2026-07-15-onboarding-config-design.md`

**Lệnh test chuẩn (chạy từ repo root, Git Bash):**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

Kết quả cần: `0 failed, 0 error(s) of N tests` với N > 0. (Task controller đổi
`hocba_employees` thành `hocba_hrm,hocba_employees` và tag `/hocba_hrm`.)

**Quy ước chung:**
- Mọi model/field mới KHÔNG tiền tố `x_` (chỉ field mở rộng trên model Odoo
  core mới dùng `x_`, theo pattern `hocba.offboarding`).
- Chuỗi UI tiếng Việt, comment tiếng Việt (match codebase).
- Commit message tiếng Việt kiểu `feat(onboarding): ...`, kết bằng dòng
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## Task 1: Model template + bước mẫu (fields, constraints, ACL)

**Files:**
- Create: `custom-addons/hocba_employees/models/hb_onboarding_template.py`
- Modify: `custom-addons/hocba_employees/models/__init__.py` (thêm import)
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv`
- Create: `custom-addons/hocba_employees/tests/test_onboarding_template.py`
- Modify: `custom-addons/hocba_employees/tests/__init__.py`

- [ ] **Step 1: Viết test fail**

```python
# custom-addons/hocba_employees/tests/test_onboarding_template.py
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingTemplate(TransactionCase):
    """Template quy trình nhận việc: constraints + matching."""

    def _tpl(self, steps, **kw):
        vals = {'name': 'TPL Test', 'step_ids': [
            (0, 0, s) for s in steps]}
        vals.update(kw)
        return self.env['hb.onboarding.template'].create(vals)

    def test_template_requires_step(self):
        with self.assertRaises(ValidationError):
            self._tpl([])

    def test_eval_flags_only_on_evaluation(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task',
                        'pass_completes': True}])
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task',
                        'is_extension': True}])

    def test_auto_action_only_on_task(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'auto_action': 'grant_assets'}])

    def test_extension_must_follow_evaluation(self):
        # is_extension đứng đầu chuỗi → lỗi
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'is_extension': True, 'sequence': 1}])
        # is_extension sau task → lỗi
        with self.assertRaises(ValidationError):
            self._tpl([
                {'name': 'T1', 'step_type': 'task', 'sequence': 1},
                {'name': 'E1', 'step_type': 'evaluation',
                 'is_extension': True, 'sequence': 2}])
        # is_extension ngay sau evaluation → OK
        tpl = self._tpl([
            {'name': 'E1', 'step_type': 'evaluation', 'sequence': 1},
            {'name': 'E2', 'step_type': 'evaluation',
             'is_extension': True, 'sequence': 2}])
        self.assertEqual(len(tpl.step_ids), 2)

    def test_position_types_csv_validated(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task'}],
                      apply_position_types='staff,khong_ton_tai')
        tpl = self._tpl([{'name': 'T1', 'step_type': 'task'}],
                        apply_position_types='staff, manager')
        self.assertTrue(tpl)

    def test_due_days_non_negative(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'due_days': -3}])
```

- [ ] **Step 2: Thêm `from . import test_onboarding_template` vào `tests/__init__.py`, chạy test → FAIL** (model chưa tồn tại — lỗi KeyError `hb.onboarding.template`)

- [ ] **Step 3: Implement model**

```python
# custom-addons/hocba_employees/models/hb_onboarding_template.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Khớp selection x_position_type trên hr.employee
POSITION_TYPES = ('manager', 'staff', 'ctv', 'freelancer', 'advisor')


class HbOnboardingTemplate(models.Model):
    _name = 'hb.onboarding.template'
    _description = 'Template quy trình nhận việc / thử việc'
    _order = 'sequence, id'

    name = fields.Char(string='Tên quy trình', required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        string='Ưu tiên', default=10,
        help='NV khớp nhiều template → lấy template sequence nhỏ nhất.')
    apply_position_types = fields.Char(
        string='Loại vị trí áp dụng',
        help='CSV các giá trị x_position_type (vd "staff,manager"). '
             'Rỗng = mọi loại vị trí.')
    apply_work_form = fields.Selection(
        [('offline', 'Offline'), ('online', 'Online'), ('any', 'Tất cả')],
        string='Hình thức làm việc', default='any', required=True)
    apply_employee_type_ids = fields.Many2many(
        'hocba.employee.type', string='Loại nhân viên áp dụng',
        help='Rỗng = mọi loại nhân viên.')
    step_ids = fields.One2many(
        'hb.onboarding.template.step', 'template_id', string='Các bước')

    @api.constrains('step_ids')
    def _check_has_steps(self):
        for tpl in self:
            if not tpl.step_ids:
                raise ValidationError(_(
                    'Quy trình "%s" phải có ít nhất 1 bước.') % tpl.name)

    @api.constrains('apply_position_types')
    def _check_position_types(self):
        for tpl in self:
            if not tpl.apply_position_types:
                continue
            vals = [p.strip() for p in tpl.apply_position_types.split(',')
                    if p.strip()]
            bad = [v for v in vals if v not in POSITION_TYPES]
            if bad:
                raise ValidationError(_(
                    'Loại vị trí không hợp lệ: %(bad)s (chấp nhận: %(ok)s).')
                    % {'bad': ', '.join(bad), 'ok': ', '.join(POSITION_TYPES)})

    # ---- Matching -------------------------------------------------------
    def _matches(self, emp):
        """Template có áp dụng cho NV emp không (3 tiêu chí AND, rỗng = khớp)."""
        self.ensure_one()
        if self.apply_position_types:
            allowed = {p.strip() for p in self.apply_position_types.split(',')
                       if p.strip()}
            if (emp.x_position_type or '') not in allowed:
                return False
        if self.apply_work_form != 'any' \
                and emp.x_work_form != self.apply_work_form:
            return False
        if self.apply_employee_type_ids \
                and emp.x_employee_type_id not in self.apply_employee_type_ids:
            return False
        return True

    @api.model
    def _match_for_employee(self, emp):
        """Template active khớp emp, ưu tiên sequence nhỏ nhất; rỗng nếu không có."""
        for tpl in self.search([]):
            if tpl._matches(emp):
                return tpl
        return self.browse()


class HbOnboardingTemplateStep(models.Model):
    _name = 'hb.onboarding.template.step'
    _description = 'Bước mẫu trong template nhận việc'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'hb.onboarding.template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên bước', required=True)
    step_type = fields.Selection(
        [('task', 'Việc cần làm'), ('evaluation', 'Đánh giá')],
        string='Loại bước', default='task', required=True)
    due_days = fields.Integer(
        string='Hạn (+N ngày)', default=0,
        help='Hạn = ngày bắt đầu thử việc + N ngày. 0 = không hạn.')
    pass_completes = fields.Boolean(
        string='Đạt → lên chính thức',
        help='Chỉ bước Đánh giá: Đạt sẽ chuyển NV lên Chính thức, '
             'bỏ qua các bước sau.')
    is_extension = fields.Boolean(
        string='Bước gia hạn',
        help='Chỉ bước Đánh giá: chỉ kích hoạt khi bước đánh giá liền '
             'trước chọn "Gia hạn".')
    auto_action = fields.Selection(
        [('none', 'Không'), ('grant_assets', 'Tự cấp tài sản mặc định')],
        string='Automation', default='none', required=True,
        help='Chỉ bước Việc cần làm: bước mở → chạy automation rồi tự '
             'hoàn thành.')
    note = fields.Text(string='Hướng dẫn')

    @api.constrains('step_type', 'pass_completes', 'is_extension',
                    'auto_action', 'due_days', 'sequence')
    def _check_step_flags(self):
        for step in self:
            if step.due_days < 0:
                raise ValidationError(_('Hạn (+N ngày) không được âm.'))
            if step.step_type != 'evaluation' \
                    and (step.pass_completes or step.is_extension):
                raise ValidationError(_(
                    'Cờ "Đạt → lên chính thức" / "Bước gia hạn" chỉ dùng '
                    'cho bước Đánh giá.'))
            if step.step_type != 'task' and step.auto_action != 'none':
                raise ValidationError(_(
                    'Automation chỉ dùng cho bước Việc cần làm.'))
            if step.is_extension:
                sibs = step.template_id.step_ids.sorted(
                    lambda s: (s.sequence, s.id))
                idx = list(sibs).index(step)
                if idx == 0 or sibs[idx - 1].step_type != 'evaluation':
                    raise ValidationError(_(
                        'Bước gia hạn "%s" phải đứng ngay sau một bước '
                        'Đánh giá.') % step.name)
```

- [ ] **Step 4: Thêm import vào `models/__init__.py`** (sau `from . import hocba_offboarding`):

```python
from . import hb_onboarding_template
```

- [ ] **Step 5: Thêm ACL** vào `security/ir.model.access.csv` (cuối file). Template: HR user đọc, HR Manager full; user thường KHÔNG cần đọc template (SPA đọc qua sudo sau check). Giáo vụ đọc:

```csv
access_hb_onb_template_user,access.hb.onb.template.user,model_hb_onboarding_template,hr.group_hr_user,1,0,0,0
access_hb_onb_template_manager,access.hb.onb.template.manager,model_hb_onboarding_template,hr.group_hr_manager,1,1,1,1
access_hb_onb_template_giaovu,access.hb.onb.template.giaovu,model_hb_onboarding_template,hocba_employees.group_hocba_giaovu,1,0,0,0
access_hb_onb_template_step_user,access.hb.onb.template.step.user,model_hb_onboarding_template_step,hr.group_hr_user,1,0,0,0
access_hb_onb_template_step_manager,access.hb.onb.template.step.manager,model_hb_onboarding_template_step,hr.group_hr_manager,1,1,1,1
access_hb_onb_template_step_giaovu,access.hb.onb.template.step.giaovu,model_hb_onboarding_template_step,hocba_employees.group_hocba_giaovu,1,0,0,0
```

- [ ] **Step 6: Chạy test → PASS** (lệnh chuẩn ở đầu plan)

- [ ] **Step 7: Test matching (thêm vào test_onboarding_template.py)**

```python
    def test_matching(self):
        Tpl = self.env['hb.onboarding.template']
        t_teacher = self.env.ref(
            'hocba_employees.employee_type_teacher', raise_if_not_found=False)
        # Nếu XML id khác, tra cứu theo code:
        if not t_teacher:
            t_teacher = self.env['hocba.employee.type'].search(
                [('code', '=', 'teacher')], limit=1)
        tpl_gv = self._tpl([{'name': 'Thử giảng', 'step_type': 'evaluation'}],
                           name='TPL GV', sequence=5,
                           apply_employee_type_ids=[(6, 0, t_teacher.ids)])
        tpl_vp = self._tpl([{'name': 'ĐG', 'step_type': 'evaluation'}],
                           name='TPL VP', sequence=10,
                           apply_position_types='staff,manager',
                           apply_work_form='offline')
        emp_gv = self.env['hr.employee'].create({
            'name': 'GV Match', 'x_employee_type_id': t_teacher.id})
        emp_vp = self.env['hr.employee'].create({
            'name': 'VP Match', 'x_position_type': 'staff',
            'x_work_form': 'offline'})
        emp_none = self.env['hr.employee'].create({
            'name': 'Freelancer Online', 'x_position_type': 'freelancer',
            'x_work_form': 'online'})
        self.assertEqual(Tpl._match_for_employee(emp_gv), tpl_gv)
        self.assertEqual(Tpl._match_for_employee(emp_vp), tpl_vp)
        self.assertFalse(Tpl._match_for_employee(emp_none))
```

Lưu ý: kiểm tra XML id thật của loại NV "Giáo viên" trong
`custom-addons/hocba_employees/data/hocba_employee_type_data.xml` khi
implement — dùng đúng ref; fallback search theo `code='teacher'` như trên.

- [ ] **Step 8: Chạy test → PASS. Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): model template + bước mẫu quy trình nhận việc (constraints, matching)"
```

---

## Task 2: Model instance `hb.onboarding.step` + gán template (snapshot)

**Files:**
- Create: `custom-addons/hocba_employees/models/hb_onboarding_step.py`
- Modify: `custom-addons/hocba_employees/models/__init__.py`
- Modify: `custom-addons/hocba_employees/models/hr_employee.py` (2 field + assign)
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv`
- Create: `custom-addons/hocba_employees/tests/test_onboarding_step.py`
- Modify: `custom-addons/hocba_employees/tests/__init__.py`

- [ ] **Step 1: Viết test fail**

```python
# custom-addons/hocba_employees/tests/test_onboarding_step.py
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingAssign(TransactionCase):
    """Gán template → sinh instance snapshot, bước đầu open."""

    def setUp(self):
        super().setUp()
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL VP', 'apply_position_types': 'staff',
            'apply_work_form': 'offline',
            'step_ids': [
                (0, 0, {'name': 'ĐG tuần-2', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 14}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2}),
                (0, 0, {'name': 'ĐG tháng-1', 'step_type': 'evaluation',
                        'sequence': 3, 'due_days': 30,
                        'pass_completes': True}),
                (0, 0, {'name': 'ĐG tháng-2', 'step_type': 'evaluation',
                        'sequence': 4, 'due_days': 60, 'is_extension': True,
                        'pass_completes': True}),
            ]})
        self.start = fields.Date.today() - timedelta(days=5)

    def _mk_emp(self, **kw):
        vals = {'name': 'NV Onb', 'x_position_type': 'staff',
                'x_work_form': 'offline',
                'x_employment_status': 'probation',
                'x_probation_start': self.start}
        vals.update(kw)
        return self.env['hr.employee'].create(vals)

    def test_auto_assign_on_create(self):
        emp = self._mk_emp()
        steps = emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))
        self.assertEqual(emp.x_onboarding_template_id, self.tpl)
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0].state, 'open')
        self.assertEqual(steps.mapped('state'),
                         ['open', 'waiting', 'waiting', 'waiting'])
        # snapshot + hạn từ probation_start
        self.assertEqual(steps[0].due_date,
                         self.start + timedelta(days=14))
        self.assertTrue(steps[3].is_extension)

    def test_assign_when_probation_starts_later(self):
        # Tạo NV chưa có ngày thử việc → chưa gán; set ngày → gán
        emp = self._mk_emp(x_probation_start=False)
        self.assertFalse(emp.x_onboarding_step_ids)
        emp.write({'x_probation_start': self.start})
        self.assertEqual(len(emp.x_onboarding_step_ids), 4)

    def test_no_template_notifies_hr_not_blocking(self):
        emp = self._mk_emp(x_position_type='freelancer',
                           x_work_form='online')
        self.assertFalse(emp.x_onboarding_step_ids)
        notif = self.env['hb.notification'].sudo().search([
            ('category', '=', 'onboarding'),
            ('kind', '=', 'onboarding_no_template'),
            ('target_ref', '=', emp.id)])
        self.assertTrue(notif)

    def test_snapshot_immune_to_template_edit(self):
        emp = self._mk_emp()
        # sửa template sau khi gán → instance giữ nguyên
        self.tpl.step_ids[0].name = 'ĐỔI TÊN'
        self.tpl.step_ids[0].due_days = 99
        step0 = emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0]
        self.assertEqual(step0.name, 'ĐG tuần-2')
        self.assertEqual(step0.due_date, self.start + timedelta(days=14))

    def test_official_employee_not_assigned(self):
        emp = self._mk_emp(x_employment_status='official',
                           identification_id='017788990001',
                           x_pit_code='8017788990',
                           x_social_insurance_no='0117788990')
        self.assertFalse(emp.x_onboarding_step_ids)
```

Lưu ý BR-010: NV `official` cần `identification_id` đúng 12 số duy nhất +
MST + BHXH (như test cuối).

- [ ] **Step 2: Chạy test → FAIL** (field `x_onboarding_step_ids` chưa có)

- [ ] **Step 3: Implement instance model**

```python
# custom-addons/hocba_employees/models/hb_onboarding_step.py
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

STATE_SEL = [
    ('waiting', 'Chưa tới lượt'),
    ('open', 'Đang chờ'),
    ('done', 'Hoàn thành'),
    ('skipped', 'Bỏ qua'),
]
RESULT_SEL = [('pass', 'Đạt'), ('extend', 'Gia hạn'), ('fail', 'Không đạt')]


class HbOnboardingStep(models.Model):
    _name = 'hb.onboarding.step'
    _description = 'Bước nhận việc/thử việc của nhân viên (instance snapshot)'
    _order = 'sequence, id'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    template_id = fields.Many2one(
        'hb.onboarding.template', string='Từ template', ondelete='set null')
    # --- snapshot từ template.step (không đọc lại template) ---
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên bước', required=True)
    step_type = fields.Selection(
        [('task', 'Việc cần làm'), ('evaluation', 'Đánh giá')],
        default='task', required=True)
    pass_completes = fields.Boolean()
    is_extension = fields.Boolean()
    auto_action = fields.Selection(
        [('none', 'Không'), ('grant_assets', 'Tự cấp tài sản mặc định')],
        default='none', required=True)
    note = fields.Text(string='Hướng dẫn')
    # --- runtime ---
    due_date = fields.Date(string='Hạn')
    state = fields.Selection(
        STATE_SEL, default='waiting', required=True, index=True)
    result = fields.Selection(RESULT_SEL, string='Kết quả')
    extend_count = fields.Integer(
        string='Số lần gia hạn tại chỗ', default=0)
    done_date = fields.Date(string='Ngày hoàn thành')
    done_by_id = fields.Many2one('res.users', string='Người thực hiện')
    result_note = fields.Text(string='Nhận xét')

    # ------------------------------------------------------------------
    # Điều hướng chuỗi
    # ------------------------------------------------------------------
    def _chain(self):
        """Toàn bộ bước của NV, đúng thứ tự."""
        self.ensure_one()
        return self.employee_id.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def _next_waiting(self):
        """Bước 'waiting' đứng sau self gần nhất (rỗng nếu hết)."""
        self.ensure_one()
        chain = list(self._chain())
        idx = chain.index(self)
        for step in chain[idx + 1:]:
            if step.state == 'waiting':
                return step
        return self.browse()
```

(Engine `_open`/`action_*` làm ở Task 3-4 — Task này chỉ cần model + gán.)

- [ ] **Step 4: Thêm `from . import hb_onboarding_step` vào `models/__init__.py`**

- [ ] **Step 5: Thêm field + engine gán vào `hr_employee.py`**

Field (đặt cạnh `x_probation_start`, ~dòng 148):

```python
    x_onboarding_template_id = fields.Many2one(
        'hb.onboarding.template', string='Quy trình nhận việc',
        tracking=True)
    x_onboarding_step_ids = fields.One2many(
        'hb.onboarding.step', 'employee_id', string='Các bước nhận việc')
```

Method (đặt sau `_hocba_notify_probation`):

```python
    # ------------------------------------------------------------------
    # Onboarding bước động — gán template (snapshot)
    # Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
    # ------------------------------------------------------------------
    def _hocba_assign_onboarding(self, template=None):
        """Sinh instance bước từ template (tự match nếu không truyền).
        Không match → chuông cảnh báo HR, KHÔNG chặn lưu NV."""
        self.ensure_one()
        tpl = template or self.env['hb.onboarding.template'].sudo(
            )._match_for_employee(self)
        if not tpl:
            self._hocba_notify_probation(
                'onboarding_no_template', 'warning',
                _('Chưa có quy trình nhận việc phù hợp: %s') % self.name,
                body=_('Tạo template khớp hoặc gán tay trong màn Cấu hình '
                       'nhận việc.'),
                dedup_key='onb_no_tpl:%s' % self.id)
            return self.env['hb.onboarding.step']
        Step = self.env['hb.onboarding.step'].sudo()
        # Đổi template: bỏ bước chưa chạy, giữ bước done/skipped làm lịch sử
        self.x_onboarding_step_ids.filtered(
            lambda s: s.state in ('waiting', 'open')).sudo().unlink()
        start = self.x_probation_start
        steps = Step.create([{
            'employee_id': self.id,
            'template_id': tpl.id,
            'sequence': ts.sequence,
            'name': ts.name,
            'step_type': ts.step_type,
            'pass_completes': ts.pass_completes,
            'is_extension': ts.is_extension,
            'auto_action': ts.auto_action,
            'note': ts.note,
            'due_date': (start + timedelta(days=ts.due_days)
                         if start and ts.due_days else False),
        } for ts in tpl.step_ids.sorted(lambda s: (s.sequence, s.id))])
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})
        if steps:
            steps.sorted(lambda s: (s.sequence, s.id))[0]._open()
        return steps

    def _hocba_maybe_assign_onboarding(self):
        """Gán tự động khi NV thử việc có ngày bắt đầu mà chưa có bước."""
        for emp in self:
            if (emp.x_employment_status == 'probation'
                    and emp.x_probation_start
                    and not emp.x_onboarding_step_ids):
                emp._hocba_assign_onboarding()
```

Trigger trong `create` và `write` của `hr.employee` (thêm cuối
`write()` hiện có, trước `return res` — và trong `create` sau khi super):

```python
        # (trong write, trước return res)
        if not self.env.context.get('hocba_onb_assigning') and any(
                f in vals for f in ('x_employment_status',
                                    'x_probation_start')):
            self._hocba_maybe_assign_onboarding()
```

`hr.employee` hiện KHÔNG override `create` trong hocba_employees? Kiểm tra khi
implement: grep `def create` trong `hr_employee.py`. Nếu có → thêm gọi
`_hocba_maybe_assign_onboarding()` sau super; nếu chưa có → thêm:

```python
    @api.model_create_multi
    def create(self, vals_list):
        emps = super().create(vals_list)
        emps._hocba_maybe_assign_onboarding()
        return emps
```

Tạm thời Task này `_open()` chỉ cần tối thiểu để test pass (Task 3 mở rộng):

```python
    # (trong hb_onboarding_step.py)
    def _open(self):
        self.ensure_one()
        self.write({'state': 'open'})
```

- [ ] **Step 6: ACL instance** (thêm `ir.model.access.csv`) — user thường đọc
record của mình qua sudo controller nên chỉ cần nhóm HR/giáo vụ + base read:

```csv
access_hb_onb_step_user,access.hb.onb.step.user,model_hb_onboarding_step,base.group_user,1,0,0,0
access_hb_onb_step_hr,access.hb.onb.step.hr,model_hb_onboarding_step,hr.group_hr_user,1,1,1,0
access_hb_onb_step_manager,access.hb.onb.step.manager,model_hb_onboarding_step,hr.group_hr_manager,1,1,1,1
access_hb_onb_step_giaovu,access.hb.onb.step.giaovu,model_hb_onboarding_step,hocba_employees.group_hocba_giaovu,1,1,0,0
```

- [ ] **Step 7: Thêm `from . import test_onboarding_step` vào tests/__init__.py; chạy test → PASS. Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): instance hb.onboarding.step + gán template snapshot tự động"
```

---

## Task 3: Engine — hoàn thành task + auto_action grant_assets

**Files:**
- Modify: `custom-addons/hocba_employees/models/hb_onboarding_step.py`
- Modify: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Viết test fail (thêm class vào test_onboarding_step.py)**

```python
@tagged('post_install', '-at_install')
class TestOnboardingEngine(TransactionCase):
    """Máy trạng thái: complete task, auto_action, evaluate đủ nhánh."""

    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.mgr_user = self.env['res.users'].create({
            'name': 'OMgr', 'login': 'onb_mgr', 'group_ids': gu})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'OMgr Emp', 'identification_id': '017788990101',
            'user_id': self.mgr_user.id})
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL VP', 'apply_position_types': 'staff',
            'apply_work_form': 'offline',
            'step_ids': [
                (0, 0, {'name': 'ĐG tuần-2', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 14}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2, 'auto_action': 'grant_assets'}),
                (0, 0, {'name': 'ĐG tháng-1', 'step_type': 'evaluation',
                        'sequence': 3, 'due_days': 30,
                        'pass_completes': True}),
                (0, 0, {'name': 'ĐG tháng-2', 'step_type': 'evaluation',
                        'sequence': 4, 'due_days': 60, 'is_extension': True,
                        'pass_completes': True}),
            ]})
        # BR-010: đủ CCCD/MST/BHXH để pass lên official không vướng
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Engine', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'parent_id': self.mgr_emp.id,
            'identification_id': '017788990102',
            'x_pit_code': '8017788991',
            'x_social_insurance_no': '0117788991',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today() - timedelta(days=10)})

    def _steps(self):
        return self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def test_eval_pass_opens_next_and_auto_grants(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        s = self._steps()
        self.assertEqual(s[0].state, 'done')
        self.assertEqual(s[0].result, 'pass')
        # bước task auto_action: tự grant + tự done → tháng-1 mở luôn
        self.assertEqual(s[1].state, 'done')
        self.assertTrue(self.emp.sudo().x_asset_ids)  # F-006 đã cấp
        self.assertEqual(s[2].state, 'open')

    def test_eval_pass_completes_goes_official_skips_rest(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('pass')
        self.assertEqual(self.emp.x_employment_status, 'official')
        self.assertTrue(self.emp.x_official_date)
        self.assertEqual(self._steps()[3].state, 'skipped')
        # promotion history source probation được ghi
        hist = self.env['hr.promotion.history'].sudo().search([
            ('employee_id', '=', self.emp.id),
            ('x_change_type', '=', 'probation')])
        self.assertTrue(hist)

    def test_eval_extend_to_extension_step(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('extend')
        s = self._steps()
        self.assertEqual(s[2].state, 'done')
        self.assertEqual(s[2].result, 'extend')
        self.assertEqual(s[3].state, 'open')  # bước gia hạn kích hoạt
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_eval_extend_in_place_when_no_extension_next(self):
        # tuần-2 extend → bước kế là task (không phải is_extension)
        # → giữ open, tăng extend_count (hành vi cổng 2w cũ)
        s = self._steps()
        s[0].action_evaluate('extend')
        s = self._steps()
        self.assertEqual(s[0].state, 'open')
        self.assertEqual(s[0].extend_count, 1)
        self.assertEqual(s[1].state, 'waiting')
        # tái đánh giá pass sau đó vẫn chạy tiếp
        s[0].action_evaluate('pass')
        self.assertEqual(self._steps()[2].state, 'open')

    def test_eval_fail_starts_offboarding_and_skips(self):
        s = self._steps()
        with self.assertRaises(ValidationError):
            s[0].action_evaluate('fail')  # fail phải có note
        s[0].action_evaluate('fail', note='Không đáp ứng')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        offb = self.env['hocba.offboarding'].sudo().search([
            ('employee_id', '=', self.emp.id),
            ('source', '=', 'probation')])
        self.assertTrue(offb)
        s = self._steps()
        self.assertTrue(all(x.state == 'skipped' for x in s[1:]))

    def test_cannot_act_when_not_open(self):
        s = self._steps()
        with self.assertRaises(ValidationError):
            s[2].action_evaluate('pass')  # đang waiting
        with self.assertRaises(ValidationError):
            s[1].action_complete()        # task đang waiting

    def test_pass_after_extension_skips_extension(self):
        # tháng-1 pass (không qua extend) → tháng-2 is_extension bị skip
        # (đã cover trong test_eval_pass_completes... vì pass_completes)
        # Thêm case: pass thường trước is_extension → skip is_extension
        tpl2 = self.env['hb.onboarding.template'].create({
            'name': 'TPL 2', 'sequence': 1,
            'apply_position_types': 'ctv',
            'step_ids': [
                (0, 0, {'name': 'E1', 'step_type': 'evaluation',
                        'sequence': 1}),
                (0, 0, {'name': 'E2-ext', 'step_type': 'evaluation',
                        'sequence': 2, 'is_extension': True}),
                (0, 0, {'name': 'T-cuối', 'step_type': 'task',
                        'sequence': 3}),
            ]})
        emp2 = self.env['hr.employee'].create({
            'name': 'NV CTV', 'x_position_type': 'ctv',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today()})
        s = emp2.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        s[0].action_evaluate('pass')
        s = emp2.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(s[1].state, 'skipped')   # ext bị bỏ
        self.assertEqual(s[2].state, 'open')

    def test_chain_done_without_official_notifies(self):
        # template chỉ có task → xong chuỗi vẫn probation → chuông HR
        tpl3 = self.env['hb.onboarding.template'].create({
            'name': 'TPL GV mini', 'sequence': 1,
            'apply_position_types': 'advisor',
            'step_ids': [(0, 0, {'name': 'Ký HĐ', 'step_type': 'task',
                                 'sequence': 1})]})
        emp3 = self.env['hr.employee'].create({
            'name': 'NV Advisor', 'x_position_type': 'advisor',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today()})
        emp3.x_onboarding_step_ids.action_complete()
        self.assertEqual(emp3.x_employment_status, 'probation')
        notif = self.env['hb.notification'].sudo().search([
            ('kind', '=', 'onboarding_chain_done'),
            ('target_ref', '=', emp3.id)])
        self.assertTrue(notif)

    def test_skip_auto_trigger_records_without_side_effects(self):
        self.emp.sudo().write({'x_skip_auto_trigger': True})
        s = self._steps()
        s[0].action_evaluate('pass')
        # asset KHÔNG tự cấp, nhưng chuỗi vẫn tiến
        self.assertFalse(self.emp.sudo().x_asset_ids)
        self._steps()[2].action_evaluate('pass')
        # KHÔNG tự lên official
        self.assertEqual(self.emp.x_employment_status, 'probation')
```

Lưu ý: `x_skip_auto_trigger` là field sẵn có trên hr.employee — kiểm tra tên
chính xác bằng grep khi implement.

- [ ] **Step 2: Chạy test → FAIL** (`action_evaluate` chưa có)

- [ ] **Step 3: Implement engine (thay `_open` tối thiểu + thêm actions)**

```python
    # (trong hb_onboarding_step.py — thay _open cũ, thêm mới)
    def _skip_auto(self):
        return self.employee_id.sudo().x_skip_auto_trigger

    def _open(self):
        """Mở bước; task có auto_action → chạy automation rồi tự done."""
        self.ensure_one()
        self.write({'state': 'open'})
        if self.step_type == 'task' and self.auto_action == 'grant_assets':
            if not self._skip_auto():
                self.employee_id._hocba_grant_default_assets()
            self.write({
                'state': 'done',
                'done_date': fields.Date.context_today(self),
                'done_by_id': self.env.user.id,
            })
            self._advance()

    def _advance(self):
        """Sau khi self done/skipped: mở bước kế; skip bước gia hạn nếu
        self pass; hết chuỗi mà chưa official → chuông HR chờ quyết định."""
        self.ensure_one()
        nxt = self._next_waiting()
        if not nxt:
            emp = self.employee_id
            if (emp.x_employment_status == 'probation'
                    and not self._skip_auto()):
                emp._hocba_notify_probation(
                    'onboarding_chain_done', 'info',
                    _('Hoàn tất quy trình nhận việc: %s') % emp.name,
                    body=_('Mọi bước đã xong — chờ HR quyết định trạng '
                           'thái nhân sự.'),
                    dedup_key='onb_chain_done:%s' % emp.id)
            return
        if nxt.is_extension and self.result != 'extend':
            nxt.write({'state': 'skipped'})
            nxt._advance()
        else:
            nxt._open()

    def _ensure_open(self, want_type):
        self.ensure_one()
        if self.state != 'open' or self.step_type != want_type:
            raise ValidationError(_(
                'Bước "%s" không ở trạng thái xử lý được.') % self.name)

    def action_complete(self, note=None):
        """Hoàn thành bước task (tay)."""
        self.ensure_one()
        self._ensure_open('task')
        vals = {'state': 'done',
                'done_date': fields.Date.context_today(self),
                'done_by_id': self.env.user.id}
        if note:
            vals['result_note'] = note
        self.write(vals)
        self.employee_id.message_post(body=_(
            '✅ Bước nhận việc "%s" hoàn thành.') % self.name)
        self._advance()

    def action_evaluate(self, result, note=None, eval_date=None):
        """Ghi kết quả bước evaluation: pass / extend / fail."""
        self.ensure_one()
        self._ensure_open('evaluation')
        if result not in ('pass', 'extend', 'fail'):
            raise ValidationError(_('Kết quả không hợp lệ.'))
        if result == 'fail' and not (note or '').strip():
            raise ValidationError(_(
                'Cần nhập nhận xét khi kết quả Không đạt.'))
        today = fields.Date.context_today(self)
        done_vals = {'done_date': eval_date or today,
                     'done_by_id': self.env.user.id}
        if note:
            done_vals['result_note'] = note
        emp = self.employee_id

        if result == 'extend':
            nxt = self._next_waiting()
            if nxt and nxt.is_extension:
                # hành vi cổng tháng-1 cũ: done + mở bước gia hạn
                self.write(dict(done_vals, state='done', result='extend'))
                self._advance()
            else:
                # hành vi cổng 2w/2m cũ: giữ open, hẹn tái đánh giá
                self.write(dict(done_vals,
                                extend_count=self.extend_count + 1))
            if not self._skip_auto():
                emp._hocba_notify_probation(
                    'probation_extend', 'warning',
                    _('Gia hạn thử việc: %s') % emp.name,
                    body=_('Bước "%s" gia hạn.') % self.name,
                    include_employee=True)
            emp.message_post(body=_(
                '⏳ Bước "%s" GIA HẠN — tiếp tục thử việc.') % self.name)
            return

        self.write(dict(done_vals, state='done', result=result))
        if result == 'fail':
            self._chain().filtered(
                lambda s: s.state in ('waiting', 'open')).write(
                    {'state': 'skipped'})
            if not self._skip_auto():
                emp._hocba_start_offboarding(self.name)
            return
        # result == 'pass'
        if self.pass_completes and not self._skip_auto():
            self._chain().filtered(
                lambda s: s.state == 'waiting').write({'state': 'skipped'})
            emp._hocba_make_official(self.name)
            return
        emp.message_post(body=_('✅ Bước "%s" ĐẠT.') % self.name)
        self._advance()
```

Chú ý import trong file: `from odoo.exceptions import AccessError, ValidationError`
(AccessError dùng ở Task 4).

- [ ] **Step 4: Chạy test → PASS. Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): engine máy trạng thái bước động (task/evaluate, extend 2 nghĩa, automation)"
```

---

## Task 4: Quyền thao tác bước (`_check_can_act`)

**Files:**
- Modify: `custom-addons/hocba_employees/models/hb_onboarding_step.py`
- Modify: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Test fail (thêm vào TestOnboardingEngine)**

```python
    def test_permission_evaluate(self):
        stranger = self.env['res.users'].create({
            'name': 'Stranger', 'login': 'onb_stranger',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        s = self._steps()
        from odoo.exceptions import AccessError
        with self.assertRaises(AccessError):
            s[0].with_user(stranger).action_evaluate('pass')
        # Quản lý trực tiếp thì được
        s[0].with_user(self.mgr_user).action_evaluate('pass')
        self.assertEqual(self._steps()[0].result, 'pass')
```

- [ ] **Step 2: Chạy → FAIL** (stranger không bị chặn — ACL base.group_user chỉ read, write bị chặn bởi ACL nên có thể FAIL kiểu khác; assert với_user mgr_user có thể fail vì mgr không có ACL write). **Đúng chủ đích**: action gọi qua sudo nội bộ sau check.

- [ ] **Step 3: Implement — check quyền rồi sudo ghi (pattern self-service)**

Thêm đầu `action_complete` và `action_evaluate` (ngay sau `ensure_one`):

```python
        self._check_can_act()
```

Và method:

```python
    def _check_can_act(self):
        """HR Manager / quản lý trực tiếp / trưởng phòng ban NV; bước task
        cho thêm Giáo vụ với giáo viên. Sau check, thao tác ghi chạy sudo."""
        self.ensure_one()
        if self.env.su:
            return
        user = self.env.user
        emp = self.employee_id.sudo()
        if user.has_group('hr.group_hr_manager'):
            return
        if emp.parent_id and emp.parent_id.user_id == user:
            return
        if emp._hocba_user_manages_dept(user):
            return
        if (self.step_type == 'task'
                and user.has_group('hocba_employees.group_hocba_giaovu')
                and emp.x_employee_type_id.code == 'teacher'):
            return
        raise AccessError(_(
            'Bạn không có quyền xử lý bước nhận việc của nhân viên này.'))
```

Đồng thời trong `action_complete`/`action_evaluate`, mọi `self.write(...)` /
`._chain().filtered(...).write(...)` đổi thành `self.sudo().write(...)` /
`.sudo().write(...)` (check quyền đã đứng trước; giữ `self.env.user.id` cho
`done_by_id` — lấy TRƯỚC khi sudo, biến cục bộ `uid = self.env.user.id`).
Tương tự `_open`/`_advance` chạy nội bộ → gọi từ record sudo sẵn.

- [ ] **Step 4: Chạy test → PASS (toàn bộ file + suite hocba_employees). Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): quyền thao tác bước theo vai trò (check rồi sudo)"
```

---

## Task 5: Seed 2 template mặc định + đổi template tay

**Files:**
- Create: `custom-addons/hocba_employees/data/hb_onboarding_template_data.xml`
- Modify: `custom-addons/hocba_employees/__manifest__.py` (thêm data file)
- Modify: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Test fail (thêm class)**

```python
@tagged('post_install', '-at_install')
class TestOnboardingSeed(TransactionCase):
    def test_seed_templates_exist(self):
        gv = self.env.ref('hocba_employees.onb_template_teacher')
        vp = self.env.ref('hocba_employees.onb_template_office')
        self.assertEqual(len(gv.step_ids), 2)
        self.assertEqual(len(vp.step_ids), 4)
        steps = vp.step_ids.sorted(lambda s: (s.sequence, s.id))
        self.assertEqual(steps.mapped('step_type'),
                         ['evaluation', 'task', 'evaluation', 'evaluation'])
        self.assertTrue(steps[2].pass_completes)
        self.assertTrue(steps[3].is_extension and steps[3].pass_completes)
        self.assertEqual(steps[1].auto_action, 'grant_assets')
        # thử giảng KHÔNG pass_completes
        gv_steps = gv.step_ids.sorted(lambda s: (s.sequence, s.id))
        self.assertFalse(gv_steps[0].pass_completes)

    def test_reassign_template_manual(self):
        vp = self.env.ref('hocba_employees.onb_template_office')
        gv = self.env.ref('hocba_employees.onb_template_teacher')
        emp = self.env['hr.employee'].create({
            'name': 'NV Reassign', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today()})
        self.assertEqual(emp.x_onboarding_template_id, vp)
        emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0].action_evaluate('pass')
        done_before = len(emp.x_onboarding_step_ids.filtered(
            lambda s: s.state == 'done'))
        emp._hocba_assign_onboarding(template=gv)
        self.assertEqual(emp.x_onboarding_template_id, gv)
        # bước done giữ lại làm lịch sử, bước mới nối vào
        self.assertEqual(len(emp.x_onboarding_step_ids.filtered(
            lambda s: s.state == 'done')), done_before)
        news = emp.x_onboarding_step_ids.filtered(
            lambda s: s.template_id == gv)
        self.assertEqual(len(news), 2)
        self.assertEqual(news.sorted(
            lambda s: (s.sequence, s.id))[0].state, 'open')
```

Lưu ý reassign: bước mới sinh với sequence của template MỚI có thể nhỏ hơn
sequence bước done cũ → khi sinh, offset sequence mới =
`max(sequence bước cũ còn giữ) + sequence template step` để chuỗi nối đúng.
Sửa `_hocba_assign_onboarding`: tính `base = max(existing.mapped('sequence') or [0])`
rồi `'sequence': base + ts.sequence`.

- [ ] **Step 2: Chạy → FAIL** (xml id chưa có)

- [ ] **Step 3: Tạo data XML**

```xml
<?xml version="1.0" encoding="utf-8"?>
<!-- Seed 2 template mặc định tái hiện luồng thử việc hiện hành.
     noupdate=1: admin sửa được trong app, upgrade không đè. -->
<odoo noupdate="1">
  <record id="onb_template_teacher" model="hb.onboarding.template">
    <field name="name">Thử việc Giáo viên</field>
    <field name="sequence">5</field>
    <field name="apply_employee_type_ids"
           eval="[(6, 0, [ref('hocba_employees.employee_type_teacher')])]"/>
  </record>
  <record id="onb_tpl_gv_step1" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_teacher"/>
    <field name="sequence">1</field>
    <field name="name">Thử giảng</field>
    <field name="step_type">evaluation</field>
  </record>
  <record id="onb_tpl_gv_step2" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_teacher"/>
    <field name="sequence">2</field>
    <field name="name">Ký hợp đồng thỉnh giảng</field>
    <field name="step_type">task</field>
  </record>

  <record id="onb_template_office" model="hb.onboarding.template">
    <field name="name">Thử việc Nhân viên văn phòng</field>
    <field name="sequence">10</field>
    <field name="apply_position_types">staff,manager</field>
    <field name="apply_work_form">offline</field>
  </record>
  <record id="onb_tpl_vp_step1" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">1</field>
    <field name="name">Đánh giá tuần-2</field>
    <field name="step_type">evaluation</field>
    <field name="due_days">14</field>
  </record>
  <record id="onb_tpl_vp_step2" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">2</field>
    <field name="name">Cấp thiết bị làm việc</field>
    <field name="step_type">task</field>
    <field name="auto_action">grant_assets</field>
  </record>
  <record id="onb_tpl_vp_step3" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">3</field>
    <field name="name">Đánh giá tháng-1</field>
    <field name="step_type">evaluation</field>
    <field name="due_days">30</field>
    <field name="pass_completes" eval="True"/>
  </record>
  <record id="onb_tpl_vp_step4" model="hb.onboarding.template.step">
    <field name="template_id" ref="onb_template_office"/>
    <field name="sequence">4</field>
    <field name="name">Đánh giá tháng-2</field>
    <field name="step_type">evaluation</field>
    <field name="due_days">60</field>
    <field name="is_extension" eval="True"/>
    <field name="pass_completes" eval="True"/>
  </record>
</odoo>
```

**QUAN TRỌNG**: xml id `employee_type_teacher` — xác minh id thật trong
`data/hocba_employee_type_data.xml` trước khi dùng; nếu khác thì sửa ref.
Constraint `_check_has_steps` sẽ fail khi record template load TRƯỚC step →
data XML load tuần tự trong 1 file thì constraint chạy theo từng record.
Giải pháp: constraint `@api.constrains('step_ids')` chỉ fire khi write
step_ids — create template không kèm step KHÔNG fire constraint này trong
Odoo? (constrains fire on create với field trong vals). Nếu install fail vì
constraint → chuyển check "≥1 bước" thành constraint trên bước cuối cùng bị
unlink + kiểm tra ở API/UI thay vì ORM, hoặc dùng
`_check_has_steps` bỏ qua khi `self.env.context.get('install_mode')`.
Quyết định khi chạy thật — ưu tiên `install_mode` guard (1 dòng).

Manifest: thêm `'data/hb_onboarding_template_data.xml'` vào list `data`
(sau `'data/hocba_employee_type_data.xml'` để ref teacher đã tồn tại).

- [ ] **Step 4: Chạy test → PASS (cả suite). Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): seed 2 template mặc định + đổi template tay nối chuỗi"
```

---

## Task 6: Cron nhắc hạn + timeline HTML từ bước động; gỡ máy cổng cũ

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py`
- Modify: `custom-addons/hocba_employees/tests/test_probation_notify.py` (viết lại)
- Modify: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

Đây là task "phẫu thuật" lớn nhất — làm theo thứ tự nhỏ:

- [ ] **Step 1: Viết lại `test_probation_notify.py` theo bước động** (giữ tên
file/class để suite ổn định). setUp tạo template VP như TestOnboardingEngine
(hoặc dùng seed `onb_template_office` + NV staff/offline). 4 test:
cron dedup (bước open có due_date <= today+2 → chuông `probation_eval`
dedup `onb_step:{id}:{due}`), fail notify (action_evaluate fail → exiting +
chuông danger), pass notify (2 lần pass → official + chuông success,
NV nhận bản 'profile'), extend notify (extend → chuông warning). Code test
mirror bản cũ nhưng thao tác qua `action_evaluate` thay vì write field cổng.

```python
# thay body test cũ — ví dụ test cron mới:
    def test_cron_reminder_notifies_manager_with_dedup(self):
        Emp = self.env['hr.employee']
        Emp._cron_probation_eval_reminders()
        first = self._notifs('probation_eval').filtered(
            lambda n: n.recipient_id == self.mgr_user)
        self.assertEqual(len(first), 1)
        Emp._cron_probation_eval_reminders()
        again = self._notifs('probation_eval').filtered(
            lambda n: n.recipient_id == self.mgr_user)
        self.assertEqual(len(again), 1)
```

(setUp: NV probation start = today−13 → bước tuần-2 due = start+14 = ngày mai
→ trong cửa sổ nhắc.)

- [ ] **Step 2: Chạy → FAIL** (cron cũ vẫn quét field cũ; NV giờ có steps)

- [ ] **Step 3: Viết lại cron trong hr_employee.py** (thay toàn bộ body
`_cron_probation_eval_reminders`, giữ tên method vì `ir_cron_data.xml` trỏ
tới):

```python
    @api.model
    def _cron_probation_eval_reminders(self):
        """CRON 7:00 SA: nhắc bước nhận việc sắp đến hạn trong 2 ngày."""
        soon = fields.Date.today() + timedelta(days=2)
        steps = self.env['hb.onboarding.step'].sudo().search([
            ('state', '=', 'open'),
            ('due_date', '!=', False),
            ('due_date', '<=', soon),
            ('employee_id.x_employment_status', '=', 'probation'),
        ])
        for step in steps:
            emp = step.employee_id
            emp._hocba_gate_activity(
                _('Sắp đến hạn bước "%(step)s": %(emp)s') % {
                    'step': step.name, 'emp': emp.name},
                step.due_date, emp.parent_id.user_id or None)
            emp._hocba_notify_probation(
                'probation_eval', 'warning',
                _('Sắp đến hạn bước "%(step)s": %(emp)s') % {
                    'step': step.name, 'emp': emp.name},
                body=_('Hạn: %s') % step.due_date,
                dedup_key='onb_step:%s:%s' % (step.id, step.due_date))
```

- [ ] **Step 4: Viết lại `_compute_probation_timeline_html`** — depends đổi
thành `@api.depends('x_probation_start', 'x_onboarding_step_ids.state',
'x_onboarding_step_ids.result', 'x_official_date')`; steps build từ:

```python
            marks = {'pass': 'done', 'fail': 'fail', 'extend': 'extend'}
            steps = [(_('Thử việc'),
                      'done' if emp.x_probation_start else 'pending',
                      fmt(emp.x_probation_start))]
            for s in emp.x_onboarding_step_ids.sorted(
                    lambda x: (x.sequence, x.id)):
                if s.state == 'done':
                    st = marks.get(s.result, 'done')
                elif s.state == 'skipped':
                    continue
                else:
                    st = 'pending'
                sub = fmt(s.done_date) or (
                    s.due_date and _('hạn %s') % fmt(s.due_date) or '')
                steps.append((s.name, st, sub))
            steps.append((_('Chính thức'),
                          'done' if emp.x_official_date else 'pending',
                          fmt(emp.x_official_date)))
```

(giữ nguyên phần render parts/HTML phía dưới).

- [ ] **Step 5: Gỡ máy cổng cũ khỏi `hr_employee.py`:**
  - Xoá: `_compute_eval_dues`, `_check_eval_due_ranges`, `_check_gate_rules`,
    `_hocba_aut_001`, `_hocba_aut_001m`, `_hocba_aut_002`.
  - Trong `write()`: xoá khối check `GATE_EDIT_FIELDS` (quyền chuyển sang
    step `_check_can_act`), khối `track_gates`/`pre` và vòng `if track_gates`.
    GIỮ: check archive tài sản, check `x_employment_status == 'official'`
    (F-001), khối `track_trial`? — **Thử giảng cũ**: xoá luôn khối
    `track_trial` + `_check_trial_lesson` giữ nguyên (constraint field cũ vô
    hại — không còn ai ghi; QUYẾT ĐỊNH: giữ constraint, xoá automation).
  - GIỮ nguyên: field definitions `x_eval_*`, `x_trial_*`,
    `x_equip_grant_date` (cột DB cho migration/đối chiếu — bỏ compute due:
    3 field `x_eval_*_due` đổi từ compute sang Date thường? KHÔNG —
    xoá compute thì field compute mất giá trị. Đơn giản: giữ
    `_compute_eval_dues` NGUYÊN TRẠNG (vô hại, chỉ tính due). Chỉ xoá
    constraint + automation + quyền.)
  - GIỮ: `GATE_RESULT_FIELDS`/`GATE_EDIT_FIELDS` constants có thể xoá nếu
    không còn tham chiếu (grep trước khi xoá — controller cũ dùng?).
  - `views/hr_employee_views.xml`: grep `x_eval_` / `x_trial_` — bỏ các field
    cổng khỏi form (giữ timeline html). Notebook page thử việc để lại
    one2many `x_onboarding_step_ids` dạng list readonly (name, step_type,
    state, result, due_date, done_date).

- [ ] **Step 6: Chạy toàn suite hocba_employees → sửa test cũ nào còn ghi
field cổng** (`test_offboarding.py` có thể dùng gate fail để tạo offboarding
— grep `x_eval` trong tests/, đổi sang `action_evaluate`). PASS toàn bộ.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): cron + timeline theo bước động; gỡ automation cổng cứng cũ"
```

---

## Task 7: Migration dữ liệu cổng cũ → bước động

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py` (method migrate)
- Create: `custom-addons/hocba_employees/migrations/19.0.2.0.0/post-migrate.py`
- Modify: `custom-addons/hocba_employees/__manifest__.py` (version 19.0.2.0.0)
- Modify: `custom-addons/hocba_employees/tests/test_onboarding_step.py`

- [ ] **Step 1: Test fail (thêm class)**

```python
@tagged('post_install', '-at_install')
class TestOnboardingMigration(TransactionCase):
    def test_migrate_legacy_group_b(self):
        start = fields.Date.today() - timedelta(days=40)
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'Legacy B', 'x_position_type': 'staff',
                'x_work_form': 'offline',
                'x_employment_status': 'probation',
                'x_probation_start': start})
        # giả lập dữ liệu cũ: tuần-2 pass, thiết bị đã cấp, tháng-1 extend
        emp.with_context(hocba_gate_automation=True).sudo().write({
            'x_eval_2w_result': 'pass',
            'x_eval_2w_date': start + timedelta(days=14),
            'x_equip_grant_date': start + timedelta(days=15),
            'x_eval_1m_result': 'extend',
            'x_eval_1m_date': start + timedelta(days=30),
        })
        emp.x_onboarding_step_ids.unlink()  # chắc chắn sạch
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        s = emp.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(len(s), 4)
        self.assertEqual(
            [(x.name, x.state) for x in s[:3]],
            [('Đánh giá tuần-2', 'done'), ('Cấp thiết bị làm việc', 'done'),
             ('Đánh giá tháng-1', 'done')])
        self.assertEqual(s[2].result, 'extend')
        self.assertEqual(s[3].state, 'open')   # cổng tháng-2 đang chờ
        # idempotent
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        self.assertEqual(len(emp.x_onboarding_step_ids), 4)

    def test_migrate_legacy_teacher_trial_pass(self):
        t_teacher = self.env['hocba.employee.type'].search(
            [('code', '=', 'teacher')], limit=1)
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'Legacy GV', 'x_employee_type_id': t_teacher.id,
                'x_employment_status': 'probation',
                'x_probation_start': fields.Date.today() - timedelta(days=9)})
        emp.sudo().write({
            'x_trial_lesson_result': 'pass',
            'x_trial_lesson_date': fields.Date.today() - timedelta(days=2),
            'x_trial_score_method': 8, 'x_trial_score_content': 9})
        emp.x_onboarding_step_ids.unlink()
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        s = emp.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(s[0].result, 'pass')
        self.assertIn('8', s[0].result_note)  # điểm cũ ghi vào note
        self.assertEqual(s[1].state, 'open')  # Ký HĐ thỉnh giảng chờ
```

Context `hocba_no_onb_assign` — thêm guard trong
`_hocba_maybe_assign_onboarding`:
`if self.env.context.get('hocba_no_onb_assign'): return`
(cần cho migration: NV cũ không được auto-assign trước khi map).

- [ ] **Step 2: Chạy → FAIL**

- [ ] **Step 3: Implement `_hocba_migrate_legacy_gates` trên hr.employee**

```python
    @api.model
    def _hocba_migrate_legacy_gates(self):
        """Một lần: map field cổng cũ (2w/1m/2m, thử giảng, thiết bị) →
        instance hb.onboarding.step. Idempotent: bỏ NV đã có bước."""
        Step = self.env['hb.onboarding.step'].sudo()
        tpl_vp = self.env.ref('hocba_employees.onb_template_office',
                              raise_if_not_found=False)
        tpl_gv = self.env.ref('hocba_employees.onb_template_teacher',
                              raise_if_not_found=False)
        emps = self.sudo().with_context(active_test=False).search([
            ('x_probation_start', '!=', False),
            ('x_onboarding_step_ids', '=', False)])
        for emp in emps:
            is_b = (emp.x_position_type in ('staff', 'manager')
                    and emp.x_work_form == 'offline')
            if is_b and tpl_vp:
                emp._migrate_legacy_group_b(Step, tpl_vp)
            elif not is_b and emp.x_trial_lesson_result \
                    and emp.x_trial_lesson_result != 'draft' and tpl_gv:
                emp._migrate_legacy_teacher(Step, tpl_gv)
            elif is_b or (emp.x_employee_type_id.code == 'teacher'):
                # chưa có dữ liệu cổng → gán mới bình thường
                emp._hocba_maybe_assign_onboarding()

    def _migrate_legacy_group_b(self, Step, tpl):
        self.ensure_one()
        done_any = self.x_official_date or self.x_employment_status in (
            'official', 'exiting', 'inactive')
        gates = [
            # (tên, kết quả cũ, ngày cũ, note cũ, due cũ, pass_completes, ext)
            ('Đánh giá tuần-2', self.x_eval_2w_result, self.x_eval_2w_date,
             self.x_eval_2w_note, self.x_eval_2w_due, False, False),
            ('Cấp thiết bị làm việc', None, self.x_equip_grant_date,
             False, False, False, False),
            ('Đánh giá tháng-1', self.x_eval_1m_result, self.x_eval_1m_date,
             self.x_eval_1m_note, self.x_eval_1m_due, True, False),
            ('Đánh giá tháng-2', self.x_eval_2m_result, self.x_eval_2m_date,
             self.x_eval_2m_note, self.x_eval_2m_due, True, True),
        ]
        opened = False
        seq = 0
        for name, res, date, note, due, pc, ext in gates:
            seq += 1
            vals = {
                'employee_id': self.id, 'template_id': tpl.id,
                'sequence': seq, 'name': name,
                'step_type': 'task' if res is None else 'evaluation',
                'pass_completes': pc, 'is_extension': ext,
                'due_date': due or False, 'result_note': note or False,
            }
            if res is None:                     # bước thiết bị
                if date:
                    vals.update(state='done', done_date=date)
                elif done_any or opened:
                    vals['state'] = 'skipped'
                else:
                    vals['state'] = 'open'
                    opened = True
            elif res in ('pass', 'fail', 'extend'):
                vals.update(state='done', result=res,
                            done_date=date or False)
                # extend cũ ở 2w nghĩa là tái đánh giá tại chỗ → nếu là
                # bước cuối cùng có dữ liệu thì để open + extend_count
                if res == 'extend' and not ext and name == 'Đánh giá tuần-2' \
                        and self.x_eval_1m_result == 'draft' and not done_any:
                    vals.update(state='open', result=False, extend_count=1)
                    opened = True
            else:                               # draft
                if done_any or opened:
                    vals['state'] = 'skipped'
                else:
                    # tháng-2 chỉ mở nếu tháng-1 = extend
                    if ext and self.x_eval_1m_result != 'extend':
                        vals['state'] = 'skipped'
                    else:
                        vals['state'] = 'open'
                        opened = True
            Step.create(vals)
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})

    def _migrate_legacy_teacher(self, Step, tpl):
        self.ensure_one()
        res = self.x_trial_lesson_result
        note_parts = []
        if self.x_trial_score_method:
            note_parts.append('PP %.1f/10' % self.x_trial_score_method)
        if self.x_trial_score_content:
            note_parts.append('CM %.1f/10' % self.x_trial_score_content)
        if self.x_trial_lesson_note:
            note_parts.append(self.x_trial_lesson_note)
        Step.create({
            'employee_id': self.id, 'template_id': tpl.id, 'sequence': 1,
            'name': 'Thử giảng', 'step_type': 'evaluation',
            'state': 'done', 'result': res,
            'done_date': self.x_trial_lesson_date or False,
            'result_note': '; '.join(note_parts) or False})
        Step.create({
            'employee_id': self.id, 'template_id': tpl.id, 'sequence': 2,
            'name': 'Ký hợp đồng thỉnh giảng', 'step_type': 'task',
            'state': 'open' if res == 'pass' else 'skipped'})
        self.sudo().with_context(hocba_onb_assigning=True).write(
            {'x_onboarding_template_id': tpl.id})
```

- [ ] **Step 4: Migration script + bump version**

```python
# custom-addons/hocba_employees/migrations/19.0.2.0.0/post-migrate.py
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['hr.employee']._hocba_migrate_legacy_gates()
```

Manifest: `'version': '19.0.2.0.0'`.

- [ ] **Step 5: Chạy test → PASS (cả suite). Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(onboarding): migration field cổng cũ → bước động (idempotent) + bump 19.0.2.0.0"
```

---

## Task 8: API config template (hocba_hrm)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Create: `custom-addons/hocba_hrm/tests/test_onboarding_api.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

Test theo pattern file `custom-addons/hocba_hrm/tests/test_permissions_tpgv.py`
(đọc file đó trước để mirror cách nó dựng HttpCase/authenticate — nếu nó test
model-level thì API test đơn giản hoá tương ứng).

- [ ] **Step 1: Test fail** (HttpCase: user thường gọi GET templates → 403;
HR Manager GET → 200 + có 2 template seed; POST tạo/sửa replace-all steps)

```python
# custom-addons/hocba_hrm/tests/test_onboarding_api.py
import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestOnboardingConfigApi(HttpCase):
    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.env['res.users'].create({
            'name': 'Plain', 'login': 'onb_plain', 'password': 'x12345678',
            'group_ids': gu})
        self.env['res.users'].create({
            'name': 'HrM', 'login': 'onb_hrm', 'password': 'x12345678',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def test_templates_forbidden_for_plain_user(self):
        self.authenticate('onb_plain', 'x12345678')
        resp = self.url_open('/hocba-hrm/api/onboarding/templates')
        self.assertEqual(resp.status_code, 403)

    def test_templates_crud_for_hr_manager(self):
        self.authenticate('onb_hrm', 'x12345678')
        resp = self.url_open('/hocba-hrm/api/onboarding/templates')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data['templates']), 2)
        # tạo mới
        resp = self.url_open(
            '/hocba-hrm/api/onboarding/templates',
            data=json.dumps({
                'name': 'TPL API', 'applyWorkForm': 'any',
                'steps': [{'name': 'B1', 'stepType': 'task', 'dueDays': 0}],
            }), headers={'Content-Type': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        tid = resp.json()['id']
        # sửa replace-all steps
        resp = self.url_open(
            '/hocba-hrm/api/onboarding/templates/%d' % tid,
            data=json.dumps({
                'name': 'TPL API v2',
                'steps': [
                    {'name': 'E1', 'stepType': 'evaluation', 'dueDays': 7},
                    {'name': 'E2', 'stepType': 'evaluation', 'dueDays': 20,
                     'isExtension': True, 'passCompletes': True}],
            }), headers={'Content-Type': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        tpl = self.env['hb.onboarding.template'].browse(tid)
        self.assertEqual(len(tpl.step_ids), 2)
        self.assertEqual(tpl.name, 'TPL API v2')
```

- [ ] **Step 2: Chạy → FAIL** (404 route). Lệnh test module hocba_hrm:

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

- [ ] **Step 3: Implement routes** (đặt cạnh `api_onboarding` ~dòng 3520;
dùng helper sẵn `self._hr_flags()`, `_d`):

```python
    # ------------------------------------------------------------------
    # Cấu hình quy trình nhận việc (bước động) — chỉ HR Manager.
    # Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
    # ------------------------------------------------------------------
    def _onb_tpl_json(self, tpl):
        return {
            'id': tpl.id, 'name': tpl.name, 'sequence': tpl.sequence,
            'active': tpl.active,
            'applyPositionTypes': tpl.apply_position_types or '',
            'applyWorkForm': tpl.apply_work_form,
            'applyEmployeeTypeIds': tpl.apply_employee_type_ids.ids,
            'steps': [{
                'id': s.id, 'sequence': s.sequence, 'name': s.name,
                'stepType': s.step_type, 'dueDays': s.due_days,
                'passCompletes': s.pass_completes,
                'isExtension': s.is_extension,
                'autoAction': s.auto_action, 'note': s.note or '',
            } for s in tpl.step_ids.sorted(lambda x: (x.sequence, x.id))],
        }

    def _onb_step_vals(self, payload_steps):
        return [(0, 0, {
            'sequence': i + 1,
            'name': (s.get('name') or '').strip(),
            'step_type': s.get('stepType') or 'task',
            'due_days': int(s.get('dueDays') or 0),
            'pass_completes': bool(s.get('passCompletes')),
            'is_extension': bool(s.get('isExtension')),
            'auto_action': s.get('autoAction') or 'none',
            'note': (s.get('note') or '').strip() or False,
        }) for i, s in enumerate(payload_steps)]

    @http.route('/hocba-hrm/api/onboarding/templates', auth='user',
                type='http', methods=['GET', 'POST'], csrf=False)
    def api_onb_templates(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'},
                                              status=410)
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        Tpl = request.env['hb.onboarding.template'].sudo()
        if request.httprequest.method == 'GET':
            emp_types = request.env['hocba.employee.type'].sudo().search([])
            return request.make_json_response({
                'templates': [self._onb_tpl_json(t) for t in
                              Tpl.with_context(active_test=False).search([])],
                'employeeTypes': [{'id': t.id, 'name': t.name}
                                  for t in emp_types],
            })
        payload = request.get_json_data()
        try:
            tpl = Tpl.create({
                'name': (payload.get('name') or '').strip(),
                'sequence': int(payload.get('sequence') or 10),
                'apply_position_types':
                    (payload.get('applyPositionTypes') or '').strip() or False,
                'apply_work_form': payload.get('applyWorkForm') or 'any',
                'apply_employee_type_ids':
                    [(6, 0, payload.get('applyEmployeeTypeIds') or [])],
                'step_ids': self._onb_step_vals(payload.get('steps') or []),
            })
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._onb_tpl_json(tpl))

    @http.route('/hocba-hrm/api/onboarding/templates/<int:tpl_id>',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_template_update(self, tpl_id, **kw):
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        tpl = request.env['hb.onboarding.template'].sudo().with_context(
            active_test=False).browse(tpl_id)
        if not tpl.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        payload = request.get_json_data()
        vals = {}
        for key, field in (('name', 'name'), ('sequence', 'sequence'),
                           ('applyWorkForm', 'apply_work_form'),
                           ('active', 'active')):
            if key in payload:
                vals[field] = payload[key]
        if 'applyPositionTypes' in payload:
            vals['apply_position_types'] = \
                (payload['applyPositionTypes'] or '').strip() or False
        if 'applyEmployeeTypeIds' in payload:
            vals['apply_employee_type_ids'] = \
                [(6, 0, payload['applyEmployeeTypeIds'] or [])]
        if 'steps' in payload:
            vals['step_ids'] = [(5, 0, 0)] + self._onb_step_vals(
                payload['steps'] or [])
        try:
            tpl.write(vals)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._onb_tpl_json(tpl))
```

(`(5,0,0)` = xoá hết step cũ rồi tạo lại — replace-all theo spec; snapshot
nên NV đang chạy không ảnh hưởng.)

- [ ] **Step 4: Thêm `from . import test_onboarding_api` vào
`custom-addons/hocba_hrm/tests/__init__.py`. Chạy → PASS. Commit**

```bash
git add custom-addons/hocba_hrm
git commit -m "feat(onboarding): API config template (GET/POST/replace-all steps) — HR Manager"
```

---

## Task 9: API vận hành bước + viết lại GET onboarding + detail payload

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`
- Modify: `custom-addons/hocba_hrm/tests/test_onboarding_api.py`

- [ ] **Step 1: Test fail (thêm vào test_onboarding_api.py)**

```python
@tagged('post_install', '-at_install')
class TestOnboardingOpsApi(HttpCase):
    def setUp(self):
        super().setUp()
        self.hrm = self.env['res.users'].create({
            'name': 'HrM2', 'login': 'onb_hrm2', 'password': 'x12345678',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Ops', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'x_employment_status': 'probation',
            'x_probation_start': '2026-07-01'})

    def _post(self, url, body=None):
        return self.url_open(url, data=json.dumps(body or {}),
                             headers={'Content-Type': 'application/json'})

    def test_onboarding_list_has_dynamic_steps(self):
        self.authenticate('onb_hrm2', 'x12345678')
        resp = self.url_open('/hocba-hrm/api/employees/onboarding')
        self.assertEqual(resp.status_code, 200)
        item = next(i for i in resp.json()['items']
                    if i['id'] == self.emp.id)
        self.assertEqual(len(item['steps']), 4)
        self.assertEqual(item['steps'][0]['state'], 'open')
        self.assertEqual(item['progress'], {'done': 0, 'total': 4})
        self.assertTrue(item['steps'][0]['canAct'])

    def test_evaluate_step_via_api(self):
        self.authenticate('onb_hrm2', 'x12345678')
        step = self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0]
        resp = self._post(
            '/hocba-hrm/api/onboarding/steps/%d/evaluate' % step.id,
            {'result': 'pass'})
        self.assertEqual(resp.status_code, 200)
        # payload trả về item NV đã refresh
        self.assertEqual(resp.json()['steps'][0]['state'], 'done')

    def test_evaluate_requires_permission(self):
        self.env['res.users'].create({
            'name': 'Plain2', 'login': 'onb_plain2',
            'password': 'x12345678',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.authenticate('onb_plain2', 'x12345678')
        step = self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0]
        resp = self._post(
            '/hocba-hrm/api/onboarding/steps/%d/evaluate' % step.id,
            {'result': 'pass'})
        self.assertEqual(resp.status_code, 403)

    def test_set_due_and_assign(self):
        self.authenticate('onb_hrm2', 'x12345678')
        step = self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0]
        resp = self._post(
            '/hocba-hrm/api/onboarding/steps/%d/due' % step.id,
            {'dueDate': '2026-08-01'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(str(step.due_date), '2026-08-01')
        gv = self.env.ref('hocba_employees.onb_template_teacher')
        resp = self._post(
            '/hocba-hrm/api/employees/%d/onboarding/assign' % self.emp.id,
            {'templateId': gv.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.emp.x_onboarding_template_id, gv)
```

- [ ] **Step 2: Chạy → FAIL**

- [ ] **Step 3: Implement.** Viết lại `api_onboarding` (thay body items —
GIỮ route + scope):

```python
    def _onb_emp_item(self, e):
        """Payload 1 NV cho màn Onboarding + drawer (bước động)."""
        can_eval = self._can_eval_emp(e)
        user = request.env.user
        is_gv_teacher = (
            user.has_group('hocba_employees.group_hocba_giaovu')
            and e.x_employee_type_id.code == 'teacher')
        steps = []
        done = total = 0
        current = None
        for s in e.x_onboarding_step_ids.sorted(
                lambda x: (x.sequence, x.id)):
            total += 1
            if s.state in ('done', 'skipped'):
                done += 1
            can_act = (s.state == 'open') and (
                can_eval or (s.step_type == 'task' and is_gv_teacher))
            item = {
                'id': s.id, 'name': s.name, 'stepType': s.step_type,
                'state': s.state, 'result': s.result or '',
                'extendCount': s.extend_count,
                'dueDate': _d(s.due_date), 'doneDate': _d(s.done_date),
                'doneBy': s.done_by_id.name or '',
                'note': s.note or '', 'resultNote': s.result_note or '',
                'passCompletes': s.pass_completes,
                'isExtension': s.is_extension,
                'canAct': can_act,
            }
            if s.state == 'open' and current is None:
                current = item
            steps.append(item)
        return {
            'id': e.id, 'code': e.x_employee_code or '—', 'name': e.name,
            'depName': e.department_id.name or 'Chưa gán',
            'jobTitle': e.job_id.name or '—',
            'hasImg': bool(e.image_1920),
            'start': _d(e.x_probation_start),
            'templateId': e.x_onboarding_template_id.id or 0,
            'templateName': e.x_onboarding_template_id.name or '',
            'steps': steps,
            'progress': {'done': done if total else 0, 'total': total},
            'current': current,
            'canEval': can_eval,
        }
```

Body mới `api_onboarding`: giữ search domain như cũ, `items =
[self._onb_emp_item(e) for e in emps]`.

Routes thao tác:

```python
    def _onb_step_response(self, step):
        return request.make_json_response(
            self._onb_emp_item(step.employee_id.sudo()))

    def _onb_get_step(self, step_id):
        step = request.env['hb.onboarding.step'].sudo().browse(step_id)
        if not step.exists():
            return None, request.make_json_response(
                {'error': 'not_found'}, status=404)
        return step, None

    def _onb_can_act(self, step):
        e = step.employee_id
        if self._can_eval_emp(e):
            return True
        user = request.env.user
        return (step.step_type == 'task'
                and user.has_group('hocba_employees.group_hocba_giaovu')
                and e.x_employee_type_id.code == 'teacher')

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/complete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_complete(self, step_id, **kw):
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        if not self._onb_can_act(step):
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        payload = request.get_json_data()
        try:
            step.with_user(request.env.user).sudo().action_complete(
                note=(payload.get('note') or '').strip() or None)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=422)
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/evaluate',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_evaluate(self, step_id, **kw):
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        if not self._can_eval_emp(step.employee_id):
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        payload = request.get_json_data()
        result = payload.get('result')
        if result not in ('pass', 'extend', 'fail'):
            return request.make_json_response({'error': 'bad_request'},
                                              status=400)
        try:
            step.with_user(request.env.user).sudo().action_evaluate(
                result, note=(payload.get('note') or '').strip() or None,
                eval_date=payload.get('date') or None)
        except (ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=422)
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/onboarding/steps/<int:step_id>/due',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_step_due(self, step_id, **kw):
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        step, err = self._onb_get_step(step_id)
        if err:
            return err
        payload = request.get_json_data()
        step.write({'due_date': payload.get('dueDate') or False})
        return self._onb_step_response(step)

    @http.route('/hocba-hrm/api/employees/<int:emp_id>/onboarding/assign',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_onb_assign(self, emp_id, **kw):
        if not self._hr_flags()[1]:
            return request.make_json_response({'error': 'forbidden'},
                                              status=403)
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'},
                                              status=404)
        payload = request.get_json_data()
        tpl = request.env['hb.onboarding.template'].sudo().browse(
            int(payload.get('templateId') or 0))
        if not tpl.exists():
            return request.make_json_response({'error': 'bad_request'},
                                              status=400)
        e._hocba_assign_onboarding(template=tpl)
        return request.make_json_response(self._onb_emp_item(e))
```

Chú ý `step.with_user(...).sudo()` — mục đích: `env.user` đúng người thao tác
cho `done_by_id`/message_post nhưng bypass ACL. NHƯNG `.sudo()` đè user →
`done_by_id` thành superuser! Fix đúng: action model lấy uid từ
`self.env.context.get('uid_action')` hoặc đơn giản hơn — controller đã check
quyền, gọi `step.with_user(request.env.user).action_...` KHÔNG sudo, và model
`_check_can_act` pass rồi tự `self.sudo().write(...)` bên trong (đã làm ở
Task 4). → Bỏ `.sudo()` ở controller, chỉ `with_user`. Nhất quán với Task 4.

**Đồng thời trong task này:**
- `_employee_detail` (~dòng 2260): thay `data['probation'] = {...}` +
  `data['trial'] = {...}` bằng `data['onboarding'] = self._onb_emp_item(e)`
  (grep `data['probation']` để tìm đúng chỗ; FE ProbationTab viết lại ở
  Task 12 dùng key mới).
- XOÁ 2 route cũ `api_employee_gate` (/gate) + `api_employee_trial` (/trial)
  và helper `_can_eval_trial` nếu không còn ai dùng (grep trước).
- Key `probStart` trong FIELD_MAP (~dòng 41) GIỮ (x_probation_start còn dùng).

- [ ] **Step 4: Chạy test hocba_hrm + hocba_employees → PASS. Commit**

```bash
git add custom-addons/hocba_hrm
git commit -m "feat(onboarding): API vận hành bước động + GET onboarding/detail trả steps; gỡ route gate/trial cũ"
```

---

## Task 10: SPA — api layer + màn Cấu hình nhận việc

**Files:**
- Create: `frontend/src/api/onboarding.js`
- Modify: `frontend/src/api/employees.js` (xoá postGate/postTrial)
- Create: `frontend/src/features/onboarding/OnboardingConfig.jsx`
- Modify: `frontend/src/app/Shell.jsx` (menu item — đọc file để biết cấu trúc
  nav trước khi sửa; thêm view `onboarding-config` gated `me.isHrManager`;
  kiểm tra fetchRoles trả `isHrManager` — grep controller `/api/me/roles`)
- Modify: `frontend/src/app/App.jsx`

- [ ] **Step 1: API layer**

```javascript
/* frontend/src/api/onboarding.js — API quy trình nhận việc bước động.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md */
import { hbGet, hbPost } from './client';

/* Config template (HR Manager) */
export const fetchOnbTemplates = () => hbGet('/hocba-hrm/api/onboarding/templates');
export const createOnbTemplate = (payload) =>
  hbPost('/hocba-hrm/api/onboarding/templates', payload);
export const updateOnbTemplate = (id, payload) =>
  hbPost(`/hocba-hrm/api/onboarding/templates/${id}`, payload);

/* Vận hành bước — mỗi call trả item NV đã refresh */
export const completeOnbStep = (stepId, payload = {}) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/complete`, payload);
export const evaluateOnbStep = (stepId, payload) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/evaluate`, payload);
export const setOnbStepDue = (stepId, dueDate) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/due`, { dueDate });
export const assignOnbTemplate = (empId, templateId) =>
  hbPost(`/hocba-hrm/api/employees/${empId}/onboarding/assign`, { templateId });
```

Xoá `postGate`, `postTrial` khỏi `api/employees.js` (sau khi Task 12 gỡ nơi
dùng — thứ tự thực tế: để Task 12 xoá; task này chỉ THÊM file mới. An toàn:
làm bước xoá ở Task 12).

- [ ] **Step 2: Màn config** — `OnboardingConfig.jsx`: danh sách template
(card: tên, tiêu chí áp dụng, số bước, active) + drawer editor. Editor: form
tên/sequence/3 tiêu chí (position types = nhóm checkbox 5 loại; work form =
select; employee types = checkbox từ `employeeTypes` payload) + bảng bước
(kéo lên/xuống bằng nút ↑↓, thêm/xoá dòng; mỗi dòng: tên, select loại, hạn
+N ngày, checkbox 2 cờ khi evaluation / select auto_action khi task, note).
Nút Lưu → create/update (steps replace-all); nút Lưu trữ (active=false).
Tái dùng `ModalHeader`, `ConfirmModal`, `useFetch`, `Badge`, `Icon`,
`LoadingState/ErrorState/EmptyState`. Component đầy đủ viết theo pattern
`frontend/src/features/employees/Onboarding.jsx` + drawer pattern trong
`frontend/src/features/offboarding/Offboarding.jsx` (đọc 2 file khi
implement). Khung chính:

```jsx
/* frontend/src/features/onboarding/OnboardingConfig.jsx
   Màn Cấu hình nhận việc — CRUD template bước động (chỉ HR Manager). */
import { useState } from 'react';
import useFetch from '../../hooks/useFetch';
import { fetchOnbTemplates, createOnbTemplate, updateOnbTemplate }
  from '../../api/onboarding';
import ModalHeader from '../../components/ModalHeader';
import ConfirmModal from '../../components/ConfirmModal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const POSITION_TYPES = [
  ['manager', 'Quản lý'], ['staff', 'Nhân viên'], ['ctv', 'CTV'],
  ['freelancer', 'Freelancer'], ['advisor', 'Cố vấn']];
const STEP_TYPES = [['task', 'Việc cần làm'], ['evaluation', 'Đánh giá']];

const EMPTY_STEP = { name: '', stepType: 'task', dueDays: 0,
  passCompletes: false, isExtension: false, autoAction: 'none', note: '' };

export default function OnboardingConfig() {
  const { data, error, reload } = useFetch(fetchOnbTemplates, []);
  const [editing, setEditing] = useState(null); // null | {} mới | template
  if (error) return <ErrorState message={error.message} onRetry={reload} />;
  if (!data) return <LoadingState label="Đang tải cấu hình…" />;
  /* ... danh sách card + nút Thêm quy trình ... */
  /* editing !== null → <TemplateDrawer tpl={editing}
       employeeTypes={data.employeeTypes}
       onClose={() => setEditing(null)}
       onSaved={() => { setEditing(null); reload(); }} /> */
}
```

(Drawer: state cục bộ `form` clone từ tpl; submit gọi create/update; lỗi 400
hiện message trong drawer. Viết đầy đủ khi implement — logic thuần form.)

- [ ] **Step 3: Nối route + menu.** `App.jsx`: import + thêm dòng

```jsx
        {view === 'onboarding-config' && canManage && me.isHrManager && (
          <OnboardingConfig />
        )}
```

`Shell.jsx`: thêm item menu "Cấu hình nhận việc" (icon settings/list) vào
nhóm quản lý, chỉ hiện khi `me.isHrManager`; thêm `'onboarding-config'` vào
`allowedViews` cho vai trò HR Manager. (Đọc Shell.jsx trước — cấu trúc
allowedViews/label breadcrumb phải cập nhật đồng bộ.) Kiểm tra
`/api/me/roles` có trả `isHrManager` — nếu chưa, thêm key đó vào controller.

- [ ] **Step 4: Build SPA + smoke test màn config trên preview
(đăng nhập test_hrmanager@hocba.vn / Hocba@2026):**

```bash
cd frontend && npm run build
```

Preview: `preview_start` (theo `.claude/launch.json`), vào `/hocba-hrm`,
mở màn Cấu hình nhận việc, tạo/sửa template thử. Xác nhận user
test_employee không thấy menu.

- [ ] **Step 5: Commit**

```bash
git add frontend custom-addons/hocba_hrm/static/spa custom-addons/hocba_hrm/controllers
git commit -m "feat(onboarding-ui): màn Cấu hình nhận việc (template bước động) — HR Manager"
```

---

## Task 11: SPA — viết lại màn Onboarding (bảng theo dõi)

**Files:**
- Modify: `frontend/src/features/employees/Onboarding.jsx`

- [ ] **Step 1: Viết lại.** Bỏ `phaseOf`/`GateCell`/key cứng. Bảng cột: NV
(avatar+tên+mã), Phòng ban, Vị trí, Ngày bắt đầu, Quy trình (templateName),
Tiến độ (`progress.done`/`progress.total` + thanh %), Bước hiện tại
(`current.name` + badge type + hạn `current.dueDate`, đỏ khi
`dueDate < TODAY`), Trạng thái tổng (suy từ steps: có fail → "Không đạt" đỏ;
mọi bước done/skipped → "Hoàn tất" xanh; else "Đang thử việc" amber +
overdue ⚠). Click dòng mở `EmployeeDrawer` (giữ pattern dirtyRef/reloadQuiet
hiện có). Search giữ nguyên (name/code/depName).

```jsx
/* Suy trạng thái tổng từ steps động */
function overallOf(o) {
  if (o.steps.some((s) => s.result === 'fail'))
    return { key: 'fail', label: 'Không đạt thử việc' };
  if (o.steps.length && o.steps.every((s) => s.state === 'done' || s.state === 'skipped'))
    return { key: 'done', label: 'Hoàn tất quy trình' };
  if (!o.steps.length) return { key: 'none', label: 'Chưa có quy trình' };
  return { key: 'run', label: o.current ? `Đang: ${o.current.name}` : 'Đang thử việc' };
}
```

- [ ] **Step 2: Build + verify preview** (bảng hiện steps đúng với NV demo;
nếu DB local chưa migrate → chạy upgrade `-u hocba_employees` trước bằng
docker compose run, migration 19.0.2.0.0 sẽ map dữ liệu cũ).

- [ ] **Step 3: Commit**

```bash
git add frontend custom-addons/hocba_hrm/static/spa
git commit -m "feat(onboarding-ui): bảng theo dõi nhận việc theo bước động (tiến độ + bước hiện tại)"
```

---

## Task 12: SPA — tab Thử việc trong EmployeeDrawer theo bước động

**Files:**
- Create: `frontend/src/features/employees/OnboardingStepsPanel.jsx`
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx`
  (thay `ProbationTab`/`GateAction`/`TrialAction` — xoá 3 component cũ)
- Modify: `frontend/src/api/employees.js` (xoá postGate/postTrial)

- [ ] **Step 1: Component mới** — timeline dọc các bước từ
`det.onboarding.steps`: mỗi bước 1 hàng (chấm màu theo state/result như
`HB_RESULT`, tên + badge loại, hạn/ngày làm/người làm/ghi chú). Bước
`canAct`:
  - task → nút "✓ Hoàn thành" (ConfirmModal, gọi `completeOnbStep`)
  - evaluation → 3 nút Đạt (xanh) / Gia hạn (amber) / Không đạt (đỏ) + ô note
    (bắt buộc khi Không đạt — validate FE, BE vẫn chặn); gọi
    `evaluateOnbStep(stepId, {result, note})`; lỗi 422 hiện message.
  - HR Manager: nút ✎ sửa hạn (input date → `setOnbStepDue`) + select
    "Đổi quy trình" (`assignOnbTemplate` — cần danh sách template: gọi
    `fetchOnbTemplates` khi user là HR Manager, hoặc đơn giản chỉ hiện khi
    `det.onboarding.steps.length === 0`? — theo spec: đổi được bất kỳ lúc
    nào → load templates lazy khi bấm nút).
  - Sau mỗi call: response là item NV (steps refreshed) → cập nhật local +
    gọi `onUpdated` để drawer refetch detail (giữ pattern cũ:
    `onUpdated(await fetchEmployee(det.id))` hoặc đơn giản trigger reload).
- [ ] **Step 2: Nối vào EmployeeDrawer** — tab 'probation' render
`<OnboardingStepsPanel det={det} onUpdated={update} />`; xoá import
postGate/postTrial + 3 component cũ + export `ProbationTab` (grep nơi khác
import `ProbationTab` — `Profile.jsx` có thể dùng cho self-service! Nếu có:
Profile dùng bản read-only của panel mới — panel nhận prop `readOnly`).
- [ ] **Step 3: Xoá `postGate`/`postTrial` khỏi api/employees.js; grep toàn
frontend/src không còn tham chiếu.**
- [ ] **Step 4: Build + verify preview đủ 3 vai trò:** test_hrmanager (đánh
giá + sửa hạn + đổi quy trình), test_truongphong (đánh giá NV phòng mình),
test_employee (chỉ xem của mình qua Profile). Chụp screenshot làm bằng chứng.
- [ ] **Step 5: Commit**

```bash
git add frontend custom-addons/hocba_hrm/static/spa
git commit -m "feat(onboarding-ui): tab Thử việc theo bước động (hoàn thành/đánh giá/sửa hạn/đổi quy trình)"
```

---

## Task 13: Hoàn tất — full test, upgrade DB, docs

- [ ] **Step 1: Chạy FULL suite backend** (2 module):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees,hocba_hrm --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_employees,/hocba_hrm --stop-after-init --log-level=test
```

Kỳ vọng: `0 failed, 0 error(s)`, N > tổng test cũ (thêm ~25 test mới).

- [ ] **Step 2: Upgrade DB local `hocba_hrm`** (migration chạy thật):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees,hocba_hrm --addons-path=/mnt/extra-addons --stop-after-init
```

Verify qua preview: NV demo cũ có steps migrate đúng.

- [ ] **Step 3: Docs.** Cập nhật:
  - `docs/DB_TEST_DATA.md`: nhật ký upgrade (local; Neon làm khi deploy —
    NHỚ endpoint trực tiếp không -pooler).
  - `docs/MANUAL_TEST_GUIDE.md`: mục mới "Cấu hình nhận việc" (tạo template,
    gán, đánh giá đủ nhánh pass/extend/fail theo vai trò).
- [ ] **Step 4: Commit + verify trước khi báo xong** (dùng skill
`superpowers:verification-before-completion` rồi
`superpowers:requesting-code-review`).

```bash
git add docs
git commit -m "docs(onboarding): hướng dẫn test tay + nhật ký upgrade DB bước động"
```

---

## Self-review checklist (đã chạy khi viết plan)

- Spec coverage: model 3.1-3.4 (Task 1-2), engine 4.1-4.2 (Task 2-5), quyền
  4.3 (Task 4, 8-9), cron/chuông 4.4 (Task 6), API §5 (Task 8-9), SPA §6
  (Task 10-12), migration/seed §7 (Task 5, 7, 13), test §8 (xuyên suốt).
- Điểm cần xác minh khi execute (đánh dấu trong task): xml id
  `employee_type_teacher`; `hr.employee.create` override đã có chưa; tên
  field `x_skip_auto_trigger`; nơi dùng `ProbationTab`/`GATE_EDIT_FIELDS`;
  constraint `_check_has_steps` với install_mode; `/api/me/roles` có
  `isHrManager`.
