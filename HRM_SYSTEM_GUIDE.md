# HOCBA HRM System - Complete User & Authentication Guide

## System Overview

Hệ thống HOCBA HRM bao gồm 2 module chính:
1. **hocba_attendance** - Quản lý chấm công
2. **hocba_users** - Xác thực, phân quyền, quản lý tài khoản

---

## Roles & Permission Hierarchy

### 1. **Admin (Quản trị viên)**
- **Quyền**: Toàn bộ hệ thống
- **Chức năng**:
  - Tạo/xóa/sửa tài khoản người dùng
  - Quản lý roles và quyền
  - Cấu hình loại nhân viên
  - Quản lý phòng ban
  - Xem tất cả dữ liệu hệ thống
  - Cấu hình truy cập chi tiết

### 2. **HR Manager (Quản lý HR)**
- **Quyền**: Quản lý nhân sự
- **Chức năng**:
  - Xem danh sách tất cả nhân viên
  - Xem và quản lý chấm công
  - Quản lý kỳ nghỉ/phép
  - Tạo báo cáo HR
  - Xem nhân viên theo phòng ban
  - Không thể tạo/xóa tài khoản

### 3. **Employee (Nhân viên chính thức)**
- **Loại**: Nhân viên văn phòng hoặc Giáo viên
- **Quyền**: Xem thông tin cá nhân
- **Chức năng**:
  - Xem chấm công của mình
  - Xem lịch làm việc
  - Xin phép/kỳ nghỉ
  - Xem thông tin hồ sơ
  - KHÔNG thể xem dữ liệu người khác

### 4. **Contractor (Cộng tác viên)**
- **Loại**: Nhân viên bán thời gian/cộng tác viên
- **Quyền**: Tối thiểu
- **Chức năng**:
  - Xem chấm công của mình ONLY
  - Không thể xem thông tin khác
  - Quyền truy cập hạn chế

---

## Employee Types (Loại Nhân Viên)

### 1. **Office Staff (Nhân viên văn phòng)**
- Lợi ích: Bảo hiểm, lương hưu, phép năm
- Giờ làm: Toàn thời gian (8:00 - 17:00)

### 2. **Teacher (Giáo viên)**
- Lợi ích: Hỗ trợ giáo dục, phát triển chuyên môn
- Giờ làm: Toàn thời gian

### 3. **Contractor (Cộng tác viên)**
- Lợi ích: Thanh toán theo dự án, lịch linh hoạt
- Giờ làm: Bán thời gian

---

## Module Structure

### hocba_attendance/
Quản lý chấm công
- **Models**:
  - `hocba.attendance` - Bản ghi chấm công
  - `hocba.work_assignment` - Gán công việc
  - `hocba.attendance.status` - Trạng thái (On Time, Late, Absent, On Leave)

### hocba_users/
Xác thực và phân quyền
- **Models**:
  - `hocba.employee.type` - Loại nhân viên
  - `hocba.user.role` - Roles
  - `hocba.user` - Tài khoản người dùng
  - `hocba.access.control` - Ma trận quyền
  - `hocba.department.manager` - Quản lý phòng ban

---

## Features & Functionality

### ✅ Authentication
- Login page với email/password
- Session management
- Last login tracking
- Account activation/deactivation

### ✅ User Management (Admin)
- Create/Edit/Delete users
- Assign roles to users
- Link users to employees
- Set employee types
- Manage departments

### ✅ Role-Based Access Control
- Fine-grained permissions
- Module-level access (attendance, leaves, reports, admin)
- Action-level permissions (read, write, create, delete)
- Department-specific permissions

### ✅ Attendance Tracking
- Check-in/Check-out timestamps
- Automatic working hours calculation
- Status detection (On Time/Late)
- Work assignment linking
- Attendance notes

### ✅ Dashboard
- Role-specific dashboards
- Quick access to relevant features
- Admin panel for system management
- HR dashboard for reporting
- Employee personal dashboard

### ✅ Security
- Record-level security rules
- User can only see their own records (employees)
- HR managers can see their department
- Admins can see everything
- Access control audit trail

---

## Usage Guide

### For Admin: Creating a New User

1. Go to **User Management → Users**
2. Click **Create**
3. Fill in:
   - Full Name
   - Email
   - ODOO User (create one in ODOO first)
   - Role (select: admin, hr_manager, employee, or contractor)
   - Employee (link to hr.employee)
   - Employee Type (office_staff, teacher, or contractor)
   - Department
4. Click **Save**
5. Can now set **Access Control** and **Managed Departments**

### For Admin: Setting Permissions

1. Go to **User Management → Access Control**
2. Select a user
3. Add permission rules:
   - Module: attendance, leaves, reports, admin, hr_management
   - Action: read, write, create, delete, or all
   - Allowed: Yes/No
4. Save

### For Admin: Department Manager Setup

1. Go to **User Management → Department Managers**
2. Click **Create**
3. Select department and manager user
4. Toggle permissions:
   - Can Manage Attendance
   - Can Manage Leaves
   - Can Manage Employees
   - Can Approve Reports

### For Employees: Login

1. Go to `/hocba/login`
2. Enter email and password
3. System automatically directs to role-specific dashboard
4. Last login is recorded

### For HR Manager: View Attendance

1. Login as HR Manager
2. Go to **Attendance → Attendance Records**
3. Can filter by:
   - Employee
   - Department
   - Date
   - Status (On Time, Late, etc.)
4. Generate reports

---

## Data Models

### hocba.user
```
- name: Tên đầy đủ
- user_id: ODOO User (liên kết)
- role_id: Role (Admin, HR Manager, Employee, Contractor)
- employee_id: Employee (liên kết)
- employee_type_id: Loại nhân viên
- department_id: Phòng ban
- is_active: Kích hoạt/Tắt
- last_login: Lần đăng nhập cuối
- access_control_ids: Danh sách quyền
- department_manager_ids: Phòng ban quản lý
```

### hocba.attendance
```
- employee_id: Nhân viên
- check_in: Giờ vào
- check_out: Giờ ra
- work_assignment_id: Công việc
- status_id: Trạng thái (On Time, Late, etc.)
- notes: Ghi chú
- working_hours: Giờ làm (tự động tính)
- date: Ngày (tự động tính)
```

### hocba.access.control
```
- user_id: Người dùng
- module_name: Module (attendance, leaves, reports, admin)
- action: Hành động (read, write, create, delete)
- allowed: Cho phép (Yes/No)
```

---

## Security Rules

- **Employees** chỉ có thể xem bản ghi của mình
- **HR Managers** có thể xem tất cả nhân viên trong phòng ban
- **Admins** có thể xem toàn bộ hệ thống
- Tất cả lần truy cập được ghi lại trong database

---

## Next Steps

1. ✅ Create ODOO users (in ODOO Settings)
2. ✅ Create hocba.user records
3. ✅ Assign roles and employees
4. ✅ Configure access control rules
5. ✅ Set up department managers
6. ✅ Test login with different roles
7. ✅ Configure attendance tracking

---

## Support & Troubleshooting

### Issue: Login not working
- Verify ODOO user exists
- Check email is correct
- Ensure hocba.user record is linked
- Verify is_active = True

### Issue: Cannot see certain menu items
- Check access_control rules
- Verify role has correct permissions
- Check record-level security rules

### Issue: Attendance not calculating working hours
- Ensure check_in AND check_out are set
- Check_out must be after check_in
- Working hours are calculated automatically

---

## File Structure

```
custom-addons/
├── hocba_attendance/           # Attendance Management
│   ├── __manifest__.py
│   ├── __init__.py
│   ├── models/
│   │   ├── hr_attendance.py
│   │   ├── hr_work_assignment.py
│   │   └── hr_attendance_status.py
│   ├── views/
│   │   ├── hr_attendance_views.xml
│   │   ├── hr_work_assignment_views.xml
│   │   ├── hr_attendance_status_views.xml
│   │   └── menus.xml
│   └── security/
│       └── ir.model.access.csv
│
└── hocba_users/                # User Management & Auth
    ├── __manifest__.py
    ├── __init__.py
    ├── models/
    │   ├── employee_type.py
    │   ├── user_role.py
    │   ├── hocba_user.py
    │   ├── access_control.py
    │   └── department_manager.py
    ├── controllers/
    │   ├── auth.py             # Login/Logout
    │   └── dashboard.py        # Role dashboards
    ├── views/
    │   ├── employee_type_views.xml
    │   ├── user_role_views.xml
    │   ├── hocba_user_views.xml
    │   ├── access_control_views.xml
    │   ├── department_manager_views.xml
    │   └── menus.xml
    ├── security/
    │   ├── ir.model.access.csv
    │   └── security_rules.xml
    └── templates/
        └── login_and_dashboards.xml
```

---

**Version**: 1.0.0  
**Last Updated**: June 9, 2026  
**Author**: HOCBA Team
