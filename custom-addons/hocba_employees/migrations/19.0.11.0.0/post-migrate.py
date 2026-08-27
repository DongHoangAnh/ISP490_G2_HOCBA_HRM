"""Thử việc văn phòng: Đạt tháng-2 KHÔNG tự lên chính thức nữa.

Chốt với khách 2026-08-27 (bản 2 của cùng ngày). Bước "Đánh giá tháng-2" khai
`pass_completes = True` nên Đạt là NV lên official ngay, HR không có chỗ nào
soát lại — nút "Chuyển chính thức" (đường duy nhất của quy trình Giáo viên)
vì thế không bao giờ hiện ra với nhân viên văn phòng. Bỏ cờ đó đi thì chuỗi
chạy hết bước rồi dừng, `_advance()` bắn chuông "chờ HR quyết định", HR bấm
nút mới chốt biên chế — hai quy trình về chung một lối.

Seed nằm trong khối noupdate="1" (admin sửa được trong app, upgrade không đè)
→ sửa file XML thôi không tới được DB đang chạy, phải vá bằng migration. Cùng
cái bẫy mà 19.0.4.0.0 và 19.0.10.0.0 đã ghi lại.

Bản ghi bước của NV là SNAPSHOT chụp lúc gán, cố ý miễn nhiễm với sửa template
sau đó. Ở đây ta CỐ Ý phá lệ đó — nhưng chỉ với bước nói trên và chỉ khi nó
còn 'waiting'/'open': bước đã done/skipped là lịch sử của một luật cũ, sửa nó
là nói dối về chuyện đã xảy ra (và NV đã lên official theo luật cũ thì cứ để
yên, không ai bị hạ xuống thử việc lại).
"""

XMLID = 'onb_tpl_vp_step4'  # Đánh giá tháng-2 của "Thử việc NV văn phòng"


def migrate(cr, version):
    if not version:
        return
    # 1) Bước MẪU trong template — vá theo xmlid chứ không theo tên bước:
    #    tên là chuỗi người dùng sửa được, xmlid thì không.
    cr.execute("""
        UPDATE hb_onboarding_template_step ts
        SET pass_completes = FALSE
        FROM ir_model_data d
        WHERE d.module = 'hocba_employees'
          AND d.name = %s
          AND d.model = 'hb.onboarding.template.step'
          AND d.res_id = ts.id
    """, (XMLID,))
    # 2) Bản snapshot CHƯA XONG của NV đang chạy quy trình đó
    cr.execute("""
        UPDATE hb_onboarding_step s
        SET pass_completes = FALSE
        FROM ir_model_data d
        JOIN hb_onboarding_template_step ts ON ts.id = d.res_id
        WHERE d.module = 'hocba_employees'
          AND d.name = %s
          AND d.model = 'hb.onboarding.template.step'
          AND s.template_id = ts.template_id
          AND s.name = ts.name
          AND s.state IN ('waiting', 'open')
    """, (XMLID,))
