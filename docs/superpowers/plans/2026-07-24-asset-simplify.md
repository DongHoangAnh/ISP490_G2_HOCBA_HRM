# Rút gọn F-006 Quản lý tài sản — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hạ tính năng tài sản xuống một danh sách phẳng "nhân viên ↔ tài sản đang giữ": bỏ trạng thái, thu hồi, chuyển giao và 2 chỗ chặn nghiệp vụ ăn theo.

**Architecture:** `hr.employee.asset` còn 5 trường, mã tài sản unique toàn bảng, xoá dòng = thu hồi. Migration pre- dọn dữ liệu lịch sử trước khi bỏ cột `state`. Offboarding/archive chuyển từ *chặn* sang *hiển thị cảnh báo*. API bỏ 2 route vòng đời, thêm route xoá dòng; SPA còn form "Cấp phát" + nút "Gỡ".

**Tech Stack:** Odoo 19 (Python 3.12, `models.Constraint`), controller `hocba_hrm`, SPA React 18/Vite 6, test `odoo --test-tags`.

**Spec:** `docs/superpowers/specs/2026-07-24-asset-simplify-design.md`

**Lệnh test dùng xuyên suốt** (Git Bash — thiếu `MSYS_NO_PATHCONV=1` sẽ chạy 0 test mà vẫn báo OK):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

---

### Task 1: Test đỏ — luật mới của tài sản

**Files:**
- Create: `custom-addons/hocba_employees/tests/test_asset.py`
- Modify: `custom-addons/hocba_employees/tests/__init__.py`
- Modify: `custom-addons/hocba_employees/tests/test_offboarding.py:82-96`

- [ ] **Step 1: Viết file test mới**

Tạo `custom-addons/hocba_employees/tests/test_asset.py`:

```python
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestEmployeeAssetSimple(TransactionCase):
    """F-006 rút gọn: danh sách phẳng 'ai đang giữ tài sản nào'."""

    def setUp(self):
        super().setUp()
        self.atype = self.env['hocba.asset.type'].create({
            'name': 'Laptop Test', 'code': 'LAPTST'})
        # BR-010: NV phải có CCCD 12 số, mỗi người một giá trị.
        self.emp = self.env['hr.employee'].create({
            'name': 'Asset Holder', 'identification_id': '021111111101'})
        self.emp2 = self.env['hr.employee'].create({
            'name': 'Asset Holder 2', 'identification_id': '021111111102'})

    def _grant(self, emp, code, **kw):
        vals = {
            'employee_id': emp.id,
            'asset_type_id': self.atype.id,
            'asset_code': code,
            'grant_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hr.employee.asset'].create(vals)

    def test_lifecycle_fields_removed(self):
        fnames = self.env['hr.employee.asset']._fields
        for gone in ('state', 'return_date', 'transferred_to',
                     'condition_out_note'):
            self.assertNotIn(gone, fnames)

    def test_delete_row_allowed(self):
        rec = self._grant(self.emp, 'LAPTST-DEL')
        rec.unlink()
        self.assertFalse(rec.exists())

    def test_asset_code_unique(self):
        self._grant(self.emp, 'LAPTST-DUP')
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self._grant(self.emp2, 'LAPTST-DUP')
                self.env.flush_all()

    def test_grant_before_week2_gate_allowed(self):
        # Ràng buộc "ngày cấp >= mốc tuần-2" đã bị bỏ.
        self.emp.sudo().x_eval_2w_date = fields.Date.today()
        rec = self._grant(self.emp, 'LAPTST-EARLY',
                          grant_date=fields.Date.today() - timedelta(days=30))
        self.assertTrue(rec.id)

    def test_archive_employee_with_asset(self):
        self._grant(self.emp, 'LAPTST-ARCH')
        self.emp.active = False
        self.assertFalse(self.emp.active)

    def test_asset_count_counts_all_rows(self):
        self._grant(self.emp, 'LAPTST-C1')
        self._grant(self.emp, 'LAPTST-C2')
        self.assertEqual(self.emp.x_asset_count, 2)
```

- [ ] **Step 2: Đăng ký test vào `tests/__init__.py`**

Thêm dòng (giữ thứ tự alphabet với các dòng `from . import test_*` sẵn có):

```python
from . import test_asset
```

- [ ] **Step 3: Đảo ngược test chặn nghỉ việc**

Trong `custom-addons/hocba_employees/tests/test_offboarding.py`, thay **toàn bộ** method `test_done_blocked_when_asset_assigned` (dòng 82–96) bằng:

```python
    def test_done_allowed_when_asset_assigned(self):
        # F-006 rút gọn: còn tài sản KHÔNG chặn hoàn tất, chỉ hiển thị.
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
        self.assertEqual(rec.asset_count, 1)
        self.assertEqual(rec.asset_codes, 'LAPOFF-1')
        rec.sudo().action_done()
        self.assertEqual(rec.state, 'done')
```

- [ ] **Step 4: Chạy test để thấy đỏ**

Chạy lệnh test ở đầu plan.
Kỳ vọng: FAIL/ERROR — `test_lifecycle_fields_removed` báo `'state' in fields`, `test_delete_row_allowed` raise `UserError: Không được xóa bản ghi tài sản`, `test_done_allowed_when_asset_assigned` báo `AttributeError`/`ValidationError` vì `asset_count` chưa tồn tại.

---

### Task 2: Rút gọn model, ACL, view backend, migration

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee_asset.py` (thay toàn bộ)
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv:8-9`
- Modify: `custom-addons/hocba_employees/views/hr_employee_asset_views.xml:4-75`
- Modify: `custom-addons/hocba_employees/__manifest__.py:3`
- Create: `custom-addons/hocba_employees/migrations/19.0.3.0.0/pre-migrate.py`

- [ ] **Step 1: Thay toàn bộ nội dung `hr_employee_asset.py`**

```python
from odoo import models, fields


class HrEmployeeAsset(models.Model):
    """F-006 (rút gọn): danh sách tài sản nhân viên ĐANG giữ.

    Không có vòng đời: thu hồi = xoá dòng; bàn giao = xoá dòng người cũ +
    thêm dòng người mới. Quyết định theo góp ý giảng viên, xem
    docs/superpowers/specs/2026-07-24-asset-simplify-design.md
    """
    _name = 'hr.employee.asset'
    _description = 'Tài sản nhân viên đang giữ'
    _order = 'employee_id, grant_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên giữ',
        required=True, ondelete='cascade', index=True)
    asset_type_id = fields.Many2one(
        'hocba.asset.type', string='Loại tài sản', required=True)
    asset_code = fields.Char(string='Mã tài sản', required=True)
    grant_date = fields.Date(
        string='Ngày cấp phát', required=True,
        default=fields.Date.context_today)
    condition_in = fields.Selection(
        selection=[('new', 'Mới'), ('good', 'Tốt'), ('fair', 'Trung bình')],
        string='Tình trạng khi cấp', required=True, default='good')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _asset_code_uniq = models.Constraint(
        'unique (asset_code)',
        'Mã tài sản này đã được gán cho nhân viên khác!',
    )
```

Lưu ý: `ondelete` đổi `restrict` → `cascade` (xoá NV thì dòng tài sản đi theo — không còn lịch sử cần giữ).

- [ ] **Step 2: Bật quyền xoá trong ACL**

Trong `custom-addons/hocba_employees/security/ir.model.access.csv`, thay 2 dòng 8–9 (cột cuối `perm_unlink` từ `0` → `1`):

```csv
access_hr_employee_asset_user,access.hr.employee.asset.user,model_hr_employee_asset,hr.group_hr_user,1,1,1,1
access_hr_employee_asset_manager,access.hr.employee.asset.manager,model_hr_employee_asset,hr.group_hr_manager,1,1,1,1
```

- [ ] **Step 3: Rút gọn view backend**

Trong `custom-addons/hocba_employees/views/hr_employee_asset_views.xml`, thay 3 record đầu (`hr_employee_asset_form`, `hr_employee_asset_list`, `hr_employee_asset_search` — dòng 4–75) bằng:

```xml
        <!-- Tài sản: danh sách phẳng "ai đang giữ gì" (F-006 rút gọn) -->
        <record id="hr_employee_asset_form" model="ir.ui.view">
            <field name="name">hr.employee.asset.form</field>
            <field name="model">hr.employee.asset</field>
            <field name="arch" type="xml">
                <form>
                    <sheet>
                        <group>
                            <field name="employee_id"/>
                            <field name="asset_type_id"/>
                            <field name="asset_code"/>
                            <field name="grant_date"/>
                            <field name="condition_in"/>
                        </group>
                    </sheet>
                </form>
            </field>
        </record>

        <record id="hr_employee_asset_list" model="ir.ui.view">
            <field name="name">hr.employee.asset.list</field>
            <field name="model">hr.employee.asset</field>
            <field name="arch" type="xml">
                <list>
                    <field name="asset_code"/>
                    <field name="asset_type_id"/>
                    <field name="employee_id"/>
                    <field name="grant_date"/>
                    <field name="condition_in" optional="show"/>
                </list>
            </field>
        </record>

        <record id="hr_employee_asset_search" model="ir.ui.view">
            <field name="name">hr.employee.asset.search</field>
            <field name="model">hr.employee.asset</field>
            <field name="arch" type="xml">
                <search>
                    <field name="asset_code"/>
                    <field name="employee_id"/>
                    <field name="asset_type_id"/>
                    <group>
                        <filter name="group_employee" string="Nhân viên" context="{'group_by': 'employee_id'}"/>
                        <filter name="group_type" string="Loại tài sản" context="{'group_by': 'asset_type_id'}"/>
                    </group>
                </search>
            </field>
        </record>
```

Đồng thời bỏ context lọc theo trạng thái ở action (dòng 98) — xoá hẳn dòng:

```xml
            <field name="context">{'search_default_assigned': 1}</field>
```

- [ ] **Step 4: Nâng version module**

Trong `custom-addons/hocba_employees/__manifest__.py` dòng 3:

```python
    'version': '19.0.3.0.0',
```

- [ ] **Step 5: Viết migration pre- dọn dữ liệu lịch sử**

Tạo `custom-addons/hocba_employees/migrations/19.0.3.0.0/pre-migrate.py`:

```python
# Migration 19.0.3.0.0 — F-006 rút gọn: bỏ vòng đời tài sản.
# Phải xoá các dòng lịch sử (đã thu hồi / đã chuyển giao) TRƯỚC khi ORM bỏ
# cột state; nếu để lại chúng sẽ được hiểu là "đang giữ" và đụng ràng buộc
# unique asset_code mới.
# Spec: docs/superpowers/specs/2026-07-24-asset-simplify-design.md
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'hr_employee_asset' AND column_name = 'state'
    """)
    if not cr.fetchone():
        return
    cr.execute("""
        DELETE FROM hr_employee_asset
         WHERE state IN ('returned', 'transferred')
    """)
    _logger.info('F-006: xoá %s dòng tài sản lịch sử.', cr.rowcount)
    # Khử trùng mã còn sót (dữ liệu bẩn) — giữ dòng id nhỏ nhất.
    cr.execute("""
        DELETE FROM hr_employee_asset a
         USING hr_employee_asset b
         WHERE a.asset_code = b.asset_code AND a.id > b.id
    """)
    if cr.rowcount:
        _logger.warning('F-006: xoá %s dòng trùng mã tài sản.', cr.rowcount)
```

---

### Task 3: Gỡ 2 chỗ chặn + đếm lại tài sản

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py:243-248, 296-305, 547-557, 635-661`
- Modify: `custom-addons/hocba_employees/models/hocba_offboarding.py:52-68, 168-186`

- [ ] **Step 1: `hr_employee.py` — đếm toàn bộ dòng tài sản**

Thay `_compute_asset_count` (dòng 243–248):

```python
    @api.depends('x_asset_ids')
    def _compute_asset_count(self):
        # F-006 rút gọn: mọi dòng tài sản đều là "đang giữ".
        for emp in self:
            emp.x_asset_count = len(emp.x_asset_ids)
```

- [ ] **Step 2: `hr_employee.py` — bỏ chặn lưu trữ hồ sơ**

Trong `write()` (dòng 547–557), xoá **toàn bộ** khối sau, để `def write(self, vals):` đi thẳng tới comment `# F-001: không sửa tay probation→official ...`:

```python
        # F-006: chặn Archive khi còn tài sản chưa thu hồi/chuyển giao
        if vals.get('active') is False:
            for emp in self:
                pending = emp.x_asset_ids.filtered(lambda a: a.state == 'assigned')
                if pending:
                    raise ValidationError(_(
                        'Không thể lưu trữ "%(emp)s" — còn %(n)d tài sản chưa thu hồi: '
                        '%(codes)s') % {
                            'emp': emp.name, 'n': len(pending),
                            'codes': ', '.join(pending.mapped('asset_code'))})
```

- [ ] **Step 3: `hr_employee.py` — bỏ tham chiếu `state` khi tự cấp tài sản**

Trong `_hocba_grant_default_assets` (dòng 643–653), thay 2 lệnh `search_count`:

```python
        for atype in defaults:
            has = Asset.search_count([
                ('employee_id', '=', self.id),
                ('asset_type_id', '=', atype.id)])
            if has:
                continue
            code = '%s-%s' % (atype.code, self.x_employee_code or self.id)
            if Asset.search_count([('asset_code', '=', code)]):
                continue
```

- [ ] **Step 4: `hocba_offboarding.py` — đổi bộ đếm thành thông tin hiển thị**

Thay field + compute (dòng 52–68):

```python
    asset_count = fields.Integer(
        string='Tài sản đang giữ', compute='_compute_asset_info')
    asset_codes = fields.Char(
        string='Mã tài sản đang giữ', compute='_compute_asset_info')
```

```python
    @api.depends('employee_id.x_asset_ids')
    def _compute_asset_info(self):
        # sudo: ACL hr.employee.asset chỉ cấp nhóm HR, nhưng NV/quản lý cần
        # thấy tài sản đang giữ trên đơn trong phạm vi mình.
        for rec in self:
            assets = rec.employee_id.sudo().x_asset_ids
            rec.asset_count = len(assets)
            rec.asset_codes = ', '.join(assets.mapped('asset_code'))
```

- [ ] **Step 5: `hocba_offboarding.py` — bỏ chặn hoàn tất**

Trong `action_done()` (dòng 179–185), xoá khối:

```python
            pending = emp.x_asset_ids.filtered(lambda a: a.state == 'assigned')
            if pending:
                raise ValidationError(_(
                    'Còn %(n)d tài sản chưa thu hồi: %(codes)s') % {
                        'n': len(pending),
                        'codes': ', '.join(pending.mapped('asset_code'))})
```

giữ lại `emp = rec.employee_id` ở dòng trên và đi thẳng tới `rec.actual_leave_date = ...`.

Đồng thời sửa nội dung thông báo khi HR duyệt (dòng 171) cho khớp thực tế:

```python
                '%s — chờ hoàn tất thủ tục nghỉ việc.' % rec.name)
```

- [ ] **Step 6: Sửa view offboarding backend**

Trong `custom-addons/hocba_employees/views/hocba_offboarding_views.xml`, đổi tên field ở **cả 2 chỗ** (dòng 39 trong form, dòng 68 trong list):

```xml
                            <field name="asset_pending_count"/>
```

thành:

```xml
                            <field name="asset_count"/>
```

- [ ] **Step 7: Chạy test — kỳ vọng xanh**

Chạy lệnh test ở đầu plan.
Kỳ vọng: `0 failed, 0 error(s) of N tests` với N > 0. Nếu module không load được, đọc log tìm tham chiếu `state` còn sót trong XML/Python.

- [ ] **Step 8: Commit backend**

```bash
git add custom-addons/hocba_employees && git commit -m "feat(asset): rut gon F-006 - bo trang thai thu hoi/ban giao, chi con danh sach ai giu gi"
```

---

### Task 4: Controller API

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py:2140, 2273-2282, 2713-2788, 2826`

- [ ] **Step 1: Đổi nhãn selection dùng cho SPA**

Dòng 2140 — thay:

```python
            'asset_state': sel(env['hr.employee.asset'], 'state'),
```

bằng:

```python
            'asset_condition': sel(env['hr.employee.asset'], 'condition_in'),
```

- [ ] **Step 2: Rút gọn payload chi tiết nhân viên**

Dòng 2273–2282 — thay:

```python
        # --- Tài sản (F-006) ---
        data['assets'] = [{
            'id': a.id,
            'type': a.asset_type_id.name or '',
            'code': a.asset_code or '',
            'grant': _d(a.grant_date),
            'conditionLabel': labels['asset_condition'].get(
                a.condition_in, a.condition_in or ''),
        } for a in e.x_asset_ids.sorted('grant_date')]
```

- [ ] **Step 3: Bỏ 2 route vòng đời, thêm route xoá dòng**

Xoá **toàn bộ** 2 method `api_asset_return` (dòng 2743–2763) và `api_asset_transfer` (dòng 2765–2788), thêm vào chỗ đó:

```python
    @http.route('/hocba-hrm/api/asset/<int:asset_id>/delete', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_asset_delete(self, asset_id, **kw):
        """Gỡ tài sản khỏi hồ sơ (thu hồi/bàn giao = sửa danh sách)."""
        a = request.env['hr.employee.asset'].sudo().browse(asset_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        e = a.employee_id
        if not self._can_edit_emp_record(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            a.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self._detail_response(e)
```

Sửa comment khối ở dòng 2713–2715 thành:

```python
    # KHÔNG có vòng đời: thu hồi = xoá dòng, bàn giao = xoá + cấp lại.
```

- [ ] **Step 4: Payload danh sách nghỉ việc**

Dòng 2826 — thay:

```python
            'assetCount': rec.asset_count,
            'assetCodes': rec.asset_codes or '',
```

- [ ] **Step 5: Khởi động lại Odoo và kiểm tra API**

Sửa controller Python thì **bắt buộc restart** container Odoo (không hot-reload):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml restart odoo
```

Sau đó mở preview (`.claude/launch.json`, proxy 8169) → `/hocba-hrm`, đăng nhập `test_hrmanager@hocba.vn` / `Hocba@2026`, mở một hồ sơ NV → tab Tài sản. Kỳ vọng: không lỗi 500 trong `preview_logs`, payload `assets[]` không còn khoá `state`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py && git commit -m "feat(asset-api): bo route thu hoi/chuyen giao, them route go tai san"
```

---

### Task 5: SPA

**Files:**
- Modify: `frontend/src/api/employees.js:35-40`
- Modify: `frontend/src/features/employees/AssetForm.jsx` (thay toàn bộ)
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx:231-279`
- Modify: `frontend/src/features/offboarding/Offboarding.jsx:106-141`

- [ ] **Step 1: API helper**

Thay dòng 37–40 của `frontend/src/api/employees.js`:

```js
export const deleteAsset = (assetId) =>
  hbPost(`/hocba-hrm/api/asset/${assetId}/delete`, {});
```

- [ ] **Step 2: Thay toàn bộ `AssetForm.jsx` bằng form cấp phát duy nhất**

```jsx
/* ============================================================
   Form Cấp phát tài sản (F-006 rút gọn) — inline trong tab Tài sản,
   chỉ HR. Không còn thu hồi/chuyển giao: gỡ tài sản = xoá dòng.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchFormMeta, createAsset } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

const TODAY = new Date().toISOString().slice(0, 10);

export default function AssetForm({ empId, onClose, onSaved }) {
  const [meta, setMeta] = useState(null);
  const [f, setF] = useState({
    assetTypeId: '', assetCode: '', grantDate: TODAY, conditionIn: 'good',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then(setMeta).catch(() => {}); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    setErr(null);
    if (!f.assetTypeId) { setErr('Vui lòng chọn loại tài sản.'); return; }
    if (!f.assetCode.trim()) { setErr('Vui lòng nhập mã tài sản.'); return; }
    try {
      setBusy(true);
      onSaved(await createAsset(empId, f));
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="plus" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Cấp phát tài sản</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Ghi nhận thiết bị nhân viên đang giữ</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Loại tài sản *">
            <select style={inp} value={f.assetTypeId} onChange={set('assetTypeId')}>
              <option value="">— Chọn —</option>
              {(meta?.assetTypes || []).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select></Field>
          <Field label="Mã tài sản *">
            <input style={inp} value={f.assetCode} onChange={set('assetCode')} placeholder="VD: LAP-007" /></Field>
          <Field label="Ngày cấp phát">
            <input type="date" style={inp} value={f.grantDate} onChange={set('grantDate')} /></Field>
          <Field label="Tình trạng khi cấp">
            <select style={inp} value={f.conditionIn} onChange={set('conditionIn')}>
              {(meta?.assetCondition || []).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !meta}>
          <Icon name="checkCircle" size={16} />
          {busy ? 'Đang lưu…' : 'Cấp phát'}
        </button>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 3: Thay `AssetsTab` trong `EmployeeDrawer.jsx` (dòng 231–279)**

```jsx
export function AssetsTab({ det, editable, onUpdated }) {
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(0);
  const canAct = editable && onUpdated;

  const remove = async (a) => {
    if (!window.confirm(`Gỡ tài sản ${a.code} khỏi hồ sơ ${det.name}?`)) return;
    setBusy(a.id);
    try { onUpdated(await deleteAsset(a.id)); } finally { setBusy(0); }
  };

  return (
    <div>
      {canAct && (
        <div className="between" style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>Tài sản đang giữ ({det.assets.length})</div>
          <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
            <Icon name="plus" size={13} />Cấp phát</button>
        </div>
      )}
      {!det.assets.length ? (
        <EmptyState>Chưa có tài sản cấp phát.</EmptyState>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead><tr><th>Mã tài sản</th><th>Loại</th><th>Ngày cấp</th><th>Tình trạng</th>{canAct && <th></th>}</tr></thead>
            <tbody>{det.assets.map((a) => (
              <tr key={a.id} style={{ cursor: 'default' }}>
                <td className="mono" style={{ fontWeight: 600 }}>{a.code}</td>
                <td>{a.type}</td>
                <td className="mono">{fmtDate(a.grant)}</td>
                <td>{a.conditionLabel || '—'}</td>
                {canAct && (
                  <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                    <button className="btn btn-ghost btn-sm" title="Gỡ khỏi hồ sơ"
                      disabled={busy === a.id} onClick={() => remove(a)}>Gỡ</button>
                  </td>
                )}
              </tr>))}</tbody>
          </table>
        </div>
      )}
      {adding && (
        <AssetForm empId={det.id}
          onClose={() => setAdding(false)}
          onSaved={(d) => { setAdding(false); onUpdated(d); }} />
      )}
    </div>
  );
}
```

Sửa dòng import số 4 của `EmployeeDrawer.jsx` (thêm `deleteAsset`):

```jsx
import { fetchEmployee, deleteDependent, verifyCert, deleteCert, fetchAccounts, fetchEvaluations, deleteAsset } from '../../api/employees';
```

- [ ] **Step 4: `Offboarding.jsx` — cảnh báo thay vì chặn**

Trong `ManagedRow` (dòng 106–141): xoá dòng `const doneBlocked = ...`, và thay 2 chỗ:

```jsx
      <td className="tbl-num mono" style={{ fontWeight: 600 }}>
        {r.assetCount > 0
          ? <span title={`Đang giữ: ${r.assetCodes}`}><Badge kind="amber">{r.assetCount} đang giữ</Badge></span>
          : '0'}
      </td>
```

(`Badge` chỉ nhận `kind`/`dot`/`children` — xem `frontend/src/components/Badge.jsx` — nên tooltip phải bọc ngoài bằng `<span title>`.)

```jsx
          {r.canDone && (
            <button className="btn btn-primary btn-sm" disabled={b}
              onClick={() => act(r, 'done',
                'Hoàn tất nghỉ việc? Hồ sơ sẽ lưu trữ và khoá tài khoản đăng nhập.')}>
              Hoàn tất</button>
          )}
```

- [ ] **Step 5: Build SPA**

```bash
cd frontend && npm run build
```

Kỳ vọng: build thành công, không còn tham chiếu `returnAsset`/`transferAsset` (Vite sẽ báo lỗi import nếu còn).

- [ ] **Step 6: Commit**

```bash
git add frontend custom-addons/hocba_hrm/static/spa && git commit -m "feat(asset-ui): tab Tai san con cap phat + go; man Nghi viec chi canh bao"
```

---

### Task 6: Kiểm chứng thực tế + tài liệu

**Files:**
- Modify: `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md` (mục F-006, BR-050, BR-052)
- Modify: `docs/DB_TEST_DATA.md` (nhật ký)

- [ ] **Step 1: Chạy lại toàn bộ test backend**

Chạy lệnh test ở đầu plan. Kỳ vọng: `0 failed, 0 error(s) of N tests`, N > 0.

- [ ] **Step 2: Kiểm chứng trên preview**

Mở `/hocba-hrm` (proxy 8169), tài khoản `test_hrmanager@hocba.vn` / `Hocba@2026`, kiểm 3 luồng:
1. Hồ sơ NV → tab Tài sản → Cấp phát một tài sản mới → thấy dòng mới, không có cột Trạng thái.
2. Bấm **Gỡ** → xác nhận → dòng biến mất.
3. Màn Nghỉ việc: một đơn `hr_approved` của NV còn tài sản → nút **Hoàn tất** bấm được, badge hiện "N đang giữ".

Kiểm `read_console_messages` và `preview_logs` không có lỗi.

- [ ] **Step 3: Cập nhật đặc tả**

Trong `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md`: viết lại mục F-006 theo mô hình danh sách phẳng, gỡ BR-050 (chuyển giao tự sinh bản ghi), sửa BR-052 (đếm toàn bộ dòng), và ghi chú "rút gọn theo góp ý giảng viên 2026-07-24, xem `docs/superpowers/specs/2026-07-24-asset-simplify-design.md`".

- [ ] **Step 4: Upgrade Neon + ghi nhật ký DB**

Upgrade `hocba_employees` lên Neon bằng **endpoint trực tiếp** (bỏ `-pooler` trong host — pooler rớt SSL giữa DDL dài). Sau đó thêm dòng nhật ký vào `docs/DB_TEST_DATA.md`: ngày, module + version `19.0.2.0.0 → 19.0.3.0.0`, số dòng tài sản lịch sử đã xoá (lấy từ log migration).

- [ ] **Step 5: Commit**

```bash
git add docs && git commit -m "docs: cap nhat F-006 rut gon + nhat ky DB"
```

---

## Ghi chú rủi ro

- Dữ liệu lịch sử tài sản **mất vĩnh viễn** sau migration — chỉ chạy trên DB đồ án.
- `static/spa/` là artifact được commit → khi merge xung đột thì **build lại**, không merge tay bundle.
- Nếu Neon còn `asset_code` trùng ngoài dự kiến, migration đã tự khử trùng và ghi `WARNING` — đọc log để biết đã xoá dòng nào.
