from odoo import models, fields, api


class HbSalaryRule(models.Model):
    _name = 'hb.salary.rule'
    _description = 'Salary Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Tên', required=True, translate=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', required=True, default=10)
    structure_id = fields.Many2one(
        'hb.salary.structure', string='Cấu trúc lương',
        required=True, ondelete='cascade', index=True,
    )
    category_id = fields.Many2one(
        'hb.salary.rule.category', string='Danh mục',
        required=True, ondelete='restrict',
    )
    active = fields.Boolean(default=True)

    # ── Computation ──────────────────────────────────────────────
    amount_type = fields.Selection(
        [
            ('fixed', 'Số tiền cố định'),
            ('percentage', 'Tỉ lệ %'),
            ('formula', 'Công thức'),
            ('code', 'Python Code'),
        ],
        string='Loại tính', default='fixed', required=True,
    )
    amount_python_compute = fields.Text(
        string='Python Code',
        help='Python code gán kết quả vào biến `result`.',
    )
    amount_formula = fields.Text(
        string='Công thức',
        help='Công thức tham chiếu mã quy tắc lương. SUM(a, b) cộng tất cả rule từ a đến b theo thứ tự. VD: luong_thoi_gian * 0.08, SUM(luong_thoi_gian, thuong_khac)',
    )
    amount_fixed = fields.Float(
        string='Số tiền cố định', digits=(16, 0),
    )
    amount_percentage = fields.Float(
        string='Tỉ lệ %', digits=(8, 4),
    )
    amount_percentage_base = fields.Char(
        string='Biểu thức base cho %',
    )

    # ── Condition ────────────────────────────────────────────────
    condition_type = fields.Selection(
        [
            ('none', 'Luôn đúng'),
            ('python', 'Biểu thức Python'),
        ],
        string='Điều kiện', default='none',
    )
    condition_python = fields.Text(string='Điều kiện Python')

    # ── Display ──────────────────────────────────────────────────
    appears_on_payslip = fields.Boolean(
        string='Hiển thị trên phiếu lương', default=True,
    )
    note = fields.Text(string='Mô tả')

    # ── Formula helper actions ─────────────────────────────────
    def action_insert_formula_func(self):
        """Append function snippet to the formula field."""
        snippet = self.env.context.get('formula_snippet', '')
        if snippet:
            current = self.amount_formula or ''
            self.amount_formula = (current + ' ' + snippet).strip()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_show_formula_help(self):
        """Open a dialog showing all available formula functions."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hướng dẫn hàm công thức',
            'res_model': 'hb.formula.help.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
