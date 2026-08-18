# -*- coding: utf-8 -*-
"""PHASE 2 — Hồ sơ sâu: chứng chỉ, người phụ thuộc, tài sản, quy trình nhận việc.

Chứng chỉ cố tình rải 3 nhóm hạn (còn hạn / sắp hết / đã hết) để panel
"Cảnh báo chứng chỉ" trên Dashboard có dữ liệu thật.
"""
exec(open('/tmp/seed/common.py').read())

import datetime

Skill = env['hr.employee.skill'].sudo()
Dep = env['hr.employee.dependent'].sudo()
Asset = env['hr.employee.asset'].sudo()
Step = env['hb.onboarding.step'].sudo()

ref = lambda x: env.ref('hocba_employees.' + x)
T_LANG = ref('skill_type_chinese')
T_PEDA = ref('skill_type_pedagogy')
L_ADV = ref('skill_level_chinese_adv')
L_MID = ref('skill_level_chinese_mid')
L_CERT = ref('skill_level_pedagogy_cert')

# ── chứng chỉ ────────────────────────────────────────────────────────────
CERTS = [
    # code, skill xmlid, type, level, ngày cấp, hạn (None = vô hạn), đã xác minh
    ('HB.17', 'skill_hsk6', T_LANG, L_ADV, D(2019, 6, 15), None, True),
    ('HB.17', 'skill_pedagogy_univ', T_PEDA, L_CERT, D(2012, 6, 30), None, True),
    ('HB.18', 'skill_hsk6', T_LANG, L_ADV, D(2020, 12, 6), None, True),
    ('HB.18', 'skill_pedagogy_ctcsol', T_PEDA, L_CERT, D(2023, 9, 1), D(2026, 9, 1), True),
    ('HB.19', 'skill_hsk5', T_LANG, L_ADV, D(2021, 5, 9), None, True),
    ('HB.19', 'skill_pedagogy_nvsp', T_PEDA, L_CERT, D(2022, 8, 20), D(2026, 8, 20), True),
    ('HB.20', 'skill_hsk5', T_LANG, L_MID, D(2024, 11, 3), None, False),
    ('HB.21', 'skill_hsk5', T_LANG, L_ADV, D(2022, 4, 17), None, True),
    ('HB.21', 'skill_pedagogy_nvsp', T_PEDA, L_CERT, D(2021, 3, 12), D(2026, 6, 30), True),
    ('HB.25', 'skill_hsk4', T_LANG, L_MID, D(2023, 10, 22), None, True),
    ('HB.27', 'skill_hsk4', T_LANG, L_MID, D(2024, 6, 2), None, False),
    ('HB.29', 'skill_hskk_trung', T_LANG, L_MID, D(2023, 12, 10), D(2026, 12, 10), True),
]
for code, skill_x, stype, level, issued, expiry, verified in CERTS:
    e = emp(code)
    sk = ref(skill_x)
    if Skill.search_count([('employee_id', '=', e.id), ('skill_id', '=', sk.id)]):
        continue
    Skill.create({
        'employee_id': e.id, 'skill_type_id': stype.id, 'skill_id': sk.id,
        'skill_level_id': level.id, 'x_cert_date': issued,
        'x_cert_expiry': expiry, 'x_cert_verified': verified,
    })
say('chứng chỉ:', Skill.search_count([]))

# ── người phụ thuộc (giảm trừ gia cảnh) ──────────────────────────────────
DEPS = [
    ('HB.01', 'Nguyễn Hoàng Bảo', 'child', D(2015, 3, 2), D(2021, 1, 1)),
    ('HB.01', 'Nguyễn Hoàng Vy', 'child', D(2018, 9, 14), D(2021, 1, 1)),
    ('HB.02', 'Đỗ Minh Khang', 'child', D(2017, 5, 8), D(2021, 6, 1)),
    ('HB.04', 'Lê Văn Bảy', 'parent', D(1958, 2, 20), D(2022, 2, 7)),
    ('HB.06', 'Trần Gia Bảo', 'child', D(2019, 11, 30), D(2021, 8, 2)),
    ('HB.12', 'Lê Nhật Minh', 'child', D(2020, 4, 6), D(2022, 3, 1)),
    ('HB.17', 'Trần Bảo Ngọc', 'child', D(2016, 8, 25), D(2021, 10, 4)),
    ('HB.23', 'Vũ Đức Duy', 'child', D(2021, 1, 19), D(2022, 1, 10)),
    ('HB.26', 'Trịnh Thị Hoa', 'parent', D(1961, 7, 3), D(2023, 8, 7)),
]
for i, (code, name, rel, bday, start) in enumerate(DEPS, 1):
    e = emp(code)
    if Dep.search_count([('employee_id', '=', e.id), ('name', '=', name)]):
        continue
    Dep.create({'employee_id': e.id, 'name': name, 'relationship': rel,
                'birthday': bday, 'date_start': start,
                'national_id': '001206%06d' % i})
say('người phụ thuộc:', Dep.search_count([]))

# ── tài sản đang giữ (chỉ NV offline) ────────────────────────────────────
AT = {t.name: t for t in env['hocba.asset.type'].sudo().search([])}
KIT = ['Cây máy tính', 'Màn hình máy tính', 'Bàn phím', 'Chuột máy tính',
       'Ghế làm việc']
n_asset = 0
for e in env['hr.employee'].sudo().search([('x_work_form', '=', 'offline')]):
    idx = int((e.x_employee_code or 'HB.00').split('.')[-1])
    for k, tname in enumerate(KIT):
        t = AT.get(tname)
        if not t:
            continue
        code = 'HB-%s-%02d' % (t.code or tname[:3].upper(), idx)
        if Asset.search_count([('asset_code', '=', code)]):
            continue
        Asset.create({
            'employee_id': e.id, 'asset_type_id': t.id, 'asset_code': code,
            'condition_in': 'new' if idx % 3 else 'good',
            'grant_date': e.x_probation_start or D(2024, 1, 1),
        })
        n_asset += 1
say('tài sản cấp phát:', Asset.search_count([]), '(+%d)' % n_asset)

# ── quy trình nhận việc ──────────────────────────────────────────────────
# NV thử việc được gán template tự động lúc create; NV thực tập gán tay.
env['hb.onboarding.template'].sudo().action_assign_pending()
intern = emp('HB.16')
if not intern.x_onboarding_step_ids:
    intern._hocba_assign_onboarding(
        env['hb.onboarding.template'].sudo().search(
            [('name', 'ilike', 'văn phòng')], limit=1))

# Đẩy tiến độ theo thời gian đã trôi: NV vào lâu thì xong nhiều bước hơn.
PROGRESS = {'HB.20': 4, 'HB.09': 3, 'HB.05': 2, 'HB.16': 1}
for code, n_done in PROGRESS.items():
    e = emp(code)
    steps = e.x_onboarding_step_ids.sorted(lambda s: (s.sequence, s.id))
    done = 0
    for s in steps:
        if done >= n_done:
            break
        if s.state in ('done', 'skipped'):
            done += 1
            continue
        try:
            if s.step_type == 'evaluation':
                # 'pass' ở bước chốt sẽ lên chính thức → demo giữ 'extend'
                s.action_evaluate('extend' if s.pass_completes else 'pass',
                                  note='Đạt yêu cầu, tiếp tục theo dõi.')
            else:
                s.action_complete(note='Đã hoàn thành.')
            done += 1
        except Exception as ex:
            say('  bỏ qua bước %s/%s: %s' % (code, s.name, str(ex)[:70]))
            break
    say('%s — %s: %d/%d bước xong' % (
        code, e.name, len(e.x_onboarding_step_ids.filtered(
            lambda s: s.state == 'done')), len(e.x_onboarding_step_ids)))

env.cr.commit()
print('\nPHASE 2 XONG — %d chứng chỉ, %d người phụ thuộc, %d tài sản, %d bước nhận việc'
      % (Skill.search_count([]), Dep.search_count([]), Asset.search_count([]),
         Step.search_count([])))
