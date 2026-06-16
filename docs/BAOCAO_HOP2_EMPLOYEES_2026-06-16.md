# Báo cáo phân tích Họp #2 — Module Employees (`hocba_employees`)

> Ngày họp/ghi nhận: 2026-06-16 · Nguồn: 3 file ghi âm "Trường Đại Học FPT" (#1, #2, #4) + transcript.
> Phạm vi báo cáo: **trọng tâm module nhân sự `hocba_employees` mà nhóm mình quản lý**. Các phần chấm công / nghỉ phép thuộc module khác chỉ ghi chú ở cuối.

---

## 0. Ma trận phân quyền chốt trong họp

| Vai trò | Quyền |
|---|---|
| **Admin** | Cao nhất, xem mọi phòng ban, sửa hệ thống. Là **tài khoản theo vai trò** (role-based), bàn giao được. |
| **HR (Nhân sự)** | Cao nhất về mảng nhân viên: kiểm soát phản hồi & quy trình, update chức vụ/vị trí/lương/trạng thái, xem lương mọi người. |
| **Quản lý (Trưởng phòng/bộ phận)** | Duyệt nghỉ phép, đi sớm về muộn **của nhân viên thuộc phòng ban mình** (phân theo **phòng ban**, không theo cá nhân). Tương đương HR nhưng chức năng khác. |
| **Nhân viên** | Tài khoản cá nhân: dashboard tổng quan, lịch sử đơn từ, báo cáo, danh sách nghỉ **của chính mình**. |

➡️ **Hệ quả lớn nhất:** tài khoản quản lý (Admin/HR/Giáo vụ) phải **tách rời** khỏi hồ sơ cá nhân của người đang giữ vai trò đó (xem mục 1).

---

## 1. 🔴 P0 — Tách "tài khoản quản lý" khỏi "hồ sơ cá nhân" (thay đổi kiến trúc UI lớn nhất)

**Khách yêu cầu (rõ ràng, nhấn mạnh nhiều lần):**
- Giao diện **quản lý nhân sự** chỉ để **quản lý**, KHÔNG chứa hồ sơ/chấm công cá nhân của người đang đăng nhập.
- Phần **cá nhân** của người làm HR/quản lý đi vào **luồng nhân viên bình thường** như mọi người khác.
- Lý do: người giữ vai trò không cố định. Khi đổi người, không được xóa/sửa dữ liệu cá nhân của người cũ để gán cho người mới. Tài khoản vai trò phải reassignable.

**Hiện trạng:** SPA/giao diện đang gộp "hồ sơ của tôi" vào màn quản lý → khách bảo "bị rối".

**Việc cần làm:**
- Tách 2 luồng: (a) **Màn quản lý** (danh sách NV, duyệt, cấp phát…) gate theo quyền; (b) **Màn cá nhân "Hồ sơ của tôi"** — chung một luồng với nhân viên thường.
- Bỏ panel cá nhân khỏi màn quản lý.
- Tài khoản vai trò = role-based (gán group, không nhúng dữ liệu cá nhân).

**Phía code:** chủ yếu ở **frontend SPA** (`frontend/src/`) + thiết kế nhóm quyền. Model `hr.employee` giữ nguyên 1 bản ghi/người (đã đúng). Anh Linh đã đồng ý "tách ra dễ hơn, nhanh hơn".

---

## 2. Đối chiếu chi tiết từng quyết định ↔ code hiện tại

Ký hiệu: ✅ đã đúng · ⚠️ cần sửa · ➕ làm mới · 🔁 đảo ngược quyết định cũ · ❓ cần làm rõ.

### F-001 — Định danh & hồ sơ

| # | Quyết định họp | Hiện trạng code | Hành động | Ưu tiên |
|---|---|---|---|---|
| 1 | Mã NV = **mã chấm công + STT** (vd `HB.001`) | `x_employee_code`, sinh từ sequence `hocba.employee.code`, định dạng `HB.xx` ([hr_employee.py:15](../custom-addons/hocba_employees/models/hr_employee.py)) | ✅ Xác nhận prefix/padding khớp "mã chấm" thật | P2 |
| 2 | Đổi nhãn **"Nhập việc" → "Nhận việc"** (N‑H‑Ậ‑N) | Có nhãn "nhập việc" ở UI | ⚠️ Sửa nhãn (view + SPA), rà toàn bộ chuỗi | P1 |
| 3 | **Ảnh hồ sơ**: cho người dùng tự up ảnh | Có `x_face_image` (nhận diện) + avatar chuẩn `image_1920` | ⚠️ Bật self-upload ảnh ở màn "Hồ sơ của tôi" | P2 |

### F-003 — Người phụ thuộc

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 4 | Người phụ thuộc: **tự thêm, không cần duyệt** | Model `hr.employee.dependent`, O2M `x_dependent_ids` đã có | ⚠️ Mở quyền self-service cho nhân viên tự thêm trong hồ sơ cá nhân | P2 |

### F-004/F-005 — Thử việc & cổng đánh giá (luồng **nhân viên**)

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 5 | Mốc thử việc: **2 tuần, 1 tháng, 2 tháng** — "có bạn hết thử việc sau 1 tháng" | Chỉ có **2 cổng**: tuần‑2 & tháng‑2 ([hr_employee.py:111-139](../custom-addons/hocba_employees/models/hr_employee.py)) | ⚠️ **Thiếu mốc 1 tháng** + cho phép lên chính thức linh hoạt sau 1 tháng | **P0** |
| 6 | Kết quả cổng thêm lựa chọn **"Gia hạn"** (pass / không pass / gia hạn) | `x_eval_2w_result`/`x_eval_2m_result` chỉ `[draft, pass, fail]` | 🔁 Thêm `extend` + nhánh tự động hóa gia hạn | **P0** |
| 7 | Tách luồng **nhân viên** vs **giáo viên** (giáo viên KHÔNG qua 2 tuần) | Fields cả 2 cùng model; có thử giảng F‑008 | ✅ Cấu trúc OK; ⚠️ tách rõ ở UI | P1 |

> 🔁 **Cảnh báo đảo ngược spec:** spec v2.1 đã chốt **GĐ‑03: tuần‑2 fail → cho nghỉ, KHÔNG gia hạn** (Vu quyết, dựa data Lark). Code đang xử lý đúng theo đó ([hr_employee.py:562-570](../custom-addons/hocba_employees/models/hr_employee.py), comment "GĐ-03: không gia hạn"). **Khách họp #2 yêu cầu CÓ "gia hạn"** → cần xác nhận lại với Vu và cập nhật spec trước khi sửa code, vì đây là mâu thuẫn trực tiếp.

### F-006 — Tài sản

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 8 | 2 nhóm tài sản: **mặc định** (tự cấp cho NV, HR không thêm) + **tự thêm** (HR thêm sau) | `hocba.asset.type` 11 loại seed, có `active`, **chưa có cờ default** ([hocba_asset_type.py](../custom-addons/hocba_employees/models/hocba_asset_type.py)) | ➕ Thêm `x_is_default` + tự cấp tài sản mặc định khi onboarding | P1 |
| 9 | HR **thêm mới loại tài sản** | Model cho phép tạo, nhưng cần menu/quyền | ➕ Thêm menu quản lý "Loại tài sản" cho HR | P1 |

### F-007 — Lịch sử thăng tiến & lương

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 10 | Lịch sử thăng tiến **không cho xóa** | `unlink()` raise UserError ([hr_promotion_history.py:85](../custom-addons/hocba_employees/models/hr_promotion_history.py)) | ✅ Đã đúng | — |
| 11 | "Thăng tiến" bao gồm **lúc vào làm** và **lên chính thức** (không chỉ lên chức) | Hiện chỉ tạo bản ghi thủ công | ⚠️ Tự sinh bản ghi khi: nhận việc + chuyển chính thức | P1 |
| 12 | Snapshot phải đủ: **ngày, chức danh, hình thức, trạng thái, phòng ban, lương** | Có: date, job, dept, wage, reason, QĐ. **Thiếu**: hình thức làm việc (`x_work_form`), trạng thái (`x_employment_status`) tại thời điểm | ⚠️ Thêm field snapshot hình thức + trạng thái | P1 |

### Lương & bảo mật

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 13 | **Chỉ HR (+ admin to) xem lương mọi người**; mỗi người xem **lương của chính mình**; người khác không xem của ai | MST/BHXH có `groups='hr.group_hr_manager'`; **lương trên promotion (`to_wage`) chưa giới hạn group** → ai vào list cũng thấy | ⚠️ Field-security: lương bản thân cho self, toàn bộ cho HR; khóa `to_wage`/`from_wage` theo group + record rule | **P0** |
| 14 | Đổi lương **bắt buộc lý do + đính link bằng chứng** (link đánh giá/KPI/kết quả) | Constraint đã bắt buộc `reason` khi đổi lương ([hr_promotion_history.py:49](../custom-addons/hocba_employees/models/hr_promotion_history.py)); **chưa có field link bằng chứng** (chỉ `decision_ref` dạng Char) | ➕ Thêm `x_evidence_url`/attachment, bắt buộc khi đổi lương | P1 |

### F-008/F-009 — Chứng chỉ & phân cấp

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 15 | Gom 2 nhóm: **Bằng chuyên môn** + **Bằng ngôn ngữ/ngoại ngữ** (giữ "ngôn ngữ" vì GV tiếng Trung) | Đang là "Tiếng Trung" + "Sư phạm ngoại ngữ" ([hr_skill_data.xml](../custom-addons/hocba_employees/data/hr_skill_data.xml)) | ⚠️ Đổi nhãn/gom nhóm: Sư phạm → chuyên môn; Tiếng Trung → ngôn ngữ | P1 |
| 16 | Nhân sự IELTS **KHÔNG add vào** (công ty khác) | — | ✅ Giữ generic "ngôn ngữ", không thêm IELTS | — |
| 17 | **Phân cấp** cho **cả giáo viên (sơ/trung/cao) lẫn nhân viên (senior/junior)**; cấp GV dùng để **lọc xếp lớp** | GV có skill level sơ/trung/cao; **NV chưa có field seniority** | ➕ Thêm cấp độ nhân viên (senior/junior…); expose cấp GV để lọc | P1 |

### Bắt buộc dữ liệu & phân quyền nhập liệu

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 18 | Lên chính thức **bắt buộc đủ thông tin**, tối thiểu **CCCD + MST** | BR‑010 bắt buộc **MST + BHXH** ([hr_employee.py:352-364](../custom-addons/hocba_employees/models/hr_employee.py)); **CCCD chưa nằm trong điều kiện** | ⚠️ Thêm CCCD (identification_id trên hr.version) vào điều kiện official | P1 |
| 19 | **Nhân sự chỉ cung cấp thông tin đầu vào**; chức vụ/vị trí/lương/trạng thái **do HR update** | Có chặn status→official & gate fields cho non‑HR; **chưa khóa job/lương cho nhân viên tự sửa** | ⚠️ Record rule/readonly: nhân viên sửa input của mình, không sửa job/lương/trạng thái | P1 |

### Màn quản lý theo vai trò

| # | Quyết định | Hiện trạng | Hành động | Ưu tiên |
|---|---|---|---|---|
| 20 | **Giáo vụ** chỉ xem/quản lý **giáo viên** | Chưa có group/record-rule scope theo loại NV | ➕ Group "Giáo vụ" + record rule domain `x_employee_type = giáo viên` | P1 |
| 21 | Màn HR **không có panel chấm công** & **không duyệt đơn chấm công** | Chấm công thuộc `hocba_attendance` (DongHoangAnh) | ⚠️ Ẩn panel/nút duyệt chấm công ở giao diện HR (phối hợp) | P1 |
| 22 | **Quản lý** duyệt nghỉ/đi sớm về muộn theo **phòng ban** | Gate hiện dựa `parent_id` (quản lý trực tiếp) | ⚠️ Mở rộng scope duyệt theo **phòng ban** | P2 |

---

## 3. 🔁 Mâu thuẫn cần giải quyết trước khi code

1. **"Gia hạn" thử việc (mục 6) vs GĐ‑03 đã chốt "không gia hạn".** → Hỏi lại Vu + cập nhật spec v2.1. **Đừng sửa code cho tới khi chốt.**
2. **Mốc "1 tháng" (mục 5).** Spec/data Lark cho median 61 ngày (2 mốc). Khách nói có người hết thử việc sau 1 tháng → cần thêm mốc giữa hoặc cho phép chốt official sớm. Làm rõ: 1 tháng là **mốc đánh giá bắt buộc** hay chỉ **đường tắt lên chính thức**?

---

## 4. ❓ Câu hỏi cần làm rõ với khách (chưa đủ thông tin trong họp)

- **Nghỉ phép / lịch sử nghỉ**: cuối họp bị gián đoạn kỹ thuật, chưa bàn xong. (Liên quan `hb_timeoff_*`, `hr_holidays_modern` — cross-team.)
- "**Admin to**" xem lương: là 1 nhóm quyền riêng hay chính là Admin hệ thống?
- Tài sản mặc định: **danh sách cụ thể** loại nào là default tự cấp (trong 11 loại)?
- Phân cấp nhân viên (senior/junior): **bộ cấp độ** gồm những mức nào?

---

## 5. Đề xuất thứ tự thực hiện

1. **Chốt 2 mâu thuẫn** (mục 3) với Vu/khách → cập nhật spec v2.1.
2. **P0**: (a) tách tài khoản quản lý ↔ cá nhân (SPA); (b) bảo mật lương; (c) mốc 1 tháng + "gia hạn" (sau khi chốt).
3. **P1**: snapshot thăng tiến đầy đủ + auto-sinh bản ghi; tài sản default/tự thêm + menu loại tài sản; gom nhóm chứng chỉ; phân cấp NV; CCCD bắt buộc; group Giáo vụ; link bằng chứng đổi lương; đổi nhãn "Nhận việc".
4. **P2**: self-upload ảnh/người phụ thuộc; scope duyệt theo phòng ban; xác nhận mã NV.

---

---

## 6. ✅ Đã triển khai (backend `hocba_employees`, verify trên Docker 2026-06-16)

> Đã làm theo yêu cầu khách, **gồm cả 2 điểm ngược spec cũ** (gia hạn + mốc 1 tháng). Module cài sạch từ đầu OK; smoke-test luồng cổng + snapshot + ràng buộc đều đạt.

- **Cổng "Gia hạn"** (`extend`) cho cả 3 cổng tuần-2 / tháng-1 / tháng-2 + tự động hóa nhánh gia hạn (không terminate, hẹn tái đánh giá).
- **Mốc tháng-1 mới** (`x_eval_1m_*`): tuần-2 Đạt → mở tháng-1; tháng-1 Đạt → **lên chính thức sớm**; Gia hạn → tiếp tục tháng-2. Timeline 6 mốc + CRON nhắc tháng-1.
- **Snapshot thăng tiến**: thêm `x_change_type`, `x_work_form`, `x_employment_status`; **auto-sinh** bản ghi khi **nhận việc** (create) và **lên chính thức**; thêm `x_evidence_url` **bắt buộc khi đổi lương**; field lương giới hạn `groups="hr.group_hr_manager"`.
- **Tài sản**: `x_is_default` + seed 8 loại mặc định; **tự cấp tài sản mặc định** khi qua cổng tuần-2; menu Loại tài sản đã có.
- **Chứng chỉ**: gom nhóm thành **"Bằng ngôn ngữ"** + **"Bằng chuyên môn"**.
- **Phân cấp** `x_seniority_level` (sơ/trung/cao) cho NV & GV.
- **CCCD bắt buộc** khi lên chính thức (cùng MST + BHXH).
- **Group "Giáo vụ"** + record rule chỉ xem giáo viên (`x_employee_type_id.code='teacher'`) + ACL.
- **Đổi nhãn "Nhập việc" → "Nhận việc"** trong SPA (`frontend/src/` + `hocba_hrm/static/src/js/`).

## 7. ⏭️ Chưa làm (cần đợt sau / cross-team)

- 🔴 **Tách tài khoản quản lý ↔ cá nhân** (mục 1) — việc lớn ở **SPA** (`frontend/src/`), chưa đụng tới.
- Ẩn panel/duyệt chấm công ở giao diện HR (phối hợp `hocba_attendance`).
- Mở rộng scope duyệt nghỉ/đi sớm về muộn **theo phòng ban** cho Quản lý (mục 22).
- Self-upload ảnh + người phụ thuộc ở "Hồ sơ của tôi" (cần phần SPA cá nhân ở trên).
- Nghỉ phép / lịch sử (cuối họp gián đoạn — chưa rõ yêu cầu).
- **Cập nhật spec v2.1** để khớp 2 thay đổi đảo ngược (gia hạn + mốc 1 tháng).

> ⚠️ Lưu ý migration: vài seed dùng `noupdate="0"` (tên nhóm chứng chỉ, cờ tài sản mặc định) để áp được trên DB đã cài khi `-u hocba_employees`. Constraint CCCD/MST/BHXH khi lên chính thức sẽ **chặn** NV cũ thiếu giấy tờ — cần bổ sung dữ liệu trước khi chuyển chính thức.
