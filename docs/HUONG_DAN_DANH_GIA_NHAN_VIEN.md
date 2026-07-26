# Hướng dẫn sử dụng — Đánh giá nhân viên

> Dành cho HR, trưởng phòng và giáo vụ. Công thức chi tiết:
> [CONG_THUC_DANH_GIA.md](CONG_THUC_DANH_GIA.md) · Thiết kế kỹ thuật:
> [spec](superpowers/specs/2026-07-26-performance-review-design.md)

## 1. Vào màn hình

Đăng nhập SPA → sidebar **Quản lý nhân sự → Đánh giá**. Màn hình có 2 tab:

- **Giảng viên** — nhân sự có Loại nhân viên = *Giáo viên*
- **Nhân viên văn phòng** — các loại còn lại (văn phòng, cộng tác viên)

Hai tab dùng **hai bộ tiêu chí khác nhau**, không lẫn lộn.

## 2. Ai thấy được gì

| Vai trò | Phạm vi | Được làm |
|---|---|---|
| Admin, HR Manager, HR officer | Toàn bộ nhân sự | Mở đợt, chấm, chốt, công bố, mở lại |
| Trưởng phòng | Nhân viên phòng mình (gồm phòng con) | Chấm, chốt |
| Giáo vụ | Chỉ giáo viên | Chấm, chốt |
| Nhân viên thường | — | Nhận thông báo kết quả khi HR công bố |

## 3. Quy trình 4 bước

### Bước 1 — Mở đợt đánh giá (HR)

1. Chọn **kỳ**: loại kỳ (Quý / Nửa năm / Năm) → kỳ thứ mấy → năm.
2. Bấm **Mở đợt đánh giá**.

Hệ thống tạo phiếu Nháp cho mọi nhân sự đang làm việc trong nhóm và tự tính
ngay các chỉ số chuyên cần. Bấm lại nhiều lần **không tạo trùng** — người đã có
phiếu sẽ bị bỏ qua (hệ thống báo rõ số tạo mới / số bỏ qua).

> Không muốn mở cả đợt? Click thẳng vào một dòng nhân viên chưa có phiếu — hệ
> thống tạo phiếu riêng cho người đó rồi mở luôn màn chấm.

### Bước 2 — Chấm điểm (quản lý trực tiếp)

Click vào dòng nhân viên để mở phiếu. Trong phiếu:

- **Khối chỉ số** phía trên là số liệu hệ thống lấy từ chấm công, nghỉ phép,
  chứng chỉ — dùng làm căn cứ khi chấm các tiêu chí định tính.
- Mỗi tiêu chí chấm bằng cách bấm số từ **0 đến 5** (0 = chưa chấm).
- Tiêu chí có nhãn **"Tự động"** đã được điền sẵn điểm đề xuất. Bạn vẫn sửa được;
  khi sửa khác đề xuất, hệ thống gắn nhãn *"Quản lý sửa đè"* và lần **Tính lại
  chỉ số** sau đó sẽ không ghi đè điểm bạn đã chọn.
- **Tổng điểm và xếp loại đổi ngay** khi bấm điểm, không cần bấm Lưu.
- Bắt buộc nhập **Nhận xét của quản lý** trước khi chốt.

Bấm **Lưu nháp** nếu muốn chấm dở rồi quay lại sau.

### Bước 3 — Chốt (quản lý hoặc HR)

Bấm **Chốt đánh giá**. Hệ thống chặn nếu chưa chấm điểm nào hoặc chưa có nhận
xét quản lý. Sau khi chốt:

- Điểm và chỉ số bị **đóng băng** — dữ liệu chấm công sau này có sửa cũng không
  làm đổi phiếu.
- Kết quả được ghi vào lịch sử trao đổi (chatter) trên hồ sơ nhân viên.
- Muốn sửa lại thì cần HR bấm **Mở lại phiếu**.

### Bước 4 — Công bố (chỉ HR/Admin)

Bấm **Công bố cho nhân viên**. Nhân viên nhận thông báo ở chuông trong SPA kèm
điểm và xếp loại của mình.

## 4. Đọc kết quả

| Xếp loại | Điểm | Gợi ý hành động |
|---|---|---|
| **A — Xuất sắc** | ≥ 85 | Xét thưởng, đưa vào diện quy hoạch thăng tiến |
| **B — Tốt** | 70–84 | Ghi nhận, đặt mục tiêu nâng cao kỳ sau |
| **C — Đạt** | 55–69 | Chỉ ra 1–2 điểm cần cải thiện cụ thể |
| **D — Cần cải thiện** | < 55 | Lập kế hoạch cải thiện, hẹn tái đánh giá |

Bốn thẻ số liệu đầu màn hình cho biết nhanh: tổng nhân sự trong nhóm, số đã
đánh giá, điểm trung bình và số người loại A/D của kỳ đang xem.

## 5. Câu hỏi thường gặp

**Nhân viên mới chưa có dữ liệu chấm công thì sao?**
Hệ thống **không tự chấm** tiêu chí chuyên cần (hiện "thiếu dữ liệu — cần chấm
tay"). Thiếu dữ liệu không đồng nghĩa làm việc kém, nên quản lý tự chấm.

**Sửa trọng số tiêu chí có làm sai lệch phiếu cũ không?**
Không. Trọng số và điểm tối đa được sao chép vào phiếu ngay lúc tạo.

**Vì sao điểm chuyên cần của giáo viên thấp dù đi dạy đủ?**
Tiêu chí này tính theo **chấm công buổi dạy hợp lệ**: đúng cửa sổ giờ, đúng vị
trí lớp, ảnh khuôn mặt không bị nghi ngờ. Chấm công sai quy định vẫn bị tính là
buổi không đạt — nếu do lỗi thiết bị, quản lý sửa điểm và ghi chú lý do.

**Đổi ngưỡng xếp loại hoặc chỉ tiêu buổi dạy ở đâu?**
Trong Odoo backend, Cài đặt → Kỹ thuật → Tham số hệ thống, sửa các khoá
`hocba_reviews.grade_a` / `grade_b` / `grade_c` /
`hocba_reviews.teacher_sessions_target`. Xem bảng đầy đủ ở
[CONG_THUC_DANH_GIA.md §6](CONG_THUC_DANH_GIA.md).

**Xoá phiếu được không?**
Chỉ xoá được phiếu đang Nháp. Phiếu đã chốt/công bố giữ lại để lưu vết đánh giá.
