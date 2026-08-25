"""Repair external IDs missing from legacy offline payroll databases."""


def migrate(cr, version):
    categories = {
        'rule_categ_alw': 'phu_cap',
        'rule_categ_bonus': 'thuong',
        'rule_categ_gross': 'tong_thu_nhap',
        'rule_categ_deduct': 'giam_tru',
        'rule_categ_ded': 'khau_tru_nv',
        'rule_categ_tax': 'thue_tncn',
        'rule_categ_net': 'thuc_lanh',
        'rule_categ_comp': 'bh_phan_cong_ty',
    }
    for xml_name, code in categories.items():
        # Một số DB offline còn external ID nhưng res_id trỏ tới các category
        # đã bị xoá/reseed (1..8), trong khi bản ghi thật hiện là id khác.
        cr.execute(
            """
            UPDATE ir_model_data AS data
               SET res_id = category.id, write_date = NOW()
              FROM hb_salary_rule_category AS category
             WHERE data.module = 'hocba_payroll'
               AND data.name = %s
               AND category.code = %s
            """,
            (xml_name, code),
        )
        cr.execute(
            """
            INSERT INTO ir_model_data
                (module, name, model, res_id, noupdate, create_date, write_date)
            SELECT 'hocba_payroll', %s, 'hb.salary.rule.category', category.id,
                   FALSE, NOW(), NOW()
              FROM hb_salary_rule_category AS category
             WHERE category.code = %s
               AND NOT EXISTS (
                   SELECT 1 FROM ir_model_data
                    WHERE module = 'hocba_payroll' AND name = %s
               )
            """,
            (xml_name, code, xml_name),
        )
