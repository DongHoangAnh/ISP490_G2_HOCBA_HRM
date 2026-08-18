# -*- coding: utf-8 -*-
"""PHASE 10 — bổ sung hồ sơ BR-010 cho NV thử việc rồi chốt các ca đã xong.

Seed chỉ khai CCCD/MST/BHXH cho NV đã Chính thức (BR-010 chỉ bắt buộc ở trạng
thái đó), nên NV thử việc chạy xong hết bước vẫn không lên Chính thức được —
_close_probation sẽ giữ Thử việc + bắn chuông "còn thiếu ...". Với bản demo ta
khai đủ cho NV thử việc để xem được cả luồng chốt thử việc.
Idempotent: chỉ ghi field còn trống.
"""
exec(open('/tmp/seed/common.py').read())

Emp = env['hr.employee'].sudo().with_context(active_test=False)

probation = Emp.search([('x_employment_status', '=', 'probation'),
                        ('x_employee_code', '!=', False)],
                       order='x_employee_code')
for i, e in enumerate(probation):
    vals = {}
    if not e.x_pit_code:
        vals['x_pit_code'] = '80%08d' % (17700000 + i)
    if not e.x_social_insurance_no:
        vals['x_social_insurance_no'] = '01%08d' % (17700000 + i)
    if vals:
        e.write(vals)
    # CCCD nằm trên hr.version (Odoo 19), không phải hr.employee
    if not e.identification_id:
        e.write({'identification_id': '0010960%05d' % (i + 800)})
    say('bổ sung hồ sơ:', e.x_employee_code, e.name)
env.cr.commit()

res = Emp._hocba_close_finished_probations()
say('chốt thử việc: %s NV lên Chính thức, %s NV còn thiếu hồ sơ'
    % (res['official'], res['blocked']))
env.cr.commit()

for e in Emp.search([('x_employee_code', '!=', False)],
                    order='x_employee_code'):
    steps = e.x_onboarding_step_ids
    if steps and all(s.state in ('done', 'skipped') for s in steps):
        print('  %-10s %-24s %s' % (e.x_employee_code, e.name,
                                    e.x_employment_status))
