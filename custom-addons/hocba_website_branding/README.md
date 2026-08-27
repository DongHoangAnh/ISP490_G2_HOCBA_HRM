# hocba_website_branding

Branding **website công khai** của Học Bá (trang `/jobs`, header, footer) dưới dạng **code**.

## Vì sao có module này

Phần rebrand làm ngày 05/07/2026 được thực hiện bằng **trình soạn website của Odoo**, nên nó
chỉ tồn tại dưới dạng dữ liệu trong đúng một DB (`neondb`): 96 bản view riêng của site trong
`ir_ui_view`, cộng vài trường trên `website` và `res_company`. Không có dòng nào trong repo.

Khi hệ thống chuyển sang DB mới (`hocba_hrm` của stack `docker-compose.nginx.yml`, dựng bằng
`--init`), toàn bộ branding biến mất và Odoo trả về bộ mặc định: *My Website* / *Your Logo* /
*+1 555-555-5556* / nút *Apply Now!* màu tím / footer *yourcompany.example.com*.

Khối "Thông tin tuyển dụng / Yêu cầu ứng viên" trên trang tin **không** bị ảnh hưởng vì nó
đến từ code của `hocba_recruitments`. Module này làm điều tương tự cho phần branding.

## Gồm những gì

| Thành phần | Nơi khai báo |
|---|---|
| Tên công ty, điện thoại, email (hiện ở header/footer/copyright) | `data/branding_data.xml` — `base.main_company` |
| Tên website, link Facebook / YouTube / Instagram / TikTok | `data/branding_data.xml` — `website.default_website` |
| Footer đỏ Học Bá: logo + tagline, bản đồ, liên hệ, cột link, MST | `views/website_branding_templates.xml` — `hb_website_footer` |
| Điện thoại/email trên header (thay số demo của Odoo) | `views/website_branding_templates.xml` — `hb_header_text_element` |
| Ẩn "Powered by Odoo" | `views/website_branding_templates.xml` — `hb_hide_brand_promotion` |
| Nút "Ứng tuyển" ở trang chi tiết tin | `views/recruitment_branding_templates.xml` — `hb_job_detail` |
| Form nộp hồ sơ: bỏ ô LinkedIn, nhãn tiếng Việt, nút "Nộp hồ sơ" | `views/recruitment_branding_templates.xml` — `hb_job_apply` |
| Bắt buộc nộp CV (vá interaction JS của Odoo) | `static/src/js/apply_form_cv_required.js` |
| Cột phải trang `/jobs`: giới thiệu + liên hệ Học Bá | `views/recruitment_branding_templates.xml` — `hb_job_right_side_bar` |
| Màu thương hiệu #8E0F12 cho `.btn-primary`, CSS footer | `static/src/scss/branding.scss` |
| Logo website + logo công ty | `hooks.py` (ảnh nhị phân, phải ghi bằng code) |
| Cài `vi_VN` và đặt làm ngôn ngữ **duy nhất** của website | `hooks.py` |

**Không** gồm (bản trên Neon có nhưng không liên quan tuyển dụng): trang `/contactus`,
`contactus_thanks` và mấy snippet mẫu (`s_accordion`, `s_contact_info`, `s_opening_hours`,
`s_website_form`) — ở đó bản Neon chỉ thay mỗi email demo. Nếu cần thì thêm sau.

## Cài / cập nhật

Stack nginx (`docker-compose.nginx.yml`) có `hocba_website_branding` trong cả
`--init` và `--update`, vì vậy module được cài/cập nhật tự động khi nhóm
build lại stack:

```bash
docker compose -f docker-compose.nginx.yml up -d --build
```

Lệnh trên recreate container, nạp lại view và dựng bundle JS/CSS của module.

## Lưu ý

- Lần cài đầu chạy `post_init_hook`: nạp bản dịch `vi_VN` (hơi lâu, ~1–2 phút) và ghi logo.
  Xem log có dòng `Logo website: … byte` — nếu ra `KHÔNG thành công` thì cài lại; field Binary
  của Odoo từng có tiền lệ ghi xong mà không nằm lại trong DB.
- `data/branding_data.xml` đặt `noupdate="1"`: chỉ áp lúc **cài**. Ai sửa tên/điện thoại công ty
  trong giao diện thì lần `-u` sau không bị ghi đè ngược.
- DB `hocba_hrm` hiện có sẵn công ty id 2 tên *Học Bá Education*. Module đổi tên công ty id 1
  (`base.main_company`, công ty của website) thành *Học Bá Education* → sẽ có **hai công ty
  trùng tên**. Đó là chuyện tồn đọng của DB đó, cần dọn riêng.
- View của module nằm trong file XML nên **không dính bẫy `arch_updated`** như hồi sửa view
  trực tiếp trong DB. Stack nginx tự chạy `--update=hocba_website_branding`
  khi recreate, nên thay đổi XML/JS/CSS được nạp trong luồng deploy chung.
- Ô CV bắt buộc được làm bằng **JS vá interaction của Odoo**, không phải `required` trong XML —
  lý do chi tiết ghi trong comment ở `views/recruitment_branding_templates.xml` và trong file JS.
  Kiểm thử đã xác nhận: gửi thiếu CV bị chặn ngay trên ô CV, gửi kèm CV vẫn tạo được ứng viên
  với tệp đính kèm.
- Nếu ai đó sửa các trang này bằng trình soạn website, Odoo tạo bản COW trong DB và bản COW
  đó **đè lên** module. Muốn quay về bản chuẩn thì xoá view COW tương ứng
  (`ir_ui_view` có `website_id` khác NULL).
