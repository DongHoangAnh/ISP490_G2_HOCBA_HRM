# FS SPEC FORMAT & CONTEXT GUIDE — HRM Odoo (Hoc Ba Education)

> File này là "tài liệu hướng dẫn format + ngữ cảnh" để Claude (trong VSCode / Claude Code) đọc
> codebase module **Payroll** rồi sinh ra các file spec **FS-PAY-XXX** giống hệt phong cách
> của các file spec module **Employee** (FS-EMP-001 → 009) đã có sẵn trong dự án.
>
> Cách dùng nhanh: bỏ file này vào root của repo, mở Claude trong VSCode, dán **PROMPT** ở cuối file.

---

## 0. NGỮ CẢNH DỰ ÁN (Project Context — bắt buộc Claude phải nắm)

| Thuộc tính | Giá trị |
| --- | --- |
| Project | HRM Odoo - Hoc Ba Education |
| System | Odoo 19 ERP (Community / Enterprise) |
| Tổ chức | FPT University — Group G2 - ISP490 |
| Reviewer | Pham Duc Thang |
| Creator / Created by / Modified by | Group G2 - ISP490 |
| Module Employee (đã làm) | technical name: `hocba_employees`, Module code: **EMP** |
| Module Payroll (cần làm spec) | technical name: `hocba_payroll` (xác nhận lại trong `__manifest__.py`), Module code: **PAY** |
| Ngôn ngữ viết spec | **Tiếng Anh** (giống FS-EMP), context name giữ nguyên tiếng Việt khi cần (CCCD, Giao vu, Hoc Ba…) |
| Multilingual của hệ thống | Vietnamese / English |

**Triết lý quan trọng nhất:** Spec phải mô tả **đúng code đã implement thật**, KHÔNG bịa.
Nếu phát hiện code khác với giả định/spec gốc, viết một dòng **technical note in nghiêng** để nêu rõ
sự khác biệt (xem mục 4). Đây là đặc trưng nổi bật của bộ FS-EMP (vd: "identification_id moved to
hr.version since Odoo 19", "không dùng base.automation mà code thẳng trong write()").

---

## 1. QUY ƯỚC ĐẶT TÊN & ĐÁNH SỐ (Naming & Numbering)

### Tên file
```
FS-PAY-00X_Ten_Function_Cach_Nhau_Bang_Underscore_v1_0.md
```
- Prefix: `FS-PAY-` + số thứ tự 3 chữ số (`001`, `002`, …).
- Tên function viết Title_Case, nối bằng `_`, bỏ dấu tiếng Việt.
- Hậu tố version: `_v1_0`.
- Ví dụ: `FS-PAY-001_Payslip_Generation_v1_0.md`.

### Function ID
- `FS-PAY-001`, `FS-PAY-002`, … (mỗi function 1 file).

### Business Rule ID
- Dạng `BR-PAY-NN0`. **Mỗi function sở hữu 1 block 10 số**, tăng 10 mỗi function:
  - FS-PAY-001 → `BR-PAY-001`, `BR-PAY-002`, …
  - FS-PAY-002 → `BR-PAY-010`, `BR-PAY-011`, …
  - FS-PAY-003 → `BR-PAY-020`, …
  - (giữ các block không trùng nhau; nếu function dùng hết 1 block thì sang block kế tiếp).

### Automation ID (nếu module payroll có CRON / write-override automation)
- Theo phong cách EMP: đặt mã ngắn như `AUT-001`, hoặc tên `ir.cron` thật trong code
  (vd `cron_xxx`). Luôn ghi mã CRON/hàm thật lấy từ code.

### Cross-reference
- Khi nhắc function khác, ghi trong ngoặc: `(FS-PAY-002)` hoặc liên-module `(FS-EMP-003)`.
  Module payroll **chắc chắn** tham chiếu sang employee (vd `x_active_dependent_count` ở FS-EMP-003,
  `from_wage/to_wage` ở FS-EMP-007). Nêu rõ ranh giới module.

---

## 2. CẤU TRÚC FILE SPEC (bắt buộc đủ 6 section + header)

Thứ tự cố định, KHÔNG đổi:

```
[HEADER BLOCK]            ← bảng metadata + bảng Approver/Reviewer/Creator
CHANGE HISTORY
1. FUNCTION OVERVIEW
2. FUNCTION FLOW
3. SCREEN LAYOUT
4. FIELD SPECIFICATION
5. BUSINESS RULES
6. STANDARD vs CUSTOM MATRIX
```

Mỗi section 1→6 **mở đầu bằng một bảng mini lặp lại** 4 dòng:
`Function ID | Function Name | Created by | Modified by`
(đúng như bản EMP — giữ nguyên để đồng bộ).

### 2.1 HEADER BLOCK
Hai bảng:

**Bảng 1 — metadata:**
| Trường | Nội dung |
| --- | --- |
| Module | PAY |
| Module Name | Payroll |
| Function ID | FS-PAY-00X |
| Function Name | <tên function> |
| Created Date | <dd/mm/yyyy> |
| Last Update Date | <dd/mm/yyyy> |
| Project | HRM Odoo - Hoc Ba Education |
| System | Odoo 19 ERP (Community / Enterprise) |
| Reference | `<model chính> (inherited / new model)` - module `hocba_payroll` |

**Bảng 2 — ký duyệt:**
| Approver | Reviewer | Creator |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

### 2.2 CHANGE HISTORY
| No | Version | Description | Sheet | Modified Date | Modified By |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial creation | All | <date> | Group G2 |

### 2.3 SECTION 1 — FUNCTION OVERVIEW
Gồm 3 phần:
1. Bảng mini 4 dòng (ID/Name/Created/Modified).
2. Bảng phân loại 1 dòng:
   `Processing Time | Processing Type | Function Type | Multilingual`
   - Processing Time: vd `On-demand`, `Real-time`, `Daily CRON HH:MM (Asia/Ho_Chi_Minh)`, `Event-driven (on write)`.
   - Processing Type: vd `Interactive (Form/List view)`, `System-triggered (no direct UI)`, `Wizard`.
   - Function Type: vd `Transaction`, `Master Data`, `Automation / Background Process`, `Report`, `Workflow / Process Control`.
   - Multilingual: `Yes (Vietnamese / English)`.
3. Khối **Business Requirement & Function Overview**, gồm các tiêu đề con (in đậm):
   - **Overview:** 1–3 câu mô tả function thay thế cái gì (thường thay Lark sheet / Excel).
   - **Business Context - Hoc Ba Education:** bối cảnh nghiệp vụ thật.
   - *(tuỳ chọn)* **Technical note** in nghiêng: điểm code khác giả định.
   - **Functional Scope:** gạch đầu dòng các năng lực chính + tên field/model thật.
   - **Users:** liệt kê role + nhóm bảo mật Odoo (`hr.group_hr_user`, `hr.group_hr_manager`,
     nhóm custom nếu payroll có), kèm quyền (full edit / read / self-service…).

### 2.4 SECTION 2 — FUNCTION FLOW
- **Main Flow** (có thể tách nhiều Main Flow con theo kịch bản, vd "Main Flow - Compute",
  "Main Flow - Confirm", "Main Flow - CRON …"). Mỗi bước 1 câu, mô tả hành động user/hệ thống,
  nêu tên hàm thật (`action_xxx()`, `_compute_xxx()`, `write()` override…).
- **Error / Exception Flow**: viết dạng **bullet** HOẶC **bảng `Condition | Result`**.
  Result nêu rõ loại exception thật: `ValidationError: …`, `UserError: …`, `AccessError: …`.

### 2.5 SECTION 3 — SCREEN LAYOUT
- Liệt kê từng **Screen N: <Tên view> (`xml_id_view`)**.
- Mỗi screen ghi: `Access:` (đường dẫn menu), các cột/nhóm field, decoration
  (`decoration-info/-warning/-danger/-muted/-success`), smart button, statusbar, filter/group-by.
- Nếu function chạy nền (CRON/automation) → ghi
  `Screen 1: No dedicated UI - runs in background …` rồi mô tả outcome (Activities, chatter,
  Scheduled Actions ở Settings > Technical > Automation).

### 2.6 SECTION 4 — FIELD SPECIFICATION
- Tổ chức **theo từng Model**, in đậm tên model + trạng thái:
  `**Model: <name> (new model)**` hoặc `**Model: <name> (inherited)**`.
- Bảng 4 cột: `Field | Type | Constraint | Description`.
  - Type: `Char`, `Text`, `Integer`, `Float (digits a,b)`, `Date`, `Datetime`, `Boolean`,
    `Selection`, `Many2one <model>`, `One2many <model>`, `Many2many <model>`, `Monetary`,
    `Html`, `Python method` (cho hàm), `ir.cron record`, `ir.config_parameter record`.
  - Constraint: `required`, `readonly`, `default=…`, `tracking`, `index`, `unique`,
    `compute (store / readonly=False)`, `groups='hr.group_hr_manager'`, `ondelete='cascade'/'restrict'`,
    `@api.constrains _check_xxx`, `domain …`, range `[+a,+b] days`…
  - Với Selection: liệt kê các giá trị (vd `draft/done/cancelled`).
  - Cho function automation: có thể liệt kê **method thay vì field** (Type = `Python method`,
    mô tả vai trò), giống FS-EMP-005.

### 2.7 SECTION 5 — BUSINESS RULES
Bảng 3 cột: `Rule ID | Rule | Details`.
- Rule ID theo block `BR-PAY-NN0` (mục 1).
- Rule: tên ngắn của luật.
- Details: cơ chế thật (tên hàm/constraint/nhóm bảo mật/công thức).

### 2.8 SECTION 6 — STANDARD vs CUSTOM MATRIX
Bảng 3 cột: `Component | Type | Notes`.
- Type chỉ dùng các nhãn: `Custom (new model)`, `Custom extension`, `Custom (inherited)`,
  `Custom`, `Standard Odoo`.
- Notes: vì sao custom / chỗ standard được tái dùng (vd `mail.activity` = Standard Odoo).

---

## 3. VĂN PHONG (Tone & Style — match đúng bộ FS-EMP)

- Tiếng Anh, thì hiện tại, mô tả hành vi **đã implement**. Câu ngắn, kỹ thuật, không marketing.
- Luôn gọi tên **thật** của field/model/method/xml_id/group/cron lấy từ code (vd
  `x_employment_status`, `hr.employee.asset`, `_compute_eval_dues`, `view_employee_form_hocba`,
  `hr.group_hr_manager`, `cron_cert_expiry_alert`).
- Selection nêu đủ option. Money/ngày nêu đơn vị (VND, days).
- Nêu rõ ranh giới phạm vi (scope note) khi một phần thuộc module khác
  (vd "tính khấu trừ thuộc hocba_payroll, không thuộc hocba_employees").
- Khi code lệch giả định → 1 dòng **Technical note** in nghiêng, mở đầu kiểu
  *"Technical note (verified against the code): …"*.
- Cross-ref các FS khác trong ngoặc đơn.

---

## 4. CHECKLIST TRƯỚC KHI XUẤT MỖI FILE

- [ ] Có đủ Header (2 bảng) + Change History + 6 section, đúng thứ tự.
- [ ] Mỗi section 1–6 có bảng mini 4 dòng (ID/Name/Created/Modified).
- [ ] Module = PAY; Reference trỏ đúng model + `hocba_payroll`.
- [ ] Mọi field/model/method/view/group/cron đều **tồn tại thật trong code** (đã đối chiếu).
- [ ] BR-PAY ID không trùng block giữa các function.
- [ ] Error flow nêu đúng loại exception (Validation/User/Access Error) như trong code.
- [ ] Standard vs Custom Matrix chỉ dùng nhãn cho phép.
- [ ] Nếu có điểm code khác giả định → đã thêm Technical note in nghiêng.
- [ ] File đặt tên `FS-PAY-00X_..._v1_0.md`.

---

## 5. TEMPLATE RỖNG (copy để điền)

```markdown
**FUNCTIONAL SPECIFICATION**

**HRM ODOO - HOC BA EDUCATION**

| **Module** | PAY |
| --- | --- |
| **Module Name** | Payroll |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created Date** | <dd/mm/yyyy> |
| **Last Update Date** | <dd/mm/yyyy> |
| **Project** | HRM Odoo - Hoc Ba Education |
| **System** | Odoo 19 ERP (Community / Enterprise) |
| **Reference** | <model> (new model / inherited) - module hocba_payroll |

| **Approver** | **Reviewer** | **Creator** |
| --- | --- | --- |
| Name | Pham Duc Thang | Group G2 - ISP490 |
| Organization | FPT University | FPT University |

## CHANGE HISTORY

| **No** | **Version** | **Description** | **Sheet** | **Modified Date** | **Modified By** |
| --- | --- | --- | --- | --- | --- |
| 1 | 1.0 | Initial creation | All | <date> | Group G2 |

## 1. FUNCTION OVERVIEW

| **Function Overview** | **Function Overview** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

| **Processing Time** | **Processing Type** | **Function Type** | **Multilingual** |
| --- | --- | --- | --- |
| <…> | <…> | <…> | Yes (Vietnamese / English) |

**Business Requirement & Function Overview**

**Overview:**
<…>

**Business Context - Hoc Ba Education:**
<…>

*Technical note (verified against the code): <chỉ thêm khi code lệch giả định>*

**Functional Scope:**
<bullet …>

**Users:** <role + group + quyền>

## 2. FUNCTION FLOW

| **Function Flow** | **Function Flow** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

**Main Flow**
<bước 1…>

**Error / Exception Flow**
<bullet hoặc bảng Condition | Result>

## 3. SCREEN LAYOUT

| **Screen Layout** | **Screen Layout** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

**Screen 1: <Tên view> (<xml_id>)**
Access: <menu path>
<cột / nhóm field / decoration / smart button / statusbar / filter>

## 4. FIELD SPECIFICATION

| **Field Specification** | **Field Specification** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

**Model: <model> (new model / inherited)**

| **Field** | **Type** | **Constraint** | **Description** |
| --- | --- | --- | --- |
| <field> | <type> | <constraint> | <desc> |

## 5. BUSINESS RULES

| **Business Rules** | **Business Rules** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

| **Rule ID** | **Rule** | **Details** |
| --- | --- | --- |
| BR-PAY-0X0 | <rule> | <details> |

## 6. STANDARD vs CUSTOM MATRIX

| **Standard vs Custom Matrix** | **Standard vs Custom Matrix** |
| --- | --- |
| **Function ID** | FS-PAY-00X |
| **Function Name** | <Function Name> |
| **Created by** | Group G2 - ISP490 |
| **Modified by** | Group G2 - ISP490 |

| **Component** | **Type** | **Notes** |
| --- | --- | --- |
| <component> | Custom (new model) / Custom extension / Custom (inherited) / Standard Odoo | <notes> |
```

---

## 6. PROMPT DÙNG NGAY (dán vào Claude trong VSCode)

> Copy nguyên khối dưới đây. Đặt file `FS_SPEC_FORMAT_GUIDE.md` này ở root repo trước khi chạy.

```text
Bạn là technical BA/PM cho dự án "HRM Odoo - Hoc Ba Education" (Odoo 19).
NHIỆM VỤ: đọc source code module Payroll trong repo và sinh ra bộ Functional Spec FS-PAY-XXX
theo ĐÚNG format trong file FS_SPEC_FORMAT_GUIDE.md (đọc file này trước tiên, tuân thủ tuyệt đối:
header, 6 section, bảng mini mỗi section, quy ước đặt tên file, đánh số BR-PAY-NN0, văn phong tiếng Anh).

BƯỚC LÀM:
1. Đọc FS_SPEC_FORMAT_GUIDE.md để nắm format + ngữ cảnh.
2. (Tham khảo phong cách) Liếc qua 1-2 file FS-EMP-*.docx/md nếu có trong repo để match tone.
3. Đọc TOÀN BỘ module payroll (xác nhận technical name trong __manifest__.py, mặc định hocba_payroll):
   - __manifest__.py (depends, data files)
   - models/*.py  (model mới, _inherit, fields, Selection options, @api.constrains/_check_*,
     @api.depends/_compute_*, write()/create()/unlink() override, action_*, _cron_*)
   - views/*.xml  (form/list/kanban/search, xml_id view, menu, smart button, statusbar,
     decoration, group, filter, invisible/readonly domain)
   - security/*   (ir.model.access.csv, ir.rule, groups)
   - data/*.xml   (ir.cron, ir.config_parameter, sequence, dữ liệu mặc định)
   - wizards/, report/ nếu có.
4. Tự phân rã module thành các function hợp lý (mỗi màn hình/luồng/automation lớn = 1 FS),
   giống cách module Employee chia 9 function. Đề xuất danh sách FS-PAY-001..00N (kèm tên) cho tôi
   DUYỆT TRƯỚC khi viết chi tiết. Sau khi tôi OK thì sinh từng file.
5. Mỗi function xuất 1 file Markdown đặt tên FS-PAY-00X_Ten_Function_v1_0.md ở thư mục ./docs/specs/payroll/.

RÀNG BUỘC QUAN TRỌNG:
- CHỈ mô tả những gì code thật có. Không bịa field/model/method/view.
- Dùng đúng tên thật của field/model/method/xml_id/group/cron lấy từ code.
- Selection phải liệt kê đủ option; tiền tệ ghi VND; thời gian ghi đơn vị.
- Error flow ghi đúng loại exception (ValidationError/UserError/AccessError) như trong code.
- Nêu rõ ranh giới module: chỗ nào payroll đọc dữ liệu từ employee (vd x_active_dependent_count,
  from_wage/to_wage, x_official_date) thì cross-ref (FS-EMP-00X).
- Nếu code khác giả định/spec gốc, thêm 1 dòng *Technical note (verified against the code): …* in nghiêng.
- Standard vs Custom Matrix chỉ dùng nhãn: Custom (new model) / Custom extension / Custom (inherited)
  / Custom / Standard Odoo.
- Trước khi xuất mỗi file, tự rà checklist ở mục 4 của guide.

OUTPUT ĐẦU TIÊN: danh sách đề xuất các FS-PAY (ID + Function Name + 1 câu mô tả + model chính),
chờ tôi duyệt. CHƯA viết nội dung chi tiết cho tới khi tôi xác nhận.
```
