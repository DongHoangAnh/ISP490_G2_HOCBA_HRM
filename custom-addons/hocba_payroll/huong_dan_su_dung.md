# Huong dan cai dat & su dung module Hoc Ba Payroll tren Odoo UI

---

## 1. Cai dat module

### Buoc 1: Rebuild Docker image (vi da them openpyxl vao Dockerfile)

```bash
docker compose build --no-cache odoo
```

### Buoc 2: Khoi dong he thong

Neu la lan dau (chua co database):

```bash
docker compose up -d
```

Neu database `hocba_hrm` da ton tai, ban **khong can** thay `--init` trong `docker-compose.yml`. Thay vao do, cai module qua Odoo UI.

### Buoc 3: Kich hoat Developer Mode

1. Truy cap `http://localhost:8069`
2. Dang nhap bang tai khoan admin
3. Vao **Settings** (Thiet lap) -> keo xuong cuoi -> nhan **Activate the developer mode**

### Buoc 4: Cai dat module Hoc Ba Payroll

1. Vao menu **Apps** (Ung dung)
2. Nhan nut **Update Apps List** (Cap nhat danh sach ung dung) — neu khong thay thi nhan icon ☰ -> Update Apps List
3. Xoa filter mac dinh "Apps", tim kiem **"Hoc Ba Payroll"**
4. Nhan **Install** (Cai dat)

> Module se tu dong cai kem cac dependency: `hr`, `mail`, `hocba_employees`

---

## 2. Cau truc menu sau khi cai

Sau khi cai xong, vao menu **Employees** (Nhan vien) -> ban se thay menu **Payroll** voi cau truc:

```
Employees
  └── Payroll
        ├── Hop dong            ← Quan ly hop dong giao vien
        ├── Payslip Batches      ← Quan ly batch luong theo ky
        ├── Payslips             ← Phieu luong tung nhan vien
        ├── Work Entries         ← Gio day (WORK200 / WORK110_OT_HOLIDAY)
        ├── File Ngan hang       ← File chuyen khoan VCB / TCB
        ├── Bao cao
        │     ├── Bao cao BHXH   ← Bao cao bao hiem xa hoi
        │     └── Bao cao thue TNCN ← eTax 05/KK-TNCN
        └── Cau hinh (HR Manager only)
              ├── Cau hinh Ngan hang ← Format VCB/TCB
              └── Loai Work Entry    ← Teaching Hours, Holiday OT
```

---

## 3. Luong su dung tu A -> Z

### Buoc A: Thiet lap hop dong giao vien

1. Vao **Payroll** -> **Hop dong** -> nhan **Create**
2. Dien thong tin hop dong:
   - **Ten hop dong**: VD `HD-GV001-2026`
   - **Nhan vien**: chon giao vien
   - **Ngay bat dau**: VD `2026-01-01`
   - **Ngay ket thuc**: (de trong neu vo thoi han)
   - **Luong co ban (dong BH)**: VD `5000000` — dung lam base tinh BHXH
3. Dien don gia gio day:
   - **Don gia gio co ban**: VD `150000` (150k/gio)
   - **Don gia gio HSK4+**: VD `200000` (200k/gio cho HSK4+)
   - **Don gia gio lop dac biet**: (tuy chon)
4. Dien nguong & bonus:
   - **Nguong gio chuan/thang**: VD `60` (gio/thang)
   - **Don gia gio vuot nguong**: VD de trong -> tu lay hourly_rate x 1.25
5. Luong co dinh (neu co):
   - **Co luong co dinh base**: tick neu GV co base salary
   - **Luong co dinh**: VD `5000000`
6. **Save** -> nhan nut **Xac nhan** de chuyen trang thai sang `Dang hieu luc`

### Buoc B: Nhap Work Entries (gio day)

1. Vao **Payroll** -> **Work Entries**
2. Nhan **Create** (Tao moi)
3. Dien:
   - **Nhan vien**: chon giao vien
   - **Loai Work Entry**: `Teaching Hours` (WORK200)
   - **Cap do lop**: `basic` / `intermediate` / `hsk4` / `hsk5` / `hsk6`
   - **Ma lop**: VD `CN301`
   - **Tu ngay / Den ngay**: thoi gian buoi day (VD: 2026-06-01 08:00 -> 2026-06-01 10:00)
   - Duration se tu tinh (2 gio)
4. **Save** -> nhan nut **Xac thuc** de chuyen tu `Nhap` -> `Da xac thuc`

> Nhap tuong tu cho OT ngay le: chon loai `Holiday OT Teaching` (WORK110_OT_HOLIDAY)

> Meo: dung list view de nhap nhanh nhieu dong

### Buoc C: Tao Payslip Batch (ky luong)

1. Vao **Payroll** -> **Payslip Batches**
2. Nhan **Create**
3. Dien:
   - **Ten batch**: VD `Luong T6/2026`
   - **Tu ngay**: `2026-06-01`
   - **Den ngay**: `2026-06-30`
4. **Save**

### Buoc D: Tao Payslip cho tung nhan vien

1. Trong form Batch, nhan nut **Payslips** (stat button) hoac vao **Payroll** -> **Payslips**
2. Nhan **Create**
3. Dien:
   - **Nhan vien**: chon giao vien
   - **Payslip Batch**: chon batch vua tao
   - **Tu ngay / Den ngay**: `2026-06-01` -> `2026-06-30`
4. **Save**

### Buoc E: Tinh luong

1. Trong form Payslip, nhan nut **Tinh luong day** (button xanh o header)
2. He thong se:
   - Tim hop dong dang hieu luc
   - Kiem tra khong co work entries nao o trang thai `Nhap` (VR-004)
   - Tinh theo pipeline: `FIXED_BASE` -> `TEACH_HOURS` -> `HSK_PREMIUM` -> `EXTRA_BONUS` -> `HOLIDAY_OT` -> `GROSS` -> `BHXH` -> `BHYT` -> `BHTN` -> `PIT` -> `NET`
   - Tao cac dong chi tiet trong tab **Chi tiet luong**
3. Ket qua hien thi:
   - **Gross**: tong luong brut
   - **Net**: thuc linh
   - State chuyen thanh `Dang xac nhan`

### Buoc F: Xac nhan va dong batch

1. Trong form Payslip, nhan **Xac nhan (Done)** de chot phieu luong
2. Quay lai Batch, nhan **Dong batch** -> tat ca payslips trong batch se tu chuyen sang `Done`

### Buoc G: Sinh file ngan hang (FUNC-PR-003)

1. Vao **Payroll** -> **File Ngan hang** -> **Create**
2. Hoac dung wizard: menu **Cau hinh** -> ban cung co the goi qua API
3. Chon Batch, Bank Format (VCB/TCB), nhap ngay thanh toan
4. Nhan **Generate** -> file XLSX duoc tao va dinh kem

### Buoc H: Bao cao BHXH (FUNC-PR-004)

1. Vao **Payroll** -> **Bao cao** -> **Bao cao BHXH** -> **Create**
2. Chon thang, nam, Payslip Batch (phai o trang thai `Hoan tat`)
3. Nhan **Tinh toan** -> he thong tao chi tiet BHXH cho tung NV
4. Sau khi kiem tra, nhan **Danh dau da nop**

### Buoc I: Bao cao thue TNCN (FUNC-PR-005)

1. Vao **Payroll** -> **Bao cao** -> **Bao cao thue TNCN** -> **Create**
2. Chon thang, nam, Payslip Batch
3. Nhan **Tinh toan** -> tinh thue TNCN 7 bac cho tung NV
4. Nhan **Danh dau da nop** sau khi hoan tat

---

## 4. Luu y quan trong

| Muc | Chi tiet |
|---|---|
| **Quyen truy cap** | HR Manager: full CRUD. HR User: chi doc |
| **VR-004** | Khong the tinh luong neu con Work Entry o trang thai `Nhap` trong ky |
| **BHXH base** | Tinh theo truong `wage` trong hop dong (luong dong BH) |
| **PIT** | Tu dong tinh 7 bac luy tien. Giam tru ban than 11M, moi nguoi phu thuoc 4.4M |
| **Reset payslip** | Can nhap ly do khi reset ve Nhap (audit trail) |

---

## 5. Test nhanh bang API (alternative)

Neu muon test qua REST API thay vi UI:

```bash
# Tao Work Entry
curl -X POST http://localhost:8069/api/payroll/work-entries \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1, "work_entry_type_code": "WORK200", "date_start": "2026-06-01 08:00:00", "date_stop": "2026-06-01 10:00:00", "x_class_level": "hsk4", "x_class_code": "CN301"}'

# Tao Batch
curl -X POST http://localhost:8069/api/payroll/batches \
  -H "Content-Type: application/json" \
  -d '{"name": "Luong T6/2026", "date_start": "2026-06-01", "date_end": "2026-06-30"}'

# Tao Payslip + Tinh luong
curl -X POST http://localhost:8069/api/payroll/payslips \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1, "payslip_run_id": 1, "date_from": "2026-06-01", "date_to": "2026-06-30"}'

curl -X POST http://localhost:8069/api/payroll/payslips/1/compute
```
