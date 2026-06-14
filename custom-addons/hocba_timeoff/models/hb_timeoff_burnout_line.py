from odoo import fields, models, tools


class HbTimeoffBurnoutLine(models.Model):
    """Per-employee burnout risk analysis — Widget 6.

    Computes BR-040 criteria 1 and 2 (OT criterion skipped — requires Attendance module).
    """

    _name = 'hb.timeoff.burnout.line'
    _description = 'Cảnh báo Burnout Nhân viên (Học Bá)'
    _auto = False
    _rec_name = 'employee_id'
    _order = 'burnout_risk desc, sick_leave_count_3m desc'

    employee_id = fields.Many2one('hr.employee', string='Nhân viên', readonly=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', readonly=True)
    sick_leave_count_3m = fields.Integer(
        string='Số lần nghỉ ốm (3 tháng)', readonly=True,
    )
    total_absence_days_3m = fields.Float(
        string='Tổng ngày vắng (3 tháng)', readonly=True,
    )
    remaining_leave_balance = fields.Float(
        string='Số dư nghỉ phép', readonly=True,
    )
    burnout_risk = fields.Boolean(
        string='Cảnh báo Burnout', readonly=True,
    )
    risk_reason = fields.Char(string='Lý do cảnh báo', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hb_timeoff_burnout_line')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hb_timeoff_burnout_line AS (
                SELECT
                    e.id                                                      AS id,
                    e.id                                                      AS employee_id,
                    v.department_id                                           AS department_id,

                    -- Số lần nghỉ ốm trong 90 ngày gần nhất (BR-040 criterion 1)
                    COUNT(hl.id) FILTER (
                        WHERE hl.state = 'validate'
                          AND hlt.support_document = True
                          AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                    )::int                                                    AS sick_leave_count_3m,

                    -- Tổng ngày vắng trong 90 ngày gần nhất (BR-040 criterion 2)
                    COALESCE(
                        SUM(hl.number_of_days) FILTER (
                            WHERE hl.state = 'validate'
                              AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                        ), 0
                    )                                                         AS total_absence_days_3m,

                    -- Số dư nghỉ phép còn lại (từ hr_leave_report: allocation + request)
                    COALESCE(rb.remaining_days, 0)                            AS remaining_leave_balance,

                    -- Cờ burnout risk tổng hợp
                    CASE
                        WHEN COUNT(hl.id) FILTER (
                            WHERE hl.state = 'validate'
                              AND hlt.support_document = True
                              AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                        ) >= 3                           THEN True
                        WHEN COALESCE(
                            SUM(hl.number_of_days) FILTER (
                                WHERE hl.state = 'validate'
                                  AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                            ), 0
                        ) > 10                           THEN True
                        WHEN rb.remaining_days IS NOT NULL
                             AND rb.remaining_days < 2
                                                         THEN True
                        ELSE False
                    END                                                       AS burnout_risk,

                    -- Lý do cảnh báo (hiển thị nguyên nhân chính)
                    CASE
                        WHEN COUNT(hl.id) FILTER (
                            WHERE hl.state = 'validate'
                              AND hlt.support_document = True
                              AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                        ) >= 3
                            THEN 'Nghỉ ốm thường xuyên (≥3 lần / 3 tháng)'
                        WHEN COALESCE(
                            SUM(hl.number_of_days) FILTER (
                                WHERE hl.state = 'validate'
                                  AND hl.date_from >= CURRENT_DATE - INTERVAL '90 days'
                            ), 0
                        ) > 10
                            THEN 'Vắng nhiều (>10 ngày / 3 tháng)'
                        WHEN rb.remaining_days IS NOT NULL
                             AND rb.remaining_days < 2
                            THEN 'Số dư nghỉ phép thấp (<2 ngày)'
                        ELSE ''
                    END                                                       AS risk_reason

                FROM hr_employee e
                LEFT JOIN hr_version    v   ON v.id  = e.current_version_id
                LEFT JOIN hr_leave      hl  ON hl.employee_id = e.id
                LEFT JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id
                LEFT JOIN (
                    SELECT r.employee_id, SUM(r.number_of_days) AS remaining_days
                    FROM hr_leave_report r
                    WHERE r.state = 'validate'
                    GROUP BY r.employee_id
                ) rb ON rb.employee_id = e.id
                WHERE e.active = True
                GROUP BY e.id, v.department_id, rb.remaining_days
            )
        """)
