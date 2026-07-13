# Spec: Dọn dẹp & cải thiện giao diện SPA Time Off

- **Ngày**: 2026-07-07
- **Owner**: Nhật Anh (nhánh `NhatAnh/TimeOff`)
- **Phạm vi**: chỉ frontend — `frontend/src/features/timeoff/`, `frontend/src/components/`, `frontend/src/hooks/` (mới), `frontend/src/styles/`. **Không** đổi API backend, **không** đụng Shell/Topbar, **không** refactor module khác.
- **Bối cảnh**: thư mục timeoff có 15 file (~3.500 dòng) với nhiều pattern copy-paste (thanh chọn năm ×5, dropdown phòng ban ×6, header modal đỏ ×11, pattern fetch `data/err/tick` ở gần như mọi panel), 1 bug badge, và vài điểm UX chưa đồng nhất. Spec này tiếp nối hướng commit `f6dea0d` (gộp 6 bản Kpi trùng lặp thành `Kpi.jsx`).

## Mục tiêu

1. Badge tab "Chờ duyệt" cập nhật đúng sau khi duyệt/từ chối đơn (bug).
2. Xóa 4 nhóm trùng lặp lớn bằng hook + component dùng chung.
3. UX đồng nhất: hủy đơn bằng modal (bỏ `window.confirm`/`alert`), giữ filter năm/phòng ban khi chuyển tab, cân hàng KPI, hint khi tìm kiếm không áp dụng.
4. Nice-to-have: skeleton loading, cache stale-while-revalidate khi quay lại tab, thao tác bàn phím cho dòng bảng click được.

## Thiết kế

### 1. Nền móng (làm trước)

#### 1.1 Hook `useFetch` — `frontend/src/hooks/useFetch.js` (file + thư mục mới)

```js
const { data, err, loading, reload, setData } = useFetch(fetcher, deps, cacheKey);
```

- `fetcher`: hàm trả Promise (vd `() => fetchDashboard(year, dept || undefined)`).
- `deps`: mảng dependency — đổi là fetch lại (thay cho pattern `useEffect + tick` hiện tại).
- `cacheKey`: chuỗi định danh cache, vd `` `timeoff:dashboard:${year}:${dept}` ``. Truyền `null` = không cache (dành cho dữ liệu chỉ dùng một lần).
- **Cache**: `Map` cấp module (in-memory, sống trong phiên SPA, mất khi F5 — chấp nhận).
- **Stale-while-revalidate**:
  - Có cache cho key → set `data` ngay (không loading), đồng thời fetch ngầm; xong thì cập nhật state + cache.
  - Chưa có cache → `loading = true`, fetch xong mới có `data`.
  - Fetch lỗi khi **chưa có** data → set `err` (panel hiện `ErrorState` + Thử lại qua `reload`).
  - Fetch lỗi khi **đang có** data cũ → giữ nguyên data, chỉ `console.warn` (không đè màn hình lỗi lên dữ liệu đang xem).
  - Chống race: response về sau khi deps đã đổi thì bỏ qua (so sánh id lần gọi).
- `setData(payload)`: cho các action ghi thẳng payload server trả về (duyệt/hủy/điều chỉnh quỹ đều trả danh sách mới) vào state + cache — không cần refetch.
- `reload()`: fetch lại thủ công (nút Thử lại).

#### 1.2 `YearNav.jsx` — `frontend/src/features/timeoff/`

`{ year, onChange }` — gói khối `◀ 2026 ▶` + nút "Năm nay" (giữ nguyên markup/icon `chevR` xoay 180° như hiện tại). `THIS_YEAR` tính bên trong component; xóa hằng số lặp ở 5 file.

Thay thế tại: `DashboardPanel`, `ApprovedPanel`, `BalancesPanel`, `SummaryPanel`, `WorkScheduleModal`.

#### 1.3 `DeptSelect.jsx` — `frontend/src/features/timeoff/`

`{ value, onChange, departments }` — `<select className="sel">` với option đầu "Mọi phòng ban". Danh sách phòng ban vẫn lấy từ payload API của từng panel như hiện nay (không thêm API mới).

Thay thế tại: `DashboardPanel`, `ApprovedPanel`, `BalancesPanel`, `BurnoutPanel`, `LapsedPanel` (`SortBar` có bản select riêng khác ngữ cảnh — giữ nguyên, ngoài phạm vi).

#### 1.4 `ModalHeader.jsx` — `frontend/src/components/` (dùng chung toàn app)

`{ icon, title, sub, onClose, children }` — gói khối `drawer-head` gradient đỏ + ô icon 44×44 nền `--red-600` + nút X (11 chỗ đang lặp). `children` render cạnh `title` (chỗ chèn Badge như modal chi tiết đơn). `title` nhận node, không chỉ string.

Thay thế tại: `TimeOff.jsx` (3), `ApprovalPanel` (2), `BalancesPanel` (2), `ApprovedPanel`, `SubstitutionsPanel`, `LeaveForm`, `WorkScheduleModal` (mỗi file 1).

#### 1.5 `ConfirmModal.jsx` — `frontend/src/components/`

`{ title, message, confirmLabel, icon, onConfirm, onClose }`:

- Dựng bằng `Modal` + `ModalHeader` (icon mặc định `alertCircle`).
- `onConfirm` trả Promise; component tự quản `busy` (disable nút, đổi nhãn "Đang xử lý…") và hiện lỗi trong modal (khối đỏ nhạt như `WithdrawModal`) — không dùng `alert`.
- Không cần prop `danger`: `btn-primary` của theme đã là đỏ, dùng luôn cho nút xác nhận.

#### 1.6 `TableSkeleton` — thêm vào `frontend/src/components/states.jsx`

`{ rows = 5 }` — các thanh xám bo góc nhấp nháy (CSS animation trong `styles/`), giả hàng bảng. Panel dùng thay `LoadingState` cho lần tải đầu (khi `loading` từ `useFetch`); các lần sau đã có cache nên không thấy skeleton nữa.

### 2. Migrate panel sang nền móng

Mỗi panel **một commit riêng**, hành vi giữ nguyên 100%, chỉ đổi cấu trúc:

`DashboardPanel`, `ApprovedPanel`, `BalancesPanel`, `SummaryPanel`, `BurnoutPanel`, `LapsedPanel`, `CalendarPanel`, `ApprovalPanel`, `WorkScheduleModal` — chuyển sang `useFetch` (kèm cacheKey theo tab+params) + `YearNav`/`DeptSelect`/`ModalHeader` nơi áp dụng. Xóa pattern `data/err/tick` và markup lặp tương ứng.

### 3. Fix hành vi (làm sau khi migrate)

#### 3.1 Badge "Chờ duyệt" cập nhật sau khi xử lý đơn (bug)

- `ApprovalPanel` nhận thêm prop `onChanged(count)`; gọi sau mỗi lần duyệt/từ chối/quyết định rút (API `decideRequest`/`decideWithdraw` đã trả danh sách approvals mới — lấy `requests.length`, không tốn request thêm).
- `TimeOff.jsx`: `onChanged={setPendingCount}` — cùng cơ chế badge dạy thay (`onChanged={refreshSubCount}`) đang có.

#### 3.2 Hủy đơn bằng `ConfirmModal`

`TimeOff.jsx` bỏ `window.confirm` + `alert` trong `onCancel`; state `cancelling` (đơn đang chờ xác nhận) mở `ConfirmModal` với title "Hủy đơn nghỉ", message nêu loại nghỉ + khoảng ngày, `confirmLabel="Hủy đơn"`. `onConfirm = () => cancelRequest(id).then(setData)` — lỗi hiện trong modal.

#### 3.3 Lift filter năm/phòng ban lên `TimeOff`

- `TimeOff.jsx` giữ state chung: `year` (mặc định năm nay), `dept` (mặc định `''`).
- Truyền props xuống: `DashboardPanel`, `CalendarPanel`, `ApprovedPanel`, `BalancesPanel` (year + dept); `LapsedPanel`, `BurnoutPanel` (chỉ dept — API không có year); `SummaryPanel` (chỉ year). Panel bỏ state cục bộ tương ứng, render `YearNav`/`DeptSelect` với value/onChange từ props.
- Filter đặc thù từng tab (loại nghỉ, `filter='expiring'`…) vẫn cục bộ trong panel.
- `WorkScheduleModal` giữ year cục bộ (là modal độc lập, không phải tab).
- Vai trò không thấy `DeptSelect` (trưởng phòng chỉ 1 phòng) giữ nguyên logic ẩn/hiện hiện tại theo payload.

#### 3.4 Gộp hàng KPI Tổng quan còn 6 thẻ

`DashboardPanel` (ManagerView): bỏ thẻ "Ngày phép đã duyệt"; thẻ "Đã duyệt" thành `value = k.approved`, `sub = "${k.approvedDays} ngày phép đã duyệt"`. Còn 6 thẻ: Tổng đơn · Chờ duyệt · Quá hạn · Tuổi đơn cũ nhất · Đã duyệt · Đang nghỉ hôm nay.

#### 3.5 Hint tìm kiếm không áp dụng

Ô search thuộc Shell dùng chung toàn app → **không** đổi placeholder theo tab. Trong `TimeOff`: khi `search` khác rỗng và tab hiện tại không hỗ trợ lọc (mọi tab trừ `me`, `approved`, `balances`), hiện dòng muted nhỏ trên panel: *“Tìm kiếm không áp dụng cho tab này.”*

#### 3.6 A11y dòng bảng click được

Các `<tr>` mở modal (tab "Của tôi", và các bảng tương tự trong timeoff nếu có): thêm `tabIndex={0}`, `onKeyDown` (Enter/Space → mở như click), CSS `.tbl tr:focus-visible` (outline theo theme) trong `styles/`.

## Kiểm chứng

Frontend không có test framework → mỗi commit:

1. `cd frontend && npm run build` sạch (hook tự build đã có).
2. Checklist thủ công qua preview (`/hocba-hrm`, mật khẩu chung `Hocba@2026`):

| # | Kịch bản | Vai trò |
|---|----------|---------|
| 1 | Duyệt/từ chối 1 đơn ở tab Chờ duyệt → số trên badge tab giảm ngay | HR Manager |
| 2 | Hủy đơn ở tab Của tôi → modal xác nhận (không còn confirm trình duyệt); lỗi server hiện trong modal | NV thường |
| 3 | Chọn năm 2025 + 1 phòng ban ở Tổng quan → sang Đơn đã duyệt/Quỹ phép vẫn giữ nguyên lựa chọn | HR Manager |
| 4 | Vào tab đã xem lại → data hiện ngay (không skeleton), số liệu tự tươi lại sau giây lát | HR Manager |
| 5 | Tab Tổng quan còn 6 thẻ KPI, thẻ Đã duyệt có sub số ngày | HR Manager |
| 6 | Gõ từ khóa search khi đang ở tab Tổng quan → thấy hint "không áp dụng" | HR Manager |
| 7 | Tab/Enter mở được modal chi tiết đơn bằng bàn phím | NV thường |
| 8 | Trưởng phòng: các tab quản lý vẫn giới hạn phòng mình; Giáo viên: tab dạy thay + badge hoạt động như cũ | Trưởng phòng, GV |

## Trình tự thực hiện (mỗi bước ≥1 commit nhỏ)

1. Nền móng: `useFetch` → `YearNav` + `DeptSelect` → `ModalHeader` → `ConfirmModal` → `TableSkeleton`.
2. Migrate 9 file (mỗi file 1 commit), thứ tự gợi ý: Burnout (nhỏ nhất) → Lapsed → Summary → Approved → Dashboard → Balances → Calendar → Approval → WorkScheduleModal.
3. Fix hành vi: badge (3.1) → modal hủy (3.2) → lift filter (3.3) → KPI (3.4) → hint search (3.5) → a11y (3.6).
4. Build cuối + chạy checklist đầy đủ, cập nhật bundle `static/spa/` trong commit tương ứng.

## Ngoài phạm vi

- Mọi thay đổi backend/API; Shell/Topbar (placeholder search theo tab); áp dụng `ModalHeader`/`ConfirmModal` cho module khác (Employees, Payroll…) — để nhóm tự áp dụng sau; select trong `SortBar`; persist filter qua F5.
