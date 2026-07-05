# Thiết kế: Offboarding SPA — Giao diện Nghỉ việc (React)

- **Ngày:** 2026-07-04
- **Phần trước:** backend + API đã merge main (`docs/superpowers/specs/2026-07-04-offboarding-design.md`)
- **Module:** `hocba_hrm` (controller enrichment) + `frontend/` (React SPA)
- **Mẫu tham chiếu:** `features/timeoff/` (TimeOff.jsx — feature giống nhất: đơn + duyệt)

## 1. Mục tiêu

Nối giao diện SPA `/hocba-hrm` vào 3 API offboarding đã có: nhân viên tự nộp đơn nghỉ việc,
cấp quản lý (TBP/quản lý trực tiếp/giáo vụ) và HR duyệt/hoàn tất — mirror cấu trúc màn Nghỉ phép.

## 2. Phần A — Mở rộng API (backend nhỏ)

Sửa `custom-addons/hocba_hrm/controllers/main.py`:

### `_offb_json(rec)` thêm field
- `stateLabel` (nhãn tiếng Việt) + `stateKind` (màu badge — xem §4).
- Cờ quyền tính cho **user hiện tại** (không hard-code trạng thái ở FE):
  - `canMgrApprove` — state=submitted VÀ user quản lý phạm vi NV (hoặc HR Manager).
  - `canHrApprove` — state=mgr_approved VÀ user là HR Manager.
  - `canDone` — state=hr_approved VÀ user là HR Manager.
  - `canRefuse` — (state=submitted VÀ user quản lý phạm vi) HOẶC (state=mgr_approved VÀ HR Manager).
  - `canCancel` — state ∈ (draft, submitted) VÀ (đơn của mình HOẶC HR Manager).
- Cờ "quản lý phạm vi NV" tái dùng đúng logic `_ensure_manages` của model (dept manager,
  `parent_id` trực tiếp, giáo vụ với giáo viên, HR) — gọi helper, bắt AccessError → False.

### `GET /hocba-hrm/api/offboarding/list` trả cấu trúc mới
```json
{ "isOfficer": bool, "isEmployee": bool,
  "mine": [ {..._offb_json} ], "managed": [ {..._offb_json} ] }
```
- `mine` = đơn của employee gắn với user (mọi user có employee).
- `managed` = đơn trong **phạm vi quản lý** — CHỈ khi `isOfficer`.
- **Sửa scope managed khớp quyền duyệt** (fix follow-up parent_id): phạm vi = trưởng phòng
  (dept + phòng con) ∪ cấp dưới trực tiếp (`parent_id`) ∪ giáo vụ→giáo viên ∪ HR→tất cả.
  KHÔNG sửa helper dùng chung `_emp_scope_domain` (tránh ảnh hưởng endpoint khác) —
  endpoint offboarding tự tính scope riêng (Lựa chọn B của follow-up task_b7fd86bf).
- `isOfficer` = `_user_can_manage(env)`; `isEmployee` = user có `employee_id` và
  KHÔNG phải tài khoản vai trò quản lý (đồng bộ triết lý tách tài khoản của Shell.jsx).

### `POST /submit`, `POST /action` — giữ nguyên, chỉ trả item đã enrich.

### Test (Odoo, `custom-addons/hocba_hrm/tests/test_offboarding_api.py`)
- Cờ can* đúng theo vai trò/trạng thái (HR, TBP, quản lý parent_id, NV thường).
- `mine`/`managed` tách đúng; quản lý `parent_id` thấy đơn cấp dưới trong `managed`.
- Chạy trên DB cô lập `off_hrm` (DB chung vẫn hỏng bởi bug payroll — ngoài phạm vi).

## 3. Phần B — Cấu trúc SPA

- **Nav** (`frontend/src/app/Shell.jsx`): item `{ id:'offboarding', label:'Nghỉ việc', icon:'logout' }`
  ở cả nhóm "Quản lý nhân sự" (`need:'manage'`) và "Cá nhân" (`need:'self'`) — như timeoff.
  Thêm `PAGE_META.offboarding = { t:'Nghỉ việc', c:'Nhân sự / Offboarding' }`.
- **Route** (`frontend/src/app/App.jsx`): `{view === 'offboarding' && <Offboarding search={search} />}`.
- **API client** (`frontend/src/api/offboarding.js`):
  - `fetchOffboarding()` → GET list.
  - `submitOffboarding(payload)` → POST submit `{reasonType, reason, expectedLeaveDate}`.
  - `offboardingAction(id, action)` → POST action.
- **Component** (`frontend/src/features/offboarding/`):
  - `Offboarding.jsx` — chính: load list, tab theo `isOfficer`:
    - `isOfficer` → tab duy nhất **"Chờ xử lý"** (list `managed`, gộp mọi trạng thái, nút thao tác inline).
    - ngược lại → tab **"Đơn của tôi"** (list `mine` + nút "Nộp đơn nghỉ" nếu `isEmployee`).
    - Tài khoản vai trò quản lý KHÔNG có tab "Của tôi" (tách tài khoản — như timeoff).
  - `OffboardingForm.jsx` — modal nộp đơn.

## 4. Phần C — Chi tiết UX

**Badge trạng thái** (BE trả `stateLabel`/`stateKind`, FE chỉ render):
| state | stateLabel | stateKind |
|---|---|---|
| draft | Nháp | gray |
| submitted | Chờ quản lý duyệt | amber |
| mgr_approved | Chờ HR duyệt | blue |
| hr_approved | Chờ hoàn tất | violet |
| done | Đã nghỉ | gray |
| refused | Từ chối | red |
| cancelled | Đã huỷ | gray |

**Tab "Chờ xử lý" (officer)** — bảng: Mã đơn · Nhân viên · Loại lý do · Ngày nộp ·
Ngày nghỉ dự kiến · Tài sản chưa thu hồi · Trạng thái · Thao tác.
- Nút theo cờ: `canMgrApprove`→"Quản lý duyệt" (primary); `canHrApprove`→"HR duyệt" (primary);
  `canDone`→"Hoàn tất" (primary); `canRefuse`→"Từ chối" (ghost).
- **Chặn Hoàn tất khi còn tài sản:** `canDone && assetPending>0` → nút disabled +
  title "Còn N tài sản chưa thu hồi". BE vẫn là chốt chặn cuối (ValidationError → alert message).
- Xác nhận trước thao tác không thuận nghịch: "Hoàn tất" và "Từ chối" dùng `window.confirm`.

**Tab "Đơn của tôi" (NV)** — bảng: Mã đơn · Loại lý do · Ngày nộp · Ngày nghỉ dự kiến ·
Trạng thái · Thao tác (`canCancel`→"Huỷ" với confirm). Bấm dòng → modal chi tiết
(mã, trạng thái, lý do, ngày, người duyệt nếu có). Trống → EmptyState "Chưa có đơn nghỉ việc nào."

**Form nộp đơn (`OffboardingForm`)** — modal theo pattern `WithdrawModal`:
- Loại lý do: select `voluntary` "Tự nguyện" (mặc định) / `contract_end` "Hết hạn HĐ" /
  `other` "Khác". KHÔNG có `performance` (luồng probation tự động, không cho tự chọn).
- Lý do chi tiết: textarea, bắt buộc nhập.
- Ngày nghỉ dự kiến: input date, mặc định hôm nay +30 ngày, bắt buộc.
- Ghi chú tĩnh: đơn sẽ qua 2 cấp duyệt (quản lý → HR).
- Submit → `submitOffboarding` → đóng modal + reload list. Lỗi hiển thị trong modal.

**Xử lý lỗi** — theo pattern timeoff: lỗi load → `ErrorState` + retry; lỗi thao tác →
`alert(message)`; message từ `ApiError.detail` (BE trả message tiếng Việt của ValidationError).

## 5. Phần D — Kiểm thử & Build

- **Backend:** test Odoo như §2; chạy `-u hocba_hrm` trên DB `off_hrm`, `0 failed` cho
  TestOffboarding* (test_teaching_days fail là pre-existing, không liên quan).
- **SPA:** dự án không có test runner JS → kiểm chứng bằng:
  1. `cd frontend && npm run build` thành công (output `custom-addons/hocba_hrm/static/spa/`).
  2. Preview thủ công: NV nộp đơn → officer duyệt 2 cấp → hoàn tất (hoặc chặn vì tài sản).
- **Build artifact** `static/spa/` commit từ build, không sửa tay (gotcha merge của dự án).

## 6. Ngoài phạm vi
- Chuông thông báo (NotificationBell) cho offboarding — để sau nếu cần.
- Không đổi `_emp_scope_domain` dùng chung; không đụng module payroll.
- Không sửa luồng backend model đã merge (chỉ enrich JSON controller).
