# Thiết kế: Offboarding — Quy trình Thôi việc (MVP thống nhất)

- **Ngày:** 2026-07-04
- **Module:** `hocba_employees` (backend) + `hocba_hrm` (controller API + SPA)
- **Owner:** Vu/Tan (nhánh `Tan/Employee`)
- **Liên quan spec gốc:** `docs/SPEC_EMPLOYEES_DAC_TA_v2.1.md` — mục 2.2.4, GIAI ĐOẠN 3 (Luồng 3A/3B), G-16/G-17, CONF-EMP-08a/08b.

## 1. Bối cảnh & Vấn đề

Module hiện tại đã có khung trạng thái vòng đời (`exiting`, `resigned` trong `x_employment_status`) và
chặn Archive khi còn tài sản chưa thu hồi ([`hr_employee.py:590`](../../../custom-addons/hocba_employees/models/hr_employee.py)),
nhưng **chưa có quy trình thôi việc thực sự**:

- `_hocba_start_offboarding` (rớt thử việc) chỉ set `x_employment_status='exiting'` + tạo activity, **không đóng được hồ sơ**.
- **Không có cách nào** để một NV chính thức nghỉ việc: không có đơn xin nghỉ, không có phê duyệt, không có bước
  chuyển `exiting → resigned`. Grep toàn addon: `'resigned'` chỉ xuất hiện ở selection/statusbar/màu chip, **không dòng code nào set nó**.

## 2. Phạm vi (MVP thống nhất 1 luồng)

Một cơ chế offboarding **dùng chung** cho cả nghỉ thử việc lẫn nghỉ chính thức:
đơn/quyết định nghỉ → duyệt → thu hồi tài sản → hoàn tất (`resigned` + archive + khoá tài khoản).

**Ngoài phạm vi (YAGNI cho MVP):**
- Không tích hợp payroll để tính lương cuối/công nợ tự động — chỉ checklist thủ công (có thể mở rộng sau).
- Không làm quy trình 7 bước đầy đủ với "Giám đốc phê duyệt" riêng biệt — dùng 2 cấp duyệt (quản lý trực tiếp + HR).
- Không snapshot lịch sử thăng tiến khi nghỉ (không cần thiết cho MVP).

## 3. Model dữ liệu

**Model mới: `hocba.offboarding`** — Đơn/Quy trình thôi việc. 1 bản ghi = 1 lần nghỉ (giữ lịch sử đầy đủ, hỗ trợ nghỉ nhiều lần nếu tái tuyển).

Kế thừa `mail.thread`, `mail.activity.mixin` (chatter + activity như các model khác trong module).

| Field | Kiểu | Ghi chú |
|---|---|---|
| `name` | Char, readonly | Mã tự sinh `OFF/YYYY/NNNN` qua `ir.sequence` |
| `employee_id` | Many2one `hr.employee` | required, `ondelete='cascade'` |
| `source` | Selection | `self` (NV tự nộp) / `hr` (HR khởi tạo thay) / `probation` (rớt thử việc, auto). Default `self`. |
| `reason_type` | Selection | `voluntary` (tự nguyện) / `performance` (không đạt) / `contract_end` (hết hạn HĐ) / `other`. required |
| `reason` | Text | Lý do chi tiết |
| `request_date` | Date | Ngày nộp đơn, default `today` |
| `expected_leave_date` | Date | Ngày nghỉ dự kiến. required |
| `actual_leave_date` | Date | Ngày nghỉ thực tế — set khi `done` |
| `mgr_approved_by` | Many2one `res.users`, readonly | Vết duyệt cấp quản lý |
| `mgr_approved_date` | Datetime, readonly | |
| `hr_approved_by` | Many2one `res.users`, readonly | Vết duyệt HR |
| `hr_approved_date` | Datetime, readonly | |
| `chk_handover` | Boolean | Đã bàn giao công việc/lớp học |
| `chk_payroll` | Boolean | Đã chốt lương / công nợ |
| `chk_documents` | Boolean | Đã lưu hồ sơ |
| `asset_pending_count` | Integer, compute | Số tài sản của NV còn `state='assigned'` (live, không lưu) |
| `state` | Selection | Xem §4. Default `draft`, `tracking=True` |
| `prev_employment_status` | Char, readonly | Kỹ thuật — lưu `x_employment_status` của NV trước khi set `exiting`, để hoàn nguyên khi `refuse` |
| `note` | Text | Ghi chú xử lý |

`asset_pending_count` compute từ `employee_id.x_asset_ids` lọc `state='assigned'`.

## 4. State machine

```
draft → submitted → mgr_approved → hr_approved → done
   │         │            │
   │         └── refused  └── refused
   └──────────── cancelled (từ draft hoặc submitted)
```

| Action (method) | Chuyển | Ai được phép | Hiệu ứng phụ |
|---|---|---|---|
| `action_submit` | draft → submitted | NV (đơn của mình) hoặc HR Manager | message_post; activity nhắc cấp quản lý duyệt |
| `action_mgr_approve` | submitted → mgr_approved | **User quản lý trực tiếp phạm vi NV** (trưởng phòng NV, HOẶC giáo vụ nếu NV là giáo viên) hoặc HR Manager | ghi `mgr_approved_by/_date`; **set NV `x_employment_status='exiting'`**; activity nhắc HR duyệt |
| `action_hr_approve` | mgr_approved → hr_approved | HR Manager | ghi `hr_approved_by/_date`; activity nhắc thu hồi tài sản + hoàn tất |
| `action_refuse` | submitted/mgr_approved → refused | Cùng người có quyền duyệt bước đó | message_post lý do; NV về trạng thái trước (nếu đã `exiting` → về trạng thái cũ) |
| `action_cancel` | draft/submitted → cancelled | Người tạo hoặc HR Manager | message_post |
| `action_done` | hr_approved → done | HR Manager | **Xem §5** |

**Ghi chú `refuse`:** khi `action_mgr_approve` set NV sang `exiting`, lưu trạng thái cũ vào field kỹ thuật
`prev_employment_status` (Char, readonly) trên chính bản ghi đơn. Khi `action_refuse` ở bước `mgr_approved`,
hoàn nguyên `x_employment_status` của NV về `prev_employment_status` để không kẹt `exiting`.

## 5. `action_done` — Hoàn tất & Đóng bảo mật

Chạy khi HR Manager bấm Hoàn tất (state `hr_approved → done`). Thứ tự:

1. **Chặn nếu còn tài sản** — nếu `employee_id` còn tài sản `state='assigned'` → `ValidationError`
   (tái dùng logic đã có ở `write()` block-archive). Yêu cầu thu hồi/chuyển giao hết trước.
2. Set `actual_leave_date = today`.
3. `employee_id.sudo().with_context(hocba_gate_automation=True).write({'x_employment_status': 'resigned', 'active': False})`.
4. **Khoá tài khoản liên kết:** nếu `employee_id.user_id` → `user_id.sudo().write({'active': False})`.
5. `message_post` xác nhận hoàn tất.

Tất cả bước ghi nhạy cảm dùng `.sudo()` **sau khi** đã xác thực `env.user` là HR Manager (theo gotcha self-service của dự án).
`with_context(hocba_gate_automation=True)` để đi qua guard `write()` hiện có (F-001 chặn set official thủ công; ở đây set resigned + active=False, context giúp automation nhất quán).

## 6. Tích hợp luồng rớt thử việc (3A cũ)

Sửa `_hocba_start_offboarding(gate_label)` ([`hr_employee.py:688`](../../../custom-addons/hocba_employees/models/hr_employee.py)):
thay vì chỉ set `exiting`, **tạo 1 bản ghi `hocba.offboarding`**:

```python
self.env['hocba.offboarding'].sudo().create({
    'employee_id': self.id,
    'source': 'probation',
    'reason_type': 'performance',
    'reason': _('Không đạt cổng thử việc %s') % gate_label,
    'expected_leave_date': today,
    'state': 'hr_approved',   # quyết định rớt cổng ≈ đã duyệt
})
```

Đồng thời vẫn set NV `x_employment_status='exiting'` và tạo activity nhắc HR thu hồi tài sản + bấm Hoàn tất.
→ Cả 2 luồng (thử việc / chính thức) **đóng hồ sơ qua cùng `action_done`**, thống nhất đúng mục tiêu MVP.

## 7. Phân quyền

Tái dùng khái niệm scope sẵn có (`_emp_scope_domain` / `_emp_in_scope` / `_managed_department_ids`
trong `hocba_hrm/controllers/main.py`; `_hocba_user_manages_dept` trong model). ACL + record rules:

| Vai trò | Quyền trên `hocba.offboarding` |
|---|---|
| **NV thường** | Create/read/write/`submit` đơn **của chính mình** khi còn `draft`; read đơn của mình mọi trạng thái. Không sửa sau khi submit. |
| **Cấp quản lý trực tiếp** — Trưởng phòng (NV trong phòng mình + phòng con) **và Giáo vụ** (các giáo viên, `x_employee_type_id.code='teacher'`) | Read + `action_mgr_approve`/`refuse` đơn của NV **thuộc phạm vi quản lý của mình**. Giáo vụ duyệt đơn giáo viên **ngang** trưởng phòng duyệt đơn phòng mình. |
| **HR Manager** (`hr.group_hr_manager`) | Toàn quyền: read tất cả, `hr_approve`, `done`, `cancel`, khởi tạo thay NV. |
| **Giáo vụ với NV không phải giáo viên** | Không có quyền (ngoài phạm vi). |

**Nguyên tắc:** bước `mgr_approve` không hard-code "trưởng phòng" mà kiểm **"user hiện tại có quản lý phạm vi
của `employee_id` không"** — tức trưởng phòng của phòng NV, hoặc giáo vụ nếu NV là giáo viên. Nhất quán với `canManage` toàn hệ thống.

Record rule cho NV thường: `['|', ('employee_id.user_id', '=', user.id), (điều kiện quản lý/HR)]`.
Kiểm quyền theo state đặt trong các `action_*` (raise `AccessError` nếu sai vai trò/phạm vi) để chắc chắn cả khi gọi qua API.

## 8. SPA / API

Controller `hocba_hrm/controllers/main.py` — nhóm endpoint `/hocba-hrm/api/offboarding/*` (auth='user', type='json'):

| Endpoint | Method | Mô tả |
|---|---|---|
| `/hocba-hrm/api/offboarding/submit` | POST | NV tự nộp đơn. Body: `reason_type`, `reason`, `expected_leave_date`. Server **pin `employee_id` theo user đăng nhập** (không cho chỉ định NV khác). Tạo bản ghi `source='self'`, gọi `action_submit`. |
| `/hocba-hrm/api/offboarding/list` | GET/POST | Danh sách đơn theo phạm vi quyền user (dùng scope domain). Trả về `canManage`, danh sách đơn + `asset_pending_count`. |
| `/hocba-hrm/api/offboarding/action` | POST | Body: `{id, action, note?}` với `action ∈ {submit, mgr_approve, hr_approve, refuse, cancel, done}`. Server kiểm quyền theo state + vai trò rồi gọi method tương ứng. |

**SPA (React) — tối thiểu, 2 điểm chạm:**
1. **Hồ sơ của tôi** → khu "Nghỉ việc": form nộp đơn (lý do, ngày nghỉ dự kiến) + hiển thị trạng thái đơn của mình.
2. **Màn quản lý** → tab/list "Đơn nghỉ việc": danh sách trong phạm vi + nút Duyệt/Từ chối/Hoàn tất theo vai trò + badge số tài sản chưa thu hồi.

**Thứ tự làm:** backend chắc trước (model + security + API + test đỏ→xanh), SPA sau — đúng workflow dự án.

## 9. Kiểm thử (TDD)

File `custom-addons/hocba_employees/tests/test_offboarding.py`. Chạy:
```
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo \
  odoo -d hocba_hrm -u hocba_employees --addons-path=/mnt/extra-addons \
  --test-enable --test-tags /hocba_employees --stop-after-init --log-level=test
```

Ca kiểm thử:
- **Happy path:** draft → submit → mgr_approve → hr_approve → done; kiểm state + `x_employment_status` từng bước (`exiting` sau mgr_approve, `resigned` sau done).
- **Block done khi còn tài sản:** NV còn asset `assigned` → `action_done` raise `ValidationError`; sau khi `returned` thì done OK.
- **Done → đóng bảo mật:** sau done, NV `active=False`, `x_employment_status='resigned'`, `user_id.active=False`.
- **Phân quyền:**
  - NV không tự duyệt được đơn của mình (`AccessError`).
  - Trưởng phòng phòng A không duyệt được đơn NV phòng B.
  - **Giáo vụ duyệt được đơn của giáo viên**, nhưng **KHÔNG** duyệt được đơn NV văn phòng.
  - Chỉ HR Manager gọi được `action_done`.
- **Refuse hoàn nguyên:** từ chối ở `mgr_approved` → NV về trạng thái trước (không kẹt `exiting`).
- **Luồng thử việc:** rớt cổng (`_hocba_aut_001` với `fail`) → tự tạo `hocba.offboarding` `source='probation'` state `hr_approved`; NV `exiting`.
- **BR-010:** NV `official` trong test có `identification_id` đúng 12 chữ số, mỗi NV một giá trị.

## 10. Kế hoạch triển khai (tóm tắt — sẽ chi tiết ở writing-plans)

1. Model `hocba.offboarding` + sequence + state machine (test đỏ→xanh).
2. Enforcement `action_done` + tích hợp `_hocba_start_offboarding`.
3. Security (ACL + record rules) + test phân quyền.
4. View backend Odoo (form/list/statusbar) cho HR thao tác.
5. API controller `/hocba-hrm/api/offboarding/*` + test.
6. SPA: form nộp đơn (Hồ sơ của tôi) + list quản lý.
7. Cập nhật `docs/DB_TEST_DATA.md` nếu seed dữ liệu mẫu.
