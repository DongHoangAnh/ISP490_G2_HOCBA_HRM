# 07 — Bộ Test Nghiệm Thu (số thật từ Excel)

> Mục tiêu: chứng minh engine tính ĐÚNG. Dùng số đã đối chiếu từ `5_1`/`5_2`.
> Nguyên tắc: **hard-assert** các dòng có math sạch (NET, BH); **review-only** các dòng thuế>0
> (vì ô thuế Excel có sai số nhập tay — xem file 05 mục 3).

---

## 1. Test BH & NET — OFFLINE (hard assert)

### TC-01 — HB.01, Tháng 3/2026 (có NPT=1, thuế=0)
| Đầu vào | Giá trị |
|---|---|
| Lương hợp đồng (wage) | 20.000.000 |
| Công tháng / Tổng công / STD_DAYS | 24 / 24 / 24 |
| Lương đóng BH | 7.300.000 |
| Số NPT | 1 |
| Thưởng khác | 150.000 |

| Kết quả mong đợi | Giá trị | Assert |
|---|---|---|
| LUONG_TG | 20.000.000 | == |
| GROSS | 20.150.000 | == |
| BHXH_NV / BHYT_NV / BHTN_NV | 584.000 / 109.500 / 73.000 | == |
| Tổng BH NV | 766.500 | == |
| TI (TN tính thuế) | 0 | == |
| TNCN | 0 | == |
| **NET (THỰC LÃNH)** | **19.383.500** | **== (hard)** |

### TC-02 — HB.01, Tháng 1/2026 (không có thưởng)
- GROSS = 20.000.000; BH NV = 766.500; thuế = 0 → **NET = 19.233.500** (hard ==)

---

## 2. Test NET — ONLINE (hard assert)

### TC-04 — HB.32, Tháng 3/2025
- Lương 10.000.000 + Thưởng 1.000.000 − 0 = **NET 11.000.000** (hard ==)

### TC-05 — HB.32, Tháng 4/2025 (không thưởng)
- Lương 10.000.000 − 0 = **NET 10.000.000** (hard ==)

---

## 3. Test hàm con (unit)

### TC-06 — `_hocba_pit(taxable)` (7 bậc)
| TI | Thuế mong đợi |
|---|---|
| 0 | 0 |
| 5.000.000 | 250.000 |
| 10.000.000 | 750.000 |
| 12.563.941 | 1.134.591 |
| 18.000.000 | 1.950.000 |
| 32.000.000 | 4.750.000 |
| 100.000.000 | 25.150.000 |

### TC-07 — BH theo policy
| Policy | base | BHXH_NV | BHYT_NV | BHTN_NV |
|---|---|---|---|---|
| standard | 7.300.000 | 584.000 | 109.500 | 73.000 |
| standard | 5.700.000 | 456.000 | 85.500 | 57.000 |
| none | bất kỳ | 0 | 0 | 0 |

---

## 4. Test đối soát tổng (reconciliation)

Sau import lịch sử + tính lại (với engine mới), so cho từng tháng:

| Chỉ tiêu | Cách kiểm |
|---|---|
| Số phiếu offline/tháng | == số dòng `5_1` của tháng đó |
| Σ NET offline (thuế=0 rows) | == Σ THỰC LÃNH Excel các dòng thuế=0 |
| Σ NET online | == Σ Thực lãnh `5_2` |
| Danh sách thiếu số TK | khớp cảnh báo "Employees Without Bank account" |

> Σ NET các dòng có thuế>0 sẽ **lệch** so với Excel (do thuế đúng luật) — đây là sai số *mong muốn*,
> ghi nhận và giải thích, không coi là lỗi.

---

## 5. Khung test Odoo (gợi ý)

```python
from odoo.tests import TransactionCase, tagged

@tagged('post_install','-at_install','hocba')
class TestHocBaPayroll(TransactionCase):

    def _make_payslip(self, code, period, **kw):
        # helper: tạo employee+contract+payslip theo input, compute_sheet()
        ...

    def test_tc01_hb01_net(self):
        slip = self._make_payslip('HB.01', '2026-03', wage=20_000_000,
                                  ins_base=7_300_000, dependents=1,
                                  paid_days=24, std_days=24, bonus_other=150_000)
        self.assertEqual(self._line(slip,'NET'), 19_383_500)

    def test_tc06_pit_brackets(self):
        f = self.env['hr.payslip']._hocba_pit
        self.assertEqual(f(5_000_000), 250_000)
        self.assertEqual(f(12_563_941), 1_134_591)
```

> Chạy: `docker compose exec odoo odoo -d neondb -i hocba_payroll --test-enable --test-tags hocba --stop-after-init`

---

## 6. Định nghĩa "PASS giai đoạn BE"

- Tất cả TC hard-assert (TC-01, 02, 04, 05, 06, 07) xanh.
- Import 7 tháng lịch sử không lỗi; đối soát tổng (mục 4) đạt.
- Cảnh báo thiếu TK ngân hàng/hợp đồng hoạt động.
- Có báo cáo chênh lệch thuế Excel <-> hệ thống cho khách duyệt.
→ Đạt thì mới chuyển sang làm FE React.
