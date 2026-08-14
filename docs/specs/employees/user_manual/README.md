# User manual — module Employee

Thư mục **nguồn** để dựng lại bản hướng dẫn sử dụng module Employee, viết theo
đúng khuôn `ISP490_G2_User_manual_Recruitment_v1.0.docx` của Việt.

- Thành phẩm: [`out/ISP490_G2_User_manual_Employee_v1.0.docx`](out/) — 31 trang,
  31 hình chụp từ app thật.
- Spec: `docs/superpowers/specs/2026-08-14-user-manual-employees-design.md`
- Đối chiếu nghiệp vụ: 13 FS tại `../fs/out/`

## Dựng lại

```bash
cd docs/specs/employees/user_manual
python build.py                      # nội dung + ảnh → out/*.docx
powershell -NoProfile -File finish_word.ps1   # mở bằng Word dựng sẵn mục lục
```

Bỏ qua bước Word cũng được — khi đó người đọc phải bấm chuột phải vào mục lục
rồi chọn **Update Field**.

## Chụp lại ảnh

App phải đang chạy. Stack Neon (mặc định):

```bash
docker compose -f docker-compose.yml -f docker-compose.onl.yml up -d odoo
```

→ `http://localhost:8070` (file `docker-compose.yml` **không** publish cổng,
phải kèm override `onl` hoặc `local`).

```bash
python shots_all.py            # chụp cả 31 hình
python shots_all.py fig-14 fig-15   # chụp lại vài hình
```

Đổi cổng bằng biến môi trường `HB_BASE`. Tài khoản dùng để chụp: HR Manager
(`test_hrmanager@hocba.vn`) cho hình 1–27, nhân viên thường
(`test_employee@hocba.vn`) cho hình 28–31 — mật khẩu chung, xem
`docs/DB_TEST_DATA.md`.

## Cách hoạt động

| File | Vai trò |
|---|---|
| `gen_um_docx.py` | Mở `donor/UM-REC-v1.0.docx` lấy nguyên styles / numbering / theme / header-footer + **bảng mẫu**, xoá sạch body rồi dựng lại. Nhờ vậy hai user manual của nhóm giống hệt nhau về font, tiêu đề, kiểu bảng, chú thích hình. |
| `build.py` | Toàn bộ nội dung tài liệu + thứ tự hình. |
| `shots.py` | Khung Selenium: đăng nhập, bấm sidebar, đóng modal (phím Escape), chụp. |
| `shots_all.py` | Kịch bản 31 hình, mỗi hình bọc try/except, cuối lượt in hình lỗi. |
| `finish_word.ps1` | Word COM: dựng mục lục thật rồi lưu lại (`-AsPdf` để xuất PDF). |

## Lưu ý

- Mục lục dựng **field TOC mới** chứ không chép field của donor — chép sẽ mang
  theo mục lục cache của module Tuyển dụng.
- Ảnh của donor bị gỡ khỏi package sau khi dựng (`drop_unused_images`), nếu
  không file gánh thêm ~4.7MB ảnh chết.
- `finish_word.ps1 -AsPdf` hay **treo** ở bước xuất PDF khi Word chạy ẩn; nếu
  gặp thì bỏ `-AsPdf`, mở file bằng Word rồi Save as PDF bằng tay.
- Hình chụp dữ liệu thật trên Neon: nếu seed đổi, các mã dùng trong
  `shots_all.py` (`HB.01`, `HB.02`, `HB.04`, `hà phi hùng`) có thể phải chọn
  lại cho khớp (cần NV có người phụ thuộc / chứng chỉ / tài sản / thăng tiến và
  một NV đang dở quy trình thử việc).
