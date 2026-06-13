---
# **TÀI LIỆU ĐẶC TẢ HỆ THỐNG ERP ODOO 19.0**
## **PHÂN HỆ: EMPLOYEES (QUẢN LÝ NHÂN SỰ) — TRUNG TÂM TIẾNG TRUNG HỌC BÁ**

> **Phiên bản:** 2.1 — Tổng hợp sau buổi họp xác nhận yêu cầu với khách hàng.  
> **Phạm vi:** Phân hệ *Employees* — Hồ sơ & Vòng đời nhân sự. Payroll, Attendance, Recruitment chỉ nêu ở mức ranh giới liên thông.  
> **Cơ sở khảo sát:** Lark hiện hành (`Học bá education.xlsx`, 168 hồ sơ thực tế), 02 sơ đồ BPMN (AS-IS & TO-BE), tài liệu đặc tả v1.0.

---

## **BIÊN BẢN CẬP NHẬT (v1.0 → v2.1)**

| # | Hạng mục thay đổi | Lý do |
|---|---|---|
| C-01 | Tách 2 luồng Onboarding: Nhân viên VP/Sales vs Giảng viên | Khách xác nhận "luồng nhân sự và giáo viên hơi khác nhau" |
| C-02 | Bổ sung 2 cổng thử việc (tuần-2 → cấp thiết bị; tháng-2 → lên chính thức) | Yêu cầu mới sau họp |
| C-03 | Bổ sung "Hồ sơ tổng quan" (Overview Profile) | Thiếu trong BPMN v1.0 |
| C-04 | Chuẩn hóa phân loại nhân sự theo 2 trục (Lark thực tế) | Dữ liệu thực tế không khớp phân loại 3 nhóm cũ |
| C-05 | Bổ sung nghiệp vụ Quản lý Tài sản gắn với cổng tuần-2 | Lark có sổ tài sản 8.3 + checklist nhúng trong hồ sơ |
| C-06 | Tách 2 luồng Offboarding: Nghỉ thử việc (4 bước) vs Nghỉ việc CT (7 bước có GĐ duyệt) | Lark đã có 2 quy trình tách biệt |
| C-07 | Bổ sung Phụ lục Data Dictionary (Lark → Odoo) | Phục vụ dev migrate dữ liệu |
| C-08 | Bổ sung Chương 7 — Functional Specification (9 chức năng custom) | Làm rõ chi tiết để dev implement ngay |
| C-09 | Cập nhật BPMN TO-BE thành sơ đồ end-to-end 2 hàng cuộn (v2.1) | Gộp 5 khối rời thành 1 sơ đồ liền mạch theo phản hồi |

---

# **CHƯƠNG 1 — PHÂN LOẠI ĐỐI TƯỢNG NHÂN SỰ**

## **1.1. Mô hình Phân loại theo Dữ liệu Thực tế (2 Trục)**

Bản v1.0 chia 3 nhóm cứng (Academic / Sales / Back-office). Khảo sát dữ liệu Lark thực tế (168 hồ sơ) cho thấy Học Bá phân loại theo **nhiều trục độc lập**:

* **Trục 1 — Hình thức làm việc (`Hình thức`):** `Offline` | `Online`
* **Trục 2 — Tình trạng / Loại hợp đồng (`Tình trạng`):** `Thử việc` | `Chính thức` | `TTS` | `Part-time` | `CTV` | `Cố vấn` | `Nghỉ việc`
* **Trục 3 — Loại vị trí (`Loại vị trí`):** `Quản lý` | `Nhân viên` | `CTV` | `Freelancer` | `Cố vấn`
* **Trục 4 — Phòng ban (`Phòng Ban`):** `Marketing` | `Sản phẩm (R&D_SP)` | `Kinh doanh (Sale)` | `Vận hành` | `Kế toán_HCNS` | `BOD`

> Phân quyền xem hồ sơ, lọc báo cáo và chọn gói Plan Onboarding/Offboarding dựa trên tổ hợp các trục này (chủ yếu Trục 2 và Trục 4).

## **1.2. Hai Nhóm Vận hành Chính & Sự Khác biệt Vòng đời**

Đứng ở góc độ **thiết kế luồng vòng đời**, chỉ cần phân biệt 2 nhóm:

| Tiêu chí | **Nhóm A — Giảng viên / Trợ giảng (Academic)** | **Nhóm B — Nhân viên VP & Sales (Back-/Front-office)** |
|---|---|---|
| Hình thức điển hình | Phần lớn `Online`, thỉnh giảng / `Freelancer` / `Part-time` | Phần lớn `Offline`, `Full-time` |
| Loại hợp đồng | HĐ thỉnh giảng / cộng tác | HĐ thử việc → HĐ chính thức |
| Cấp tài nguyên | Tài khoản dạy (Zoom Pro/ClassIn), kho slide — **cấp sớm ngay đầu** | Thiết bị văn phòng — **cấp sau khi đạt cổng tuần-2** |
| Cổng đánh giá | Đánh giá thử giảng (phương pháp) trong tuần đầu | Cổng tuần-2 (cấp thiết bị) + Cổng tháng-2 (lên chính thức) |
| Nghiệp vụ trọng tâm | Ma trận kỹ năng (HSK/HSKK/Sư phạm), cảnh báo hạn chứng chỉ | Thử việc theo mốc, tài sản, KPI, luân chuyển cơ sở |

> **Giả định GĐ-01 cần khách xác nhận:** GV có áp dụng cổng thử việc theo mốc không, hay chỉ đánh giá thử giảng một lần? Thời hạn HĐ thỉnh giảng?

---

# **CHƯƠNG 2 — HIỆN TRẠNG VÀ QUY TRÌNH VẬN HÀNH THỰC TẾ (AS-IS)**

## **2.1. Phân loại Đối tượng Nhân sự (User Persona & Staff Categorization)**

*(Đã chuyển lên Chương 1 — xem mục 1.1 và 1.2)*

Trước khi triển khai Odoo, toàn bộ nghiệp vụ nhân sự đang vận hành trên **Hệ sinh thái Lark (Base/Sheet)**. Các bảng dữ liệu cốt lõi liên quan phân hệ Employees:

| Bảng Lark | Vai trò thực tế | Ánh xạ Odoo |
|---|---|---|
| **2.1. Quản lý nhân sự** (53 trường) | Hồ sơ tổng / Master Data — gộp định danh, phân loại, mốc vòng đời, thông tin cá nhân, checklist tài sản nhúng | `hr.employee` (Header + Tabs) |
| **2.3. Thông tin thuế, bảo hiểm** | MST TNCN, Số BHXH, Số thẻ BHYT, Nơi KCB, Người phụ thuộc | Tab Private + custom fields |
| **2.4. Lộ trình thăng tiến** | Snapshot theo Tháng/Năm: chức danh, lương, phụ cấp | Lịch sử HĐ + custom log |
| **2.5. Theo dõi ký hợp đồng** | Ngày thử việc, Ngày kết thúc TV, Loại HĐ, Ngày ký/hết hạn, Link HĐ | `hr.contract` |
| **8.3. Lookup tài sản** | Sổ tài sản: mã tài sản + checklist + "Chuyển giao cho người mới" | Equipment/Assets |
| **8.4. Lookup chức danh** | Cây chức danh theo phòng ban | `hr.job` + `hr.department` |

**Điểm nghẽn nền tảng:** Dữ liệu phân mảnh trên nhiều sheet, đồng bộ thủ công → lệch thông tin và rủi ro sai sót khi tính lương/quyết toán.

## **2.2. Đặc tả các Quy trình Nghiệp vụ Hiện tại (As-Is Workflows)**

### **Quy trình 2.2.1: Tiếp nhận & Hội nhập Nhân viên VP/Sales (Onboarding Nhóm B — Có 2 Cổng)**

* **Mục tiêu:** Tiếp nhận nhân sự trúng tuyển, đào tạo hội nhập, kiểm soát thử việc theo mốc.
* **Tình trạng hiện tại:** Thủ công — không có cơ chế kiểm soát cổng tuần-2 và tháng-2 tự động.

1. **Bước 1 — Tiếp nhận & đào tạo đầu vào:** HCNS gửi tài liệu hội nhập, đào tạo văn hóa, **bàn giao/định hướng cho TBP** phụ trách đào tạo và đánh giá.
2. **Bước 2 — Thử việc tuần 1–2:** Nhân sự làm việc dưới kèm cặp của TBP. *Lưu ý: giai đoạn này CHƯA cấp thiết bị văn phòng.*
3. **Bước 3 — Cổng đánh giá tuần-2:** TBP đánh giá. **Đạt → Admin cấp máy tính + vật dụng** (ghi sổ 8.3 + checklist 2.1). **Không đạt → chuyển luồng Nghỉ thử việc.**
4. **Bước 4 — Thử việc đến tháng-2:** Tiếp tục thử việc.
5. **Bước 5 — Cổng đánh giá tháng-2:** Xét lên chính thức. Đạt → ký HĐ chính thức, cập nhật `Ngày chính thức`. Không đạt → kết thúc.

### **Quy trình 2.2.2: Tiếp nhận & Hội nhập Giảng viên (Onboarding Nhóm A)**

* **Mục tiêu:** Cấp tài nguyên dạy, đào tạo phương pháp, số hóa năng lực.
* **Tình trạng hiện tại:** Bán tự động — checklist thủ công, kết quả thử giảng lưu Excel rời.

1. **Bước 1:** HCNS gửi Offer, yêu cầu hồ sơ → báo IT cấp email `@hoc-ba.edu.vn` + tài khoản dạy **ngay từ đầu**.
2. **Bước 2:** Phòng Đào tạo training văn hóa & phương pháp; tổ chức **dự giờ/thử giảng** và chấm điểm (lưu Excel riêng — *pain point*).
3. **Bước 3:** Ghi nhận chứng chỉ (HSK/HSKK/Sư phạm) vào "bể năng lực" — ít đồng bộ ngược cho HR.
4. **Bước 4:** Ký HĐ thỉnh giảng; lưu bản mềm Drive, bản cứng tủ hồ sơ.

### **Quy trình 2.2.3: Quản lý Biến động & Năng lực (Lifecycle)**

* **Mục tiêu:** Cập nhật hồ sơ, nâng cấp chứng chỉ, thăng tiến/điều chuyển.
* **Tình trạng hiện tại:** Thủ công và phân mảnh. Mỗi phòng ban giữ file dữ liệu riêng dẫn đến lệch thông tin.

1. **Bước 1 (Duy trì Master Data):** HR cập nhật sheet 2.1 tổng của trung tâm.
2. **Bước 2 (Chứng chỉ chuyên môn):** Khi GV đạt chứng chỉ cao hơn, phòng Đào tạo ghi vào file "Bể năng lực" nội bộ — ít đồng bộ ngược cho HR.
3. **Bước 3 (Biến động nhân sự):** Thăng tiến/điều chuyển theo quyết định BGĐ. HR cập nhật file Excel và báo Kế toán qua chat.

### **Quy trình 2.2.4: Thôi việc & Thu hồi Tài sản (Offboarding — 2 Luồng tách biệt)**

**Luồng (a) — Nghỉ thử việc** *(theo Lark: "Quy trình nghỉ thử việc")*

1. B1 HCNS thông báo đánh giá TV (trước ≥5 ngày)
2. B2 TBP đánh giá kết quả (trước ≥3 ngày)
3. B3 Bàn giao công việc & tài sản
4. B4 Bảo mật: xóa tài khoản Lark, QL xóa khỏi nhóm

**Luồng (b) — Nghỉ việc chính thức** *(theo Lark: "Quy trình nghỉ việc")*

1. B1 Đơn xin nghỉ (trước 30/45 ngày)
2. B2 TBP xem xét (2 ngày)
3. B3 HCNS phỏng vấn nghỉ (5 ngày)
4. **B4 Giám đốc phê duyệt (≤1 tuần)**
5. B5 Bàn giao công việc & tài sản (chậm nhất 5 ngày trước nghỉ)
6. **B6 Thanh lý HĐLĐ + chốt công nợ (HCNS + Kế toán)**
7. B7 Lưu hồ sơ, hoàn tất BHXH

## **2.3. Ma trận Điểm nghẽn Vận hành (Operational Pain Points Matrix)**

| Nhóm quy trình | Điểm nghẽn vận hành | Thực tế tại Học Bá & Nguyên nhân | Hệ quả & Tác động |
|---|---|---|---|
| **Onboarding** | Trễ hạn cấp tài nguyên dạy học (Zoom, Slide) | Báo IT qua Zalo nên thông tin dễ trôi và quên sót | GV đến ngày nhận lớp chưa có tài khoản, học viên phàn nàn |
| **Onboarding** | **[MỚI]** Không kiểm soát được cổng tuần-2/tháng-2 | Không có cơ chế hẹn lịch và nhắc đánh giá tự động | Cấp thiết bị nhầm người chưa đạt; quên xét chính thức đúng hạn; tranh chấp ngày chính thức |
| **Onboarding** | Kết quả thử giảng nằm rời ở Excel phòng Đào tạo | HR không biết GV đạt/không để làm HĐ kịp thời | Chậm trễ thủ tục ký kết |
| **Lifecycle** | Mất dấu năng lực thực tế; không cảnh báo hết hạn chứng chỉ | Trình độ lưu phân tán, không có cơ chế alert | Không thống kê được để xin cấp phép chi nhánh; GV dạy với CC hết hạn |
| **Lifecycle** | Chậm cập nhật ca trực & luân chuyển cơ sở Sales | Đổi ca qua Zalo, HR cập nhật file Master chậm | Sai phụ cấp khi tính lương → khiếu nại |
| **Offboarding** | Rủi ro rò rỉ tài liệu & lãng phí tài khoản Zoom Pro | Khóa quyền chậm do báo qua Zalo | GV nghỉ vẫn dùng Zoom của TC hoặc sao chép kho đề gửi đối thủ |
| **Offboarding** | Đứt gãy tiến độ lớp khi GV nghỉ ngang | Không có form bàn giao tiến độ lớp chuẩn hóa | Phòng ĐT không biết lớp học đến bài nào; học viên đòi hoàn phí |
| **Offboarding** | **[MỚI]** 2 luồng nghỉ (thử việc / chính thức) xử lý chung | Thiếu phân biệt → thiếu/thừa bước | Sai thủ tục pháp lý; sót thu hồi tài sản |
| **Tài sản** | **[MỚI]** Sổ tài sản (8.3) và checklist hồ sơ (2.1) tách rời | Không tự đồng bộ thu hồi/chuyển giao | Thất thoát tài sản khi nghỉ việc |

---

# **CHƯƠNG 3 — PHÂN TÍCH QUY TRÌNH TIÊU CHUẨN CỦA ODOO 19.0 (STANDARD)**

## **3.1. Kiến trúc Dữ liệu Hồ sơ Nhân sự Tiêu chuẩn**

Mỗi hồ sơ nhân viên trong Odoo được tổ chức khoa học qua các phân vùng dữ liệu sau:

* **Header Hồ sơ:** Họ tên, ảnh, Email/Điện thoại công việc, Công ty (đa chi nhánh), Phòng ban, Chức vụ.
* **Tab Work Information:** Manager/Coach; sơ đồ tổ chức trực quan; Work Location (hỗ trợ đa cơ sở).
* **Tab Resumé & Skills:** Lịch sử làm việc, bằng cấp, Skill Types/Levels theo %, Certifications.
* **Tab Private Information:** Địa chỉ, số tài khoản ngân hàng, tình trạng hôn nhân, người phụ thuộc, liên hệ khẩn cấp, hồ sơ pháp lý (CCCD/Hộ chiếu).
* **Tab Payroll:** Hợp đồng hiện tại, Employer Cost, Working Schedule.
* **Tab HR Settings:** Related User (liên kết tài khoản đăng nhập), Approvers, Badge ID, PIN Kiosk.

## **3.2. Khung Kế hoạch Tự động hóa Hội nhập & Thôi việc (Plans)**

Odoo 19.0 sở hữu tính năng **Plans** mạnh mẽ để tự động hóa quy trình phối hợp liên phòng ban:

1. **Định nghĩa kế hoạch (Plan Setup):** Tạo mẫu Plans với Activities phân vai (User đích danh hoặc vai trò tương đối: Manager/HR/IT) và Deadline (sau bao nhiêu ngày).
2. **Kích hoạt & Giám sát:** HR nhấn **Launch Plan** → hệ thống sinh chuỗi tác vụ, bắn thông báo, hiển thị thanh tiến độ % realtime.
3. **Lưu trữ & Khóa (Offboarding):** HR nhấn **Archive** → hồ sơ chuyển *Inactive*, đồng thời tự **khóa Related User**.

> **Hạn chế cần xử lý:** Plan tiêu chuẩn **không có rẽ nhánh điều kiện** (Đạt/Không đạt). Cơ chế "cấp thiết bị chỉ khi đạt cổng tuần-2" cần Automated Action bổ sung — xem GAP G-13, G-14 và FUNC-EMP-005.

## **3.3. Cơ chế Kiểm soát Hiện diện Nâng cao (Advanced Presence Control)**

* **Presence Control dựa trên IP văn phòng:** Định nghĩa dải IP mạng nội bộ. Nếu nhân sự đăng nhập trong dải IP này, hệ thống tự động ghi nhận trạng thái hiện diện (xanh).
* **Presence Control dựa trên hoạt động Hệ thống:** Theo dõi tần suất thao tác / gửi email → quản lý chính xác trạng thái làm việc từ xa của GV Online.

## **3.4. Hồ sơ Tổng quan — Overview Profile (MỚI)**

Bản thân `hr.employee` form đã là hồ sơ tổng. Để đáp ứng yêu cầu "1 profile tổng quan/nhân viên", đề xuất bổ sung:

* **Kanban card:** Ảnh, Họ tên, Chức danh, Phòng ban, Tình trạng (badge màu), Hình thức, % tiến độ Plan.
* **Smart Buttons:** Hợp đồng, Tài sản đang giữ, Chứng chỉ sắp hết hạn, Lịch sử thăng tiến, Đơn từ (nghỉ phép/OT).
* **Trường tổng hợp ở Header:** Tình trạng, Hình thức, Ngày thử việc, Ngày chính thức, Số tháng làm việc chính thức (computed).
* **Dòng thời gian thử việc:** Mini-timeline 5 điểm (Ngày TV → ĐG tuần-2 → Cấp thiết bị → ĐG tháng-2 → Ngày CT) — chỉ hiển thị với Nhóm B.

> **Tham khảo UI:** `WIREFRAME_HoSoTongQuan.svg`

## **3.5. Quản lý Tài sản Nhân viên (MỚI)**

Dùng model `hr.employee.asset` để thay sổ 8.3 + checklist 2.1: mỗi tài sản có Mã, Loại, Người giữ, Ngày cấp, Trạng thái (`assigned/returned/transferred`). Cấp phát = tạo bản ghi (kích hoạt sau cổng tuần-2); Thu hồi = cập nhật trạng thái trong Offboarding Plan.

---

# **CHƯƠNG 4 — MA TRẬN PHÂN TÍCH KHOẢNG CÁCH (GAP ANALYSIS)**

## **4.1. Ma trận GAP Đã Chuẩn hóa từ v1.0 (Giữ nguyên)**

| Mã GAP | Yêu cầu Nghiệp vụ (Học Bá) | Odoo 19 Standard | Phân loại | Ưu tiên | Giải pháp kỹ thuật |
|---|---|---|---|---|---|
| **G-01** | CCCD 12 số — kiểm tra định dạng | Trường tự do, không bắt lỗi | VN Legal | Thấp | CFG-001: Regex `^\d{12}$` |
| **G-02** | Ngày cấp CCCD | Không có sẵn | VN Legal | **Cao** | CUS-001: `x_id_date_issue` |
| **G-03** | Nơi cấp CCCD | Không có sẵn | VN Legal | **Cao** | CUS-001: `x_id_place_issue` |
| **G-04** | Mã số thuế TNCN (MST) | Không có sẵn | VN Tax | **Cao** | CUS-002: `x_pit_code` |
| **G-05** | Địa chỉ VN 2 cấp phẳng (Tỉnh–Phường/Xã) | Mô hình 3 cấp cũ | VN Admin | TB | CFG-002: Cấu hình bỏ cấp Quận |
| **G-06** | Tách Thường trú / Tạm trú độc lập | Gom chung một Address block | VN Legal | TB | CUS-001: Cụm trường tạm trú |
| **G-07** | Số sổ BHXH (10 số) | Không có sẵn | VN SI | **Cao** | CUS-001: `x_social_insurance_no` |
| **G-08** | Số thẻ BHYT + Nơi KCB ban đầu | Không có sẵn | VN SI | TB | CUS-001: `x_health_insurance_no` |
| **G-09** | 4 nhóm lao động đặc thù Học Bá | Thiếu danh mục giáo dục ngoại ngữ | Custom | Thấp | CFG-003: Employment Types |
| **G-10** | Chứng chỉ HSK/HSKK/Sư phạm + cảnh báo hết hạn | Chứng chỉ phổ thông, chưa tối ưu | Custom | Thấp | CFG-004: Skill Types/Levels |
| **G-11** | Lịch làm việc linh hoạt cho GV Online | Cố định theo giờ hành chính | Custom | TB | CFG-005: Flexible Schedule |
| **G-12** | Người phụ thuộc chi tiết (giảm trừ gia cảnh) | Chỉ có trường số lượng thô | VN Tax | **Cao** | CUS-002: Model `hr.employee.dependent` |

## **4.2. GAP Mới Phát sinh sau Họp**

| Mã GAP | Yêu cầu Nghiệp vụ | Odoo Standard | Phân loại | Ưu tiên | Giải pháp kỹ thuật |
|---|---|---|---|---|---|
| **G-13** | **Hai cổng thử việc theo mốc** (tuần-2 cấp thiết bị; tháng-2 lên chính thức) với trạng thái Đạt/Không đạt | Plan không lưu kết quả đánh giá theo mốc; không có state machine thử việc | Custom | **Cao** | **CUS-010:** Nhóm trường `x_probation_start`, `x_eval_2w_*`, `x_eval_2m_*`, `x_official_date`. Activity nhắc tự sinh theo deadline. |
| **G-14** | **Cấp thiết bị chỉ khi Đạt cổng tuần-2** (rẽ nhánh điều kiện) | Plan tuyến tính, không rẽ nhánh | Custom | **Cao** | **AUT-001:** Automated Action `On Update` field `x_eval_2w_result`: Đạt → Launch Plan cấp thiết bị; Không đạt → Launch Plan nghỉ TV. AUT-002 tương tự cho cổng tháng-2. |
| **G-15** | **Hồ sơ tổng quan** gộp toàn cảnh nhân viên | Form tabs rời, chưa có Kanban/summary tùy chỉnh | Custom | TB | **CUS-011 + CFG-011:** Kanban card + Smart Buttons + dòng thời gian TV |
| **G-16** | **Phân biệt 2 luồng Offboarding** (thử việc vs chính thức có GĐ duyệt + thanh lý HĐ) | Chỉ có Plan tuyến tính chung | Custom | **Cao** | **CFG-012:** 2 Plan template riêng: "Offboarding – Nghỉ thử việc" (4 bước) & "Offboarding – Nghỉ việc CT" (7 bước) |
| **G-17** | **Quản lý tài sản cấp phát/thu hồi/chuyển giao** đồng bộ với hồ sơ | Có Equipment nhưng chưa khớp checklist Học Bá | Custom | TB | **CUS-012:** Model `hr.employee.asset`; danh mục tài sản chuẩn; tự tạo tác vụ thu hồi trong Offboarding. Block Archive khi còn tài sản chưa thu. |
| **G-18** | **Lịch sử thăng tiến/lương dạng snapshot** theo tháng (sheet 2.4) | Lịch sử HĐ có nhưng không snapshot phụ cấp tháng | Custom | Thấp | **CUS-013:** Model `hr.promotion.history` (One2many) — ghi nhận thay đổi chức danh/phụ cấp kèm ngày hiệu lực |
| **G-19** | **Đồng bộ kết quả thử giảng (GV)** vào hồ sơ thay vì Excel rời | Kết quả lưu ngoài hệ thống | Custom | TB | **CFG-013:** Activity "Đánh giá thử giảng" với ghi chú Đạt/Không đạt; trường `x_trial_lesson_result` trên hr.employee |

## **4.3. Ranh giới Liên thông Dữ liệu (Scope & Integration Boundaries)**

* **Trách nhiệm của phân hệ Employees:** Khởi tạo, xác thực và lưu trữ **Master Data** (dữ liệu tĩnh): MST TNCN, Số BHXH, danh sách nhân thân người phụ thuộc, trạng thái vòng đời, tài sản, kỹ năng.
* **Trách nhiệm của phân hệ Payroll:** Toàn bộ quy tắc tính toán tài chính: công thức trích BHXH, biểu thuế TNCN lũy tiến 7 bậc, đếm số người phụ thuộc hợp lệ để áp giảm trừ gia cảnh. Payroll **đọc trực tiếp** từ Employees.
* **Trách nhiệm của phân hệ Recruitment:** Đẩy ứng viên trúng tuyển → tự sinh hồ sơ Draft bên Employees.

---

# **CHƯƠNG 5 — ĐẶC TẢ CHI TIẾT CẤU HÌNH HỆ THỐNG (CONFIGURATION SPECIFICATION)**

## **5.1. Bảng Đặc tả Cấu hình Hệ thống (System Configuration Matrix)**

| Mã Cấu hình | Tên Cấu hình | Khu vực thiết lập (Odoo) | Kết quả kỳ vọng |
|---|---|---|---|
| **CONF-EMP-01** | Ràng buộc định dạng CCCD (12 số) | Employees > Settings > Constraints | Regex `^\d{12}$` tại `identification_id`. Nhập sai → cảnh báo đỏ. |
| **CONF-EMP-02** | Địa giới hành chính 2 cấp phẳng | Settings > Technical > Countries > Vietnam | Module `l10n_vn`, ẩn cấp Quận/Huyện. 34 tỉnh → Phường/Xã liên kết trực tiếp. |
| **CONF-EMP-03** | Danh mục phân loại nhân sự (Employment Types) | Employees > Configuration > Employment Types | Tạo: `Chính thức`, `Thử việc`, `TTS`, `Part-time`, `CTV`, `Cố vấn`, `Thỉnh giảng` |
| **CONF-EMP-04** | Ma trận Kỹ năng Tiếng Trung & Sư phạm | Employees > Configuration > Skill Types | Skill Types: "Tiếng Trung" (HSK 1–6, HSKK Sơ/Trung/Cao, TOCFL A2–C2), "Sư phạm", "Kỹ năng bổ trợ" |
| **CONF-EMP-05** | Thang đo cấp độ năng lực | Employees > Configuration > Skill Levels | Levels theo từng Skill Type. VD HSKK: Sơ cấp / Trung cấp / Cao cấp |
| **CONF-EMP-06** | Lịch làm việc linh hoạt cho GV Online | Employees > Configuration > Working Schedules | Mẫu "Flexible Hours" — không gán khung giờ cố định |
| **CONF-EMP-07a** | **[MỚI] Plan: Onboarding Giảng viên** | Employees > Configuration > Plans | Tác vụ: IT cấp email + Zoom/ClassIn (ngày 1); Admin giao giáo trình; Academic dự giờ thử giảng (tuần 1, ghi Đạt/Không đạt); Academic số hóa kỹ năng |
| **CONF-EMP-07b** | **[MỚI] Plan: Onboarding NV VP/Sales — Giai đoạn 1 (Hội nhập)** | Plans | Tác vụ: HCNS gửi TL + đào tạo văn hóa; bàn giao TBP; sinh Activity "Đánh giá tuần-2" deadline +14 ngày. **Chưa cấp thiết bị.** |
| **CONF-EMP-07c** | **[MỚI] Plan: Cấp thiết bị (Giai đoạn 2)** | Plans + Automated Action | Tự kích hoạt khi AUT-001 chạy: Admin tạo bản ghi tài sản; sinh Activity "Đánh giá tháng-2" +60 ngày |
| **CONF-EMP-08a** | **[MỚI] Plan: Offboarding — Nghỉ thử việc** | Plans | 4 bước: thông báo ĐG → TBP đánh giá → bàn giao CV + thu hồi tài sản → bảo mật |
| **CONF-EMP-08b** | **[MỚI] Plan: Offboarding — Nghỉ việc Chính thức** | Plans | 7 bước: nhận đơn → TBP xem xét → HCNS phỏng vấn → **GĐ phê duyệt** → bàn giao → **thanh lý HĐ + chốt công nợ (KT)** → lưu hồ sơ + Archive |
| **CONF-EMP-09** | Kiểm soát hiện diện nâng cao | Employees > Settings > Presence Control | Kích hoạt IP Address + System Email Sent |
| **CONF-EMP-10** | Huy hiệu (Badges) vinh danh | Employees > Configuration > Badges | "GV được yêu thích nhất tháng", "Sứ giả HSK", "Cố vấn học tập tận tâm" |
| **CONF-EMP-11** | Phòng ban chuẩn | Employees > Departments | Marketing, Sản phẩm (R&D_SP), Kinh doanh, Vận hành, Kế toán_HCNS, BOD |
| **CONF-EMP-12** | Cây chức danh (Job Positions) | Employees > Recruitment > Job Positions | Nhập theo 8.4 Lookup chức danh: Trưởng phòng > Trưởng bộ phận > Chuyên viên > Nhân viên > CTV |
| **CONF-EMP-13** | Danh mục tài sản chuẩn | Maintenance/Equipment > Configuration | Màn hình, Cây máy tính, Bàn phím, Chuột, Lót bàn phím, Tai nghe (to/sale), Ghế, Bàn, Máy in |

## **5.2. Hướng dẫn Nghiệp vụ Chi tiết cho Thiết lập Trọng yếu**

### **5.2.1. Chi tiết Automated Action cổng thử việc (G-13/G-14)**

* **AUT-001 — Cổng tuần-2:** Trigger `On Update` field `x_eval_2w_result`.
  * `= Đạt` → Server Action: Launch Plan "Cấp thiết bị" + tạo Activity "Đánh giá tháng-2".
  * `= Không đạt` → Server Action: Launch Plan "Offboarding – Nghỉ thử việc".
* **AUT-002 — Cổng tháng-2:** Trigger `On Update` field `x_eval_2m_result`.
  * `= Đạt` → set `x_employment_status = official`, `x_official_date = today`, gợi ý tạo HĐ chính thức.
  * `= Không đạt` → Launch Plan "Offboarding – Nghỉ thử việc".
* **CRON nhắc đánh giá:** Quét hằng ngày 7:00 SA các hồ sơ `Thử việc` có `x_eval_2w_due`/`x_eval_2m_due` đến hạn trong 2 ngày → bắn Activity nhắc HCNS & TBP.

### **5.2.2. Chi tiết cấu hình cây danh mục kỹ năng (CONF-EMP-04)**

* **Skill Type: Tiếng Trung** → Skills: HSK 1/2/3/4/5/6 (cũ), HSK 5–6 (mô hình 9 bậc mới), HSKK Trung/Cao cấp, TOCFL A2/B1/B2/C1/C2.
* **Skill Type: Sư phạm ngoại ngữ** → Skills: Bằng ĐH Sư phạm tiếng Trung, Chứng chỉ NVSP (Bộ GD VN), CTCSOL Quốc tế.
* *Mỗi kỹ năng khi gán vào hồ sơ GV kèm `x_cert_expiry`. Hệ thống tự alert trước 60 ngày.*

### **5.2.3. Validation Rules Offboarding**

* Với GV: không cho Mark as Done bước "Nghiệm thu bàn giao lớp" khi form tiến độ lớp còn trống.
* Với mọi nhân sự: không cho Archive khi tài sản chưa ở trạng thái `returned/transferred`.

---

# **CHƯƠNG 6 — ĐẶC TẢ QUY TRÌNH TO-BE: VÒNG ĐỜI NHÂN SỰ TRÊN ODOO 19.0**

> **Tài liệu tham chiếu:** Sơ đồ BPMN TO-BE v2.1 (file `BPMN_TOBE_v2.1_gop.svg/.png`) — 1 sơ đồ end-to-end gồm 2 hàng cuộn, 6 lane xuyên suốt.  
> **Camunda BPMN:** Hàng 1 (`HocBa_Onboarding_TOBE_v2.1.bpmn`), Hàng 2 (`HocBa_Lifecycle_Offboarding_TOBE_v2.1.bpmn`).

## **GIAI ĐOẠN 1 — HỘI NHẬP NHÂN SỰ MỚI (ONBOARDING)**

*(Hàng 1 BPMN — cổng Nhóm nhân sự? phân luồng)*

### **Luồng 1A: Giảng viên (Nhóm A)**

1. **(Tự động)** Recruitment "Trúng tuyển" → sinh hồ sơ Draft Employee + Hồ sơ tổng quan.
2. **(HR)** Launch Plan "Onboarding Giảng viên".
3. **(Tự động)** Sinh chuỗi Activities: IT, Academic, GV.
4. **(GV)** Portal hoàn thiện thông tin cá nhân (địa chỉ 2 cấp phẳng).
5. **(IT)** Cấp email `@hoc-ba.edu.vn` + Zoom Pro/ClassIn → Mark as Done **ngay ngày đầu**.
6. **(Academic)** Training phương pháp; **dự giờ thử giảng** → ghi kết quả Đạt/Không đạt vào Activity và trường `x_trial_lesson_result`.
7. **(Academic)** Số hóa ma trận kỹ năng (HSK/HSKK/Sư phạm) + `x_cert_expiry` vào Tab Resumé & Skills.

### **Luồng 1B: Nhân viên VP/Sales (Nhóm B) — 2 Cổng**

**Giai đoạn 1 — Hội nhập (Tuần 1–2):**

1. **(Tự động)** Sinh hồ sơ Draft từ Recruitment.
2. **(HR)** Launch Plan "Onboarding NV (Hội nhập)" → set `x_probation_start`, `x_eval_2w_due = +14 ngày`.
3. **(HR/Academic)** Đào tạo văn hóa, gửi tài liệu, **bàn giao cho TBP chuyên môn**.
4. **(NV)** Portal hoàn thiện thông tin cá nhân. *(Chưa cấp thiết bị.)*

**Cổng 1 — Đánh giá tuần-2:**

5. **(TBP)** Điền `x_eval_2w_result` + `x_eval_2w_note` + `x_eval_2w_date`.
   * **Đạt →** (AUT-001) Launch Plan "Cấp thiết bị": Admin cấp máy tính + vật dụng, ghi sổ tài sản; sinh Activity "Đánh giá tháng-2" (`x_eval_2m_due = +60 ngày`). → Giai đoạn 2.
   * **Không đạt →** (AUT-001) Launch Plan "Offboarding – Nghỉ thử việc". → Kết thúc.

**Giai đoạn 2 — Thử việc đến tháng-2:**

6. **(NV)** Làm việc; Presence Control giám sát.

**Cổng 2 — Đánh giá tháng-2:**

7. **(TBP/HR)** Điền `x_eval_2m_result` + `x_eval_2m_note`.
   * **Đạt →** (AUT-002) `x_employment_status = Chính thức`, `x_official_date = today`, sinh HĐ chính thức nháp. → Lifecycle.
   * **Không đạt →** Launch Plan "Offboarding – Nghỉ thử việc".

## **GIAI ĐOẠN 2 — QUẢN LÝ VẬN HÀNH & BIẾN ĐỘNG VÒNG ĐỜI (LIFECYCLE)**

*(Hàng 2 BPMN — phần Lifecycle)*

* **(Tự động — CRON)** Hằng ngày 7:00 SA: quét `hr.employee.skill` có `x_cert_expiry ≤ today+60` → tạo Activity cảnh báo cho GV & HR Manager.
* **Nhánh A — Thăng tiến / Điều chuyển (vòng lặp):**
  * **(HR)** Cập nhật chức vụ + `hr.contract` phụ lục + ghi `hr.promotion.history`. → Quay lại vận hành.
* **Nhánh B — Phát sinh nghỉ việc:**
  * **(HR)** Rẽ sang Giai đoạn 3 — Offboarding.

## **GIAI ĐOẠN 3 — THÔI VIỆC & ĐÓNG BẢO MẬT HỒ SƠ (OFFBOARDING)**

*(Hàng 2 BPMN — phần Offboarding; 2 luồng tách biệt)*

### **Luồng 3A — Nghỉ thử việc (4 bước, rút gọn)**

1. **(HR)** Launch Plan "Offboarding – Nghỉ thử việc" + thông báo TBP đánh giá kết quả.
2. **(TBP)** Đánh giá và xác nhận lý do.
3. **(NV + IT/Admin)** Bàn giao công việc + thu hồi toàn bộ tài sản (`state = returned/transferred`).
4. **(Tự động)** Khóa Related User + gỡ nhóm Lark → HR bấm **Archive** → *Inactive hoàn toàn*.

> *Không có: phỏng vấn nghỉ, GĐ phê duyệt, thanh lý HĐ.*

### **Luồng 3B — Nghỉ việc Chính thức (7 bước)**

1. **(HR)** Tiếp nhận đơn + Launch Plan "Offboarding – Nghỉ việc CT".
2. **(TBP)** Xem xét nguyên nhân (2 ngày).
3. **(HR)** Phỏng vấn nghỉ việc (5 ngày).
4. ***(BGĐ)* Giám đốc phê duyệt (≤1 tuần).**
5. **(NV)** Bàn giao công việc / lớp học (điền form tiến độ — bắt buộc trước khi Mark as Done).
6. **(IT/Admin)** Thu hồi thiết bị + tài sản.
7. ***(HR + Kế toán)* Thanh lý HĐ + chốt công nợ.**
8. **(HR)** Bấm **Archive** → (Tự động) Inactive + khóa Related User. → Kết thúc.

---

# **CHƯƠNG 7 — FUNCTIONAL SPECIFICATION (MÔ TẢ CHỨC NĂNG CHI TIẾT)**

> **Phạm vi:** 9 chức năng lập trình mở rộng (prefix `x_` / model mới). Cấu hình thuần không thuộc phạm vi.  
> **Quy ước:** `Required*` = bắt buộc khi lưu; `Required°` = bắt buộc theo điều kiện nghiệp vụ.

| Function ID | Tên chức năng | GAP ref | Độ phức tạp |
|---|---|---|---|
| FUNC-EMP-001 | Hồ sơ tổng quan (Overview Profile) | G-15 | Trung bình |
| FUNC-EMP-002 | Trường dữ liệu pháp lý Việt Nam | G-01..08 | Thấp |
| FUNC-EMP-003 | Quản lý người phụ thuộc giảm trừ gia cảnh | G-12 | Trung bình |
| FUNC-EMP-004 | Dòng thời gian thử việc & 2 cổng đánh giá | G-13 | Cao |
| FUNC-EMP-005 | Tự động hóa cổng thử việc (AUT-001 / AUT-002) | G-14 | Cao |
| FUNC-EMP-006 | Quản lý tài sản cấp phát & thu hồi | G-17 | Trung bình |
| FUNC-EMP-007 | Lịch sử thăng tiến & lương (Promotion Snapshot) | G-18 | Thấp |
| FUNC-EMP-008 | Đánh giá thử giảng & Ma trận kỹ năng giảng viên | G-10 / G-19 | Trung bình |
| FUNC-EMP-009 | CRON cảnh báo chứng chỉ sắp hết hạn | G-10 | Thấp |

---

## **7.1. FUNC-EMP-001 — Hồ sơ tổng quan (Overview Profile)**

**Function ID:** FUNC-EMP-001 | **Module:** `hr.employee` | **Actor:** HR (xem/sửa), NV (xem Portal), TBP (xem)

**Purpose:** Cung cấp một màn hình duy nhất tổng hợp toàn bộ thông tin nhân viên — thay thế tra cứu rải rác nhiều sheet Lark.

**Preconditions:** Hồ sơ `hr.employee` đã tạo; quyền `hr.group_hr_user` trở lên.

**Trigger:** Mở record `hr.employee`; hoặc Recruitment sinh hồ sơ Draft tự động.

**Main Flow:**
1. HR mở form `hr.employee`. Header: ảnh, Họ tên (lớn), Chức danh, Phòng ban.
2. Hàng chip phân loại: `[Hình thức] [Phòng ban] [Mã NS]` (colored chips).
3. Statusbar góc phải: **Thử việc → Chính thức → Nghỉ việc** (đồng bộ `x_employment_status`).
4. Hàng Smart Buttons: **Hợp đồng** | **Tài sản (n)** | **Chứng chỉ (n sắp hết — highlight cam)** | **Thăng tiến** | **Đơn từ**.
5. Khối "Dòng thời gian thử việc" (chỉ hiển thị Nhóm B): 5 điểm tròn trên timeline.
6. Tab đầu tiên "Tổng quan" chia 3 cột: Định danh & Tổ chức | Liên hệ & Pháp lý | Chuyên môn & Tài chính.
7. Tabs còn lại: Work Information, Resumé & Skills, Private Information, Payroll, HR Settings.

**Alternative Flow:** Nghỉ việc → statusbar hiện trạng thái cuối, nút Archive thay bằng "Đã lưu trữ" (readonly). Nhân viên qua Portal → chỉ Tab Tổng quan, ẩn dữ liệu lương/thuế.

**Exception Flow:** Chưa có ảnh → avatar placeholder chữ tắt họ tên. Smart Button "Chứng chỉ" highlight đỏ nếu có chứng chỉ **đã hết hạn**.

**Validation Rules:**
* `x_employee_code`: unique, không sửa sau khi có HĐ chính thức.
* `x_employment_status` chỉ chuyển `Thử việc → Chính thức` qua AUT-002 (không cho sửa thủ công nếu không phải `hr.group_hr_manager`).

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Mã nhân sự | `x_employee_code` | Char(10) | * | Unique; `HB\.\d{2,3}`; auto-generate |
| Hình thức làm việc | `x_work_form` | Selection | * | `offline / online` |
| Tình trạng | `x_employment_status` | Selection | * | Xem danh sách trạng thái |
| Loại vị trí | `x_position_type` | Selection | * | `manager / staff / ctv / freelancer / advisor` |
| Số tháng chính thức | `x_official_months` | Float (computed) | — | `(today - x_official_date).days / 30`; readonly |

**Output:** Form đầy đủ; Smart Button counts tự refresh khi navigate.

**Business Rules:**
* BR-001: Mã NS sinh tự động format `HB.<next_seq>`; HR có thể override trước khi lưu lần đầu.
* BR-002: `x_employment_status` mặc định `draft`; chuyển `Thử việc` khi HR xác nhận onboarding.
* BR-003: Smart Button "Tài sản" đếm records `hr.employee.asset` có `state = assigned`.

**UI Reference:** `WIREFRAME_HoSoTongQuan.svg` — Header + Statusbar + Smart Buttons + Tab Tổng quan.

---

## **7.2. FUNC-EMP-002 — Trường Dữ liệu Pháp lý Việt Nam**

**Function ID:** FUNC-EMP-002 | **Module:** `hr.employee` — Tab Private Information | **Actor:** HR (nhập/sửa), NV (tự cập nhật địa chỉ qua Portal)

**Purpose:** Lưu trữ đầy đủ thông tin pháp lý VN: CCCD (ngày/nơi cấp), MST TNCN, BHXH, BHYT, địa chỉ thường trú và tạm trú tách biệt.

**Preconditions:** Hồ sơ nhân viên đã tạo.

**Trigger:** HR mở Tab Private Information → điền/cập nhật thông tin pháp lý.

**Main Flow:**
1. HR mở Tab **Private Information** → nhóm "Giấy tờ pháp lý" → nhập số CCCD (12 số), ngày cấp, nơi cấp.
2. HR nhập MST TNCN (10 hoặc 13 số) → validate format.
3. HR nhập số sổ BHXH (10 số) và số thẻ BHYT + nơi KCB.
4. HR nhập địa chỉ thường trú: chọn Tỉnh/Thành (dropdown `res.country.state`, filter VN) → nhập Phường/Xã → nhập Số nhà/Đường.
5. Nếu tạm trú khác: bỏ tick "Giống địa chỉ thường trú" → nhập tương tự.
6. Lưu → hệ thống validate tất cả format.

**Alternative Flow:** Nhân viên nước ngoài → MST/BHXH là optional; CCCD nhận Passport (bỏ validation 12 số). Tạm trú = thường trú → tick checkbox → tự copy và lock.

**Exception Flow:** CCCD đã tồn tại trên hồ sơ khác → cảnh báo (không block — có thể là lỗi data cũ).

**Validation Rules:**
* CCCD: `^\d{12}$`. MST TNCN: `^\d{10}(\d{3})?$`. Số BHXH: `^\d{10}$`.
* `x_id_date_issue` ≤ today và ≥ birthday + 14 năm.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Số CCCD | `identification_id` | Char(12) | * | Regex `^\d{12}$`; chuẩn Odoo |
| Ngày cấp CCCD | `x_id_date_issue` | Date | ° | Nếu có CCCD; ≤ today; ≥ DOB+14y |
| Nơi cấp CCCD | `x_id_place_issue` | Char(100) | ° | Nếu có CCCD |
| MST TNCN | `x_pit_code` | Char(13) | ° | Regex `^\d{10}(\d{3})?$`; khi lên Chính thức |
| Số sổ BHXH | `x_social_insurance_no` | Char(10) | ° | Regex `^\d{10}$`; khi lên Chính thức |
| Số thẻ BHYT | `x_health_insurance_no` | Char(15) | — | Free format |
| Nơi KCB ban đầu | `x_health_care_place` | Char(100) | — | |
| Tỉnh/Thành thường trú | `x_permanent_state_id` | Many2one `res.country.state` | * | Filter VN |
| Phường/Xã thường trú | `x_permanent_ward` | Char(100) | * | |
| Số nhà/Đường thường trú | `x_permanent_street` | Char(200) | * | |
| Giống địa chỉ thường trú | `x_current_same_as_permanent` | Boolean | — | Default: True |
| Tỉnh/Thành tạm trú | `x_current_state_id` | Many2one | ° | Hiện khi checkbox = False |
| Phường/Xã tạm trú | `x_current_ward` | Char(100) | ° | Hiện khi checkbox = False |
| Số nhà/Đường tạm trú | `x_current_street` | Char(200) | ° | Hiện khi checkbox = False |

**Business Rules:**
* BR-010: MST TNCN và Số BHXH bắt buộc trước khi tạo HĐ chính thức.
* BR-011: CCCD, MST, BHXH ẩn với `hr.group_hr_user`; chỉ hiển thị đầy đủ với HR Manager và Kế toán.
* BR-012: Khi `x_current_same_as_permanent = True`, trường tạm trú readonly và mirror thường trú.

---

## **7.3. FUNC-EMP-003 — Quản lý Người phụ thuộc Giảm trừ Gia cảnh**

**Function ID:** FUNC-EMP-003 | **Module:** Model mới `hr.employee.dependent` | **Actor:** HR (nhập/duyệt), Kế toán (đọc)

**Purpose:** Lưu danh sách người phụ thuộc phục vụ tính giảm trừ gia cảnh thuế TNCN (TT 111/2013/TT-BTC).

**Preconditions:** Hồ sơ nhân viên đã tạo. NV đã cung cấp hồ sơ đăng ký người phụ thuộc.

**Main Flow:**
1. HR mở Tab **Private Information** → section "Người phụ thuộc".
2. Bấm **Thêm dòng** → nhập: Họ tên, Quan hệ, Ngày sinh, Số CCCD/MST.
3. Nhập ngày bắt đầu tính giảm trừ (tháng đăng ký với cơ quan thuế).
4. Nhập ngày kết thúc (nếu NTT đã tự chủ thu nhập hoặc mất).
5. Lưu → `x_active_dependent_count` (computed) tự cập nhật.
6. Kế toán đọc `x_active_dependent_count` khi tính lương: giảm trừ = 4.4tr × số NTT/tháng.

**Validation Rules:**
* `date_start` ≤ today. `date_end` > `date_start` (nếu có). `relationship` ∈ danh sách cố định.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Họ tên NTT | `name` | Char(100) | * | |
| Quan hệ | `relationship` | Selection | * | `spouse/child/parent/sibling/other` |
| Ngày sinh | `birthday` | Date | * | ≤ today |
| Số CCCD/Hộ chiếu | `national_id` | Char(20) | ° | Nếu đủ tuổi |
| Ngày bắt đầu giảm trừ | `date_start` | Date | * | Theo tháng đăng ký thuế |
| Ngày kết thúc | `date_end` | Date | — | > date_start |
| Ghi chú | `notes` | Text | — | |

**Business Rules:**
* BR-020: Mức giảm trừ NTT: **4.400.000 VNĐ/tháng** — cấu hình qua `ir.config_parameter`, không hardcode.
* BR-021: Giảm trừ tính theo tháng của `date_start`; tháng kết thúc theo `date_end`.
* BR-022: Kế toán có quyền readonly; chỉ HR Manager thêm/sửa/xóa.

---

## **7.4. FUNC-EMP-004 — Dòng Thời gian Thử việc & 2 Cổng Đánh giá**

**Function ID:** FUNC-EMP-004 | **Module:** `hr.employee` — custom block | **Actor:** TBP (điền kết quả), HR (xem tổng quan)

**Purpose:** Quản lý chu trình thử việc 2 bước cho Nhóm B — thay thế Excel theo dõi thủ công; kiểm soát cổng cấp thiết bị và lên chính thức.

**Preconditions:** `x_employment_status = Thử việc`; `x_position_type ∈ {staff, manager}`; HR đã Launch Plan Onboarding.

**Trigger:** HR Launch Plan → hệ thống ghi `x_probation_start = today`, tính `x_eval_2w_due` và `x_eval_2m_due`. CRON nhắc khi đến hạn.

**Main Flow — Cổng tuần-2:**
1. Hệ thống tạo Activity "Đánh giá thử việc tuần-2" giao TBP.
2. TBP chọn `x_eval_2w_result` (Đạt / Không đạt) + ghi chú + ngày thực tế.
3. Lưu → trigger AUT-001. Mini-timeline cập nhật màu.

**Main Flow — Cổng tháng-2:**
1. Sau cổng tuần-2 Đạt, hệ thống sinh Activity "Đánh giá tháng-2".
2. TBP/HR điền `x_eval_2m_result` + ghi chú. Lưu → trigger AUT-002.

**Alternative Flow:** HR Manager ghi đè kết quả (log user + timestamp). Gia hạn thử việc: HR đặt lại `x_eval_2m_due` (không quá +60 ngày) + ghi chú lý do.

**Exception Flow:** TBP chọn "Đạt" nhưng chưa nhập ghi chú → warning. `x_eval_2w_due` qua 3 ngày chưa đánh giá → escalate Activity lên HR Manager.

**Validation Rules:**
* `x_eval_2w_date` ≥ `x_probation_start` và ≤ today.
* Không cho điền kết quả cổng tháng-2 nếu cổng tuần-2 chưa Đạt.
* Chỉ `hr.group_hr_manager` hoặc manager trực tiếp mới được điền kết quả.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Ngày bắt đầu thử việc | `x_probation_start` | Date | * | Auto-set khi Launch Plan |
| Hạn đánh giá tuần-2 | `x_eval_2w_due` | Date | * | Computed: start+14 ngày; có thể sửa [7, 21] ngày |
| Kết quả đánh giá tuần-2 | `x_eval_2w_result` | Selection | ° | `draft / pass / fail` |
| Ngày đánh giá thực tế (tuần-2) | `x_eval_2w_date` | Date | ° | Nếu result ≠ draft |
| Người đánh giá (tuần-2) | `x_eval_2w_evaluator_id` | Many2one `res.users` | ° | |
| Ghi chú đánh giá (tuần-2) | `x_eval_2w_note` | Text | ° | Bắt buộc nếu result = pass |
| Ngày cấp thiết bị | `x_equip_grant_date` | Date | — | Auto-set khi AUT-001 chạy |
| Hạn đánh giá tháng-2 | `x_eval_2m_due` | Date | * | Computed: start+60 ngày; có thể sửa |
| Kết quả đánh giá tháng-2 | `x_eval_2m_result` | Selection | ° | `draft / pass / fail` |
| Ngày đánh giá (tháng-2) | `x_eval_2m_date` | Date | ° | |
| Người đánh giá (tháng-2) | `x_eval_2m_evaluator_id` | Many2one | ° | |
| Ghi chú đánh giá (tháng-2) | `x_eval_2m_note` | Text | ° | Bắt buộc nếu result = pass |
| Ngày chính thức | `x_official_date` | Date | — | Auto-set khi AUT-002 chạy; readonly |

**Business Rules:**
* BR-030: Block timeline chỉ hiển thị khi `x_position_type ∈ {staff, manager}` VÀ `x_work_form = offline`. Ẩn với Nhóm A.
* BR-031: Lịch sử thay đổi kết quả ghi vào chatter với user + timestamp.

**UI Reference:** BPMN Khối 2 (Cổng tuần-2 và tháng-2); Wireframe — khối nét đứt xanh "Dòng thời gian thử việc".

---

## **7.5. FUNC-EMP-005 — Tự động hóa Cổng Thử việc (AUT-001 & AUT-002)**

**Function ID:** FUNC-EMP-005 | **Module:** `base.automation` | **Actor:** Hệ thống Odoo (trigger tự động)

**Purpose:** Loại bỏ thao tác thủ công sau đánh giá — hệ thống tự kích hoạt Plan cấp thiết bị, Plan offboarding hoặc xác nhận Chính thức dựa trên kết quả đánh giá.

**Trigger:**
* **AUT-001a:** `x_eval_2w_result` → `pass` (On Update).
* **AUT-001b:** `x_eval_2w_result` → `fail` (On Update).
* **AUT-002a:** `x_eval_2m_result` → `pass` (On Update).
* **AUT-002b:** `x_eval_2m_result` → `fail` (On Update).
* **CRON nhắc:** Hằng ngày 7:00 SA — quét hồ sơ đến hạn đánh giá trong 2 ngày.

**Main Flow — AUT-001a (Đạt tuần-2):**
1. Tạo Activity "Cấp thiết bị" giao IT/Admin, deadline = today+1 ngày.
2. Set `x_equip_grant_date = today` (pending).
3. Ghi log chatter: "✅ Cổng tuần-2 ĐẠT — Kế hoạch cấp thiết bị đã được khởi động."

**Main Flow — AUT-001b (Không đạt tuần-2):**
1. Launch Plan "Offboarding – Nghỉ thử việc".
2. Set `x_employment_status = exiting`.
3. Ghi log: "❌ Cổng tuần-2 KHÔNG ĐẠT — Đã khởi động Plan nghỉ thử việc."

**Main Flow — AUT-002a (Đạt tháng-2):**
1. `x_official_date = today`, `x_employment_status = official`.
2. Sinh `hr.contract` nháp loại "Chính thức" với `date_start = x_official_date`.
3. Ghi log: "🎉 Cổng tháng-2 ĐẠT — Chuyển Chính thức. HĐ chính thức đã tạo nháp."
4. Gửi email thông báo cho nhân viên (template "Chúc mừng lên chính thức").

**Main Flow — AUT-002b (Không đạt tháng-2):** Launch Plan "Offboarding – Nghỉ thử việc" + set `exiting` + log.

**Main Flow — CRON nhắc:**
1. Quét `x_eval_2w_result = draft` AND `x_eval_2w_due ≤ today+2` → tạo Activity nhắc TBP và HR Manager.
2. Tương tự với `x_eval_2m_due`.

**Alternative Flow:** HR set `x_skip_auto_trigger = True` → bỏ qua AUT, ghi log "Auto trigger bị bỏ qua bởi [user]."

**Exception Flow:** Plan không tồn tại → ghi lỗi log + tạo Activity thủ công nhắc HR. Email server down → bỏ qua email, không block action.

**Validation Rules:**
* Mỗi trigger chỉ chạy 1 lần per lần thay đổi field (old ≠ new).
* Không chạy AUT-002 nếu `x_eval_2w_result ≠ pass`.

**Business Rules:**
* BR-040: Tất cả Server Actions chạy với `sudo()`; nhưng ghi log user trigger thực tế vào chatter.
* BR-041: CRON chỉ tạo Activity nếu chưa có Activity cùng loại còn open trong 7 ngày qua.
* BR-042: AUT-001b/002b chỉ Launch Plan khi Plan chưa đang chạy trên nhân viên đó.

---

## **7.6. FUNC-EMP-006 — Quản lý Tài sản Cấp phát & Thu hồi**

**Function ID:** FUNC-EMP-006 | **Module:** Model mới `hr.employee.asset` | **Actor:** IT/Admin (cấp/thu hồi), HR (xem tổng)

**Purpose:** Thay thế sổ tài sản 8.3 Lark + checklist nhúng hồ sơ — quản lý tập trung việc cấp phát, theo dõi và thu hồi thiết bị; đảm bảo không thất thoát khi nhân sự nghỉ việc.

**Preconditions:** Danh mục tài sản đã cấu hình; Nhóm B: cổng tuần-2 đã Đạt (AUT-001 đã chạy).

**Main Flow — Cấp phát:**
1. IT/Admin nhận Activity "Cấp thiết bị" → mở Smart Button "Tài sản" trên hồ sơ.
2. Bấm **Tạo mới** → chọn loại tài sản, nhập mã, ngày cấp.
3. `state = assigned` tự set khi lưu. Lặp lại mỗi thiết bị.
4. Mark as Done Activity.

**Main Flow — Thu hồi:**
1. Offboarding Plan tạo Activity "Thu hồi thiết bị".
2. IT/Admin mở Smart Button "Tài sản" → danh sách `state = assigned`.
3. Từng thiết bị: bấm **Thu hồi** → nhập ngày, ghi chú tình trạng → `state = returned`.
4. Hoặc **Chuyển giao** → chọn NV nhận → `state = transferred`, tạo bản ghi mới bên NV nhận.
5. Khi tất cả đã `returned/transferred` → Mark as Done Activity.

**Exception Flow:** Cố Archive NV khi còn tài sản `assigned` → hệ thống **block** với cảnh báo danh sách thiết bị chưa thu.

**Validation Rules:**
* `grant_date` ≥ `x_eval_2w_date`.
* `return_date` ≥ `grant_date`.
* Không xóa bản ghi — chỉ đổi state.
* `asset_code` unique toàn hệ thống.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Nhân viên giữ | `employee_id` | Many2one `hr.employee` | * | Auto-fill từ context |
| Loại tài sản | `asset_type_id` | Many2one `x.asset.type` | * | |
| Mã tài sản | `asset_code` | Char(50) | * | Unique |
| Ngày cấp phát | `grant_date` | Date | * | ≥ x_eval_2w_date |
| Tình trạng khi cấp | `condition_in` | Selection | * | `new/good/fair` |
| Trạng thái | `state` | Selection | * | `assigned/returned/transferred` |
| Ngày thu hồi | `return_date` | Date | ° | Khi state = returned |
| Nhân viên nhận (chuyển giao) | `transferred_to` | Many2one | ° | Khi state = transferred |
| Ghi chú tình trạng khi thu | `condition_out_note` | Text | — | |

**Business Rules:**
* BR-050: Khi `transferred` → tự tạo bản ghi tài sản mới trên `transferred_to` với `grant_date = return_date`.
* BR-051: Danh mục loại tài sản chuẩn: Màn hình, Cây máy tính, Bàn phím, Chuột, Lót bàn phím, Tai nghe (sales/to), Ghế, Bàn, Máy in, Thùng rác.
* BR-052: Smart Button count chỉ đếm `state = assigned`.

---

## **7.7. FUNC-EMP-007 — Lịch sử Thăng tiến & Lương (Promotion Snapshot)**

**Function ID:** FUNC-EMP-007 | **Module:** Model mới `hr.promotion.history` | **Actor:** HR Manager (tạo/sửa), Kế toán (đọc)

**Purpose:** Lưu lịch sử snapshot thay đổi chức vụ, lương và phụ cấp theo mốc — thay thế sheet 2.4 Lark, đảm bảo audit trail cho quyết toán lương.

**Main Flow:**
1. HR mở Smart Button "Thăng tiến (n)" → **Tạo mới**.
2. Nhập: ngày hiệu lực, chức vụ mới, phòng ban mới (nếu thay đổi).
3. Nhập mức lương mới, phụ cấp, lý do, số quyết định, người phê duyệt.
4. Lưu → hệ thống tự cập nhật `job_id`, `department_id` và `wage` trên `hr.employee`.
5. Ghi log chatter: "📈 Cập nhật chức vụ: [Cũ] → [Mới] từ [Ngày]."

**Validation Rules:**
* `date_effective` ≤ today+30. `to_wage` > 0.
* Bắt buộc một trong: `to_job_id ≠ from_job_id` HOẶC `to_wage ≠ from_wage`.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Nhân viên | `employee_id` | Many2one | * | Auto-fill |
| Ngày có hiệu lực | `date_effective` | Date | * | ≤ today+30 |
| Chức vụ trước | `from_job_id` | Many2one `hr.job` | * | Auto-fill từ employee |
| Chức vụ mới | `to_job_id` | Many2one `hr.job` | * | |
| Phòng ban mới | `to_department_id` | Many2one | — | |
| Lương cũ | `from_wage` | Float | * | Auto-fill từ contract |
| Lương mới | `to_wage` | Float | * | > 0 |
| Phụ cấp (tóm tắt) | `allowance_note` | Text | — | |
| Lý do / Căn cứ | `reason` | Text | ° | Bắt buộc nếu wage thay đổi |
| Số quyết định | `decision_ref` | Char(50) | — | |
| Người phê duyệt | `approved_by` | Many2one `res.users` | * | |

**Business Rules:**
* BR-060: Không xóa bản ghi — chỉ sửa trong 24h đầu sau khi tạo; sau đó chỉ HR Director mới sửa được.
* BR-061: CRON tháng (tùy chọn): ngày 1 hằng tháng chụp snapshot nếu không có bản ghi trong tháng đó.

---

## **7.8. FUNC-EMP-008 — Đánh giá Thử giảng & Ma trận Kỹ năng Giảng viên**

**Function ID:** FUNC-EMP-008 | **Module:** `hr.employee` — Tab Resumé & Skills + custom fields | **Actor:** Academic/TBP Đào tạo (điền kết quả), HR (xem), GV (xem kỹ năng)

**Purpose:** Đưa kết quả thử giảng vào hồ sơ thay vì Excel rời; số hóa ma trận kỹ năng tiếng Trung để phân công giảng dạy và cảnh báo hết hạn.

**Preconditions:** NV là Giảng viên: `x_work_form = online` hoặc loại HĐ ∈ {thỉnh giảng, parttime, ctv}. Skill Types đã cấu hình.

**Main Flow — Đánh giá thử giảng:**
1. Onboarding Plan tạo Activity "Dự giờ thử giảng" giao TBP Đào tạo.
2. TBP điền: ngày thử giảng, lớp thử, điểm phương pháp (1–10), điểm chuyên môn (1–10), nhận xét.
3. TBP chọn kết quả: Đạt / Không đạt → lưu.
4. Đạt → Activity nhắc HR ký HĐ thỉnh giảng. Không đạt → Activity nhắc HR thông báo GV.

**Main Flow — Nhập ma trận kỹ năng:**
1. TBP/HR mở Tab **Resumé & Skills** → thêm skill (Tiếng Trung / Sư phạm) + ngày cấp `x_cert_date` + ngày hết hạn `x_cert_expiry`.
2. GV upload ảnh chứng chỉ → HR set `x_cert_verified = True` sau kiểm tra bản gốc.

**Exception Flow:** Điểm < 5 nhưng chọn Đạt → warning "Điểm trung bình < 5, xác nhận Đạt?". `x_cert_expiry` < today → badge "Hết hạn" đỏ ngay khi nhập.

**Input Fields:**

| Field | Model field | Type | Required | Rule |
|---|---|---|---|---|
| Ngày thử giảng | `x_trial_lesson_date` | Date | ° | Nhóm A; ≤ today |
| Lớp thử giảng | `x_trial_lesson_class` | Char(50) | — | |
| Điểm phương pháp | `x_trial_score_method` | Float | ° | [1, 10]; 1 decimal |
| Điểm chuyên môn | `x_trial_score_content` | Float | ° | [1, 10]; 1 decimal |
| Nhận xét thử giảng | `x_trial_lesson_note` | Text | ° | Bắt buộc nếu Không đạt |
| Kết quả thử giảng | `x_trial_lesson_result` | Selection | ° | `draft/pass/fail` |
| Ngày cấp chứng chỉ | `x_cert_date` | Date | ° | Nếu có CC (trên `hr.employee.skill`) |
| Ngày hết hạn chứng chỉ | `x_cert_expiry` | Date | ° | > x_cert_date |
| Đã xác minh | `x_cert_verified` | Boolean | — | HR set sau kiểm tra |

**Business Rules:**
* BR-070: Skill Types chuẩn tạo sẵn khi cài module (HSK 1–6, HSKK, TOCFL, NVSP, CTCSOL…).
* BR-071: GV có thể có nhiều chứng chỉ cùng type (CC cũ hết hạn + CC mới còn hạn).
* BR-072: `x_cert_verified = False` → badge "Chờ xác minh" màu vàng.

---

## **7.9. FUNC-EMP-009 — CRON Cảnh báo Chứng chỉ Sắp hết hạn**

**Function ID:** FUNC-EMP-009 | **Module:** `ir.cron` + `hr.employee.skill` | **Actor:** Hệ thống Odoo (tự chạy), HR & GV (nhận cảnh báo)

**Purpose:** Tự động phát hiện chứng chỉ sắp hết hạn trước 60 ngày — ngăn GV dạy với chứng chỉ không hợp lệ; thay thế kiểm tra thủ công.

**Preconditions:** Chứng chỉ đã nhập với `x_cert_expiry` có giá trị; NV còn `active = True`.

**Trigger:** `ir.cron` chạy hằng ngày lúc **7:00 SA** (timezone `Asia/Ho_Chi_Minh`).

**Main Flow:**
1. CRON query: `hr.employee.skill` WHERE `x_cert_expiry ≤ today+60` AND `x_cert_expiry ≥ today` AND `employee_id.active = True` AND `x_cert_verified = True`.
2. Nhóm theo `employee_id`.
3. Với mỗi NV: kiểm tra Activity "Cảnh báo chứng chỉ" open trong 7 ngày qua → nếu có, bỏ qua.
4. Tạo Activity giao HR Manager, deadline = `x_cert_expiry - 30 ngày`.
5. Gửi email GV: danh sách chứng chỉ sắp hết + hướng dẫn gia hạn.
6. Query thứ hai: `x_cert_expiry < today` AND active → tạo Activity ưu tiên cao (đỏ).
7. Ghi log CRON: số GV cảnh báo, số CC sắp hết, số CC đã hết.

**Exception Flow:** Email server down → bỏ qua email, vẫn tạo Activity. GV không có email công ty → gửi cho HR Manager thay thế.

**Validation Rules:**
* Interval tối thiểu giữa 2 Activity cùng loại trên cùng employee: 7 ngày.
* Chỉ cảnh báo `x_cert_verified = True`.

**Business Rules:**
* BR-090: Ngưỡng cảnh báo: **60 ngày** — cấu hình qua `ir.config_parameter` `hoc_ba.cert_alert_days`, không hardcode.
* BR-091: Email template liệt kê: tên CC, ngày hết hạn, số ngày còn lại, link hướng dẫn gia hạn.
* BR-092: CRON log vào `ir.logging` level `info`; exception → level `error` + email IT Admin.

**UI Reference:** Smart Button "Chứng chỉ (n sắp hết hạn)"; badge màu trên skill row Tab Resumé & Skills; BPMN Hàng 2 node "CRON cảnh báo".

---

# **PHỤ LỤC A — DATA DICTIONARY (LARK → ODOO)**

## **A.1. Fields trên `hr.employee`**

| Trường Lark (sheet 2.1) | Trường Odoo | Loại | Ghi chú |
|---|---|---|---|
| Mã nhân sự (HB.xx) | `x_employee_code` | Char | Mã định danh nội bộ |
| Họ và tên | `name` | Char | |
| Hình thức (Offline/Online) | `x_work_form` | Selection | Trục 1 |
| Tình trạng | `x_employment_status` | Selection | Trục 2 |
| Loại vị trí | `x_position_type` | Selection | Trục 3 |
| Chức danh | `job_id` | Many2one | `hr.job` (theo 8.4) |
| Phòng Ban | `department_id` | Many2one | `hr.department` |
| Ngày thử việc | `x_probation_start` | Date | Mốc cổng |
| Ngày chính thức | `x_official_date` | Date | Set khi đạt cổng tháng-2 |
| Ngày nghỉ việc | `departure_date` | Date | |
| Giới tính / NTNS / Nơi sinh / Quốc tịch | `gender / birthday / place_of_birth / country_id` | chuẩn | |
| Số CCCD / Ngày cấp / Nơi cấp | `identification_id / x_id_date_issue / x_id_place_issue` | Char/Date/Char | G-01/02/03 |
| SĐT / Email cá nhân / Email công ty | `private_phone / private_email / work_email` | Char | |
| Địa chỉ thường trú / hiện tại | `x_permanent_* / x_current_*` | Char | G-06 |
| Tình trạng hôn nhân / Học vấn | `marital / certificate` | chuẩn | |
| Người liên lạc / SĐT người thân | `emergency_contact / emergency_phone` | chuẩn | |
| Số tài khoản / Ngân hàng | `bank_account_id` | Many2one | |
| MST TNCN | `x_pit_code` | Char | G-04 |
| Số sổ BHXH / Số thẻ BHYT / Nơi KCB | `x_social_insurance_no / x_health_insurance_no / x_health_care_place` | Char | G-07/08 |
| Checklist tài sản | Records `hr.employee.asset` | One2many | G-17; cấp sau cổng tuần-2 |
| Trình độ tiếng Trung | Skills (Tab Resumé) | One2many | G-10 |
| Số tháng làm việc chính thức | `x_official_months` | Float (computed) | từ `x_official_date` |

## **A.2. Tóm tắt Custom Fields**

| Model | Field name | Loại | FUNC |
|---|---|---|---|
| `hr.employee` | `x_employee_code / x_work_form / x_employment_status / x_position_type / x_official_months` | Char/Sel/Float | F-001 |
| `hr.employee` | `x_id_date_issue / x_id_place_issue / x_pit_code / x_social_insurance_no / x_health_insurance_no / x_health_care_place` | Date/Char | F-002 |
| `hr.employee` | `x_permanent_* / x_current_* (×7 fields)` | Many2one/Char | F-002 |
| `hr.employee` | `x_probation_start / x_eval_2w_* (×4) / x_equip_grant_date / x_eval_2m_* (×4) / x_official_date / x_skip_auto_trigger` | Date/Sel/M2o/Text | F-004 |
| `hr.employee` | `x_trial_lesson_date / x_trial_lesson_class / x_trial_score_method / x_trial_score_content / x_trial_lesson_note / x_trial_lesson_result` | Date/Char/Float/Text/Sel | F-008 |
| `hr.employee.skill` | `x_cert_date / x_cert_expiry / x_cert_verified` | Date/Bool | F-008/009 |
| `hr.employee.dependent` | *(model mới — xem F-003)* | — | F-003 |
| `hr.employee.asset` | *(model mới — xem F-006)* | — | F-006 |
| `hr.promotion.history` | *(model mới — xem F-007)* | — | F-007 |

---

# **PHỤ LỤC B — GIẢ ĐỊNH & CÂU HỎI MỞ CẦN KHÁCH XÁC NHẬN**

| # | Câu hỏi / Giả định | Tác động nếu sai |
|---|---|---|
| GĐ-01 | Giảng viên (Nhóm A) **không** áp cổng thử việc theo mốc tuần-2/tháng-2 (chỉ đánh giá thử giảng 1 lần) | Nếu GV có cổng → cần thêm Plan và AUT cho Nhóm A |
| GĐ-02 | "Quản lý đào tạo chuyên môn" = Trưởng bộ phận (TBP) của phòng nghiệp vụ, không phải bộ phận đào tạo tập trung | Ảnh hưởng phân vai trong AUT-001/002 và Plans |
| GĐ-03 | "Không đạt" cổng tuần-2 → chấm dứt ngay, không gia hạn | Nếu cần gia hạn → bổ sung trạng thái `probation_extended` |
| GĐ-04 | "2 tháng" tính từ **ngày bắt đầu thử việc** (`x_probation_start`), không phải từ ngày đạt cổng tuần-2 | Ảnh hưởng tính `x_eval_2m_due` |
| GĐ-05 | Danh mục "vật dụng cơ bản" khớp với sổ 8.3 Lark (Màn hình, Cây, Bàn phím, Chuột, Tai nghe, Ghế, Bàn, Máy in) — cần khách duyệt danh sách cuối | Ảnh hưởng CONF-EMP-13 |
| GĐ-06 | TTS/Part-time/CTV **không** qua 2 cổng thử việc như nhân viên chính thức | Nếu họ có cổng → bổ sung Plan cho nhóm này |
| GĐ-07 | Luân chuyển cơ sở của Sales quản lý ở **Work Location** trong phân hệ Employees; phụ cấp cơ sở tính bên Payroll | Nếu cần workflow duyệt luân chuyển → thêm chức năng |
| GĐ-08 | Ngưỡng cảnh báo chứng chỉ sắp hết hạn = **60 ngày** | Nếu khách muốn ngưỡng khác → cập nhật `ir.config_parameter` |
| GĐ-09 | Chứng chỉ "Chờ xác minh" (`x_cert_verified = False`) **không** được tính trong CRON cảnh báo | Nếu muốn cảnh báo cả CC chờ xác minh → bỏ điều kiện filter |

---

## **TÀI LIỆU ĐÍNH KÈM**

| Tên file | Nội dung | Định dạng |
|---|---|---|
| `BPMN_TOBE_v2.1_gop.svg` | Sơ đồ TO-BE end-to-end (2 hàng cuộn, 6 lane) | SVG (scalable) |
| `BPMN_TOBE_v2.1_gop.png` | Sơ đồ TO-BE (bản PNG hi-res 3440px để nhúng tài liệu) | PNG |
| `HocBa_Onboarding_TOBE_v2.1.bpmn` | Hàng 1 — Onboarding (mở trong Camunda Modeler) | BPMN 2.0 |
| `HocBa_Lifecycle_Offboarding_TOBE_v2.1.bpmn` | Hàng 2 — Lifecycle + Offboarding (Camunda Modeler) | BPMN 2.0 |
| `WIREFRAME_HoSoTongQuan.svg` | Wireframe màn hình Hồ sơ tổng quan nhân viên | SVG |
| `WIREFRAME_HoSoTongQuan.png` | Wireframe (bản PNG hi-res 2400px) | PNG |

---
*Hết tài liệu đặc tả v2.1 — Phân hệ Employees (Quản lý Nhân sự) — Học Bá Education.*

---

# PHỤ LỤC C — AS-BUILT (BỔ SUNG SAU KHI IMPLEMENT, 12/06/2026)

> Phần này do team dev bổ sung, ghi lại các quyết định chốt và khác biệt giữa đặc tả gốc v2.1 và bản cài đặt thực tế trên module `hocba_employees` (Odoo 19, db Docker `hocba_hrm`). Toàn bộ F-001..F-009 đã hoàn thành và merge vào `main` ngày 10/06/2026.

## C.1. Giả định Phụ lục B — kết quả chốt (10/06/2026, từ 168 bản ghi Lark + quyết định của Vũ)

| Mã | Kết luận |
|----|----------|
| GĐ-01 | Giảng viên (Nhóm A) KHÔNG đi qua 2 cổng thử việc — đi luồng thử giảng F-008. |
| GĐ-02 | TBP (quản lý trực tiếp) là người đánh giá 2 cổng. |
| GĐ-03 | Trượt cổng tuần-2 → chấm dứt, KHÔNG gia hạn. |
| GĐ-04 | Hạn cổng tháng-2 = ngày thử việc + 60 (median Lark = 61 ngày, max 77). |
| GĐ-05 | Danh mục tài sản = 11 mục theo sheet 8.3 Lark; có trạng thái "Đã chuyển giao". |
| GĐ-06 | TTS/Part-time/CTV không có mốc thử việc — xác nhận từ dữ liệu. |
| GĐ-07 | Trường địa điểm làm việc — HOÃN (chưa làm). |
| GĐ-08 | Ngưỡng cảnh báo chứng chỉ = 60 ngày, cấu hình `ir.config_parameter` khóa `hoc_ba.cert_alert_days`. |
| GĐ-09 | Chỉ chứng chỉ ĐÃ XÁC MINH (`x_cert_verified`) mới được CRON cảnh báo. |

## C.2. Khác biệt implement so với đặc tả gốc

1. **F-005 dùng write-trigger Python thay vì `base.automation`**: logic AUT-001/AUT-002 đặt trong `hr_employee.write()` (xem `models/hr_employee.py`) — dễ test, không phụ thuộc module Automation. Cờ `x_skip_auto_trigger` (chỉ HR Manager) để nhập liệu lịch sử không kích hoạt automation.
2. **Thêm trạng thái `exiting` (Đang offboarding)** vào `x_employment_status` — trạng thái trung gian khi trượt cổng, trước khi chuyển `resigned`.
3. **Constraint CCCD đặt trên `hr.version`** chứ không phải `hr.employee` (Odoo 19 chuyển `identification_id` thành related không lưu trên employee). CCCD 12 chữ số; chuỗi có ký tự chữ (hộ chiếu) được bỏ qua kiểm tra.
4. **BR-010 tương tác với AUT-002**: nếu nhân viên chưa khai MST/BHXH mà TBP chấm Đạt cổng tháng-2, automation chuyển Chính thức sẽ bị BR-010 chặn (ValidationError) — HR phải nhập đủ pháp lý TRƯỚC khi chấm Đạt. Đây là hành vi chủ đích.
5. **Chuyển Chính thức thủ công bị khóa**: chỉ HR Manager hoặc automation (context `hocba_gate_automation`) được set `x_employment_status = official`.
6. **Quyền điền kết quả 2 cổng**: HR Manager hoặc quản lý trực tiếp (`parent_id.user_id`); quản lý trực tiếp cần thêm nhóm `hr.group_hr_user` để có ACL ghi `hr.employee`.
7. **Tài sản (F-006)**: mã tài sản gắn với thiết bị vật lý — chuyển giao giữ nguyên mã, ràng buộc "mỗi mã chỉ 1 bản ghi Đang giữ"; cấm `unlink` (audit); chặn Archive nhân viên còn tài sản Đang giữ; chặn cấp phát trước ngày đánh giá tuần-2.
8. **Thăng tiến (F-007)**: tạo bản ghi tự áp `job_id`/`department_id` mới lên employee + post message; cấm xóa; sau 24h chỉ HR Manager sửa (BR-060). Lưu ý ACL: HR Officer vốn chỉ được đọc.
9. **Trường lương/thuế nhạy cảm** (`x_pit_code`, `x_social_insurance_no`) gắn `groups='hr.group_hr_manager'` ở mức field.
10. **2 CRON** chạy 7:00 sáng VN (00:00/00:05 UTC): nhắc đánh giá đến hạn trong 2 ngày; cảnh báo chứng chỉ sắp/đã hết hạn (tạo Activity, chống trùng theo summary — BR-041).
11. **Phòng ban seed 7 bản ghi** (data `hr_department_data.xml`) — danh sách cuối cần xác nhận lại với khách (Lark thực tế: R&D_SP, Kinh Doanh, Marketing, Vận Hành, Phòng Nhân sự, Kế Toán — không có BOD, NS/KT tách riêng, khác CONF-EMP-11).
12. **Danh mục dùng chung `hocba.employee.type`** đặt tại `hocba_employees` (single source); `hocba_users` depends và đọc related qua `hr.employee.x_employee_type_id`.

## C.3. Tình trạng kiểm thử

Backend đã qua bộ test 132 ca (104 ORM + 27 HTTP + khóa tài khoản) ngày 12/06/2026 — chi tiết xem `docs/TEST_BACKEND_2026-06-12.md`. Mọi business rule liệt kê ở C.2 đều có test tương ứng và PASS.
