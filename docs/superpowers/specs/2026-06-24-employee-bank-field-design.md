# Spec — Field "Ngân hàng nhận lương" trên hồ sơ nhân viên

- **Ngày:** 2026-06-24
- **Owner:** Tân (nhánh `Tan/Employee`)
- **Đề xuất bởi:** Hùng (module payroll)
- **Module ảnh hưởng:** `hocba_employees` (model), `hocba_hrm` (API + SPA glue), `frontend/` (form)

## 1. Bối cảnh & vấn đề

Hồ sơ nhân viên hiện **không** có thông tin ngân hàng nhận lương. Khi nhập tay tên ngân hàng,
dữ liệu không đồng nhất ("vcb" vs "Vietcombank" vs "VietComBank") → khó lọc/gộp, dễ sai khi
đối chiếu chi lương.

Payroll đã có sẵn danh sách ngân hàng được cấu hình ở **Bảng lương → Cấu hình → Ngân hàng**
(model `hb.bank.format`, vd VCB / TCB). Tận dụng danh sách này làm nguồn cho một dropdown
trên form nhân viên để **chuẩn hoá** giá trị ngân hàng.

### Phân biệt quan trọng
`hb.bank.format` là danh sách **định dạng file xuất** cho từng ngân hàng (formatter, encoding,
regex STK), do wizard sinh file chuyển khoản dùng. Nó **không** phải master ngân hàng đầy đủ
của Odoo (`res.bank`). Ta cố tình dùng danh sách payroll này (theo yêu cầu) — chấp nhận giới hạn
là chỉ chọn được các ngân hàng đã có format.

## 2. Mục tiêu

- Lưu **số tài khoản** + **ngân hàng nhận lương** trên hồ sơ nhân viên.
- Ngân hàng chọn từ **dropdown** lấy từ danh sách cấu hình payroll (`hb.bank.format`), không nhập tay → chuẩn hoá.
- Chỉ **Quản lý (HR Manager)** xem/sửa được (cùng tầng nhạy cảm với lương).

### Không làm (out of scope)
- **Không** nối field này vào wizard sinh file ngân hàng. Wizard hiện đọc số tài khoản từ
  `res.partner.bank`; field mới tạm thời là **dữ liệu hồ sơ**, chưa tự đẩy vào file chuyển khoản.
  → Đây là *known gap*; nếu muốn dùng để sinh file, đó là task riêng của Hùng (payroll) sau này.
- **Không** ràng buộc cứng `x_bank_code` phải tồn tại trong `hb.bank.format` (tránh vỡ dữ liệu
  cũ nếu sau này xoá/đổi một format). Chuẩn hoá chỉ ở tầng nhập liệu (dropdown).
- **Không** đụng tới logic/permission của module payroll.

## 3. Quyết định thiết kế (đã chốt)

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Cách lưu | 2 field `Char` trên `hr.employee` | Coupling lỏng — `hocba_employees` **không** depends `hocba_payroll` |
| Nguồn dropdown | `hb.bank.format` (list payroll) | Đúng yêu cầu; chuẩn hoá theo list công ty đã cấu hình |
| Lưu mã hay tên | Lưu **mã** (`x_bank_code`, vd `VCB`) | Đồng nhất tuyệt đối; lọc/gộp dễ |
| Phân quyền | Tier `mgr` (HR Manager) | Cùng nhóm nhạy cảm với lương |

## 4. Thiết kế chi tiết

### 4.1 Model — `custom-addons/hocba_employees/models/hr_employee.py`
Thêm 2 field trên `hr.employee`:

```python
x_bank_account_no = fields.Char(string='Số tài khoản nhận lương')
x_bank_code = fields.Char(
    string='Ngân hàng nhận lương',
    help='Mã ngân hàng chuẩn hoá (vd VCB), đồng bộ với danh sách cấu hình payroll.',
)
```

- Kiểu `Char`, không `required`, không constraint cứng tham chiếu `hb.bank.format`.
- Đặt gần nhóm field lương/bảo hiểm để dễ đọc code.

### 4.2 API — `custom-addons/hocba_hrm/controllers/main.py`

**a) `EMP_FORM_FIELDS`** — thêm 2 dòng (tier `mgr`):
```python
'bankCode': ('x_bank_code', 'mgr'),
'bankAccountNo': ('x_bank_account_no', 'mgr'),
```

**b) `api_form_meta`** — trả thêm danh sách ngân hàng (guard nếu payroll chưa cài):
```python
banks = []
if 'hb.bank.format' in env:
    banks = [{'code': b.code, 'name': b.name}
             for b in env['hb.bank.format'].sudo().search(
                 [('active', '=', True)], order='sequence, name')]
# ... thêm 'banks': banks vào dict trả về
```

**c) `_employee_detail`** — trong block `if is_mgr:` (~dòng 1460), thêm prefill:
```python
'bankCode': e.x_bank_code or '',
'bankAccountNo': e.x_bank_account_no or '',
```

> Field map qua `_split_form_payload` đã tự lọc theo tier `mgr` → user thường/HR thường gửi lên
> cũng bị bỏ. Không cần code chặn riêng.

### 4.3 SPA — `frontend/src/features/employees/EmployeeForm.jsx`

**a) `initForm`** — thêm:
```js
bankAccountNo: emp?.bankAccountNo || '', bankCode: emp?.bankCode || '',
```

**b) Section "Lương & bảo hiểm (Quản lý)"** (`isMgr`, ~dòng 146) — thêm:
- Dropdown **"Ngân hàng nhận lương"**: option từ `meta.banks`, hiển thị `name`, value = `code`,
  có option rỗng `— Chọn —`.
- Ô text **"Số tài khoản nhận lương"**.

```jsx
<Field label="Ngân hàng nhận lương">
  <select style={inp} value={f.bankCode} onChange={set('bankCode')}>
    <option value="">— Chọn —</option>
    {(meta.banks || []).map((b) => <option key={b.code} value={b.code}>{b.name}</option>)}
  </select></Field>
<Field label="Số tài khoản nhận lương">
  <input style={inp} value={f.bankAccountNo} onChange={set('bankAccountNo')} placeholder="VD: 0123456789" /></Field>
```

## 5. Data flow

```
Form (mgr) → bankCode='VCB', bankAccountNo='0123...'
  → POST /api/employee[s]
  → _split_form_payload (lọc tier mgr)
  → write hr.employee.x_bank_code / x_bank_account_no
Detail GET (mgr) → trả bankCode/bankAccountNo → prefill khi sửa
form/meta → banks[] (từ hb.bank.format) → đổ dropdown
```

## 6. Test (backend)

Trong `hocba_hrm` (hoặc `hocba_employees`), thêm test:

1. **Ghi đúng field:** create + update NV với `bankCode`/`bankAccountNo` (tài khoản HR Manager)
   → `x_bank_code` / `x_bank_account_no` được lưu đúng.
2. **Chặn theo tier:** payload có `bankCode`/`bankAccountNo` nhưng quyền `hr` (không phải `mgr`)
   → field **không** được ghi (giữ rỗng).
3. **`form/meta` trả `banks`:** có ít nhất 1 record `hb.bank.format` active → list `banks` chứa
   `{code, name}` tương ứng.

> Tuân thủ BR-010: NV `official` trong test phải có `identification_id` (CCCD) 12 số, mỗi NV một giá trị.
> Lệnh test: `... -u hocba_hrm,hocba_employees,hocba_payroll --test-tags ...` (cần payroll để có model `hb.bank.format`).

## 7. Tiêu chí hoàn thành

- [ ] 2 field hiển thị trên form ở section Quản lý, ẩn với HR thường/user thường.
- [ ] Dropdown ngân hàng đổ đúng từ list cấu hình payroll; lưu mã, prefill đúng khi sửa.
- [ ] Test backend xanh (ghi đúng field + chặn tier + meta trả banks), `0 failed, 0 error(s)`.
- [ ] Build SPA lại từ source.
- [ ] Cập nhật `docs/DB_TEST_DATA.md` nếu có seed dữ liệu ngân hàng cho NV demo.
