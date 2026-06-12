# Face + Geolocation Attendance Check-in — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-service attendance check-in/out for official employees that captures a face photo (verified against an enrolled descriptor via face-api.js in the browser), records GPS location, validates against a configurable time window + office geofence, and flags anomalies for HR review.

**Architecture:** A browser-side OWL client action uses face-api.js to capture a photo and compute a 128-d face descriptor, reads GPS via `navigator.geolocation`, then calls Python model methods (`action_check_in`/`action_check_out`) over RPC. The server compares the descriptor against the employee's enrolled descriptor (euclidean distance), checks the office geofence (Haversine) and the time window, then always creates/updates one attendance record per employee per day, setting boolean flags (`face_suspect`, `out_of_zone`, `out_of_window`) rather than blocking. A singleton config model (`hocba.attendance.policy`) holds the windows, office coordinates, radius, and face threshold. All numeric/temporal logic lives in pure, unit-testable helper methods.

**Tech Stack:** Odoo 19, Python 3.12, PostgreSQL 15, OWL (JS), face-api.js (TensorFlow.js, vendored static). Tests: Odoo `TransactionCase`. Runtime: Docker Compose (`hocba_hrm` DB).

---

## Conventions for this plan

- **Run tests** (all steps that say "Run tests" use this, adjusting `--test-tags`):
  ```bash
  docker compose run --rm odoo odoo -d hocba_hrm \
    -u hocba_attendance,hocba_employees --test-enable \
    --test-tags /hocba_attendance --stop-after-init --log-level=test
  ```
  Look for `X passed, 0 failed` style lines and absence of `FAIL`/`ERROR` in test output.
- **Commit** after each task that ends green.
- All new Python files start with `from odoo import ...` imports as shown.
- Face descriptor = JSON list of 128 floats, stored as Text.
- Datetimes from Odoo are **UTC**; window checks operate on a **local** datetime the caller converts via `fields.Datetime.context_timestamp`. Helpers receive the already-localized naive datetime so they stay pure & testable.

---

## File Structure

**Create:**
- `custom-addons/hocba_attendance/models/hocba_attendance_policy.py` — singleton config model + pure helpers (geofence, time window, workday).
- `custom-addons/hocba_attendance/data/hocba_attendance_policy_data.xml` — default policy record + new attendance statuses.
- `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml` — config form + menu.
- `custom-addons/hocba_attendance/tests/__init__.py`
- `custom-addons/hocba_attendance/tests/test_policy_geofence.py`
- `custom-addons/hocba_attendance/tests/test_policy_window.py`
- `custom-addons/hocba_attendance/tests/test_face_distance.py`
- `custom-addons/hocba_attendance/tests/test_checkin_flow.py`
- `custom-addons/hocba_attendance/static/src/js/attendance_kiosk.js` — OWL client action.
- `custom-addons/hocba_attendance/static/src/xml/attendance_kiosk.xml` — OWL template.
- `custom-addons/hocba_attendance/static/src/scss/attendance_kiosk.scss` — styles.
- `custom-addons/hocba_attendance/static/lib/face-api/face-api.min.js` — vendored library (downloaded).
- `custom-addons/hocba_attendance/static/lib/face-api/models/` — vendored model weights (downloaded).

**Modify:**
- `custom-addons/hocba_attendance/models/__init__.py` — register new model.
- `custom-addons/hocba_attendance/models/hr_attendance.py` — add photo/geo/score/flag fields + check-in/out methods + face distance helper.
- `custom-addons/hocba_employees/models/hr_employee.py` — add `x_face_image`, `x_face_descriptor`, `x_face_enrolled`.
- `custom-addons/hocba_attendance/security/ir.model.access.csv` — access for `hocba.attendance.policy`.
- `custom-addons/hocba_attendance/views/hr_attendance_views.xml` — flag columns + "Needs review" filter + photo/map on form.
- `custom-addons/hocba_attendance/views/menus.xml` — "My Attendance" client-action menu + Policy config menu.
- `custom-addons/hocba_attendance/__manifest__.py` — register data, views, assets, depend on `hocba_employees`.
- `custom-addons/hocba_employees/views/hr_employee_views.xml` — face enrollment widget on employee form.

---

## Task 1: Config model `hocba.attendance.policy` (skeleton + access)

**Files:**
- Create: `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`
- Modify: `custom-addons/hocba_attendance/models/__init__.py`
- Modify: `custom-addons/hocba_attendance/security/ir.model.access.csv`
- Modify: `custom-addons/hocba_attendance/__manifest__.py`
- Create: `custom-addons/hocba_attendance/data/hocba_attendance_policy_data.xml`

- [ ] **Step 1: Create the model file**

Create `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`:

```python
import json
import math

from odoo import models, fields, api


class AttendancePolicy(models.Model):
    _name = 'hocba.attendance.policy'
    _description = 'Attendance Policy (geofence, time window, face threshold)'

    name = fields.Char(string='Name', required=True, default='Default Policy')
    active = fields.Boolean(default=True)

    # Time windows (local hours as float: 8.5 = 08:30)
    morning_start = fields.Float(string='Check-in window start', default=8.0)
    morning_end = fields.Float(string='Check-in window end', default=9.5)
    evening_start = fields.Float(string='Check-out window start', default=16.0)
    evening_end = fields.Float(string='Check-out window end', default=17.5)

    # Workdays (Mon..Sun); default Mon-Fri True
    workday_mon = fields.Boolean(string='Monday', default=True)
    workday_tue = fields.Boolean(string='Tuesday', default=True)
    workday_wed = fields.Boolean(string='Wednesday', default=True)
    workday_thu = fields.Boolean(string='Thursday', default=True)
    workday_fri = fields.Boolean(string='Friday', default=True)
    workday_sat = fields.Boolean(string='Saturday', default=False)
    workday_sun = fields.Boolean(string='Sunday', default=False)

    # Geofence
    office_lat = fields.Float(string='Office latitude', digits=(10, 7))
    office_lng = fields.Float(string='Office longitude', digits=(10, 7))
    office_radius_m = fields.Float(string='Allowed radius (m)', default=150.0)

    # Face matching: euclidean distance threshold; distance > threshold => suspect
    face_threshold = fields.Float(string='Face match threshold', default=0.6)

    @api.model
    def get_policy(self):
        """Return the active policy, creating a default one if none exists."""
        policy = self.search([], limit=1)
        if not policy:
            policy = self.create({'name': 'Default Policy'})
        return policy
```

- [ ] **Step 2: Register the model in `__init__.py`**

Modify `custom-addons/hocba_attendance/models/__init__.py` — add the import (keep existing lines):

```python
from . import hocba_attendance_policy
```

- [ ] **Step 3: Add access rules**

Append to `custom-addons/hocba_attendance/security/ir.model.access.csv`:

```csv
access_hocba_attendance_policy_user,access.hocba.attendance.policy.user,model_hocba_attendance_policy,hr.group_hr_user,1,0,0,0
access_hocba_attendance_policy_manager,access.hocba.attendance.policy.manager,model_hocba_attendance_policy,hr.group_hr_manager,1,1,1,1
```

- [ ] **Step 4: Create default data record**

Create `custom-addons/hocba_attendance/data/hocba_attendance_policy_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="hocba_attendance_policy_default" model="hocba.attendance.policy">
            <field name="name">Default Policy</field>
        </record>
    </data>
</odoo>
```

- [ ] **Step 5: Wire manifest (depend on hocba_employees + load data)**

Modify `custom-addons/hocba_attendance/__manifest__.py`:
- Change `'depends': ['hr', 'web'],` to `'depends': ['hr', 'web', 'hocba_employees'],`
- In `'data'`, add `'data/hocba_attendance_policy_data.xml',` as the FIRST data entry (before view files).

The `data` list becomes:
```python
    'data': [
        'security/ir.model.access.csv',
        'data/hocba_attendance_policy_data.xml',
        'views/hr_attendance_status_views.xml',
        'views/hr_work_assignment_views.xml',
        'views/hr_attendance_views.xml',
        'views/menus.xml',
    ],
```

- [ ] **Step 6: Verify module upgrades cleanly**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance --stop-after-init --log-level=warn
```
Expected: process exits 0, no traceback, no `ERROR`/`CRITICAL` lines mentioning `hocba.attendance.policy`.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): add attendance policy config model"
```

---

## Task 2: Geofence helper (Haversine) — TDD

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`
- Create: `custom-addons/hocba_attendance/tests/__init__.py`
- Create: `custom-addons/hocba_attendance/tests/test_policy_geofence.py`

- [ ] **Step 1: Create tests package init**

Create `custom-addons/hocba_attendance/tests/__init__.py`:

```python
from . import test_policy_geofence
```

- [ ] **Step 2: Write the failing test**

Create `custom-addons/hocba_attendance/tests/test_policy_geofence.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPolicyGeofence(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].create({
            'name': 'Test',
            'office_lat': 21.028511,    # Hanoi
            'office_lng': 105.804817,
            'office_radius_m': 150.0,
        })

    def test_distance_zero_for_same_point(self):
        d = self.policy._haversine_m(21.028511, 105.804817,
                                     21.028511, 105.804817)
        self.assertAlmostEqual(d, 0.0, places=3)

    def test_known_distance_about_1km(self):
        # ~0.009 deg latitude ~= 1 km
        d = self.policy._haversine_m(21.028511, 105.804817,
                                     21.037511, 105.804817)
        self.assertTrue(950 < d < 1050, f"expected ~1000m, got {d}")

    def test_within_office_true_inside(self):
        # ~50m north of office
        self.assertTrue(self.policy.is_within_office(21.028961, 105.804817))

    def test_within_office_false_outside(self):
        # ~1km away -> outside 150m radius
        self.assertFalse(self.policy.is_within_office(21.037511, 105.804817))

    def test_within_office_false_when_coords_missing(self):
        self.assertFalse(self.policy.is_within_office(False, False))
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance --test-enable \
  --test-tags /hocba_attendance:TestPolicyGeofence --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError: ... '_haversine_m'` (method not defined).

- [ ] **Step 4: Implement the helpers**

In `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`, add these methods to the `AttendancePolicy` class (after `get_policy`):

```python
    @staticmethod
    def _haversine_m(lat1, lng1, lat2, lng2):
        """Great-circle distance between two WGS84 points, in meters."""
        r = 6371000.0  # Earth radius (m)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlmb = math.radians(lng2 - lng1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2)
        return 2 * r * math.asin(math.sqrt(a))

    def is_within_office(self, lat, lng):
        """True if (lat, lng) is within office_radius_m of the office point.
        Returns False if any coordinate is missing/unset."""
        self.ensure_one()
        if not lat or not lng or not self.office_lat or not self.office_lng:
            return False
        dist = self._haversine_m(self.office_lat, self.office_lng, lat, lng)
        return dist <= self.office_radius_m
```

- [ ] **Step 5: Run test to verify it passes**

Run the same command as Step 3.
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): geofence (haversine) helpers + tests"
```

---

## Task 3: Time-window & workday helpers — TDD

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hocba_attendance_policy.py`
- Modify: `custom-addons/hocba_attendance/tests/__init__.py`
- Create: `custom-addons/hocba_attendance/tests/test_policy_window.py`

- [ ] **Step 1: Register the new test module**

Modify `custom-addons/hocba_attendance/tests/__init__.py`:

```python
from . import test_policy_geofence
from . import test_policy_window
```

- [ ] **Step 2: Write the failing test**

Create `custom-addons/hocba_attendance/tests/test_policy_window.py`:

```python
from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPolicyWindow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].create({
            'name': 'Test',
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
        })

    def test_is_workday_weekday(self):
        # 2026-06-11 is a Thursday
        self.assertTrue(self.policy.is_workday(datetime(2026, 6, 11, 8, 0)))

    def test_is_workday_weekend(self):
        # 2026-06-13 is a Saturday (workday_sat default False)
        self.assertFalse(self.policy.is_workday(datetime(2026, 6, 13, 8, 0)))

    def test_checkin_window_inside(self):
        # Thursday 08:30 -> inside morning window
        self.assertTrue(
            self.policy.is_within_window(datetime(2026, 6, 11, 8, 30), 'in'))

    def test_checkin_window_too_late(self):
        # Thursday 10:00 -> after morning_end 09:30
        self.assertFalse(
            self.policy.is_within_window(datetime(2026, 6, 11, 10, 0), 'in'))

    def test_checkout_window_inside(self):
        # Thursday 16:30 -> inside evening window
        self.assertTrue(
            self.policy.is_within_window(datetime(2026, 6, 11, 16, 30), 'out'))

    def test_window_false_on_weekend_even_if_time_ok(self):
        # Saturday 08:30 -> right time but not a workday
        self.assertFalse(
            self.policy.is_within_window(datetime(2026, 6, 13, 8, 30), 'in'))
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance --test-enable \
  --test-tags /hocba_attendance:TestPolicyWindow --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError: ... 'is_workday'`.

- [ ] **Step 4: Implement the helpers**

Add to the `AttendancePolicy` class in `hocba_attendance_policy.py`:

```python
    def is_workday(self, dt_local):
        """True if dt_local (naive local datetime) falls on an enabled workday."""
        self.ensure_one()
        flags = [
            self.workday_mon, self.workday_tue, self.workday_wed,
            self.workday_thu, self.workday_fri, self.workday_sat,
            self.workday_sun,
        ]
        return bool(flags[dt_local.weekday()])

    def is_within_window(self, dt_local, kind):
        """True if dt_local is on a workday AND within the window for `kind`
        ('in' = check-in / morning, 'out' = check-out / evening)."""
        self.ensure_one()
        if not self.is_workday(dt_local):
            return False
        hour = dt_local.hour + dt_local.minute / 60.0
        if kind == 'in':
            return self.morning_start <= hour <= self.morning_end
        return self.evening_start <= hour <= self.evening_end
```

- [ ] **Step 5: Run test to verify it passes**

Run the same command as Step 3. Expected: PASS (6 tests).

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): time-window + workday helpers + tests"
```

---

## Task 4: Employee face enrollment fields

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py`
- Modify: `custom-addons/hocba_employees/views/hr_employee_views.xml`

- [ ] **Step 1: Add face fields to hr.employee**

In `custom-addons/hocba_employees/models/hr_employee.py`, add these fields inside the `hr.employee` class (place them near the other `x_` personal fields, e.g. right after the `x_health_care_place` block around line 81). Keep existing imports; ensure `api` is imported (the file already imports from odoo — verify `from odoo import models, fields, api` at top; if `api` is missing, add it):

```python
    # --- Face enrollment (for hocba_attendance face check-in) ---
    x_face_image = fields.Binary(string='Ảnh khuôn mặt mẫu', attachment=True)
    x_face_descriptor = fields.Text(
        string='Face descriptor (JSON)',
        help='128-d face descriptor as JSON list, computed by face-api.js.',
        copy=False,
    )
    x_face_enrolled = fields.Boolean(
        string='Đã đăng ký khuôn mặt',
        compute='_compute_x_face_enrolled',
        store=True,
    )

    @api.depends('x_face_descriptor')
    def _compute_x_face_enrolled(self):
        for emp in self:
            emp.x_face_enrolled = bool(emp.x_face_descriptor)
```

> Note: no separate access rule needed — these are fields on the existing `hr.employee` model.

- [ ] **Step 2: Add the enrollment widget to the employee form**

In `custom-addons/hocba_employees/views/hr_employee_views.xml`, locate the form view inheriting `hr.employee` (search for `inherit_id` referencing `hr.view_employee_form`, or the existing custom form). Add a new page/group inside the notebook. Use this xpath (adjust the anchor `xpath` target to an existing `<page>` or `<notebook>` in that file — if a notebook exists, append a page):

```xml
<xpath expr="//notebook" position="inside">
    <page string="Khuôn mặt &amp; Điểm danh" name="hocba_face">
        <group>
            <field name="x_face_enrolled" readonly="1"/>
            <field name="x_face_image" widget="image" class="oe_avatar"/>
            <field name="x_face_descriptor"
                   widget="hocba_face_descriptor"
                   options="{'image_field': 'x_face_image'}"/>
        </group>
        <div class="text-muted">
            Tải ảnh chân dung rõ mặt; hệ thống sẽ tự tính vector khuôn mặt
            (cần trình duyệt hỗ trợ, chạy trên localhost hoặc HTTPS).
        </div>
    </page>
</xpath>
```

> The `hocba_face_descriptor` widget is implemented in Task 8. Until then the field renders as a plain text field — that is acceptable; the upgrade must not error.

- [ ] **Step 3: Verify upgrade**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_employees --stop-after-init --log-level=warn
```
Expected: exits 0, no traceback. (If the xpath anchor is wrong you'll get a `ParseError` naming the view — fix the anchor to a real element in that file.)

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_employees
git commit -m "feat(employees): add face enrollment fields + form page"
```

---

## Task 5: Face-distance helper + attendance fields — TDD

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py`
- Modify: `custom-addons/hocba_attendance/tests/__init__.py`
- Create: `custom-addons/hocba_attendance/tests/test_face_distance.py`

- [ ] **Step 1: Register the new test module**

Modify `custom-addons/hocba_attendance/tests/__init__.py`:

```python
from . import test_policy_geofence
from . import test_policy_window
from . import test_face_distance
```

- [ ] **Step 2: Write the failing test**

Create `custom-addons/hocba_attendance/tests/test_face_distance.py`:

```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestFaceDistance(TransactionCase):

    def test_distance_zero_identical(self):
        Att = self.env['hocba.attendance']
        a = [0.1] * 128
        self.assertAlmostEqual(Att._face_distance(a, a), 0.0, places=6)

    def test_distance_known_value(self):
        Att = self.env['hocba.attendance']
        a = [0.0] * 128
        b = [0.0] * 128
        b[0] = 3.0
        b[1] = 4.0  # euclidean = sqrt(9+16) = 5
        self.assertAlmostEqual(Att._face_distance(a, b), 5.0, places=6)

    def test_distance_none_when_length_mismatch(self):
        Att = self.env['hocba.attendance']
        self.assertIsNone(Att._face_distance([0.1, 0.2], [0.1] * 128))

    def test_distance_none_when_empty(self):
        Att = self.env['hocba.attendance']
        self.assertIsNone(Att._face_distance([], [0.1] * 128))
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance --test-enable \
  --test-tags /hocba_attendance:TestFaceDistance --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError: ... '_face_distance'`.

- [ ] **Step 4: Add imports, fields, and the helper to hr_attendance.py**

In `custom-addons/hocba_attendance/models/hr_attendance.py`:

(a) Replace the top import line `from odoo import models, fields, api` with:
```python
import json
import math

from odoo import models, fields, api
```

(b) Add these fields to the `Attendance` class (after the existing `active` field, line ~58):
```python
    # --- Face + geolocation check-in (F: face attendance) ---
    check_in_photo = fields.Binary(string='Check-in Photo', attachment=True)
    check_out_photo = fields.Binary(string='Check-out Photo', attachment=True)
    check_in_lat = fields.Float(string='Check-in Latitude', digits=(10, 7))
    check_in_lng = fields.Float(string='Check-in Longitude', digits=(10, 7))
    check_out_lat = fields.Float(string='Check-out Latitude', digits=(10, 7))
    check_out_lng = fields.Float(string='Check-out Longitude', digits=(10, 7))
    check_in_face_score = fields.Float(string='Check-in Face Distance')
    check_out_face_score = fields.Float(string='Check-out Face Distance')
    face_suspect = fields.Boolean(string='Face Suspect')
    out_of_zone = fields.Boolean(string='Out of Office Zone')
    out_of_window = fields.Boolean(string='Out of Time Window')
    needs_review = fields.Boolean(
        string='Needs Review',
        compute='_compute_needs_review',
        store=True,
    )
    check_in_map_url = fields.Char(
        string='Check-in Map', compute='_compute_map_urls')
    check_out_map_url = fields.Char(
        string='Check-out Map', compute='_compute_map_urls')

    @api.depends('face_suspect', 'out_of_zone', 'out_of_window')
    def _compute_needs_review(self):
        for rec in self:
            rec.needs_review = (
                rec.face_suspect or rec.out_of_zone or rec.out_of_window)

    @api.depends('check_in_lat', 'check_in_lng',
                 'check_out_lat', 'check_out_lng')
    def _compute_map_urls(self):
        for rec in self:
            rec.check_in_map_url = (
                'https://www.google.com/maps?q=%s,%s'
                % (rec.check_in_lat, rec.check_in_lng)
                if rec.check_in_lat and rec.check_in_lng else False)
            rec.check_out_map_url = (
                'https://www.google.com/maps?q=%s,%s'
                % (rec.check_out_lat, rec.check_out_lng)
                if rec.check_out_lat and rec.check_out_lng else False)

    @staticmethod
    def _face_distance(desc_a, desc_b):
        """Euclidean distance between two 128-d descriptors (lists of floats).
        Returns None if either is empty or lengths differ."""
        if not desc_a or not desc_b or len(desc_a) != len(desc_b):
            return None
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(desc_a, desc_b)))
```

- [ ] **Step 5: Run test to verify it passes**

Run the same command as Step 3. Expected: PASS (4 tests).

- [ ] **Step 6: Run the full module test suite (regression)**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance,hocba_employees --test-enable \
  --test-tags /hocba_attendance --stop-after-init --log-level=test
```
Expected: all tests pass (geofence + window + face), no failures.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): face-distance helper + photo/geo/flag fields"
```

---

## Task 6: `action_check_in` / `action_check_out` server methods — TDD

**Files:**
- Modify: `custom-addons/hocba_attendance/models/hr_attendance.py`
- Modify: `custom-addons/hocba_attendance/tests/__init__.py`
- Create: `custom-addons/hocba_attendance/tests/test_checkin_flow.py`

- [ ] **Step 1: Register the new test module**

Modify `custom-addons/hocba_attendance/tests/__init__.py`:

```python
from . import test_policy_geofence
from . import test_policy_window
from . import test_face_distance
from . import test_checkin_flow
```

- [ ] **Step 2: Write the failing test**

Create `custom-addons/hocba_attendance/tests/test_checkin_flow.py`:

```python
import json

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCheckinFlow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'office_lat': 21.028511, 'office_lng': 105.804817,
            'office_radius_m': 150.0, 'face_threshold': 0.6,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Nguyen Van A',
            'x_employment_status': 'official',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })

    def _payload(self, **over):
        data = {
            'employee_id': self.employee.id,
            'photo': 'ZmFrZQ==',            # base64 "fake"
            'descriptor': [0.0] * 128,       # identical -> distance 0
            'latitude': 21.028961,           # ~50m -> inside zone
            'longitude': 105.804817,
        }
        data.update(over)
        return data

    def test_checkin_creates_record(self):
        res = self.env['hocba.attendance']._do_check(self._payload(), 'in')
        self.assertTrue(res['record_id'])
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertEqual(rec.employee_id, self.employee)
        self.assertTrue(rec.check_in)
        self.assertEqual(rec.check_in_lat, 21.028961)

    def test_matching_face_not_suspect(self):
        res = self.env['hocba.attendance']._do_check(self._payload(), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertFalse(rec.face_suspect)

    def test_mismatched_face_flagged(self):
        bad = [0.0] * 128
        bad[0] = 5.0  # distance 5 > 0.6
        res = self.env['hocba.attendance']._do_check(
            self._payload(descriptor=bad), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertTrue(rec.face_suspect)

    def test_out_of_zone_flagged(self):
        res = self.env['hocba.attendance']._do_check(
            self._payload(latitude=21.037511, longitude=105.804817), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertTrue(rec.out_of_zone)

    def test_second_checkin_same_day_updates_not_duplicates(self):
        Att = self.env['hocba.attendance']
        r1 = Att._do_check(self._payload(), 'in')
        r2 = Att._do_check(self._payload(), 'in')
        self.assertEqual(r1['record_id'], r2['record_id'])
        count = Att.search_count([('employee_id', '=', self.employee.id)])
        self.assertEqual(count, 1)

    def test_checkout_updates_same_record(self):
        Att = self.env['hocba.attendance']
        r1 = Att._do_check(self._payload(), 'in')
        r2 = Att._do_check(self._payload(), 'out')
        self.assertEqual(r1['record_id'], r2['record_id'])
        rec = Att.browse(r2['record_id'])
        self.assertTrue(rec.check_out)
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance,hocba_employees --test-enable \
  --test-tags /hocba_attendance:TestCheckinFlow --stop-after-init --log-level=test
```
Expected: FAIL — `AttributeError: ... '_do_check'`.

- [ ] **Step 4: Implement `_do_check` + public RPC wrappers**

Add to the `Attendance` class in `hocba_attendance/models/hr_attendance.py`:

```python
    def _do_check(self, payload, kind):
        """Core check-in/out logic. `kind` is 'in' or 'out'.
        payload keys: employee_id, photo (base64 str), descriptor (list),
        latitude (float), longitude (float).
        Returns dict {record_id, kind, face_suspect, out_of_zone,
        out_of_window, face_score}."""
        employee = self.env['hr.employee'].browse(payload['employee_id'])
        if not employee.exists():
            from odoo.exceptions import UserError
            raise UserError('Không tìm thấy nhân viên cho điểm danh.')

        policy = self.env['hocba.attendance.policy'].get_policy()
        now = fields.Datetime.now()
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'), now
        ).replace(tzinfo=None)
        today = now_local.date()

        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        # Face matching
        face_score = 0.0
        face_suspect = False
        enrolled = []
        if employee.x_face_descriptor:
            try:
                enrolled = json.loads(employee.x_face_descriptor)
            except (ValueError, TypeError):
                enrolled = []
        dist = self._face_distance(payload.get('descriptor') or [], enrolled)
        if dist is None:
            face_suspect = True   # cannot verify -> flag for review
        else:
            face_score = dist
            face_suspect = dist > policy.face_threshold

        out_of_zone = not policy.is_within_office(lat, lng)
        out_of_window = not policy.is_within_window(now_local, kind)

        # One record per employee per day
        record = self.search([
            ('employee_id', '=', employee.id),
            ('date', '=', today),
        ], limit=1)

        if kind == 'in':
            vals = {
                'check_in': now,
                'check_in_photo': payload.get('photo'),
                'check_in_lat': lat,
                'check_in_lng': lng,
                'check_in_face_score': face_score,
            }
            if not record:
                vals['employee_id'] = employee.id
        else:  # out
            vals = {
                'check_out': now,
                'check_out_photo': payload.get('photo'),
                'check_out_lat': lat,
                'check_out_lng': lng,
                'check_out_face_score': face_score,
            }
            if not record:
                # checkout with no prior check-in today: still create
                vals['employee_id'] = employee.id
                vals['check_in'] = now

        vals.update({
            'face_suspect': face_suspect,
            'out_of_zone': out_of_zone,
            'out_of_window': out_of_window,
        })

        if record:
            record.write(vals)
        else:
            record = self.create(vals)

        return {
            'record_id': record.id,
            'kind': kind,
            'face_suspect': face_suspect,
            'out_of_zone': out_of_zone,
            'out_of_window': out_of_window,
            'face_score': face_score,
        }

    @api.model
    def action_check_in(self, payload):
        """RPC entry: self-service check-in for the current user's employee."""
        payload = dict(payload or {})
        payload.setdefault('employee_id', self.env.user.employee_id.id)
        return self._do_check(payload, 'in')

    @api.model
    def action_check_out(self, payload):
        """RPC entry: self-service check-out for the current user's employee."""
        payload = dict(payload or {})
        payload.setdefault('employee_id', self.env.user.employee_id.id)
        return self._do_check(payload, 'out')
```

> Note: the existing `_compute_status` runs on `check_in` change and searches `hocba.attendance.status` records by code; that remains unaffected. Move the `from odoo.exceptions import UserError` import to the top of the file alongside the others if you prefer — inline import shown to keep the diff local; top-level is cleaner.

- [ ] **Step 5: Run test to verify it passes**

Run the same command as Step 3. Expected: PASS (6 tests).

- [ ] **Step 6: Run full suite**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance,hocba_employees --test-enable \
  --test-tags /hocba_attendance --stop-after-init --log-level=test
```
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): server check-in/out with face+geo flagging"
```

---

## Task 7: HR views — flags, review filter, policy config menu

**Files:**
- Modify: `custom-addons/hocba_attendance/views/hr_attendance_views.xml`
- Create: `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml`
- Modify: `custom-addons/hocba_attendance/views/menus.xml`
- Modify: `custom-addons/hocba_attendance/__manifest__.py`

- [ ] **Step 1: Add flag columns + photos/map to attendance views**

In `custom-addons/hocba_attendance/views/hr_attendance_views.xml`:

(a) In the list view (`hocba_attendance_tree`), add before `</list>`:
```xml
                    <field name="needs_review" widget="boolean_toggle" optional="show"/>
                    <field name="face_suspect" optional="hide"/>
                    <field name="out_of_zone" optional="hide"/>
                    <field name="out_of_window" optional="hide"/>
```

(b) In the search view (`hocba_attendance_search`), add after the existing `filter_late` filter:
```xml
                    <separator/>
                    <filter name="filter_needs_review" string="Cần xem xét"
                            domain="[('needs_review', '=', True)]"/>
```

(c) In the form view (`hocba_attendance_form`), add a new group after the "Notes" group, before `</sheet>`:
```xml
                        <group string="Điểm danh khuôn mặt &amp; vị trí">
                            <group>
                                <field name="check_in_photo" widget="image"/>
                                <field name="check_in_face_score"/>
                                <field name="check_in_map_url" widget="url"
                                       readonly="1"/>
                            </group>
                            <group>
                                <field name="check_out_photo" widget="image"/>
                                <field name="check_out_face_score"/>
                                <field name="check_out_map_url" widget="url"
                                       readonly="1"/>
                            </group>
                            <group>
                                <field name="face_suspect"/>
                                <field name="out_of_zone"/>
                                <field name="out_of_window"/>
                                <field name="needs_review"/>
                            </group>
                        </group>
```

- [ ] **Step 2: Create the policy config view**

Create `custom-addons/hocba_attendance/views/hocba_attendance_policy_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <record id="hocba_attendance_policy_form" model="ir.ui.view">
            <field name="name">Attendance Policy Form</field>
            <field name="model">hocba.attendance.policy</field>
            <field name="arch" type="xml">
                <form>
                    <sheet>
                        <group>
                            <field name="name"/>
                            <field name="active"/>
                        </group>
                        <group string="Khung giờ (giờ địa phương)">
                            <group>
                                <field name="morning_start"/>
                                <field name="morning_end"/>
                            </group>
                            <group>
                                <field name="evening_start"/>
                                <field name="evening_end"/>
                            </group>
                        </group>
                        <group string="Ngày làm việc">
                            <field name="workday_mon"/>
                            <field name="workday_tue"/>
                            <field name="workday_wed"/>
                            <field name="workday_thu"/>
                            <field name="workday_fri"/>
                            <field name="workday_sat"/>
                            <field name="workday_sun"/>
                        </group>
                        <group string="Văn phòng (geofence)">
                            <field name="office_lat"/>
                            <field name="office_lng"/>
                            <field name="office_radius_m"/>
                        </group>
                        <group string="Nhận diện khuôn mặt">
                            <field name="face_threshold"/>
                        </group>
                    </sheet>
                </form>
            </field>
        </record>

        <record id="hocba_attendance_policy_tree" model="ir.ui.view">
            <field name="name">Attendance Policy List</field>
            <field name="model">hocba.attendance.policy</field>
            <field name="arch" type="xml">
                <list>
                    <field name="name"/>
                    <field name="office_radius_m"/>
                    <field name="face_threshold"/>
                    <field name="active"/>
                </list>
            </field>
        </record>

        <record id="hocba_attendance_policy_action" model="ir.actions.act_window">
            <field name="name">Attendance Policy</field>
            <field name="res_model">hocba.attendance.policy</field>
            <field name="view_mode">list,form</field>
        </record>
    </data>
</odoo>
```

- [ ] **Step 3: Add the config menu**

In `custom-addons/hocba_attendance/views/menus.xml`, add inside the Configuration menu block (after the Attendance Status menu item, before `</data>`):

```xml
        <menuitem name="Attendance Policy" id="hocba_attendance_policy_menu_items"
                  parent="hocba_attendance_config_menu"
                  action="hocba_attendance_policy_action" sequence="20"/>
```

- [ ] **Step 4: Register the policy view in the manifest**

In `custom-addons/hocba_attendance/__manifest__.py`, add to `'data'` after `'data/hocba_attendance_policy_data.xml',`:
```python
        'views/hocba_attendance_policy_views.xml',
```
(Place it before `views/menus.xml` so the action exists when the menu references it.)

- [ ] **Step 5: Verify upgrade**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance --stop-after-init --log-level=warn
```
Expected: exits 0, no `ParseError`/traceback. (A ParseError will name the offending view — fix field names/anchors as needed.)

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_attendance
git commit -m "feat(attendance): HR views for flags, review filter, policy config"
```

---

## Task 8: Frontend — vendored face-api.js + OWL client action + employee widget

> This task delivers the browser UI. It cannot be unit-tested with the Odoo test runner; it ends with a **manual verification** step. Keep server changes (Tasks 1-7) green before starting.

**Files:**
- Create: `custom-addons/hocba_attendance/static/lib/face-api/face-api.min.js`
- Create: `custom-addons/hocba_attendance/static/lib/face-api/models/` (weight files)
- Create: `custom-addons/hocba_attendance/static/src/js/attendance_kiosk.js`
- Create: `custom-addons/hocba_attendance/static/src/xml/attendance_kiosk.xml`
- Create: `custom-addons/hocba_attendance/static/src/js/face_descriptor_field.js`
- Create: `custom-addons/hocba_attendance/static/src/xml/face_descriptor_field.xml`
- Create: `custom-addons/hocba_attendance/static/src/scss/attendance_kiosk.scss`
- Modify: `custom-addons/hocba_attendance/views/menus.xml`
- Modify: `custom-addons/hocba_attendance/__manifest__.py`

- [ ] **Step 1: Vendor face-api.js and model weights**

Download the library and the required model weights into the module. Run from repo root:

```bash
mkdir -p custom-addons/hocba_attendance/static/lib/face-api/models
curl -L -o custom-addons/hocba_attendance/static/lib/face-api/face-api.min.js \
  https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.js
BASE=https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model
for f in tiny_face_detector_model-weights_manifest.json \
         tiny_face_detector_model.bin \
         face_landmark_68_model-weights_manifest.json \
         face_landmark_68_model.bin \
         face_recognition_model-weights_manifest.json \
         face_recognition_model-shard1 \
         face_recognition_model-shard2; do
  curl -L -o "custom-addons/hocba_attendance/static/lib/face-api/models/$f" "$BASE/$f"
done
```
Expected: 8 files present and non-empty. Verify:
```bash
ls -la custom-addons/hocba_attendance/static/lib/face-api/models
```

> If `@vladmandic/face-api` model filenames differ, open the downloaded `*-weights_manifest.json` and fetch the exact `.bin`/`-shard*` filenames it references. The three models needed are: **tiny_face_detector**, **face_landmark_68**, **face_recognition**.

- [ ] **Step 2: Write the OWL client action JS**

Create `custom-addons/hocba_attendance/static/src/js/attendance_kiosk.js`:

```javascript
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";

const MODELS_URL = "/hocba_attendance/static/lib/face-api/models";

export class AttendanceKiosk extends Component {
    static template = "hocba_attendance.AttendanceKiosk";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.state = useState({
            ready: false,
            busy: false,
            enrolled: false,
            employeeName: "",
            message: "Đang khởi tạo...",
        });
        this._stream = null;

        onWillStart(async () => {
            await this._loadFaceApi();
            await this._loadEmployee();
        });
        onMounted(() => this._startCamera());
        onWillUnmount(() => this._stopCamera());
    }

    async _loadFaceApi() {
        if (!window.faceapi) {
            await new Promise((resolve, reject) => {
                const s = document.createElement("script");
                s.src = "/hocba_attendance/static/lib/face-api/face-api.min.js";
                s.onload = resolve;
                s.onerror = reject;
                document.head.appendChild(s);
            });
        }
        const faceapi = window.faceapi;
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL);
        await faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL);
        await faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL);
    }

    async _loadEmployee() {
        const emp = await this.orm.call("hr.employee", "get_self_attendance_info", []);
        this.state.employeeName = emp.name || "";
        this.state.enrolled = !!emp.enrolled;
        this.state.ready = true;
        this.state.message = this.state.enrolled
            ? "Sẵn sàng điểm danh"
            : "Bạn chưa đăng ký khuôn mặt — bấm Đăng ký để chụp ảnh mẫu.";
    }

    async _startCamera() {
        try {
            this._stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.videoRef.el.srcObject = this._stream;
        } catch (e) {
            this.state.message = "Không truy cập được camera. Cần HTTPS/localhost và cấp quyền.";
        }
    }

    _stopCamera() {
        if (this._stream) {
            this._stream.getTracks().forEach((t) => t.stop());
            this._stream = null;
        }
    }

    _capturePhotoDataUrl() {
        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        return canvas.toDataURL("image/jpeg", 0.85);
    }

    async _computeDescriptor() {
        const faceapi = window.faceapi;
        const det = await faceapi
            .detectSingleFace(this.videoRef.el, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();
        return det ? Array.from(det.descriptor) : null;
    }

    _getLocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({ latitude: 0, longitude: 0 });
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                }),
                () => resolve({ latitude: 0, longitude: 0 }),
                { enableHighAccuracy: true, timeout: 8000 }
            );
        });
    }

    async _captureCommon() {
        const descriptor = await this._computeDescriptor();
        if (!descriptor) {
            this.notification.add("Không phát hiện khuôn mặt. Thử lại.", { type: "warning" });
            return null;
        }
        const dataUrl = this._capturePhotoDataUrl();
        const photo = dataUrl.split(",")[1]; // strip data: prefix -> base64
        const loc = await this._getLocation();
        return { descriptor, photo, latitude: loc.latitude, longitude: loc.longitude };
    }

    async onEnroll() {
        this.state.busy = true;
        try {
            const cap = await this._captureCommon();
            if (!cap) return;
            await this.orm.call("hr.employee", "enroll_self_face", [
                { photo: cap.photo, descriptor: cap.descriptor },
            ]);
            this.state.enrolled = true;
            this.state.message = "Đăng ký khuôn mặt thành công.";
            this.notification.add("Đã lưu khuôn mặt mẫu.", { type: "success" });
        } finally {
            this.state.busy = false;
        }
    }

    async _check(kind) {
        if (!this.state.enrolled) {
            this.notification.add("Hãy đăng ký khuôn mặt trước.", { type: "warning" });
            return;
        }
        this.state.busy = true;
        try {
            const cap = await this._captureCommon();
            if (!cap) return;
            const method = kind === "in" ? "action_check_in" : "action_check_out";
            const res = await this.orm.call("hocba.attendance", method, [cap]);
            const flags = [];
            if (res.face_suspect) flags.push("khuôn mặt nghi ngờ");
            if (res.out_of_zone) flags.push("ngoài vùng văn phòng");
            if (res.out_of_window) flags.push("ngoài khung giờ");
            const msg = (kind === "in" ? "Đã check-in" : "Đã check-out")
                + (flags.length ? " (⚠ " + flags.join(", ") + ")" : " thành công");
            this.notification.add(msg, { type: flags.length ? "warning" : "success" });
        } finally {
            this.state.busy = false;
        }
    }

    onCheckIn() { return this._check("in"); }
    onCheckOut() { return this._check("out"); }
}

registry.category("actions").add("hocba_attendance_kiosk", AttendanceKiosk);
```

- [ ] **Step 3: Write the OWL template**

Create `custom-addons/hocba_attendance/static/src/xml/attendance_kiosk.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="hocba_attendance.AttendanceKiosk">
        <div class="o_hocba_kiosk p-3">
            <h2>Điểm danh — <t t-esc="state.employeeName"/></h2>
            <p class="text-muted" t-esc="state.message"/>
            <div class="o_hocba_kiosk_video">
                <video t-ref="video" autoplay="true" playsinline="true" width="480"/>
                <canvas t-ref="canvas" class="d-none"/>
            </div>
            <div class="mt-3 d-flex gap-2">
                <button class="btn btn-secondary" t-on-click="onEnroll"
                        t-att-disabled="state.busy or not state.ready">
                    Đăng ký khuôn mặt
                </button>
                <button class="btn btn-primary" t-on-click="onCheckIn"
                        t-att-disabled="state.busy or not state.enrolled">
                    Check In
                </button>
                <button class="btn btn-warning" t-on-click="onCheckOut"
                        t-att-disabled="state.busy or not state.enrolled">
                    Check Out
                </button>
            </div>
        </div>
    </t>
</templates>
```

- [ ] **Step 4: Write the employee descriptor widget (form view)**

Create `custom-addons/hocba_attendance/static/src/js/face_descriptor_field.js`:

```javascript
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const MODELS_URL = "/hocba_attendance/static/lib/face-api/models";

export class FaceDescriptorField extends Component {
    static template = "hocba_attendance.FaceDescriptorField";
    static props = { ...standardFieldProps, imageField: { type: String, optional: true } };

    setup() {
        this.notification = useService("notification");
        onWillStart(() => this._loadFaceApi());
    }

    async _loadFaceApi() {
        if (!window.faceapi) {
            await new Promise((resolve, reject) => {
                const s = document.createElement("script");
                s.src = "/hocba_attendance/static/lib/face-api/face-api.min.js";
                s.onload = resolve;
                s.onerror = reject;
                document.head.appendChild(s);
            });
        }
        const faceapi = window.faceapi;
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL);
        await faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL);
        await faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL);
    }

    get hasDescriptor() {
        return !!this.props.record.data[this.props.name];
    }

    async onCompute() {
        const imageField = this.props.imageField || "x_face_image";
        const b64 = this.props.record.data[imageField];
        if (!b64) {
            this.notification.add("Hãy tải ảnh khuôn mặt trước.", { type: "warning" });
            return;
        }
        const img = new Image();
        img.src = "data:image/png;base64," + b64;
        await img.decode();
        const faceapi = window.faceapi;
        const det = await faceapi
            .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();
        if (!det) {
            this.notification.add("Không phát hiện khuôn mặt trong ảnh.", { type: "danger" });
            return;
        }
        await this.props.record.update({
            [this.props.name]: JSON.stringify(Array.from(det.descriptor)),
        });
        this.notification.add("Đã tính vector khuôn mặt. Nhớ Lưu.", { type: "success" });
    }
}

export const faceDescriptorField = {
    component: FaceDescriptorField,
    supportedTypes: ["text"],
    extractProps: ({ options }) => ({ imageField: options.image_field }),
};

registry.category("fields").add("hocba_face_descriptor", faceDescriptorField);
```

Create `custom-addons/hocba_attendance/static/src/xml/face_descriptor_field.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="hocba_attendance.FaceDescriptorField">
        <div class="o_field_face_descriptor">
            <span t-if="hasDescriptor" class="badge text-bg-success">Đã có vector</span>
            <span t-else="" class="badge text-bg-secondary">Chưa có vector</span>
            <button class="btn btn-sm btn-secondary ms-2" t-on-click="onCompute">
                Tính vector từ ảnh
            </button>
        </div>
    </t>
</templates>
```

- [ ] **Step 5: Add the SCSS (minimal)**

Create `custom-addons/hocba_attendance/static/src/scss/attendance_kiosk.scss`:

```scss
.o_hocba_kiosk {
    max-width: 560px;

    .o_hocba_kiosk_video video {
        border-radius: 8px;
        background: #000;
        max-width: 100%;
    }
}
```

- [ ] **Step 6: Add the two employee helper methods (server)**

In `custom-addons/hocba_employees/models/hr_employee.py`, add to the `hr.employee` class:

```python
    @api.model
    def get_self_attendance_info(self):
        """Return current user's employee name + enrollment state for kiosk."""
        emp = self.env.user.employee_id
        return {
            'employee_id': emp.id,
            'name': emp.name,
            'enrolled': bool(emp.x_face_descriptor),
        }

    def enroll_self_face(self, payload):
        """Save the current user's face sample (image + descriptor)."""
        emp = self.env.user.employee_id
        if not emp:
            from odoo.exceptions import UserError
            raise UserError('Tài khoản chưa gắn với hồ sơ nhân viên.')
        emp.write({
            'x_face_image': payload.get('photo'),
            'x_face_descriptor': json.dumps(payload.get('descriptor') or []),
        })
        return True
```

Also add `import json` to the top of `hr_employee.py` if not already present (check the existing imports; the file uses `from odoo import ...` and `from datetime import timedelta` — add `import json` near the top).

- [ ] **Step 7: Register assets + client-action menu in manifest and menus**

(a) In `custom-addons/hocba_attendance/__manifest__.py`, add an `assets` key (after `'data': [...]`):
```python
    'assets': {
        'web.assets_backend': [
            'hocba_attendance/static/src/js/attendance_kiosk.js',
            'hocba_attendance/static/src/xml/attendance_kiosk.xml',
            'hocba_attendance/static/src/js/face_descriptor_field.js',
            'hocba_attendance/static/src/xml/face_descriptor_field.xml',
            'hocba_attendance/static/src/scss/attendance_kiosk.scss',
        ],
    },
```

(b) In `custom-addons/hocba_attendance/views/menus.xml`, add a client action + menu under the Attendance root (after `hocba_attendance_menu`):
```xml
        <record id="hocba_my_attendance_action" model="ir.actions.client">
            <field name="name">My Attendance</field>
            <field name="tag">hocba_attendance_kiosk</field>
        </record>
        <menuitem name="My Attendance" id="hocba_my_attendance_menu"
                  parent="hocba_attendance_menu_root"
                  action="hocba_my_attendance_action" sequence="5"/>
```

- [ ] **Step 8: Upgrade and confirm server boots**

Run:
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance,hocba_employees --stop-after-init --log-level=warn
```
Expected: exits 0, no traceback. (Asset bundle errors usually surface at runtime, not here — Step 9 covers that.)

- [ ] **Step 9: Manual verification (browser)**

1. Start the stack: `docker compose up -d`
2. Open `http://localhost:8069`, log in as a user whose `employee_id` has `x_employment_status = official`.
3. Open menu **HOCBA HRM → Attendance → My Attendance**. Grant camera + location permission.
4. If not enrolled: click **Đăng ký khuôn mặt** → expect "Đăng ký thành công" and the buttons enable.
5. Click **Check In** → expect a success/warning notification; verify a record appears in **Attendance Records** for today with a check-in photo, a Google-Maps URL, and a face distance.
6. Set the office coordinates far from your location in **Configuration → Attendance Policy**, check in again → expect the **out_of_zone** flag and **Needs Review** = true.
7. Click **Check Out** → expect the same record updated with check-out fields.
8. As an HR user, open the attendance list, enable the **Cần xem xét** filter → flagged records appear.

Record the outcome of each sub-step. If any fails, debug before marking the task complete.

- [ ] **Step 10: Commit**

```bash
git add custom-addons/hocba_attendance custom-addons/hocba_employees
git commit -m "feat(attendance): kiosk client action + face widget + vendored face-api"
```

---

## Final verification

- [ ] **Run the complete test suite:**
```bash
docker compose run --rm odoo odoo -d hocba_hrm \
  -u hocba_attendance,hocba_employees --test-enable \
  --test-tags /hocba_attendance --stop-after-init --log-level=test
```
Expected: all tests in `test_policy_geofence`, `test_policy_window`, `test_face_distance`, `test_checkin_flow` pass, 0 failures/errors.

- [ ] **Confirm manual browser checks (Task 8 Step 9) all passed.**

---

## Spec coverage check

| Spec requirement | Task |
|---|---|
| Capture face photo, save to DB | Task 5 (`check_in_photo`/`check_out_photo`), Task 6 (store), Task 8 (capture) |
| Face verification (descriptor match) | Task 5 (`_face_distance`), Task 6 (`face_suspect`), Task 4 (enroll fields), Task 8 (compute) |
| Enrollment: HR upload + self-service | Task 4 (HR field + widget), Task 8 (`enroll_self_face`, widget compute) |
| GPS capture + geofence | Task 2 (haversine), Task 6 (`out_of_zone`), Task 8 (geolocation) |
| Time window 08:00-09:30 / 16:00-17:30, Mon-Fri | Task 1 (policy defaults), Task 3 (window helpers), Task 6 (`out_of_window`) |
| Official employees only | Task 6 (employee resolution); Task 8 Step 9 (UI access via official user) |
| Allow-but-flag on violation | Task 6 (`_do_check` always creates/updates, sets flags) |
| One record per employee per day | Task 6 (`test_second_checkin_same_day_updates_not_duplicates`) |
| HR review UI (flags, filter, photo, map) | Task 7 |
| Configurable policy | Task 1 + Task 7 |
| Backend self-service OWL UI | Task 8 |
| Unit tests (geofence/window/threshold/flags/one-per-day) | Tasks 2, 3, 5, 6 |
| HTTPS/localhost constraint | Task 8 Step 9 (documented in manual steps) |

> **Note on "official only":** the server methods resolve the current user's employee and flag anomalies but do not hard-block non-official employees (consistent with the allow-but-flag decision). The UI is reached via menu; restricting the menu/action to official employees is out of scope per the spec's allow-but-flag stance. If hard restriction is later desired, add a guard in `action_check_in`/`action_check_out` raising for non-official status — tracked as a possible follow-up, not implemented here.
