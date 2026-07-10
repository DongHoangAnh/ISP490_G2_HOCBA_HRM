# Notify Phase 2–5 — Migrate timeoff + producers (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** Hợp nhất chuông timeoff về `hb.notification` (gỡ model/API cũ, migrate data, FE dùng 1 endpoint) rồi thêm producers: offboarding, onboarding/thử việc, nhắc hạn hồ sơ.

**Architecture:** Giữ nguyên chữ ký helper `_push_notification(env, recipient, leave, kind, title, body)` trong hocba_timeoff làm wrapper mỏng gọi `env['hb.notification']._notify(...)` (map kind→level, category='timeoff', target_ref=leave.id) → mọi caller hiện có không đổi. Model cũ + 2 inherit mở rộng kind + 3 route cũ bị gỡ; pre-migrate copy data. FE: 1 api client mới, bell map level→màu, App điều hướng theo targetView. Producers Phase 3–5 gọi `_notify` trực tiếp trong model action/cron với dedup_key cho cron.

**Tech Stack:** Odoo 19, TransactionCase, Docker local (db `hocba_hrm`), Vite/React SPA.

> Spec: `docs/superpowers/specs/2026-07-05-unified-notifications-design.md` §3–4. Test command (Git Bash, prefix BẮT BUỘC):
> ```bash
> MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
>   odoo -d hocba_hrm -u <modules>,hocba_employees --addons-path=/mnt/extra-addons \
>   --test-enable --test-tags <tags> --stop-after-init --log-level=test
> ```

## Map kind→level (dùng chung BE)

| level | kinds |
|---|---|
| warning | pending, withdraw_pending, sub_request, sub_returned, probation_eval, cert_expiry (sắp), contract_end |
| success | approved, sub_accepted, withdraw_approved, probation_pass, done (offb) |
| danger | refused, sub_declined, sub_cancelled, withdraw_refused, probation_fail, cert_expired |
| info | các kind còn lại |

---

## Task P2-BE: Migrate backend timeoff

**Files:**
- Modify: `custom-addons/hocba_timeoff/__manifest__.py` (version 19.0.14.0.0; depends += 'hocba_notify')
- Modify: `custom-addons/hocba_timeoff/controllers/main.py`
- Delete: `custom-addons/hocba_timeoff/models/hb_leave_notification.py` (+ bỏ import trong `models/__init__.py`)
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_teacher.py` (rewire `_notify_sub_cancelled`; xoá class inherit `HbLeaveNotification`)
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_withdraw.py` (xoá class inherit `HbLeaveNotification`, giữ `HrLeave`)
- Modify: `custom-addons/hocba_timeoff/security/ir.model.access.csv` (bỏ 2 dòng hb_leave_notification)
- Create: `custom-addons/hocba_timeoff/migrations/19.0.14.0.0/pre-migrate.py`
- Modify tests: `tests/test_notifications.py`, `tests/test_substitution.py`, `tests/test_handover_chain.py` (đổi model + `leave_id`→`target_ref`)

- [ ] Controller: thêm map level + wrapper (thay body `_push_notification`):
```python
_KIND_LEVEL = {
    'pending': 'warning', 'withdraw_pending': 'warning',
    'sub_request': 'warning', 'sub_returned': 'warning',
    'approved': 'success', 'sub_accepted': 'success', 'withdraw_approved': 'success',
    'refused': 'danger', 'sub_declined': 'danger', 'sub_cancelled': 'danger',
    'withdraw_refused': 'danger',
}

def _push_notification(env, recipient, leave, kind, title, body):
    """Wrapper mỏng → hb.notification (giữ chữ ký cũ cho mọi caller)."""
    if not recipient:
        return
    env['hb.notification'].sudo()._notify(
        recipient, category='timeoff', kind=kind,
        level=_KIND_LEVEL.get(kind, 'info'), title=title, body=body,
        target_view='timeoff', target_ref=leave.id,
        target_tab='sub' if kind.startswith('sub_') else None)
```
- [ ] Controller: XOÁ `_notif_row`, `_list_notifications`, `_mark_notification_read`, `_mark_all_notifications_read` + 3 route `api_notifications*`.
- [ ] `hr_leave_teacher.py`: `_notify_sub_cancelled` gọi `self.env['hb.notification'].sudo()._notify(sub_user, category='timeoff', kind='sub_cancelled', level='danger', title=..., body=..., target_view='timeoff', target_ref=self.id, target_tab='sub')` (title/body giữ nguyên chuỗi cũ); xoá class inherit kind.
- [ ] Migration `pre-migrate.py` (SQL, idempotent, bảng cũ có thể không tồn tại):
```python
def migrate(cr, version):
    cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name='hb_leave_notification'")
    if not cr.fetchone():
        return
    cr.execute("""
        INSERT INTO hb_notification
            (recipient_id, category, kind, level, title, body,
             target_view, target_ref, target_tab, is_read,
             create_date, write_date, create_uid, write_uid)
        SELECT n.recipient_id, 'timeoff', n.kind,
               CASE WHEN n.kind IN ('pending','withdraw_pending','sub_request','sub_returned') THEN 'warning'
                    WHEN n.kind IN ('approved','sub_accepted','withdraw_approved') THEN 'success'
                    WHEN n.kind IN ('refused','sub_declined','sub_cancelled','withdraw_refused') THEN 'danger'
                    ELSE 'info' END,
               n.title, n.body, 'timeoff', n.leave_id,
               CASE WHEN n.kind LIKE 'sub_%' THEN 'sub' ELSE NULL END,
               n.is_read, n.create_date, n.write_date, n.create_uid, n.write_uid
        FROM hb_leave_notification n
    """)
    cr.execute("DROP TABLE hb_leave_notification CASCADE")
```
- [ ] Tests: đổi `env['hb.leave.notification']` → `env['hb.notification']`, domain `leave_id` → `target_ref` (id), giữ assertions kind/recipient. Chạy: `--test-tags /hocba_timeoff,/hocba_notify` với `-u hocba_timeoff,hocba_notify,hocba_employees`. Kỳ vọng 0 failed với N>0 (suite timeoff ~50+ test + 14 notify).
- [ ] Commit.

## Task P2-FE: SPA chuông dùng endpoint chung

**Files:**
- Create: `frontend/src/api/notifications.js`
- Modify: `frontend/src/components/NotificationBell.jsx`, `frontend/src/app/App.jsx`, `frontend/src/app/Shell.jsx` (file CHUNG — chỉ đổi tối thiểu), `frontend/src/api/timeoff.js` (xoá 3 hàm notification)

- [ ] `api/notifications.js`:
```javascript
/* API chuông thông báo hợp nhất (hb.notification) — mọi module. */
import { hbGet, hbPost } from './client';

export const fetchNotifications = (limit = 20) =>
  hbGet(`/hocba-hrm/api/notifications?limit=${limit}`);
export const markNotificationRead = (id) =>
  hbPost(`/hocba-hrm/api/notifications/${id}/read`, {});
export const markAllNotificationsRead = () =>
  hbPost('/hocba-hrm/api/notifications/read-all', {});
```
- [ ] `NotificationBell.jsx`: import từ `../api/notifications`; thay `KIND_DOT` bằng `LEVEL_DOT = { info: 'var(--blue,#3b82f6)', success: 'var(--green,#10b981)', warning: 'var(--amber,#f59e0b)', danger: 'var(--red-600,#dc2626)' }`; chấm màu dùng `LEVEL_DOT[n.level]`; prop `onOpenRequest` → `onOpenNotification`; `onItem` gọi `onOpenNotification(n)` khi có handler.
- [ ] `Shell.jsx` Topbar: prop `onOpenRequest` → `onOpenNotification`, truyền xuống bell.
- [ ] `App.jsx`: thay `openRequest` bằng:
```javascript
const openNotification = (n) => {
  const view = n.targetView || 'timeoff';
  setView(view);
  if (view === 'timeoff') setFocus({ requestId: n.targetRef, kind: n.kind, nonce: Date.now() });
};
```
  và `<Topbar ... onOpenNotification={openNotification} />`.
- [ ] Xoá 3 hàm notification khỏi `api/timeoff.js`.
- [ ] `cd frontend && npm run build`; verify preview: login, chuông load `/api/notifications` 200, không lỗi console.
- [ ] Commit.

## Task P3: Producers offboarding

**Files:**
- Modify: `custom-addons/hocba_employees/__manifest__.py` (depends += 'hocba_notify')
- Modify: `custom-addons/hocba_employees/models/hocba_offboarding.py`
- Create: `custom-addons/hocba_employees/tests/test_offboarding_notify.py` (+ import trong tests/__init__.py)

- [ ] Thêm helper trong class `HocbaOffboarding`:
```python
def _notify_users(self, users, kind, level, title, body=None):
    self.env['hb.notification'].sudo()._notify(
        users, category='offboarding', kind=kind, level=level,
        title=title, body=body, target_view='offboarding', target_ref=self.id)

def _offb_manager_users(self):
    """QL trực tiếp + trưởng phòng (loại chính chủ)."""
    emp = self.employee_id.sudo()
    users = self.env['res.users']
    if emp.parent_id.user_id:
        users |= emp.parent_id.user_id
    if emp.department_id.manager_id.user_id:
        users |= emp.department_id.manager_id.user_id
    if emp.user_id:
        users -= emp.user_id
    return users

def _offb_hr_users(self):
    grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
    if not grp:
        return self.env['res.users']
    return self.env['res.users'].sudo().search(
        [('all_group_ids', 'in', grp.id), ('active', '=', True)])
```
- [ ] Hook cuối mỗi action (trong vòng for, sau message_post):
  - `action_submit`: `rec._notify_users(rec._offb_manager_users(), 'pending', 'warning', 'Đơn nghỉ việc mới chờ duyệt', '%s — %s' % (rec.employee_id.name, rec.name))`
  - `action_mgr_approve`: `rec._notify_users(rec._offb_hr_users(), 'pending', 'warning', 'Đơn nghỉ việc chờ HR duyệt', ...)`
  - `action_hr_approve`: báo `rec.employee_id.user_id` kind 'approved' level 'info', title 'Đơn nghỉ việc đã được HR duyệt'
  - `action_refuse`: báo `rec.employee_id.user_id` kind 'refused' level 'danger'
  - `action_done`: báo `rec._offb_manager_users()` kind 'done' level 'success' (NV đã bị khoá login)
- [ ] Test (TransactionCase, employee + parent mgr + HR user như `hocba_hrm/tests/test_offboarding_api.py` setUp): mỗi transition tạo đúng notification (search `hb.notification` theo `category='offboarding'`, `target_ref=rec.id`, kind, recipient). Chạy `--test-tags /hocba_employees` (`-u hocba_employees,hocba_notify`).
- [ ] Commit.

## Task P4: Producers onboarding/thử việc

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py`
- Create: `custom-addons/hocba_employees/tests/test_probation_notify.py` (+ import)

- [ ] Trong `_cron_probation_eval_reminders`, cạnh mỗi `_hocba_gate_activity(...)` thêm phát chuông (helper chung trong class HrEmployee):
```python
def _hocba_notify_probation(self, milestone, due):
    users = self.env['res.users']
    if self.parent_id.user_id:
        users |= self.parent_id.user_id
    grp = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
    if grp:
        users |= self.env['res.users'].sudo().search(
            [('all_group_ids', 'in', grp.id), ('active', '=', True)])
    self.env['hb.notification'].sudo()._notify(
        users, category='onboarding', kind='probation_eval', level='warning',
        title='Sắp đến hạn đánh giá %s: %s' % (milestone, self.name),
        body='Hạn: %s' % due, target_view='employees', target_ref=self.id,
        dedup_key='probation_eval:%s:%s:%s' % (self.id, milestone, due))
```
  gọi với milestone 'tuần-2'/'tháng-1'/'tháng-2' + due tương ứng.
- [ ] Kết quả cổng: tìm các nhánh xử lý pass→official / extend / fail trong gate methods (quanh `_hocba_start_offboarding` và chỗ ghi `x_employment_status='official'`) → phát tới `parent_id.user_id + user_id` (category 'onboarding', target_view='employees', target_ref=emp.id): `probation_pass`/success, `probation_extend`/warning, `probation_fail`/danger.
- [ ] Test: NV probation có due trong 2 ngày → chạy cron 2 lần → đúng 1 bộ notification (dedup); gate pass tạo `probation_pass`. Chạy `--test-tags /hocba_employees`.
- [ ] Commit.

## Task P5: Nhắc hạn hồ sơ

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py` (`_cron_cert_expiry_alerts` + cron mới nếu 5b khả thi)
- Create/Modify: `custom-addons/hocba_employees/data/` (ir.cron cho 5b nếu làm), test `test_reminder_notify.py`

- [ ] 5a — trong `_cron_cert_expiry_alerts`, cạnh mỗi `_hocba_gate_activity` phát:
  - sắp hết hạn: kind 'cert_expiry', level 'warning', dedup `cert_expiry:{emp.id}:{min_expiry}`; recipient = HR managers + emp.user_id
  - đã hết hạn: kind 'cert_expired', level 'danger', dedup `cert_expired:{emp.id}:{today-month}` (YYYY-MM để không spam mỗi ngày)
  - category 'hr_reminder', target_view='employees', target_ref=emp.id.
- [ ] 5b — kiểm tra field ngày hết hạn hợp đồng trên `hr.version` (Odoo 19: `contract_date_end`). Nếu đọc được qua `employee.version_id` gọn: cron mới `_cron_contract_end_alerts` (ir.cron data XML, 7:00 daily) quét NV active có ngày hết hạn HĐ trong ≤30 ngày → HR managers, kind 'contract_end', level 'warning', dedup `contract_end:{emp.id}:{date_end}`. Nếu field không tồn tại/vướng payroll → GHI CHÚ vào commit message + spec, bỏ 5b (làm sau).
- [ ] Test 5a dedup (chạy cron 2 lần → không nhân bản) + 5b nếu làm. Chạy `--test-tags /hocba_employees`.
- [ ] Commit.

## Verify cuối
- [ ] Full test: `-u hocba_notify,hocba_timeoff,hocba_employees --test-tags /hocba_notify,/hocba_timeoff,/hocba_employees` → 0 failed, N>0.
- [ ] Build SPA + preview smoke (chuông hiển thị notification offboarding thật).
- [ ] Cập nhật memory + finishing-a-development-branch.
