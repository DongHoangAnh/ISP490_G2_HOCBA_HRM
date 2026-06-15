# Câu hỏi cần xác nhận với Khách hàng — Module Nhân sự (Employees)

> Owner: Tân · Cập nhật: 15/06/2026
> Mục đích: chốt các giả định nghiệp vụ còn mở trước khi hoàn thiện/bàn giao.
> Ký hiệu: 🔴 = cần chốt gấp (ảnh hưởng dữ liệu/logic) · 🟡 = nên chốt · 🟢 = xác nhận cho chắc.

---

## A. Cơ cấu tổ chức & phân loại nhân sự

**A1. 🔴 Danh sách phòng ban cuối cùng?**
- Spec (v2.1) ghi 6 phòng: Marketing, Sản phẩm (R&D_SP), Kinh doanh, Vận hành, **Kế toán_HCNS** (gộp NS+KT), **BOD**.
- Dữ liệu Lark thật lại có: R&D_SP, Kinh Doanh, Marketing, Vận Hành, **Phòng Nhân sự** (tách riêng), **Kế Toán** (tách riêng), **không có BOD**.
- ❓ Chốt: gộp NS+KT hay tách? Có phòng BOD không? Tên chính thức từng phòng?

**A2. 🟡 4 trục phân loại** (hình thức làm việc / tình trạng / loại vị trí / phòng ban) có đúng và đủ không?
- Hình thức: Offline / Online.
- Tình trạng: Thử việc / Chính thức / TTS / Part-time / CTV / Cố vấn / Nghỉ việc.
- Loại vị trí: Quản lý / Nhân viên / CTV / Freelancer / Cố vấn.
- ❓ Có giá trị nào thừa/thiếu? (Dữ liệu Lark cũ bị lẫn "Online" vào cột Tình trạng — cần khách xác nhận giá trị chuẩn.)

**A3. 🟢 Mã nhân sự** theo định dạng `HB.xx` — đúng quy ước? Ai cấp mã (tự sinh hay HR nhập tay)?

---

## B. Luồng Nhập việc — Thử việc 2 cổng & Thử giảng

**B1. 🔴 Khi nào một NV ở trạng thái "Thử việc"?**
- Hiện tại trên demo mọi NV đang "Chính thức" → màn Nhập việc trống.
- ❓ NV thử việc được tạo từ đâu: từ module Tuyển dụng đẩy sang, hay HR tạo tay với trạng thái Thử việc? Mốc "bắt đầu thử việc" lấy theo ngày nào?

**B2. 🟢 Hai cổng đánh giá** (tuần-2 → cấp thiết bị, tháng-2 → chính thức) — đúng quy trình?
- Cổng tháng-2 mặc định hạn = ngày bắt đầu + **60 ngày** (theo dữ liệu Lark: median 61, max 77).
- ❓ Thời gian thử việc chuẩn là 2 tháng? Hạn cổng tuần-2 = +14 ngày đúng không?

**B3. 🟡 Quy tắc "Không đạt" cổng tuần-2?**
- Giả định (theo anh Vũ): **chấm dứt, KHÔNG gia hạn**.
- ❓ Khách xác nhận? Có trường hợp gia hạn thử việc không?

**B4. 🟡 Giảng viên có qua 2 cổng không?**
- Giả định: giảng viên (Nhóm A) **không** qua 2 cổng, thay bằng **thử giảng** (1 buổi, chấm 2 điểm: phương pháp + chuyên môn, thang 1–10).
- ❓ Đúng không? Thang điểm và 2 tiêu chí có phù hợp? Ai chấm (HR / Trưởng bộ phận chuyên môn / cả hai)?

**B5. 🟡 "Cấp thiết bị" tự động** khi đạt cổng tuần-2 (AUT-001): hệ thống cần tự cấp **bộ thiết bị mặc định** nào? (máy tính, màn hình, tai nghe…?) Hay HR cấp tay theo từng người?

**B6. 🟢 Ai có quyền đánh giá cổng?** Hiện: HR Manager **hoặc** quản lý trực tiếp. ❓ Đúng phân quyền?

---

## C. Quản lý Tài sản (F-006)

**C1. 🟢 Danh mục 11 loại tài sản** (từ sổ 8.3 Lark) đã đủ chưa? Có cần thêm loại?

**C2. 🟡 Quy tắc chuyển giao** (BR-050): khi chuyển giao, **giữ nguyên mã thiết bị**, tự tạo bản ghi mới cho người nhận; mỗi mã chỉ 1 người "đang giữ" tại một thời điểm. ❓ Đúng thực tế?

**C3. 🟡 Không cho xoá bản ghi tài sản** (chỉ Thu hồi/Chuyển giao) để giữ lịch sử. ❓ Khách đồng ý chính sách này?

**C4. 🟢 Chặn lưu trữ (archive) NV khi còn tài sản chưa thu hồi** — đúng mong muốn?

---

## D. Thăng tiến & Lương (F-007)

**D1. 🟡 Lịch sử thăng tiến không cho xoá** (audit trail); sau **24h** chỉ HR Manager được sửa. ❓ Khoảng thời gian 24h hợp lý? Ai được sửa/huỷ một mốc đã ghi nhầm?

**D2. 🟢 Tạo mốc thăng tiến tự cập nhật chức vụ + phòng ban hiện tại của NV** — đúng mong muốn?

**D3. 🔴 Ai được xem lương?** Hiện: chỉ **HR Manager** thấy lương cơ bản (HR User và NV thường không thấy). ❓ Đúng chính sách bảo mật lương?

**D4. 🟡 Khi đổi mức lương** bắt buộc nhập **Lý do/Căn cứ** + số quyết định. ❓ Có cần thêm trường (phụ cấp chi tiết, hệ số…)?

---

## E. Chứng chỉ & Kỹ năng (F-008/009)

**E1. 🔴 Bộ chứng chỉ cần quản lý?**
- Hiện có 2 nhóm: **Tiếng Trung** (HSK 1–6, HSKK Sơ/Trung/Cao, TOCFL A2–C2) và **Sư phạm ngoại ngữ** (Bằng ĐH, NVSP, CTCSOL).
- ❓ Có cần thêm ngôn ngữ khác (Anh, Nhật, Hàn…)? Còn loại chứng chỉ nào khác?

**E2. 🟡 Cấp độ chứng chỉ** dùng chung Sơ/Trung/Cao cấp cho cả nhóm Tiếng Trung — có phù hợp, hay mỗi chứng chỉ nên gắn cấp riêng?

**E3. 🟢 "Xác minh"**: chỉ chứng chỉ **đã xác minh** (HR kiểm bản gốc) mới được cảnh báo hết hạn. ❓ Đúng quy trình?

**E4. 🟡 Ngưỡng cảnh báo hết hạn = 60 ngày** (cấu hình được). ❓ Khách muốn mốc bao nhiêu ngày? Cảnh báo gửi cho ai (HR / quản lý / chính NV)?

---

## F. Người phụ thuộc & Hồ sơ pháp lý (F-002/003)

**F1. 🟢 Ràng buộc định dạng:** CCCD 12 số; MST 10 hoặc 13 số; số sổ BHXH 10 số. ❓ Đúng chuẩn?

**F2. 🟡 Điều kiện lên Chính thức** (BR-010): bắt buộc đã có **MST + BHXH**. ❓ Còn điều kiện nào khác (HĐLĐ, khám sức khoẻ…)?

**F3. 🟢 Địa chỉ 2 cấp** (thường trú / tạm trú, có tỉnh/thành) — đủ chưa, hay cần tới phường/xã chuẩn hoá?

**F4. 🟡 Người phụ thuộc** dùng cho giảm trừ gia cảnh: các trường (quan hệ, ngày sinh, CCCD, ngày bắt đầu/kết thúc giảm trừ) đã đủ cho mục đích thuế chưa?

---

## G. Phân quyền

**G1. 🔴 HR User có được quản lý Người phụ thuộc không?**
- Hiện: chỉ **HR Manager** thêm/sửa/xoá NPT; HR User chỉ xem.
- ❓ Có muốn HR User cũng quản lý NPT? (chỉ cần đổi 1 dòng cấu hình quyền).

**G2. 🟡 Phân quyền tổng thể:** ngoài 4 vai trò demo (NV / NV thử việc / HR User / HR Manager), có vai trò nào khác (Trưởng bộ phận xem hồ sơ phòng mình, BOD xem toàn bộ…)?

**G3. 🟢 NV tự sửa hồ sơ:** hiện NV chỉ tự sửa **điện thoại + địa chỉ**. ❓ Có cho NV tự cập nhật thêm trường nào (ảnh, liên hệ khẩn cấp…)?

---

## H. Phạm vi & Tích hợp

**H1. 🟡 Nghỉ việc / Offboarding:** hiện có trạng thái "Nghỉ việc"/"exiting". ❓ Khách có cần quy trình offboarding đầy đủ (thu hồi tài sản, bàn giao, quyết định thôi việc) trong module này?

**H2. 🟡 Hợp đồng lao động:** quản lý HĐLĐ (loại HĐ, thời hạn, gia hạn) thuộc module này hay Payroll/khác?

**H3. 🟡 File đính kèm:** có cần lưu bản scan (CCCD, bằng cấp, chứng chỉ, HĐ) đính kèm hồ sơ?

**H4. 🟢 Di trú dữ liệu (migration):** 168 bản ghi Lark thật — cần làm sạch trước khi nhập (cột Tình trạng lẫn "Online", "Loại vị trí" có khoảng trắng thừa). ❓ Khách cung cấp file Lark mới nhất + xác nhận quy tắc làm sạch.

---

## Tổng hợp các câu 🔴 cần chốt gấp
1. **A1** — danh sách phòng ban cuối cùng (gộp/tách NS-KT, có BOD?).
2. **B1** — NV thử việc được tạo từ đâu, mốc bắt đầu thử việc.
3. **D3** — chính sách ai được xem lương.
4. **E1** — bộ chứng chỉ cần quản lý (có thêm ngôn ngữ khác?).
5. **G1** — HR User có quản lý Người phụ thuộc không.
