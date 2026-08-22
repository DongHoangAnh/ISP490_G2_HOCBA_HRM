# Bộ seed dữ liệu demo — DB local `hocba_hrm`

Dựng một "công ty Học Bá" hoàn chỉnh để review đủ 11 module: 28 nhân viên,
6 phòng ban, mốc thời gian neo vào **16/08/2026** (một kỳ lương đã chốt +
một kỳ đang chạy).

## Chạy

```powershell
.\tools\demo_seed\seed_all.ps1          # chạy tuần tự p0 → p9
.\tools\demo_seed\run.ps1 p4_timeoff.py # chạy lại một pha
```

> ⚠️ `p0_clean.py` **xoá sạch** dữ liệu nghiệp vụ (nhân viên, chấm công, lương,
> tuyển dụng, đánh giá…) và giữ lại dữ liệu cấu hình. **Chỉ chạy trên DB local**,
> tuyệt đối không chạy trên Neon. Sao lưu trước:
> ```bash
> docker exec isp490_g2_hocba_hrm-db-1 pg_dump -U odoo -d hocba_hrm -f /tmp/bk.sql
> ```

Script chạy trong `odoo shell` của container `isp490_g2_hocba_hrm-odoo-1` nên có
`env` với quyền superuser — không vướng ACL như gọi qua XML-RPC.

## Các pha

| Script | Nội dung |
|---|---|
| `p0_clean.py` | Xoá dữ liệu nghiệp vụ, giữ cấu hình (loại nghỉ, quy tắc lương, template nhận việc, tiêu chí đánh giá, stage tuyển dụng…) |
| `p1_org.py` | 6 phòng ban + trưởng phòng, 28 hồ sơ NV, 28 tài khoản đăng nhập & phân quyền |
| `p2_profile.py` | Chứng chỉ (rải 3 nhóm hạn), người phụ thuộc, tài sản cấp phát, quy trình nhận việc |
| `p3_attendance.py` | Chấm công 01/07–15/08, ca OT/CTV, đơn chấm công, lịch dạy |
| `p4_timeoff.py` | Quỹ phép theo chính sách + 25 đơn nghỉ đủ trạng thái (gồm đơn xin rút) |
| `p5_payroll.py` | Hợp đồng, giờ dạy, kỳ lương 07/2026 (chốt) + 08/2026 (đang chạy) |
| `p5b_fix_rules.py` | Vá dữ liệu quy tắc lương: điều kiện python, `x_is_sale`, rule trùng |
| `p5c_fix_categories.py` | Tách dòng trung gian khỏi nhóm tiền (chống cộng 2 lần) |
| `p5d_fix_base_rule.py` | Dòng lương gốc tính theo `nctt`; gom hợp đồng về cấu trúc Offline |
| `p6_recruitment.py` | 6 phiếu YCTD, 32 ứng viên rải 8 bước, slot phỏng vấn |
| `p7_reviews_career.py` | Đánh giá Q2 (công bố) + Q3 (đang chấm), thăng tiến, lộ trình, vinh danh |
| `p8_service_finance.py` | Nghỉ việc 3 trạng thái, 10 yêu cầu dịch vụ, quỹ tiền + 20 phiếu thu/chi |
| `p9_finalize.py` | Dọn nốt + in bảng tổng kết và danh sách tài khoản |
| `p10_fix_probation_profile.py` | Khai đủ CCCD/MST/BHXH cho NV thử việc rồi chốt các ca đã xong hết bước |
| `p11_onboarding_queue.py` | **Bù** hàng đợi màn Nhận việc cho đủ 4 NV (2 template, rải giai đoạn) |

`common.py` là hằng số/tiện ích dùng chung, được các pha `exec()` vào.

## Lưu ý khi sửa

- Các pha **idempotent**: chạy lại không nhân đôi dữ liệu. Riêng quỹ phép
  (`p4`) chỉ áp chính sách cho NV **chưa có** allocation — allocation đã dùng
  thì Odoo không cho giảm/xoá. `p11` thì **bù cho đủ 4**, không tạo lại: xong
  hết bước rồi HR bấm "Chuyển chính thức" là NV rời hàng đợi, nên chạy lại để
  nạp thêm.
- `random.seed(490)` trong `common.py` → chạy lại ra đúng cùng bộ dữ liệu.
- Nhóm `p5b/p5c/p5d` chỉ vá **dữ liệu cấu hình lương** trong DB. Lỗi gốc nằm ở
  module `hocba_payroll` (chi tiết ghi trong docstring từng file và trong
  `docs/DB_TEST_DATA.md` §4, mục ngày 2026-08-16) — cần chủ sở hữu module sửa.
