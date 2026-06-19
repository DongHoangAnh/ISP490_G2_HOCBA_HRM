# 09 — Quản lý Ngân hàng & Xuất file Chuyển khoản (MB BulkPayment)

> Nguồn: `eMB_BulkPayment_-_Copy.xlsx` (3 sheet: template giao dịch, hướng dẫn, danh sách 174 ngân hàng).
> Yêu cầu khách: (a) quản lý ngân hàng CRUD; (b) xuất file lô lương **lọc theo từng ngân hàng từ trên xuống**.

---

## 1. Quản lý Ngân hàng (CRUD)

### Model `hocba.bank` (hoặc mở rộng `res.bank`)
| Field | Type | Ghi chú |
|---|---|---|
| `name` | Char | Tên ngắn hiển thị nội bộ (vd "Techcombank", "MB Bank") |
| `mb_full_name` | Char | **Tên đầy đủ theo chuẩn MB** (cột D file chuyển khoản), vd `TCB - Ngan hang TMCP Ky Thuong Viet Nam` |
| `short_code` | Char | Mã ngắn (TCB, MB, VCB, BIDV, VIETINBANK…) |
| `transfer_type` | Selection | `mb_internal` / `normal` / `fast_247` (xem mục 2) |
| `active` | Boolean | cho phép "xóa mềm" |

- **Seed dữ liệu**: import 174 dòng từ sheet "Danh sách ngân hàng - Bank list" (cột B = `mb_full_name`, cột C = `transfer_type`).
- CRUD đầy đủ qua UI (list + form). Xóa = set `active=False` (an toàn, tránh mất tham chiếu lịch sử).
- Tài khoản NV (`res.partner.bank`) gắn `bank_id` trỏ tới `hocba.bank` → khi xuất file lấy `mb_full_name`.

### Map `transfer_type` (từ cột C bank list)
| Giá trị Excel | Code |
|---|---|
| CHUYỂN KHOẢN TRONG MB | `mb_internal` |
| CHUYỂN KHOẢN THƯỜNG | `normal` |
| Chuyển khoản NHANH liên ngân hàng 24/7… | `fast_247` |

---

## 2. Format file MB BulkPayment (sheet `eMB_BulkPayment`)

Header thật ở **row 2** (row 1 là tiêu đề "DANH SÁCH GIAO DỊCH"). Dữ liệu từ **row 3**.

| Cột | Tiêu đề (song ngữ) | Nguồn | Ràng buộc MB |
|---|---|---|---|
| A | STT (Ord. No.) | số thứ tự | chỉ số 0-9 |
| B | Số tài khoản (Account No.) | `res.partner.bank.acc_number` | chỉ [0-9A-Z], ≤24 ký tự, **không khoảng trắng** |
| C | Tên đơn vị thụ hưởng (Beneficiary) | `employee.name` | ≤69 ký tự (gồm space) |
| D | Ngân hàng thụ hưởng/Chi nhánh | `bank.mb_full_name` | copy đúng tên đầy đủ |
| E | Số tiền (Amount) | `payslip NET` (Y) | số VND, **không thập phân** |
| F | Chi tiết thanh toán (Payment Detail) | `Hoc Ba thanh toan luong T{MM}-{YYYY}` | ≤140 ký tự, **không dấu** |

> Số giao dịch tối thiểu 2, tối đa 40.000. Bỏ khoảng trắng trong số TK trước khi ghi
> (vd `1903 8175 4050 11` → `190381754050 11`? → **xóa hết space** → `19038175405011`).

---

## 3. Quy tắc làm sạch ký tự (BẮT BUỘC áp dụng khi xuất)

MB tự thay thế nếu không làm; ta nên làm trước để file sạch.

### 3.1 Cột "Số tài khoản" & "Tên đơn vị thụ hưởng"
| Ký tự | Thay bằng |
|---|---|
| `&` | `VA` |
| `! @ # ^ * - _ + \ \| ` ~ , / ? ; : " ' % = € £ $` | `.` |
| `( ) [ ] { } < >` | (xóa) |
| Ký tự khác ngoài `[A-Za-z0-9]` và các nhóm trên | (xóa) |

> Số TK: ngoài ra **xóa toàn bộ khoảng trắng**.

### 3.2 Cột "Chi tiết thanh toán"
| Ký tự | Thay bằng |
|---|---|
| `&` | `VA` |
| `( ) [ ] { } < >` | (xóa) |
| `! @ # ^ * - _ + \ \| ` ~ , / ? ; : " '` | `.` |
| `%` | `PT` |
| `=` | `BANG` |
| `€` | `EURO` |
| `£` | `BANG ANH` |
| `$` | `DO LA MY` |

### 3.3 Bỏ dấu tiếng Việt cho "Chi tiết thanh toán"
Mặc định "Hoc Ba thanh toan luong T05-2026" — sinh bằng cách bỏ dấu (unidecode/unicodedata NFD + strip combining).
> ❓ Tên thụ hưởng (cột C) giữ dấu tiếng Việt (như demo `Nguyễn Trung Kiên`) hay bỏ dấu?
> Demo giữ dấu → mặc định **giữ dấu** cho cột C. Riêng "chuyển khoản trong MB" không cho `~ ! # " |`.

```python
import unicodedata, re
def strip_accents(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ','d').replace('Đ','D')

def clean_acc(s):              # số tài khoản
    return re.sub(r'\s+','', str(s))

def clean_detail(month, year):
    return strip_accents(f"Hoc Ba thanh toan luong T{month:02d}-{year}")
```

---

## 4. Yêu cầu: lọc/nhóm theo từng ngân hàng

> "danh sách sẽ là lọc theo từng ngân hàng từ trên xuống"

Khi xuất file lô lương, **sắp xếp các giao dịch gom theo ngân hàng** (group by `bank.short_code`),
trong mỗi nhóm sắp theo STT/tên. Hai phương án (chọn theo khách):

- **PA1 (khuyến nghị)**: 1 file Excel, các dòng được **sort gộp theo ngân hàng** (MB trước, rồi TCB, VCB, BIDV, VietinBank…). STT đánh lại liên tục 1..n.
- **PA2**: mỗi ngân hàng **một file riêng** (hoặc một sheet riêng) — tiện up từng lô theo bank. Tên file `eMB_BulkPayment_{BANK}_{T-MM-YYYY}.xlsx`.

> ❓ Khách chọn PA1 hay PA2. MB upload 1 file lô cho mọi ngân hàng được (chuyển liên NH), nên PA1 đủ;
> nhưng nếu khách quen up từng bank thì PA2.

---

## 5. Spec hàm xuất (gợi ý)

```
Action "Xuất file chuyển khoản (MB)" trên hr.payslip.run:
1. Lấy các payslip trạng thái đã duyệt + NET > 0 + NV có payment_method = bank.
2. Bỏ NV trả tiền mặt (đưa vào báo cáo riêng).
3. Với mỗi payslip → 1 dòng: acc_number(clean), name, bank.mb_full_name, round(NET), detail.
4. Sort theo bank.short_code rồi STT.
5. Ghi openpyxl theo layout mục 2 (row1 tiêu đề, row2 header, data từ row3).
6. (PA2) nếu chọn tách: tạo nhiều sheet/file theo bank.
7. Validate: ≥2 dòng, ≤40.000, mọi NET là số nguyên, số TK ≤24 ký tự không space.
```

- Đối chiếu tổng: Σ cột E (Amount) phải khớp Σ NET (qua bank) trong bảng lương (file 08, dòng "Trả qua MB").
- Lưu file vào `ir.attachment` gắn với payslip.run để tra lại lịch sử (liên quan file 10).

---

## 6. Liên kết NET ↔ Bulk

Số tiền cột E = `Y` (Tổng lương thực lĩnh) của phiếu lương tháng đó (file 08 mục 3.5).
Ví dụ thực tế trong file demo bulk (T5-2026): Nguyễn Trung Kiên 24.141.825, Phùng Minh Anh 26.098.819…
(số của tháng 5 thực tế, khác demo BL4 vì khác kỳ — chỉ minh hoạ format).
