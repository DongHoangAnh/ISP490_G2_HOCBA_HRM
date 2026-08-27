"""Repair legacy salary-rule XML IDs and remove duplicate rules.

Some upgraded databases lost external IDs for seed rules.  Loading the XML
again then created a second rule with the same code in the same structure,
which made payroll generate duplicate lines and broke formula dependencies.
"""


RULE_XML_IDS = {
    'STRUCT_OFFLINE': {
        'luong_co_ban': 'rule_off_luong_co_ban',
        'cong': 'rule_off_cong',
        'ngay_nghi': 'rule_off_ngay_nghi',
        'nctt': 'rule_off_nctt',
        'an_ca': 'rule_off_an_ca',
        'xang_xe': 'rule_off_xang_xe',
        'dien_thoai': 'rule_off_dien_thoai',
        'thuong_khac': 'rule_off_thuong_khac',
        'ho_tro_nuoi_con': 'rule_off_ho_tro_nuoi_con',
        'role_allowance': 'rule_off_role_allowance',
        'bonus_extra': 'rule_off_bonus_extra',
        'tong_thu_nhap': 'rule_off_gross',
        'tn_mien_thue': 'rule_off_tn_mien_thue',
        'tn_truoc_thue': 'rule_off_tn_truoc_thue',
        'npt': 'rule_off_npt',
        'giam_tru': 'rule_off_giam_tru',
        'bhxh_8_nv': 'rule_off_bhxh_nv',
        'bhyt_1_5_nv': 'rule_off_bhyt_nv',
        'bhtn_1_nv': 'rule_off_bhtn_nv',
        'tn_tinh_thue': 'rule_off_tn_tinh_thue',
        'thue_tncn': 'rule_off_tncn',
        'penalty_amount': 'rule_off_penalty_amount',
        'thuc_lanh': 'rule_off_net',
        'bhxh_17_5_ct': 'rule_off_bhxh_ct',
        'bhyt_3_ct': 'rule_off_bhyt_ct',
        'bhtn_1_ct': 'rule_off_bhtn_ct',
    },
    'STRUCT_ONLINE': {
        'luong': 'rule_on_wage',
        'thuong': 'rule_on_thuong',
        'tong_thu_nhap': 'rule_on_gross',
        'tam_ung_tru_khac': 'rule_on_tam_ung',
        'thuc_lanh': 'rule_on_net',
    },
}


def migrate(cr, version):
    for structure_code, rules in RULE_XML_IDS.items():
        for rule_code, xml_name in rules.items():
            cr.execute(
                """
                SELECT rule.id
                  FROM hb_salary_rule AS rule
                  JOIN hb_salary_structure AS structure
                    ON structure.id = rule.structure_id
                 WHERE structure.code = %s AND rule.code = %s
                 ORDER BY rule.id
                """,
                (structure_code, rule_code),
            )
            ids = [row[0] for row in cr.fetchall()]
            if not ids:
                continue

            # Keep the oldest legacy record so existing configuration/history
            # remains attached; the following XML load refreshes seed values.
            keep_id, duplicate_ids = ids[0], ids[1:]
            cr.execute(
                """
                UPDATE ir_model_data
                   SET model = 'hb.salary.rule', res_id = %s, write_date = NOW()
                 WHERE module = 'hocba_payroll' AND name = %s
                """,
                (keep_id, xml_name),
            )
            if not cr.rowcount:
                cr.execute(
                    """
                    INSERT INTO ir_model_data
                        (module, name, model, res_id, noupdate, create_date, write_date)
                    VALUES ('hocba_payroll', %s, 'hb.salary.rule', %s,
                            FALSE, NOW(), NOW())
                    """,
                    (xml_name, keep_id),
                )

            if duplicate_ids:
                cr.execute(
                    'UPDATE hb_payslip_line SET rule_id = %s WHERE rule_id = ANY(%s)',
                    (keep_id, duplicate_ids),
                )
                cr.execute(
                    'DELETE FROM ir_model_data WHERE model = %s AND res_id = ANY(%s)',
                    ('hb.salary.rule', duplicate_ids),
                )
                cr.execute(
                    'DELETE FROM hb_salary_rule WHERE id = ANY(%s)',
                    (duplicate_ids,),
                )
