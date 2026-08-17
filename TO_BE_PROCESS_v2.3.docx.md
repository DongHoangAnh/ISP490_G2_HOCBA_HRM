

![][image1]

**Capstone Project Report**

**TO-BE PROCESS** 

**Topic: Human Resource Management System for Hoc Ba Learning Center**

| Project Name | Human Resource Management System for Hoc Ba Learning Center |
| :---- | :---- |
| **Project Code** | ISP490\_G2 \- HOCBA\_HRM |
| **Platform** | Odoo 19 (Community \+ Custom Modules) |
| **Team** | ISP490\_G2 \- FPT University |
| **Supervisor** | Pham Duc Thang (ThangPD10) |
| **Version** | 2.3 |
| **Date** | 12/08/2026 |

**Team Members**

| No | Full Name | Student ID | Module Responsibility |
| :---: | ----- | ----- | ----- |
| 1 | Dong Hoang Anh | HE182321 | Team Leader / Attendance Module |
| 2 | Vu Cong Tan | HE182322 | Employee Module / Business Analyst |
| 3 | Hoang Van Viet | HE186511 | Recruitment Module |
| 4 | Nguyen Nhat Anh | HE181913 | Time Off Module |
| 5 | Ha Phi Hung | HE186793 | Payroll Module |

**Change History:**

| Changed Date | Items Changed | Changed Content/Reason | Updated By | Type(A/C/D) | Version |
| ----- | ----- | ----- | ----- | ----- | ----- |
| 20/06/2026 | Initial Creation | First draft of To-Be process document | ISP490\_G2 Team | A | 1.0 |
| 20/07/2026 | As-built alignment | Updated module documentation: replaced PIN check-in with face+GPS, corrected model names, added As-Built status tables, and marked deferred features. | ISP490\_G2 Team | C | 2.0 |
| 06/08/2026 | As-built refresh | Updated docs for REV & SVC modules, asset lifecycle, runtime configs, and WRICEF metrics (241 routes, 814 tests). | ISP490\_G2 Team | C | 2.1 |
| 11/08/2026 | As-built refresh | Updated doc tests. | ISP490\_G2 Team | C | 2.2 |
| 12/08/2026 | As-built check | Updated doc corrected recruitment approvals, payroll/OT rules | ISP490\_G2 Team | C | 2.3 |

# **Table of Contents**

[Table of Contents	3](#heading=)

[**I: Overview	4**](#i:-overview)

[1.1  Purpose	4](#heading=)

[1.2  Scope	4](#heading=)

[1.3  Glossary	5](#heading=)

[**II: AS-IS Process	7**](#ii:-as-is-process)

[2.1  Employee Management	7](#heading=)

[2.2  Attendance	7](#heading=)

[2.3  Recruitment	8](#heading=)

[2.4  Time Off	8](#heading=)

[2.5  Payroll	8](#heading=)

[**III. TO BE Process	10**](#iii.-to-be-process)

[3.1 : Employee Module (EMP)	10](#3.1-:-employee-module-\(emp\))

[3.2: Attendance Module (ATT)	17](#3.2:-attendance-module-\(att\))

[3.3: Recruitment Module (REC)	24](#3.3:-recruitment-module-\(rec\))

[3.4: Time Off Module (TO)	33](#3.4:-time-off-module-\(to\))

[3.5: Payroll Module (PR)	38](#3.5:-payroll-module-\(pr\))

[3.6: Performance Review Module (REV)	45](#heading=)

[3.7: HR Service Request Module (SVC)	47](#heading=)

[**IV: Cross-Module Integration Flow	51**](#iv:-cross-module-integration-flow)

[**V: Development Consideration (WRICEF)	52**](#v:-development-consideration-\(wricef\))

[5.1  Form Consideration	52](#heading=)

[5.2  Report Consideration	52](#heading=)

[5.3  Enhancement Consideration	53](#heading=)

# **I: Overview** {#i:-overview}

## **1.1  Purpose**

This document describes the To-Be business processes for the Human Resource Management System (HRMS) of Hoc Ba Education \- a growing Chinese language center operating multiple branches in Vietnam. The system is built on Odoo 19 with custom modules developed by the ISP490\_G2 team.

Key objectives of the To-Be implementation:

* Data Centralization & Standardization: Replace fragmented Lark workflows with a unified Odoo platform covering all HRM functions across 7 modules.

* Compliance Control: Enforce Vietnamese labor law requirements including BHXH/BHYT/BHTN contributions, PIT calculation (7-tier progressive), annual leave accrual, overtime limits, and CCCD identity validation.

* Process Automation: Automate attendance capture, payroll computation (including teaching-hours salary), leave quota accrual/carry-over, and statutory reporting (iBHXH, eTax \- **Phase 2**).

* Self-Service Enablement: Provide a Single-Page Application (SPA) embedded in Odoo allowing employees to manage their own profile, check-in/out, request leave, and view payslips.

* Management Visibility: Provide managers and HR with real-time dashboards for attendance, recruitment pipeline, headcount, and payroll cost analysis.

* Integration Readiness: Link all 5 modules through a Work Entry layer so that attendance/leave data automatically feeds into payroll computation at month-end.

## **1.2  Scope**

The To-Be system covers the following 7 HRM modules implemented on Odoo 19:

| No | Module | Description | Functions |
| ----- | ----- | ----- | ----- |
| 1 | Employee (EMP) | Manage employee master data, legal records, dependents, onboarding/offboarding plans, skills, and organizational structure. | EMP-01 to EMP-06 |
| 2 | Attendance (ATT) | Handle office/remote check-in/out, teaching-hours capture, GPS/IP validation, collaborator shift registration, and exception handling. | ATT-01 to ATT-05 |
| 3 | Recruitment (REC) | End-to-end hiring: job requisition, multi-channel posting, candidate pipeline, screening, interviews, offer signing, and talent pool. | REC-01 to REC-09 |
| 4 | Time Off (TO) | Leave request submission, multi-level approval, quota accrual, carry-over, teaching schedule conflict detection, and analytics. | TO-01 to TO-05 |
| 5 | Payroll (PR) | Salary structure configuration, teaching-hours computation, net-to-gross wizard, payslip approval, bank payment, BHXH/eTax reporting, and year-end PIT. | PR-01 to PR-07 |
| 6 | Performance Review (REV) | Periodic appraisal of teaching and office staff on two configurable criteria sets, mixing automatically computed operational indicators with the manager’s scoring, and producing an A/B/C/D grade. | REV-01 to REV-02 |
| 7 | HR Service Requests (SVC) | One channel for HR service requests, questions and feedback, optionally anonymous, with a processing inbox, deadlines and overdue reminders. | SVC-01 to SVC-03 |

**Added beyond the To-Be design:**

• Administrator-only recruitment process configuration screen: per-stage deadline, success criteria, support person, drag-and-drop ordering, hide/show a stage and four auto-close modes.

• In-app notifications on every round of the requisition approval chain, and a cron that reminds owners of candidates past their stage deadline.

## **1.3  Glossary**

| Term | Definition | Note |
| ----- | ----- | ----- |
| HRM | Human Resource Management \- the overall system managing employee lifecycle. |  |
| ERP | Enterprise Resource Planning \- integrated business management platform (Odoo 19). |  |
| SPA | Single-Page Application \- React/Vite frontend embedded at /hocba-hrm in Odoo. |  |
| Work Entry | hr.work.entry \- Odoo model linking attendance/leave hours to payroll computation. | Bridge between ATT/TO and Payroll |
| BHXH | Bảo hiểm xã hội \- Social Insurance (8% employee / 17.5% employer). | Vietnamese statutory |
| BHYT | Bảo hiểm y tế \- Health Insurance (1.5% employee / 3% employer). | Vietnamese statutory |
| BHTN | Bảo hiểm thất nghiệp \- Unemployment Insurance (1% employee / 1% employer). | Vietnamese statutory |
| PIT | Personal Income Tax \- Vietnamese progressive tax (7 brackets, up to 35%). | Calculated on taxable income |
| CCCD | Căn cước công dân \- Vietnamese Citizen ID card (12 digits, mandatory for official staff). | BR-010 enforcement |
| Cut-off Date | 25th of each month — the designed deadline for locking attendance/leave data. Not implemented: payroll reads validated data at computation time. |  |
| OT | Overtime work \- capped at 4h/day, 40h/month per Vietnamese labor law.(legal limit; not enforced by the system)  |  |
| CTV | Collaborator (Cộng tác viên) \- shift-based part-time workers with separate shift registration. |  |
| Kanban | Odoo view type \- card-based pipeline view used in Recruitment and Time Off. |  |
| WRICEF | Workflow, Report, Interface, Conversion, Enhancement, Form \- SAP/Odoo customization classification. |  |
| iBHXH | Government portal for electronic BHXH declaration filing. |  |
| eTax | Government portal for electronic PIT/tax filing. |  |
| Review period | Quarter, half-year or full year over which an employee is appraised (module REV). |  |
| Anonymous request | Service request whose sender identity is stored in a separate table without access rules, so it cannot be resolved from the request itself (module SVC). |  |
| Processing deadline | Number of calendar days a recruitment stage or a service request may stay open before the system flags it as overdue. |  |

# **II: AS-IS Process**  {#ii:-as-is-process}

## **2.1  Employee Management**

**Current Pain Points:**

* Employee profiles maintained in separate Excel files per department with no central database.

* Delayed provisioning: new hires wait 3-5 days before system access is granted.

* Training and certification records stored in scattered Google Drive folders with no version control.

* Offboarding has no structured checklist \- asset returns and knowledge handover are informal.

* No dependency tracking for PIT exemptions \- dependent registrations done manually on paper.

* Organizational chart updated manually in PowerPoint after each headcount change.

| Business Impact | Risk of data inconsistency, compliance gaps in legal record-keeping, and slow HR response time during onboarding/offboarding events. |
| :---- | :---- |

## **2.2  Attendance**

**Current Pain Points:**

* Attendance tracked via physical fingerprint scanner with data exported to Excel for manual reconciliation.

* Remote/WFH attendance reported via Zalo messages or Google Forms with no geolocation verification.

* Teaching hours for instructors manually entered into separate Excel from class schedules.

* Collaborator (CTV) shifts verbally agreed \- no formal registration or system tracking.

* Missing punch (late check-in or forgotten check-out) requires a 3-5 day HR correction cycle.

* Month-end attendance reconciliation requires 3-5 business days of manual HR effort.

| Business Impact | High fraud risk, data disputes between employees and HR, payroll delays due to late attendance data submission. |
| :---- | :---- |

## **2.3  Recruitment**

**Current Pain Points:**

* Job postings manually published on Facebook, LinkedIn, and education job boards with no unified tracking.

* CVs collected via email, stored in shared Google Drive folders with inconsistent naming conventions.

* Candidate pipeline tracked in an Excel spreadsheet \- stage updates done manually by recruiters.

* No structured pre-screening: initial filtering done informally via email reply or phone call.

* Interview scheduling done via email/Zalo \- no calendar integration or panel coordination tool.

* Offer letter created in Word and sent via email \- no digital signing or audit trail.

* Rejected candidates not tracked in a talent pool for future reuse.

| Business Impact | Slow hiring cycle (average 4-6 weeks), high chance of losing qualified candidates, no data for channel ROI analysis. |
| :---- | :---- |

## **2.4  Time Off**

**Current Pain Points:**

* Leave requests submitted via Zalo message to direct manager with no formal system.

* No real-time leave quota visibility \- employees unaware of remaining balance.

* Annual leave accrual calculated manually in Excel at year-end with risk of errors.

* Teaching schedule not checked against leave requests \- risk of class disruption.

* Carry-over rules applied inconsistently \- no automated expiry enforcement.

* No audit trail for approval/rejection decisions \- disputes resolved informally.

| Business Impact | Unplanned class cancellations, inconsistent leave entitlement enforcement, employee dissatisfaction due to lack of transparency. |
| :---- | :---- |

## **2.5  Payroll**

**Current Pain Points:**

* Payroll computed entirely in Excel \- formulas built and maintained by a single HR staff member.

* Teaching-hours salary for instructors manually summed from class schedule spreadsheets.

* BHXH/BHYT/BHTN contributions manually calculated and re-keyed into MISA accounting software.

* PIT computation done manually \- brackets applied incorrectly for part-year employees.

* Bank payment files generated by re-typing account numbers from employee records into bank portal.

* No formal payslip approval workflow \- director signs printed payroll sheet.

* Year-end PIT finalization (quyết toán) is a 2-3 week manual exercise.

| Business Impact | High error rate in statutory deductions, payroll preparation takes 5-7 business days per cycle, compliance risk for BHXH and tax authorities. |
| :---- | :---- |

# **III. TO BE Process** {#iii.-to-be-process}

## **3.1 : Employee Module (EMP)** {#3.1-:-employee-module-(emp)}

![][image2]  
*Employee lifecycle To-be process* 

| Task | Lane (Actor) | Activity on the diagram | Description / Outcome |
| ----- | ----- | ----- | ----- |
| — | Nhân viên / Giảng viên | "Ứng viên trúng tuyển (đã ký Offer)" | Start event: the applicant has signed the offer in the Recruitment module. |
| A. Hiring and probation |   |   |   |
| 1 | Phòng HR | "Bấm Onboard trên hồ sơ ứng viên" | A recruiter presses Onboard on the applicant. The applicant is advanced to the Onboarding stage and linked to the profile that is about to be created. |
| 2 | Hệ thống | "Tạo hồ sơ NV, sinh mã HB.xx, đặt Thử việc" | The system creates the employee record, allocates the internal employee code from the sequence, sets the status to Probation and writes the joining milestone into the promotion history. |
| 3 | Hệ thống | "Gán quy trình nhận việc theo template (snapshot bước)" | The onboarding template matching the employee's type, work form and position type is copied onto the employee. The first sequential step and every independent step are opened at once. |
| 4 | Hệ thống | "Chuông cho HR: thiếu CCCD / MST / BHXH (BR-010)" | A profile created from an applicant never carries the legal fields, so the incomplete-profile alert is raised immediately rather than at the end of probation. |
| 5 | Nhân viên / Giảng viên | "Bổ sung hồ sơ cá nhân & CCCD trên SPA" | The employee completes their own record through the self-service portal. |
| 6 | Bộ phận IT & Admin | "Bước độc lập: cấp thiết bị, bấm Hoàn thành" | The equipment step sits outside the sequence and is closed in parallel with the probation reviews. |
| 7 | Nhân viên / Giảng viên | "Giảng dạy / Làm việc (thử việc)" | The employee works through the probation period. |
| 8 | Quản lý trực tiếp / Trưởng phòng | "Ghi kết quả bước đánh giá" | The direct manager, the department head or an HR Manager records the verdict on the open evaluation step. |
| 9 | Hệ thống | "Kết quả bước?" | Exclusive gateway on the verdict recorded in step 8\. |
| 9A | Hệ thống | "Đạt" → step 10 | The step is passed. |
| 9B | Hệ thống | "Gia hạn — hẹn tái đánh giá" → step 8 | The extension step is opened, or a re-review is scheduled in place; the employee and the reviewers are notified. |
| 9C | Hệ thống | "Không đạt" → step 11 | The probation is failed. |
| 10 | Hệ thống | "Bước chốt lên chính thức?" | Second gateway: only a step flagged as the closing gate confirms the employee. |
| 10A | Hệ thống | "Đạt, là bước chốt" → step 12 | The closing gate has been passed. |
| 10B | Hệ thống | "Chưa chốt — mở bước kế tiếp" → step 8 | The next step in the sequence is opened; a pending extension step is skipped. |
| 11 | Hệ thống | "Bỏ bước còn lại, tự tạo đơn nghỉ việc" | Remaining steps are skipped and an offboarding request is created automatically with the origin "probation failure", already at the awaiting-completion state. The flow continues at step 23\. |
| 12 | Hệ thống | "Chuyển Chính thức, ghi lịch sử thăng tiến" | The legal prerequisites are re-checked (BR-010), the status becomes Official, the confirmation date is stamped, the promotion history is written and HR is assigned the task of issuing the permanent contract. |
| B. Employment and lifecycle changes |   |   |   |
| 13 | Nhân viên / Giảng viên | "Làm việc chính thức" | Steady working state; the flow returns here after every recorded change. |
| 14 | Phòng HR | "Sự kiện vòng đời?" | Exclusive gateway on the event arising during employment. |
| 14A | Phòng HR | "Thăng tiến / điều chỉnh lương" → step 15 | A promotion or salary revision has been decided. |
| 14B | Nhân viên / Giảng viên | "Nghỉ việc" → step 17 | The employee resigns. |
| 15 | Phòng HR | "Nhập thăng tiến từ phiếu đánh giá" | HR captures the movement from the evaluation form. A salary change is rejected unless it carries a reason and either an evidence link or the linked evaluation. |
| 16 | Hệ thống | "Ghi lịch sử thăng tiến & bảng vinh danh" | The immutable history entry is written; a movement granting a new job title also publishes an honour-board entry. The flow returns to step 13\. |
| C. Offboarding |   |   |   |
| 17 | Nhân viên / Giảng viên | "Nộp đơn nghỉ việc trên SPA" | The employee submits the resignation request with the expected leaving date and the reason. |
| 18 | Quản lý trực tiếp / Trưởng phòng | "Quản lý duyệt đơn nghỉ" | The direct manager or the department head reviews the request. |
| 19 | Quản lý trực tiếp / Trưởng phòng | "Quản lý duyệt?" | Exclusive gateway on the manager's decision. |
| 19A | Hệ thống | "Duyệt" → step 20 | The request is approved at the first level. |
| 19B | Hệ thống | "Từ chối — trả trạng thái cũ" → step 13 | The previous employment status is restored and the employee is notified. |
| 20 | Hệ thống | "Đặt Đang offboarding, báo HR" | The employee is switched to Exiting and every HR Manager is notified. |
| 21 | Phòng HR | "HR duyệt đơn nghỉ" | HR gives the second approval. |
| 22 | Nhân viên / Giảng viên | "Bàn giao lớp / tài liệu" | Classes, teaching materials and student progress are handed over. |
| 23 | Phòng HR | "Tick checklist & Hoàn tất đơn nghỉ" | HR ticks the clearance items (work handover, payroll settlement, document filing) against the assets still held, which are displayed on the request itself, and completes the request. |
| 24 | Hệ thống | "Ẩn hồ sơ & khoá tài khoản đăng nhập" | The status becomes Resigned, the profile is archived and the linked login account is deactivated in the same transaction. |
| 25 | Hệ thống | "Hồ sơ đóng (lưu trữ)" | End event: the employee file is closed. |
| D. Scheduled automation (independent flow) |   |   |   |
| 26 | Hệ thống | "Hằng ngày 07:00" | Timer start event (Asia/Ho\_Chi\_Minh). |
| 27 | Hệ thống | "Quét & bắn chuông: bước đến hạn, chứng chỉ, hợp đồng" | Three schedulers scan open probation steps due within two days, verified certificates expiring within a configurable threshold (default 60 days) or already expired, and contracts ending within 30 days. A deduplication key stops the daily scan republishing the same alert. |
| 28 | Hệ thống | "Đã nhắc HR & nhân viên" | End event. |

| EMP-01  Employee Master Profile & VN Legal Data |
| :---- |

| Function Name | Employee Master Profile & Vietnamese Legal Data Management |
| :---- | :---- |
| **Purpose** | Create and maintain the complete employee profile including personal data, contract info, and Vietnamese legal identifiers required for BHXH/PIT compliance. |
| **Actors** | HR Manager, Employee (self-service) |
| **Trigger** | New hire onboarded or existing employee data update requested. |
| **Output** | Complete hr.employee record with contract, CCCD, tax code, BHXH number. |
| **Business Rules** | CCCD must be exactly 12 digits (BR-010). Each employee must have a unique CCCD. Official employees require a valid labor contract before activation. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR creates a new employee record in Odoo: enters full name, date of birth, gender, personal email, phone number. |
| HR Manager | 2 | HR fills the Vietnamese Legal Data tab: CCCD number (12 digits), issue date, issue place; tax registration code; BHXH participant code. |
| HR Manager | 3 | HR attaches scanned copies of CCCD, labor contract, and degree certificates as document attachments. |
| HR Manager | 4 | HR creates the hb.contract record: contract type (official/probation/CTV), start date, wage, job position, department. |
| System | 5 | System validates CCCD format (BR-010): rejects if not exactly 12 numeric digits or if duplicate found. |
| System | 6 | System auto-links employees to appropriate access groups based on job position (Teacher, Admin, Manager). |
| Employee | 7 | Employee logs into SPA and completes self-service fields: bank account, emergency contact, marital status, dependents. |
| HR Manager | 8 | HR reviews and approves the completed profile; employee status set to 'Active'. |

**Function Description \- Key Fields:**

| No | Field | Description | Activity | Required(Y/N) | Multiple/Single Value | DefaultValue |
| :---: | ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | Full Name (Vietnamese) | Employee's legal name as on CCCD. | Text Input | Y | Single Value | \- |
| 2 | CCCD Number | 12-digit citizen ID card number. Validated on save. | Text Input | Y | Single Value | \- |
| 3 | Date of Birth | Used for age calculation and PIT dependent validation. | DatePicker | Y | Single Value | \- |
| 4 | Tax Code | Vietnamese personal tax registration code. | Text Input | Y | Single Value | \- |
| 5 | BHXH Code | Social insurance participant code from BHXH authority. | Text Input | Y | Single Value | \- |
| 6 | Contract Type | Official / Probation / Collaborator (CTV). | Dropdown Select | Y | Single Value | Official |
| 7 | Job Position | hr.job record determining salary structure and access group. | Search Select | Y | Single Value | \- |
| 8 | Department | hr.department for reporting hierarchy and manager assignment. | Search Select | Y | Single Value | \- |
| 9 | Bank Account | For payroll transfer. IBAN-format Vietnamese account number. | Text Input | Y | Single Value | \- |
| 10 | Profile Photo | Employee portrait photo. | File Upload (JPG/PNG) | N | Single Value | \- |
| 11 | Active Status | System toggles Active when contract is confirmed. | System Display | Y | Single Value | Active |

| EMP-02  Dependents & PIT Deduction Registration |
| :---- |

| Function Name | Dependents & Personal Income Tax Deduction Registration |
| :---- | :---- |
| **Purpose** | Register employee dependents to claim family circumstance deductions (giảm trừ gia cảnh) for PIT calculation per Vietnamese tax law. |
| **Actors** | Employee (self-service), HR Manager |
| **Trigger** | Employee has qualifying dependents (child under 18, disabled child, elderly parent with no income). |
| **Output** | hr.employee.dependent records linked to employee; PIT deduction amount updated in payroll computation. |
| **Business Rules** | Max deduction 6.2M VND/dependent/month (rate applied from tax period 2026\)  |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Employee accesses Dependents tab in SPA profile and clicks Add Dependent. |
| Employee | 2 | Employee fills in: dependent name, relationship (Child/Parent/Spouse), date of birth, CCCD/MST of dependent. |
| Employee | 3 | Employee uploads supporting documents: birth certificate for child, disability certificate if applicable. |
| HR Manager | 4 | HR reviews the dependent registration and verifies documents. |
| HR Manager | 5 | HR approves registration; record status set to Confirmed. |
| System | 6 | The system adds 6,200,000 VND deduction per approved dependent  to the employee's PIT calculation in the next payroll run. |
| System | 7 | System flags if the dependent's age exceeds 18 (for non-disabled dependents) for annual review. |

| No | Field | Description | Activity | Required(Y/N) | Multiple/Single Value | DefaultValue |
| :---: | ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | Dependent Name | Full legal name of dependent. | Text Input | Y | Single Value | \- |
| 2 | Relationship | Child / Parent / Spouse. | Dropdown | Y | Single Value | \- |
| 3 | Date of Birth | Used to calculate age eligibility. | DatePicker | Y | Single Value | \- |
| 4 | CCCD / MST | Dependent's ID card or tax code. | Text Input | Y | Single Value | \- |
| 5 | Supporting Document | Upload birth cert, disability cert, etc. | File Upload | Y | Multiple Value | \- |
| 6 | Registration Status | Pending / Approved / Expired. | System Display | Y | Single Value | Pending |
| 7 | Monthly Deduction | 6,200,000 VND per  approved dependent. | System Display | Y | Number | 6,200,000  |

| EMP-03  Onboarding Plan Execution |
| :---- |

| Function Name | Employee Onboarding Plan Execution |
| :---- | :---- |
| **Purpose** | Structured onboarding checklist ensuring new hires complete all required steps (IT setup, orientation, training) within the first 30 days. |
| **Actors** | HR Manager, IT Admin, Direct Manager, New Employee |
| **Trigger** | Employee record status changes to Active (contract confirmed). |
| **Output** | Completed onboarding checklist with timestamps; employee cleared for full duties. |
| **Business Rules** | All critical tasks (system access, contract signing, safety briefing) must be completed within Day 1\. Full onboarding must be complete within 30 days. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | On contract confirmation, the system auto-creates an onboarding activity list for the new employee. |
| HR Manager | 2 | HR assigns the owner and the due date for each onboarding step from the template configured for the employee’s group.  |
| IT Admin | 3 | IT Admin creates system accounts: Odoo login, email, Zalo/internal chat, and face-template enrolment for attendance  |
| HR Manager | 4 | HR conducts orientation sessions: company policies, HR handbook, benefits, leave policy. |
| Direct Manager | 5 | The manager conducts role-specific training and introduces team members. |
| New Employee | 6 | Employee signs labor contract, acknowledges handbook receipt, completes bank account setup. |
| System | 7 | The system tracks completion status of each task; sends reminders to the responsible person if overdue. |
| HR Manager | 8 | HR marks onboarding as complete; sends welcome notification to the whole team. |

| No | Field | Description | Activity | Required(Y/N) | Multiple/Single Value | DefaultValue |
| :---: | ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | Task Name | Name of onboarding step. | System Display | Y | Single Value | \- |
| 2 | Responsible Person | Who must complete this task? | Search Select | Y | Single Value | \- |
| 3 | Due Date | Auto-calculated from contract start date. | System Display | Y | Date | \- |
| 4 | Status | Pending / In Progress / Done / Overdue. | Dropdown | Y | Single Value | Pending |
| 5 | Completion Date | The date task was marked done. | DatePicker | N | Single Value | \- |
| 6 | Notes | Optional remarks by a responsible person. | Text Area | N | Single Value | \- |

| EMP-04  Offboarding Plan & Knowledge Handover |
| :---- |

| Function Name | Offboarding Plan & Knowledge Handover |
| :---- | :---- |
| **Purpose** | Structured exit process covering asset return, access revocation, knowledge transfer, and final settlement calculation. |
| **Actors** | HR Manager, IT Admin, Direct Manager, Exiting Employee |
| **Trigger** | Employee resignation, contract termination, or retirement notice received. |
| **Output** | Completed offboarding checklist; final payslip with settlement; access revoked. |
| **Business Rules** | Asset return must be confirmed before final payslip is generated. Access revocation on the last working day. 30-day notice period enforced for official staff. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR records termination reasons and last working date in the system. |
| System | 2 | System auto-creates offboarding task list (asset return, access revocation, handover docs). |
| Exiting Employee | 3 | Employee prepares knowledge handover documents and hands over to designated successor. |
| IT Admin | 4 | IT revokes all system access on the last working day. |
| Direct Manager | 5 | Manager confirms handover completion and asset return. |
| HR Manager | 6 | HR calculates final settlement: unused leave payout, severance (if applicable), pro-rated salary. |
| System | 7 | The system generates final payslip and locks employee records (Archived status). |

| EMP-05  Skills & Certification Management |
| :---- |

| Function Name | Skills & Certification Management |
| :---- | :---- |
| **Purpose** | Track employee skills, language certifications (HSK for Chinese teachers), and professional qualifications to support training planning and role assignment. |
| **Actors** | Employee, HR Manager |
| **Trigger** | Employee completes a training course or obtains a new certificate; HR initiates annual skill review. |
| **Output** | Updated skill profile on employee record; training gap report for HR. |
| **Business Rules** | Chinese proficiency certificates (HSK/HSKK/TOCFL) are recorded as optional profile data; no minimum level is enforced by the system. Expired certificates must be renewed within 90 days. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Employee accesses Skills tab and adds new skills or certification. |
| Employee | 2 | Employee fills in certificate name, issuing body, issue date, expiry date, and uploads scan. |
| HR Manager | 3 | HR verifies certificate authenticity and approves. |
| System | 4 | System alerts HR 60 days before certificate expiry for renewal planning. |
| HR Manager | 5 | HR generates a skill gap report comparing current skills to role requirements. |

| EMP-06  Organizational Structure & Presence Control |
| :---- |

| Function Name | Organizational Structure & Presence Control |
| :---- | :---- |
| **Purpose** | Maintain the department hierarchy, job position catalog, and provide real-time headcount and presence dashboard for managers. |
| **Actors** | HR Manager, Department Manager |
| **Trigger** | Department restructuring, new position creation, or daily presence monitoring. |
| **Output** | Updated org chart; real-time presence status per department. |
| **Business Rules** | Each department must have exactly one manager (hr.department.manager\_id). Manager inherits view rights over all employees in their department subtree (\_managed\_department\_ids). |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR creates or edits department structure in Odoo org chart view. |
| HR Manager | 2 | HR assigns Department Manager; system grants manager access rights to department employees. |
| HR Manager | 3 | HR creates Job Position records with associated salary grade and required skills. |
| Department Manager | 4 | Manager views real-time presence dashboard: who is checked in, on leave, or absent. |
| System | 5 | System maintains \_managed\_department\_ids to include all child departments for hierarchical reporting. |

## **3.2: Attendance Module (ATT)** {#3.2:-attendance-module-(att)}

![][image3]  
*Attendance recording flow To-be process*

| Task | Lane (Actor) | Activity on the diagram | Description / Outcome |
| ----- | ----- | ----- | ----- |
| 1 | Hệ thống | **Bắt đầu**  | Start attendance. |
| 2 | Hệ thống | **Phân loại nhân sự** | The system identifies and classifies the employee according to the applicable attendance category. |
| 3 | Hệ thống | **Check lịch làm việc** | The system checks whether the employee has a scheduled work shift. |
| 4A | Hệ thống | **Không có lịch \- End Task** | If there is no scheduled work shift, the attendance process is terminated. |
| 4B | Nhân sự | **Vào chấm công** | If a work schedule exists, the employee proceeds with the attendance check-in. |
| 5 | Hệ thống | **Check trạng thái của bản ghi** | The system checks the current status of the employee's attendance record. |
| 6A | Hệ thống | **Chuẩn theo quy định** | If the record complies with the attendance regulations, the system proceeds to record the working time. |
| 6B | Nhân sự | **Giải trình** | If the record does not comply with the regulations, the employee provides an explanation for the irregular attendance. |
| 7 | Hệ thống | **Ghi nhận giờ vào làm** | The system records the employee's check-in time. |
| 8 | Hệ thống | **Hoàn thành bản ghi (checkout)** | The system completes and finalizes the attendance record for the employee. |
| 9 | Hệ thống | **Check trạng thái của bản ghi** | The system checks whether the completed attendance record complies with the required regulations. |
| 10A | Hệ thống | **Chuẩn theo quy định** | If the attendance record complies with the regulations, the system records the attendance information in the employee's personnel record. |
| 10B | Hệ thống | **Chưa đúng quy định** | If the attendance record violates the regulations, the system proceeds to notify the manager. |
| 11 | Quản lý (HR) | **Thông báo cho quản lý** | The system sends a notification to the manager about the attendance record that does not comply with the regulations. |
| 12 | Hệ thống | **Ghi nhận vào lịch sử**  | The completed attendance information is stored in the employee's attendance history.The attendance process is completed. |
| 13 | Nhân viên | **Thắc mắc** | The employee raises an inquiry or expresses doubt regarding the attendance record.  |
| 14A | Nhân viên | **Không \- End task** | If the employee decides not to take further action, the process is terminated.  |
| 14B | Nhân viên | **Gửi đơn cho quản lý** | If the employee decides to proceed, they submit an adjustment request/inquiry form to the manager.  |
| 15 | Quản lý (HR) | **Xem xét và duyệt đơn** | The manager (or HR) reviews the submitted request and makes an approval decision.  |
| 16A | Hệ thống | **Không duyệt \- End task** | If the manager rejects the request, the system terminates the process without changes.  |
| 16B | Hệ thống | **Duyệt \- Ghi nhận vào lịch sử**  | If the manager approves the request, the system updates the record and logs the changes into the attendance history.  |

| ATT-01  Office/Sales Check-in & Check-out |
| :---- |

| Function Name | Office & Sales Staff Check-in / Check-out |
| :---- | :---- |
| **Purpose** | Record daily attendance for office and sales staff via face-verified self-service check-in (selfie \+ face-descriptor match \+ GPS) on the SPA, creating hocba.attendance records for payroll. |
| **Actors** | Employee, HR Manager |
| **Trigger** | Employee arrives at/departs from the workplace. |
| **Output** | hocba.attendance record with check\_in and check\_out timestamps; work entry WORK100 generated at month-end. |
| **Business Rules** | Check-in window \= shift start ±30 minutes. Late is determined by the late-threshold hour configured in the attendance policy (default 09:30). Missing check-out auto-flagged for correction. Cut-off: 25th of month. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Employee opens SPA (/hocba-hrm) and navigates to the Attendance page. |
| Employee | 2 | The camera captures a selfie and the browser sends GPS coordinates; the system matches the face descriptor against the employee's enrolled template. |
| System | 3 | The system checks if an employee has an open attendance record (already checked in). If no open record → Check-in mode; if open → Check-out mode. |
| System | 4 | System validates check-in time against assigned shift window (shift start \- 30min to shift start \+ 30min). Displays shift name and expected hours. |
| Employee | 5 | The employee confirms and clicks the Check In / Check Out button. |
| System | 6 | System creates/updates hocba.attendance record with UTC timestamp; displays confirmation and current session duration. |
| System | 7 | At shift end \+ grace period, system flags attendance records with no check-out for HR review. |
| HR Manager | 8 | HR reviews flagged records and either approves estimated check-out time or requests correction from the employee. |

**Function Description \- Key Fields:**

| No | Field | Description | Activity | Required(Y/N) | Multiple/Single Value | DefaultValue |
| :---: | ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | Face Capture | Selfie captured at punch; matched against the enrolled face template (face\_suspect flag raised on mismatch, out\_of\_zone on GPS failure). | Camera Capture | Y | Single Value | \- |
| 2 | Check In Time | System-recorded UTC timestamp of check-in action. | System Display | Y | DateTime | \- |
| 3 | Check Out Time | System-recorded UTC timestamp of check-out action. | System Display | Y | DateTime | \- |
| 4 | Shift Name | Assigned shift for the day (e.g., HC-Morning, HC-Afternoon). | System Display | Y | Single Value | \- |
| 5 | Worked Hours | Computed field: check\_out \- check\_in. | System Display | Y | Number | 0 |
| 6 | Attendance Status | Normal / Late / Missing Check-out / Absent. | System Display | Y | Status Tag | Normal |
| 7 | Work Entry Type | WORK100 for standard hours; WORK110 for OT. | System Display | Y | Single Value | WORK100 |
| 8 | Correction Request | Employees can submit corrections if the timestamp is wrong. | Click Action | N | Single Value | \- |

| ATT-02  Automated Teaching-Hours Attendance Capture |
| :---- |

| Function Name | Automated Teaching-Hours Attendance Capture |
| :---- | :---- |
| **Purpose** | Automatically generate attendance records for teaching staff based on confirmed class schedules, eliminating manual entry for standard teaching sessions. |
| **Actors** | System (automated), Academic Admin, Teacher |
| **Trigger** | Class session is marked as Completed in the academic scheduling system. |
| **Output** | hocba.attendance record with work entry type WORK200 (teaching hours) for each completed class session. |
| **Business Rules** | Teaching attendance only created for sessions with status Completed. Cancelled/substituted sessions create LEAVE or substitute records instead. Hourly rate per teacher stored in hr.contract. |

| Actor | Step | Description |
| ----- | :---: | ----- |
| Academic Admin | 1 | Academic Admin creates/confirms class schedule in Odoo (hocba.teaching.session model): teacher, subject, date, start time, end time, room. |
| System | 2 | After class ends, the system checks if session status is Completed. |
| System | 3 | The system creates a hocba.attendance record for the teacher: check\_in \= session start, check\_out \= session end. |
| System | 4 | System tags work entry as WORK200 (teaching hours) for payroll to use hourly rate. |
| Teacher | 5 | Teachers can view their teaching attendance log in SPA; can submit corrections if class time was different. |
| Academic Admin | 6 | Admin reviews and approves corrections within 3 business days. |
| System | 7 | At month cut-off (25th), the system locks all teaching attendance records and generates work entries for payroll run. |

| No | Field | Description | Activity | Required(Y/N) | Multiple/Single Value | DefaultValue |
| :---: | ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | Session ID | Reference to hocba.teaching.session record. | System Display | Y | Single Value | \- |
| 2 | Teacher | hr.employee linked to the session. | System Display | Y | Single Value | \- |
| 3 | Session Date | Date of the teaching session. | System Display | Y | Date | \- |
| 4 | Start Time / End Time | Scheduled session times. | System Display | Y | Time | \- |
| 5 | Teaching Hours | Computed: end\_time \- start\_time. | System Display | Y | Number | \- |
| 6 | Work Entry Type | WORK200 \- Teaching Hours. | System Display | Y | Single Value | WORK200 |
| 7 | Hourly Rate | From teacher's hr.contract; used for payroll. | System Display | Y | Number | \- |
| 8 | Session Status | Completed / Cancelled / Substituted. | System Display | Y | Status Tag | \- |

| ATT-03  GPS/IP Perimeter Validation & WFH Control |
| :---- |

| Function Name | GPS/IP Perimeter Validation & Work-From-Home Control |
| :---- | :---- |
| **Purpose** | Validate that remote/WFH check-ins occur within approved GPS coordinates or IP address ranges; flag out-of-perimeter attempts for HR review. |
| **Actors** | Employee, HR Manager |
| **Trigger** | Employee attempts check-in from a non-office location. |
| **Output** | Geo-validated attendance record or flagged exception for HR review. |
| **Business Rules** | Approved office GPS coordinates stored in system config. WFH must be pre-approved via Time Off module. IP range validation as backup when GPS unavailable. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Employee submits WFH request via Time Off module (leave type \= WFH) at least 1 day in advance. |
| Manager | 2 | Manager approves WFH request; system flags employee as WFH-approved for that day. |
| Employee | 3 | Employee checks in via SPA from home; browser captures GPS coordinates. |
| System | 4 | The system compares the captured coordinates with the approved office zone and flags the punch as out\_of\_zone when it falls outside the configured radius. |
| System | 5 | For flagged check-ins: system checks if employee has WFH approval for that day. |
| System | 6 | The system records the punch together with its flag and adds it to the HR review queue.  |
| HR Manager | 7 | HR reviews exceptions and either approves or marks as Unauthorized Absence. |

| ATT-04  Collaborator Shift Registration & Reconciliation |
| :---- |

| Function Name | Collaborator (CTV) Shift Registration & Reconciliation |
| :---- | :---- |
| **Purpose** | Manage part-time collaborator shift assignments, track actual worked hours against registered shifts, and produce reconciliation report for payment. |
| **Actors** | HR Manager, Collaborator (CTV) |
| **Trigger** | Weekly shift schedule published by HR for the upcoming week. |
| **Output** | hocba.work\_shift records; reconciliation report for CTV payment. |
| **Business Rules** | CTVs use a separate shift registration model (hocba.work\_shift). Shift confirmation required by CTV within 24 hours. Unconfirmed shifts auto-assigned after deadline. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR creates a weekly shift schedule in hocba.work\_shift: assigns CTV to date/time slot. |
| System | 2 | The system sends a shift notification to CTV via Odoo internal messaging. |
| CTV | 3 | CTV confirms or requests modification of assigned shifts within 24 hours. |
| HR Manager | 4 | HR approves any shift swap or modification requests. |
| CTV | 5 | CTV checks in/out via SPA using the face-verified flow; system records against the registered shift. |
| System | 6 | At month-end (25th), the system generates CTV reconciliation: registered shifts vs. actual attendance, calculating payment hours. |
| HR Manager | 7 | HR reviews and approves CTV reconciliation report; sends to payroll for processing. |

| ATT-05  Late/Absence Exception Handling & Work Entry Generation |
| :---- |

| Function Name | Late/Absence Exception Handling & Work Entry Generation |
| :---- | :---- |
| **Purpose** | Detect attendance exceptions (late arrival, early departure, unplanned absence), trigger correction workflows, and generate validated Work Entry records for payroll consumption. |
| **Actors** | Employee, HR Manager, System |
| **Trigger** | End of each working day |
| **Output** | Resolved attendance exceptions; hr.work.entry records (WORK100/WORK110/LEAVE1xx) ready for payroll. |
| **Business Rules** | Late \> grace period (5 min) triggers deduction flag. Missing check-out after shift end \+ 1h triggers auto-flag. All exceptions must be resolved before payroll runs. Validated attendance is read by payroll at computation time; no cut-off lock is applied.  |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | Daily automated job scans all attendance records for exceptions: missing check-out, late \> 5min, unplanned absence. |
| System | 2 | For each exception, the system creates an exception record and sends notification to employees and HR. |
| Employee | 3 | Employee reviews exceptions and either accepts (no action) or submits correction requests with justification. |
| HR Manager | 4 | HR reviews correction requests and approves/rejects within 2 business days. |
| System | 5 | On the 25th, the system runs work entry generation job: converts validated attendance \+ leave records into hr.work.entry. |
| System | 6 | Work entries created: WORK100 (standard), WORK110 (overtime), WORK200 (teaching), LEAVE1xx (various leave types). |
| HR Manager | 7 | HR validates total work entry report before confirming payroll run. |

.

## **3.3: Recruitment Module (REC)** {#3.3:-recruitment-module-(rec)}

![][image4]  
*Recruitment flow To-be process*

| Task | Lane (Actor) | Activity on the diagram | Description / Outcome |
| :---- | :---- | :---- | :---- |
| 1 | Trưởng phòng (TBP) | **Tạo & Gửi phiếu yêu cầu tuyển dụng** | Description: Department Head creates a new job request. Outcome: Request status changes to Submitted and alerts the HR team. |
| 2 | BP tuyển dụng / HR | **Phê duyệt phiếu yêu cầu tuyển dụng** | Description: HR reviews the request and clicks Approve or Refuse. Outcome: If Approved, headcount is added to the job position. If Refused, HR adds a reason and notifies the Department Head. |
| 3 | BP tuyển dụng / HR | **Cấu hình JD & Đăng tin tuyển dụng** | Description: HR fills in job details (JD link, education level, weekly sessions) and turns on the publish toggle (published) Outcome: Job Description is saved and ready to be published online. |
| 4 | Hệ thống HRM (Odoo 19\) | **Thu thập & Tiếp nhận CV ứng viên** | Description: System automatically receives CVs submitted on the /jobs website or uploaded manually by HR Outcome: Creates a candidate record |
| 5 | BP tuyển dụng / HR | **Sàng lọc & Đánh giá CV** | Description: HR reviews the CV and selects a result (Pass, Fail, Talent Pool, or Contact Later).. Outcome: Saves the result. If Pass, the system automatically moves the candidate to Schedule Interview. |
| 6 | Trưởng phòng (TBP) | **Khai báo lịch rảnh phỏng vấn** | Description: Department Head or interviewer registers available time slots Outcome: Interview slots |
| 7 | BP tuyển dụng / HR | **Xếp lịch & Gửi thư mời phỏng vấn** | Description: HR books a candidate into a time slot and sends an interview invitation email. Outcome: Interview is scheduled, email is sent, and candidate moves to the Interview stage automatically. |
| 8 | BP tuyển dụng / HR | **Thực hiện phỏng vấn & Đánh giá** | Description: Interview panel conducts the interview. HR records attendance (Show / No-show) and result (Pass / Fail) Outcome: Saves interview result. Passed candidates appear in the Offer tab |
| 9 | BP tuyển dụng / HR | **Gửi thư thông báo kết quả PV** | Description: For candidates who failed the interview, HR sends a polite rejection/thank-you email. Outcome: Rejection email is sent, and candidate processing ends. |
| 10 | BP tuyển dụng / HR | **Lập & Gửi thư mời nhận việc (Offer)** | Description: HR enters offer details (salary, bonus, probation pay rate, start date) and emails the offer letter Outcome: Job offer email is sent, and the candidate automatically moves to the Offer stage. |
| 11 | BP tuyển dụng / HR | **Xác nhận kết quả tiếp nhận (Onboard)** | Description: On the start date, HR marks whether the candidate actually arrived Outcome: If No-show, the candidate is marked as "No-show", but the job request stays open to hire another person.. |
| 12 | BP tuyển dụng / HR | **Tạo hồ sơ** (Tạo hồ sơ nhân viên) | Description: For candidates who arrived, HR clicks the Onboard button Outcome: Starts the automatic employee profile creation process. |
| 13 | Hệ thống HRM (Odoo 19\) | **Khởi tạo & Bàn giao Nhân sự mới** | Description: System generates employee ID, creates (Probation), sets start date, and auto-moves to Handover when employee becomes Official. Outcome: Employee profile created, candidate stage locked, headcount reduced, and job auto-closed if target reached. |

| REC-01  Job Requisition & Budget Approval |
| :---- |

| Function Name | Job Requisition & Budget Approval |
| :---- | :---- |
| **Purpose** | Formalize the hiring request process: department manager submits headcount requisition, HR validates budget, director approves before job is posted. |
| **Actors** | Department Manager, HR Manager, Director |
| **Trigger** | Department headcount need identified (new role or replacement). |
| **Output** | Approved hr.job record with budget allocation; recruitment campaign created. |
| **Business Rules** | Requisition must specify: position, department, expected salary range, target start date. Budget approval required from the Director for positions \> 15M VND/month. SLA: 3 business days for HR review, 2 days for Director approval. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Department Manager | 1 | Manager submits Job Requisition form: position title, department, number of openings, salary range, required skills, target start date. |
| HR Manager | 2 | HR validates the requisition against headcount plan and budget. |
| HR Manager | 3 | HR forwards the requisition for approval and records the signers (department manager, HR manager, director).  |
| Director | 4 | Director reviews and approves/rejects the requisition. |
| System | 5 | On approval, the system creates hr.recruitment.stage pipeline and notifies HR to begin sourcing. |
| HR Manager | 6 | HR creates job postings in the Odoo Recruitment module with full JD and requirements. |

| REC-02  Multi-Channel Job Posting |
| :---- |

| Function Name | Multi-Channel Job Posting |
| :---- | :---- |
| **Purpose** | Publish approved job openings simultaneously to website career page, LinkedIn, Facebook, and education job boards from Odoo. |
| **Actors** | HR Manager |
| **Trigger** | Job requisition approved; posting ready. |
| **Output** | Live job posting on all configured channels; UTM tracking codes per channel for ROI analysis. |
| **Business Rules** | Each channel assigned a UTM source tag for conversion tracking. Odoo website job portal auto-published. External channels updated via Odoo integration or manual with tracking code. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR finalizes job description in Odoo: responsibilities, requirements, benefits, salary range (if disclosed). |
| HR Manager | 2 | HR selects publication channels: Website (auto), LinkedIn, Facebook, VietnamWorks, TopCV, Education job boards. |
| System | 3 | System auto-publishes to Odoo website career page at /jobs. |
| HR Manager | 4 | HR copies posting with channel-specific UTM links to LinkedIn/Facebook/job boards. |
| System | 5 | System records source UTM tag on each incoming hr.applicant record for ROI tracking. |
| System | 6 | The system sends a weekly summary to HR: applications received per channel. |

| REC-03  Candidate Pipeline Management (10 Stages) |
| :---- |

| Function Name | Candidate Pipeline Management \- 10-Stage Kanban |
| :---- | :---- |
| **Purpose** | Track each candidate through the full hiring pipeline using Odoo Kanban view with standardized 10 stages from New to Hired/Rejected. |
| **Actors** | HR Manager, Recruiter, Hiring Manager |
| **Trigger** | New application received (website form, email, or manual entry). |
| **Output** | Candidates progressed to hire or archived to the talent pool with a full activity log. |
| **Business Rules** | SLA per stage defined. Candidates must not stay \> 5 business days in any stage without an activity logged. Auto-reminder sent to recruiter at SLA breach. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | New application creates hr.applicant at stage Yêu cầu tuyển dụng. |
| HR Manager | 2 | Recruitment publishes the vacancy and collects CVs — stage Đăng tuyển & tổng hợp CV. |
| Hiring Mgr | 3 | Unit leader screens each CV and marks it Pass or Fail — stage Lọc CV. |
| Hiring Mgr | 4 | Unit leader declares available interview slots for the week — stage Lên lịch phỏng vấn. |
| HR Manager | 5 | Recruitment books the candidate into a slot and sends the invitation e-mail — stage Hẹn & mời phỏng vấn. |
| Hiring Mgr | 6 | Interview is held at the booked time — stage Phỏng vấn. |
| System | 7 | Thirty minutes after the slot ends, the candidate moves to Kết quả phỏng vấn. |
| HR Manager | 8 | Recruitment records the result and sends the offer e-mail — stage Gửi Offer. |
| HR Manager | 9 | Candidate accepts; the employee record is created and the candidate moves to Onboarding. |
| System | 10 | When probation ends and the employee becomes official, the candidate moves to Bàn giao nhân sự and the job headcount is reduced. |

| REC-04  Pre-Screening Competency Assessment |
| :---- |

| Function Name | Pre-Screening Competency Assessment |
| :---- | :---- |
| **Purpose** | Standardize initial candidate screening with scored competency questionnaire to filter applicants objectively before phone screening. |
| **Actors** | System (auto-send), Candidate, HR Manager |
| **Trigger** | The candidate reaches CV Review stage and HR marks CV as Passed. |
| **Output** | Competency score for each candidate; auto-rank within job posting. |
| **Business Rules** | Assessment auto-sent within 24 hours of CV pass. Minimum score 70% to advance to Phone Screening. Results visible only to HR (not candidates). |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR creates an assessment template per job position: 10-15 multiple choice and short answer questions. |
| System | 2 | System auto-emails assessment link to candidate when CV passes review. |
| Candidate | 3 | The candidate completes online assessment within 48 hours. |
| System | 4 | System auto-scores multiple choice; flags short answers for HR review. |
| HR Manager | 5 | HR reviews scores and moves qualified candidates (≥70%) to the Phone Screening stage. |
| System | 6 | System archives low-score candidates with auto-rejection email and feedback summary. |

| REC-05  Interview Scheduling & Panel Evaluation |
| :---- |

| Function Name | Interview Scheduling & Panel Evaluation |
| :---- | :---- |
| **Purpose** | Coordinate interview logistics, assign panel members, capture structured feedback scores, and consolidate panel decisions. |
| **Actors** | HR Manager, Interviewer Panel, Candidate |
| **Trigger** | The candidate advances to the interview stage. |
| **Output** | Structured interview score sheet; panel hiring recommendation. |
| **Business Rules** | Panel must include: HR \+ Hiring Manager (minimum). For teacher roles: add Academic Lead. Each interviewer submits an individual score before panel debrief. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR creates interview event in Odoo calendar: date, time, format (in-person/online), invites panel. |
| System | 2 | System sends calendar invites to panel and candidate via email. |
| Candidate | 3 | Candidate confirms attendance or requests rescheduling. |
| Panel | 4 | Panel conducts interview; each interviewer fills structured scorecard in Odoo (Technical/Behavioral/Culture Fit). |
| HR Manager | 5 | HR facilitates debrief meeting; panel votes: Hire / Hold / Reject. |
| System | 6 | System consolidates scores and recommendation; moves candidate to appropriate next stage. |

| REC-06  Compensation Proposal & Digital Offer Signing |
| :---- |

| Function Name | Compensation Proposal & Digital Offer Letter |
| :---- | :---- |
| **Purpose** | Generate structured offer letter from approved template with negotiated compensation package; collect digital signature for audit trail. |
| **Actors** | HR Manager, Director (approval), Candidate |
| **Trigger** | Panel decision: Hire. |
| **Output** | Signed offer letter PDF stored in candidate record; triggers onboarding. |
| **Business Rules** | The offer is prepared from a template and sent by e-mail after human review. No salary threshold, no director approval step and no automatic expiry are applied. A candidate who accepts and then does not start is recorded in the joining-result field. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR generates offer letters from Odoo template: fills in position, start date, salary, benefits, probation terms. |
| Director | 2 | Director reviews and approves offers (required for senior/high-salary positions). |
| System | 3 | The system generates PDF offer letters and sends to candidate email with an e-signature link. |
| Candidate | 4 | Candidate reviews, negotiates (optional \- HR updates and resends), and signs digitally. |
| System | 5 | System records signature timestamp and stores signed PDF in hr.applicant attachments. |
| System | 6 | On signature confirmation, the system moves candidates to the Hired stage and triggers EMP onboarding workflow. |

| REC-07  Candidate Refusal & Talent Pool Management |
| :---- |

| Function Name | Candidate Refusal & Talent Pool Management |
| :---- | :---- |
| **Purpose** | Respectfully manage rejected candidates, archive qualified near-misses in talent pool for future reuse, ensuring positive candidate experience. |
| **Actors** | HR Manager |
| **Trigger** | Candidate rejected at any pipeline stage. |
| **Output** | Refusal email sent; high-potential candidates tagged in talent pool. |
| **Business Rules** | A rejection is recorded as Fail at CV screening or Fail at interview, together with free-text notes. There is no refusal-reason catalogue and no talent-pool tagging. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR selects Refuse on candidate record; system prompts for refusal reason (dropdown \+ notes). |
| HR Manager | 2 | HR selects if a candidate should be added to the Talent Pool (for future opportunities). |
| System | 3 | The system sends a templated rejection email within 24 hours (customizable by HR). |
| System | 4 | If Talent Pool \= Yes, system tags candidate with job category and skill tags for future search. |
| HR Manager | 5 | HR can search the Talent Pool when a new requisition opens to re-engage previous candidates. |

| REC-08  Recruitment Analytics & Channel ROI Reporting |
| :---- |

| Function Name | Recruitment Analytics & Channel ROI Reporting |
| :---- | :---- |
| **Purpose** | Provide HR and management with data-driven insights on hiring performance: time-to-fill, cost-per-hire, channel effectiveness, and pipeline conversion rates. |
| **Actors** | HR Manager, Director |
| **Trigger** | Monthly reporting cycle; ad-hoc management request. |
| **Output** | Recruitment dashboard with KPIs; channel ROI report. |
| **Business Rules** | Reports pull from hr.applicant data with UTM source tags. Time-to-fill measured from requisition approval to offer acceptance. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR accesses Recruitment Analytics dashboard in Odoo. |
| System | 2 | System displays KPIs: open positions, applications this month, time-to-fill by position, conversion rate per stage. |
| System | 3 | Channel ROI chart: applications, screenings, hires, and cost per channel (LinkedIn, Facebook, Referral, etc.). |
| HR Manager | 4 | HR exports report as Excel/PDF for monthly HR meeting presentation. |
| Director | 5 | Director reviews hiring velocity and approves/adjusts sourcing budget per channel. |

| REC-09  Handover to Employee Onboarding |
| :---- |

| Function Name | Recruitment to Employee Onboarding Handover |
| :---- | :---- |
| **Purpose** | Seamlessly convert accepted candidate (hr.applicant) to employee record (hr.employee) and trigger onboarding workflow without data re-entry. |
| **Actors** | HR Manager, System |
| **Trigger** | Candidate signs offer letter; stage \= Hired. |
| **Output** | hr.employee record created from applicant data; EMP-03 onboarding plan initiated. |
| **Business Rules** | Applicant data mapped to employee fields automatically. Contract created from offer letter terms. Employee ID assigned sequentially. Start date from offer letter. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | On the Hired stage, the system prompts HR to Create Employee from Applicant. |
| HR Manager | 2 | HR reviews auto-populated employee forms (name, email, phone, position from applicant record). |
| HR Manager | 3 | HR completes legal fields not captured in recruitment: CCCD, tax code, BHXH code, bank account. |
| System | 4 | System creates hr.employee record with status Onboarding. |
| System | 5 | System auto-creates labor contract draft from offer letter terms. |
| System | 6 | System triggers EMP-03 onboarding task list; notifies HR and the receiving department head. |

## **3.4: Time Off Module (TO)** {#3.4:-time-off-module-(to)}

![][image5]  
*Time off flow To-be process*

| Task | Lane (Actor) | Activity on the diagram | Description / Outcome |
| :---- | :---- | :---- | :---- |
| **1** | Employee | Employee needs to request leave (Start) | Employee initiates a leave request. |
| **2** | Employee | Select leave type and date range | The employee selects the leave type and the date range. |
| **3** | System | Validate: no duplicate request from the same employee, not entirely non-working days, valid supporting documents | System validates the request: checks for a duplicate request from the same employee, that the range isn't entirely non-working days, and that supporting documents are valid. |
| **4** | System | Create leave request | The system creates the leave request record. |
| **5** | System | Is the leave type flagged “emergency”? (Gateway) | The system checks whether the chosen leave type is marked as emergency. |
| **5A** | System | Yes → Notify direct manager | In an emergency, the direct manager is notified immediately first, then the flow still continues to step 6\. |
| **5B** | System | No → (go straight to step 6\) | If not an emergency, skip straight to notifying the scope approver. |
| **6** | System | Notify scope approver | System notifies the scope approver (Department Head / HR Manager-Admin) that a request is pending. |
| **7** | Scope Approver | Awaiting approval | The approver reviews the pending request. |
| **7A** | Scope Approver | (Boundary – Timer, non-interrupting) Leave start date passes while still pending → Send overdue-approval reminder | If the leave start date arrives while the request is still unapproved, the system sends an overdue reminder to the approver — the pending review keeps running in parallel. |
| **7B** | Scope Approver | (Boundary – Message, interrupting) Employee self-withdraws request (while pending) → Request withdrawn (cancelled before approval) (End) | If the employee withdraws the request while it's still pending, the review is cancelled immediately and the process ends as “withdrawn before approval.” |
| **8** | Scope Approver | Decision? (Gateway) | The approver decides: approve or reject. |
| **8A** | Employee | Reject → Notify request rejected → Request rejected (End) | If rejected, the employee is notified and the process ends as refused. |
| **8B** | System | Approve → System records request as approved | If approved, the system marks the request as approved. |
| **9** | Employee | Does the employee later submit a request to withdraw the approved leave? (Gateway) | Later on, does the employee submit a request to withdraw the already-approved leave? |
| **9A** | Employee | No → End (request remains in effect) (End) | If no withdrawal is requested, the process ends with the leave remaining in effect. |
| **9B** | Employee | Yes → Employee submits withdrawal request \+ reason | If yes, the employee submits a withdrawal request with a reason. |
| **10** | System | Notify scope approver (withdrawal request) | System notifies the scope approver of the withdrawal request. |
| **11** | Scope Approver | Scope approver reviews withdrawal request | Approver reviews the withdrawal request. |
| **12** | Scope Approver | Agree to allow withdrawal? (Gateway) | The approver decides whether to allow the withdrawal. |
| **12A** | System | Agree → Invalidate request → Refund leave balance | If allowed, the system invalidates the leave request and refunds the used leave balance/quota. |
| **13A** | Employee | Notify request withdrawn → Request withdrawn (End) | The employee is notified; the process ends with the request successfully withdrawn. |
| **12B** | System | Refuse → Keep request valid/unchanged | If the withdrawal is rejected, the system keeps the original leave request unchanged. |
| **13B** | Employee | Notify withdrawal request refused → Withdrawal request refused (leave remains in effect) (End) | The employee is notified; the process ends with the withdrawal refused and the original leave still valid. |

 

| TO-01  Leave Request Submission |
| :---- |

| Function Name | Leave Request Submission |
| :---- | :---- |
| **Purpose** | Allow employees to submit leave requests via SPA with real-time quota visibility, replacing Zalo/email-based requests with a traceable digital workflow. |
| **Actors** | Employee |
| **Trigger** | Employees need to take leave (annual, sick, unpaid, WFH). |
| **Output** | hr.leave record submitted for manager approval. |
| **Business Rules** | Employees can only request leave within the available quota. Annual leave: 1 day/month accrual, 12 days/year cap. Sick leave: up to 30 days/year with a medical certificate. Leave requests must be submitted a minimum 1 day in advance (except sick leave). |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Employee opens Leave Request form in SPA; selects leave type from dropdown. |
| System | 2 | The system displays the current balance for selected leave types (available days, used days, pending days). |
| Employee | 3 | Employee selects start date and end date; system auto-calculates number of working days. |
| System | 4 | System checks for teaching schedule conflicts (calls TO-04 check). Warns employees if conflict is detected. |
| Employee | 5 | Employee adds description/reason; attaches medical certificate if sick leave. |
| Employee | 6 | Employee submits request; status \= Draft → Submitted. |
| System | 7 | The system sends notification to the direct manager for approval. |

| TO-02  Quota, Accrual & Carry-Over Management |
| :---- |

| Function Name | Leave Quota, Accrual & Carry-Over Management |
| :---- | :---- |
| **Purpose** | Automate annual leave accrual (1 day/month), carry-over rules (max 5 days, expires end of Q1), and quota allocation for all leave types. |
| **Actors** | HR Manager, System (automated) |
| **Trigger** | 1st of each month (accrual job); January 1 (new year allocation); April 1 (carry-over expiry). |
| **Output** | Updated hr.leave.allocation records per employee; carry-over expiry notifications. |
| **Business Rules** | Annual leave accrual: 1 day/month for official staff. Probation staff: no leave in first 3 months. Carry-over: max 5 days, must be used by March 31\. Unused after March 31 \= forfeited. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | On 1st of month, automated cron job runs accrual: adds 1 day to each active official employee's annual leave allocation. |
| System | 2 | System caps allocation at 12 days/year; does not add more once cap reached. |
| System | 3 | On January 1, the system calculates carry-over: min(unused days, 5\) moved to carry-over allocation for the new year. |
| System | 4 | System creates hr.leave.allocation record for carry-over days with expiry date \= March 31\. |
| System | 5 | On April 1, system expires unused carry-over days; HR notified of forfeiture amounts. |
| HR Manager | 6 | HR can manually adjust allocations for special cases (maternity leave, BHXH sick leave beyond 30 days). |
| HR Manager | 7 | HR generates quota summary reports for payroll and audit purposes. |

| TO-03  Teaching Schedule Conflict Detection |
| :---- |

| Function Name | Teaching Schedule Conflict Detection |
| :---- | :---- |
| **Purpose** | Automatically detect when a teacher's leave request overlaps with scheduled teaching sessions and alert HR/Academic Admin to arrange substitution. |
| **Actors** | System, HR Manager, Academic Admin |
| **Trigger** | Teacher submits leave request in TO-01. |
| **Output** | Conflict alert with list of affected sessions; substitution request raised. |
| **Business Rules** | Conflict detection runs on every leave submission by teaching staff. Warning (not block) for conflicts; HR must explicitly confirm substitution before approval. Minimum 48-hour notice required for finding a substitute. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | On leave submission by employee with job position \= Teacher, system queries hocba.teaching.session for sessions in requested leave period. |
| System | 2 | If sessions found → system displays conflict warning: list of affected classes (date, time, subject, student group). |
| Employee | 3 | The employee acknowledges conflict and adds notes on who could substitute. |
| HR Manager | 4 | HR reviews conflict reports and contacts Academic Admin to arrange substitution. |
| Academic Admin | 5 | Academic Admin assigns substitute teacher and updates hocba.teaching.session. |
| HR Manager | 6 | HR confirms substitution arranged and proceeds with leave approval. |
| System | 7 | System links leave records to affected sessions for audit trail. |

| TO-04  Leave Analytics Dashboard |
| :---- |

| Function Name | Leave Analytics & Reporting Dashboard |
| :---- | :---- |
| **Purpose** | Provide HR and management with real-time visibility into leave patterns, quota utilization, absenteeism rates, and department coverage. |
| **Actors** | HR Manager, Department Manager |
| **Trigger** | Ongoing; monthly reporting cycle. |
| **Output** | Leave analytics dashboard; absence report; quota utilization report. |
| **Business Rules** | Dashboard visible to HR (all employees) and Managers (their department only). Data refreshed daily. Monthly report auto-generated on 1st of month. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR accesses Leave Dashboard in Odoo: views absence rate by department, leave type distribution, pending approvals. |
| System | 2 | Dashboard shows: leave balance per employee (filterable), upcoming planned absences, YTD absence rate. |
| Department Manager | 3 | Manager views own department's leave calendar and coverage gaps. |
| System | 4 | System generates monthly leave report: total leaves by type, cost impact (unpaid leave), carry-over balance warnings. |
| HR Manager | 5 | HR exports report for payroll reconciliation and management review. |

## **3.5: Payroll Module (PR)** {#3.5:-payroll-module-(pr)}

| PR-01  Salary Structure Configuration & Work Entry Consumption |
| :---- |

![][image6]  
*Payroll flow To-be process*

| Task | Lane (Actor) | Activity on the diagram | Description / Outcome |
| :---: | :---- | :---- | :---- |
| **1** | **HR / Chuyên viên C&B (HR Manager)** | Tạo Đợt lương Batch (hb.payslip.run) & Nhấn "Tạo & Tính lương" | Description: HR Manager opens the payroll module, creates a monthly payroll batch (hb.payslip.run), selects target period and department, and clicks "Tạo & Tính lương".  Outcome: Opens a new payroll execution cycle in draft state. |
| **2** | **Hệ thống Odoo 19 Engine (hocba_payroll)** | Tìm NV có HĐ hiệu lực → Bulk-insert phiếu lương (hb.payslip) | Description: System queries active employment contracts and bulk-inserts draft payslips (hb.payslip) for all eligible employees.  Outcome: Generates initial batch payslip records. |
| **3** | **Hệ thống Odoo 19 Engine (hocba_payroll)** | Background Worker: Tính lương Async (Topo Sort → AST → Bulk INSERT) — Chunk 50/lần | Description: System collects validated work entries (WORK100, WORK110, WORK200, LEAVE1xx), calculates gross wage, statutory deductions (BHXH, BHYT, BHTN, 7-bracket PIT), allowances, penalties, and net pay asynchronously in background chunks of 50 payslips.  Outcome: Populates payslip line computation results. |
| **4** | **HR / Chuyên viên C&B (HR Manager)** | Theo dõi tiến độ tính lương trên SPA (Poll Progress Bar mỗi 1.5s) | Description: HR Manager monitors background calculation progress via real-time SPA progress bar polling every 1.5 seconds.  Outcome: Tracks completion status of async payroll calculation. |
| **5** | **HR / Chuyên viên C&B (HR Manager)** | Kiểm tra Bảng lương tổng hợp & Báo cáo Biến động (chênh lệch >20%) | Description: HR Manager reviews master payroll summary sheet and variation report highlighting salary deviations exceeding 20% compared to previous period.  Outcome: Audits calculation accuracy and detects potential anomalies. |
| **6** | **HR / Chuyên viên C&B (HR Manager)** | Sửa dữ liệu đầu vào / Tính lại phiếu lương (từng NV hoặc cả batch) | Description: If figures require adjustment (Gateway = "Không đạt"), HR Manager updates input attendance/work entries or manual variables and re-computes specific payslips or the full batch.  Outcome: Corrects input data and updates computed payslips. |
| **7** | **HR / Chuyên viên C&B (HR Manager)** | Xác nhận Batch (draft → verify) | Description: Once payroll figures pass review (Gateway = "Đạt"), HR Manager confirms the payslip batch, transitioning state from Draft to Verify.  Outcome: Locks draft inputs and prepares payslips for employee verification. |
| **8** | **HR / Chuyên viên C&B (HR Manager)** | Chọn phiếu lương → Nhấn "Gửi mail" cho NV | Description: HR Manager selects verified payslips and triggers the bulk email dispatch action to notify employees.  Outcome: Initiates employee email verification workflow. |
| **9** | **Hệ thống Odoo 19 Engine (hocba_payroll)** | Tạo Token UUID → Render Email Template → Gửi Email kèm link xem phiếu | Description: System generates unique UUID secure tokens, renders custom HTML payslip email templates, and dispatches emails containing direct portal viewing links.  Outcome: Transmits secure payslip notification emails to employees. |
| **10** | **Nhân viên / Giảng viên / CTV** | NV Đăng nhập SPA → Xem phiếu lương (MyPayslipsView) → Xác nhận / Từ chối | Description: Employees log in to SPA Portal (MyPayslipsView), inspect detailed salary breakdowns, and click Confirm ("Đúng") or Submit Dispute/Feedback ("Sai").  Outcome: Records employee confirmation ("Xác nhận") or dispute feedback ("Khấu nại/Xử lý"). |
| **11** | **Hệ thống Odoo 19 Engine (hocba_payroll)** | CRON Job Daily: Tự động Confirm NV không phản hồi quá Deadline (auto_confirmed) | Description: System background CRON job runs daily to check unconfirmed payslips exceeding deadline and automatically confirms them (auto_confirmed = True).  Outcome: Resolves unconfirmed payslips automatically after deadline expiry. |
| **12** | **HR / Chuyên viên C&B (HR Manager)** | Xử lý NV chưa confirm: Gửi lại mail / Gia hạn deadline / Liên hệ NV | Description: If unconfirmed payslips remain (Gateway = "Chưa đủ NV confirm"), HR Manager resends notifications, extends confirmation deadline, or contacts employees directly.  Outcome: Resolves remaining pending employee confirmations. |
| **13** | **HR / Chuyên viên C&B (HR Manager)** | Đóng Batch & Lưu lịch sử kỳ lương (verify → close) | Description: Once all employee confirmations are completed (Gateway = "Đủ NV confirm"), HR Manager closes the payroll batch, permanently locking all payslips for the period.  Outcome: Transitions batch state from Verify to Close. |
| **14** | **HR / Chuyên viên C&B (HR Manager)** | Nhấn "Tạo File Ngân hàng" — Chọn NH (VCB / TCB / MB / BIDV / ACB...) | Description: HR Manager initiates bulk payment file generation by selecting beneficiary bank provider.  Outcome: Triggers bank file export sequence. |
| **15** | **Hệ thống Odoo 19 Engine (hocba_payroll)** | BankFormatterRegistry (Strategy Pattern) → Export XLSX theo định dạng từng NH | Description: System utilizes BankFormatterRegistry (Strategy Pattern) to format net payment records and exports customized XLSX files per bank specification (Vietcombank, Techcombank, MB Bank, BIDV, etc.).  Outcome: Produces bank-ready payment file for bulk salary disbursement. |
| **16** | **HR / Chuyên viên C&B (HR Manager)** | In bảng lương / Xuất Excel tổng hợp → Đưa Kế toán & Ban GĐ ký (ngoài HT) | Description: HR Manager prints/exports official master payroll report for final signoff by Accounting & Director to execute bank disbursement and close the cycle.  Outcome: Completes monthly payroll processing and disbursement cycle. |

| Function Name | Salary Structure Configuration & Work Entry Consumption |
| :---- | :---- |
| **Purpose** | Define salary computation rules (BHXH base, PIT rules, allowances) and consume validated Work Entry records from Attendance/Time Off as input for payroll. |
| **Actors** | HR Manager |
| **Trigger** | Monthly payroll run initiated (after attendance and leave data for the month have been validated ). |
| **Output** | Payslip lines populated from salary rules and work entry hours. |
| **Business Rules** | Salary structure: Basic Wage \+ Fixed Allowances \+ Teaching Hours \+ OT \- BHXH \- BHYT \- BHTN \- PIT. Work entries must be in Validated state before payroll run. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR confirms all work entries are validated (ATT-05 completed) after attendance and leave data for the month have been validated. |
| HR Manager | 2 | HR initiates monthly payslip batch run in Odoo Payroll module. |
| System | 3 | The system collects hr.work.entry records per employee for the month: WORK100 (standard), WORK110 (OT), WORK200 (teaching), LEAVE1xx (leave). |
| System | 4 | The system applies salary rules in configured sequence: compute gross wage from hours × rates. |
| System | 5 | System computes BHXH/BHYT/BHTN deductions: employee share subtracted from gross. |
| System | 6 | System computes taxable income \= gross \- BHXH employee share \- personal deduction (15.5M) \- dependent deductions. |
| System | 7 | The system applies a 7-tier PIT bracket to compute PIT deduction. |
| System | 8 | System generates payslip draft with all lines; HR proceeds to verification (PR-04). |

| PR-02  Teaching-Hours Salary Computation |
| :---- |

| Function Name | Teaching-Hours Salary Computation |
| :---- | :---- |
| **Purpose** | Compute variable teaching salary for instructors based on actual WORK200 hours multiplied by individual hourly rate from contract. |
| **Actors** | System (automated) |
| **Trigger** | Monthly payroll run (PR-01). |
| **Output** | Teaching salary line on instructor payslip. |
| **Business Rules** | Hourly rate stored in hb.contract.x\_teaching\_hourly\_rate. Hours sourced from WORK200 work entries only. Substitute teaching hours counted at the original teacher's rate. Minimum 60 hours/month guaranteed for full-time instructors. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | Payroll rule hb\_payroll\_teaching\_hours queries WORK200 entries for employees in payroll period. |
| System | 2 | System sums total teaching hours from validated work entries. |
| System | 3 | The system multiplies total hours × teaching\_hourly\_rate from contract. |
| System | 4 | If full-time teacher and hours \< 60 → system applies guaranteed minimum: 60h × hourly rate. |
| System | 5 | Teaching salary line added to payslip: shows hours, rate, and total amount. |
| HR Manager | 6 | HR reviews teaching salary computation against class schedule for spot-check validation. |

| PR-03  Net-to-Gross Negotiation Wizard |
| :---- |

| Function Name | Net-to-Gross Salary Negotiation Wizard |
| :---- | :---- |
| **Purpose** | Allow HR to input a desired net salary figure and auto-calculate the required gross salary accounting for all statutory deductions, used during offer negotiations. |
| **Actors** | HR Manager |
| **Trigger** | Offer negotiation stage (REC-06) or contract revision. |
| **Output** | Calculated gross salary recommendation for the target net amount. |
| **Business Rules** | Wizard uses same BHXH/PIT rules as production payroll. Dependent count input adjusts PIT calculation. Result is a recommendation; HR sets actual contract wage. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR opens Net-to-Gross Wizard: enters target net salary, job position, dependent count. |
| System | 2 | System runs iterative calculation: starts with net as gross, applies deductions, computes resulting net, adjusts gross up until net target is met. |
| System | 3 | System displays breakdown: recommended gross, BHXH (employee+employer), PIT, net salary. |
| HR Manager | 4 | HR uses result as basis for offer letter gross salary in REC-06. |
| System | 5 | HR saves calculations for reference; can re-run with different assumptions. |

| PR-04  Payslip Verification, Approval & Accounting Posting |
| :---- |

| Function Name | Payslip Verification, Approval & Accounting Posting |
| :---- | :---- |
| **Purpose** | Multi-step review and approval of monthly payslips before payment, ensuring accuracy. |
| **Actors** | HR Manager, Accountant, Director |
| **Trigger** | Payslip batch generated (PR-01). |
| **Output** | Approved payslip batch; journal entries posted in accounting; employees notified. |
| **Business Rules** | HR verifies spot-check 10% of payslips. Accountant reviews total payroll cost vs. budget. Director approves batch total. No payment without Director approval. Payslip PDF auto-generated and emailed to employees on approval. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR reviews payslip batch in draft state: spot-checks individual payslips for anomalies. |
| HR Manager | 2 | HR submits a batch for accounting review. |
| Accountant | 3 | Accountant verifies total payroll cost against budget; reviews BHXH/PIT totals. |
| Director | 4 | Director approves batch payment. |
| System | 5 | On approval, the system: Salary Expense, BHXH Payable, Tax Payable, Bank. |
| System | 6 | The system generates payslip PDFs and emails to each employee. |
| System | 7 | System marks payslip batch as Paid; locks for further modification. |

| PR-05  Vietnamese Bank Payment File Generation |
| :---- |

| Function Name | Vietnamese Bank Payment File Generation |
| :---- | :---- |
| **Purpose** | Generate bank-compatible bulk payment files for salary transfer, supporting major Vietnamese banks (Vietcombank, Techcombank, MB Bank and other configured bank format). |
| **Actors** | HR Manager, Accountant |
| **Trigger** | Payslip batch approved (PR-04). |
| **Output** | Bank payment file (CSV/XML per bank format); payment confirmation uploaded. |
| **Business Rules** | Bank account must be validated (account number \+ bank name on employee record). Multi-bank split supported. Payment file must balance to approved payroll total. Payment date \= last working day of month. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR selects approved payslip batch and clicks Generate Payment File. |
| System | 2 | System queries each employee's bank account details; groups by bank. |
| System | 3 | System generates bank-format file per bank (Vietcombank XML, BIDV CSV, etc.). |
| Accountant | 4 | Accountant uploads file to internet banking portal for batch approval. |
| System | 5 | After bank transfer completed, HR uploads payment confirmation file to Odoo. |
| System | 6 | System matches confirmation to payslip records; marks as Transferred. |

| PR-06  Statutory Reporting \- BHXH & eTax |
| :---- |

| Function Name | Statutory Reporting \- BHXH Declaration & eTax Filing |
| :---- | :---- |
| **Purpose** | Generate monthly BHXH contribution report and quarterly PIT withholding declaration in formats required by Vietnamese authorities for iBHXH and eTax portals. |
| **Actors** | HR Manager, Accountant |
| **Trigger** | Monthly payroll completion; quarterly PIT deadline. |
| **Output** | BHXH declaration file for iBHXH portal; PIT withholding report (Phụ lục 05-1/BK-TNCN) for eTax. |
| **Business Rules** | BHXH report: total employee \+ employer contributions by employee. PIT report: gross income, deductions, taxable income, PIT withheld per employee. Filing deadlines: BHXH by 15th next month; PIT withholding by 30th next month. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | HR runs BHXH Report from Payroll menu; selects month. |
| System | 2 | System aggregates BHXH contributions from payslips: employee share (10.5%), employer share (21.5%) per employee. |
| System | 3 | System exports BHXH declaration in iBHXH-compatible format. |
| HR Manager | 4 | HR uploads to iBHXH portal by 15th of following month. |
| Accountant | 5 | Accountant runs PIT Withholding Report (quarterly); system generates Phụ lục 05-1. |
| Accountant | 6 | Accountant uploads to eTax portal by 30th of following month. |

| PR-07  Year-End PIT Finalization & 13th-Month Bonus |
| :---- |

| Function Name | Year-End PIT Finalization & 13th-Month Bonus |
| :---- | :---- |
| **Purpose** | Perform annual PIT finalization (quyết toán thuế TNCN) comparing withheld PIT to actual PIT liability; compute and disburse 13th-month bonus for eligible employees. |
| **Actors** | HR Manager, Accountant, Employee |
| **Trigger** | January of following year (after December payroll). |
| **Output** | PIT reconciliation per employee; 13th-month payslip; eTax annual declaration file. |
| **Business Rules** | PIT finalization: if withheld \> actual → refund via January payslip. If withheld \< actual → collect additional. 13th-month bonus: prorated for partial-year employees (months worked / 12). Minimum 1 month service required. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| System | 1 | In January, system generates year-end PIT summary per employee: total income, total deductions, total PIT withheld. |
| System | 2 | System recomputes annual PIT on full-year taxable income using progressive brackets. |
| System | 3 | System calculates reconciliation: withheld PIT \- actual annual PIT \= refund (positive) or additional collection (negative). |
| HR Manager | 4 | HR reviews reconciliation report; adjusts for any employees who filed their own declaration. |
| System | 5 | System generates 13th-month payslip: basic wage × (months worked / 12). |
| HR Manager | 6 | HR approves combined January payslip (regular \+ 13th month \+ PIT reconciliation). |
| Accountant | 7 | Accountant generates annual PIT declaration (Tờ khai quyết toán) for eTax filing. |
| System | 8 | System generates individual PIT certificate (chứng từ khấu trừ) for each employee as PDF. |

## **3.6: Performance Review Module (REV)**

**Both this module and section 3.7 were designed and built after the v1.0 To-Be baseline. The process described here is therefore the delivered process, not a forward-looking design.**

| REV-01  Periodic Performance Review |
| :---- |

| Function Name | Periodic Performance Review of Teaching and Office Staff |
| :---- | :---- |
| **Purpose** | Score every employee against a weighted criteria set each quarter, half-year or year, mixing indicators computed automatically from operational data with the manager’s own scoring, and publish a grade the employee can read. |
| **Actors** | HR Manager, Department Head (evaluator), Employee (self-assessment and published result) |
| **Trigger** | A review period is opened for a role group, or HR opens a single review for one employee. |
| **Output** | hb.performance.review record with scored lines, a weighted total on a 100-point scale, grade A/B/C/D, and an in-app notification to the employee once published. |
| **Business Rules** | One review per employee per period. The role group is frozen at creation so re-categorising an employee later does not distort past reviews. Indicators recompute only while the review is in Draft; confirming freezes them. Publishing requires a confirmed review. Grade thresholds come from configuration (A ≥ 85, B ≥ 70, C ≥ 55, otherwise D). |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | Opens the review period for a role group — Giảng viên or Nhân viên văn phòng — choosing quarter, half-year or year. |
| System | 2 | Creates one draft review per employee in that group, copying the current criteria with their weights and maximum scores onto the review lines. |
| System | 3 | Computes the four automatic indicators from data already in the system: teaching sessions or worked days, punctuality rate and late count, leave days in the period, and certificate validity. |
| System | 4 | Converts each indicator to a suggested score on the 1–5 scale using the threshold tables and pre-fills the matching criterion. |
| Evaluator | 5 | Opens the review drawer, keeps or overrides each suggested score, scores the remaining criteria manually and writes the manager comment. |
| Employee | 6 | Optionally records a self-assessment note before the review is confirmed. |
| Evaluator | 7 | Confirms the review; the system freezes the indicator snapshot and computes the weighted total and the grade. |
| HR Manager | 8 | Publishes the review; the employee receives an in-app notification and can read the result. |

| REV-02  Review Criteria & Grade Threshold Configuration |
| :---- |

| Function Name | Review Criteria and Grade Threshold Configuration |
| :---- | :---- |
| **Purpose** | Let HR maintain the two criteria sets and the grading thresholds without a code change or a deployment. |
| **Actors** | HR Manager, Administrator |
| **Trigger** | The appraisal policy changes, or a new criterion is agreed with management. |
| **Output** | Updated hb.review.criteria catalogue and updated configuration parameters, applied from the next review period. |
| **Business Rules** | Criterion codes are unique. Weights must not be negative and each group’s weights should total 100; the maximum score must be at least 1\. The seeded catalogue is declared noupdate so HR edits survive a module upgrade. Changing a criterion never alters reviews already created — weights are copied onto each review line at creation. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | Opens the criteria catalogue and selects the role group to maintain. |
| HR Manager | 2 | Edits a criterion: name, weight, maximum score, scoring guideline and scoring source (manual or one of the automatic sources). |
| System | 3 | Validates the weight and the maximum score and rejects a duplicate criterion code. |
| HR Manager | 4 | Deactivates criteria that no longer apply instead of deleting them, so historical reviews stay readable. |
| Administrator | 5 | Adjusts the grade thresholds and the teaching-session target through configuration parameters. |
| System | 6 | Applies the new catalogue from the next review created; reviews already open keep the weights copied at their own creation. |

## **3.7: HR Service Request Module (SVC)**

| SVC-01  Submit a Service Request, Question or Feedback |
| :---- |

| Function Name | Submit an HR Service Request, Question or Feedback |
| :---- | :---- |
| **Purpose** | Give every employee one channel to ask HR or their department head for a service — employment or income confirmation letters, contract copies, salary/insurance/tax questions, badge reissue — or to send feedback, a suggestion or a complaint, anonymously when the request type allows it. |
| **Actors** | Employee, System |
| **Trigger** | An employee needs a document, has a question, or wants to give feedback about their work environment or their manager. |
| **Output** | hocba.hr.request record with a sequence number and a processing deadline, plus a notification to the recipient. For an anonymous request the sender identity is written to a separate table that has no access rules. |
| **Business Rules** | Anonymity is only available on types that declare it, and such types must not allow attachments because an attachment records its creator. Complaint-about-management types always go to HR. An anonymous request may go to a department head only if that department has at least the configured minimum headcount (default 5\) and only one recipient may be chosen. At most three anonymous requests per employee per day. A request cannot be addressed to a department that has no head. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Employee | 1 | Opens the Yêu cầu dịch vụ screen and chooses a request type; the form adapts to the rules declared on that type. |
| Employee | 2 | Writes a subject and body, and adds an attachment or a 1–5 star rating when the type allows it. |
| Employee | 3 | Chooses the recipient — HR or the department head — and switches on anonymity if the type permits it. |
| System | 4 | Validates every rule (anonymity allowed, department size, daily cap, single recipient, attachments) and rejects with a specific message when one fails. |
| System | 5 | Creates the request with a sequence number, writes the sender identity to the separate sender table, and computes the deadline from the type’s SLA in calendar days. |
| System | 6 | Notifies the recipient — the HR officers or the department head — without revealing the sender of an anonymous request. |
| Employee | 7 | Follows the request under Đơn của tôi, reads replies and answers back; anonymity is preserved throughout the conversation. |
| Employee | 8 | May withdraw the request while it is still open. |

| SVC-02  Process the Request Inbox |
| :---- |

| Function Name | Claim, Answer and Close HR Service Requests |
| :---- | :---- |
| **Purpose** | Give HR and department heads a worklist with clear ownership, a deadline and an audit trail for every request. |
| **Actors** | HR Officer, HR Manager, Department Head |
| **Trigger** | A new request arrives in the recipient’s inbox, or the cron flags a request past its deadline. |
| **Output** | Request moved through Mới → Đang xử lý → Đã trả lời → Đã đóng, with the conversation, the internal notes and the closing reason recorded. |
| **Business Rules** | Only a new request can be claimed and only the handler may answer it. HR does not supervise requests addressed to a department head — such a request reaches an HR account only when that person is also the head of the target department. Internal notes are never visible to the sender. A closed or cancelled request accepts no further messages. Overdue requests produce a de-duplicated reminder notification. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| Handler | 1 | Opens the processing inbox, filtered to the requests within their scope, with overdue items marked. |
| Handler | 2 | Claims a request; the system records the handler and the claim time and moves the request to Đang xử lý. |
| Handler | 3 | Writes an internal note when coordination is needed; the sender never sees it. |
| Handler | 4 | Replies publicly; the sender is notified and can answer back in the same thread. |
| Handler | 5 | Marks the request answered once the outcome has been delivered. |
| Handler | 6 | Closes the request with a reason; the closing time is recorded. |
| System | 7 | Runs the overdue cron: every open request past its deadline produces one reminder notification for the handler and the administrator, de-duplicated per request. |
| HR Manager | 8 | Reviews the statistics tab — volume, overdue count and distribution by type — to spot recurring issues. |

| SVC-03  Request Type Catalogue & Anonymity Thresholds |
| :---- |

| Function Name | HR Service Request Type Catalogue and Anonymity Thresholds |
| :---- | :---- |
| **Purpose** | Let an HR Manager add or change request types and adjust the anonymity guardrails without a code change or a deployment. |
| **Actors** | HR Manager, Administrator |
| **Trigger** | A new kind of request appears in practice, or the thresholds must be adapted to the real department sizes. |
| **Output** | Updated hocba.hr.request.type catalogue and updated configuration parameters. |
| **Business Rules** | A type code is unique and uses lower-case letters, digits and underscores only. A type that allows anonymity must not allow attachments. The SLA must be a positive number of days. A type is deactivated rather than deleted, and the last active type cannot be switched off. Threshold values are capped so that a typing error cannot disable anonymity system-wide. |

**Process Flow:**

| Actor | Step | Description |
| ----- | :---: | ----- |
| HR Manager | 1 | Opens the Cấu hình tab of the service screen, visible only to HR Manager and Administrator. |
| HR Manager | 2 | Creates or edits a type: name, code, order, default recipient, force-HR-only, anonymity, attachments, rating, SLA and guidance text. |
| System | 3 | Validates the code format and uniqueness, the SLA, and the anonymity/attachment incompatibility. |
| HR Manager | 4 | Deactivates a type that is no longer used; the system refuses to switch off the last active one. |
| Administrator | 5 | Adjusts the minimum department size for anonymous requests and the daily anonymous cap. |
| System | 6 | Applies the new rules to requests submitted from that moment; requests already in flight keep the SLA copied at submission. |

# **IV: Cross-Module Integration Flow** {#iv:-cross-module-integration-flow}

The seven modules are connected through a linear data flow. Each module's output feeds the next, with the Work Entry layer serving as the central bridge between operational HR data and payroll computation.

| Step | From Module | To Module | Data Transferred | Trigger |
| ----- | ----- | ----- | ----- | ----- |
| 1 | Recruitment (REC) | Employee (EMP) | Applicant data → Employee record (name, email, position, contract terms) | Offer letter signed (REC-09) |
| 2 | Employee (EMP) | Attendance (ATT) | Employee profile, contract type, shift assignment | Employee Active status confirmed |
| 3 | Employee (EMP) | Time Off (TO) | Employee profile, contract type, annual leave entitlement | Employee Active status confirmed |
| 4 | Attendance (ATT) | Payroll (PR) | Work entries: WORK100, WORK110, WORK200 (validated) | Payroll computation for the period  |
| 5 | Time Off (TO) | Payroll (PR) | Work entries: LEAVE1xx types (annual, sick, unpaid) | Payroll computation for the period  |
| 6 | Payroll (PR) | Statutory Authorities | BHXH declaration (iBHXH), PIT withholding (eTax) | Monthly/Quarterly filing |

#  **V: Development Consideration (WRICEF)** {#v:-development-consideration-(wricef)}

## **5.1  Form Consideration**

Custom forms (PDF/printed outputs) required for Vietnamese regulatory compliance and internal processes:

| No | Form ID | Form Name | Module | Odoo Model | Priority |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | FORM-01 | Employee Profile Print (Sơ yếu lý lịch) | Employee | hr.employee | High |
| 2 | FORM-02 | Labor Contract Template (Hợp đồng lao động) | Employee | hb.contract  | High |
| 3 | FORM-03 | Payslip (Phiếu lương) | Payroll | hb.payslip | Very High |
| 4 | FORM-04 | PIT Certificate (Chứng từ khấu trừ thuế) | Payroll | hb.payslip | High |
| 5 | FORM-05 | Leave Request Form (Đơn xin nghỉ phép) | Time Off | hr.leave | Medium |
| 6 | FORM-06 | Offer Letter Template | Recruitment | hr.applicant | High |

## **5.2  Report Consideration**

Custom reports for HR analytics, compliance, and management decision support:

| No | Report ID | Report Name | Module | Output Format | Priority |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | REP-01 | Monthly Attendance Summary Report | Attendance | Excel/PDF | High |
| 2 | REP-02 | Teaching Hours Report by Instructor | Attendance | Excel | Very High |
| 3 | REP-03 | Leave Quota Utilization Report | Time Off | Excel/PDF | High |
| 4 | REP-04 | Recruitment Pipeline & Channel ROI | Recruitment | Dashboard/Excel | Medium |
| 5 | REP-05 | BHXH Contribution Monthly Declaration | Payroll | XML (iBHXH) | High |
| 6 | REP-06 | PIT Withholding Quarterly Report (05-1/BK-TNCN) | Payroll | XML (eTax) | High |
| 7 | REP-07 | Annual PIT Finalization Declaration | Payroll | XML (eTax) | High |

## **5.3  Enhancement Consideration**

Custom Odoo modules and technical enhancements (WRICEF Classification: Enhancement):

| No | Module / Enhancement | Description | Scope | Priority |
| ----- | ----- | ----- | :---: | ----- |
| 1 | hocba\_employees | Employee master with VN legal fields: CCCD validation (BR-010), tax code, BHXH code, dependent management. | EMP | High |
| 2 | hocba\_attendance | SPA-based face-verified check-in (selfie \+ GPS), policy-driven check-in window and work credits, OT levels with credit rates, correction requests with preview-approve, per-session teaching check-in. | ATT | High |
| 3 | hocba\_recruitments | Full recruitment pipeline with 10 stages, competency assessment, offer letter generation. | REC | High |
| 4 | hocba\_timeoff | Leave request SPA, multi-level approval, accrual cron, carry-over rules, teaching conflict detection. | TO | High |
| 5 | hocba\_payroll | Teaching-hours salary rule, BHXH/PIT Vietnamese computation, net-to-gross wizard, bank file generation. | PR | Very High |
| 6 | hb\_payroll\_teaching\_hours | Delivered inside hocba\_payroll: teaching hours × contract rate via work entries (guaranteed-minimum logic not delivered). | PR | Very High |
| 7 | hocba\_hrm (SPA Controller) | React/Vite SPA embedded at /hocba-hrm: check-in UI, profile self-service, leave request, payslip view. | All | High |
| 8 | hocba\_users | Role/permission groups: HR Admin, Manager, Giao Vu (teacher admin), Employee. ACL matrices per module. | All | High |
| 9 | GPS \+ Face Validation | Browser geolocation \+ client-side face-descriptor matching; out-of-zone and face-suspect punches flagged for manager review (IP range check not delivered). | ATT | Medium |
| 10 | CTV Shift Register | hocba.work\_shift custom model for part-time collaborator shift management (ATT-04). | ATT | Medium |
| 11 | Academic Schedule Integration | hocba.teaching.session model linking class schedule to attendance auto-capture (ATT-02, TO-04). | ATT/TO | High |
| 12 | Work Entry Automation | Changed: payroll pulls validated attendance work credits and teaching work entries (hb.work.entry) at computation time — no month cut-off cron delivered. | ATT/TO | High |
| 13 | Bank Payment File Generator | Bank-format payment file generation (hb.bank.file) per bank, with Generated → Uploaded → Bank confirmed states, marked manually by the operator. | PR | High |
| 14 | BHXH iBHXH Export | Generate iBHXH-compatible XML declaration file from monthly payroll data (PR-06). — Deferred to Phase 2 (not delivered). | PR | High |
| 15 | eTax PIT Export | Generate eTax-compatible XML for PIT withholding (quarterly) and year-end finalization (PR-06/07). — Deferred to Phase 2 (not delivered). | PR | High |
| 16 | Onboarding/Offboarding Checklist | Changed: delivered as two-gate probation evaluation (EMP-03) and a three-level offboarding approval flow with asset clearance (EMP-04) instead of auto task lists. | EMP | Medium |
| 17 | Net-to-Gross Wizard | Interactive wizard computing required gross salary for a desired net amount with full VN deduction rules (PR-03). — Deferred: FS spec drafted, no code yet. | PR | Medium |
| 18 | hocba\_notify (Added v2.0) | Unified in-app notification centre (hb.notification) with producers across all modules: approvals, reminders, payslip events; read/read-all API. | All | Delivered |
| 19 | hocba\_finance (Added v2.0) | Light cash-flow voucher & fund tracking module with SPA screen (full Financial Accounting remains out of scope). | Support | Delivered |
| 20 | hocba\_reviews (Added v2.1) | Periodic performance review: two configurable criteria sets, weighted five-point scoring, four indicators computed from operational data, A/B/C/D grading and a publish flow with employee notification (REV-01/02). | REV | Delivered |
| 21 | hocba\_service (Added v2.1) | HR service requests, questions and feedback with anonymity enforced at data level, a configurable request-type catalogue, a processing inbox with deadlines and an overdue-reminder cron (SVC-01/02/03). | SVC | Delivered |

 XÁC NHẬN CỦA ĐƠN VỊ / KHÁCH HÀNG

I. THÔNG TIN TÀI LIỆU

   Tên tài liệu     : ..........TO\_BE\_PROCESS............

   Mã tài liệu      : ISP490\_G2\_....       Phiên bản: v2.3.

   Ngày phát hành   : ..12../..08../2026....      Tổng số trang: ..71....

   Dự án            : Hệ thống Quản lý Nhân sự — Học Bá Education

   Nhóm thực hiện   : ISP490\_G2

II. THÔNG TIN ĐƠN VỊ XÁC NHẬN

   Đơn vị           : ..............................................

   Địa chỉ          : ..............................................

   Người đại diện   : ....................  Chức vụ: ..............

   Email / SĐT      : ..............................................

III. NỘI DUNG XÁC NHẬN

   Chúng tôi xác nhận đã tiếp nhận, rà soát và thống nhất với toàn bộ nội dung nghiệp vụ, phạm vi và yêu cầu được mô tả trong tài liệu nêu trên do nhóm ISP490\_G2 xây dựng và bàn giao.

   Mức độ:  ☐ Đồng ý toàn bộ   ☐ Đồng ý sau chỉnh sửa   ☐ Chưa đồng ý

   Ý kiến khác: .................................................................................................................

                                    *...Hà Nội...., ngày .12.. tháng .08.. năm 2026...*

 *ĐẠI DIỆN ĐƠN VỊ                       GIẢNG VIÊN HƯỚNG DẪN                ĐẠI DIỆN NHÓM*

*(Ký, đóng dấu, ghi rõ họ tên)             (Ký, ghi rõ họ tên)                               (Ký, ghi rõ họ tên)*

   *.....................                                              ....................                                    ....................*

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,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>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,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>