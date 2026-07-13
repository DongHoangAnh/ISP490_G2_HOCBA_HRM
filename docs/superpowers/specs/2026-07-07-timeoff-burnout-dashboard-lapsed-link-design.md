# Spec — Tab "Sức khỏe NV" (Burnout) + Link nhanh Lapsed → Chờ duyệt

- **Ngày:** 2026-07-07 · **Owner:** Nhật Anh · **Module:** `hocba_timeoff` (controller nằm trong `hocba_timeoff/controllers/main.py`, route prefix `/hocba-hrm/api`)
- **Trạng thái:** Đã duyệt design (chat) — chờ plan TDD
- **Liên quan:** `docs/superpowers/specs/2026-06-21-timeoff-hr-quota-management-design.md` (Widget 6 / BR-040),
  `docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md` (Phase 12)

## 1. Bối cảnh & Mục tiêu

Model SQL view `hb.timeoff.burnout.line` (BR-040) đã tồn tại trong backend từ trước
nhưng **chưa có endpoint API lẫn màn hình SPA nào hiển thị** — giá trị đã build mà chưa dùng.
Đồng thời ở màn "Giám sát duyệt" (Phase 12), các đơn không có đề xuất (Xem tay,
nghỉ buổi dạy) chỉ hiện chữ xám *"xử lý ở tab Chờ duyệt"* — quản lý phải tự chuyển tab
rồi tự tìm lại đơn.

Hai tính năng trong spec này:

1. **Tab "Sức khỏe NV"** — màn cảnh báo burnout cho officer, đọc từ view có sẵn.
2. **Link nhanh Lapsed → Chờ duyệt** — bấm 1 phát từ dòng "Xem tay" là sang tab
   Chờ duyệt và mở luôn modal xử lý đúng đơn đó.

## 2. Tính năng 1 — Tab "Sức khỏe NV" (Burnout, Widget 5-6)

### 2.1 Nguồn dữ liệu (KHÔNG sửa)

`hb.timeoff.burnout.line` — SQL view tính live, mỗi dòng 1 NV active:

| Field | Ý nghĩa |
|---|---|
| `sick_leave_count_3m` | Số lần nghỉ ốm (loại có `support_document`) validated trong 90 ngày |
| `total_absence_days_3m` | Tổng ngày vắng validated trong 90 ngày |
| `remaining_leave_balance` | Số dư phép còn lại (từ `hr_leave_report`) |
| `burnout_risk` | True khi: ốm ≥3 lần/3 tháng **hoặc** vắng >10 ngày/3 tháng **hoặc** dư <2 ngày |
| `risk_reason` | 1 lý do chính (CASE ưu tiên: ốm → vắng → dư thấp) |

### 2.2 Backend — helper + endpoint (`hocba_timeoff/controllers/main.py`)

**Helper cấp module** (test import được, theo mẫu `_lapsed_table`):

```python
def _burnout_table(env, scope, dept_id=None):
    """Bảng cảnh báo burnout trong phạm vi scope. Đọc view qua sudo
    SAU khi caller đã kiểm scope (quy ước self-service của module)."""
```

- Domain: `burnout_risk = True`, sắp xếp `sick_leave_count_3m` giảm dần.
- Phạm vi (tái dùng `_scope_for` + `_dept_domain` — **y hệt `/lapsed-dashboard`**):
  - Gate: `scope['canApprove']` (HR/Admin/HR User hoặc trưởng phòng); không có → 403.
  - `seeAll` (HR/Admin/HR User): toàn công ty; lọc thêm `department_id = dept_id` nếu truyền.
  - Trưởng phòng: `department_id in scope['deptIds']` (gồm phòng con).
  - (Giáo vụ thuần không có `canApprove` trong timeoff → 403, nhất quán các màn giám sát hiện có.)
- Response:

```json
{
  "kpi": { "total": 5, "sickFreq": 2, "highAbsence": 2, "lowBalance": 1 },
  "items": [{
    "employeeId": 7, "employee": "Nguyen Van A",
    "departmentId": 3, "department": "Giảng viên",
    "sickCount3m": 4, "absenceDays3m": 6.0,
    "remainingBalance": 8.5,
    "riskReason": "Nghỉ ốm thường xuyên (≥3 lần / 3 tháng)"
  }],
  "byDepartment": [{ "id": 3, "name": "Giảng viên", "count": 2 }],
  "allDepartments": [{ "id": 3, "name": "Giảng viên" }],
  "seeAll": true
}
```

- KPI đếm theo `risk_reason` (view trả đúng 1 lý do chính/NV → `sickFreq + highAbsence + lowBalance = total`).
  Map: chuỗi bắt đầu "Nghỉ ốm" → `sickFreq`; "Vắng nhiều" → `highAbsence`; "Số dư" → `lowBalance`.
- `byDepartment`: gom items theo phòng, đếm giảm dần; NV không có phòng gom vào nhóm tên `—` (id=false, khớp pattern `_lapsed_table`).
- `allDepartments`: chỉ trả khi `seeAll` (giống `/lapsed-dashboard`).

**Endpoint:** `GET /hocba-hrm/api/timeoff/burnout?dept=<id>` (`auth='user'`, type http, JSON out):
- Không phải officer (`_scope_for` không có quyền quản lý nào) → **403** `{"error": "forbidden"}`.
- `dept` chỉ có tác dụng khi `seeAll`.

**ACL:** đã có sẵn trong `security/ir.model.access.csv` (dòng
`access_hb_burnout_line_hr_user` + `access_hb_burnout_line_base_user`, read-only)
— **không cần sửa**. Controller đi `.sudo()` sau kiểm scope.

### 2.3 Frontend

- `frontend/src/api/timeoff.js`: thêm `fetchBurnout(dept)` (giống `fetchLapsedDashboard`).
- **`frontend/src/features/timeoff/BurnoutPanel.jsx`** (file mới, khung sao LapsedPanel):
  - Filterbar chọn phòng ban — chỉ khi `seeAll`.
  - 4 KPI card: **Tổng cảnh báo** (đỏ khi >0) · **Nghỉ ốm thường xuyên** (amber) ·
    **Vắng nhiều** (amber) · **Sắp cạn phép**.
  - Card "Cảnh báo theo phòng ban": bar ngang như LapsedPanel.
  - Bảng chi tiết: Nhân viên · Phòng ban · Nghỉ ốm (3 tháng) · Ngày vắng (3 tháng) ·
    Số dư phép · Lý do cảnh báo (Badge: đỏ = ốm thường xuyên, amber = vắng nhiều,
    gray = dư thấp).
  - Empty state: *"Không có nhân viên nào trong diện cảnh báo. 🎉"*
- `TimeOff.jsx`: tab mới `['health', 'Sức khỏe NV']` **ngay sau** `'lapsed'`,
  render `{activeTab === 'health' && data.isOfficer && <BurnoutPanel />}`.

### 2.4 Test TDD (`hocba_timeoff/tests/test_burnout.py`)

Gọi thẳng helper `_burnout_table` với `env` (mẫu `test_lapsed.py`):

1. NV có ≥3 đơn ốm validated trong 90 ngày → có mặt trong `items`,
   `riskReason` nhóm ốm, KPI `sickFreq` ≥1.
2. NV vắng >10 ngày (loại thường) trong 90 ngày → nhóm "Vắng nhiều".
3. NV bình thường (0 đơn) → KHÔNG có trong `items`.
4. Scope trưởng phòng: chỉ thấy NV phòng mình (NV phòng khác không xuất hiện).
5. Endpoint: user thường (không officer) → 403.

Lưu ý test: NV `official` phải có `identification_id` 12 số duy nhất (BR-010);
đơn ốm dùng leave type có `support_document=True`.

## 3. Tính năng 2 — Link nhanh Lapsed → Chờ duyệt (mở thẳng modal)

Thuần frontend, theo pattern `focus` từ chuông đã có ở `TimeOff.jsx`.

### 3.1 Hành vi

- Ở bảng "Chi tiết đơn lỡ hạn" (LapsedPanel), dòng **không có đề xuất**
  (badge "Xem tay" — đơn lẫn lộn chấm công hoặc nghỉ buổi dạy): thay chữ xám
  `xử lý ở tab Chờ duyệt` bằng **nút link "Xử lý ở tab Chờ duyệt →"**.
- Bấm nút → chuyển sang tab **Chờ duyệt** và **mở luôn DecisionModal** của đúng
  đơn đó (modal có sẵn khối cảnh báo lỡ hạn + đối chiếu chấm công của Phase 12).
- Đơn đang có yêu cầu rút (`withdrawState === 'pending'`) → mở
  `WithdrawDecisionModal` thay vì DecisionModal (khớp nút "Xử lý rút" ở bảng).
- Nếu đơn không còn trong danh sách chờ duyệt (vừa được xử lý xong ở nơi khác):
  chỉ hiển thị tab Chờ duyệt bình thường, không mở modal, không báo lỗi.
- Focus **tiêu thụ 1 lần**: user đóng modal rồi thì không tự mở lại; đổi tab
  qua lại cũng không mở lại.

### 3.2 Thay đổi code

1. **`TimeOff.jsx`**
   - State mới: `const [approvalFocus, setApprovalFocus] = useState(null); // requestId`
   - `<LapsedPanel onOpenApproval={(id) => { setApprovalFocus(id); setTab('approvals'); }} />`
   - `<ApprovalPanel isHrManager={...} focusRequestId={approvalFocus} onFocusConsumed={() => setApprovalFocus(null)} />`
2. **`LapsedPanel.jsx`** — nhận prop `onOpenApproval`; nhánh `!r.suggestion`
   đổi `<span>` thành `<button className="btn btn-ghost btn-sm">Xử lý ở tab Chờ duyệt →</button>`.
3. **`ApprovalPanel.jsx`** — nhận props `focusRequestId`, `onFocusConsumed`;
   `useEffect([data, focusRequestId])`: khi có data + focus → tìm
   `data.requests.find(r => r.id === focusRequestId)`;
   tìm thấy → `withdrawState === 'pending' ? setWithdrawDecision(row) : setDecision(row)`;
   mọi nhánh đều gọi `onFocusConsumed()`.

### 3.3 Kiểm thử

Dự án không có test JS → **verify tay trên preview** (tài khoản `hr.manager`):
- Tab Giám sát duyệt: dòng "Xem tay" có nút link; bấm → sang tab Chờ duyệt,
  modal mở đúng đơn (tên NV + khoảng ngày khớp).
- Đóng modal → không tự mở lại; chuyển tab qua lại → không tự mở lại.
- Dòng có đề xuất (Duyệt trễ/Từ chối) giữ nguyên nút "Xử lý theo đề xuất".

## 4. Ngoài phạm vi (YAGNI)

- Không sửa SQL view burnout / tiêu chí BR-040 (kể cả tiêu chí OT còn thiếu).
- Không thêm export Excel, không lịch sử burnout theo thời gian.
- Không thông báo chuông cho cảnh báo burnout.
- Không deep-link bằng URL (SPA không có router).

## 5. Triển khai & nghiệm thu

- Backend trước (helper + endpoint + test xanh) → UI sau (quy trình module).
- Build SPA (`cd frontend && npm run build`), upgrade `hocba_timeoff`/`hocba_hrm`
  trên Neon bằng **endpoint trực tiếp** (bỏ `-pooler`).
- Nghiệm thu: tab "Sức khỏe NV" hiện đúng NV có cờ theo scope từng vai trò;
  link Lapsed mở đúng modal; test module `0 failed, 0 error mới`.
