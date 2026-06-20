# Attendance OT/CTV Scheduling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add by-shift-type visibility, time-gated review/edit/reject (with auto-reject), manager add-for-anyone, and history-only correction requests to the attendance OT/CTV feature.

**Architecture:** Backend models live in `custom-addons/hocba_attendance` (Odoo ORM); JSON API helpers + routes live in `custom-addons/hocba_hrm/controllers/main.py`; UI is a React SPA in `frontend/src/features/attendance/`. Auto-reject is hybrid: a stored `deadline` field drives a lazy on-read sweep, an `ir.cron` backstop, and a hard server-side action guard.

**Tech Stack:** Odoo 19 (Python), PostgreSQL, React 18 + Vite. Tests: Odoo `TransactionCase` (no JS test harness — frontend verified via `npm run build` + manual).

## Global Constraints

- Odoo `res.users` group field is `group_ids` (not `groups_id`) — Odoo 19.
- Run tests against the LOCAL Docker stack only (never Neon). On Windows Git Bash, prefix with `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` and confirm the printed test count is non-zero.
- Backend test command (model tests, tag `/hocba_attendance`):
  ```bash
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
    odoo -d hocba_hrm -u hocba_attendance,hocba_employees \
    --addons-path=/mnt/extra-addons \
    --test-enable --test-tags /hocba_attendance --stop-after-init --log-level=test
  ```
- Controller test command (tag `/hocba_hrm`): same form but `-u hocba_hrm` and `--test-tags /hocba_hrm`. (`hocba_hrm` is already installed locally; if `of 0 tests`, install once with `-i hocba_hrm`.)
- Success line: `0 failed, 0 error(s) of N tests` with N non-zero.
- Datetimes stored UTC-naive; convert local→UTC with `_to_utc(env, s)`, UTC→local wire with `_dt_local(rec, dt)`. Tests build records `.with_context(tz='Asia/Ho_Chi_Minh')`.
- Deadline rule: `deadline = start − 1 minute`. Manager add-for-anyone employee field is `hr.employee.x_employee_code` (unique).
- Commit message trailer on every commit:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```

---

## Task 1: `hocba.work_shift` — deadline, auto-reject, action guard

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_work_shift.py`
- Create: `custom-addons/hocba_attendance/tests/test_shift_deadline.py`
- Modify: `custom-addons/hocba_attendance/tests/__init__.py`

**Interfaces:**
- Produces:
  - field `deadline: Datetime` (computed, stored) on `hocba.work_shift` = `start − timedelta(minutes=1)`.
  - `model._auto_reject_expired(domain=None) -> recordset` — rejects all `state='pending'` shifts with `deadline < now` (AND-ed with `domain`); writes `state='rejected'`, `review_note='Tự động từ chối: quá hạn duyệt'`, `decision_date=now`.
  - `shift._assert_actionable()` — raises `UserError` if `now >= deadline`.

- [ ] **Step 1: Write the failing tests**

Create `custom-addons/hocba_attendance/tests/test_shift_deadline.py`:

```python
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestShiftDeadline(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV OT', 'x_employment_status': 'ctv'})
        self.Shift = self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh')

    def _shift(self, **vals):
        base = {'employee_id': self.emp.id, 'shift_type': 'ot',
                'start': '2026-06-15 02:00:00', 'end': '2026-06-15 04:00:00'}
        base.update(vals)
        return self.Shift.create(base)

    def test_deadline_is_start_minus_one_minute(self):
        s = self._shift(start='2026-06-15 03:00:00')
        self.assertEqual(s.deadline, fields.Datetime.from_string('2026-06-15 02:59:00'))

    def test_auto_reject_expired_rejects_past_pending(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2), state='pending')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'rejected')
        self.assertTrue(s.decision_date)

    def test_auto_reject_leaves_future_pending(self):
        future = fields.Datetime.now() + timedelta(hours=1)
        s = self._shift(start=future, end=future + timedelta(hours=2), state='pending')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'pending')

    def test_auto_reject_ignores_approved(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2), state='approved')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'approved')

    def test_assert_actionable_raises_after_deadline(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2))
        with self.assertRaises(UserError):
            s._assert_actionable()

    def test_assert_actionable_passes_before_deadline(self):
        future = fields.Datetime.now() + timedelta(hours=1)
        s = self._shift(start=future, end=future + timedelta(hours=2))
        s._assert_actionable()  # should not raise
```

Register it in `custom-addons/hocba_attendance/tests/__init__.py` by adding this line at the end:

```python
from . import test_shift_deadline
```

- [ ] **Step 2: Run tests to verify they fail**

Run the backend test command (Global Constraints).
Expected: FAIL/ERROR — `deadline` field and methods don't exist yet (`AttributeError` / field unknown).

- [ ] **Step 3: Implement the model changes**

In `custom-addons/hocba_attendance/models/hocba_work_shift.py`, change the imports at the top:

```python
from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
```

Add the `deadline` field right after the `decision_date` field (after line 35):

```python
    deadline = fields.Datetime(
        string='Hạn thao tác', compute='_compute_deadline', store=True,
        help='Hạn cuối duyệt/sửa/từ chối = giờ bắt đầu trừ 1 phút.')
```

Add these methods after `_compute_rate` (after line 45):

```python
    @api.depends('start')
    def _compute_deadline(self):
        for rec in self:
            rec.deadline = (rec.start - timedelta(minutes=1)) if rec.start else False

    def _auto_reject_expired(self, domain=None):
        """Tự động từ chối mọi ca pending đã quá hạn (deadline < now).
        domain: lọc thêm (AND). Trả recordset đã từ chối."""
        now = fields.Datetime.now()
        base = [('state', '=', 'pending'), ('deadline', '<', now)]
        expired = self.sudo().search(base + (domain or []))
        if expired:
            expired.write({
                'state': 'rejected',
                'review_note': 'Tự động từ chối: quá hạn duyệt',
                'decision_date': now,
            })
        return expired

    def _assert_actionable(self):
        """Raise nếu đã quá hạn thao tác với ca (now >= deadline)."""
        self.ensure_one()
        if self.deadline and fields.Datetime.now() >= self.deadline:
            raise UserError('Đã quá hạn thao tác với ca này (trước giờ bắt đầu 1 phút).')
```

- [ ] **Step 4: Run tests to verify they pass**

Run the backend test command.
Expected: PASS — the 6 new tests pass; existing `/hocba_attendance` tests still pass.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/models/hocba_work_shift.py custom-addons/hocba_attendance/tests/test_shift_deadline.py custom-addons/hocba_attendance/tests/__init__.py
git commit -m "feat(attendance): work_shift deadline + auto-reject + action guard

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Cron backstop for auto-reject

**Files:**
- Create: `custom-addons/hocba_attendance/data/hocba_work_shift_cron.xml`
- Modify: `custom-addons/hocba_attendance/__manifest__.py`

**Interfaces:**
- Consumes: `model._auto_reject_expired()` (Task 1).
- Produces: an `ir.cron` running every 5 minutes.

- [ ] **Step 1: Create the cron data file**

Create `custom-addons/hocba_attendance/data/hocba_work_shift_cron.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="ir_cron_auto_reject_expired_shift" model="ir.cron">
        <field name="name">Tự động từ chối ca quá hạn</field>
        <field name="model_id" ref="model_hocba_work_shift"/>
        <field name="state">code</field>
        <field name="code">model._auto_reject_expired()</field>
        <field name="interval_number">5</field>
        <field name="interval_type">minutes</field>
        <field name="active" eval="True"/>
    </record>
</odoo>
```

- [ ] **Step 2: Register the data file in the manifest**

In `custom-addons/hocba_attendance/__manifest__.py`, add the cron file to the `data` list right after the policy data line (line 11):

```python
        'data/hocba_attendance_policy_data.xml',
        'data/hocba_work_shift_cron.xml',
        'views/hr_attendance_status_views.xml',
```

- [ ] **Step 3: Verify the module upgrades cleanly**

Run the backend test command (it performs `-u hocba_attendance`, which loads the new data file).
Expected: module upgrades without XML errors; `0 failed, 0 error(s)`.

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_attendance/data/hocba_work_shift_cron.xml custom-addons/hocba_attendance/__manifest__.py
git commit -m "feat(attendance): ir.cron backstop to auto-reject expired shifts

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `hocba.attendance` — missing-minutes cap 240 + half-day basis

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py:127-157` (`_compute_work_metrics`)
- Modify: `custom-addons/hocba_attendance/tests/test_work_credit.py`

**Interfaces:**
- Produces: `missing_minutes = clamp(round(basis*60 − worked_min), 0, 240)` where `basis = std/2` when `work_credit == 0.5`, else `std`.

**Note:** The existing test `test_early_checkout_loses_afternoon_credit` currently asserts `missing_minutes == 180`. Under the new half-day basis (worked 5h, half credit → basis 4h → `max(0, 240−300)=0`) it becomes `0`. This task updates that assertion and adds new tests.

- [ ] **Step 1: Update the existing test and add new tests**

In `custom-addons/hocba_attendance/tests/test_work_credit.py`, change `test_early_checkout_loses_afternoon_credit` so the missing-minutes assertion reflects the half-day basis:

```python
    def test_early_checkout_loses_afternoon_credit(self):
        # 09:00 in (02:00 UTC), 14:00 out (07:00 UTC) = chỉ 5h, < check_in+6h
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 07:00:00')
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.work_credit, 0.5)
        # Nửa công -> phút thiếu so với 4h: worked 5h > 4h -> 0
        self.assertEqual(rec.missing_minutes, 0)
        self.assertEqual(rec.early_leave_minutes, 180)
```

Add these two tests to the `TestWorkCreditFields` class:

```python
    def test_half_day_missing_vs_four_hours(self):
        # 09:00 in (02:00 UTC), 12:00 out (05:00 UTC) = 3h. Nửa công -> thiếu vs 4h = 60'
        rec = self._rec('2026-06-17 02:00:00', '2026-06-17 05:00:00')
        self.assertEqual(rec.work_credit, 0.5)
        self.assertEqual(rec.missing_minutes, 60)

    def test_missing_minutes_capped_at_240(self):
        # 10:30 in (03:30 UTC) sau mốc sáng -> morning 0; 12:30 out (05:30 UTC) ->
        # worked 2h, afternoon 0 -> work_credit 0 -> basis 8h -> 360' kẹp tối đa 240'
        rec = self._rec('2026-06-17 03:30:00', '2026-06-17 05:30:00')
        self.assertEqual(rec.work_credit, 0.0)
        self.assertEqual(rec.missing_minutes, 240)
```

- [ ] **Step 2: Run tests to verify they fail**

Run the backend test command.
Expected: FAIL — `test_half_day_missing_vs_four_hours` (gets 0 under old 8h basis: 240−180... actually old gives `max(0,480−180)=300`≠60), `test_missing_minutes_capped_at_240` (old gives 480), and the edited `test_early_checkout...` (old gives 180) all fail against current code.

- [ ] **Step 3: Implement the formula change**

In `custom-addons/hocba_attendance/models/hr_attendance.py`, replace the body of the `if ci and co:` / `else:` block and the trailing `work_credit` line (lines 145-157) so credits are computed before missing-minutes:

```python
            if ci and co:
                worked_min = (co - ci).total_seconds() / 60.0
                expected = ci + timedelta(hours=std)
                rec.early_leave_minutes = max(
                    0, int(round((expected - co).total_seconds() / 60.0)))
                aft_threshold = ci + timedelta(hours=std - aft_margin)
                rec.afternoon_credit = 0.5 if co >= aft_threshold else 0.0
                work_credit = rec.morning_credit + rec.afternoon_credit
                basis = (std / 2.0) if work_credit == 0.5 else std
                rec.missing_minutes = max(
                    0, min(240, int(round(basis * 60 - worked_min))))
            else:
                rec.missing_minutes = 0
                rec.early_leave_minutes = 0
                rec.afternoon_credit = 0.0
            rec.work_credit = rec.morning_credit + rec.afternoon_credit
```

- [ ] **Step 4: Run tests to verify they pass**

Run the backend test command.
Expected: PASS — new + edited tests pass; `test_full_day_one_credit` (8h, full credit, missing 0) and `test_no_checkout_no_missing` still pass.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_attendance/models/hr_attendance.py custom-addons/hocba_attendance/tests/test_work_credit.py
git commit -m "feat(attendance): cap phút thiếu at 240 and use 4h basis for half-day

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Controller — shift visibility by type, type filter, lazy reject, richer row

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — add `_shift_scope_domain`; rewrite `_shifts_week` visibility (lines 803-840); extend `_shift_row` (lines 740-759); add `type` param to `api_shifts_week` route (line 2271-2273).
- Create: `custom-addons/hocba_hrm/tests/test_shift_scope.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: `_user_can_manage`, `_emp_scope_domain`, `_dt_local`, `_auto_reject_expired` (Task 1).
- Produces:
  - `_shift_scope_domain(env, type_filter=None) -> domain list` on `hocba.work_shift`.
  - `_shifts_week(env, monday_str, type_filter=None)` — new signature.
  - `_shift_row(s)` now includes `shiftTypeLabel`, `deadline`, `locked`, `mine`.
  - route `GET /shifts/week?monday=&type=`.

- [ ] **Step 1: Write the failing tests**

Check `custom-addons/hocba_hrm/tests/test_shift_api.py` for the existing setup pattern (how it builds users/employees and calls helpers). Create `custom-addons/hocba_hrm/tests/test_shift_scope.py` mirroring that pattern:

```python
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _shift_scope_domain


@tagged('post_install', '-at_install')
class TestShiftScope(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctv = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.reg = self.env['hr.employee'].create({
            'name': 'NV B', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789'})

    def _user_for(self, emp, manager=False):
        groups = [self.env.ref('base.group_user').id]
        if manager:
            groups.append(self.env.ref('hr.group_hr_manager').id)
        user = self.env['res.users'].create({
            'name': emp.name, 'login': 'u_%s' % emp.id,
            'group_ids': [(6, 0, groups)]})
        emp.user_id = user
        return user

    def test_regular_employee_sees_only_ot(self):
        env = self.env(user=self._user_for(self.reg))
        dom = _shift_scope_domain(env)
        self.assertIn(('shift_type', '=', 'ot'), dom)

    def test_ctv_sees_only_ctv(self):
        env = self.env(user=self._user_for(self.ctv))
        dom = _shift_scope_domain(env)
        self.assertIn(('shift_type', '=', 'ctv'), dom)

    def test_manager_no_type_restriction_by_default(self):
        env = self.env(user=self._user_for(self.reg, manager=True))
        dom = _shift_scope_domain(env)
        self.assertFalse([t for t in dom if t[0] == 'shift_type'])

    def test_manager_type_filter_applies(self):
        env = self.env(user=self._user_for(self.reg, manager=True))
        dom = _shift_scope_domain(env, 'ctv')
        self.assertIn(('shift_type', '=', 'ctv'), dom)
```

Register it in `custom-addons/hocba_hrm/tests/__init__.py` by adding at the end:

```python
from . import test_shift_scope
```

- [ ] **Step 2: Run tests to verify they fail**

Run the controller test command (tag `/hocba_hrm`).
Expected: FAIL — `_shift_scope_domain` import error / not defined.

- [ ] **Step 3: Add `_shift_scope_domain`**

In `custom-addons/hocba_hrm/controllers/main.py`, add this function immediately before `_shift_row` (before line 740):

```python
def _shift_scope_domain(env, type_filter=None):
    """Domain trên hocba.work_shift theo người xem (Section 2 spec).
    - Manager: theo _emp_scope_domain (dịch sang employee_id.*) + lọc loại nếu gửi.
    - CTV (x_employment_status='ctv'): chỉ thấy ca CTV (của mọi người).
    - NV thường: chỉ thấy ca OT (của mọi người)."""
    if _user_can_manage(env):
        dom = []
        for field, op, val in _emp_scope_domain(env):
            if field == 'id':
                dom.append(('employee_id', op, val))
            else:
                dom.append(('employee_id.%s' % field, op, val))
        if type_filter in ('ot', 'ctv'):
            dom.append(('shift_type', '=', type_filter))
        return dom
    emp = env.user.employee_id
    is_ctv = bool(emp) and emp.x_employment_status == 'ctv'
    return [('shift_type', '=', 'ctv' if is_ctv else 'ot')]
```

- [ ] **Step 4: Extend `_shift_row`**

In `_shift_row` (lines 740-759), add four keys to the returned dict (after the existing `'shiftType': s.shift_type,` line):

```python
        'shiftTypeLabel': 'CTV' if s.shift_type == 'ctv' else 'OT',
        'deadline': _dt_local(s, s.deadline),
        'locked': bool(s.deadline) and fields.Datetime.now() >= s.deadline,
        'mine': bool(s.env.user.employee_id) and s.employee_id.id == s.env.user.employee_id.id,
```

- [ ] **Step 5: Rewrite `_shifts_week` visibility + signature**

Replace the `_shifts_week` signature line (803) and the visibility block (lines 816-829) so it accepts `type_filter`, runs the lazy reject, and scopes by shift type:

```python
def _shifts_week(env, monday_str, type_filter=None):
```

Then replace lines 816-828 (`can_manage = ...` through the `domain = [...] + visible` line) with:

```python
    can_manage = _user_can_manage(env)
    scope = _shift_scope_domain(env, type_filter)
    env['hocba.work_shift'].sudo()._auto_reject_expired(scope)  # lazy backstop (Section 3)
    me = user.employee_id
    if can_manage:
        visible = scope
    else:
        # NV thường/CTV: ca approved của mọi người cùng loại + ca của mình mọi state
        visible = scope + ['|', ('state', '=', 'approved'),
                           ('employee_id', '=', me.id if me else -1)]
    domain = [('start', '>=', start_utc), ('start', '<', end_utc)] + visible
```

- [ ] **Step 6: Pass the `type` param from the route**

Replace the `api_shifts_week` route (lines 2271-2273) with:

```python
    @http.route('/hocba-hrm/api/shifts/week', auth='user', type='http', methods=['GET'])
    def api_shifts_week(self, monday=None, type=None, **kw):
        return request.make_json_response(_shifts_week(request.env, monday, type))
```

- [ ] **Step 7: Run tests to verify they pass**

Run the controller test command.
Expected: PASS — 4 new tests pass; existing `/hocba_hrm` shift tests still pass.

- [ ] **Step 8: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_scope.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance): shift visibility by type + type filter + lazy auto-reject

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Controller — time-gated decide/edit/reject/level/cancel

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — `_shift_decide` (lines 843-876), `_shift_set_level` (lines 879-895), `_shift_cancel` (lines 898-912).
- Create: `custom-addons/hocba_hrm/tests/test_shift_deadline_guard.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: `shift._assert_actionable()` (Task 1).
- Produces: `_shift_decide` now allows acting on `pending` OR `approved` shifts (blocks `rejected`), and all three helpers raise `UserError` past the deadline.

- [ ] **Step 1: Write the failing tests**

Create `custom-addons/hocba_hrm/tests/test_shift_deadline_guard.py`:

```python
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _shift_decide


@tagged('post_install', '-at_install')
class TestShiftDeadlineGuard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.mgr_user = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_guard',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def _shift(self, start, state='pending'):
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'shift_type': 'ot', 'state': state,
                'start': start, 'end': start + timedelta(hours=2)})

    def test_decide_blocked_after_deadline(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() - timedelta(hours=1))
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, True, {})

    def test_decide_approved_shift_can_be_rejected_before_deadline(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() + timedelta(hours=2), state='approved')
        _shift_decide(env, s.id, False, {'reviewNote': 'đổi ý'})
        self.assertEqual(s.state, 'rejected')

    def test_decide_rejected_shift_is_already_decided(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() + timedelta(hours=2), state='rejected')
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, True, {})
```

Register it in `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_shift_deadline_guard
```

- [ ] **Step 2: Run tests to verify they fail**

Run the controller test command.
Expected: FAIL — `test_decide_approved_shift_can_be_rejected_before_deadline` fails (`already_decided` raised for approved), and the deadline tests fail (no guard yet).

- [ ] **Step 3: Implement the guards**

In `_shift_decide`, replace the state check (line 852) and add the deadline guard. The block currently reads:

```python
    if shift.state != 'pending':
        raise UserError('already_decided')
```

Replace with:

```python
    if shift.state == 'rejected':
        raise UserError('already_decided')
    shift._assert_actionable()
```

In `_shift_set_level`, after the scope check (after line 889) and before the `if shift.state != 'approved':` check, add:

```python
    shift._assert_actionable()
```

In `_shift_cancel`, after the scope check (after line 908) and before the `if shift.state != 'pending':` check, add:

```python
    shift._assert_actionable()
```

- [ ] **Step 4: Run tests to verify they pass**

Run the controller test command.
Expected: PASS — 3 new tests pass; existing shift-decide tests still pass.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_shift_deadline_guard.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance): time-gate shift decide/level/cancel; allow edit/reject of approved before deadline

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Controller — employee search by code (manager add-for-anyone)

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — add `_employee_search` helper + `GET /api/employees/search` route.
- Create: `custom-addons/hocba_hrm/tests/test_employee_search.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: `_user_can_manage`, `_emp_scope_domain`.
- Produces:
  - `_employee_search(env, q) -> list[{id, code, name, employmentStatus}]` (empty for non-managers / empty query).
  - route `GET /hocba-hrm/api/employees/search?q=` → `{rows: [...]}`.

- [ ] **Step 1: Write the failing tests**

Create `custom-addons/hocba_hrm/tests/test_employee_search.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _employee_search


@tagged('post_install', '-at_install')
class TestEmployeeSearch(TransactionCase):

    def setUp(self):
        super().setUp()
        self.target = self.env['hr.employee'].create({
            'name': 'Nguyen Van Tim', 'x_employee_code': 'EMP-TIM-001'})
        self.mgr = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_search',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_search',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

    def test_manager_finds_by_code(self):
        rows = _employee_search(self.env(user=self.mgr), 'EMP-TIM')
        self.assertTrue(any(r['code'] == 'EMP-TIM-001' for r in rows))

    def test_manager_finds_by_name(self):
        rows = _employee_search(self.env(user=self.mgr), 'Van Tim')
        self.assertTrue(any(r['id'] == self.target.id for r in rows))

    def test_non_manager_gets_empty(self):
        self.assertEqual(_employee_search(self.env(user=self.plain), 'EMP-TIM'), [])

    def test_empty_query_gets_empty(self):
        self.assertEqual(_employee_search(self.env(user=self.mgr), '  '), [])
```

Register it in `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_employee_search
```

- [ ] **Step 2: Run tests to verify they fail**

Run the controller test command.
Expected: FAIL — `_employee_search` not defined.

- [ ] **Step 3: Implement the helper**

In `custom-addons/hocba_hrm/controllers/main.py`, add this function immediately before `_shift_scope_domain` (from Task 4):

```python
def _employee_search(env, q):
    """Tìm NV theo mã (x_employee_code) hoặc tên cho manager (add-for-anyone).
    [] nếu không phải manager hoặc query rỗng. Giới hạn theo phạm vi vai trò."""
    if not _user_can_manage(env):
        return []
    q = (q or '').strip()
    if not q:
        return []
    domain = ['|', ('x_employee_code', 'ilike', q), ('name', 'ilike', q)]
    domain += _emp_scope_domain(env)
    emps = env['hr.employee'].sudo().search(domain, limit=20)
    return [{
        'id': e.id,
        'code': e.x_employee_code or '—',
        'name': e.name,
        'employmentStatus': e.x_employment_status or '',
    } for e in emps]
```

- [ ] **Step 4: Add the route**

In `custom-addons/hocba_hrm/controllers/main.py`, add this route inside the controller class, right after `api_shift_set_level` (after line 2334):

```python
    @http.route('/hocba-hrm/api/employees/search', auth='user',
                type='http', methods=['GET'])
    def api_employee_search(self, q=None, **kw):
        return request.make_json_response(
            {'rows': _employee_search(request.env, q)})
```

- [ ] **Step 5: Run tests to verify they pass**

Run the controller test command.
Expected: PASS — 4 new tests pass.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_employee_search.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance): employee search by code for manager add-for-anyone

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Controller — correction requests only from records + recompute preview

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py` — `_request_create` (lines 659-683); add `_request_preview` + route.
- Create: `custom-addons/hocba_hrm/tests/test_request_preview.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: `_to_utc`, `_dt_local`, `_user_can_manage`, `_emp_in_scope`.
- Produces:
  - `_request_create` raises `ValidationError('Bản ghi không hợp lệ.')` when `attendanceId` is missing/foreign.
  - `_request_preview(env, req_id, body) -> dict` with `workingHours, workCredit, expectedCheckOut, earlyLeaveMinutes, missingMinutes, lateMinutes, needsReview`.
  - route `POST /hocba-hrm/api/attendance/requests/<id>/preview`.

- [ ] **Step 1: Write the failing tests**

Create `custom-addons/hocba_hrm/tests/test_request_preview.py`:

```python
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _request_create, _request_preview


@tagged('post_install', '-at_install')
class TestRequestPreview(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'NV B', 'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109', 'x_social_insurance_no': '0123456789'})
        self.user = self.env['res.users'].create({
            'name': 'NV B', 'login': 'nvb_prev',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp.user_id = self.user
        self.mgr = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_prev',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})
        self.att = self.env['hocba.attendance'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'check_in': '2026-06-17 02:00:00'})

    def test_create_requires_attendance_id(self):
        env = self.env(user=self.user)
        with self.assertRaises(ValidationError):
            _request_create(env, {'reason': 'quên', 'requestDate': '2026-06-17'})

    def test_create_with_record_ok(self):
        env = self.env(user=self.user)
        row = _request_create(env, {'attendanceId': self.att.id, 'reason': 'quên ra',
                                    'checkOut': '2026-06-17T17:00'})
        self.assertEqual(row['attendanceId'], self.att.id)

    def test_preview_recomputes_full_day(self):
        env = self.env(user=self.user)
        row = _request_create(env, {'attendanceId': self.att.id, 'reason': 'quên ra'})
        req = self.env['hocba.attendance.request'].browse(row['id'])
        # 09:00–17:00 local = 02:00–10:00 UTC = đủ 8h, đủ công
        out = _request_preview(self.env(user=self.mgr), req.id,
                               {'checkIn': '2026-06-17T09:00', 'checkOut': '2026-06-17T17:00'})
        self.assertEqual(out['workCredit'], 1.0)
        self.assertEqual(out['missingMinutes'], 0)
        self.assertFalse(out['needsReview'])
```

Register it in `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_request_preview
```

- [ ] **Step 2: Run tests to verify they fail**

Run the controller test command.
Expected: FAIL — `_request_preview` not defined; `test_create_requires_attendance_id` fails (current code allows missing record).

- [ ] **Step 3: Tighten `_request_create`**

In `_request_create` (lines 669-678), replace the attendance-resolution block:

```python
    Att = env['hocba.attendance'].sudo()
    att_id = body.get('attendanceId') or None
    attendance = Att.browse(int(att_id)) if att_id else Att.browse()
    if att_id and (not attendance.exists() or attendance.employee_id != emp):
        raise ValidationError('Bản ghi không hợp lệ.')
    request_date = body.get('requestDate') or (attendance.date if att_id else False)
    req = env['hocba.attendance.request'].sudo().create({
        'employee_id': emp.id,
        'request_date': request_date,
        'attendance_id': attendance.id or False,
```

with (correction requests must target an existing record belonging to the user):

```python
    Att = env['hocba.attendance'].sudo()
    att_id = body.get('attendanceId') or None
    attendance = Att.browse(int(att_id)) if att_id else Att.browse()
    if not att_id or not attendance.exists() or attendance.employee_id != emp:
        raise ValidationError('Bản ghi không hợp lệ.')
    req = env['hocba.attendance.request'].sudo().create({
        'employee_id': emp.id,
        'request_date': attendance.date,
        'attendance_id': attendance.id,
```

- [ ] **Step 4: Add `_request_preview`**

In `custom-addons/hocba_hrm/controllers/main.py`, add this function immediately after `_request_decide` (after line 711):

```python
def _request_preview(env, req_id, body):
    """Tính thử (dry-run) các trường công khi áp giờ đề xuất, KHÔNG lưu.
    Manager xem trước khi duyệt. AccessError nếu vượt quyền; None nếu không tồn tại."""
    req = env['hocba.attendance.request'].sudo().browse(req_id)
    if not req.exists():
        return None
    if not (_user_can_manage(env) and _emp_in_scope(env, req.employee_id)):
        raise AccessError('forbidden')
    ci = _to_utc(env, body['checkIn']) if 'checkIn' in body else req.proposed_check_in
    co = _to_utc(env, body['checkOut']) if 'checkOut' in body else req.proposed_check_out
    draft = env['hocba.attendance'].sudo().new({
        'employee_id': req.employee_id.id,
        'check_in': ci or False,
        'check_out': co or False,
    })
    return {
        'workingHours': round(draft.working_hours, 2),
        'workCredit': draft.work_credit,
        'expectedCheckOut': _dt_local(req, draft.expected_check_out),
        'earlyLeaveMinutes': draft.early_leave_minutes,
        'missingMinutes': draft.missing_minutes,
        'lateMinutes': draft.late_minutes,
        'needsReview': draft.needs_review,
    }
```

- [ ] **Step 5: Add the preview route**

In `custom-addons/hocba_hrm/controllers/main.py`, add this route right after `api_attendance_request_reject` (after line 2251):

```python
    @http.route('/hocba-hrm/api/attendance/requests/<int:req_id>/preview',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_attendance_request_preview(self, req_id, **kw):
        try:
            row = _request_preview(request.env, req_id,
                                   request.get_json_data() or {})
        except AccessError:
            return request.make_json_response({'error': 'forbidden'}, status=403)
        if row is None:
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(row)
```

- [ ] **Step 6: Run tests to verify they pass**

Run the controller test command.
Expected: PASS — 3 new tests pass. Existing `test_attendance_request.py` may have a "missing day" test that now expects rejection — if any existing test creates a request without `attendanceId`, update it to attach a record or assert the `ValidationError`. Re-run until `0 failed`.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_request_preview.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(attendance): require record for correction requests + dry-run preview

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Frontend API — new endpoints + week type param

**Files:**
- Modify: `frontend/src/api/attendance.js`

**Interfaces:**
- Produces JS exports: `searchEmployees(q)`, `previewRequest(id, body)`, and `fetchWeekShifts(monday, type)` (added optional `type`).

- [ ] **Step 1: Update the API module**

In `frontend/src/api/attendance.js`, replace the `fetchWeekShifts` export (line 34-35):

```javascript
export const fetchWeekShifts = (monday, type) =>
  hbGet(`/hocba-hrm/api/shifts/week?monday=${monday}${type ? `&type=${type}` : ''}`);
```

Add these exports at the end of the file (after line 53):

```javascript
export const searchEmployees = (q) =>
  hbGet(`/hocba-hrm/api/employees/search?q=${encodeURIComponent(q)}`);
export const previewRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/preview`, body);
```

- [ ] **Step 2: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/attendance.js
git commit -m "feat(attendance-ui): API for employee search, request preview, week type filter

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Frontend — ShiftForm manager employee picker

**Files:**
- Modify: `frontend/src/features/attendance/ShiftForm.jsx`
- Modify: `frontend/src/features/attendance/ShiftCalendar.jsx:76` (pass `canManage` to `ShiftForm`)

**Interfaces:**
- Consumes: `searchEmployees` (Task 8), `createShift`.
- Produces: `ShiftForm` accepts a `canManage` prop; when true, submits `empId` of the selected employee.

- [ ] **Step 1: Add the employee picker to ShiftForm**

Replace the whole `frontend/src/features/attendance/ShiftForm.jsx` with:

```jsx
/* Form đăng ký ca làm việc (Gói 4A). User chọn giờ vào/ra (datetime-local),
   loại ca (CTV/OT), lý do. Manager: chọn NV theo mã/tên để thêm ca hộ. */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createShift, searchEmployees } from '../../api/attendance';

export default function ShiftForm({ canManage, onClose, onSaved }) {
  const [form, setForm] = useState({ start: '', end: '', shiftType: 'ot', otLevel: '100', reason: '' });
  const [emp, setEmp] = useState(null);          // {id, code, name}
  const [q, setQ] = useState('');
  const [opts, setOpts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function doSearch(text) {
    setQ(text); setEmp(null);
    if (!text.trim()) { setOpts([]); return; }
    try { const d = await searchEmployees(text); setOpts(d.rows || []); }
    catch { setOpts([]); }
  }

  async function submit() {
    if (canManage && !emp) { setErr('Vui lòng chọn nhân viên.'); return; }
    if (!form.start || !form.end) { setErr('Vui lòng chọn giờ bắt đầu và kết thúc.'); return; }
    setBusy(true); setErr(null);
    try {
      await createShift({
        empId: canManage && emp ? emp.id : undefined,
        start: form.start, end: form.end,
        shiftType: form.shiftType, otLevel: form.otLevel,
        reason: form.reason.trim(),
      });
      onSaved && onSaved();
      onClose();
    } catch (e) {
      setErr('Đăng ký ca thất bại (' + e.message + ').');
    } finally { setBusy(false); }
  }

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, flex: 1 }}>
          {canManage ? 'Thêm ca cho nhân viên' : 'Đăng ký ca làm việc'}
        </h2>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {canManage && (
          <label style={{ fontSize: 12.5 }}>Nhân viên (mã hoặc tên)
            {emp ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                <span style={{ fontWeight: 600 }}>{emp.name}</span>
                <span className="muted" style={{ fontSize: 12 }}>{emp.code}</span>
                <button className="btn btn-ghost btn-sm" onClick={() => { setEmp(null); setQ(''); }}>Đổi</button>
              </div>
            ) : (
              <>
                <input className="sel" value={q} placeholder="VD: EMP-001 hoặc Nguyễn…"
                  onChange={(e) => doSearch(e.target.value)} />
                {opts.length > 0 && (
                  <div style={{ border: '1px solid var(--border)', borderRadius: 8, marginTop: 4, maxHeight: 160, overflowY: 'auto' }}>
                    {opts.map((o) => (
                      <button key={o.id} onClick={() => { setEmp(o); setOpts([]); }}
                        style={{ display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', background: 'none', border: 'none', cursor: 'pointer' }}>
                        <span style={{ fontWeight: 600 }}>{o.name}</span>
                        <span className="muted" style={{ fontSize: 12, marginLeft: 6 }}>{o.code}</span>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </label>
        )}
        <label style={{ fontSize: 12.5 }}>Loại ca
          <select className="sel" value={form.shiftType}
            onChange={(e) => setForm({ ...form, shiftType: e.target.value,
              otLevel: e.target.value === 'ctv' ? '100' : form.otLevel })}>
            <option value="ot">Tăng ca (OT)</option>
            <option value="ctv">CTV</option>
          </select>
        </label>
        {form.shiftType === 'ot' && (
          <label style={{ fontSize: 12.5 }}>Mức hệ số
            <select className="sel" value={form.otLevel}
              onChange={(e) => setForm({ ...form, otLevel: e.target.value })}>
              <option value="100">100%</option>
              <option value="150">150%</option>
              <option value="300">300%</option>
            </select>
          </label>
        )}
        <label style={{ fontSize: 12.5 }}>Bắt đầu
          <input type="datetime-local" className="sel" value={form.start}
            onChange={(e) => setForm({ ...form, start: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Kết thúc
          <input type="datetime-local" className="sel" value={form.end}
            onChange={(e) => setForm({ ...form, end: e.target.value })} />
        </label>
        <label style={{ fontSize: 12.5 }}>Lý do
          <textarea className="sel" rows={2} value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={submit}>
            {canManage ? 'Thêm ca' : 'Đăng ký ca'}
          </button>
          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={onClose}>Hủy</button>
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Pass `canManage` from ShiftCalendar**

In `frontend/src/features/attendance/ShiftCalendar.jsx`, line 76, change:

```jsx
      {showForm && <ShiftForm onClose={() => setShowForm(false)} onSaved={load} />}
```

to:

```jsx
      {showForm && <ShiftForm canManage={canManage} onClose={() => setShowForm(false)} onSaved={load} />}
```

- [ ] **Step 3: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 4: Manual verification**

Run `cd frontend && npm run dev` (or use the built SPA at `/hocba-hrm`). As a manager, open Ca làm việc → Đăng ký ca → confirm an employee search box appears, typing a code/name lists matches, selecting one and submitting creates an approved shift for that employee.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/attendance/ShiftForm.jsx frontend/src/features/attendance/ShiftCalendar.jsx
git commit -m "feat(attendance-ui): manager add-for-anyone employee picker in ShiftForm

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Frontend — ShiftCalendar type filter, names, locked styling

**Files:**
- Modify: `frontend/src/features/attendance/ShiftCalendar.jsx`

**Interfaces:**
- Consumes: `fetchWeekShifts(monday, type)` (Task 8); row fields `empName`, `shiftTypeLabel`, `mine`, `locked` (Task 4).
- Produces: a manager-only OT/CTV filter; chips show employee name + type; locked chips dimmed.

- [ ] **Step 1: Add filter state and name/locked rendering**

In `frontend/src/features/attendance/ShiftCalendar.jsx`:

Add a `typeFilter` state after the `monday` state (after line 27):

```jsx
  const [typeFilter, setTypeFilter] = useState('');   // '' | 'ot' | 'ctv' (manager only)
```

Change `load` (lines 33-36) to pass the filter, and add `typeFilter` to the effect deps:

```jsx
  const load = () => {
    setErr(null); setData(null);
    fetchWeekShifts(ymd(monday), typeFilter || undefined).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [monday, typeFilter]);
```

In the toolbar row, add a filter control before the "Đăng ký ca" button. Replace the spacer + button (lines 54-55):

```jsx
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>Đăng ký ca</button>
```

with:

```jsx
        <div style={{ flex: 1 }} />
        {canManage && (
          <select className="sel" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            style={{ width: 'auto' }}>
            <option value="">Tất cả</option>
            <option value="ot">OT</option>
            <option value="ctv">CTV</option>
          </select>
        )}
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>Đăng ký ca</button>
```

Replace the shift chip (lines 65-71) so it shows the employee name and dims locked shifts:

```jsx
            {day.shifts.map((s) => (
              <button key={s.id} onClick={() => setSel(s)}
                style={{ display: 'block', width: '100%', textAlign: 'left', border: '1px solid ' + (s.mine ? 'var(--red-300,#fca5a5)' : 'var(--border)'), borderRadius: 8, padding: '6px 8px', marginBottom: 6, background: CHIP_BG[s.state], cursor: 'pointer', opacity: s.locked ? 0.6 : 1 }}>
                <div style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.empName}</div>
                <div className="mono" style={{ fontSize: 12, fontWeight: 600 }}>{fmtTime(s.start)}–{fmtTime(s.end)}</div>
                <div style={{ fontSize: 11 }}>{s.shiftTypeLabel} ×{s.rate}{s.locked ? ' · đã khóa' : ''}</div>
              </button>
            ))}
```

- [ ] **Step 2: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 3: Manual verification**

As a regular (non-CTV) employee, open Ca làm việc → confirm you see OT shifts of multiple employees (names shown) but no CTV shifts. As a CTV user, confirm only CTV shifts appear. As a manager, confirm the Tất cả/OT/CTV filter narrows the calendar and past-deadline shifts appear dimmed with "đã khóa".

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/ShiftCalendar.jsx
git commit -m "feat(attendance-ui): OT/CTV filter, employee names, locked styling in week calendar

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Frontend — ShiftDrawer edit/reject approved before deadline

**Files:**
- Modify: `frontend/src/features/attendance/ShiftDrawer.jsx`

**Interfaces:**
- Consumes: row fields `state`, `locked` (Task 4); `approveShift`, `rejectShift`, `cancelShift`.
- Produces: manager action panel for `pending` OR `approved` shifts while `!locked`; owner cancel for `pending` while `!locked`; a "đã khóa" notice when locked.

- [ ] **Step 1: Gate the panels on state + locked**

In `frontend/src/features/attendance/ShiftDrawer.jsx`:

Replace line 15:

```jsx
  const isPending = shift.state === 'pending';
```

with:

```jsx
  const isPending = shift.state === 'pending';
  const canAct = !shift.locked && shift.state !== 'rejected';   // duyệt/sửa/từ chối được
```

Replace the manager-panel guard (line 73):

```jsx
      {canManage && isPending && (
```

with:

```jsx
      {canManage && canAct && (
```

Replace the owner-cancel guard (line 103):

```jsx
      {!canManage && isPending && (
```

with:

```jsx
      {!canManage && isPending && !shift.locked && (
```

Add a locked notice. Immediately after the closing `</div>` of the details block (after line 71, before the `{canManage && canAct && (` panel), insert:

```jsx
      {shift.locked && (
        <div className="muted" style={{ padding: '0 24px 14px', fontSize: 12.5 }}>
          Đã quá hạn thao tác (trước giờ bắt đầu 1 phút) — không thể sửa/duyệt/từ chối.
        </div>
      )}
```

- [ ] **Step 2: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 3: Manual verification**

As a manager: open an already-approved future shift → confirm the edit fields + Duyệt/Từ chối buttons appear and rejecting it works. Open a shift whose start is in the past → confirm the "đã quá hạn" notice shows and no action buttons appear. Attempt to approve right at/after the deadline → backend returns the deadline error (shown in the panel).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/ShiftDrawer.jsx
git commit -m "feat(attendance-ui): allow manager edit/reject of approved shifts before deadline

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Frontend — correction requests only from history records

**Files:**
- Modify: `frontend/src/features/attendance/Attendance.jsx` (remove standalone forgot-form entry)
- Modify: `frontend/src/features/attendance/RequestForm.jsx` (require `attendanceId`; drop free-date mode)

**Interfaces:**
- Produces: `RequestForm` only usable with an `attendanceId` (always supplied by `AttendanceDrawer`).

- [ ] **Step 1: Remove the standalone entry in Attendance.jsx**

In `frontend/src/features/attendance/Attendance.jsx`:

Remove the `RequestForm` import (line 10):

```jsx
import RequestForm from './RequestForm';
```

Remove the `showForm` state (line 20):

```jsx
  const [showForm, setShowForm] = useState(false);
```

Replace the `requests` tab block (lines 77-89) so there is no standalone "Gửi đơn quên chấm công" button:

```jsx
      {activeTab === 'requests' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!isManager && (
            <div className="muted" style={{ fontSize: 12.5 }}>
              Để gửi đơn sửa/quên chấm công, mở một bản ghi trong “Lịch sử chấm công” rồi bấm “Gửi đơn sửa”.
            </div>
          )}
          <RequestList rows={reqs.rows} loading={reqs.loading} error={reqs.error}
            onReload={() => loadReqs(isManager)} canReview={isManager} />
        </div>
      )}
```

Remove the trailing standalone form render (lines 93-95):

```jsx
      {showForm && (
        <RequestForm onClose={() => setShowForm(false)} onSaved={() => loadReqs(false)} />
      )}
```

- [ ] **Step 2: Require `attendanceId` in RequestForm**

In `frontend/src/features/attendance/RequestForm.jsx`, update the header comment and the validation so the free-date path is gone. Replace lines 1-3 (comment) and the `submit` validation (lines 20-22):

Comment (lines 1-3):

```jsx
/* Form gửi đơn sửa chấm công (Gói 3). Chỉ mở từ một bản ghi chấm công có sẵn
   (AttendanceDrawer truyền attendanceId + requestDate). Không hỗ trợ ngày trống. */
```

Validation (inside `submit`, lines 21-22):

```jsx
    if (!attendanceId) { setErr('Đơn phải gắn với một bản ghi chấm công.'); return; }
    if (!form.reason.trim()) { setErr('Vui lòng nhập lý do.'); return; }
```

The `Ngày công` input is already `disabled={fixedDate}` and `fixedDate` is always true now (attendanceId required), so no further change is needed there.

- [ ] **Step 3: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds with no unused-import or undefined-variable errors.

- [ ] **Step 4: Manual verification**

As a regular employee: open the Đơn của tôi tab → confirm there is no standalone "Gửi đơn quên chấm công" button, only the helper hint + list. Open Lịch sử chấm công → click a record → "Gửi đơn sửa" → confirm the form submits successfully and the request appears in Đơn của tôi.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/attendance/Attendance.jsx frontend/src/features/attendance/RequestForm.jsx
git commit -m "feat(attendance-ui): correction requests only from history records

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: Frontend — RequestList recompute preview on approval

**Files:**
- Modify: `frontend/src/features/attendance/RequestList.jsx`

**Interfaces:**
- Consumes: `previewRequest(id, body)` (Task 8), `approveRequest`, `rejectRequest`.
- Produces: in the manager approval panel, read-only previews of giờ công / công ngày / giờ ra mong đợi / về sớm / phút thiếu / cờ kiểm tra that refresh when the proposed check-in/out change.

- [ ] **Step 1: Add the preview to RequestRow**

In `frontend/src/features/attendance/RequestList.jsx`:

Update the import (line 10):

```jsx
import { approveRequest, rejectRequest, previewRequest } from '../../api/attendance';
```

Add `useEffect` to the React import (line 4):

```jsx
import { useState, useEffect } from 'react';
```

In `RequestRow`, add preview state after the existing `useState` hooks (after line 37):

```jsx
  const [preview, setPreview] = useState(null);
```

Add an effect that refreshes the preview whenever ci/co change while reviewing (after the `act` function, before the `return`, i.e. after line 51):

```jsx
  useEffect(() => {
    if (!canReview || r.state !== 'pending') return;
    let alive = true;
    previewRequest(r.id, { checkIn: ci || null, checkOut: co || null })
      .then((p) => { if (alive) setPreview(p); })
      .catch(() => { if (alive) setPreview(null); });
    return () => { alive = false; };
  }, [ci, co, canReview, r.id, r.state]);
```

In the manager review block, add a preview row before the action buttons. Insert this right after the "Ghi chú" label/input (after line 89, before the Duyệt button):

```jsx
          {preview && (
            <div style={{ flexBasis: '100%', fontSize: 12, display: 'flex', gap: 14, flexWrap: 'wrap', color: 'var(--text-muted,#555)' }}>
              <span>Giờ công: <b>{preview.workingHours}</b></span>
              <span>Công ngày: <b>{preview.workCredit}</b></span>
              <span>Giờ ra mong đợi: <b>{preview.expectedCheckOut ? preview.expectedCheckOut.slice(11, 16) : '—'}</b></span>
              <span>Về sớm: <b>{preview.earlyLeaveMinutes > 0 ? preview.earlyLeaveMinutes + "'" : '—'}</b></span>
              <span>Phút thiếu: <b>{preview.missingMinutes > 0 ? preview.missingMinutes + "'" : '—'}</b></span>
              <span>Cờ kiểm tra: <b>{preview.needsReview ? 'Có' : 'Không'}</b></span>
            </div>
          )}
```

- [ ] **Step 2: Verify the build compiles**

Run: `cd frontend && npm run build`
Expected: build succeeds.

- [ ] **Step 3: Manual verification**

As a manager: open Đơn chấm công → for a pending correction request, change the Giờ vào / Giờ ra fields → confirm the preview row updates live (giờ công, công ngày, phút thiếu etc.), then Duyệt → open the underlying record in the day table and confirm the saved values match what the preview showed.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/attendance/RequestList.jsx
git commit -m "feat(attendance-ui): live recompute preview in correction-request approval

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final verification

- [ ] Run the full `/hocba_attendance` suite — `0 failed, 0 error(s) of N tests`, N non-zero.
- [ ] Run the full `/hocba_hrm` suite — `0 failed, 0 error(s) of N tests`, N non-zero.
- [ ] `cd frontend && npm run build` succeeds.
- [ ] Manual smoke of all five requirement areas (visibility, deadline gating + auto-reject, manager add-for-anyone, history-only correction requests, missing-minutes cap/half-day).
```
