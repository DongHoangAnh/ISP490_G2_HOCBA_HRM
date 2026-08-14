"""Nội dung User manual module Employee + lệnh dựng file .docx.

    python build.py            # → out/ISP490_G2_User_manual_Employee_v1.0.docx

Mọi câu mô tả bám code thật (frontend/src/features/*, hocba_employees,
hocba_hrm/controllers/main.py) — xem spec:
docs/superpowers/specs/2026-08-14-user-manual-employees-design.md
"""
import os

from docx.shared import Pt

from gen_um_docx import Doc, _fill_table, _toc_table

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
OUT = os.path.join(HERE, 'out',
                   'ISP490_G2_User_manual_Employee_v1.0.docx')

VERSION = '1.0'
DATE = '14/08/2026'
AUTHOR = 'Vũ Chí Tân'
AUTHOR_MAIL = 'vct0866@gmail.com'


def fig(doc, key, caption):
    doc.figure(os.path.join(IMG, key + '.png'), caption)


# ======================================================================
def build():
    doc = Doc()

    # ---------------- Trang bìa ----------------
    p = doc.d.add_paragraph()
    p.alignment = 1
    for _ in range(4):
        p.add_run().add_break()
    doc.para('USER MANUAL', bold=True, size=Pt(30), center=True)
    doc.para('HRM ODOO – HỌC BÁ EDUCATION', bold=True, size=Pt(15),
             center=True)
    doc.para('Employee Module (Nhân sự)', bold=True, size=Pt(17), center=True)
    doc.para()
    doc.para('Project: HRM Odoo – Học Bá Education (ISP490_G2)', center=True)
    doc.para('System: Odoo 19 ERP + ReactJS SPA (/hocba-hrm)', center=True)
    doc.para('Module: hocba_employees', center=True)
    doc.para(f'Version {VERSION} – {DATE}', bold=True, center=True)
    doc.para('FPT University', center=True)
    doc.para()

    # ---------------- Change history ----------------
    doc.raw_table(_fill_table('history', {
        (0, 0): ('Change history', True),
        (1, 0): ('Changed date', True),
        (1, 1): ('Items have been changed', True),
        (1, 2): ('Change content / Reason', True),
        (1, 3): ('Updated by', True),
        (1, 4): ('Type (A/C/D)', True),
        (1, 5): ('Version', True),
        (2, 0): DATE, (2, 1): 'All', (2, 2): 'First Release',
        (2, 3): AUTHOR, (2, 4): 'A', (2, 5): VERSION,
    }))
    doc.note('A – Create        C – Change        D – Delete')

    # ---------------- FPT Signature ----------------
    doc.raw_table(_fill_table('sign', {
        (0, 0): ('FPT Signature', True),
        (1, 1): ('Full name & Role', True), (1, 2): ('Signature', True),
        (1, 3): ('Date', True), (1, 4): ('Note', True),
        (2, 0): ('Created by', True),
        (2, 1): f'{AUTHOR} / {AUTHOR_MAIL} / Developer – Employee module',
        (2, 3): DATE,
        (3, 0): ('Reviewed by', True),
        (3, 1): 'Phạm Đức Thắng / Reviewer – ISP490_G2',
        (4, 0): ('Approved by', True),
        (4, 1): 'Thesis Supervisor / FPT University',
    }))

    # ---------------- Table of contents ----------------
    doc.raw_table(_toc_table())
    doc.note('(Right-click the table of contents and choose “Update Field” '
             'to refresh page numbers.)')

    # ==================================================================
    # 1. OVERVIEW
    # ==================================================================
    doc.para(page_break=True)
    doc.h1('1. OVERVIEW')

    doc.h2('1.1 Process used in guide document')
    doc.para(
        'This user manual describes how to run the whole working life of an '
        'employee of Học Bá Education on the HRM system: from the profile '
        'opened on the first day, through the onboarding steps of the '
        'probation, the assets handed over, the certificates, the promotions '
        'and the career record, up to the resignation and the closing of the '
        'login account. Each business process below is one section of '
        'chapter 2.')
    doc.table('process', [
        ['Process No', 'Definition', 'Note'],
        ['EMP-BP-01', 'Employee profile – create, search, read, update '
                      '(Hồ sơ nhân viên)', 'Section 2.1 · FS-EMP-001 / 002'],
        ['EMP-BP-02', 'Dependents for personal income tax deduction '
                      '(Người phụ thuộc)', 'Section 2.2 · FS-EMP-003'],
        ['EMP-BP-03', 'Certificates, verification and expiry alerts '
                      '(Chứng chỉ)', 'Section 2.3 · FS-EMP-008 / 009'],
        ['EMP-BP-04', 'Asset register (Tài sản đang giữ)',
         'Section 2.4 · FS-EMP-006'],
        ['EMP-BP-05', 'Onboarding / probation by dynamic steps (Nhận việc)',
         'Section 2.5 · FS-EMP-004 / 005'],
        ['EMP-BP-06', 'Onboarding process configuration '
                      '(Cấu hình nhận việc)', 'Section 2.6 · FS-EMP-004'],
        ['EMP-BP-07', 'Promotion and salary history (Thăng tiến)',
         'Section 2.7 · FS-EMP-007 / 011'],
        ['EMP-BP-08', 'Career dashboard and honour board '
                      '(Lộ trình sự nghiệp)', 'Section 2.8 · FS-EMP-012'],
        ['EMP-BP-09', 'Login account management (Tài khoản)',
         'Section 2.9 · FS-EMP-013'],
        ['EMP-BP-10', 'Department management (Phòng ban)', 'Section 2.10'],
        ['EMP-BP-11', 'Offboarding / resignation (Nghỉ việc)',
         'Section 2.11 · FS-EMP-010'],
        ['EMP-BP-12', 'Self-service – my own profile (Hồ sơ của tôi)',
         'Section 2.12 · FS-EMP-001 / 002'],
    ])

    doc.h2('1.2 The working life of an employee')
    doc.para(
        'Every employee record carries a state (Tình trạng). The state drives '
        'the badge colour in every list, decides whether the person appears '
        'in tab Nhận việc, and is changed by the system itself at the two '
        'ends of the cycle: the onboarding step marked “Đạt → lên chính thức” '
        'turns the record official, and the completion of a resignation turns '
        'it resigned and archives it.')
    doc.table('stages', [
        ['#', 'State (Tình trạng)', 'Meaning', 'Where the employee appears'],
        ['1', 'Thử việc', 'Probation – the onboarding steps are running',
         'Nhân viên + Nhận việc'],
        ['2', 'Chính thức', 'Official – probation passed, official date set',
         'Nhân viên'],
        ['3', 'TTS', 'Intern', 'Nhân viên'],
        ['4', 'Part-time', 'Part-time contract', 'Nhân viên'],
        ['5', 'CTV', 'Collaborator (cộng tác viên)', 'Nhân viên'],
        ['6', 'Cố vấn', 'Advisor', 'Nhân viên'],
        ['7', 'Đang offboarding', 'A resignation request is being approved',
         'Nhân viên + Nghỉ việc'],
        ['8', 'Nghỉ việc', 'Resigned – record archived, login locked',
         'Tài khoản (marked Đã nghỉ)'],
    ])
    doc.para(
        'Beside the state, four classification axes are filled on the '
        'profile. They are not decoration: the first three decide which '
        'onboarding process the system assigns automatically (see section '
        '2.6), and the department decides who may read the record.')
    doc.bullets([
        'Hình thức làm việc – Offline or Online;',
        'Loại vị trí – Quản lý, Nhân viên, CTV, Freelancer, Cố vấn;',
        'Loại nhân viên – Nhân viên văn phòng, Giáo viên, Cộng tác viên;',
        'Phòng ban – the department the person belongs to.',
    ])

    doc.h2('1.3 Roles and permissions')
    doc.para(
        'A management account (HR, Admin, Giáo vụ) is separate from a '
        'personal account: it manages other people and therefore has no '
        '“Hồ sơ của tôi” entry in the sidebar. Read the table before '
        'reporting a missing button – most “the button is not there” cases '
        'are simply the permission working as designed.')
    doc.table('roles', [
        ['Role', 'Can do', 'Cannot do'],
        ['Administrator / (base.group_system)',
         'Everything in this manual, on every employee of the centre.', '—'],
        ['HR Manager / (hr.group_hr_manager)',
         'Everything: profiles, salary, onboarding steps and their deadlines, '
         'the onboarding configuration, accounts, departments, and the final '
         'approval of a resignation.', '—'],
        ['HR officer / (hr.group_hr_user)',
         'Create and edit any profile, dependents, certificates, assets; '
         'create and lock login accounts; manage departments.',
         'See or edit the salary block (Lương cơ bản, MST TNCN, số sổ BHXH, '
         'bank account); change an onboarding step deadline; complete a '
         'resignation.'],
        ['Giáo vụ / (group_hocba_giaovu)',
         'Everything an HR officer can do, plus the salary block – but only '
         'on the teachers (Loại nhân viên = Giáo viên).',
         'Touch a record of any other employee type; manage accounts or '
         'departments.'],
        ['Department manager / (hr.department.manager_id)',
         'Read and edit the profiles of the own department and of its child '
         'departments, see their salary, approve at the first level a '
         'resignation of the own staff.',
         'Reach an employee outside the own branch; manage accounts, '
         'departments or the onboarding configuration.'],
        ['Employee / (any logged-in account)',
         'Read the own profile in Hồ sơ của tôi, update contact and address, '
         'change the own photo, submit and cancel a resignation request, read '
         'the own career page.',
         'Open the management screens – they are not in the sidebar, and '
         'every write API answers HTTP 403 Forbidden.'],
    ])

    doc.h2('1.4 How to open the module')
    doc.para('(1) Open the HRM system: http://<server>/hocba-hrm and sign in '
             'with the company account.')
    fig(doc, 'fig-01-workspace',
        'The HRM workspace right after signing in')
    doc.para('(2) In the left sidebar, group QUẢN LÝ NHÂN SỰ, click '
             'Nhân viên. The screens of this manual are spread over three '
             'sidebar groups.')
    doc.table('tabs', [
        ['Screen', 'Used for', 'Section'],
        ['Nhân viên', 'Every profile: list, card view, and the detail drawer '
                      'with five tabs', '2.1 – 2.4, 2.7'],
        ['Nhận việc', 'Employees on probation and their onboarding steps',
         '2.5'],
        ['Nghỉ việc', 'Resignation requests and their two-level approval',
         '2.11'],
        ['Lộ trình sự nghiệp', 'Honour board and the full career record of '
                               'one person', '2.8'],
        ['Tài khoản', 'Login accounts: create, lock, reset the password',
         '2.9'],
        ['Phòng ban', 'Departments, their manager and their headcount',
         '2.10'],
        ['Cấu hình nhận việc', 'Onboarding process templates (HỆ THỐNG group)',
         '2.6'],
        ['Hồ sơ của tôi', 'Self-service – personal accounts only', '2.12'],
    ])
    fig(doc, 'fig-02-sidebar',
        'The sidebar of a management account – no “Hồ sơ của tôi” entry')

    # ==================================================================
    # 2. USER MANUAL
    # ==================================================================
    doc.para(page_break=True)
    doc.h1('2. USER MANUAL')

    # ---------- 2.1 ----------
    doc.h2('2.1 Employee profile (EMP-BP-01)')
    doc.h3('Content')
    doc.para('Purpose: hold one record per person, from which every other '
             'module reads. The record carries:')
    doc.bullets([
        'the identity block: employee code (Mã nhân sự, format HB.xx, '
        'generated by the system), full name, department, job title;',
        'the four classification axes of section 1.2;',
        'the legal block required by Vietnamese law: date of birth, CCCD, '
        'issue date and place, health insurance card, addresses;',
        'the salary block, visible only to the roles listed in section 1.3: '
        'base salary, PIT code, social insurance number, bank account;',
        'the child records: dependents, certificates, assets, onboarding '
        'steps, promotions – each in its own tab or block.',
    ])
    doc.para('Rule BR-010: an employee cannot be turned Chính thức while the '
             'CCCD (exactly 12 digits), the PIT code (10 or 13 digits) and '
             'the social insurance number (exactly 10 digits) are not all '
             'filled. The system refuses the save and names the missing '
             'field.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Nhân viên', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Nhân viên',
         'Every employee inside your scope'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Nhân viên. The chips on top filter by department and '
             'show the live headcount; the two drop-downs on the right filter '
             'by state and by working form. The list is paginated 20 rows at '
             'a time, and the search box in the top bar looks into the name, '
             'the code, the job title and the department.')
    fig(doc, 'fig-03-employees-table',
        'Screen Nhân viên – table view with the department chips')
    doc.para('(2) Use the switch Bảng / Thẻ on the right to change the '
             'presentation. The card view shows the same people with their '
             'state, working form and department as badges.')
    fig(doc, 'fig-04-employees-grid', 'Screen Nhân viên – card view (Thẻ)')
    doc.para('(3) Click Thêm nhân viên to open a new profile. Họ và tên is '
             'the only required field; leave Mã nhân sự empty and the system '
             'generates it. Fill in Ngày bắt đầu thử việc – without it the '
             'employee gets no onboarding process at all (see section 2.5).')
    fig(doc, 'fig-05-employee-form', 'Form Thêm nhân viên')
    doc.para('(4) Click a row to open the profile drawer. It has four tabs '
             'for everybody – Thông tin, Thử việc, Tài sản, Thăng tiến – and '
             'a fifth one, Tài khoản, for HR and Admin only.')
    fig(doc, 'fig-06-drawer-info', 'Profile drawer – tab Thông tin')
    doc.para('(5) Click Chỉnh sửa in the top right of the drawer to change '
             'the profile. The salary block appears in the form only for a '
             'role allowed to edit it; for everybody else the fields are not '
             'sent to the browser at all.')
    doc.para('Note: the list only ever shows the employees of your scope – '
             'the whole centre for HR and Admin, the own branch for a '
             'department manager, the teachers for Giáo vụ. A profile you '
             'cannot see does not exist for your session, so a headcount read '
             'on this screen is a headcount of your scope, not of the '
             'company.')

    # ---------- 2.2 ----------
    doc.h2('2.2 Dependents for tax deduction (EMP-BP-02)')
    doc.h3('Content')
    doc.para('Purpose: register the people an employee supports so that the '
             'payroll can apply the personal income tax deduction. Each line '
             'holds the name, the relationship, the date of birth and the '
             'period the deduction runs over (Giảm trừ từ … đến). An open '
             'end date means the deduction is still running.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Người phụ thuộc', 'Nhân viên ▸ open a profile ▸ tab Thông tin',
         'Block under the identity fields'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open the profile and scroll down in tab Thông tin to the '
             'block Người phụ thuộc, which shows the number of lines in its '
             'title.')
    fig(doc, 'fig-07-dependents', 'Block Người phụ thuộc inside tab Thông tin')
    doc.para('(2) Click Thêm NPT, fill in the form and save. Use the pencil '
             'icon to correct a line and the bin icon to delete it; the '
             'deletion asks for a confirmation because the payroll of the '
             'closed months keeps its own copy of the deduction.')
    fig(doc, 'fig-08-dependent-form', 'Form Thêm người phụ thuộc')
    doc.para('(3) The employee can also read and maintain this block on the '
             'own profile (section 2.12), which is the fastest way to keep '
             'the family data up to date at the end of the year.')

    # ---------- 2.3 ----------
    doc.h2('2.3 Certificates and expiry alerts (EMP-BP-03)')
    doc.h3('Content')
    doc.para('Purpose: keep the qualification of the teachers provable. A '
             'certificate line carries the type, the skill, the level, the '
             'issue date and, when the paper expires, the expiry date. The '
             'state column is computed from that date: Còn hạn, Sắp hết hạn '
             'and Hết hạn.')
    doc.para('A daily scheduled action raises a notification on the bell '
             'icon for the certificates that fall due inside the alert '
             'window – 60 days by default, held in the system parameter '
             'hoc_ba.cert_alert_days. Only a certificate marked Đã xác minh '
             'is watched, so an unverified paper never triggers a false '
             'alert. A second daily action does the same for the contracts '
             'that come to their end.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Chứng chỉ', 'Nhân viên ▸ open a profile ▸ tab Thông tin',
         'Block under Người phụ thuộc'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open the profile, tab Thông tin, block Chứng chỉ.')
    fig(doc, 'fig-09-certs', 'Block Chứng chỉ with the expiry states')
    doc.para('(2) Click Thêm chứng chỉ. Choose Loại first – the lists Cấp độ '
             'and Chứng chỉ are filled from it, so an impossible combination '
             'cannot be saved. Ngày hết hạn stays empty for a paper that '
             'never expires.')
    fig(doc, 'fig-10-cert-form', 'Form Thêm chứng chỉ')
    doc.para('(3) Tick “Đã xác minh bản gốc” once you have seen the original '
             'document. You can also switch the verification later straight '
             'from the table, by clicking the badge in the column Xác minh.')

    # ---------- 2.4 ----------
    doc.h2('2.4 Asset register (EMP-BP-04)')
    doc.h3('Content')
    doc.para('Purpose: know what company equipment a person is holding right '
             'now. The register is deliberately short – asset type, asset '
             'code, grant date and the condition recorded when it was handed '
             'over. There is no return or hand-over workflow: when the item '
             'comes back, the line is removed from the profile.')
    doc.para('The count of the assets still held is shown on a resignation '
             'request (section 2.11), which is where it matters: it is the '
             'checklist of what has to be collected before the last day.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Tài sản', 'Nhân viên ▸ open a profile ▸ tab Tài sản',
         'Equipment currently held by this employee'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open the profile and go to tab Tài sản. The tab title '
             'carries the number of items.')
    fig(doc, 'fig-11-assets', 'Tab Tài sản – equipment currently held')
    doc.para('(2) Click Cấp phát, choose the type, type the asset code and '
             'save.')
    fig(doc, 'fig-12-asset-form', 'Modal Cấp phát tài sản')
    doc.para('(3) When the item is returned, click Gỡ on its row and confirm. '
             'The line disappears from the profile – the register answers '
             '“what is out there now”, not “what happened in the past”.')
    doc.para('An onboarding step can hand out the standard equipment by '
             'itself: set its automation to “Tự cấp tài sản mặc định” in the '
             'onboarding configuration (section 2.6) and completing the step '
             'writes the default assets onto the profile.')

    # ---------- 2.5 ----------
    doc.h2('2.5 Onboarding by dynamic steps (EMP-BP-05)')
    doc.h3('Content')
    doc.para('Purpose: run the probation of a new employee as a list of '
             'steps that HR can configure, instead of three fixed evaluation '
             'gates. There are two kinds of step:')
    doc.bullets([
        'Việc cần làm – something to do (hand over the laptop, sign the '
        'contract, open the mailbox). It is closed with Hoàn thành and an '
        'optional note;',
        'Đánh giá – an evaluation, closed with one of Đạt, Gia hạn or Không '
        'đạt. A comment is mandatory for Không đạt.',
    ])
    doc.para('The steps run in order: only the current step can be acted on, '
             'the following ones stay “Chưa tới lượt”. A step marked '
             '“Không ràng buộc thứ tự” is the exception – it opens as soon as '
             'the process is assigned and can be done at any moment.')
    doc.para('The three results of an evaluation have three different '
             'effects. Đạt on a step configured as “Đạt → lên chính thức” '
             'turns the employee Chính thức and writes the official date. '
             'Gia hạn extends the probation by opening the extension step of '
             'the process. Không đạt ends the probation and pushes the '
             'employee into the offboarding flow of section 2.11 – the '
             'system asks for a confirmation before doing it.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Nhận việc', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Nhận việc',
         'Every employee on probation inside your scope'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Nhận việc. The four counters read the whole list: how '
             'many people are on probation, how many have a process still '
             'running, how many are waiting for an evaluation, and how many '
             'have passed the deadline of their current step. The column '
             'Tiến độ shows the progress bar, Bước hiện tại shows the current '
             'step with its deadline, in red when it is late.')
    fig(doc, 'fig-13-onboarding-list', 'Screen Nhận việc – employees on '
                                       'probation and their progress')
    doc.para('(2) Click a row to open the profile drawer straight on tab Thử '
             'việc. The header shows the name of the process and the '
             'progress; below it every step is one card with its state, its '
             'deadline, who closed it and when.')
    fig(doc, 'fig-14-onboarding-steps', 'Tab Thử việc – the steps of the '
                                        'assigned process')
    doc.para('(3) The action block only appears on the step you are allowed '
             'to act on. For an evaluation step, type the comment and click '
             'Đạt, Gia hạn or Không đạt.')
    fig(doc, 'fig-15-step-actions', 'Action block of an evaluation step')
    doc.para('(4) An HR Manager can correct the deadline of the open step '
             'with the pencil next to the date, and can change the whole '
             'process with Đổi quy trình. Changing the process drops the '
             'steps not done yet and appends the steps of the new process '
             'after them; the steps already completed are kept as history.')
    fig(doc, 'fig-16-template-picker', 'Đổi quy trình – choosing another '
                                       'onboarding process')
    doc.para('(5) When every step is done or skipped, the row reads “Hoàn '
             'tất quy trình”. If the process contains a step “Đạt → lên '
             'chính thức”, the line “Chính thức từ <date>” appears at the '
             'bottom of the tab.')
    doc.para('Note: an employee with no start date of probation, or matching '
             'no process at all, shows the message “Chưa có quy trình nhận '
             'việc” instead of the step list. Fill in Ngày bắt đầu thử việc '
             'and the classification axes, or assign a process by hand with '
             'Đổi quy trình.')

    # ---------- 2.6 ----------
    doc.h2('2.6 Onboarding process configuration (EMP-BP-06)')
    doc.h3('Content')
    doc.para('Purpose: let HR write the probation processes of the centre '
             'without touching any code – a different list of steps for a '
             'teacher, for an office employee, for a collaborator.')
    doc.para('Two rules decide everything on this screen. First, a new '
             'employee is matched against the processes from top to bottom '
             'and enters the first one that fits, so the order of the cards '
             'is the priority order. An empty criterion matches everything. '
             'Second, editing a process only changes the employees assigned '
             'from now on: the people already running keep the steps they '
             'were given (a snapshot), so a correction made today never '
             'rewrites a probation in progress.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Cấu hình nhận việc', 'Sidebar ▸ HỆ THỐNG ▸ Cấu hình nhận việc',
         'HR Manager / Admin only'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Cấu hình nhận việc. Every process is one card showing '
             'its matching criteria and its steps in order. The number on the '
             'left is the matching position.')
    fig(doc, 'fig-17-onb-config', 'Screen Cấu hình nhận việc – the processes '
                                  'in matching order')
    doc.para('(2) Drag a card, or use the ▲▼ arrows, to change that order. '
             'The new order is saved immediately.')
    doc.para('(3) Click Thêm quy trình, or click a card to edit it. Set the '
             'matching criteria on the three axes, then build the list of '
             'steps.')
    fig(doc, 'fig-18-onb-template-editor', 'Editing a process – criteria and '
                                           'steps')
    doc.para('(4) Each step needs a name, a kind (Việc cần làm or Đánh giá) '
             'and a deadline written as a number of days after the start of '
             'the probation. The remaining switches are what make the process '
             'behave:')
    doc.table('two', [
        ['Switch', 'What it does'],
        ['Đạt → lên chính thức',
         'Evaluation steps only. Passing this step turns the employee '
         'Chính thức and writes the official date.'],
        ['Bước gia hạn',
         'Evaluation steps only. The step stays closed and only opens when '
         'the previous evaluation was answered Gia hạn.'],
        ['Không ràng buộc thứ tự',
         'Task steps only. The step opens as soon as the process is assigned '
         'and can be closed at any time, in any order.'],
        ['Automation',
         'Task steps only. “Tự cấp tài sản mặc định” writes the default '
         'assets onto the profile when the step is completed. Not available '
         'on a step with no order constraint.'],
    ])
    doc.para('(5) If the criteria of the process you are editing overlap '
             'another one, a yellow warning names the rival and tells you '
             'which of the two wins by position. Use it before saving – two '
             'processes that fully overlap mean the lower one will never '
             'match anybody.')
    doc.para('(6) Use Gán NV đang chờ to assign a process to the employees on '
             'probation who have no steps yet – typically people created '
             'before the right process existed. The result line reports how '
             'many were assigned, how many matched nothing, and how many are '
             'missing their probation start date.')
    doc.para('Warning: Lưu trữ hides a process from future matching but does '
             'not touch anybody running it. Deleting a step from a process, '
             'on the other hand, only affects the employees assigned after '
             'the change.')

    # ---------- 2.7 ----------
    doc.h2('2.7 Promotion and salary history (EMP-BP-07)')
    doc.h3('Content')
    doc.para('Purpose: keep every move of a person – job title and salary – '
             'as a dated milestone that can be read years later. A promotion '
             'record holds the date, the job title before and after, the '
             'department, the salary before and after, the decision '
             'reference and the reason.')
    doc.para('Since 12/08/2026 this tab is read-only. A promotion is created '
             'from the evaluation form of module Đánh giá, together with the '
             'evaluation round that justifies it, so that a raise is never '
             'recorded without the paperwork behind it. What you see here is '
             'the result: the timeline, the salary chart and the radar of the '
             'criteria of the last round.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Thăng tiến', 'Nhân viên ▸ open a profile ▸ tab Thăng tiến',
         'Career milestones of this employee'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open the profile and go to tab Thăng tiến. The four metric '
             'cards read the seniority in months, the months since the last '
             'promotion, the number of evaluation rounds and the last score.')
    fig(doc, 'fig-19-promo-tab', 'Tab Thăng tiến – timeline and charts')
    doc.para('(2) The timeline lists the milestones from the oldest to the '
             'newest. The salary figures and the green “+” badge of a raise '
             'are only drawn for a role allowed to see the salary.')
    doc.para('(3) Click Mở trang lộ trình đầy đủ to jump to the career '
             'dashboard of the same person, described in the next section.')

    # ---------- 2.8 ----------
    doc.h2('2.8 Career dashboard and honour board (EMP-BP-08)')
    doc.h3('Content')
    doc.para('Purpose: put on one page everything that happened to one '
             'person – joining, onboarding steps, evaluations with their '
             'comments, promotions and honours – and, above it, the honour '
             'board of the whole centre. It is meant to be read, not '
             'clicked: the comments are open on the page, not hidden behind '
             'a popup.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Lộ trình sự nghiệp', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Lộ trình sự '
                               'nghiệp', 'Management accounts'],
        ['Lộ trình của tôi', 'Sidebar ▸ CÁ NHÂN ▸ Lộ trình của tôi',
         'The employee’s own record'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Lộ trình sự nghiệp. The honour board is shown '
             'straight away because it belongs to the whole company. A '
             'management account has no employee record attached, so the '
             'career part below waits until you pick somebody: type a name '
             'or an employee code in the search box at the top right.')
    fig(doc, 'fig-20-career-top', 'Screen Lộ trình sự nghiệp – honour board '
                                  'and the header of one employee')
    doc.para('(2) HR can add a name to the honour board with Thêm vinh danh, '
             'choosing the person, the title, the kind (Thành tích, Bổ '
             'nhiệm / Thăng chức, Kỷ niệm gắn bó, Khác) and the date. A '
             'department manager can read the board but not write on it.')
    doc.para('(3) The six figures under the profile card read the seniority, '
             'the number of promotions, the months since the last one, the '
             'number of evaluation rounds, the last score with its average, '
             'and the number of honours. The insight cards under them say in '
             'one sentence what the charts show.')
    fig(doc, 'fig-21-career-charts', 'Career charts – criteria radar, score '
                                     'trend and onboarding progress')
    doc.para('(4) The charts compare the last evaluation round with the '
             'previous one: the radar needs at least three criteria to be '
             'drawn, the score trend marks the 80 % qualification threshold, '
             'and the salary chart is only drawn for a role allowed to see '
             'the salary.')
    doc.para('(5) The table at the bottom is the full history. Use the '
             'buttons Tất cả / Thăng tiến / Đánh giá / Thử việc / Vinh danh '
             'to narrow it down; the score of each criterion is written as a '
             'chip under the corresponding round.')
    fig(doc, 'fig-22-career-timeline', 'Bảng lịch sử – the full record with '
                                       'the criteria scores')

    # ---------- 2.9 ----------
    doc.h2('2.9 Login account management (EMP-BP-09)')
    doc.h3('Content')
    doc.para('Purpose: decide who can sign in, with which role, and cut the '
             'access when it must stop. An account is always attached to an '
             'employee record; the account type sets the permission group of '
             'section 1.3.')
    doc.para('Locking is reversible and immediate: a locked person cannot '
             'sign in until somebody unlocks the account, while the employee '
             'record itself stays untouched. Completing a resignation locks '
             'the account by itself, so a person who has left never keeps a '
             'working login.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Tài khoản', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Tài khoản',
         'HR / Admin only. Every employee who has a login'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Tài khoản. The header counts the accounts and how '
             'many of them are locked; the two drop-downs filter by '
             'department and by state, and the search box looks into the '
             'name, the login and the employee code.')
    fig(doc, 'fig-23-accounts', 'Screen Tài khoản – the login accounts')
    doc.para('(2) To create an account, open the employee profile and go to '
             'tab Tài khoản, then click Tạo tài khoản. Fill in the login, a '
             'password of at least 8 characters, its confirmation, and the '
             'account type – Nhân viên thường, Giáo vụ or Trưởng phòng. The '
             'field Phòng ban only appears for Trưởng phòng, because that is '
             'the account type whose rights depend on a department.')
    fig(doc, 'fig-24-account-form', 'Form Tạo tài khoản đăng nhập')
    doc.para('(3) Back on the list, Khóa / Mở khóa switches the access and '
             'Cấp lại MK sets a new password. Both ask for a confirmation.')
    doc.para('(4) Two rows carry no buttons on purpose. A system '
             'administrator account is marked “Quản trị hệ thống” and cannot '
             'be locked from here. An employee already gone is marked '
             '“Đã nghỉ”: the account was locked when the resignation was '
             'completed, and unlocking it would produce a login without an '
             'employee record behind it, which the server refuses anyway.')

    # ---------- 2.10 ----------
    doc.h2('2.10 Department management (EMP-BP-10)')
    doc.h3('Content')
    doc.para('Purpose: hold the departments of the centre, each with its '
             'function, its manager and its headcount. The department is not '
             'only a label: the manager set here is what gives that person '
             'the reading and approval rights over the branch, child '
             'departments included.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Phòng ban', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Phòng ban',
         'HR / Admin only'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Phòng ban. The list shows the function, the manager, '
             'the headcount and the state of each department.')
    fig(doc, 'fig-25-departments', 'Screen Phòng ban')
    doc.para('(2) Click Thêm phòng ban to create one, or Sửa on a row to '
             'change it – typically to hand the department over to another '
             'manager.')
    fig(doc, 'fig-26-department-form', 'Form phòng ban')
    doc.para('(3) Lưu trữ takes a department out of use; if it still holds '
             'employees, the system says how many and asks for a '
             'confirmation. Tick “Hiện phòng đã lưu trữ” to see the archived '
             'ones and Khôi phục to bring one back.')

    # ---------- 2.11 ----------
    doc.h2('2.11 Resignation (EMP-BP-11)')
    doc.h3('Content')
    doc.para('Purpose: run a departure as a request that is approved twice '
             'and then completed, so that nobody disappears from the system '
             'without the assets being collected and the account being '
             'closed. The states are: Nháp → Chờ quản lý duyệt → Chờ HR '
             'duyệt → Chờ hoàn tất → Đã nghỉ, plus Từ chối and Đã huỷ.')
    doc.para('A request is raised in three ways: the employee submits it, HR '
             'opens it on their behalf, or the system creates it when an '
             'onboarding evaluation is answered Không đạt (section 2.5).')
    doc.para('Completing the request is the point of no return: the employee '
             'becomes Nghỉ việc, the record is archived and the login account '
             'is locked in the same movement. Only an HR Manager may do it.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Nghỉ việc', 'Sidebar ▸ QUẢN LÝ NHÂN SỰ ▸ Nghỉ việc',
         'Requests inside your scope, with the action buttons'],
        ['Nghỉ việc', 'Sidebar ▸ CÁ NHÂN ▸ Nghỉ việc',
         'The employee’s own requests'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) An approver opens Nghỉ việc and sees every request of the '
             'own scope. The column Tài sản shows how many items the person '
             'is still holding – hover it to read the asset codes. The '
             'buttons on a row are only the ones your role may press at the '
             'current state.')
    fig(doc, 'fig-27-offboarding-managed', 'Screen Nghỉ việc – requests '
                                           'waiting for approval')
    doc.para('(2) An employee opens the same entry under CÁ NHÂN and clicks '
             'Nộp đơn nghỉ. The form asks for the kind of reason (Tự nguyện, '
             'Không đạt, Hết hạn HĐ, Khác), the detailed reason and the '
             'expected last day.')
    fig(doc, 'fig-28-offboarding-form', 'Form Nộp đơn nghỉ việc')
    doc.para('(3) The employee follows the request in the table Đơn nghỉ '
             'việc của tôi. Click the row to read the detail, including who '
             'approved at each level; Huỷ is offered while the request has '
             'not been approved yet.')
    fig(doc, 'fig-29-offboarding-mine',
        'Đơn nghỉ việc của tôi – the employee’s own requests')
    doc.para('(4) The direct manager clicks Quản lý duyệt, then an HR '
             'Manager clicks HR duyệt. Either of them can click Từ chối, '
             'which puts the employee back into the state held before the '
             'request.')
    doc.para('(5) Once the equipment has been collected and the last day has '
             'come, the HR Manager clicks Hoàn tất and confirms. Remove the '
             'assets from tab Tài sản before this step – after it the profile '
             'is archived and no longer reachable from the employee list.')

    # ---------- 2.12 ----------
    doc.h2('2.12 Self-service – my own profile (EMP-BP-12)')
    doc.h3('Content')
    doc.para('Purpose: let every employee read their own record without '
             'asking HR, and keep the data that only they know – phone '
             'number, addresses, dependents, photo – up to date. The screen '
             'reuses the tabs of the profile drawer, in read-only mode for '
             'everything the employee must not rewrite: the classification, '
             'the salary, the onboarding results and the promotions.')
    doc.h3('Navigation')
    doc.table('nav', [
        ['Screen', 'Path', 'Description'],
        ['Hồ sơ của tôi', 'Sidebar ▸ CÁ NHÂN ▸ Hồ sơ của tôi',
         'Personal accounts only – not shown on a management account'],
    ])
    doc.h3('Detail implementation')
    doc.para('(1) Open Hồ sơ của tôi. The header carries the photo, the '
             'state badge and the contact details; the four tabs below are '
             'Thông tin, Thử việc, Tài sản and Thăng tiến.')
    fig(doc, 'fig-30-profile', 'Screen Hồ sơ của tôi')
    doc.para('(2) Click the photo to replace it – any image up to 8 MB. The '
             'new picture is used everywhere in the system at once.')
    doc.para('(3) Click Cập nhật thông tin to change the phone number and the '
             'two addresses. Everything else on the profile stays with HR.')
    fig(doc, 'fig-31-profile-edit', 'Form Cập nhật thông tin cá nhân')
    doc.para('(4) Tab Thử việc shows the onboarding steps as they stand, '
             'with no action buttons: the employee follows the probation but '
             'does not close its steps.')

    # ==================================================================
    # Appendix
    # ==================================================================
    doc.para(page_break=True)
    doc.h1('Appendix A – Frequently asked questions')
    doc.table('faq', [
        ['Question', 'Answer'],
        ['The employee cannot be turned Chính thức.',
         'Rule BR-010: the CCCD (12 digits), the PIT code (10 or 13 digits) '
         'and the social insurance number (10 digits) must all be filled '
         'first. The error message names the missing field; the bell also '
         'raises “cần hoàn thiện hồ sơ” when the onboarding reaches that '
         'point.'],
        ['A new employee has no onboarding steps.',
         'Either Ngày bắt đầu thử việc is empty, or the classification axes '
         'match no process. Fill them in, or use Gán NV đang chờ in Cấu hình '
         'nhận việc, or assign a process by hand with Đổi quy trình.'],
        ['The column Lương CB is not in the list.',
         'The salary block is hidden from an HR officer by design. '
         'Administrator, HR Manager, Giáo vụ and the department manager of '
         'the person see it; nobody else does.'],
        ['I edited a process but the employees on probation did not change.',
         'That is the snapshot rule: an edit only applies to the employees '
         'assigned from that moment on. Use Đổi quy trình on the profile to '
         'move somebody onto the new version.'],
        ['A resigned employee cannot be unlocked in Tài khoản.',
         'Completing a resignation archives the employee record and locks '
         'the account together. An unlocked login without an employee record '
         'is refused by the server, so the button is hidden. Ask HR to '
         'restore the employee record first.'],
        ['An evaluation answered Không đạt started a resignation.',
         'That is the designed behaviour – a failed probation ends the '
         'contract. The confirmation dialog says so before the answer is '
         'saved. If it was a mistake, refuse the resignation request: the '
         'employee goes back to the state held before it.'],
        ['A colleague does not appear in my employee list.',
         'You only ever see your own scope: your branch as a department '
         'manager, the teachers as Giáo vụ. It is not a data problem.'],
    ])

    doc.h1('Appendix B – Reference documents')
    doc.table('ref', [
        ['Document', 'Content'],
        ['FS-EMP-001 Employee Overview Profile',
         'Profile fields, the drawer tabs, the permission matrix'],
        ['FS-EMP-002 Vietnam Legal Data Fields',
         'CCCD, PIT code, social insurance, bank account and their checks'],
        ['FS-EMP-003 Dependent (Tax Deduction) Management',
         'Dependents and the deduction period'],
        ['FS-EMP-004 Onboarding Process & Dynamic Steps',
         'Process templates, matching, steps and their switches'],
        ['FS-EMP-005 Onboarding Step Automation & Reminders',
         'Deadlines, scheduled actions and notifications'],
        ['FS-EMP-006 Employee Asset Register',
         'Asset types, grant and removal'],
        ['FS-EMP-007 Promotion & Salary History (Snapshot)',
         'Promotion milestones and the salary journey'],
        ['FS-EMP-008 Trial Lesson Step & Teacher Skill Matrix',
         'Teacher skills, levels and the trial lesson step'],
        ['FS-EMP-009 Certificate & Contract Expiry Alerts',
         'Expiry states, the alert window and the daily jobs'],
        ['FS-EMP-010 Offboarding (Resignation) Management',
         'Request, two-level approval, completion'],
        ['FS-EMP-011 Promotion Evaluation Rounds & Criteria',
         'Evaluation rounds, criteria and scores'],
        ['FS-EMP-012 Career Path Dashboard & Honour Board',
         'Career page, charts and the honour board'],
        ['FS-EMP-013 Employee Login Account Management',
         'Account creation, roles, locking and password reset'],
    ])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)
    print('OK ->', OUT, '| figures:', doc.fig)
    return OUT


if __name__ == '__main__':
    build()
