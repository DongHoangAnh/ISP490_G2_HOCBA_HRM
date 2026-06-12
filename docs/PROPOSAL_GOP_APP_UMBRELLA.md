# Đề xuất: Gộp các module thành MỘT app "Học Bá HRM"

> Tài liệu gửi team ISP490_G2 — đọc 5 phút. Trạng thái: **đề xuất, chờ team chốt**.
> Người soạn: Tân (Employees). Ngày: 12/06/2026.

## 1. Vấn đề hiện tại

Mỗi thành viên làm một module riêng, và mỗi module tự tạo **menu gốc riêng**.
Hậu quả trên giao diện: app switcher (menu 9 chấm) hiển thị rời rạc —
*Employees*, *Recruitment*, *Time Off*, *Payroll*, *HOCBA HRM*... như 5 phần mềm
khác nhau, trong khi đồ án của mình là **một hệ thống HRM thống nhất**.

```
HIỆN TẠI (app switcher)                 SAU KHI GỘP
┌──────────────────────┐               ┌──────────────────────────────┐
│ ▢ Employees          │               │ ▢ Học Bá HRM   (1 app duy nhất)
│ ▢ Recruitment        │               │   ├── Nhân viên      (Tân)   │
│ ▢ Time Off           │      ──►      │   ├── Chấm công  (Hoàng Anh) │
│ ▢ Payroll            │               │   ├── Tuyển dụng    (Việt)   │
│ ▢ HOCBA HRM          │               │   ├── Nghỉ phép  (Nhật Anh)  │
│ ▢ ...                │               │   ├── Lương         (Hùng)   │
└──────────────────────┘               │   └── Cấu hình               │
                                       └──────────────────────────────┘
```

## 2. Nguyên tắc quan trọng nhất: GỘP GIAO DIỆN, KHÔNG GỘP CODE

Hai chuyện hoàn toàn tách biệt nhau trong Odoo:

| | Code (module Python/XML) | Giao diện (menu/app) |
|---|---|---|
| Sau khi gộp | **Giữ nguyên** — ai làm module nấy, nhánh git riêng | Gom về 1 app gốc |
| Ai phải sửa | **Không ai cả** | Chỉ 1 module trung gian |

Trong Odoo, một "app" trên app switcher thực chất chỉ là một **menu gốc**
(bản ghi `ir.ui.menu` không có cha). Menu là dữ liệu, có thể đổi cha (re-parent)
từ một module khác — giống dời shortcut vào chung một thư mục, file gốc không
đổi chỗ.

## 3. Cách làm: module "ô dù" (umbrella)

Dùng module `hocba_hrm` (sẵn có) làm umbrella. Nó chỉ chứa 2 thứ:

**a) Depends tất cả module của team** → cài 1 module là kéo theo toàn bộ:

```python
# hocba_hrm/__manifest__.py
'depends': [
    'hocba_employees',    # Tân
    'hocba_attendance',   # Hoàng Anh
    'hocba_users',
    'hocba_tuyen_dung',   # Việt
    'hr_holidays_modern', # Nhật Anh
    # 'hocba_payroll',    # Hùng — thêm khi merge vào main
],
```

**b) Một menu gốc + các record re-parent menu của từng module:**

```xml
<!-- hocba_hrm/views/menu.xml -->
<!-- Menu gốc duy nhất = app "Học Bá HRM" -->
<menuitem id="menu_hocba_root" name="Học Bá HRM"
          web_icon="hocba_hrm,static/description/icon.png"
          sequence="1"/>

<!-- Dời app Employees của core vào làm menu con "Nhân viên" -->
<record id="hr.menu_hr_root" model="ir.ui.menu">
    <field name="name">Nhân viên</field>
    <field name="parent_id" ref="menu_hocba_root"/>
</record>

<!-- Tương tự với Recruitment, Time Off, menu gốc hocba_attendance... -->
<record id="hr_recruitment.menu_hr_recruitment_root" model="ir.ui.menu">
    <field name="name">Tuyển dụng</field>
    <field name="parent_id" ref="menu_hocba_root"/>
</record>
```

Mọi thay đổi nằm **gọn trong `hocba_hrm`** — không ai phải sửa module của mình.

## 4. Mỗi thành viên cần làm gì?

**Không cần làm gì với code hiện có.** Chỉ cần giữ 2 quy ước từ nay về sau:

1. **Không tự tạo thêm menu gốc mới** — menu mới thì treo vào menu gốc sẵn có
   của module mình (umbrella sẽ dời cả cụm).
2. **Không đổi `xml_id` của menu gốc** module mình mà không báo — umbrella
   re-parent theo `xml_id`, đổi tên là gãy.

## 5. Lợi ích cụ thể

- **Demo/bảo vệ đồ án**: mở 1 app duy nhất, điều hướng liền mạch — đúng hình
  ảnh "một hệ thống HRM" thay vì 5 module rời.
- **Cài đặt 1 lệnh**: `docker-compose` chỉ cần `--init=hocba_hrm`, không phải
  nối thêm tên module mỗi lần có người merge (hiện dòng `--init=` đã 2 lần
  conflict giữa các nhánh).
- **Không tăng rủi ro conflict git**: vì không ai sửa file của nhau; chỉ
  `hocba_hrm` thay đổi, và module đó do một người quản.

## 6. Lưu ý / đánh đổi (cần team biết trước khi đồng ý)

- Recruitment, Time Off... sẽ **biến mất khỏi app switcher dưới dạng app
  riêng** — chúng thành menu con trong "Học Bá HRM". Đây là chủ đích, nhưng
  ai đang quen mở app riêng sẽ thấy khác.
- Khi có **module mới**, phải thêm vào `depends` của umbrella (báo người quản
  `hocba_hrm`, hiện là Tân).
- Menu gốc cũ của từng module vẫn tồn tại trong db cũ — db nào cài trước khi
  gộp thì cần **upgrade `hocba_hrm`** (`-u hocba_hrm`) để menu được dời.

## 7. Thứ tự triển khai đề xuất

1. Tân commit phần đang làm dở + merge `origin/main` vào nhánh `Tan/Employee`.
2. Sửa `hocba_hrm` thành umbrella (manifest + menu.xml như trên), test trên
   db Docker `hocba_hrm`.
3. Mở PR cho cả team xem giao diện sau gộp trước khi merge vào `main`.
4. Hùng merge payroll vào main xong thì thêm `hocba_payroll` vào depends.

## 8. FAQ nhanh

**Hỏi: Gộp vậy có phải viết lại model/kế thừa gì không?**
Không. Model của ai giữ nguyên của người đó (kể cả `hocba.attendance` tự viết
của Hoàng Anh). Umbrella chỉ đụng tới menu.

**Hỏi: Điểm số/phân công có bị lẫn không?**
Không — git history và module vẫn tách bạch theo từng người, ai chấm phần nào
vẫn nhìn rõ.

**Hỏi: Lỡ muốn tách lại thì sao?**
Gỡ các record re-parent trong `hocba_hrm` là menu về chỗ cũ. Hoàn toàn đảo
ngược được.
