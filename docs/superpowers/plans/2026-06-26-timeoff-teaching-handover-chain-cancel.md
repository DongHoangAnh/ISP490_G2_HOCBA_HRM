# Đổi lịch dạy chuyền tiếp + Hủy/Trả buổi + Đồng bộ DB↔FE — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho phép buổi dạy bàn giao chuyền tiếp không giới hạn (A→B→C…), cho chủ hiện tại "trả" buổi và người giao hủy/rút đơn với thông báo + đồng bộ lịch dạy về DB để FE luôn hiện đúng.

**Architecture:** `hocba.teaching.session.employee_id` luôn = chủ hiện tại; "ngăn xếp bàn giao" suy từ các `hocba.leave.session.resolution` (substitute + accepted + leave validate), `source_leave_id` trỏ đỉnh. Pop một lần bàn giao → về chủ liền trước, tính lại đỉnh từ resolution kế dưới. Không thêm bảng lịch sử.

**Tech Stack:** Odoo 19 (Python models + HTTP controller), React 18 + Vite SPA (`frontend/`), test bằng `odoo --test-enable`.

**Spec:** `docs/superpowers/specs/2026-06-26-timeoff-teaching-handover-chain-cancel-design.md`

**Lệnh test backend (chạy lại sau mỗi task có test):**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```
Mong đợi: `0 failed, 0 error(s) of N tests`.

---

## File Structure

- `models/hr_leave_teacher.py` — MODIFY: thêm kind `sub_cancelled`/`sub_returned`; `action_refuse(was_applied)`; `_revert_teaching_changes(was_applied)`; `_notify_sub_cancelled`.
- `models/hocba_teaching_session.py` — MODIFY: thêm `_pop_handover`.
- `models/hocba_leave_resolution.py` — MODIFY: thêm state `returned`.
- `controllers/main.py` — MODIFY: đổi lọc `_upcoming_teaching_sessions`/`_find_teaching_conflicts`; thêm `_return_substitution`, `_notify_substitute_returned`; sửa `api_request_cancel`; thêm route return; bổ sung payload `_my_request`; `_substitution_rows` thêm cờ ownership.
- `__manifest__.py` — MODIFY: bump version `19.0.13.0.0` → `19.0.14.0.0`.
- `tests/test_handover_chain.py` — CREATE: ca test §9 spec.
- `frontend/src/api/timeoff.js` — MODIFY: `returnSubstitution`.
- `frontend/src/features/timeoff/SubstitutionsPanel.jsx` — MODIFY: nút "Trả buổi".
- `frontend/src/features/timeoff/TimeOff.jsx` — MODIFY: cột "GV dạy thay".
- `frontend/src/components/NotificationBell.jsx` — MODIFY: 2 kind mới.

---

## Task 1: Thêm 2 kind chuông + state `returned`

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_teacher.py:76-87`
- Modify: `custom-addons/hocba_timeoff/models/hocba_leave_resolution.py:36-42`

- [ ] **Step 1: Thêm state `returned` cho resolution**

Trong `hocba_leave_resolution.py`, sửa field `state`:

```python
    state = fields.Selection(
        [('pending', 'Chờ GV thay đồng ý'),
         ('accepted', 'Đã chốt'),
         ('declined', 'GV thay từ chối'),
         ('returned', 'GV thay đã trả lại')],
        string='Trạng thái', required=True, index=True,
        help="'class_off' chốt ngay; 'substitute' chờ GV thay đồng ý; "
             "'returned' = đã trả lại buổi sau khi nhận.",
    )
```

- [ ] **Step 2: Thêm 2 kind chuông**

Trong `hr_leave_teacher.py`, sửa `HbLeaveNotification.kind`:

```python
    kind = fields.Selection(
        selection_add=[
            ('sub_request', 'Yêu cầu dạy thay'),
            ('sub_accepted', 'GV thay đồng ý'),
            ('sub_declined', 'GV thay từ chối'),
            ('sub_cancelled', 'Yêu cầu dạy thay đã hủy'),
            ('sub_returned', 'GV thay đã trả lại buổi'),
        ],
        ondelete={
            'sub_request': 'cascade',
            'sub_accepted': 'cascade',
            'sub_declined': 'cascade',
            'sub_cancelled': 'cascade',
            'sub_returned': 'cascade',
        },
    )
```

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_timeoff/models/hr_leave_teacher.py custom-addons/hocba_timeoff/models/hocba_leave_resolution.py
git commit -m "feat(timeoff): thêm state 'returned' cho buổi dạy thay + 2 kind chuông hủy/trả"
```

---

## Task 2: `_pop_handover` trên session + test chuỗi/trả buổi

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hocba_teaching_session.py` (thêm method cuối class, trước/ sau `_upsert_session`)
- Create: `custom-addons/hocba_timeoff/tests/test_handover_chain.py`
- Modify: `custom-addons/hocba_timeoff/tests/__init__.py`

- [ ] **Step 1: Đăng ký test file**

Thêm dòng vào `tests/__init__.py`:

```python
from . import test_handover_chain
```

- [ ] **Step 2: Viết test đỏ (chuỗi + trả buổi)**

Tạo `tests/test_handover_chain.py`:

```python
# ============================================================
# Test — Đổi lịch dạy chuyền tiếp (A→B→C), trả buổi, hủy/rút có chặn chuỗi.
# Owner: Nhật Anh. Spec: 2026-06-26-timeoff-teaching-handover-chain-cancel §9.
# ============================================================
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _upcoming_teaching_sessions, _find_teaching_conflicts, _return_substitution,
)


@tagged('post_install', '-at_install')
class TestHandoverChain(TransactionCase):

    def setUp(self):
        super().setUp()
        U = self.env['res.users']
        self.uA = U.create({'name': 'UA', 'login': 'hc_ua'})
        self.uB = U.create({'name': 'UB', 'login': 'hc_ub'})
        self.uC = U.create({'name': 'UC', 'login': 'hc_uc'})
        E = self.env['hr.employee']
        self.A = E.create({'name': 'GV A', 'x_cms_user_id': 'HC_A', 'user_id': self.uA.id})
        self.B = E.create({'name': 'GV B', 'x_cms_user_id': 'HC_B', 'user_id': self.uB.id})
        self.C = E.create({'name': 'GV C', 'x_cms_user_id': 'HC_C', 'user_id': self.uC.id})
        self.session = self.env['hocba.teaching.session'].create({
            'cms_session_id': 'HC-1', 'employee_id': self.A.id,
            'class_name': 'LX', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00'})
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        self.Res = self.env['hocba.leave.session.resolution']
        self.Notif = self.env['hb.leave.notification']

    def _handover(self, frm, to):
        """Tạo đơn nghỉ của `frm`, gắn substitute `to` (accepted), duyệt → áp lịch.
        Trả về (leave, resolution)."""
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': frm.id,
            'request_date_from': '2026-07-06', 'request_date_to': '2026-07-06'})
        if leave.state == 'draft':
            leave.action_confirm()
        res = self.Res.create({
            'leave_id': leave.id, 'session_id': self.session.id,
            'resolution': 'substitute', 'substitute_id': to.id})
        res.state = 'accepted'
        leave.action_approve()
        return leave, res

    # ---------- §9.2: chuỗi A→B→C ----------
    def test_chain_apply(self):
        self._handover(self.A, self.B)
        self.assertEqual(self.session.employee_id, self.B)
        l_b, _ = self._handover(self.B, self.C)
        self.assertEqual(self.session.employee_id, self.C)
        self.assertEqual(self.session.state, 'substituted')
        self.assertEqual(self.session.source_leave_id, l_b)

    # ---------- §9.3: C trả buổi → về B, báo B ----------
    def test_return_top_reverts_to_previous(self):
        l_a, _ = self._handover(self.A, self.B)
        l_b, res_c = self._handover(self.B, self.C)
        out = _return_substitution(self.env, res_c.id, self.C)
        self.assertTrue(out)
        self.assertEqual(self.session.employee_id, self.B)
        self.assertEqual(self.session.state, 'substituted')
        self.assertEqual(self.session.source_leave_id, l_a)
        self.assertEqual(res_c.state, 'returned')
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_returned')])
        self.assertEqual(len(n), 1)

    # ---------- §9.4: trả buổi giữa chuỗi bị chặn ----------
    def test_return_middle_blocked(self):
        _, res_b = self._handover(self.A, self.B)
        self._handover(self.B, self.C)  # C đang giữ buổi
        out = _return_substitution(self.env, res_b.id, self.B)
        self.assertFalse(out)
        self.assertEqual(self.session.employee_id, self.C)
        self.assertEqual(res_b.state, 'accepted')

    # ---------- §9.5: pop về gốc → planned ----------
    def test_return_to_original_planned(self):
        _, res_b = self._handover(self.A, self.B)
        out = _return_substitution(self.env, res_b.id, self.B)
        self.assertTrue(out)
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        self.assertFalse(self.session.source_leave_id)
```

- [ ] **Step 3: Chạy test → đỏ**

Chạy lệnh test backend. Mong đợi: FAIL/ERROR vì `_return_substitution` chưa tồn tại (ImportError) và `_pop_handover` chưa có.

- [ ] **Step 4: Thêm `_pop_handover` vào session model**

Trong `hocba_teaching_session.py`, thêm method (sau `create`, trước `_import_from_cms`):

```python
    def _pop_handover(self, resolution):
        """Gỡ 1 lần bàn giao: đưa buổi về chủ liền trước (= leave.employee_id của
        `resolution`), tính lại đỉnh stack từ lần bàn giao kế dưới (substitute đã
        accepted, đơn đang validate, substitute_id = chủ liền trước). Hết → về
        original_employee_id / 'planned'. KHÔNG tự đổi resolution.state."""
        self.ensure_one()
        prev_owner = resolution.leave_id.employee_id
        below = self.env['hocba.leave.session.resolution'].sudo().search([
            ('session_id', '=', self.id),
            ('resolution', '=', 'substitute'),
            ('state', '=', 'accepted'),
            ('substitute_id', '=', prev_owner.id),
            ('leave_id.state', '=', 'validate'),
            ('id', '!=', resolution.id),
        ], order='id desc', limit=1)
        vals = {'employee_id': (prev_owner.id
                                or self.original_employee_id.id
                                or self.employee_id.id)}
        if below:
            vals['state'] = 'substituted'
            vals['source_leave_id'] = below.leave_id.id
        else:
            vals['state'] = 'planned'
            vals['source_leave_id'] = False
        self.write(vals)
```

- [ ] **Step 5: Thêm `_return_substitution` + `_notify_substitute_returned` vào controller**

Trong `controllers/main.py`, ngay sau `_decide_substitution` (kết thúc ~dòng 678), thêm:

```python
def _notify_substitute_returned(env, resolution):
    """Báo người giao (chủ liền trước) khi chủ hiện tại trả lại buổi dạy thay."""
    giver_user = resolution.leave_id.employee_id.sudo().user_id
    if not giver_user:
        return
    _push_notification(
        env, giver_user, resolution.leave_id, 'sub_returned',
        'Giáo viên thay đã trả lại buổi',
        '%s đã trả lại buổi %s — vui lòng xử lý lại lịch dạy.' % (
            resolution.substitute_id.sudo().name,
            resolution.session_id.display_name))


def _return_substitution(env, res_id, employee):
    """Chủ hiện tại trả lại buổi đã nhận. Trả record hoặc False.

    False khi: không tồn tại / không phải GV thay của mình / không phải đỉnh stack
    (đã giao tiếp xuống dưới) / không ở trạng thái accepted."""
    r = env['hocba.leave.session.resolution'].sudo().browse(res_id)
    if not r.exists() or r.resolution != 'substitute' or r.state != 'accepted':
        return False
    if r.substitute_id.id != (employee.id if employee else 0):
        return False
    session = r.session_id
    # Chỉ trả được khi đang là đỉnh stack (chưa giao tiếp xuống dưới).
    if session.source_leave_id.id != r.leave_id.id:
        return False
    session._pop_handover(r)
    r.write({'state': 'returned', 'decided_at': fields.Datetime.now()})
    _notify_substitute_returned(env, r)
    return r
```

- [ ] **Step 6: Chạy test → xanh**

Chạy lệnh test backend. Mong đợi: 4 test mới của `TestHandoverChain` PASS (`test_chain_apply`, `test_return_top_reverts_to_previous`, `test_return_middle_blocked`, `test_return_to_original_planned`), `0 failed`.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_timeoff/models/hocba_teaching_session.py custom-addons/hocba_timeoff/controllers/main.py custom-addons/hocba_timeoff/tests/test_handover_chain.py custom-addons/hocba_timeoff/tests/__init__.py
git commit -m "feat(timeoff): chuỗi bàn giao buổi dạy + trả buổi về GV liền trước"
```

---

## Task 3: Chủ hiện tại thấy buổi đã nhận (Gap hiển thị)

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py:542-547` (`_find_teaching_conflicts`) và `:567-572` (`_upcoming_teaching_sessions`)
- Modify: `custom-addons/hocba_timeoff/tests/test_handover_chain.py`

- [ ] **Step 1: Viết test đỏ**

Thêm vào `TestHandoverChain`:

```python
    # ---------- §9.1: chủ mới thấy buổi đã nhận; chủ cũ không còn thấy ----------
    def test_visibility_follows_owner(self):
        self._handover(self.A, self.B)
        up_b = _upcoming_teaching_sessions(self.env, self.B)
        self.assertIn(self.session, up_b)
        up_a = _upcoming_teaching_sessions(self.env, self.A)
        self.assertNotIn(self.session, up_a)
        conf_b = _find_teaching_conflicts(
            self.env, self.B, '2026-07-06', '2026-07-06')
        self.assertIn(self.session, conf_b)
```

Lưu ý: buổi ngày `2026-07-06`. Nếu `_upcoming_teaching_sessions` lọc theo "hôm nay → +28 ngày" và ngày test đã quá khứ so với ngày chạy, đổi `session_date` trong `setUp` sang ngày tương lai cố định (vd `'2027-01-04'`) cho cả file để test ổn định. Cập nhật mọi `request_date_*` tương ứng.

- [ ] **Step 2: Chạy test → đỏ**

Mong đợi: `test_visibility_follows_owner` FAIL — `assertIn(self.session, up_b)` sai vì buổi state `substituted` đang bị loại.

- [ ] **Step 3: Đổi điều kiện lọc**

Trong `_find_teaching_conflicts`, đổi:

```python
    return env['hocba.teaching.session'].sudo().search([
        ('employee_id', '=', employee.id),
        ('state', 'in', ['planned', 'substituted']),
        ('session_date', '>=', date_from),
        ('session_date', '<=', date_to),
    ], order='session_date, start_time')
```

Trong `_upcoming_teaching_sessions`, đổi:

```python
    return env['hocba.teaching.session'].sudo().search([
        ('employee_id', '=', employee.id),
        ('state', 'in', ['planned', 'substituted']),
        ('session_date', '>=', today),
        ('session_date', '<=', horizon),
    ], order='session_date, start_time')
```

Đồng thời cập nhật docstring 2 hàm: bỏ chữ "planned" cứng, ghi "buổi đang hoạt động (planned + substituted) của chủ hiện tại".

- [ ] **Step 4: Chạy test → xanh**

Mong đợi: `test_visibility_follows_owner` PASS; các test cũ vẫn xanh.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/main.py custom-addons/hocba_timeoff/tests/test_handover_chain.py
git commit -m "feat(timeoff): hiện buổi đã nhận cho chủ hiện tại để xin nghỉ/giao tiếp"
```

---

## Task 4: Refuse/withdraw — chặn chuỗi + báo GV thay; class_off pop

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_teacher.py:40-69`
- Modify: `custom-addons/hocba_timeoff/tests/test_handover_chain.py`

- [ ] **Step 1: Viết test đỏ**

Thêm vào `TestHandoverChain`:

```python
    # ---------- §9.7: rút đơn đã duyệt → revert + báo GV thay ----------
    def test_refuse_reverts_and_notifies_substitute(self):
        l_a, _ = self._handover(self.A, self.B)
        l_a.action_refuse()
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_cancelled')])
        self.assertEqual(len(n), 1)

    # ---------- §9.8: chặn rút khi buổi đã giao tiếp xuống dưới ----------
    def test_refuse_blocked_when_downstream_exists(self):
        l_a, _ = self._handover(self.A, self.B)
        self._handover(self.B, self.C)  # buổi giờ do C giữ
        with self.assertRaises(ValidationError):
            l_a.action_refuse()
        self.assertEqual(self.session.employee_id, self.C)

    # ---------- §9.9: class_off → refuse trả về planned ----------
    def test_class_off_refuse_reverts_planned(self):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.A.id,
            'request_date_from': self.session.session_date,
            'request_date_to': self.session.session_date})
        if leave.state == 'draft':
            leave.action_confirm()
        self.Res.create({
            'leave_id': leave.id, 'session_id': self.session.id,
            'resolution': 'class_off'})
        leave.action_approve()
        self.assertEqual(self.session.state, 'cancelled')
        leave.action_refuse()
        self.assertEqual(self.session.state, 'planned')

    # ---------- §9.6: refuse đơn pending không revert/không lỗi ----------
    def test_refuse_pending_leave_no_revert(self):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.A.id,
            'request_date_from': self.session.session_date,
            'request_date_to': self.session.session_date})
        if leave.state == 'draft':
            leave.action_confirm()
        self.Res.create({
            'leave_id': leave.id, 'session_id': self.session.id,
            'resolution': 'substitute', 'substitute_id': self.B.id, 'state': 'accepted'})
        leave.action_refuse()  # chưa duyệt → không đổi lịch, không lỗi
        self.assertEqual(self.session.employee_id, self.A)
        self.assertEqual(self.session.state, 'planned')
```

- [ ] **Step 2: Chạy test → đỏ**

Mong đợi: `test_refuse_reverts_and_notifies_substitute` FAIL (chưa có chuông `sub_cancelled`); `test_refuse_blocked_when_downstream_exists` FAIL (chưa chặn); có thể `test_class_off_refuse_reverts_planned` vẫn xanh nhờ revert cũ.

- [ ] **Step 3: Sửa `action_refuse` + `_revert_teaching_changes` + thêm `_notify_sub_cancelled`**

Thay block `action_refuse`/`_revert_teaching_changes` trong `hr_leave_teacher.py` bằng:

```python
    def action_refuse(self):
        # Chụp trước tập đơn ĐÃ ÁP lịch (state validate) — super() sẽ đổi state.
        applied = self.filtered(lambda l: l.state == 'validate')
        res = super().action_refuse()
        for leave in self:
            leave._revert_teaching_changes(was_applied=leave in applied)
        return res

    def _revert_teaching_changes(self, was_applied=True):
        """Đơn đã duyệt bị từ chối/rút → trả lịch dạy về chủ liền trước.
        Đơn chờ duyệt (chưa áp lịch) → bỏ qua. Chặn nếu buổi đã giao tiếp
        xuống dưới (phải gỡ chuỗi sau trước)."""
        self.ensure_one()
        if not was_applied:
            return
        for r in self.teaching_resolution_ids:
            session = r.session_id
            if session.source_leave_id and session.source_leave_id.id != self.id:
                raise ValidationError(_(
                    'Không thể hủy/từ chối: buổi %s đã được giao tiếp cho giáo '
                    'viên khác. Cần gỡ các thay đổi phía sau trước.',
                    session.display_name))
            if session.source_leave_id.id == self.id:
                session.sudo()._pop_handover(r)
                if r.resolution == 'substitute' and r.state == 'accepted':
                    self._notify_sub_cancelled(r)

    def _notify_sub_cancelled(self, resolution):
        """Báo GV thay khi đơn (đã/đang nhờ dạy thay) bị hủy/rút."""
        sub_user = resolution.substitute_id.sudo().user_id
        if not sub_user:
            return
        self.env['hb.leave.notification'].sudo().create({
            'recipient_id': sub_user.id,
            'leave_id': self.id,
            'kind': 'sub_cancelled',
            'title': 'Yêu cầu dạy thay đã hủy',
            'body': '%s đã hủy/rút đơn — bạn không cần dạy thay buổi %s nữa.' % (
                self.employee_id.sudo().name,
                resolution.session_id.display_name),
        })
```

Giữ nguyên `_apply_teaching_changes` (không đổi).

- [ ] **Step 4: Chạy test → xanh**

Mong đợi: cả 4 test mới PASS. Đặc biệt `test_refuse_reverts_schedule_changes` cũ trong `test_teacher_approval.py` vẫn xanh (refuse đơn đã duyệt 1 cấp → pop về gốc).

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_timeoff/models/hr_leave_teacher.py custom-addons/hocba_timeoff/tests/test_handover_chain.py
git commit -m "feat(timeoff): hủy/rút đơn dạy thay — revert chủ liền trước, báo GV thay, chặn chuỗi"
```

---

## Task 5: Báo GV thay khi hủy đơn chờ duyệt

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py:1422-1429` (trong `api_request_cancel`)
- Modify: `custom-addons/hocba_timeoff/tests/test_handover_chain.py`

- [ ] **Step 1: Viết test đỏ (gọi thẳng helper model)**

Thêm vào `TestHandoverChain`:

```python
    # ---------- Hủy đơn pending → báo GV thay (qua helper model) ----------
    def test_notify_sub_cancelled_helper(self):
        leave = self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.A.id,
            'request_date_from': self.session.session_date,
            'request_date_to': self.session.session_date})
        if leave.state == 'draft':
            leave.action_confirm()
        r = self.Res.create({
            'leave_id': leave.id, 'session_id': self.session.id,
            'resolution': 'substitute', 'substitute_id': self.B.id})
        leave._notify_sub_cancelled(r)
        n = self.Notif.search([
            ('recipient_id', '=', self.uB.id), ('kind', '=', 'sub_cancelled')])
        self.assertEqual(len(n), 1)
```

- [ ] **Step 2: Chạy test → xanh ngay**

`_notify_sub_cancelled` đã có từ Task 4 → test này PASS. (Đây là test bảo vệ; nếu đã xanh, sang bước sửa controller.)

- [ ] **Step 3: Sửa `api_request_cancel` để báo trước khi unlink**

Trong `api_request_cancel`, ngay trước khối `try: ... unlink()`, thêm:

```python
        # Báo các GV thay (đơn chờ duyệt: lịch chưa đổi nên chỉ cần báo hủy).
        for r in leave.teaching_resolution_ids.filtered(
                lambda x: x.resolution == 'substitute'
                and x.state in ('pending', 'accepted')):
            leave._notify_sub_cancelled(r)
```

- [ ] **Step 4: Chạy test → xanh**

Mong đợi: toàn bộ suite `0 failed`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/main.py custom-addons/hocba_timeoff/tests/test_handover_chain.py
git commit -m "feat(timeoff): hủy đơn chờ duyệt báo GV thay (sub_cancelled)"
```

---

## Task 6: Route HTTP trả buổi + cờ ownership cho panel

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py` (thêm route sau `api_substitution_decide` ~1196; sửa `_substitution_rows` ~640-660)

- [ ] **Step 1: Thêm cờ `canReturn` vào `_substitution_rows`**

Trong `_substitution_rows`, sửa dict `rows.append({...})` thêm 2 khóa (sau `'state'`):

```python
            'state': r.state,
            'isOwner': s.employee_id.id == employee.id,
            'canReturn': (r.state == 'accepted'
                          and s.employee_id.id == employee.id
                          and s.source_leave_id.id == r.leave_id.id),
```

(GV thay chỉ "trả" được buổi mình đang giữ và là đỉnh stack.)

- [ ] **Step 2: Thêm route trả buổi**

Sau `api_substitution_decide`, thêm:

```python
    @http.route('/hocba-hrm/api/timeoff/substitutions/<int:res_id>/return',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_substitution_return(self, res_id, **kw):
        emp = request.env.user.employee_id
        if not emp:
            return request.make_json_response({'error': 'no_employee'}, status=403)
        r = _return_substitution(request.env, res_id, emp)
        if not r:
            return request.make_json_response(
                {'error': 'cannot_return',
                 'message': 'Không thể trả buổi này (đã giao tiếp cho GV khác '
                            'hoặc không hợp lệ).'}, status=400)
        return request.make_json_response(
            {'items': _substitution_rows(request.env, emp)})
```

- [ ] **Step 3: Khởi động lại container (route Python cần reload)**

```bash
docker restart odoo19-odoo-1
```

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/main.py
git commit -m "feat(timeoff): API trả buổi dạy thay + cờ canReturn cho panel"
```

---

## Task 7: Payload cột "GV dạy thay" (tab Của tôi)

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py:983-1005` (`_my_request`)

- [ ] **Step 1: Thêm `substituteNames` + `sessionResolutions` vào `_my_request`**

Trong `_my_request`, ngay trước `return {`, thêm tính toán:

```python
        sub_names, sess_res = [], []
        if leave.holiday_status_id.id == _teaching_off_type_id(request.env):
            for r in leave.teaching_resolution_ids:
                s = r.session_id.sudo()
                if r.resolution == 'class_off':
                    label = 'Cả lớp nghỉ'
                else:
                    label = r.substitute_id.sudo().name or '—'
                    if label not in sub_names:
                        sub_names.append(label)
                sess_res.append({
                    'date': _d(s.session_date),
                    'className': s.class_name or '',
                    'kind': r.resolution,
                    'substituteName': (r.substitute_id.sudo().name or ''
                                       if r.resolution == 'substitute' else ''),
                    'state': r.state,
                })
```

Rồi thêm vào dict trả về (sau `'sessionCount'`):

```python
            'sessionCount': len(leave.teaching_resolution_ids),
            'substituteNames': ', '.join(sub_names) if sub_names else (
                'Cả lớp nghỉ' if sess_res else ''),
            'sessionResolutions': sess_res,
```

- [ ] **Step 2: Khởi động lại container**

```bash
docker restart odoo19-odoo-1
```

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/main.py
git commit -m "feat(timeoff): payload GV dạy thay cho tab 'Của tôi'"
```

---

## Task 8: FE — API + nút Trả buổi + cột GV dạy thay + chuông

**Files:**
- Modify: `frontend/src/api/timeoff.js`
- Modify: `frontend/src/features/timeoff/SubstitutionsPanel.jsx`
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`
- Modify: `frontend/src/components/NotificationBell.jsx`

- [ ] **Step 1: Thêm API `returnSubstitution`**

Trong `frontend/src/api/timeoff.js`, cạnh `decideSubstitution`, thêm:

```js
// POST trả lại buổi dạy thay đã nhận → trả { items } đã refresh
export const returnSubstitution = (resId) =>
  hbPost(`/hocba-hrm/api/timeoff/substitutions/${resId}/return`, {});
```

(Dùng đúng helper POST hiện có trong file — nếu tên là `hbPost`/`postJSON`, theo file.)

- [ ] **Step 2: Nút "Trả buổi" trong SubstitutionsPanel**

Trong `SubstitutionsPanel.jsx`: import `returnSubstitution`; với mỗi item có `item.canReturn`, render nút "Trả buổi" (xác nhận `window.confirm('Trả lại buổi dạy thay này? Buổi sẽ về lại giáo viên đã nhờ bạn.')` rồi gọi `returnSubstitution(item.id)` và refresh danh sách như `decideSubstitution`). Item `state==='pending'` giữ nút Đồng ý/Từ chối; `state==='accepted'` + `canReturn` hiện "Trả buổi"; trạng thái khác chỉ hiện nhãn.

- [ ] **Step 3: Cột "GV dạy thay" trong bảng "Đơn nghỉ của tôi"**

Trong `TimeOff.jsx`, bảng "Đơn nghỉ của tôi": thêm `<th>GV dạy thay</th>` giữa cột "Lý do" và "Trạng thái"; mỗi hàng thêm `<td>` hiển thị: nếu `r.isTeachingOff` → `r.substituteNames || '—'` (tùy chọn: tooltip/chi tiết từ `r.sessionResolutions`); ngược lại `—`.

- [ ] **Step 4: Chuông 2 kind mới**

Trong `NotificationBell.jsx`: thêm `sub_cancelled` và `sub_returned` vào `KIND_DOT` (màu phù hợp, vd đỏ nhạt cho cancelled, xanh dương cho returned). Điều hướng: `sub_cancelled` → mở tab phù hợp (vd 'mine' của GV thay hoặc 'substitutions'); `sub_returned` → mở 'mine' (người giao xử lý lại). Theo cơ chế `onItem(requestId, kind)` hiện có.

- [ ] **Step 5: Build SPA**

```bash
cd frontend && npm run build
```
Mong đợi: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src custom-addons/hocba_hrm/static/spa
git commit -m "feat(timeoff): FE trả buổi dạy thay + cột GV dạy thay + chuông hủy/trả"
```

---

## Task 9: Bump version + chạy toàn bộ test

**Files:**
- Modify: `custom-addons/hocba_timeoff/__manifest__.py`

- [ ] **Step 1: Bump version**

Trong `__manifest__.py`, đổi `'version'` từ `'19.0.13.0.0'` sang `'19.0.14.0.0'`.

- [ ] **Step 2: Chạy toàn bộ test backend**

Chạy lệnh test backend đầy đủ. Mong đợi: `0 failed, 0 error(s) of N tests` với N ≥ 69 (60 cũ + 9 ca mới).

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_timeoff/__manifest__.py
git commit -m "chore(timeoff): bump version 19.0.14.0.0"
```

---

## Verification cuối (trước khi báo hoàn thành)

- [ ] Chạy lại toàn bộ test backend: `0 failed`.
- [ ] Upgrade neondb (endpoint TRỰC TIẾP, bỏ `-pooler`) `-u hocba_timeoff` rồi `docker restart odoo19-odoo-1`.
- [ ] Smoke UI trên `/hocba-hrm`: A nghỉ buổi → B; HR duyệt; B vào form thấy buổi đã nhận, giao tiếp C; C trả → B nhận chuông; A rút khi C đang giữ → bị chặn; tab "Của tôi" của A hiện cột "GV dạy thay".
- [ ] Cập nhật memory `timeoff-teacher-session-leave` nếu hành vi đổi.
