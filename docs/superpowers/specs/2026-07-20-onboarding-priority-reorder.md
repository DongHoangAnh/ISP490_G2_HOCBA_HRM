# Spec — Bỏ ô số "Ưu tiên", thay bằng kéo-thả xếp thứ tự quy trình

**Ngày:** 2026-07-20 · **Owner:** Tân · **Trạng thái:** Đã duyệt (user chọn qua AskUserQuestion)

## Vấn đề

Ô số "Ưu tiên (số nhỏ thắng)" trong màn Cấu hình nhận việc quá trừu tượng — người
dùng (kể cả PO) phải hỏi lại 3-4 lần mới hiểu. Bản chất chỉ là *thứ tự giành quyền
khi một NV khớp nhiều quy trình*.

## Giải pháp

Mô hình "danh sách quy tắc" quen thuộc (lọc email / tường lửa):

> **Nhân viên mới được dò từ TRÊN xuống — khớp quy trình nào trước thì vào quy trình đó.**

Con số `sequence` GIỮ NGUYÊN dưới nắp (backend/matching không đổi), chỉ đổi cách
người dùng thao tác: kéo-thả (+ nút ▲▼) thay vì gõ số.

## Quyết định

| # | Quyết định | Lý do |
|---|---|---|
| 1 | UI danh sách 1 cột, badge vị trí `#1 #2…`, drag handle + nút ▲▼ | "Trên thắng dưới" chỉ rõ nghĩa khi xếp dọc; ▲▼ cho touch/a11y |
| 2 | Mỗi lần thả/bấm ▲▼ → lưu ngay qua API reorder (ghi sequence 10,20,30…) | Không cần nút "Lưu thứ tự"; bước 10 chừa khe cho API thủ công |
| 3 | Chỉ quy trình **đang dùng** tham gia thứ tự; mục "Đã lưu trữ" tách riêng bên dưới | Quy trình lưu trữ không tham gia matching |
| 4 | Template MỚI (và bản nhân bản) vào **cuối danh sách** (sequence = max+10) | Mặc định an toàn: không cướp quyền của quy trình cũ; muốn thắng thì kéo lên |
| 5 | Editor: **bỏ hẳn** ô số + help text; cảnh báo trùng đổi lời theo vị trí: "«X» đứng TRÊN → NV khớp cả hai sẽ theo «X»; kéo quy trình này lên trên nếu muốn ngược lại" | Không còn khái niệm số với người dùng; hết ca "cùng số" |
| 6 | Backend: model method `action_reorder(ids)` + route POST `/api/onboarding/templates/reorder` (gate HR Manager) | Logic ở model để test được; matching `_match_for_employee` không đổi |

## Không làm

- Không đổi schema / không migration (sequence là field sẵn có).
- Không đụng snapshot NV đang chạy (reorder chỉ ảnh hưởng lượt gán mới).
- Không thư viện drag ngoài — HTML5 draggable thuần.

## Test (TDD)

1. `action_reorder(ids)` ghi sequence tăng dần đúng thứ tự truyền vào; id lạ → ValidationError.
2. Sau reorder, `_match_for_employee` chọn theo thứ tự mới.
3. Create template không truyền sequence → tự vào cuối (max+10).

## Deploy

Code-only (không schema) → Neon chỉ cần pull code + restart container serve; KHÔNG cần `-u`.
