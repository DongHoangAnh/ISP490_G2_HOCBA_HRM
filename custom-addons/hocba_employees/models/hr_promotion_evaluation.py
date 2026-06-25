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
