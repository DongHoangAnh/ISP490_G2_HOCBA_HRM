BUSINESS BLUEPRINT




BUSINESS BLUEPRINT
	

Document information
	Project Name
	Human Resource Management System for Hoc Ba Learning Center
	Module
	MM - Materials Management 
	Created by
	Dong Hoang Anh (AnhDH)
	Version
	1.0
	Date
	21/05/2026
	________________


Table of content
CHAPTER 1 — PROJECT OVERVIEW        4
1.1 Project Information        4
1.2 Business Problem Statement.        6
1.3 Project Scope        8
CHAPTER 2 — BUSINESS PROCESS DISCOVERY (AS-IS)        13
2.1 Organizational Structure        13
2.2 Current Attendance Process        15
2.3 Current Employee Management Process        17
2.4 Current Recruitment Process (AS-IS)        21
2.5 Current Payroll Process        23
2.6 Current time off  Process        31
CHAPTER 3 — ODOO STANDARD PROCESS ANALYSIS        34
3.1 Standard Employee Management in Odoo        34
3.2 Standard Attendance Workflow in Odoo        37
3.3 Standard Recruitment Workflow in Odoo        38
3.4 Standard Payroll Workflow in Odoo        40
3.5 Standard Time off Workflow in Odoo        44
CHAPTER 4 — GAP ANALYSIS        47
I.  Module Employee        47
4.1. GAP Analysis Matrix        47
4.2 FIT Analysis        50
4.3 Configuration Gap        50
4.4 Customization gap        51
II. Module Attendance        52
4.1 GAP Analysis Matrix for Recruitment Module        52
4.2 FIT Analysis (Standard Odoo)        54
4.3 CONFIGURATION GAP (Configuration Only)        54
4.4 CUSTOMIZATION GAP (Development Required)        55
III. Module Payroll        56
4.1 GAP Analysis Matrix for Payroll Module        56
4.2 FIT Analysis (Standard Odoo)        61
4.3 CONFIGURATION GAP (Configuration Only)        62
4.4 CUSTOMIZATION GAP (Development Required)        65
IV. Module Recruitment        70
4.1 GAP Analysis Matrix for Recruitment Module        70
4.2 FIT Analysis (Standard Odoo)        73
4.3 CONFIGURATION GAP (Configuration Only)        73
4.4 CUSTOMIZATION GAP (Development Required)        75
V. Module Time off        76
4.1 GAP Analysis Matrix for Recruitment Module        76
4.2 FIT Analysis (Standard Odoo)        78
4.3 CONFIGURATION GAP (Configuration Only)        78
4.4 CUSTOMIZATION GAP (Development Required)        80
CHAPTER 5 — CONFIGURATION SPECIFICATION        84
5.1 Employee Module Configuration        84
5.2 Recruitment Configuration        86
5.2.1 Recruitment Stages        86
5.2.2 Email Templates        88
5.2.3 Interview Forms        88
5.3 Attendance Configuration        90
5.4 Payroll Configuration        90
5.5 Time off Configuration        90
________________


CHAPTER 1 — PROJECT OVERVIEW
1.1 Project Information
* English name: Human Resource Management System for Hoc Ba Learning Center.
* Vietnamese name: Hệ thống quản lý nhân sự cho trung tâm dạy và học tiếng Trung Học Bá.
* Project code: LCM
* Group name: ISP490-G2
* Software type: Web application 


1.1.2 Project Purpose
  
The purpose of this project is to design and develop a Human Resource Management System that supports the efficient operation of Học Bá Center’s Chinese language learning center. The system aims to streamline staff enrollment and employee management for Chinese language study. By integrating administrative management with managing.


















1.1.3. Product Background
  
Học Bá Company operates a specialized Chinese language learning center that provides comprehensive, multi-tiered educational curricula tailored for students at various proficiency levels, including beginner, intermediate, advanced, and HSK/HSKK examination preparation . Driven by the accelerating demand in the EdTech market, the center has experienced exponential growth in student enrollment, teaching faculty, active course sections, and multi-channel marketing campaigns . This rapid expansion has triggered severe operational bottlenecks, exposing critical limitations within the center's disconnected infrastructure and manual back-office administration .
Currently, core administrative and business processes at Học Bá Center rely heavily on manual workflows and decentralized, standalone applications such as spreadsheets, localized paper records, messaging platforms, and disjointed social media channels . Vital institutional records—encompassing student demographics, complex class rosters, daily attendance, examination scores, and instructional materials—are managed in siloes without an underlying database structure to cross-reference entries . Concurrently, the marketing and sales units generate high volumes of prospective student leads through ad platforms like Facebook Lead Ads Forms and Facebook Messenger . Because an automated synchronization layer is absent, these data payloads must be extracted and manually typed into a separate CRM application by sales consultants .
This fragmented data model and reliance on manual entry introduce significant operational vulnerabilities and friction points across the organization:
* Academic & Administrative Bottlenecks: Academic coordinators face massive administrative overhead when mapping shifting class schedules, optimizing teacher assignments, tracking daily student/staff attendance, and distributing timely course updates or examination reports .
* Faculty Disconnection: Instructors lack a centralized cloud console to view their assignment calendars, log classroom progress, monitor individual student performance metrics, or feed data back to administrators .
* Degraded Student Experience: Learners endure a fragmented touchpoint due to the absence of a unified self-service portal to access digital learning materials, check historical academic grades, or receive automated course alerts .
* Data Inefficiency & Revenue Leakage: Manual lead processing from Facebook causes severe lead-response delays, data corruption, duplicate profile creation, and the erasure of campaign attribution parameters, while denying executive management real-time data to audit advertising ROI .
Consequently, Học Bá Center lacks an integrated enterprise architecture capable of binding marketing execution, sales conversion pipelines, academic scheduling, and daily back-office operations into a single, cohesive workflow . To bridge these operational gaps, the implementation of a comprehensive Human Resource Management engine on the Odoo 19 platform (Odoo HRM) serves as the core digital backbone for internal workforce management. The platform will centralize multi-tier workforce profiles, automate recruitment lifecycles via Kanban states, enforce strict timekeeping compliance through localized GPS and IP-locked attendance trackers, automate complex payroll scripts for varied contract types, and eliminate manual request processes via self-service employee portals.
1.2 Business Problem Statement.

The rapid expansion of the student base and staff members at Hoc Ba Chinese Language Center is posing significant challenges to its internal governance. Currently, Human Resource Management (HRM) practices still heavily rely on manual tools and traditional workflows, leading to the following critical business pain points:
1.2.1. Scattered and Decentralized HR Data
* As-Is Situation: Employee profiles, background information, labor contracts, and qualifications are stored fragmentedly across multiple platforms (such as independent Excel files, personal Google Drives, Zalo/Messenger chats, and physical paper files).
* Consequence: There is a lack of a unified "Single Source of Truth." The HR department spends excessive time searching for and consolidating data. Information is highly prone to discrepancies, duplication, or loss when an employee resigns, posing security and corporate data integrity risks.
1.2.2 Heavy Reliance on Manual Operational Workflows
* As-Is Situation: Day-to-day HR administrative tasks — ranging from profile updates, contract renewal tracking, new hire onboarding checklists, offboarding handovers, to internal announcements — are processed manually or via informal chats and phone calls.
* Consequence: This creates operational bottlenecks. The approval process for administrative requests is severely delayed, consuming substantial time from both managers and employees, which lowers organizational professionalism and negatively impacts employee experience.
1.2.3. Inefficient Recruitment Control & Applicant Tracking
* As-Is Situation: Applicant resumes (CVs) arrive from various sourcing channels (Facebook, TopCV, Email, referrals) but are not categorized or managed centrally. Tracking the recruitment pipeline (Screening → Interview → Probation) is done through manual entry.
* Consequence: Hiring managers struggle to capture the real-time status of each candidate, leading to lost potential talent due to delayed responses. The center lacks concrete data to evaluate the efficiency (ROI) of recruitment channels and misses an organized "Talent Pool" to leverage for future hiring campaigns.
1.2.4. Inaccurate and Non-Real-time Attendance Tracking
* As-Is Situation: Hoc Ba's workforce is highly diverse (Teachers paid by teaching hours/shifts, Sales consultants working rotating shifts, and Back-office staff working fixed hours). Attendance tracking currently relies on manual spreadsheets or self-reporting without automated validation tools.
* Consequence: It is highly difficult to monitor late arrivals, early departures, absences, or overtime (OT) hours accurately in real-time. The end-of-month attendance reconciliation between HR and employees is stressful and prone to disputes due to the lack of transparent, verifiable data logs.
1.2.5. Complex and Error-Prone Payroll Processing
* As-Is Situation: Hoc Ba applies three completely distinct compensation structures: Teachers are paid based on actual teaching hours; Consultants (Sales) are paid based on base salary plus sales commission per student enrollment; Back-office staff are paid based on fixed working days.
* Consequence: Every month, the HR-Accounting department must manually process three separate Excel payroll sheets with highly sophisticated formulas. Consolidating commission metrics from the sales team and teaching hours from the academic department is prone to human error, causing payroll delays and diminishing employee trust.
1.2.6. Unstandardized Performance Appraisal System
* As-Is Situation: The center has not yet established a standardized performance evaluation framework (KPIs/OKRs) or periodic tracking tools for each job position. Most year-end evaluations are subjective and based on the qualitative perception of direct managers.
* Consequence: Employees cannot clearly visualize their career paths or growth opportunities within the organization. Rewards, salary increments, or disciplinary actions lack quantitative, data-driven evidence, potentially creating a sense of unfairness, lowering morale, and increasing the turnover rate of high-performing talents.
1.3 Project Scope
In Scope
Module 1 — Employees
This module manages all employee master data and organizational structure information.
Functional Scope
Employee Profile
* Maintain centralized employee records
* Personal information management
* Contact details
* Employment history
* Identification documents
* Emergency contact information
Department Management
* Create and manage organizational departments
* Define reporting hierarchy
* Assign employees to departments
* Department-based employee categorization
Contract Management
* Create employment contracts
* Contract type definition
* Contract duration tracking
* Contract renewal reminders
* Contract status monitoring
Role Assignment
* Assign job positions
* Define user access permissions
* Role-based system access control
* Responsibility allocation
Expected Outcomes
* Centralized employee information repository
* Improved employee data consistency
* Better organizational visibility
Module 2 — Recruitment
This module digitizes the hiring process for teachers and operational staff.
Functional Scope
Job Position Management
* Create recruitment requests
* Define job descriptions
* Manage vacancy status
* Publish internal/external openings
Applicant Tracking
* Candidate profile collection
* CV storage and evaluation
* Application stage tracking
* Candidate pipeline visibility
Interview Workflow
* Schedule interviews
* Assign interviewers
* Interview evaluation forms
* Candidate assessment tracking
Offer Management
* Generate offer letters
* Approval workflow
* Offer acceptance tracking
* Candidate conversion to employee record
Expected Outcomes
* Faster hiring process
* Better recruitment transparency
* Improved applicant tracking accuracy


Module 3 — Attendance
This module automates attendance recording and working time control.
Functional Scope
Check-in / Check-out
* Daily attendance logging
* Timestamp recording
* Late arrival / early leave detection
* Attendance history tracking
Shift Management
* Define work schedules
* Assign shifts to employees
* Flexible teaching schedule support
* Schedule conflict detection
Work Entry Rules
* Working hour calculation
* Overtime recognition
* Attendance exception handling
* Rule-based validation
Expected Outcomes
* Reduced manual attendance errors
* Accurate work-hour tracking
* Better operational discipline


Module 4 — Payroll
This module automates salary processing and compensation calculation.
Functional Scope
Salary Structure
* Define salary components
* Fixed and variable salary setup
* Salary rule configuration
Allowance Management
* Teaching allowances
* Performance incentives
* Transportation and support allowances
Deduction Management
* Absence deductions
* Late attendance penalties
* Insurance / statutory deductions
Payslip Generation
* Monthly payroll calculation
* Payslip generation
* Payroll approval workflow
* Employee payroll history access
Expected Outcomes
* Payroll accuracy
* Reduced processing time
* Transparent compensation management


Module 5 — Time Off
This module manages leave requests and approval workflows.
Functional Scope
Leave Request Management
* Submit leave applications
* Leave type selection
* Supporting document upload
Approval Workflow
* Manager review and approval
* Multi-level approval routing
* Leave status tracking
Leave Allocation
* Annual leave entitlement setup
* Sick leave allocation
* Special leave management
Leave Reporting
* Leave balance monitoring
* Department leave analytics
* Leave trend reports
Expected Outcomes
* Faster leave processing
* Reduced administrative burden
* Improved leave transparency
Out of Scope
The following modules are excluded from this project phase:
* Learning Management System (LMS)
* Student Information Management
* Academic Scheduling System
* CRM / Lead Management
* Financial Accounting
* Parent / Student Portal
* Online Course Delivery Platform
* Marketing Automation
* Website Redesign






CHAPTER 2 — BUSINESS PROCESS DISCOVERY (AS-IS)
2.1 Organizational Structure
Sơ đồ tổ chức
* Director
* HR
* Academic
* Teachers
* Sales
* Marketing
* Finance
2.1.1 Organizational Chart 
  

2.1.2 Functions, responsibilities, and specific human resource management characteristics of each department.
1. Board of Directors (Director)
Function: The highest level of management, responsible for strategic planning, budget approval, overall compensation policy issuance, and core personnel decisions (senior staff recruitment, dismissals, salary increases/decreases).
Specific Human Resource Management Features: The final authority to receive and approve long-term leave requests, additional recruitment requests from departments, and approve monthly payroll before payment.
Belongs to the group of personnel with fixed salaries (Management salaries).
2. Human Resources Department (HR)
* Function: Responsible for recruitment, onboarding, managing employee records and employment contracts, monitoring attendance and leave, directly calculating salaries, and handling handover procedures when employees leave (offboarding).
* Specific Human Resource Management Responsibilities:  Responsible for monitoring and managing the entire employee lifecycle at the center.
* Belongs to the office staff group, applying a fixed monthly salary system and attendance tracking based on standard office hours.
3. Academic & Teachers Department
Academic Staff:
* Functions: Managing the quality of professional education, compiling curricula/learning materials, setting and scheduling classes, managing online classes, and monitoring the teaching progress of instructors.
* Personnel Management Characteristics: Directly manages the faculty; responsible for checking, coordinating, and approving faculty leave schedules, substitute teaching shifts, or shift changes. Belongs to the administrative staff with a fixed salary.
Teachers:
* Function: Directly participate in teaching online Chinese language classes (Beginner, Intermediate, Advanced, HSK 3.0, VCT) as coordinated and assigned by the Training Department.
* Personnel Management Characteristics: Includes both full-time and part-time instructors, with significant fluctuations in size and working hours. Timekeeping is entirely based on actual teaching shifts/hours (extracted from class management data). Salary is calculated based on the hourly rate multiplied by the actual number of teaching hours, combined with allowances, attendance bonuses, or penalties for class cancellations as per regulations.
4. Admissions Consulting Department (Sales / Consultants)
* Function: Receiving potential customer leads from the Marketing department, contacting them to advise on suitable learning pathways, closing deals, and guiding students through the enrollment process and tuition payment.
* Personnel Management Characteristics: Flexible shift work (morning/afternoon/evening shifts) to optimize interaction time with customers; daily shift registration and tracking.
* Unique and highly variable income structure: Base salary + Sales commissions based on the number or value of successfully closed orders in the month. Commission data is compiled directly from the actual sales revenue recorded by each employee.
5. Marketing & Communications Department
* Functions: Building and positioning the brand of Hoc Ba Chinese Language Center, implementing advertising campaigns, managing social media channels to attract new students, and coordinating communication to attract candidates for the HR department.
* Specific Human Resources Management: Employees work during regular business hours or utilize a flexible (remote) work schedule. They are part of the office staff with a fixed salary, and may receive additional bonuses based on campaign performance (KPI Bonus).
6. Finance Department
* Functions: Control cash flow, manage tuition revenue, reconcile student payments (via PayOS and bank transfers), control operating expenses, and process payroll.
* Specific Human Resources Management Responsibilities:  Closely coordinate with the HR department to verify and check the accuracy of payroll, bonus, and commission summaries before exporting files for bank payments.
*  Responsible for accounting for all expenses related to salaries, social insurance, and personal income tax (PIT) in the center's accounting records.


2.2 Current Attendance Process
2.2.1. AS-IS PROCESS DISCOVERY
Học Bá Education currently operates an online training model with a diverse workforce divided into 3 specialized blocks:
* Office & Operations Bloc (Full-time Backoffice): Works according to a fixed administrative schedule (08:00-09:30 to 16:00-17:30, Monday to Friday). Requires strict control over late arrivals and early departures, ensuring a minimum daily working quota of 8 hours.
* Teachers & Tutors Bloc (Teachers/Tutors): Works flexibly on a part-time or visiting lecturer basis. Working hours depend entirely on the online class assignment schedule (Sessions) established by the Academic Affairs department, with each teaching session lasting from 1.5 to 2 hours.
* Collaborator Bloc (CTV/Part-time): Registers flexible working shifts weekly based on the volume of work arising at the center.
2.2.1.1 Current Manual Operational Workflow
* Shift Start (Check-in): Office staff, upon arriving at the company or working remotely, voluntarily log their clock-in time into a shared Excel file stored on Microsoft OneDrive without any authentication tools or network IP locking. Teachers and collaborators do not perform any administrative check-in actions and enter online classrooms (Zoom/Google Meet) or work groups directly.
* Shift End (Check-out) & Reporting: Office staff fill in their clock-out times in the OneDrive Excel file before leaving. Teachers, upon finishing a session, must access a Google Form link provided by the Academic Affairs department to submit a classroom acceptance report (class code, attendance count, lesson content, actual duration). Collaborators report their working hours via Zalo groups for manual approval by their Line Manager.
* End-of-Month Reconciliation: The C&B Specialist downloads the attendance file from OneDrive. The Academic Affairs department extracts data from the teachers' Google Forms and performs manual cross-reconciliation with the class schedule and classroom history logs (Zoom Attendance Report) to check for short-taught sessions or missed shifts. Once manually signed and approved, the data is consolidated into a master Excel file and sent to the HR department for manual payroll calculation.
2.2.1.2 Operational Pain Points and Risks
* PP-ATT-01 (Fraud and Inaccuracy): The manual entry mechanism on OneDrive Excel and Google Forms allows employees to easily declare incorrect hours, clock in on behalf of others, or falsify online teaching hours.
* PP-ATT-02 (Wasted Reconciliation Resources): The Academic Affairs and HR departments spend 3 to 5 days at the beginning of the month solely to collect and manually cross-reconcile data from scattered sources, delaying the payroll calculation and payment cycle.
* PP-ATT-03 (Data Dispute Risks): The lack of a transparent, real-time attendance logging storage system leads to frequent complaints and disputes over working hours between personnel and accounting.




  

2.3 Current Employee Management Process
Below is the BPMN diagram describing the current employee management process of Hoc Ba — before Odoo implementation:
  







User Persona & Staff Categorization
Hoc Ba currently manages its workforce across three distinct functional categories, each exhibiting unique operational requirements:
Academic Staff (Instructors & Teaching Assistants): Predominantly comprised of part-time or freelance (visiting) personnel. Core operations require comprehensive skills profiling for course mapping, professional certification management, and complex availability tracking for class scheduling.
Front-Office Staff (Admissions Consultants / Sales): Comprised of full-time and part-time shift-based personnel. Core operations are highly driven by sales targets (KPIs), online/hotline shift routing, and cross-campus resource deployment.
Back-Office Staff (Operations / Administration): Comprised of fixed full-time personnel across human resources, marketing, IT, and accounting. Core operations revolve around standardized attendance tracking, payroll, internal recognitions, and routine administrative workflows.
As-is Operational Workflows
Workflow 2.3.1: New Hire Onboarding Process
·         • Objective: Receive selected candidates from recruitment, provision required operational resources, and manage induction training.
·         • Current State: Semi-automated, heavily reliant on isolated Excel/Notion checklists and ad-hoc chat groups for task assignments.
·         • Procedural Steps:
Step 1: Data Intake (HR Department): HR ingests successful candidate files, issues the formal Offer Letter, and requests hard-copy compliance files alongside personal baseline records.
Step 2: Account Provisioning & Asset Issuance (IT & Admin): HR posts notifications within a shared chat group (Zalo/Slack) prompting IT to provision corporate emails (@hoc-ba.edu.vn) and grant LMS access rights. Admin prepares physical workstations or dispatches equipment.
Step 3: Induction & Training (Academic Training Dept): New instructors undergo mandatory training sessions covering 'Classroom Culture' and 'LMS Operational Protocols'. Evaluation metrics are manually stored in siloed Excel files within the Training department.
Step 4: Contract Execution & Archiving (HR Department): Execution of probationary or freelance contracts. Soft copies are archived on Google Drive, and physical copies are deposited in office filing cabinets.
Workflow 2.3.2: Employee Lifecycle & Skill Management
·         • Objective: Maintain personal records, track technological/pedagogical proficiency updates for instructors, and manage structural movements (promotions/transfers).
·         • Current State: Manual and highly fragmented. Each department hosts independent spreadsheets, leading to systemic data desynchronization.
·         • Procedural Steps:
Step 1: Master Record Maintenance (HR Department): HR maintains an Excel Master File containing core parameters: Full Name, Contact Details, Date of Birth, Department, and Base Salary.
Step 2: Competency & Certifications Updates (Academic Dept): When instructors achieve higher proficiency levels (e.g., advanced language metrics, pedagogical certifications), the Academic department updates its internal 'Instructor Competency Grid' for class dispatching. HR remains unaware of these updates in real-time.
Step 3: Lifecycle Transformations (Promotions/Transfers): When a Teaching Assistant is promoted to Full Instructor, or a Sales Consultant transfers between physical campuses or online teams, the executive board issues a written decree. HR manually updates the Excel Master File and notifies Accounting via chat for salary realignments.
Workflow 2.3.3: Offboarding & Asset Retrieval Process
·         • Objective: Terminate contracts, execute course/work handovers, revoke systems access, and retrieve corporate assets.
·         • Current State: Manual and prone to critical operational oversights, particularly surrounding system access revocation and in-progress class handovers.
·         • Procedural Steps:
Step 1: Resignation Reception (HR & Direct Manager): The employee submits a formal notice. The direct manager reviews, approves, and locks down the Last Working Day.
Step 2: Classroom & Work Handover (Departing Personnel & Academic Dept): Instructors hand over ongoing course syllabi, student progress reports, and grades to the Academic department to facilitate instructor substitution. Office staff transfer operational documentation.
Step 3: Asset Retrieval & Access Revocation (IT & Admin): HR alerts IT via chat to terminate corporate email access and revoke credentials across internal applications. Admin collects physical keys, parking passes, and company-owned devices.
Step 4: Financial Settlement & Final Archiving (HR & Accounting): Accounting calculates final working days, deductions, and processes final payouts. HR transfers the employee's soft-copy folder on Google Drive into an 'Archived/Terminated' repository.


2.3.4. Pain point




Lifecycle Group
	Identified Operational Pain Point
	Current Practical Reality & Root Cause
	Business Consequences & Operational Impact
	Onboarding
	Delayed Provisioning of Instructional Resources (Resource Bottleneck)
	New Chinese language instructors require corporate emails, Zoom Pro/ClassIn licenses, and academic slide decks. Due to HR issuing notifications via Zalo, requests frequently get buried.
	Instructors arrive on day one without teaching tools or authorized materials, causing significant class delays and damaging center reputation.
	Onboarding
	Fragmented Pedagogical Training Records (Training Silos)
	Before teaching, instructors undergo training on 'Language Reflex Methodology' or 'Pinyin Correction'. Evaluation logs are saved on local Academic spreadsheets.
	HR lacks real-time visibility into training outcomes, preventing them from proactively drafting contracts or executing early termination for underperforming staff.
	Lifecycle
	Blind Spots in Instructor Competencies & Certification Expirations (Skill Blindness)
	Instructor language metrics (HSK 6, Advanced HSKK, Pedagogical Certs) are maintained strictly by the Academic team for scheduling. HR only keeps flat administrative records.
	When management requires urgent workforce metrics for marketing campaigns or new branch approvals, staff must manually cross-reference files. No automated alerts occur for certificate expirations.
	Lifecycle
	Clunky Shift Rostering and Cross-Campus Sales Redeployment (Rostering Latency)
	Sales teams operate on fluid morning/evening shifts and rotate across campuses. Shift swaps and reassignments are approved via ad-hoc personal chat groups.
	HR updates the Master File with significant delays. End-of-month data transfers to Accounting lead to incorrect night-shift or location premium payouts, causing payroll disputes.
	Offboarding
	Leaked Intellectual Property and Active Zoom Pro Licenses (Data Leakage Risks)
	Upon employee departure, HR alerts IT via chat. IT must manually access multiple independent systems to terminate software access and shared cloud links.
	Delays lead to terminated instructors using company Zoom Pro licenses for private tutoring or copying proprietary HSK slide decks and test banks over to competitors.
	Offboarding
	Disrupted Classroom Workflows & Student Attrition (Class Disruption)
	Part-time instructors occasionally resign abruptly mid-course without providing lesson progress logs, class journals, or historical attendance files.
	The Academic department cannot verify exactly what has been taught. Substitute instructors face massive confusion, leading to poor student experience and refund requests.
	

2.4 Current Recruitment Process (AS-IS)
2.4.1. Process Flow
  

AS-IS
2.4.2. Process Description
Trigger: 
The process is triggered when there is a sudden surge in the number of students, causing departments to become overloaded (e.g., Training Department lacks instructors for evening classes, Sales Department lacks consultants for hotline services), or when the center implements a business expansion campaign as directed by the Board of Directors.
Steps:
1. Request Proposal: The Head of Department (Sales/Academic/Marketing) prepares a recruitment proposal based on the actual workload (clearly stating the number of positions, job titles, professional requirements, and expected salary) and submits it directly to the Board of Directors via Group Chat or Email.
2. Proposal Approval: The Board of Directors reviews the proposal's reasonableness based on the center's current budget to decide whether to approve or reject it.
3. Recruitment Communication: After receiving approval, the HR department compiles the job description (JD) and manually posts it to Facebook groups, freelance job sites (TopCV), or through the internal referral network.
4. Reception and Screening of Applications: Candidates send their CVs to the HR department's personal/departmental email address or via text message. HR personnel download the CVs, review them, manually categorize them, and update candidate information in a shared Excel tracking file.
5. Scheduling Interviews: HR contacts candidates directly via phone/Zalo to schedule interviews, then contacts the Head of Department to verify and confirm available time slots.
6. Conducting Interviews: Interviews are conducted online (via Zoom/Google Meet) or in person at the office with the participation of an HR representative (assessing cultural fit and soft skills) and the Head of Department (assessing teaching skills for lecturers or closing skills for sales).
7. Evaluation and Finalizing Results: After the interview, HR compiles written/message feedback from the Department Head, seeks salary budget approval from the Board of Directors, and drafts an Offer Letter to successful candidates.
Decision points: 
* Step 1 (Approval of Recruitment Proposal): The Board of Directors reviews whether the staffing needs are truly urgent and whether the budget can meet them. If not approved, the process ends.
* Step 2 (Resume Screening): HR evaluates candidates' CVs based on strict criteria (e.g., Lecturers must have HSK 5/6 certificates, Consultants must have telesales experience). If not met, the application is rejected or passively stored in a computer folder.
* Step 3 (Post-Interview Evaluation): The interview panel makes a decision on whether the candidate is successful or not based on an independent scoring system. If unsuccessful, HR sends a rejection email.
* Step 4 (Confirmation of Acceptance from Candidate): The candidate responds, agreeing to or rejecting the terms in the Offer Letter (Salary, probationary period, benefits).
Outputs:
Decisions regarding the recruitment and onboarding of new employees.
Excel file compiling a list of candidate statuses (difficult to update continuously).
CV data stored manually on Google Drive or the HR staff's computer memory.
2.4.3. Pain Points 
* Dispersed and easily lost candidate data: Candidate resumes (CVs) come from many different sources (Facebook, TopCV, personal email, Zalo) but lack a centralized storage system. HR personnel have to download them manually, leading to missed information, loss of potential candidates, or duplicate resumes between recruitment rounds.
* Pipeline management using Excel lacks visual clarity: Tracking candidate status (Contacted, Awaiting Interview, Accepted, Rejected) relies entirely on manual data entry in Excel files. When the number of candidates increases (especially for seasonal lecturer recruitment), the Excel file becomes overloaded, difficult to track, and managers cannot monitor recruitment progress in real time.
* Slow and unprofessional candidate responses: Because all interactions (sending interview invitations, thank-you letters, rejection letters) must be manually drafted email by email, the HR department frequently experiences delays in responding to candidates. This diminishes the candidate experience and results in the loss of many talented individuals to competitors.
* Lack of automated screening tools: For instructors and consultants, the center urgently needs screening tests (Chinese language knowledge test, sales situation handling skills test). Currently, sending and collecting tests is done via email, and scoring is done manually, consuming an extremely large amount of time for the professional department.
* Loss of the "Talent Pool": Highly qualified candidates who are not currently suitable are often "forgotten" in computer folders due to the lack of tagging features (such as skill tags, desired salary tags, position tags) to easily retrieve them for future recruitment campaigns.
* Lack of effective recruitment channel analysis reports: The Board of Directors and HR do not have accurate statistics on conversion rates (e.g., how many resumes from Facebook resulted in one job offer compared to TopCV), leading to subjective allocation of monthly job posting budgets and failure to optimize the cost per successful recruitment (Cost per Hire).
2.5 Current Payroll Process
This section describes the current state (AS-IS) of payroll processing at Học Bá Education, including the upstream activities of recording working hours and teaching hours that feed directly into the monthly salary calculation. Because Học Bá currently has no separate system for managing work entries, the recording of working hours, the validation of teaching sessions, and the salary calculation are all performed as one continuous manual process — and are therefore documented together in this single section.
2.5.1 AS-IS Process Discovery
Học Bá Education is currently processing payroll through a hybrid model combining Microsoft Excel (for raw data collection, working hours consolidation, and salary calculation) and accounting software MISA/Fast Accounting (for accounting entries, tax declarations, and statutory insurance reporting). This hybrid approach reflects the center's growth from a small operation but is increasingly inadequate as the headcount and number of teaching sessions expand monthly.
The compensation structure varies significantly between the three personnel blocks, each requiring a distinct calculation logic that cannot be standardized in a single Excel template:
•         Office & Operations Bloc: Fixed monthly salary based on the labor contract, plus position allowance, lunch allowance, transport allowance, and seniority allowance. KPI bonuses for the Marketing department and sales commissions for the Admissions Consulting department add another layer of variability.
•         Teachers & Tutors Bloc: Salary calculated entirely on an hourly basis — hourly rate (configured per teacher, varying by experience, certification level, and class type) multiplied by the actual validated teaching hours in the month. May include attendance bonuses for full class delivery and penalties for last-minute cancellations.
•         Collaborator Bloc: Pay-per-task or pay-per-shift basis, calculated case by case based on the agreement between the collaborator and the line manager. No fixed structure.


  

2.5.2 Current Manual Operational Workflow
Data Collection (Day 28 of month → Day 3 of next month)
The C&B Specialist (HR) initiates the payroll cycle by collecting input data from multiple sources:
•         Downloads the attendance OneDrive Excel file for Office staff (worked hours, late arrivals, early departures).
•         Requests the Academic department to send the consolidated teaching hours Excel for Teachers/Tutors (cross-reconciled with Zoom attendance logs and Google Form acceptance reports — see section 2.5.3 below for full detail).
•         Collects the approved leave list from the leave reconciliation file maintained by HR.
•         Requests the Sales Manager to send the monthly commission file (commission per consultant based on closed deals).
•         Collects approved overtime hours from the OT registration Excel maintained by department heads.
•         Collects ad-hoc bonuses, penalties, salary advances from Zalo messages or email approvals from the Board of Directors.
Salary Calculation in Excel (Day 3 → Day 6)
The C&B Specialist consolidates all input data into a master Excel file structured by department, then manually applies the following calculation steps for each employee:
•         Calculates Gross Salary: base salary + allowances + OT pay + commission/KPI bonus.
•         Calculates the insurance contribution base (BHXH/BHYT/BHTN), separating allowances that are subject to insurance (position, seniority) from those that are not (lunch, transport, phone).
•         Applies the insurance cap manually — checking each high-income employee against the BHXH/BHYT cap (20 × base salary reference) and the BHTN cap (20 × regional minimum wage).
•         Calculates personal income tax (PIT) by manually applying the 7-tier progressive tax brackets, subtracting personal deduction (11M VND) and dependent deduction (4.4M VND per dependent).
•         Calculates Net Salary = Gross − Insurance (employee portion) − PIT − other deductions (loan, advance, unpaid leave deduction).
•         Cross-checks formulas line by line — particularly for new hires (pro-rata calculation), employees who left mid-month, and employees in probation (85% salary).
Approval and Accounting Entry (Day 6 → Day 8)
After the Excel file is finalized:
•         HR sends the consolidated payroll file to the Finance department via email for verification.
•         Finance double-checks the calculations against the budget and previous month's payroll for any unusual variations.
•         HR submits the final file to the Board of Directors for approval (typically via email with the Excel file attached).
•         After approval, Finance manually enters salary expense entries, insurance entries, and PIT entries into MISA/Fast Accounting software — line by line per employee.
•         Finance generates the bank payment file (typically a separate Excel template required by the bank) and uploads it to the corporate banking platform for batch payment.
Payslip Distribution and Statutory Reporting (Day 8 → Day 10)
•         HR manually generates individual payslips by copying data from the master Excel into a payslip Word template, then exports each to PDF and sends via personal email to each employee.
•         Finance prepares the monthly insurance contribution report and submits it to the Social Insurance Authority through the iBHXH portal (data re-entered manually).
•         Finance prepares the monthly PIT withholding declaration and submits it to the Tax Authority through eTax (data re-entered manually).
2.5.3 Teaching Hours & Work Recording (Payroll Input Preparation)
Although Học Bá does not currently use the term 'work entry', the preparation of working-hours and teaching-hours data — which serves as the primary input for the payroll calculation described in section 2.5.2 — is one of the most labor-intensive parts of the entire payroll cycle. This sub-section documents the AS-IS practices for recording, validating, and reconciling work-hour data, since these activities will be encapsulated into a formal Work Entry concept when migrating to Odoo.
Daily Recording — Office Staff
•         Office staff voluntarily log their clock-in time into a shared Excel file stored on Microsoft OneDrive without any authentication tools or network IP locking.
•         At the end of the shift, the same staff member fills in the clock-out time in the same OneDrive Excel file before leaving.
•         There is no real-time validation: late arrivals, early departures, or missing entries are only detected at month-end during reconciliation.
•         Public holidays and weekends are not pre-marked in the attendance Excel. The C&B Specialist must remember to exclude them manually during payroll calculation.
Daily Recording — Teachers & Tutors
•         Teachers do not perform any administrative clock-in. They enter the Zoom/Google Meet classroom directly at the scheduled time.
•         After each teaching session, the teacher must access a Google Form link provided by the Academic department to submit a classroom acceptance report containing: class code, attendance count, lesson content, and actual session duration.
•         Collaborators (CTV) report their working hours via Zalo group messages, which the Line Manager approves verbally or with a simple 'OK' reply.
End-of-Month Reconciliation — The Hidden Bottleneck
This is currently the single most time-consuming activity in the payroll cycle. At month-end, the Academic department performs what is effectively a manual validation of teaching hours for Teachers/Tutors:
•         Downloads all Google Forms teaching-hours responses into a consolidated Excel file.
•         Downloads the Zoom Attendance Report for each class held during the month from the Zoom admin portal.
•         Manually cross-references each declared teaching session against: (a) the assigned class schedule, (b) the Zoom log proving the teacher actually entered the virtual classroom, (c) the duration of the Zoom session vs. the declared duration.
•         Flags discrepancies (declared 2 hours but Zoom shows 1h30, declared session but no Zoom log, etc.) and contacts the teacher via Zalo for explanation.
•         Manually resolves each discrepancy — either by accepting the teacher's explanation, requesting evidence (screenshots), or rejecting the declared hours.
•         Once all discrepancies are resolved, the Academic Head signs the consolidated Excel and sends it to HR. This signed file is treated as the validated teaching-hours input for payroll calculation.
This entire reconciliation process typically takes 3 to 5 working days, involves coordination between 1–2 Academic staff, 40+ teachers, and the C&B Specialist. There is no standardized validation form, no audit log, and no way to roll back changes once HR has consumed the data for payroll. After the data has been used for payroll, the source files on OneDrive and Google Drive remain editable, meaning a later edit creates a permanent mismatch between the data used and the data currently in the file.
Leave-Day Override Handling
When an employee has an approved leave during a working day, the C&B Specialist must remember to manually adjust the payroll Excel:
•         Subtract that day from the worked-days count in the payroll Excel.
•         If unpaid leave: apply the deduction formula (base / working_days × unpaid_days).
•         If paid leave: leave the salary unchanged but deduct from the annual leave balance file.
•         If a public holiday falls on a workday: ensure the day is counted as paid but not deducted from the leave balance. If a teacher actually conducted a class on a public holiday, ensure the 300% overtime rate is applied.
Because there is no system link between the leave records and the payroll Excel, these overrides depend entirely on the C&B Specialist's memory and manual cross-reference. Mistakes are caught only when employees complain after receiving their payslip — typically several days later.
2.5.4 Operational Pain Points and Risks
The following pain points cover the entire end-to-end Payroll process, including both the salary calculation (PP-PR-01 to PP-PR-10) and the upstream work-hour preparation activities (PP-PR-11 to PP-PR-15) that will be replaced by a formal Work Entry layer in Odoo:
ID
	Issue
	Detailed Description
	Impact Level
	PP-PR-01
	Excel–MISA Disconnect
	Payroll is calculated in Excel but accounting entries are made in MISA/Fast. Finance has to manually re-enter every payroll line into MISA after HR finalizes the Excel — duplicating work and creating opportunities for transcription errors. When the Excel is revised (frequent), the MISA entries must be reversed and re-entered.
	High
	PP-PR-02
	Complex Teacher Salary Calculation
	Teacher salaries depend on validated teaching hours, which themselves come from cross-reconciliation between Zoom logs, Google Form reports, and the Academic schedule. Any discrepancy in input data leads to incorrect salary calculation. Teachers frequently dispute their teaching hours after receiving payslips, requiring HR to manually re-check 3–5 cases per month.
	High
	PP-PR-03
	Manual Insurance Cap & Bracket Calculation
	BHXH/BHYT/BHTN caps and the 7-tier progressive PIT brackets are coded manually in Excel formulas. When the government adjusts the base salary reference, regional minimum wage, or tax brackets (which has happened multiple times in recent years), the formulas must be manually updated in every payslip template — error-prone and time-consuming.
	High
	PP-PR-04
	Lack of Audit Trail
	Excel files are edited directly without version history. When an issue is detected later (e.g., a dependent deduction missed for one employee for 3 months), it is impossible to determine when the data was changed, who changed it, or why. This creates audit and legal compliance risks.
	High
	PP-PR-05
	Slow Payroll Cycle (10+ days)
	The end-to-end cycle from data collection to bank payment currently takes 8–10 working days. Employees often receive salaries late (10th–12th of the following month), causing dissatisfaction and trust issues — particularly for hourly-paid teachers who depend on timely payment.
	High
	PP-PR-06
	No Net-to-Gross Calculation Tool
	When negotiating salary with new hires (especially senior teachers and foreign instructors), the offer is often agreed in Net terms. HR has to manually iterate the Gross calculation backward in Excel to arrive at the Net target — a process that frequently produces errors and creates contract disputes when the actual first payslip differs from the agreed Net.
	Medium
	PP-PR-07
	Manual Payslip Generation & Distribution
	Payslips are generated one by one in Word, exported to PDF, and emailed individually to each employee. For 40–50 employees per month, this takes a full working day. Mistakes in attachment (sending the wrong payslip to the wrong person) have happened multiple times, raising confidentiality concerns.
	Medium
	PP-PR-08
	Manual Bank File & Statutory Filing
	The bank payment file format differs by bank (the center uses VCB and Techcombank). HR maintains separate templates and re-formats data each cycle. The monthly iBHXH and eTax submissions also require manual re-entry of data, with no direct integration from the payroll system.
	Medium
	PP-PR-09
	Difficult Year-End Tax Finalization
	At year-end, HR must generate the PIT finalization report (Form 05/QTT-TNCN) by aggregating 12 monthly Excel files manually. This typically takes 3–5 working days for HR and is highly error-prone, especially for employees who joined or left mid-year.
	Medium
	PP-PR-10
	No Self-Service Payslip Access
	Employees have no portal to view their historical payslips. Whenever they need a salary confirmation (e.g., for personal loan applications), they must contact HR who manually retrieves and resends the PDF — an average of 10–15 requests per month.
	Low
	PP-PR-11
	No Validation Layer Between Recording and Payroll
	Working hours and teaching hours flow directly from raw recording (OneDrive Excel, Google Form) into the payroll Excel without an intermediate validation checkpoint. There is no mechanism to catch issues such as duplicate entries, overlapping shifts, or impossible durations (e.g., a teacher declaring 14 hours of teaching in a single day) before they affect salary calculation.
	High
	PP-PR-12
	Manual Teaching-Hours Cross-Reconciliation Bottleneck
	The Academic department spends 3–5 working days each month manually reconciling teaching hours between Google Forms declarations, Zoom logs, and class schedules. This is one of the heaviest recurring operational burdens at the center and is the primary cause of the slow payroll cycle described in PP-PR-05.
	High
	PP-PR-13
	No Conflict Detection
	Overlapping work records (e.g., a teacher accidentally declaring two teaching sessions at the same time slot, or a teacher being on approved leave but also declaring teaching hours) cannot be detected automatically. Such conflicts are typically discovered only when totals fail to match at month-end, forcing rework on data that has already been processed.
	High
	PP-PR-14
	No Distinction Between Work Types
	Normal working hours, overtime hours, teaching hours, public holiday work hours, and various leave types are not categorized in a standardized way in the source Excel files. The C&B Specialist applies different calculation logics from memory, which is error-prone and not scalable as the headcount grows.
	Medium
	PP-PR-15
	No Locking Mechanism After Payroll Calculation
	Once payroll has been calculated using a particular attendance/teaching-hours Excel file, there is no mechanism to lock that source data. The files on OneDrive and Google Drive remain editable, meaning a later edit (intentional or accidental) creates a permanent mismatch between the data used for payroll and the data currently in the file — a serious audit risk.
	Medium
	

2.6 Current time off  Process
2.6.1. AS-IS PROCESS DISCOVERY
Office & Operations Bloc (Full-time Backoffice): Employees are entitled to a fixed annual leave policy according to their labor contracts. Leave requests must be approved in advance by both the Direct Manager and HR department to ensure stable internal operations.
Teachers & Tutors Bloc (Teachers/Tutors): Teachers and tutors work flexibly based on teaching schedules and assigned online classes. Leave requests must be cross-checked against actual teaching schedules to avoid class disruption or unexpected session cancellations.
Collaborator Bloc (CTV/Part-time): Collaborators and part-time staff do not have fixed annual leave entitlements. However, leave status still needs to be recorded to support workforce coordination and work schedule management.
  

2.6.2 Current Manual Operational Workflow
Leave Request Submission
Employees currently submit leave requests through multiple communication channels such as:
* Zalo messages to their Direct Manager
* Internal Google Forms
* Direct verbal communication
Leave requests are often submitted without a standardized format and frequently lack important information such as:
* Leave type
* Specific leave duration
* Work handover person
* Supporting attachments or documents
Approval Process
Direct Managers review leave requests based on:
* Current staffing conditions
* Teaching schedules
* Work progress and operational workload
Approvals or rejections are then communicated manually via messages or phone calls.
The HR department currently does not have a centralized system to:
* Track leave history
* Monitor remaining leave quotas
* Audit approval activities
End-of-Month Reconciliation
At the end of each month:
* HR consolidates leave information from multiple disconnected sources
* Performs manual reconciliation using Excel files
* Calculates paid leave and unpaid leave balances
* Sends finalized leave data to the Payroll department for manual salary calculation
For Teachers and Tutors:
* The Academic Affairs department must additionally cross-check actual teaching schedules to determine whether leave requests affected any scheduled classes or caused session cancellations.
2.6.3 Operational Pain Points and Risks
PP-TO-01 (Lack of Centralized Data Management)
Leave information is scattered across:
* Zalo
* Google Forms
* Excel files
* Emails
This makes it difficult to maintain accurate and centralized leave history records across departments.
PP-TO-02 (Leave Quota Miscalculation)
HR manually calculates remaining leave balances using Excel spreadsheets, which can easily lead to:
* Incorrect annual leave calculations
* Wrong leave deductions
* Missing carry-over updates
PP-TO-03 (Class Operation Disruption Risks)
Teachers may request leave that overlaps with teaching schedules, while the current process does not provide automatic conflict detection or warnings. This can result in:
* Unexpected class cancellations
* Lack of substitute teachers
* Negative student learning experiences
PP-TO-04 (Lack of Transparency & Audit Logs)
There is currently no centralized:
* Approval history tracking
* Change log management
* System-generated timestamp records
This frequently leads to operational disputes such as:
* “The leave request was submitted but never approved.”
* “HR has not updated the leave balance.”
* “Nobody remembers who approved the request.”
CHAPTER 3 — ODOO STANDARD PROCESS ANALYSIS
3.1 Standard Employee Management in Odoo
3.1.1 Comprehensive Human Resource Data Architecture (Employee Profile Master Data)
The employee profile in Odoo 19.0 is designed as a centralized data hub, managing information through a strict tab-based separation structure:
* Main Identification Header: Includes Full Name, Portrait Image, Work Email, Work Phone, Company (within the Multi-company matrix), Department, and Job Position.
* Work Tab:
   * Hierarchy Management: Defines the direct Manager and Coach.
   * Organization Chart: The system automatically generates a hierarchical tree chart based on the parent_id (Manager) field configured on each profile.
   * Work Location: Defines the Work Location and Usual Work Location to serve presence control mechanics.
* Resumé & Skills Tab:
   * Resume: Manages education history and work experience on a visual timeline.
   * Skills: Defines skill types, specific sub-skills, and competency levels measured as predefined percentage scales (%).
   * Certifications: Tracks professional certifications tied to the employee.
* Private Information Tab:
   * Private Contact: Home address, personal email/phone number, and bank account details for payroll routing.
   * Dependents & Relations: Marital status, dependent count, and emergency contact information.
   * Legal Metrics: Nationality, Citizen ID/Passport, Visa, and Work Permit for foreign employees.
   * Attachments: Allows storing and managing the validity periods of scanned files such as Citizen IDs, Driver's licenses, and internet bills for remote work stipends.
* Payroll Tab: Provides a high-level overview of the contract status (Contract overview), total labor costs (Employer costs), and linked Working Schedule calendars.
* HR Settings Tab:
   * System Linkage: Connects the Employee profile with a system User account (Related User) for access control and permissions.
   * Approvers: Defines dedicated individual approvers for Time Off and Expense modules separately for each employee.
   * Attendance Codes: Manages Badge IDs (RFID cards) and secret PIN codes for native attendance check-ins/check-outs.
3.1.2. Lifecycle Plan Configuration & Execution Framework (Onboarding & Offboarding Plans)
Odoo 19.0 provides an automated mechanism for employee readiness and separation workflows through the definition of action Plans:
* Configuration Architecture
   * Plan Steps / Activities: The system allows predefining reusable task templates. Each task includes: Task Name, Activity Type (Email, To-do list, Phone call), Responsible party (explicitly assigned User accounts or relative roles such as Manager, HR, IT), and a relative completion timeline (number of days allocated).
   * Plan Templates (Plans): Bundles individual Activity templates into a comprehensive procedural package (e.g., Office Staff Onboarding Plan, Standard Offboarding Plan).
*  Execution & Monitoring Workflow
   * Execution (Launch Plan): When an operational workflow is triggered, the HR administrator executes the 'Launch Plan' wizard on a specific employee profile and selects the corresponding template. The system instantly clones template steps into real-time Activities and transmits automated notifications/emails to the dashboard of each responsible party.
   * Progress Tracking: The employee profile renders a visual progress bar, dynamically calculating the exact completion percentage (%) of the plan based on the number of tasks marked as 'Mark as Done' by the assignees.
   * Finalization (Archive): For the offboarding workflow, after all handover tasks are completed, the system provides an 'Archive' action. The employee profile transitions to an Inactive state, hiding it from daily operational lists and revoking system access from the linked User account, while completely preserving historical logs within the database for future reporting and auditing.
3.1.3. Presence & Advanced Presence Control Mechanics
Odoo 19.0 integrates a native mechanism to automatically determine real-time employee work states (Online/Offline/Away) based on two verification tiers:
* Basic Control: Synchronizes presence states directly with the Attendances module when employees perform Check-in/Check-out interactions, or tracks the real-time login status of the linked User account.
* Advanced Control: Allows activating logical validation rules, including:
   * Corporate IP Address Validation: Defines corporate office IP ranges. Employees are only considered "Present at Work" if their session connects from an authorized IP.
   * Outbound Communication Tracking: Monitors employee presence based on the frequency and volume of work emails sent directly through the system within a fixed time frame.
3.1.4. Organizational Structure & Departmental Hierarchy Management
* Multi-Tier Departmental Hierarchy: Supports deeply nested, multi-level parent-child department structures utilizing recursive data relationships.
* Smart Buttons Integration: The department dashboard embeds dynamic, single-click routing indicators that aggregate live data from connected modules. This grants managers instant access to: Appraisals, pending leave requests (Time Off), time-off allocation grants (Allocation), active job applications (Applicants), and expense reports awaiting managerial approval (Expenses) within that department's scope.
3.1.5. Employee Engagement & Recognition Framework (Gamification - Badges)
* Odoo standard integrates a digital recognition engine allowing the configuration of digital Badges.
* The system allows setting up automated Challenges or peer-to-peer appreciation mechanics (Grant badges) to allow managers or colleagues to directly reward exceptional performance.
3.1.6. Standard HR Analytics & Reporting Dashboard
The platform provides automated, native analytics out of the box, utilizing graphical Charts, Pivot tables, or Cohort views, including:
* Employee retention rate comparison reports across distinct operational periods or individual departments.
* Real-time status and validity tracking reports for professional Certifications across the entire organization.


  

3.2 Standard Attendance Workflow in Odoo
The standard Attendance module on the Odoo platform provides an automated working time management flow, synchronously processing the lifecycle of attendance data from input to accounting output:
* Shift In (Check-in):
   * Office Bloc: Employees log into the Odoo system via a desktop browser or mobile application and click the green "Check In" button in the top right corner of the screen.
   * On-site center staff: Use Kiosk Mode on a shared tablet placed at the entrance to quickly check in by entering a secure 4-digit PIN or scanning a personal Badge ID.
* Shift Out (Check-out): At the end of the workday or shift, employees click the "Check Out" button in the same manner as checking in.
* Automated Background Data Processing (Odoo Core Logic): The system records the actual timestamp in the database and links it directly to the employee's profile (hr.attendance). Based on the Working Schedule framework (resource.calendar) configured and assigned individually to each employee (e.g., 08:30 – 17:30, lunch break 12:00 – 13:00), Odoo automatically calculates the total actual net worked hours (worked_hours) and Overtime hours. The system automatically scans and compares: if the Check-in timestamp is later than the work schedule, it applies a Late In warning label ; if the Check-out timestamp is earlier than the work schedule, it applies an Early Out warning label.
* Payroll Output: Raw attendance data is automatically aggregated by the system into Work Entries records to serve as the sole legal foundation for the Payroll module to automatically calculate monthly payslips.


  

3.3 Standard Recruitment Workflow in Odoo
The Odoo Recruitment application provides an end-to-end, highly automated, and visually structured pipeline to track job applicants from their initial interest to their onboarding as full employees. Utilizing a dynamic Kanban board architecture, recruiters can seamlessly move candidates through sequential hiring steps while automating background communications, document handling, and interviews. 
Below is a detailed analysis of the standard recruitment workflow in Odoo:


3.3.1. Creation and Publication of Job Positions
The process begins with the structural definition of an open vacancy:
* Job Configuration: The HR team defines the Job Position name, department, company branch, targeted headcount, and the dedicated HR Recruiter responsible for the process.
* Website Publishing: Odoo integrates directly with the Website module. With a single click (Published / Unpublished toggle), the job post, along with its description and requirements, is made live on the public careers portal.
* Applicant Capture channels: Odoo assigns a dedicated email alias (e.g., jobs-hr@company.com) to each job position. Applications can be captured via:
   1. The online "Apply Now" web form.
   2. Direct emails sent to the job position's email alias.
   3. Manual creation by an HR officer or recruiter
3.3.2. The Core Recruitment Pipeline (Standard Stages)
  

Once an application is captured, Odoo automatically generates an Applicant Card within a visual kanban view. By default, Odoo structures the standard workflow into six distinct stages:
▶ New ▶ Initial Qualification ▶ First Interview ▶ Second Interview ▶ Contract Proposal ▶ Contract Signed 
Stage 1: New
* Objective: Centralized intake of all incoming applications.
* Key Functionality:  CV/Résumé Digitization (OCR): Odoo automatically extracts the candidate's name, email, phone number, and skills from their uploaded PDF resume, minimizing manual data entry.
   * Document Repository: All attachments (resumes, cover letters) are automatically stored in the integrated Documents application and displayed side-by-side with the candidate’s profile.
Stage 2: Initial Qualification
* Objective: Pre-screening and basic eligibility assessment.
* Key Functionality:  Recruiter reviews the digitized resume profile.
   * Send Interview/Survey: Recruiters can dispatch a pre-configured questionnaire or screening survey (powered by Odoo Surveys) with an answer deadline. This allows the system to collect structured parameters (e.g., salary expectations, work availability) before moving them to a live interview.
Stage 3: First Interview
* Objective: Conducting initial personal or phone screening.
* Key Functionality:  Automated Action Trigger: Moving a candidate into this stage can be configured to automatically dispatch a customizable email template (e.g., Applicant: Acknowledgement) acknowledging their progression.
   * Calendar Integration: Recruiters can schedule a meeting or video call directly from the application card. It syncs seamlessly with Odoo Calendar, Google Calendar, or Microsoft Outlook, sending out calendar invites automatically.
Stage 4: Second Interview
* Objective: Deep technical assessment or managerial evaluation.
* Key Functionality:  Interview Panels: Multiple internal team members can be tagged as interviewers.
   * Chatter Logs & Feedback: Detailed interview feedback, notes, and technical assessment scores are kept in the applicant’s continuous timeline (Chatter) for transparent collaborative hiring.
Stage 5: Contract Proposal
* Objective: Negotiating and extending the formal job offer.
* Key Functionality:  Salary Package Configurator: Odoo generates a dynamic salary and benefits offer link. The candidate can review their gross salary, time off allocation, meal vouchers, and insurance benefits remotely via the portal.
   * Digital Signatures (Odoo Sign): Offers can be securely signed online by both the HR manager and the applicant, eliminating paper workflows.
Stage 6: Contract Signed (The Hired Stage)
* Objective: Successful closure of the recruitment pipeline.
* Key Functionality:  Once fully executed, the applicant's card reflects a visual "Hired" banner. The entry into this stage registers the official hiring date for organizational tracking and HR analytics.
3.3.3. Pipeline Status and Health Indicators
To help recruiters prioritize daily tasks, each card features a color-coded status bar indicating candidate readiness:
* 🟢 Green (Ready for Next Stage): The candidate has passed the current stage’s benchmarks (e.g., completed the required survey) and is cleared to advance.
* 🔴 Red (Blocked): The candidate cannot proceed further due to unresolved issues or pending requirements.
* ⚪ Gray (In Progress): The candidate is actively undergoing evaluation within the current stage.
3.3.4. Post-Recruitment Integration: Transition to Employee
One of Odoo’s greatest workflow strengths is its modular interconnectedness. Once a candidate reaches the Contract Signed phase:
* One-Click Conversion: The recruiter clicks the "Create Employee" smart button. Odoo instantly ports the applicant’s metadata (contact info, address, banking info, signed contract, and resume) to create a brand-new profile within the Employees (HR) application.
* Onboarding Launch: The creation of the employee profile triggers a predefined Onboarding Plan—generating automated target activities for IT setup, badge allocation, training sessions, and system orientation.
3.3.5. Alternative Path: The Refusal Mechanism
If an applicant does not meet expectations at any point in the workflow:
* The recruiter clicks the "Refuse" action.
* A specific Refusal Reason must be selected (e.g., lack of experience, salary mismatch) for background reporting.
* Odoo prompts an optional, pre-configured automated email template to inform the applicant politely, maintaining a professional employer brand image while archiving the card for future consideration.
3.4 Standard Payroll Workflow in Odoo
The Odoo Payroll application provides an end-to-end, fully automated salary calculation engine that consumes validated work data (attendance, time off, contracts) and produces ready-to-pay payslips compliant with Vietnamese labor law (Personal Income Tax, mandatory insurance, dependent deductions). By integrating natively with the Work Entry layer, Time Off, Attendance, and Accounting modules, Odoo eliminates the manual Excel-MISA disconnect, the cross-reconciliation bottleneck, and the audit-trail gaps that characterize the AS-IS process.
3.4.1 Configuration Foundations (Pre-requisites)
Before any payslip is generated, three foundational configurations must be in place. These are typically set up once during system implementation and reviewed quarterly:
* Salary Structures (hr.payroll.structure): Each personnel block has its own structure — for Học Bá this means an "Office Staff Structure" (fixed monthly salary + allowances), a "Teacher Structure" (hourly rate × validated teaching hours), and a "Collaborator Structure" (pay-per-task). Each structure defines its own ordered set of Salary Rules.
* Salary Rules (hr.salary.rule): The atomic computation units (BASE, OT, BHXH, BHYT, BHTN, PIT, NET) written as Python expressions referencing inputs, contract fields, and previous rule outputs. Insurance caps, tax brackets, and the personal/dependent deductions are configurable parameters — not hardcoded — so changes to government regulations require only a configuration update, not a code change.
* Contracts & Work Entry Types: Each active contract (hr.contract) is linked to a Salary Structure, a Working Schedule, and a list of allowed Work Entry Types (WORK100, WORK110 OT, WORK200 Teaching Hours, LEAVE100 Paid Leave, LEAVE120 Unpaid, LEAVE300 Public Holiday, etc.).
3.4.2 The Core Payroll Pipeline (Standard Stages)
Once configuration is complete, Odoo structures every monthly payroll cycle into five sequential states tracked on the Payslip record (hr.payslip):
[ Draft ] ➔ [ Waiting ] ➔ [ Done ] ➔ [ Paid ] ➔ [ Cancelled (optional) ]
Stage 1: Draft (Batch Generation)
* Objective: Bulk creation of payslips for the payroll period.
* Key Functionality:
   * Payslip Batch (hr.payslip.run): HR creates a single batch (e.g., "Payroll October 2026") with a date range. From the batch, the "Generate Payslips" wizard automatically creates one payslip per active employee in scope — selecting the correct Salary Structure per contract.
   * Work Entry Consumption: Each payslip automatically pulls all validated work entries falling within its period — replacing the AS-IS manual reconciliation between OneDrive Excel, Google Forms, and Zoom logs with a single source of truth.
   * Input Lines (hr.payslip.input): One-time adjustments (commission, KPI bonus, advance, penalty, referral bonus) are added as input lines either manually by HR or imported in bulk via CSV.
Stage 2: Waiting / Verify (Computation & Review)
* Objective: Apply salary rules and review the calculated result before approval.
* Key Functionality:
   * Compute Sheet: Odoo executes all Salary Rules in sequence, producing the payslip lines — Gross, allowances, OT, insurance contributions (with caps applied automatically), PIT (with progressive bracket calculation), and Net. The full breakdown is visible on the Salary Computation tab of each payslip.
   * Variation Report: A side-by-side comparison between the current month and the previous month flags unusual variations (e.g., Net dropped by more than 20%) — helping HR catch errors before approval.
   * Rule Trace: For any line, HR can drill down into the rule expression and intermediate variables — providing the complete audit trail absent in the AS-IS Excel approach.
Stage 3: Done (Approval & Locking)
* Objective: Finalize the payslip and lock the underlying work entries.
* Key Functionality:
   * Multi-level Approval: Configurable two-step approval (HR Officer → HR Manager, optionally → BoD for high-value payslips). Each approval action is recorded in the Chatter with timestamp and user identity.
   * Work Entry Lock: When a payslip moves to Done, all consumed work entries transition to state payslip_included — they can no longer be edited unless the payslip is explicitly reset to draft by an HR Manager, with the reason captured in an audit log.
   * Accounting Entry Generation: A draft accounting move is automatically created in the Accounting module, posting salary expense to the appropriate cost center, mandatory insurance and PIT to the corresponding liability accounts, and Net Salary as the payable to employee. This single integration eliminates the AS-IS Excel-MISA disconnect entirely.
Stage 4: Paid (Payment Execution)
* Objective: Execute bank transfers and distribute payslips.
* Key Functionality:
   * Bank File Generation: Odoo generates the bulk payment file in the format required by the corporate bank (VCB, Techcombank, BIDV…) — using per-bank templates configured during implementation. The file is downloaded by Finance and uploaded to the bank's corporate portal.
   * Payslip PDF & Email: Each payslip is automatically rendered as a Vietnamese-compliant PDF and dispatched to the employee via a templated email — eliminating the manual Word-to-PDF copy-paste cycle and the risk of sending the wrong payslip to the wrong person.
   * Employee Portal: Every employee can log into the Odoo Portal to view their full payslip history, download PDFs on demand, and request salary confirmation letters — eliminating the recurring HR workload of handling 10–15 manual payslip requests per month.
Stage 5: Statutory Filing (Parallel Track)
* Objective: Submit mandatory contributions and tax declarations to authorities.
* Key Functionality:
   * BHXH Contribution Report: Odoo aggregates monthly mandatory insurance contributions (employee + employer portions) by employee and generates the report in the iBHXH-compatible format for submission to the Social Insurance Authority.
   * PIT Withholding Declaration: Monthly PIT withholding is exported in the eTax-compatible format for submission to the Tax Authority.
   * Year-End PIT Finalization (Form 05/QTT-TNCN): At year-end, Odoo aggregates 12 monthly payslips per employee automatically — producing the finalization report in minutes instead of the 3–5 days required by the AS-IS manual aggregation.
3.4.3 Payslip Status and Health Indicators
Each payslip card features color-coded indicators to help HR prioritize:
* 🟢 Green (Computed Cleanly): All work entries are validated, no conflicts, no missing inputs — ready for approval.
* 🟡 Yellow (Needs Attention): Variation from previous month exceeds threshold, or a manual input has been added but not yet reviewed.
* 🔴 Red (Blocked): Underlying work entries are in conflict state, contract is missing or expired, or a required rule input cannot be computed — payslip cannot move to Done until resolved.
3.4.4 Cross-Module Integration
Payroll's value comes from its deep integration with every other HR module:
* From Attendance: Validated check-in/check-out hours flow through Work Entry into the BASE rule and OT rule automatically.
* From Time Off: Approved leave requests generate LEAVE-type work entries, which the salary rules consume to apply paid-leave preservation or unpaid-leave deduction without any manual adjustment.
* From Contracts: Wage, allowances, salary structure, and probation flag (85% rate) are read directly from the active contract version — no re-entry needed.
* From Recruitment: When a candidate is hired and the "Create Employee" action is triggered, an initial contract is drafted, immediately enabling the new hire to appear in the next payroll batch with a pro-rata calculation based on actual joining date.
* To Accounting: Salary expense, insurance liabilities, PIT liabilities, and net-payable journal entries post automatically — closing the Excel-MISA gap forever.
3.4.5 Alternative Paths & Special Cases
The standard workflow handles all common deviation scenarios out of the box:
* Payslip Cancellation / Reset: If an error is discovered after approval, the HR Manager can reset a payslip to draft. The action is logged in the Chatter with a mandatory justification, all consumed work entries are unlocked, and a corrected payslip can be issued.
* Pro-rata Mid-month Hires & Departures: When a contract starts or ends mid-period, Odoo applies the proration formula base_salary × (worked_days / standard_working_days) automatically — no manual calculation required.
* Net-to-Gross Computation: For employees whose offer was agreed in Net (typical for senior teachers and foreign instructors), the salary structure includes a Net-to-Gross reverse calculation rule, eliminating the AS-IS iterative Excel guesswork.
* 13th-month Salary & Tet Bonus: A separate "Bonus Payslip" can be generated using a dedicated structure — keeping the bonus tracked distinctly while still being included in the year-end PIT finalization.
* Refusal & Re-issue: At any step before "Paid", the payslip can be refused with a documented reason, sent back to HR for correction, and re-processed — providing the same kind of structured rejection mechanism that the Recruitment module offers for applicants.
  

3.5 Standard Time off Workflow in Odoo
The standard Time Off module on the Odoo platform provides a centralized and fully automated leave management workflow throughout the entire leave data lifecycle:
[ EMPLOYEE CREATES LEAVE REQUEST ]
                ↓
[ ODOO TIME OFF ]
- Quota Validation
- Approval Workflow
- Calendar Synchronization
- Leave Balance Update
                ↓
[ HR & PAYROLL OUTPUT ]
- Payroll Work Entries
- Leave Reports
- Remaining Leave Balance


  

Leave Request Submission
Employees:
* Log in to the Odoo system
* Access the Time Off module
* Select the leave type
* Choose start and end dates
* Enter the leave reason
* Upload supporting documents (if required)
Then click:
* Submit to Manager
Approval Workflow
Depending on the system configuration:
* Direct Manager
* HR Officer
* HR Manager
will receive approval notifications.
The system supports the following approval actions:
* Approve
* Refuse
* Second Approval
Automated Data Processing (Odoo Core Logic)
* Leave Quota Validation
The system automatically:
* Calculates remaining leave balances
* Prevents requests exceeding leave quotas
* Automatically deducts leave balances after approval


* Work Calendar Synchronization
Once approved, leave requests are automatically:
* Synchronized with the Calendar module
* Generated as Work Entries
* Linked to the Payroll system


* Automatic Leave Accrual
Odoo supports:
* Accrual Plans
* Carry-over policies
* Automatic leave allocation by month or year
Payroll Output
Approved leave data is transferred to:
* Payroll
* Work Entries
to support:
* Salary calculation
* Unpaid leave deductions
* HR reporting
CHAPTER 4 — GAP ANALYSIS
I.  Module Employee
4.1. GAP Analysis Matrix
Gap table:

GAP Code
	Business Requirements (Hoc Ba)
	Out-of-the-Box Features (Odoo 19)
	Classification
	Priority
	Technical Solution
	G-01
	Validate Citizen ID (CCCD) format to ensure exactly 12 digits.
	identification_id (Free-text field, no validation error handling).
	VN Legal
	Low
	CFG-001: Configure Regex ^\d{12}$ to block data entry errors.
	G-02
	Store Employee Citizen ID (CCCD) Date of Issue.
	No dynamic field available.
	VN Legal
	High
	CUS-001: Customize and extend x_id_date_issue field into the Private Tab.
	G-03
	Store Employee Citizen ID (CCCD) Place of Issue.
	No dynamic field available.
	VN Legal
	High
	CUS-001: Customize and extend x_id_place_issue field into the Private Tab.
	G-04
	Manage Personal Income Tax (PIT) codes for Teachers/Staff.
	No dedicated field available.
	VN Tax Legal
	High
	CUS-002: Customize x_pit_code field to serve as Master Data for the upcoming Payroll app.
	G-05
	Select 3-tier Vietnamese administrative addresses (Province/District/Ward).
	Only 2 standard tiers available (State/City).
	VN Admin
	Medium
	CFG-002: Install the VN administrative hierarchy localization module (l10n_vn_viin_base_ward).
	G-06
	Separate Permanent Address and Temporary Address (for police declaration).
	Odoo aggregates personal addresses into a single address block.
	VN Legal
	Medium
	CUS-001: Add an independent Temporary Address field group within the Private Tab.
	G-07
	Manage Social Insurance Book Number (10 digits).
	No dynamic field available.
	VN SI Legal
	High
	CUS-001: Add x_social_insurance_number field into the Insurance section.
	G-08
	Manage Health Insurance Card Number & Initial Medical Examination Place.
	No dynamic field available.
	VN SI Legal
	Medium
	CUS-001: Add x_health_insurance_number field and Registered Hospital field.
	G-09
	Classify 4 specific personnel groups of Hoc Ba for profile access control.
	employee_type field lacks options for language center categories.
	Hoc Ba Custom
	Low
	CFG-003: Configure additional "Visiting Instructor" option and specific classification Tags.
	G-10
	Manage Chinese language certification levels (HSK 3-6, HSKK) and Foreign Language Pedagogical Certificates.
	Standard Certificate Level storage is not optimized.
	Hoc Ba Custom
	Low
	CFG-004: Configure a professional Skill Types and Skill Levels category tree for Chinese language.
	G-11
	Setup flexible working schedules for Online teachers (to avoid false late/early-out flags).
	Standard working hours are fixed for administrative office shifts.
	Hoc Ba Custom
	Medium
	CFG-005: Configure "Flexible Schedule" within the Working Hours section of the Employee profile.
	G-12
	Manage dependents list (Full Name, Dependent PIT Code, Relationship) for family circumstance deduction.
	No database table (Model) available to store this list.
	VN Tax Legal
	High
	CUS-002: Create a child Model hr.dependent with an One2many relationship linked to the master employee profile.
	

4.2 FIT Analysis


* FIT-001 — Basic Employee Profile (Name, photo, work email, department, job title, direct manager): Fully supported by the Odoo Employee Form. No change required.


* FIT-002 — Organizational Structure for 6 Departments of Hoc Ba: Supported via Departments + Org Chart view. No change required.


* FIT-003 — Passport Tracking (For instructors with foreign elements): The passport_id field is available out-of-the-box. No change required.


* FIT-004 — Remote Digital Contract Signing with Visiting Instructors: Fully integrated via Odoo Sign. No change required.


* FIT-005 — Time Off Management for Full-time Employees (Request, approval, remaining leaves allocation): Fully supported by the Time Off module. No change required.


* FIT-006 — Candidate to Employee Conversion from Recruitment: Supported via 1-click "Create Employee" button. No change required.


* FIT-007 — Employee Self-Service Portal (View payslips, request time off): Available out-of-the-box. No change required.


4.3 Configuration Gap


CFG-001 — Validate 12-digit Citizen ID Format
* Configuration Area: Employees → Employee Profile → identification_id field
* Configuration Details: Utilize system view/UI editing capabilities to apply a Python constraint or a Regular Expression (Regex) validation rule to the field: ^\d{12}$
* Expected Result: If a user inputs fewer or more than 12 digits for the Citizen ID (CCCD), the system will automatically block the action, trigger a red error alert, and prevent the profile from being saved, thereby ensuring strict data cleanliness.
CFG-002 — Integrate a 2-Tier Administrative Hierarchy System (Province and Base-Level Model)
* Configuration Area: Odoo Application System → Extended module l10n_vn_viin_base_ward (The Deployment/Dev team will execute the refactoring of this module's underlying data structure).
* Configuration Details:
   * Database Schema Redesign: Break the legacy 3-tier dependency structure of Odoo Standard (res.country.state (Province) → res.district (District) → res.ward (Ward)). Proceed to completely hide or remove the intermediate District structural layer (res.district).
   * Establish a Flat 2-Tier Hierarchy:
      * Tier 1 (Province / Central-Affiliated City Level): Configure and standardize the new dataset containing exactly 34 provincial-level administrative units (including 28 provinces and 6 municipalities directly under the Central Government following comprehensive mergers).
      * Tier 2 (Base Level - Ward / Commune / Township): All administrative units at the commune, ward, and township levels—after being reorganized under the new population scale metrics—will be configured with a direct link (Many2one relationship) to their governing Province.
   * User Interface (UI/UX): On the Employee Profile (hr.employee → Private Information Tab), under the Permanent Address and Temporary Address sections, the system will only display 2 distinct Dropdown menu fields:
      * Field 1: Select Province/City (Data sourced directly from the new 34 Provinces/Cities master list).
      * Field 2: Select Ward/Commune/Township (The system automatically filters base-level units directly managed by the selected Province).
* Expected Result:
   * The system operates in a streamlined manner, optimizing data entry for the HR department (requiring only two dropdown selections to complete an address), and completely eliminating the overlap of the intermediate District layer.
   * Ensures that the Employees module Master Data stays one step ahead and aligns 100% with the Government's administrative management roadmap, preventing data extraction from becoming obsolete during legal and compliance procedures.


4.4 Customization gap
CUS-001 — Develop Vietnam HR Legal Extension Module (l10n_vn_hr_employee)
* Objective: Append mandatory information fields to ensure compliance with the Vietnam Labor Law regulations.
* Code Solution: Initialize a new custom module that inherits from Odoo's native hr.employee object. Design a dedicated data section named "Legal & Insurance Information" located within the Private Information Tab to store the following additional fields:
   * x_id_date_issue (Data Type: Date - Citizen ID Date of Issue).
   * x_id_place_issue (Data Type: Many2one linked directly to the Province/City master list - Citizen ID Place of Issue).
   * x_social_insurance_num (Data Type: Char - Social Insurance Book Number).
   * x_health_insurance_num (Data Type: Char - Health Insurance Card Number).
CUS-002 — Develop Dependents Management Feature (hr.dependent)
* Objective: Build a foundational data model to manage family relations, serving as the basis for Personal Income Tax (PIT) family circumstance deduction calculations.
* Code Solution:
   * Define and create an independent data Model named hr.dependent containing the following mandatory fields: Dependent Full Name, Date of Birth, Dependent PIT Code, Relationship (Child, Parent, Spouse), Deduction Start Date, and Deduction End Date.
   * Establish a record linkage from this new Model to the native hr.employee Model via a One2many relational field.
   * Configure the User Interface (UI) to allow HR users to click the "Add a line" button directly on the employee profile view to rapidly declare the associated dependents list.
  

To-be process
II. Module Attendance
4.1 GAP Analysis Matrix for Recruitment Module


GAP Code
	Process / Business Requirement
	Standard Odoo 19 Solution
	Assessment
	System Handling Direction
	G-ATT-05
	Control lateness, early leave discipline, and a minimum 8-hour daily duration for office staff.
	Automatically records timestamps and calculates total actual hours. Supports warning flags.
	FIT / Config
	Maintain Odoo standards. Configure parameters for quota control.
	G-ATT-06
	Automatically generate Check-in/Check-out data for online teachers based directly on the completion status of the Teaching Schedule.
	Standard Odoo requires manual physical interaction (clicking a button or scanning a code) to generate attendance data. No automated link to the teaching schedule.
	GAP
	Develop custom source code for automated extension (CUS-ATT-001).
	G-ATT-07
	Limit attendance boundaries, block office network IPs, and capture GPS coordinates to prevent fraudulent clock-ins when working outside.
	Odoo only supports IP locking for the shared Kiosk Mode screen. The personal Web interface allows attendance logging from any network environment.
	GAP
	Develop custom source code for location extension (CUS-ATT-002).
	G-ATT-08
	Reconcile actual attendance data for the Collaborator (CTV) block based on a flexible weekly shift registration sheet.
	Standard Odoo only supports referencing a fixed working schedule attached to the Profile; it does not support flexible weekly shift changes.
	GAP
	Develop a weekly registered shift management and reconciliation module (CUS-ATT-003).
	

4.2 FIT Analysis (Standard Odoo)
4.3 CONFIGURATION GAP (Configuration Only)
CFG-ATT-003 — Setting up Working Schedules
* Configuration Path: Employees -> Configuration -> Working Schedules
* Setup Details:
   * Office Schedule: Configure a fixed Standard Hours type from Monday to Friday (Morning: 08:30 – 12:00, Afternoon: 13:00 – 17:30). Activate the Late Tolerance property of 15 minutes, allowing employees to Check-in before 08:45 without being counted as late. Activate the Count Extra Hours property after 18:00 daily.
   * Teacher Schedule: Configure a Flexible Hours type and set the weekly mandatory quota to 0.0 hours. The purpose is to completely remove Odoo's administrative lateness scanning mechanisms for the teaching bloc, laying the groundwork for importing clean work hours based on actual class durations.
   * Collaborator (CTV) Schedule: Configure a Shift-Based / Scheduled Shifts type to manage shifts allocated flexibly on a weekly basis.


4.4 CUSTOMIZATION GAP (Development Required)
* CUS-ATT-001: Process to automatically record attendance from Academic Classes (Teachers Block)
   * Standard Odoo Limitation: Requires users to manually interact to generate attendance logs.
   * Custom Solution: Program an automated background handler (Event Listener) to link the Attendance module with the online class management module (academic.session). When an online class ends and the academic coordinator changes the class record status to "Completed", the system automatically triggers a process to generate a clean hr.attendance record for the assigned teacher with precise timestamps: check_in = actual_start_time and check_out = actual_end_time. This process completely eliminates manual entry, automatically accumulating teaching hours for payroll processing.
* CUS-ATT-002: Module to control and limit attendance perimeters (GPS & IP Lock)
   * Standard Odoo Limitation: Does not support capturing location or blocking IPs for individual accounts clocking in via the Webapp interface.
   * Custom Solution: Extend the source code of the Check-in/Check-out button interface by embedding a JavaScript positioning library (navigator.geolocation). Build a configuration table for Học Bá Center's Center Coordinates (Latitude, Longitude) and the valid corporate Wi-Fi IP range. When an employee logs attendance, the system runs a check in the background. If the device is outside the allowed radius (e.g., $> 100$ meters), the system blocks standard data saving and forces a Pop-up window to appear, requiring the employee to select a reason category (Working From Home - WFH, Business Trip, Meeting Partner/Student) and enter a detailed text explanation before allowing the attendance log to be committed to the database with an "Outside Location" flag for easy HR reviewing.
* CUS-ATT-003: Module to Reconcile Registered Rotating Shifts (Collaborator Bloc)
   * Standard Odoo Limitation: Lacks features to reconcile real-time attendance logs against a flexible weekly rotating shift schedule.
   * Custom Solution: Build a new data model named ctv.shift.register allowing collaborators to freely register their shift schedules week by week. When a collaborator performs a Check-in or Check-out action, the system executes an SQL query to match the actual timestamp with that user's weekly registered shift frame. If the actual attendance time deviates from the shift or falls outside the registered window by more than a 30-minute tolerance, the system automatically flags a shift exception error for direct managers to handle, preventing collaborators from overstaying their shifts to exploit hourly wages.






  

To-be process

III. Module Payroll
4.1 GAP Analysis Matrix for Payroll Module
Process
	Business Need
	Odoo Standard
	GAP Level
	Solution
	Monthly Payslip Generation
	Generate monthly payslips for Office Staff with fixed salary, allowances, and deductions.
	Fully supported by Payroll module with automatic payslip creation and computation.
	None (FIT)
	FIT-PR-001: Use standard Payroll module without modification.
	Salary Structure Engine
	Configure salary computation logic with rules for base, allowances, OT, insurance, and tax.
	Supported via hr.payroll.structure and hr.salary.rule with Python expressions.
	None (FIT)
	FIT-PR-002: Leverage Odoo's built-in salary rule engine.
	Payslip Batch Processing
	Bulk-create payslips for all employees in a payroll period in one action.
	Fully supported by hr.payslip.run with "Generate Payslips" wizard.
	None (FIT)
	FIT-PR-003: Use standard Payslip Batch feature.
	Accounting Integration
	Automatically post salary expense, insurance, and tax entries to the Accounting module.
	Native integration generates draft accounting moves when payslip moves to Done state.
	None (FIT)
	FIT-PR-004: Use native Payroll-Accounting integration.
	Employee Payslip Portal
	Employees can view their payslip history and download PDFs anytime.
	Fully supported via Employee Portal with self-service access.
	None (FIT)
	FIT-PR-005: Activate Employee Portal access.
	Payslip Audit Trail
	Track every change to payslip data with timestamp, user, and reason.
	Standard Chatter mechanism logs all state transitions and modifications.
	None (FIT)
	FIT-PR-006: Use standard Chatter audit log.
	Pro-rata Calculation
	Calculate prorated salary for mid-month hires and departures.
	Automatic worked-days ratio applied via base × (worked_days / standard_days).
	None (FIT)
	FIT-PR-007: Use built-in pro-rata mechanism.
	Multi-block Salary Structures
	Apply different salary calculation logic for Office Staff, Teachers/TA, and Collaborators.
	Standard Odoo allows multiple structures but requires manual configuration per block.
	Low
	CFG-PR-001: Configure 3 separate salary structures for Học Bá's personnel blocks.
	Vietnamese Mandatory Insurance
	Apply BHXH/BHYT/BHTN contributions with VN-specific caps and rates.
	Generic insurance rules available but VN-specific caps (20× base salary, 20× regional minimum wage) require parameterization.
	Medium
	CFG-PR-002: Configure VN insurance rules with parametric caps and rates.
	Personal Income Tax (PIT)
	Calculate PIT using Vietnam's 7-tier progressive bracket system.
	Bracket-based tax rules supported but VN-specific brackets must be configured.
	Medium
	CFG-PR-003: Configure 7-tier PIT brackets per Resolution 954/2020/UBTVQH14.
	Personal & Dependent Deductions
	Apply 11M VND personal deduction and 4.4M VND per dependent for PIT calculation.
	Configurable deduction parameters supported.
	Medium
	CFG-PR-004: Configure personal and dependent deduction parameters.
	Probation Salary
	Apply 85% wage rate during probation period per VN labor law.
	Standard wage rule supports multipliers but probation logic requires configuration.
	Low
	CFG-PR-005: Configure probation flag and 85% rate rule.
	Holiday Overtime Rate
	Apply 300% rate for work performed on public holidays per VN Labor Code Article 98.
	Standard OT multiplier configurable, but separate work entry type for holiday OT needed.
	Low
	CFG-PR-006: Configure WORK110_OT_HOLIDAY with 300% multiplier.
	Hourly-rate Teacher Salary
	Calculate teacher salary based on validated teaching hours × per-employee hourly rate.
	No native rule for hourly wage based on validated teaching hours with per-employee variable rate.
	High
	CUS-PR-001: Develop custom module hb_payroll_teaching_hours for hourly salary computation.
	Net-to-Gross Calculation
	Compute Gross salary from negotiated Net target for senior teachers and foreign instructors.
	Odoo computes Gross → Net only; no reverse iterative calculation.
	High
	CUS-PR-002: Develop custom Net-to-Gross wizard hb_payroll_net_to_gross.
	Vietnamese Bank Payment File
	Generate bulk payment file in VCB and Techcombank-specific format.
	Only SEPA XML format (European standard) supported natively.
	High
	CUS-PR-003: Develop custom module hb_payroll_vn_bank_files with per-bank templates.
	BHXH Monthly Report
	Generate monthly social insurance contribution report in iBHXH portal format.
	No native iBHXH-compatible export available.
	High
	CUS-PR-004: Develop custom module hb_payroll_bhxh_report.
	eTax Monthly Report
	Generate monthly PIT withholding declaration in eTax portal format.
	No native eTax-compatible export available.
	High
	CUS-PR-005: Develop custom module hb_payroll_etax_report.
	Year-end PIT Finalization
	Generate Form 05/QTT-TNCN aggregating 12 monthly payslips per employee.
	No native VN year-end finalization report.
	High
	CUS-PR-006: Develop custom module hb_payroll_year_end_pit.
	13th-month Salary & Tet Bonus
	Calculate 13th-month bonus with year-aware proration for partial-year employees.
	Standard bonus is single-period only without year-aware logic.
	Medium
	CUS-PR-007: Develop custom module hb_payroll_13th_month.
	Multi-bank Account Split
	Allow salary distribution across multiple bank accounts by percentage.
	Native Odoo supports single primary bank account only.
	Low
	CUS-PR-008: Develop custom module hb_payroll_multi_bank (defer to Phase 3).
	Variation Report
	Compare current month payslip against previous month to detect anomalies.
	No native side-by-side variation comparison report.
	Medium
	CUS-PR-009: Develop custom dashboard hb_payroll_variation_report.
	Sales Commission Integration
	Auto-import monthly commission from CRM closed deals for Sales consultants.
	Manual input via payslip input lines supported; no CRM integration.
	Medium
	CUS-PR-010: Develop custom module hb_payroll_sales_commission (defer to Phase 3).
	

4.2 FIT Analysis (Standard Odoo)
FIT-PR-001
* Requirement: Generate monthly payslips automatically for Office Staff with fixed salary, allowances, OT, and standard deductions.
* Odoo Support: The Payroll module supports complete payslip generation through the standard hr.payslip workflow. HR creates a Payslip Batch, the system auto-creates one payslip per active employee in scope, applies the assigned Salary Structure, and computes Gross → Net.
* No change required: Use Odoo's standard payslip generation workflow without modification.
FIT-PR-002
* Requirement: Configure flexible salary computation logic with atomic rules for base wage, allowances, overtime, mandatory insurance, and tax brackets.
* Odoo Support: hr.payroll.structure (the salary structure container) and hr.salary.rule (atomic computation units written as Python expressions) provide complete flexibility. Each rule references inputs, contract fields, and previous rule outputs.
* No change required: Use Odoo's built-in salary rule engine to define all computation logic.
FIT-PR-003
* Requirement: Bulk-process payslips for all employees in a payroll period within a single transaction to reduce HR effort.
* Odoo Support: hr.payslip.run (Payslip Batch) allows HR to create a single batch (e.g., "Payroll October 2026") with a date range. The "Generate Payslips" wizard automatically creates one payslip per employee in scope and pulls all validated work entries.
* No change required: Use the standard Payslip Batch feature for monthly processing.
FIT-PR-004
* Requirement: Eliminate the manual re-entry of payroll data into the accounting software by posting salary expenses, mandatory insurance, and PIT entries automatically.
* Odoo Support: When a payslip moves to the Done state, Odoo automatically creates a draft accounting move posting salary expense to the appropriate cost center, mandatory insurance and PIT to the corresponding liability accounts, and Net Salary as the payable to employee.
* No change required: Activate the standard Payroll-Accounting integration. This single integration eliminates the AS-IS Excel-MISA disconnect (PP-PR-01) entirely.
FIT-PR-005
* Requirement: Provide employees with self-service access to view their historical payslips and download PDFs without contacting HR.
* Odoo Support: The Employee Portal allows every employee to log in, view their full payslip history, download PDFs on demand, and request salary confirmation letters — all without HR intervention.
* No change required: Activate Employee Portal access for all employees. Eliminates the recurring HR workload of handling 10–15 manual payslip requests per month (PP-PR-10).
FIT-PR-006
* Requirement: Track every modification to payroll data with full audit trail including user identity, timestamp, and reason for changes.
* Odoo Support: The standard Chatter mechanism logs every state transition (Draft → Verify → Done → Paid), user identity, timestamp, and IP for each action, as well as reason and justification for resets or cancellations and all input adjustments with full history.
* No change required: Use standard Chatter audit log functionality. Fully addresses the AS-IS audit gap (PP-PR-04).
FIT-PR-007
* Requirement: Calculate prorated salary automatically for employees who join or leave mid-month without manual Excel adjustment.
* Odoo Support: When a contract starts or ends mid-period, Odoo applies the proration formula base_salary × (worked_days / standard_working_days) automatically through the worked-days ratio computed by the Work Entry layer.
* No change required: Use the built-in pro-rata mechanism.


4.3 CONFIGURATION GAP (Configuration Only)
CFG-PR-001
* Requirement: Configure three distinct salary calculation logics matching Học Bá's personnel structure: Office Staff (fixed monthly), Teachers/TA (hourly), and Collaborators (per-task).
* Odoo Configuration Area: Payroll → Configuration → Salary Structures
* Configuration Detail: Create three separate salary structures. The Office Staff Structure contains rules for BASE (from contract wage), ALLOW_LUNCH, ALLOW_TRANSPORT, ALLOW_PHONE, ALLOW_POSITION, ALLOW_SENIORITY, OT, KPI_BONUS, COMMISSION, BHXH, BHYT, BHTN, PIT, and NET. The Teacher Structure contains TEACH_HOURS (hourly_rate × validated teaching hours), FIXED_BASE (optional), EXTRA_HOURS_BONUS, HOLIDAY_OT, plus standard insurance and tax rules. The Collaborator Structure contains TASK_PAY, SHIFT_PAY, and a lightweight PIT rule. Each active contract is assigned to the matching structure based on the personnel category.
* Expected Result: Each personnel block is calculated according to its own logic — the AS-IS problem of trying to standardize all blocks in one Excel template (PP-PR-02) is fully eliminated.
CFG-PR-002
* Requirement: Configure Vietnam-specific mandatory insurance contributions with proper rates and caps for BHXH, BHYT, and BHTN.
* Odoo Configuration Area: Payroll → Configuration → Salary Rules + Salary Rule Parameters
* Configuration Detail: Configure three insurance rules with VN-specific caps as parameters (not hardcoded). BHXH applies Employee 8% and Employer 17.5% capped at 20× the base salary reference (currently 20 × 2,340,000 = 46,800,000 VND). BHYT applies Employee 1.5% and Employer 3% capped at the same BHXH limit. BHTN applies Employee 1% and Employer 1% capped at 20× the regional minimum wage (Zone I: 20 × 4,960,000 = 99,200,000 VND). The insurance base is defined separately from gross — only specific allowances are subject to insurance (BASE, ALLOW_POSITION, ALLOW_SENIORITY), while ALLOW_LUNCH, ALLOW_TRANSPORT, ALLOW_PHONE, and OT are NOT subject to insurance per VN Decree 28/2015/ND-CP.
* Expected Result: When the government adjusts the base salary reference or the regional minimum wage, HR updates the single parameter value — no formula re-coding required across multiple Excel templates (resolves PP-PR-03).
CFG-PR-003
* Requirement: Configure Vietnam's 7-tier progressive Personal Income Tax brackets per Resolution 954/2020/UBTVQH14.
* Odoo Configuration Area: Payroll → Configuration → Salary Rules + Salary Rule Parameters
* Configuration Detail: Configure the PIT salary rule using a parametrized lookup table for the 7 brackets: Bracket 1 (Up to 5,000,000 VND) at 5%, Bracket 2 (5,000,001 – 10,000,000) at 10%, Bracket 3 (10,000,001 – 18,000,000) at 15%, Bracket 4 (18,000,001 – 32,000,000) at 20%, Bracket 5 (32,000,001 – 52,000,000) at 25%, Bracket 6 (52,000,001 – 80,000,000) at 30%, and Bracket 7 (Above 80,000,000) at 35%. Taxable Income = Gross − Insurance (employee portion) − Personal Deduction − Dependent Deduction.
* Expected Result: PIT is calculated correctly for every employee in every payslip; the AS-IS risk of manual bracket lookup errors (PP-PR-03) is fully eliminated.
CFG-PR-004
* Requirement: Apply personal deduction (11M VND) and dependent deduction (4.4M VND per dependent) when calculating Personal Income Tax.
* Odoo Configuration Area: Payroll → Configuration → Salary Rule Parameters + Employee Profile
* Configuration Detail: Configure the Personal Deduction parameter at 11,000,000 VND/month (adjustable when the government updates the figure) and the Dependent Deduction parameter at 4,400,000 VND per registered dependent per month. Dependents must be registered in the Employee Profile under a dedicated Dependents tab — this cross-references G-12 in Module Employee (the hr.dependent model with One2many relationship). Each dependent record contains Full Name, Date of Birth, Dependent PIT Code, Relationship, and Effective Date From/To.
* Expected Result: When an employee registers a new dependent (e.g., new child birth), the deduction is automatically applied from the registered effective date onward, with no manual Excel adjustment.
CFG-PR-005
* Requirement: Apply a 85% salary rate during probation period and handle the transition automatically when an employee converts to official status mid-month.
* Odoo Configuration Area: Payroll → Configuration → Salary Rules + Contract
* Configuration Detail: Add an is_probation boolean field on hr.contract (or use existing contract state). Configure the BASE rule to apply × 0.85 (configurable probation rate parameter) when is_probation = True. Handle mid-month transition automatically by prorating days 1–14 at probation rate and days 15–31 at official rate.
* Expected Result: Probationary employees receive the correctly reduced salary (85%) without manual HR intervention; the transition month is handled correctly.
CFG-PR-006
* Requirement: Apply overtime rate of 300% when work is performed on public holidays per VN Labor Code Article 98.
* Odoo Configuration Area: Payroll → Configuration → Work Entry Types + Salary Rules
* Configuration Detail: Per VN Labor Code Article 98, overtime rates are 150% for normal weekday OT, 200% for weekend OT, and 300% for public holiday OT. Configure separate Work Entry Types (WORK110_OT_NORMAL, WORK110_OT_WEEKEND, WORK110_OT_HOLIDAY) with respective multipliers in the OT salary rule.
* Expected Result: When a teacher conducts a class on Tet, the system automatically applies the 300% multiplier — eliminating the AS-IS scenario where the C&B Specialist had to "remember" to apply the correct rate manually.


4.4 CUSTOMIZATION GAP (Development Required)
CUS-PR-001
* Business Need: Calculate teacher and teaching assistant salaries based on validated teaching hours of the month multiplied by an hourly rate that varies per teacher (based on experience, HSK certification level, and class type). Without this calculation, hourly-paid teachers (the largest workforce block at Học Bá) cannot receive correct salaries — making this the single most critical customization for go-live.
* Standard Limitation: Standard Odoo Payroll supports only fixed-amount or percentage-based salary rules. There is no native rule template that multiplies a configurable per-employee hourly_rate field by the aggregated worked_hours of WORK200 (Teaching Hours) work entries.
* Custom Solution: Develop a custom module hb_payroll_teaching_hours containing an extension of hr.contract with field x_teaching_hourly_rate (Float, VND/hour) and optional fields for tiered rates by class type (x_rate_beginner_class, x_rate_intermediate_class, x_rate_advanced_class, x_rate_hsk_class). Add a new salary rule TEACH_HOURS with the computation sum(work_entries WHERE type=WORK200) × contract.x_teaching_hourly_rate. Add an EXTRA_HOURS_BONUS rule for teaching hours exceeding the contract's standard threshold using an extra hourly rate. Implement validation to prevent payslip computation if any WORK200 entry in the period is still in draft or conflict state.
* Business Benefit: Eliminates the AS-IS bottleneck of cross-reconciling Zoom logs, Google Forms, and class schedules manually (PP-PR-02, PP-PR-12). Teaching salaries are calculated correctly the first time, on time, every month. This single customization recovers 3–5 working days per month for the Academic department.
CUS-PR-002
* Business Need: When negotiating salary with new hires (especially senior teachers and foreign instructors), the offer is often agreed in Net terms (e.g., "20 million VND Net per month"). HR needs to calculate the corresponding Gross such that after deducting insurance and PIT, the Net matches exactly the agreed amount.
* Standard Limitation: Odoo's salary rule engine computes Gross → Net in a forward direction only. There is no native Net → Gross reverse calculation, making it impossible to honor Net-based salary commitments without manual iteration.
* Custom Solution: Develop a custom module hb_payroll_net_to_gross containing a wizard hb.payroll.net.to.gross.wizard that accepts as input: target Net, employee/contract, number of dependents, and insurance base eligibility flags. The wizard implements a backward iterative algorithm: estimate initial Gross, compute forward through insurance and PIT, compare resulting Net to target, adjust Gross, and iterate until convergence (typically 3–5 iterations for VN PIT brackets). For simple cases below the tax threshold, apply the closed-form gross = net / (1 - insurance_rate_employee). Add a flag x_negotiated_in_net on the contract — when checked, the system computes Gross from the stored Net target at the start of each payslip cycle. Output a detailed breakdown showing Net target → Gross → Insurance breakdown → PIT → Net actual.
* Business Benefit: Eliminates the AS-IS error-prone manual iteration in Excel (PP-PR-06). New hire contracts can be issued in either Net or Gross terms confidently, removing a recurring source of contract disputes during the first payroll cycle. Particularly important for retaining senior teachers and foreign instructors who typically negotiate on Net terms.
CUS-PR-003
* Business Need: Học Bá uses Vietcombank (VCB) and Techcombank (TCB) for corporate banking. Each bank requires a specific file format for batch payroll payments (typically XLSX with bank-defined columns), which differs from Odoo's standard SEPA XML format used in Europe. Without this customization, Finance must manually re-format payroll data in Excel templates each cycle.
* Standard Limitation: Odoo Payroll provides only SEPA-compatible payment file generation (European banking standard), which is not accepted by Vietnamese banks. There is no out-of-the-box format support for VCB, TCB, BIDV, MB, or any Vietnamese bank.
* Custom Solution: Develop a custom module hb_payroll_vn_bank_files with a pluggable template architecture — one Python class per supported bank (VCBFormatter, TCBFormatter, with future extensibility for BIDV, MB, ACB). Create a configuration table hb.bank.format storing per-bank metadata including column headers, column order, date format, currency representation, and file encoding (UTF-8 vs ANSI per bank requirement). Add a "Generate Bank File" button on the Payslip Batch that produces one file per bank account currency, downloadable directly from Odoo. Implement validation to prevent file generation if any payslip in the batch is not in "Done" state, or if any employee is missing bank account details.
* Business Benefit: Finance no longer maintains a separate Excel template per bank and re-formats data manually each cycle (PP-PR-08). One-click generation reduces the bank file preparation time from approximately 2 hours to under 5 minutes per month, and removes the risk of formatting errors causing failed bank uploads.
CUS-PR-004
* Business Need: The Social Insurance Authority of Vietnam requires monthly submission of mandatory insurance contributions via the iBHXH portal in a specific XML or Excel format. Currently, Finance re-enters data manually from the payroll Excel into the iBHXH portal — a duplicate-entry process that takes a full working day each month and is error-prone.
* Standard Limitation: Odoo Payroll does not include a Vietnamese BHXH-specific export report. The native social insurance reports are designed for European jurisdictions and do not produce the data structure required by iBHXH.
* Custom Solution: Develop a custom module hb_payroll_bhxh_report containing a new report BHXH Contribution Report that aggregates per employee the BHXH (employee + employer), BHYT (employee + employer), BHTN (employee + employer), insurance base, and contribution period. Export the report in iBHXH-compatible XML format following the specification provided by Vietnam Social Security. Implement a validation step that highlights any employees missing the Social Insurance Book Number (x_social_insurance_number from Module Employee G-07). Maintain a history log of submitted reports per period for audit purposes.
* Business Benefit: Eliminates duplicate data entry between Odoo and iBHXH (PP-PR-08). Reduces monthly statutory filing time from approximately 1 day to 30 minutes and removes the risk of transcription errors leading to insurance compliance issues.
CUS-PR-005
* Business Need: The Tax Authority of Vietnam requires monthly submission of PIT withholding declarations via the eTax portal. Currently, Finance re-enters data manually — a duplicate process that compounds with the iBHXH submission burden.
* Standard Limitation: Odoo Payroll does not include a Vietnamese eTax-specific export report. The native tax withholding reports do not match the format required by the eTax portal.
* Custom Solution: Develop a custom module hb_payroll_etax_report containing a new report PIT Withholding Report that aggregates per employee the monthly taxable income, personal deduction, dependent deduction, PIT withheld, and PIT code (x_pit_code from Module Employee G-04). Export in eTax-compatible XML format. Implement cross-validation with the Dependents list — flagging any inconsistency between declared dependents and applied deductions.
* Business Benefit: Eliminates duplicate data entry between Odoo and eTax (PP-PR-08). Reduces monthly tax filing time and supports automated audit reconciliation, protecting Học Bá from potential PIT compliance issues.
CUS-PR-006
* Business Need: At year-end, HR must generate the PIT finalization report (Form 05/QTT-TNCN) by aggregating 12 monthly Excel files manually. This process is highly error-prone, especially for employees who joined or left mid-year, and typically takes 3–5 working days for HR each January.
* Standard Limitation: Odoo does not include a Vietnamese year-end PIT finalization report template. There is no native aggregation logic for the annual settlement required by Vietnamese tax law.
* Custom Solution: Develop a custom module hb_payroll_year_end_pit containing a wizard hb.payroll.year.end.pit.wizard that accepts as input: fiscal year and employee filter (all/department/individual). The wizard aggregates the sum of 12 monthly taxable incomes, total dependent deductions used, total PIT withheld, total PIT calculated on annual taxable income, and year-end PIT settlement (under-paid or over-paid). Output the Form 05/QTT-TNCN PDF compliant with Circular 80/2021/TT-BTC, plus a per-employee finalization receipt for each individual employee's records.
* Business Benefit: Reduces year-end PIT finalization effort from 3–5 days of manual aggregation to under 1 hour. Provides accurate end-of-year settlements automatically, especially benefiting employees who joined or left mid-year (PP-PR-09).
CUS-PR-007
* Business Need: Học Bá pays a 13th-month salary (Tet bonus) at the end of the lunar year. Employees who worked the full 12 months receive 100%; employees who joined mid-year receive a prorated amount based on months worked. Without automation, calculating this for 50+ employees with varied join dates is a manual Excel exercise prone to disputes.
* Standard Limitation: Standard Odoo bonus configuration is single-period only, not year-aware with proration logic. There is no built-in mechanism for the Tet bonus pattern common in Vietnamese organizations.
* Custom Solution: Develop a custom module hb_payroll_13th_month containing a wizard hb.payroll.13th.wizard to generate 13th-month bonus payslips. Implement the logic bonus = base_salary × (months_worked_in_year / 12) with a configurable proration policy (calendar year vs lunar year, full month vs half month threshold). Handle tax correctly — 13th-month bonus is included in the December payslip's taxable income (per VN tax regulation), not taxed separately. Provide an option to generate a separate "Bonus Payslip" (hr.payslip with structure BONUS_13TH) for distinct tracking, while still being included in year-end PIT finalization.
* Business Benefit: Eliminates manual Excel calculation for 50+ employees with varied join dates. Ensures correct tax treatment per VN regulation and provides clear audit trail for HR and Finance. Reduces Tet bonus processing from 1–2 days to under 30 minutes.
CUS-PR-008
* Business Need: Some employees (especially senior teachers) request their salary to be split across multiple bank accounts by percentage — for example 70% to a primary account for daily expenses and 30% to a savings account at another bank.
* Standard Limitation: Native Odoo supports only a single primary bank account per employee for salary payment.
* Custom Solution: Develop a custom module hb_payroll_multi_bank containing an extension of hr.employee with One2many field bank_account_distribution_ids linking to a new model hr.employee.bank.account.distribution with fields bank_account_id and percentage. Implement validation that the total percentage across all distributions equals 100%. Modify the Bank File Generation logic (CUS-PR-003) to read the distribution table and generate one row per (employee × bank account) in each bank's file.
* Business Benefit: Supports flexible employee preferences for salary distribution. Low priority — recommended for Phase 3 only if 5+ employees actively request this feature.
CUS-PR-009
* Business Need: Before approving a monthly payroll, HR should detect any unusual variations compared to the previous month (e.g., an employee's Net dropping by more than 20% may indicate a data error or missing input). Without this, errors are only caught after employees receive payslips and complain.
* Standard Limitation: Odoo does not provide a built-in variation comparison report between consecutive payroll periods.
* Custom Solution: Develop a custom module hb_payroll_variation_report containing a new dashboard view Payslip Variation that shows for each employee in the current batch the Net previous month, Net current month, absolute delta, and percentage delta. Apply color-coded indicators: 🔴 if |delta| > 20%, 🟡 if 10–20%, 🟢 if < 10%. Implement one-click drill-down: clicking an employee row shows the full rule-by-rule comparison between the two payslips. Provide Excel export for offline review by Finance.
* Business Benefit: Catches data errors before the payslip is approved and the bank file is sent, preventing the embarrassment of correcting paid salaries. Adds a proactive quality gate to the monthly cycle.
CUS-PR-010
* Business Need: Học Bá's Admissions Consulting (Sales) staff receive monthly commission based on the number and value of closed enrollments. Currently, the Sales Manager sends a commission file to HR each month for manual import into the payroll Excel — a process that depends on timing and accuracy of the Sales report.
* Standard Limitation: Odoo Payroll has no native link to the CRM/Sales modules for automated commission ingestion. Manual data entry via Payslip Input lines is supported but tedious for 10+ consultants each month.
* Custom Solution: Develop a custom module hb_payroll_sales_commission with a scheduled action (cron) that aggregates closed deals per consultant per month from CRM (crm.lead with stage = "Won"). Implement a configurable commission rule per consultant (percentage of revenue / fixed amount per deal / tiered structure). Auto-create hr.payslip.input line COMMISSION on each consultant's payslip with the computed amount. Provide a review screen where the Sales Manager validates the commission list before HR generates the payslips.
* Business Benefit: Eliminates the manual file exchange between Sales and HR each month (part of PP-PR-05). Ensures commission accuracy and provides a single source of truth tied directly to CRM deals. Recommended for Phase 3, after the CRM module rollout.
  

To-be process

IV. Module Recruitment
4.1 GAP Analysis Matrix for Recruitment Module
Process
	Business Need
	Odoo Standard
	GAP Level
	Solution
	Job Vacancy Posting
	Post recruitment vacancies for Teachers and Consultants directly onto the organization's official website.
	Job Positions seamlessly sync with the Odoo Website application to publish listings.
	Low
	Install the Odoo Website module and configure the dedicated "Careers" page.
	Recruitment Pipeline Management
	Visually track candidate progress through customized stages: Received, Shortlisted, Interview, Proposal.
	Kanban view displays applicant cards moving flexibly across pre-defined stage columns.
	Low
	Rename and create new Stages standardized to match internal recruitment workflows.
	Applicant Communication
	Automatically send notification emails when a candidate's application status transitions to another stage.
	Supports automated email triggers based on Kanban Stage movement actions.
	Low
	Configure customized Email Templates reflecting Hoc Ba's distinctive brand identity.
	Pre-screening Assessment
	Distribute Chinese language proficiency or situational judgment test forms to applicants.
	The "Interview Survey" feature links with the Survey application for automated testing.
	Low
	Activate "Interview Survey" in Recruitment Settings and design the digital question banks.
	Interview Scheduling
	Schedule interviews, verify the availability of the interviewer panel, and dispatch calendar invites.
	The Recruitment module directly syncs with the system's global Calendar application.
	None (FIT)
	Directly utilize standard out-of-the-box features without any system modification.
	Applicant Data Storage
	Centrally archive all CVs, profiles, and historical communication logs of applicants.
	Applicant Cards support unlimited tệp attachments and comprehensive tracking via Chatter.
	None (FIT)
	Leverage standard applicant database management structures directly.
	Analytical Reporting
	Generate reports on applicant volume trends over time and the conversion efficiency of each channel.
	Provides out-of-the-box Recruitment Reporting with multi-dimensional metrics (Pivot, charts).
	None (FIT)
	Utilize Odoo's default visual reporting dashboards and metrics.
	Local Job Portal Integration
	Automatically synchronize CVs submitted from Vietnamese recruitment platforms (e.g., TopCV, VietnamWorks).
	Mặc định only supports native API integration with the international professional network LinkedIn.
	Medium
	Develop custom API/Webhook integrations or provision Odoo's incoming Email Alias mechanism.


	4.2 FIT Analysis (Standard Odoo)
FIT-001
* Requirement: Schedule interview appointments for candidates, automatically cross-check and synchronize with the interviewer panel's calendar availability, and dispatch confirmation emails.
* Odoo Support: The "Schedule Interview" functionality integrates tightly with the native Calendar application, allowing the seamless creation of online or in-person meetings while instantly logging the event details on the applicant's card.
* No change required: The operational workflow coordination between HR and functional departments remains completely unchanged, following the standard out-of-the-box mechanism of the Odoo platform.
FIT-002
* Requirement: Centrally store candidate resumes, background profiles, attached files (CVs, academic transcripts, HSK Chinese language certificates), and all interaction histories throughout the recruitment lifecycle.
* Odoo Support: Each candidate is represented by a unique Applicant Card that allows unlimited document attachments and continuously logs detailed communication history, internal notes, and status updates via the Chatter log.
* No change required: Directly utilize the default data schemas and document models provided by the standard Odoo Recruitment module.
FIT-003
* Requirement: Export analytical reports to evaluate the conversion performance of various recruitment communication channels and calculate the average time-to-fill for vacant positions.
* Odoo Support: The built-in "Recruitment Reporting" dashboard features robust source-tracking filters, visually illustrating applicant conversion trends through bar graphs, pie charts, or multi-dimensional Pivot tables.
* No change required: Deploy the standard analytical reporting interface without any modifications to the core data calculation logic or structures.
4.3 CONFIGURATION GAP (Configuration Only)
CFG-001
* Requirement: Establish an online job portal on the center's public website to automatically capture job applications from external job seekers.
* Odoo Configuration Area: Settings / Recruitment Module / Website Module
* Configuration Detail: Install the Website application and toggle on the "Online Posting" option within Recruitment Settings. Design the user interface of the careers page to display active Job Positions and link the "Apply Now" CTA button directly to the applicant data ingestion form.
* Expected Result: As soon as a job position is set to "Published", external candidates can apply online; the system instantly generates a corresponding applicant card inside the backend Recruitment module.
CFG-002
* Requirement: Configure a visual drag-and-drop Recruitment Pipeline that precisely maps to Hoc Ba's current 7-step candidate screening process.
* Odoo Configuration Area: Recruitment -> Configuration -> Stages
* Configuration Detail: Modify and expand the default stage columns to establish the new standardized funnel: 1. Application Received -> 2. CV Screening -> 3. Proficiency Test -> 4. Technical Interview -> 5. Compensation Proposal -> 6. Offer Letter Signing -> 7. Probation (Onboarding).
* Expected Result: The Kanban board interface correctly populates the entire operational flow, enabling HR staff to seamlessly categorize and progress candidates using intuitive drag-and-drop actions.
CFG-003
* Requirement: Automatically trigger progress update emails to applicants the moment their profile is successfully moved to a subsequent recruitment stage.
* Odoo Configuration Area: Recruitment Stages / Email Templates configuration
* Configuration Detail: Bind an automated "Email Template" directly to the definition of each specific Kanban Stage. Draft and format the template contents (e.g., Interview Invitation, Test Notification, Thank You Letter) embedded with dynamic placeholders (e.g., Candidate Name, Scheduled Time, Job Position).
* Expected Result: When an HR officer slides an applicant card into the "Technical Interview" column, Odoo autonomously dispatches a detailed schedule notification email, eliminating the need to manually draft individual messages.
CFG-004
* Requirement: Automate the distribution and evaluation of teaching proficiency screening surveys for Teachers and situational judgment assessments for Sales Consultants.
* Odoo Configuration Area: Recruitment Settings -> Interview Forms linked with the Survey Application
* Configuration Detail: Enable the "Interview Survey" option in the general configuration of the Recruitment module. Switch to the Survey app to construct dedicated question banks containing multiple-choice and open-ended text questions, then link this survey form to the respective Job Position records.
* Expected Result: Odoo automatically generates a unique tokenized survey link and delivers it via email to candidates reaching the testing phase, records their online submissions, and logs the final scores directly into the candidate's master profile.








4.4 CUSTOMIZATION GAP (Development Required)
CUS-001
* Business Need: Automatically aggregate incoming application data streams from popular domestic job portals in Vietnam (such as TopCV or VietnamWorks) into a single centralized database to completely eradicate manual data fragmentation.
* Standard Limitation: Standard Odoo (including the Enterprise edition) only provides pre-built API connectors for the international professional network LinkedIn, entirely lacking standard out-of-the-box integration integrations for localized Vietnamese job boards.
* Custom Solution: Develop an odoo custom module to expose an API/Webhook endpoint on the Odoo server. This endpoint will listen for structural JSON data payloads pushed from the employer accounts of TopCV/VietnamWorks whenever a candidate submits an application. The custom script will parse critical payload fields (Full Name, Phone Number, Email, Attached CV file) to automatically map and instantiate a new Applicant record within Odoo Recruitment. (Note: To manage Phase 1 implementation costs, if this feature is deferred to a future phase, the temporary configuration workaround is to configure Odoo's standard incoming Email Alias feature to parse CV notifications forwarded from the job boards).
* Business Benefit: Frees the HR department from the daily administrative chore of manually downloading CV files to local storage and typing candidate information into disconnected Excel spreadsheets. This significantly cuts down candidate response times, eliminates the risk of losing high-potential resumes, establishes a robust corporate Talent Pool, and dramatically improves Hoc Ba Center's organizational professionalism in the competitive job market.
  

To-be-process
V. Module Time off
4.1 GAP Analysis Matrix for Recruitment Module
ID
	Requirement
	Odoo Standard
	Category
	Priority/Severity
	Solution Code
	G-TO-01
	Annual Leave Request & Approval Workflow
	Fully supported by Time Off module
	Standard HR
	Low
	FIT-001
	G-TO-02
	Remaining Leave Balance Tracking
	Supported via Leave Allocation & Accrual
	Standard HR
	Low
	FIT-002
	G-TO-03
	Multi-level Leave Approval
	Requires configuration of approval hierarchy
	Hoc Ba Specifics
	Medium
	CFG-TO-001
	G-TO-04
	Automatic Annual Leave Accrual (12 days/year)
	Supported via Accrual Plans
	VN Labor Policy
	Medium
	CFG-TO-002
	G-TO-05
	Vietnamese Public Holidays Management
	Public Holidays available but requires configuration
	VN Localization
	Low
	CFG-TO-003
	G-TO-06
	Mandatory Attachment for Sick Leave
	No strict validation by default
	VN HR Compliance
	Medium
	CUS-TO-001
	G-TO-07
	Separate Leave Policies by Employee Group
	Odoo does not auto-map policies by employee type
	Hoc Ba Specifics
	High
	CUS-TO-002
	G-TO-08
	Prevent Instructor Leave Conflict with Teaching Schedule
	No integration with teaching schedule
	Hoc Ba Academic Operations
	High
	CUS-TO-003
	G-TO-09
	Leave Dashboard & Analytics
	Only basic reporting available
	Hoc Ba Specifics
	Medium
	CUS-TO-004
	G-TO-10
	Carry-over Rules for Remaining Annual Leave
	Supported through configuration
	VN Labor Policy
	Medium
	CFG-TO-004
	G-TO-11
	Unpaid Leave Payroll Synchronization
	Supported via Payroll Work Entries
	Payroll Integration
	Low
	FIT-003
	G-TO-12
	Employee Self-service Leave Portal
	Fully supported by Employee Portal
	Standard HR
	Low
	FIT-004
	G-TO-13
	HR Audit Trail for Leave Approval History
	Standard chatter log available
	Standard HR
	Low
	FIT-005
	G-TO-14
	Emergency Leave with Fast Approval
	Requires custom approval condition
	Hoc Ba Specifics
	Medium
	CUS-TO-005
	G-TO-15
	Leave Quota Restrictions for Part-time/Collaborators
	Requires custom policy logic
	Hoc Ba Workforce Model
	High
	CUS-TO-002
	



4.2 FIT Analysis (Standard Odoo)
FIT-001 — Annual Leave Request & Approval Workflow
Fully supported by the Odoo Time Off module. Employees can submit leave requests, managers can approve/reject requests, and the system automatically updates leave balances. No change required.
FIT-002 — Remaining Leave Balance Tracking
Supported through Leave Allocation and Accrual Plans. Employees and HR can monitor remaining leave balances in real time. No change required.
FIT-003 — Payroll Synchronization for Unpaid Leave
Approved unpaid leave automatically generates Payroll Work Entries and impacts salary calculations accordingly. No change required.
FIT-004 — Employee Self-service Leave Portal
Employees can:
* submit leave requests
* view approval status
* check remaining leave balance
via Employee Portal or mobile app. No change required.
FIT-005 — Leave Approval Audit Trail
The standard chatter mechanism logs:
* approval actions
* refusal actions
* timestamps
* comments
ensuring traceability and HR auditability. No change required.
4.3 CONFIGURATION GAP (Configuration Only)
CFG-TO-001 — Multi-level Leave Approval Workflow
Odoo Configuration Area: Time Off → Configuration → Time Off Types
Configuration Detail:
Configure approval hierarchy:
* ≤ 2 days: Direct Manager approval
* 2 days: Manager + HR approval
* 5 days: Director approval required
Enable “Apply Double Validation” for long leave requests.
Expected Result:
Improves operational control and prevents workforce shortages caused by long unreviewed leave periods.
CFG-TO-002 — Annual Leave Accrual Plan (12 days/year)
Odoo Configuration Area: Time Off → Configuration → Accrual Plans
Configuration Detail:
Create an Accrual Plan:
* Monthly accrual: 1 day/month
* Maximum allocation: 12 days/year
* Automatically assigned to full-time employees
* Carry-over policy configurable separately
Expected Result:
Annual leave is accumulated automatically without manual Excel tracking.


CFG-TO-003 — Vietnamese Public Holidays Configuration
Odoo Configuration Area: Time Off → Configuration → Public Holidays
Configuration Detail:
Import/configure Vietnamese public holidays:
* Lunar New Year
* Hung Kings Festival
* Liberation Day (30/4)
* Labor Day (1/5)
* National Day (2/9)
Expected Result:
Public holidays are excluded automatically from leave calculations and payroll deductions.
CFG-TO-004 — Annual Leave Carry-over Policy
Odoo Configuration Area: Time Off → Configuration → Accrual Plans
Configuration Detail:
Configure carry-over rules:
* Maximum transferable leave:
   * 5 days/year
* Expiration:
   * End of Q1 next year
Expected Result:
Prevents unlimited leave accumulation while remaining compliant with company HR policy.
CFG-TO-005 — Leave Types Configuration for Hoc Ba
Odoo Configuration Area: Time Off → Configuration → Time Off Types
Configuration Detail:
Create standardized leave categories:
* Annual Leave
* Sick Leave
* Unpaid Leave
* Maternity Leave
* Emergency Leave
Define:
* Paid/Unpaid behavior
* Validation policy
* Required approvals
Expected Result:
Standardized leave processing across all departments and employee groups.


4.4 CUSTOMIZATION GAP (Development Required)
CUS-TO-001 — Mandatory Medical Attachment for Sick Leave
* Business need: Employees requesting Sick Leave must upload supporting medical documents to ensure policy compliance and prevent abuse.
* Standard limitation: Odoo Time Off does not strictly enforce attachment validation based on leave type.
* Custom Solution:
Develop a custom validation module:
hb_timeoff_medical_validation
Logic:
* If leave_type = Sick Leave
* attachment_ids must not be empty
* otherwise raise ValidationError
Add:
* warning popup
* HR validation check


* Business benefit: Improves HR compliance, reduces fake sick leave requests, and standardizes medical documentation.


CUS-TO-002 — Employee-type-based Leave Policy Engine
* Business need:
Different workforce groups at Hoc Ba have different leave entitlements:
* Full-time employees
* Part-time staff
* Visiting instructors
* Collaborators
* Standard limitation: Odoo does not automatically assign leave policies based on employee_type or contract_type.
* Custom solution:
Develop module:
hb_timeoff_policy
Logic:
* Full-time:
   * 12 annual leave days/year
* Part-time:
   * no accrual allocation
* Visiting Instructor:
   * unpaid leave only
* Collaborator:
   * disable leave allocation
Auto-map:
* Leave Types
* Accrual Plans
* Approval Rules


* Business benefit: Eliminates manual HR setup and ensures consistent leave policy enforcement.
CUS-TO-003 — Instructor Teaching Schedule Conflict Detection
* Business need: Instructors should not be able to take leave during confirmed teaching sessions without replacement arrangements.
* Standard limitation: Odoo Time Off has no native integration with academic schedules or teaching sessions.
* Custom solution:
Develop module:
hb_timeoff_schedule_conflict
Logic:
* During leave request submission:
   * search teaching.schedule / academic.session
* If teaching sessions exist:
   * trigger warning popup
   * require Academic Manager approval
   * optionally block submission


* Business benefit: Prevents unexpected class cancellations and protects learning operations.


CUS-TO-004 — Advanced Leave Analytics Dashboard
* Business need: HR Managers require advanced leave insights for workforce planning and operational monitoring.
* Standard limitation: Odoo standard reporting provides only basic leave statistics.
* Custom solution:
Develop custom dashboard:
* Leave by Department
* Monthly Leave Trend
* Sick Leave Frequency
* Top Absent Employees
* Remaining Leave Balance
* Burnout Risk Indicators
Export:
* Excel
* PDF


* Business benefit: Supports strategic HR planning and enables proactive employee workload management.
CUS-TO-005 — Emergency Leave Fast-track Approval Workflow
* Business need:Emergency leave requests require immediate approval without waiting for the full standard workflow.
* Standard imitation: Odoo approval flow is static and does not dynamically bypass approval layers for emergencies.
* Custom Solution:
Develop fast-track approval logic:
* Emergency Leave type
* Auto-notify HR + Manager instantly
* Allow one-step approval
* Trigger mobile push notification/email
* Business benefit: Improves responsiveness during emergencies and minimizes operational delays.


  

To-be process
CHAPTER 5 — CONFIGURATION SPECIFICATION
5.1 Employee Module Configuration


ID
	Configuration Name
	Odoo Config Area
	Expected Result
	CONF-EMP-01
	Citizen ID Format Constraint (12 digits)
	Employees > Settings > Studio / Python Constraints
	System blocks record saving if identification_id does not match the 12-digit format (Regex: ^\d{12}$).
	CONF-EMP-02
	2-Tier Administrative Directory (Modernized)
	Settings > Technical > Countries > Viet Nam (State & Wards)
	Users only select Province $\rightarrow$ Commune/Ward. Intermediate District level is completely removed/hidden.
	CONF-EMP-03
	Hoc Ba Staff Categorization
	Employees > Configuration > Employment Types
	Added types: "Visiting Instructor", "Collaborator", "Full-time Staff", "Teaching Assistant".
	CONF-EMP-04
	Chinese Language & Pedagogy Skill Matrix
	Employees > Configuration > Skill Types
	Skill tree created for: "HSK Certs (3-6)", "HSKK Certs", "Pedagogical Skills", "TOCFL Certs".
	CONF-EMP-05
	Competency Scaling (Skill Levels)
	Employees > Configuration > Skill Levels
	Setup % scales or labels: "Elementary", "Intermediate", "Advanced", "Native" for each skill.
	CONF-EMP-06
	Flexible Schedules (Remote/Online Teachers)
	Employees > Configuration > Working Schedules
	Configured "Flexible Hours" for Online instructors to prevent false absence alerts.
	CONF-EMP-07
	Onboarding Plan: New Instructor
	Employees > Configuration > Plans
	Auto-generates tasks: IT assigns Zoom Pro; Admin issues syllabus; Academic schedules demo teaching.
	CONF-EMP-08
	Offboarding Plan: Academic Handover
	Employees > Configuration > Plans
	Mandatory task: Instructors input lesson progress; Academic confirms e-logbook handover.
	CONF-EMP-09
	Advanced Presence Monitoring
	Employees > Settings > Presence Control
	Activates monitoring based on Corporate IP and Email activity to track real-time working status.
	CONF-EMP-10
	Gamification Badges
	Employees > Configuration > Badges
	Created badges: "Teacher of the Month", "HSK Ambassador", "Dedicated Academic Advisor".
	

5.2 Recruitment Configuration
The Odoo Recruitment module will be configured to streamline the talent acquisition pipeline, ensuring seamless tracking from application submission to onboarding. This section defines the foundational setup for applicant tracking stages, automated communication templates, and structured interview evaluation forms.
5.2.1 Recruitment Stages
Applicant tracking is managed via a visual Kanban pipeline. Stages can be global (applicable to all job positions) or specific to certain departments or roles. Moving an applicant to a new stage can automatically trigger predefined actions, such as sending an email template.
The table below outlines the standard recruitment stages to be configured in Recruitment > Configuration > Stages:
Stage Name
	Sequence
	Folded in Kanban
	Automated Email Template
	Description / Exit Criteria
	Initial Qualification
	10
	No
	Recruitment: Application Acknowledgment
	Default landing stage for all incoming applications via the website or email alias.
	First Interview
	20
	No
	Recruitment: Invite to HR Screening
	Initial screening (phone/video) conducted by the HR team to assess cultural fit and basic requirements.
	Technical Assessment
	30
	No
	Recruitment: Technical Test Assignment
	Practical test, portfolio review, or technical assessment phase.
	Second Interview
	40
	No
	Recruitment: Invite to Technical/Manager Interview
	In-depth interview with the hiring manager and departmental technical leads.
	Contract Proposal
	50
	No
	Recruitment: Job Offer Letter
	Background checks cleared; formal offer generated and extended to the candidate.
	Contract Signed
	60
	Yes
	None
	Candidate has accepted and signed the offer. Moving here triggers the "Create Employee" option.
	Refused
	70
	Yes
	Recruitment: Application Refusal
	Archived state for unsuccessful applicants. Requires a specified "Refusal Reason".
	Odoo System Note:
When an applicant is moved to the Contract Signed stage, the system should be configured to automatically change the status of the corresponding Job Position if the hiring quota has been met.
5.2.2 Email Templates
Automated email templates ensure timely, professional, and consistent communication with candidates while reducing manual administrative overhead for the HR team. These templates utilize dynamic placeholders to personalize candidate details, job titles, and interview schedules.
Configuration path: Settings > Technical > Email > Templates (mapped to the hr.applicant model).
* Template Name: Recruitment: Application Acknowledgment
   * Trigger: Automated upon entry into Initial Qualification.
   * Key Content: Expresses gratitude for the application, confirms receipt, and outlines the expected evaluation timeline.
* Template Name: Recruitment: Invite to HR Screening / Technical Interview
   * Trigger: Manual or Automated upon entering First/Second Interview stages.
   * Key Content: Provides interview details and includes an integration link to the Odoo Calendar or an external scheduling tool (e.g., Calendly link mapped to the recruiter's user profile).
* Template Name: Recruitment: Job Offer Letter
   * Trigger: Manual trigger by HR Recruiter in the Contract Proposal stage.
   * Key Content: Formal offer details with a secure link to the Odoo Sign module for digital signature of the employment contract attachment.
* Template Name: Recruitment: Application Refusal
   * Trigger: Automated when an applicant is archived or moved to Refused.
   * Key Content: Polite rejection text.
   * Configuration Rule: A 48-hour automated sending delay should be configured via an automated action to avoid immediate, robotic-looking rejections after an interview.
5.2.3 Interview Forms
To standardize candidate evaluation and eliminate hiring bias, Odoo’s native Surveys application is integrated directly into the Recruitment module. Interview forms are linked to specific job positions or recruitment stages to allow interviewers to log structured feedback.
Configuration path: Recruitment > Configuration > Job Positions (under the Recruitment tab).
[Job Position: Senior Developer] 
   └── Linked Interview Form: "Technical Interview Evaluation Sheet"
         ├── Section 1: Core Architecture Knowledge (Rating Scale 1-5)
         ├── Section 2: Coding Exercise Performance (Text Box + Score)
         └── Section 3: Team Fit & Communication (Multiple Choice)


Configuration Specifications for Interview Sheets:
* Access Control: Interview forms are restricted to internal users (Recruiters, Hiring Managers, and Interviewers). They are not public-facing.
* Scoring & Evaluation: Questions should utilize a mix of matrix/rating scales (1 to 5 stars) for quantitative evaluation and open text fields for qualitative feedback.
* Attachment Matrix: 


Job Position Category
	Linked Interview Form
	Trigger Point / Stage
	All Positions
	HR Screening Questionnaire
	First Interview
	Technical / Engineering
	Coding & Architecture Evaluation
	Technical Assessment
	Management / Executive
	Leadership Case Study Scorecard
	Second Interview
	

* Implementation Requirement:
Once an interviewer completes and submits the linked survey form, the final score and a PDF summary of the answers must automatically attach to the Chatter of the applicant's record for centralized visibility.
5.3 Attendance Configuration
* Work Schedules
* Shift Rules
* Late Policies


5.4 Payroll Configuration
* Salary Structures
* Salary Rules
* Allowances
* Deductions
5.5 Time off Configuration


ID
	Configuration Name
	Odoo Config Area
	Expected Result
	CONF-TO-01
	Multi-Level Leave Approval Workflow
	Time Off > Configuration > Time Off Types
	Configure approval hierarchy: Direct Manager → HR → Director based on leave duration. Long leave requests require Double Validation before approval.
	CONF-TO-02
	Annual Leave Accrual Plan (12 Days/Year)
	Time Off > Configuration > Accrual Plans
	Full-time employees automatically accrue 1 leave day per month, up to 12 days per year, without manual HR calculations.
	CONF-TO-03
	Vietnamese Public Holiday Calendar
	Time Off > Configuration > Public Holidays
	National holidays are predefined and automatically excluded from leave calculations and payroll deductions.
	CONF-TO-04
	Annual Leave Carry-over Policy
	Time Off > Configuration > Accrual Plans
	Remaining annual leave can be carried forward up to 5 days and expires at the end of Q1 of the following year.
	CONF-TO-05
	Standardized Leave Types
	Time Off > Configuration > Time Off Types
	Create standardized leave categories: Annual Leave, Sick Leave, Unpaid Leave, Maternity Leave, Emergency Leave.
	CONF-TO-06
	Leave Allocation by Employee Group
	Time Off > Configuration > Time Off Types / Accrual Plans
	Different leave entitlements are configured for Full-time Staff, Teachers, Teaching Assistants, and Collaborators according to company policy.
	CONF-TO-07
	Leave Approval Notifications
	Settings > Discuss > Notifications / Time Off
	Automatic notifications are sent to Managers and HR whenever a leave request is submitted, approved, or rejected.
	CONF-TO-08
	Leave Reason & Supporting Documents
	Time Off > Configuration > Time Off Types
	Configure leave request forms to capture leave reasons and allow supporting document uploads for auditing purposes.
	CONF-TO-09
	Payroll Integration for Unpaid Leave
	Payroll > Work Entries Types / Time Off Integration
	Approved unpaid leave automatically generates Work Entries and affects salary calculations correctly.
	CONF-TO-10
	Calendar Synchronization
	Time Off > Configuration > Settings
	Approved leave requests are automatically synchronized with employee calendars to improve workforce visibility and scheduling.
	CONF-TO-11
	Leave Reporting & Analytics Access
	Time Off > Reporting
	HR Managers can access leave reports, department leave statistics, leave balances, and leave utilization trends.
	CONF-TO-12
	Employee Self-Service Leave Portal
	Employees Portal / Time Off
	Employees can independently submit leave requests, check approval status, and view remaining leave balances through the portal.
	





Tab 2






	

BUSINESS BLUEPRINT
	

Document information
	Project Name
	Human Resource Management System for Hoc Ba Learning Center
	Module
	MM - Materials Management
	Created by
	Dong Hoang Anh (AnhDH)
	Version
	1.0
	Date
	21/05/2026
	

	

	

	



Change history
	Changed date
	Items have been changed
	Changed content/Reason
	Updated by
	Type
(A/C/D)
	Version
	21/05/2026
	All
	Initial Create
	ISP490_G2
	C
	1.0
	

	

	

	

	

	

	

	

	

	

	

	

	A – Create  C – Change  D – Delete
	



















        
















Advisor Signature
	

	Full name & Role
	Signature
	Date
	Note
	Created by
	Dong Hoang Anh
Anhdhhe182321@fpt.edu.vn 
Functional Consultant
	

	

	

	Reviewed by


	

	

	

	

	Approved by


	

	

	

	

	________________


FU Signature
	

	Full name & Role
	Signature
	Date
	Note
	Approved by
	

	

	

	

	

	

	

	

	

________________




* Table of Contents
	

Table of Contents        5
OVERVIEW        7
1.1 Glossary        7
1.2 Flowchart shapes usage        8
ORGANIZATIONAL STRUCTURE        10
2.1 Introduction        10
2.2  SAP Organizational Structure (MM)        10
2.2.1: Client        12
2.2.2: Company code        12
2.2.3: Plant        12
2.2.4: Storage Location        12
2.2.5: Purchasing Organization        14
2.2.6: Purchasing Group        14
2.3  SAP Organizational Structure (SD)        15
2.3.1:  Sales Organization        15
2.3.2:  Distribution Channel        16
2.3.3: Division        16
MASTER DATA        17
3.1  MM-MD-01 Supplier Master - Data List        17
3.1.1: Supplier Details        17
3.1.2: Process Flow        18
3.1.3: Process Description        19
3.2  MM-MD-02: Material Master Data        20
3.2.1: Material Details        20
3.2.2: Process Flow        23
3.2.3: Process Description        24
3.3  MM-MD-03: Customer Master Data        25
3.4.1: Details        25
3.4.2: Process Flow        30
3.3.3: Process Description        31
BUSINESS PROCESS        33
4.1  MM-BP-01: Procure-to-pay Process (MM)        33
4.1.1: Process Flow        33
4.1.2: Process Description        34
4.2: MM-BP-02: Supplier Return Process        36
4.2.1: Process Flow        36
4.2.2: Process Description        39
4.3: SD-BP-01: Order-to-cash Process        41
4.3.1: Process Flow        41
4.3.2: Process Description        42
4.4: SD-BP-02: Customer Returns Order Process        44
4.4.1: Process flow        44
4.4.2: Process Description        45
4.5: MM-BP-03 Return RTP Process        46
4.5.1: Supplier Return RTP Process        46
4.5.1.1: Process flow        46
4.5.1.2: Process Description        48
4.5.2: Customer Return for RTP Process        49
4.5.2.1: Process flow        49
4.5.2.2: Process Description        51
REPORTS        51
________________


* OVERVIEW
   1. Glossary


Thuật ngữ
	Định nghĩa
	Note
	Odoo
	Nền tảng ERP mã nguồn mở được sử dụng để triển khai dự án.
	

	Dùng sẵn
	Tính năng có sẵn ngay khi cài đặt module, không cần cấu hình hay lập trình.
	

	Config
	Tính năng yêu cầu thiết lập, cấu hình trong giao diện quản trị trước khi sử dụng.
	

	Customize
	Tính năng yêu cầu lập trình bổ sung, không có sẵn hoặc không thể cấu hình được.
	

	Future
	Tính năng đề xuất cho giai đoạn 2, không nằm trong phạm vi triển khai hiện tại.
	

	HRM
	Hệ thống Quản trị Nhân sự.
	

	Work Entry
	Bản ghi về thời gian làm việc thực tế của nhân viên, được tổng hợp từ dữ liệu Chấm công, Nghỉ phép,...
	

	Payslip
	Phiếu lương của nhân viên cho một kỳ nhất định.
	

	Payslip Batch
	Tính năng tạo hàng loạt phiếu lương cho nhiều nhân viên cùng một kỳ lương.
	

	   2. Flowchart shapes usage
Example
  * ORGANIZATIONAL STRUCTURE
   * 2.1 Introduction 
  

Học Bá Company operates a Chinese language learning center that provides Chinese courses for students at different proficiency levels, including beginner, intermediate, advanced, and HSK examination preparation. As the number of students, teachers, classes, and marketing activities continues to grow, the center faces increasing difficulties in managing its academic, operational, and business processes efficiently. 
Currently, many activities at the center are handled through manual processes and disconnected tools such as spreadsheets, paper records, messaging applications, and standalone social media channels. Student information, class schedules, attendance, examination results, and learning materials are managed separately, while marketing and sales teams also rely on Facebook advertising channels such as Facebook Lead Ads Forms and Facebook Messenger to attract potential learners. These leads are often entered manually into the CRM system. 
This fragmented management approach creates several problems. Academic staff face difficulties in arranging class schedules, assigning teachers, tracking attendance, managing examinations, and notifying students of study schedules and results. Teachers lack a centralized platform to manage teaching schedules, monitor student performance, and provide timely feedback. Students also do not have a convenient system to access learning materials, receive study notifications, or track their academic progress. 
At the same time, manual lead processing from Facebook causes delays, data inconsistency, missing campaign tracking information, duplicate leads, and the absence of real-time reports for marketing effectiveness. As a result, the center lacks an integrated system that can connect marketing, sales, academic management, and daily operations in a unified workflow. 
Therefore, there is a strong need for an ERP-based Human Resource Management and Education System that integrates employees on a single platform. The project idea was proposed by the management team of Học Bá Center, who require a centralized digital system to improve operational efficiency, enhance service quality, and support future business growth.


   * 2.2  SAP Organizational Structure (MM)
The organizational structure of Brew Up Vietnam in the SAP S/4HANA Materials Management (MM) module is designed to support efficient material control, inventory tracking, and streamlined procurement operations across two major operational locations: Hanoi and Ho Chi Minh City.
  

      * 2.2.1: Client 
* Client: 302 – Brew Up Vietnam: This is the client system being managed in the SAP system. Client 302 represents Brew Up's operations.
* The highest-level organizational unit in the SAP system. It contains all company codes, configuration data, and master data. It acts as the central layer where all business units and organizational elements are integrated. And it represents the entire SAP environment for Brew Up Vietnam.
      * 2.2.2: Company code
* BU00 : Represents the legal entity for operations in Viet Nam, serving as an independent legal entity for financial accounting and external reporting purposes.
      * 2.2.3: Plant 
Plants represent operational units within the company where production, storage, or distribution activities take place. Each plant is associated with specific logistics and inventory management functions.
Code
	Plant
	Description
	BUHN
	Ha Noi
	Represents the storage facility in Hanoi
	BUSG
	Sai Gon 
	Represents the storage facility in Sai Gon
	      * 2.2.4: Storage Location
Storage locations within each plant are specific areas designated for storing goods. They help  manage inventory and ensure proper stock control. 










STT
	Storage Location
	Code
	Description
	1
	Regular beer storage
	RB00
	This location is used for the regular beer products. These are products ready for daily sales and distribution
	2
	Chiller beer Storage
	CB00
	Dedicated to chilled beer products that require storage under temperature-controlled conditions to maintain quality and freshness.
	3
	Promotion products Storage
	PP00
	This location stores promotional items including samples, display products, gifts, and other marketing-related stock that is not for direct commercial sale.
	4
	Returnable products Storage
	RP00
	Includes both returnable packaging and defective/returned products to be sent back to Suppliers.
	5
	Operation Storage
	OP00
	This location stores internal-use operational supplies
	

      * 2.2.5: Purchasing Organization 
* VN00: Central purchasing organization managing procurement activities for all plants under Brew Up Vietnam.
* It’s where the buying activity for a plant takes place. It is an organization unit responsible for procuring services and materials, and it negotiates conditions of the purchase with the Suppliers.
      * 2.2.6: Purchasing Group
* Purchasing Group: Key that represents the buyer or group of buyers who are responsible for certain purchasing activities
* Channel of communication for Suppliers
Code
	Description
	BUN
	Handles procurement requests for the north
	BUS
	Handles procurement requests for the south
	   * 2.3  SAP Organizational Structure (SD)
  

      * 2.3.1:  Sales Organization 
Sales Organization represents the organizational unit responsible for the sale of products and services. It is responsible for distributing goods and services and negotiating terms of sales.
* Brew Up Viet Nam : The sales organization responsible for managing sales activities in  Vietnam. It handles product distribution, negotiates sales terms, and is accountable for sales revenue within this region.


 
Code 
	Sales Organization
	Description
	VN00
	Brew Up Viet Nam
	Sales operations in Vietnam
	      * 2.3.2:  Distribution Channel
Distribution Channel defines the method or path through which products or services reach the customers. It helps BRcategorize sales activities and pricing.
* Indirect Sales: Utilizes intermediaries or partners to distribute products, extending market reach through different channels.
Code 
	Distribution Channel
	Description
	IS
	Indirect Sales
	Sales via intermediaries
	      * 2.3.3: Division
Division represents a product line or a range of products. It is a way to segment products or services and apply specific strategies for sales.
* BE - BRUP Beer : Represents the product group related to alcoholic drinks, primarily beer products distributed by Brew Up from Suppliers.
Code 
	Division 
	Description
	BE
	Beer 
	Product group for beer
	________________
* * MASTER DATA
   * 3.1  MM-MD-01 Supplier Master - Data List
      * 3.1.1: Supplier Details
Supplier name 
	Supplier type
	Supplies / Services
	Hanoi Beer Alcohol and Beverage Joint Stock Corporation (HABECO)
	Domestic
	Regular Beer, Chiller Beer, Promotion Products
	Saigon Beer – Alcohol – Beverage Corporation (SABECO)
	Domestic
	Regular Beer, Chiller Beer, Promotion Products
	Heineken Vietnam Brewery
	Imported
	Regular Beer, Promotion Products
	Hai Dang Pro Company Limited
	Imported
	Imported craft beers
	An Khang Industrial Cleaning Co., Ltd.
	Domestic
	Industrial cleaning services
	Hong Ha Office Supplies Joint Stock Company
	Domestic
	Office paper, pens, folders, ink, notepads
	Hai Anh Uniforms Co., Ltd.
	Domestic
	Employee uniforms, caps
	Bao Tin Technical Services Co., Ltd.
	Domestic
	Facility repair, plumbing, minor electrical maintenance
	ABC Creative Advertising Co., Ltd.
	Domestic
	Marketing campaign services, digital promotions
	Minh Quan Cold Storage Solutions Co., Ltd.
	Domestic
	Cold storage for chiller beer
	      * 3.1.2: Process Flow
  

      * 3.1.3: Process Description
Step 
	Step Name
	Detailed Description
	Role
	

	Start
	

	

	1
	Request for Supplier Creation/Change
	Initiate the request for creating or modifying Supplier data.
	Purchasing staff
	2
	Fill in/Adjust Material Template
	Complete or update the material data template with the required information, including specifications and classifications.
	Purchasing staff
	3
	Review Material Template
	Review the submitted material template for accuracy, completeness, and compliance with standards.
	Purchasing Manager


	3.1
	Sufficient Information?
	Check if the information provided in the Supplier template is sufficient. If not, return to Step 2 for adjustments.
	Purchasing Manager
	4
	Approve Supplier Template
	Approve the Supplier creation/change request based on the reviewed template.
	Master team leader
	4.1
	Approve?
	Approve the changes made to the Supplier data. If not approved, end the process.
	Master team leader
	5.1
	Create Supplier 
	Create the Supplier data in the system 
	Purchasing Manager
	5.2
	Change Supplier 
	Modify the Supplier data in the system 
	Purchasing Manager
	5.3
	Set Flag for Deletion Supplier 
	Set a flag for deletion if the Supplier is obsolete or no longer needed
	Purchasing Manager
	6
	Check if it is correct?
	Verify whether the data changes were applied correctly. If incorrect, necessary corrections are made, return to Step 5.
	Purchasing staff
	 
	End
	Complete the process once all changes are confirmed and implemented.
	

	

   * 3.2  MM-MD-02: Material Master Data
      * 3.2.1: Material Details
* Material Type 
Material Type
	Description
	HAWA
	Trading goods
	LEIH
	Returnable Packaging
	ROH
	Raw materials
	



* Material Group
Material Group
	Material Group Description
	RB01
	Regular beer
	CB00
	Chiller beer
	PP00
	Promotion products
	OP00
	Operation products
	RTP00
	Returnable transport packaging
	DP00
	Defective Products
	

* Material Specifications (Example of each group)


Specifications
	Lager Can 330ml
(Regular beer) 
	Keg beer 50L
(Chiller beer) 
	Glass 500ml 
(Promotion products) 
	Uniform
(Operation products) 
	Keg 50L 
(Returnable packaging) 
	Broken Lager Can 330ml
(Defective Products)
	Base Unit of Measure
	CAR (Carton)
24 bottles/ 1 carton
	PC (Piece)
	PC (Piece)
	PC (Piece)
	PC (Piece)
	PC (Piece)
	Gross Weight (Total weight of the product including packaging.)
	10.8 kg
	65 kg
	0.2 kg 
	0.2 kg
	15 kg 
	0.45 kg
	Net Weight
(The product's actual weight excluding packaging.)


	7.92 kg
	50 kg
	0.18kg 
	0.2kg 
	15 kg
	0.33 kg
	Volume
	0.0096 m³
	0.06 m³
	0.0005 m³
	0.001 m³
	0.06 m³
	0.0004 m³
	Dimensions (H x W x D)
	25 × 27 × 15 cm
	60 × 40 × 35 cm
	15 × 7 × 7 cm
	30 × 25 × 10 cm
	60 × 40 × 35 cm
	12 × 6.5 × 6.5 cm
	Valuation Class
	7920
	7920 
	3402
	3030
	3050
	3300
	Procurement Type
	External procurement
	External procurement
	External procurement
	External procurement
	External procurement
	External procurement
	Price Control
	Standard
	Standard
	Standard
	Standard
	Standard
	Standard
	Item Category Group
	NORM
	NORM
	NORM
	NORM
	NORM
	NORM
	

* General Item Category Group: Defines how the item is treated in PO, e.g., NORM (Standard Item)
      * 3.2.2: Process Flow
  

      * 3.2.3: Process Description
Step 
	Step Name
	Detailed Description
	Role
	

	Start
	

	

	1
	Request for Material Creation/Change
	Initiate the request for creating or modifying material data.
	Purchasing staff
	2
	Fill in/Adjust Material Template
	Complete or update the material data template with the required information, including specifications and classifications.
	Purchasing staff
	3
	Review Material Template
	Review the submitted material template for accuracy, completeness, and compliance with standards.
	Purchasing Manager


	3.1
	Sufficient Information?
	Check if the information provided in the material template is sufficient. If not, return to Step 2 for adjustments.
	Purchasing Manager
	4
	Approve Material Template
	Approve the material creation/change request based on the reviewed template.
	Master team leader
	4.1
	Approve?
	Approve the changes made to the material data. If not approved, end the process.
	Master team leader
	5.1
	Create Material
	Create the material data in the system
	Purchasing Manager
	5.2
	Change Material 
	Modify the material data in the system 
	Purchasing Manager
	5.3
	Set Flag for Deletion Material
	Set a flag for deletion if the material is obsolete or no longer needed
	Purchasing Manager
	6
	Check if it is correct?
	Verify whether the data changes were applied correctly. If incorrect, necessary corrections are made, return to Step 5.
	Purchasing staff
	 
	End
	Complete the process once all changes are confirmed and implemented.
	

	   * 3.3  MM-MD-03: Customer Master Data 
      * 3.4.1: Details
1. Business Partner Grouping for Customers:
Domestic Customers are clients based within Vietnam. They represent Brew Up's primary market and include:
* Restaurants, bars, pubs, karaoke chains
* Retail stores, convenience stores
* National food & beverage chains
* Event-based short-term contractual buyers
2. Key Areas of Customer Master Data:
General data
* Title: Identifies the form of address for the customer, such as "Company" or "Mr./Mrs." This helps categorize the customer for formal communication.
* Company Name/ Name:  The name of the customer or company.
* Search Term: A keyword or term to quickly search and find the customer in the system. It acts as a shortcut when navigating through large customer lists.
* Address (Street, City, Postal Code)
* Country
* Region
* Communication Language: English
* Tax Jurisdiction Code (if applicable): A unique code identifying the customer’s tax area. It is used for calculating the correct tax on transactions.
Accounting 
* Company Code: Represents the specific legal entity within the organization responsible for a accounting  (BU00 - Brew Up)
* Reconciliation Account: Links customer transactions to the appropriate general ledger accounts.
* Payment Terms: The terms under which payments are expected to be made, such as the number of days allowed for payment and any discounts available for early payment.


Payment Terms
	Description
	0001
	Payable immediately Due net
	0002
	within 14 days 2% cash discount, within 30 days Due net


	

Sale data
* Sale Organization 


Code 
	Sales Organization
	Description
	VN00
	Brew Up Viet Nam
	Sales operations in Vietnam
	

* Distribution Channel 


Code 
	Distribution Channel
	Description
	ID00
	Indirect Sales
	Sales via intermediaries
	

* Division 


Code 
	Division 
	Description
	BR
	Beer 
	Product group for beer
	

* Sale District: Identifies the geographical sales area, helping in organizing customers by location for reporting and sales analysis.
Sales District 
	Description
	BU0001
	Northern Vietnam
	BU0002
	Southern Vietnam
	* Currency : VND
* Delivery Priority: Specifies how urgent the deliveries are for this customer. Higher priority customers may receive faster shipping services.
* Delivering Plant: The location from which the products will be dispatched to the customer. It is important for shipment logistics and inventory management.
* Shipping Conditions: Defines the conditions under which goods are shipped to the customer, such as standard shipping or express delivery.
* Max. Partial Deliveries: Limits the number of partial shipments that can be made for an order, helping to manage customer expectations on how orders are fulfilled.
* Incoterms: Specifies the terms of trade, indicating who is responsible for shipping, insurance, and customs duties. It defines the point at which the ownership of goods is transferred from the seller to the buyer. (DDP - Delivered Duty Paid)
* Incoterms Location 1: The specific location (e.g., port or city) related to the Incoterms agreement, such as the port where goods will be delivered.
Account Assignment Group (Customer): Groups customers based on account assignment for revenue reporting. It defines how revenue from the customer is posted in financial statements.


Account assignment group
	Description
	01 
	Domestic Revenues
	

Tax Classification: Defines how the customer is treated for tax purposes (e.g., taxable, non-taxable) and is crucial for applying the correct tax rates to sales orders.
Tax Classification
	Description
	1
	Standard Rate
	











      * 3.4.2: Process Flow
  

      * 3.3.3: Process Description
Step
	Step Name
	Detailed Description
	Role
	

	Start
	

	

	1
	Request for Customer Creation/Change
	Initiate the request for creating or modifying customer data.
	Sales/Supply Chain Department
	2
	Fill in/ Adjust Template
	Complete or update the customer data template with necessary information.
	Sales/Supply Chain Department
	3
	Review Template
	Review the submitted template for accuracy and completeness.
	FI Department
	3.1
	Sufficient Information?
	Check if the information provided in the template is sufficient. If not, return to Step 2.
	FI Department
	4
	Approve Template
	Approve the customer creation/change request based on the reviewed template.
	FI Manager
	4.1
	Approve?
	Approve the changes made to the customer data. If not approved, return to Step 2.
	FI Manager
	5.1
	Create/Change Customer 
	Create or modify the customer data in the system as per the approved template.
	FI Department
	5.2
	Block/Unblock Customer
	Block or unblock the customer as required.
	FI Department
	5.3
	Set Flag for Deletion Customer
	Set a flag for deletion if the customer is no longer needed.
	FI Department
	6
	Check if it is correct?
	Verify whether the customer data changes were applied correctly. If incorrect, necessary corrections are made, return to step 5.
	Sales/Supply Chain Department
	 
	End
	Complete the process once all changes are confirmed and implemented.
	

	* BUSINESS PROCESS
   * System Overview
The Human Resources Management System on the Odoo platform comprises five main modules, integrated to form a complete human resources management process from recruitment, onboarding, payroll management, leave management to timekeeping management.
Main Modules:
* Module 1: Attendances – Manage check-in/out, calculate working hours, alert for late arrivals/early departures
* Module 2: Employees – Manage employee records, organizational structure, onboarding/offboarding
* Module 3: Payroll – Create automatic payslips, approve them, export payment files
* Module 4: Time Off – Request leave, approve it, manage remaining time off
* Module 5: Recruitment – ​​Post job openings, manage candidate pipeline, schedule interviews
   * Integration Flow
The modules operate according to the following integrated process:


Step-by-Step Process
	Input From
	Module
	Processing
	Output To
	1. Recruitment
	CV from website/email
	Recruitment
	Kanban pipeline
	→ Employees
	2. Employee Creation
	Offer accepted
	Employees
	Create NV records
	→ Timekeeping, Payroll
	3. Timekeeping
	Check-in/out
	Attendances
	Work Entries
	→ Payroll
	4. Leave Processing
	Please leave
	Time Off
	Approved
	→ Payroll
	5. Payroll Calculation
	Attendance + Leave
	Payroll
	Create Payslip
	→ Email, Bank
	   * 4.1  HR-BP-01: Attendance Procedure
      * 4.1.1: Description
This process allows employees (including office staff and faculty) to record their daily working hours. The system supports multiple check-in/check-out methods (via personal computers, via shared kiosk devices). The recorded attendance data serves as input for calculations of working hours, overtime (OT), and as the basis for salary calculation.


      * 4.1.2: Process Flow 
  

      * 4.1.3: Process Description 


Step
	Step Name
	Detailed Description
	Role
	

	Start
	Begin your shift for the day
	

	1
	Employee Check-in


	The employee executes the check-in action via one of two methods:
- Office staff: Logs into Odoo and clicks the green "Check In" button at the top right corner of the screen.
- On-site staff (Kiosk): Uses a dedicated tablet at the entrance to enter a personal PIN or scan a badge.


	Employee 
	2
	System Records Check-in Time
	The Odoo system automatically captures the check-in timestamp in the database and links it directly to the employee's profile.
	Odoo System 
	3
	Work
	The employee performs their assigned duties during the shift.
	Employee 
	4
	Employee Check-out
	At the end of the shift, the employee performs the check-out action similarly to check-in (clicks the "Check Out" button on the web or via the Kiosk tablet).
	Employee 
	5
	System Records Check-out Time
	The system captures and stores the check-out timestamp.
	Odoo System 
	6
	Calculate Working Hours & OT


	Based on the check-in/check-out timestamps and the pre-configured Working Schedule assigned to each employee (e.g., 8:30 AM – 5:30 PM, 1-hour lunch break), the system automatically calculates:
- Total actual worked hours (worked_hours).
- Overtime (OT) hours, if applicable.
	Odoo System 
	7
	Check and Process Alerts


	The system cross-checks the check-in/out timestamps with the defined working schedule:
- If check-in is later than scheduled -> "Late In" alert.
- If check-out is earlier than scheduled -> "Early Out" alert.
Note: Automatic alert emails require additional setup via a Scheduled Action.
	Odoo System / Manager 
	

	End
	The attendance logging process for the workday is successfully completed. 
	

	

Important notes for the deployment phase:
* Kiosk Mode: To use the check-in/out feature via shared devices, Kiosk mode must be configured in the Attendances application, and tablets/touchscreens must be prepared in suitable locations.
* Fingerprint device integration (Hardware): If the center needs to integrate with fingerprint or facial recognition time attendance machines (third-party hardware), this functionality is not available and requires custom development to communicate via API. It is recommended to include this in a later phase (Future).
* Output data for Payroll: Data from the hr_attendance table (specifically Work Entries records) will be used directly to calculate hourly wages for instructors or office staff.


   * 4.2: HR-BP-02: Employee Management Process
      * 4.2.1 Description
This process encompasses the entire lifecycle of an employee/lecturer within the system: from creating a new profile (after recruitment), updating information, managing contracts, skills, assets, to departure (offboarding). The goal is to centralize HR data, automate alerts (for expiring contracts), and provide an intuitive organizational structure. 
      * 4.2.1: Process Flow
  

      * 4.2.3: Process Description


Step 
	Step Name
	Detailed Description
	Role
	

	Start
	Triggered by a demand to establish management parameters for a human resource member. 
	

	1
	Request Profile Creation/Update 
	Initiated by recruitment needs (new profile) or modifications in employee status (promotion, department transfer, skills upgrade). Requests can originate from the Department Head or the employee. 
	Manager / Employee 
	2
	Input/Modify Employee Info 
	The HR department performs the "Create" or "Edit" actions on the Employee master form. Core fields include: Full Name, Work Email, Phone Number, Date of Birth, Joining Date, Gender, Marital Status, etc. 
	HR Officer 
	3
	Attach Contracts, Assets & Skills 
	Within the same employee file, HR performs supplementary data linking:
- Contracts: Creates a new contract record linked to the hr.contract model, uploads PDF copies, and sets the validity range.
- Assets: Allocates corporate hardware (laptops, monitors, uniform items).
- Skills: Declares skills matrices and proficiency rankings (e.g., English C1, Office Productivity Tools).
	HR Officer 
	4
	Assign Department, Job & Manager 
	Defines the operational reporting structure and hierarchy:
- Selects target Department.
- Maps Job Position.
- Designates the Direct Manager for approval matrix workflows.
	HR Officer 
	

	Save Profile & Activate 
	Commits data changes by clicking the "Save" button. The system validates and activates the record, provisioning access control tokens (if user accounts are linked) and exposing the profile to dependent subsystems (Attendance, Time Off).
	HR Officer 
	

	Check & Process Contract Expiry Alerts 
	The system runs periodic cron checks on the end date (date_end) of active labor contracts. If the expiration falls within the threshold window (e.g., 30 days out), an alert notification is dispatched to HR and the Line Manager.


Note: This execution path requires setting up a Scheduled Action or custom logic.
	Odoo System 
	

	Periodic Update 
	Throughout the lifecycle, HR updates records to reflect organizational modifications: promotions, transfers, salary increments (via new contracts), competency updates, or asset re-allocations. 
	HR Officer 
	

	Execute Offboarding Process 
	Upon formal contract termination, HR initiates the offboarding flow:
- Records the termination date on the profile.
- Revokes system application access by archiving/deactivating the linked user account.
- Executes customized offboarding checklists to log step-by-step tasks.
	HR Officer
	

	Revoke and Return Assets 
	Records the hardware collection protocol and changes asset operational states back to stock inside the asset tracking views. 
	HR Officer 
	

	End
	Terminates the active system lifecycle of the employee profile, preserving historical records for legal compliance.
	

	Important notes for the deployment phase:
* Organizational structure: It is necessary to fully establish Departments, Job Positions, and Management before creating employee profiles.
* Skills: To use the skills management feature, the Skills Management function must be enabled in the HR application's Settings.
* Offboarding Checklist: Odoo provides a built-in "Offboarding Activity Plan" concept, which allows you to configure steps (e.g., "Retrieve laptop," "Cancel company email," "Terminate contract") and assign responsibilities to each person. This is the Config function.
* Retention Rate: This report can be generated from contract data and end dates using the pivot tool in Reporting without additional programming (built-in).


   * 4.3: HR-BP-03: Recruitment Process
      * 4.3.1 Description
This process manages the entire candidate lifecycle, from application submission to onboarding. Utilizing an intuitive Kanban interface, it automates staged emails, schedules interviews, and centrally stores resumes. The process standardizes the recruitment pipeline, shortens hiring times, and enhances the candidate experience.
      * 4.3.2: Process Flow
  



      * 4.3.2: Process Description
Step 
	Step Name
	Detailed Description
	Role
	

	Start
	Triggered when a department submits an approved headcount request or vacancy occurs. 
	

	1
	Publish Job Position 
	HR creates a new Job Position in the Recruitment module, filling out job titles, responsibilities, prerequisites, target department, and internal recruitment teams. The position is then published directly onto the integrated Odoo Website portal. 
	HR Recruiter 
	2
	Submit Application 
	Candidates submit their resumes (CVs) through the web platform form, via direct employer email aliases, or external job hunting sources. 
	Candidate 
	3
	Receive and Parse CV 
	HR reviews submission pools or maps an incoming email directly to spawn a new digital Applicant record. Core identifiers (Full Name, Email, Phone, CV Attachment) are matched and dropped into the initial entry status. 
	HR Recruiter 
	4
	Pass Screening? (Gateway) 
	HR validates the CV parameters against the mandatory technical competencies, professional experience baselines, and academic requirements. 
	HR Recruiter 
	5
	Reject and Archive Application 
	- If passed: HR updates the candidate status by moving the Kanban card to the "Interview" stage.
- If failed: The record is marked as "Refused" (Archived), triggering a tracking log of the rejection reason.
	HR Recruiter 
	6
	Schedule & Invite Candidate 
	HR leverages the native Odoo Calendar overlay within the applicant file to block out interview slots and assign internal panelists. The system dispatches automated meeting invites containing location details or digital conference links (e.g., Odoo Discuss, Teams, Zoom). 
	HR Recruiter 
	7
	Conduct Interview 
	The designated panelists run the interview panels (can be structured across multiple consecutive phases like HR Screening, Technical Assessment, and Culture Fit). 
	Hiring Manager 
	8
	Evaluation Result? 
	Interviewers log structured qualitative performance scorecards and approval feedback directly into the applicant logs. If failed, the applicant is archived. If approved, the pipeline progresses to the "Offer" phase. 
	HR Recruiter 
	9
	Generate & Send Offer Letter 
	HR generates a structured job offer utilizing system document templates—populating variables such as Job Title, compensation package, start date, and benefit structures—and forwards it to the candidate. 
	HR Recruiter 
	10
	Accept Offer? 
	- If accepted: The candidate card moves into the "Hired" stage.
- If declined: The card moves to "Refused", tracking details like salary mismatch, location issues, or alternative offers.
	HR Recruiter 
	11
	Convert to Employee Profile 
	Upon entering the "Hired" stage, HR executes the native "Create Employee" command. The system ports core biographical data directly into a brand-new profile record (hr.employee). A new Employment Contract (hr.contract) is mapped out, triggering onboarding workflows. 
	HR Recruiter 
	

	End 
	The active candidate loop is concluded, handing execution off to formal Employee Onboarding protocols. 
	

	





Important notes for the deployment phase:
* Automated emails by stage: It can be configured so that when a candidate moves to a certain stage (e.g., "Interview"), the system automatically sends an invitation or notification email. This is a Config function (requires email template creation and automation activation).
* Online surveys (Interview Survey): If you want to send survey questionnaires to candidates before the interview, you can enable the Surveys function and integrate it with Recruitment. This is also a Config function.
* LinkedIn / TopCV / VietnamWorks integration: Odoo Enterprise has built-in LinkedIn integration (drag and drop profiles from LinkedIn). For TopCV and VietnamWorks, custom development (custom API webhook) is required and it is recommended to include them in the Future phase.
* Recruitment reports: Odoo provides ready-made reports (Reporting > Recruitment) on average recruitment time, candidate sources, and effectiveness of each stage – ready to use.
________________


1. HR-BP-04: Quy trình Quản lý Nghỉ phép (Time Off)
1.1 Mô tả quy trình
Quy trình này quản lý vòng đời đơn nghỉ phép của nhân viên, từ việc đăng ký, phê duyệt qua quy trình 2 cấp (Manager → HR), cập nhật số dư phép (allocation), cho đến việc đồng bộ sang module Work Entry và Payroll. Hệ thống hỗ trợ nhiều loại nghỉ (nghỉ phép năm, nghỉ ốm, nghỉ thai sản, nghỉ không lương, ngày lễ…), nhiều đơn vị thời gian (theo ngày / nửa ngày / theo giờ), và cơ chế tự động cấp phép theo thời gian (accrual plan).
1.2 Process Flow
[Sơ đồ luồng — sẽ vẽ bằng draw.io/Lucidchart]
1.3 Process Description
Step
	Step Name
	Detailed Description
	Role
	Start
	Khởi tạo nhu cầu nghỉ
	Nhân viên có nhu cầu nghỉ phép (nghỉ phép năm, nghỉ ốm, nghỉ việc riêng…) và muốn đăng ký với hệ thống.
	 
	1
	Tạo đơn nghỉ phép
	Nhân viên đăng nhập Odoo, truy cập module Time Off → tạo Leave Request. Khai báo: Leave Type (loại phép), Date From / Date To, Half-day (nửa ngày), Hourly (theo giờ), Reason (lý do — public hoặc private). Hệ thống tự động tạo calendar event tương ứng với đơn nghỉ.
	Employee
	2
	Kiểm tra leave balance
	Hệ thống tự động compute virtual_remaining_leaves = total allocation – used – pending. Nếu loại phép có requires_allocation = True và balance không đủ → cảnh báo và chặn submit. Riêng Sick Leave có thể có cấu hình không cần allocation.
	Odoo System
	3
	Số dư đủ?
	(Gateway) Hệ thống kiểm tra hợp lệ. Nếu không đủ balance → quay lại Step 1 để điều chỉnh hoặc huỷ. Nếu đủ → Submit for Approval (state: draft → confirm).
	Odoo System
	4
	Manager duyệt cấp 1
	Manager trực tiếp (parent_id) nhận thông báo và mở đơn để xem xét. Hai lựa chọn: (1) Approve → state chuyển sang validate1; (2) Refuse → state chuyển sang refuse với lý do bắt buộc. Hệ thống ngăn self-approval (manager không thể duyệt đơn của chính mình).
	Manager
	5
	HR duyệt cấp 2
	Với các loại phép có cấu hình double_validation = True (ví dụ: nghỉ thai sản, nghỉ dài ngày), HR mở đơn đã được Manager duyệt và quyết định approve cuối cùng. Khi HR approve → state = validate, hệ thống tự động trừ leave balance, tạo work entry loại LEAVE100/LEAVE110/LEAVE120…, và gửi calendar invite cho nhân viên.
	HR Officer
	6
	Trừ leave balance & sinh work entry
	Sau khi state = validate, hệ thống tự động: (a) giảm allocation tương ứng (number_of_days đã được tính loại trừ weekends và public holidays); (b) tạo hr.work.entry với type theo loại phép (LEAVE100 Paid Time Off, LEAVE110 Sick, LEAVE120 Unpaid, LEAVE200 Maternity, LEAVE210 Paternity); (c) đẩy event lên dashboard và calendar phòng ban.
	Odoo System
	7
	Theo dõi & xử lý đặc biệt
	Trong thời gian đơn đã approved nhưng chưa hết hiệu lực, nhân viên có thể yêu cầu Cancel. HR có quyền: Reset to Draft (yêu cầu duyệt lại), Cancel Approved (hoàn lại balance), hoặc giữ nguyên. Mọi thay đổi được ghi log tracking và post message cho follower.
	HR Officer / Employee
	8
	Đồng bộ sang Payroll
	Khi đến kỳ tính lương, các work entries loại LEAVE đã validated sẽ được Payroll đọc để áp dụng salary rules tương ứng: LEAVE100 = PAID_LEAVE (không trừ lương), LEAVE120 = UNPAID_LEAVE (trừ lương theo công thức base / working_days × unpaid_days), LEAVE110 trong hạn mức không trừ lương.
	Odoo System
	End
	Kết thúc quy trình
	Đơn nghỉ đã hoàn tất vòng đời, dữ liệu lưu lại làm lịch sử và phục vụ báo cáo (số ngày nghỉ trung bình, tỉ lệ nghỉ phép theo phòng ban…).
	 
	1.4 Cấu hình loại nghỉ phép (Leave Types)
Theo Luật Lao động Việt Nam 2019 và đặc thù của Học Bá, cấu hình tối thiểu các loại phép sau:
Leave Type
	Code
	Requires Allocation
	Approval
	Allocation/năm
	Ghi chú
	Nghỉ phép năm
	ANNUAL
	True
	Manager
	12-16 ngày (theo thâm niên)
	Có thể carryover, accrual plan hàng tháng
	Nghỉ ốm có lương
	SICK
	False
	Manager
	—
	Cần đính kèm giấy bác sĩ nếu > 1 ngày
	Nghỉ không lương
	UNPAID
	False
	Manager → HR
	—
	Trừ lương theo công thức prorated
	Nghỉ thai sản
	MATERNITY
	True
	Manager → HR
	180 ngày
	Theo luật BHXH VN
	Nghỉ vợ sinh
	PATERNITY
	True
	Manager
	5-14 ngày
	Tuỳ trường hợp sinh thường/mổ
	Nghỉ kết hôn
	MARRIAGE
	False
	Manager
	3 ngày
	Có lương
	Nghỉ tang
	BEREAVEMENT
	False
	Manager
	3 ngày
	Có lương
	Ngày lễ
	PUBLIC_HOLIDAY
	False
	Auto
	11 ngày
	Hệ thống tự generate, không trừ balance
	Nghỉ bù
	COMP_TIME
	True
	Manager
	—
	Convert từ OT (nếu cấu hình)
	1.5 Lưu ý triển khai
•         Two-level approval workflow: Phải cấu hình double_validation = True cho các loại phép nhạy cảm như UNPAID và MATERNITY. Workflow chuẩn: draft → confirm → validate1 (Manager) → validate (HR).
•         Accrual Plan cho nghỉ phép năm: Cấu hình accrual_plan_id để hệ thống tự động cộng 1 ngày phép/tháng cho nhân viên (12 ngày/năm cơ bản). Thâm niên đủ năm sẽ cấp thêm theo level rules.
•         Carryover policy: Học Bá nên thống nhất chính sách carry over phép sang năm sau (đề xuất: tối đa 5 ngày, hết hạn 31/03 năm sau).
•         Public Holiday auto-generation: Hệ thống tự generate LEAVE300 cho 11 ngày lễ VN. Cần cấu hình resource.calendar.leaves đúng năm. Nếu ngày lễ rơi vào cuối tuần → không generate.
•         Private leave reason: Đối với nghỉ ốm/lý do cá nhân, dùng field private_name để chỉ HR thấy, Manager chỉ thấy đơn ở dạng tổng quát.
•         Validation tính duration: Số ngày nghỉ tự động loại trừ Weekends và Public Holidays khi tính number_of_days.
•         Calendar integration: Mỗi đơn approved tạo 1 calendar.event hiển thị trên dashboard phòng ban và lịch cá nhân của nhân viên.


 
2. HR-BP-05: Quy trình Tính Lương (Payroll)
2.1 Mô tả quy trình
Đây là quy trình phức tạp nhất trong hệ thống HRM, có vai trò tính toán bảng lương hàng tháng cho 3 nhóm nhân sự khác nhau của Học Bá: Office Staff (lương cố định), Teacher (lương theo giờ dạy), Teaching Assistant (lương theo giờ). Quy trình tuân thủ đầy đủ pháp luật lao động Việt Nam: bảo hiểm bắt buộc (BHXH/BHYT/BHTN), thuế TNCN lũy tiến 7 bậc, giảm trừ gia cảnh, trần đóng bảo hiểm. Hỗ trợ các trường hợp đặc biệt: lương thử việc (probation 85%), Net-to-Gross, thưởng Tết/tháng 13, prorate vào/nghỉ giữa tháng, multi-bank split.
2.2 Process Flow
[Sơ đồ luồng — sẽ vẽ bằng draw.io/Lucidchart]
2.3 Process Description
Step
	Step Name
	Detailed Description
	Role
	Start
	Đến kỳ tính lương
	Vào ngày X hàng tháng (ví dụ ngày 28), HR khởi động kỳ tính lương cho tháng vừa kết thúc.
	 
	1
	Tạo Payroll Period (Batch)
	HR truy cập Payroll → Payslip Batches → tạo hr.payslip.run mới. Khai báo: Tên batch (ví dụ 'Lương tháng 10/2026'), Date From / Date To (01/10 – 31/10), Department filter (nếu cần). Một batch sẽ chứa nhiều payslip của các nhân viên thuộc phạm vi.
	HR Officer
	2
	Đóng work entries của kỳ
	HR đối soát và xác nhận tất cả work entries trong period đã ở state 'validated'. Nếu còn entries ở state 'conflict' hoặc 'draft' → phải xử lý xong trước khi tính lương. Đây là bước critical để đảm bảo dữ liệu đầu vào chính xác.
	HR Officer
	3
	Generate payslips hàng loạt
	Hệ thống chạy chức năng Generate Payslips → tự động tạo hr.payslip cho từng nhân viên trong batch. Mỗi payslip tự động: (a) chọn salary_structure_id theo contract (Office Staff Structure vs Teacher Structure); (b) đọc work entries trong period; (c) đọc inputs (bonus, advance, penalty); (d) chuẩn bị tính toán.
	Odoo System
	4
	Tính Gross Salary
	Hệ thống áp dụng salary rules theo cấu trúc lương: Office Staff: BASE (lương cơ bản theo contract_wage) + ALLOWANCES (ăn trưa, đi lại, điện thoại, chức vụ, thâm niên) + OT (overtime hours × hourly_rate × multiplier) + COMMISSION + BONUS. Teacher/TA: TEACH_HOURS (validated teaching hours × hourly_rate) + FIXED_BASE (nếu có) + EXTRA_HOURS_BONUS (nếu vượt standard hours).
	Odoo System
	5
	Tính bảo hiểm bắt buộc
	Insurance Base = lương cơ bản + phụ cấp chức vụ + thâm niên (KHÔNG bao gồm phụ cấp ăn trưa, đi lại, điện thoại, OT). Áp trần: BHXH/BHYT cap = 20 × lương cơ sở (20 × 2.340.000 = 46.800.000). BHTN cap = 20 × lương tối thiểu vùng I (20 × 4.960.000 = 99.200.000). Tỉ lệ nhân viên đóng: BHXH 8%, BHYT 1.5%, BHTN 1% (tổng 10.5%). Tỉ lệ công ty đóng: BHXH 17.5%, BHYT 3%, BHTN 1% (tổng 21.5%). Tỉ lệ và lương cơ sở phải cấu hình được, KHÔNG hardcode.
	Odoo System
	6
	Tính giảm trừ
	Giảm trừ bản thân: 11.000.000 VND/tháng. Giảm trừ người phụ thuộc: 4.400.000 VND × số người. Người phụ thuộc lấy từ hr.employee.dependent_ids. Thay đổi số người phụ thuộc có hiệu lực từ tháng đăng ký.
	Odoo System
	7
	Tính Thuế TNCN
	Taxable Income = Gross – Insurance (NV đóng) – Personal Deduction – Dependent Deduction. Nếu taxable <= 0 → PIT = 0. Nếu > 0 → áp biểu thuế lũy tiến 7 bậc: 0-5tr (5%), 5-10tr (10%), 10-18tr (15%), 18-32tr (20%), 32-52tr (25%), 52-80tr (30%), >80tr (35%). Lương OT KHÔNG cộng vào insurance base, nhưng vẫn chịu thuế TNCN.
	Odoo System
	8
	Tính Net Salary
	Net = Gross – Insurance (NV đóng) – PIT – Other Deductions (loan, advance, penalty, meal voucher, unpaid leave). Hệ thống hiển thị đầy đủ breakdown trên payslip line cho từng rule.
	Odoo System
	9
	HR review & adjust
	HR mở từng payslip review breakdown. Có thể: (a) Add input (one-time bonus, penalty, referral bonus); (b) Override input value; (c) Check variation report so sánh với tháng trước → phát hiện bất thường. Nếu sai → reset draft, sửa, compute lại.
	HR Officer
	10
	Approve Payslips
	Khi mọi payslip OK, HR confirm payslip → state chuyển 'draft' → 'verify' → 'done'. Có thể bulk approve cả batch. Khi done, payslip locked, work entries liên quan chuyển state 'payslip_included' (không sửa được nữa).
	HR Manager
	11
	Generate báo cáo & file ngân hàng
	Hệ thống xuất: (a) PDF Payslip cho từng nhân viên (theo template chuẩn VN); (b) File chuyển khoản hàng loạt cho ngân hàng (VCB, BIDV, TCB… với format đặc thù từng bank); (c) Báo cáo BHXH (tổng hợp BHXH/BHYT/BHTN của công ty + NV); (d) Báo cáo Thuế TNCN (mẫu 05/KK-TNCN).
	Odoo System
	12
	Gửi payslip cho nhân viên
	HR trigger gửi payslip qua email tự động. Nhân viên cũng có thể truy cập Employee Portal để xem payslip cá nhân (gross, net, breakdown deductions). Tài chính nhận file ngân hàng để upload lên hệ thống ngân hàng và thực hiện chi.
	Odoo System / Finance
	13
	Lock period
	Sau khi tất cả payslip = 'done', hệ thống auto-lock payroll period. Không cho phép tạo payslip mới hoặc sửa work entry trong period đã lock. Unlock chỉ HR Manager được thực hiện, có audit trail ghi log lý do.
	Odoo System
	End
	Kết thúc kỳ lương
	Dữ liệu lương được archive làm lịch sử, phục vụ báo cáo nội bộ và quyết toán thuế cuối năm.
	 
	2.4 Salary Structure cho từng nhóm nhân sự
2.4.1 Office Staff Structure
Code
	Tên
	Loại
	Công thức
	BASE
	Lương cơ bản
	Earning
	contract.wage × working_days_ratio
	ALLOW_LUNCH
	Phụ cấp ăn trưa
	Earning
	Cố định, KHÔNG tính BH
	ALLOW_TRANSPORT
	Phụ cấp đi lại
	Earning
	Cố định, KHÔNG tính BH
	ALLOW_POSITION
	Phụ cấp chức vụ
	Earning
	Cố định, CÓ tính BH
	OT
	Lương overtime
	Earning
	OT_hours × hourly_rate × multiplier (1.5x/2x/3x)
	BHXH
	BHXH NV đóng
	Deduction
	min(insurance_base, 46.8M) × 8%
	BHYT
	BHYT NV đóng
	Deduction
	min(insurance_base, 46.8M) × 1.5%
	BHTN
	BHTN NV đóng
	Deduction
	min(insurance_base, 99.2M) × 1%
	PIT
	Thuế TNCN
	Deduction
	Lũy tiến 7 bậc trên taxable income
	UNPAID_LEAVE
	Trừ nghỉ không lương
	Deduction
	base / working_days × unpaid_days
	NET
	Lương thực nhận
	Total
	Gross − Insurance − PIT − Other
	2.4.2 Teacher Structure
Code
	Tên
	Loại
	Công thức
	TEACH_HOURS
	Lương giờ dạy
	Earning
	validated_teaching_hours × hourly_rate
	FIXED_BASE
	Lương cố định (nếu có)
	Earning
	Cố định theo contract
	EXTRA_HOURS
	Bonus giờ vượt
	Earning
	max(0, actual − standard) × extra_rate
	HOLIDAY_OT
	OT ngày lễ
	Earning
	hours × hourly_rate × 3.0
	BHXH/BHYT/BHTN
	Bảo hiểm
	Deduction
	Tính trên contract base, không theo actual earnings
	PIT
	Thuế TNCN
	Deduction
	Lũy tiến 7 bậc
	NET
	Lương thực nhận
	Total
	Gross − Insurance − PIT
	Lưu ý đặc biệt: Giáo viên 0 giờ dạy trong tháng → gross = 0, nhưng vẫn phải tính insurance trên contract base (đúng luật BHXH VN — đang đóng BH thì vẫn phải đóng).
2.5 Edge Cases
2.5.1 Lương thử việc (Probation)
•         Probation rate mặc định 85%, configurable per contract.
•         Gross salary trong thời gian thử việc = official_gross × 0.85.
•         Transition giữa tháng (ví dụ ngày 15 chuyển chính thức): prorate ngày 1-14 thử việc, ngày 15-31 chính thức.
2.5.2 Net-to-Gross
•         Áp dụng cho nhân viên thoả thuận lương Net (đặc biệt giáo viên nước ngoài).
•         Tính ngược: Net → cộng thuế và BH → ra Gross.
•         Nếu Net dưới ngưỡng thuế: gross = net / (1 - insurance_rate_employee).
•         Nếu Net trên ngưỡng: dùng iterative algorithm để hội tụ.
2.5.3 Thưởng Tết / Lương tháng 13
•         13th month salary cho nhân viên làm đủ 12 tháng.
•         Prorate cho nhân viên vào/nghỉ giữa năm: bonus = base × (months_worked / 12).
•         Thuế trên bonus: tính cùng thu nhập regular của tháng nhận bonus (KHÔNG tách riêng).
•         Có thể tạo bonus payslip riêng (separate hr.payslip) nếu muốn track riêng.
2.5.4 Pro-rata vào/nghỉ giữa tháng
•         New employee mid-month: salary = base / working_days_in_month × actual_worked_days.
•         Terminated employee: prorated theo ngày làm thực tế, tính cả leave encashment (unused annual leave × daily_rate).
2.5.5 Multi-bank Split
•         Lương được chia sang nhiều tài khoản theo % cấu hình trong hr.employee.bank_account_ids.
•         Validate tổng % = 100% trước khi gen file ngân hàng.
•         Trường hợp 1 tài khoản → 100% vào tài khoản primary.
2.6 Lưu ý triển khai
•         Configurable rates: BHXH/BHYT/BHTN rates, lương cơ sở, lương tối thiểu vùng, biểu thuế TNCN — TẤT CẢ phải cấu hình được trong settings, KHÔNG hardcode. Pháp luật VN thay đổi định kỳ.
•         Insurance Cap formula: Trần BHXH/BHYT thay đổi theo lương cơ sở (do Chính phủ điều chỉnh). Trần BHTN thay đổi theo lương tối thiểu vùng (cần cấu hình theo từng vùng I/II/III/IV).
•         Dependent Management: Tạo model hr.employee.dependent (extend hr.employee) để track danh sách người phụ thuộc với hiệu lực từ ngày cụ thể.
•         Payslip Locking: Strict rule — chỉ HR Manager mới được unlock period, mọi unlock đều ghi audit log với lý do và timestamp.
•         Bank File Format: Mỗi ngân hàng (VCB, BIDV, TCB, MB, ACB…) có format khác nhau (TXT, XLSX, XML). Cần tạo template per bank, có thể là Future phase.
•         Quyết toán thuế cuối năm: Hệ thống cần xuất được Mẫu 05/QTT-TNCN cuối năm. Đây có thể là phase 2 hoặc custom report.
•         Insurance Base Field Configuration: Mỗi allowance phải có flag insurance_applicable (boolean) để xác định có cộng vào insurance base hay không. Ví dụ: ALLOW_POSITION = True, ALLOW_LUNCH = False.


 
3. HR-BP-06: Quy trình Quản lý Mục Công (Work Entry)
3.1 Mô tả quy trình
Module Work Entry đóng vai trò là tầng trung gian (middleware) giữa các nguồn dữ liệu công (Attendance, Time Off, Contract Calendar) và Payroll. Mỗi work entry là một mục công đại diện cho 1 khoảng thời gian làm việc hoặc nghỉ của 1 nhân viên (employee, date, type, duration). Hệ thống hỗ trợ generate tự động qua cron job, phát hiện conflict overlapping, phân biệt source (calendar vs attendance) cho 2 nhóm Office Staff (lấy từ calendar) và Teacher/TA (lấy từ attendance thực tế).
3.2 Process Flow
[Sơ đồ luồng — sẽ vẽ bằng draw.io/Lucidchart]
3.3 Process Description
Step
	Step Name
	Detailed Description
	Role
	Start
	Cần dữ liệu công cho kỳ lương
	Đầu tháng (hoặc theo cron schedule), hệ thống cần tạo work entries cho cả tháng làm việc dựa trên 3 nguồn: contract calendar, attendance, leave.
	 
	1
	Generate work entries tự động (Cron)
	Cron job 'Generate Missing Work Entries' chạy hàng ngày/hàng tuần. Với mỗi nhân viên có active contract, hệ thống: (a) đọc resource_calendar_id (lịch làm việc); (b) đọc work_entry_source ('calendar' / 'attendance' / 'hybrid'); (c) generate work entries cho date_generated_from → date_generated_to.
	Odoo System
	2
	Determine Source & Type
	Office Staff (work_entry_source = 'calendar'): tạo WORK100 (Normal Working Day) 8h/ngày theo calendar. Teacher (source = 'attendance'): chờ check-in/out, sau đó tạo WORK200 (Teaching Hours) theo actual worked_hours. Hybrid: kết hợp cả hai.
	Odoo System
	3
	Áp dụng Leave Overrides
	Khi có hr.leave đã validated trong date range, hệ thống tạo work entry loại LEAVE thay thế WORK trong khung giờ tương ứng. Ví dụ: nhân viên xin nghỉ ốm ngày 15/10 → ngày 15/10 sẽ có LEAVE110 thay vì WORK100.
	Odoo System
	4
	Áp dụng Public Holidays
	Hệ thống đọc resource.calendar.leaves loại 'public_holiday'. Generate LEAVE300 (Public Holiday) cho 11 ngày lễ VN. Nếu ngày lễ rơi vào cuối tuần → không generate. Nếu nhân viên đi làm ngày lễ → vẫn có WORK + thêm OT entry tính 300%.
	Odoo System
	5
	Manual entry / Import
	Trường hợp đặc biệt cần HR can thiệp: (a) Manual entry: HR tạo work entry trực tiếp (ví dụ giáo viên dạy thay, làm thêm…); (b) Import from bộ phận Vận hành: import file Excel teaching hours từ bộ phận Vận hành & SP (lịch dạy thực tế).
	HR Officer
	6
	Conflict Detection
	Sau khi generate/manual entry, hệ thống tự động scan overlapping entries (cùng employee, cùng date, time intervals chồng nhau). Nếu phát hiện → state chuyển 'conflict', không bao gồm trong payroll cho đến khi resolved.
	Odoo System
	7
	Resolve Conflicts
	HR mở danh sách entries state='conflict', review và xử lý: (a) Delete duplicate entry; (b) Adjust duration/time của 1 trong 2 entries; (c) Cancel entry không đúng. Sau khi xử lý, state quay về 'draft'.
	HR Officer
	8
	Validate Work Entries
	Khi đã sạch (không còn conflict), HR thực hiện bulk validate. State chuyển 'draft' → 'validated'. Chỉ entries 'validated' mới được Payroll đọc khi tính lương. Đối với Teaching Hours (WORK200), HR cần đối chiếu với báo cáo từ bộ phận Vận hành trước khi validate.
	HR Officer
	9
	Cancel Entries (nếu cần)
	Trong trường hợp đặc biệt (nhập sai, nhân viên không thực sự đi làm…), HR có thể cancel entry. State chuyển 'cancelled', không tính vào lương. Lưu ý: KHÔNG được unlink entries đã 'validated', chỉ được 'cancel'.
	HR Officer
	10
	Lock khi Payroll consume
	Khi Payroll tính lương và include work entry vào payslip, state chuyển 'validated' → 'payslip_included'. Lúc này entry locked, không thể sửa/xóa cho đến khi payslip bị reset draft.
	Odoo System
	End
	Work entry hoàn tất vòng đời
	Dữ liệu lưu lại làm lịch sử công, phục vụ báo cáo và audit.
	 
	3.4 Work Entry Types (Seed Data)
Hệ thống cấu hình sẵn các loại work entry sau:
Code
	Tên (EN)
	Tên (VN)
	is_work
	is_leave
	Mapping → Payroll Rule
	WORK100
	Normal Working Day
	Ngày làm việc thường
	True
	False
	BASE
	WORK110
	Overtime
	Tăng ca
	True
	False
	OT
	WORK200
	Teaching Hours
	Giờ dạy
	True
	False
	TEACH_HOURS
	LEAVE100
	Paid Time Off
	Nghỉ phép có lương
	False
	True
	PAID_LEAVE
	LEAVE110
	Sick Leave
	Nghỉ ốm
	False
	True
	—(không trừ)
	LEAVE120
	Unpaid Leave
	Nghỉ không lương
	False
	True
	UNPAID_LEAVE
	LEAVE200
	Maternity Leave
	Nghỉ thai sản
	False
	True
	—(BHXH chi trả)
	LEAVE210
	Paternity Leave
	Nghỉ vợ sinh
	False
	True
	—(không trừ)
	LEAVE300
	Public Holiday
	Ngày lễ
	False
	True
	PUBLIC_HOLIDAY
	LEAVE310
	Compensatory Time Off
	Nghỉ bù
	False
	True
	—(không trừ)
	3.5 Office Staff vs Teacher: 2 luồng riêng
3.5.1 Office Staff Flow
•         work_entry_source = 'calendar'
•         Hệ thống generate WORK100 mỗi ngày làm việc theo resource_calendar_id (mặc định 8h/ngày, T2-T6).
•         Check-in/out qua hr.attendance KHÔNG generate work entry mới (chỉ để track thực tế presence).
•         Nếu vắng mặt mà không có leave → vẫn có WORK100 (theo calendar), nhưng manager có thể chuyển thành UNPAID_LEAVE manually.
3.5.2 Teacher / TA Flow
•         work_entry_source = 'attendance'
•         KHÔNG có WORK100 mặc định. Chỉ có khi giáo viên thực sự check-in/out hoặc HR nhập tay.
•         Mỗi lần check-in/out → tạo WORK200 (Teaching Hours) với duration = worked_hours.
•         Nguồn dữ liệu thay thế: HR import file Excel từ bộ phận Vận hành chứa lịch giảng dạy thực tế cho từng giáo viên.
•         Validated teaching hours mới được tính lương. Draft entries → warning trên payslip.
3.5.3 Hybrid Flow (TA kiêm Office)
•         Một số TA vừa làm văn phòng vừa dạy → work_entry_source = 'hybrid'.
•         WORK100 từ calendar cho phần văn phòng + WORK200 từ attendance cho phần giảng dạy.
•         Lương tính tổng hợp 2 phần với 2 rate khác nhau.
3.6 Cron Jobs cần cấu hình
Tên Cron
	Tần suất
	Mô tả
	Generate Missing Work Entries
	Hàng ngày 02:00
	Tự generate WE cho tất cả nhân viên active contract, từ ngày generated_to gần nhất → today + N days
	Detect Work Entry Conflicts
	Hàng ngày 03:00
	Scan overlapping entries, gán state='conflict', gửi notification cho HR
	Notify Conflicts to HR
	Hàng ngày 09:00
	Email summary cho HR Officer danh sách conflicts cần xử lý
	Cleanup Cancelled Old Entries
	Hàng tuần
	Archive entries cancelled > 90 ngày
	

* REPORTS
Based on local requirement, following are reports that can use in the future


Template
CHAPTER 1 — PROJECT OVERVIEW
1.1 Project Background
* Giới thiệu trung tâm Học Bá
* Bối cảnh quản lý nhân sự
* Lý do triển khai Odoo HRM
1. Overview
1.1 Project Information
* English name: 
* Vietnamese name: 
* Project code: 
* Group name: 
* Software type:
1.2 Project Purpose
  
The purpose of this project is to design and develop a Student Management & Education System that supports the efficient operation of Học Bá Center’s Chinese language learning center. The system aims to streamline student enrollment, class management, course delivery, and academic progress tracking while providing an effective online learning environment for Chinese language study. By integrating administrative management with teaching and learning features, the system enhances communication between students, teachers, and administrators, improves learning outcomes, and ensures accurate, centralized data management to support long-term educational growth and scalability of the center.




















1.3 Project Stakeholders


2. Product Background
  
Học Bá Company operates a Chinese language learning center that provides Chinese courses for students at different proficiency levels, including beginner, intermediate, advanced, and HSK examination preparation. As the number of students, teachers, classes, and marketing activities continues to grow, the center faces increasing difficulties in managing its academic, operational, and business processes efficiently.
Currently, many activities at the center are handled through manual processes and disconnected tools such as spreadsheets, paper records, messaging applications, and standalone social media channels. Student information, class schedules, attendance, examination results, and learning materials are managed separately, while marketing and sales teams also rely on Facebook advertising channels such as Facebook Lead Ads Forms and Facebook Messenger to attract potential learners. These leads are often entered manually into the CRM system.
This fragmented management approach creates several problems. Academic staff face difficulties in arranging class schedules, assigning teachers, tracking attendance, managing examinations, and notifying students of study schedules and results. Teachers lack a centralized platform to manage teaching schedules, monitor student performance, and provide timely feedback. Students also do not have a convenient system to access learning materials, receive study notifications, or track their academic progress.
At the same time, manual lead processing from Facebook causes delays, data inconsistency, missing campaign tracking information, duplicate leads, and the absence of real-time reports for marketing effectiveness. As a result, the center lacks an integrated system that can connect marketing, sales, academic management, and daily operations in a unified workflow.




________________


1.2 Business Problem Statement
Các vấn đề hiện tại:
* dữ liệu phân tán
* quản lý thủ công
* khó kiểm soát tuyển dụng
* chấm công thiếu chính xác
* payroll phức tạp
* appraisal chưa chuẩn hóa


3. Existing Solutions Analysis (HRM-Relevant Filtering)
3.1 Current Internal System – Tiếng Trung Học Bá
Tiếng Trung Học Bá currently operates mainly as a learning content delivery platform, focusing on online Chinese language education for Vietnamese learners. The system supports academic content management but lacks dedicated Human Resource Management capabilities for internal staff operations.
HR-Related Actors
* Teachers / Instructors
* Academic Coordinators
* Sales & Admissions Staff
* Administrative Staff
* Center Managers
* IT/System Administrators
Current HR-Related Capabilities
* Basic teacher/course assignment tracking
* Manual class schedule coordination
* Manual attendance follow-up through spreadsheets/chat tools
* Staff communication through external platforms (Zalo/Messenger)
HR Limitations
* No centralized employee database
* Recruitment process is handled manually (CV collection via email/Facebook/Zalo)
* Attendance tracking is fragmented and lacks automation
* Leave requests are processed manually via chat or paper forms
* Payroll calculation depends heavily on Excel/manual validation
* No performance tracking for teaching staff or operational staff
Advantages
* Staff are already familiar with operational workflow
* Existing educational data is structured enough for migration
Disadvantages
* HR operations are disconnected across multiple tools
* High administrative workload
* Error-prone payroll and attendance reconciliation
* Lack of reporting for workforce planning
Key Takeaways for HRM Development
The new Odoo HRM system must:
* Centralize all employee information
* Digitize recruitment workflow
* Automate attendance and leave management
* Standardize payroll calculation
* Provide workforce reporting dashboards
________________


3.2 ClassIn (Benchmark for Operational Staff Coordination)
ClassIn provides strong educational operational management with automation features that reduce coordination workload.
Relevant HR Features
* Teacher scheduling automation
* Attendance logging for instructors and classes
* Workload allocation visibility
* Automated academic activity reporting
Advantages
* Reduces manual coordination effort
* Improves teaching resource utilization
* Provides visibility into staff workload
Disadvantages
* Limited HR customization
* Payroll and internal HR policy management are weak
* Expensive licensing structure
Key Takeaways for HRM Development
The Odoo HRM system should adopt:
* Automated teacher scheduling support
* Attendance-to-workload synchronization
* Performance activity reporting for teachers
But extend further with:
* Payroll integration
* Leave approval workflows
* Recruitment pipeline management
________________


3.3 Manabie (Benchmark for Strategic HR Analytics)
Manabie demonstrates strong enterprise-level operational visibility and data-driven management.
Relevant HR Features
* Staff performance analytics
* Operational KPI dashboards
* Workforce utilization reporting
* Role-based access management
Advantages
* Supports management decision-making
* Improves staffing optimization
* Enables long-term HR planning
Disadvantages
* High complexity
* Requires significant staff digital literacy
* Difficult to adapt to smaller center workflows
Key Takeaways for HRM Development
The Odoo HRM system should provide:
* HR KPI dashboards
   * Employee attendance trends
   * Leave frequency
   * Recruitment conversion rates
   * Payroll cost analysis
* Management-level reporting for workforce health monitoring
while maintaining:
* Simplicity
* Custom workflow flexibility for Học Bá
________________


3.4 Consolidated GAP Identified for Học Bá HRM
From the analysis above, the major HR gaps are:
Area
	Current Issue
	Required Odoo HRM Solution
	Recruitment
	Manual applicant handling
	Recruitment pipeline automation
	Employee Records
	Fragmented files/spreadsheets
	Centralized employee master data
	Attendance
	Manual tracking
	Automated attendance logging
	Leave Management
	Informal requests
	Digital leave workflow approval
	Payroll
	Excel-based calculation
	Payroll rule automation
	Reporting
	No workforce analytics
	Dashboard & KPI reporting
	________________


Final Strategic Insight
The proposed Odoo HRM implementation should not replicate LMS functionality, because Học Bá already has learning delivery capability.
Instead, it should solve the operational bottleneck by becoming the internal workforce management backbone, integrating:
* Recruitment
* Employee administration
* Attendance
* Leave management
* Payroll
* HR analytics
This creates a scalable operational foundation for Học Bá’s future growth.


________________




________________


1.4 Project Scope


In Scope
Module 1 — Employees
* Employee Profile
* Department
* Contract
* Role Assignment
________________


Module 2 — Recruitment
* Job Position
* Applicant Tracking
* Interview Workflow
* Offer Management
________________


Module 3 — Attendance
* Check-in/out
* Shift Management
* Work Entry Rules
________________


Module 4 — Payroll
* Salary Structure
* Allowance
* Deduction
* Payslip
________________


Module 5 — Time Off
* ________________


Out of Scope
* CRM
* Accounting
* LMS
* Student Management
1.4 Project Scope
The project focuses on implementing the Human Resource Management (HRM) system on Odoo to centralize employee administration, streamline workforce operations, and improve internal management efficiency for Học Bá Chinese Language Center.
The scope covers five core HR modules essential for supporting staff lifecycle management, from recruitment to payroll processing and leave administration.
________________


In Scope
Module 1 — Employees
This module manages all employee master data and organizational structure information.
Functional Scope
Employee Profile
* Maintain centralized employee records
* Personal information management
* Contact details
* Employment history
* Identification documents
* Emergency contact information
Department Management
* Create and manage organizational departments
* Define reporting hierarchy
* Assign employees to departments
* Department-based employee categorization
Contract Management
* Create employment contracts
* Contract type definition
* Contract duration tracking
* Contract renewal reminders
* Contract status monitoring
Role Assignment
* Assign job positions
* Define user access permissions
* Role-based system access control
* Responsibility allocation
Expected Outcomes
* Centralized employee information repository
* Improved employee data consistency
* Better organizational visibility
________________


Module 2 — Recruitment
This module digitizes the hiring process for teachers and operational staff.
Functional Scope
Job Position Management
* Create recruitment requests
* Define job descriptions
* Manage vacancy status
* Publish internal/external openings
Applicant Tracking
* Candidate profile collection
* CV storage and evaluation
* Application stage tracking
* Candidate pipeline visibility
Interview Workflow
* Schedule interviews
* Assign interviewers
* Interview evaluation forms
* Candidate assessment tracking
Offer Management
* Generate offer letters
* Approval workflow
* Offer acceptance tracking
* Candidate conversion to employee record
Expected Outcomes
* Faster hiring process
* Better recruitment transparency
* Improved applicant tracking accuracy
________________


Module 3 — Attendance
This module automates attendance recording and working time control.
Functional Scope
Check-in / Check-out
* Daily attendance logging
* Timestamp recording
* Late arrival / early leave detection
* Attendance history tracking
Shift Management
* Define work schedules
* Assign shifts to employees
* Flexible teaching schedule support
* Schedule conflict detection
Work Entry Rules
* Working hour calculation
* Overtime recognition
* Attendance exception handling
* Rule-based validation
Expected Outcomes
* Reduced manual attendance errors
* Accurate work-hour tracking
* Better operational discipline
________________


Module 4 — Payroll
This module automates salary processing and compensation calculation.
Functional Scope
Salary Structure
* Define salary components
* Fixed and variable salary setup
* Salary rule configuration
Allowance Management
* Teaching allowances
* Performance incentives
* Transportation and support allowances
Deduction Management
* Absence deductions
* Late attendance penalties
* Insurance / statutory deductions
Payslip Generation
* Monthly payroll calculation
* Payslip generation
* Payroll approval workflow
* Employee payroll history access
Expected Outcomes
* Payroll accuracy
* Reduced processing time
* Transparent compensation management
________________


Module 5 — Time Off
This module manages leave requests and approval workflows.
Functional Scope
Leave Request Management
* Submit leave applications
* Leave type selection
* Supporting document upload
Approval Workflow
* Manager review and approval
* Multi-level approval routing
* Leave status tracking
Leave Allocation
* Annual leave entitlement setup
* Sick leave allocation
* Special leave management
Leave Reporting
* Leave balance monitoring
* Department leave analytics
* Leave trend reports
Expected Outcomes
* Faster leave processing
* Reduced administrative burden
* Improved leave transparency
________________


Out of Scope
The following modules are excluded from this project phase:
* Learning Management System (LMS)
* Student Information Management
* Academic Scheduling System
* CRM / Lead Management
* Financial Accounting
* Parent / Student Portal
* Online Course Delivery Platform
* Marketing Automation
* Website Redesign
These areas may be considered in future implementation phases.
________________


Project Deliverables
The project will deliver:
* Configured Odoo HRM environment
* Custom workflow adjustments for Học Bá operations
* Employee data migration support
* User roles and access configuration
* Standard reports and dashboards
* User training documentation
* System testing and deployment support


________________




________________


1.6 Assumptions and Constraints
________________


CHAPTER 2 — BUSINESS PROCESS DISCOVERY (AS-IS)
(Phần khám phá quy trình thực tế Học Bá)
________________


2.1 Organizational Structure
Sơ đồ tổ chức
* Director
* HR
* Academic
* Teachers
* Sales
* Marketing
* Finance
________________


2.2 Current Recruitment Process
Process Flow
(vẽ BPMN)
Process Description
* Trigger
* Steps
* Decision points
* Outputs
Pain Points
________________


2.3 Current Employee Management Process
Process Flow
Description
Pain Points
________________


2.4 Current Attendance Process
Process Flow
Description
Pain Points
________________


2.5 Current Payroll Process
Process Flow
Description
Pain Points
________________


2.6 Current Performance Appraisal Process
Process Flow
Description
Pain Points
________________


CHAPTER 3 — ODOO STANDARD PROCESS ANALYSIS
(Phân tích Odoo hỗ trợ gì)
________________


3.1 Standard Employee Management in Odoo
________________


3.2 Standard Recruitment Workflow in Odoo
________________


3.3 Standard Attendance Workflow in Odoo
________________


3.4 Standard Payroll Workflow in Odoo
________________


3.5 Standard Time off Workflow in Odoo
________________




CHAPTER 4 — GAP ANALYSIS
(Phần quan trọng nhất)
________________


4.1 GAP Analysis Matrix
Bảng:
| Process | Business Need | Odoo Standard | GAP Level | Solution |
________________


4.2 FIT Analysis
(Dùng nguyên Odoo)
Template:
FIT-001
Requirement
Odoo Support
No change required
________________


4.3 CONFIGURATION GAP
(Chỉ cần cấu hình)
Template:
CFG-001
Requirement
Odoo Configuration Area
Configuration Detail
Expected Result
________________


4.4 CUSTOMIZATION GAP
(Phải code)
Template:
CUS-001
Business Need
Standard Limitation
Custom Solution
Business Benefit
________________


CHAPTER 5 — CONFIGURATION SPECIFICATION
(Mô tả cấu hình cụ thể)
________________


5.1 Employee Module Configuration
* Departments
* Job Positions
* Tags
* Employee Types
________________


5.2 Recruitment Configuration
* Stages
* Email Templates
* Interview Forms
________________


5.3 Attendance Configuration
* Work Schedules
* Shift Rules
* Late Policies
________________


5.4 Payroll Configuration
* Salary Structures
* Salary Rules
* Allowances
* Deductions
________________


5.5 Time off Configuration
* ________________


CHAPTER 6 — FUNCTIONAL SPECIFICATION
(Mô tả chức năng chi tiết)
________________


Template mỗi chức năng:
Function ID
________________


Function Name
________________


Module
________________


Actor
________________


Purpose
________________


Preconditions
________________


Trigger
________________


Main Flow
1. 2. 3. ________________


Alternative Flow
________________


Exception Flow
________________


Validation Rules
________________


Input Fields
| Field | Type | Required | Rule |
________________


Output
________________


Business Rules
________________


UI Reference
________________


Làm cho tất cả custom feature.
________________


CHAPTER 7 — TECHNICAL CUSTOMIZATION SPECIFICATION
________________


7.1 Custom Module Architecture
Module list:
* hb_hr_core
* hb_recruitment_ext
* hb_attendance_ext
* hb_payroll_ext
* hb_appraisal_ext
________________


7.2 Data Model Design
Template:
Model Name
Fields
| Field | Type | Description |
Relationships
________________


7.3 View Design
* Tree
* Form
* Kanban
* Dashboard
________________


7.4 Security Access Rules
| Role | Permission |
________________


7.5 Automation Logic
* Scheduled Action
* Trigger
* Server Action
________________


7.6 Business Logic / Algorithms
Ví dụ:
Payroll Formula:
* session rate
* bonus factor
* deduction factor
________________


CHAPTER 8 — UML / BPMN / SYSTEM DESIGN
________________


8.1 Use Case Diagram
________________


8.2 Activity Diagram
________________


8.3 Sequence Diagram
________________


8.4 BPMN Workflow
________________


8.5 System Architecture Diagram
________________


CHAPTER 9 — IMPLEMENTATION PLAN
________________


Phase 1 — Discovery
________________


Phase 2 — Configuration
________________


Phase 3 — Development
________________


Phase 4 — Testing
________________


Phase 5 — Deployment
________________


Phase 6 — Training
________________


CHAPTER 10 — RISK MANAGEMENT
| Risk | Impact | Mitigation |
________________


CHAPTER 11 — CONCLUSION
* Summary
* Expected benefits
* Future extension
________________


APPENDICES
Appendix A — Master Data
* Department list
* Position list
* Salary structures
________________


Appendix B — Screenshots
________________


Appendix C — Test Cases






Bộ tài liệu toàn diện
  



HỌC BÁ EDUCATION
Trung tâm đào tạo tiếng Trung trực tuyến
hoc-ba.edu.vn
Odoo 19 — HR Module Implementation
Bộ tài liệu toàn diện
Comprehensive Implementation Document
Module: Employees (hr.employee)  |  Phiên bản: 1.0  |  05/2025
	

Dự án
	Triển khai Odoo 19 HR — Học Bá Education
	Phiên bản
	Module
	Employees (hr.employee)
	1.0 — Draft
	Bao gồm
	AS-IS · Gap Analysis · Config Spec · Functional Spec · Technical Spec
	Ngày
	Đối tượng
	Business Owner · PM · BA · Functional Consultant · Developer · Tester
	05/2025
	

Bộ tài liệu gồm 5 phần
	

Phần
	Tên tài liệu
	Nội dung
	Đối tượng đọc chính
	P01
	Business Process Discovery (AS-IS)
	Org chart, quy trình hiện tại Học Bá, BPMN, pain points
	Business Owner · PM · BA
	P02
	Gap Analysis
	Bảng FIT/CFG/CUS, so sánh Odoo chuẩn vs yêu cầu VN + Học Bá
	BA · Functional Consultant
	P03
	Configuration Specification
	Chi tiết cấu hình từng CFG, FIT analysis, checklist triển khai
	Functional Consultant · PM
	P04
	Functional Specification
	Data dictionary, mô tả chức năng, phân quyền, test scenarios
	BA · Functional Consultant · Tester
	P05
	Technical Customization Specification
	Module structure, data model, Python code, XML views, test cases
	Developer · Tech Lead
	







Phần 01
Business ProcessDiscovery
Khám phá quy trình thực tế — AS-IS
	________________


1. CƠ CẤU TỔ CHỨC — Học Bá Education
	

Học Bá Education là trung tâm đào tạo tiếng Trung trực tuyến 100%, thành lập 06/2023, vận hành theo mô hình edtech startup. Quy mô ước tính 15–30 nhân sự bao gồm nhân viên cơ hữu, cộng tác viên và giảng viên thỉnh giảng.


  



1.1 Sơ đồ tổ chức 6 phòng ban
BAN GIÁM ĐỐC — Director / Founder
	HR Nhân sự
	Academic Học thuật
	Teachers Giảng viên
	Sales Kinh doanh
	Marketing Tiếp thị
	FinanceTài chính
	

Học Bá có 3 loại hình lao động chính: (1) Nhân viên cơ hữu — HĐLĐ không xác định thời hạn, có BHXH; (2) Cộng tác viên (CTV) — HĐDV, thanh toán theo tháng, không BHXH; (3) Giảng viên thỉnh giảng — HĐ ngắn hạn, thanh toán theo buổi.


1.2 Quy trình AS-IS — Tuyển dụng & Onboarding
  



Bước
	Thực hiện
	Công cụ hiện tại
	Vấn đề
	1. Phát sinh nhu cầu
	Giám đốc
	Zalo / Google Form
	⚠ Không có văn bản chính thức
	2. Đăng tuyển
	HR
	Facebook, Zalo cá nhân, email
	⚠ CV nộp qua nhiều kênh, không tập trung
	3. Sàng lọc CV
	HR
	Excel, Gmail
	⚠ Tiêu chí không chuẩn, dễ bỏ sót
	4. Phỏng vấn
	HR + Academic
	Zalo, Google Meet
	⚠ Kết quả ghi tay, không có hệ thống
	5. Thử việc
	Academic
	Zalo nhóm
	⚠ Không có checklist, không track deadline
	6. Ký hợp đồng
	HR + Finance
	Word → in → ký tay → scan
	⚠ Mất thời gian, dễ nhầm phiên bản
	7. Onboarding
	HR
	Zalo nhóm, email
	⚠ Không có checklist chuẩn
	8. Cập nhật hồ sơ
	HR
	Google Sheet, Notion
	⚠ Dữ liệu phân tán, không realtime
	

1.3 Pain Points tổng hợp
#
	Vấn đề
	Mô tả
	Mức độ
	PP-01
	Dữ liệu nhân sự phân tán
	Google Sheet, Zalo, Gmail, Notion — không có nguồn sự thật duy nhất
	Cao
	PP-02
	Không có quy trình chuẩn
	Mỗi lần tuyển dụng làm khác nhau, phụ thuộc cá nhân HR
	Cao
	PP-03
	Quản lý GV phức tạp
	Cơ hữu/thỉnh giảng/part-time có chế độ khác nhau nhưng quản lý chung
	Cao
	PP-04
	Hợp đồng thủ công
	Soạn/ký/lưu mất thời gian, dễ nhầm phiên bản
	Trung bình
	PP-05
	Không track thử việc
	Không có deadline và tiêu chí đánh giá rõ ràng
	Trung bình
	PP-06
	Báo cáo nhân sự chậm
	Tổng hợp thủ công từ nhiều file mỗi khi cần báo cáo
	Cao
	PP-07
	Tính lương GV thủ công
	Đếm buổi dạy trên Excel, dễ sai sót, mất 3–5 ngày/tháng
	Cao
	________________




2.1 Odoo Standard Process — TO-BE
TO-BE: Quy trình chuẩn Odoo 19 — Employee Management 

  

Luồng tuyển dụng → onboarding (Recruitment → Employee)
Odoo xử lý toàn bộ vòng đời nhân sự trong một hệ thống thống nhất. Khi có nhu cầu tuyển, HR tạo Job Position trong module Recruitment, gắn vào phòng ban và lịch tuyển dụng. Ứng viên nộp hồ sơ qua website tích hợp sẵn, pipeline Kanban tự động hiển thị theo từng giai đoạn (Mới → Phỏng vấn → Offer → Từ chối). Khi ứng viên được chấp nhận, chỉ cần nhấn "Tạo nhân viên" — toàn bộ thông tin tự động điền vào employee form, không cần nhập lại.
Hồ sơ nhân viên (Employee Form)
Mỗi nhân viên có một bản ghi duy nhất gồm 6 tab: thông tin chung, thông tin công việc (phòng ban, lịch làm, địa điểm), thông tin cá nhân (CMND, visa, địa chỉ), resume & kỹ năng, cài đặt HR (loại nhân viên, tài khoản portal), và tab Certifications (mới từ v19). Smart buttons trên đầu form liên kết trực tiếp sang hợp đồng, bảng lương, nghỉ phép, chấm công.
Hợp đồng (Contracts — tích hợp vào Employee từ v19)
Từ Odoo 19, hợp đồng được tích hợp trực tiếp vào hồ sơ nhân viên với cơ chế versioning — mỗi lần thay đổi lương hoặc điều khoản tạo ra một phiên bản mới, giữ lại lịch sử đầy đủ. Hợp đồng gắn với Salary Structure để tự động tính lương.
Lịch làm việc & Chấm công (Work Schedule + Attendance)
HR cấu hình Work Schedule (ca ngày, ca tối, part-time) và gán cho từng nhân viên. Chấm công qua kiosk, PIN, thẻ badge hoặc nhập tay. Odoo tự động tính giờ làm thực tế so với lịch chuẩn, flagging đi muộn và OT.
Nghỉ phép (Time Off)
Cấu hình các loại phép (phép năm, ốm, không lương, thai sản), thiết lập Accrual Plans tích lũy tự động theo thâm niên. Nhân viên tự đăng ký qua portal, quản lý phê duyệt trên Odoo, lịch nghỉ phép hiển thị trên calendar chung.
Đánh giá (Appraisal)
Tạo chu kỳ đánh giá định kỳ (3 tháng thử việc, 6 tháng, 1 năm), gửi form tự đánh giá cho nhân viên và form đánh giá cho quản lý. Kết quả gắn với hồ sơ nhân viên và có thể liên kết sang điều chỉnh lương.
Phân quyền (Access Rights)
Ba cấp quyền trong module Employees: Employee (chỉ xem hồ sơ bản thân), Officer (quản lý nhân viên trong phạm vi), Administrator (toàn quyền). Kết hợp với multi-company để phân quyền theo công ty.




3. Bảng Gap tổng hợp (18 gaps — phân loại theo pháp lý VN + đặc thù Học Bá)
#
	Yêu cầu
	Odoo Standard
	Phân loại
	GAP
	Giải pháp
	G-01
	Số CCCD 12 số (validate)
	identification_id — text tự do
	Định danh VN
	Low
	CFG-001
	G-02
	Ngày cấp CCCD
	Không có field
	Pháp lý BHXH
	High
	CUS-001
	G-03
	Nơi cấp CCCD
	Không có field
	Pháp lý BHXH
	High
	CUS-001
	G-04
	MST cá nhân
	Không có field riêng
	Thuế TNCN
	High
	CUS-002
	G-05
	Địa chỉ 3 cấp VN (Tỉnh/Huyện/Xã)
	Chỉ 2 cấp State/City
	Hành chính VN
	Medium
	CFG-004
	G-06
	Địa chỉ tạm trú riêng
	Không phân biệt
	Lao động VN
	Medium
	CUS-001
	G-07
	Mã số BHXH (10 số)
	Không có field
	Pháp lý BHXH
	High
	CUS-001
	G-08
	Số thẻ BHYT
	Không có field
	Pháp lý BHXH
	Medium
	CUS-001
	G-09
	Lương đóng BH ≠ tổng lương
	wage không tách riêng
	Pháp lý BHXH
	High
	CUS-003
	G-10
	Salary Rules BH VN (NLĐ 10.5%, CTY 21.5%)
	Không có template VN
	Payroll VN
	High
	CFG-004
	G-11
	Biểu thuế TNCN 7 bậc lũy tiến
	Cần tự tạo Salary Rules
	Thuế TNCN
	High
	CFG-005
	G-12
	Người phụ thuộc (NPT) + giảm trừ gia cảnh
	Không có model NPT
	Thuế TNCN
	High
	CUS-002
	G-13
	Phân loại NV 4 nhóm Học Bá
	employee_type thiếu option
	Đặc thù Học Bá
	Low
	CFG-006
	G-14
	Chứng chỉ GV tiếng Trung (HSK, sư phạm)
	Certificate Level không phù hợp
	Đặc thù Học Bá
	Low
	CFG-007
	G-15
	Lương GV theo buổi dạy
	Payroll không có per-session
	Đặc thù Học Bá
	High
	CUS-004
	G-16
	Lịch dạy linh hoạt GV online
	Flexible schedule cần setup
	Đặc thù Học Bá
	Medium
	CFG-008
	G-17
	Thanh toán CTV qua Vendor Bill
	Vendor flow có sẵn, cần config
	Đặc thù Học Bá
	Low
	CFG-009
	G-18
	Báo cáo theo kỳ học
	Chỉ báo cáo tháng/quý
	Đặc thù Học Bá
	Medium
	CUS-004
	

FIT (7) — Dùng nguyên
	CFG (7) — Cấu hình
	CFG complex (2) — Payroll Rules
	CUS (4) — Cần code
	________________


FIT Analysis 
FIT-001 — Hồ sơ nhân viên cơ bản (tên, ảnh, email công việc, phòng ban, chức danh, quản lý trực tiếp): Odoo Employee Form đáp ứng đầy đủ. No change required.
FIT-002 — Cơ cấu tổ chức 6 phòng ban Học Bá: Departments + Org Chart view. No change required.
FIT-003 — Hộ chiếu (với GV có yếu tố nước ngoài): field passport_id có sẵn. No change required.
FIT-004 — Ký hợp đồng số từ xa với GV thỉnh giảng: Odoo Sign tích hợp sẵn. No change required.
FIT-005 — Quản lý nghỉ phép nhân viên cơ hữu (đăng ký, phê duyệt, số ngày còn lại): Time Off module đầy đủ. No change required.
FIT-006 — Chuyển ứng viên thành nhân viên từ Recruitment: 1-click "Create Employee". No change required.
FIT-007 — Employee portal tự phục vụ (xem phiếu lương, đăng ký phép): có sẵn. No change required.


Configuration Gap 
CFG-001 — Validate định dạng CCCD 12 số
* Odoo Configuration Area: Employee Form → field identification_id
* Configuration Detail: Thêm constraint Python hoặc regex validation ^\d{12}$ trên field; hiển thị warning nếu không đúng 12 chữ số
* Expected Result: Không thể lưu CCCD sai định dạng, giảm lỗi nhập liệu
CFG-002 — Salary Rules BHXH/BHYT/BHTN theo tỷ lệ VN 2025–2026
* Odoo Configuration Area: Payroll → Salary Structures → Salary Rules
* Configuration Detail: Tạo rules: BHXH_NLD = insurance_salary × 8%, BHYT_NLD = insurance_salary × 1.5%, BHTN_NLD = insurance_salary × 1%; tương tự cho NSDLĐ (17.5% / 3% / 1%); áp mức trần đóng BH (20 × lương cơ sở); cân nhắc cài viin_l10n_vn_hr_payroll để tiết kiệm thời gian
* Expected Result: Phiếu lương tự động khấu trừ đúng theo luật, giảm công kế toán
CFG-003 — Biểu thuế TNCN 7 bậc lũy tiến
* Odoo Configuration Area: Payroll → Salary Rules (Python code)
* Configuration Detail: Tạo rule TNCN với Python code tính lũy tiến 7 bậc (5%/10%/15%/20%/25%/30%/35%); tích hợp giảm trừ bản thân 11tr/tháng; tích hợp với field NPT (sau khi custom G-12)
* Expected Result: Thuế TNCN tự động, đúng luật, có thể audit từng dòng
CFG-004 — Địa chỉ 3 cấp Tỉnh/Huyện/Phường
* Odoo Configuration Area: Cài module l10n_vn_viin_base_ward (Viindoo/VIIN)
* Configuration Detail: Cài module → dữ liệu 63 tỉnh/thành, quận/huyện, phường/xã được preload; gắn vào field địa chỉ trên Employee form và Contact form
* Expected Result: Địa chỉ chuẩn hành chính VN 3 cấp, chọn từ dropdown, không nhập tay
CFG-005 — Phân loại nhân sự Học Bá
* Odoo Configuration Area: Employee Form → employee_type + Tags + Contract Type
* Configuration Detail: Thêm giá trị "Giảng viên thỉnh giảng" vào employee_type; tạo tags "CTV", "Part-time"; tạo Contract Type riêng cho từng nhóm với cấu trúc lương và phép khác nhau
* Expected Result: Lọc, báo cáo và áp quy tắc lương/phép đúng theo từng nhóm nhân lực
CFG-006 — Kỹ năng chuyên môn giảng viên
* Odoo Configuration Area: Employees → Configuration → Skill Types
* Configuration Detail: Tạo Skill Type "Tiếng Trung" với Skills: HSK 3 / HSK 4 / HSK 5 / HSK 6 / HSKK / YCT; Skill Type "Chứng chỉ sư phạm" với: Sư phạm Trung văn / Phương pháp giảng dạy Hán ngữ quốc tế; cấp độ: Cơ bản / Trung cấp / Cao cấp
* Expected Result: Hồ sơ GV thể hiện rõ trình độ, hỗ trợ phân công lớp học phù hợp
CFG-007 — Luồng thanh toán CTV/GV thỉnh giảng qua Vendor Bill
* Odoo Configuration Area: Accounting → Vendors + HR → Contracts
* Configuration Detail: Đăng ký CTV là Vendor trong Accounting; cuối tháng tổng hợp số buổi từ Timesheet → tạo Vendor Bill → duyệt → thanh toán; tạo template bill chuẩn; tách riêng analytic account cho chi phí GV
* Expected Result: Kế toán phân biệt rõ chi phí nhân công cơ hữu (Payroll) vs chi phí dịch vụ CTV (Vendor Bill)
________________


Customization Gap (cập nhật)
CUS-001 — Bộ fields CCCD/BHXH/BHYT đặc thù Việt Nam
* Business Need: Lưu đầy đủ thông tin pháp lý: ngày cấp CCCD, nơi cấp, mã số BHXH, số thẻ BHYT, nơi KCB ban đầu, địa chỉ tạm trú
* Standard Limitation: Odoo core không có localization HR cho VN — thiếu ~7 fields bắt buộc theo pháp luật lao động VN
* Custom Solution: Tạo module l10n_vn_hr_employee kế thừa hr.employee; thêm các fields vào tab Private Information; thêm section "Thông tin bảo hiểm" và "Thông tin thuế"; validate CCCD 12 số và mã BHXH 10 số
* Business Benefit: Đáp ứng 100% yêu cầu pháp lý lao động VN; đủ dữ liệu để xuất báo cáo BHXH và quyết toán thuế TNCN
CUS-002 — Mã số thuế cá nhân + quản lý người phụ thuộc
* Business Need: Lưu MST cá nhân và danh sách NPT (tên, MST NPT, quan hệ) để tính giảm trừ thuế TNCN tự động
* Standard Limitation: Odoo không có model NPT; field ssnid không phù hợp ngữ cảnh VN
* Custom Solution: Thêm field personal_tax_code trên hr.employee; tạo model hr.dependent (one2many) với các trường: tên NPT, MST NPT, quan hệ, ngày bắt đầu/kết thúc; tích hợp vào Salary Rule tính giảm trừ gia cảnh
* Business Benefit: Tự động hóa tính thuế TNCN đúng luật; giảm sai sót kế toán; phục vụ quyết toán thuế cuối năm
CUS-003 — Mức lương đóng bảo hiểm riêng biệt
* Business Need: Tách insurance_salary (lương đóng BH) khỏi wage (tổng lương thực lĩnh) vì hai giá trị này khác nhau tại nhiều doanh nghiệp VN
* Standard Limitation: Odoo Payroll chỉ có một field wage trên Contract; không có logic tách lương đóng BH
* Custom Solution: Thêm field insurance_salary trên hr.contract; tạo computed field kiểm tra mức sàn (≥ lương tối thiểu vùng); các Salary Rules BHXH/BHYT/BHTN tính từ insurance_salary thay vì wage
* Business Benefit: Phản ánh đúng thực tế doanh nghiệp VN; tránh sai lệch khi kiểm tra BHXH
CUS-004 — Tính lương GV theo buổi dạy
* Business Need: Lương GV Học Bá = số buổi thực dạy trong tháng × đơn giá/buổi (khác nhau theo GV và môn học)
* Standard Limitation: Payroll tính theo wage tháng hoặc giờ — không có logic "per session" từ Timesheet
* Custom Solution: Thêm field session_rate (VNĐ/buổi) trên hr.contract; viết Salary Rule Python đọc số buổi từ hr.timesheet trong kỳ lương tương ứng; tạo Payroll Structure riêng "GV Học Bá" áp dụng rule này
* Business Benefit: Tự động hóa 100% tính lương GV — loại bỏ file Excel đếm buổi thủ công, minh bạch với GV






Phần 05
ConfigurationSpecification
Chi tiết cấu hình Odoo — không cần code
	________________


4. CONFIGURATION SPECIFICATION (Tóm tắt)
	

Phần này tóm tắt 9 nhóm cấu hình chính. Để xem chi tiết từng bước thực hiện, tham chiếu tài liệu Configuration Specification riêng (HocBa_Odoo_Configuration_Specification_v1.0.docx).


ID
	Tên cấu hình
	Odoo Config Area
	Kết quả kỳ vọng
	CFG-001
	Validate CCCD 12 số
	Employee Form → identification_id
	Ngăn nhập CCCD sai định dạng
	CFG-002
	Đổi nhãn field sang tiếng Việt
	Odoo Studio → form labels
	Giao diện thân thiện với HR VN
	CFG-003
	Cài module địa chỉ 3 cấp VN
	Apps → l10n_vn_viin_base_ward
	Dropdown Tỉnh/Huyện/Phường đầy đủ 63 tỉnh
	CFG-004
	Salary Rules BHXH/BHYT/BHTN
	Payroll → Salary Structures
	Tự động tính BH đúng tỷ lệ NLĐ+NSDLĐ
	CFG-005
	Biểu thuế TNCN 7 bậc lũy tiến
	Payroll → Salary Rules → Python
	Thuế TNCN tính tự động đúng luật VN
	CFG-006
	Phân loại 4 nhóm nhân sự
	employee_type + Contract Types
	Lọc/báo cáo theo từng nhóm nhân lực
	CFG-007
	Skill Types chứng chỉ GV tiếng Trung
	Configuration → Skill Types
	Hồ sơ GV thể hiện HSK, sư phạm Trung văn
	CFG-008
	Work Schedule linh hoạt GV online
	Work Schedules → Flexible
	GV không bị cảnh báo đi muộn/thiếu giờ
	CFG-009
	Vendor Bill flow CTV/GV thỉnh giảng
	Accounting → Vendors
	Tách bạch chi phí cơ hữu vs CTV
	________________


________________


Phần 04
FunctionalSpecification
Mô tả chức năng chi tiết — Actor · Steps · Rules
	________________


4. FUNCTIONAL SPECIFICATION (Tóm tắt)
	

Phần này tóm tắt 14 chức năng chính. Chi tiết đầy đủ (data dictionary, steps, business rules, error handling) trong tài liệu Functional Specification riêng (HocBa_Odoo_Functional_Specification_v1.0.docx).


FS
	Chức năng
	Actor chính
	Module
	Business Rule nổi bật
	FS-01
	Tạo & quản lý hồ sơ nhân viên
	HR Officer
	Employees
	CCCD unique, email unique, audit trail đầy đủ
	FS-02
	Thông tin định danh CCCD VN
	HR Officer
	Employees (CUS-001)
	12 số, ngày cấp ≤ hôm nay, mỗi CCCD duy nhất
	FS-03
	Quản lý BHXH/BHYT
	HR Officer
	Employees (CUS-001)
	Mã BHXH 10 số; cảnh báo BHYT hết hạn 30 ngày
	FS-04
	Người phụ thuộc & thuế TNCN
	HR Officer
	Employees (CUS-002)
	MST 10 số; giảm trừ 4.4tr/NPT/tháng tự động
	FS-05
	Cơ cấu tổ chức
	HR Admin
	Departments
	6 phòng ban; org chart tự cập nhật khi chuyển ban
	FS-06
	Hợp đồng lao động & ký số
	HR Officer
	Contracts + Sign
	Thử việc ≤60 ngày; versioning khi đổi lương
	FS-07
	Bảng lương nhân viên cơ hữu
	Finance
	Payroll
	Bắt buộc có mã BHXH trước khi confirm payslip
	FS-08
	Lương GV theo buổi dạy
	Finance + Academic
	Payroll (CUS-004)
	Chỉ tính timesheet đã approved; áp guarantee nếu ít buổi
	FS-09
	Thanh toán CTV Vendor Bill
	Finance
	Accounting
	Khấu trừ TNCN 10% nếu thù lao >2tr/lần
	FS-10
	Quản lý nghỉ phép
	NV + HR
	Time Off
	Phép năm ≥12 ngày/năm (Luật LĐ Điều 113)
	FS-11
	Đánh giá thử việc 2 tháng
	HR + Academic
	Appraisal
	Tự trigger 60 ngày sau contract_start_date
	FS-12
	Tuyển dụng → tạo nhân viên
	HR Officer
	Recruitment
	1-click Create Employee từ ứng viên pass
	FS-13
	Employee self-service portal
	Nhân viên
	Portal
	Xem payslip, đăng ký phép, cập nhật thông tin cơ bản
	FS-14
	Ma trận phân quyền
	HR Admin
	Settings
	3 cấp: Employee / Officer / Administrator
	________________


________________


Phần 05
TechnicalCustomization Spec
Module structure · Python · XML · Test cases
	________________


5. TECHNICAL CUSTOMIZATION SPECIFICATION (Tóm tắt)
	

Phần này tóm tắt 4 custom modules cần phát triển. Code đầy đủ, field specs và test cases trong tài liệu Technical Specification riêng (HocBa_Odoo_Technical_Spec_v1.0.docx).


5.1 Tổng quan 4 custom modules
Module
	Mục đích
	Model chính
	Sprint / Effort
	Fields mới
	l10n_vn_hr_employee
	Fields pháp lý VN: CCCD, BHXH, BHYT, địa chỉ tạm trú
	hr.employee (extend)
	Sprint 1 · ~3 ngày
	9 fields vn_*
	l10n_vn_hr_dependent
	Người phụ thuộc & MST cá nhân cho thuế TNCN
	hr.dependent (new model)
	Sprint 2 · ~4 ngày
	Model mới + 5 fields trên hr.employee
	l10n_vn_hr_insurance
	Mức lương đóng BH độc lập với tổng lương
	hr.contract (extend)
	Sprint 2 · ~2 ngày
	3 fields vn_insurance_*
	hocba_hr_payroll_session
	Tính lương GV theo buổi dạy từ Timesheet
	hr.contract + hr.payslip (extend)
	Sprint 3 · ~5 ngày
	5 fields hocba_* + SQL view report
	

5.2 Salary Rules quan trọng nhất
Rule Code
	Tên
	Category
	Logic (Python tóm tắt)
	BHXH_NLD
	BHXH người lao động
	Deduction
	−insurance_salary × 8%
	BHYT_NLD
	BHYT người lao động
	Deduction
	−insurance_salary × 1.5%
	BHTN_NLD
	BHTN người lao động
	Deduction
	−insurance_salary × 1%
	BHXH_CTY
	BHXH công ty
	Employer
	insurance_salary × 17.5%
	BHYT_CTY
	BHYT công ty
	Employer
	insurance_salary × 3%
	BHTN_CTY
	BHTN công ty
	Employer
	insurance_salary × 1%
	TNCN
	Thuế TNCN
	Deduction
	Lũy tiến 7 bậc từ 5%→35%; trừ 11tr bản thân + 4.4tr × n NPT
	SESSION_BASE
	Lương GV theo buổi
	Basic
	max(session_count, guarantee) × session_rate
	

6. KẾ HOẠCH TRIỂN KHAI TỔNG HỢP
	

Sprint
	Item
	Nội dung
	Effort
	Priority
	Sprint 1
	CUS-001
	Module l10n_vn_hr_employee: CCCD, BHXH, BHYT fields
	~3 ngày
	Critical
	Sprint 1
	CFG-003
	Cài l10n_vn_viin_base_ward: địa chỉ 3 cấp
	~0.5 ngày
	High
	Sprint 1
	CFG-004
	Salary Rules BHXH/BHYT/BHTN (10.5% + 21.5%)
	~1 ngày
	Critical
	Sprint 1
	CFG-005
	Biểu thuế TNCN 7 bậc Python
	~1 ngày
	Critical
	Sprint 2
	CUS-002
	Module l10n_vn_hr_dependent: NPT + MST
	~4 ngày
	High
	Sprint 2
	CUS-003
	Module l10n_vn_hr_insurance: insurance_salary
	~2 ngày
	High
	Sprint 2
	CFG-006
	Phân loại nhân sự 4 nhóm Học Bá
	~0.5 ngày
	Medium
	Sprint 2
	CFG-007
	Skill Types HSK + sư phạm Trung văn
	~0.5 ngày
	Medium
	Sprint 2
	CFG-008
	Work Schedule linh hoạt GV online
	~0.5 ngày
	Medium
	Sprint 3
	CUS-004
	Module hocba_hr_payroll_session: lương theo buổi
	~5 ngày
	High
	Sprint 3
	CFG-009
	Vendor Bill flow CTV/GV thỉnh giảng
	~1 ngày
	Medium
	Sprint 3
	UAT
	User Acceptance Testing — 17 test cases
	~2 ngày
	Critical
	Sprint 3
	Go-live
	Deploy production, import data master, training HR
	~1 ngày
	Critical
	

7. PHÊ DUYỆT TỔNG THỂ
	

Vai trò
	Họ và tên
	Ngày
	Chữ ký
	Business Owner — Học Bá
	

	

	

	Project Manager
	

	

	

	Business Analyst
	

	

	

	Tech Lead / Developer
	

	

	

	

Bộ tài liệu này được lập bởi đội BA và Technical dựa trên phân tích thực tế Học Bá Education, chuẩn pháp lý lao động Việt Nam và khả năng của Odoo 19. Bộ tài liệu gồm 5 file: tài liệu tổng hợp này + 4 file chi tiết riêng cho Configuration Spec, Functional Spec, Technical Spec. Mọi thay đổi yêu cầu phê duyệt bằng văn bản từ Project Manager.




Attendance1
TÀI LIỆU TẢ CẤU HÌNH HỆ THỐNG (CONFIGURATION SPECIFICATION)
PHÂN HỆ: QUẢN LÝ CHẤM CÔNG (ODOO 19 ATTENDANCES)
Khách hàng: Học Bá Education
Mã cấu hình tổng thể: CFG-ATT-PRO-01
1. CẤU HÌNH THAM SỐ HỆ THỐNG CHUNG (GENERAL SETTINGS)
Cấu hình các thuộc tính cốt lõi của phân hệ Chấm công để kích hoạt các tính năng nền tảng.
* Đường dẫn truy cập: Attendances ➔ Configuration ➔ Settings
* Các tham số cần thiết lập:
Tên Tham số (Odoo Field/Setting)
	Trạng thái
	Giá trị cấu hình
	Giải thích nghiệp vụ
	Kiosk Mode
	Kích hoạt
	Barcode / PIN
	Áp dụng cho khối nhân sự làm việc trực tiếp tại trung tâm nhằm tối ưu hóa tốc độ ghi nhận đầu ca bằng máy tính bảng dùng chung.
	Kiosk Mode Document
	Kích hoạt
	Choose Employee
	Cho phép nhân viên chọn nhanh tên mình trên màn hình và nhập mã PIN để xác thực.
	Extra Hours (Overtime)
	Kích hoạt
	Checked (True)
	Bật tính năng chạy ngầm tự động tính toán số giờ làm việc vượt định mức so với lịch làm việc chuẩn làm cơ sở tính lương tăng ca.
	Count Extra Hours From
	Thiết lập
	Theo từng Lịch làm việc
	Cho phép cấu hình linh hoạt mốc thời gian bắt đầu tính tăng ca riêng biệt cho từng khối nhân sự đặc thù.
	2. CHI TIẾT CẤU HÌNH LỊCH LÀM VIỆC (WORKING SCHEDULES - resource.calendar)
Thiết lập khung thời gian tiêu chuẩn và các quy tắc kiểm soát đi muộn/về sớm áp dụng riêng cho 3 khối nhân sự đặc thù.
* Đường dẫn truy cập: Employees ➔ Configuration ➔ Working Schedules
2.1. Lịch Khối Văn phòng & Vận hành (Mã cấu hình: CFG-ATT-003-OFF)
* Tên lịch hiển thị: Lịch Hành chính Cố định - Khối Văn phòng Học Bá
* Số giờ định mức tiêu chuẩn: 8.0 giờ/ngày
* Chi tiết khung giờ làm việc theo ngày (Từ Thứ 2 đến Thứ 6):
   * Ca Sáng: Từ 08:30 đến 12:00
   * Giờ Nghỉ Trưa (Hệ thống tự động loại trừ): Từ 12:00 đến 13:00
   * Ca Chiều: Từ 13:00 đến 17:30
* Cấu hình nâng nâng cao thuộc tính kiểm soát (Advanced Tab):
   * Dung sai đi muộn (Late In Tolerance): Điền 15 phút. Hệ thống cho phép nhân viên Check-in trước mốc 08:45 sáng mà không bị gán nhãn cảnh báo vi phạm đi muộn hành chính.
   * Mốc bắt đầu tính tăng ca (Count Extra Hours After): Điền 18:00. Mọi log làm việc phát sinh sau 18:00 hàng ngày mới được Odoo ghi nhận vào quỹ thời gian tăng ca (Overtime).
2.2. Lịch Khối Giảng viên & Trợ giảng (Mã cấu hình: CFG-ATT-003-TCH)
* Tên lịch hiển thị: Lịch Linh hoạt Khối Giảng viên & Trợ giảng
* Loại lịch làm việc (Working Schedule Type): Chọn Flexible Hours (Giờ linh hoạt)
* Định mức bắt buộc theo tuần (Target Weekly Hours): Cấu hình cố định bằng 0.0 giờ.
* Giải thích nghiệp vụ: Việc đưa định mức về 0.0 giờ nhằm loại bỏ hoàn toàn cơ chế quét lỗi đi muộn, về sớm hành chính tự động của Odoo đối với các hoạt động thỉnh giảng trực tuyến. Đây là cấu hình nền tảng giúp nạp dữ liệu công ròng theo đúng độ dài lớp học thực tế (1.5h - 2h/ca) từ phân hệ quản lý lớp học đẩy về thông qua API.
2.3. Lịch Khối Cộng tác viên - CTV (Mã cấu hình: CFG-ATT-003-CTV)
* Tên lịch hiển thị: Lịch Phân Ca Tuần - Khối Cộng tác viên (CTV)
* Loại lịch làm việc (Working Schedule Type): Chọn Shift-Based / Scheduled Shifts
* Giải thích nghiệp vụ: Thiết lập này cho phép hệ thống làm căn cứ đối chiếu động với cấu trúc bảng đăng ký ca tuần tự do phát sinh tại module tùy biến mở rộng.
3. CẤU HÌNH LIÊN KẾT TRÊN HỒ SƠ NHÂN VIÊN (EMPLOYEE MASTER DATA)
Để kích hoạt đúng logic chấm công, mỗi nhân sự khi tạo mới trên hệ thống bắt buộc phải được thiết lập các trường thông tin đồng bộ.
* Đường dẫn truy cập: Employees ➔ Employees ➔ [Chọn Nhân viên] ➔ Tab: Work Information
* Các trường thông tin bắt buộc điền:
1. Working Hours (resource_calendar_id): Gán chính xác 1 trong 3 loại lịch làm việc được mô tả ở Mục 2 tương ứng với khối nhân sự của nhân viên đó.
2. PIN Code (pin): Cấu hình chuỗi 4 số bảo mật riêng biệt (Ví dụ: 1982, 2026). Chỉ áp dụng bắt buộc đối với nhân sự cần tương tác qua máy tính bảng tại trung tâm để Check-in/Out.
3. Badge ID (barcode): Nhập chuỗi mã vạch định danh cá nhân in trên thẻ nhân viên (phục vụ quét nhanh bằng máy đọc mã vạch nếu có).
4. CẤU HÌNH GIAO DIỆN CHẾ ĐỘ KI-ỐT ĐẶT TẠI TRUNG TÂM (KIOSK MODE)
Thiết lập môi trường phần cứng dùng chung cho nhân sự tương tác trực tiếp tại cơ sở vật chất của Học Bá.
* Yêu cầu thiết bị: Máy tính bảng (Tablet) hoặc màn hình máy tính chuyên dụng đặt tại cửa ra vào, có kết nối camera hoặc máy quét ngoại vi.
* Quy trình cấu hình kích hoạt giao diện:
   1. Người vận hành truy cập menu Attendances ➔ Kiosk Mode.
   2. Hệ thống sẽ chuyển sang giao diện toàn màn hình, khóa các thanh điều hướng chuẩn của Odoo.
   3. Cơ chế hoạt động: Nhân viên sử dụng thao tác quét thẻ vật lý qua camera (Badge ID) hoặc click vào nút “Identify Manually” ➔ Tìm kiếm tên mình trong danh sách ➔ Nhập mã PIN 4 số đã cấu hình bảo mật để hoàn tất chu kỳ công đầu ca hoặc cuối ca.
5. MA TRẬN PHÂN QUYỀN VÀ BẢO MẬT (ACCESS RIGHTS SECURITY MATRIX)
Cấu hình nhóm quyền để đảm bảo tính minh bạch, hạn chế tối đa rủi ro can thiệp chỉnh sửa sai lệch nhật ký thời gian thực.
* Đường dẫn truy cập: Settings ➔ Users & Companies ➔ Users
Nhóm quyền (Odoo Roles)
	Phạm vi hiển thị dữ liệu (Data Visibility)
	Quyền hạn Thao tác (Action Permissions)
	Nhân viên thông thường (Employee)
	Chỉ thấy duy nhất dữ liệu log chấm công của bản thân.
	* Thực hiện bấm nút Check-In/Check-Out cá nhân trên Webapp/Mobile .
* Không có quyền sửa đổi mốc thời gian thực tế đã lưu.
	Quản lý Trực tiếp (Line Manager / Officer)
	Thấy toàn bộ bảng công của các nhân viên thuộc Phòng ban/Bộ phận mình phụ trách theo sơ đồ tổ chức.
	* Kiểm duyệt, xem chi tiết các cờ cảnh báo lỗi vi phạm đi muộn, về sớm hoặc cờ ngoài vị trí.
* Không được quyền tự ý xóa bỏ nhật ký thô của nhân viên.
	Quản trị viên Nhân sự (HR Administrator / C&B)
	Toàn quyền trên toàn hệ thống (All Records).
	* Chỉnh sửa bản ghi chấm công lỗi trong trường hợp nhân viên có giải trình hợp lệ.
* Phê duyệt chốt dữ liệu để hệ thống tự động tổng hợp sang bản ghi Ngày công làm việc (Work Entries), chuyển tiếp dữ liệu sạch sang cấu trúc phân hệ tính Lương (Payroll).
	







SYSTEM CONFIGURATION SPECIFICATION
MODULE: ATTENDANCE MANAGEMENT (ODOO 19 ATTENDANCES)
Client: Học Bá Education
Global Configuration Code: CFG-ATT-PRO-01
1. GENERAL SYSTEM PARAMETERS SETTINGS
Configure the core properties of the Attendance module to activate the foundational features.
* Access Path: Attendances ➔ Configuration ➔ Settings
* Required Parameter Settings:
Parameter Name (Odoo Field/Setting)
	Status
	Configuration Value
	Business Rationale
	Kiosk Mode
	Activated
	Barcode / PIN
	Applied to the on-site staff block at centers to optimize clock-in speed at the beginning of shifts using a shared tablet.
	Kiosk Mode Document
	Activated
	Choose Employee
	Allows employees to quickly select their names on the screen and enter their PIN for verification.
	Extra Hours (Overtime)
	Activated
	Checked (True)
	Enables background automatic calculation of working hours exceeding the standard quota to serve as the basis for overtime payroll.
	Count Extra Hours From
	Configured
	Per Working Schedule
	Allows flexible configuration of the starting time for overtime calculations for each specific workforce block.
	2. DETAILED WORKING SCHEDULES CONFIGURATION (resource.calendar)
Establish the standard timeframe and lateness/early departure control rules applied specifically to the 3 distinct workforce blocks.
* Access Path: Employees ➔ Configuration ➔ Working Schedules
2.1. Office & Operations Block Schedule (Configuration Code: CFG-ATT-003-OFF)
* Display Name: Fixed Administrative Schedule - Học Bá Office Bloc
* Standard Daily Quota: 8.0 hours/day
* Detailed Daily Working Hours (Monday to Friday):
   * Morning Shift: From 08:30 to 12:00
   * Lunch Break (Automatically excluded by the system): From 12:00 to 13:00
   * Afternoon Shift: From 13:00 to 17:30
* Advanced Configuration Properties (Advanced Tab):
   * Late In Tolerance: Enter 15 minutes. The system allows employees to Check-in before 08:45 AM without being flagged with an administrative late-in violation warning.
   * Count Extra Hours After: Enter 18:00. Only working logs arising after 18:00 daily will be recorded by Odoo into the Overtime hours pool.
2.2. Teachers & Tutors Block Schedule (Configuration Code: CFG-ATT-003-TCH)
* Display Name: Flexible Schedule - Teachers & Tutors Block
* Working Schedule Type: Select Flexible Hours
* Target Weekly Hours: Fixed at 0.0 hours.
* Business Rationale: Setting the mandatory weekly quota to 0.0 hours completely eliminates Odoo's automatic administrative late-in and early-out scanning mechanisms for online visiting teachers. This is a foundational configuration to ingest net work hours matching the exact actual class durations (1.5h - 2h/session) pushed from the academic management module via API.
2.3. Collaborator Bloc Schedule - CTV (Configuration Code: CFG-ATT-003-CTV)
* Display Name: Weekly Shift Schedule - Collaborator Bloc (CTV)
* Working Schedule Type: Select Shift-Based / Scheduled Shifts
* Business Rationale: This setting serves as the basis for dynamic cross-matching against the flexible weekly shift registration matrix generated in the custom extended module.
3. EMPLOYEE MASTER DATA LINKAGE CONFIGURATION
To trigger the correct attendance logic, each employee record created in the system must be configured with synchronized fields.
* Access Path: Employees ➔ Employees ➔ [Select Employee] ➔ Tab: Work Information
* Mandatory Fields:
1. Working Hours (resource_calendar_id): Accurately assign 1 of the 3 working schedules described in Section 2 corresponding to the employee's block.
2. PIN Code (pin): Configure a unique secure 4-digit sequence (e.g., 1982, 2026). Mandatory only for personnel who need to interact via the shared tablet at centers for Check-in/Out.
3. Badge ID (barcode): Enter the unique personal barcode printed on the employee badge (for quick scanning using a barcode reader, if applicable).
4. ON-SITE KIOSK MODE INTERFACE CONFIGURATION
Set up the shared hardware environment for personnel interacting directly at Học Bá's facilities.
* Hardware Requirements: A dedicated tablet or computer monitor placed at the entrance, equipped with a camera or external barcode scanner.
* Activation Process:
   1. The operator navigates to the menu: Attendances ➔ Kiosk Mode.
   2. The system switches to full-screen mode, locking Odoo's standard navigation bars.
   3. Operational Mechanism: Employees scan their physical badges via the camera (Badge ID) or click the “Identify Manually” button ➔ Search for their name in the list ➔ Enter their secure 4-digit PIN to complete the clock-in or clock-out cycle.
5. ACCESS RIGHTS SECURITY MATRIX CONFIGURATION
Configure user roles to ensure transparency and minimize the risk of unauthorized modification to real-time logs.
* Access Path: Settings ➔ Users & Companies ➔ Users
Odoo Roles
	Data Visibility
	Action Permissions
	Employee
	Can only view their own attendance log data.
	* Perform personal Check-In/Check-Out via Webapp/Mobile.


* No permission to modify saved actual timestamps.
	Line Manager / Officer
	Can view the full attendance table of employees within their assigned Departments/Units based on the organizational chart.
	* Review and audit details of late-in, early-out, or outside-location warning flags.


* No permission to delete raw employee logs.
	HR Administrator / C&B
	Full access across the entire system (All Records).
	* Edit erroneous attendance records if the employee provides an approved explanation.


* Validate and close data to allow the system to automatically aggregate it into Work Entries, forwarding clean data to the Payroll module structure.
	



BEta
TÀI LIỆU KHẢO SÁT NGHIỆP VỤ & THIẾT KẾ KIẾN TRÚC ĐÍCH TRIỂN KHAI ODOO 19 ERP
Dự án: Số hóa và Chuyển đổi Hệ thống Quản trị Nhân sự (HRM) - Học Bá Education
Tác giả: Senior ERP Solution Architect + Senior Data Analyst + Odoo Technical Consultant




PHẦN 1: BẢN PHÂN TÍCH CHI TIẾT THEO TỪNG PHÂN HỆ VÀ THỰC THỂ DỮ LIỆU


MODULE 1 — EMPLOYEES & ORGANIZATIONAL MANAGEMENT (HỒ SƠ NHÂN SỰ & CƠ CẤU TỔ CHỨC)
1. Business Analysis (Phân tích Nghiệp vụ)
Học Bá Education vận hành một mạng lưới nhân sự phức tạp, phân tầng sâu sắc giữa các khối chức năng. Vòng đời của một nhân sự tuân thủ nghiêm ngặt theo chuỗi trạng thái: Ứng viên (Applicant) $\rightarrow$ Thử việc (Probation) $\rightarrow$ Chính thức (Regular) $\rightarrow$ Nghỉ việc (Terminated).
Hệ thống quản lý 4 nhóm nhân sự cốt lõi:
* Khối Văn phòng & Vận hành (Backoffice): Làm việc cố định, thụ hưởng phụ cấp hành chính, đóng BHXH đầy đủ.
* Khối Giảng viên (Teachers): Tính thù lao theo số buổi dạy (Session-based rate) và cấp độ chuyên môn (Level HSK/TOCFL).
* Khối Trợ giảng (Tutors/Mentors): Chấm bài, hỗ trợ học viên, nhận thù lao khoán.
* Khối Cộng tác viên (CTV Part-time): Đăng ký ca làm việc linh hoạt, hưởng lương cứng theo giờ và hoa hồng bậc thang (Commission bậc thang).
Sơ đồ tổ chức phân chia theo cấu trúc: Tổng công ty (BOD) $\rightarrow$ Các Chi nhánh (Hà Nội, Trực tuyến) $\rightarrow$ Các Phòng ban chuyên biệt (Kinh doanh, Marketing, Sản phẩm, Vận hành, Kế toán).
Thách thức kiến trúc lớn nhất là xử lý kịch bản nhân sự đa vai trò (Multi-role): Một nhân sự thuộc phòng Sản phẩm vừa có thể đảm nhiệm vị trí Chuyên viên Giáo vụ (hưởng lương thời gian) vừa tham gia dạy các lớp VIP (hưởng lương theo buổi). Hệ thống đích bắt buộc phải quản lý tập trung mã định danh cá nhân nhưng phân tách minh bạch các vai trò trên sơ đồ chức danh.
2. Source Excel Analysis (Phân tích Bảng tính Nguồn)
* Tệp tin nguồn: Học bá education - 2.1. Quản lý nhân sự.csv, Học bá education - 3.1 Employee_Info.csv, Học bá education - 3.2 Department_Info.csv, Học bá education - 2.5. Theo dõi ký hợp đồng.csv.
* Cấu trúc dữ liệu và Mẫu dữ liệu (Data Sample): Cột mã nhân sự định dạng HB.xxx (Ví dụ: HB.01, HB.02). Chứa đầy đủ thông tin định danh cá nhân (CCCD, SĐT, Email cá nhân/công ty), thông tin công tác (Phòng ban, Chức danh, Ngày thử việc, Ngày chính thức) và danh mục tài sản phần cứng phân phối (Màn hình, Cây máy tính, Tai nghe sale).
* Đánh giá chất lượng dữ liệu (Data Quality Assessment):
   * Rủi ro trùng lặp (Duplicate Risk): Cao. Xuất hiện tình trạng trùng tên hiển thị do nhân viên tự nhập liệu trên hệ thống cũ. Bản ghi 3.1 Employee_Info lưu tên không dấu, lệch chuẩn với bảng nhân sự chính thức 2.1. Quản lý nhân sự.
   * Dữ liệu trống (Missing Values): Các trường ngày chính thức (Ngày chính thức) và ngày nghỉ việc (Ngày nghỉ việc) bị bỏ trống diện rộng ở khối nhân sự thử việc và CTV. Các trường mã số thuế TNCN và số sổ BHXH trống 90% ở khối Online và CTV.
   * Tính không nhất quán (Data Inconsistency): Cột Hình thức sử dụng chuỗi không đồng bộ lúc là "Văn phòng", lúc là "Offline", "Online". Tên phòng ban chứa các ký tự lạ hoặc định dạng Emoji (Châu Anh 💰, Lead MKT - Đặng Thuỳ Trang).
3. Data Model Design (Thiết kế Mô hình Dữ liệu Đích)
* Thực thể chính (Main Entities): hr.employee (Hồ sơ nhân viên), hr.department (Phòng ban), hr.job (Vị trí chức danh), hr.contract (Hợp đồng lao động).
* Mối quan hệ dữ liệu (Relationships):
   * hr.employee $\rightarrow$ hr.department: Quan hệ Many2one thông qua trường department_id.
   * hr.department $\rightarrow$ hr.department: Quan hệ tự tham chiếu Many2one (parent_id) để dựng cây phân cấp phòng ban mẹ-con.
   * hr.employee $\rightarrow$ hr.contract: Quan hệ One2many (contract_ids). Tại một thời điểm, chỉ một hợp đồng ở trạng thái 'open' (Đang hiệu lực).
* Trường tính toán (Computed Fields): x_tenure_months (Số tháng làm việc thực tế, tính từ first_contract_date đến ngày hiện tại hoặc departure_date). x_hardware_count (Tổng số lượng thiết bị phần cứng đang bàn giao cho nhân sự, đếm từ quan hệ với module Tài sản).
* Ràng buộc (Constraints): Ràng buộc SQL Unique cứng đối với barcode (Mã định danh nội bộ HB.xxx), identification_id (Số CCCD), và work_email (Email công ty). Chặn lưu nếu trùng lặp.
4. Odoo Model Mapping (Bảng Ánh xạ Dữ liệu Cấp Trường)
Trường dữ liệu Excel
	Ý nghĩa nghiệp vụ
	Mô hình Odoo Đích
	Trường Odoo Đích
	Kiểu dữ liệu
	Bắt buộc
	Quy tắc chuyển đổi (Transformation Rule)
	Mã nhân sự
	Mã định danh duy nhất
	hr.employee
	barcode
	Char
	YES
	Giữ nguyên định dạng HB.xxx, cắt bỏ khoảng trắng đầu cuối.
	Họ và tên
	Tên đầy đủ nhân viên
	hr.employee
	name
	Char
	YES
	Chuẩn hóa viết hoa chữ cái đầu (Ví dụ: Nguyễn Trung Kiên).
	Tài khoản Lark
	Định danh người dùng Lark
	hr.employee
	x_lark_user_id
	Char
	NO
	Dùng làm khóa liên kết đồng bộ Webhook.
	Hình thức
	Phân loại địa điểm
	hr.employee
	x_work_mode
	Selection
	YES
	"Offline" / "Văn phòng" $\rightarrow$ 'offline'; "Online" $\rightarrow$ 'online'.
	Tình trạng
	Trạng thái lao động
	hr.employee
	x_hr_status
	Selection
	YES
	"Chính thức" $\rightarrow$ 'regular'; "Thử việc" $\rightarrow$ 'probation'.
	Phòng Ban
	Phòng ban công tác
	hr.employee
	department_id
	Many2one
	YES
	Tìm kiếm ID tương ứng trong bảng hr.department bằng tên.
	Chức danh
	Vị trí công việc
	hr.employee
	job_id
	Many2one
	YES
	Tìm kiếm ID tương ứng trong bảng hr.job.
	Số căn cước công dân
	Mã định danh cá nhân
	hr.employee
	identification_id
	Char
	NO
	Loại bỏ toàn bộ khoảng trắng và dấu chấm văn bản.
	Số điện thoại
	Điện thoại di động
	hr.employee
	mobile_phone
	Char
	YES
	Chuẩn hóa về định dạng quốc tế (Thêm +84 nếu cần).
	Email công ty
	Hòm thư công vụ
	hr.employee
	work_email
	Char
	NO
	Chuyển toàn bộ về chữ thường, kiểm tra Regex Email.
	Trình độ tiếng Trung
	Năng lực ngoại ngữ
	hr.employee
	x_chinese_level
	Char
	NO
	Lưu chuỗi văn bản phục vụ phân phối giảng dạy.
	5. Customization Requirements (Yêu cầu Tùy biến Phát triển)
* Custom Fields: Thêm nhóm trường quản lý thiết bị phần cứng cấp phát trực tiếp trên Form hồ sơ nhân sự (Liên kết sang mô hình hr.equipment). Thêm trường x_teaching_level phục vụ riêng cho Khối Giảng viên.
* Custom Workflows: Thiết lập luồng tự động thay đổi trạng thái hồ sơ: Khi một hợp đồng thử việc (hr.contract) chuyển sang trạng thái 'expired', hệ thống tự động bắn cảnh báo đến nhân sự yêu cầu kích hoạt quy trình đánh giá thử việc trước 5 ngày (Bám sát quy trình Học bá education - Quy trình nghỉ thử việc.csv).
* Security Groups: Phân tách 3 phân quyền hệ thống:
   * Group Employee: Chỉ được xem hồ sơ cá nhân.
   * Group Department Manager (TBP): Xem toàn bộ nhân sự thuộc phòng ban quản lý theo cấu trúc phân cấp.
   * Group HR Officer / C&B: Toàn quyền tạo sửa, lưu trữ dữ liệu nhân sự trên toàn hệ thống.
6. Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Quy tắc xử lý trùng lặp (Duplicate Logic): Quét toàn bộ cơ sở dữ liệu Excel nguồn, nếu phát hiện 2 bản ghi trùng nhau về Số căn cước công dân hoặc Số điện thoại, giữ lại bản ghi có tiến trình cập nhật gần nhất tại tệp 2.4 Lộ trình thăng tiến, bản ghi còn lại chuyển vào danh sách log cảnh báo lỗi để HR xử lý thủ công.
* Chuẩn hóa giá trị (Normalize Values): Loại bỏ hoàn toàn Emoji và các chuỗi tiền tố chức vụ thừa trong cột họ tên (Lead MKT - , Châu Anh 💰 $\rightarrow$ Phan Hoàng Châu Anh). Ép toán bộ định dạng ngày tháng về chuẩn ISO YYYY-MM-DD.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu (Import Sequence):
   1. res.company (Cấu hình Chi nhánh hệ thống)
   2. hr.department (Khởi tạo các phòng ban gốc, sau đó import quan hệ mẹ-con)
   3. hr.job (Danh mục vị trí công việc từ tệp 8.4 Lookup chức danh)
   4. hr.employee (Hồ sơ nhân sự cốt lõi)
   5. hr.contract (Hợp đồng lao động phụ thuộc vào nhân sự)
* Cơ chế External IDs: Đặt mã External ID theo cú pháp chuẩn hóa: __export__.hr_department_ + department_id của Lark (Ví dụ: __export__.hr_department_marketing_hocba). Đối với nhân sự, sử dụng mã nhân sự làm ID duy nhất: __export__.hr_employee_HB_01.
8. Risks & Edge Cases (Rủi ro & Kịch bản Đặc biệt)
* Nhân sự nghỉ việc quay lại làm việc: Kịch bản nhân sự HB.50 nghỉ việc sau đó quay lại làm CTV. Odoo không được phép tạo bản ghi hr.employee mới để tránh gãy chuỗi báo cáo tài chính. Phương án xử lý: Kích hoạt lại (Unarchive) hồ sơ cũ, tạo một dòng hợp đồng hr.contract mới với loại hình công tác cập nhật.
________________
MODULE 2 — ATTENDANCE & TIME TRACKING (QUẢN LÝ CHẤM CÔNG & CA LÀM VIỆC)
1. Business Analysis (Phân tích Nghiệp vụ)
Học Bá áp dụng cơ chế chấm công đa phương thức bám sát cấu trúc của 3 khối nhân sự vận hành:
* Khối Văn phòng: Chấm công 2 chiều (Check-in/Check-out) bắt buộc tại tọa độ GPS văn phòng. Định mức ca chuẩn là 8 giờ làm việc/ngày. Cho phép đi muộn tối đa 15 phút đầu ca theo chính sách phúc lợi.
* Khối CTV: Phải đăng ký ca làm việc tuần trên hệ thống. Dữ liệu chấm công thực tế sẽ được đối soát tự động với ca đăng ký.
* Khối Giảng viên/Trợ giảng: Chấm công dựa trên tiến độ hoàn thành lớp học (Session-based). Khung giờ dạy được quản lý trực tiếp từ phân hệ Đào tạo.
Quy trình dữ liệu yêu cầu xử lý tích hợp 3 loại đơn từ phê duyệt (Dựa trên các tệp 4.1, 4.2, 4.3): Đơn xin nghỉ phép/đi muộn, Đơn đề xuất làm việc Online, và Đơn giải trình quên chấm công. Khi đơn giải trình quên chấm công được phê duyệt, hệ thống phải tự động bổ sung dữ liệu chấm công thô bị thiếu để bảo toàn quỹ công cuối tháng.
2. Source Excel Analysis (Phân tích Bảng tính Nguồn)
* Tệp tin nguồn: Học bá education - 3.3 Attendance_Results.csv, Học bá education - 3.4. Bảng công tháng.csv, Học bá education - 4.2. Đề xuất làm online.csv, Học bá education - 4.3. Phiếu đề xuất quên chấm công.csv.
* Cấu trúc dữ liệu: Tệp dữ liệu chấm công thô lưu trữ mốc thời gian chi tiết (Check in time, Check out time), trạng thái điểm quét (Check in - Is offsite), số phút đi trễ toán học (Số phút đi trễ), và mã định danh dòng Result id.
* Đánh giá chất lượng dữ liệu:
   * Lỗi múi giờ (Timezone Mismatch): Nghiêm trọng. Dữ liệu Lark đẩy về qua Anycross hiển thị chuỗi thời gian cục bộ (Múi giờ Việt Nam UTC+7), trong khi cơ sở dữ liệu Odoo yêu cầu lưu trữ múi giờ UTC chuẩn hóa quốc tế.
   * Bản ghi mồ côi (Orphan Records): Rất nhiều dòng chấm công có mốc Check out time trống do nhân viên quên quét thẻ khi về, dẫn đến việc công cụ Excel cũ tính toán số giờ làm việc ra giá trị âm hoặc lỗi công thức hệ thống.
3. Data Model Design (Thiết kế Mô hình Dữ liệu Đích)
* Thực thể chính: hr.attendance (Bản ghi chấm công chi tiết), resource.calendar (Khung lịch làm việc tổng thể), resource.calendar.attendance (Chi tiết ca làm việc trong tuần).
* Mối quan hệ dữ liệu: hr.attendance $\rightarrow$ hr.employee (Quan hệ Many2one qua trường employee_id). Mỗi bản ghi chấm công bắt buộc phải định danh chính xác chủ thể nhân sự.
* Trường tính toán (Computed Fields): x_late_minutes (Tính bằng công thức: Thời gian Check-in thực tế trừ đi thời gian mở ca tiêu chuẩn của Lịch làm việc. Nếu giá trị nhỏ hơn hoặc bằng 0, ghi nhận bằng 0).
* Ràng buộc: Ràng buộc hỗn hợp kiểm soát logic Database: Thời gian Check-out bắt buộc phải lớn hơn thời gian Check-in trên cùng một dòng bản ghi (check_out > check_in).
4. Odoo Model Mapping (Bảng Ánh xạ Dữ liệu Cấp Trường)
Trường dữ liệu Excel
	Ý nghĩa nghiệp vụ
	Mô hình Odoo Đích
	Trường Odoo Đích
	Kiểu dữ liệu
	Bắt buộc
	Quy tắc chuyển đổi (Transformation Rule)
	Result id
	Mã bản ghi chấm công gốc
	hr.attendance
	x_lark_result_id
	Char
	YES
	Đặt làm Unique Constraint để chặn trùng dữ liệu khi chạy ETL.
	Mã nhân viên
	Nhân sự thực hiện quét công
	hr.attendance
	employee_id
	Many2one
	YES
	Đối soát từ mã HB.xxx sang ID nội bộ của hr.employee.
	Check in time
	Thời gian vào ca thực tế
	hr.attendance
	check_in
	Datetime
	YES
	Chuyển đổi định dạng chuỗi từ UTC+7 sang giờ UTC quốc tế.
	Check out time
	Thời gian ra ca thực tế
	hr.attendance
	check_out
	Datetime
	NO
	Cho phép Null trong ngày, ép giờ kết thúc ca nếu quên checkout.
	Check in - Is offsite
	Cờ báo điểm chấm công sai vị trí
	hr.attendance
	x_is_offsite
	Boolean
	YES
	Chuỗi "true" / "false" chuyển đổi sang kiểu logic True/False.
	Số phút đi trễ
	Thời gian đi muộn tính bằng phút
	hr.attendance
	x_late_minutes_raw
	Integer
	YES
	Ép kiểu chuỗi số nguyên từ Excel sang Integer.
	5. Customization Requirements (Yêu cầu Tùy biến Phát triển)
* Custom Models: Khởi tạo mô hình ctv.shift.register để lưu trữ dữ liệu lịch đăng ký ca tuần của khối CTV phục vụ đối soát chấm công chéo.
* Automation & Custom Workflows: Viết hàm đè (Override) phương thức tạo mới bản ghi chấm công. Khi dữ liệu API đổ về có cờ x_is_offsite = True, hệ thống tự động sinh một Activity cảnh báo mức độ khẩn cấp (Urgent) gửi thẳng tới tài khoản của Trưởng bộ phận nhân sự để hậu kiểm vị trí làm việc.
* Cron Jobs: Thiết lập Scheduled Action chạy định kỳ vào 23:00 hàng ngày: Tự động quét toàn bộ bản ghi chấm công trong ngày, nếu phát hiện bản ghi có check_out trống, hệ thống tự động đối chiếu với đơn giải trình quên chấm công (hr.leave loại đặc biệt), nếu không có đơn được duyệt, tự động điền mốc giờ kết thúc ca mặc định và đánh dấu cờ lỗi công việc.
6. Data Quality & Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Xử lý trùng lặp Check-in: Loại bỏ toàn bộ các bản ghi check-in trùng lặp của cùng một nhân sự phát sinh trong biên độ 5 phút (Do nhân viên quét vân tay liên tiếp nhiều lần). Chỉ giữ lại mốc thời gian của lần quét thành công đầu tiên trong ngày.
* Chuẩn hóa dữ liệu: Điền giá trị mặc định công chuẩn bằng 1.0 hoặc 0.5 dựa trên tổng thời gian lưu trú thực tế của nhân sự giữa hai mốc check-in/out.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu: Nạp toàn bộ danh mục lịch làm việc tiêu chuẩn của công ty (resource.calendar), sau đó tiến hành nạp dữ liệu chấm công lịch sử theo chu kỳ từng tháng một để đảm bảo không làm quá tải bộ nhớ đệm máy chủ Postgres.
* Dependency: Bắt buộc phải hoàn tất import dữ liệu Master của hr.employee trước khi nạp dữ liệu chấm công, sử dụng barcode nhân sự làm khóa ngoại tham chiếu.
8. Risks & Edge Cases (Rủi ro & Kịch bản Đặc biệt)
* Xung đột ca làm việc xuyên đêm: Nhân sự khối vận hành kỹ thuật hoặc trực page ca tối làm việc từ 22:00 ngày hôm trước đến 06:00 ngày hôm sau. Odoo tiêu chuẩn sẽ cắt đôi bản ghi chấm công tại mốc 00:00 làm sai lệch số giờ làm việc.
* Giải pháp xử lý: Cấu hình trường check_out cho phép ghi nhận mốc thời gian của ngày T+1, đồng thời tùy biến tầng trung gian Work Entry để phân bổ chính xác ngày công lao động vào tháng phát sinh ca làm việc.
MODULE 3 — PAYROLL & COMPENSATION (QUẢN TRỊ BẢNG LƯƠNG & PHÚC LỢI)
1. Business Analysis (Phân tích Nghiệp vụ)
Hệ thống tính toán tiền lương của Học Bá áp dụng 3 thuật toán cấu trúc lương hoàn toàn biệt lập cho các khối chức năng công tác:
1. Cấu trúc Lương Khối Văn phòng: Lương thực lĩnh tính theo ngày công thời gian thực tế, cộng phụ cấp cố định (Xăng xe, ăn ca, gửi xe, điện thoại), trừ đi khấu trừ bảo hiểm bắt buộc (10.5% phần nhân sự đóng đóng trên mức lương định mức bảo hiểm) và thuế TNCN lũy tiến.
2. Cấu trúc Lương Khối Giảng viên: Thù lao tính khoán trực tiếp bằng: Tổng số giờ dạy thực tế trong tháng $\times$ Đơn giá giờ dạy theo Level chức danh. Không phát sinh khấu trừ BHXH.
3. Cấu trúc Lương Khối Kinh doanh (Sale/CTV): Áp dụng mô hình tính toán hoa hồng doanh số bậc thang động dựa trên bảng cấu hình ma trận 8.2. Lookup KPI. Phần trăm hoa hồng (% COM) dao động từ 1.0% đến 4.4% tùy thuộc vào tổng doanh số tuyển sinh thực thu mà cá nhân đó mang lại trong kỳ tính lương.
2. Source Excel Analysis (Phân tích Bảng tính Nguồn)
* Tệp tin nguồn: Học bá education - 5.1. Tính lương offline.csv, Học bá education - 5.2. Tính lương online.csv, Học bá education - 5.3.Lưu trữ lương offline.csv, Học bá education - 8.2. Lookup KPI.csv.
* Cấu trúc dữ liệu: Lưu trữ ma trận thông tin kế toán lương phức tạp gồm: Lương hợp đồng, Doanh thu, Tỷ lệ hoa hồng, Các khoản phụ cấp phân rã, Tiền phạt đi muộn, Thuế TNCN, Tiền thực lĩnh, Thông tin tài khoản ngân hàng chuyển khoản trực tiếp.
* Đánh giá chất lượng dữ liệu:
   * Vi phạm nguyên tắc chuẩn hóa cơ sở dữ liệu (Denormalization): Nghiêm trọng. Số tài khoản và tên ngân hàng của nhân sự bị sao chép lặp đi lặp lại trên từng dòng lương tháng của file Excel.
   * Lỗi công thức (Formula Errors): Xuất hiện hàng loạt chuỗi ký tự lỗi #ERROR!, #VALUE! tại các cột tính Thuế TNCN và Tổng thu nhập do tham chiếu sang các dòng trống hoặc sai kiểu dữ liệu (Văn bản cộng với Số). Ký hiệu tiền tệ dạng chuỗi văn bản ("₫7,300,000.0") làm công cụ tính toán tự động không thể đọc trực tiếp.
3. Data Model Design (Thiết kế Mô hình Dữ liệu Đích)
* Thực thể chính: hr.payslip (Phiếu lương nhân sự), hr.salary.rule (Quy tắc tính lương), hr.payroll.structure (Cấu trúc lương tổng thể), hr.payslip.input (Tham số biến động đầu vào phiếu lương).
* Mối quan hệ dữ liệu:
   * hr.payslip $\rightarrow hr.employee (Quan hệ Many2one).
   * hr.payroll.structure $\rightarrow hr.salary.rule (Quan hệ One2many cấu thành bộ máy tính toán lương).
* Tham số biến động đầu vào (Payslip Inputs): Khởi tạo các mã tham số đầu vào cố định: REVENUE (Tổng doanh số chốt đơn tuyển sinh tháng), BONUS_LE (Thưởng ngày lễ), PENALTY_LATE (Tiền phạt đi muộn).
* Ràng buộc hệ thống: Không cho phép tạo hai phiếu lương cùng thuộc một kỳ tính lương (Trùng tháng/năm) cho một nhân sự duy nhất.
4. Odoo Model Mapping (Bảng Ánh xạ Dữ liệu Cấp Trường)
Trường dữ liệu Excel
	Ý nghĩa nghiệp vụ
	Mô hình Odoo Đích
	Trường Odoo Đích
	Kiểu dữ liệu
	Bắt buộc
	Quy tắc chuyển đổi (Transformation Rule)
	Mã nhân sự
	Nhân sự nhận lương
	hr.payslip
	employee_id
	Many2one
	YES
	Đối soát từ mã HB.xxx sang ID của hr.employee.
	Tháng / Năm
	Kỳ tính lương tháng
	hr.payslip
	date_from / date_to
	Date
	YES
	Convert chuỗi "Tháng 5" + "2026" $\rightarrow$ 2026-05-01 đến 2026-05-31.
	Lương hợp đồng
	Lương cứng gốc đóng bảo hiểm
	hr.contract
	wage
	Monetary
	YES
	Làm sạch ký hiệu "₫", dấu phẩy phân cách, ép về kiểu Float.
	Doanh thu
	Doanh số sale chốt trong tháng
	hr.payslip.input
	amount (Mã: REVENUE)
	Float
	NO
	Đẩy vào làm tham số Input Line để tính hoa hồng bậc thang.
	Thưởng khác
	Các khoản khen thưởng đột xuất
	hr.payslip.input
	amount (Mã: BONUS)
	Float
	NO
	Nhập dữ liệu phát sinh trực tiếp vào phiếu lương.
	Thuế TNCN
	Khấu trừ thuế thu nhập cá nhân
	hr.payslip.line
	total (Mã: PIT)
	Float
	YES
	Trường tính toán tự động bằng mã Python Rule lũy tiến.
	THỰC LÃNH
	Số tiền chuyển khoản cuối cùng
	hr.payslip.line
	total (Mã: NET)
	Float
	YES
	Kết quả cuối cùng của bài toán tổng thu nhập trừ tổng khấu trừ.
	5. Customization Requirements (Yêu cầu Tùy biến Phát triển)
* Custom Python Salary Rules: Lập trình quy tắc tính Thuế TNCN lũy tiến 7 bậc chuẩn luật Việt Nam bằng mã nguồn Python Rule. Lập trình quy tắc tính hoa hồng bậc thang động cho khối Kinh doanh:
Python
# Python Rule: Tính Hoa hồng bậc thang dựa trên Doanh thu đầu vào (Inputs)
revenue = inputs.REVENUE.amount if hasattr(inputs, 'REVENUE') else 0.0
commission_rate = 0.0
if revenue >= 340000000:
    commission_rate = 0.044
elif revenue >= 270000000:
    commission_rate = 0.040
elif revenue >= 210000000:
    commission_rate = 0.035
elif revenue >= 160000000:
    commission_rate = 0.030
elif revenue >= 120000000:
    commission_rate = 0.025
elif revenue >= 90000000:
    commission_rate = 0.015
elif revenue >= 50000000:
    commission_rate = 0.010


result = revenue * commission_rate


* Automation Workflows: Tích hợp tự động hóa: Khi Trưởng phòng nhân sự xác nhận đóng Bảng công tháng (hr.work.entry chuyển trạng thái duyệt cuối), hệ thống tự động kích hoạt tính năng tạo hàng loạt Phiếu lương nhân sự (Batch Generating Payslips) cho toàn bộ nhân viên đang hoạt động, tự động kéo số ngày công thực tế đi làm vào dòng tính lương thời gian.
6. Data Quality & Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Tách cấu trúc thông tin Ngân hàng: Trích xuất toàn bộ dữ liệu từ cột Số tài khoản và Ngân hàng của file Excel nguồn, đưa về lưu trữ duy nhất tại mô hình thông tin thanh toán tài khoản tư nhân cá nhân (res.partner.bank) liên kết với hồ sơ gốc của nhân viên. Xóa hoàn toàn các chuỗi dữ liệu rác thừa thãi trong cột tiền lương để đưa về kiểu số thuần túy.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu: Bắt buộc phải import dữ liệu lịch sử hợp đồng lao động (hr.contract) ở trạng thái hoạt động trước để hệ thống lấy làm gốc thông tin Lương cơ bản. Tiến hành import dữ liệu biến động đầu vào (hr.payslip.input) cho từng tháng, cuối cùng mới nạp lệnh tính toán tạo dòng lương chi tiết.
8. Risks & Edge Cases (Rủi ro & Kịch bản Đặc biệt)
* Lệch số liệu do điều chỉnh hồi tố (Retroactive Payroll Risk): Kịch bản nhân viên được phê duyệt đơn giải trình công của tháng 4 nhưng đơn này lại được duyệt vào ngày 5 của tháng 5 (Sau khi bảng lương tháng 4 đã chốt và chi trả xong thực tế). Odoo tiêu chuẩn sẽ chặn sửa bảng lương cũ.
* Giải pháp xử lý: Hệ thống tùy biến quy tắc lương để tự động tính toán phần công thiếu sót này và đẩy giá trị tiền lương bù vào danh mục cấu trúc lương của kỳ tháng 5 dưới dạng một dòng tính toán độc lập (Mã quy tắc: PAY_RETRO).
________________
MODULE 4 — RECRUITMENT & TALENT ACQUISITION (QUẢN TRỊ TUYỂN DỤNG & THU HÚT TÀI NĂNG)
1. Business Analysis (Phân tích Nghiệp vụ)
Học Bá Education liên tục mở rộng quy mô đào tạo, dẫn đến tần suất tuyển dụng khối Giảng viên tiếng Trung và khối Tư vấn tuyển sinh diễn ra liên tục. Quy trình bắt đầu từ khi Trưởng bộ phận gửi phiếu yêu cầu bổ sung nhân sự (7.2 Phiếu yêu cầu tuyển dụng). Đường ống quản trị ứng viên (Candidate Pipeline) được chuẩn hóa qua các giai đoạn Kanban chặt chẽ:
[1. Nhận Hồ Sơ] ➔ [2. Lọc CV] ➔ [3. Kiểm Tra Năng Lực / Test Đầu Vào] ➔ [4. Phỏng Vấn] ➔ [5. Đề Xuất Offer] ➔ [6. Nhận Việc / Hired]


Điểm đặc thù của quy trình tuyển dụng giáo viên tại Học Bá là bắt buộc phải trải qua bước Vòng 3: Kiểm tra năng lực ngôn ngữ và dạy thử (Demo Teaching). Kết quả điểm số bài kiểm tra ngữ pháp/khẩu ngữ bám sát cấu trúc của tệp Quy trình Test đầu vào và kết quả đánh giá trình độ phải được lưu trữ trực tiếp trên thẻ hồ sơ ứng viên để làm căn cứ duyệt mức lương Offer cứng sau này.
2. Source Excel Analysis (Phân tích Bảng tính Nguồn)
* Tệp tin nguồn: Học bá education - 7.1 Quy trình tuyển dụng.csv, Học bá education - 7.4 Danh sách CV.csv, Học bá education - 7.5 Danh sách phỏng vấn.csv, Học bá education - 7.6 Danh sách Pass PV_ Nhận việ.csv.
* Cấu trúc dữ liệu: Lưu thông tin liên hệ của ứng viên, kênh nguồn đổ CV (Facebook Ads, Website, Người quen giới thiệu), liên kết tệp tin đính kèm hồ sơ năng lực (Link CV ứng viên), đánh giá kết quả lọc sơ bộ, thời gian hẹn lịch phỏng vấn và chi tiết hạn định mức lương offer được phê duyệt.
* Đánh giá chất lượng dữ liệu:
   * Rủi ro trùng lặp ứng viên (Candidate Duplication): Rất cao. Một ứng viên nộp hồ sơ nhiều lần qua nhiều kênh quảng cáo khác nhau trong vòng 3 tháng dẫn đến hiện tượng nhân bản dữ liệu trên file Excel theo dõi thủ công.
   * Lỗi liên kết dữ liệu (Broken Links): Các cột Link CV ứng viên lưu trữ đường dẫn cục bộ dạng Lark Drive hoặc liên kết hỏng, không thể truy cập trực tiếp từ hệ thống mạng bên ngoài.
3. Data Model Design (Thiết kế Mô hình Dữ liệu Đích)
* Thực thể chính: hr.applicant (Hồ sơ ứng viên chi tiết), hr.recruitment.stage (Các giai đoạn đường ống tuyển dụng), hr.job (Vị trí công việc cần tuyển dụng).
* Mối quan hệ dữ liệu:
   * hr.applicant $\rightarrow hr.job: Quan hệ Many2one phân bổ ứng viên vào đúng chiến dịch tuyển dụng vị trí chức danh.
   * hr.applicant $\rightarrow hr.recruitment.stage: Quan hệ Many2one xác định vị trí thực tế của ứng viên trên bảng Kanban trực quan.
* Trường tính toán: x_conversion_time (Số ngày đo lường từ thời điểm tiếp nhận hồ sơ create_date cho đến khi chuyển trạng thái thành công sang giai đoạn Nhận việc date_open).
* Ràng buộc hệ thống: Thiết lập chỉ mục Unique hỗn hợp kết hợp giữa trường số điện thoại cá nhân của ứng viên và mã vị trí tuyển dụng chiến dịch (partner_phone + job_id). Chặn đứng rủi ro tạo 2 thẻ hồ sơ cho 1 ứng viên trong cùng một đợt tuyển dụng vị trí công việc.
4. Odoo Model Mapping (Bảng Ánh xạ Dữ liệu Cấp Trường)
Trường dữ liệu Excel
	Ý nghĩa nghiệp vụ
	Mô hình Odoo Đích
	Trường Odoo Đích
	Kiểu dữ liệu
	Bắt buộc
	Quy tắc chuyển đổi (Transformation Rule)
	Họ tên ứng viên
	Tên đầy đủ của ứng viên
	hr.applicant
	partner_name
	Char
	YES
	Chuẩn hóa danh từ riêng viết hoa chữ cái đầu.
	Số điện thoại ứng viên
	Điện thoại liên hệ ứng viên
	hr.applicant
	partner_phone
	Char
	YES
	Khóa kiểm tra trùng lặp hồ sơ hệ thống.
	Email ứng viên
	Thư điện tử ứng viên
	hr.applicant
	email_from
	Char
	NO
	Kiểm tra định dạng chuỗi Regex Mail chuẩn hóa.
	Vị trí ứng tuyển
	Vị trí công việc mong muốn
	hr.applicant
	job_id
	Many2one
	YES
	Tìm kiếm mã ID tương ứng trong bảng hr.job.
	Link CV ứng viên
	Tệp tin đính kèm hồ sơ
	hr.applicant
	attachment_ids
	Many2many
	NO
	Download tệp tin từ link nguồn, nạp trực tiếp vào Odoo Binary Attachment.
	Kết quả PV
	Đánh giá vòng phỏng vấn
	hr.applicant
	stage_id
	Many2one
	YES
	"Pass" $\rightarrow$ Dịch chuyển sang Giai đoạn Đề xuất Offer; "Fail" $\rightarrow$ Lưu trữ thẻ.
	Ngày nhận việc
	Ngày bắt đầu đi làm thực tế
	hr.applicant
	date_open
	Date
	NO
	Căn cứ tự động để kích hoạt khởi tạo hồ sơ nhân sự.
	5. Customization Requirements (Yêu cầu Tùy biến Phát triển)
* Custom Fields: Mở rộng mô hình hr.applicant thêm các trường: x_grammar_score (Điểm bài test ngữ pháp), x_speaking_score (Điểm bài test khẩu ngữ), x_demo_class_rating (Đánh giá buổi dạy thử của hội đồng đào tạo).
* Automated Actions & Workflows: Cấu hình luồng tự động gửi Email Mẫu (Bám sát nội dung tệp 7.7 Mail mẫu.csv):
   * Khi kéo ứng viên vào giai đoạn "Phỏng Vấn", hệ thống tự động kích hoạt gửi thư mời tham gia phỏng vấn kèm sơ đồ địa chỉ văn phòng.
   * Khi bấm nút chuyển ứng viên sang trạng thái thành công "Hired", hệ thống tự động kích hoạt Action sinh cấu trúc tài khoản nhân viên mới trên mô hình hr.employee, kế thừa toàn bộ thông tin định danh cá nhân cũ mà không cần nhập liệu lại thủ công.
6. Data Quality & Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Quy trình Gộp Hồ sơ trùng lặp (Deduplication Pipeline): Khi thực hiện chạy script import dữ liệu lịch sử tuyển dụng, nếu phát hiện trùng lặp Số điện thoại, hệ thống tự động gộp dữ liệu (Merge Records), giữ lại thẻ ứng viên có lịch sử phỏng vấn chi tiết nhất và gom toàn bộ các file đính kèm CV cũ vào phần nhật ký Log lưu vết (Chatter) của bản ghi chính duy nhất.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu: Khởi tạo danh mục các giai đoạn Kanban tuyển dụng (hr.recruitment.stage), tiếp theo nạp danh mục vị trí tuyển dụng (hr.job), cuối cùng chạy ETL import toàn bộ danh sách hồ sơ ứng viên lịch sử từ tệp danh sách CV.
* Dependency: Yêu cầu các vị trí công việc phải ở trạng thái hoạt động trên hệ thống trước khi gán hồ sơ ứng viên vào.
8. Risks & Edge Cases (Rủi ro & Kịch bản Đặc biệt)
* Ứng viên ứng tuyển lại sau 6 tháng: Ứng viên từng trượt vòng phỏng vấn cách đây nửa năm, nay tiếp tục nộp hồ sơ ứng tuyển lại cho chiến dịch tuyển dụng mới. Hệ thống Odoo chặn không cho tạo bản ghi trùng dựa trên cấu trúc khóa Unique điện thoại.
* Giải pháp xử lý: Lập trình mã tùy biến kiểm tra khoảng thời gian (Time window check): Nếu bản ghi cũ đã ở giai đoạn 'Refused' (Đã từ chối) và khoảng cách thời gian lớn hơn 180 ngày, hệ thống cho phép bypass qua bộ lọc chặn trùng, tự động lưu trữ hồ sơ cũ thành dữ liệu lịch sử (Archive History) và mở ra một thẻ ứng viên mới tinh cho chiến dịch hiện tại.
________________
MODULE 5 — TIME OFF & LEAVE MANAGEMENT (QUẢN LÝ NGHỈ PHÉP & VẮNG MẶT)
1. Business Analysis (Phân tích Nghiệp vụ)
Công tác quản trị nghỉ phép và vắng mặt tại Học Bá tuân thủ chặt chẽ theo hai nhóm quy trình nghiệp vụ lõi: Cấp phát định mức quỹ phép năm (hr.leave.allocation) và Đăng ký phê duyệt đơn xin nghỉ phép thực tế (hr.leave). Nhân sự chính thức khối văn phòng được hưởng chế độ cấp phát lũy tiến 1 ngày phép hưởng lương cho mỗi tháng làm việc công tác.
Quy trình phê duyệt đơn bám sát cấu trúc tệp 4.1. Xin nghỉ phép, đi trễ_về s.csv yêu cầu kiểm soát chặt chẽ luồng phê duyệt 2 cấp (Trưởng bộ phận duyệt cấp 1 $\rightarrow$ Trưởng phòng nhân sự phê duyệt cấp cuối). Ràng buộc logic quan trọng nhất đối với khối Giảng viên là: Tuyệt đối không cho phép nộp đơn xin nghỉ phép nếu khung thời gian xin nghỉ trùng với lịch dạy trực tuyến cố định đã được phân công từ trước, trừ trường hợp đã có nhân sự dạy thay được xác nhận trên phân hệ Sản phẩm.
2. Source Excel Analysis (Phân tích Bảng tính Nguồn)
* Tệp tin nguồn: Học bá education - 3.5. Theo dõi ngày phép.csv, Học bá education - 4.1. Xin nghỉ phép, đi trễ_về s.csv.
* Cấu trúc dữ liệu: Lưu trữ thông tin nhân sự làm đơn, loại nghỉ phép (Nghỉ phép năm, Nghỉ thai sản, Nghỉ việc riêng không lương, Xin đi trễ/về sớm), mốc thời gian bắt đầu/kết thúc đơn chi tiết, tổng thời hạn định mức nghỉ quy đổi ra số ngày công, lý do làm đơn, trạng thái phê duyệt của cấp quản lý và mã đơn gốc SourceID.
* Đánh giá chất lượng dữ liệu:
   * Tính toán sai lệch quỹ công tồn phép (Wrong Balance Accumulation): Xuất hiện tình trạng giá trị âm tại cột số phép còn lại (Số phép còn lại) trên file Excel do quản lý duyệt phép vượt định mức cho phép của nhân sự thử việc hoặc CTV chưa được cấu hình quyền hưởng phép năm.
   * Lỗi chuỗi số (Duration Formatting Error): Cột tổng thời gian nghỉ lưu chuỗi hỗn hợp lúc tính bằng đơn vị ngày ("1 day"), lúc tính bằng đơn vị giờ ("4 hours"), gây mất tính thống nhất của thuật toán đối soát tự động cuối tháng.
3. Data Model Design (Thiết kế Mô hình Dữ liệu Đích)
* Thực thể chính: hr.leave (Đơn đăng ký nghỉ phép), hr.leave.type (Danh mục phân loại hình thức nghỉ), hr.leave.allocation (Quy trình cấp phát định mức quỹ phép).
* Mối quan hệ dữ liệu: hr.leave $\rightarrow$ hr.leave.type (Quan hệ Many2one qua trường holiday_status_id). hr.leave $\rightarrow$ hr.employee (Quan hệ Many2one).
* Trường tính toán: number_of_days (Trường tính toán tự động lấy mốc ngày kết thúc trừ ngày bắt đầu, tích hợp cấu hình loại trừ các ngày nghỉ lễ quốc gia theo quy định nhà nước và hai ngày nghỉ cuối tuần Thứ 7/Chủ nhật khỏi quỹ phép khấu trừ).
* Ràng buộc hệ thống (Database Level Constraints): Chặn hoàn toàn hành vi nộp đơn trùng lặp thời gian (Leave Overlap): Không được tồn tại 2 đơn xin nghỉ phép có khoảng thời gian giao nhau của cùng một nhân sự.
4. Odoo Model Mapping (Bảng Ánh xạ Dữ liệu Cấp Trường)
Trường dữ liệu Excel
	Ý nghĩa nghiệp vụ
	Mô hình Odoo Đích
	Trường Odoo Đích
	Kiểu dữ liệu
	Bắt buộc
	Quy tắc chuyển đổi (Transformation Rule)
	SourceID
	Mã đơn gốc hệ thống Lark
	hr.leave
	x_lark_leave_id
	Char
	YES
	Khóa kiểm soát đồng bộ dữ liệu đơn qua cổng API Staging layer.
	Status
	Trạng thái phê duyệt của đơn
	hr.leave
	state
	Selection
	YES
	"Approved" $\rightarrow$ 'validate'; "Under Review" $\rightarrow$ 'confirm'.
	Requester
	Nhân sự làm đơn xin nghỉ
	hr.leave
	employee_id
	Many2one
	YES
	Match chuỗi họ tên hoặc tài khoản Lark sang ID của hr.employee.
	Leave type
	Phân loại hình thức nghỉ
	hr.leave
	holiday_status_id
	Many2one
	YES
	"Xin nghỉ phép" $\rightarrow$ Loại phép năm; "Nghỉ thai sản" $\rightarrow$ Loại thai sản.
	Start time
	Thời điểm bắt đầu nghỉ phép
	hr.leave
	date_from
	Datetime
	YES
	Ép chuẩn hóa về cấu trúc thời gian máy chủ hệ thống (Múi giờ UTC).
	End time
	Thời điểm kết thúc nghỉ phép
	hr.leave
	date_to
	Datetime
	YES
	Ép chuẩn hóa về cấu trúc thời gian máy chủ hệ thống (Múi giờ UTC).
	Duration (number)
	Tổng số ngày xin nghỉ
	hr.leave
	number_of_days
	Float
	YES
	Chuyển đổi định dạng số thực để trừ trực tiếp vào quỹ số dư phép.
	5. Customization Requirements (Yêu cầu Tùy biến Phát triển)
* Custom Inter-Module Constraint Workflow: Lập trình mã nguồn mở mở rộng cơ chế kiểm tra chéo (Cross-module validation rule) mức cơ sở dữ liệu: Khi nhân sự thuộc Khối Giảng viên nộp đơn nghỉ phép, hệ thống tự động kích hoạt một câu lệnh SQL truy vấn sang bảng quản lý lịch lớp học (academic.session). Nếu phát hiện giảng viên có lịch dạy đang ở trạng thái hoạt động nằm trong khung giờ xin nghỉ phép, hệ thống lập tức chặn thao tác và hiển thị thông báo lỗi yêu cầu điều phối giảng viên dạy thay trước.
Python
# Python Constraint: Chặn giảng viên nghỉ phép nếu vướng lịch dạy lớp học cố định
from odoo import models, api, _
from odoo.exceptions import ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'


    @api.constrains('date_from', 'date_to', 'employee_id', 'state')
    def _check_academic_session_conflicts(self):
        for record in self:
            if record.state in ['confirm', 'validate'] and record.employee_id.x_work_mode == 'online':
                # Truy vấn kiểm tra chéo sang bảng phân hệ quản lý lớp học online
                conflicting_sessions = self.env['academic.session'].search([
                    ('teacher_id', '=', record.employee_id.id),
                    ('start_time', '<', record.date_to),
                    ('end_time', '>', record.date_from),
                    ('state', '=', 'confirmed')
                ])
                if conflicting_sessions:
                    raise ValidationError(_("Lỗi hệ thống: Giảng viên đang có lịch dạy lớp học trực tuyến cố định trong khung giờ xin nghỉ phép. Vui lòng thực hiện điều phối nhân sự dạy thay trên phân hệ Giáo vụ trước khi phê duyệt đơn phép!"))


6. Data Quality & Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Đồng bộ hóa đơn từ Giải trình Công: Các đơn mang tính chất giải trình vắng mặt ngắn như "Xin đi trễ", "Xin về sớm", hoặc "Đề xuất làm online" bắt buộc phải được tách lọc ra khỏi mô hình nghỉ phép khấu trừ phép năm. Toàn bộ các loại đơn này sẽ được cấu hình map sang hệ thống phân loại công trung gian của Odoo (Work Entry Types), đảm bảo khi đơn được phê duyệt, hệ thống tự động sinh giờ công làm việc bình thường cho nhân sự trên bảng công tổng hợp.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu: Khởi tạo danh mục các loại nghỉ phép (hr.leave.type), sau đó chạy import toàn bộ dữ liệu định mức số dư phép tồn năm cũ của nhân viên vào bảng quy trình cấp phát quỹ phép (hr.leave.allocation) ở trạng thái đã phê duyệt ('validate'). Cuối cùng mới thực hiện import danh sách lịch sử các đơn xin nghỉ phép thực tế của các tháng cũ để hệ thống tự động thực hiện trừ lùi số dư phép.
8. Risks & Edge Cases (Rủi ro & Kịch bản Đặc biệt)
* Đơn nghỉ phép vắt qua 2 năm tài chính: Nhân sự nộp đơn xin nghỉ phép từ ngày 25/12/2025 đến ngày 05/01/2026. Odoo tiêu chuẩn yêu cầu khấu trừ toàn bộ số ngày nghỉ vào quỹ phép của năm tạo đơn (2025), dẫn đến hiện tượng sai lệch hạn định quỹ phép năm mới 2026.
* Giải pháp xử lý: Lập trình mã nguồn tùy biến tự động phân rã đơn phép (Leave Splitting Algorithm): Khi phát hiện đơn nghỉ phép vắt qua mốc ngày 31/12, hệ thống tự động tách đơn thành 2 bản ghi độc lập trên cơ sở dữ liệu: Bản ghi 1 thuộc quỹ phép năm 2025, Bản ghi 2 tự động trừ vào hạn mức quỹ phép năm mới 2026.
________________
PHẦN 2: KIẾN TRÚC KỸ THUẬT TỔNG THỂ & CHIẾN LƯỢC CHUYỂN ĐỔI DỮ LIỆU
1. DATABASE DESIGN & GLOBAL ENTITY RELATIONSHIP DIAGRAM (ERD)
Để đảm bảo tính toàn vẹn dữ liệu và triệt tiêu hoàn toàn các lỗi phi chuẩn hóa từ hệ thống Excel cũ, cấu trúc cơ sở dữ liệu đích trên Postgres của hệ thống Odoo 19 ERP được thiết kế theo chuẩn hóa dữ liệu sâu sắc, thiết lập các ràng buộc khóa cứng nghiêm ngặt ở mức Database vật lý.
Đặc tả Kiến trúc Mối Quan hệ Thực thể Hệ thống (Global ERD Schema Definition)
+--------------------------------------------------------------------------------------------------+
|                                        RES.COMPANY (Chi Nhánh)                                   |
+--------------------------------------------------------------------------------------------------+
| PK | id (Integer)                                                                                |
|    | name (Varchar) - UNIQUE                                                                     |
+--------------------------------------------------------------------------------------------------+
                                                 | 1
                                                 |
                                                 | N (Foreign Key: company_id)
+--------------------------------------------------------------------------------------------------+
|                                     HR.DEPARTMENT (Phòng Ban)                                    |
+--------------------------------------------------------------------------------------------------+
| PK | id (Integer)                                                                                |
|    | name (Varchar)                                                                              |
| FK | parent_id (Integer) REFERENCES hr_department(id) ON DELETE SET NULL [Self-Reference]         |
| FK | company_id (Integer) REFERENCES res_company(id) ON DELETE RESTRICT                          |
+--------------------------------------------------------------------------------------------------+
                                                 | 1
                                                 |
                                                 | N (Foreign Key: department_id)
+--------------------------------------------------------------------------------------------------+
|                                       HR.EMPLOYEE (Nhân Sự Master)                               |
+--------------------------------------------------------------------------------------------------+
| PK | id (Integer)                                                                                |
|    | name (Varchar)                                                                              |
|    | barcode (Varchar) - UNIQUE INDEX [HB.xxx]                                                   |
|    | identification_id (Varchar) - UNIQUE INDEX [CCCD]                                           |
|    | work_email (Varchar) - UNIQUE INDEX                                                         |
|    | mobile_phone (Varchar) - UNIQUE INDEX                                                       |
| FK | department_id (Integer) REFERENCES hr_department(id) ON DELETE RESTRICT                    |
| FK | job_id (Integer) REFERENCES hr_job(id) ON DELETE RESTRICT                                   |
|    | x_lark_user_id (Varchar) - UNIQUE INDEX                                                     |
|    | x_work_mode (Selection) - ['offline', 'online', 'ctv']                                      |
+--------------------------------------------------------------------------------------------------+
         | 1                               | 1                                 | 1
         |                                 |                                   |
         | N                               | N                                 | N
+-----------------------+         +-----------------------+         +-----------------------+
|  HR.CONTRACT (HĐLĐ)   |         | HR.ATTENDANCE (Công)  |         |   HR.LEAVE (Nghỉ Phép)  |
+-----------------------+         +-----------------------+         +-----------------------+
| PK | id (Integer)     |         | PK | id (Integer)     |         | PK | id (Integer)     |
| FK | employee_id (FK) |         | FK | employee_id (FK) |         | FK | employee_id (FK) |
|    | date_start (Date)|         |    | check_in (Tstamp)|         |    | date_from (Tstamp)|
|    | date_end (Date)  |         |    | check_out(Tstamp)|         |    | date_to (Tstamp)  |
|    | wage (Monetary)  |         |    | x_lark_id - UNIQUE|        |    | state (Selection) |
|    | state (Selection)|         |    | CONSTRAINT:      |         |    | CONSTRAINT:       |
|    | CONSTRAINT:      |         |    | check_out >      |         |    | No overlap per    |
|    | No overlapping   |         |    | check_in         |         |    | employee          |
|    | contracts active |         |                       |         |                       |
+-----------------------+         +-----------------------+         +-----------------------+
         | 1
         |
         | 1
+--------------------------------------------------------------------------------------------------+
|                                        HR.PAYSLIP (Phiếu Lương)                                  |
+--------------------------------------------------------------------------------------------------+
| PK | id (Integer)                                                                                |
| FK | employee_id (Integer) REFERENCES hr_employee(id) ON DELETE RESTRICT                         |
| FK | contract_id (Integer) REFERENCES hr_contract(id) ON DELETE RESTRICT                         |
|    | date_from (Date)                                                                            |
|    | date_to (Date)                                                                              |
|    | state (Selection) - ['draft', 'verify', 'done', 'cancel']                                   |
+--------------------------------------------------------------------------------------------------+


Chiến lược Thiết lập Chỉ mục Cơ sở dữ liệu (Database Indexing Strategy)
Để đảm bảo hiệu năng vận hành hệ thống tối ưu khi quy mô nhân sự tăng trưởng liên tục và cổng API đồng bộ dữ liệu chấm công quét liên tục hàng giờ, các cấu trúc Index chuyên biệt được thiết lập trực tiếp tại tầng vật lý Postgres:
* B-Tree Indexes mở rộng: Áp dụng cho toàn bộ các trường khóa tìm kiếm tần suất cao: hr_employee(barcode), hr_employee(x_lark_user_id), hr_attendance(check_in, check_out).
* Partial Indexes đặc thù: Tối ưu hóa hiệu năng thuật toán quét bảng lương và phân bổ công việc bằng cách chỉ lập chỉ mục cho danh mục nhân sự đang hoạt động thực tế trên hệ thống: CREATE INDEX idx_active_employees ON hr_employee(id) WHERE active = true;.
2. RECOMMENDED ODOO TECHNICAL ARCHITECTURE (KIẾN TRÚC HỆ THỐNG ĐỀ XUẤT)
Hệ thống kiến trúc đích được xây dựng trên nền tảng phiên bản Odoo 19 Enterprise, triển khai theo mô hình hạ tầng độc lập để đảm bảo tối đa quyền kiểm soát mã nguồn và tối ưu hiệu năng xử lý cơ sở dữ liệu.
                 [ CỔNG TRUY CẬP NGƯỜI DÙNG / USER CLIENTS ]
             (Ứng dụng Mobile Odoo / Trình duyệt Web Văn phòng)
                                     |
                                     v
                  +--------------------------------------+
                  |   Nginx Reverse Proxy & SSL Offload  |
                  +--------------------------------------+
                                     |
                +--------------------+--------------------+
                | Giờ hành chính                          | Tải nặng / Báo cáo
                v                                         v
+--------------------------------+        +--------------------------------+
|  Odoo App Server (Instance 1)  |        |  Odoo App Server (Instance 2)  |
|     [Xử lý giao dịch chính]     |        |   [Xử lý tác vụ nền/Cron]      |
+--------------------------------+        +--------------------------------+
                |                                         |
                +--------------------+--------------------+
                                     | Kết nối kết khối
                                     v
                  +--------------------------------------+
                  |        PgBouncer (Connection Pool)   |
                  +--------------------------------------+
                                     |
                                     v
                  +--------------------------------------+
                  |      PostgreSQL Database Server      |
                  |     (Bộ lưu trữ dữ liệu vật lý)      |
                  +--------------------------------------+


* Tách biệt Luồng xử lý công việc (Multi-Instance Load Balancing): Hạ tầng chia tách thành 2 Odoo Instances chạy song song: Instance 1 chuyên biệt tiếp nhận luồng tương tác thao tác trực tiếp của người dùng (Web/Mobile Client). Instance 2 cấu hình cô lập chuyên trách xử lý các tác vụ ngầm tính toán nặng (Scheduled Actions/Cron Jobs) như thuật toán tự động tính toán lương cuối tháng, chạy ma trận đối soát công vân tay, để đảm bảo hệ thống không bao giờ xảy ra hiện tượng nghẽn lag (CPU Spike).
* Tích hợp Hệ thống Lark Suite qua Cổng API Gateway: Xây dựng một Custom Controller đóng vai trò cổng tiếp nhận Endpoint Webhook an toàn từ Lark. Khi nhân sự quét chấm công vân tay thành công hoặc phiếu phê duyệt đơn từ trên Lark chuyển sang trạng thái duyệt cuối, hệ thống Lark tự động bắn một gói tin JSON chứa Metadata sang Odoo API Gateway. Odoo phân tích gói tin, chạy bộ lọc quy tắc kiểm tra tính toàn vẹn (Validation Rules) và cập nhật thẳng dữ liệu vào Postgres theo thời gian thực (Realtime).
3. COMPREHENSIVE MASTER DATA MIGRATION STRATEGY (CHIẾN LƯỢC CHUYỂN ĐỔI DỮ LIỆU TOÀN DIỆN)
Quá trình chuyển đổi dữ liệu từ hệ thống các bảng tính Excel phân tán cũ sang cơ sở dữ liệu tập trung Odoo 19 tuân thủ chặt chẽ theo mô hình thiết kế đường ống ETL (Extract - Transform - Load) 4 giai đoạn, vận hành qua vùng đệm Staging Layer độc lập để triệt tiêu hoàn toàn rủi ro làm nhiễm bẩn cơ sở dữ liệu đích.
Sơ đồ Kiến trúc Đường ống Dịch chuyển Dữ liệu (ETL Pipeline Architecture)
[ Hệ thống Excel Nguồn ] 
          |
          v
+---------------------------------------------------------------------------------+
|                          STAGE 1: EXTRACT & STAGING LAYER                       |
| - Đọc toàn bộ file CSV thô, nạp vào các bảng tạm vật lý trong Database Postgres.|
| - Không áp bất kỳ ràng buộc logic hay khóa ngoại nào tại giai đoạn này.        |
+---------------------------------------------------------------------------------+
          |
          v
+---------------------------------------------------------------------------------+
|                        STAGE 2: TRANSFORM & VALIDATION LAYER                    |
| - Khởi chạy Script Python làm sạch chuỗi (Trim, loại bỏ emoji rác 💰).         |
| - Quy đổi múi giờ từ UTC+7 cục bộ về múi giờ máy chủ UTC chuẩn quốc tế.         |
| - Chạy hàm toán học xử lý Net-to-Gross đối với dữ liệu lịch sử bảng lương.       |
+---------------------------------------------------------------------------------+
          |
          v
+---------------------------------------------------------------------------------+
|                          STAGE 3: LOAD & INTEGRITY CHECK                        |
| - Tiến hành nạp dữ liệu tuần tự vào Odoo tuân thủ theo cây trình tự phụ thuộc.  |
| - Thực thi lệnh lưu vết liên kết mã nguồn cũ thông qua cơ chế External IDs.     |
+---------------------------------------------------------------------------------+
          |
          v
[ Hệ thống Odoo 19 Đích (Sạch & Chuẩn Hóa) ]


Bản Đặc tả Trình tự Nạp Dữ liệu An toàn (Safe Import Sequence Order)
Để chặn hoàn toàn các lỗi vi phạm ràng buộc khóa ngoại (Integrity Constraint Violations), tiến trình Load bắt buộc phải thực thi tuần tự theo đúng 7 bước quy định của cây cấu trúc phụ thuộc dưới đây:
(Bước 1: res.company / res.users) ➔ (Bước 2: hr.department) ➔ (Bước 3: hr.job)
                                                                     |
                                                                     v
(Bước 6: hr.attendance / hr.leave) ⮘ (Bước 5: hr.contract) ⮘ (Bước 4: hr.employee)
       |
       v
(Bước 7: hr.payslip - Thực thể phụ thuộc cuối cùng)


Chiến lược Quay lui và An toàn Cơ sở dữ liệu (Rollback & Data Isolation Strategy)
Toàn bộ tiến trình import dữ liệu của từng lô tệp tin (Batch) bắt buộc phải được đóng gói gọn gàng trong một khối giao dịch cơ sở dữ liệu mã nguồn duy nhất (Database Transaction Block).
Nếu trong quá trình import tệp tin danh sách 500 nhân sự, hệ thống phát hiện chỉ duy nhất 1 dòng bản ghi ở dòng thứ 499 bị sai lệch định dạng ngày tháng hoặc vắng mặt khóa ngoại tham chiếu sang phòng ban, hệ thống lập tức phát lệnh db.rollback() hủy bỏ hoàn toàn trạng thái import của toàn bộ 499 dòng trước đó, trả cơ sở dữ liệu về trạng thái sạch hoàn hảo ban đầu. Không chấp nhận kịch bản import lỗi một nửa làm rác hệ thống.
4. GLOBAL GAP ANALYSIS SUMMARY (BẢN TỔNG HỢP PHÂN TÍCH GAP HỆ THỐNG)
Bản phân tích Gap xác định rõ ranh giới kiến trúc giữa các tính năng tiêu chuẩn hệ thống Odoo 19 sẵn có (Standard Out-of-the-box) và các phân hệ bắt buộc phải tiến hành lập trình tùy biến mở rộng (Custom Development) để đáp ứng trọn vẹn mô hình vận hành giáo dục đặc thù của Học Bá.
                               [ MA TRẬN PHÂN BỔ TÍNH NĂNG GAP ]
+---------------------------------------------------------------------------------------------------+
|  [ PHÂN HỆ ODOO STANDARD ]                                                                        |
|  - Sơ đồ tổ chức phòng ban (hr.department)                                                         |
|  - Hồ sơ nhân viên cơ bản (hr.employee)                                                           |
|  - Hợp đồng lao động tiêu chuẩn (hr.contract)                                                      |
|  - Bộ máy chạy quy tắc tính toán lương thời gian tĩnh (hr.payslip)                                 |
|  - Đường ống Kanban tiếp nhận hồ sơ ứng viên tuyển dụng (hr.applicant)                             |
+---------------------------------------------------------------------------------------------------+
                                                 |
                                                 v Tích hợp / Kế thừa mã nguồn
+---------------------------------------------------------------------------------------------------+
|  [ PHÂN HỆ DEVELOPMENT CUSTOMIZATION (YÊU CẦU LẬP TRÌNH BỔ SUNG) ]                                 |
|  - Module x_hb_attendance_ext:                                                                    |
|    + Cơ chế so khớp ma trận lịch đăng ký ca tuần cho khối CTV.                                    |
|    + Tự động đồng bộ phiếu quên chấm công, làm online để vá dữ liệu chấm công thô.               |
|  - Module x_hb_payroll_ext:                                                                       |
|    + Thuật toán nhúng mã Python tính hoa hồng bậc thang động liên kết với doanh thu thực thu CRM. |
|    + Cơ chế tách lọc thù lao giảng dạy theo buổi (Session rate) khối Giáo viên.                   |
|  - Module x_hb_leave_ext:                                                                         |
|    + Thuật toán chặn cứng vắng mặt trùng lịch ca dạy trực tuyến cố định của Giáo viên.            |
+---------------------------------------------------------------------------------------------------+


5. SYSTEMIC RISKS & BUSINESS EDGE CASES MATRIX (MA TRẬN QUẢN TRỊ RỦI RO HỆ THỐNG)
Bản đặc tả kỹ thuật dự phòng các kịch bản lỗi hệ thống (Edge Cases) có thể phát sinh trong quá trình vận hành thực tế tại doanh nghiệp giáo dục Học Bá, đi kèm giải pháp thiết kế kiến trúc xử lý triệt để:
Mã Rủi Ro
	Phân Hệ
	Mô tả Tình huống Lỗi (Edge Case Scenario)
	Tác động Vận hành
	Phương án Giải quyết Kiến trúc (Architectural Solution)
	R-SYS-01
	Payroll
	Xung đột cấu trúc lương khi đổi vai trò giữa tháng: Nhân viên HB.85 đang hưởng cấu trúc lương thử việc Kinh doanh, đến ngày 15 của tháng có quyết định lên chính thức chuyển sang Khối Vận hành.
	Tính toán sai lệch tiền lương, lỗi ma trận phụ cấp hành chính.
	Thiết lập quy trình tự động đóng (Close) hợp đồng cũ tại ngày 14, tạo mới hợp đồng chính thức có hiệu lực từ ngày 15. Bộ máy lương Odoo tự động sinh 2 phiếu lương thành phần tỉ lệ theo ngày công (Pro-rata Payslips) trong cùng một kỳ lương tháng.
	R-SYS-02
	Attendance
	Hiện tượng Spam thiết bị đẩy dữ liệu trùng lặp ca: Hệ thống Anycross bị lỗi mạng dẫn đến việc đẩy lặp đi lặp lại một bản ghi chấm công thô của ứng viên qua cổng API.
	Nhân đôi số lượng ngày công, tính sai lệch số phút đi muộn.
	Thiết lập chỉ mục Unique cứng kết hợp giữa mã định danh bản ghi Lark và mốc thời gian (x_lark_result_id + check_in). Sử dụng mệnh đề SQL ON CONFLICT DO NOTHING ở tầng kiến trúc để loại bỏ hoàn toàn các gói tin trùng lặp.
	R-SYS-03
	Time Off
	Giảng viên đột xuất xin nghỉ phép khi lớp học đang diễn ra: Giáo viên gặp sự cố bất khả kháng, làm đơn xin nghỉ cấp bách khi học viên đã vào phòng học trực tuyến Zoom.
	Hủy hoại trải nghiệm khách hàng học viên, vỡ tiến độ đào tạo.
	Luồng phê duyệt đơn khẩn cấp kích hoạt: Hệ thống Odoo chạy lệnh gửi thông báo Realtime qua Bot Lark tag trực tiếp bộ phận Giáo vụ (Academic Officers). Đồng thời đóng băng trạng thái lớp học, tự động chuyển đổi quyền sở hữu phòng Zoom sang danh sách Giảng viên dự phòng (Substitute Teacher) đã cấu hình sẵn trong hệ thống Database.
	R-SYS-04
	Recruitment
	Ứng viên nộp hồ sơ đồng thời vào hai vị trí chức danh: Một ứng viên vừa nộp CV vào vị trí Giảng viên tiếng Trung vừa nộp vào vị trí Chuyên viên Nghiên cứu Sản phẩm (R&D).
	Phân rã dữ liệu, hai chuyên viên tuyển dụng tiếp cận trùng nhau.
	Hệ thống thiết lập mô hình hồ sơ đối tác trung tâm (res.partner). Một ứng viên duy nhất chỉ có một bản ghi Partner gốc lưu trữ định danh SĐT/Email, nhưng được phép liên kết song song với hai thẻ ứng tuyển tuyển dụng (hr.applicant) độc lập gắn với hai Stage Kanban khác nhau.
	



Alpha


HỌC BÁ EDUCATION
PHÂN TÍCH NHÂN SỰ & ĐỀ XUẤT TRIỂN KHAI ODOO 19 HR




Tài liệu phân tích nội bộ
Phiên bản 1.0  |  Tháng 5/2026
Người soạn: Claude (Anthropic AI) theo yêu cầu của Học Bá
	________________


Mục lục




________________


PHẦN 1: PHÂN TÍCH NHÂN SỰ HIỆN TẠI CỦA HỌC BÁ
Phần này tổng hợp toàn bộ cách Học Bá Education đang quản lý nhân sự, bao gồm cơ cấu tổ chức, quy mô nhân sự, các quy trình vận hành và công cụ đang sử dụng, dựa trên dữ liệu thực tế từ file Excel quản lý nội bộ.
1.1. Quy mô & cơ cấu tổ chức
Tổng nhân sự
	Chính thức
	Thử việc
	Đã nghỉ việc
	53 người (T5/2026)
	30 người
	23 người
	~15 hồ sơ lưu trữ
	

Học Bá có 6 phòng ban, mỗi phòng có trưởng phòng chịu trách nhiệm:
Phòng ban
	Trưởng phòng
	Số NS (offline/online)
	Chức năng chính
	Kinh Doanh
	Trần Thị Ngọc Ánh
	Tư vấn tuyển sinh (TVTS)
	Bán hàng, chốt học viên
	Marketing
	Nguyễn Trung Kiên
	Content, Ads, Social
	Tăng lead, thương hiệu
	Phòng R&D_SP
	Phan Quỳnh Giang
	Giáo viên, R&D, Tester
	Sản phẩm, học liệu
	Vận Hành
	Cao Vân Khánh
	QLHV, lớp học
	Quản lý học viên
	Kế Toán
	Nguyễn Thị Len (online)
	Online
	Thu chi, quyết toán
	Phòng Nhân sự
	Hoàng Thị Ngọc Anh
	HCNS offline
	HR, tuyển dụng, hành chính
	

Phân loại hình thức làm việc:
* Offline (full-time tại văn phòng 360 Giải Phóng, Hà Nội): ~16 nhân sự
* Online/Remote (part-time, remote): ~20 nhân sự
* CTV – Cộng tác viên (theo đầu việc): ~17 nhân sự


1.2. Các module quản lý nhân sự hiện tại
Học Bá đang quản lý nhân sự phân tán trên nhiều file Excel, Google Sheet và ứng dụng Lark Suite. Dưới đây là 8 module chính:
1.2.1 Hồ sơ nhân sự (Sheet 2.1 – 168 dòng)
Đây là master record của toàn bộ nhân sự, chứa thông tin đầy đủ:
* Định danh: Mã HB.xx, họ tên, ngày sinh, giới tính, CCCD, số điện thoại, email cá nhân/công ty
* Địa chỉ thường trú và địa chỉ hiện tại
* Thông tin gia đình, học vấn, tình trạng hôn nhân
* Trạng thái: Chính thức / Thử việc / Nghỉ việc / Online / TTS / Parttime
* Hình thức: Offline hoặc Online
* Ngày thử việc, ngày chính thức, ngày nghỉ việc
* Tài khoản ngân hàng (số TK + ngân hàng)
* Tài sản cấp phát: màn hình, CPU, bàn phím, chuột, tai nghe, ghế, bàn


1.2.2 Lương & Phúc lợi (Sheets 2.2, 5.1, 5.2)
Lương được chia thành 2 dạng riêng biệt:
* Lương Offline (nhân sự tại VP): tính phức tạp, gồm lương thời gian + COM + KPI + phụ cấp
* Lương Online/CTV: đơn giản hơn, chủ yếu là lương cứng + thưởng theo kết quả


Cấu trúc thu nhập nhân sự Offline bao gồm:
Khoản mục
	Mô tả
	Ghi chú
	Lương cơ bản (wage)
	Mức lương hợp đồng
	6.2M – 24M
	Lương đóng BHXH
	Mức lương làm căn cứ đóng BH
	5.1M – 7.3M
	PC xăng xe
	Phụ cấp xăng xe hàng tháng
	0 – 1,000,000
	PC gửi xe
	Phụ cấp gửi xe
	0 – 100,000
	PC chức vụ
	Phụ cấp theo chức danh quản lý
	Tuỳ chức vụ
	PC thâm niên
	Phụ cấp theo số tháng làm việc
	Theo thâm niên
	Hỗ trợ điện thoại
	Cước điện thoại công việc
	300,000
	Hỗ trợ ăn ca
	Tiền ăn trưa
	700,000
	Hỗ trợ trang phục
	Phụ cấp trang phục
	400,000
	Hỗ trợ đi lại
	Đi lại ngoài VP (chủ yếu online NS)
	200,000
	COM / Lương KPI
	Hoa hồng doanh thu theo % và level
	Biến động lớn
	BHXH 8% NV
	Nhân viên đóng BHXH
	Bắt buộc
	BHYT 1.5% NV
	Nhân viên đóng BHYT
	Bắt buộc
	BHTN 1% NV
	Nhân viên đóng BHTN
	Bắt buộc
	Thuế TNCN
	Thuế thu nhập cá nhân
	Sau giảm trừ NPT
	THỰC LÃNH
	Thu nhập thực nhận = TỔNG THU NHẬP – BH NV – Thuế
	Net wage
	

1.2.3 Hệ thống KPI & COM – Bảng Level 0–10
Học Bá sử dụng bảng 11 level (0–10) để xác định lương cứng, KPI target và % COM cho vị trí TVTS (Tư vấn tuyển sinh). Đây là cấu trúc đặc thù nhất, cần xử lý riêng khi triển khai Odoo:
Level
	Lương cứng
	KPI Target
	% COM
	COM (nếu đạt)
	Tổng TN
	0
	6,200,000
	50,000,000
	1.0%
	500,000
	6,700,000
	1
	6,200,000
	90,000,000
	1.5%
	1,350,000
	7,550,000
	2
	7,000,000
	120,000,000
	2.5%
	3,000,000
	10,000,000
	3
	8,000,000
	160,000,000
	3.0%
	4,800,000
	12,800,000
	5
	9,200,000
	270,000,000
	4.0%
	10,800,000
	20,000,000
	7
	11,400,000
	420,000,000
	4.7%
	19,740,000
	31,140,000
	10
	15,000,000
	720,000,000
	5.2%
	37,440,000
	52,440,000
	

1.2.4 Chấm công (Sheets 3.3, 3.4, 3.6)
Hệ thống chấm công được tích hợp qua Lark Suite với dữ liệu sync về Anycross:
* Sheet 3.3 – Raw attendance log: 10,076 bản ghi, lưu check-in/check-out theo ngày, gồm vị trí (GPS), loại (onsite/offsite), số phút đi trễ, số phút thiếu
* Sheet 3.4 – Bảng công tháng: Tổng hợp công chuẩn, công thực tế, công online, nghỉ phép, nghỉ lễ, nghỉ thai sản, tăng ca, trừ công
* Sheet 3.6 – Bảng công OT: Phân loại giờ tăng ca theo hệ số 100%, 150%, 300%


Quy trình chấm công: Ca làm việc 8h–19h (check-in từ 8h–9h30). Nhân viên check-in/check-out qua app Lark. Nếu quên → nộp phiếu quên chấm công, leader duyệt trước 12h ngày T+1.
	

1.2.5 Nghỉ phép & Làm online (Sheets 4.1, 4.2, 3.5)
* Các loại nghỉ: Nghỉ phép năm, Nghỉ ốm, Về sớm, Đi trễ, Nghỉ thai sản
* Sheet 3.5 theo dõi số dư nghỉ phép theo từng nhân viên (phép năm, phép tồn, phép đã dùng, còn lại)
* Sheet 4.2 theo dõi 279 yêu cầu làm online – hiện không có loại riêng trong Odoo, cần cấu hình thêm
* Tất cả đơn xin nghỉ đều qua luồng Approval trên Lark: Nhân viên → Leader → HCNS duyệt


1.2.6 Theo dõi hợp đồng lao động (Sheet 2.5)
* 39 hợp đồng đang theo dõi (chỉ nhân sự offline đang làm và một số đã nghỉ)
* Loại hợp đồng: HĐ thử việc 2 tháng → HĐ lao động 6 tháng / 12 tháng / không xác định thời hạn
* Theo dõi: Ngày ký, ngày hết hạn, ngày tái ký, số lần ký, link file hợp đồng
* Quy trình nghỉ việc chuẩn: Đơn 30–45 ngày trước → phỏng vấn nghỉ việc → bàn giao → thanh lý HĐ


1.2.7 Tuyển dụng (Sheets 7.1 – 7.9)
Quy trình 10 bước từ Order đến Onboarding:
* Bước 1: TBP gửi Order tuyển dụng (kèm JD)
* Bước 2: Đăng tuyển + tổng hợp CV
* Bước 3: Lọc CV (Pass/Fail)
* Bước 4–5: Sắp xếp lịch phỏng vấn, hẹn ứng viên
* Bước 6–7: Phỏng vấn + ghi kết quả
* Bước 8: Gửi offer, ứng viên xác nhận
* Bước 9–10: Onboarding + bàn giao cho TBP


Vị trí đang tuyển: TVTS, R&D, Giáo viên tiếng Trung, Content Marketing, Quản lý học viên, Digital ADS.


1.2.8 Báo cáo nhân sự (Sheets 2.7, 2.8)
Dashboard thời gian thực tháng 5/2026:
Tổng
	Kinh Doanh
	Marketing
	R&D/SP
	Vận Hành
	Nhân sự
	53
	20
	14
	13
	4
	2
	CT: 30
	CT: 10
	CT: 10
	CT: 7
	CT: 2
	CT: 1
	TV: 23
	TV: 10
	TV: 4
	TV: 6
	TV: 2
	TV: 1
	

1.3. Công cụ & Điểm yếu hiện tại
Học Bá đang sử dụng các công cụ sau:
* Lark Suite: chấm công, approval đơn nghỉ phép / làm online / quên chấm công
* Anycross: sync dữ liệu chấm công từ Lark → Google Sheet
* Excel / Google Sheet: toàn bộ hồ sơ nhân sự, lương, bảng công, hợp đồng, tuyển dụng
* Gmail: gửi phiếu lương, mail mời nhận việc, chào mừng


Điểm yếu cần cải thiện:
* Dữ liệu phân mảnh: Mỗi module là một file/sheet riêng, không liên thông tự động
* Tính lương thủ công: Bảng công phải tổng hợp bằng tay rồi mới tính lương, dễ sai sót
* Không có employee self-service: Nhân viên muốn xem phiếu lương / số dư phép phải hỏi HR
* Không có lịch sử thay đổi tự động: Sheet 2.4 snapshot lộ trình thăng tiến được cập nhật thủ công
* Tuyển dụng rải rác: CV/PV theo dõi qua sheet, không có pipeline trực quan
* COM phức tạp: Tính COM theo level TVTS cần nhiều công thức Excel, khó kiểm soát
________________


PHẦN 2: ODOO 19 – CÁC MODULE HR
Odoo 19 cung cấp 9 ứng dụng HR tích hợp hoàn toàn với nhau, dữ liệu liên thông tự động. Đây là nền tảng đáp ứng đầy đủ nhu cầu hiện tại của Học Bá và có khả năng mở rộng theo quy mô phát triển.
2.1. Danh sách ứng dụng HR trong Odoo 19
Module
	Chức năng chính
	Tính năng nổi bật Odoo 19
	Employees
	Hồ sơ nhân viên, phòng ban, hợp đồng, onboarding/offboarding
	Certifications, equipment tracking, customizable programs
	Payroll
	Tính lương, payslip cá nhân & hàng loạt, salary rules
	Localization VN, AI-assisted rules, salary package configurator
	Attendances
	Chấm công web/mobile/kiosk/biometric, OT tracking
	Auto check-out, offsite detection, work entries tự động
	Time Off
	Nghỉ phép, accrual plans, carry-forward, mandatory days
	Overlap support, cleaner dashboard, flexible leave types
	Recruitment
	Kanban pipeline, CV/PV tracking, offer, onboarding
	Talent Pools (AI), email automation, interview forms
	Appraisals
	Đánh giá định kỳ, self-assessment, skills tracking
	Skills Evolution report, goal management, peer review
	Fleet
	Quản lý xe công ty, bảo hiểm, chi phí
	Mobility card, contract alerts
	Frontdesk
	Check-in khách, kiosk lễ tân, thông báo nhân viên
	Drinks management, visitor flow tracking
	eLearning/Training
	Khoá học nội bộ, chứng chỉ, theo dõi tiến độ
	Certifications linked to employee profile
	

2.2. Luồng dữ liệu tích hợp
Điểm mạnh cốt lõi của Odoo là các module liên thông tự động – loại bỏ hoàn toàn việc nhập dữ liệu trùng lặp:
Attendance + Time Off → Work Entries → Payslip → Bank TransferToàn bộ luồng từ chấm công → nghỉ phép → tổng hợp công → tính lương → chuyển khoản diễn ra tự động, không cần nhập tay vào bất kỳ bước trung gian nào.
	

Chi tiết từng bước:
* Nhân viên check-in/check-out → hr.attendance được tạo tự động
* Nhân viên xin nghỉ phép → hr.leave, sau khi approve tự động tạo work entry loại 'Time Off'
* Cuối tháng: HR chạy Generate Work Entries → hệ thống tổng hợp từ attendance + leave thành hr.work.entry
* Tạo payslip → hệ thống kéo work entries, tính lương theo salary rules, ra THỰC LÃNH
* Confirm payslip → tạo journal entry kế toán + chuyển khoản ngân hàng


2.3. Tính năng mới đáng chú ý trong Odoo 19
* AI Document Sorting: Tự động phân loại hồ sơ nhân sự (hợp đồng, CCCD, onboarding forms)
* AI Interview Assistant: Ghi âm buổi phỏng vấn → tự động transcript + tóm tắt + gắn task
* Talent Pools: Nhóm ứng viên tiềm năng theo skills, tự động gợi ý khi có vị trí phù hợp
* Employee Self-Service Portal: Nhân viên tự xem phiếu lương, số dư phép, bảng công, đổi thông tin cá nhân
* Split salary: Chia lương vào nhiều tài khoản ngân hàng khác nhau
* Salary Package Configurator: Cấu hình gói lương linh hoạt khi đàm phán với ứng viên
________________


PHẦN 3: PHÂN TÍCH DATA MODEL – MAP EXCEL → ODOO
Phần này phân tích từng sheet Excel của Học Bá và xác định object Odoo tương ứng, mức độ khớp và các điểm cần xử lý thêm.
3.1. Bảng mapping tổng quan
Sheet Excel
	Rows
	Trường chính
	Odoo Model
	Odoo Fields
	Mức khớp
	NHÂN SỰ & TỔ CHỨC
	2.1 Quản lý nhân sự
	168
	Mã HB.xx, CCCD, ngày sinh, phòng ban, chức danh, trạng thái, ngân hàng
	hr.employee
	name, identification_id, department_id, job_id, employee_type, active, bank_account_id
	✓ Khớp
	3.2 Department_Info
	6
	department_id, name, leader, parent
	hr.department
	name, manager_id, parent_id
	✓ Khớp
	8.4 Lookup chức danh
	68
	Vị trí, phòng ban, chức vụ
	hr.job
	name, department_id, expected_employees
	✓ Khớp
	HỢP ĐỒNG & LƯƠNG
	2.5 Theo dõi HĐ
	39
	Loại HĐ, ngày ký, ngày hết hạn, tái ký
	hr.contract
	contract_type_id, date_start, date_end, trial_date_end, state
	✓ Khớp
	2.2 Thông tin lương
	158
	Lương cơ bản, 8 loại phụ cấp, ngân hàng
	hr.contract
	wage + salary rules cho từng phụ cấp
	✓ Khớp
	2.3 Thuế, bảo hiểm
	30
	MST, số sổ BHXH, thẻ BHYT, NPT, mức đóng BH
	hr.employee + l10n_vn
	ssnid, private_info, VN localization fields
	✓ Khớp
	8.2 Lookup KPI
	11
	Level 0–10, lương, %COM, KPI target
	hr.salary.rule
	Python expression rules – cần viết thủ công
	⚠ Custom
	2.4 Lộ trình thăng tiến
	370
	Snapshot lương hàng tháng theo từng nhân viên
	hr.contract (versioning)
	Archive contract cũ, tạo contract mới mỗi lần đổi lương
	⚠ Partial
	5.1 Tính lương offline
	266
	Doanh thu, COM, công, BH, thuế, THỰC LÃNH
	hr.payslip
	payslip.line_ids, worked_days_line_ids, net_wage
	✓ Khớp
	CHẤM CÔNG & NGHỈ PHÉP
	3.3 Attendance_Results
	10,076
	Check-in/out time, offsite, phút trễ
	hr.attendance
	check_in, check_out, worked_hours (auto)
	✓ Khớp
	3.4 Bảng công tháng
	415
	Công chuẩn, thực tế, OT, nghỉ lễ, thai sản
	hr.work.entry
	Tự động từ attendance+leave, không cần sheet riêng
	✓ Tốt hơn
	3.6 Bảng công OT
	68
	Giờ OT 100%/150%/300%
	hr.work.entry.type
	OT work entry types với hệ số tính lương
	✓ Khớp
	3.5 Theo dõi ngày phép
	26
	Phép năm, tồn, đã dùng, còn lại
	hr.leave.allocation
	number_of_days, accrual_plan_id, carry_forward
	✓ Tốt hơn
	4.1 Xin nghỉ phép
	347
	Loại nghỉ, ngày, lý do, trạng thái duyệt
	hr.leave
	holiday_status_id, date_from/to, state, duration
	✓ Khớp
	4.2 Làm online
	279
	Ngày làm remote, lý do, người duyệt
	hr.leave (Remote type)
	Cần tạo Time Off Type = 'Remote/WFH' hoặc dùng work location
	⚠ Config
	4.3 Quên chấm công
	247
	Ngày quên, thời gian bổ sung, lý do
	hr.attendance
	Chỉnh sửa manual attendance record
	✓ Khớp
	TUYỂN DỤNG
	7.4 Danh sách CV
	160
	Ứng viên, SĐT, email, vị trí, CV link
	hr.applicant
	partner_name, email_from, job_id, stage_id
	✓ Tốt hơn
	7.5 Danh sách PV
	104
	Ngày PV, người PV, kết quả, offer
	hr.applicant
	interviewer_ids, priority, kanban_state
	✓ Tốt hơn
	7.6 Pass PV → Nhận việc
	59
	Ứng viên pass, ngày nhận việc
	hr.applicant → hr.employee
	'Create Employee' button → tự tạo hr.employee
	✓ Tốt hơn
	

3.2. Các điểm cần custom/cấu hình đặc thù
3 điểm sau không có sẵn trong Odoo tiêu chuẩn, cần được xây dựng hoặc cấu hình thêm trước khi go-live.
	

3.2.1 Bảng KPI Level 0–10 (Phức tạp nhất)
Đây là cấu trúc đặc thù của Học Bá, không có analog trong Odoo tiêu chuẩn. Phương án đề xuất:
* Tạo 11 salary structures (mỗi level là 1 structure) với wage và KPI threshold khác nhau
* Viết salary rule 'COM' bằng Python expression: result = contract.revenue * contract.com_rate, trong đó com_rate được nhập từ input line tháng đó
* Nhân viên TVTS cần có trường custom: current_level (0–10) trên hr.employee hoặc hr.contract
* Mỗi tháng HR nhập doanh thu thực tế vào payslip input → system tính COM tự động


3.2.2 Làm online / Remote Work
Sheet 4.2 ghi nhận 279 yêu cầu làm online. Phương án trong Odoo:
* Tạo Time Off type mới: 'Làm online / WFH' với loại 'No Validation' (không trừ phép)
* Hoặc sử dụng Work Location module (có sẵn trong Odoo 17+): nhân viên cập nhật work location = Home
* Approval flow tương tự: nhân viên submit → Leader duyệt → HCNS confirm


3.2.3 Lịch sử lộ trình thăng tiến
Sheet 2.4 chứa 370 dòng snapshot lương hàng tháng. Odoo lưu lịch sử qua contract versioning:
* Mỗi lần thay đổi lương/chức danh → archive contract cũ, tạo contract mới với effective date
* Odoo lưu toàn bộ contract history của một nhân viên → có thể xem timeline
* Cần tạo báo cáo custom 'Salary History' nếu muốn xem dạng timeline đẹp như sheet 2.4
________________


PHẦN 4: KẾ HOẠCH TRIỂN KHAI
Dựa trên phân tích data model, đây là lộ trình triển khai Odoo 19 HR được đề xuất cho Học Bá, chia thành 4 giai đoạn trong khoảng 3–4 tháng.
4.1. Tổng quan lộ trình
Giai đoạn
	Tên
	Thời gian
	Nội dung
	Deliverable
	G1
	Nền tảng
	Tháng 1
	Cài đặt Odoo, cấu hình phòng ban, chức danh, nhập dữ liệu nhân sự cơ bản
	HR master data live
	G2
	Chấm công & Nghỉ phép
	Tháng 2
	Cấu hình chấm công, leave types, approval flow, thay thế Lark approval
	Attendance + Time Off live
	G3
	Lương & Payroll
	Tháng 3
	Cấu hình salary rules, BH, thuế, COM level table, chạy payroll tháng đầu tiên
	First payslip run
	G4
	Tuyển dụng & Hoàn thiện
	Tháng 4
	Recruitment pipeline, onboarding flow, self-service portal, training
	Full HR live
	

4.2. Chi tiết từng giai đoạn
Giai đoạn 1: Cấu hình nền tảng
* Cài đặt Odoo 19 + cài localization Việt Nam (l10n_vn)
* Cấu hình 6 phòng ban trong hr.department với manager
* Tạo 68 chức danh trong hr.job theo bảng 8.4
* Import toàn bộ 53 nhân sự đang hoạt động vào hr.employee
* Khai báo thông tin bảo hiểm, CCCD vào private info tab
* Cấu hình tài khoản ngân hàng cho từng nhân viên
* Tạo hr.contract cho tất cả nhân sự offline đang làm


Giai đoạn 2: Chấm công & Nghỉ phép
* Cấu hình working schedule (ca làm việc 8h–19h, 5 ngày/tuần)
* Thiết lập Attendance kiosk tại văn phòng hoặc dùng mobile app
* Tạo các loại Time Off: Nghỉ phép năm (accrual), Nghỉ ốm, Nghỉ thai sản, Về sớm/Đi trễ
* Tạo Time Off type 'Remote/WFH' cho luồng xin làm online
* Cấu hình approval chain: Leader → HR Manager
* Cấu hình work entry types cho OT (100%, 150%, 300%)
* Import lịch sử nghỉ phép tồn đọng vào hr.leave.allocation
* Training nhân viên sử dụng self-service portal


Giai đoạn 3: Payroll
* Cấu hình salary structure: Offline Staff, Online/CTV
* Viết salary rules cho từng khoản: lương thời gian, PC xăng, PC gửi xe, PC chức vụ, PC thâm niên, hỗ trợ ĐT/ăn ca/trang phục
* Viết salary rules BHXH (17.5% CT + 8% NV), BHYT (3% CT + 1.5% NV), BHTN (1% CT + 1% NV)
* Viết salary rules Thuế TNCN với giảm trừ bản thân 11M + NPT 4.4M/người
* Custom: Tạo COM salary rule theo doanh thu input, có lookup bảng level 0–10
* Chạy payroll thử tháng đầu tiên song song với Excel để kiểm tra
* Sau khi verify → cutover hoàn toàn sang Odoo


Giai đoạn 4: Tuyển dụng & Hoàn thiện
* Cấu hình recruitment pipeline: Job positions + stages (Mới → Lọc CV → PV → Offer → Nhận việc)
* Tạo email templates tương ứng với 7.7 (mời PV, kết quả PV, mời nhận việc, chào mừng)
* Thiết lập Talent Pools theo kỹ năng (TVTS, Giáo viên tiếng Trung, Content Marketing)
* Cấu hình onboarding checklist trong Employees app
* Setup Employee self-service: phiếu lương, số dư phép, bảng công
* Training toàn bộ HCNS và trưởng phòng sử dụng hệ thống


4.3. Rủi ro & Giảm thiểu
Rủi ro
	Mức độ
	Giảm thiểu
	COM calculation sai
	🔴 Cao
	Chạy song song 2–3 tháng, so sánh từng dòng với Excel cũ
	Nhân viên không quen hệ thống mới
	🟡 TB
	Training 2 buổi + tài liệu hướng dẫn + period Q&A 1 tháng sau go-live
	Dữ liệu lịch sử bị mất
	🟡 TB
	Giữ file Excel archive, không cần migrate dữ liệu cũ hơn 12 tháng vào Odoo
	Localization VN chưa đầy đủ
	🟡 TB
	Kiểm tra l10n_vn trước khi deploy, backup plan: tự viết salary rules thuế thủ công
	Approval flow phức tạp hơn Lark
	🟢 Thấp
	Odoo approval flow đơn giản hơn Lark, training 30 phút là đủ
	________________


PHỤ LỤC: CHECKLIST CHUẨN BỊ DỮ LIỆU
Danh sách dữ liệu cần chuẩn bị trước khi import vào Odoo, ưu tiên theo thứ tự giai đoạn:


A. Dữ liệu bắt buộc (Giai đoạn 1)
* File danh sách nhân viên: Mã HB.xx, họ tên, ngày sinh, CCCD, SĐT, email, phòng ban, chức danh, ngày vào làm, loại hình thức, trạng thái
* File danh sách phòng ban: ID, tên, trưởng phòng, phòng ban cha
* File danh sách chức danh: tên vị trí, phòng ban
* File hợp đồng: nhân viên, loại HĐ, ngày ký, ngày hết hạn, lương cơ bản, mức đóng BHXH
* File tài khoản ngân hàng: nhân viên, số TK, tên ngân hàng, chi nhánh
* File bảo hiểm: nhân viên, số sổ BHXH, số thẻ BHYT, nơi đăng ký KCB, số NPT


B. Dữ liệu cần chuẩn bị (Giai đoạn 2)
* Số dư nghỉ phép còn lại của từng nhân viên (để import vào hr.leave.allocation)
* Lịch sử nghỉ phép 3–6 tháng gần nhất (nếu cần kiểm tra)


C. Dữ liệu cần xây dựng (Giai đoạn 3)
* Salary structure document: mô tả từng khoản thu/khấu trừ, công thức tính
* Bảng level KPI 0–10 dạng JSON/CSV cho việc viết salary rule
* Danh sách salary inputs cần nhập thủ công hàng tháng: doanh thu từng TVTS, thưởng bất thường


Tài liệu được tạo tự động bởi Claude (Anthropic) – Tháng 5/2026  |  Học Bá Education


format Beta
 
TÀI LIỆU KHẢO SÁT NGHIỆP VỤ
&
THIẾT KẾ KIẾN TRÚC ĐÍCH TRIỂN KHAI ODOO 19 ERP
 
 
Học Bá Education
Dự án
	Số hóa và Chuyển đổi Hệ thống Quản trị Nhân sự (HRM) — Học Bá Education
	Tác giả
	Senior ERP Solution Architect  |  Senior Data Analyst  |  Odoo Technical Consultant
	Phiên bản
	v1.0 — Tài liệu Thiết kế Kiến trúc Đích
	Nền tảng
	Odoo 19 Enterprise
	

 
MỤC LỤC
 
 
 


 
PHẦN 1: PHÂN TÍCH CHI TIẾT THEO TỪNG PHÂN HỆ VÀ THỰC THỂ DỮ LIỆU
 
 


 
  MODULE 1    EMPLOYEES & ORGANIZATIONAL MANAGEMENT (HỒ SƠ NHÂN SỰ & CƠ CẤU TỔ CHỨC)
 
1. Business Analysis — Phân tích Nghiệp vụ
 
Học Bá Education vận hành một mạng lưới nhân sự phức tạp, phân tầng sâu sắc giữa các khối chức năng. Vòng đời nhân sự tuân thủ nghiêm ngặt theo chuỗi trạng thái:
Ứng viên (Applicant) → Thử việc (Probation) → Chính thức (Regular) → Nghỉ việc (Terminated)
 
Hệ thống quản lý 4 nhóm nhân sự cốt lõi:
•     Khối Văn phòng & Vận hành (Backoffice): Làm việc cố định, thụ hưởng phụ cấp hành chính, đóng BHXH đầy đủ.
•     Khối Giảng viên (Teachers): Tính thù lao theo số buổi dạy (Session-based rate) và cấp độ chuyên môn (Level HSK/TOCFL).
•     Khối Trợ giảng (Tutors/Mentors): Chấm bài, hỗ trợ học viên, nhận thù lao khoán.
•     Khối Cộng tác viên (CTV Part-time): Đăng ký ca làm việc linh hoạt, hưởng lương cứng theo giờ và hoa hồng bậc thang.
 
Sơ đồ tổ chức phân chia theo cấu trúc:
Tổng công ty (BOD) → Chi nhánh (Hà Nội, Trực tuyến) → Các Phòng ban chuyên biệt (Kinh doanh, Marketing, Sản phẩm, Vận hành, Kế toán)
 
Thách thức kiến trúc lớn nhất: Xử lý kịch bản nhân sự đa vai trò (Multi-role) — một nhân sự có thể vừa là Chuyên viên Giáo vụ (lương thời gian) vừa tham gia dạy lớp VIP (lương theo buổi). Hệ thống đích bắt buộc quản lý tập trung mã định danh cá nhân nhưng phân tách minh bạch các vai trò chức danh.
 
2. Source Excel Analysis — Phân tích Bảng tính Nguồn
 
•     Tệp nguồn: Quản lý nhân sự.csv, Employee_Info.csv, Department_Info.csv, Theo dõi ký hợp đồng.csv
•     Cấu trúc: Mã nhân sự định dạng HB.xxx, thông tin định danh (CCCD, SĐT, Email), thông tin công tác, danh mục tài sản phần cứng.
 
Đánh giá chất lượng dữ liệu:
◦     Rủi ro trùng lặp (Duplicate Risk) — Cao: Trùng tên do nhân viên tự nhập, tên không dấu trong bảng Employee_Info lệch chuẩn.
◦     Dữ liệu trống (Missing Values): Ngày chính thức, ngày nghỉ việc trống diện rộng ở khối CTV. MST TNCN và sổ BHXH trống ~90% khối Online.
◦     Không nhất quán (Data Inconsistency): Cột "Hình thức" sử dụng chuỗi lẫn lộn ("Văn phòng", "Offline", "Online"). Tên phòng ban chứa ký tự Emoji (Châu Anh 💰, Lead MKT ...).
 
3. Data Model Design — Thiết kế Mô hình Dữ liệu Đích
 
Thực thể chính:
•     hr.employee — Hồ sơ nhân viên
•     hr.department — Phòng ban
•     hr.job — Vị trí chức danh
•     hr.contract — Hợp đồng lao động
 
Mối quan hệ dữ liệu:
•     hr.employee → hr.department: Many2one qua trường department_id.
•     hr.department → hr.department: Tự tham chiếu Many2one (parent_id) để dựng cây phân cấp mẹ-con.
•     hr.employee → hr.contract: One2many (contract_ids) — tại một thời điểm chỉ một hợp đồng ở trạng thái "open".
 
Trường tính toán (Computed Fields):
•     x_tenure_months: Số tháng làm việc thực tế từ first_contract_date đến ngày hiện tại hoặc departure_date.
•     x_hardware_count: Tổng số thiết bị phần cứng đang bàn giao, đếm từ quan hệ với module Tài sản.
 
Ràng buộc (Constraints):
•     Unique SQL cứng: barcode (mã HB.xxx), identification_id (CCCD), work_email. Chặn lưu nếu trùng lặp.
 
4. Odoo Model Mapping — Bảng Ánh xạ Dữ liệu Cấp Trường
 
 
Trường Excel
	Ý nghĩa NV
	Mô hình Odoo
	Trường Odoo
	Kiểu DL
	Bắt buộc
	Quy tắc chuyển đổi
	Mã nhân sự
	Mã định danh duy nhất
	hr.employee
	barcode
	Char
	YES
	Giữ định dạng HB.xxx, cắt khoảng trắng.
	Họ và tên
	Tên đầy đủ nhân viên
	hr.employee
	name
	Char
	YES
	Chuẩn hóa viết hoa chữ cái đầu.
	Tài khoản Lark
	Định danh người dùng Lark
	hr.employee
	x_lark_user_id
	Char
	NO
	Khóa liên kết đồng bộ Webhook.
	Hình thức
	Phân loại địa điểm làm việc
	hr.employee
	x_work_mode
	Selection
	YES
	"Offline"/"Văn phòng" → offline; "Online" → online.
	Tình trạng
	Trạng thái lao động
	hr.employee
	x_hr_status
	Selection
	YES
	"Chính thức" → regular; "Thử việc" → probation.
	Phòng Ban
	Phòng ban công tác
	hr.employee
	department_id
	Many2one
	YES
	Tìm kiếm ID trong bảng hr.department theo tên.
	Chức danh
	Vị trí công việc
	hr.employee
	job_id
	Many2one
	YES
	Tìm kiếm ID trong bảng hr.job.
	Số CCCD
	Mã định danh cá nhân
	hr.employee
	identification_id
	Char
	NO
	Loại bỏ khoảng trắng và dấu chấm.
	Số điện thoại
	Điện thoại di động
	hr.employee
	mobile_phone
	Char
	YES
	Chuẩn hóa định dạng quốc tế (+84).
	Email công ty
	Hòm thư công vụ
	hr.employee
	work_email
	Char
	NO
	Chuyển về chữ thường, kiểm tra Regex Email.
	Trình độ tiếng Trung
	Năng lực ngoại ngữ
	hr.employee
	x_chinese_level
	Char
	NO
	Lưu chuỗi văn bản phục vụ phân phối giảng dạy.
	 
5. Customization Requirements — Yêu cầu Tùy biến Phát triển
 
Custom Fields:
•     Thêm nhóm trường quản lý thiết bị phần cứng cấp phát trực tiếp trên Form hồ sơ nhân sự (liên kết sang hr.equipment).
•     Thêm trường x_teaching_level phục vụ riêng Khối Giảng viên.
 
Custom Workflows:
•     Khi hr.contract thử việc chuyển trạng thái "expired", hệ thống tự động gửi cảnh báo yêu cầu kích hoạt quy trình đánh giá thử việc trước 5 ngày.
 
Security Groups:
•     Group Employee: Chỉ được xem hồ sơ cá nhân.
•     Group Department Manager (TBP): Xem toàn bộ nhân sự thuộc phòng ban quản lý theo phân cấp.
•     Group HR Officer / C&B: Toàn quyền tạo, sửa, lưu trữ dữ liệu nhân sự toàn hệ thống.
 
6. Data Cleaning Requirements — Chuẩn hóa & Làm sạch
 
Quy tắc xử lý trùng lặp:
Nếu phát hiện 2 bản ghi trùng Số CCCD hoặc SĐT, giữ lại bản ghi có cập nhật gần nhất tại tệp "2.4 Lộ trình thăng tiến". Bản ghi còn lại đưa vào log cảnh báo cho HR xử lý thủ công.
 
Chuẩn hóa giá trị:
•     Loại bỏ Emoji và tiền tố chức vụ thừa trong cột họ tên (Lead MKT -, Châu Anh 💰 → Phan Hoàng Châu Anh).
•     Ép toàn bộ định dạng ngày tháng về chuẩn ISO YYYY-MM-DD.
 
7. Import Strategy — Chiến lược Nạp Dữ liệu
 
Trình tự nạp dữ liệu:
•     Bước 1: res.company — Cấu hình Chi nhánh hệ thống
•     Bước 2: hr.department — Khởi tạo phòng ban gốc, sau đó import quan hệ mẹ-con
•     Bước 3: hr.job — Danh mục vị trí từ tệp 8.4 Lookup chức danh
•     Bước 4: hr.employee — Hồ sơ nhân sự cốt lõi
•     Bước 5: hr.contract — Hợp đồng lao động phụ thuộc nhân sự
 
Cơ chế External IDs:
•     Phòng ban: __export__.hr_department_{dept_id} (VD: __export__.hr_department_marketing_hocba)
•     Nhân sự: __export__.hr_employee_{barcode} (VD: __export__.hr_employee_HB_01)
 
8. Risks & Edge Cases — Rủi ro & Kịch bản Đặc biệt
 
Nhân sự nghỉ việc quay lại làm CTV:
Giải pháp: Không tạo bản ghi hr.employee mới. Kích hoạt lại (Unarchive) hồ sơ cũ và tạo dòng hợp đồng hr.contract mới với loại hình công tác cập nhật.


 
  MODULE 2    ATTENDANCE & TIME TRACKING (QUẢN LÝ CHẤM CÔNG & CA LÀM VIỆC)
 
1. Business Analysis — Phân tích Nghiệp vụ
 
Học Bá áp dụng cơ chế chấm công đa phương thức bám sát cấu trúc 3 khối nhân sự:
•     Khối Văn phòng: Chấm công 2 chiều (Check-in/Check-out) tại tọa độ GPS văn phòng. Ca chuẩn 8h/ngày, cho phép đi muộn tối đa 15 phút.
•     Khối CTV: Phải đăng ký ca làm việc tuần trên hệ thống. Dữ liệu chấm công thực tế được đối soát tự động với ca đăng ký.
•     Khối Giảng viên/Trợ giảng: Chấm công dựa trên tiến độ hoàn thành lớp học (Session-based). Khung giờ dạy quản lý từ phân hệ Đào tạo.
 
Quy trình xử lý 3 loại đơn từ phê duyệt: Đơn xin nghỉ phép/đi muộn, Đề xuất làm việc Online, và Giải trình quên chấm công. Khi đơn giải trình được phê duyệt, hệ thống tự động bổ sung dữ liệu chấm công thô để bảo toàn quỹ công cuối tháng.
 
2. Source Excel Analysis — Phân tích Bảng tính Nguồn
 
•     Tệp nguồn: Attendance_Results.csv, Bảng công tháng.csv, Đề xuất làm online.csv, Phiếu đề xuất quên chấm công.csv
•     Cấu trúc: Mốc thời gian chi tiết (Check in/out time), trạng thái điểm quét (Is offsite), số phút đi trễ toán học, mã định danh dòng Result id.
 
Đánh giá chất lượng dữ liệu:
◦     Lỗi múi giờ (Timezone Mismatch) — Nghiêm trọng: Lark đẩy chuỗi thời gian UTC+7 cục bộ, Odoo yêu cầu lưu trữ UTC chuẩn quốc tế.
◦     Bản ghi mồ côi (Orphan Records): Nhiều dòng chấm công có check_out trống do nhân viên quên quét thẻ khi về, dẫn đến số giờ âm trên Excel cũ.
 
3. Data Model Design — Thiết kế Mô hình Dữ liệu Đích
 
Thực thể chính:
•     hr.attendance — Bản ghi chấm công chi tiết
•     resource.calendar — Khung lịch làm việc tổng thể
•     resource.calendar.attendance — Chi tiết ca làm việc trong tuần
 
Mối quan hệ & Trường tính toán:
•     hr.attendance → hr.employee: Many2one qua employee_id. Mỗi bản ghi chấm công bắt buộc định danh chính xác nhân sự.
•     x_late_minutes: Thời gian Check-in thực tế trừ thời gian mở ca tiêu chuẩn. Nếu ≤ 0 thì ghi nhận bằng 0.
 
Ràng buộc:
•     check_out > check_in — Bắt buộc trên cùng một dòng bản ghi.
 
4. Odoo Model Mapping — Bảng Ánh xạ Dữ liệu Cấp Trường
 
 
Trường Excel
	Ý nghĩa NV
	Mô hình Odoo
	Trường Odoo
	Kiểu DL
	Bắt buộc
	Quy tắc chuyển đổi
	Result id
	Mã bản ghi chấm công gốc
	hr.attendance
	x_lark_result_id
	Char
	YES
	Unique Constraint — chặn trùng khi chạy ETL.
	Mã nhân viên
	Nhân sự thực hiện quét công
	hr.attendance
	employee_id
	Many2one
	YES
	Đối soát mã HB.xxx → ID nội bộ hr.employee.
	Check in time
	Thời gian vào ca thực tế
	hr.attendance
	check_in
	Datetime
	YES
	Chuyển đổi UTC+7 → UTC quốc tế.
	Check out time
	Thời gian ra ca thực tế
	hr.attendance
	check_out
	Datetime
	NO
	Cho phép Null trong ngày, ép giờ kết thúc ca nếu quên.
	Is offsite
	Cờ báo chấm công sai vị trí
	hr.attendance
	x_is_offsite
	Boolean
	YES
	"true"/"false" → True/False kiểu logic.
	Số phút đi trễ
	Thời gian đi muộn tính bằng phút
	hr.attendance
	x_late_minutes_raw
	Integer
	YES
	Ép kiểu chuỗi số nguyên từ Excel → Integer.
	 
5. Customization Requirements
 
Custom Models:
•     Khởi tạo mô hình ctv.shift.register để lưu lịch đăng ký ca tuần khối CTV phục vụ đối soát chấm công chéo.
 
Automation & Custom Workflows:
•     Override phương thức tạo bản ghi chấm công: khi x_is_offsite = True, tự động sinh Activity cảnh báo Urgent gửi tới Trưởng bộ phận HR.
 
Cron Jobs:
•     Scheduled Action chạy lúc 23:00 hàng ngày: quét bản ghi chấm công thiếu check_out, đối chiếu đơn giải trình — nếu không có đơn duyệt thì điền giờ kết thúc ca mặc định và đánh cờ lỗi.
 
6. Data Cleaning Requirements
 
•     Xử lý trùng lặp Check-in: Loại bỏ bản ghi check-in trùng trong biên độ 5 phút của cùng nhân sự. Chỉ giữ lần quét thành công đầu tiên trong ngày.
•     Chuẩn hóa dữ liệu: Điền giá trị công chuẩn 1.0 hoặc 0.5 dựa trên tổng thời gian lưu trú thực tế giữa hai mốc check-in/out.
 
7. Import Strategy
 
Nạp toàn bộ resource.calendar trước, sau đó import chấm công lịch sử theo từng tháng để tránh quá tải bộ nhớ đệm Postgres. Bắt buộc hoàn tất import hr.employee trước khi nạp chấm công (barcode làm khóa ngoại).
 
8. Risks & Edge Cases
 
Xung đột ca làm việc xuyên đêm (22:00 → 06:00 hôm sau):
Giải pháp: Cấu hình check_out cho phép ghi nhận thời gian ngày T+1. Tùy biến tầng Work Entry để phân bổ chính xác ngày công vào tháng phát sinh ca làm việc.


 
  MODULE 3    PAYROLL & COMPENSATION (QUẢN TRỊ BẢNG LƯƠNG & PHÚC LỢI)
 
1. Business Analysis — Phân tích Nghiệp vụ
 
Hệ thống tính lương của Học Bá áp dụng 3 thuật toán cấu trúc lương hoàn toàn biệt lập:
•     Khối Văn phòng: Lương theo ngày công thực tế + phụ cấp cố định (xăng, ăn ca, điện thoại) - khấu trừ BHXH (10.5%) - thuế TNCN lũy tiến.
•     Khối Giảng viên: Tổng giờ dạy thực tế × Đơn giá theo Level chức danh. Không phát sinh khấu trừ BHXH.
•     Khối Kinh doanh (Sale/CTV): Hoa hồng bậc thang động theo bảng ma trận 8.2 Lookup KPI. Tỷ lệ % COM dao động 1.0% – 4.4% tùy doanh số tuyển sinh thực thu.
 
2. Source Excel Analysis — Phân tích Bảng tính Nguồn
 
•     Tệp nguồn: Tính lương offline.csv, Tính lương online.csv, Lưu trữ lương offline.csv, Lookup KPI.csv
•     Cấu trúc: Ma trận kế toán lương gồm: Lương hợp đồng, Doanh thu, Tỷ lệ hoa hồng, Phụ cấp phân rã, Tiền phạt đi muộn, Thuế TNCN, Tiền thực lĩnh, Tài khoản ngân hàng chuyển khoản.
 
Đánh giá chất lượng dữ liệu:
◦     Vi phạm chuẩn hóa DB (Denormalization) — Nghiêm trọng: Số tài khoản và tên ngân hàng bị sao chép lặp lại trên từng dòng lương tháng.
◦     Lỗi công thức (#ERROR!, #VALUE!): Xuất hiện tại các cột Thuế TNCN và Tổng thu nhập do tham chiếu dòng trống/sai kiểu. Ký hiệu tiền tệ dạng chuỗi ("₫7,300,000.0") khiến công thức tự động không đọc được.
 
3. Data Model Design
 
Thực thể chính:
•     hr.payslip — Phiếu lương nhân sự
•     hr.salary.rule — Quy tắc tính lương
•     hr.payroll.structure — Cấu trúc lương tổng thể
•     hr.payslip.input — Tham số biến động đầu vào phiếu lương
 
Tham số đầu vào (Payslip Inputs):
•     REVENUE: Tổng doanh số chốt đơn tuyển sinh tháng.
•     BONUS_LE: Thưởng ngày lễ.
•     PENALTY_LATE: Tiền phạt đi muộn.
 
Ràng buộc:
•     Không cho phép tạo 2 phiếu lương cùng kỳ tính lương (trùng tháng/năm) cho một nhân sự.
 
4. Odoo Model Mapping — Bảng Ánh xạ Dữ liệu Cấp Trường
 
 
Trường Excel
	Ý nghĩa NV
	Mô hình Odoo
	Trường Odoo
	Kiểu DL
	Bắt buộc
	Quy tắc chuyển đổi
	Mã nhân sự
	Nhân sự nhận lương
	hr.payslip
	employee_id
	Many2one
	YES
	Đối soát mã HB.xxx → ID hr.employee.
	Tháng / Năm
	Kỳ tính lương tháng
	hr.payslip
	date_from / date_to
	Date
	YES
	Convert "Tháng 5" + "2026" → 2026-05-01 đến 2026-05-31.
	Lương HĐ
	Lương cứng gốc đóng bảo hiểm
	hr.contract
	wage
	Monetary
	YES
	Làm sạch ký hiệu "₫", dấu phẩy, ép về Float.
	Doanh thu
	Doanh số sale chốt trong tháng
	hr.payslip.input
	amount (REVENUE)
	Float
	NO
	Đẩy vào Input Line để tính hoa hồng bậc thang.
	Thưởng khác
	Các khoản khen thưởng đột xuất
	hr.payslip.input
	amount (BONUS)
	Float
	NO
	Nhập phát sinh trực tiếp vào phiếu lương.
	Thuế TNCN
	Khấu trừ thuế thu nhập cá nhân
	hr.payslip.line
	total (PIT)
	Float
	YES
	Trường tính toán tự động bằng Python Rule lũy tiến.
	THỰC LÃNH
	Số tiền chuyển khoản cuối cùng
	hr.payslip.line
	total (NET)
	Float
	YES
	Kết quả: tổng thu nhập − tổng khấu trừ.
	 
5. Customization Requirements — Python Salary Rules
 
Custom Python Salary Rules:
•     Quy tắc tính Thuế TNCN lũy tiến 7 bậc chuẩn luật Việt Nam bằng Python Rule.
•     Quy tắc tính hoa hồng bậc thang động cho khối Kinh doanh:
 
# Python Rule: Tính Hoa hồng bậc thang dựa trên Doanh thu đầu vào
revenue = inputs.REVENUE.amount if hasattr(inputs, "REVENUE") else 0.0
commission_rate = 0.0
 
if   revenue >= 340_000_000: commission_rate = 0.044
elif revenue >= 270_000_000: commission_rate = 0.040
elif revenue >= 210_000_000: commission_rate = 0.035
elif revenue >= 160_000_000: commission_rate = 0.030
elif revenue >= 120_000_000: commission_rate = 0.025
elif revenue >=  90_000_000: commission_rate = 0.015
elif revenue >=  50_000_000: commission_rate = 0.010
 
result = revenue * commission_rate
 
Automation Workflows:
•     Khi Trưởng phòng HR xác nhận đóng Bảng công (hr.work.entry chuyển trạng thái duyệt cuối), hệ thống tự động tạo hàng loạt Phiếu lương (Batch Generating Payslips) cho toàn bộ nhân viên đang hoạt động và kéo số ngày công thực tế vào dòng tính lương thời gian.
 
6. Data Cleaning Requirements
 
•     Trích xuất dữ liệu Số tài khoản và Ngân hàng từ Excel, đưa về lưu trữ duy nhất tại res.partner.bank liên kết với hồ sơ nhân viên.
•     Làm sạch hoàn toàn chuỗi rác trong cột tiền lương, đưa về kiểu số thuần túy.
 
7. Import Strategy
 
Bắt buộc import hr.contract (trạng thái hoạt động) trước để hệ thống lấy làm gốc lương cơ bản. Tiếp theo import hr.payslip.input từng tháng, cuối cùng mới nạp lệnh tính toán tạo dòng lương chi tiết.
 
8. Risks & Edge Cases
 
Điều chỉnh hồi tố (Retroactive Payroll Risk):
VD: Đơn giải trình công tháng 4 được duyệt vào ngày 5 tháng 5 — sau khi bảng lương tháng 4 đã chốt. Odoo tiêu chuẩn chặn sửa bảng lương cũ.
Giải pháp: Tùy biến quy tắc lương tự động tính phần công thiếu và đẩy giá trị bù vào kỳ tháng 5 dưới dạng dòng tính toán độc lập (Mã quy tắc: PAY_RETRO).


 
  MODULE 4    RECRUITMENT & TALENT ACQUISITION (QUẢN TRỊ TUYỂN DỤNG & THU HÚT TÀI NĂNG)
 
1. Business Analysis — Phân tích Nghiệp vụ
 
Học Bá liên tục mở rộng đào tạo, tần suất tuyển dụng Giảng viên tiếng Trung và Tư vấn tuyển sinh diễn ra liên tục. Quy trình bắt đầu từ Phiếu yêu cầu tuyển dụng của Trưởng bộ phận. Đường ống ứng viên (Candidate Pipeline) chuẩn hóa qua 6 giai đoạn Kanban:
[1. Nhận Hồ Sơ] → [2. Lọc CV] → [3. Kiểm Tra Năng Lực / Test Đầu Vào] → [4. Phỏng Vấn] → [5. Đề Xuất Offer] → [6. Nhận Việc / Hired]
 
Đặc thù tuyển dụng giáo viên: bắt buộc qua Vòng 3 — kiểm tra năng lực ngôn ngữ và dạy thử (Demo Teaching). Kết quả điểm ngữ pháp/khẩu ngữ lưu trực tiếp trên thẻ ứng viên làm căn cứ duyệt mức lương Offer.
 
2. Source Excel Analysis
 
•     Tệp nguồn: Quy trình tuyển dụng.csv, Danh sách CV.csv, Danh sách phỏng vấn.csv, Danh sách Pass PV_Nhận việc.csv
 
Đánh giá chất lượng dữ liệu:
◦     Rủi ro trùng lặp ứng viên — Rất cao: Một ứng viên nộp nhiều lần qua nhiều kênh trong 3 tháng, gây nhân bản dữ liệu trên Excel thủ công.
◦     Lỗi liên kết (Broken Links): Cột Link CV lưu đường dẫn cục bộ Lark Drive hoặc liên kết hỏng, không truy cập được từ ngoài.
 
3. Data Model Design
 
Thực thể chính:
•     hr.applicant — Hồ sơ ứng viên chi tiết
•     hr.recruitment.stage — Các giai đoạn đường ống tuyển dụng
•     hr.job — Vị trí công việc cần tuyển dụng
 
Trường tính toán & Ràng buộc:
•     x_conversion_time: Số ngày từ create_date đến khi chuyển sang Nhận việc (date_open).
•     Unique Index hỗn hợp: Kết hợp partner_phone + job_id — chặn 2 thẻ hồ sơ cho 1 ứng viên trong cùng đợt tuyển dụng.
 
4. Odoo Model Mapping — Bảng Ánh xạ Dữ liệu Cấp Trường
 
 
Trường Excel
	Ý nghĩa NV
	Mô hình Odoo
	Trường Odoo
	Kiểu DL
	Bắt buộc
	Quy tắc chuyển đổi
	Họ tên ứng viên
	Tên đầy đủ ứng viên
	hr.applicant
	partner_name
	Char
	YES
	Chuẩn hóa danh từ riêng viết hoa chữ cái đầu.
	SĐT ứng viên
	Điện thoại liên hệ
	hr.applicant
	partner_phone
	Char
	YES
	Khóa kiểm tra trùng lặp hồ sơ.
	Email ứng viên
	Thư điện tử ứng viên
	hr.applicant
	email_from
	Char
	NO
	Kiểm tra định dạng Regex Mail.
	Vị trí ứng tuyển
	Vị trí công việc mong muốn
	hr.applicant
	job_id
	Many2one
	YES
	Tìm kiếm ID tương ứng trong hr.job.
	Link CV
	Tệp tin đính kèm hồ sơ
	hr.applicant
	attachment_ids
	Many2many
	NO
	Download từ link nguồn, nạp vào Odoo Binary Attachment.
	Kết quả PV
	Đánh giá vòng phỏng vấn
	hr.applicant
	stage_id
	Many2one
	YES
	"Pass" → Đề xuất Offer; "Fail" → Lưu trữ thẻ.
	Ngày nhận việc
	Ngày bắt đầu đi làm thực tế
	hr.applicant
	date_open
	Date
	NO
	Căn cứ kích hoạt khởi tạo hồ sơ hr.employee.
	 
5. Customization Requirements
 
Custom Fields trên hr.applicant:
•     x_grammar_score: Điểm bài test ngữ pháp.
•     x_speaking_score: Điểm bài test khẩu ngữ.
•     x_demo_class_rating: Đánh giá buổi dạy thử của hội đồng đào tạo.
 
Automated Actions:
•     Khi ứng viên vào giai đoạn "Phỏng Vấn": tự động gửi thư mời kèm sơ đồ địa chỉ văn phòng.
•     Khi chuyển ứng viên sang "Hired": tự động sinh tài khoản hr.employee mới, kế thừa toàn bộ thông tin định danh cá nhân — không cần nhập lại.
 6. Data Quality & Data Cleaning Requirements (Yêu cầu Chuẩn hóa & Làm sạch)
* Quy trình Gộp Hồ sơ trùng lặp (Deduplication Pipeline): Khi thực hiện chạy script import dữ liệu lịch sử tuyển dụng, nếu phát hiện trùng lặp Số điện thoại, hệ thống tự động gộp dữ liệu (Merge Records), giữ lại thẻ ứng viên có lịch sử phỏng vấn chi tiết nhất và gom toàn bộ các file đính kèm CV cũ vào phần nhật ký Log lưu vết (Chatter) của bản ghi chính duy nhất.
7. Import Strategy (Chiến lược Nạp Dữ liệu)
* Trình tự nạp dữ liệu: Khởi tạo danh mục các giai đoạn Kanban tuyển dụng (hr.recruitment.stage), tiếp theo nạp danh mục vị trí tuyển dụng (hr.job), cuối cùng chạy ETL import toàn bộ danh sách hồ sơ ứng viên lịch sử từ tệp danh sách CV.
* Dependency: Yêu cầu các vị trí công việc phải ở trạng thái hoạt động trên hệ thống trước khi gán hồ sơ ứng viên vào.
8. Risks & Edge Cases
 
Ứng viên nộp lại hồ sơ sau 6 tháng:
Giải pháp: Time window check: nếu bản ghi cũ ở trạng thái "Refused" và khoảng cách > 180 ngày, bypass bộ lọc trùng lặp, tự động archive hồ sơ cũ thành lịch sử và mở thẻ ứng viên mới cho chiến dịch hiện tại.


 
  MODULE 5    TIME OFF & LEAVE MANAGEMENT (QUẢN LÝ NGHỈ PHÉP & VẮNG MẶT)
 
1. Business Analysis — Phân tích Nghiệp vụ
 
Công tác quản trị nghỉ phép tuân thủ 2 quy trình nghiệp vụ lõi: Cấp phát định mức quỹ phép năm (hr.leave.allocation) và Đăng ký phê duyệt đơn xin nghỉ phép (hr.leave). Nhân sự chính thức khối văn phòng được cấp phát lũy tiến 1 ngày phép hưởng lương/tháng.
 
Quy trình phê duyệt 2 cấp: Trưởng bộ phận (cấp 1) → Trưởng phòng HR (cấp cuối).
 
Ràng buộc quan trọng đối với Khối Giảng viên: Tuyệt đối không cho phép nộp đơn xin nghỉ nếu khung giờ xin nghỉ trùng với lịch dạy đã phân công — trừ khi đã có nhân sự dạy thay được xác nhận trên phân hệ Sản phẩm.
 
2. Source Excel Analysis
 
•     Tệp nguồn: Theo dõi ngày phép.csv, Xin nghỉ phép đi trễ_về sớm.csv
 
Đánh giá chất lượng dữ liệu:
◦     Sai lệch quỹ công tồn phép: Giá trị âm tại cột "Số phép còn lại" do duyệt vượt định mức cho nhân sự thử việc/CTV chưa có quyền hưởng phép năm.
◦     Lỗi chuỗi số (Duration Formatting): Cột thời gian nghỉ hỗn hợp đơn vị — lúc tính bằng ngày ("1 day"), lúc bằng giờ ("4 hours"), gây mất tính thống nhất khi đối soát.
 
3. Data Model Design
 
Thực thể chính:
•     hr.leave — Đơn đăng ký nghỉ phép
•     hr.leave.type — Danh mục phân loại hình thức nghỉ
•     hr.leave.allocation — Cấp phát định mức quỹ phép
 
Trường tính toán & Ràng buộc:
•     number_of_days: Tự động tính ngày kết thúc − ngày bắt đầu, loại trừ ngày lễ quốc gia và cuối tuần (T7/CN).
•     Chặn overlap: Không tồn tại 2 đơn nghỉ phép có khoảng thời gian giao nhau của cùng một nhân sự.
 
4. Odoo Model Mapping — Bảng Ánh xạ Dữ liệu Cấp Trường
 
 
Trường Excel
	Ý nghĩa NV
	Mô hình Odoo
	Trường Odoo
	Kiểu DL
	Bắt buộc
	Quy tắc chuyển đổi
	SourceID
	Mã đơn gốc hệ thống Lark
	hr.leave
	x_lark_leave_id
	Char
	YES
	Khóa đồng bộ đơn qua API Staging layer.
	Status
	Trạng thái phê duyệt đơn
	hr.leave
	state
	Selection
	YES
	"Approved" → validate; "Under Review" → confirm.
	Requester
	Nhân sự làm đơn
	hr.leave
	employee_id
	Many2one
	YES
	Match họ tên/tài khoản Lark → ID hr.employee.
	Leave type
	Phân loại hình thức nghỉ
	hr.leave
	holiday_status_id
	Many2one
	YES
	"Xin nghỉ phép" → Loại phép năm; "Nghỉ thai sản" → Loại thai sản.
	Start time
	Thời điểm bắt đầu nghỉ
	hr.leave
	date_from
	Datetime
	YES
	Chuẩn hóa về múi giờ UTC máy chủ.
	End time
	Thời điểm kết thúc nghỉ
	hr.leave
	date_to
	Datetime
	YES
	Chuẩn hóa về múi giờ UTC máy chủ.
	Duration (số ngày)
	Tổng số ngày xin nghỉ
	hr.leave
	number_of_days
	Float
	YES
	Chuyển đổi định dạng số thực để trừ vào quỹ phép.
	 
5. Customization Requirements — Cross-Module Constraint
 
Custom Inter-Module Constraint Workflow:
Khi giảng viên nộp đơn nghỉ phép, hệ thống truy vấn chéo bảng academic.session. Nếu phát hiện lịch dạy đang hoạt động trong khung giờ xin nghỉ, hệ thống chặn và hiển thị thông báo lỗi.
 
# Python Constraint: Chặn giảng viên nghỉ phép nếu vướng lịch dạy lớp học
from odoo import models, api, _
from odoo.exceptions import ValidationError
 
class HrLeave(models.Model):
        _inherit = "hr.leave"
 
        @api.constrains("date_from", "date_to", "employee_id", "state")
        def _check_academic_session_conflicts(self):
            for record in self:
                if record.state in ["confirm", "validate"] and \
                   record.employee_id.x_work_mode == "online":
                    conflicting_sessions = self.env["academic.session"].search([
                        ("teacher_id", "=", record.employee_id.id),
                        ("start_time", "<",  record.date_to),
                        ("end_time",   ">",  record.date_from),
                        ("state",          "=",  "confirmed"),
                    ])
                    if conflicting_sessions:
                        raise ValidationError(_(\
                            "Giảng viên đang có lịch dạy trong khung giờ xin nghỉ. "
                            "Vui lòng điều phối nhân sự dạy thay trước khi phê duyệt đơn phép!"
                        ))
 
8. Risks & Edge Cases
 
Đơn nghỉ phép vắt qua 2 năm tài chính (VD: 25/12/2025 → 05/01/2026):
Giải pháp: Leave Splitting Algorithm: tự động tách đơn thành 2 bản ghi độc lập — Bản ghi 1 trừ vào quỹ phép 2025, Bản ghi 2 trừ vào hạn mức quỹ phép năm mới 2026.


 
PHẦN 2: KIẾN TRÚC KỸ THUẬT TỔNG THỂ & CHIẾN LƯỢC CHUYỂN ĐỔI DỮ LIỆU
 
 
1. Database Design & Global ERD
Để đảm bảo toàn vẹn dữ liệu và triệt tiêu các lỗi phi chuẩn hóa từ hệ thống Excel cũ, cấu trúc cơ sở dữ liệu đích trên Postgres được thiết kế theo chuẩn hóa sâu sắc với ràng buộc khóa cứng tại tầng vật lý Database.
 
Đặc tả Kiến trúc Mối Quan hệ Thực thể (Global ERD Schema)
┌─────────────────────────────────────────────────┐
│                   RES.COMPANY (Chi Nhánh)               │
│  PK  id (Integer)                                   │
│          name (Varchar) — UNIQUE                        │
└─────────────────────────┬───────────────────────┘
                              │ 1 : N (company_id)
┌─────────────────────────▼───────────────────────┐
│                 HR.DEPARTMENT (Phòng Ban)                │
│  PK  id (Integer)                                   │
│          name (Varchar)                                 │
│  FK  parent_id → hr_department(id) ON DELETE SET NULL
│  FK  company_id → res_company(id) ON DELETE RESTRICT
└─────────────────────────┬───────────────────────┘
                              │ 1 : N (department_id)
┌─────────────────────────▼───────────────────────┐
│               HR.EMPLOYEE (Nhân Sự Master)               │
│  PK  id (Integer)                                   │
│          name (Varchar)                                 │
│          barcode (Varchar)             — UNIQUE INDEX   │
│          identification_id (Varchar) — UNIQUE INDEX │
│          work_email (Varchar)          — UNIQUE INDEX   │
│          mobile_phone (Varchar)        — UNIQUE INDEX   │
│          x_lark_user_id (Varchar)  — UNIQUE INDEX   │
│          x_work_mode (Selection)  [offline|online|ctv]
│  FK  department_id → hr_department(id) RESTRICT │
│  FK  job_id → hr_job(id) RESTRICT                   │
└──────┬─────────────────┬──────────────┬─────────┘
   1:N │                  1:N│               1:N│
┌──────▼──────┐  ┌───────▼──────┐  ┌───▼──────────┐
│HR.CONTRACT  │  │HR.ATTENDANCE │  │HR.LEAVE          │
│date_start   │  │check_in          │  │date_from     │
│date_end         │  │check_out         │  │date_to       │
│wage             │  │x_lark_id(UQ) │  │state             │
│CONSTRAINT:  │  │CONSTRAINT:   │  │CONSTRAINT:   │
│No overlap   │  │check_out >   │  │No overlap    │
│contracts        │  │check_in          │  │per employee  │
└──────┬──────┘  └──────────────┘  └──────────────┘
        1:1│
┌──────▼──────────────────────────────────────────┐
│                      HR.PAYSLIP (Phiếu Lương)            │
│  FK  employee_id → hr_employee(id) RESTRICT         │
│  FK  contract_id → hr_contract(id) RESTRICT         │
│          date_from / date_to (Date)                     │
│          state [draft|verify|done|cancel]               │
└─────────────────────────────────────────────────┘
 
Chiến lược Database Indexing
•     B-Tree Indexes mở rộng: hr_employee(barcode), hr_employee(x_lark_user_id), hr_attendance(check_in, check_out).
•     Partial Index đặc thù:
CREATE INDEX idx_active_employees
  ON hr_employee(id)
  WHERE active = true;
 
2. Recommended Odoo Technical Architecture
Hệ thống kiến trúc đích xây dựng trên nền tảng Odoo 19 Enterprise, triển khai theo mô hình hạ tầng độc lập để đảm bảo tối đa quyền kiểm soát mã nguồn và tối ưu hiệu năng xử lý CSDL.
 
            [ CỔNG TRUY CẬP NGƯỜI DÙNG / USER CLIENTS ]
             (Mobile App Odoo / Trình duyệt Web Văn phòng)
                                  │
                                  ▼
                 ┌────────────────────────────┐
                 │  Nginx Reverse Proxy & SSL │
                 └────────────┬───────────────┘
               ┌──────────────┴──────────────┐
               │ Giờ hành chính                  │ Tác vụ nền/Báo cáo
               ▼                                 ▼
┌─────────────────────┐  ┌─────────────────────────┐
│ Odoo App Server 1   │  │  Odoo App Server 2          │
│  [Giao dịch chính]  │  │  [Cron / Background]        │
└──────────┬──────────┘  └────────────┬────────────┘
               └──────────────┬───────────┘
                              ▼
                 ┌────────────────────────────┐
                 │  PgBouncer (Connection Pool)│
                 └────────────┬───────────────┘
                              ▼
                 ┌────────────────────────────┐
                 │  PostgreSQL Database Server │
                 │   (Bộ lưu trữ dữ liệu vật lý)│
                 └────────────────────────────┘
 
Điểm kiến trúc chính:
•     Multi-Instance Load Balancing: Instance 1 tiếp nhận luồng tương tác người dùng (Web/Mobile). Instance 2 cô lập xử lý tác vụ nặng (Cron, tính lương cuối tháng, đối soát công vân tay).
•     Tích hợp Lark Suite qua API Gateway: Custom Controller tiếp nhận Webhook từ Lark. Khi nhân sự quét chấm công hoặc đơn từ được duyệt, Lark đẩy JSON Metadata sang Odoo — hệ thống validate và cập nhật Postgres theo Realtime.
 
3. Comprehensive Master Data Migration Strategy (ETL Pipeline)
Quá trình chuyển đổi từ Excel phân tán sang Odoo 19 tuân thủ mô hình ETL 4 giai đoạn qua Staging Layer độc lập để triệt tiêu rủi ro làm nhiễm bẩn CSDL đích.
 
[ Hệ thống Excel Nguồn (CSV files) ]
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│  STAGE 1: EXTRACT & STAGING LAYER                      │
│  - Đọc toàn bộ CSV thô, nạp vào bảng tạm Postgres.│
│  - Không áp ràng buộc logic hay khóa ngoại.           │
└────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│  STAGE 2: TRANSFORM & VALIDATION LAYER                 │
│  - Script Python làm sạch chuỗi (Trim, bỏ Emoji). │
│  - Quy đổi múi giờ UTC+7 → UTC chuẩn quốc tế.        │
│  - Xử lý Net-to-Gross dữ liệu lịch sử bảng lương. │
└────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│  STAGE 3: LOAD & INTEGRITY CHECK                       │
│  - Nạp tuần tự theo cây phụ thuộc dữ liệu.            │
│  - Lưu vết liên kết cũ qua cơ chế External IDs.   │
└────────────────────────┬───────────────────────────┘
                             │
                             ▼
[ Hệ thống Odoo 19 Đích — Sạch & Chuẩn Hóa ]
 
Bản Đặc tả Trình tự Nạp Dữ liệu An toàn
(Bước 1: res.company / res.users)
            │
            ▼
(Bước 2: hr.department)
            │
            ▼
(Bước 3: hr.job)
            │
            ▼
(Bước 4: hr.employee)
            │
            ▼
(Bước 5: hr.contract)
            │
            ▼
(Bước 6: hr.attendance / hr.leave)
            │
            ▼
(Bước 7: hr.payslip — Thực thể phụ thuộc cuối cùng)
 
Chiến lược Rollback & Data Isolation
Toàn bộ tiến trình import của từng Batch đóng gói trong một Database Transaction Block. Nếu phát hiện dữ liệu lỗi ở bất kỳ dòng nào, hệ thống lập tức phát lệnh db.rollback() — hủy bỏ toàn bộ dữ liệu đã import trong Batch đó, trả CSDL về trạng thái sạch ban đầu. Không chấp nhận import lỗi một nửa.
 
4. Global Gap Analysis Summary
Bản phân tích Gap xác định ranh giới giữa tính năng tiêu chuẩn Odoo 19 sẵn có (Out-of-the-box) và các phần bắt buộc phải lập trình tùy biến (Custom Development) để đáp ứng mô hình vận hành giáo dục đặc thù của Học Bá.
 
Phân hệ Odoo Standard (Sử dụng trực tiếp)
•     hr.department — Sơ đồ tổ chức phòng ban
•     hr.employee — Hồ sơ nhân viên cơ bản
•     hr.contract — Hợp đồng lao động tiêu chuẩn
•     hr.payslip — Bộ máy quy tắc tính toán lương thời gian tĩnh
•     hr.applicant — Đường ống Kanban tiếp nhận hồ sơ ứng viên
 
Phân hệ Custom Development (Yêu cầu lập trình bổ sung)
•     Module x_hb_attendance_ext:
◦     So khớp ma trận lịch đăng ký ca tuần cho khối CTV.
◦     Tự động đồng bộ phiếu quên chấm công / làm online để vá dữ liệu thô.
•     Module x_hb_payroll_ext:
◦     Thuật toán hoa hồng bậc thang động liên kết doanh thu thực thu CRM.
◦     Cơ chế tách lọc thù lao giảng dạy theo buổi (Session rate) khối Giáo viên.
•     Module x_hb_leave_ext:
◦     Thuật toán chặn cứng vắng mặt trùng lịch ca dạy trực tuyến cố định của Giáo viên.
 
5. Systemic Risks & Business Edge Cases Matrix
Bản đặc tả kỹ thuật dự phòng các kịch bản lỗi hệ thống (Edge Cases) có thể phát sinh trong quá trình vận hành thực tế, đi kèm giải pháp kiến trúc xử lý triệt để.
 
Mã Rủi Ro
	Phân Hệ
	Tình huống Lỗi
	Tác động
	Phương án Giải quyết
	R-SYS-01
	Payroll
	Xung đột cấu trúc lương khi đổi vai trò giữa tháng: nhân viên HB.85 chuyển từ thử việc Kinh doanh sang chính thức Vận hành từ ngày 15.
	Tính sai tiền lương, lỗi ma trận phụ cấp hành chính.
	Đóng hợp đồng cũ tại ngày 14, tạo hợp đồng mới từ ngày 15. Bộ máy lương tự sinh 2 phiếu lương Pro-rata trong cùng một kỳ tháng.
	R-SYS-02
	Attendance
	Spam thiết bị đẩy dữ liệu trùng: Anycross bị lỗi mạng, đẩy lặp một bản ghi chấm công thô nhiều lần qua API.
	Nhân đôi ngày công, tính sai số phút đi muộn.
	Unique index kết hợp x_lark_result_id + check_in. SQL ON CONFLICT DO NOTHING ở tầng kiến trúc để loại bỏ gói tin trùng lặp.
	R-SYS-03
	Time Off
	Giảng viên đột xuất xin nghỉ khi lớp đang diễn ra — học viên đã vào phòng Zoom.
	Hủy hoại trải nghiệm học viên, vỡ tiến độ đào tạo.
	Gửi thông báo Realtime qua Bot Lark tới Giáo vụ. Đóng băng lớp học, tự động chuyển quyền phòng Zoom sang Giảng viên dự phòng trong Database.
	R-SYS-04
	Recruitment
	Ứng viên nộp đồng thời vào 2 vị trí (VD: Giảng viên tiếng Trung + Chuyên viên R&D).
	Phân rã dữ liệu, 2 chuyên viên tuyển dụng tiếp cận trùng nhau.
	Mô hình res.partner trung tâm: 1 ứng viên = 1 Partner gốc (SĐT/Email), nhưng được liên kết song song với 2 thẻ hr.applicant độc lập trên 2 Stage Kanban khác nhau.
	 


Chapter 6 - Employee
CHƯƠNG 5 — ĐẶC TẢ CẤU HÌNH HỆ THỐNG (CONFIGURATION — UPDATED)
5.1. Cấu hình giữ từ v1.0
CONF-EMP-01 Regex CCCD · CONF-EMP-02 Địa giới 2 cấp · CONF-EMP-04/05 Skill Types/Levels (HSK/HSKK/Sư phạm/TOCFL) · CONF-EMP-06 Flexible Schedule GV Online · CONF-EMP-09 Presence Control · CONF-EMP-10 Badges Gamification.
 
5.2. Cấu hình bổ sung / hiệu chỉnh
 
Mã
	Tên cấu hình
	Khu vực Odoo
	Kết quả kỳ vọng
	CONF-EMP-03b
	Employment Types theo Lark
	Employees > Configuration > Employment Types
	Tạo: Chính thức, Thử việc, TTS, Part-time, CTV, Cố vấn, Thỉnh giảng (khớp Trục 2).
	CONF-EMP-11
	Phòng ban chuẩn
	Employees > Departments
	Tạo: Marketing, Sản phẩm (R&D_SP), Kinh doanh, Vận hành, Kế toán_HCNS, BOD (kèm Manager).
	CONF-EMP-12
	Cây chức danh (Job Positions)
	Employees > Recruitment > Job Positions
	Nhập theo 8.4 Lookup chức danh: Trưởng phòng > Trưởng bộ phận > Chuyên viên > Nhân viên > CTV cho từng phòng.
	CONF-EMP-07a
	Plan: Onboarding Giảng viên
	Plans
	Tác vụ: IT cấp email + Zoom/ClassIn (ngày 1); Admin giao giáo trình/slide; Academic dự giờ thử giảng (tuần 1, ghi Đạt/Không đạt); Academic số hóa kỹ năng.
	CONF-EMP-07b
	Plan: Onboarding Nhân viên VP/Sales (Giai đoạn 1 – Hội nhập)
	Plans
	Tác vụ: HCNS gửi tài liệu + đào tạo văn hóa; bàn giao cho TBP; sinh Activity "Đánh giá tuần-2" với deadline +14 ngày. Chưa cấp thiết bị.
	CONF-EMP-07c
	Plan: Cấp thiết bị (Giai đoạn 2)
	Plans + Automated Action
	Tự kích hoạt khi x_eval_2w_result = Đạt: HCNS/Admin tạo bản ghi tài sản (máy tính + vật dụng), tích checklist; sinh Activity "Đánh giá tháng-2" deadline +60 ngày.
	CONF-EMP-08a
	Plan: Offboarding – Nghỉ thử việc
	Plans
	4 bước: thông báo đánh giá → TBP đánh giá → bàn giao CV & tài sản → bảo mật (khóa Related User, gỡ nhóm).
	CONF-EMP-08b
	Plan: Offboarding – Nghỉ việc chính thức
	Plans
	7 bước: nhận đơn → TBP xem xét → HCNS phỏng vấn → Giám đốc phê duyệt → bàn giao → thanh lý HĐ + chốt công nợ (Kế toán) → lưu hồ sơ + Archive.
	CONF-EMP-13
	Danh mục tài sản chuẩn
	Maintenance/Equipment > Configuration
	Tạo loại tài sản: Màn hình, Cây máy tính, Bàn phím, Chuột, Lót bàn phím, Tai nghe (to/sale), Ghế, Bàn, Máy in.
	 
5.3. Chi tiết Automated Action cổng thử việc (G-13/G-14)
● AUT-001 — Cổng tuần-2: Trigger On Update field x_eval_2w_result.
○ = Đạt → Server Action: Launch Plan "Cấp thiết bị" + tạo Activity "Đánh giá tháng-2".
○ = Không đạt → Server Action: Launch Plan "Offboarding – Nghỉ thử việc".
● AUT-002 — Cổng tháng-2: Trigger On Update field x_eval_2m_result.
○ = Đạt → set Tình trạng = Chính thức, gán x_official_date = today, gợi ý tạo HĐ chính thức (hr.contract).
○ = Không đạt → Launch Plan "Offboarding – Nghỉ thử việc".
● CRON — Nhắc đánh giá: quét hằng ngày các hồ sơ Thử việc có x_eval_2w_due/x_eval_2m_due đến hạn → bắn Activity nhắc HCNS & TBP.
 
 
 
Chapter6: FUNCTIONAL SPECIFICATION — MODULE EMPLOYEES (ODOO 19)
Học Bá Education · Phiên bản 1.0 · Custom Features Only
Phạm vi tài liệu: 9 chức năng lập trình mở rộng (prefix x_ / model mới). Các hạng mục cấu hình thuần (Employment Types, Plans, Departments) không thuộc phạm vi này.
Quy ước: Required* = bắt buộc khi lưu; Required° = bắt buộc theo điều kiện nghiệp vụ.
 


MỤC LỤC CHỨC NĂNG
 
Function ID
	Tên chức năng
	GAP ref
	Độ phức tạp
	FUNC-EMP-001
	Hồ sơ tổng quan (Overview Profile)
	G-15
	Trung bình
	FUNC-EMP-002
	Trường dữ liệu pháp lý Việt Nam
	G-01..08
	Thấp
	FUNC-EMP-003
	Quản lý người phụ thuộc giảm trừ gia cảnh
	G-12
	Trung bình
	FUNC-EMP-004
	Dòng thời gian thử việc & 2 cổng đánh giá
	G-13
	Cao
	FUNC-EMP-005
	Tự động hóa cổng thử việc (AUT-001 / AUT-002)
	G-14
	Cao
	FUNC-EMP-006
	Quản lý tài sản cấp phát & thu hồi
	G-17
	Trung bình
	FUNC-EMP-007
	Lịch sử thăng tiến & lương (Promotion Snapshot)
	G-18
	Thấp
	FUNC-EMP-008
	Đánh giá thử giảng & Ma trận kỹ năng giảng viên
	G-10 / G-19
	Trung bình
	FUNC-EMP-009
	CRON cảnh báo chứng chỉ sắp hết hạn
	G-10
	Thấp
	 
 
 
FUNC-EMP-001 — Hồ sơ tổng quan (Overview Profile)
Function ID: FUNC-EMP-001
Function Name: Hồ sơ tổng quan nhân viên
Module: Employees (hr.employee)
Actor: HR (xem/sửa), Nhân viên (xem qua Portal), TBP (xem)
Purpose: Cung cấp một màn hình duy nhất tổng hợp toàn bộ thông tin nhân viên — định danh, phân loại, mốc vòng đời, smart buttons liên kết — thay thế cho việc tra cứu rải rác nhiều sheet Lark.
 
 
 
Preconditions:
● Hồ sơ nhân viên (hr.employee) đã được tạo (từ Recruitment hoặc thủ công).
● Người dùng có quyền hr.group_hr_user trở lên.
 
Trigger:
● Người dùng mở record hr.employee bất kỳ.
● Hệ thống Recruitment tạo hồ sơ Draft từ ứng viên trúng tuyển.
 
 
 
Main Flow:
1. HR mở form hr.employee. Header hiển thị: ảnh đại diện, Họ tên (lớn), Chức danh, Phòng ban.
2. Hàng chip phân loại hiển thị ngay dưới tên: [Hình thức] [Phòng ban] [Mã NS] (colored chips).
3. Statusbar trạng thái hiển thị ở góc phải: Thử việc → Chính thức → Nghỉ việc (trạng thái hiện tại được tô đậm). Trạng thái đồng bộ với x_employment_status.
4. Hàng Smart Buttons hiển thị bên dưới header: Hợp đồng (số lượng), Tài sản (số thiết bị đang giữ), Chứng chỉ (số mục sắp hết hạn — highlight cam nếu > 0), Thăng tiến (số bản ghi log), Đơn từ (nghỉ phép/OT).
5. Khối "Dòng thời gian thử việc" (chỉ hiển thị khi x_employment_status ∈ {Thử việc, Chính thức} và loại nhân viên là Nhóm B): xem FUNC-EMP-004.
6. Notebook tab đầu tiên "Tổng quan" chia 3 cột: Định danh & Tổ chức | Liên hệ & Pháp lý | Chuyên môn & Tài chính.
7. Các tab tiêu chuẩn còn lại: Work Information, Resumé & Skills, Private Information, Payroll, HR Settings.
 
Alternative Flow:
● Nếu x_employment_status = Nghỉ việc: statusbar hiện trạng thái cuối, nút Archive thay bằng "Đã lưu trữ" (readonly). Smart buttons vẫn hiển thị để tra lịch sử.
● Nhân viên truy cập qua Portal: chỉ hiển thị tab Tổng quan ở chế độ xem, không thấy dữ liệu lương/thuế.
 
Exception Flow:
● Nếu hồ sơ chưa có ảnh: hiển thị avatar placeholder mặc định có chữ tắt họ tên.
● Smart Button "Chứng chỉ" highlight đỏ nếu có chứng chỉ đã hết hạn (không chỉ sắp hết).
 
 
 
Validation Rules:
● x_employee_code (Mã NS): unique, không được sửa sau khi đã có hợp đồng chính thức.
● x_employment_status chỉ được chuyển từ Thử việc → Chính thức qua cơ chế AUT-002 (không cho sửa thủ công nếu không có quyền hr.group_hr_manager).
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Mã nhân sự
	x_employee_code
	Char(10)
	*
	Unique; pattern HB\.\d{2,3}
	Hình thức làm việc
	x_work_form
	Selection
	*
	offline / online
	Tình trạng / Loại HĐ
	x_employment_status
	Selection
	*
	Xem danh sách trạng thái
	Loại vị trí
	x_position_type
	Selection
	*
	manager / staff / ctv / freelancer / advisor
	Số tháng chính thức
	x_official_months
	Float (computed)
	—
	(today - x_official_date).days / 30; readonly
	 
Output: Form hiển thị đầy đủ; Smart Button counts tự động refresh khi navigate.
 
Business Rules:
● BR-001: Mã nhân sự được sinh tự động theo format HB.<next_seq> khi tạo mới; HR có thể override trước khi lưu lần đầu.
● BR-002: x_employment_status mặc định là draft khi tạo; chuyển Thử việc khi HR xác nhận onboarding.
● BR-003: Smart Button "Tài sản" đếm records hr.employee.asset có state = assigned và employee_id = current.
 
UI Reference: Wireframe WIREFRAME_HoSoTongQuan.svg — Header + Statusbar + Smart Buttons + Tab Tổng quan.
 
 
 
FUNC-EMP-002 — Trường dữ liệu pháp lý Việt Nam
Function ID: FUNC-EMP-002
Function Name: Mở rộng trường pháp lý theo quy định Việt Nam
Module: Employees (hr.employee) — Tab Private Information
Actor: HR (nhập/sửa), Nhân viên (tự cập nhật qua Portal — phần địa chỉ)
Purpose: Lưu trữ đầy đủ thông tin pháp lý bắt buộc theo luật lao động VN: CCCD (ngày/nơi cấp), MST TNCN, BHXH, BHYT, địa chỉ thường trú và tạm trú tách biệt.
 
 
 
Preconditions: Hồ sơ nhân viên đã tạo.
 
Trigger: HR mở Tab Private Information và điền/cập nhật thông tin pháp lý.
 
 
 
Main Flow:
1. HR mở Tab Private Information → nhóm "Giấy tờ pháp lý" hiển thị các trường CCCD mở rộng.
2. HR nhập số CCCD (12 số) → nhập ngày cấp → nhập nơi cấp (tỉnh/thành, cơ quan cấp).
3. HR nhập MST TNCN (13 số) → hệ thống validate format.
4. HR nhập số sổ BHXH (10 số) và số thẻ BHYT + nơi KCB ban đầu.
5. HR nhập địa chỉ thường trú: chọn Tỉnh/Thành (dropdown res.country.state, filter VN) → nhập Phường/Xã → nhập Số nhà/Đường.
6. Nếu địa chỉ tạm trú khác thường trú: bỏ tick "Giống địa chỉ thường trú" → nhập tương tự.
7. Lưu → hệ thống validate tất cả format.
 
Alternative Flow:
● Nhân viên nước ngoài: MST TNCN và BHXH là optional; trường CCCD nhận Passport number (bỏ validation 12 số).
● Địa chỉ tạm trú giống thường trú: tick checkbox x_current_same_as_permanent = True → tự copy và lock các trường tạm trú.
 
Exception Flow:
● Nhập CCCD đã tồn tại trên hồ sơ khác → hiện warning "CCCD đã được đăng ký cho [Tên NV]". Không block lưu (có thể là lỗi data cũ).
 
 
 
Validation Rules:
● CCCD: ^\d{12}$ — 12 chữ số.
● MST TNCN: ^\d{10}(\d{3})?$ — 10 hoặc 13 số.
● Số sổ BHXH: ^\d{10}$ — 10 chữ số.
● x_id_date_issue ≤ ngày hiện tại.
● x_id_date_issue ≥ ngày sinh (birthday) + 14 năm.
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Số CCCD
	identification_id
	Char(12)
	*
	Regex ^\d{12}$; chuẩn Odoo
	Ngày cấp CCCD
	x_id_date_issue
	Date
	°
	Nếu có CCCD; ≤ today; ≥ DOB+14y
	Nơi cấp CCCD
	x_id_place_issue
	Char(100)
	°
	Nếu có CCCD
	MST TNCN
	x_pit_code
	Char(13)
	°
	Regex ^\d{10}(\d{3})?$; khi lên Chính thức
	Số sổ BHXH
	x_social_insurance_no
	Char(10)
	°
	Regex ^\d{10}$; khi lên Chính thức
	Số thẻ BHYT
	x_health_insurance_no
	Char(15)
	—
	Free format
	Nơi KCB ban đầu
	x_health_care_place
	Char(100)
	—
	 
	Tỉnh/Thành thường trú
	x_permanent_state_id
	Many2one res.country.state
	*
	Filter country_id.code='VN'
	Phường/Xã thường trú
	x_permanent_ward
	Char(100)
	*
	 
	Số nhà/Đường thường trú
	x_permanent_street
	Char(200)
	*
	 
	Giống địa chỉ thường trú
	x_current_same_as_permanent
	Boolean
	—
	Default: True
	Tỉnh/Thành tạm trú
	x_current_state_id
	Many2one
	°
	Hiện khi checkbox = False
	Phường/Xã tạm trú
	x_current_ward
	Char(100)
	°
	Hiện khi checkbox = False
	Số nhà/Đường tạm trú
	x_current_street
	Char(200)
	°
	Hiện khi checkbox = False
	 
Output: Dữ liệu lưu vào hr.employee; hiển thị trong Tab Private và Tab Tổng quan (che một phần theo phân quyền).
 
Business Rules:
● BR-010: MST TNCN và Số BHXH bắt buộc trước khi tạo Hợp đồng chính thức (hr.contract với contract_type = official).
● BR-011: Dữ liệu CCCD, MST, BHXH ẩn với hr.group_hr_user; chỉ hiển thị đầy đủ với hr.group_hr_manager và Kế toán.
● BR-012: Khi x_current_same_as_permanent = True, các trường tạm trú bị readonly và mirror thường trú.
 
UI Reference: Tab "Private Information" → section "Giấy tờ pháp lý & Địa chỉ VN".
 
 
 
FUNC-EMP-003 — Quản lý người phụ thuộc giảm trừ gia cảnh
Function ID: FUNC-EMP-003
Function Name: Quản lý người phụ thuộc (Dependents)
Module: Employees — model mới hr.employee.dependent
 Actor: HR (nhập/duyệt), Kế toán (đọc để tính thuế TNCN)
Purpose: Lưu trữ danh sách người phụ thuộc của từng nhân viên phục vụ tính giảm trừ gia cảnh theo Thông tư 111/2013/TT-BTC (hiện hành).
 
 
 
Preconditions: Hồ sơ nhân viên đã tạo. Nhân viên đã cung cấp hồ sơ đăng ký người phụ thuộc (MST hoặc CCCD của NTT).
 
Trigger: HR nhận hồ sơ đăng ký NTT từ nhân viên; hoặc nhân viên tự khai qua Portal.
 
 
 
Main Flow:
1. HR mở Tab Private Information → section "Người phụ thuộc".
2. Bấm Thêm dòng (One2many widget) → nhập thông tin NTT.
3. Nhập: Họ tên, Quan hệ (vợ/chồng / con / bố mẹ / anh chị em), Ngày sinh, Số CCCD/MST.
4. Nhập ngày bắt đầu được tính giảm trừ (tháng đăng ký với cơ quan thuế).
5. Nhập ngày kết thúc (nếu NTT đã tự chủ về thu nhập hoặc đã mất).
6. Lưu → hệ thống tính tự động số NTT đang còn hiệu lực (x_active_dependent_count).
7. Kế toán đọc x_active_dependent_count khi tính lương: giảm trừ = 4.4tr × số NTT/tháng.
 
Alternative Flow:
● Nhân viên nước ngoài cư trú: NTT là người nước ngoài → số hộ chiếu thay CCCD.
 
Exception Flow:
● Ngày bắt đầu > ngày kết thúc → block lưu, hiện lỗi "Ngày bắt đầu phải trước ngày kết thúc".
● Trùng CCCD NTT với NTT của nhân viên khác → cảnh báo (không block, vì cha/mẹ có thể được 2 con cùng khai — kiểm tra riêng với cơ quan thuế).
 
 
 
Validation Rules:
● date_start ≤ today.
● date_end > date_start (nếu có).
● relationship ∈ danh sách cố định.
● Không giới hạn số NTT (theo luật không giới hạn số con).
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Họ tên NTT
	name
	Char(100)
	*
	 
	Quan hệ
	relationship
	Selection
	*
	spouse/child/parent/sibling/other
	Ngày sinh NTT
	birthday
	Date
	*
	≤ today
	Số CCCD / Hộ chiếu NTT
	national_id
	Char(20)
	°
	Nếu đủ tuổi; regex ^\d{9,12}$ hoặc passport
	Ngày bắt đầu tính giảm trừ
	date_start
	Date
	*
	≤ today; theo tháng đăng ký thuế
	Ngày kết thúc
	date_end
	Date
	—
	> date_start nếu có
	Ghi chú
	notes
	Text
	—
	 
	 
Output:
● x_active_dependent_count (computed): đếm records hr.employee.dependent của nhân viên có date_start <= today và (date_end null hoặc > today).
● Hiển thị số này ở Tab Tổng quan và dùng trong bảng lương.
 
Business Rules:
● BR-020: Mức giảm trừ gia cảnh cho NTT: 4.400.000 VNĐ/tháng (cập nhật khi luật thay đổi qua cấu hình hệ thống, không hardcode).
● BR-021: Giảm trừ tính theo tháng của date_start; tháng kết thúc tính theo date_end.
● BR-022: Kế toán có quyền readonly; chỉ HR Manager được thêm/sửa/xóa.
 
UI Reference: Tab "Private Information" → section "Người phụ thuộc" (One2many list + form dialog).
 
 
 
FUNC-EMP-004 — Dòng thời gian thử việc & 2 cổng đánh giá
Function ID: FUNC-EMP-004
Function Name: Probation Timeline — Cổng đánh giá tuần-2 & tháng-2
Module: Employees (hr.employee) — custom block
Actor: TBP / HR (điền kết quả đánh giá), HR (xem tổng quan)
Purpose: Quản lý chu trình thử việc 2 bước cho Nhân viên Nhóm B: cổng tuần-2 kiểm soát cấp thiết bị; cổng tháng-2 kiểm soát lên chính thức. Thay thế Excel theo dõi thủ công.
 
 
 
Preconditions:
● x_employment_status = Thử việc.
● x_position_type ∈ {staff, manager} (Nhóm B — Nhân viên VP/Sales; không áp cho GV/CTV).
● HR đã Launch Plan "Onboarding Nhân viên (Hội nhập)".
 
Trigger:
● HR Launch Plan Onboarding → hệ thống ghi x_probation_start = today và tính x_eval_2w_due, x_eval_2m_due.
● CRON ngày đến hạn: tạo Activity nhắc TBP đánh giá.
 
 
 
Main Flow — Cổng tuần-2:
1. Hệ thống tạo Activity "Đánh giá thử việc tuần-2" giao cho TBP (x_eval_2w_due là deadline).
2. TBP mở hồ sơ nhân viên → xem block "Dòng thời gian thử việc".
3. TBP chọn x_eval_2w_result: Đạt hoặc Không đạt.
4. TBP nhập ghi chú đánh giá (x_eval_2w_note) và ngày thực tế (x_eval_2w_date).
5. TBP lưu → hệ thống trigger AUT-001 (xem FUNC-EMP-005).
6. Mini-timeline trên form cập nhật trạng thái cổng 1 (xanh = Đạt / đỏ = Không đạt).
 
Main Flow — Cổng tháng-2:
1. Sau khi cổng tuần-2 Đạt, hệ thống tạo Activity "Đánh giá thử việc tháng-2" deadline = x_eval_2m_due.
2. TBP + HR đánh giá, điền x_eval_2m_result và x_eval_2m_note.
3. Lưu → trigger AUT-002 (xem FUNC-EMP-005).
 
Alternative Flow:
● HR Manager có thể ghi đè kết quả đánh giá (override) nếu TBP đánh giá nhầm — log lại user + timestamp.
● Nếu cần gia hạn thử việc: HR đặt lại x_eval_2m_due bằng tay (không quá 60 ngày tiếp theo); ghi chú lý do.
 
Exception Flow:
● TBP cố chọn "Đạt" nhưng chưa nhập x_eval_2w_note → warning "Vui lòng ghi chú căn cứ đánh giá".
● x_eval_2w_due đã qua 3 ngày mà chưa đánh giá → hệ thống escalate Activity lên HR Manager.
 
 
 
Validation Rules:
● x_eval_2w_date ≥ x_probation_start và ≤ today.
● x_eval_2m_date ≥ x_eval_2w_date.
● Không cho điền kết quả cổng tháng-2 nếu cổng tuần-2 chưa Đạt.
● Chỉ user thuộc nhóm hr.group_hr_manager hoặc là manager trực tiếp mới được điền kết quả.
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Ngày bắt đầu thử việc
	x_probation_start
	Date
	*
	Auto-set khi launch Plan; sửa được trước 24h
	Hạn đánh giá tuần-2
	x_eval_2w_due
	Date
	*
	Computed: x_probation_start + 14 days; sửa được
	Kết quả đánh giá tuần-2
	x_eval_2w_result
	Selection
	°
	draft / pass / fail; ° khi đến hạn
	Ngày đánh giá thực tế (tuần-2)
	x_eval_2w_date
	Date
	°
	Nếu result ≠ draft
	Người đánh giá (tuần-2)
	x_eval_2w_evaluator_id
	Many2one res.users
	°
	Nếu result ≠ draft
	Ghi chú đánh giá (tuần-2)
	x_eval_2w_note
	Text
	°
	Bắt buộc nếu result = pass
	Ngày cấp thiết bị
	x_equip_grant_date
	Date
	—
	Auto-set khi AUT-001 chạy
	Hạn đánh giá tháng-2
	x_eval_2m_due
	Date
	*
	Computed: x_probation_start + 60 days; sửa được
	Kết quả đánh giá tháng-2
	x_eval_2m_result
	Selection
	°
	draft / pass / fail
	Ngày đánh giá thực tế (tháng-2)
	x_eval_2m_date
	Date
	°
	Nếu result ≠ draft
	Người đánh giá (tháng-2)
	x_eval_2m_evaluator_id
	Many2one res.users
	°
	 
	Ghi chú đánh giá (tháng-2)
	x_eval_2m_note
	Text
	°
	Bắt buộc nếu result = pass
	Ngày chính thức
	x_official_date
	Date
	—
	Auto-set khi AUT-002 chạy; readonly
	 
Output:
● Mini-timeline trên form (xem Wireframe): 5 điểm tròn với màu trạng thái.
● Activities tự tạo trong chatter.
● x_employment_status được cập nhật tự động qua AUT-001/002.
 
Business Rules:
● BR-030: Block "Dòng thời gian thử việc" chỉ hiển thị khi x_position_type ∈ {staff, manager} VÀ x_work_form = offline. Ẩn với Giảng viên (Nhóm A) và CTV.
● BR-031: x_eval_2w_due mặc định +14 ngày nhưng HR có thể điều chỉnh trong range [7, 21] ngày kể từ x_probation_start.
● BR-032: Lịch sử thay đổi kết quả đánh giá ghi vào chatter với user + thời điểm.
 
UI Reference: BPMN Khối 2 (Onboarding NV) — Cổng tuần-2 và tháng-2; Wireframe "Dòng thời gian thử việc" (khối nét đứt xanh).
 
 
 
FUNC-EMP-005 — Tự động hóa cổng thử việc (AUT-001 & AUT-002)
Function ID: FUNC-EMP-005
Function Name: Automated Actions cổng thử việc
Module: Employees — Automated Actions (base.automation)
Actor: Hệ thống Odoo (trigger tự động), HR (xem kết quả)
Purpose: Loại bỏ thao tác thủ công sau đánh giá: hệ thống tự kích hoạt Plan cấp thiết bị khi Đạt tuần-2; tự xác nhận Chính thức khi Đạt tháng-2; tự khởi động Plan nghỉ thử việc khi Không đạt.
 
 
 
Preconditions:
● Plans "Cấp thiết bị", "Offboarding – Nghỉ thử việc" đã được cấu hình trong hệ thống.
● x_eval_2w_result hoặc x_eval_2m_result vừa được cập nhật.
 
Trigger:
● AUT-001a: x_eval_2w_result chuyển sang pass (On Update).
● AUT-001b: x_eval_2w_result chuyển sang fail (On Update).
● AUT-002a: x_eval_2m_result chuyển sang pass (On Update).
● AUT-002b: x_eval_2m_result chuyển sang fail (On Update).
● CRON nhắc: hằng ngày 7:00 SA — quét hồ sơ đến hạn đánh giá trong 2 ngày tới.
 
 
 
Main Flow — AUT-001a (Đạt tuần-2):
1. Trigger: x_eval_2w_result = pass.
2. Server Action: gọi employee.activity_schedule() tạo Activity type "Cấp thiết bị" giao IT/Admin, deadline = today + 1 ngày.
3. Server Action: set x_equip_grant_date = today (pending — chờ IT xác nhận thực tế).
4. Server Action: ghi log vào chatter: "✅ Cổng tuần-2 ĐẠT — Kế hoạch cấp thiết bị đã được khởi động."
5. Gợi ý: hiển thị smart button "Plan cấp thiết bị" để HR theo dõi.
 
Main Flow — AUT-001b (Không đạt tuần-2):
1. Trigger: x_eval_2w_result = fail.
2. Server Action: gọi Launch Plan "Offboarding – Nghỉ thử việc" trên employee hiện tại.
3. Server Action: set x_employment_status = exiting (đang thực hiện thủ tục).
4. Ghi log chatter: "❌ Cổng tuần-2 KHÔNG ĐẠT — Đã khởi động Plan nghỉ thử việc."
 
Main Flow — AUT-002a (Đạt tháng-2):
1. Trigger: x_eval_2m_result = pass.
2. Server Action: x_official_date = today.
3. Server Action: x_employment_status = official.
4. Server Action: gọi wizard tạo hợp đồng mới (hr.contract) loại "Chính thức" với date_start = x_official_date.
5. Server Action: ghi log chatter: "🎉 Cổng tháng-2 ĐẠT — Nhân viên được chuyển sang Chính thức. Hợp đồng chính thức đã được tạo nháp."
6. Gửi email thông báo cho nhân viên (template mail.template "Chúc mừng lên chính thức").
 
Main Flow — AUT-002b (Không đạt tháng-2):
1. Trigger: x_eval_2m_result = fail.
2. Server Action: Launch Plan "Offboarding – Nghỉ thử việc".
3. Set x_employment_status = exiting.
4. Ghi log chatter.
 
Main Flow — CRON nhắc:
1. Hằng ngày 7:00 SA — ir.cron quét hr.employee có x_eval_2w_result = draft AND x_eval_2w_due <= today + 2.
2. Với mỗi hồ sơ: gọi activity_schedule() nhắc TBP (là parent_id của nhân viên) và HR Manager.
3. Tương tự với x_eval_2m_due.
 
Alternative Flow:
● HR có thể disable AUT-001/002 cho một nhân viên cụ thể bằng cách set x_skip_auto_trigger = True (flag bảo vệ trường hợp đặc biệt). Khi đó hệ thống ghi log "Auto trigger bị bỏ qua — đã bị override bởi [user]."
 
Exception Flow:
● Plan "Cấp thiết bị" không tồn tại → AUT-001a ghi lỗi vào log và tạo Activity thủ công nhắc HR kích hoạt Plan.
● Email template không tồn tại → bỏ qua email, không block action.
 
 
 
Validation Rules:
● Mỗi trigger chỉ chạy MỘT LẦN cho mỗi lần thay đổi field (kiểm tra bằng old value ≠ new value).
● Không chạy AUT-002 nếu x_eval_2w_result ≠ pass (guard condition).
 
Input Fields: Không có input trực tiếp — tất cả kích hoạt tự động.
 
Output:
● Activities mới trong chatter nhân viên.
● x_employment_status, x_official_date, x_equip_grant_date được cập nhật.
● Email gửi tới nhân viên (AUT-002a).
● hr.contract nháp được tạo (AUT-002a).
 
Business Rules:
● BR-040: Tất cả Server Actions chạy với sudo() để tránh lỗi quyền; nhưng ghi log user trigger thực tế vào chatter.
● BR-041: CRON nhắc chỉ tạo Activity nếu chưa có Activity cùng loại còn open trên employee đó (tránh duplicate).
● BR-042: AUT-001b và AUT-002b chỉ Launch Plan khi Plan chưa có trạng thái đang chạy trên nhân viên.
 
UI Reference: BPMN Khối 2 (Onboarding) — nhánh "Đạt/Không đạt" sau mỗi gateway.
 
 
 
FUNC-EMP-006 — Quản lý tài sản cấp phát & thu hồi
Function ID: FUNC-EMP-006
Function Name: Quản lý tài sản nhân viên (Employee Assets)
Module: Model mới hr.employee.asset + extension hr.employee
 Actor: IT/Admin (cấp phát/thu hồi), HR (xem tổng), Nhân viên (xem tài sản đang giữ)
Purpose: Thay thế sổ tài sản 8.3 trên Lark và checklist nhúng trong sheet 2.1: quản lý tập trung việc cấp phát, theo dõi và thu hồi thiết bị, đảm bảo không thất thoát khi nhân viên nghỉ việc.
 
 
 
Preconditions:
● Danh mục tài sản đã được cấu hình (màn hình, cây máy tính, bàn phím, chuột, tai nghe, ghế, bàn, máy in...).
● Nhân viên đã có hồ sơ. Với Nhóm B: cổng tuần-2 đã Đạt (AUT-001 đã chạy).
 
Trigger:
● IT/Admin nhận Activity "Cấp thiết bị" từ AUT-001 → mở hồ sơ nhân viên → thêm bản ghi tài sản.
● HR khởi động Plan Offboarding → Activity "Thu hồi thiết bị" giao IT/Admin.
 
 
 
Main Flow — Cấp phát:
1. IT/Admin mở hồ sơ nhân viên → click Smart Button "Tài sản".
2. Bấm Tạo mới → form hr.employee.asset.
3. Chọn loại tài sản từ danh mục → nhập mã tài sản (từ sổ vật tư), ngày cấp.
4. Trạng thái tự chuyển sang assigned khi lưu.
5. Lặp lại cho mỗi thiết bị (tối thiểu: màn hình, cây máy, bàn phím, chuột).
6. Smart Button "Tài sản" cập nhật số lượng.
7. IT/Admin Mark as Done Activity "Cấp thiết bị".
 
Main Flow — Thu hồi:
1. Offboarding Plan tạo Activity "Thu hồi thiết bị" giao IT/Admin.
2. IT/Admin mở Smart Button "Tài sản" → xem danh sách state = assigned.
3. Với từng thiết bị: bấm Thu hồi → nhập ngày thu, ghi chú tình trạng → state = returned.
4. Nếu chuyển giao cho nhân viên mới: bấm Chuyển giao → chọn nhân viên nhận → state = transferred, tạo bản ghi mới trên nhân viên nhận.
5. Khi tất cả tài sản đã returned hoặc transferred → IT Mark as Done Activity.
 
Alternative Flow:
● Tài sản hư hỏng khi thu hồi: nhập ghi chú "hư hỏng", hệ thống tạo ghi chú bảo trì nhưng vẫn cho phép returned.
● Nhân viên giảng viên Online: tab tài sản vẫn tồn tại nhưng thường không có bản ghi (thiết bị họ tự sắm). Không bắt buộc.
 
Exception Flow:
● Cố Archive nhân viên khi còn tài sản state = assigned → hệ thống block với cảnh báo: "Còn [n] thiết bị chưa thu hồi: [danh sách]. Vui lòng thu hồi trước khi lưu trữ hồ sơ."
 
 
 
Validation Rules:
● grant_date ≥ x_eval_2w_date (không cấp trước khi đánh giá Đạt).
● return_date ≥ grant_date.
● Không cho xóa bản ghi tài sản — chỉ cho returned hoặc transferred.
● asset_code unique trong toàn hệ thống (một thiết bị chỉ thuộc một người tại một thời điểm).
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Nhân viên giữ
	employee_id
	Many2one hr.employee
	*
	Auto-fill từ context
	Loại tài sản
	asset_type_id
	Many2one x.asset.type
	*
	 
	Mã tài sản
	asset_code
	Char(50)
	*
	Unique toàn hệ thống
	Ngày cấp phát
	grant_date
	Date
	*
	≥ x_eval_2w_date
	Tình trạng khi cấp
	condition_in
	Selection
	*
	new/good/fair
	Trạng thái
	state
	Selection
	*
	assigned/returned/transferred; chỉ system/admin đổi
	Ngày thu hồi
	return_date
	Date
	°
	Khi state = returned; ≥ grant_date
	Nhân viên nhận (chuyển giao)
	transferred_to
	Many2one hr.employee
	°
	Khi state = transferred
	Ghi chú tình trạng khi thu
	condition_out_note
	Text
	—
	 
	 
Output:
● Danh sách tài sản trong Smart Button "Tài sản" của nhân viên.
● Báo cáo tài sản theo nhân viên / theo loại (Tree view).
● Block Archive nếu còn tài sản chưa thu hồi.
 
Business Rules:
● BR-050: Khi state chuyển từ assigned → transferred, hệ thống tự tạo bản ghi tài sản mới trên transferred_to với grant_date = return_date và state = assigned.
● BR-051: Danh mục loại tài sản chuẩn (từ Lark 8.3): Màn hình, Cây máy tính, Bàn phím, Chuột, Lót bàn phím, Tai nghe (sales / to), Ghế, Bàn, Máy in, Thùng rác.
● BR-052: Smart Button count chỉ đếm state = assigned.
 
UI Reference: Smart Button "Tài sản (n)" trên hr.employee form → list view hr.employee.asset.
 
 
 
FUNC-EMP-007 — Lịch sử thăng tiến & lương (Promotion Snapshot)
Function ID: FUNC-EMP-007
Function Name: Lịch sử thăng tiến và lương theo mốc
Module: Model mới hr.promotion.history + extension hr.employee
 Actor: HR Manager (tạo/sửa), Kế toán (đọc), Nhân viên (đọc phần của mình)
Purpose: Lưu lịch sử snapshot thay đổi chức vụ, mức lương và phụ cấp theo từng mốc — thay thế sheet 2.4 Lark, đảm bảo audit trail đầy đủ cho quyết toán lương.
 
 
 
Preconditions:
● Nhân viên đang có hồ sơ hoạt động.
● HR có quyết định thăng tiến / điều chỉnh lương được BGĐ duyệt.
 
Trigger:
● HR nhận quyết định điều chuyển/thăng tiến → ghi nhận vào hệ thống.
● Kết thúc mỗi tháng: tùy chọn snapshot tự động (CRON monthly).
 
 
 
Main Flow:
1. HR mở hồ sơ nhân viên → Smart Button "Thăng tiến (n)".
2. Bấm Tạo mới → form hr.promotion.history.
3. Nhập: Ngày có hiệu lực, Chức vụ mới, Phòng ban mới (nếu thay đổi).
4. Nhập mức lương cơ bản mới, các khoản phụ cấp (text hoặc structured nếu tích hợp Payroll).
5. Nhập Lý do thăng tiến, Số quyết định, người phê duyệt.
6. Lưu → hệ thống tự cập nhật job_id, department_id, wage trên hr.employee theo giá trị mới.
7. Ghi log chatter: "📈 Cập nhật chức vụ: [Chức vụ cũ] → [Chức vụ mới] từ [Ngày]."
 
Alternative Flow:
● Điều chỉnh lương mà không thay đổi chức vụ: from_job_id = to_job_id, chỉ thay wage.
● Điều chuyển cơ sở: nhập cơ sở mới vào work_location_id (field chuẩn Odoo).
 
Exception Flow:
● Ngày hiệu lực trùng với bản ghi cũ của cùng nhân viên → cảnh báo "Đã có bản ghi thăng tiến ngày [X]. Xác nhận ghi đè?"
 
 
 
Validation Rules:
● date_effective ≤ today + 30 ngày (không nhập quá xa tương lai).
● to_wage > 0.
● Bắt buộc một trong hai: to_job_id ≠ from_job_id HOẶC to_wage ≠ from_wage.
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Nhân viên
	employee_id
	Many2one hr.employee
	*
	Auto-fill
	Ngày có hiệu lực
	date_effective
	Date
	*
	≤ today+30
	Chức vụ trước
	from_job_id
	Many2one hr.job
	*
	Auto-fill từ employee hiện tại
	Chức vụ mới
	to_job_id
	Many2one hr.job
	*
	 
	Phòng ban mới
	to_department_id
	Many2one hr.department
	—
	Nếu khác phòng ban hiện tại
	Lương cũ
	from_wage
	Float
	*
	Auto-fill từ contract hiện tại
	Lương mới
	to_wage
	Float
	*
	> 0
	Phụ cấp (tóm tắt)
	allowance_note
	Text
	—
	VD: "PC điện thoại 500k; PC xăng xe 300k"
	Lý do / Căn cứ
	reason
	Text
	°
	Bắt buộc nếu wage thay đổi
	Số quyết định
	decision_ref
	Char(50)
	—
	 
	Người phê duyệt
	approved_by
	Many2one res.users
	*
	 
	 
Output:
● List view lịch sử tất cả thay đổi, sắp xếp mới nhất lên đầu.
● Smart Button "Thăng tiến (n)" hiển thị số bản ghi.
● Sau khi lưu: hr.employee.job_id, department_id được cập nhật tự động.
 
Business Rules:
● BR-060: Không được xóa bản ghi hr.promotion.history — chỉ được sửa trong 24h đầu sau khi tạo.
● BR-061: Sau 24h, chỉ HR Director mới được sửa (audit log).
● BR-062: CRON tháng (tùy chọn): ngày 1 hằng tháng chụp snapshot trạng thái hiện tại của nhân viên (chức vụ + lương) nếu không có bản ghi trong tháng đó.
 
UI Reference: Smart Button "Thăng tiến" trên hr.employee → list hr.promotion.history.
 
 
 
FUNC-EMP-008 — Đánh giá thử giảng & Ma trận kỹ năng giảng viên
Function ID: FUNC-EMP-008
Function Name: Đánh giá thử giảng và ma trận kỹ năng Giảng viên (Nhóm A)
Module: Employees — Tab Resumé & Skills + custom fields
Actor: Academic/TBP Đào tạo (điền kết quả thử giảng), HR (xem), Giảng viên (xem kỹ năng của mình)
Purpose: Đưa kết quả thử giảng vào hồ sơ nhân viên thay vì Excel rời; số hóa ma trận kỹ năng tiếng Trung (chứng chỉ, trình độ) để phân công giảng dạy và cảnh báo hết hạn.
 
 
 
Preconditions:
● Nhân viên là Giảng viên: x_work_form = online hoặc x_employment_type ∈ {thinhgiang, parttime, ctv}.
● Skill Types đã được cấu hình: "Tiếng Trung", "Sư phạm", "Kỹ năng bổ trợ".
 
Trigger:
● Onboarding Plan GV tạo Activity "Dự giờ thử giảng" giao TBP Đào tạo.
● TBP hoàn thành dự giờ → điền kết quả vào hồ sơ.
 
 
 
Main Flow — Đánh giá thử giảng:
1. TBP mở hồ sơ GV → xem section "Đánh giá thử giảng" trong Tab Work Information.
2. TBP điền: ngày thử giảng, lớp thử giảng, điểm phương pháp (1-10), điểm chuyên môn (1-10), nhận xét tự do.
3. TBP chọn kết quả: Đạt / Không đạt.
4. Lưu → hệ thống ghi vào chatter và tạo Activity nhắc HR ký HĐ thỉnh giảng (nếu Đạt).
5. Nếu Không đạt: hệ thống tạo Activity nhắc HR thông báo GV (không khởi động Plan offboarding vì GV chưa có HĐ ký chính thức).
 
Main Flow — Nhập ma trận kỹ năng:
1. TBP / HR mở Tab Resumé & Skills → phần Skills.
2. Thêm skill thuộc Skill Type "Tiếng Trung": chọn Skill (HSK 1 → HSK 6 / HSKK Sơ cấp → Cao cấp / TOCFL A2 → C2) → chọn Level.
3. Nhập ngày cấp chứng chỉ (x_cert_date) và ngày hết hạn (x_cert_expiry).
4. Tương tự cho "Sư phạm": Chứng chỉ Nghiệp vụ Sư phạm, Phương pháp Pinyin...
5. Lưu.
 
Alternative Flow:
● GV tự cập nhật chứng chỉ qua Portal (upload ảnh scan → HR phê duyệt thủ công trước khi hệ thống ghi nhận verified = True).
● Gia hạn chứng chỉ: cập nhật x_cert_expiry mới; bản ghi cũ không xóa (lưu lịch sử).
 
Exception Flow:
● TBP điền điểm < 5 (thang 10) nhưng chọn Đạt → warning "Điểm trung bình < 5, xác nhận Đạt?"
● x_cert_expiry < today → badge "Hết hạn" màu đỏ ngay khi nhập, không block lưu.
 
 
 
Validation Rules:
● x_trial_score_method và x_trial_score_content ∈ [1, 10].
● x_trial_lesson_date ≤ today.
● x_cert_expiry > x_cert_date.
 
Input Fields:
 
Field
	Model field
	Type
	Required
	Rule
	Ngày thử giảng
	x_trial_lesson_date
	Date
	°
	Nhóm A; ≤ today
	Lớp thử giảng
	x_trial_lesson_class
	Char(50)
	—
	 
	Điểm phương pháp
	x_trial_score_method
	Float
	°
	[1, 10]; 1 decimal
	Điểm chuyên môn
	x_trial_score_content
	Float
	°
	[1, 10]; 1 decimal
	Nhận xét thử giảng
	x_trial_lesson_note
	Text
	°
	Bắt buộc nếu Không đạt
	Kết quả thử giảng
	x_trial_lesson_result
	Selection
	°
	draft/pass/fail
	Skill (trên hr.employee.skill)
	skill_id
	Many2one hr.skill
	*
	Từ skill type Tiếng Trung / Sư phạm
	Ngày cấp chứng chỉ
	x_cert_date
	Date
	°
	Nếu có chứng chỉ
	Ngày hết hạn chứng chỉ
	x_cert_expiry
	Date
	°
	Nếu có chứng chỉ; > x_cert_date
	Đã xác minh
	x_cert_verified
	Boolean
	—
	HR set sau khi kiểm tra bản gốc
	 
Output:
● Kết quả thử giảng hiện trên hồ sơ và chatter.
● Ma trận kỹ năng visible trong Tab Resumé & Skills với badge hết hạn (nếu có).
● Smart Button "Chứng chỉ (n)" đếm các kỹ năng có x_cert_expiry trong vòng 60 ngày.
 
Business Rules:
● BR-070: Skill Types chuẩn phải được tạo sẵn khi cài module: "Tiếng Trung" (levels: HSK 1..6, HSKK Sơ/Trung/Cao cấp, TOCFL A2/B1/B2/C1/C2), "Sư phạm" (levels: Chứng chỉ NVSP, Phương pháp Pinyin, Giảng Online), "Kỹ năng bổ trợ".
● BR-071: Một GV CÓ THỂ có nhiều loại chứng chỉ cùng type (ví dụ: HSK 5 cũ hết hạn + HSK 6 mới).
● BR-072: x_cert_verified = False → skill hiển thị badge "Chờ xác minh" màu vàng.
 
UI Reference: Tab "Resumé & Skills" chuẩn Odoo; thêm section "Đánh giá thử giảng" trong Tab Work Information.
 
 
 
FUNC-EMP-009 — CRON cảnh báo chứng chỉ sắp hết hạn
Function ID: FUNC-EMP-009
Function Name: Scheduled Action cảnh báo chứng chỉ hết hạn
Module: ir.cron + hr.employee.skill
 Actor: Hệ thống Odoo (tự chạy), HR (nhận cảnh báo), Giảng viên (nhận email nhắc)
Purpose: Tự động phát hiện và cảnh báo chứng chỉ sắp hết hạn trước 60 ngày — thay thế việc HR kiểm tra thủ công từng hồ sơ, ngăn tình huống GV dạy với chứng chỉ không còn hợp lệ.
 
 
 
Preconditions:
● Chứng chỉ đã được nhập vào Tab Resumé & Skills với x_cert_expiry có giá trị.
● Nhân viên còn active (active = True, x_employment_status ≠ exiting/archived).
 
Trigger: ir.cron chạy hằng ngày lúc 7:00 SA (giờ VN, timezone Asia/Ho_Chi_Minh).
 
 
 
Main Flow:
1. CRON query: hr.employee.skill WHERE x_cert_expiry IS NOT NULL AND x_cert_expiry <= today + 60 AND x_cert_expiry >= today AND employee_id.active = True.
2. Nhóm kết quả theo employee_id.
3. Với mỗi nhân viên có chứng chỉ sắp hết:
a. Kiểm tra đã có Activity "Cảnh báo chứng chỉ" open trong 7 ngày qua chưa → nếu có, bỏ qua (tránh spam).
b. Tạo Activity type "Cảnh báo chứng chỉ" trên hồ sơ nhân viên, giao HR Manager, deadline = x_cert_expiry - 30 ngày.
c. Gửi email cho GV (email công ty) với danh sách chứng chỉ sắp hết hạn + hướng dẫn gia hạn.
4. Query thứ hai: x_cert_expiry < today AND employee_id.active = True → chứng chỉ đã hết hạn nhưng GV vẫn active.
5. Với mỗi trường hợp hết hạn: tạo Activity ưu tiên cao (màu đỏ) giao HR Manager; ghi chú "⚠️ Chứng chỉ ĐÃ HẾT HẠN."
6. Ghi log CRON: số GV được cảnh báo, số chứng chỉ sắp hết, số đã hết.
 
Alternative Flow:
● x_cert_expiry = NULL (không có ngày hết hạn): bỏ qua record này (chứng chỉ vĩnh viễn / không rõ hạn).
● GV đã gia hạn chứng chỉ (cập nhật x_cert_expiry mới): Activity cũ vẫn tồn tại; HR tự đóng sau khi kiểm tra.
 
Exception Flow:
● Email server down → bỏ qua email, vẫn tạo Activity (không fail toàn bộ CRON).
● GV không có email công ty → gửi email cho HR Manager thay thế.
 
 
 
Validation Rules:
● CRON không chạy nếu không có record thỏa điều kiện (không tạo email trống).
● Interval tối thiểu giữa 2 Activity cùng loại trên cùng employee: 7 ngày.
 
Input Fields: Không có input trực tiếp (đọc từ hr.employee.skill.x_cert_expiry).
 
Output:
● Activities trong chatter nhân viên (badge màu cam = sắp hết / đỏ = đã hết).
● Email tới GV và HR Manager.
● Smart Button "Chứng chỉ (n)" highlight màu cam/đỏ nếu có cảnh báo.
● Log CRON trong ir.logging.
 
Business Rules:
● BR-090: Ngưỡng cảnh báo mặc định: 60 ngày trước khi hết hạn. Có thể cấu hình qua ir.config_parameter hoc_ba.cert_alert_days (không hardcode).
● BR-091: Email template cảnh báo phải liệt kê: tên chứng chỉ, ngày hết hạn, số ngày còn lại, link hướng dẫn gia hạn.
● BR-092: Chỉ cảnh báo chứng chỉ có x_cert_verified = True (đã xác minh). Chứng chỉ chờ xác minh không tính.
● BR-093: CRON log kết quả vào ir.logging với level info; nếu có exception ghi error và gửi email tới IT Admin.
 
UI Reference: Smart Button "Chứng chỉ (n sắp hết hạn)" trên hr.employee form; badge màu trên skill row trong Tab Resumé & Skills. BPMN Khối 3 (Lifecycle) — node "CRON cảnh báo chứng chỉ".
 
 
 
PHỤ LỤC — Tóm tắt Custom Fields
 
Model
	Field name
	Type
	Dùng cho
	hr.employee
	x_employee_code
	Char
	Mã NS
	hr.employee
	x_work_form
	Selection
	Hình thức
	hr.employee
	x_employment_status
	Selection
	Tình trạng
	hr.employee
	x_position_type
	Selection
	Loại vị trí
	hr.employee
	x_official_months
	Float (computed)
	Số tháng CT
	hr.employee
	x_id_date_issue
	Date
	Ngày cấp CCCD
	hr.employee
	x_id_place_issue
	Char
	Nơi cấp CCCD
	hr.employee
	x_pit_code
	Char
	MST TNCN
	hr.employee
	x_social_insurance_no
	Char
	Số BHXH
	hr.employee
	x_health_insurance_no
	Char
	Số BHYT
	hr.employee
	x_health_care_place
	Char
	Nơi KCB
	hr.employee
	x_permanent_state_id
	Many2one
	Tỉnh thường trú
	hr.employee
	x_permanent_ward
	Char
	Phường thường trú
	hr.employee
	x_permanent_street
	Char
	Đường thường trú
	hr.employee
	x_current_same_as_permanent
	Boolean
	Địa chỉ tạm trú
	hr.employee
	x_current_state_id
	Many2one
	Tỉnh tạm trú
	hr.employee
	x_current_ward
	Char
	Phường tạm trú
	hr.employee
	x_current_street
	Char
	Đường tạm trú
	hr.employee
	x_probation_start
	Date
	Ngày TV
	hr.employee
	x_eval_2w_due
	Date
	Hạn ĐG tuần-2
	hr.employee
	x_eval_2w_result
	Selection
	KQ ĐG tuần-2
	hr.employee
	x_eval_2w_date
	Date
	Ngày ĐG tuần-2
	hr.employee
	x_eval_2w_evaluator_id
	Many2one
	Người ĐG tuần-2
	hr.employee
	x_eval_2w_note
	Text
	Ghi chú tuần-2
	hr.employee
	x_equip_grant_date
	Date
	Ngày cấp thiết bị
	hr.employee
	x_eval_2m_due
	Date
	Hạn ĐG tháng-2
	hr.employee
	x_eval_2m_result
	Selection
	KQ ĐG tháng-2
	hr.employee
	x_eval_2m_date
	Date
	Ngày ĐG tháng-2
	hr.employee
	x_eval_2m_evaluator_id
	Many2one
	Người ĐG tháng-2
	hr.employee
	x_eval_2m_note
	Text
	Ghi chú tháng-2
	hr.employee
	x_official_date
	Date
	Ngày chính thức
	hr.employee
	x_skip_auto_trigger
	Boolean
	Bỏ qua AUT
	hr.employee
	x_trial_lesson_date
	Date
	Ngày thử giảng
	hr.employee
	x_trial_lesson_class
	Char
	Lớp thử giảng
	hr.employee
	x_trial_score_method
	Float
	Điểm PP giảng
	hr.employee
	x_trial_score_content
	Float
	Điểm chuyên môn
	hr.employee
	x_trial_lesson_note
	Text
	Nhận xét thử giảng
	hr.employee
	x_trial_lesson_result
	Selection
	KQ thử giảng
	hr.employee.skill
	x_cert_date
	Date
	Ngày cấp CC
	hr.employee.skill
	x_cert_expiry
	Date
	Ngày hết hạn CC
	hr.employee.skill
	x_cert_verified
	Boolean
	Đã xác minh
	hr.employee.dependent
	(model mới)
	—
	Người phụ thuộc
	hr.employee.asset
	(model mới)
	—
	Tài sản NV
	hr.promotion.history
	(model mới)
	—
	Lịch sử thăng tiến
	 


Chap 5 6 - attendance
CHAPTER 5 — CONFIGURATION SPECIFICATION
Phần này mô tả cấu hình cụ thể cho Module Attendance (Module 3) trong hệ thống Odoo 19 triển khai tại Trung tâm Học Bá. Mỗi mục cấu hình ánh xạ trực tiếp đến gap analysis trong Chapter 4.


5.3 Attendance Configuration


5.3.1 Work Schedules
Configuration Path: Employees → Configuration → Working Schedules


ID
	Schedule Name
	Type
	Working Hours
	Configuration Details
	CFG-ATT-SCH-01
	Office Standard Hours
	Fixed Hours
	Mon–Fri 08:30–17:30
	Morning: 08:30–12:00; Afternoon: 13:00–17:30. Late Tolerance: 15 min (check-in trước 08:45 không bị đánh late). Activate "Count Extra Hours" sau 18:00. Lunch break 60 min excluded. Áp dụng: HR, Marketing, Finance, Admin, Sales.
	CFG-ATT-SCH-02
	Online Teacher Flexible
	Flexible Hours
	Variable (session-based)
	Weekly hours quota = 0.0 hrs — tắt hoàn toàn cơ chế scan late/early của Odoo. Giờ làm thực tế được import tự động từ CUS-ATT-001 khi session hoàn thành. Áp dụng: Full-time Teacher, Part-time Instructor, Teaching Assistant.
	CFG-ATT-SCH-03
	Collaborator Shift Schedule
	Shift-Based
	Weekly registered shifts
	Shift blocks đăng ký theo tuần qua CUS-ATT-003. Hệ thống reconcile check-in/out với khung shift đã đăng ký. Tolerance ±30 phút trước khi raise shift_exception flag. Áp dụng: Collaborator (CTV), Part-time Support.
	CFG-ATT-SCH-04
	Sales Rotating Shifts
	Scheduled Shifts
	Sáng / Chiều / Tối
	Ca sáng: 08:00–12:00; Ca chiều: 13:00–17:00; Ca tối: 17:30–21:00. Phân ca do Sales Manager assign hàng tuần. OT tính cho giờ vượt quá cuối ca được assign. Áp dụng: Admissions Consultant.
	

5.3.2 Shift Rules — Work Entry Types
Configuration Path: Payroll → Configuration → Work Entry Types
Mỗi Work Entry Type xác định cách tính lương cho từng loại giờ làm. Attendance module tạo work entries tương ứng; Payroll module đọc để tính lương.


Rule ID
	Rule Name
	Work Entry Code
	Applies To
	Logic / Multiplier
	CFG-ATT-SR-01
	Standard Work Hours
	WORK100
	Office, Sales, Admin
	Rate 1.0×. Giờ trong khung làm việc hợp đồng. Input cơ bản cho payroll (BASE rule). Được tạo từ check-in/check-out thông thường.
	CFG-ATT-SR-02
	Teaching Hours
	WORK200
	Teachers / TAs
	Rate = x_teaching_hourly_rate (per contract). Tự động tạo bởi CUS-ATT-001 khi academic session hoàn thành. Input duy nhất cho TEACH_HOURS rule trong STR-02 (Teacher Payroll).
	CFG-ATT-SR-03
	OT — Weekday
	WORK110_OT
	Office, Sales, Admin
	Rate 1.5×. Trigger khi check-out sau 18:00 ngày thường (T2–T6). Tính từ phút vượt 17:30 trở đi sau khi đủ 8 giờ làm.
	CFG-ATT-SR-04
	OT — Weekend
	WORK110_OT_WE
	All staff
	Rate 2.0×. Áp dụng khi có attendance hoặc teaching session vào Thứ 7 hoặc Chủ Nhật ngoài lịch tiêu chuẩn.
	CFG-ATT-SR-05
	OT — Public Holiday
	WORK110_OT_PH
	All staff incl. Teachers
	Rate 3.0×. Theo Điều 98 Bộ Luật Lao Động. Trigger khi attendance hoặc teaching session rơi vào ngày lễ đã cấu hình trong Public Holidays.
	CFG-ATT-SR-06
	WFH / Off-site Work
	WORK100_WFH
	Office Staff (WFH approved)
	Rate 1.0×. Gắn tag bởi CUS-ATT-002 khi nhân viên check-in ngoài vùng IP/GPS được phép và đã chọn lý do WFH hợp lệ. Manager phải confirm trong 24h.
	CFG-ATT-SR-07
	Collaborator Shift
	WORK100_CTV
	Collaborators (CTV)
	Rate theo thỏa thuận hợp đồng. Validate bởi CUS-ATT-003 — giờ ngoài shift đã đăng ký (vượt tolerance ±30 phút) bị flag exception và không tính vào giờ được trả lương.
	

5.3.3 Late & Absence Policies
Configuration Path: Employees → Configuration → Working Schedules (per schedule) + Attendance → Settings


Policy ID
	Policy Name
	Applies To
	Threshold / Trigger
	System Action
	CFG-ATT-LP-01
	Late Tolerance Buffer
	Office Staff, Sales
	Check-in 08:30–08:45
	Không raise late flag. Attendance ghi nhận on-time. Payroll không bị ảnh hưởng.
	CFG-ATT-LP-02
	Late Arrival Warning
	Office Staff, Sales
	Check-in 08:45–09:30 (>15 phút muộn)
	Stamp "Late In" label trên bản ghi attendance. HR nhận daily exception report. Manager được notify qua chatter.
	CFG-ATT-LP-03
	Severe Late — Half Day
	Office Staff
	Check-in sau 09:30 không có phép
	Flag "Late – Half Day". HR review và có thể apply khấu trừ 0.5 ngày lương qua LEAVE120 work entry trong payroll.
	CFG-ATT-LP-04
	Early Leave Detection
	Office Staff, Sales
	Check-out trước 17:15 (>15 phút sớm)
	Stamp "Early Out" label. Tính vào tổng giờ ngày. Nếu tổng < 8 giờ → flag deficit cho HR review.
	CFG-ATT-LP-05
	Minimum 8-Hour Enforcement
	Office Staff (Full-time)
	Worked hours < 8.0 giờ/ngày làm việc
	Flag deficit hours trên bản ghi. Tích lũy > 4 giờ/tháng → C&B Specialist nhận đề xuất khấu trừ tự động.
	CFG-ATT-LP-06
	Absent Without Record (AWR)
	Toàn bộ employee types
	Không có bản ghi check-in ngày làm việc
	Hệ thống auto-tạo LEAVE120 (Unpaid Leave) work entry dạng draft. HR confirm hoặc override. Nếu confirm → khấu trừ 1 ngày lương trong payroll.
	CFG-ATT-LP-07
	Teacher Session Absence
	Teachers / TAs
	Academic session = "Cancelled by Teacher" không có phép được duyệt
	Tạo ATT_EXCEPTION record. Không tạo WORK200 work entry. Penalty rule áp dụng trong payroll (x_cancellation_penalty per session trong contract).
	CFG-ATT-LP-08
	CTV Shift Deviation
	Collaborators (CTV)
	Check-in/out lệch > 30 phút so với shift đã đăng ký
	CUS-ATT-003 raise shift_exception flag. Giờ ngoài shift window bị loại khỏi giờ trả lương. Line Manager nhận notification ngay lập tức.
	



________________


CHAPTER 6 — FUNCTIONAL SPECIFICATION
Chương này mô tả chi tiết các chức năng custom-developed cho Module Attendance (Module 3). Tất cả functions dưới đây ánh xạ trực tiếp đến các Customization Gap (CUS-ATT-001, CUS-ATT-002, CUS-ATT-003) đã xác định trong Chapter 4.


Function ID
	Function Name
	Custom Module
	Actor
	Mapped Gap
	ATT-F-001
	Auto Check-In từ Session Start
	hb_attendance_academic
	System / Academic Coordinator
	CUS-ATT-001
	ATT-F-002
	Auto Check-Out từ Session Completion
	hb_attendance_academic
	System / Academic Coordinator
	CUS-ATT-001
	ATT-F-003
	GPS & IP Validation tại Check-In
	hb_attendance_geofence
	Employee (Office/Sales)
	CUS-ATT-002
	ATT-F-004
	Location Config Management
	hb_attendance_geofence
	HR Manager
	CUS-ATT-002
	ATT-F-005
	Weekly Shift Registration (CTV)
	hb_attendance_ctv_shift
	Collaborator
	CUS-ATT-003
	ATT-F-006
	Line Manager Shift Approval
	hb_attendance_ctv_shift
	Line Manager
	CUS-ATT-003
	ATT-F-007
	Real-time Shift Deviation Detection
	hb_attendance_ctv_shift
	System / Collaborator
	CUS-ATT-003
	





6.1 CUS-ATT-001 — Automated Attendance from Academic Sessions
Standard Odoo yêu cầu nhân viên tương tác thủ công (bấm nút hoặc quét mã) để tạo dữ liệu chấm công. Giải pháp này tự động hóa hoàn toàn quá trình đó cho khối Teachers dựa trên vòng đời của academic session.


ATT-F-001 — Auto Check-In Generation upon Session Start


ATT-F-001  ·  Auto Check-In Generation upon Session Start
	Function ID
	ATT-F-001
	Function Name
	Auto Check-In Generation upon Session Start
	Module
	Attendance (Custom: hb_attendance_academic)
	Actor
	System (Automated Event Listener) | Khởi tạo bởi: Academic Coordinator
	Purpose
	Tự động tạo bản ghi hr.attendance check-in cho giảng viên được phân công khi academic session chuyển sang trạng thái "In Progress", loại bỏ hoàn toàn thao tác check-in thủ công và đảm bảo timestamp chính xác lấy trực tiếp từ hệ thống quản lý lớp học.
	Preconditions
	* Bản ghi academic.session tồn tại với employee_id (giảng viên được phân công)
* Session đang chuyển trạng thái từ "Scheduled" → "In Progress"
* Lịch làm việc của giảng viên đã cấu hình là "Online Teacher Flexible Schedule" (CFG-ATT-SCH-02)
* Không tồn tại bản ghi hr.attendance đang mở (check_out = NULL) cho cùng nhân viên trong cùng ngày
	Trigger
	Academic Coordinator ghi status = "in_progress" trên academic.session (bấm "Start Session" hoặc cron tự động kích hoạt khi đến start_time).
	Main Flow
	1. Academic Coordinator mở bản ghi session và click "Start Session" — hoặc scheduled cron trigger khi session.scheduled_start_time được đến.
2. Hệ thống ghi academic.session.status = "in_progress" và actual_start_time = datetime.now().
3. ORM @api.model write override (Event Listener) phát hiện thay đổi status trên model academic.session.
4. Hệ thống query hr.employee theo employee_id được gán, validate employee đang active và có Flexible Schedule.
5. Deduplication guard: kiểm tra bản ghi hr.attendance đang mở (check_out = NULL) cho cùng employee, cùng ngày — nếu đã tồn tại, không tạo duplicate.
6. Hệ thống tạo hr.attendance mới: employee_id, check_in = actual_start_time, work_type = WORK200, source_session_id = session.id, attendance_origin = "auto_academic".
7. Ghi chú tự động lên chatter của session: "Attendance check-in auto-generated cho [Tên GV] lúc [HH:MM]."
8. hr.attendance được lưu với state = "open" (chờ check-out).
	Alternative Flow
	* Giảng viên đang trong trạng thái nghỉ phép được duyệt: Hệ thống phát hiện LEAVE work entry. Attendance KHÔNG được tạo. Academic Coordinator nhận cảnh báo: "Teacher [Tên] có phép nghỉ ngày này. Vui lòng phân công lại trước khi bắt đầu."
* Đã tồn tại bản ghi attendance mở: Deduplication guard trigger — không tạo mới. Hệ thống log cảnh báo vào HR queue: "Duplicate attendance attempt suppressed cho [Tên] trên session [Code]."
* actual_start_time trễ hơn 30 phút so với scheduled_start_time: Session bị flag "Late Start". Attendance vẫn được tạo nhưng hr.attendance mang x_late_start = True cho HR visibility.
	Exception Flow
	* academic.session không có employee_id: Hệ thống raise ValidationError, block status change: "Không thể bắt đầu session — chưa phân công giảng viên."
* Ghi hr.attendance thất bại (lỗi DB constraint): Hệ thống log vào system.log, gửi email alert đến HR mailbox. Session tiếp tục nhưng x_attendance_sync_error = True trên session record.
* Employee account bị archived/inactive: Hệ thống raise warning, block auto-generation, notify Academic Manager.
	Validation Rules
	* Deduplication: Chỉ cho phép một bản ghi attendance mở (check_out = NULL) mỗi nhân viên mỗi ngày.
* employee_type phải thuộc ["full_time_teacher", "part_time_instructor", "teaching_assistant"] để gán WORK200.
* actual_start_time phải nằm trong ±4 giờ so với scheduled_start_time để tránh data corruption từ stale sessions.
* attendance_origin = "auto_academic" cho tất cả auto-generated records — phân biệt với manual kiosk check-in.
	Input Fields
	

Field
	Type
	Required
	Rule
	academic.session.id
	Many2one
	Yes
	Phải tham chiếu đến session đang active
	academic.session.employee_id
	Many2one (hr.employee)
	Yes
	Employee active, có Flexible Schedule
	academic.session.actual_start_time
	Datetime
	Yes
	Capture tại thời điểm status write, không được future-dated
	academic.session.status
	Selection
	Yes
	Phải chuyển từ "scheduled" → "in_progress"
	

	Output
	Một bản ghi hr.attendance được tạo với check_in timestamp, WORK200 work type và traceable source_session_id. Chatter note được thêm vào session record.
	Business Rules
	* BR-ATT-001: Auto-generated attendance records là read-only với employees. Chỉ HR Manager hoặc System Administrator mới được override check_in timestamp, kèm mandatory justification note.
* BR-ATT-002: Auto-generated records tag attendance_origin = "auto_academic", có thể filter riêng trong báo cáo để audit.
* BR-ATT-003: Một giảng viên có thể có nhiều bản ghi WORK200 trong một ngày (nhiều session). Mỗi session tạo một hr.attendance record độc lập — không merge thành một block liên tục.
* BR-ATT-004: Nếu session bị xóa hoặc cancelled sau khi auto check-in được tạo, hr.attendance liên kết bị chuyển sang state "Exception" để HR review — KHÔNG tự động xóa.
	UI Reference
	Academic Session Form > "Start Session" button | HR > Attendance > List View (filter: origin=auto_academic) | HR > Attendance > Exception Queue.
	

ATT-F-002 — Auto Check-Out Generation upon Session Completion


ATT-F-002  ·  Auto Check-Out Generation upon Session Completion
	Function ID
	ATT-F-002
	Function Name
	Auto Check-Out Generation upon Session Completion
	Module
	Attendance (Custom: hb_attendance_academic)
	Actor
	System (Automated) | Khởi tạo bởi: Academic Coordinator hoàn thành session
	Purpose
	Tự động đóng bản ghi hr.attendance của giảng viên khi academic session được đánh dấu "Completed", capture thời gian kết thúc thực tế làm check-out timestamp và tạo WORK200 work entry cho payroll — thay thế hoàn toàn quy trình đối chiếu thủ công Google Forms + Zoom logs.
	Preconditions
	* Bản ghi hr.attendance đang mở (check_in set, check_out = NULL) tồn tại, linked qua source_session_id
* Academic session đang chuyển sang trạng thái "Completed"
* actual_end_time đã được ghi vào academic.session record
	Trigger
	Academic Coordinator click "Complete Session" và nhập actual_end_time. Hệ thống ghi status = "completed".
	Main Flow
	9. Academic Coordinator click "Complete Session" trên session record. Hệ thống prompt nhập actual_end_time và class summary.
10. Hệ thống ghi status = "completed", actual_end_time = input, session_duration = end - start.
11. Hệ thống query hr.attendance tìm bản ghi mở matching (employee_id = session.employee_id, source_session_id = session.id, check_out = NULL).
12. Hệ thống ghi hr.attendance.check_out = session.actual_end_time.
13. Tính worked_hours = check_out - check_in (decimal hours).
14. Tạo WORK200 work entry (hr.work.entry): employee_id, date_start = check_in, date_stop = check_out, work_entry_type = WORK200, state = validated.
15. Cập nhật session: x_attendance_synced = True, x_work_entry_id = work entry ID vừa tạo.
16. Chatter note trên session: "Check-out auto-generated cho [Tên GV]. Duration: [X.X hrs]. Work entry WORK200 đã tạo."
	Alternative Flow
	* Session duration < minimum contract threshold (< 1 giờ): Tạo hr.attendance bình thường nhưng work entry được flag "Short Session" — cần Academic Manager confirm trước khi đạt "validated" state.
* actual_end_time sớm hơn actual_start_time (lỗi nhập liệu): ValidationError: "Session end time không thể trước start time."
* Giảng viên yêu cầu chỉnh sửa thời gian trong vòng 24h: Submit x_attendance_correction_request. Academic Manager approve → HR adjust record. Log chỉnh sửa kèm lý do trong chatter.
	Exception Flow
	* Không tìm thấy hr.attendance mở cho session: Tạo "Orphan Session" warning trong HR Exception Queue. HR tạo thủ công với attendance_origin = "manual_correction".
* Session completed > 12 giờ sau actual_start_time: Flag record cho HR review — khả năng có data quality issue.
* WORK200 work entry creation thất bại: Log lỗi, gửi HR email alert. Session ở trạng thái "pending sync" hiển thị trong Academic Sync Dashboard.
	Validation Rules
	* session_duration phải từ 0.5 giờ (30 phút tối thiểu) đến 6 giờ (một session liên tục tối đa) — ngoài range này trigger HR review flag.
* check_out phải sau check_in ít nhất 30 phút.
* WORK200 work entry phải nằm trong payroll period đang mở để được đưa vào batch payslip tiếp theo.
* Một work entry WORK200 được tạo cho mỗi session completion — không consolidate nhiều session.
	Input Fields
	

Field
	Type
	Required
	Rule
	academic.session.actual_end_time
	Datetime
	Yes
	Phải sau actual_start_time ít nhất 30 phút
	academic.session.status
	Selection
	Yes
	Phải = "completed"
	academic.session.session_notes
	Text
	No
	Optional summary — log trên work entry để audit
	academic.session.student_attendance_count
	Integer
	No
	Lưu trên work entry cho Academic reporting
	

	Output
	hr.attendance record đóng với check_out timestamp. hr.work.entry WORK200 tạo ở state "validated". Session flag x_attendance_synced = True.
	Business Rules
	* BR-ATT-005: Auto-generated WORK200 work entries là nguồn dữ liệu duy nhất để tính lương giảng viên (TEACH_HOURS rule). Quy trình đối chiếu Google Forms + Zoom logs thủ công được xóa bỏ hoàn toàn.
* BR-ATT-006: WORK200 work entries bị lock khi payslip của kỳ liên quan chuyển sang state "Done". Không cho phép chỉnh sửa ngược trừ khi HR Manager reset payslip kèm justification bắt buộc.
* BR-ATT-007: Session bị cancel sau khi check-out đã tạo → WORK200 work entry chuyển sang "conflict" state. Payslip batch computation bị block cho đến khi HR resolve conflict.
	UI Reference
	Academic Session Form > "Complete Session" button | Payroll > Work Entries > Filter: Type=WORK200 | HR > Attendance > Academic Sync Dashboard (custom view).
	





6.2 CUS-ATT-002 — GPS & IP-Lock Attendance Perimeter Control
Standard Odoo chỉ hỗ trợ IP lock cho màn hình Kiosk dùng chung; giao diện web cá nhân cho phép chấm công từ bất kỳ mạng nào. Giải pháp này mở rộng nút Check-In/Check-Out để validate vị trí GPS và IP ngay tại thời điểm chấm công.


ATT-F-003 — GPS & IP Validation tại Check-In


ATT-F-003  ·  GPS & IP Validation tại Check-In (Perimeter Enforcement)
	Function ID
	ATT-F-003
	Function Name
	GPS & IP Validation tại Check-In (Perimeter Enforcement)
	Module
	Attendance (Custom: hb_attendance_geofence)
	Actor
	Employee (Office Staff, Sales Consultants) | System validate ngầm
	Purpose
	Xác thực tính xác thực của vị trí chấm công bằng cách validate IP address và/hoặc tọa độ GPS của thiết bị nhân viên so với ranh giới đã cấu hình ngay khi check-in, ngăn chặn gian lận chấm công từ xa và đảm bảo trách nhiệm hiện diện.
	Preconditions
	* Nhân viên đã đăng nhập Odoo Web hoặc Mobile App
* IP whitelist và/hoặc GPS geofence coordinates đã được cấu hình trong hb.attendance.location.config
* Location Services của trình duyệt/thiết bị đã được bật (cho GPS validation)
* Working schedule của nhân viên KHÔNG phải "Online Teacher Flexible" (giảng viên không áp dụng GPS check)
	Trigger
	Nhân viên click nút "Check In" trên Odoo portal hoặc mobile app.
	Main Flow
	17. Nhân viên click "Check In" trên Odoo portal/mobile.
18. JavaScript layer (navigator.geolocation.getCurrentPosition) async request tọa độ GPS của thiết bị. Đồng thời, backend đọc IP address từ HTTP request headers.
19. Hệ thống query hb.attendance.location.config lấy tọa độ trung tâm (lat, lng, radius_meters) và allowed IP ranges.
20. Thực hiện hai validation song song: (A) IP Check: so sánh client IP với allowed_ip_ranges. (B) GPS Check: tính khoảng cách Haversine giữa thiết bị và trung tâm. Pass = distance ≤ radius (default 100m).
21. Nếu cả hai pass (hoặc một pass, một không khả dụng): check-in tiến hành bình thường — tạo hr.attendance với check_in = now(), location_flag = "on_site", ip_address, gps_lat/lng.
22. Chatter note: "Check-in verified: On-site [Tên địa điểm] lúc [HH:MM]."
23. Trả về xác nhận thành công đến UI nhân viên.
	Alternative Flow
	* GPS không khả dụng (user từ chối permission / thiết bị không có GPS): Fallback sang IP-only validation. Nếu IP hợp lệ → check-in với location_flag = "ip_verified_only".
* IP ngoài range nhưng GPS trong geofence: Check-in được phép, tag location_flag = "gps_verified_only". Xảy ra khi nhân viên dùng mobile data thay vì Wi-Fi văn phòng.
* Nhân viên đã có trạng thái WFH/Business Trip được duyệt trước: Check-in tự động proceed với location_flag = "pre_approved_remote".
	Exception Flow
	* Cả GPS lẫn IP đều fail: Hệ thống block check-in tiêu chuẩn. Modal popup yêu cầu nhân viên chọn Out-of-Office Reason và nhập text giải thích (tối thiểu 20 ký tự).
* Nhân viên submit lý do ngoài văn phòng: Check-in được lưu với location_flag = "outside_perimeter", out_of_office_reason, out_of_office_note. Bản ghi vào HR Review Queue để manager confirm trong 24h.
* Manager approve: location_flag → "approved_remote". Payroll không bị ảnh hưởng.
* Manager reject: location_flag → "rejected_remote". HR có thể apply deduction vắng mặt. Nhân viên được notify.
	Validation Rules
	* GPS coordinates phải capture trong 5 giây sau khi click Check-In — nếu timeout, chuyển sang IP-only validation.
* Haversine distance dùng hệ tọa độ WGS84.
* Geofence radius: 50m (min) – 500m (max) mỗi location config.
* Allowed IP ranges hỗ trợ CIDR notation (IPv4 và IPv6).
* out_of_office_note tối thiểu 20 ký tự, không chứa toàn whitespace.
	Input Fields
	

Field
	Type
	Required
	Rule
	GPS Coordinates (auto-capture)
	Float (lat, lng)
	No (best-effort)
	navigator.geolocation — fallback sang IP nếu không khả dụng
	Client IP Address (auto-capture)
	Char
	Yes (auto)
	Đọc từ HTTP headers — không chỉnh sửa được bởi nhân viên
	Out-of-Office Reason (conditional)
	Selection
	Yes (nếu ngoài vùng)
	WFH / Business Trip / Gặp khách hàng / Gặp học viên / Khác
	Out-of-Office Note (conditional)
	Text
	Yes (nếu ngoài vùng)
	Tối thiểu 20 ký tự
	

	Output
	hr.attendance record với check_in, location_flag, ip_address, gps_lat/lng, và tùy chọn out_of_office_reason/note. HR Review Queue được cập nhật nếu location_flag = "outside_perimeter".
	Business Rules
	* BR-ATT-008: GPS/IP validation chỉ áp dụng cho Office Staff và Sales Consultants. Giảng viên (dùng CUS-ATT-001) và CTV (dùng CUS-ATT-003) không áp dụng.
* BR-ATT-009: Bản ghi location_flag = "outside_perimeter" chưa được Manager review sau 48h sẽ tự động escalate lên HR Manager.
* BR-ATT-010: Bảng cấu hình hb.attendance.location.config chỉ được chỉnh sửa bởi user có role "HR Manager". Mọi thay đổi được log trong chatter.
* BR-ATT-011: Tọa độ GPS nhân viên chỉ lưu phục vụ compliance chấm công. Retention 12 tháng, không accessible với non-HR personnel theo nội quy bảo mật dữ liệu nội bộ.
	UI Reference
	Employee Portal > Attendance > Check In (modified with geofence overlay) | HR > Attendance > Location Config (admin view) | HR > Attendance > Outside Perimeter Review Queue.
	

ATT-F-004 — Attendance Location Configuration Management


ATT-F-004  ·  Attendance Location Configuration Management (Admin)
	Function ID
	ATT-F-004
	Function Name
	Attendance Location Configuration Management (Admin)
	Module
	Attendance (Custom: hb_attendance_geofence)
	Actor
	HR Manager / System Administrator
	Purpose
	Cung cấp giao diện cấu hình chuyên biệt cho HR Manager để định nghĩa, cập nhật và duy trì ranh giới địa lý (tọa độ GPS + bán kính + IP ranges) được sử dụng bởi ATT-F-003 cho real-time perimeter validation.
	Preconditions
	* User có quyền "HR Manager"
* Ít nhất một địa điểm công ty (văn phòng hoặc trung tâm) đã được khai báo trong hệ thống
	Trigger
	HR Manager vào Attendance → Configuration → Location Settings và tạo mới hoặc chỉnh sửa location record.
	Main Flow
	24. HR Manager vào Attendance > Configuration > Location Settings.
25. Click "Create" để thêm location mới hoặc chọn record hiện có để sửa.
26. Điền thông tin: Location Name, Latitude/Longitude (có thể pin trên embedded map widget), GPS Radius (m), Allowed IP Ranges (CIDR), Active flag, Applies To (employee types).
27. Click "Save". Hệ thống validate tọa độ nằm trong bounding box Việt Nam (lat 8–24, lng 102–110) và IP ranges là CIDR hợp lệ.
28. Ghi log thay đổi vào chatter của config record với timestamp và user identity.
29. Cấu hình mới có hiệu lực ngay lập tức cho tất cả check-in attempts tiếp theo.
	Alternative Flow
	* HR Manager deactivate một location (Active = False): Tất cả check-in của employees thuộc location đó revert về "no geofence enforcement" đến khi có active location mới được cấu hình.
	Exception Flow
	* CIDR notation không hợp lệ: ValidationError: "Invalid IP range format. Vui lòng dùng CIDR notation (vd: 192.168.1.0/24)."
* Tọa độ ngoài bounding box Việt Nam: Cảnh báo mềm (không block): "Tọa độ có vẻ nằm ngoài Việt Nam. Vui lòng xác nhận lại."
	Validation Rules
	* Location Name phải unique trong tất cả active records.
* Latitude: float, -90 đến 90. Longitude: float, -180 đến 180.
* GPS Radius: integer, 50–500 meters.
* Allowed IP Ranges: danh sách CIDR hợp lệ, cách nhau bằng dấu phẩy.
	Input Fields
	

Field
	Type
	Required
	Rule
	Location Name
	Char
	Yes
	Unique, tối đa 128 ký tự
	Latitude
	Float
	Yes
	Decimal latitude hợp lệ (-90 đến 90)
	Longitude
	Float
	Yes
	Decimal longitude hợp lệ (-180 đến 180)
	GPS Radius (meters)
	Integer
	Yes
	50–500 meters
	Allowed IP Ranges
	Text (CIDR list)
	Yes
	Ít nhất một CIDR range hợp lệ
	Applies To (Employee Types)
	Many2many
	No
	Blank = áp dụng tất cả trừ Teachers
	Active
	Boolean
	Yes
	Default True
	

	Output
	Bản ghi hb.attendance.location.config được lưu. Cấu hình active ngay lập tức cho tất cả check-in validations tiếp theo.
	Business Rules
	* BR-ATT-012: Chỉ HR Manager được tạo, sửa hoặc deactivate location config records.
* BR-ATT-013: Mọi thay đổi config được log immutably trong chatter để audit compliance.
* BR-ATT-014: Nếu không có active location config cho một employee type, geofence validation bị skip (fail-open policy) để tránh operational lockout.
	UI Reference
	Attendance > Configuration > Location Settings (menu item mới) | Form view có embedded Google Maps / OpenStreetMap widget để pin-drop tọa độ.
	





6.3 CUS-ATT-003 — Collaborator Rotating Shift Registration & Reconciliation
Standard Odoo chỉ hỗ trợ tham chiếu lịch làm việc cố định đính kèm profile; không hỗ trợ đăng ký ca linh hoạt theo tuần. Module này xây dựng hệ thống đăng ký, duyệt và đối soát ca làm việc cho khối CTV.


ATT-F-005 — Weekly Shift Registration by Collaborator


ATT-F-005  ·  Weekly Shift Registration by Collaborator
	Function ID
	ATT-F-005
	Function Name
	Weekly Shift Registration by Collaborator
	Module
	Attendance (Custom: hb_attendance_ctv_shift)
	Actor
	Collaborator (CTV) / Part-time Staff
	Purpose
	Cung cấp giao diện self-service để CTV đăng ký ca làm việc dự kiến cho tuần tới, tạo ra cam kết ca chính thức làm baseline để đối soát chấm công và validate giờ trả lương.
	Preconditions
	* Nhân viên đăng nhập portal Odoo với employee_type = "Collaborator" hoặc "Part-time"
* Cửa sổ đăng ký ca cho tuần mục tiêu đang mở (cấu hình: mở Thứ 2, đóng Chủ Nhật 23:59 tuần trước)
* Line Manager đã publish các shift blocks khả dụng cho tuần đó
	Trigger
	CTV vào Attendance > My Shift Registration và click "Đăng ký ca tuần [Số tuần]".
	Main Flow
	30. CTV vào My Shift Registration view trên employee portal.
31. Hệ thống hiển thị lưới lịch 7 ngày với các shift blocks khả dụng do Line Manager publish (vd: Sáng 08:00–12:00, Chiều 13:00–17:00, Tối 17:30–21:00).
32. CTV chọn ca mong muốn bằng cách click/toggle ô trên lưới (multi-select).
33. Hệ thống validate tổng giờ đăng ký không vượt weekly maximum trong hợp đồng (x_weekly_max_hours).
34. CTV click "Submit Shift Registration".
35. Hệ thống tạo ctv.shift.register records cho mỗi (ngày × shift_block): employee_id, shift_date, shift_block_id, planned_start, planned_end, status = "registered".
36. Line Manager nhận in-app notification và email: "[Tên CTV] đã submit đăng ký ca tuần [Số tuần]. Cần review."
	Alternative Flow
	* Submit sau deadline (CN 23:59): Thông báo: "Hạn đăng ký ca tuần này đã qua. Vui lòng liên hệ Line Manager để được assign ca thủ công."
* Chỉnh sửa đăng ký trước khi được duyệt: Cho phép. Hệ thống gửi notification mới đến manager. Phiên bản cũ bị thay thế.
* Hủy một ca đơn lẻ sau khi đăng ký nhưng trước khi được duyệt: Record đó bị xóa. Manager được notify.
	Exception Flow
	* Tổng giờ vượt x_weekly_max_hours: ValidationError cứng: "Bạn đã chọn [X] giờ vượt quá giới hạn [Y] giờ/tuần. Vui lòng bỏ bớt ca."
* Chưa có shift block nào được publish cho tuần mục tiêu: "Chưa có ca nào được đăng cho tuần này. Vui lòng chờ hoặc liên hệ Line Manager."
* Hệ thống không khả dụng trong cửa sổ đăng ký: CTV nhắn tin cho Line Manager qua Odoo chat. Manager tạo ctv.shift.register thay mặt CTV.
	Validation Rules
	* Tổng giờ đăng ký/tuần ≤ x_weekly_max_hours trong hợp đồng.
* Không có shift blocks overlap nhau trong cùng một ngày.
* Đăng ký phải submit trước CN 23:59 tuần trước (configurable parameter).
* CTV chỉ được đăng ký shift trong department/cost center được assign.
	Input Fields
	

Field
	Type
	Required
	Rule
	Shift Date
	Date
	Yes
	Trong phạm vi T2–CN của tuần mục tiêu
	Shift Block
	Many2one (hb.shift.block)
	Yes
	Phải là shift block đã được publish
	Employee (auto-filled)
	Many2one (hr.employee)
	Yes
	Tự động từ session người dùng
	Notes (optional)
	Text
	No
	Tối đa 200 ký tự — yêu cầu đặc biệt cho Line Manager
	

	Output
	ctv.shift.register records tạo với status = "registered". Line Manager notification gửi. Lịch ca cập nhật cho cả CTV và Manager view.
	Business Rules
	* BR-ATT-015: CTV được đăng ký tối đa 6 shift slots/tuần. Trần giờ tổng được enforce bởi x_weekly_max_hours trong hợp đồng.
* BR-ATT-016: Shift registration records là baseline binding cho giờ trả lương. Giờ làm ngoài shift window đã đăng ký có thể bị loại khỏi payroll (CFG-ATT-LP-08).
* BR-ATT-017: Shift blocks khả dụng do Line Manager quản lý — định nghĩa nhu cầu nhân lực cho mỗi tuần.
	UI Reference
	Employee Portal > Attendance > My Shifts > Weekly Registration Calendar | Manager Dashboard > Team Shifts > Submitted Registrations.
	

ATT-F-006 — Line Manager Shift Approval


ATT-F-006  ·  Line Manager Shift Approval / Rejection
	Function ID
	ATT-F-006
	Function Name
	Line Manager Shift Approval / Rejection
	Module
	Attendance (Custom: hb_attendance_ctv_shift)
	Actor
	Line Manager
	Purpose
	Cho phép Line Manager review, approve hoặc reject đăng ký ca tuần của CTV, đảm bảo độ phủ nhân lực phù hợp với nhu cầu vận hành trước khi tuần bắt đầu.
	Preconditions
	* ctv.shift.register records tồn tại với status = "registered" từ CTV
* User có quyền Line Manager cho department liên quan
* Đang trong review window (Thứ 2–Thứ 4 của tuần mục tiêu)
	Trigger
	Line Manager vào Manager Dashboard > Team Shifts > Pending Approvals hoặc nhận in-app notification.
	Main Flow
	37. Line Manager mở Team Shifts view filter theo tuần mục tiêu.
38. Hệ thống hiển thị lưới tổhợp tất cả shift đăng ký mỗi CTV mỗi ngày với status badges.
39. Manager review từng đăng ký: click "Approve" (status → "approved") hoặc "Reject" kèm rejection reason bắt buộc.
40. Hệ thống gửi notification tự động đến CTV cho mỗi quyết định.
41. Manager có thể Bulk Approve tất cả shift trong tuần bằng một action.
42. Approved shifts bị lock: ctv.shift.register chuyển sang status = "approved" và trở thành baseline cho ATT-F-007.
	Alternative Flow
	* Manager chỉnh sửa shift đã approve (điều chỉnh giờ): Có thể edit planned_start/end trong ±1 giờ nếu nhu cầu vận hành thay đổi. CTV được notify về sự chỉnh sửa.
* Manager tạo ad-hoc shift cho CTV (không phải tự đăng ký): Dùng "Add Shift" trực tiếp trên lưới team, tạo ctv.shift.register thay mặt CTV. CTV được notify.
	Exception Flow
	* Manager không review trước Thứ 4 của tuần mục tiêu: Hệ thống auto-approve tất cả pending registrations không vượt quá weekly max. Log với system user và note: "Auto-approved: Manager review deadline exceeded."
	Validation Rules
	* Rejection reason bắt buộc khi reject (tối thiểu 10 ký tự).
* Tổng giờ approved toàn team trong một ngày không được vượt department headcount maximum (configurable).
	Input Fields
	

Field
	Type
	Required
	Rule
	Approval Decision
	Selection (Approve/Reject)
	Yes
	Phải chọn một cho mỗi registration
	Rejection Reason
	Text
	Yes (nếu Reject)
	Tối thiểu 10 ký tự
	

	Output
	ctv.shift.register cập nhật status = "approved" hoặc "rejected". CTV notification. Approved shifts thành baseline reconciliation cho ATT-F-007.
	Business Rules
	* BR-ATT-018: Sau khi approve, chỉ Line Manager hoặc HR Manager mới được sửa. Thay đổi log trong chatter.
* BR-ATT-019: Rejected registrations không tính vào weekly hours. CTV có thể đăng ký lại nếu chưa hết deadline.
	UI Reference
	Manager Dashboard > Team Shifts > Pending Approvals list | Gantt-style weekly grid view cho team shift coverage.
	

ATT-F-007 — Real-time Shift Deviation Detection at Check-In/Check-Out


ATT-F-007  ·  Real-time Shift Deviation Detection tại Check-In/Check-Out
	Function ID
	ATT-F-007
	Function Name
	Real-time Shift Deviation Detection tại Check-In/Check-Out
	Module
	Attendance (Custom: hb_attendance_ctv_shift)
	Actor
	System (Automated) | Khởi tạo bởi: Collaborator Check-In / Check-Out action
	Purpose
	Tự động validate mỗi timestamp check-in/check-out của CTV so với shift đã được approve, phát hiện deviations (đến sớm, đến muộn, làm quá giờ, session không đăng ký) và flag exceptions cho Line Manager review, ngăn chặn tích lũy giờ trái phép.
	Preconditions
	* CTV có ít nhất một ctv.shift.register record được approve cho ngày hiện tại
* Nhân viên đang thực hiện check-in/check-out qua Kiosk hoặc portal
* Geofence validation (ATT-F-003) đã được áp dụng (CTV cũng subject to IP/GPS check)
	Trigger
	CTV hoàn thành check-in hoặc check-out. Hệ thống xử lý write event trên hr.attendance record.
	Main Flow
	43. CTV check-in qua Kiosk (PIN/Badge) hoặc portal. Timestamp check_in được capture.
44. Hệ thống query ctv.shift.register tìm shift approved cho employee, ngày hiện tại.
45. Tính deviation: delta_start = check_in - planned_start_time.
46. |delta_start| ≤ 30 phút (tolerance): Chấm công bình thường với reconciliation_status = "on_time".
47. delta_start > 30 phút (đến muộn): Ghi reconciliation_status = "late_arrival". Line Manager được notify.
48. delta_start < -30 phút (đến sớm hơn shift): Cảnh báo mềm: "Bạn đang check-in [X phút] trước ca đăng ký. Ca bắt đầu lúc [HH:MM]." Attendance vẫn được ghi.
49. Khi check-out: Reconciliation tương tự. delta_end = check_out - planned_end_time.
50. check_out > planned_end + 30 phút (làm quá giờ): reconciliation_status = "overstay_detected". Giờ vượt bị flag x_unregistered_hours, loại khỏi giờ trả lương — chờ Line Manager approve.
51. Daily reconciliation summary email gửi đến Line Manager lúc 23:00.
	Alternative Flow
	* CTV check-in ngày không có shift được approve: reconciliation_status = "unregistered_attendance". Toàn bộ attendance record bị mark non-payable. Manager phải (A) approve retroactively hoặc (B) mark unauthorized.
* CTV có nhiều shift trong cùng ngày (vd: sáng và tối): Hệ thống match check-in với planned_start gần nhất. Mỗi cặp check-in/out được reconcile với shift block tương ứng độc lập.
	Exception Flow
	* Không tồn tại ctv.shift.register nào cho CTV cả tuần: Hệ thống flag HR để setup missing shift. CTV không thể tạo giờ trả lương cho đến khi có approved shifts.
* Kiosk offline (lỗi mạng): CTV ghi giờ trên paper form. HR tạo thủ công attendance với flag "manual_entry_exception" để post-hoc reconciliation.
	Validation Rules
	* Tolerance deviation: ±30 phút so với planned shift start/end trước khi raise exception.
* Overstay hours (vượt planned_end + 30 phút) tự động mark non-payable trừ khi Line Manager explicitly approve làm OT.
* Unregistered attendance (không có shift approve ngày đó) = zero payable hours, bất kể giờ thực tế là bao nhiêu.
	Input Fields
	

Field
	Type
	Required
	Rule
	check_in (auto-capture)
	Datetime
	Yes
	System timestamp, nhân viên không được sửa
	check_out (auto-capture)
	Datetime
	Yes (cho payroll)
	System timestamp tại thời điểm check-out
	employee_id (auto-capture)
	Many2one
	Yes
	Từ authenticated session
	

	Output
	hr.attendance record với reconciliation_status, x_unregistered_hours và shift deviation data. Exception records vào Line Manager review queue nếu deviation được phát hiện.
	Business Rules
	* BR-ATT-020: Giờ trả lương cho CTV = min(actual_worked_hours, registered_shift_hours + approved_overtime). Giờ ngoài cap này không được đưa vào WORK100_CTV work entry.
* BR-ATT-021: Tất cả shift exception flags phải được Line Manager resolve trước khi monthly payroll batch được generate. Payroll batch wizard block execution nếu tồn tại unresolved exceptions.
* BR-ATT-022: Tolerance 30 phút là configurable parameter (lưu trong hb.attendance.ctv.config). Thay đổi không ảnh hưởng retroactively đến records cũ.
* BR-ATT-023: CTV payroll không thể compute (STR-03 batch block) nếu WORK100_CTV work entry nào trong kỳ còn ở state "exception" hoặc "pending_approval".
	UI Reference
	Attendance Kiosk (shared tablet) | Employee Portal > Attendance > My Shift History | Manager Dashboard > Team Shifts > Exception Review Queue | HR > Attendance > Monthly Exception Report.
	





6.4 Tổng Hợp Custom Functions — Module Attendance


Function ID
	Function Name
	Custom Module
	Actor
	Gap
	ATT-F-001
	Auto Check-In từ Session Start
	hb_attendance_academic
	System / Acad. Coord.
	CUS-ATT-001
	ATT-F-002
	Auto Check-Out từ Session Completion
	hb_attendance_academic
	System / Acad. Coord.
	CUS-ATT-001
	ATT-F-003
	GPS & IP Validation tại Check-In
	hb_attendance_geofence
	Employee (Office/Sales)
	CUS-ATT-002
	ATT-F-004
	Location Config Management
	hb_attendance_geofence
	HR Manager
	CUS-ATT-002
	ATT-F-005
	Weekly Shift Registration (CTV)
	hb_attendance_ctv_shift
	Collaborator
	CUS-ATT-003
	ATT-F-006
	Line Manager Shift Approval
	hb_attendance_ctv_shift
	Line Manager
	CUS-ATT-003
	ATT-F-007
	Real-time Shift Deviation Detection
	hb_attendance_ctv_shift
	System / CTV
	CUS-ATT-003
	

Tất cả 7 custom functions trên đều được validate theo Gap Analysis Matrix trong Chapter 4 (Module Attendance), ánh xạ trực tiếp đến CUS-ATT-001, CUS-ATT-002 và CUS-ATT-003. Các module được phát triển theo kiến trúc extension-only — không chỉnh sửa Odoo core source code.




Chap 6 Recruitment


FS-REC-001 Job Position Management
COVER
FUNCTIONAL SPECIFICATION
HRM ODOO – HỌC BÁ EDUCATION
	

	Module
	REC
	Module Name
	Recruitment
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created Date
	02/06/2026
	Last Update Date
	02/06/2026
	Project
	HRM Odoo – Học Bá Education
	System
	Odoo 19 ERP (Community / Enterprise)
	Reference
	Odoo 19.0 Official Docs – Job Positions (https://www.odoo.com/documentation/19.0/applications/hr/recruitment/new_job.html)
	

	

	Approver
	Reviewer
	Creator
	Name
	Giảng viên hướng dẫn
	—
	Nhóm G2 – ISP490
	Organization
	FPT University
	—
	FPT University
	________________


CHANGE HISTORY
No
	Version
	Description
	Sheet
	Modified Date
	Modified By
	1
	1.0
	Initial creation
	All
	02/06/2026
	Nhóm G2
	2
	1.1
	Sửa theo feedback: xóa hr.recruitment, sửa state logic, thêm Standard vs Custom Matrix
	All
	02/06/2026
	Nhóm G2
	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	________________


1. FUNCTION OVERVIEW
Function Overview
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Processing Time
	On-demand / Real-time
	Processing Type
	Interactive (UI-driven)
	Function Type
	Master Data Maintenance
	Multilingual
	Yes (Vietnamese / English)
	

Business Requirement & Function Overview
	Mô tả tổng quan:
Chức năng Job Position Management quản lý danh mục vị trí tuyển dụng (hr.job) trong Odoo 19 Recruitment. Đây là dữ liệu Master (Master Data) — nền tảng để tất cả hồ sơ ứng viên (hr.applicant) liên kết vào. Mỗi vị trí xác định phòng ban, số lượng cần tuyển, và khi được kích hoạt tuyển dụng, hệ thống sẽ hiển thị thẻ Kanban trên Dashboard và badge PUBLISHED trên website (nếu bật website_published).
Business Context – Học Bá Education:
Học Bá Education liên tục mở rộng quy mô đào tạo tiếng Trung, dẫn đến tần suất tuyển dụng Giảng viên (HSK2/HSK3/TOCFL) và Tư vấn tuyển sinh diễn ra quanh năm. Quy trình bắt đầu khi Trưởng bộ phận gửi Phiếu yêu cầu tuyển dụng (Tài liệu 7.2). HR Officer căn cứ vào phiếu đó để tạo hoặc cập nhật Job Position tương ứng trong hệ thống, trước khi mở đường ống Kanban tiếp nhận ứng viên.
Phạm vi chức năng:
(1) Tạo mới / Chỉnh sửa Job Position với thông tin: tên vị trí, phòng ban, số lượng cần tuyển, mô tả công việc.
(2) Liên kết hr.job ↔ hr.department và hr.job ↔ hr.applicant (One2many).
(3) Quản lý trạng thái tuyển dụng thông qua trường active và no_of_recruitment (Odoo Standard) và badge PUBLISHED (website_published).
(4) Trường tùy biến x_teaching_level (Custom) phục vụ phân công lớp học sau khi onboard giảng viên.
Người dùng liên quan: HR Officer/C&B (toàn quyền tạo/sửa/xóa), BOD (xem báo cáo).
	Supplement / Ghi chú bổ sung
	• Odoo 19 Standard: HR Officer (group_hr_recruitment_manager) có quyền tạo/sửa/xóa hr.job. Department Manager (TBP) KHÔNG trực tiếp tạo Job Position — chỉ gửi Phiếu yêu cầu tuyển dụng (giấy tờ nội bộ/Lark). Đây là thiết kế Odoo Standard, phù hợp với quy trình kiểm soát nội bộ của Học Bá.
• Odoo 19 không có model 'hr.recruitment' độc lập. Đường ống ứng viên được quản lý trực tiếp qua hr.applicant liên kết với hr.job thông qua trường job_id.
• Nguồn tham chiếu: Odoo 19.0 Official Docs – Job Positions (https://www.odoo.com/documentation/19.0/applications/hr/recruitment/new_job.html)
	________________


2. FUNCTION FLOW
Function Flow
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	

Screen Flow / Luồng Màn hình
	Luồng chính (Main Flow — HR Officer):
  [1] HR Officer truy cập: Recruitment ▸ Configuration ▸ Job Positions
       ↓
  [2] Hệ thống hiển thị danh sách Job Position (List/Kanban View). Mặc định hiển thị tất cả vị trí active.
       ↓
  [3a] Nhấn [New] → Pop-up 'Create a Job Position' → Nhập Job Position Name + Application Email → [Create]
  [3b] Chọn dòng vị trí hiện có → Mở Form View → Chỉnh sửa → [Save]
       ↓
  [4] Hệ thống lưu bản ghi vào hr.job. Trạng thái tuyển dụng được thể hiện qua:
       • active = True/False (vị trí đang hoạt động hay đã archive)
       • website_published = True → Badge PUBLISHED xuất hiện trên thẻ Kanban và website tuyển dụng
       ↓
  [5] Smart Button [# Applications] tự động đếm hr.applicant có job_id = id vị trí này.
       ↓
  [6] Để kích hoạt nhận hồ sơ: Set website_published = True (trên Form View hoặc từ Kanban Dashboard). Ứng viên có thể apply qua website hoặc HR tạo thủ công hr.applicant.
Luồng xử lý lỗi (Error / Exception Flow):
  • Người dùng không thuộc group Recruitment Manager cố tạo/xóa hr.job → Odoo từ chối, hiện thông báo lỗi phân quyền.
  • [Custom] Tên vị trí trùng trong cùng phòng ban → Custom Python constraint raise ValidationError.
  • Archive vị trí đang có hr.applicant active → Odoo cảnh báo xác nhận trước khi thực thi.
	________________


3. SCREEN LAYOUT
Screen Layout
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	

Screen 1: Recruitment Dashboard / Job Position Kanban View (Odoo Standard)
	Truy cập: Recruitment ▸ (Main Dashboard)
Hiển thị: Mỗi Job Position là một thẻ Kanban. Badge PUBLISHED (màu xanh) xuất hiện khi website_published = True.
Thông tin trên thẻ: Job Position Name | Department | # Applications (button) | # New Applications | Badge PUBLISHED
Buttons trên Dashboard: [New] | [Filters▼] | [Group By▼] | [Favorites▼] | [List View / Kanban View toggle]
	Screen 2: Job Position List View – Configuration Menu
	Truy cập: Recruitment ▸ Configuration ▸ Job Positions
Columns hiển thị: Job Position | Department | Job Location | Expected New Employees | Current Employees | New Applications | Status (Published / Unpublished)
Buttons: [New] | [Import] | [Filters▼] | [Group By▼] | [Search Bar]
	Screen 3: Job Position Form View (Odoo Standard + Custom Extension)
	Header Block (Standard): Job Position Name* | Department | Company | Recruiter | Interviewers
Tab 'Recruitment' (Standard): Expected New Employees | Job Location | Industry | Employment Type | Target | Website | Contract Template | Interview Form | Mission Dates
Tab 'Application Info' (Standard): Process Details (số bước phỏng vấn, thời gian phản hồi)
Tab 'Job Summary' (Standard): HTML Editor – Mô tả công việc hiển thị lên website tuyển dụng
Custom Extension – Học Bá (x_hb_recruitment_ext):
  • Field x_teaching_level (Selection): HSK2 / HSK3 / TOCFL / N/A — hiển thị trong Tab Recruitment
  • Field x_required_sessions_per_week (Integer): Số buổi/tuần yêu cầu tối thiểu
Smart Buttons (Standard): [# Applications] | [# Employees]
Action Buttons: [Go to Website] (nếu website_published=True) | [Archive] | [Save / Discard]
	________________


4. PROCESSING DESCRIPTION
Processing Description
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Created date
	02/06/2026
	Modified date
	02/06/2026
	

1. Input Data Table – Job Position Form Fields
	No
	Field
	Odoo 19 Model & Field
	Validation / Ghi chú
	Standard / Custom
	Required
	1
	Job Position Name
	hr.job – name (Char)
	Không trống. [Custom] Unique trong cùng department_id
	Standard + Custom constraint
	YES
	2
	Department
	hr.job – department_id (M2O hr.department)
	Chọn từ danh mục hr.department active
	Standard
	Recommended
	3
	Company
	hr.job – company_id (M2O res.company)
	Auto = company của user đăng nhập (multi-company)
	Standard
	Auto
	4
	Expected New Employees
	hr.job – no_of_recruitment (Integer)
	Giá trị ≥ 1; Default = 1
	Standard
	Recommended
	5
	Job Location
	hr.job – address_id (M2O res.partner)
	Địa điểm làm việc. Blank = Remote
	Standard
	NO
	6
	Employment Type
	hr.job – contract_type_id (M2O hr.contract.type)
	Loại hình: Toàn thời gian / CTV / Part-time
	Standard
	NO
	7
	Website Published
	hr.job – website_published (Boolean)
	True = Đăng lên cổng tuyển dụng; False = Nội bộ
	Standard
	NO
	8
	Recruiter
	hr.job – user_id (M2O res.users)
	Nhân viên HR phụ trách tuyển dụng vị trí này
	Standard
	Recommended
	9
	Teaching Level [Custom]
	hr.job – x_teaching_level (Selection)
	'hsk2'|'hsk3'|'tocfl'|'na'. Bắt buộc nếu department = Giảng viên/Trợ giảng
	CUSTOM
	COND
	10
	Job Summary
	hr.job – description (Html)
	Nội dung HTML hiển thị lên website tuyển dụng
	Standard
	NO
	

2. Output Data Table – Kết quả sau lưu thành công
	No
	Field
	Odoo 19 Model & Field
	Mô tả & Ghi chú
	Data Type
	1
	Job Position ID
	hr.job – id
	Primary Key, tự tăng; dùng làm khóa liên kết job_id trong hr.applicant
	Integer
	2
	Active Status
	hr.job – active (Boolean)
	True = đang active; False = đã archive; Default = True (Odoo Standard)
	Boolean
	3
	Published Status
	hr.job – website_published (Boolean)
	True = badge PUBLISHED xuất hiện trên Kanban Dashboard và website
	Boolean
	4
	No. of Applications
	hr.job – no_of_applications (Computed)
	COUNT hr.applicant WHERE job_id = self.id AND active = True (Odoo Standard)
	Integer
	5
	No. of Employees
	hr.job – no_of_employee (Computed)
	COUNT hr.employee WHERE job_id = self.id AND active = True (Odoo Standard)
	Integer
	6
	External ID
	ir.model.data
	Cú pháp: __export__.hr_job_<dept_slug>_<pos_slug>
	Char
	

3. Processing Logic / Quy tắc xử lý
	Logic 1 – [ODOO STANDARD] Quản lý trạng thái tuyển dụng:
Odoo 19 KHÔNG sử dụng workflow state 'recruit'/'open' cho hr.job. Trạng thái được quản lý qua hai trường:
  • active (Boolean): True = vị trí đang hoạt động; False = archive (ẩn khỏi list mặc định). HR Officer có thể Archive/Unarchive từ Action menu.
  • website_published (Boolean): True = Đăng lên website, hiển thị badge PUBLISHED màu xanh trên Kanban Dashboard.
  • no_of_recruitment (Integer): Số lượng cần tuyển. Hệ thống tự tính no_of_hired_employee từ hr.applicant ở stage 'hired'.
Logic 2 – [CUSTOM] Kiểm tra trùng lặp tên vị trí (Duplicate Check):
Đây là yêu cầu tùy biến — Odoo Standard KHÔNG có constraint này.
  Cài đặt trong module x_hb_recruitment_ext:
  @api.constrains('name', 'department_id')
  def _check_duplicate_position(self):
      domain = [('name','=',self.name),('department_id','=',self.department_id.id),('id','!=',self.id),('active','=',True)]
      if self.search_count(domain) > 0:
          raise ValidationError('Vị trí này đã tồn tại trong phòng ban. Vui lòng kiểm tra lại.')
Logic 3 – [CUSTOM] Conditional Required cho x_teaching_level:
  Nếu department_id.name in ['Giảng viên', 'Trợ giảng'] và x_teaching_level == 'na' → raise ValidationError.
Logic 4 – [ODOO STANDARD] Access Control (Phân quyền):
  • group_hr_recruitment_manager (HR Officer): Create/Read/Write/Delete toàn bộ hr.job.
  • group_hr_recruitment_user (Recruitment User): Read/Write hr.applicant; Read-only hr.job.
  • Department Manager (TBP): KHÔNG có quyền tạo hr.job trong Odoo Standard. Yêu cầu tuyển dụng được thực hiện qua Phiếu yêu cầu tuyển dụng nội bộ (giấy/Lark), HR Officer xử lý tiếp.
	________________


5. SCREEN DEFINITION
Screen Definition
	Function ID
	FS-REC-001
	Function Name
	Job Position Management
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Page Title
	Job Positions – Học Bá Education HRM (Odoo 19)
	

1. Form View – Field Definitions
	No
	Field Name
	UI Type
	I/O
	Data Type
	Length
	Required
	Default
	S/C
	Remarks
	1
	Job Position Name
	Text Input
	I/O
	CHAR
	128
	YES
	—
	S
	hr.job – name. Key field
	2
	Department
	M2O Dropdown
	I/O
	INT FK
	—
	Rec.
	—
	S
	hr.job – department_id
	3
	Company
	M2O Dropdown
	I/O
	INT FK
	—
	Auto
	Current
	S
	hr.job – company_id
	4
	Exp. New Employees
	Integer Input
	I/O
	INTEGER
	4
	Rec.
	1
	S
	hr.job – no_of_recruitment
	5
	Job Location
	M2O Dropdown
	I/O
	INT FK
	—
	NO
	—
	S
	hr.job – address_id
	6
	Employment Type
	M2O Dropdown
	I/O
	INT FK
	—
	NO
	—
	S
	hr.job – contract_type_id
	7
	Website Published
	Toggle/Checkbox
	I/O
	BOOLEAN
	1
	NO
	False
	S
	hr.job – website_published. Badge PUBLISHED khi = True
	8
	Recruiter
	M2O Dropdown
	I/O
	INT FK
	—
	Rec.
	Current user
	S
	hr.job – user_id
	9
	No. Applications
	Smart Button
	O
	INTEGER
	4
	—
	Auto
	S
	hr.job – no_of_applications (Computed/Readonly)
	10
	Teaching Level
	Selection Dropdown
	I/O
	CHAR
	10
	COND
	na
	C
	x_teaching_level: hsk2/hsk3/tocfl/na
	11
	Job Summary
	HTML Rich Text
	I/O
	TEXT
	—
	NO
	—
	S
	hr.job – description (Tab Job Summary)
	Legend: S = Odoo Standard | C = Custom Development | COND = Conditional Required
	________________


6. STANDARD vs CUSTOM GAP ANALYSIS MATRIX
Standard vs Custom GAP Analysis Matrix
	Feature / Tính năng
	Odoo 19 Standard
	Custom (x_hb_recruitment_ext)
	Ghi chú
	Job Position CRUD (hr.job)
	✓
	

	Odoo Standard – Recruitment module
	Liên kết hr.job → hr.department
	✓
	

	M2O department_id – Standard
	Smart Button: # Applications
	✓
	

	Computed no_of_applications – Standard
	Smart Button: # Employees
	✓
	

	Computed no_of_employee – Standard
	Website Published (Badge PUBLISHED)
	✓
	

	website_published – website_hr_recruitment module
	Employment Type / Contract Type
	✓
	

	hr.contract.type – Standard
	Recruiter / Interviewers
	✓
	

	user_id / interviewer_ids – Standard
	Job Summary (HTML Editor)
	✓
	

	description field – Standard
	Access Control: HR Officer create/edit
	✓
	

	group_hr_recruitment_manager – Standard
	Teaching Level (x_teaching_level)
	

	✓ Cần phát triển
	Selection field cho Giảng viên HSK/TOCFL
	Duplicate Position Name Check
	

	✓ Cần phát triển
	Python @constrains trên hr.job
	Required Teaching Level (Conditional)
	

	✓ Cần phát triển
	@constrains kiểm tra nếu dept = Giảng viên
	Sessions per Week Field
	

	✓ Cần phát triển
	x_required_sessions_per_week (Integer)
	

Supplement / Ghi chú kỹ thuật
	Odoo Module Dependencies:
  • hr (hr.job, hr.department, hr.employee)
  • hr_recruitment (hr.applicant) — không có model hr.recruitment riêng biệt
  • website_hr_recruitment (website_published field, badge PUBLISHED)
Custom Module: x_hb_recruitment_ext
  • Inherit hr.job để thêm x_teaching_level (Selection) và x_required_sessions_per_week (Integer)
  • Python constraints: @api.constrains('name','department_id') và @api.constrains('x_teaching_level','department_id')
External ID Convention:
  Cú pháp: __export__.hr_job_<dept_slug>_<pos_slug>
  Ví dụ: __export__.hr_job_giangvien_hsk3  |  __export__.hr_job_kinh_doanh_tvts
Nguồn tham chiếu (References):
  • Odoo 19.0 Docs – Job Positions: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/new_job.html
  • Odoo 19.0 Docs – Recruitment: https://www.odoo.com/documentation/19.0/applications/hr/recruitment.html
  • Tài liệu nghiệp vụ Học Bá: 7.2 Phiếu yêu cầu tuyển dụng, 3.2 Department_Info.csv
	



FS-REC-002 Applicant Tracking
COVER
FUNCTIONAL SPECIFICATION
HRM ODOO – HỌC BÁ EDUCATION
	 
	Module
	REC
	Module Name
	Recruitment
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created Date
	02/06/2026
	Last Update Date
	02/06/2026
	Project
	HRM Odoo – Học Bá Education
	System
	Odoo 19 ERP (Community / Enterprise)
	Reference
	Odoo 19.0 Docs – Recruitment Flow: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/recruitment-flow.html
	 
	 
	Approver
	Reviewer
	Creator
	Name
	Giảng viên hướng dẫn
	—
	Nhóm G2 – ISP490
	Organization
	FPT University
	—
	FPT University
	

 
CHANGE HISTORY
No
	Version
	Description
	Sheet
	Modified Date
	Modified By
	1
	1.0
	Initial creation
	All
	02/06/2026
	Nhóm G2
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	

 
1. FUNCTION OVERVIEW
Function Overview
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Processing Time
	Real-time / On-demand
	Processing Type
	Interactive (UI-driven)
	Function Type
	Transaction Processing
	Multilingual
	Yes (Vietnamese / English)
	 
Business Requirement & Function Overview
	Mô tả tổng quan:
Applicant Tracking (Quản lý Hồ sơ Ứng viên) là chức năng cốt lõi của Module Recruitment trong Odoo 19. Chức năng này quản lý toàn bộ vòng đời của một hồ sơ ứng viên (hr.applicant) từ khi nộp CV đến khi được tuyển dụng (Hired) hoặc từ chối (Refused), thông qua một đường ống Kanban (Pipeline) với các Stage tuần tự.
Business Context – Học Bá Education:
Học Bá Education tiếp nhận ứng viên qua hai kênh song song: (1) Website tuyển dụng tích hợp Odoo (ứng viên tự nộp CV online) và (2) HR tạo thủ công hồ sơ ứng viên được giới thiệu qua mạng lưới nội bộ hoặc Lark. Thách thức đặc thù là xử lý kịch bản một ứng viên apply vào hai vị trí đồng thời (Tham chiếu: R-SYS-04 từ tài liệu nghiệp vụ) — Odoo Standard hỗ trợ kịch bản này thông qua mô hình res.partner trung tâm.
Pipeline Kanban mặc định Odoo 19 (6 stages):
  [1] New  →  [2] Initial Qualification  →  [3] First Interview  →  [4] Second Interview  →  [5] Contract Proposal  →  [6] Contract Signed (Folded)
Pipeline tùy chỉnh cho Học Bá (Custom Stages):
  [1] New / Mới  →  [2] Lọc CV (CV Review)  →  [3] Phỏng vấn HR  →  [4] Phỏng vấn Chuyên môn  →  [5] Demo giảng dạy (Giảng viên only)  →  [6] Đề xuất hợp đồng  →  [7] Ký hợp đồng
Phạm vi chức năng:
(1) Tạo mới / nhập thủ công hồ sơ ứng viên (hr.applicant).
(2) Di chuyển hồ sơ qua các Stage Kanban (drag-and-drop hoặc click status bar).
(3) Gắn tag, đính kèm CV, ghi chú nội bộ, lên lịch Activities (gọi điện, phỏng vấn).
(4) Từ chối ứng viên (Refuse) với lý do rõ ràng; ứng viên bị từ chối tự động archive.
(5) Xử lý kịch bản ứng viên apply nhiều vị trí đồng thời (Multi-position applicant).
(6) Chuyển đổi ứng viên thành nhân viên chính thức (Create Employee) khi ký hợp đồng.
Người dùng: HR Officer (toàn quyền), Recruitment User (xem + cập nhật stage), Interviewer (xem + ghi chú).
	Supplement / Ghi chú bổ sung
	• Mỗi hr.applicant liên kết với một res.partner (Candidate). Một ứng viên (partner) có thể có NHIỀU hr.applicant trên NHIỀU job_id khác nhau — đây là cơ chế Standard để xử lý R-SYS-04.
• Stage 'Demo giảng dạy' là Custom Stage chỉ áp dụng cho các vị trí Giảng viên (Job Specific = True, liên kết job_id thuộc nhóm Giảng viên/Trợ giảng).
• Nguồn: Odoo 19.0 Docs – Recruitment Flow & Add New Applicants.
	

 
2. FUNCTION FLOW
Function Flow
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	 
Screen Flow / Luồng Màn hình Chính
	── LUỒNG A: Ứng viên tự nộp CV qua Website ──
  [A1] Ứng viên truy cập website tuyển dụng → Chọn Job Position đã Published → Điền form → Submit
             ↓  Odoo tự động
  [A2] Hệ thống tạo bản ghi res.partner (candidate_id) nếu chưa tồn tại (đối chiếu email)
  [A3] Hệ thống tạo hr.applicant với stage_id = 'New', gửi email xác nhận tự động (nếu Email Template được cấu hình)
  [A4] HR Officer nhận thông báo → Mở Kanban view → Bắt đầu xử lý hồ sơ
── LUỒNG B: HR tạo thủ công hồ sơ ứng viên ──
  [B1] HR Officer vào: Recruitment ▸ [Chọn Job Position] ▸ Applications ▸ [New] hoặc Quick Add (+)
             ↓
  [B2] Pop-up 'Add a new application': nhập Candidate Name + Email + Phone → [Add]
             ↓
  [B3] Hệ thống tạo hr.applicant ở Stage hiện tại đang chọn (hoặc Stage 'New' nếu dùng nút New)
── LUỒNG C: Di chuyển Stage & Xử lý ──
  [C1] Drag-and-drop thẻ Kanban sang Stage tiếp theo, HOẶC mở Form View → Click tên Stage trên Status Bar
             ↓  Hệ thống tự động (nếu có Email Template trên Stage)
  [C2] Gửi email thông báo cho ứng viên (ví dụ: Stage 'Phỏng vấn HR' → gửi lịch hẹn)
  [C3] Tạo Activity (To-Do / Phone Call / Meeting) để nhắc HR thực hiện bước tiếp theo
  [C4] Cập nhật Kanban State (màu): ● Xanh (Ready) / ● Đỏ (Blocked) / ● Xám (In Progress)
── LUỒNG D: Từ chối ứng viên (Refuse) ──
  [D1] Mở Form View ứng viên → [Refuse] → Chọn Refuse Reason → [Refuse Applicant]
  [D2] Hệ thống set active = False, date_closed = today, refuse_reason_id = lý do đã chọn
  [D3] Hồ sơ biến mất khỏi Kanban active, còn truy xuất qua filter 'Archived'
  [D4] Ứng viên bị từ chối có thể Restore (Unarchive) để xem xét lại nếu cần
── LUỒNG E: Tuyển dụng thành công → Tạo nhân viên ──
  [E1] Ứng viên đến Stage 'Ký hợp đồng' (Contract Signed / hired_stage = True) → Badge HIRED xuất hiện
  [E2] HR nhấn [Create Employee] → Hệ thống tạo hr.employee với dữ liệu từ hr.applicant
  [E3] Liên kết hr.applicant ↔ hr.employee được thiết lập qua emp_id
	

 
3. SCREEN LAYOUT
Screen Layout
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	 
Screen 1: Applications Kanban View (Odoo Standard)
	Truy cập: Recruitment ▸ [Job Position Card] ▸ Click '# Applications'
Bố cục: Các cột Kanban = Stages. Mỗi thẻ ứng viên hiển thị:
  • Candidate Name (tiêu đề thẻ) | Job Position | Department
  • Applied Date | Tags | Appreciation (đánh giá sao)
  • Kanban State indicator (màu ●: xanh/đỏ/xám) | Activity icon
  • Avatar ảnh ứng viên (nếu có)
Buttons trên View: [New] | [Quick Add (+) trên mỗi Stage] | [Filters▼] | [Group By▼] | [Search] | [List / Kanban / Activity view]
	Screen 2: Applicant Form View (Odoo Standard)
	Header Block:
  • Subject / Application Name* (tên hồ sơ, thường là tên ứng viên + vị trí)
  • Candidate (M2O res.partner) | Job Position (M2O hr.job) | Department | Applied Job (chức danh)
  • Status Bar (Stage pipeline) ở trên cùng — click để chuyển stage
Tab 'Contract' / 'Recruitment' (Standard):
  • Interviewer(s) | Recruiter | Expected Salary | Contract Type | Kanban State | Last Stage Update
Tab 'Application' (Standard):
  • Appreciation (★★★ rating) | Source (kênh tuyển dụng) | Medium | Campaign | Availability
Tab 'Contract' — Custom Extension (x_hb_recruitment_ext):
  • x_demo_teaching_date (Date): Ngày demo giảng dạy — chỉ hiển thị nếu job_id thuộc nhóm Giảng viên
  • x_demo_teaching_result (Selection: Pass/Fail/N/A): Kết quả demo giảng dạy
  • x_cv_source_lark (Char): Link Lark Document đính kèm CV (nếu nhận qua Lark)
Chatter (Standard): Ghi chú nội bộ | Email log | Activities log | Stage change history
Smart Buttons (Standard): [Schedule Activity] | [Send Email] | [Create Employee] (khi hired)
	Screen 3: Refuse Applicant Dialog (Odoo Standard)
	Trigger: Nhấn [Refuse] trên Form View hoặc Kanban thẻ
Fields: Refuse Reason* (M2O hr.applicant.refuse.reason) | Send Email (checkbox, gửi từ chối ứng viên)
Buttons: [Refuse Applicant] / [Cancel]
	Screen 4: Stage Configuration (Recruitment ▸ Configuration ▸ Stages)
	Fields cấu hình stage (hr.recruitment.stage):
  • Stage Name* | Email Template | Folded in Kanban (Boolean) | Hired Stage (Boolean) | Job Specific (M2M hr.job)
Cấu hình Học Bá – Pipeline tùy chỉnh 7 stages:
  Stage 1: New / Mới                      — Folded=False | Hired=False | Job Specific=None
  Stage 2: Lọc CV                         — Folded=False | Hired=False | Template: Xác nhận nhận hồ sơ
  Stage 3: Phỏng vấn HR                   — Folded=False | Hired=False | Template: Lịch hẹn phỏng vấn HR
  Stage 4: Phỏng vấn Chuyên môn           — Folded=False | Hired=False
  Stage 5: Demo giảng dạy [Custom]        — Folded=False | Hired=False | Job Specific=Giảng viên/Trợ giảng
  Stage 6: Đề xuất hợp đồng               — Folded=False | Hired=False | Template: Thư mời ký HĐ
  Stage 7: Ký hợp đồng                — Folded=True  | Hired=True
	

 
4. PROCESSING DESCRIPTION
Processing Description
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Created date
	02/06/2026
	Modified date
	02/06/2026
	 
1. Input Data Table – Applicant Form Fields
	No
	Field
	Odoo 19 Model & Field
	Validation / Ghi chú
	S / C
	Required
	1
	Candidate Name
	hr.applicant – partner_name (Char) → res.partner – name
	Bắt buộc khi tạo. Tự động tạo res.partner nếu chưa tồn tại
	Standard
	YES
	2
	Email
	hr.applicant – email_from (Char)
	Format email hợp lệ. Dùng để match partner trùng lặp
	Standard
	YES
	3
	Phone
	hr.applicant – partner_phone (Char)
	Định dạng số điện thoại
	Standard
	YES
	4
	Job Position
	hr.applicant – job_id (M2O hr.job)
	Phải chọn từ danh mục hr.job active
	Standard
	YES
	5
	Applied Job (Job Title)
	hr.applicant – categ_ids hoặc job_id.name
	Tự động điền từ job_id. Có thể chỉnh sửa
	Standard
	Auto
	6
	Department
	hr.applicant – department_id (M2O hr.department)
	Tự động lấy từ job_id.department_id
	Standard
	Auto
	7
	Stage
	hr.applicant – stage_id (M2O hr.recruitment.stage)
	Default = Stage đầu tiên ('New'). Thay đổi qua Kanban drag/drop hoặc Status Bar
	Standard
	Auto
	8
	Recruiter
	hr.applicant – user_id (M2O res.users)
	Default = current user. HR Officer phụ trách theo dõi
	Standard
	Auto
	9
	Interviewer(s)
	hr.applicant – interviewer_ids (M2M res.users)
	Có thể chọn nhiều người
	Standard
	NO
	10
	Expected Salary
	hr.applicant – salary_expected (Float)
	Mức lương kỳ vọng ứng viên yêu cầu
	Standard
	NO
	11
	Source / Medium
	hr.applicant – source_id / medium_id (M2O)
	Kênh tuyển dụng: Website / Lark / Giới thiệu nội bộ
	Standard
	NO
	12
	Tags
	hr.applicant – tag_ids (M2M hr.applicant.category)
	Gán nhãn tùy chỉnh cho ứng viên
	Standard
	NO
	13
	CV / Attachment
	ir.attachment liên kết hr.applicant
	File PDF/Word đính kèm, hiển thị trên chatter
	Standard
	NO
	14
	Demo Teaching Date [C]
	hr.applicant – x_demo_teaching_date (Date)
	[Custom] Ngày demo. Hiển thị có điều kiện: job_id thuộc nhóm GV
	CUSTOM
	COND
	15
	Demo Result [C]
	hr.applicant – x_demo_teaching_result (Selection)
	[Custom] 'pass'|'fail'|'na'. Bắt buộc nếu stage = Demo giảng dạy
	CUSTOM
	COND
	16
	CV Source Lark [C]
	hr.applicant – x_cv_source_lark (Char)
	[Custom] Link Lark Doc chứa CV nhận qua Lark
	CUSTOM
	NO
	 
2. Output Data Table – Kết quả sau xử lý
	No
	Field
	Odoo 19 Model & Field
	Mô tả
	Data Type
	1
	Applicant ID
	hr.applicant – id
	Primary Key tự tăng
	Integer
	2
	Stage (Current)
	hr.applicant – stage_id
	Stage hiện tại sau khi di chuyển, log vào chatter
	M2O
	3
	Kanban State
	hr.applicant – kanban_state (Selection)
	'normal'(xám) | 'done'(xanh) | 'blocked'(đỏ) — HR cập nhật thủ công
	Selection
	4
	Date Last Stage Update
	hr.applicant – date_last_stage_update (Datetime)
	Tự động cập nhật khi thay đổi stage — Odoo Standard
	Datetime
	5
	Active (Refused/Not)
	hr.applicant – active (Boolean)
	True = đang xử lý; False = đã Refused/Archived
	Boolean
	6
	Refuse Reason
	hr.applicant – refuse_reason_id (M2O)
	Lý do từ chối (Standard model hr.applicant.refuse.reason)
	M2O
	7
	Date Closed
	hr.applicant – date_closed (Datetime)
	Thời điểm ứng viên bị Refused hoặc Hired
	Datetime
	8
	Employee (Created)
	hr.applicant – emp_id (M2O hr.employee)
	Liên kết sang hồ sơ nhân viên sau khi nhấn [Create Employee]
	M2O
	9
	Date Hired
	hr.applicant – date_closed (khi hired_stage=True)
	Tự động ghi nhận khi vào stage có Hired Stage = True
	Datetime
	 
3. Processing Logic / Quy tắc xử lý
	Logic 1 – [ODOO STANDARD] Phát hiện ứng viên trùng lặp (Duplicate Candidate Detection):
Khi tạo hr.applicant với email_from đã tồn tại trong res.partner, Odoo 19 tự động liên kết vào partner cũ thay vì tạo mới. HR Officer sẽ thấy cảnh báo 'This candidate already has an application' nếu trùng cả email lẫn job_id.
Logic 2 – [ODOO STANDARD] Email tự động theo Stage (Automated Email on Stage Change):
Khi hr.applicant.stage_id thay đổi, Odoo kiểm tra stage mới có Email Template không. Nếu có → gửi email tự động tới email_from. HR có thể override template trong cài đặt Stage (Recruitment ▸ Configuration ▸ Stages).
Logic 3 – [ODOO STANDARD] Kanban State Color Coding:
  • kanban_state = 'normal' → ● Xám: đang xử lý bình thường
  • kanban_state = 'done'   → ● Xanh: sẵn sàng chuyển sang stage tiếp theo
  • kanban_state = 'blocked'→ ● Đỏ: bị chặn, cần xử lý vấn đề trước
Logic 4 – [ODOO STANDARD] Multi-position Application (R-SYS-04 Học Bá):
Một ứng viên (res.partner) được phép có NHIỀU hr.applicant với NHIỀU job_id khác nhau. Mỗi hr.applicant là bản ghi độc lập trên Kanban riêng của từng Job Position. HR Officer của từng vị trí quản lý độc lập, tránh trùng lặp tiếp cận.
Logic 5 – [CUSTOM] Conditional Display & Validation cho Demo giảng dạy:
Đây là yêu cầu tùy biến — implement trong module x_hb_recruitment_ext:
  • Trường x_demo_teaching_date và x_demo_teaching_result chỉ hiển thị khi job_id.x_teaching_level != 'na'
  • @api.constrains: nếu stage_id.name == 'Demo giảng dạy' và x_demo_teaching_result == 'na' → raise ValidationError
Logic 6 – [CUSTOM] Cảnh báo trùng ứng viên cross-position tới HR Officer:
Khi tạo hr.applicant mới, kiểm tra xem partner_id đã có hr.applicant active ở job_id KHÁC chưa. Nếu có → hiển thị Warning (không chặn): 'Ứng viên này đang trong pipeline của [Tên vị trí khác]. Vui lòng phối hợp với HR phụ trách.'
	

 
5. SCREEN DEFINITION
Screen Definition
	Function ID
	FS-REC-002
	Function Name
	Applicant Tracking
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Page Title
	Applications – Học Bá Education HRM (Odoo 19)
	 
1. Applicant Form View – Field Definitions
	No
	Field Name
	UI Type
	I/O
	Data Type
	Length
	Required
	Default
	S/C
	Remarks
	1
	Candidate Name
	Text Input
	I/O
	CHAR
	128
	YES
	—
	S
	hr.applicant – partner_name
	2
	Email
	Email Input
	I/O
	CHAR
	254
	YES
	—
	S
	hr.applicant – email_from
	3
	Phone
	Tel Input
	I/O
	CHAR
	32
	YES
	—
	S
	hr.applicant – partner_phone
	4
	Job Position
	M2O Dropdown
	I/O
	INT FK
	—
	YES
	—
	S
	hr.applicant – job_id
	5
	Department
	M2O (Auto)
	O
	INT FK
	—
	Auto
	From job
	S
	hr.applicant – department_id
	6
	Stage (Status Bar)
	Status Bar / M2O
	I/O
	INT FK
	—
	Auto
	New
	S
	hr.applicant – stage_id
	7
	Kanban State
	Color Badge
	I/O
	Selection
	—
	NO
	normal
	S
	normal/done/blocked
	8
	Recruiter
	M2O Dropdown
	I/O
	INT FK
	—
	Auto
	Current user
	S
	hr.applicant – user_id
	9
	Interviewer(s)
	M2M Tags
	I/O
	INT FK
	—
	NO
	—
	S
	hr.applicant – interviewer_ids
	10
	Expected Salary
	Monetary Input
	I/O
	FLOAT
	—
	NO
	0.0
	S
	hr.applicant – salary_expected
	11
	Tags
	M2M Tags
	I/O
	INT FK
	—
	NO
	—
	S
	hr.applicant – tag_ids
	12
	Source
	M2O Dropdown
	I/O
	INT FK
	—
	NO
	—
	S
	hr.applicant – source_id
	13
	Demo Teaching Date
	Date Picker
	I/O
	DATE
	—
	COND
	—
	C
	x_demo_teaching_date (GV only)
	14
	Demo Result
	Selection Dropdown
	I/O
	CHAR
	10
	COND
	na
	C
	x_demo_teaching_result: pass/fail/na
	15
	CV Source Lark
	URL Input
	I/O
	CHAR
	512
	NO
	—
	C
	x_cv_source_lark – link Lark Doc
	Legend: S = Odoo Standard  |  C = Custom Development  |  COND = Conditional Required  |  Auto = Auto-populated
	

 
6. STANDARD vs CUSTOM GAP ANALYSIS MATRIX
Standard vs Custom GAP Analysis Matrix – FS-REC-002
	Feature / Tính năng
	Odoo 19 Standard
	Custom (x_hb_recruitment_ext)
	Ghi chú
	hr.applicant CRUD & Kanban Pipeline
	✓
	 
	Core Recruitment module – Standard
	6 Default Stages (New → Contract Signed)
	✓
	 
	hr.recruitment.stage – Standard
	Kanban State (●Xanh / ●Đỏ / ●Xám)
	✓
	 
	kanban_state field – Standard
	Email Template tự động theo Stage
	✓
	 
	Stage.email_template_id – Standard
	Refuse Applicant + Refuse Reason
	✓
	 
	hr.applicant.refuse.reason – Standard
	Multi-position: 1 Partner → N Applicants
	✓
	 
	res.partner + hr.applicant M2O – Standard
	Create Employee từ ứng viên
	✓
	 
	Button [Create Employee] – Standard
	Duplicate Candidate Detection (email)
	✓
	 
	Auto partner matching – Standard
	Activity (Phone/Meeting/To-Do)
	✓
	 
	mail.activity – Standard
	Tags / Appreciation Rating
	✓
	 
	tag_ids / priority – Standard
	Stage 'Demo giảng dạy' (Job Specific)
	 
	✓ Cấu hình Custom Stage
	Job Specific = Giảng viên/Trợ giảng
	x_demo_teaching_date + x_demo_teaching_result
	 
	✓ Custom fields trên hr.applicant
	Conditional display & validation
	x_cv_source_lark (Link Lark CV)
	 
	✓ Custom field trên hr.applicant
	Gắn kết workflow Lark → Odoo
	Cross-position Warning cho HR
	 
	✓ Custom @api.onchange warning
	Cảnh báo không chặn – UX
	 
Supplement / Ghi chú kỹ thuật & Nguồn tham chiếu
	Odoo Module Dependencies:
  • hr_recruitment (hr.applicant, hr.recruitment.stage, hr.applicant.refuse.reason)
  • mail (mail.activity, chatter, email templates)
  • hr (hr.employee – liên kết khi Create Employee)
  • website_hr_recruitment (tiếp nhận apply từ website)
Custom Module: x_hb_recruitment_ext
  • Inherit hr.applicant: thêm x_demo_teaching_date, x_demo_teaching_result, x_cv_source_lark
  • Tạo Custom Stage 'Demo giảng dạy' với Job Specific = các job_id Giảng viên/Trợ giảng
  • @api.constrains cho validation demo result theo stage
  • @api.onchange cho cross-position warning
Liên kết với các FS khác:
  • FS-REC-001 (Job Position): hr.job là parent của hr.applicant qua job_id
  • FS-REC-003 (Interview Workflow): Stage 'Phỏng vấn HR/CM' trong pipeline này dẫn sang luồng phỏng vấn
  • FS-REC-004 (Offer Management): Stage 'Đề xuất hợp đồng' dẫn sang luồng gửi offer
Nguồn tham chiếu:
  • Odoo 19.0 Docs – Recruitment Flow: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/recruitment-flow.html
  • Odoo 19.0 Docs – Add New Applicants: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/add-new-applicants.html
  • Tài liệu nghiệp vụ Học Bá: R-SYS-04 (Multi-position applicant), 7.2 Phiếu yêu cầu tuyển dụng
	 


FS-REC-003 Interview Workflow
COVER
FUNCTIONAL SPECIFICATION
HRM ODOO – HỌC BÁ EDUCATION
	 
	Module
	REC
	Module Name
	Recruitment
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created Date
	02/06/2026
	Last Update Date
	02/06/2026
	Project
	HRM Odoo – Học Bá Education
	System
	Odoo 19 ERP (Community / Enterprise)
	Reference
	Odoo 19.0 Docs – Schedule Interviews: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/schedule_interviews.html
	 
	 
	Approver
	Reviewer
	Creator
	Name
	Giảng viên hướng dẫn
	—
	Nhóm G2 – ISP490
	Organization
	FPT University
	—
	FPT University
	

 
CHANGE HISTORY
No
	Version
	Description
	Sheet
	Modified Date
	Modified By
	1
	1.0
	Initial creation
	All
	02/06/2026
	Nhóm G2
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	 
	

 
1. FUNCTION OVERVIEW
Function Overview
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Processing Time
	Real-time / On-demand
	Processing Type
	Interactive (UI-driven)
	Function Type
	Transaction Processing
	Multilingual
	Yes (Vietnamese / English)
	 
Business Requirement & Function Overview
	Mô tả tổng quan:
Interview Workflow (Luồng Phỏng vấn) quản lý toàn bộ quy trình lên lịch, thực hiện và ghi nhận kết quả các buổi phỏng vấn trong Odoo 19. Chức năng này bao gồm hai cơ chế chính: (1) Lên lịch phỏng vấn thông qua calendar.event tích hợp với lịch Odoo (và Google Calendar nếu đồng bộ), và (2) Gửi Interview Form (Survey) để đánh giá ứng viên theo tiêu chí chuẩn hóa.
Business Context – Học Bá Education:
Quy trình phỏng vấn tại Học Bá có hai vòng chính: (1) Phỏng vấn HR (do HR Officer thực hiện, đánh giá thái độ và kỹ năng mềm) và (2) Phỏng vấn Chuyên môn (do Trưởng bộ phận / Giảng viên Senior thực hiện, đánh giá năng lực chuyên môn HSK/TOCFL). Riêng vị trí Giảng viên có thêm vòng Demo giảng dạy trực tiếp (Custom Stage – đã mô tả trong FS-REC-002). Thách thức: người phỏng vấn (interviewer) thường không cùng địa điểm vật lý → cần tích hợp Google Meet / Zoom link vào lịch hẹn.
Phạm vi chức năng:
(1) Lên lịch phỏng vấn (Schedule Interview): tạo calendar.event liên kết hr.applicant, tự động gửi lời mời đến ứng viên và interviewer.
(2) Self-service scheduling [Odoo Standard]: ứng viên tự chọn khung giờ phỏng vấn qua link trong email.
(3) Gửi Interview Form (Send Interview / Survey): gửi bộ câu hỏi đánh giá năng lực qua email trước/sau buổi phỏng vấn.
(4) Ghi nhận kết quả phỏng vấn: Appreciation (★ rating), ghi chú nội bộ (Internal Note trên chatter), Kanban State.
(5) [Custom] Scorecard phỏng vấn chuẩn hóa cho Học Bá: thang điểm 1-5 cho từng tiêu chí.
Người dùng: HR Officer (toàn quyền), Interviewer (xem lịch + ghi nhận kết quả), Ứng viên (tự chọn giờ qua link).
	Supplement / Ghi chú bổ sung
	• Odoo 19 Standard tích hợp sẵn calendar.event (model lịch hẹn). Khi tạo lịch phỏng vấn, bản ghi calendar.event được liên kết với hr.applicant qua trường calendar_event_id.
• Interview Form trong Odoo là survey.survey (module Surveys). Kết quả khảo sát được lưu trong survey.user_input liên kết với hr.applicant.
• Self-service scheduling: Odoo 19 gửi link tự động khi ứng viên vào stage có Email Template = 'Recruitment: Schedule Interview'. Automation này tắt theo mặc định.
• Tích hợp Google Calendar: cần kích hoạt module google_calendar và cấu hình OAuth2 — là yêu cầu infrastructure, không phải custom code.
	

 
2. FUNCTION FLOW
Function Flow
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	 
Screen Flow / Luồng Màn hình Chính
	── LUỒNG A: HR lên lịch phỏng vấn thủ công ──
  [A1] HR Officer mở Form View ứng viên đang ở Stage 'Phỏng vấn HR' hoặc 'Phỏng vấn Chuyên môn'
             ↓
  [A2] Nhấn [No Meeting] (hoặc nút lịch trên Chatter) → Pop-up 'New Event' mở ra
             ↓
  [A3] Điền thông tin lịch hẹn: Meeting Title | Start/End datetime | Attendees (ứng viên + interviewer) | Location / Meet link | Reminders
             ↓
  [A4] Nhấn [Email] hoặc [Send] → Odoo gửi email lời mời lịch (.ics) đến tất cả Attendees
             ↓  (Hệ thống tự động)
  [A5] Bản ghi calendar.event được tạo; Smart Button [1 Meeting] xuất hiện trên Form View ứng viên
  [A6] Lịch hẹn đồng bộ sang Google Calendar của Interviewer (nếu đã kích hoạt google_calendar module)
── LUỒNG B: Self-service scheduling (ứng viên tự chọn giờ) ──
  [B1] HR cấu hình Stage 'Phỏng vấn HR' → set Email Template = 'Recruitment: Schedule Interview'
             ↓  (Tự động khi drag ứng viên vào Stage)
  [B2] Odoo gửi email cho ứng viên có chứa nút [Schedule my interview]
             ↓
  [B3] Ứng viên click link → chọn khung giờ trống từ lịch của Recruiter → Confirm
             ↓  (Odoo tự động)
  [B4] calendar.event được tạo, gửi xác nhận cho ứng viên và toàn bộ Attendees
  [B5] Smart Button [1 Meeting] cập nhật trên Form View ứng viên
── LUỒNG C: Gửi Interview Form (Survey) ──
  [C1] HR Officer mở Form View ứng viên → nhấn [Send Interview] (button trên header)
             ↓
  [C2] Pop-up 'Send Interview' xuất hiện: chọn Survey (Interview Form đã tạo trên hr.job) → chọn Template email → [Send]
             ↓
  [C3] Ứng viên nhận email, click link → hoàn thành survey trên browser (không cần đăng nhập Odoo)
             ↓
  [C4] Kết quả survey.user_input được lưu và hiển thị trên chatter của hr.applicant; HR xem kết quả
── LUỒNG D: Ghi nhận kết quả phỏng vấn & quyết định ──
  [D1] Sau buổi phỏng vấn, Interviewer mở Form View ứng viên → cập nhật:
           • Appreciation (★★★ rating: 1=Good / 2=Very Good / 3=Excellent)
           • Kanban State: ●Xanh (Sẵn sàng chuyển tiếp) / ●Đỏ (Cần xem xét thêm)
           • Internal Note (chatter): ghi nhận nhận xét phỏng vấn chi tiết
  [D2] [Custom Scorecard] HR điền bảng điểm Học Bá (x_interview_score_xxx fields)
             ↓
  [D3] HR Officer quyết định: Chuyển sang Stage tiếp theo (Pass) hoặc Refuse (Fail)
             ↓
  [D4] Nếu Pass → Drag sang 'Phỏng vấn Chuyên môn' hoặc 'Đề xuất hợp đồng'
	Error / Exception Flow
	  • Attendee không có email → Odoo không gửi được lời mời; hệ thống hiển thị cảnh báo 'No email found for attendee [Name]'.
  • Self-service link hết hạn (sau 7 ngày mặc định) → ứng viên thấy thông báo lỗi, HR cần gửi lại email.
  • Google Calendar chưa đồng bộ → calendar.event chỉ lưu trong Odoo, không xuất hiện trên Google Calendar của Interviewer. HR cần hướng dẫn cấu hình OAuth2.
  • [Custom] Demo giảng dạy: nếu x_demo_teaching_result chưa điền khi chuyển sang Stage 'Đề xuất hợp đồng' → ValidationError (đã mô tả FS-REC-002, Logic 5).
	

 
3. SCREEN LAYOUT
Screen Layout
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	 
Screen 1: Schedule Interview Pop-up (Odoo Standard – calendar.event)
	Trigger: Nhấn [No Meeting] hoặc Activity 'Phone Call / Meeting' trên Form View ứng viên
Fields trên New Event pop-up:
  • Meeting Title*: mặc định = [Tên ứng viên] – [Tên vị trí]
  • Start / End*: Date-time picker (bắt buộc)
  • All Day: Checkbox (nếu tick, Start/End chuyển thành Date Only)
  • Attendees: M2M res.partner — mặc định = ứng viên + Recruiter. Thêm Interviewer thủ công
  • Location: text field — nhập địa chỉ hoặc paste Google Meet / Zoom link
  • Reminders: M2M (5 phút, 1 giờ, 1 ngày trước — Odoo Standard)
  • Mail Template: chọn email template gửi lời mời (mặc định: Recruitment: Schedule Interview)
Buttons: [Email] (gửi lời mời + tạo event) | [Save] (chỉ tạo event, không gửi email) | [Discard]
	Screen 2: Calendar View – Applicant Meetings (Odoo Standard)
	Truy cập: Smart Button [# Meeting] trên Applicant Form View → mở Calendar View lọc theo applicant
Hiển thị: Lịch hẹn dạng Calendar (Day/Week/Month view). Màu event theo Recruiter/Interviewer.
Truy cập tổng hợp: Recruitment ▸ Reporting ▸ All Meetings → xem toàn bộ lịch phỏng vấn của tất cả ứng viên (nếu có quyền HR Manager)
	Screen 3: Send Interview Form Pop-up (Odoo Standard – survey.survey)
	Trigger: Nhấn [Send Interview] trên Applicant Form View
Fields:
  • Survey*: M2O survey.survey — chọn Interview Form đã tạo tại hr.job
  • Email Template: M2O mail.template — template gửi link survey
  • Deadline: Date — hạn chót hoàn thành survey
  • To: email ứng viên (tự động điền từ email_from)
Buttons: [Send] | [Cancel]
	Screen 4: Interview Scorecard – Custom Tab 'Phỏng vấn' (x_hb_recruitment_ext)
	Vị trí: Tab mới 'Phỏng vấn Học Bá' thêm vào Applicant Form View (inherit view)
Bảng điểm Phỏng vấn HR (hiển thị với tất cả vị trí):
  • x_score_communication (Integer 1-5): Kỹ năng giao tiếp
  • x_score_attitude         (Integer 1-5): Thái độ / Phong cách làm việc
  • x_score_culture_fit  (Integer 1-5): Phù hợp văn hóa Học Bá
  • x_hr_interview_note  (Text): Nhận xét tổng hợp của HR
Bảng điểm Phỏng vấn Chuyên môn (chỉ hiển thị khi job_id thuộc nhóm Giảng viên/Trợ giảng):
  • x_score_subject_knowledge (Integer 1-5): Kiến thức chuyên môn HSK/TOCFL
  • x_score_teaching_method   (Integer 1-5): Phương pháp giảng dạy
  • x_score_classroom_mgmt        (Integer 1-5): Quản lý lớp học
  • x_expert_interview_note   (Text): Nhận xét của Trưởng bộ phận
Computed field [Custom]:
  • x_total_score (Float, Computed): Trung bình cộng các điểm thành phần đã chấm — hiển thị dạng badge màu (≥4: xanh, 2-4: cam, <2: đỏ)
	

 
4. PROCESSING DESCRIPTION
Processing Description
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Created date
	02/06/2026
	Modified date
	02/06/2026
	 
1. Input Data Table – Schedule Interview & Interview Form Fields
	No
	Field
	Odoo 19 Model & Field
	Validation / Ghi chú
	S / C
	Required
	1
	Meeting Title
	calendar.event – name (Char)
	Mặc định: '[Candidate] – [Job Position]'. Có thể sửa
	Standard
	YES
	2
	Start Datetime
	calendar.event – start (Datetime)
	Phải > now(). Kiểm tra conflict với lịch Interviewer
	Standard
	YES
	3
	End Datetime
	calendar.event – stop (Datetime)
	Phải > start. Duration tối thiểu 15 phút
	Standard
	YES
	4
	All Day
	calendar.event – allday (Boolean)
	Nếu True, bỏ qua trường giờ
	Standard
	NO
	5
	Attendees
	calendar.event – partner_ids (M2M res.partner)
	Phải có ít nhất Recruiter. Ứng viên tự động thêm
	Standard
	YES
	6
	Location
	calendar.event – location (Char)
	Địa chỉ vật lý hoặc Meeting link (Zoom/Meet)
	Standard
	NO
	7
	Reminders
	calendar.event – alarm_ids (M2M calendar.alarm)
	Tùy chọn: 5min/1h/1day trước. Gửi email/notification
	Standard
	NO
	8
	Mail Template
	mail.template liên kết calendar.event
	Mặc định: 'Recruitment: Schedule Interview'
	Standard
	NO
	9
	Survey (Interview Form)
	survey.survey – id (M2O từ hr.job.survey_id)
	Chọn từ danh sách survey active. Tạo từ Job Position form
	Standard
	YES (khi Send)
	10
	Survey Deadline
	survey.user_input – deadline (Date)
	Hạn chót ứng viên hoàn thành form. Không bắt buộc
	Standard
	NO
	11
	Score Communication [C]
	hr.applicant – x_score_communication (Integer)
	Range: 1–5. Visible tất cả vị trí
	CUSTOM
	NO
	12
	Score Attitude [C]
	hr.applicant – x_score_attitude (Integer)
	Range: 1–5. Visible tất cả vị trí
	CUSTOM
	NO
	13
	Score Culture Fit [C]
	hr.applicant – x_score_culture_fit (Integer)
	Range: 1–5. Visible tất cả vị trí
	CUSTOM
	NO
	14
	Score Subject Knowledge [C]
	hr.applicant – x_score_subject_knowledge (Integer)
	Range: 1–5. Chỉ hiện với vị trí Giảng viên/TG
	CUSTOM
	COND
	15
	Score Teaching Method [C]
	hr.applicant – x_score_teaching_method (Integer)
	Range: 1–5. Chỉ hiện với vị trí Giảng viên/TG
	CUSTOM
	COND
	16
	Score Classroom Mgmt [C]
	hr.applicant – x_score_classroom_mgmt (Integer)
	Range: 1–5. Chỉ hiện với vị trí Giảng viên/TG
	CUSTOM
	COND
	17
	HR Interview Note [C]
	hr.applicant – x_hr_interview_note (Text)
	Nhận xét tổng hợp của HR Officer sau phỏng vấn
	CUSTOM
	NO
	18
	Expert Interview Note [C]
	hr.applicant – x_expert_interview_note (Text)
	Nhận xét của Trưởng bộ phận / Giảng viên Senior
	CUSTOM
	NO
	 
2. Output Data Table – Kết quả sau xử lý phỏng vấn
	No
	Field
	Odoo 19 Model & Field
	Mô tả
	Data Type
	1
	Calendar Event ID
	calendar.event – id
	ID lịch hẹn phỏng vấn; liên kết với hr.applicant qua calendar_event_id
	Integer
	2
	Meeting Count (Smart Btn)
	hr.applicant – meeting_count (Computed)
	COUNT calendar.event liên kết applicant — hiển thị Smart Button
	Integer
	3
	Survey Response
	survey.user_input – id
	Bản ghi kết quả ứng viên hoàn thành Interview Form
	Integer
	4
	Survey Score
	survey.user_input – scoring_percentage
	% điểm survey tự động tính nếu survey có điểm (Odoo Standard)
	Float
	5
	Appreciation
	hr.applicant – priority (Selection)
	'0'=Normal / '1'=Good / '2'=Very Good / '3'=Excellent
	Selection
	6
	Kanban State
	hr.applicant – kanban_state
	'normal'/'done'/'blocked' — HR cập nhật thủ công sau phỏng vấn
	Selection
	7
	Total Score (Custom)
	hr.applicant – x_total_score (Computed Float)
	Avg của tất cả x_score_xxx đã điền. Tính lại khi lưu
	Float
	8
	Chatter Log
	mail.message liên kết hr.applicant
	Tự động log: stage change, email sent, internal notes, activity done
	Text
	 
3. Processing Logic / Quy tắc xử lý
	Logic 1 – [ODOO STANDARD] Tự động gửi email lịch phỏng vấn khi tạo calendar.event:
Khi HR nhấn [Email] trong New Event pop-up, Odoo gọi method calendar.event.write() → trigger _send_mail_to_attendees() → gửi email có file .ics đính kèm tới partner_ids. Mỗi Attendee nhận một email riêng với Accept/Decline buttons.
Logic 2 – [ODOO STANDARD] Self-service scheduling (Recruitment: Schedule Interview template):
Khi ứng viên vào stage có Email Template = 'Recruitment: Schedule Interview', Odoo gửi email chứa link booking có token unique (valid 7 ngày). Link dẫn tới trang calendar booking hiển thị các khung giờ trống của Recruiter. Sau khi ứng viên chọn, Odoo tự động tạo calendar.event và gửi xác nhận cho cả hai bên.
Logic 3 – [ODOO STANDARD] Survey Token & Access Control:
Mỗi survey.user_input có access_token unique. Ứng viên truy cập link survey không cần đăng nhập Odoo. Sau khi submit, survey.user_input.state = 'done'. HR xem kết quả từ Chatter của hr.applicant (link 'View Answers').
Logic 4 – [CUSTOM] Tính điểm tổng hợp x_total_score:
Implement trong x_hb_recruitment_ext:
  @api.depends('x_score_communication','x_score_attitude','x_score_culture_fit',
               'x_score_subject_knowledge','x_score_teaching_method','x_score_classroom_mgmt')
  def _compute_total_score(self):
          for rec in self:
              scores = [s for s in [rec.x_score_communication, rec.x_score_attitude,
                        rec.x_score_culture_fit, rec.x_score_subject_knowledge,
                    rec.x_score_teaching_method, rec.x_score_classroom_mgmt] if s]
              rec.x_total_score = sum(scores)/len(scores) if scores else 0.0
Logic 5 – [CUSTOM] Conditional visibility Scorecard Chuyên môn:
Dùng attrs domain trên view: {'invisible': [('job_id.x_teaching_level','=','na')]}
→ Nhóm điểm Chuyên môn (x_score_subject_knowledge, x_score_teaching_method, x_score_classroom_mgmt, x_expert_interview_note) chỉ hiển thị khi x_teaching_level != 'na'.
Logic 6 – [ODOO STANDARD] Phòng ngừa lịch chồng chéo (Conflict Detection):
Khi tạo calendar.event, Odoo kiểm tra calendar.event của cùng partner trong cùng khung giờ. Nếu phát hiện xung đột → cảnh báo 'This event overlaps with [Event Name]'. HR có thể Override hoặc chọn giờ khác.
	

 
5. SCREEN DEFINITION
Screen Definition
	Function ID
	FS-REC-003
	Function Name
	Interview Workflow
	Created by
	Nhóm G2 – ISP490
	Modified by
	Nhóm G2 – ISP490
	Page Title
	Interview Workflow – Học Bá Education HRM (Odoo 19)
	 
1. Schedule Interview Pop-up + Scorecard Tab – Field Definitions
	No
	Field Name
	UI Type
	I/O
	Data Type
	Length
	Required
	Default
	S/C
	Remarks
	1
	Meeting Title
	Text Input
	I/O
	CHAR
	256
	YES
	[Cand-Job]
	S
	calendar.event – name
	2
	Start Datetime
	Datetime Picker
	I/O
	DATETIME
	—
	YES
	Now+1h
	S
	calendar.event – start
	3
	End Datetime
	Datetime Picker
	I/O
	DATETIME
	—
	YES
	Start+1h
	S
	calendar.event – stop
	4
	Attendees
	M2M Tags
	I/O
	INT FK
	—
	YES
	Cand+Recruiter
	S
	calendar.event – partner_ids
	5
	Location
	Text Input
	I/O
	CHAR
	512
	NO
	—
	S
	calendar.event – location
	6
	Reminders
	M2M Dropdown
	I/O
	INT FK
	—
	NO
	—
	S
	calendar.alarm – alarm_ids
	7
	Mail Template
	M2O Dropdown
	I/O
	INT FK
	—
	NO
	Sched.Interview
	S
	mail.template liên kết
	8
	Survey (Interview Form)
	M2O Dropdown
	I/O
	INT FK
	—
	YES*
	From hr.job
	S
	survey.survey – id (*khi Send Interview)
	9
	Score Communication
	Integer (1-5)
	I/O
	INTEGER
	1
	NO
	—
	C
	x_score_communication
	10
	Score Attitude
	Integer (1-5)
	I/O
	INTEGER
	1
	NO
	—
	C
	x_score_attitude
	11
	Score Culture Fit
	Integer (1-5)
	I/O
	INTEGER
	1
	NO
	—
	C
	x_score_culture_fit
	12
	Score Subj. Knowledge
	Integer (1-5)
	I/O
	INTEGER
	1
	COND
	—
	C
	x_score_subject_knowledge (GV/TG only)
	13
	Score Teaching Method
	Integer (1-5)
	I/O
	INTEGER
	1
	COND
	—
	C
	x_score_teaching_method (GV/TG only)
	14
	Score Classroom Mgmt
	Integer (1-5)
	I/O
	INTEGER
	1
	COND
	—
	C
	x_score_classroom_mgmt (GV/TG only)
	15
	Total Score
	Float Badge (Computed)
	O
	FLOAT
	—
	—
	Computed
	C
	x_total_score – avg of filled scores
	16
	HR Interview Note
	Text Area
	I/O
	TEXT
	—
	NO
	—
	C
	x_hr_interview_note
	17
	Expert Interview Note
	Text Area
	I/O
	TEXT
	—
	NO
	—
	C
	x_expert_interview_note (GV/TG only)
	Legend: S = Odoo Standard  |  C = Custom  |  COND = Conditional Required  |  GV/TG = Giảng viên / Trợ giảng only
	

 
6. STANDARD vs CUSTOM GAP ANALYSIS MATRIX
Standard vs Custom GAP Analysis Matrix – FS-REC-003
	Feature / Tính năng
	Odoo 19 Standard
	Custom (x_hb_recruitment_ext)
	Ghi chú
	Schedule Interview (calendar.event)
	✓
	 
	calendar module – Standard
	Email lời mời có file .ics
	✓
	 
	_send_mail_to_attendees – Standard
	Self-service scheduling (booking link)
	✓
	 
	Template 'Schedule Interview' – Standard (tắt mặc định)
	Smart Button [# Meeting] trên Applicant
	✓
	 
	meeting_count Computed – Standard
	Send Interview Form (Survey)
	✓
	 
	survey.survey + user_input – Standard
	Appreciation Rating (★ 0-3)
	✓
	 
	hr.applicant – priority field – Standard
	Calendar Conflict Detection
	✓
	 
	Odoo calendar overlap check – Standard
	Google Calendar Sync
	✓
	 
	google_calendar module – Standard (cần cấu hình OAuth2)
	Reminders / Notifications
	✓
	 
	calendar.alarm – Standard
	Interview Scorecard (5 tiêu chí HR)
	 
	✓ 3 custom fields + note
	x_score_communication/attitude/culture_fit
	Scorecard Chuyên môn (3 tiêu chí GV)
	 
	✓ 3 custom fields – cond.display
	x_score_subject/teaching/classroom
	x_total_score (Computed avg)
	 
	✓ @api.depends computed
	Badge màu: xanh/cam/đỏ theo ngưỡng
	Conditional visibility Scorecard CM
	 
	✓ attrs domain trong XML view
	Chỉ hiện nếu x_teaching_level != 'na'
	 
Supplement / Ghi chú kỹ thuật & Nguồn tham chiếu
	Odoo Module Dependencies:
  • calendar (calendar.event, calendar.alarm)
  • hr_recruitment (hr.applicant – calendar_event_id, meeting_count)
  • survey (survey.survey, survey.user_input)
  • google_calendar (Google Calendar OAuth2 sync — optional, cần cấu hình)
  • mail (mail.template, mail.activity)
Custom Module: x_hb_recruitment_ext (tiếp nối từ FS-REC-002)
  • Thêm fields x_score_xxx vào hr.applicant
  • Computed field x_total_score với @api.depends
  • Inherit view hr.applicant.form: thêm Tab 'Phỏng vấn Học Bá' với attrs conditional visibility
  • Widget badge color cho x_total_score (dùng widget='badge' + decoration-success/warning/danger)
Cấu hình yêu cầu trước khi Go-Live:
  [1] Tạo Interview Forms (survey.survey) cho từng nhóm vị trí: GV-HSK2/3/TOCFL, TVTS, Hành chính
  [2] Gán Interview Form vào hr.job tương ứng (trường survey_id trên Job Position form)
  [3] Cấu hình Email Template 'Recruitment: Schedule Interview' → set trên Stage 'Phỏng vấn HR'
  [4] (Optional) Kích hoạt google_calendar, cấu hình OAuth2 cho tài khoản Google Workspace Học Bá
Liên kết với các FS khác:
  • FS-REC-002 (Applicant Tracking): Stage 'Phỏng vấn HR/CM' là điểm kết nối
  • FS-REC-004 (Offer Management): Sau khi qua Interview Workflow, ứng viên chuyển sang Offer stage
Nguồn tham chiếu:
  • Odoo 19.0 Docs – Schedule Interviews: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/schedule_interviews.html
  • Odoo 19.0 Docs – Recruitment Flow: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/recruitment-flow.html
  • Odoo 19.0 Docs – Job Positions (Interview Form): https://www.odoo.com/documentation/19.0/applications/hr/recruitment/new_job.html
	 


FS-REC-004 Offer Management
COVER
FUNCTIONAL SPECIFICATION
HRM ODOO – HỌC BÁ EDUCATION
	

	Module
	REC
	Module Name
	Recruitment
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created Date
	02/06/2026
	Last Update Date
	02/06/2026
	Project
	HRM Odoo – Học Bá Education
	System
	Odoo 19 ERP (Community / Enterprise)
	Reference
	Odoo 19.0 Docs – Offer Job Positions: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/offer_job_positions.html
	

	

	Approver
	Reviewer
	Creator
	Name
	Giảng viên hướng dẫn
	—
	Nhóm G3 – SAP490
	Organization
	FPT University
	—
	FPT University
	________________


CHANGE HISTORY
No
	Version
	Description
	Sheet
	Modified Date
	Modified By
	1
	1.0
	Initial creation
	All
	02/06/2026
	Nhóm G3
	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	

	________________


1. FUNCTION OVERVIEW
Function Overview
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created by
	Nhóm G3 – SAP490
	Modified by
	Nhóm G3 – SAP490
	Processing Time
	Real-time / On-demand
	Processing Type
	Interactive (UI-driven)
	Function Type
	Transaction Processing
	Multilingual
	Yes (Vietnamese / English)
	

Business Requirement & Function Overview
	Mô tả tổng quan:
Offer Management (Quản lý Đề xuất & Ký hợp đồng) là chức năng cuối của Module Recruitment trong Odoo 19, đánh dấu giai đoạn chuyển đổi ứng viên (hr.applicant) thành nhân viên chính thức (hr.employee). Chức năng bao gồm: tạo và gửi thư đề nghị làm việc (Offer Letter), thu thập ký hợp đồng điện tử qua Odoo Sign, và tạo hồ sơ nhân viên từ dữ liệu ứng viên.
Business Context – Học Bá Education:
Học Bá Education ký hai loại hợp đồng chính: (1) Hợp đồng lao động toàn thời gian (cho Tư vấn tuyển sinh, Hành chính) và (2) Hợp đồng cộng tác viên / Hợp đồng dịch vụ (cho Giảng viên theo buổi/module). Điểm đặc thù: Giảng viên thường nhận offer bao gồm cả phân công lớp học sơ bộ ngay trong thư đề nghị — thông tin này cần tích hợp sang Module Timesheets/Class Management sau khi onboard.
Phạm vi chức năng:
(1) [Standard] Generate Offer: tạo liên kết offer page để ứng viên xem điều kiện lương và nhập thông tin cá nhân trực tuyến.
(2) [Standard] Gửi Offer Letter qua email với nút [Review Contract & Sign] — tích hợp Odoo Sign (module sign).
(3) [Standard] Ứng viên ký hợp đồng điện tử (e-signature) qua trình duyệt, không cần cài phần mềm.
(4) [Standard] Chuyển Stage: Contract Proposal → Contract Signed khi hợp đồng được ký; banner HIRED xuất hiện.
(5) [Standard] Create Employee: tạo hr.employee từ hr.applicant, import dữ liệu cá nhân ứng viên đã nhập.
(6) [Custom] Thư đề nghị Học Bá: template tùy chỉnh bằng tiếng Việt, có thêm mục Phân công lớp sơ bộ cho Giảng viên.
Người dùng: HR Officer (toàn quyền tạo offer + tạo nhân viên), BOD (phê duyệt offer lương cao ≥ ngưỡng tùy chỉnh).
	Supplement / Ghi chú bổ sung
	• Odoo 19 sử dụng cơ chế 'Generate Offer' thay vì tạo hr.contract trực tiếp tại đây. Hợp đồng lao động chính thức (hr.contract) được tạo ở Module Payroll sau khi nhân viên được onboard.
• Tính năng 'Configure your package' (ứng viên tự điều chỉnh gói lương) KHÔNG khả dụng với localization Việt Nam — đây là tính năng theo localization (Bỉ, Pháp...). Tại Học Bá, HR sẽ cố định mức lương đề nghị.
• Odoo Sign (module sign) phải được cài đặt trước khi sử dụng e-signature. Contract Template được tạo tại Payroll ▸ Configuration ▸ Contract Templates.
• Nguồn: Odoo 19.0 Docs – Offer Job Positions & Contracts.
	________________


2. FUNCTION FLOW
Function Flow
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created by
	Nhóm G3 – SAP490
	Modified by
	Nhóm G3 – SAP490
	

Screen Flow / Luồng Màn hình Chính
	── LUỒNG A: Gửi Offer Letter (Generate Offer) ──
  [A1] HR Officer kéo thẻ ứng viên vào Stage 'Đề xuất hợp đồng' (Contract Proposal) trên Kanban
         ↓
  [A2] Mở Form View ứng viên → Nhấn [Generate Offer]
         ↓
  [A3] Trang 'Offer for [email ứng viên]' tải ra — điền các thông tin:
       • Contract Template (M2O): chọn mẫu hợp đồng phù hợp
       • Job Position / Department (auto từ hr.applicant)
       • Start Date: ngày bắt đầu làm việc dự kiến
       • Wage: mức lương đề nghị (VND)
       • Contract Type: Toàn thời gian / CTV / Dịch vụ
         ↓
  [A4] Nhấn [Send Offer by Email] → Pop-up email mở ra, có thể chỉnh Subject/Body → [Send]
         ↓  Odoo tự động
  [A5] Email gửi đến ứng viên, trong email có nút [Review Contract & Sign] liên kết tới Odoo Sign
  [A6] Log ghi vào Chatter của hr.applicant: 'Offer sent on [date]'
── LUỒNG B: Ứng viên ký hợp đồng điện tử ──
  [B1] Ứng viên nhận email → nhấn [Review Contract & Sign]
         ↓
  [B2] Trình duyệt mở trang Odoo Sign (không cần tài khoản Odoo). Ứng viên xem nội dung hợp đồng PDF
  [B3] Ứng viên nhập thông tin cá nhân (họ tên, CCCD, địa chỉ...) vào các trường trên form
         ↓
  [B4] Ứng viên ký điện tử (vẽ chữ ký hoặc upload ảnh chữ ký) → [Sign & Submit]
         ↓  Odoo tự động
  [B5] Hệ thống ghi nhận: sign.request.item.state = 'signed'. Gửi bản hợp đồng đã ký cho ứng viên và HR
  [B6] Khi tất cả bên ký xong → sign.request.state = 'signed'
── LUỒNG C: Xác nhận Hired & Tạo nhân viên ──
  [C1] HR Officer xác nhận hợp đồng ký thành công → kéo thẻ sang Stage 'Ký hợp đồng' (Contract Signed)
         ↓  Odoo tự động (vì hired_stage = True)
  [C2] Banner HIRED (màu xanh) xuất hiện góc trên phải thẻ ứng viên
  [C3] hr.applicant.date_closed = today; hr.job.no_of_hired_employee tự động tăng +1
         ↓
  [C4] HR nhấn [Create Employee] → Odoo tạo hr.employee với dữ liệu được import từ hr.applicant và thông tin ứng viên đã nhập trên Offer page
  [C5] Liên kết hr.applicant.emp_id → hr.employee.id được thiết lập
  [C6] HR hoàn chỉnh hồ sơ nhân viên trong Module Employees (ảnh, thông tin cá nhân, tài khoản ngân hàng...)
── LUỒNG D: [Custom] Phê duyệt Offer lương cao ──
  [D1] Nếu Wage trong offer > x_offer_approval_threshold (ngưỡng cấu hình) → Workflow phê duyệt kích hoạt
  [D2] HR Officer submit offer → Trạng thái offer: 'Chờ phê duyệt' → Gửi thông báo cho BOD
  [D3] BOD mở link approval → [Approve] hoặc [Reject with reason]
  [D4] Nếu Approve → HR Officer tiếp tục Luồng A từ bước [A4]
  [D5] Nếu Reject → HR Officer nhận thông báo, xem lý do, điều chỉnh Wage và resubmit
	Error / Exception Flow
	  • Ứng viên không có email → [Generate Offer] báo lỗi: 'Offer link cannot be sent' → HR phải cập nhật email trước.
  • Contract Template chưa được tạo → Dropdown rỗng → HR vào Payroll ▸ Configuration ▸ Contract Templates để tạo trước.
  • Odoo Sign chưa cài → Nút [Review Contract & Sign] không hoạt động → Admin cần cài module sign.
  • Ứng viên không ký trong thời hạn → HR gửi email nhắc nhở thủ công hoặc [Resend] từ sign.request.
  • [Custom] Offer bị Reject bởi BOD → hr.applicant vẫn ở stage 'Đề xuất hợp đồng', không bị archive; HR điều chỉnh lại.
	________________


3. SCREEN LAYOUT
Screen Layout
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created by
	Nhóm G3 – SAP490
	Modified by
	Nhóm G3 – SAP490
	

Screen 1: Applicant Form View – Stage 'Đề xuất hợp đồng' (Odoo Standard)
	Điểm nhận diện: Status Bar hiển thị stage 'Đề xuất hợp đồng' đang active (bold/highlight)
Button chính xuất hiện tại thời điểm này:
  • [Generate Offer]: Mở trang tạo offer, điền thông tin lương & hợp đồng
  • [Refuse]: Từ chối ứng viên bất cứ lúc nào (vẫn khả dụng)
  • [No Meeting] / [1 Meeting]: Smart Button lịch phỏng vấn (từ FS-REC-003)
Thông tin hiển thị trong Tab 'Contract' (Standard):
  • Contract Template | Start Date | Wage | Contract Type | HR Responsible
	Screen 2: Generate Offer Page (Odoo Standard – Offer Configuration)
	Truy cập: Form View ứng viên → [Generate Offer]
Header: 'Offer for [email_from]'
Fields:
  • Contract Template*: M2O hr.contract.type — chọn template từ Payroll ▸ Config ▸ Contract Templates
  • Job Position (auto, readonly): từ hr.applicant.job_id
  • Department (auto, readonly): từ hr.applicant.department_id
  • Job Title: Char — chức danh trên hợp đồng
  • Contract Type*: Selection — Toàn thời gian / CTV / Dịch vụ
  • Start Date*: Date — ngày bắt đầu hợp đồng
  • Wage*: Monetary (VND) — mức lương tháng cơ bản
  • HR Responsible: M2O res.users — người ký phía Học Bá
Buttons: [Send Offer by Email] | [Copy Offer Link] | [Back]
	Screen 3: Send Offer Email Pop-up (Odoo Standard)
	Trigger: Nhấn [Send Offer by Email] trên Generate Offer Page
Fields: To (email ứng viên, auto) | Subject (auto: 'Your Offer – [Job Position]') | Body (từ email template, có thể chỉnh)
Email body chứa nút [Review Contract & Sign] → deep link tới Odoo Sign với token unique
Buttons: [Send] | [Discard]
	Screen 4: Odoo Sign – Contract Review Page (Ứng viên truy cập qua link)
	Không cần đăng nhập Odoo. Giao diện public page của module Sign.
Hiển thị: PDF hợp đồng có các trường ký tên được đánh dấu (highlight màu vàng)
Fields ứng viên điền (từ Contract Template):
  • Họ và tên đầy đủ | Số CCCD | Ngày sinh | Địa chỉ thường trú | Số điện thoại
  • Chữ ký điện tử (vẽ trực tiếp / upload ảnh / font chữ viết tay)
Buttons: [Sign & Submit] | [Download] (xem PDF trước)
	Screen 5: [Custom] Offer Approval Workflow – Tab 'Phê duyệt Offer' (x_hb_recruitment_ext)
	Chỉ hiển thị khi Wage > x_offer_approval_threshold (mặc định: 15,000,000 VND/tháng).
Fields:
  • x_offer_approval_state (Selection): 'draft' / 'pending' / 'approved' / 'rejected'
  • x_offer_approver_id (M2O res.users): người phê duyệt — mặc định là BOD
  • x_offer_approved_date (Datetime): thời điểm phê duyệt
  • x_offer_rejection_reason (Text): lý do từ chối offer (khi BOD reject)
Buttons: [Submit for Approval] (HR) | [Approve] / [Reject] (BOD)
	________________


4. PROCESSING DESCRIPTION
Processing Description
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created by
	Nhóm G3 – SAP490
	Modified by
	Nhóm G3 – SAP490
	Created date
	02/06/2026
	Modified date
	02/06/2026
	

1. Input Data Table – Offer & Contract Fields
	No
	Field
	Odoo 19 Model & Field
	Validation / Ghi chú
	S / C
	Required
	1
	Contract Template
	hr.applicant – contract_id (M2O hr.contract.type)
	Phải chọn từ danh sách template đã tạo tại Payroll
	Standard
	YES
	2
	Job Title
	hr.applicant – categ_ids / job_title (Char)
	Chức danh ghi trên hợp đồng, có thể khác với Job Position
	Standard
	NO
	3
	Contract Type
	hr.applicant – contract_type_id (M2O hr.contract.type)
	Toàn thời gian / CTV / Dịch vụ — liên kết với Payroll
	Standard
	YES
	4
	Start Date
	hr.applicant – date_start (Date)
	Ngày bắt đầu hợp đồng. Phải >= ngày hiện tại
	Standard
	YES
	5
	Wage
	hr.contract – wage (Monetary, VND)
	Mức lương cơ bản tháng. Giá trị > 0
	Standard
	YES
	6
	HR Responsible
	hr.job – user_id (M2O res.users)
	Người đại diện Học Bá ký hợp đồng phía công ty
	Standard
	Rec.
	7
	Họ tên đầy đủ (Sign)
	sign.request.item – trường trên PDF template
	Ứng viên điền trên Odoo Sign page
	Standard
	YES
	8
	Số CCCD (Sign)
	sign.request.item – trường tùy chỉnh trên PDF
	9 hoặc 12 số
	Standard
	YES
	9
	Địa chỉ thường trú (Sign)
	sign.request.item – trường tùy chỉnh trên PDF
	Text free
	Standard
	YES
	10
	Chữ ký điện tử
	sign.request.item – signature field
	Vẽ / upload / font. Bắt buộc để hoàn thành ký
	Standard
	YES
	11
	Offer Approval State [C]
	hr.applicant – x_offer_approval_state (Selection)
	draft/pending/approved/rejected. Kích hoạt khi Wage > ngưỡng
	CUSTOM
	COND
	12
	Offer Approver [C]
	hr.applicant – x_offer_approver_id (M2O res.users)
	Mặc định = BOD. Có thể cấu hình theo phòng ban
	CUSTOM
	COND
	13
	Rejection Reason [C]
	hr.applicant – x_offer_rejection_reason (Text)
	BOD điền khi reject offer. Hiển thị cho HR
	CUSTOM
	COND
	14
	Preliminary Class Assignment [C]
	hr.applicant – x_preliminary_class_ids (M2M x_class)
	Phân công lớp sơ bộ cho Giảng viên — ghi trên thư offer
	CUSTOM
	COND
	

2. Output Data Table – Kết quả sau xử lý Offer & Ký hợp đồng
	No
	Field
	Odoo 19 Model & Field
	Mô tả
	Data Type
	1
	Offer URL / Token
	sign.request – access_token (Char)
	URL unique gửi cho ứng viên. Hết hạn sau thời gian cấu hình
	Char
	2
	Sign Request ID
	sign.request – id (Integer)
	Bản ghi yêu cầu ký; liên kết với hr.applicant
	Integer
	3
	Sign Request State
	sign.request – state (Selection)
	'sent'→'signed'→'canceled'. Tự động cập nhật
	Selection
	4
	Signed Date
	sign.request – completion_date (Datetime)
	Thời điểm tất cả các bên hoàn tất ký
	Datetime
	5
	Applicant Stage (hired)
	hr.applicant – stage_id → hired_stage=True
	Khi HR kéo sang 'Ký hợp đồng'; banner HIRED xuất hiện
	M2O
	6
	Date Closed / Hired
	hr.applicant – date_closed (Datetime)
	Tự động = today() khi vào hired stage
	Datetime
	7
	Employee ID (Created)
	hr.employee – id (Integer)
	Tạo sau khi nhấn [Create Employee]; liên kết qua emp_id
	Integer
	8
	No. Hired Employee
	hr.job – no_of_hired_employee (Computed)
	COUNT hr.applicant có emp_id != False, tự tăng +1
	Integer
	9
	Offer Approval State [C]
	hr.applicant – x_offer_approval_state
	'approved' khi BOD xác nhận. Unlock nút [Send Offer]
	Selection
	

3. Processing Logic / Quy tắc xử lý
	Logic 1 – [ODOO STANDARD] Generate Offer & Odoo Sign Integration:
Khi HR nhấn [Generate Offer], Odoo tạo sign.request với contract PDF đính kèm. Token unique được sinh ra theo cơ chế: access_token = uuid4(). Email gửi đến ứng viên chứa URL dạng: /sign/document/<sign_request_id>/<access_token>. Ứng viên điền thông tin và ký → sign.request.item.state = 'signed'. Khi tất cả signers ký → sign.request.state = 'signed', Odoo gửi bản PDF cuối cho tất cả các bên.
Logic 2 – [ODOO STANDARD] Import dữ liệu ứng viên vào hr.employee:
Khi nhấn [Create Employee], Odoo gọi method hr.applicant.create_employee() → tạo hr.employee và copy các trường: partner_name → name, job_id → job_id, department_id → department_id, user_id → coach_id. Thông tin cá nhân ứng viên đã nhập trên Offer page (CCCD, địa chỉ...) được import từ sign.request vào hr.employee.private_info.
Logic 3 – [ODOO STANDARD] Tự động cập nhật hr.job.no_of_hired_employee:
Computed field no_of_hired_employee = COUNT(hr.applicant WHERE job_id = self.id AND emp_id != False). Tự động tính lại khi hr.applicant.emp_id được gán (sau Create Employee). Dùng để theo dõi tiến độ tuyển dụng so với no_of_recruitment.
Logic 4 – [CUSTOM] Offer Approval Workflow (x_hb_recruitment_ext):
Cài đặt Python constraint + server action:
  • Khi HR lưu Wage > x_offer_approval_threshold: x_offer_approval_state tự set = 'pending'
  • Server Action gửi email notification đến x_offer_approver_id
  • Nút [Send Offer by Email] bị ẩn (invisible) khi x_offer_approval_state in ('pending','rejected')
  • BOD click [Approve] → x_offer_approval_state = 'approved' → [Send Offer] xuất hiện trở lại
  • BOD click [Reject] → Form x_offer_rejection_reason hiện ra → HR nhận notification
Logic 5 – [CUSTOM] Phân công lớp sơ bộ cho Giảng viên:
Trường x_preliminary_class_ids (M2M x_class) chỉ visible khi job_id.x_teaching_level != 'na'. Dữ liệu này được ghi vào thư offer PDF qua template tiếng Việt tùy chỉnh (template_id tùy biến) và sau khi Create Employee sẽ được dùng để pre-populate lịch giảng dạy trong Module Timesheets.
Logic 6 – [ODOO STANDARD] Validation email trước khi Generate Offer:
Method hr.applicant.create_offer() kiểm tra email_from != False. Nếu rỗng → raise UserError('Offer link cannot be sent – no email on applicant card'). HR phải cập nhật email trước khi tiếp tục.
	________________


5. SCREEN DEFINITION
Screen Definition
	Function ID
	FS-REC-004
	Function Name
	Offer Management
	Created by
	Nhóm G3 – SAP490
	Modified by
	Nhóm G3 – SAP490
	Page Title
	Offer Management – Học Bá Education HRM (Odoo 19)
	

1. Generate Offer Page + Sign Contract – Field Definitions
	No
	Field Name
	UI Type
	I/O
	Data Type
	Length
	Required
	Default
	S/C
	Remarks
	1
	Contract Template
	M2O Dropdown
	I/O
	INT FK
	—
	YES
	—
	S
	hr.contract.type từ Payroll config
	2
	Job Title
	Text Input
	I/O
	CHAR
	128
	NO
	From job
	S
	Chức danh trên HĐ
	3
	Contract Type
	M2O Dropdown
	I/O
	INT FK
	—
	YES
	—
	S
	hr.contract.type
	4
	Start Date
	Date Picker
	I/O
	DATE
	—
	YES
	—
	S
	hr.applicant – date_start
	5
	Wage (VND)
	Monetary Input
	I/O
	FLOAT
	—
	YES
	0.0
	S
	hr.contract – wage. Phải > 0
	6
	HR Responsible
	M2O Dropdown
	I/O
	INT FK
	—
	Rec.
	Current user
	S
	Người ký phía Học Bá
	7
	Sign – Full Name
	Text (PDF field)
	I/O
	CHAR
	128
	YES
	—
	S
	Ứng viên điền trên Sign page
	8
	Sign – CCCD
	Text (PDF field)
	I/O
	CHAR
	12
	YES
	—
	S
	9 hoặc 12 số CCCD
	9
	Sign – Địa chỉ
	Text (PDF field)
	I/O
	TEXT
	—
	YES
	—
	S
	Địa chỉ thường trú
	10
	E-Signature
	Signature Widget
	I/O
	BINARY
	—
	YES
	—
	S
	Vẽ / upload / font
	11
	Offer Approval State
	Status Badge
	O
	CHAR
	20
	COND
	draft
	C
	x_offer_approval_state: draft/pending/approved/rejected
	12
	Offer Approver
	M2O Dropdown
	I/O
	INT FK
	—
	COND
	BOD user
	C
	x_offer_approver_id
	13
	Rejection Reason
	Text Area
	I/O
	TEXT
	—
	COND
	—
	C
	x_offer_rejection_reason – BOD điền khi reject
	14
	Preliminary Classes [C]
	M2M Tags
	I/O
	INT FK
	—
	COND
	—
	C
	x_preliminary_class_ids – GV/TG only
	2. Trạng thái Sign Request – State Machine
	State
	Giá trị
	Điều kiện chuyển
	Hành động tự động
	Draft
	'draft'
	HR tạo offer
	Lưu sign.request, chưa gửi
	Sent
	'sent'
	HR nhấn [Send Offer by Email]
	Gửi email + token cho ứng viên
	Signed
	'signed'
	Tất cả signers hoàn tất
	Gửi PDF bản ký cho tất cả bên; log vào chatter
	Canceled
	'canceled'
	HR hủy hoặc ứng viên Refuse
	Link token bị vô hiệu hóa
	Legend: S = Odoo Standard  |  C = Custom  |  COND = Conditional Required  |  GV/TG = Giảng viên / Trợ giảng only
	________________


6. STANDARD vs CUSTOM GAP ANALYSIS MATRIX
Standard vs Custom GAP Analysis Matrix – FS-REC-004
	Feature / Tính năng
	Odoo 19 Standard
	Custom (x_hb_recruitment_ext)
	Ghi chú
	Generate Offer (link + token)
	✓
	

	hr.applicant.create_offer() – Standard
	Send Offer by Email
	✓
	

	mail.template + sign.request – Standard
	Odoo Sign e-signature
	✓
	

	module sign – Standard (cần cài đặt)
	Sign Request State Machine
	✓
	

	sign.request – draft/sent/signed/canceled
	Contract Template (từ Payroll)
	✓
	

	hr.contract.type – Standard
	Stage Contract Proposal → Contract Signed
	✓
	

	hired_stage=True → banner HIRED
	Create Employee từ Applicant
	✓
	

	hr.applicant.create_employee() – Standard
	Import dữ liệu Sign vào hr.employee
	✓
	

	private_info import từ sign.request – Standard
	no_of_hired_employee Computed
	✓
	

	hr.job – auto count – Standard
	Validation: email bắt buộc trước Offer
	✓
	

	UserError raise – Standard
	Offer Approval Workflow (Wage > ngưỡng)
	

	✓ Custom workflow
	x_offer_approval_state + BOD notification
	Custom Email Template tiếng Việt
	

	✓ Custom mail.template
	Thư đề nghị song ngữ Việt-Anh
	Preliminary Class Assignment (GV)
	

	✓ x_preliminary_class_ids
	M2M x_class – only Giảng viên/TG
	Configure Salary Package
	✗ N/A tại VN
	

	Localization feature – không áp dụng
	

Supplement / Ghi chú kỹ thuật, Cấu hình Go-Live & Nguồn tham chiếu
	Odoo Module Dependencies:
  • hr_recruitment (hr.applicant – offer flow, stage Contract Proposal/Signed)
  • sign (sign.request, sign.request.item, e-signature engine)
  • hr (hr.employee – Create Employee)
  • payroll (hr.contract.type – Contract Templates)
  • mail (mail.template – Offer email, notification)
Custom Module: x_hb_recruitment_ext (tiếp nối từ FS-REC-002 & FS-REC-003)
  • Thêm fields x_offer_approval_state, x_offer_approver_id, x_offer_rejection_reason vào hr.applicant
  • Server Action: @api.onchange('wage') → tự set x_offer_approval_state = 'pending' nếu wage > threshold
  • attrs: invisible [Send Offer] khi x_offer_approval_state in ('pending','rejected')
  • x_preliminary_class_ids (M2M x_class) – conditional visible khi x_teaching_level != 'na'
  • Custom mail.template tiếng Việt cho Offer Letter
Cấu hình bắt buộc trước Go-Live:
  [1] Cài đặt module sign (Odoo Sign). Cấu hình chữ ký của đại diện Học Bá (BOD / Giám đốc)
  [2] Tạo Contract Templates tại Payroll ▸ Configuration ▸ Contract Templates:
      - Hợp đồng Lao động toàn thời gian (upload PDF mẫu, đánh dấu các trường ký)
      - Hợp đồng Cộng tác viên Giảng viên (PDF mẫu riêng có mục phân công lớp)
      - Hợp đồng Dịch vụ (TVTS, Hành chính ngắn hạn)
  [3] Cấu hình x_offer_approval_threshold (mặc định đề xuất: 15,000,000 VND)
  [4] Gán x_offer_approver_id = tài khoản BOD / Giám đốc
Toàn cảnh Module Recruitment – Kết thúc FS-REC-004:
  FS-REC-001 (Job Position) → FS-REC-002 (Applicant Tracking) → FS-REC-003 (Interview Workflow) → FS-REC-004 (Offer Management) → [Onboarding – Module Employees]
Nguồn tham chiếu:
  • Odoo 19.0 Docs – Offer Job Positions: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/offer_job_positions.html
  • Odoo 19.0 Docs – Contracts: https://www.odoo.com/documentation/19.0/applications/hr/payroll/contracts.html
  • Odoo 19.0 Docs – Recruitment Flow: https://www.odoo.com/documentation/19.0/applications/hr/recruitment/recruitment-flow.html
	



chap 5- payroll
CHƯƠNG 5 — ĐẶC TẢ CẤU HÌNH HỆ THỐNG
IV. Module Payroll
5.4. Payroll Configuration
Phần này mô tả toàn bộ cấu hình hệ thống cần thiết lập trước khi go-live cho Module Payroll tại Học Bá Education. Các cấu hình tại đây định nghĩa bộ khung tính lương mà sau này từng nhân viên cụ thể sẽ được gán vào — không phải dữ liệu giao dịch hàng tháng. Tất cả cấu hình được ánh xạ trực tiếp đến Gap Analysis trong Chapter 4 (CFG-PR-001 đến CFG-PR-006).
Nguyên tắc chủ đạo: Mỗi tham số có khả năng thay đổi theo quy định Nhà nước (lương cơ sở, lương tối thiểu vùng, biểu thuế, giảm trừ) đều được lưu dưới dạng Salary Rule Parameter — không hardcode trong công thức — để HR có thể cập nhật bằng cách sửa duy nhất 1 giá trị khi Nhà nước điều chỉnh.
5.4.1. Cấu trúc lương theo 3 nhóm nhân sự (CFG-PR-001)
Học Bá có 3 nhóm nhân sự với logic tính lương khác nhau hoàn toàn, không thể chuẩn hóa vào cùng một cấu trúc. Hệ thống cần cấu hình 3 Salary Structure riêng biệt — mỗi nhân viên được gán đúng một cấu trúc qua hợp đồng lao động.
Đường dẫn cấu hình: Payroll → Configuration → Salary Structures
Mã
	Tên cấu hình
	Áp dụng cho
	Các Salary Rules chính
	Đặc trưng
	STR-PR-01
	Cấu trúc lương Khối Văn phòng
	Office & Operations (HR, Marketing, Sales, Admin, Finance)
	BASE + ALLOW_LUNCH + ALLOW_TRANSPORT + ALLOW_PHONE + ALLOW_POSITION + ALLOW_SENIORITY + OT + KPI_BONUS + COMMISSION + BHXH + BHYT + BHTN + PIT → NET
	Lương cố định tháng theo hợp đồng + phụ cấp + thưởng KPI/hoa hồng
	STR-PR-02
	Cấu trúc lương Khối Giáo viên
	Full-time Teacher, Part-time Instructor, Teaching Assistant
	TEACH_HOURS (giờ dạy × đơn giá riêng) + FIXED_BASE (nếu có) + EXTRA_HOURS_BONUS + HOLIDAY_OT + BHXH + BHYT + BHTN + PIT → NET
	Lương theo giờ dạy đã xác thực từ Work Entry WORK200, đơn giá khác nhau theo từng giáo viên
	STR-PR-03
	Cấu trúc lương Khối CTV
	Collaborator (CTV), Part-time Support
	TASK_PAY + SHIFT_PAY + PIT (light) → NET
	Trả theo task/ca, không đóng BHXH (vì CTV không có hợp đồng lao động chính thức)
	Lưu ý quan trọng về việc gán cấu trúc:
* Mỗi hr.contract chỉ được gán đúng một Salary Structure

* Cấu trúc được gán lúc tạo hợp đồng, không thay đổi giữa kỳ trừ khi nhân viên đổi loại vị trí (ví dụ: TA chuyển thành Office Staff)

* Khi nhân viên thử việc → chính thức, giữ nguyên Salary Structure nhưng đổi is_probation từ True sang False (xem CFG-PR-005 bên dưới)

5.4.2. Cấu hình Bảo hiểm bắt buộc Việt Nam (CFG-PR-002)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rules + Salary Rule Parameters
(a) Tham số tỷ lệ đóng (Salary Rule Parameters)
Mã
	Tham số
	Giá trị
	Cơ sở pháp lý
	PARAM-PR-01
	BHXH — Tỷ lệ NV đóng
	8.0%
	Luật BHXH 2014 + Nghị định 58/2020/NĐ-CP
	PARAM-PR-02
	BHXH — Tỷ lệ Cty đóng
	17.5%
	Như trên
	PARAM-PR-03
	BHYT — Tỷ lệ NV đóng
	1.5%
	Luật BHYT 2008 (sửa đổi 2014)
	PARAM-PR-04
	BHYT — Tỷ lệ Cty đóng
	3.0%
	Như trên
	PARAM-PR-05
	BHTN — Tỷ lệ NV đóng
	1.0%
	Luật Việc làm 2013
	PARAM-PR-06
	BHTN — Tỷ lệ Cty đóng
	1.0%
	Như trên
	PARAM-PR-07
	Lương cơ sở (tham chiếu BHXH/BHYT)
	2.340.000 VND/tháng
	Nghị định 73/2024/NĐ-CP (từ 01/07/2024)
	PARAM-PR-08
	Lương tối thiểu vùng I (tham chiếu BHTN)
	4.960.000 VND/tháng
	Nghị định 74/2024/NĐ-CP (từ 01/07/2024)
	PARAM-PR-09
	Hệ số trần
	20 (lần)
	Theo Luật BHXH — trần đóng BHXH/BHYT/BHTN
	→ Trần đóng BHXH/BHYT = PARAM-PR-07 × PARAM-PR-09 = 46.800.000 VND/tháng
→ Trần đóng BHTN = PARAM-PR-08 × PARAM-PR-09 = 99.200.000 VND/tháng
(b) Định nghĩa Cơ sở tính bảo hiểm (Insurance Base)
Không phải toàn bộ thu nhập đều đóng BH. Theo Nghị định 28/2015/NĐ-CP, chỉ một số khoản tính vào cơ sở đóng:
Khoản thu nhập
	Đóng BH?
	Ghi chú
	Lương cơ bản (BASE)
	✅ Có
	Bắt buộc theo luật
	Phụ cấp chức vụ (ALLOW_POSITION)
	✅ Có
	Có tính chất ổn định
	Phụ cấp thâm niên (ALLOW_SENIORITY)
	✅ Có
	Có tính chất ổn định
	Phụ cấp ăn trưa (ALLOW_LUNCH)
	❌ Không
	Hỗ trợ sinh hoạt
	Phụ cấp đi lại (ALLOW_TRANSPORT)
	❌ Không
	Hỗ trợ sinh hoạt
	Phụ cấp điện thoại (ALLOW_PHONE)
	❌ Không
	Hỗ trợ công cụ làm việc
	OT (overtime pay)
	❌ Không
	Khoản biến động
	Thưởng (KPI_BONUS, COMMISSION)
	❌ Không
	Khoản biến động
	Thưởng tháng 13/Tết
	❌ Không
	Khoản biến động
	→ Cấu hình Salary Rule INSURANCE_BASE với công thức: BASE + ALLOW_POSITION + ALLOW_SENIORITY (capped tại PARAM-PR-07 × 20 cho BHXH/BHYT, PARAM-PR-08 × 20 cho BHTN).
5.4.3. Cấu hình Thuế TNCN — Biểu thuế 7 bậc (CFG-PR-003)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rule Parameters
Cấu hình bảng tra cứu biểu thuế theo Nghị quyết 954/2020/UBTVQH14:
Mã
	Bậc
	Thu nhập tính thuế/tháng (VND)
	Thuế suất
	Tham số Odoo
	PARAM-PR-PIT-01
	Bậc 1
	Đến 5.000.000
	5%
	pit_bracket_1_max = 5.000.000 / pit_bracket_1_rate = 0.05
	PARAM-PR-PIT-02
	Bậc 2
	Trên 5 → 10 triệu
	10%
	pit_bracket_2_max = 10.000.000 / pit_bracket_2_rate = 0.10
	PARAM-PR-PIT-03
	Bậc 3
	Trên 10 → 18 triệu
	15%
	pit_bracket_3_max = 18.000.000 / pit_bracket_3_rate = 0.15
	PARAM-PR-PIT-04
	Bậc 4
	Trên 18 → 32 triệu
	20%
	pit_bracket_4_max = 32.000.000 / pit_bracket_4_rate = 0.20
	PARAM-PR-PIT-05
	Bậc 5
	Trên 32 → 52 triệu
	25%
	pit_bracket_5_max = 52.000.000 / pit_bracket_5_rate = 0.25
	PARAM-PR-PIT-06
	Bậc 6
	Trên 52 → 80 triệu
	30%
	pit_bracket_6_max = 80.000.000 / pit_bracket_6_rate = 0.30
	PARAM-PR-PIT-07
	Bậc 7
	Trên 80 triệu
	35%
	pit_bracket_7_rate = 0.35
	Công thức Thu nhập tính thuế (Taxable Income):
TAXABLE_INCOME = GROSS_TAXABLE - INSURANCE_EMPLOYEE - PERSONAL_DEDUCTION - DEPENDENT_DEDUCTION


Trong đó GROSS_TAXABLE là Gross trừ đi các khoản được miễn thuế (phụ cấp ăn trưa trong định mức, phụ cấp điện thoại trong định mức theo Thông tư 111/2013/TT-BTC).
5.4.4. Cấu hình Giảm trừ Bản thân & Người phụ thuộc (CFG-PR-004)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rule Parameters + Employee Profile → Dependents tab
Mã
	Tham số
	Giá trị
	Cơ sở pháp lý
	PARAM-PR-DED-01
	Giảm trừ Bản thân
	11.000.000 VND/tháng
	Nghị quyết 954/2020/UBTVQH14
	PARAM-PR-DED-02
	Giảm trừ Người phụ thuộc
	4.400.000 VND/người/tháng
	Như trên
	Liên kết với Module Employee:
Người phụ thuộc được khai báo trong Module Employee (xem FUNC-EMP-003 — hr.dependent). Quan hệ One2many: 1 nhân viên có thể có nhiều người phụ thuộc, mỗi người có:
   * Họ tên
   * Ngày sinh
   * Mã số thuế người phụ thuộc
   * Quan hệ (con, cha mẹ...)
   * Ngày hiệu lực Từ / Ngày hiệu lực Đến
→ Hệ thống tự tính số người phụ thuộc đang còn hiệu lực trong kỳ tính lương dựa trên ngày tính lương so với ngày Từ/Đến — không cần HR điều chỉnh thủ công khi nhân viên sinh con hoặc cha mẹ qua đời.
5.4.5. Cấu hình Lương Thử việc 85% (CFG-PR-005)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rules + Contract
Mã
	Cấu hình
	Mô tả
	PARAM-PR-PROB-01
	Tỷ lệ lương thử việc
	0.85 (85%) — cấu hình được, có thể điều chỉnh nếu chính sách thay đổi
	FIELD-PR-PROB-01
	is_probation (Boolean trên hr.contract)
	True khi nhân viên đang thử việc, False khi chính thức
	RULE-PR-PROB-01
	Rule BASE — điều kiện thử việc
	if contract.is_probation: BASE = wage × 0.85 else: BASE = wage
	RULE-PR-PROB-02
	Pro-rate chuyển trạng thái giữa tháng
	Tự động: ngày 1 → ngày chuyển trạng thái áp 85%, ngày chuyển → ngày cuối tháng áp 100%
	Liên kết Module Employee: Khi x_employment_status trên hr.employee chuyển từ "Thử việc" sang "Chính thức" (qua Automated Action AUT-002 của Module Employee), hệ thống tự động:
   * Cập nhật is_probation = False trên hợp đồng đang hoạt động

   * Lưu lại x_official_date để pro-rate tháng chuyển đổi

5.4.6. Cấu hình OT — Đặc biệt là OT Ngày lễ 300% (CFG-PR-006)
Đường dẫn cấu hình: Payroll → Configuration → Work Entry Types + Salary Rules
(a) Định nghĩa Work Entry Types cho OT
Mã Work Entry
	Mô tả
	Multiplier
	Trigger
	WET-PR-OT-01
	OT thường (WORK110_OT_NORMAL)
	1.5×
	Check-out sau 18:00 ngày thường (T2–T6)
	WET-PR-OT-02
	OT cuối tuần (WORK110_OT_WEEKEND)
	2.0×
	Làm việc Thứ 7 / Chủ nhật ngoài lịch chuẩn
	WET-PR-OT-03
	OT ngày lễ (WORK110_OT_HOLIDAY)
	3.0×
	Làm việc vào ngày lễ trong danh sách Public Holidays
	Cơ sở pháp lý: Điều 98 Bộ luật Lao động 2019 — quy định bắt buộc.
(b) Tham số đơn giá OT giờ
Cấu hình công thức OT_HOURLY_RATE được tính tự động: OT_HOURLY_RATE = BASE / (working_days_per_month × hours_per_day)
→ Khi giáo viên dạy lớp vào Tết Nguyên đán: hệ thống tự nhận biết qua Public Holiday → áp Work Entry Type WET-PR-OT-03 → áp multiplier 3.0× → không cần HR nhớ áp tay.
5.4.7. Cấu hình Allowances chuẩn (Phụ cấp định mức)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rules (loại Allowance)
Mã
	Tên phụ cấp
	Giá trị mặc định
	Đóng BH?
	Tính thuế?
	ALLOW-PR-01
	Phụ cấp ăn trưa
	730.000 VND/tháng (miễn thuế đến mức này)
	❌
	⚠️ Chỉ tính phần vượt 730.000
	ALLOW-PR-02
	Phụ cấp đi lại
	Theo hợp đồng (default 500.000)
	❌
	✅
	ALLOW-PR-03
	Phụ cấp điện thoại
	Theo hợp đồng (default 300.000)
	❌
	⚠️ Phần vượt định mức công ty quy định mới tính thuế
	ALLOW-PR-04
	Phụ cấp chức vụ
	Theo bảng (Trưởng phòng/TBP/Chuyên viên)
	✅
	✅
	ALLOW-PR-05
	Phụ cấp thâm niên
	Theo công thức (% lương × số năm)
	✅
	✅
	ALLOW-PR-06
	Phụ cấp xăng xe cho Sales
	Theo hợp đồng
	❌
	✅
	Tham chiếu pháp lý: Thông tư 111/2013/TT-BTC quy định các khoản thu nhập được miễn thuế.
5.4.8. Cấu hình Deductions chuẩn (Các khoản khấu trừ)
Đường dẫn cấu hình: Payroll → Configuration → Salary Rules (loại Deduction)
Mã
	Tên khoản khấu trừ
	Khi nào áp dụng
	Nguồn dữ liệu
	DED-PR-01
	BHXH NV đóng (8%)
	Hàng tháng
	Tự tính từ Insurance Base
	DED-PR-02
	BHYT NV đóng (1.5%)
	Hàng tháng
	Tự tính từ Insurance Base
	DED-PR-03
	BHTN NV đóng (1%)
	Hàng tháng
	Tự tính từ Insurance Base
	DED-PR-04
	Thuế TNCN
	Hàng tháng
	Tự tính từ biểu 7 bậc
	DED-PR-05
	Tạm ứng lương
	Khi có yêu cầu
	Input line nhập tay vào payslip
	DED-PR-06
	Vay nội bộ (trả góp)
	Theo lịch trả
	Module Loan (Phase sau) hoặc input line
	DED-PR-07
	Khấu trừ nghỉ không lương
	Khi có Work Entry LEAVE120
	Tự tính từ Time Off module
	DED-PR-08
	Phạt đi muộn (nếu áp dụng)
	Khi vượt ngưỡng late/tháng
	Input line nhập tay (chính sách công ty)
	DED-PR-09
	Hoàn ứng (refund advance)
	Khi có advance chưa hoàn
	Liên kết với DED-PR-05
	5.4.9. Cấu hình Ngày lễ Việt Nam (Public Holidays)
Đường dẫn cấu hình: Time Off → Configuration → Public Holidays (dùng chung với Module Time Off)
Module Payroll đọc lại danh sách Public Holidays đã cấu hình ở Module Time Off (CFG-TO-003) để:
      * Xác định ngày nào không tính lương (đã được hưởng nguyên lương theo luật)
      * Trigger Work Entry Type WET-PR-OT-03 khi có người dạy vào ngày lễ
Các ngày lễ tối thiểu cần có (theo Điều 112 Bộ luật Lao động):
      * Tết Dương lịch (01/01) — 1 ngày
      * Tết Nguyên đán — 5 ngày (theo lịch âm)
      * Giỗ Tổ Hùng Vương (10/3 âm lịch) — 1 ngày
      * Ngày Giải phóng Miền Nam (30/4) — 1 ngày
      * Quốc tế Lao động (01/5) — 1 ngày
      * Quốc khánh — 2 ngày (02/9 và 1 ngày kề liền)
→ Cấu hình một lần đầu năm, sau đó hệ thống tự áp dụng cho cả năm.
5.4.10. Cấu hình Tài khoản Kế toán (Chart of Accounts mapping)
Đường dẫn cấu hình: Payroll → Configuration → Salary Structures → Accounting Tab
Để bút toán Payroll → Accounting tự động (FIT-PR-004), cần cấu hình ánh xạ:
Loại tài khoản
	Account Code (gợi ý theo TT200)
	Áp dụng cho rule
	Chi phí lương
	622 / 642 / 6421 / 6422 (theo phòng ban)
	BASE, ALLOW_*, OT, KPI_BONUS, COMMISSION
	Công nợ phải trả NV
	334 — Phải trả công nhân viên
	NET
	Công nợ BHXH/BHYT/BHTN
	3383 / 3384 / 3389
	BHXH, BHYT, BHTN (cả NV và Cty đóng)
	Công nợ Thuế TNCN
	3335 — Thuế TNCN phải nộp
	PIT
	Tạm ứng lương
	141 — Tạm ứng
	DED-PR-05
	→ Khi payslip chuyển trạng thái Done, Odoo tự tạo Journal Entry draft với các bút toán này. Finance chỉ cần review và post.
5.4.11. Cấu hình Phân quyền vai trò (Security Groups)
Đường dẫn cấu hình: Settings → Users & Companies → Groups
Mã
	Vai trò
	Quyền chính
	SEC-PR-01
	Payroll User (HR Officer)
	Xem/tạo/sửa payslip ở trạng thái Draft/Waiting. Không duyệt được sang Done. Không xem được payslip của nhân viên khác phòng.
	SEC-PR-02
	Payroll Officer (C&B Specialist)
	Toàn quyền với payslip Draft/Waiting. Confirm payslip sang Done request. Xem được toàn bộ payslip công ty. Không reset Done → Draft được.
	SEC-PR-03
	Payroll Manager (HR Manager)
	Toàn quyền — bao gồm reset payslip từ Done về Draft (kèm lý do bắt buộc ghi audit log). Cấu hình Salary Rules.
	SEC-PR-04
	Payroll Accountant (Finance)
	Read-only payslip. Post Journal Entry. Generate Bank File. Submit BHXH/eTax reports.
	SEC-PR-05
	Payroll Approver (BGĐ)
	Read-only toàn bộ payslip. Phê duyệt batch Payslip Run (multi-level approval).
	SEC-PR-06
	Employee Portal
	Chỉ xem payslip của chính mình qua Portal — không thấy được dữ liệu Gross của người khác.
	→ Phân định quyền cụ thể giải quyết vấn đề AS-IS PP-PR-04 (Không có audit trail) và PP-PR-15 (Không có cơ chế khóa sau khi tính lương).
5.4.12. Cấu hình Payslip PDF Template
Đường dẫn cấu hình: Settings → Technical → Reports
Cấu hình
	Yêu cầu
	Template Header
	Logo Học Bá + Thông tin pháp lý công ty (Tên đầy đủ, MST, Địa chỉ)
	Block thông tin NV
	Họ tên + Mã NS + Phòng ban + Chức danh + Mã số thuế + Số CCCD (4 số cuối)
	Block thông tin kỳ
	Kỳ lương + Ngày tính + Ngày tải PDF
	Block lương Gross
	Liệt kê chi tiết từng rule: BASE / từng phụ cấp / OT / thưởng → Tổng Gross
	Block khấu trừ
	BHXH / BHYT / BHTN / PIT / khác → Tổng khấu trừ
	Block kết quả
	NET (số tiền + số viết bằng chữ)
	Block xác nhận
	Người lập / Người duyệt / Mã hash để verify
	Ngôn ngữ
	Tiếng Việt (mặc định) — fallback tiếng Anh cho giáo viên ngoại
	→ Eliminate AS-IS pain point PP-PR-07 (Tạo payslip thủ công).
________________


5.4.13. Bảng tổng kết ánh xạ Chapter 4 GAP → Chapter 5 Configuration
Bảng này giúp đọc nhanh: mỗi item CFG-PR-XXX ở Chapter 4 được cấu hình thành các thành phần cụ thể nào trong Chapter 5.
Chapter 4 GAP
	Chapter 5 Configuration Components
	Số tham số/rule
	CFG-PR-001 Salary Structures 3 khối
	5.4.1 — STR-PR-01/02/03
	3 structures
	CFG-PR-002 BHXH/BHYT/BHTN VN
	5.4.2 — PARAM-PR-01 đến PR-09 + INSURANCE_BASE rule
	9 params + 1 rule
	CFG-PR-003 Thuế TNCN 7 bậc
	5.4.3 — PARAM-PR-PIT-01 đến PIT-07
	7 params
	CFG-PR-004 Giảm trừ bản thân/người phụ thuộc
	5.4.4 — PARAM-PR-DED-01/02 + tích hợp hr.dependent
	2 params
	CFG-PR-005 Lương thử việc 85%
	5.4.5 — PARAM-PR-PROB-01 + RULE-PR-PROB-01/02
	1 param + 2 rules
	CFG-PR-006 OT ngày lễ 300%
	5.4.6 — WET-PR-OT-01/02/03
	3 work entry types
	Bổ sung Allowances chuẩn
	5.4.7 — ALLOW-PR-01 đến PR-06
	6 allowances
	Bổ sung Deductions chuẩn
	5.4.8 — DED-PR-01 đến PR-09
	9 deductions
	Bổ sung Public Holidays
	5.4.9 — Tích hợp với Module Time Off
	Shared
	Bổ sung Accounting mapping
	5.4.10 — 5 loại account codes
	5 mappings
	Bổ sung Security Groups
	5.4.11 — SEC-PR-01 đến PR-06
	6 groups
	Bổ sung Payslip PDF Template
	5.4.12 — Custom QWeb report
	1 template
	Tổng cộng: 6 GAP từ Chapter 4 + 6 nhóm cấu hình bổ sung cần thiết → toàn bộ 12 nhóm cấu hình phải hoàn thành trước go-live.
5.4.14. Lưu ý triển khai
Thứ tự cấu hình bắt buộc (do dependency):
1. PUBLIC HOLIDAYS (5.4.9) ────┐
2. ALLOWANCES (5.4.7) ─────────┤
3. DEDUCTIONS (5.4.8) ─────────┼──→ 5. SALARY STRUCTURES (5.4.1)
4. PARAMETERS (5.4.2/3/4/5/6) ─┘                    │
                                                     ↓
                              6. ACCOUNTING MAPPING (5.4.10)
                                                     │
                                                     ↓
                              7. SECURITY GROUPS (5.4.11)
                                                     │
                                                     ↓
                              8. PAYSLIP TEMPLATE (5.4.12)


→ Không thể tạo Salary Structure trước khi có Allowances/Deductions. Không thể test payroll trước khi có Public Holidays.
Dữ liệu test cần chuẩn bị sau khi cấu hình xong:
      * 1 nhân viên Office (lương cố định, có người phụ thuộc, có OT) → test STR-PR-01
      * 1 giáo viên Teacher (có giờ dạy WORK200 + có dạy ngày lễ) → test STR-PR-02
      * 1 CTV (chỉ có task pay) → test STR-PR-03
      * 1 nhân viên Thử việc (test 85%) → test CFG-PR-005
      * 1 nhân viên thu nhập > 100 triệu/tháng (test trần BH) → test CFG-PR-002
      * 1 nhân viên có thu nhập rơi vào bậc thuế 5, 6, 7 → test CFG-PR-003
→ Bộ dữ liệu test này phải được Học Bá cung cấp trước UAT (User Acceptance Test).