# Spec: Đơn lỡ hạn duyệt — đối chiếu chấm công + màn giám sát (Time Off)

- **Ngày**: 2026-07-03
- **Module**: `hocba_timeoff` (backend) + `frontend/src/features/timeoff/` (SPA)
- **Trạng thái**: Đã duyệt thiết kế, chờ plan
- **Bối cảnh**: Quản lý quên duyệt đơn nghỉ phép; ngày nghỉ đã trôi qua mà đơn vẫn nằm ở "Chờ duyệt". Cần cơ chế phát hiện, đối chiếu thực tế chấm công, hỗ trợ xử lý nhanh và giám sát tổng thể.

## 1. Mục tiêu

1. Gắn cờ **"đơn lỡ hạn"** cho đơn nghỉ đã qua ngày bắt đầu mà vẫn chờ duyệt.
2. **Đối chiếu chấm công** các ngày xin nghỉ đã trôi qua để biết nhân viên nghỉ thật hay vẫn đi làm.
3. **Gợi ý xử lý + nút 1-chạm** cho người duyệt (duyệt trễ / từ chối), giữ nguyên trách nhiệm phê duyệt ở con người.
4. **Màn giám sát riêng** cho HR/quản lý: KPI + bảng chi tiết + thống kê theo phòng.
5. **Thông báo chuông 1 lần** cho người duyệt khi đơn chuyển sang lỡ hạn.

**Ngoài phạm vi (YAGNI)**: không tự động duyệt/từ chối bằng cron; không escalate lên cấp trên; không gửi email (chỉ chuông in-app); không sửa module chấm công (chỉ đọc); không đổi flow duyệt hiện có.

## 2. Quy tắc nghiệp vụ

### BR-L01 — Định nghĩa đơn lỡ hạn
Đơn ở trạng thái chờ duyệt (`state in ('confirm', 'validate1')`) và **ngày bắt đầu nghỉ < hôm nay** (theo múi giờ Asia/Ho_Chi_Minh). Tính real-time khi đọc API, **không lưu cờ vào DB**.

### BR-L02 — Đối chiếu chấm công
- Phạm vi đối chiếu: các ngày nghỉ trong đơn **đã trôi qua** (từ `request_date_from` đến `min(hôm qua, request_date_to)`), chỉ tính ngày làm việc (T2–T6 + `hb.work.day`, trừ ngày lễ) — tái dùng helper working-day sẵn có của Phase 8.
- Một ngày tính là **"vẫn đi làm"** khi bản ghi `hocba.attendance` của nhân viên ngày đó có `work_credit ≥ 0.5`.
- **Đơn nghỉ nửa ngày**: ngày đó chỉ tính mâu thuẫn khi `work_credit = 1.0` (nửa ngày làm + nửa ngày nghỉ là khớp đơn, không phải mâu thuẫn).
- **Ngoại lệ giáo viên**: đơn loại "Nghỉ Buổi Dạy" (nghỉ theo buổi dạy, không trừ quỹ) **được miễn đối chiếu chấm công** — GV nghỉ một buổi dạy vẫn có thể chấm công tại trung tâm cùng ngày. Loại này chỉ gắn cờ lỡ hạn (BR-L01), không có gợi ý xử lý.

### BR-L03 — Gợi ý xử lý
Dựa trên tập ngày đã đối chiếu (BR-L02):

| Kết quả đối chiếu | Gợi ý | Diễn giải |
|---|---|---|
| Tất cả ngày đã qua đều **không** đi làm | `approve` — "Duyệt trễ" | Nhân viên nghỉ thật, hợp thức hoá đơn |
| Tất cả ngày đã qua đều **có** đi làm | `refuse` — "Từ chối" | Nhân viên vẫn làm, đơn không còn hiệu lực; từ chối hoàn quỹ theo flow chuẩn |
| Lẫn lộn (ngày làm ngày nghỉ) | không gợi ý | Hiện chi tiết từng ngày, người duyệt tự quyết |
| Chưa có ngày nào đã qua để đối chiếu / loại được miễn | không gợi ý | Chỉ hiện cờ lỡ hạn |

### BR-L04 — Xử lý 1-chạm và ghi vết
- Nút **"Xử lý theo đề xuất"** chỉ hiện khi có gợi ý rõ (`approve` hoặc `refuse`). Bấm nút gọi đúng endpoint duyệt hiện có (`/request/<id>/decision`) với action theo gợi ý — **không tạo flow duyệt mới**, chuỗi quyền duyệt giữ nguyên.
- Khi một đơn **đang lỡ hạn** được duyệt/từ chối (bằng nút 1-chạm hay bấm tay thường), hệ thống tự ghi note vào chatter, ví dụ:
  - *"Duyệt trễ — đơn lỡ hạn 4 ngày. Đối chiếu chấm công: không đi làm 2/2 ngày nghỉ."*
  - *"Từ chối — đơn lỡ hạn 4 ngày. Đối chiếu chấm công: vẫn đi làm 2/2 ngày nghỉ."*
- Duyệt trễ vẫn trừ quỹ như duyệt thường; từ chối hoàn quỹ theo cơ chế chuẩn của Odoo.

### BR-L05 — Thông báo
- Cron hàng ngày quét đơn thoả BR-L01 và chưa được báo → tạo `hb.leave.notification` kind mới **`lapsed`** cho từng người duyệt của đơn, tiêu đề dạng *"Đơn nghỉ của X đã lỡ hạn duyệt"*.
- Mỗi đơn chỉ báo **1 lần duy nhất** (chốt bằng field `x_lapsed_notified`). Không nhắc lại, không escalate.

### BR-L06 — Phân quyền màn giám sát
Theo convention sẵn có của dự án (giống Phase 8):
- HR/Admin: thấy toàn bộ.
- Trưởng phòng (`hr.department.manager_id`, gồm phòng con qua `_managed_department_ids`): chỉ thấy đơn của phòng mình.
- Nhân viên thường: bị chặn (không thấy màn, API trả lỗi quyền).
- Đọc `hocba.attendance` trong helper dùng `.sudo()` **sau khi** đã kiểm quyền phạm vi trên đơn (gotcha self-service ACL của dự án).

## 3. Thiết kế backend (`hocba_timeoff`)

### 3.1 Model
- `hr.leave` thêm **một field duy nhất**: `x_lapsed_notified` (Boolean, default `False`) — chống báo chuông lặp. Không lưu cờ lỡ hạn hay kết quả đối chiếu (tính sống khi đọc).
- `hb.leave.notification.kind` thêm selection value `lapsed`.

### 3.2 Controller (`controllers/main.py`)
- **Helper mới** `_lapsed_info(env, leave)` → dict:
  ```
  {
    "isLapsed": bool,
    "lapsedDays": int,            # số ngày làm việc kể từ ngày bắt đầu nghỉ
    "dayChecks": [                # từng ngày nghỉ đã qua
      {"date": "2026-06-30", "worked": true, "workCredit": 1.0}
    ],
    "suggestion": "approve" | "refuse" | null,
    "workedCount": int, "checkedCount": int,
    "exempt": bool                # true với loại Nghỉ Buổi Dạy
  }
  ```
  Trả `null` khi đơn không lỡ hạn. Đọc attendance bằng `.sudo()` theo BR-L06.
- **Mở rộng `GET /approvals`**: mỗi item trong danh sách chờ duyệt thêm key `lapsed` (object trên hoặc `null`).
- **Endpoint mới** `GET /hocba-hrm/api/timeoff/lapsed-dashboard` (params: `dept` tuỳ chọn):
  - `kpi`: tổng đơn lỡ hạn, số gợi ý duyệt trễ, số đơn mâu thuẫn chấm công (gợi ý từ chối), số đơn cần xem tay, đơn lỡ lâu nhất (ngày).
  - `items`: bảng chi tiết từng đơn — nhân viên, phòng, loại nghỉ, khoảng nghỉ, số ngày lỡ, tóm tắt đối chiếu (`workedCount/checkedCount`), gợi ý, id đơn (để mở drawer/xử lý).
  - `byDepartment`: đếm đơn lỡ hạn theo phòng (cho biểu đồ).
  - Phân quyền theo BR-L06; scope trưởng phòng lọc theo `_managed_department_ids`.
- **Mở rộng `POST /request/<id>/decision`**: trước khi thực thi, nếu `_lapsed_info` báo lỡ hạn → sau khi duyệt/từ chối thành công, `message_post` note theo BR-L04. Không đổi chữ ký request.

### 3.3 Cron (`models/hb_timeoff_cron.py` + `data/ir_cron_lapsed_data.xml`)
- Method `_cron_notify_lapsed_approvals()`: search đơn `state in PENDING_STATES`, `request_date_from < today`, `x_lapsed_notified = False` → với mỗi đơn, xác định danh sách người duyệt (tái dùng logic notify sẵn có của module) → tạo notification kind `lapsed` → set `x_lapsed_notified = True`.
- Record `ir.cron` chạy hàng ngày (theo pattern `ir_cron_reminder_data.xml` sẵn có; lưu ý Odoo 19 `ir.cron` không còn `numbercall`).

## 4. Thiết kế frontend (`frontend/src/features/timeoff/`)

### 4.1 Tab Chờ duyệt (`ApprovalPanel.jsx`)
- Card đơn lỡ hạn: **badge đỏ "Lỡ hạn N ngày"** + dòng tóm tắt đối chiếu (*"Không chấm công 2/2 ngày nghỉ"* / *"Vẫn đi làm 2/2 ngày nghỉ"* / *"Đi làm 1/3 ngày — cần xem tay"* / *"Nghỉ buổi dạy — không đối chiếu"*).
- Khi có gợi ý: nút **"Xử lý theo đề xuất"** (nhãn động: *"Duyệt trễ"* / *"Từ chối"*) đặt cạnh nút Duyệt/Từ chối hiện có, có confirm trước khi thực thi. Dữ liệu lấy từ key `lapsed` của `/approvals`, không gọi thêm API.

### 4.2 Màn mới "Giám sát duyệt đơn" (`LapsedPanel.jsx`)
- Tab mới trong khu Time Off, **chỉ hiện với tài khoản quản lý/HR** (`canManage`), theo cách các panel quản lý hiện có ẩn/hiện.
- Bố cục: hàng thẻ KPI (4–5 thẻ theo `kpi`) → biểu đồ cột đơn lỡ hạn theo phòng (`byDepartment`) → bảng chi tiết (`items`) có lọc theo phòng, mỗi dòng có nút mở đơn/xử lý nhanh.
- Gọi `GET /lapsed-dashboard`; style/thành phần tái dùng pattern của `DashboardPanel.jsx` (Phase 8).

## 5. Kiểm thử (backend, DB Docker local)

File test mới trong `hocba_timeoff/tests/`, nhân viên `official` trong setUp có `identification_id` đúng 12 chữ số, mỗi người một giá trị (BR-010).

1. **Phát hiện lỡ hạn**: đơn qua ngày bắt đầu → lỡ hạn; đơn bắt đầu hôm nay/tương lai → không; đơn đã duyệt/từ chối → không.
2. **Đối chiếu**: ngày có `work_credit = 1.0` → worked; `0.5` → worked; không có bản ghi → không worked; ngày nghỉ tương lai không nằm trong `dayChecks`; ngày cuối tuần/lễ bị loại.
3. **Nửa ngày**: đơn half-day + `work_credit = 0.5` → không mâu thuẫn; + `1.0` → mâu thuẫn.
4. **Miễn trừ**: đơn loại Nghỉ Buổi Dạy → `exempt = True`, không gợi ý.
5. **Gợi ý**: 0/N worked → `approve`; N/N worked → `refuse`; lẫn lộn → `null`.
6. **Chatter**: duyệt đơn lỡ hạn → có note "Duyệt trễ…"; từ chối → note "Từ chối…"; duyệt đơn thường → không có note.
7. **Cron**: chạy lần 1 tạo đúng notification kind `lapsed` cho người duyệt, set `x_lapsed_notified`; chạy lần 2 không tạo thêm.
8. **Phân quyền dashboard**: HR thấy tất; trưởng phòng chỉ thấy phòng mình (gồm phòng con); nhân viên thường bị chặn.
9. **Hoàn quỹ**: từ chối đơn lỡ hạn qua decision → quỹ phép hoàn đúng số ngày.

Frontend kiểm thử tay qua tài khoản test (`hr.manager` thấy màn giám sát; `nv.test` không thấy).

## 6. Rủi ro & lưu ý

- **Hiệu năng**: đối chiếu chấm công query theo từng đơn lỡ hạn — số đơn lỡ hạn thực tế nhỏ nên chấp nhận; nếu sau này chậm mới cân nhắc cache (phương án C đã bị loại có chủ đích).
- **Múi giờ**: mọi phép so "hôm nay" dùng ngày theo Asia/Ho_Chi_Minh (đồng bộ với `hocba.attendance._compute_date`).
- **SPA build artifacts** commit vào repo — khi merge xung đột thì build lại từ source, không merge tay bundle.
