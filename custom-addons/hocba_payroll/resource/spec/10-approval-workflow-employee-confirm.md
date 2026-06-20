# 10 — Quy trình duyệt, Xác nhận của NV qua Email, & Lịch sử lương

> Yêu cầu khách:
> - HR tạo bảng lương → Quản lý xác nhận → gửi email kèm **link web** để giáo viên/NV xem
>   bảng lương (đã tính thuế, lương cuối) → NV xác nhận OK → **áp dụng**.
> - Xem **lịch sử thanh toán lương** theo từng tháng và từng người.

---

## 1. State machine bảng lương tháng (`hr.payslip.run`)

Thêm field `x_state` (ghi đè/bổ sung state OOTB):

```
draft ──(HR: Tính lương)──▶ computed
computed ──(Quản lý: Xác nhận)──▶ manager_approved
manager_approved ──(Gửi email phiếu)──▶ sent
sent ──(tất cả NV xác nhận)──▶ employees_confirmed
employees_confirmed ──(HR: Áp dụng/Khoá)──▶ applied
applied ──(Kế toán: xuất file CK + đánh dấu trả)──▶ paid
(bất kỳ → cancelled)
```

| State | Ai | Hành động | Ghi chú |
|---|---|---|---|
| `draft` | HR | tạo run, chọn kỳ + nhân sự | |
| `computed` | HR | nhấn **Tính lương** (import công + compute) | sinh payslip + lines |
| `manager_approved` | Quản lý | **Xác nhận** sau khi soát | nút "Quản lý xác nhận" |
| `sent` | HR/hệ thống | **Gửi email** phiếu lương kèm link | mỗi NV 1 token riêng |
| `employees_confirmed` | (tự động) | khi 100% NV bấm xác nhận trên web | có thể cho phép áp dụng sớm dù 1 số NV chưa xác nhận ❓ |
| `applied` | HR | **Áp dụng/Khoá** → số liệu chốt | không sửa được nữa |
| `paid` | Kế toán | xuất file CK (file 09), đánh dấu đã trả | gắn ngày trả |

> Mỗi `hr.payslip` con cũng có cờ xác nhận riêng:
> `x_employee_confirm_state` = `pending / confirmed / rejected` + `x_employee_confirm_date` + `x_employee_reject_note`.

---

## 2. Gửi email + Link web cho NV xem & xác nhận

### 2.1 Token truy cập an toàn
- Mỗi payslip sinh `access_token` (uuid4, lưu trên payslip). Link không cần đăng nhập:
  `https://<web>/payslip/view/<payslip_id>/<access_token>`
- Token chỉ mở đúng phiếu của NV đó. Có thể đặt hạn dùng (`x_token_expire`) ❓.
- (Tùy chọn) dùng cơ chế Portal của Odoo nếu NV có user portal; mặc định **token link** để giáo viên/CTV không cần tài khoản.

### 2.2 Email
- Template `mail.template` (QWeb), biến: tên NV, kỳ lương, NET, link.
- Tiêu đề: `[Học Bá] Phiếu lương T{MM}/{YYYY} — vui lòng kiểm tra & xác nhận`.
- Nội dung: tóm tắt NET + nút "Xem & xác nhận phiếu lương" (link mục 2.1).
- Gửi khi chuyển sang `sent`. Ghi log gửi (chatter) + `x_sent_date`.
- ❗ Giai đoạn BE: dựng **template + endpoint + token + state**; cấu hình SMTP có thể để sau (test bằng outgoing mail giả/log). Đánh dấu rõ phần SMTP là TODO khi go-live.

### 2.3 Trang web xem phiếu (BE cung cấp endpoint, FE render sau)
Controller Odoo (`http.Controller`, `auth='public'`):
- `GET /payslip/view/<id>/<token>` → trả JSON/HTML phiếu lương (các cột file 08) cho FE React.
- `POST /payslip/confirm/<id>/<token>` → set `x_employee_confirm_state=confirmed`, ghi thời điểm.
- `POST /payslip/reject/<id>/<token>` body `{note}` → set `rejected` + lưu ghi chú, thông báo HR.
- Validate token; chống xác nhận khi run chưa `sent` hoặc đã `applied`.

```python
# pseudo-controller
@http.route('/payslip/view/<int:pid>/<token>', auth='public', type='http')
def view(self, pid, token):
    slip = request.env['hr.payslip'].sudo().browse(pid)
    if not slip.exists() or slip.access_token != token:
        return request.not_found()
    # trả dữ liệu phiếu (file 08 columns) cho FE
    ...

@http.route('/payslip/confirm/<int:pid>/<token>', auth='public', type='json', methods=['POST'])
def confirm(self, pid, token):
    slip = request.env['hr.payslip'].sudo().browse(pid)
    if slip.access_token != token or slip.payslip_run_id.x_state != 'sent':
        return {'error': 'invalid'}
    slip.write({'x_employee_confirm_state':'confirmed',
                'x_employee_confirm_date': fields.Datetime.now()})
    slip.payslip_run_id._check_all_confirmed()   # nếu đủ → employees_confirmed
    return {'ok': True}
```

### 2.4 Theo dõi tiến độ xác nhận
- Trên `hr.payslip.run`: smart counter `Đã xác nhận: x/y`.
- Danh sách NV chưa xác nhận để HR nhắc lại (resend email).

---

## 3. Lịch sử thanh toán lương

### 3.1 Theo tháng
- `hr.payslip.run` chính là bản ghi theo tháng. List view: Kỳ, Số NV, Σ Gross, Σ NET, Trạng thái, Ngày trả.
- Filter theo năm/tháng; group theo trạng thái.
- Mở 1 run → xem toàn bộ phiếu + file Excel bảng lương (file 08) + file CK (file 09) đã đính kèm.

### 3.2 Theo từng người
- Trên hồ sơ NV: smart button "Lịch sử lương" → list các payslip của NV qua các tháng
  (Kỳ, NET, Trạng thái xác nhận, Ngày trả).
- Báo cáo "Bảng lương cá nhân" theo khoảng thời gian (từ tháng – đến tháng) → xuất PDF/Excel.

### 3.3 Model bổ sung (tracking)
Trên `hr.payslip`:
| Field | Type | |
|---|---|---|
| `x_paid_date` | Date | ngày chuyển khoản thực tế |
| `x_payment_ref` | Char | mã GD/bill (nhập tay hoặc từ file CK) |
| `x_payment_method` | Selection `[bank, cash]` | |
| `access_token` | Char | token link |
| `x_employee_confirm_state` | Selection | pending/confirmed/rejected |
| `x_employee_confirm_date` | Datetime | |

> Lịch sử = dữ liệu sẵn có (payslip + run) + view/report. Không cần model lịch sử riêng;
> đảm bảo **không xóa cứng** run đã `applied/paid`.

---

## 4. Phân quyền (groups) — sơ bộ

| Nhóm | Quyền |
|---|---|
| `HR Payroll Officer` | tạo/sửa run ở `draft/computed`, tính lương, gửi email |
| `Manager` (TBP/Quản lý) | xác nhận `computed → manager_approved` |
| `Accountant` | xuất file CK, đánh dấu `paid` |
| `Director` (Giám đốc) | xem tất cả, (tùy) duyệt cuối |
| `Employee/Public (token)` | chỉ xem & xác nhận phiếu của mình qua link |

> Ràng buộc state: chỉ đúng nhóm mới chuyển được state tương ứng (kiểm trong method, không chỉ UI).

---

## 5. Checklist BE giai đoạn này

- [ ] Field state + transition methods (mục 1) + ràng buộc nhóm.
- [ ] `access_token` + 3 controller public (view/confirm/reject).
- [ ] `mail.template` phiếu lương + action gửi (SMTP để TODO).
- [ ] Smart counter xác nhận + danh sách chưa xác nhận + resend.
- [ ] View lịch sử theo tháng (run) + theo người (smart button).
- [ ] Field paid_date/payment_ref/payment_method.
- [ ] Test: token sai → 404; xác nhận khi chưa `sent` → từ chối; đủ xác nhận → tự lên `employees_confirmed`.
