#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed dữ liệu **Dashboard sự nghiệp**: vinh danh + đánh giá thăng tiến.

    docker compose -f docker-compose.yml -f docker-compose.local.yml \
        run --rm -v "$PWD/tools:/tools" odoo python3 /tools/seed_demo_honor.py

Env: SEED_DB (mặc định hocba_demo)

Màn "Lộ trình sự nghiệp" ghép 3 nguồn, seed đủ cả ba thì khung nào cũng có số:
  1. `hb.honor.entry`            → khung Bảng vinh danh (kỳ = THÁNG dương lịch;
                                   kỳ hiện tại rỗng thì API tự lùi về kỳ gần nhất)
  2. `hr.promotion.evaluation`   → bảng xếp hạng bên cạnh (chỉ lấy đợt đã xác
                                   nhận + kết luận "Đủ điều kiện" TRONG kỳ đó)
  3. `hr.promotion.history`      → mốc lộ trình, biểu đồ bậc lương, radar tiêu chí

Bổ nhiệm (`x_change_type='promotion'` + đổi chức vụ) TỰ sinh mục vinh danh
`source='auto'` — cố ý dùng đường này cho 2 người để demo cả luồng tự động.
Chạy lại được: xoá sạch mục vinh danh + đợt đánh giá do script này tạo trước khi
seed lại (lịch sử thăng tiến KHÔNG xoá được bằng ORM nên dọn bằng SQL).
"""
import logging
import os
import sys
from datetime import date

import odoo
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

_log = logging.getLogger('seed_honor')
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

DB = os.environ.get('SEED_DB', 'hocba_demo')
THIS_MONTH = date(2026, 8, 1)

# Vinh danh HR nhập tay — (tên NV, nhóm, danh hiệu, mô tả, ngày, hạng)
MANUAL_HONORS = [
    ('Nguyễn Thị Thương', 'achievement', 'Nhân viên xuất sắc tháng 8',
     'Chốt 18 hợp đồng tuyển sinh, dẫn đầu phòng Kinh doanh 2 tháng liên tiếp.',
     date(2026, 8, 5), 1),
    ('Hán Vũ Tú Ngọc', 'achievement', 'Giáo viên được yêu thích nhất',
     'Điểm hài lòng học viên 4.9/5, không buổi nào vào lớp trễ trong tháng 7.',
     date(2026, 8, 5), 2),
    ('Lô Đức Thịnh', 'achievement', 'Chiến dịch Marketing ấn tượng',
     'Chiến dịch "Hè HSK" vượt 140% chỉ tiêu lead với chi phí giảm 18%.',
     date(2026, 8, 5), 3),
    ('Ngô Thị Minh Tuyết', 'achievement', 'Ngôi sao chăm sóc học viên',
     'Giữ chân 96% học viên tái đăng ký khoá mới.',
     date(2026, 8, 5), 0),
    ('Lê Thu Thảo', 'other', 'Sáng kiến của tháng',
     'Bộ đề luyện HSK4 rút ngắn 30% thời gian soạn bài cho giáo viên.',
     date(2026, 8, 10), 0),
    # Kỳ trước — để bấm xem lịch sử vinh danh có dữ liệu
    ('Vũ Hoàng Minh', 'achievement', 'Nhân viên xuất sắc tháng 7',
     'Tối ưu quảng cáo Google, giảm 22% chi phí trên mỗi lead.',
     date(2026, 7, 6), 1),
    ('Đỗ Thu Giang', 'achievement', 'Giáo viên tận tâm tháng 7',
     'Nhận dạy bù 6 buổi cho lớp HSK3 khi đồng nghiệp nghỉ ốm.',
     date(2026, 7, 6), 2),
    ('Lê Thị Dung', 'tenure', 'Gắn bó 2 năm cùng Học Bá',
     'Ghi nhận 2 năm đồng hành cùng bộ phận Hành chính – Nhân sự.',
     date(2026, 7, 6), 0),
]

# Bổ nhiệm → tự sinh vinh danh (tên NV, chức vụ mới, phòng ban, lương, ngày, lý do)
# Chức vụ mới PHẢI khác chức vụ đang giữ: hook vinh danh tự động chỉ chạy khi
# `to_job_id != from_job_id` (tăng lương suông không có chức danh mới để công bố).
# Nhân sự trong DB demo đang gắn đúng vị trí JD lúc tuyển, nên bổ nhiệm cần vị
# trí quản lý mới — tạo sẵn ở đây, đánh dấu ngừng tuyển để không lẫn vào màn
# Tuyển dụng.
PROMOTIONS = [
    ('Đỗ Thị Hải Ngọc', 'Trưởng nhóm Tư vấn tuyển sinh', 'Kinh doanh',
     12_000_000, date(2026, 8, 3),
     'Đạt 128% chỉ tiêu doanh số quý 2, đủ điều kiện lên Trưởng nhóm.'),
    ('Nguyễn Thị Mai', 'Trưởng nhóm Content Marketing', 'Marketing',
     11_500_000, date(2026, 8, 12),
     'Dẫn dắt nhóm Social 6 tháng, kết quả vượt mục tiêu tương tác.'),
]

# Đợt đánh giá thăng tiến — (tên NV, ngày, điểm 4 tiêu chí, kết luận)
EVALUATIONS = [
    ('Nguyễn Thị Thương',  date(2026, 8, 8),  [5, 5, 5, 4], 'qualified'),
    ('Hán Vũ Tú Ngọc',     date(2026, 8, 8),  [5, 5, 4, 5], 'qualified'),
    ('Lô Đức Thịnh',       date(2026, 8, 9),  [5, 4, 5, 4], 'qualified'),
    ('Ngô Thị Minh Tuyết', date(2026, 8, 9),  [4, 5, 5, 4], 'qualified'),
    ('Lê Thu Thảo',        date(2026, 8, 10), [5, 4, 4, 5], 'qualified'),
    ('Vũ Hoàng Minh',      date(2026, 8, 10), [4, 4, 4, 4], 'consider'),
    ('Bùi Thị Trang',      date(2026, 8, 11), [3, 4, 4, 3], 'not_yet'),
    # Đợt cũ hơn của chính vài người trên → radar có cột "đợt trước" để so
    ('Nguyễn Thị Thương',  date(2026, 6, 12), [4, 4, 4, 3], 'consider'),
    ('Hán Vũ Tú Ngọc',     date(2026, 6, 12), [4, 5, 3, 4], 'consider'),
    ('Lô Đức Thịnh',       date(2026, 6, 15), [4, 4, 4, 4], 'consider'),
]


def main():
    odoo.tools.config.parse_config([
        '-c', '/etc/odoo/odoo.conf', '-d', DB,
        '--addons-path=/mnt/extra-addons',
        '--db_host=%s' % os.environ.get('HOST', 'db'),
        '--db_port=%s' % os.environ.get('PORT', '5432'),
        '--db_user=%s' % os.environ.get('USER', 'odoo'),
        '--db_password=%s' % os.environ.get('PASSWORD', 'odoo_password'),
    ])
    reg = Registry(DB)
    with reg.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {
            'lang': 'en_US', 'tz': 'Asia/Ho_Chi_Minh',
            'tracking_disable': True, 'mail_notrack': True,
        })
        Emp = env['hr.employee'].sudo()
        Honor = env['hb.honor.entry'].sudo().with_context(active_test=False)
        Eval = env['hr.promotion.evaluation'].sudo()
        Promo = env['hr.promotion.history'].sudo()
        hr_user = env['res.users'].sudo().search(
            [('login', '=', 'test_hrmanager@hocba.vn')], limit=1)

        def emp_of(name):
            e = Emp.search([('name', '=', name)], limit=1)
            if not e:
                _log.warning('  ! không thấy nhân viên "%s" — bỏ qua', name)
            return e

        # ── Dọn dữ liệu của lần chạy trước ───────────────────────────────
        Honor.search([]).unlink()
        cr.execute("DELETE FROM hr_promotion_evaluation_line")
        cr.execute("DELETE FROM hr_promotion_evaluation")
        # unlink() của hr.promotion.history bị chặn (audit trail) → SQL, và chỉ
        # xoá mốc thăng chức/điều chỉnh lương do script sinh, GIỮ mốc 'join'.
        cr.execute("DELETE FROM hr_promotion_history "
                   "WHERE x_change_type IN ('promotion', 'salary')")
        _log.info('Dọn dữ liệu cũ: %s mốc thăng tiến', cr.rowcount)
        env.invalidate_all()

        # ── 1. Bổ nhiệm (tự sinh mục vinh danh source='auto') ────────────
        n_promo = 0
        for name, job_name, dept_name, wage, eff, reason in PROMOTIONS:
            emp = emp_of(name)
            if not emp:
                continue
            job = env['hr.job'].sudo().search([('name', '=', job_name)], limit=1)
            if not job:
                dept = env['hr.department'].sudo().search(
                    [('name', '=', dept_name)], limit=1)
                job = env['hr.job'].sudo().create({
                    'name': job_name,
                    'department_id': dept.id or False,
                    'recruitment_status': 'stopped',
                    'x_published': False,
                })
            old_wage = emp.version_id.wage
            Promo.create({
                'employee_id': emp.id,
                'x_change_type': 'promotion',
                'date_effective': eff,
                'from_job_id': emp.job_id.id or False,
                'to_job_id': job.id or False,
                'to_department_id': emp.department_id.id,
                'x_work_form': emp.x_work_form,
                'x_employment_status': emp.x_employment_status,
                'from_wage': old_wage,
                'to_wage': wage,
                'reason': reason,
                'x_evidence_url': 'https://drive.hocba.vn/danh-gia/%s' % emp.id,
                'decision_ref': 'QĐ-%s/2026-HB' % (100 + n_promo),
                'approved_by': (hr_user or env.user).id,
            })
            emp.version_id.sudo().write({'wage': wage})
            n_promo += 1
            _log.info('  ↑ bổ nhiệm %-22s → %s (%s đ)', name, job_name,
                      '{:,}'.format(wage))
        _log.info('Bổ nhiệm: %s (mỗi cái tự sinh 1 mục vinh danh)', n_promo)

        # ── 2. Vinh danh HR nhập tay ─────────────────────────────────────
        n_honor = 0
        for name, categ, title, desc, when, rank in MANUAL_HONORS:
            emp = emp_of(name)
            if not emp:
                continue
            Honor.create({
                'employee_id': emp.id, 'category': categ, 'title': title,
                'description': desc, 'date_awarded': when, 'rank': rank,
                'source': 'manual',
            })
            n_honor += 1
        _log.info('Vinh danh HR nhập tay: %s mục', n_honor)

        # ── 3. Đợt đánh giá thăng tiến (nguồn của bảng xếp hạng) ─────────
        crits = env['hr.promotion.criteria'].sudo().search([], order='sequence, id')
        n_eval = 0
        for name, when, scores, verdict in EVALUATIONS:
            emp = emp_of(name)
            if not emp or not crits:
                continue
            ev = Eval.create({
                'employee_id': emp.id,
                'eval_date': when,
                'evaluator_id': (emp.department_id.manager_id.user_id
                                 or hr_user or env.user).id,
                'verdict_final': verdict,
                'conclusion_note': {
                    'qualified': 'Đủ điều kiện xét thăng tiến đợt tới.',
                    'consider': 'Cân nhắc — cần thêm một kỳ quan sát.',
                    'not_yet': 'Chưa đủ điều kiện, tiếp tục theo dõi.',
                }[verdict],
                'snapshot_job_id': emp.job_id.id or False,
                'line_ids': [(0, 0, {
                    'criteria_id': c.id,
                    'score': scores[i] if i < len(scores) else 4,
                }) for i, c in enumerate(crits)],
            })
            ev.action_confirm()
            n_eval += 1
        _log.info('Đợt đánh giá thăng tiến: %s (đã xác nhận)', n_eval)

        cr.commit()

        # ── Kiểm chứng ───────────────────────────────────────────────────
        cr.execute("""SELECT period_key, count(*) FROM hb_honor_entry
                       WHERE active GROUP BY 1 ORDER BY 1 DESC""")
        for period, cnt in cr.fetchall():
            _log.info('KỲ %s: %s mục vinh danh', period, cnt)
        cr.execute("""SELECT count(*) FROM hr_promotion_evaluation
                       WHERE state = 'confirmed' AND verdict_final = 'qualified'
                         AND eval_date >= %s""", (THIS_MONTH,))
        _log.info('Xếp hạng kỳ này: %s người đủ điều kiện', cr.fetchone()[0])
    _log.info('✅ Xong.')


if __name__ == '__main__':
    main()
