# Báo cáo rà soát — Phân quyền, Duyệt thử việc & Hồ sơ NV

- **Ngày:** 2026-06-26
- **Người rà soát:** Claude (theo yêu cầu của Tân)
- **Phạm vi:** Phân quyền theo vai trò · luồng duyệt cổng thử việc (Nhóm B) & thử giảng (Nhóm A) · hiển thị trường hồ sơ · 2 hiện tượng người dùng báo.
- **Phương pháp:** Đọc code (`hocba_hrm/controllers/main.py`, `hocba_employees/models/hr_employee.py`, SPA `frontend/src/...`) + kiểm dữ liệu thật trên app local (DB `hocba_hrm`, 17 NV) khi đăng nhập `test_hrmanager` + tái hiện 1 ca từ chối thật.
- **Tài khoản đang test:** `test_hrmanager@hocba.vn` → `isHrManager=true, isHrUser=true, isAdmin=false, hasEmployee=false`.

---

## A. Ma trận phân quyền thực tế (đang chạy)

### A.1 Ai thấy màn nào (SPA — `frontend/src/app/Shell.jsx`)
| Màn | Điều kiện (`need`) | Ai thấy |
|---|---|---|
| Dashboard, Nhân viên, Nhận việc, Chấm công, Nghỉ phép, **Bảng lương**, **Tuyển dụng** | `manage` = `canManage` | Admin, HR Manager, HR User, **Giáo vụ, Trưởng phòng** |
| Tài khoản, Phòng ban | `hr` | Admin, HR User/Manager |
| Chấm công (cá nhân), Nghỉ phép (cá nhân), **Hồ sơ của tôi** | `self` = KHÔNG phải tài khoản vai trò | Chỉ **nhân viên thường** |

→ Tài khoản vai trò (Admin/HR/Giáo vụ/Trưởng phòng) **không** thấy "Hồ sơ của tôi" (đúng chủ trương họp #2: tách tài khoản quản lý ↔ cá nhân).

### A.2 Ai được DUYỆT cái gì
| Hành động | Điều kiện thực tế (code) | Ghi chú |
|---|---|---|
| **Cổng thử việc** (Nhóm B) `api_employee_gate` + `hr_employee.write` | **HR Manager** *hoặc* quản lý trực tiếp (`parent_id.user_id`) *hoặc* trưởng phòng ban của NV | **KHÔNG** gồm HR User thuần, **không** gồm Giáo vụ (trừ khi họ là TP/quản lý trực tiếp) |
| **Thử giảng** (Nhóm A) `api_employee_trial` | **`is_hr`** (HR User *hoặc* HR Manager) | **KHÔNG** gồm Giáo vụ, **không** gồm Trưởng phòng (trừ khi cũng là HR) |
| **Đợt đánh giá thăng tiến** (mới) | `_can_eval_emp` (HR Manager / quản lý trực tiếp / TP) | |
| **Tạo bản ghi thăng tiến** | Chỉ **HR Manager** | |

> ⚠️ **Hai luồng đánh giá dùng 2 mô hình quyền khác nhau:** cổng thử việc cho **TP/quản lý** nhưng **không cho HR User**; thử giảng cho **HR User** nhưng **không cho TP/Giáo vụ**. Không nhất quán (xem F-2, F-3).

---

## B. Hai hiện tượng người dùng báo — nguyên nhân gốc

### B.1 "Duyệt Đạt nhận việc thỉnh thoảng bị từ chối" — ĐÃ TÁI HIỆN
**Tái hiện thật:** `POST /api/employee/21/gate {gate:'1m', result:'pass'}` →
`HTTP 403`, body `{"error":"rejected","message":"Chỉ đánh giá cổng tháng-1 sau khi cổng tuần-2 đã Đạt."}`.

**Nguyên nhân gốc (model `_check_gate_rules` + automation `_hocba_make_official`):** Khi ghi kết quả cổng, model áp loạt ràng buộc; vi phạm bất kỳ điều nào → `ValidationError` → endpoint trả `rejected`. Các điều kiện hay làm "Đạt" bị chặn:
1. **Chưa có `Ngày bắt đầu thử việc`** → mọi kết quả cổng bị chặn. *(Live: rất nhiều NV `hasStart=false`: id 5,7,22–26,39,40,41,42,47.)*
2. **Sai trình tự:** cổng tháng-1 chỉ mở sau tuần-2 = Đạt; **cổng tháng-2 chỉ mở khi tháng-1 = "Gia hạn"** (mô hình 3 mốc M-02). Bấm Đạt sai mốc → từ chối.
3. **BR-010 khi lên chính thức:** tháng-1/tháng-2 Đạt → tự chuyển `official` → bắt buộc **CCCD (12 số) + MST + BHXH**; thiếu → từ chối.

**Lỗi UX khuếch đại (đây là phần khiến bạn thấy "ngẫu nhiên, không rõ lý do"):**
- Endpoint trả các từ chối nghiệp vụ bằng **HTTP 403** (lẽ ra nên 400/422; 403 = "không có quyền").
- FE `GateAction` ([EmployeeDrawer.jsx:235](frontend/src/features/employees/EmployeeDrawer.jsx:235)) gặp **bất kỳ 403** nào đều hiện chung một câu: *"Không có quyền hoặc thao tác bị từ chối (kiểm tra điều kiện cổng)."* → **nuốt mất message thật**. Người duyệt không bao giờ thấy lý do cụ thể.

→ **Kết luận:** Việc từ chối (phần lớn) là **đúng nghiệp vụ**, nhưng hệ thống **giấu lý do** nên bị hiểu nhầm là lỗi/ngẫu nhiên.

### B.2 "HR không xem được cổng bên giáo viên" — ĐÃ XÁC ĐỊNH
**Nguyên nhân gốc:** Việc hiện cổng đánh giá **không phụ thuộc vai trò người xem** (HR hay không) mà phụ thuộc **cách phân loại NV**:
- Cổng thử việc 2 mốc (Nhóm B) chỉ hiện khi `x_position_type ∈ {staff, manager}` **và** `x_work_form == 'offline'`.
- Khối thử giảng (Nhóm A) chỉ hiện khi `x_work_form == 'online'` **hoặc** `x_employment_status ∈ {parttime, ctv, advisor}`.

→ NV nào **không lọt cả hai** điều kiện sẽ **không có cổng nào** — với *mọi* người xem, kể cả HR. *(Live: id 39 "Test Giáo Vụ" và id 42 "Test Trưởng Phòng" có `work_form=""` (rỗng) → `isGroupB=false`, `trial=none` → không hiện cổng.)*

- "HR là to nhất" **không liên quan**: HR vẫn xem được hồ sơ (in-scope), nhưng phần cổng bị ẩn do **phân loại NV**, không phải do quyền.
- Giáo viên online thật (id 40/41 "GV Tiếng Trung A/B" — online/ctv) **có** hiện khối thử giảng và HR chấm được. Vấn đề rơi vào các bản ghi có `work_form` rỗng/sai (các tài khoản vai trò seed thiếu Hình thức), hoặc giáo viên cấu hình offline.
- **Lệch trục phân loại:** hệ thống có `x_employee_type_id.code == 'teacher'` (dùng cho phạm vi Giáo vụ) **nhưng logic cổng lại dựa trên `work_form`/`position_type`** — hai trục không khớp nhau. Một "giáo viên" offline có thể bị xem là Nhóm B (cổng thử việc) thay vì thử giảng.

---

## C. Các phát hiện khác / thiếu sót / sai logic

| # | Phát hiện | Mức | Bằng chứng |
|---|---|---|---|
| **F-1** | **Cổng thử việc (Nhóm B) KHÔNG có ô nhập "Ghi chú đánh giá"** — chỉ có 3 nút Đạt/Gia hạn/Không đạt. Không thể ghi nhận đánh giá khi duyệt. (Thử giảng thì CÓ ô nhận xét.) Spec FUNC-EMP-004 muốn "ghi chú bắt buộc khi Đạt" — **chưa làm** (model cũng không bắt buộc note khi pass). | Cao | `GateAction` không có input note; `_check_gate_rules` không kiểm note |
| **F-2** | **Giáo vụ KHÔNG chấm được thử giảng** (`api_employee_trial` yêu cầu `is_hr`; Giáo vụ không thuộc `hr.group_hr_user`). Vai trò sinh ra để quản lý giáo viên lại không đánh giá được giáo viên. | Cao | [main.py:1933](custom-addons/hocba_hrm/controllers/main.py:1933) |
| **F-3** | **HR User (không phải Manager) KHÔNG duyệt được cổng thử việc** (`_can_eval_emp` + `write` chỉ nới cho HR **Manager**/quản lý/TP). Trái cảm nhận "HR = tất cả". | Trung bình | [main.py:1639](custom-addons/hocba_hrm/controllers/main.py:1639), [hr_employee.py:601](custom-addons/hocba_employees/models/hr_employee.py:601) |
| **F-4** | **Menu Bảng lương & Tuyển dụng hiện cho Giáo vụ + Trưởng phòng** (chỉ cần `canManage`). Lương là dữ liệu nhạy cảm — cần kiểm API payroll có chặn theo vai trò không (chưa kiểm tầng API trong rà soát này). | Trung bình | [Shell.jsx:18-19](frontend/src/app/Shell.jsx:18) |
| **F-5** | **NV đã `official` vẫn hiện timeline cổng Nhóm B "trống"** (id 22–26: official, `hasStart=false`, cổng draft). Bấm duyệt → từ chối (thiếu ngày thử việc). Gây nhiễu. | Trung bình | Live data |
| **F-6** | **Từ chối nghiệp vụ trả HTTP 403** (nên 400/422) → lẫn với lỗi quyền; kết hợp F-1/UX gây khó hiểu. | Trung bình | [main.py:1920](custom-addons/hocba_hrm/controllers/main.py:1920) |
| **F-7** | **Khoảng trống dữ liệu (seed):** nhiều NV thử việc thiếu `Ngày bắt đầu thử việc`; tài khoản vai trò thiếu `Hình thức`; **toàn bộ 17 NV chưa có dữ liệu Ngân hàng/Số TK**; một số NV thiếu CCCD/MST/BHXH nên không lên chính thức được. | Trung bình | Live data |

---

## D. Trường hồ sơ — đã đúng/chuẩn chưa?
- ✅ Validate: MST (10/13 số), BHXH (10 số), CCCD 12 số bắt buộc khi `official` (BR-010), ngày cấp CCCD hợp lệ.
- ✅ **Lương / Ngân hàng / Số TK** nay đã hiển thị ở tab Thông tin (sửa hôm nay) + resolve tên NH từ payroll. Nhưng **dữ liệu ngân hàng rỗng** trên toàn bộ NV demo (chưa nhập) → hiển thị "—".
- ⚠️ Trục phân loại NV chưa nhất quán (employee_type vs work_form/position) — xem B.2.

---

## E. Đề xuất sửa (ưu tiên)
1. **(Cao, nhỏ)** FE `GateAction`: hiện **message thật** từ endpoint thay vì câu chung; + đổi endpoint trả **400/422** cho từ chối nghiệp vụ, giữ **403** chỉ cho thiếu quyền. → Giải quyết phần lớn cảm giác "từ chối ngẫu nhiên".
2. **(Cao)** Cổng thử việc: thêm **ô Ghi chú** khi duyệt; chốt có bắt buộc note khi "Đạt" không (theo spec).
3. **(Cao)** Xử lý NV không lọt phân loại cổng: khi `work_form` rỗng/không khớp → hiện hướng dẫn rõ ("Cần đặt Hình thức / phân loại") thay vì ẩn trắng; cân nhắc dùng `employee_type=teacher` để quyết định Nhóm A/B.
4. **(Trung bình)** Thống nhất quyền duyệt: quyết định Giáo vụ/HR User có được duyệt cổng/thử giảng không, rồi đồng bộ `api_employee_gate` ↔ `api_employee_trial`.
5. **(Trung bình)** Không hiện cổng "thao tác được" cho NV đã `official`.
6. **(Trung bình)** Kiểm tầng API Payroll/Recruitment có chặn Giáo vụ/TP không (F-4).
7. **(Seed)** Bổ sung `Ngày bắt đầu thử việc`, `Hình thức`, CCCD/MST/BHXH cho NV thử việc; seed vài giá trị Ngân hàng để demo.

---

## F. Ghi chú kiểm thử
- Rà soát chủ yếu ở **tầng code + dữ liệu thật** (đăng nhập đa vai trò bị giới hạn do không tự nhập mật khẩu). Ma trận quyền ở mục A là **kết luận từ code** (đáng tin cho "ai được làm gì").
- Ca từ chối B.1 đã **tái hiện thật** và xác nhận **không gây thay đổi dữ liệu** (rollback đúng; emp 21 vẫn `draft`).
- Khuyến nghị bổ sung **test backend tự động** cho ma trận quyền (tạo user từng vai trò, assert duyệt được/không) — hiện chưa có test phủ phần này.
