"""
BHXH Report Line — per-employee detail.
FUNC-PR-004
"""
from odoo import api, fields, models


class BhxhReportLine(models.Model):
    _name = 'hb.bhxh.report.line'
    _description = 'Chi tiết BHXH theo nhân viên'
    _order = 'employee_code'

    report_id = fields.Many2one(
        'hb.bhxh.report', string='Báo cáo', required=True, ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True, ondelete='restrict',
    )
    employee_code = fields.Char(string='Mã NV')
    social_insurance_no = fields.Char(string='Số sổ BHXH')
    insurance_base = fields.Float(string='Mức đóng BH', digits=(16, 0))
    # Employee portion
    bhxh_ee = fields.Float(string='BHXH (NV)', digits=(16, 0))
    bhyt_ee = fields.Float(string='BHYT (NV)', digits=(16, 0))
    bhtn_ee = fields.Float(string='BHTN (NV)', digits=(16, 0))
    # Employer portion
    bhxh_er = fields.Float(string='BHXH (DN)', digits=(16, 0))
    bhyt_er = fields.Float(string='BHYT (DN)', digits=(16, 0))
    bhtn_er = fields.Float(string='BHTN (DN)', digits=(16, 0))

    total_ee = fields.Float(
        string='Tổng NV đóng', compute='_compute_totals', store=True, digits=(16, 0),
    )
    total_er = fields.Float(
        string='Tổng DN đóng', compute='_compute_totals', store=True, digits=(16, 0),
    )

    @api.depends('bhxh_ee', 'bhyt_ee', 'bhtn_ee', 'bhxh_er', 'bhyt_er', 'bhtn_er')
    def _compute_totals(self):
        for rec in self:
            rec.total_ee = rec.bhxh_ee + rec.bhyt_ee + rec.bhtn_ee
            rec.total_er = rec.bhxh_er + rec.bhyt_er + rec.bhtn_er

    def _to_api_dict(self):
        self.ensure_one()
        return {
            'id': self.id,
            'employee_id': self.employee_id.id,
            'employee_name': self.employee_id.name,
            'employee_code': self.employee_code,
            'social_insurance_no': self.social_insurance_no,
            'insurance_base': self.insurance_base,
            'bhxh_ee': self.bhxh_ee,
            'bhyt_ee': self.bhyt_ee,
            'bhtn_ee': self.bhtn_ee,
            'bhxh_er': self.bhxh_er,
            'bhyt_er': self.bhyt_er,
            'bhtn_er': self.bhtn_er,
            'total_ee': self.total_ee,
            'total_er': self.total_er,
        }
