"""Thử việc văn phòng: phải Đạt CẢ tháng-2 mới lên chính thức.

Chốt với khách 2026-08-27. Trước bản này template khai:
  - Đánh giá tháng-1: pass_completes = True  → Đạt là lên chính thức luôn
  - Đánh giá tháng-2: is_extension  = True   → bị _advance() bỏ qua mỗi khi
    tháng-1 Đạt (bước gia hạn chỉ mở khi bước trước cho kết quả Gia hạn)
nên trên thực tế KHÔNG AI đi qua tháng-2: cứ Đạt tháng-1 là xong thử việc.

Template seed nằm trong khối noupdate="1" (admin sửa được trong app, upgrade
không đè) → đổi file XML thôi không tới được DB đang chạy, phải vá bằng
migration. Đây đúng là cái bẫy đã làm migration 19.0.4.0.0 vá trượt trước đây.

Bản ghi bước của NV là SNAPSHOT chụp lúc gán, cố ý miễn nhiễm với sửa template
sau đó. Lần này ta CỐ Ý phá lệ đó — nhưng chỉ với hai bước nói trên và chỉ khi
bước còn 'waiting'/'open': bước đã done/skipped là lịch sử của một luật cũ, sửa
nó là nói dối về chuyện đã xảy ra. Hệ quả: NV đang thử việc dở sẽ phải qua nốt
tháng-2, đúng ý khách.
"""

# (module, xmlid, cột, giá trị mới) — vá theo xmlid chứ không theo tên bước:
# tên là chuỗi người dùng sửa được, xmlid thì không.
FIXES = [
    ('onb_tpl_vp_step3', 'pass_completes'),
    ('onb_tpl_vp_step4', 'is_extension'),
]


def migrate(cr, version):
    if not version:
        return
    for xmlid, column in FIXES:
        # 1) Bước MẪU trong template
        cr.execute("""
            UPDATE hb_onboarding_template_step ts
            SET {col} = FALSE
            FROM ir_model_data d
            WHERE d.module = 'hocba_employees'
              AND d.name = %s
              AND d.model = 'hb.onboarding.template.step'
              AND d.res_id = ts.id
        """.format(col=column), (xmlid,))
        # 2) Bản snapshot CHƯA XONG của NV đang chạy quy trình đó
        cr.execute("""
            UPDATE hb_onboarding_step s
            SET {col} = FALSE
            FROM ir_model_data d
            JOIN hb_onboarding_template_step ts ON ts.id = d.res_id
            WHERE d.module = 'hocba_employees'
              AND d.name = %s
              AND d.model = 'hb.onboarding.template.step'
              AND s.template_id = ts.template_id
              AND s.name = ts.name
              AND s.state IN ('waiting', 'open')
        """.format(col=column), (xmlid,))
