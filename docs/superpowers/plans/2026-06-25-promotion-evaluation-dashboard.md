# Dashboard Đánh giá Thăng tiến — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm dashboard đánh giá thăng tiến theo từng NV: chấm tiêu chí có trọng số → tổng điểm % + gợi ý verdict, kèm chỉ số tự động & biểu đồ, nối vào luồng tạo thăng tiến hiện có.

**Architecture:** 3 model mới trong `hocba_employees` (`hr.promotion.criteria`, `hr.promotion.evaluation`, `hr.promotion.evaluation.line`) + ngưỡng `ir.config_parameter`. 2 endpoint mới trong `hocba_hrm` (GET dữ liệu eval, POST lưu eval) tái dùng helper quyền sẵn có. SPA nâng cấp tab "Thăng tiến" thành dashboard (recharts, theme đỏ/sáng). Backend (model + security + test) làm trước, UI sau.

**Tech Stack:** Odoo 19 (Python), Postgres, React 18 + Vite 6, recharts ^2.x.

**Spec:** `docs/superpowers/specs/2026-06-25-promotion-evaluation-dashboard-design.md`

**Lệnh test backend (Docker local — BẮT BUỘC `MSYS_NO_PATHCONV=1`):**
```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```
Cần thấy: `0 failed, 0 error(s) of N tests` với N > 0.

---

## File Structure

**Backend (`custom-addons/hocba_employees/`):**
- Create `models/hr_promotion_criteria.py` — model tiêu chí (config).
- Create `models/hr_promotion_evaluation.py` — model đợt đánh giá + dòng chấm (2 class cùng file vì cùng trách nhiệm).
- Modify `models/__init__.py` — import 2 file mới.
- Create `data/hr_promotion_criteria_data.xml` — seed 4 tiêu chí mặc định + 2 ngưỡng config_parameter.
- Modify `security/ir.model.access.csv` — ACL cho 3 model.
- Modify `__manifest__.py` — thêm data file mới.
- Modify `models/hr_employee.py` — thêm O2m `x_evaluation_ids` + helper `_promo_auto_metrics()`.
- Create `tests/test_promotion_evaluation.py` — test model + quyền.
- Modify `tests/__init__.py` — import test mới.

**API (`custom-addons/hocba_hrm/controllers/main.py`):**
- Modify — thêm `EVAL_*` constant, 2 endpoint, mở rộng `api_promotion_create` nhận `evaluationId`.

**Frontend (`frontend/`):**
- Modify `package.json` — thêm `recharts`.
- Modify `src/api/employees.js` — thêm `fetchEvaluations`, `saveEvaluation`.
- Create `src/features/employees/EvaluationForm.jsx` — form chấm tiêu chí.
- Create `src/features/employees/PromoCharts.jsx` — line + radar (recharts).
- Modify `src/features/employees/EmployeeDrawer.jsx` — `PromoTab` thành dashboard.

---

## Task 1: Model `hr.promotion.criteria` + ACL + seed

**Files:**
- Create: `custom-addons/hocba_employees/models/hr_promotion_criteria.py`
- Modify: `custom-addons/hocba_employees/models/__init__.py`
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv`
- Create: `custom-addons/hocba_employees/data/hr_promotion_criteria_data.xml`
- Modify: `custom-addons/hocba_employees/__manifest__.py`
- Create: `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`
- Modify: `custom-addons/hocba_employees/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`:
```python
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPromotionCriteria(TransactionCase):
    def test_seed_criteria_exist_with_weight(self):
        crits = self.env['hr.promotion.criteria'].search([('active', '=', True)])
        self.assertTrue(len(crits) >= 4, 'Phải seed >= 4 tiêu chí mặc định')
        self.assertTrue(all(c.weight > 0 for c in crits), 'Mọi tiêu chí có trọng số > 0')
        self.assertTrue(all(c.max_score > 0 for c in crits))
```

Create `custom-addons/hocba_employees/tests/__init__.py` (nếu chưa import) — đảm bảo có:
```python
from . import test_face_enroll
from . import test_promotion_evaluation
```

- [ ] **Step 2: Run test to verify it fails**

Run lệnh test backend ở đầu plan (test-tags `/hocba_employees`).
Expected: FAIL — `KeyError`/`Model 'hr.promotion.criteria' not found` (model chưa tồn tại).

- [ ] **Step 3: Create the model**

Create `custom-addons/hocba_employees/models/hr_promotion_criteria.py`:
```python
from odoo import models, fields


class HrPromotionCriteria(models.Model):
    _name = 'hr.promotion.criteria'
    _description = 'Tiêu chí đánh giá thăng tiến (cấu hình)'
    _order = 'sequence, id'

    name = fields.Char(string='Tiêu chí', required=True, translate=True)
    code = fields.Char(string='Mã', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    weight = fields.Float(string='Trọng số', required=True, default=1.0)
    max_score = fields.Integer(string='Điểm tối đa', default=5)
    guideline = fields.Text(string='Hướng dẫn chấm')
    active = fields.Boolean(string='Hiệu lực', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã tiêu chí phải duy nhất.'),
    ]
```

- [ ] **Step 4: Register the model**

In `custom-addons/hocba_employees/models/__init__.py`, add (giữ thứ tự theo file hiện có):
```python
from . import hr_promotion_criteria
```

- [ ] **Step 5: Add ACL rows**

In `custom-addons/hocba_employees/security/ir.model.access.csv`, append:
```csv
access_hr_promotion_criteria_user,access.hr.promotion.criteria.user,model_hr_promotion_criteria,hr.group_hr_user,1,0,0,0
access_hr_promotion_criteria_manager,access.hr.promotion.criteria.manager,model_hr_promotion_criteria,hr.group_hr_manager,1,1,1,1
access_hr_promotion_criteria_giaovu,access.hr.promotion.criteria.giaovu,model_hr_promotion_criteria,hocba_employees.group_hocba_giaovu,1,0,0,0
```

- [ ] **Step 6: Seed criteria + thresholds**

Create `custom-addons/hocba_employees/data/hr_promotion_criteria_data.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
  <record id="crit_competency" model="hr.promotion.criteria">
    <field name="name">Năng lực chuyên môn / KPI</field>
    <field name="code">competency</field>
    <field name="sequence">10</field>
    <field name="weight">35</field>
    <field name="max_score">5</field>
    <field name="guideline">Mức độ hoàn thành công việc, chất lượng chuyên môn, KPI.</field>
  </record>
  <record id="crit_attitude" model="hr.promotion.criteria">
    <field name="name">Thái độ &amp; kỷ luật</field>
    <field name="code">attitude</field>
    <field name="sequence">20</field>
    <field name="weight">25</field>
    <field name="max_score">5</field>
  </record>
  <record id="crit_teamwork" model="hr.promotion.criteria">
    <field name="name">Phối hợp &amp; teamwork</field>
    <field name="code">teamwork</field>
    <field name="sequence">30</field>
    <field name="weight">20</field>
    <field name="max_score">5</field>
  </record>
  <record id="crit_potential" model="hr.promotion.criteria">
    <field name="name">Tiềm năng phát triển</field>
    <field name="code">potential</field>
    <field name="sequence">40</field>
    <field name="weight">20</field>
    <field name="max_score">5</field>
  </record>

  <record id="ir_config_promo_qualified" model="ir.config_parameter">
    <field name="key">hocba_employees.promo_eval_qualified</field>
    <field name="value">80</field>
  </record>
  <record id="ir_config_promo_consider" model="ir.config_parameter">
    <field name="key">hocba_employees.promo_eval_consider</field>
    <field name="value">60</field>
  </record>
</odoo>
```

In `custom-addons/hocba_employees/__manifest__.py`, add to `data` list **sau** `security/ir.model.access.csv` và trước `views/...`:
```python
        'data/hr_promotion_criteria_data.xml',
```

- [ ] **Step 7: Run test to verify it passes**

Run lệnh test backend (`-u hocba_employees`). Expected: PASS `test_seed_criteria_exist_with_weight`.

- [ ] **Step 8: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_promotion_criteria.py \
        custom-addons/hocba_employees/models/__init__.py \
        custom-addons/hocba_employees/security/ir.model.access.csv \
        custom-addons/hocba_employees/data/hr_promotion_criteria_data.xml \
        custom-addons/hocba_employees/__manifest__.py \
        custom-addons/hocba_employees/tests/test_promotion_evaluation.py \
        custom-addons/hocba_employees/tests/__init__.py
git commit -m "feat(hrm): model+seed tiêu chí đánh giá thăng tiến (hr.promotion.criteria)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Model `hr.promotion.evaluation` + line + tính điểm/verdict

**Files:**
- Create: `custom-addons/hocba_employees/models/hr_promotion_evaluation.py`
- Modify: `custom-addons/hocba_employees/models/__init__.py`
- Modify: `custom-addons/hocba_employees/security/ir.model.access.csv`
- Test: `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`

- [ ] **Step 1: Write the failing test**

Append vào `test_promotion_evaluation.py`:
```python
@tagged('post_install', '-at_install')
class TestPromotionEvaluation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Eval Target',
            'identification_id': '012345678901',
        })
        Crit = self.env['hr.promotion.criteria']
        self.c1 = Crit.create({'name': 'C1', 'code': 'c1', 'weight': 60, 'max_score': 5})
        self.c2 = Crit.create({'name': 'C2', 'code': 'c2', 'weight': 40, 'max_score': 5})

    def _make_eval(self, s1, s2):
        return self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id,
            'line_ids': [
                (0, 0, {'criteria_id': self.c1.id, 'score': s1}),
                (0, 0, {'criteria_id': self.c2.id, 'score': s2}),
            ],
        })

    def test_total_score_weighted_percent(self):
        ev = self._make_eval(5, 5)            # full → 100%
        self.assertAlmostEqual(ev.total_score, 100.0, places=1)
        ev2 = self._make_eval(4, 2)           # (4/5*60 + 2/5*40)/100*100 = 64
        self.assertAlmostEqual(ev2.total_score, 64.0, places=1)

    def test_line_copies_weight_and_max(self):
        ev = self._make_eval(3, 3)
        line1 = ev.line_ids.filtered(lambda l: l.criteria_id == self.c1)
        self.assertEqual(line1.weight, 60)
        self.assertEqual(line1.max_score, 5)

    def test_verdict_auto_thresholds(self):
        self.assertEqual(self._make_eval(5, 5).verdict_auto, 'qualified')   # 100
        self.assertEqual(self._make_eval(4, 2).verdict_auto, 'consider')    # 64
        self.assertEqual(self._make_eval(2, 2).verdict_auto, 'not_yet')     # 40
```

- [ ] **Step 2: Run test to verify it fails**

Run test backend. Expected: FAIL — `hr.promotion.evaluation` not found.

- [ ] **Step 3: Create the models**

Create `custom-addons/hocba_employees/models/hr_promotion_evaluation.py`:
```python
from odoo import models, fields, api, _


class HrPromotionEvaluation(models.Model):
    _name = 'hr.promotion.evaluation'
    _description = 'Đợt đánh giá thăng tiến'
    _order = 'eval_date desc, id desc'

    VERDICT_SEL = [
        ('qualified', 'Đủ điều kiện'),
        ('consider', 'Cân nhắc'),
        ('not_yet', 'Chưa đủ'),
    ]

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='restrict', index=True)
    eval_date = fields.Date(
        string='Ngày đánh giá', required=True,
        default=fields.Date.context_today)
    evaluator_id = fields.Many2one(
        'res.users', string='Người đánh giá',
        default=lambda self: self.env.user)
    state = fields.Selection(
        [('draft', 'Nháp'), ('confirmed', 'Đã xác nhận')],
        string='Trạng thái', default='draft', required=True)
    line_ids = fields.One2many(
        'hr.promotion.evaluation.line', 'evaluation_id', string='Dòng chấm')
    total_score = fields.Float(
        string='Tổng điểm (%)', compute='_compute_total_score', store=True)
    verdict_auto = fields.Selection(
        VERDICT_SEL, string='Gợi ý', compute='_compute_total_score', store=True)
    verdict_final = fields.Selection(VERDICT_SEL, string='Kết luận')
    conclusion_note = fields.Text(string='Nhận xét / Kết luận')
    promotion_id = fields.Many2one(
        'hr.promotion.history', string='Bản ghi thăng tiến')
    snapshot_tenure_months = fields.Float(string='Thâm niên (tháng)')
    snapshot_months_since_promo = fields.Float(string='Tháng từ thăng tiến')
    snapshot_job_id = fields.Many2one('hr.job', string='Chức vụ tại thời điểm')

    @api.depends('line_ids.score', 'line_ids.weight', 'line_ids.max_score')
    def _compute_total_score(self):
        ICP = self.env['ir.config_parameter'].sudo()
        q = float(ICP.get_param('hocba_employees.promo_eval_qualified', 80))
        c = float(ICP.get_param('hocba_employees.promo_eval_consider', 60))
        for rec in self:
            wsum = sum(l.weight for l in rec.line_ids)
            if wsum:
                acc = sum((l.score / l.max_score) * l.weight
                          for l in rec.line_ids if l.max_score)
                rec.total_score = acc / wsum * 100
            else:
                rec.total_score = 0.0
            if rec.total_score >= q:
                rec.verdict_auto = 'qualified'
            elif rec.total_score >= c:
                rec.verdict_auto = 'consider'
            else:
                rec.verdict_auto = 'not_yet'


class HrPromotionEvaluationLine(models.Model):
    _name = 'hr.promotion.evaluation.line'
    _description = 'Dòng chấm tiêu chí'
    _order = 'sequence, id'

    evaluation_id = fields.Many2one(
        'hr.promotion.evaluation', required=True, ondelete='cascade', index=True)
    criteria_id = fields.Many2one(
        'hr.promotion.criteria', string='Tiêu chí', required=True)
    sequence = fields.Integer(related='criteria_id.sequence', store=True)
    score = fields.Float(string='Điểm', default=0.0)
    weight = fields.Float(string='Trọng số')
    max_score = fields.Integer(string='Điểm tối đa')
    note = fields.Text(string='Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            crit = self.env['hr.promotion.criteria'].browse(
                vals.get('criteria_id'))
            if crit and not vals.get('weight'):
                vals['weight'] = crit.weight
            if crit and not vals.get('max_score'):
                vals['max_score'] = crit.max_score
        return super().create(vals_list)
```

- [ ] **Step 4: Register models + ACL**

In `models/__init__.py` add:
```python
from . import hr_promotion_evaluation
```

In `security/ir.model.access.csv` append:
```csv
access_hr_promotion_evaluation_user,access.hr.promotion.evaluation.user,model_hr_promotion_evaluation,hr.group_hr_user,1,1,1,0
access_hr_promotion_evaluation_manager,access.hr.promotion.evaluation.manager,model_hr_promotion_evaluation,hr.group_hr_manager,1,1,1,1
access_hr_promotion_evaluation_giaovu,access.hr.promotion.evaluation.giaovu,model_hr_promotion_evaluation,hocba_employees.group_hocba_giaovu,1,1,1,0
access_hr_promotion_evaluation_line_user,access.hr.promotion.evaluation.line.user,model_hr_promotion_evaluation_line,hr.group_hr_user,1,1,1,1
access_hr_promotion_evaluation_line_manager,access.hr.promotion.evaluation.line.manager,model_hr_promotion_evaluation_line,hr.group_hr_manager,1,1,1,1
access_hr_promotion_evaluation_line_giaovu,access.hr.promotion.evaluation.line.giaovu,model_hr_promotion_evaluation_line,hocba_employees.group_hocba_giaovu,1,1,1,1
```

- [ ] **Step 5: Run test to verify it passes**

Run test backend. Expected: PASS `test_total_score_weighted_percent`, `test_line_copies_weight_and_max`, `test_verdict_auto_thresholds`.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_promotion_evaluation.py \
        custom-addons/hocba_employees/models/__init__.py \
        custom-addons/hocba_employees/security/ir.model.access.csv \
        custom-addons/hocba_employees/tests/test_promotion_evaluation.py
git commit -m "feat(hrm): model đợt đánh giá + tính điểm trọng số & verdict

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Ràng buộc điểm + confirm + audit (no-unlink / 24h)

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_promotion_evaluation.py`
- Test: `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`

- [ ] **Step 1: Write the failing test**

Append vào class `TestPromotionEvaluation`:
```python
    def test_score_out_of_range_raises(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['hr.promotion.evaluation'].create({
                'employee_id': self.emp.id,
                'line_ids': [(0, 0, {'criteria_id': self.c1.id, 'score': 9})],
            })

    def test_confirm_requires_verdict_final(self):
        from odoo.exceptions import UserError
        ev = self._make_eval(4, 4)
        with self.assertRaises(UserError):
            ev.action_confirm()
        ev.verdict_final = 'qualified'
        ev.action_confirm()
        self.assertEqual(ev.state, 'confirmed')

    def test_confirmed_cannot_be_deleted(self):
        from odoo.exceptions import UserError
        ev = self._make_eval(4, 4)
        ev.verdict_final = 'qualified'
        ev.action_confirm()
        with self.assertRaises(UserError):
            ev.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run test backend. Expected: FAIL — không raise (chưa có constrain/confirm/unlink).

- [ ] **Step 3: Add constraints + confirm + unlink guard**

In `hr_promotion_evaluation.py`, thêm import ở đầu:
```python
from datetime import timedelta
from odoo.exceptions import UserError, AccessError, ValidationError
```
Thêm vào class `HrPromotionEvaluation` (sau `_compute_total_score`):
```python
    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Cần chấm ít nhất một tiêu chí trước khi xác nhận.'))
            if not rec.verdict_final:
                raise UserError(_('Cần chọn Kết luận (verdict) trước khi xác nhận.'))
            rec.state = 'confirmed'
            rec.employee_id.message_post(body=_(
                '📋 Đợt đánh giá thăng tiến %(d)s: %(score).0f%% — %(v)s.') % {
                    'd': rec.eval_date,
                    'score': rec.total_score,
                    'v': dict(rec.VERDICT_SEL).get(rec.verdict_final, ''),
                })
        return True

    def write(self, vals):
        # Sau 24h chỉ HR Manager được sửa (giống hr.promotion.history)
        if not self.env.su and not self.env.user.has_group('hr.group_hr_manager'):
            cutoff = fields.Datetime.now() - timedelta(hours=24)
            for rec in self:
                if rec.create_date and rec.create_date < cutoff:
                    raise AccessError(_(
                        'Đợt đánh giá quá 24h — chỉ HR Manager được sửa.'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_(
                    'Không được xóa đợt đánh giá đã xác nhận (audit trail).'))
        return super().unlink()
```
Thêm vào class `HrPromotionEvaluationLine`:
```python
    @api.constrains('score', 'max_score')
    def _check_score_range(self):
        for line in self:
            if line.score < 0 or (line.max_score and line.score > line.max_score):
                raise ValidationError(_(
                    'Điểm phải trong khoảng 0..%s.') % line.max_score)
```
Thêm import `api` vào line class (đã import ở đầu file).

- [ ] **Step 4: Run test to verify it passes**

Run test backend. Expected: PASS 3 test mới.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_promotion_evaluation.py \
        custom-addons/hocba_employees/tests/test_promotion_evaluation.py
git commit -m "feat(hrm): ràng buộc điểm + confirm verdict + audit đợt đánh giá

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Chỉ số tự động + O2m trên hr.employee

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py`
- Test: `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`

- [ ] **Step 1: Write the failing test**

Append vào class `TestPromotionEvaluation`:
```python
    def test_auto_metrics_keys_and_attendance_guard(self):
        # Tạo 1 mốc thăng tiến để có "tháng từ thăng tiến gần nhất"
        self.env['hr.promotion.history'].create({
            'employee_id': self.emp.id,
            'x_change_type': 'join',
            'date_effective': fields.Date.today(),
        })
        m = self.emp._promo_auto_metrics()
        for key in ('tenureMonths', 'monthsSincePromo', 'currentJob',
                    'attendance'):
            self.assertIn(key, m)
        # Không có module chấm công/khoá → attendance là None hoặc dict, không lỗi
        self.assertTrue(m['attendance'] is None or isinstance(m['attendance'], dict))
```
Thêm import ở đầu file test (nếu chưa có): `from odoo import fields`.

- [ ] **Step 2: Run test to verify it fails**

Run test backend. Expected: FAIL — `_promo_auto_metrics` không tồn tại.

- [ ] **Step 3: Add O2m + helper**

In `custom-addons/hocba_employees/models/hr_employee.py`, thêm field (gần các O2m khác như `x_promotion_ids`):
```python
    x_evaluation_ids = fields.One2many(
        'hr.promotion.evaluation', 'employee_id', string='Đợt đánh giá thăng tiến')
```
Thêm method (trong class hr.employee):
```python
    def _promo_auto_metrics(self):
        """Chỉ số tự động cho dashboard đánh giá thăng tiến (read-only).
        Chấm công lấy best-effort: thiếu model/khoá → trả None, không vỡ."""
        self.ensure_one()
        today = fields.Date.today()

        def _months(d):
            if not d:
                return 0.0
            return round((today - d).days / 30.44, 1)

        last_promo = self.env['hr.promotion.history'].search(
            [('employee_id', '=', self.id)], order='date_effective desc', limit=1)
        metrics = {
            'tenureMonths': _months(self.x_probation_start)
            or _months(self.create_date and self.create_date.date()),
            'officialMonths': round(self.x_official_months or 0, 1),
            'monthsSincePromo': _months(last_promo.date_effective)
            if last_promo else None,
            'currentJob': self.job_id.name or '',
            'attendance': self._promo_attendance_summary(),
        }
        return metrics

    def _promo_attendance_summary(self):
        """Tổng hợp chấm công ~3 tháng. Best-effort: module owner khác."""
        self.ensure_one()
        Att = self.env.get('hr.attendance')
        if Att is None or 'hr.attendance' not in self.env:
            return None
        try:
            since = fields.Datetime.now() - timedelta(days=90)
            recs = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', self.id),
                ('check_in', '>=', since),
            ])
            return {'days': len(recs)}
        except Exception:
            return None
```
Đảm bảo đầu `hr_employee.py` có `from datetime import timedelta` (thêm nếu thiếu).

- [ ] **Step 4: Run test to verify it passes**

Run test backend. Expected: PASS `test_auto_metrics_keys_and_attendance_guard`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py \
        custom-addons/hocba_employees/tests/test_promotion_evaluation.py
git commit -m "feat(hrm): chỉ số tự động + O2m đợt đánh giá trên hr.employee

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Quyền — user thường không tạo được đợt đánh giá

**Files:**
- Test: `custom-addons/hocba_employees/tests/test_promotion_evaluation.py`

- [ ] **Step 1: Write the failing test**

Append class mới:
```python
@tagged('post_install', '-at_install')
class TestPromotionEvalAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Acc Target', 'identification_id': '019999999901'})
        self.crit = self.env['hr.promotion.criteria'].create(
            {'name': 'X', 'code': 'accx', 'weight': 100, 'max_score': 5})
        self.regular = self.env['res.users'].create({
            'name': 'Reg', 'login': 'reg_eval_acc',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

    def test_regular_user_cannot_create_evaluation(self):
        from odoo.exceptions import AccessError
        Ev = self.env['hr.promotion.evaluation'].with_user(self.regular)
        with self.assertRaises(AccessError):
            Ev.create({
                'employee_id': self.emp.id,
                'line_ids': [(0, 0, {'criteria_id': self.crit.id, 'score': 3})]})
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run test backend. Expected: PASS ngay (ACL Task 2 chỉ cấp cho nhóm HR/giáo vụ → user `base.group_user` thuần không có quyền create → `AccessError`). Nếu FAIL (không raise), kiểm tra lại ACL ở Task 2 — không được có dòng cấp create cho `base.group_user`.

- [ ] **Step 3: (nếu cần) Sửa ACL**

Không có thay đổi nếu Step 2 PASS. Đây là test bảo vệ chống regression.

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_employees/tests/test_promotion_evaluation.py
git commit -m "test(hrm): user thường không tạo được đợt đánh giá (ACL guard)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: API GET dữ liệu đánh giá

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

- [ ] **Step 1: Add endpoint**

Thêm method vào class controller (gần `api_promotion_create`, ~ line 2148):
```python
    @http.route('/hocba-hrm/api/promotion/eval/<int:emp_id>', auth='user',
                type='http', methods=['GET'], csrf=False)
    def api_eval_get(self, emp_id, **kw):
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_eval_emp(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        crits = request.env['hr.promotion.criteria'].sudo().search(
            [('active', '=', True)])
        criteria = [{'id': c.id, 'name': c.name, 'code': c.code,
                     'weight': c.weight, 'maxScore': c.max_score,
                     'guideline': c.guideline or ''} for c in crits]
        evals = []
        for ev in e.sudo().x_evaluation_ids.sorted('eval_date'):
            evals.append({
                'id': ev.id,
                'date': _d(ev.eval_date),
                'evaluator': ev.evaluator_id.name or '',
                'state': ev.state,
                'totalScore': round(ev.total_score, 1),
                'verdictAuto': ev.verdict_auto or '',
                'verdictFinal': ev.verdict_final or '',
                'note': ev.conclusion_note or '',
                'lines': [{'criteriaId': l.criteria_id.id,
                           'name': l.criteria_id.name,
                           'score': l.score, 'maxScore': l.max_score,
                           'weight': l.weight, 'note': l.note or ''}
                          for l in ev.line_ids],
            })
        return request.make_json_response({
            'criteria': criteria,
            'autoMetrics': e.sudo()._promo_auto_metrics(),
            'evaluations': evals,
        })
```
(Helper `_d` đã có ở module này; `_can_eval_emp` = HR Manager / quản lý trực tiếp / trưởng phòng ban — đúng yêu cầu phân quyền.)

- [ ] **Step 2: Verify (manual — không có HttpCase tự động)**

Restart Odoo (sửa controller Python cần restart). Đăng nhập `test_hrmanager@hocba.vn` (`Hocba@2026`), gọi:
`GET /hocba-hrm/api/promotion/eval/<id NV demo>` → JSON có `criteria` (4 mục), `autoMetrics`, `evaluations: []`.
Với tài khoản `test_employee@hocba.vn` xem NV khác → HTTP 403.

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(api): GET dữ liệu đánh giá thăng tiến theo NV

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: API POST lưu đợt đánh giá + nối evidence vào promotion

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/main.py`

- [ ] **Step 1: Add save endpoint**

Thêm method:
```python
    @http.route('/hocba-hrm/api/promotion/eval/save', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_eval_save(self, **kw):
        payload = request.get_json_data()
        emp_id = self._conv_id(payload.get('employeeId'))
        e = request.env['hr.employee'].browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._can_eval_emp(e):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        lines = []
        for ln in payload.get('lines', []):
            cid = self._conv_id(ln.get('criteriaId'))
            if not cid:
                continue
            lines.append((0, 0, {
                'criteria_id': cid,
                'score': float(ln.get('score') or 0),
                'note': ln.get('note') or False,
            }))
        vals = {
            'employee_id': emp_id,
            'eval_date': payload.get('date') or fields.Date.context_today(
                request.env['hr.promotion.evaluation']),
            'verdict_final': payload.get('verdictFinal') or False,
            'conclusion_note': payload.get('note') or False,
            'line_ids': lines,
            'snapshot_job_id': e.job_id.id or False,
        }
        try:
            ev = request.env['hr.promotion.evaluation'].sudo().create(vals)
            if payload.get('confirm'):
                ev.action_confirm()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return self.api_eval_get(emp_id)
```
(Cần `from odoo import fields` ở controller — kiểm tra import; thêm nếu thiếu.)

- [ ] **Step 2: Nối evaluationId vào api_promotion_create**

Trong `api_promotion_create`, **sau** khi tạo `hr.promotion.history` (sau dòng `request.env['hr.promotion.history'].create(vals)`), gán lại biến và nối:
Đổi đoạn create thành:
```python
        try:
            promo = request.env['hr.promotion.history'].create(vals)
            ev_id = self._conv_id(payload.get('evaluationId'))
            if ev_id:
                ev = request.env['hr.promotion.evaluation'].sudo().browse(ev_id)
                if ev.exists() and ev.employee_id.id == emp_id:
                    ev.promotion_id = promo.id
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
```

- [ ] **Step 3: Verify (manual)**

Restart Odoo. Đăng nhập HR Manager, POST `/hocba-hrm/api/promotion/eval/save` body `{"employeeId":<id>,"lines":[{"criteriaId":<c>,"score":4}],"verdictFinal":"qualified","confirm":true}` → trả lại JSON eval có 1 đợt `state=confirmed`, `totalScore` đúng.

- [ ] **Step 4: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/main.py
git commit -m "feat(api): lưu đợt đánh giá + nối evidence vào thăng tiến

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: FE — thêm recharts + API client

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/api/employees.js`

- [ ] **Step 1: Add recharts dependency**

```bash
cd frontend && npm install recharts@^2.12.0
```
Xác nhận `frontend/package.json` `dependencies` có `"recharts": "^2.12.0"`.

- [ ] **Step 2: Add API client functions**

Mở `frontend/src/api/employees.js`, xem pattern hàm hiện có (vd `createPromotion`, `fetchFormMeta`) rồi thêm 2 hàm cùng kiểu fetch/parse JSON:
```javascript
export async function fetchEvaluations(empId) {
  const r = await fetch(`/hocba-hrm/api/promotion/eval/${empId}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!r.ok) throw new Error('Không tải được dữ liệu đánh giá.');
  return r.json();
}

export async function saveEvaluation(payload) {
  const r = await fetch('/hocba-hrm/api/promotion/eval/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.message || 'Lưu đánh giá thất bại.');
  return data;
}
```
> **Lưu ý:** Nếu các hàm khác trong file dùng helper riêng (vd `postJson`/`getJson`) thay vì `fetch` trần, hãy theo đúng helper đó cho nhất quán.

- [ ] **Step 3: Build SPA + smoke check**

```bash
cd frontend && npm run build
```
Expected: build thành công, output vào `custom-addons/hocba_hrm/static/spa/`.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/api/employees.js \
        custom-addons/hocba_hrm/static/spa/
git commit -m "feat(spa): thêm recharts + API client đánh giá thăng tiến

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: FE — form chấm tiêu chí (EvaluationForm)

**Files:**
- Create: `frontend/src/features/employees/EvaluationForm.jsx`

- [ ] **Step 1: Create the form component**

Tham khảo `PromotionForm.jsx` cho style modal/Field. Create `EvaluationForm.jsx`:
```jsx
/* Form chấm đợt đánh giá thăng tiến — chỉ người quản lý. Owner: Tân. */
import { useState, useMemo } from 'react';
import { saveEvaluation } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

const TODAY = new Date().toISOString().slice(0, 10);
const VERDICTS = [
  ['qualified', 'Đủ điều kiện'], ['consider', 'Cân nhắc'], ['not_yet', 'Chưa đủ'],
];

function autoVerdict(pct) {
  if (pct >= 80) return 'qualified';
  if (pct >= 60) return 'consider';
  return 'not_yet';
}

export default function EvaluationForm({ empId, criteria, onClose, onSaved }) {
  const [date, setDate] = useState(TODAY);
  const [scores, setScores] = useState(() =>
    Object.fromEntries(criteria.map((c) => [c.id, 0])));
  const [notes, setNotes] = useState({});
  const [verdictFinal, setVerdictFinal] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const pct = useMemo(() => {
    const wsum = criteria.reduce((s, c) => s + c.weight, 0);
    if (!wsum) return 0;
    const acc = criteria.reduce(
      (s, c) => s + (scores[c.id] / c.maxScore) * c.weight, 0);
    return Math.round((acc / wsum) * 1000) / 10;
  }, [scores, criteria]);

  const submit = async (confirm) => {
    setErr(null);
    if (confirm && !verdictFinal) { setErr('Chọn kết luận trước khi xác nhận.'); return; }
    setBusy(true);
    try {
      const data = await saveEvaluation({
        employeeId: empId, date, verdictFinal, note, confirm,
        lines: criteria.map((c) => ({
          criteriaId: c.id, score: scores[c.id], note: notes[c.id] || '' })),
      });
      onSaved(data);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head">
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Đợt đánh giá thăng tiến</h2>
          <div className="muted" style={{ fontSize: 12.5 }}>Chấm theo tiêu chí · gợi ý theo ngưỡng</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '18px 24px' }}>
        <label style={{ fontSize: 12, fontWeight: 700 }}>Ngày đánh giá&nbsp;
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <div style={{ marginTop: 14 }}>
          {criteria.map((c) => (
            <div key={c.id} style={{ marginBottom: 12 }}>
              <div className="between">
                <span style={{ fontWeight: 600, fontSize: 13 }}>{c.name} <span className="muted">· w{c.weight}</span></span>
                <span style={{ fontWeight: 700 }}>{scores[c.id]}/{c.maxScore}</span>
              </div>
              <input type="range" min="0" max={c.maxScore} step="1"
                value={scores[c.id]} style={{ width: '100%' }}
                onChange={(e) => setScores((p) => ({ ...p, [c.id]: Number(e.target.value) }))} />
            </div>
          ))}
        </div>
        <div className="between" style={{ marginTop: 8, padding: '10px 0', borderTop: '1px solid var(--border)' }}>
          <span style={{ fontWeight: 700 }}>Tổng điểm</span>
          <span style={{ fontWeight: 800, fontSize: 20, color: 'var(--red-700)' }}>{pct}% · {VERDICTS.find((v) => v[0] === autoVerdict(pct))[1]}</span>
        </div>
        <label style={{ display: 'block', marginTop: 10, fontSize: 12, fontWeight: 700 }}>Kết luận
          <select value={verdictFinal} onChange={(e) => setVerdictFinal(e.target.value)} style={{ width: '100%' }}>
            <option value="">— Chọn —</option>
            {VERDICTS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </label>
        <label style={{ display: 'block', marginTop: 10, fontSize: 12, fontWeight: 700 }}>Nhận xét
          <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} style={{ width: '100%' }} />
        </label>
        {err && <div style={{ marginTop: 12, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-soft" onClick={() => submit(false)} disabled={busy}>Lưu nháp</button>
        <button className="btn btn-primary" onClick={() => submit(true)} disabled={busy}>
          <Icon name="checkCircle" size={16} />Xác nhận</button>
      </div>
    </Modal>
  );
}
```
> Kiểm timport `Icon`, `Modal` đúng đường dẫn như `PromotionForm.jsx`.

- [ ] **Step 2: Build SPA**

```bash
cd frontend && npm run build
```
Expected: build thành công (chưa wire vào tab — chỉ kiểm compile).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/employees/EvaluationForm.jsx custom-addons/hocba_hrm/static/spa/
git commit -m "feat(spa): form chấm đợt đánh giá thăng tiến (EvaluationForm)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: FE — biểu đồ (PromoCharts) + dashboard PromoTab

**Files:**
- Create: `frontend/src/features/employees/PromoCharts.jsx`
- Modify: `frontend/src/features/employees/EmployeeDrawer.jsx`

- [ ] **Step 1: Create charts component**

Create `frontend/src/features/employees/PromoCharts.jsx`:
```jsx
/* Biểu đồ lộ trình (line) + radar tiêu chí — recharts. Owner: Tân. */
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';

export function SalaryJourneyChart({ promotions }) {
  const data = (promotions || []).map((p) => ({
    date: p.date, wage: p.toWage || 0, label: p.toJob }));
  if (!data.length) return <div className="muted" style={{ fontSize: 12 }}>Chưa có dữ liệu lộ trình.</div>;
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="date" fontSize={11} />
        <YAxis fontSize={11} />
        <Tooltip />
        <Line type="monotone" dataKey="wage" stroke="var(--red-600, #a01b1b)" strokeWidth={2} dot />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CriteriaRadar({ lines }) {
  const data = (lines || []).map((l) => ({
    crit: l.name, current: l.score, target: l.maxScore }));
  if (!data.length) return <div className="muted" style={{ fontSize: 12 }}>Chưa có đợt đánh giá.</div>;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="crit" fontSize={10} />
        <PolarRadiusAxis fontSize={9} />
        <Radar name="Mục tiêu" dataKey="target" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.1} />
        <Radar name="Hiện tại" dataKey="current" stroke="var(--red-600, #a01b1b)" fill="var(--red-600, #a01b1b)" fillOpacity={0.35} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 2: Upgrade PromoTab into dashboard**

Trong `EmployeeDrawer.jsx`: thêm import đầu file:
```jsx
import EvaluationForm from './EvaluationForm';
import { SalaryJourneyChart, CriteriaRadar } from './PromoCharts';
import { fetchEvaluations } from '../../api/employees';
```
Thay thân hàm `PromoTab` (đang ở ~line 488) bằng phiên bản dashboard:
```jsx
export function PromoTab({ det, isMgr, editable, onUpdated }) {
  const [adding, setAdding] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evalData, setEvalData] = useState(null);
  const canAct = editable && onUpdated;

  useEffect(() => {
    if (canAct) fetchEvaluations(det.id).then(setEvalData).catch(() => setEvalData(null));
  }, [det.id, canAct]);

  const latest = evalData?.evaluations?.[evalData.evaluations.length - 1];
  const am = evalData?.autoMetrics;
  const VLABEL = { qualified: 'Đủ điều kiện', consider: 'Cân nhắc', not_yet: 'Chưa đủ' };

  return (
    <div>
      {/* Hàng chỉ số tự động */}
      {am && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
          <MetricCard label="Thâm niên (tháng)" value={am.tenureMonths} />
          <MetricCard label="Từ thăng tiến" value={am.monthsSincePromo ?? '—'} />
          <MetricCard label="Chấm công 3T" value={am.attendance ? `${am.attendance.days} ngày` : 'Chưa có'} />
          <MetricCard label="Kết luận gần nhất" value={latest ? `${latest.totalScore}%` : '—'} />
        </div>
      )}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 320px' }}>
          <SectionTitle>Lộ trình chức vụ & lương</SectionTitle>
          <SalaryJourneyChart promotions={det.promotions} />
        </div>
        <div style={{ flex: '1 1 260px' }}>
          <SectionTitle>Radar tiêu chí (đợt gần nhất)</SectionTitle>
          <CriteriaRadar lines={latest?.lines} />
        </div>
      </div>

      {canAct && (
        <div className="between" style={{ margin: '16px 0' }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>
            Lịch sử ({det.promotions.length} mốc · {evalData?.evaluations?.length || 0} đợt đánh giá)
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-soft btn-sm" disabled={!evalData}
              onClick={() => setEvaluating(true)}>
              <Icon name="checkCircle" size={13} />Đánh giá mới</button>
            {isMgr && (
              <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
                <Icon name="arrowUp" size={13} />Tạo thăng tiến</button>
            )}
          </div>
        </div>
      )}

      {!det.promotions.length ? (
        <EmptyState>Chưa có lịch sử thăng tiến.</EmptyState>
      ) : (
        <PromoTimeline path={det.promotions} isMgr={isMgr} />
      )}

      {adding && (
        <PromotionForm det={det}
          onClose={() => setAdding(false)}
          onSaved={(d) => { setAdding(false); onUpdated(d); }} />
      )}
      {evaluating && evalData && (
        <EvaluationForm empId={det.id} criteria={evalData.criteria}
          onClose={() => setEvaluating(false)}
          onSaved={(d) => { setEvaluating(false); setEvalData(d); }} />
      )}
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div style={{ flex: '1 1 110px', background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 12px', textAlign: 'center' }}>
      <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--red-700)' }}>{value}</div>
      <div style={{ fontSize: 10.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</div>
    </div>
  );
}

function SectionTitle({ children }) {
  return <div style={{ fontWeight: 700, fontSize: 12.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 6 }}>{children}</div>;
}
```
> Đảm bảo `useEffect`, `useState` đã import từ `react` ở đầu `EmployeeDrawer.jsx` (thêm `useEffect` nếu thiếu). Giữ nguyên các component `PromoTimeline`, `EmptyState` đang dùng.

- [ ] **Step 3: Build + verify trên preview**

```bash
cd frontend && npm run build
```
Sau đó dùng preview (`preview_start` → mở `/hocba-hrm`, đăng nhập `test_hrmanager@hocba.vn`/`Hocba@2026`). Mở 1 NV → tab "Thăng tiến":
- Thấy hàng 4 thẻ chỉ số, 2 biểu đồ, nút "Đánh giá mới" + "Tạo thăng tiến".
- Bấm "Đánh giá mới" → kéo điểm → tổng % cập nhật → chọn kết luận → Xác nhận → radar hiện đợt vừa chấm.
- Kiểm `preview_console_logs` không có lỗi recharts/React.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/employees/PromoCharts.jsx \
        frontend/src/features/employees/EmployeeDrawer.jsx \
        custom-addons/hocba_hrm/static/spa/
git commit -m "feat(spa): dashboard đánh giá thăng tiến (charts + chấm điểm)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11: Verify toàn luồng + cập nhật tài liệu

**Files:**
- Modify: `docs/DB_TEST_DATA.md` (nếu seed/đổi DB)

- [ ] **Step 1: Chạy lại toàn bộ test backend**

Run lệnh test ở đầu plan. Expected: `0 failed, 0 error(s) of N tests`, N gồm các test mới.

- [ ] **Step 2: Verify quyền end-to-end (manual)**

- HR Manager: chấm + xác nhận + "Tạo thăng tiến" (đính evaluationId) OK.
- Trưởng phòng (`test_truongphong@hocba.vn`): chấm được NV phòng mình; KHÔNG thấy nút "Tạo thăng tiến".
- Giáo vụ (`test_giaovu@hocba.vn`): chấm được giáo viên; chặn NV không phải giáo viên (403).
- NV thường (`test_employee@hocba.vn`): không thấy dashboard đánh giá của người khác.

- [ ] **Step 3: Cập nhật tài liệu nếu cần**

Nếu có seed/đổi dữ liệu DB phục vụ demo → cập nhật `docs/DB_TEST_DATA.md` (bảng tài khoản + nhật ký) theo quy ước nhóm.

- [ ] **Step 4: Commit (nếu có thay đổi tài liệu)**

```bash
git add docs/DB_TEST_DATA.md
git commit -m "docs: nhật ký dữ liệu demo đánh giá thăng tiến

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Finish branch**

Dùng skill `superpowers:finishing-a-development-branch` để quyết định merge/PR cho nhánh `Tan/Employee`.

---

## Self-Review notes (đã kiểm)

- **Spec coverage:** model (Task 1-3) ✓ · chỉ số tự động + attendance guard (Task 4) ✓ · phân quyền (Task 5, helper `_can_eval_emp` Task 6/7) ✓ · API GET/POST + nối evidence (Task 6/7) ✓ · UI dashboard + recharts + theme đỏ/sáng (Task 8-10) ✓ · NV thường không xem (Task 6 `_can_eval_emp`, Task 10 chỉ render khi `canAct`) ✓ · bỏ panel ⚠ (không có task) ✓.
- **Verdict ngưỡng** nhất quán FE (80/60 hardcode gợi ý realtime) ↔ BE (`ir.config_parameter`, nguồn sự thật). Nếu khách đổi ngưỡng, sửa cả config_parameter (BE) + hằng `autoVerdict` (FE) — đã ghi chú.
- **Tên field/khóa** nhất quán: `total_score`, `verdict_auto`, `verdict_final`, `_promo_auto_metrics`, `x_evaluation_ids`, endpoint `/api/promotion/eval/...`.
- **Audit/permission** theo đúng pattern `hr.promotion.history` + `_can_eval_emp`.
