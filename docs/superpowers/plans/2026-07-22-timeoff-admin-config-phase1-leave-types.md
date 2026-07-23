# Trung tâm Cấu hình Time Off — Phase 1 (Loại nghỉ) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho tài khoản Admin (`base.group_system`) một khu "Cấu hình nghỉ phép" trong SPA `/hocba-hrm` để **xem / tạo / sửa / bật-tắt loại nghỉ phép** (`hr.leave.type`), thay cơ chế lọc cứng `xml_id` bằng cờ DB `x_hb_managed`.

**Architecture:** Backend thêm field `x_hb_managed` trên `hr.leave.type` (+ migration seed 8 loại có sẵn), đổi `_hb_leave_type_ids` sang lọc theo cờ này, và thêm controller mới `controllers/config.py` với 3 endpoint (list/save/toggle) gate bằng `base.group_system` + ghi qua `sudo()`. Frontend thêm nav item "Cấu hình nghỉ phép" (chỉ `me.isAdmin`) + màn React gọi các endpoint đó. Logic đặt ở hàm cấp module để test `TransactionCase` gọi trực tiếp (theo quy ước repo).

**Tech Stack:** Odoo 19 (Python), `hr_holidays`, React 18 + Vite (không TypeScript), fetch qua `src/api/client.js`. Test backend chạy Docker local theo CLAUDE.md.

**Nền tảng đã có sẵn (không phải làm lại):** `/hocba-hrm/api/me` đã trả `isAdmin = has_group('base.group_system')` (`hocba_hrm/controllers/main.py:3377`) và `Shell.jsx` đã tham chiếu `me.isAdmin`. Nên FE gate bằng `me.isAdmin`; **không** cần sửa `_scope_for` của timeoff.

**Kiểu field `hr.leave.type` (đã xác minh từ core `hr_holidays/models/hr_leave_type.py`):**
- `name` Char (required) · `color` Integer · `active` Boolean
- `requires_allocation` **Boolean** (required) · `unpaid` Boolean · `support_document` Boolean
- `leave_validation_type` Selection `('no_validation','hr','manager','both')` default `'hr'`
- `request_unit` Selection `('day','half_day','hour')` default `'day'` (Học Bá chỉ dùng day/half_day)
- `x_is_emergency_type` Boolean (custom, `models/hr_leave_type.py`)

---

## File Structure

**Backend (`custom-addons/hocba_timeoff/`):**
- Modify `models/hr_leave_type.py` — thêm field `x_hb_managed`.
- Modify `data/hr_leave_type_data.xml` — set `x_hb_managed=True` cho 8 loại (fresh install).
- Create `migrations/19.0.18.0.0/post-migrate.py` — seed cờ cho DB đã cài (noupdate chặn XML).
- Modify `__manifest__.py` — bump version `19.0.17.0.0` → `19.0.18.0.0`.
- Modify `controllers/main.py` — `_hb_leave_type_ids` lọc theo `x_hb_managed`.
- Create `controllers/config.py` — controller + hàm cấp module cho khu cấu hình.
- Modify `controllers/__init__.py` — import `config`.
- Create `tests/test_admin_config.py` — test khu Loại nghỉ.
- Modify `tests/__init__.py` — import test mới.

**Frontend (`frontend/`):**
- Create `src/api/timeoffConfig.js` — wrapper fetch cho endpoint cấu hình.
- Create `src/features/timeoff-config/TimeoffConfig.jsx` — shell + tab.
- Create `src/features/timeoff-config/LeaveTypesTab.jsx` — bảng + form CRUD loại nghỉ.
- Modify `src/app/Shell.jsx` — nav `need:'admin'` + item `timeoffConfig` + PAGE_META.
- Modify `src/app/App.jsx` — import + render view `timeoffConfig`.

---

## Task 1: Field `x_hb_managed` trên hr.leave.type + seed

**Files:**
- Modify: `custom-addons/hocba_timeoff/models/hr_leave_type.py`
- Modify: `custom-addons/hocba_timeoff/data/hr_leave_type_data.xml`
- Create: `custom-addons/hocba_timeoff/migrations/19.0.18.0.0/post-migrate.py`
- Modify: `custom-addons/hocba_timeoff/__manifest__.py`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`
- Modify: `custom-addons/hocba_timeoff/tests/__init__.py`

- [ ] **Step 1: Viết test thất bại — 8 loại seed phải có `x_hb_managed=True`**

Tạo `custom-addons/hocba_timeoff/tests/test_admin_config.py`:

```python
# ============================================================
# Test — Trung tâm Cấu hình Time Off (Admin), Phase 1: Loại nghỉ.
# Theo quy ước repo: TransactionCase gọi thẳng hàm cấp module của controller
# với self.env(user=...). Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError

HB_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
    'hb_leave_type_teaching_off',
)


@tagged('post_install', '-at_install')
class TestAdminConfigLeaveTypes(TransactionCase):

    def test_seeded_types_are_managed(self):
        for xmlid in HB_XMLIDS:
            lt = self.env.ref('hocba_timeoff.%s' % xmlid)
            self.assertTrue(
                lt.x_hb_managed,
                'Loại nghỉ %s phải có x_hb_managed=True' % xmlid)
```

Thêm import vào `custom-addons/hocba_timeoff/tests/__init__.py` (thêm dòng, giữ nguyên các dòng cũ):

```python
from . import test_admin_config
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigLeaveTypes --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError` hoặc `x_hb_managed` False (field chưa tồn tại / chưa seed).

- [ ] **Step 3: Thêm field `x_hb_managed`**

Trong `custom-addons/hocba_timeoff/models/hr_leave_type.py`, thêm field vào class `HrLeaveType` (sau `x_is_emergency_type`):

```python
    x_hb_managed = fields.Boolean(
        string='Do Học Bá quản lý',
        default=False,
        help='Bật = loại nghỉ này hiển thị & cấu hình được trong SPA Học Bá. '
             'Các loại nghỉ demo/bản địa hoá của Odoo để False để ẩn khỏi SPA.',
    )
```

- [ ] **Step 4: Seed cờ trong XML (fresh install)**

Trong `custom-addons/hocba_timeoff/data/hr_leave_type_data.xml`, thêm dòng `<field name="x_hb_managed">True</field>` vào **mỗi** trong 8 record (`hb_leave_type_annual`, `_sick`, `_unpaid`, `_maternity`, `_compensatory`, `_personal`, `_emergency`, `_teaching_off`). Ví dụ với record đầu:

```xml
        <record id="hb_leave_type_annual" model="hr.leave.type">
            <field name="name">Nghỉ Phép Năm</field>
            <field name="time_type">leave</field>
            <field name="requires_allocation">True</field>
            <field name="leave_validation_type">hr</field>
            <field name="allocation_validation_type">hr</field>
            <field name="unpaid">False</field>
            <field name="request_unit">half_day</field>
            <field name="color">10</field>
            <field name="x_hb_managed">True</field>
        </record>
```

- [ ] **Step 5: Migration seed cờ cho DB đã cài + bump version**

Bump version trong `custom-addons/hocba_timeoff/__manifest__.py`:
```python
    'version': '19.0.18.0.0',
```

Tạo `custom-addons/hocba_timeoff/migrations/19.0.18.0.0/post-migrate.py`:
```python
# Seed cờ x_hb_managed cho 8 loại nghỉ chuẩn Học Bá trên DB ĐÃ CÀI.
# Block hr_leave_type_data.xml là noupdate="1" → Odoo KHÔNG tự set field mới
# vào record cũ; migration này ghi thủ công. Các loại nghỉ demo/khác giữ mặc
# định False (khi thêm cột) nên tự động bị ẩn khỏi SPA.
from odoo import SUPERUSER_ID, api

HB_XMLIDS = (
    'hb_leave_type_annual', 'hb_leave_type_sick', 'hb_leave_type_unpaid',
    'hb_leave_type_maternity', 'hb_leave_type_emergency',
    'hb_leave_type_compensatory', 'hb_leave_type_personal',
    'hb_leave_type_teaching_off',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ids = []
    for xmlid in HB_XMLIDS:
        lt = env.ref('hocba_timeoff.%s' % xmlid, raise_if_not_found=False)
        if lt:
            ids.append(lt.id)
    if ids:
        cr.execute(
            "UPDATE hr_leave_type SET x_hb_managed = TRUE WHERE id IN %s",
            (tuple(ids),))
        env.invalidate_all()
```

- [ ] **Step 6: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: `test_seeded_types_are_managed` PASS. Kết quả tổng `0 failed, 0 error(s)`.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_timeoff/models/hr_leave_type.py \
  custom-addons/hocba_timeoff/data/hr_leave_type_data.xml \
  custom-addons/hocba_timeoff/migrations/19.0.18.0.0/post-migrate.py \
  custom-addons/hocba_timeoff/__manifest__.py \
  custom-addons/hocba_timeoff/tests/test_admin_config.py \
  custom-addons/hocba_timeoff/tests/__init__.py
git commit -m "feat(timeoff): field x_hb_managed đánh dấu loại nghỉ Học Bá + seed 8 loại"
```

---

## Task 2: `_hb_leave_type_ids` lọc theo `x_hb_managed`

**Files:**
- Modify: `custom-addons/hocba_timeoff/controllers/main.py:177-184`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`

- [ ] **Step 1: Viết test thất bại — regression + hành vi mới**

Thêm 2 test vào class `TestAdminConfigLeaveTypes` trong `tests/test_admin_config.py`:

```python
    def test_hb_leave_type_ids_matches_seeded(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        expected = set()
        for xmlid in HB_XMLIDS:
            expected.add(self.env.ref('hocba_timeoff.%s' % xmlid).id)
        self.assertEqual(set(_hb_leave_type_ids(self.env)), expected)

    def test_hb_leave_type_ids_excludes_unmanaged(self):
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        other = self.env['hr.leave.type'].create({
            'name': 'Loại demo không thuộc HB', 'x_hb_managed': False})
        self.assertNotIn(other.id, _hb_leave_type_ids(self.env))
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigLeaveTypes --stop-after-init --log-level=test
```
Expected: `test_hb_leave_type_ids_excludes_unmanaged` FAIL (bản cũ lọc theo xml_id nên loại demo mới sẽ không lọt vào danh sách chỉ vì thiếu xml_id — nhưng cũng không phản ánh cờ; test regression `matches_seeded` vẫn PASS ở bản cũ). Nếu cả hai PASS sẵn, vẫn tiếp tục Step 3 để chuyển sang cờ DB (mục tiêu kiến trúc).

- [ ] **Step 3: Đổi implementation `_hb_leave_type_ids`**

Trong `custom-addons/hocba_timeoff/controllers/main.py`, thay toàn bộ hàm `_hb_leave_type_ids` (dòng 177-184):

```python
def _hb_leave_type_ids(env):
    """ID các loại nghỉ Học Bá — lọc theo cờ DB x_hb_managed (thay cho lọc
    cứng theo xml_id): loại admin tạo mới tự xuất hiện, loại tắt (active=False)
    tự ẩn khỏi SPA. Giữ HB_LEAVE_TYPE_XMLIDS chỉ để migration seed cờ."""
    return env['hr.leave.type'].sudo().search(
        [('x_hb_managed', '=', True)], order='id').ids
```

- [ ] **Step 4: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: cả 2 test mới + `test_seeded_types_are_managed` PASS.

- [ ] **Step 5: Regression — chạy toàn bộ test module**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff --stop-after-init --log-level=test
```
Expected: `0 failed, 0 error(s) of N tests` (N là tổng test module, > 0). Các test cũ (balances, day_calc…) vẫn xanh vì 8 loại vẫn được nhận diện.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/main.py \
  custom-addons/hocba_timeoff/tests/test_admin_config.py
git commit -m "refactor(timeoff): _hb_leave_type_ids lọc theo x_hb_managed thay xml_id cứng"
```

---

## Task 3: Controller cấu hình + endpoint Loại nghỉ

**Files:**
- Create: `custom-addons/hocba_timeoff/controllers/config.py`
- Modify: `custom-addons/hocba_timeoff/controllers/__init__.py`
- Test: `custom-addons/hocba_timeoff/tests/test_admin_config.py`

- [ ] **Step 1: Viết test thất bại — cổng quyền + list + CRUD**

Thêm vào đầu `tests/test_admin_config.py` (sau các import hiện có) một `setUp` cho user, và các test. Cập nhật class như sau (giữ các test đã có ở Task 1-2, chỉ thêm `setUp` + test mới):

```python
    def setUp(self):
        super().setUp()
        self.admin_user = self.env['res.users'].create({
            'name': 'Cfg Admin', 'login': 'cfg_admin',
            'group_ids': [(4, self.env.ref('base.group_system').id)]})
        self.hr_mgr_user = self.env['res.users'].create({
            'name': 'Cfg HRM', 'login': 'cfg_hrm',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

    def _admin_env(self):
        return self.env(user=self.admin_user)

    def test_is_admin_gate(self):
        from odoo.addons.hocba_timeoff.controllers.config import _is_admin
        self.assertTrue(_is_admin(self._admin_env()))
        self.assertFalse(_is_admin(self.env(user=self.hr_mgr_user)))

    def test_list_returns_eight_managed(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_list_leave_types
        rows = _config_list_leave_types(self._admin_env())
        self.assertEqual(len(rows), len(HB_XMLIDS))
        annual = next(r for r in rows
                      if r['id'] == self.env.ref('hocba_timeoff.hb_leave_type_annual').id)
        self.assertTrue(annual['requiresAllocation'])
        self.assertEqual(annual['requestUnit'], 'half_day')

    def test_create_leave_type_appears(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        env = self._admin_env()
        row = _config_save_leave_type(env, {
            'name': 'Nghỉ Thử Nghiệm', 'requiresAllocation': False,
            'unpaid': False, 'validationType': 'hr', 'requestUnit': 'day',
            'supportDocument': False, 'isEmergency': False, 'color': 5})
        self.assertTrue(row['id'])
        lt = self.env['hr.leave.type'].browse(row['id'])
        self.assertTrue(lt.x_hb_managed)
        self.assertIn(row['id'], _hb_leave_type_ids(self.env))

    def test_update_leave_type_writes(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        env = self._admin_env()
        annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        row = _config_save_leave_type(env, {
            'id': annual.id, 'name': 'Phép Năm (đã sửa)',
            'requiresAllocation': True, 'unpaid': False,
            'validationType': 'both', 'requestUnit': 'half_day',
            'supportDocument': False, 'isEmergency': False, 'color': 10})
        self.assertEqual(row['name'], 'Phép Năm (đã sửa)')
        self.assertEqual(row['validationType'], 'both')
        self.assertEqual(annual.leave_validation_type, 'both')

    def test_toggle_archives_and_hides(self):
        from odoo.addons.hocba_timeoff.controllers.config import (
            _config_save_leave_type, _config_toggle_leave_type)
        from odoo.addons.hocba_timeoff.controllers.main import _hb_leave_type_ids
        env = self._admin_env()
        row = _config_save_leave_type(env, {
            'name': 'Nghỉ Tạm', 'requiresAllocation': False, 'unpaid': False,
            'validationType': 'hr', 'requestUnit': 'day',
            'supportDocument': False, 'isEmergency': False, 'color': 3})
        _config_toggle_leave_type(env, row['id'], False)
        self.assertNotIn(row['id'], _hb_leave_type_ids(self.env))

    def test_save_empty_name_raises(self):
        from odoo.addons.hocba_timeoff.controllers.config import _config_save_leave_type
        with self.assertRaises(ValidationError):
            _config_save_leave_type(self._admin_env(), {'name': '   '})
```

- [ ] **Step 2: Chạy test — kỳ vọng FAIL**

Run:
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_timeoff,hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_timeoff:TestAdminConfigLeaveTypes --stop-after-init --log-level=test
```
Expected: FAIL — `ModuleNotFoundError`/`ImportError` (chưa có `controllers/config.py`).

- [ ] **Step 3: Tạo controller `config.py`**

Tạo `custom-addons/hocba_timeoff/controllers/config.py`:
```python
# ============================================================
# JSON API cho SPA — khu CẤU HÌNH Time Off (chỉ Admin base.group_system).
# Tách khỏi main.py: đây là cấu hình hệ thống, không phải nghiệp vụ vận hành.
# Mọi endpoint gate has_group('base.group_system'); ghi qua sudo() sau cổng
# quyền (theo gotcha self-service của dự án). Hàm cấp module để test gọi trực
# tiếp với env(user=...). Owner: Nhật Anh.
# ============================================================
from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

VALIDATION_TYPES = ('no_validation', 'hr', 'manager', 'both')
REQUEST_UNITS = ('day', 'half_day')  # Học Bá không dùng 'hour'


def _is_admin(env):
    return env.user.has_group('base.group_system')


def _leave_type_row(env, lt):
    in_use = env['hr.leave'].sudo().search_count(
        [('holiday_status_id', '=', lt.id)])
    return {
        'id': lt.id,
        'name': lt.name or '',
        'requiresAllocation': bool(lt.requires_allocation),
        'unpaid': bool(lt.unpaid),
        'validationType': lt.leave_validation_type or 'hr',
        'requestUnit': lt.request_unit or 'day',
        'supportDocument': bool(lt.support_document),
        'isEmergency': bool(lt.x_is_emergency_type),
        'color': lt.color or 0,
        'active': bool(lt.active),
        'inUseCount': in_use,
    }


def _config_list_leave_types(env):
    types = (env['hr.leave.type'].sudo()
             .with_context(active_test=False)
             .search([('x_hb_managed', '=', True)], order='active desc, id'))
    return [_leave_type_row(env, lt) for lt in types]


def _normalize_leave_type_vals(vals):
    name = (vals.get('name') or '').strip()
    if not name:
        raise ValidationError('Tên loại nghỉ không được để trống.')
    validation = vals.get('validationType') or 'hr'
    if validation not in VALIDATION_TYPES:
        raise ValidationError('Bậc duyệt không hợp lệ.')
    unit = vals.get('requestUnit') or 'day'
    if unit not in REQUEST_UNITS:
        raise ValidationError('Đơn vị nghỉ không hợp lệ (chỉ cả ngày / nửa ngày).')
    return {
        'name': name,
        'requires_allocation': bool(vals.get('requiresAllocation')),
        'unpaid': bool(vals.get('unpaid')),
        'leave_validation_type': validation,
        'request_unit': unit,
        'support_document': bool(vals.get('supportDocument')),
        'x_is_emergency_type': bool(vals.get('isEmergency')),
        'color': int(vals.get('color') or 0),
    }


def _config_save_leave_type(env, vals):
    write_vals = _normalize_leave_type_vals(vals)
    Model = env['hr.leave.type'].sudo()
    rec_id = vals.get('id')
    if rec_id:
        lt = Model.with_context(active_test=False).browse(int(rec_id))
        if not lt.exists() or not lt.x_hb_managed:
            raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
        lt.write(write_vals)
    else:
        write_vals['x_hb_managed'] = True
        lt = Model.create(write_vals)
    return _leave_type_row(env, lt)


def _config_toggle_leave_type(env, rec_id, active):
    lt = (env['hr.leave.type'].sudo()
          .with_context(active_test=False).browse(int(rec_id)))
    if not lt.exists() or not lt.x_hb_managed:
        raise ValidationError('Loại nghỉ không tồn tại hoặc không thuộc Học Bá.')
    lt.active = bool(active)
    return _leave_type_row(env, lt)


class HocBaTimeoffConfig(http.Controller):

    def _guard(self):
        """Trả response 403 nếu không phải Admin; None nếu OK."""
        if not _is_admin(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        return None

    @http.route('/hocba-hrm/api/timeoff/config/leave-types',
                auth='user', type='http', methods=['GET'])
    def leave_types(self, **kw):
        block = self._guard()
        if block:
            return block
        return request.make_json_response(
            {'leaveTypes': _config_list_leave_types(request.env)})

    @http.route('/hocba-hrm/api/timeoff/config/leave-types/save',
                auth='user', type='http', methods=['POST'], csrf=False)
    def leave_type_save(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_save_leave_type(request.env, payload)
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'leaveType': row})

    @http.route('/hocba-hrm/api/timeoff/config/leave-types/toggle-active',
                auth='user', type='http', methods=['POST'], csrf=False)
    def leave_type_toggle(self, **kw):
        block = self._guard()
        if block:
            return block
        payload = request.get_json_data() or {}
        try:
            row = _config_toggle_leave_type(
                request.env, payload.get('id'), payload.get('active'))
        except (UserError, ValidationError) as e:
            return request.make_json_response(
                {'error': 'invalid', 'message': str(e)}, status=400)
        return request.make_json_response({'leaveType': row})
```

- [ ] **Step 4: Đăng ký controller**

Trong `custom-addons/hocba_timeoff/controllers/__init__.py`, thêm dòng (giữ dòng cũ):
```python
from . import config
```

- [ ] **Step 5: Chạy test — kỳ vọng PASS**

Run: (như Step 2)
Expected: tất cả test trong `TestAdminConfigLeaveTypes` PASS.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_timeoff/controllers/config.py \
  custom-addons/hocba_timeoff/controllers/__init__.py \
  custom-addons/hocba_timeoff/tests/test_admin_config.py
git commit -m "feat(timeoff): controller cấu hình admin — endpoint CRUD loại nghỉ (gate group_system)"
```

---

## Task 4: Frontend — nav "Cấu hình nghỉ phép" + màn Loại nghỉ

> Repo không có test FE. Kiểm chứng = build thành công + verify qua Browser pane (đăng nhập admin). Component theo quy ước: KHÔNG fetch trực tiếp trong component — dùng wrapper `src/api/`.

**Files:**
- Create: `frontend/src/api/timeoffConfig.js`
- Create: `frontend/src/features/timeoff-config/TimeoffConfig.jsx`
- Create: `frontend/src/features/timeoff-config/LeaveTypesTab.jsx`
- Modify: `frontend/src/app/Shell.jsx`
- Modify: `frontend/src/app/App.jsx`

- [ ] **Step 1: API wrapper**

Tạo `frontend/src/api/timeoffConfig.js`:
```javascript
/* API khu Cấu hình Time Off (chỉ Admin). Spec: docs/superpowers/specs/2026-07-22-timeoff-admin-config-center-design.md */
import { hbGet, hbPost } from './client';

const BASE = '/hocba-hrm/api/timeoff/config';

/* Danh sách loại nghỉ do Học Bá quản lý (cả active/inactive). → { leaveTypes: [...] } */
export const fetchLeaveTypes = () => hbGet(`${BASE}/leave-types`);

/* Tạo mới (không id) hoặc cập nhật (có id) một loại nghỉ. → { leaveType: {...} }
   payload: { id?, name, requiresAllocation, unpaid, validationType,
              requestUnit, supportDocument, isEmergency, color } */
export const saveLeaveType = (payload) =>
  hbPost(`${BASE}/leave-types/save`, payload);

/* Bật/tắt (archive) một loại nghỉ. → { leaveType: {...} } */
export const toggleLeaveType = (id, active) =>
  hbPost(`${BASE}/leave-types/toggle-active`, { id, active });
```

- [ ] **Step 2: Component bảng loại nghỉ**

Tạo `frontend/src/features/timeoff-config/LeaveTypesTab.jsx`:
```javascript
/* Khu Cấu hình → tab "Loại nghỉ": bảng + form tạo/sửa + bật/tắt.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchLeaveTypes, saveLeaveType, toggleLeaveType } from '../../api/timeoffConfig';
import { LoadingState, ErrorState } from '../../components/states';

const VALIDATION_LABEL = {
  no_validation: 'Không cần duyệt',
  hr: 'HR Officer duyệt',
  manager: 'Quản lý duyệt',
  both: 'Quản lý + HR',
};
const EMPTY = {
  id: null, name: '', requiresAllocation: false, unpaid: false,
  validationType: 'hr', requestUnit: 'day', supportDocument: false,
  isEmergency: false, color: 0,
};

export default function LeaveTypesTab() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null);
    fetchLeaveTypes()
      .then((d) => setRows(d.leaveTypes))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const onSave = async () => {
    setSaving(true);
    try {
      await saveLeaveType(editing);
      setEditing(null);
      load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onToggle = async (row) => {
    try {
      await toggleLeaveType(row.id, !row.active);
      load();
    } catch (e) {
      setErr(e.message);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!rows) return <LoadingState label="Đang tải loại nghỉ…" />;

  return (
    <div className="to-config-leave-types">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <h3>Loại nghỉ phép ({rows.length})</h3>
        <button className="btn btn-primary" onClick={() => setEditing({ ...EMPTY })}>
          + Thêm loại nghỉ
        </button>
      </div>
      <table className="hb-table">
        <thead>
          <tr>
            <th>Tên</th><th>Trừ quỹ</th><th>Không lương</th>
            <th>Bậc duyệt</th><th>Nửa ngày</th><th>Chứng từ</th>
            <th>Đang dùng</th><th>Trạng thái</th><th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} style={{ opacity: r.active ? 1 : 0.5 }}>
              <td>{r.name}</td>
              <td>{r.requiresAllocation ? '✓' : '—'}</td>
              <td>{r.unpaid ? '✓' : '—'}</td>
              <td>{VALIDATION_LABEL[r.validationType] || r.validationType}</td>
              <td>{r.requestUnit === 'half_day' ? '✓' : '—'}</td>
              <td>{r.supportDocument ? '✓' : '—'}</td>
              <td>{r.inUseCount}</td>
              <td>{r.active ? 'Đang bật' : 'Đã tắt'}</td>
              <td>
                <button className="btn btn-sm" onClick={() => setEditing({ ...r })}>Sửa</button>
                <button className="btn btn-sm" onClick={() => onToggle(r)}>
                  {r.active ? 'Tắt' : 'Bật'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing && (
        <div className="hb-modal-backdrop" onClick={() => !saving && setEditing(null)}>
          <div className="hb-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.id ? 'Sửa loại nghỉ' : 'Thêm loại nghỉ'}</h3>
            <label>Tên
              <input value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </label>
            <label>Bậc duyệt
              <select value={editing.validationType}
                onChange={(e) => setEditing({ ...editing, validationType: e.target.value })}>
                {Object.entries(VALIDATION_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </label>
            <label>Đơn vị nghỉ
              <select value={editing.requestUnit}
                onChange={(e) => setEditing({ ...editing, requestUnit: e.target.value })}>
                <option value="day">Cả ngày</option>
                <option value="half_day">Cho phép nửa ngày</option>
              </select>
            </label>
            <label><input type="checkbox" checked={editing.requiresAllocation}
              onChange={(e) => setEditing({ ...editing, requiresAllocation: e.target.checked })} /> Trừ vào quỹ phép</label>
            <label><input type="checkbox" checked={editing.unpaid}
              onChange={(e) => setEditing({ ...editing, unpaid: e.target.checked })} /> Nghỉ không lương</label>
            <label><input type="checkbox" checked={editing.supportDocument}
              onChange={(e) => setEditing({ ...editing, supportDocument: e.target.checked })} /> Yêu cầu chứng từ</label>
            <label><input type="checkbox" checked={editing.isEmergency}
              onChange={(e) => setEditing({ ...editing, isEmergency: e.target.checked })} /> Loại khẩn cấp (fast-track)</label>
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" disabled={saving} onClick={onSave}>
                {saving ? 'Đang lưu…' : 'Lưu'}
              </button>
              <button className="btn" disabled={saving} onClick={() => setEditing(null)}>Huỷ</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Component shell + tab**

Tạo `frontend/src/features/timeoff-config/TimeoffConfig.jsx`:
```javascript
/* Trung tâm Cấu hình Time Off (chỉ Admin). Phase 1: tab "Loại nghỉ".
   Các tab Chính sách / Ngày lễ / Tích lũy sẽ bổ sung ở phase sau. */
import { useState } from 'react';
import LeaveTypesTab from './LeaveTypesTab';

const TABS = [
  { id: 'types', label: 'Loại nghỉ' },
  { id: 'policies', label: 'Chính sách', disabled: true },
  { id: 'holidays', label: 'Ngày lễ', disabled: true },
  { id: 'accrual', label: 'Tích lũy', disabled: true },
];

export default function TimeoffConfig() {
  const [tab, setTab] = useState('types');
  return (
    <div className="to-config">
      <div className="hb-tabs" style={{ marginBottom: 16 }}>
        {TABS.map((t) => (
          <button key={t.id}
            className={`hb-tab ${tab === t.id ? 'active' : ''}`}
            disabled={t.disabled}
            title={t.disabled ? 'Sắp có' : ''}
            onClick={() => !t.disabled && setTab(t.id)}>
            {t.label}{t.disabled ? ' (sắp có)' : ''}
          </button>
        ))}
      </div>
      {tab === 'types' && <LeaveTypesTab />}
    </div>
  );
}
```

- [ ] **Step 4: Thêm nav item + PAGE_META (Shell.jsx)**

Trong `frontend/src/app/Shell.jsx`:

(a) Thêm nhánh `admin` vào hàm `allow` — thay khối:
```javascript
const allow = (need, me) => {
  if (need === 'manage') return !!(me && me.canManage);
  if (need === 'hr') return !!(me && (me.isHrUser || me.isHrManager || me.isAdmin));
  if (need === 'finance') return !!(me && me.isFinance);
  if (need === 'self') return !isRoleAccount(me);
  return true;
};
```
bằng:
```javascript
const allow = (need, me) => {
  if (need === 'manage') return !!(me && me.canManage);
  if (need === 'hr') return !!(me && (me.isHrUser || me.isHrManager || me.isAdmin));
  if (need === 'admin') return !!(me && me.isAdmin);
  if (need === 'finance') return !!(me && me.isFinance);
  if (need === 'self') return !isRoleAccount(me);
  return true;
};
```

(b) Thêm section "Hệ thống" vào mảng `NAV`, ngay trước phần tử `{ sec: 'Cá nhân', ... }`:
```javascript
  { sec: 'Hệ thống', need: 'admin', items: [
    { id: 'timeoffConfig', label: 'Cấu hình nghỉ phép', icon: 'settings', need: 'admin' },
  ]},
```

(c) Thêm entry vào `PAGE_META` (sau `dashboard`/`employees`… bất kỳ vị trí trong object):
```javascript
  timeoffConfig: { t: 'Cấu hình nghỉ phép', c: 'Hệ thống / Time Off' },
```

- [ ] **Step 5: Render view (App.jsx)**

Trong `frontend/src/app/App.jsx`:

(a) Thêm import (cùng cụm import feature):
```javascript
import TimeoffConfig from '../features/timeoff-config/TimeoffConfig';
```

(b) Thêm dòng render trong khối `<div className="main">` (sau dòng `departments`):
```javascript
        {view === 'timeoffConfig' && me.isAdmin && <TimeoffConfig />}
```

- [ ] **Step 6: Build SPA**

Run:
```bash
cd frontend && npm run build
```
Expected: build thành công, không lỗi; output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 7: Verify qua Browser pane**

1. `preview_start` (theo `.claude/launch.json`), đăng nhập `test_admin@hocba.vn` / `Hocba@2026`.
2. Xác nhận sidebar có mục **"Hệ thống → Cấu hình nghỉ phép"**; mở ra thấy bảng 8 loại nghỉ.
3. Bấm "Thêm loại nghỉ", tạo 1 loại thử → xuất hiện trong bảng; kiểm `read_network_requests` thấy `save` trả 200.
4. Bấm "Tắt" một loại thử → dòng mờ đi, trạng thái "Đã tắt".
5. Đăng nhập lại `test_hrmanager@hocba.vn` → **KHÔNG** thấy mục "Cấu hình nghỉ phép" (xác nhận tách quyền). Gọi thẳng `GET /hocba-hrm/api/timeoff/config/leave-types` dưới tài khoản này → 403.
6. Chụp screenshot màn cấu hình cho user.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/api/timeoffConfig.js \
  frontend/src/features/timeoff-config/ \
  frontend/src/app/Shell.jsx frontend/src/app/App.jsx \
  custom-addons/hocba_hrm/static/spa/
git commit -m "feat(timeoff-spa): khu Cấu hình nghỉ phép cho Admin — tab Loại nghỉ (CRUD + bật/tắt)"
```

---

## Ghi chú vận hành

- Trên **Neon** (DB mặc định), khi upgrade `-u hocba_timeoff` để chạy migration 19.0.18.0.0: nếu pooler rớt SSL giữa DDL, dùng **endpoint trực tiếp** (bỏ `-pooler`) theo gotcha CLAUDE.md.
- `HB_LEAVE_TYPE_XMLIDS` trong `controllers/main.py` giữ nguyên (được migration tham chiếu gián tiếp qua bản copy trong post-migrate) — không xoá để tránh vỡ import ở test cũ.
- Các tab Chính sách / Ngày lễ / Tích lũy hiển thị "(sắp có)" và bị disable — sẽ mở ở Phase 2-4 (mỗi phase một plan riêng).

## Self-Review (đã rà)

- **Spec coverage (Phase 1):** isAdmin gate ✓ (dùng `me.isAdmin` có sẵn); `x_hb_managed` + migration ✓ (Task 1); đổi `_hb_leave_type_ids` ✓ (Task 2); controller gate group_system + sudo + CRUD loại nghỉ ✓ (Task 3); nav admin-only + UI ✓ (Task 4); test permission/create-appears/toggle/regression ✓. Ngày lễ/Chính sách/Tích lũy = phase sau (ngoài phạm vi plan này).
- **Placeholder scan:** không có TBD/“xử lý lỗi phù hợp”; mọi bước có code/lệnh cụ thể.
- **Type consistency:** field keys FE↔BE khớp (`requiresAllocation/unpaid/validationType/requestUnit/supportDocument/isEmergency/color/active/inUseCount`); tên hàm `_config_list_leave_types/_config_save_leave_type/_config_toggle_leave_type/_is_admin` dùng nhất quán ở test lẫn controller; endpoint path khớp giữa `timeoffConfig.js` và `config.py`.
