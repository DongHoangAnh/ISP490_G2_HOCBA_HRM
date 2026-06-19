# 11 — Cấu hình Mã phí theo Vai trò & Tổng hợp lương từ Chấm công

> Yêu cầu khách:
> - Config được các **mã phí** (thuế, %, BH…) — thêm/sửa/xóa — và **tùy vai trò**:
>   NV chính thức thu thuế/BH; CTV / giáo viên online / giáo viên offline có **mã tính khác**.
> - Người khác làm **chấm công** (công, OT, nghỉ phép, nghỉ không lương) → payroll **nhân lương/hệ số/chi phí với công** → ra lương tháng.

---

## 1. "Mã phí" cấu hình được = Salary Rules (CRUD qua UI)

Tận dụng `hr.salary.rule` (OCA payroll). Mỗi "mã phí" = 1 salary rule:

| Field | Ý nghĩa |
|---|---|
| `code` | Mã (vd `BHXH_NV`, `TNCN`, `AN_CA`, `HOA_HONG`, `PC_XANG`) |
| `category_id` | Nhóm (BASIC/ALW/DED/TAX/NET…) |
| `amount_select` | `fix` (số cố định) / `percentage` (%) / `code` (python) |
| `amount_percentage` + `amount_percentage_base` | cho loại % (vd 8% trên `contract.wage`) |
| `amount_python_compute` | cho loại công thức |
| `condition_select` + `condition_python` | điều kiện áp dụng (vd chỉ NV offline) |
| `appears_on_payslip`, `sequence`, `active` | hiển thị, thứ tự, bật/tắt |

→ **Thêm/sửa/xóa mã phí** = thêm/sửa/(vô hiệu hoá) salary rule trong UI. Quản trị tự cấu hình %, base, điều kiện.
> Khuyến nghị: xóa = `active=False` để giữ lịch sử phiếu đã tính.

### Màn hình quản trị (BE cung cấp model+view; FE sau)
- Danh mục **Nhóm mã phí** (`hr.salary.rule.category`): CRUD.
- Danh mục **Mã phí** (`hr.salary.rule`): CRUD + test thử trên 1 NV mẫu.
- Danh mục **Cấu trúc lương** (`hr.payroll.structure`): gom các mã phí theo vai trò.

---

## 2. Cấu trúc lương theo Vai trò (Salary Structure per role)

Mỗi vai trò có một bộ mã phí khác nhau. Tạo nhiều `hr.payroll.structure`:

| Structure | Áp dụng cho | Mã phí gồm |
|---|---|---|
| `STRUCT_STAFF` (NV chính thức) | offline, official/probation | Lương TG, Phụ cấp, Ăn ca, **BHXH/BHYT/BHTN NV+CT**, **TNCN**, NET (file 08) |
| `STRUCT_SALE` (NV sale) | staff + có doanh thu | như STAFF + **HOA_HONG** (file 04) |
| `STRUCT_CTV` (cộng tác viên) | online/parttime | Lương + Thưởng − Tạm ứng (file 04 §4); **không BH**; thuế ❓ (vãng lai 10%?) |
| `STRUCT_TEACHER_ON` (GV online) | giáo viên online | theo buổi/giờ dạy × đơn giá; mã phí riêng ❓ |
| `STRUCT_TEACHER_OFF` (GV offline) | giáo viên offline | theo buổi dạy × đơn giá + phụ cấp ❓ |

### Gán structure cho NV
- `hr.contract.structure_type_id` / `struct_id` chọn structure theo vai trò.
- Tự suy luận mặc định theo `x_work_form` + `x_position_type` + `job_id`; cho phép override.

> ❓ **Cần khách cung cấp công thức GV online/offline & CTV**: đơn giá theo buổi/giờ? có thuế vãng lai 10%
> với thu nhập ≥ 2.000.000/lần chi cho cá nhân không ký HĐ ≥3 tháng (TT111)? → tạo mã `TNCN_VANGLAI` (10%) bật theo điều kiện.
> Hiện dữ liệu `5_2` (online) chưa có thuế → mặc định CTV/online **chưa khấu thuế**, chờ khách xác nhận.

### Thuế vãng lai (chuẩn bị sẵn mã phí)
```python
# Rule TNCN_VANGLAI (điều kiện: hợp đồng < 3 tháng / CTV, mỗi lần chi >= 2.000.000)
gross = categories.GROSS
result = -round(gross * 0.10) if gross >= 2_000_000 else 0.0
```
→ Bật/tắt bằng `condition_python` theo loại NV. Cho khách tự config %.

---

## 3. Tổng hợp lương từ Chấm công

### 3.1 Luồng
```
[Bộ phận chấm công] → bảng công tháng (Công, OT, Nghỉ phép, Nghỉ không lương)
        │  (import/đẩy sang payroll)
        ▼
[Payroll] gắn vào hr.payslip.worked_days → Tính lương (compute) → lương tháng
```

### 3.2 Dữ liệu công đầu vào (per NV/tháng)
| Loại | work_entry code | Vai trò trong công thức (file 08) |
|---|---|---|
| Công thực tế (NCTT) | `WORK100` | `actual_days` |
| Ngày nghỉ tính lương (phép có lương) | `LEAVE_PAID` | cộng vào "Công" hưởng lương |
| Tăng ca (OT) | `OT` | quy đổi ra ngày/giờ, cộng "Công" |
| Nghỉ không lương | `LEAVE_UNPAID` | KHÔNG tính công |
| Ngày lễ | `HOLIDAY` | tính công nếu có lương |
| Công chuẩn của tháng | `STD_DAYS`/`G6` | mẫu số proration |

> **Công (G, file 08)** = NCTT + nghỉ có lương + OT(quy đổi). **Hệ số công** = Công / Công chuẩn.
> Lương tháng = (Lương CB + phụ cấp) × hệ số công (đã chi tiết file 08 §3).

### 3.3 Cách nhận công (giai đoạn này)
- **Import Excel/TSV bảng công** (cột: Mã NV, tháng, năm, NCTT, nghỉ phép có lương, OT, nghỉ không lương).
- Hàm `action_import_attendance(run, file)` → tạo/cập nhật `worked_days` cho từng payslip.
- Hoặc API `POST /payroll/attendance/import` cho hệ thống chấm công đẩy sang (JSON).
- (Tương lai) tích hợp trực tiếp Lark Attendance_Result / máy chấm công — **ngoài scope hiện tại**.

### 3.4 Nút "Tính lương" trên run
```
action_compute(run):
  for payslip in run.slip_ids:
      payslip._onchange_worked_days()      # nạp công đã import
      payslip.compute_sheet()              # chạy mã phí theo struct của NV
  run.x_state = 'computed'
```

---

## 4. Quan hệ với các file khác

- Công thức từng mã phí: **file 04** (sale) + **file 08** (NV thường, format chuẩn) + **file 05** (BH/thuế).
- Sau khi compute → xuất **bảng lương** (file 08 §5) + **file CK** (file 09).
- State/duyệt/email/lịch sử: **file 10**.

---

## 5. Checklist BE giai đoạn này

- [ ] Cho phép CRUD salary rule category + salary rule + structure qua UI (có sẵn ở OCA payroll, kiểm tra menu).
- [ ] Tạo 5 structure theo vai trò (STAFF/SALE/CTV/TEACHER_ON/TEACHER_OFF) — STAFF & SALE & CTV làm trước (đủ dữ liệu), TEACHER chờ công thức khách.
- [ ] Rule `TNCN_VANGLAI` 10% (tắt mặc định, bật theo điều kiện).
- [ ] Logic gán structure tự động theo work_form + position + job.
- [ ] Import bảng công (Excel) + API nhận công (JSON).
- [ ] Nút "Tính lương" trên run → compute toàn bộ.
- [ ] Test: đổi % của 1 mã phí (vd BHXH 8%→9%) → phiếu tính lại đúng; tắt 1 mã → biến mất khỏi phiếu.
