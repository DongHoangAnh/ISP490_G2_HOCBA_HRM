# 01 — Bối cảnh nghiệp vụ & Phạm vi

## 1. Khách hàng

**Học Bá Education** — doanh nghiệp giáo dục. Quy mô ~ **100+ mã nhân sự** (HB.01 → HB.116+ trong dữ liệu, gồm cả đã nghỉ việc).
Hiện quản lý lương trên **Excel + Lark** (Attendance_Result, bảng công, bảng lương, phiếu chi).

Cơ cấu phòng ban xuất hiện trong dữ liệu: Marketing, Kinh Doanh, Vận Hành, R&D_SP, Kế Toán, HCNS…
Hai hình thức làm việc: **Offline** (nhân sự cơ hữu) và **Online** (cộng tác viên/part-time).

---

## 2. Quy trình "đi lương" hiện tại (giữ nguyên khi số hóa)

| Bước | Nội dung | Hạn | Trách nhiệm |
|---|---|---|---|
| B1 | Hoàn thành **bảng công** (chốt công + nhập OT từ Lark Attendance_Result) | Ngày 04 | HCNS |
| B2 | **Chốt bảng lương** (offline + online, rà thưởng/phụ cấp/khấu trừ) | Ngày 07 | HCNS |
| B3 | **Gửi phiếu lương** cho từng NV qua email để soát | Ngày 08 | Kế toán |
| B4 | **Trình đề xuất chi lương**, Giám đốc duyệt | Ngày 09 | TBP → GĐ |
| B5 | **Thực hiện đi lương** (chuyển khoản) | Ngày 10 | Kế toán |

> Hệ thống mới phải đỡ được luồng: **nhập công → tính lương → phát phiếu → duyệt chi → đánh dấu đã trả**.
> Các state cần có trên bảng lương: `draft → computed → confirmed (TBP xác nhận) → sent (gửi phiếu) → approved (GĐ duyệt) → paid`.
> Giai đoạn BE: chỉ cần các **state field + chuyển trạng thái**; UI luồng duyệt làm sau.

---

## 3. Hai loại bảng lương

### 3.1. Lương OFFLINE (đầy đủ) — file nguồn `5_1__Tính_lương_offline`
69 cột. Bao gồm: chấm công, công chuẩn/công tháng/tăng ca, lương thời gian, lương hợp đồng,
**hoa hồng sale theo Doanh thu × %COM theo Level/KPI**, các phụ cấp, thưởng, **BHXH/BHYT/BHTN**,
**giảm trừ gia cảnh + người phụ thuộc**, **thuế TNCN**, tạm ứng/trừ khác, **THỰC LÃNH**.

Áp dụng cho: nhân sự `Chính thức`, `Thử việc`, `Parttime` (offline).

### 3.2. Lương ONLINE (đơn giản) — file nguồn `5_2__Tính_lương_online`
22 cột. Công thức gọn:

```
TỔNG THU NHẬP = Lương + Thưởng
THỰC LÃNH     = TỔNG THU NHẬP − Tạm ứng/Trừ khác
```

KHÔNG có công, KHÔNG đóng BH, KHÔNG thuế (theo dữ liệu hiện tại). Áp dụng cho nhóm `Online`.

---

## 4. Thông tin nền của nhân sự (master data)

Từ file `2_2__Thông_tin_lương__phúc_lợi` (157 dòng) và `2_3__Thông_tin_thuế__bảo_hiểm`:

**Lương & phúc lợi (2_2)**: Mã NV, Tài khoản Lark, Họ tên, Trạng thái, Phòng ban, Hình thức (Offline/Online),
Chức danh, Loại vị trí (Quản lý/Nhân viên), Ngày thử việc, Tháng/Ngày chính thức, Thâm niên,
**Lương đóng BHXH**, **Lương cơ bản**, các phụ cấp (PC gửi xe, PC xăng xe, PC chức vụ, PC thâm niên,
HT đi lại, HT điện thoại, HT ăn ca, HT trang phục), **Lương KPI**, Số TK, Ngân hàng.

**Thuế & bảo hiểm (2_3)**: Mã số thuế TNCN, CCCD (ngày/nơi cấp), Số sổ BHXH, Số thẻ/Nơi ĐK BHYT,
**Giảm trừ thuế TNCN** (per người phụ thuộc), **Số người phụ thuộc**, **Chính sách bảo hiểm**
(`BH theo định mức` / `Đóng 0.5% BH TNLĐ`…), **Mức lương đóng BH**.

> ❓ Lưu ý mâu thuẫn dữ liệu: "Lương đóng BHXH" (2_2) ≠ "Mức lương đóng BH" (2_3) cho cùng người.
> Hệ thống mới lấy **một** field chuẩn (đề xuất: theo file tính lương `5_1` cột "Lương đóng BH").

---

## 5. Scope giai đoạn này (nhắc lại, chi tiết)

**Phải làm (BE/DB)**
1. Master data nhân sự đủ field phục vụ payroll (file 03).
2. Hợp đồng lương (`hr.contract`) giữ: lương hợp đồng, lương đóng BH, chính sách BH, số NPT, các phụ cấp định mức.
3. Cấu hình bậc hoa hồng sale (Level → ngưỡng KPI → %COM → lương cứng sale).
4. 2 Salary Structure + đầy đủ Salary Rules (file 04, 05).
5. Nhập công theo tháng (worked days input — chấp nhận import, chưa cần máy chấm công).
6. Tạo & tính bảng lương theo lô tháng; xuất các chỉ tiêu khớp Excel.
7. Import dữ liệu lịch sử (10/2025 → 04/2026 đã có trong file).
8. Test đối chiếu (file 07).

**Chưa làm**: React FE, tích hợp máy chấm công/bank/BHXH điện tử, email tự động, e-sign.
