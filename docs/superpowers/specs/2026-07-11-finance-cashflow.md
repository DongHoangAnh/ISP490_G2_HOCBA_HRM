# DESIGN SPEC — Module Tài chính / Quản lý dòng tiền (`hocba_finance`)

> **Loại tài liệu:** Design spec "trước code" (theo quy trình `brainstorming → spec` của CLAUDE.md).
> Đây KHÔNG phải FS deliverable. Sau khi implement xong sẽ sinh bộ `FS-FIN-00X` tiếng Anh từ code
> thật theo `FS_SPEC_FORMAT_GUIDE.md`.

| Thuộc tính | Giá trị |
| --- | --- |
| Module code | **FIN** |
| Technical name | `hocba_finance` |
| Project | HRM Odoo — Hoc Ba Education (ISP490_G2) |
| System | Odoo 19 (custom-addons) |
| Owner | (được giao mảng Tài chính) |
| Created | 11/07/2026 |
| Status | **DRAFT — chờ duyệt scope** |

---

## 0. Mục tiêu & triết lý

Xây một **sổ quản lý dòng tiền (cash-flow ledger) độc lập** cho doanh nghiệp Học Bá: ghi nhận
**tiền thực vào (thu)** và **tiền thực ra (chi)**, theo dõi **số dư quỹ**, và xuất **báo cáo Thu −
Chi = Lãi/Lỗ**.

**Nguyên tắc cốt lõi (đã chốt với chủ mảng):**

1. **Thuần dòng tiền (cash basis).** Ghi nhận theo thời điểm tiền thực chạy. **KHÔNG** làm kế toán
   dồn tích / phân bổ theo kỳ (mục 3.2 trong sơ đồ gốc bị loại khỏi phạm vi).
2. **Lợi nhuận = Tổng thu − Tổng chi** (thuần tiền), không phải P&L kế toán.
3. **Độc lập hoàn toàn** với các module khác (payroll, enrollment, timeoff…). "Trả lương" chỉ là
   **một mục chi nhập tay/nhận qua API**, KHÔNG đọc dữ liệu từ `hocba_payroll`.
4. **Quỹ tiền quản theo phòng ban**; role **Giám đốc (BGĐ)** xem/tổng hợp toàn công ty.
5. **Quy trình duyệt gọn:** `Nháp → Duyệt → Ghi sổ`.

---

## 1. Phạm vi

### 1.1 Trong phạm vi (In-scope)

- Danh mục **quỹ tiền** theo phòng ban (+ quỹ tổng công ty).
- Danh mục **mục thu / mục chi** (income/expense categories) — phân loại lý do.
- **Phiếu thu / Phiếu chi** (chứng từ trung tâm) với state machine `draft → approved → posted → cancel`.
- Chiều phân tích **phòng ban** (`hr.department`) trên mỗi phiếu.
- **2 đường nạp thu:**
  - (a) **Nhập tay** — nhân viên tạo phiếu thu (nháp), Kế toán duyệt.
  - (b) **API / JSON** — hệ thống ngoài đẩy khoản thu vào qua endpoint, idempotent theo `external_ref`.
- **Cập nhật số dư quỹ** khi phiếu được ghi sổ (idempotent).
- **Báo cáo:** (1) Tổng quan Thu−Chi=Lãi/Lỗ, (2) Dòng tiền theo thời gian, (3) Theo phòng ban,
  (4) Theo mục thu/chi, (5) Số dư & biến động quỹ.
- **Phân quyền:** nhóm Kế toán, nhóm BGĐ; nhân viên thường tạo phiếu nháp.

### 1.2 Ngoài phạm vi (Out-of-scope)

- ❌ Kế toán dồn tích / deferred revenue / phân bổ doanh thu-chi phí theo kỳ.
- ❌ Tích hợp tự động với `hocba_payroll`, enrollment, học phí, timeoff.
- ❌ Chart of accounts, journal, thuế, hóa đơn, đối chiếu ngân hàng của Odoo `account`.
- ❌ Đa tiền tệ (chỉ **VND**), tỷ giá.
- ❌ SPA React dashboard ở phase đầu (dùng view Odoo pivot/graph; SPA để phase sau).

---

## 2. Mô hình dữ liệu (Data Model)

Ba model mới, tất cả `Custom (new model)`.

### 2.1 `hocba.fund` — Quỹ tiền

| Field | Type | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `name` | Char | required | Tên quỹ (vd "Quỹ tiền mặt — MKT") |
| `code` | Char | required, unique | Mã quỹ (dùng cho API map) |
| `department_id` | Many2one `hr.department` | index | Quỹ thuộc phòng ban; **để trống = quỹ tổng công ty** |
| `fund_type` | Selection | `cash`/`bank`, default `cash` | Tiền mặt / Tài khoản ngân hàng |
| `opening_balance` | Monetary | default 0 | Số dư đầu kỳ |
| `current_balance` | Monetary | compute (store), readonly | `opening + Σ thu posted − Σ chi posted` |
| `currency_id` | Many2one `res.currency` | default VND | Chỉ VND ở phase này |
| `active` | Boolean | default True | Archive |

### 2.2 `hocba.fin.category` — Mục thu/chi

| Field | Type | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `name` | Char | required | Tên mục (vd "Chạy ads", "Học phí") |
| `code` | Char | required, unique | Mã (API map) |
| `category_type` | Selection | `income`/`expense`, required | Loại mục |
| `parent_id` | Many2one self | ondelete `restrict` | Phân cấp (tùy chọn) |
| `active` | Boolean | default True | |

**Seed data (data/fin_category_data.xml):**
- **Income:** Doanh thu bán hàng, Thu từ bảo lưu, Thu hoạt động tài chính, Thu góp vốn, Thu khác.
- **Expense:** Trả lương, Khen thưởng, Outsource, Mua CSVC, Chạy ads, Booking, Gửi sách/Hợp đồng,
  Cước điện thoại, Tiền nhà, Điện nước, Sinh hoạt VP, Internet, Liên hoan/Du lịch, BHXH, Khác.

### 2.3 `hocba.fin.voucher` — Phiếu thu / Phiếu chi (TRUNG TÂM)

| Field | Type | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `name` | Char | readonly, default `/` | Số phiếu tự sinh: `PT/2026/0001` (thu), `PC/2026/0001` (chi) qua `ir.sequence` |
| `voucher_type` | Selection | `income`/`expense`, required | Thu / Chi |
| `amount` | Monetary | required, `> 0` | Số tiền (VND) |
| `voucher_date` | Date | required, default today | **Ngày tiền thực chạy** — mốc cho báo cáo dòng tiền |
| `fund_id` | Many2one `hocba.fund` | required | Quỹ nhận/chi |
| `category_id` | Many2one `hocba.fin.category` | required, domain theo `voucher_type` | Mục thu/chi |
| `department_id` | Many2one `hr.department` | store, related-editable từ `fund_id.department_id` | Chiều báo cáo theo phòng ban |
| `partner_name` | Char | | Người nộp/nhận (đơn giản, không dùng `res.partner`) |
| `memo` | Text | | Diễn giải |
| `source` | Selection | `manual`/`api`, default `manual`, readonly | Nguồn tạo phiếu |
| `external_ref` | Char | index, **unique khi `source=api`** | Mã tham chiếu hệ thống ngoài → **chống trùng** |
| `payload_raw` | Text | readonly | JSON gốc khi nhận từ API (audit) |
| `state` | Selection | `draft`/`approved`/`posted`/`cancel`, default `draft`, tracking | Trạng thái |
| `approved_by` / `approved_date` | Many2one `res.users` / Datetime | readonly | Ai duyệt |
| `posted_by` / `posted_date` | Many2one `res.users` / Datetime | readonly | Ai ghi sổ |
| `company_id` | Many2one `res.company` | default env.company | |
| `currency_id` | Many2one `res.currency` | related `fund_id.currency_id` | |

---

## 3. Luồng nghiệp vụ (Function Flow)

### 3.1 State machine

```
draft ──action_approve()──▶ approved ──action_post()──▶ posted
  ▲            │                  │                        │
  └─ action_reset_draft() ◀───────┘                        │
                                                           ▼
                                      action_cancel() ──▶ cancel  (hoàn số dư nếu đã posted)
```

- **`action_approve()`** — `draft → approved`. Chỉ nhóm **Kế toán** (`group_finance_user`). Ghi
  `approved_by/date`.
- **`action_post()`** — `approved → posted`. Kích hoạt cập nhật số dư quỹ. **Idempotent**: một phiếu
  chỉ tác động số dư đúng một lần (số dư là compute-store từ tập phiếu `posted`, không cộng dồn thủ công).
  Sau `posted` → các field khóa readonly.
- **`action_cancel()`** — về `cancel`. Nếu phiếu đang `posted` → recompute số dư quỹ (loại phiếu này ra).
- **`action_reset_draft()`** — `approved → draft` (sửa lại). Không cho reset phiếu `posted`.

### 3.2 Main Flow — Nhập tay (phiếu thu/chi)

1. Nhân viên/Kế toán mở form phiếu, chọn `voucher_type`, nhập `amount`, `voucher_date`, chọn
   `fund_id`, `category_id`; `department_id` tự điền theo quỹ. Lưu → `draft`.
2. Kế toán kiểm tra → `action_approve()` → `approved`.
3. Kế toán `action_post()` → `posted` → **số dư `fund_id` cập nhật ngay**.
4. Báo cáo phản ánh phiếu (đã `posted`).

### 3.3 Main Flow — Nạp thu qua API/JSON

1. Hệ thống ngoài `POST` payload danh sách khoản thu tới endpoint (mục 4).
2. Controller validate + map `code` (fund/category/department) → id.
3. Với mỗi item: nếu `external_ref` đã tồn tại → **bỏ qua** (idempotent); nếu chưa → tạo
   `hocba.fin.voucher` với `source=api`, `state=draft` (mặc định, chờ Kế toán duyệt — an toàn).
4. Trả JSON `{created, skipped, errors[]}`.

### 3.4 Error / Exception Flow

| Điều kiện | Kết quả |
| --- | --- |
| `amount <= 0` | `ValidationError` |
| `category.category_type != voucher_type` | `ValidationError` |
| Trùng `external_ref` khi tạo qua API | Item bị **skip** (không lỗi), đếm vào `skipped` |
| Ghi sổ khi chưa `approved` | `UserError` |
| Nhân viên thường bấm approve/post | `AccessError` (chặn bởi group) |
| Sửa/xóa phiếu `posted` | `UserError` (chỉ được `cancel`) |
| API sai key | HTTP 401 |
| API map `code` không tồn tại | Item vào `errors[]` với lý do |

---

## 4. Hợp đồng API nạp thu (Ingestion Contract)

- **Endpoint:** `POST /hocba-hrm/api/finance/vouchers`
- **Auth:** header `X-API-Key` khớp `ir.config_parameter` `hocba_finance.api_key`.
- **Controller:** theo pattern project (`hocba_hrm/controllers` hoặc `hocba_finance/controllers`),
  `auth='public'`, `type='json'`, tự kiểm key.

**Request body:**
```json
{
  "vouchers": [
    {
      "external_ref": "ORD-2026-0001",
      "voucher_type": "income",
      "amount": 10000000,
      "date": "2026-07-11",
      "fund_code": "MKT_CASH",
      "category_code": "TUITION",
      "department_code": "MKT",
      "partner_name": "Nguyen Van A",
      "memo": "Học phí khóa HSK4"
    }
  ]
}
```

**Response:**
```json
{ "created": 1, "skipped": 0, "errors": [] }
```

**Ràng buộc:** idempotent theo `external_ref`; item lỗi không làm hỏng cả batch (per-item try/commit
theo savepoint); `payload_raw` lưu JSON gốc mỗi phiếu để audit.

---

## 5. Phân quyền (Security)

| Nhóm (`res.groups`) | Quyền |
| --- | --- |
| `group_finance_user` (**Kế toán**) | CRUD phiếu; approve; post; CRUD quỹ & mục |
| `group_finance_manager` (**BGĐ / Giám đốc**) | Như trên **+ xem toàn bộ quỹ/phiếu/báo cáo toàn công ty** (tổng hợp) |
| Nhân viên thường (mọi user nội bộ) | Tạo phiếu **nháp** (create + read phiếu mình tạo); KHÔNG approve/post |

**Record rules (`ir.rule`):**
- BGĐ + Kế toán: thấy tất cả quỹ/phiếu.
- Trưởng phòng: thấy quỹ/phiếu thuộc **phòng mình** (tái dùng `_managed_department_ids` của
  `hocba_users`/`hocba_employees`) — tùy chọn, nếu muốn phân quyền theo phòng.
- Nhân viên thường: chỉ phiếu do chính mình tạo, trạng thái `draft`.

*Ghi chú:* Odoo 19 dùng `group_ids` cho `res.users` và `res.groups` bỏ `category_id` (xem CLAUDE.md).

---

## 6. Báo cáo (Reports) — bám sơ đồ "Luồng báo cáo"

Phase đầu dùng **view Odoo (pivot / graph / list)** trên `hocba.fin.voucher` (lọc `state=posted`):

| # | Báo cáo | Cách dựng |
| --- | --- | --- |
| 1 | **Tổng quan tài chính** (Thu − Chi = Lãi/Lỗ) | Pivot: hàng = tháng, đo = tổng thu, tổng chi, chênh lệch |
| 2 | **Dòng tiền theo thời gian** | Graph line theo `voucher_date` (ngày/tuần/tháng) |
| 3 | **Theo phòng ban** | Pivot group by `department_id` × `voucher_type` |
| 4 | **Theo mục thu/chi** | Pivot group by `category_id` |
| 5 | **Số dư & biến động quỹ** | List/kanban `hocba.fund` (current_balance) + graph biến động |

SPA React dashboard tổng hợp → **Phase 3 (tùy chọn)**, phục vụ tại `/hocba-hrm`.

---

## 7. Business Rules (nháp — sẽ đánh số `BR-FIN-0X0` khi lên FS)

| ID | Rule | Cơ chế |
| --- | --- | --- |
| BR-FIN-001 | Số tiền dương | `@api.constrains` `amount > 0` |
| BR-FIN-002 | Mục khớp loại phiếu | `category_type == voucher_type` |
| BR-FIN-003 | Chỉ phiếu `posted` ảnh hưởng số dư | `current_balance` compute từ tập `posted` |
| BR-FIN-004 | Ghi sổ idempotent | Số dư là compute-store, không cộng dồn thủ công |
| BR-FIN-005 | Không sửa/xóa phiếu `posted` | override `write()/unlink()` → `UserError`, chỉ cho `cancel` |
| BR-FIN-006 | API idempotent | `external_ref` unique khi `source=api`; trùng → skip |
| BR-FIN-007 | Chuyển trạng thái đúng thứ tự | approve chỉ từ `draft`; post chỉ từ `approved` |
| BR-FIN-008 | Phân quyền duyệt/ghi sổ | chỉ `group_finance_user`/`_manager` |

---

## 8. Phân kỳ (Phasing) — backend trước, UI sau

- **Phase 0 — Nền:** 3 model + `ir.sequence` + seed `hocba.fin.category` + security (2 group,
  ACL, record rule). **+ test.**
- **Phase 1 — Nghiệp vụ dòng tiền:** state machine approve/post/cancel + compute số dư quỹ +
  form/list/pivot/graph views + menu. **+ test** (balance, idempotency, state, permission).
- **Phase 2 — API ingestion:** endpoint + API key + idempotent theo `external_ref` + audit
  `payload_raw`. **+ test** (tạo, trùng, lỗi item).
- **Phase 3 — (tùy chọn) SPA dashboard** tổng quan Thu−Chi−Lãi/Lỗ tại `/hocba-hrm`.

## 9. Kiểm thử (bắt buộc theo CLAUDE.md)

Test Odoo (Docker local), lệnh chuẩn với `MSYS_NO_PATHCONV=1` và `-u hocba_finance,hocba_employees`.
Kết quả cần: `0 failed, 0 error(s) of N tests` với N > 0. Ca test tối thiểu:
- Số dư quỹ = opening + Σthu − Σchi (chỉ posted); post rồi cancel → số dư về đúng.
- Post 2 lần không nhân đôi số dư (idempotent).
- Chuyển trạng thái sai thứ tự → `UserError`.
- `amount<=0`, mục lệch loại → `ValidationError`.
- API: tạo mới, gửi lại `external_ref` → skip, item lỗi không hỏng batch.
- Nhân viên thường không approve/post được (`AccessError`).

## 10. Điểm cần chốt còn lại (Open questions)

1. Record rule theo phòng ban cho Kế toán: **bật** (Kế toán chỉ thấy phòng mình) hay Kế toán thấy
   tất cả, chỉ trưởng phòng bị giới hạn? (Mặc định đề xuất: Kế toán + BGĐ thấy tất cả.)
2. API auto-post hay luôn để `draft` chờ duyệt? (Mặc định đề xuất: **draft**, an toàn.)
3. Có cần chuyển quỹ (fund transfer) giữa các phòng không? (Đề xuất: chưa, để phase sau.)
4. Cho phép số dư quỹ âm không? (Đề xuất: **cảnh báo** chứ không chặn.)
