# Spec — Cấu hình tuyển dụng · v1.2

> v1.2 (2026-08-03, theo yêu cầu user): quyền **nới lại** từ CHỈ Admin →
> **Admin hoặc HR Manager** (`base.group_system` | `hr.group_hr_manager`), cho
> khớp màn "Cấu hình nhận việc" vốn đã dùng `need: 'hrm'`. Backend thêm
> `_can_config()` thay cho `_is_admin()` trên 6 route cấu hình; sidebar đổi
> `need: 'admin'` → `'hrm'`. **Không** mở cho nhóm tuyển dụng
> (`group_hr_recruitment_user`): họ chạy quy trình hằng ngày chứ không phải
> người được đổi quy trình/hạn xử lý.
>
> v1.1 (2026-07-23): quyền siết từ HR toàn quyền → **CHỈ Admin
> (`base.group_system`)**; UI chuyển từ tab trong màn Tuyển dụng → **mục sidebar
> riêng "Cấu hình tuyển dụng"** (như "Cấu hình nhận việc"), `need: 'admin'`.

**Ngày**: 2026-07-23 · **Owner**: Việt (`hocba_recruitments`) · **Nhánh**: `Viet/Recruitment`

## Bối cảnh

Gợi ý của giáo viên: đăng nhập role Admin cần có phần **cấu hình tuyển dụng** để khi
công ty (Học Bá) yêu cầu chỉnh sửa quy trình thì tự chỉnh trên UI, không phải sửa code.
Hiện trạng hardcode:

- Quy trình 10 bước seed trong `data/hr_recruitment_stages.xml` với `noupdate="0"` —
  admin sửa trong DB cũng bị XML ghi đè khi upgrade module.
- Thời hạn xử lý từng bước ("trong 24h", "1 ngày làm việc") chỉ là text mô tả, hệ thống
  không cảnh báo trễ.
- Auto-close khi tuyển đủ chỉ tiêu (`_hb_auto_close_if_filled`) luôn bật, hành vi cố định
  (ngừng đăng + đóng phiếu).

## Phạm vi (đã chốt với user 2026-07-23)

1. **Cấu hình quy trình (stages)** — thêm/sửa/xoá bước, kéo-thả xếp thứ tự, chọn bước
   "Đã tuyển" (`hired_stage`), sửa mô tả/tiêu chí/người hỗ trợ.
2. **SLA từng bước** — số ngày xử lý tối đa mỗi bước; ứng viên ở lâu hơn SLA → badge
   "Trễ SLA" trên kanban CV.
3. **Tuỳ chỉnh auto-close** — 4 chế độ: đủ chỉ tiêu thì (a) ngừng đăng + đóng phiếu
   (mặc định, hành vi hiện tại), (b) chỉ ngừng đăng, (c) chỉ cảnh báo, (d) tắt hẳn.

Ngoài phạm vi (cân nhắc sau): danh mục nguồn tuyển, luồng duyệt phiếu, cấu hình offer,
mail tự động, liên kết template onboarding theo vị trí.

## Thiết kế

### Model (`hocba_recruitments`)

`hr.recruitment.stage` (extend, đã có `success_criteria`, `support_person`):

- `sla_days` — Integer ≥ 0, default 0 (= không áp SLA). Số ngày tối đa ứng viên được
  ở trong bước này.
- `action_reorder(ids)` — nhận list id theo thứ tự mới, ghi `sequence` 10/20/30…
  (mirror `hb.onboarding.template.action_reorder`).
- `@api.ondelete`: chặn xoá stage còn ứng viên (kể cả archived) với thông báo tiếng
  Việt dễ hiểu (thay vì lỗi FK thô); chặn xoá stage cuối cùng.

`hr.applicant` (extend):

- `_hb_sla_state()` → `(days_in_stage, sla_days, overdue)`. Mốc vào bước =
  `date_last_stage_update` (core, fallback `create_date`). `overdue` khi
  `sla_days > 0` và `days_in_stage > sla_days` và stage chưa phải hired.
- `_hb_auto_close_if_filled()` đọc `ir.config_parameter`
  **`hocba_recruitments.auto_close_mode`**:
  - `full` (mặc định/khoá lạ): ngừng đăng + đóng phiếu — hành vi hiện tại;
  - `stop`: ngừng đăng, KHÔNG đóng phiếu;
  - `warn`: chỉ `message_post` cảnh báo đã đủ chỉ tiêu, không đổi trạng thái;
  - `off`: không làm gì.

### Data & migration

- `data/hr_recruitment_stages.xml`: chuyển `noupdate="0"` → `noupdate="1"` (admin sửa
  không bị ghi đè khi upgrade) + seed `sla_days` mặc định theo sheet: Lọc CV 1, Lên
  lịch PV 1, Hẹn & mời PV 1, Kết quả PV 1, Gửi Offer 1, Onboarding 2; các bước còn
  lại 0.
- Migration `19.0.2.2.0/post-migrate.py` (DB hiện có, vì noupdate=1 không tự ghi):
  set `noupdate=True` trên `ir.model.data` của 10 stage xmlid; seed `sla_days` như
  trên cho stage đang có `sla_days` NULL/0.

### API (controller `hocba_recruitments`, quyền `_is_admin()` — chỉ `base.group_system`)

| Route | Method | Mô tả |
|---|---|---|
| `/hocba-hrm/api/recruitment/config` | GET | `{isHr, autoCloseMode, autoCloseLabels, stages:[{id, name, sequence, hiredStage, slaDays, supportPerson, requirements, successCriteria, applicantCount}]}` |
| `/hocba-hrm/api/recruitment/config/stages` | POST | tạo stage (name bắt buộc; sequence = cuối) |
| `/hocba-hrm/api/recruitment/config/stage/<id>` | POST | sửa stage (whitelist field trên) |
| `/hocba-hrm/api/recruitment/config/stage/<id>/delete` | POST | xoá (guard ondelete → 400 kèm message) |
| `/hocba-hrm/api/recruitment/config/stages/reorder` | POST | `{ids}` → `action_reorder` |
| `/hocba-hrm/api/recruitment/config/settings` | POST | `{autoCloseMode}` (validate ∈ 4 mode) |

Wire format camelCase, lỗi `{error, message}` theo `docs/QUY_UOC_FRONTEND.md`.

`_cv_row` bổ sung: `daysInStage`, `slaDays`, `slaOverdue` (từ `_hb_sla_state()`).
`_meta().stages` bổ sung `hiredStage`, `slaDays`.

### SPA

- Mục sidebar riêng **"Cấu hình tuyển dụng"** (`recruitment-config`, `need:'admin'`
  trong Shell — chỉ Admin thấy; App gate `me.isAdmin`).
- `RecruitmentConfig.jsx` (mới, theo pattern `OnboardingConfig.jsx`, trang độc lập):
  - Card **Tự động đóng tuyển**: 4 radio mode, lưu ngay.
  - Danh sách stage dạng thẻ kéo-thả (+ nút ▲▼), rail `#thứ tự`; click mở editor
    modal: tên, người hỗ trợ, SLA (ngày), checkbox "Bước nhận việc (hired)", yêu cầu,
    tiêu chí thành công; nút xoá (ConfirmModal, hiện applicantCount).
  - Cảnh báo mềm khi không có stage nào `hiredStage` (auto-close & thống kê "đã tuyển"
    dựa vào nó).
- `CvList.jsx` kanban: badge đỏ "Trễ SLA +Nngày" khi `slaOverdue` (N = daysInStage −
  slaDays).

### Test (`hocba_recruitments/tests`)

- `test_stage_config.py`: SLA state (đúng hạn / quá hạn / stage hired không tính /
  sla_days=0 không tính), `action_reorder` ghi sequence đúng thứ tự, ondelete guard
  (còn ứng viên → UserError; stage trống xoá được).
- `test_auto_close.py` mở rộng: 3 mode mới (`stop` không đóng phiếu, `warn` giữ
  nguyên trạng thái + có message, `off` không làm gì); param rác → coi như `full`.

## Quyết định

- Dùng thẳng `hr.recruitment.stage` (không tạo model mới) — kanban/stat "đã tuyển"
  đang chạy trên nó, đổi model là đập nền.
- Auto-close mode lưu `ir.config_parameter` (1 giá trị toàn hệ thống) — đủ dùng,
  không cần `res.config.settings` (SPA không dùng form Settings của Odoo).
- SLA tính theo **ngày lịch** (đơn giản, dễ giải thích khi demo); ngày làm việc để sau.
- Sửa stage ảnh hưởng ứng viên đang chạy (không snapshot như onboarding) — chấp nhận:
  stage là cột kanban sống, không phải lộ trình từng người.

## Bổ sung 2026-07-26 — Ẩn bước (thay vì chỉ xoá)

- `hr.recruitment.stage` thêm `active` (Boolean, default True). Ẩn = archive:
  biến mất khỏi kanban CV + form chọn bước (mọi `search([])` tự lọc), dữ liệu
  ứng viên cũ giữ nguyên, hiện lại được bất cứ lúc nào.
- Guard `_check_can_hide()` (chạy trong `write` khi set `active=False`, kiểm tra
  "còn ≥1 bước hiển thị" TRƯỚC rồi mới đếm ứng viên — thứ tự này để test
  tất-định trên DB có sẵn dữ liệu):
  - Phải còn ít nhất 1 bước đang hiển thị.
  - Không ẩn bước còn ứng viên **đang hoạt động** (ứng viên lưu trữ KHÔNG chặn —
    khác guard xoá vốn chặn cả archived; đây chính là lý do có nút Ẩn).
- API: `/config` trả cả bước ẩn (`active_test=False`) + field `active`,
  `activeApplicantCount`; update endpoint nhận `active` (whitelist). Version
  19.0.2.3.0 (chỉ thêm cột, không cần migration).
- UI `RecruitmentConfig.jsx`: nút "Ẩn bước"/"Hiện lại" trong editor (cạnh Xoá),
  khu "Bước đã ẩn" mờ dưới danh sách với nút Hiện lại; danh sách chính/kéo-thả
  chỉ gồm bước hiển thị.
- Test: ẩn bị chặn khi còn UV hoạt động; UV lưu trữ không chặn; ẩn hết mọi bước
  bị chặn; hiện lại giữ nguyên cấu hình (test_09–11).
