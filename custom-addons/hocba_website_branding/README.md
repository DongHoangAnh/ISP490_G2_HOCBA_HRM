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

Stack nginx (`docker-compose.nginx.yml`) **cố tình không chạy `--init/--update` lúc khởi động**
để không đụng schema DB production (commit `f170ac6`), nên cài module là một **thao tác bảo trì
riêng**, chạy tay khi đã thống nhất với nhóm:

```bash
docker compose -f docker-compose.nginx.yml run --rm --no-deps --entrypoint bash odoo -lc 'odoo -d "$DB_NAME" -i hocba_website_branding --db_host="$HOST" --db_port="$PORT" --db_user="$USER" --db_password="$PASSWORD" --db_sslmode=prefer --addons-path=/mnt/extra-addons --stop-after-init'
```

(Nháy đơn để **container** giãn biến chứ không phải shell ở máy bạn: `HOST/PORT/USER/PASSWORD/DB_NAME`
do khối `environment:` trong compose bơm vào từ `.env`. Phải ghi rõ `--db_*` vì từ `f170ac6` thông tin
kết nối không còn nằm trong `odoo.local.conf` mà được truyền qua `command:`, mà `run` thì thay luôn
`command:` đó.)

Sau đó **BẮT BUỘC restart container** — không chỉ để xoá cache view mà vì Odoo chỉ dựng lại
bundle JS/CSS khi khởi động lại; thiếu bước này thì `apply_form_cv_required.js` không nằm trong
bundle và ô CV vẫn không bắt buộc (đã gặp đúng lỗi này lúc kiểm thử):

```bash
docker compose -f docker-compose.nginx.yml restart odoo
```

Lần sau sửa file trong module thì thay `-i` bằng `-u hocba_website_branding`, rồi restart y hệt.

⚠️ Hệ quả chung của `f170ac6` (không riêng module này): dựng lại container **không còn tự cập nhật
module nào cả**. Deploy code mới mà quên `-u` thì DB và code lệch nhau — sửa Python thì restart là
đủ, nhưng thêm field/bảng, sửa view XML, security hay data đều phải `-u` mới vào DB.

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
  trực tiếp trong DB. Đổi lại, stack nginx nay chạy không có `--dev=xml`: sửa file xong phải
  `-u hocba_website_branding` rồi restart mới thấy, restart suông là chưa đủ.
- Ô CV bắt buộc được làm bằng **JS vá interaction của Odoo**, không phải `required` trong XML —
  lý do chi tiết ghi trong comment ở `views/recruitment_branding_templates.xml` và trong file JS.
  Kiểm thử đã xác nhận: gửi thiếu CV bị chặn ngay trên ô CV, gửi kèm CV vẫn tạo được ứng viên
  với tệp đính kèm.
- Nếu ai đó sửa các trang này bằng trình soạn website, Odoo tạo bản COW trong DB và bản COW
  đó **đè lên** module. Muốn quay về bản chuẩn thì xoá view COW tương ứng
  (`ir_ui_view` có `website_id` khác NULL).
