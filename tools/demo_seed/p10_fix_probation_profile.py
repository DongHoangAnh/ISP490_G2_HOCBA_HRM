# -*- coding: utf-8 -*-
"""PHASE 10 — bổ sung hồ sơ BR-010 cho NV thử việc rồi chốt các ca đã xong.

Seed chỉ khai CCCD/MST/BHXH cho NV đã Chính thức (BR-010 chỉ bắt buộc ở trạng
thái đó), nên NV thử việc chạy xong hết bước vẫn không lên Chính thức được —
BR-010 chặn ngay ở `_hocba_make_official`. Với bản demo ta khai đủ cho NV thử
việc để xem được cả luồng chốt thử việc.

Chốt thử việc đi đúng đường của quy trình: `action_hocba_finalize_onboarding`
(nút "Chuyển chính thức" của HR) — hệ thống KHÔNG tự lên chính thức khi hết
chuỗi bước, phải có người bấm.
Idempotent: chỉ ghi field còn trống; NV đã Chính thức không còn khớp bộ lọc.
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

official = blocked = 0
for e in Emp.search([('x_employment_status', '=', 'probation')]):
    ok, reason = e._hocba_onboarding_can_finalize()
    if not ok:
        continue
    if e._hocba_missing_official_fields():
        # BR-010 vẫn thiếu: bấm nút cũng chỉ ăn ValidationError giữa chừng.
        blocked += 1
        continue
    e.action_hocba_finalize_onboarding()
    official += 1
say('chốt thử việc: %s NV lên Chính thức, %s NV còn thiếu hồ sơ'
    % (official, blocked))
env.cr.commit()

for e in Emp.search([('x_employee_code', '!=', False)],
                    order='x_employee_code'):
    steps = e.x_onboarding_step_ids
    if steps and all(s.state in ('done', 'skipped') for s in steps):
        print('  %-10s %-24s %s' % (e.x_employee_code, e.name,
                                    e.x_employment_status))
