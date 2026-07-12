# Thiết kế: Luồng co-work chạy test tay tự động (Nhân viên · Nhận việc · Nghỉ việc)

**Ngày:** 2026-07-10 · Owner: Vu/Tan · Trạng thái: chờ duyệt spec

## 1. Mục tiêu

Tự động thực thi kịch bản trong [`docs/MANUAL_TEST_GUIDE.md`](../../MANUAL_TEST_GUIDE.md) bằng các **subagent điều khiển trình duyệt preview**, rồi kết xuất **2 file kết quả** cho người dùng duyệt:

- **File 1 — kết quả thuần** (`docs/KETQUA_TEST_TAY_2026-07-10.md`): bảng Pass/Fail/Blocked + bằng chứng dạng chữ, commit vào repo.
- **File 2 — kết quả kèm ảnh** (HTML tự chứa, ảnh nhúng data-URI, đặt **ngoài repo** trong scratchpad): người dùng tự lưu đi nơi khác.

Chạy **đầy đủ E2E** kể cả các case phá dữ liệu (tạo NV, Hoàn tất đơn nghỉ khoá tài khoản), sau đó **khôi phục** DB về trạng thái ban đầu.

## 2. Ràng buộc định hình kiến trúc

- **Một** phiên trình duyệt preview dùng chung (một `serverId`). Đăng nhập vai trò mới ghi đè session vai trò cũ → **không** chạy song song được.
- Luồng nghỉ việc có phụ thuộc thứ tự cứng trên **cùng một** đơn: NV nộp → TP duyệt cấp 1 → HR duyệt cấp 2 + Hoàn tất.
- ⟹ **Thực thi tuần tự**: 1 orchestrator điều phối + các subagent theo pha chạy nối tiếp (`run_in_background: false`). Mỗi subagent cô lập context để không phình bộ nhớ orchestrator.

## 3. Kiến trúc

### 3.1 Orchestrator (phiên Claude chính)
1. **Chuẩn bị môi trường**: đảm bảo docker Neon chạy (`docker compose -f docker-compose.yml up -d odoo`), preview 8169 bật (tái tạo `hb_tcp_proxy.py` nếu thiếu), đăng nhập thử `test_hrmanager` để xác nhận app sống.
2. **Khởi tạo output**: tạo khung File 1, thư mục ảnh scratchpad `…/scratchpad/test-img/`, ghi metadata (thời điểm, môi trường, commit hash).
3. **Điều phối pha**: spawn subagent từng pha, truyền brief (§3.3). Chờ subagent trả kết quả rồi mới spawn pha kế.
4. **Theo dõi phụ thuộc**: nếu một pha chặn (vd P3 nộp đơn Fail) → đánh dấu case downstream là **Blocked (phụ thuộc Px)**, vẫn chạy các pha độc lập còn lại.
5. **Hợp nhất**: gộp các section subagent trả về thành File 1; sinh File 2 (HTML nhúng ảnh).
6. **Khôi phục (P7)** + ghi trạng thái rollback.

### 3.2 Các pha (tuần tự)

| Pha | Đăng nhập | Case (theo guide) | Ghi chú phụ thuộc |
|---|---|---|---|
| P1 | `test_hrmanager` | §1 (danh sách/lọc/xem/CRUD) + tạo **NV mẫu A/B/C** | tạo dữ liệu gốc cho P2, P3 |
| P2 | (giữ HRM) | §2 đánh giá cổng NV B (tuần-2→tháng-1 Gia hạn→tháng-2) + thử giảng NV C | cần NV B/C từ P1 |
| P3 | `test_employee` | §3.1 nộp đơn nghỉ (mẫu D) | tạo đơn OFF cho P4/P6 |
| P4 | `test_truongphong` | §4 (vai trò TP) + §3.2 duyệt cấp 1 | cần đơn từ P3 |
| P5 | `test_giaovu` | §5 (vai trò GV) | độc lập chuỗi offboarding |
| P6 | `test_hrmanager` | §3.3 HR duyệt cấp 2 + thu tài sản + Hoàn tất + §3.4/§3.5 chuông & chặn quyền | cần đơn đã qua P4 |
| P7 | orchestrator | §6 khôi phục | luôn chạy, kể cả khi có pha Fail |

> Gom P1+P2 vào **một** subagent (cùng phiên HRM) để khỏi login lại. P6 là phiên HRM thứ hai (sau khi P3–P5 đã đổi login).

### 3.3 Giao thức subagent

**Input brief (orchestrator → subagent)** gồm:
- `serverId` của preview, URL gốc `http://localhost:8169`.
- Vai trò + tài khoản + mật khẩu (`Hocba@2026`).
- Danh sách case ID + mô tả kỳ vọng (trích từ guide).
- Dữ liệu mẫu cần điền (bảng A/B/C/D trong guide).
- Đường dẫn thư mục ảnh + file section kết quả subagent phải ghi.
- Quy tắc: đăng nhập qua **màn login SPA** (không dùng /web/login); mỗi case chụp ít nhất 1 ảnh mốc; không tự ý chạy case ngoài danh sách.

**Output (subagent → orchestrator):**
- Ghi trực tiếp `…/scratchpad/test-sections/P<x>.md` (bảng case + bằng chứng + tên file ảnh).
- Trả về orchestrator: tóm tắt Pass/Fail/Blocked của pha + cờ `blocking_failure` (true nếu hỏng bước tạo dữ liệu/đơn mà pha sau phụ thuộc).

### 3.4 Định dạng bằng chứng
Mỗi case một dòng: **ID · Mô tả · Kết quả · Bằng chứng · Ghi chú**.
- Bằng chứng chữ: trích `preview_snapshot` (nội dung/nhãn), `preview_network` (vd `POST /offboarding/action → state=mgr_approved`), `preview_console_logs` (lỗi nếu có).
- Ảnh: `preview_screenshot` lưu `test-img/P<x>_<caseId>.png`; File 1 tham chiếu tên, File 2 nhúng data-URI.
- Case Fail: ghi rõ **Kỳ vọng** vs **Thực tế**.

## 4. Định dạng file kết quả

### 4.1 File 1 — `docs/KETQUA_TEST_TAY_2026-07-10.md` (thuần chữ, commit)
- **Tóm tắt**: tổng số case, Pass/Fail/Blocked, môi trường (Neon/local), commit, thời điểm bắt đầu/kết thúc, người/agent chạy.
- **Bảng chi tiết theo pha** (P1–P6): các dòng case, cột Kết quả + Bằng chứng (chữ) + tên ảnh tương ứng.
- **Danh sách defect**: mã case, mức độ (Blocker/Major/Minor), mô tả, bước tái hiện.
- **Trạng thái khôi phục (P7)**: net DB = 0 hay còn sót gì.

### 4.2 File 2 — HTML tự chứa (scratchpad, ngoài repo)
- Đường dẫn: `…/scratchpad/KETQUA_TEST_TAY_2026-07-10.html`.
- Một file duy nhất, **ảnh nhúng data-URI** (không cần thư mục kèm) → người dùng copy đi đâu cũng mở được.
- Cùng nội dung File 1 + mỗi case hiển thị ảnh chụp inline.
- Có mục lục theo pha, badge màu Pass(xanh)/Fail(đỏ)/Blocked(xám).

## 5. Xử lý dữ liệu & khôi phục (P7)

### 5.1 Dữ liệu tạo ra khi test
- NV mẫu QA: mã `HB.QA.T1` (A), `HB.QA.B1` (B), `HB.QA.A1` (C) — thêm hậu tố ngày nếu trùng.
- Đơn nghỉ `OFF/2026/xxxx` của `test_employee`.
- Khi Hoàn tất: `hr.employee` + `res.users` + `res.partner` của `test_employee` bị archive (khoá login).

### 5.2 Khôi phục
Script XML-RPC (theo cách lần E2E 05/07, xem nhật ký `DB_TEST_DATA.md`):
1. `active=True` lại cho employee/user/partner của `test_employee` (tra cứu uid/eid theo `login=test_employee@hocba.vn` lúc chạy — không hardcode) → login lại được.
2. Xoá/huỷ đơn `OFF/2026/xxxx` sinh trong lượt test.
3. Archive hoặc xoá các NV mẫu QA đã tạo.
4. Verify: `test_employee` đăng nhập lại OK; đếm bản ghi offboarding về mức trước test.
Ghi kết quả từng bước vào File 1 §Trạng thái khôi phục.

> Nếu khôi phục thất bại một phần → đánh dấu **⚠ CẦN CAN THIỆP TAY** ở đầu File 1, liệt kê bản ghi còn sót.

## 6. Xử lý lỗi khi chạy

- Subagent gặp lỗi thao tác (không tìm thấy nút, timeout): retry 1 lần, nếu vẫn lỗi → ghi case **Fail** kèm ảnh + log, tiếp tục case sau.
- `blocking_failure=true` (không tạo được NV B hoặc không nộp được đơn): orchestrator đánh dấu các case phụ thuộc **Blocked** và bỏ qua pha phụ thuộc, **vẫn** chạy P5 (độc lập) và P7 (khôi phục).
- Mọi trường hợp đều phải chạy **P7** để không để rác/khoá tài khoản.

## 7. Tiêu chí hoàn thành

- [ ] File 1 tồn tại, đủ 6 pha + defect + trạng thái khôi phục, commit.
- [ ] File 2 (HTML) tồn tại trong scratchpad, mở được offline, ảnh hiển thị inline.
- [ ] P7 chạy xong; `test_employee` đăng nhập lại được; net DB ≈ 0 (hoặc nêu rõ sai lệch).
- [ ] Báo cáo tóm tắt cho người dùng: pass rate + defect nổi bật + đường dẫn 2 file.

## 8. Ngoài phạm vi (YAGNI)

- Không test các module khác (Chấm công, Nghỉ phép, Lương, Tuyển dụng).
- Không dựng CI/tự động hoá lặp lại; đây là một lượt chạy theo yêu cầu.
- Không chèn assertion tự động vào backend; xác minh qua quan sát UI + network.
