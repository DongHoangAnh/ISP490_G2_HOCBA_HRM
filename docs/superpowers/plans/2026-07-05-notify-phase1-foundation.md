# Notify Phase 1 — Module nền `hocba_notify` (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tạo addon nền `hocba_notify` chứa model thông báo tổng quát `hb.notification` + helper `_notify` + 3 API chung cho chuông SPA — chạy & test được độc lập, chưa đụng module nào khác.

**Architecture:** Module `depends: ['base']`. Model `hb.notification` lưu 1 thông báo/1 người nhận với field điều hướng (`target_view/ref/tab`) và `dedup_key` chống trùng. Helper `_notify` (chạy sudo) tạo dòng, bỏ recipient rỗng/inactive, dedup theo key khi chưa đọc. Controller phát 3 route `/hocba-hrm/api/notifications*` lọc `recipient_id = uid` (sudo sau khi pin). Mọi thao tác ghi qua sudo; record rule `recipient_id = user` phòng thủ chiều sâu.

**Tech Stack:** Odoo 19 (Python), `odoo.tests.common.TransactionCase`, Docker local Postgres (db `hocba_hrm`).

> Spec: `docs/superpowers/specs/2026-07-05-unified-notifications-design.md` (§2). Đây là **Phase 1/5**; Phase 2–5 (migrate timeoff, offboarding, onboarding, nhắc-hạn) có plan riêng.

**Lưu ý test (CLAUDE.md):** trên Git Bash BẮT BUỘC prefix `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`, thiếu → chạy 0 test mà vẫn báo OK. Kết quả cần thấy `0 failed, 0 error(s) of N tests` với N>0.

---

## File Structure

```
custom-addons/hocba_notify/
  __init__.py                         # from . import models, controllers
  __manifest__.py                     # depends base; data security
  models/
    __init__.py                       # from . import hb_notification
    hb_notification.py                # model HbNotification + _notify
  controllers/
    __init__.py                       # from . import main
    main.py                           # HocbaNotify routes + helpers _list/_mark/_mark_all/_notif_row
  security/
    ir.model.access.csv               # ACL group_user
    hb_notification_rules.xml         # record rule recipient_id=user
  tests/
    __init__.py                       # from . import test_notification
    test_notification.py              # TransactionCase
```

---

## Task 1: Scaffold module `hocba_notify` (cài được, rỗng)

**Files:**
- Create: `custom-addons/hocba_notify/__init__.py`
- Create: `custom-addons/hocba_notify/__manifest__.py`
- Create: `custom-addons/hocba_notify/models/__init__.py`
- Create: `custom-addons/hocba_notify/models/hb_notification.py`
- Create: `custom-addons/hocba_notify/controllers/__init__.py`
- Create: `custom-addons/hocba_notify/controllers/main.py`
- Create: `custom-addons/hocba_notify/security/ir.model.access.csv`
- Create: `custom-addons/hocba_notify/security/hb_notification_rules.xml`
- Create: `custom-addons/hocba_notify/tests/__init__.py`
- Create: `custom-addons/hocba_notify/tests/test_notification.py`

- [ ] **Step 1: Tạo `__manifest__.py`**

```python
{
    'name': 'Học Bá — Thông báo (Notify)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Model thông báo in-app dùng chung cho chuông SPA (hb.notification)',
    'author': 'Học Bá / Vu-Tan',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/hb_notification_rules.xml',
    ],
    'installable': True,
    'application': False,
}
```

- [ ] **Step 2: Tạo các `__init__.py`**

`custom-addons/hocba_notify/__init__.py`:
```python
from . import models
from . import controllers
```

`custom-addons/hocba_notify/models/__init__.py`:
```python
from . import hb_notification
```

`custom-addons/hocba_notify/controllers/__init__.py`:
```python
from . import main
```

`custom-addons/hocba_notify/tests/__init__.py`:
```python
from . import test_notification
```

- [ ] **Step 3: Tạo model tối thiểu tạm** (`models/hb_notification.py`)

```python
from odoo import api, fields, models


class HbNotification(models.Model):
    _name = 'hb.notification'
    _description = 'Thông báo in-app (chuông SPA) — dùng chung mọi module'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    recipient_id = fields.Many2one(
        'res.users', string='Người nhận',
        required=True, ondelete='cascade', index=True)
    title = fields.Char(required=True)
```

- [ ] **Step 4: Tạo controller rỗng tạm** (`controllers/main.py`)

```python
from odoo import http
```

- [ ] **Step 5: Tạo security tối thiểu** — `security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_hb_notification_user,hb.notification.user,model_hb_notification,base.group_user,1,1,0,0
```

`security/hb_notification_rules.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="hb_notification_own_rule" model="ir.rule">
        <field name="name">Notification: chỉ của mình</field>
        <field name="model_id" ref="model_hb_notification"/>
        <field name="domain_force">[('recipient_id', '=', user.id)]</field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    </record>
</odoo>
```

- [ ] **Step 6: Test rỗng để pipeline chạy** (`tests/test_notification.py`)

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestNotification(TransactionCase):
    def test_module_loaded(self):
        self.assertIn('hb.notification', self.env)
```

- [ ] **Step 7: Cài module + chạy test (verify scaffold)**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -i hocba_notify -u hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_notify --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of 1 tests`.

- [ ] **Step 8: Commit**

```bash
git add custom-addons/hocba_notify
git commit -m "feat(notify): scaffold module hocba_notify (model rỗng + ACL + test)"
```

---

## Task 2: Model `hb.notification` đầy đủ field + helper `_notify`

**Files:**
- Modify: `custom-addons/hocba_notify/models/hb_notification.py`
- Test: `custom-addons/hocba_notify/tests/test_notification.py`

- [ ] **Step 1: Viết test thất bại** — thay nội dung `tests/test_notification.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestNotifyHelper(TransactionCase):
    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.u1 = self.env['res.users'].create({
            'name': 'Notif U1', 'login': 'notif_u1', 'group_ids': gu})
        self.u2 = self.env['res.users'].create({
            'name': 'Notif U2', 'login': 'notif_u2', 'group_ids': gu})
        self.Notif = self.env['hb.notification']

    def test_notify_creates_row_with_fields(self):
        recs = self.Notif._notify(
            self.u1, category='offboarding', kind='pending', level='warning',
            title='Đơn mới', body='ND', target_view='offboarding', target_ref=42)
        self.assertEqual(len(recs), 1)
        r = recs
        self.assertEqual(r.recipient_id, self.u1)
        self.assertEqual(r.category, 'offboarding')
        self.assertEqual(r.kind, 'pending')
        self.assertEqual(r.level, 'warning')
        self.assertEqual(r.target_view, 'offboarding')
        self.assertEqual(r.target_ref, 42)
        self.assertFalse(r.is_read)

    def test_notify_multiple_recipients(self):
        recs = self.Notif._notify(
            self.u1 | self.u2, category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 2)

    def test_notify_skips_inactive_recipient(self):
        self.u2.active = False
        recs = self.Notif._notify(
            self.u1 | self.u2, category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(recs.recipient_id, self.u1)

    def test_notify_skips_falsy_recipient(self):
        recs = self.Notif._notify(
            self.env['res.users'], category='timeoff', kind='pending',
            level='info', title='X')
        self.assertEqual(len(recs), 0)

    def test_notify_dedup_when_unread(self):
        kw = dict(category='hr_reminder', kind='cert_expiry', level='warning',
                  title='Chứng chỉ', dedup_key='cert:1:2026-08')
        first = self.Notif._notify(self.u1, **kw)
        second = self.Notif._notify(self.u1, **kw)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)  # trùng key + chưa đọc → bỏ qua

    def test_notify_dedup_allows_after_read(self):
        kw = dict(category='hr_reminder', kind='cert_expiry', level='warning',
                  title='Chứng chỉ', dedup_key='cert:1:2026-09')
        first = self.Notif._notify(self.u1, **kw)
        first.is_read = True
        second = self.Notif._notify(self.u1, **kw)
        self.assertEqual(len(second), 1)  # dòng cũ đã đọc → cho tạo lại
```

- [ ] **Step 2: Chạy test — verify FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_notify,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_notify --stop-after-init --log-level=test
```
Expected: FAIL — `hb.notification` chưa có method `_notify` / field `category`.

- [ ] **Step 3: Viết model đầy đủ** — thay `models/hb_notification.py`:

```python
from odoo import api, fields, models


class HbNotification(models.Model):
    _name = 'hb.notification'
    _description = 'Thông báo in-app (chuông SPA) — dùng chung mọi module'
    _order = 'create_date desc, id desc'
    _rec_name = 'title'

    CATEGORY_SEL = [
        ('timeoff', 'Nghỉ phép'),
        ('offboarding', 'Nghỉ việc'),
        ('onboarding', 'Nhận việc / Thử việc'),
        ('hr_reminder', 'Nhắc hạn hồ sơ'),
    ]
    LEVEL_SEL = [
        ('info', 'Info'), ('success', 'Success'),
        ('warning', 'Warning'), ('danger', 'Danger'),
    ]

    recipient_id = fields.Many2one(
        'res.users', string='Người nhận',
        required=True, ondelete='cascade', index=True)
    category = fields.Selection(CATEGORY_SEL, string='Nhóm', required=True, index=True)
    kind = fields.Char(string='Loại', required=True)
    level = fields.Selection(LEVEL_SEL, string='Mức', default='info', required=True)
    title = fields.Char(string='Tiêu đề', required=True)
    body = fields.Text(string='Nội dung')
    target_view = fields.Char(string='View đích')
    target_ref = fields.Integer(string='ID đích')
    target_tab = fields.Char(string='Tab đích')
    dedup_key = fields.Char(string='Khoá chống trùng', index=True)
    is_read = fields.Boolean(string='Đã đọc', default=False, index=True)

    @api.model
    def _notify(self, recipients, category, kind, level, title, body=None,
                target_view=None, target_ref=None, target_tab=None,
                dedup_key=None):
        """Tạo 1 thông báo cho mỗi recipient (chạy sudo). Bỏ recipient rỗng/
        inactive. Nếu có dedup_key: bỏ qua khi đã có dòng CHƯA ĐỌC cùng
        (recipient, dedup_key). Trả về recordset đã tạo."""
        if recipients is None:
            return self.browse()
        if isinstance(recipients, models.BaseModel):
            users = recipients
        else:
            ids = recipients if isinstance(recipients, (list, tuple, set)) else [recipients]
            users = self.env['res.users'].browse([i for i in ids if i])
        created = self.browse()
        for user in users:
            if not user or not user.exists() or not user.active:
                continue
            if dedup_key and self.sudo().search_count([
                    ('recipient_id', '=', user.id),
                    ('dedup_key', '=', dedup_key),
                    ('is_read', '=', False)]):
                continue
            created |= self.sudo().create({
                'recipient_id': user.id, 'category': category, 'kind': kind,
                'level': level, 'title': title, 'body': body or False,
                'target_view': target_view or False,
                'target_ref': target_ref or 0,
                'target_tab': target_tab or False,
                'dedup_key': dedup_key or False,
            })
        return created
```

- [ ] **Step 4: Chạy test — verify PASS**

Run (lệnh như Step 2).
Expected: `0 failed, 0 error(s) of 6 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_notify
git commit -m "feat(notify): model hb.notification đầy đủ field + helper _notify (dedup)"
```

---

## Task 3: Controller API `/hocba-hrm/api/notifications*` + helpers

**Files:**
- Modify: `custom-addons/hocba_notify/controllers/main.py`
- Test: `custom-addons/hocba_notify/tests/test_notification.py` (thêm class)

- [ ] **Step 1: Viết test thất bại** — thêm vào cuối `tests/test_notification.py`:

```python
@tagged('post_install', '-at_install')
class TestNotifyApiHelpers(TransactionCase):
    def setUp(self):
        super().setUp()
        from odoo.addons.hocba_notify.controllers.main import (
            _list_notifications, _mark_read, _mark_all)
        self._list = _list_notifications
        self._mark = _mark_read
        self._mark_all = _mark_all
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.u1 = self.env['res.users'].create({
            'name': 'AU1', 'login': 'napi_u1', 'group_ids': gu})
        self.u2 = self.env['res.users'].create({
            'name': 'AU2', 'login': 'napi_u2', 'group_ids': gu})
        N = self.env['hb.notification']
        N._notify(self.u1, category='timeoff', kind='pending', level='info', title='A')
        N._notify(self.u1, category='timeoff', kind='approved', level='success', title='B')
        N._notify(self.u2, category='timeoff', kind='pending', level='info', title='C')

    def test_list_only_own(self):
        env1 = self.env(user=self.u1)
        res = self._list(env1, limit=20)
        self.assertEqual(res['unread'], 2)
        self.assertEqual({i['title'] for i in res['items']}, {'A', 'B'})
        self.assertIn('targetView', res['items'][0])
        self.assertIn('createdAt', res['items'][0])

    def test_mark_read_own(self):
        env1 = self.env(user=self.u1)
        first = self._list(env1)['items'][0]
        ok = self._mark(env1, first['id'])
        self.assertTrue(ok)
        self.assertEqual(self._list(env1)['unread'], 1)

    def test_mark_read_rejects_other_user(self):
        env1 = self.env(user=self.u1)
        other = self.env['hb.notification'].sudo().search(
            [('recipient_id', '=', self.u2.id)], limit=1)
        ok = self._mark(env1, other.id)
        self.assertFalse(ok)  # không phải của u1
        self.assertFalse(other.is_read)

    def test_mark_all_own(self):
        env1 = self.env(user=self.u1)
        n = self._mark_all(env1)
        self.assertEqual(n, 2)
        self.assertEqual(self._list(env1)['unread'], 0)
```

- [ ] **Step 2: Chạy test — verify FAIL**

Run (lệnh như Task 2 Step 2). Expected: FAIL — `ImportError` `_list_notifications`.

- [ ] **Step 3: Viết controller + helpers** — thay `controllers/main.py`:

```python
from odoo import fields, http
from odoo.http import request


def _d(dt):
    return fields.Datetime.to_string(dt) if dt else None


def _notif_row(rec):
    return {
        'id': rec.id,
        'category': rec.category,
        'kind': rec.kind,
        'level': rec.level,
        'title': rec.title,
        'body': rec.body or '',
        'targetView': rec.target_view or None,
        'targetRef': rec.target_ref or None,
        'targetTab': rec.target_tab or None,
        'isRead': rec.is_read,
        'createdAt': _d(rec.create_date),
    }


def _list_notifications(env, limit=20):
    """Thông báo của chính user (mới nhất trước) + số chưa đọc cho badge."""
    N = env['hb.notification'].sudo()
    base = [('recipient_id', '=', env.uid)]
    recs = N.search(base, limit=limit or 20)
    unread = N.search_count(base + [('is_read', '=', False)])
    return {'items': [_notif_row(r) for r in recs], 'unread': unread}


def _mark_read(env, notif_id):
    """Đánh dấu 1 thông báo đã đọc — chỉ khi thuộc về chính user. True/False."""
    rec = env['hb.notification'].sudo().browse(int(notif_id))
    if not rec.exists() or rec.recipient_id.id != env.uid:
        return False
    if not rec.is_read:
        rec.is_read = True
    return True


def _mark_all(env):
    """Đánh dấu tất cả của user là đã đọc — trả số dòng vừa đổi."""
    recs = env['hb.notification'].sudo().search(
        [('recipient_id', '=', env.uid), ('is_read', '=', False)])
    recs.write({'is_read': True})
    return len(recs)


class HocbaNotify(http.Controller):

    @http.route('/hocba-hrm/api/notifications', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_list(self, **kw):
        limit = int(kw.get('limit') or 20)
        return request.make_json_response(
            _list_notifications(request.env, limit))

    @http.route('/hocba-hrm/api/notifications/<int:notif_id>/read',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_read(self, notif_id, **kw):
        if not _mark_read(request.env, notif_id):
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(_list_notifications(request.env))

    @http.route('/hocba-hrm/api/notifications/read-all',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_read_all(self, **kw):
        _mark_all(request.env)
        return request.make_json_response(_list_notifications(request.env))
```

- [ ] **Step 4: Chạy test — verify PASS**

Run (lệnh như Task 2 Step 2).
Expected: `0 failed, 0 error(s) of 10 tests` (6 helper + 4 API).

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_notify
git commit -m "feat(notify): API /api/notifications list/read/read-all + helpers"
```

---

## Task 4: Verify tổng thể Phase 1

- [ ] **Step 1: Chạy lại toàn bộ test module**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_notify,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_notify --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of 10 tests`.

- [ ] **Step 2: Xác nhận không hồi quy** — module chưa được ai depends nên không ảnh hưởng build khác. Ghi nhận Phase 1 xong; Phase 2 (migrate timeoff + FE) sẽ có plan riêng.

---

## Ghi chú chuyển tiếp
- Phase 1 KHÔNG đụng module khác, KHÔNG cần build SPA (chưa có FE).
- Trước Phase 2, tạo plan `2026-07-…-notify-phase2-timeoff-migrate.md`: thêm
  `hocba_notify` vào `depends` của hocba_timeoff/hocba_employees/hocba_hrm,
  rewire `_push_notification`, migration data `hb.leave.notification` →
  `hb.notification`, refactor `api/notifications.js` + `NotificationBell` + `App.jsx`.
- Chưa cài lên Neon ở Phase 1; khi cài/upgrade Neon dùng endpoint TRỰC TIẾP (bỏ `-pooler`).
```
