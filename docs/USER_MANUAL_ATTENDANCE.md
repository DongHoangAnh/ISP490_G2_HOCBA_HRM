# USER MANUAL: COMPLETE ATTENDANCE MANAGEMENT (HOCBA HRM)

## Document Information
**Project Name:** Human Resource Management System (HOCBA HRM)  
**Module:** HRM - Attendance & Timekeeping  
**Created by:** ISP490_G2 Team  
**Version:** 1.0  
**Date:** 08/08/2025

---

## 1 OVERVIEW
### 1.1 Role-Based Access
The system automatically adjusts the interface based on user roles:
*   **Employee (Official/Teacher/CTV):** Personal check-in, history tracking, requests, and shift registration.
*   **Manager/HR:** Summary boards, daily monitoring, and request approvals.
*   **Admin:** Calculation cycles and global system policies.

---

## 2 FOR EMPLOYEES (USER GUIDE)

### 2.1 Face Enrollment & Daily Timekeeping
**Purpose:** Record daily presence using Face ID and GPS.
1.  **Face Enrollment:** (First time only) Click **[Đăng ký khuôn mặt]**. Look at the camera until the "Success" message appears.
2.  **Daily Check-in/out:**
    *   Navigate to the **Chấm công của tôi** tab.
    *   Click **[Check-in]** when arriving and **[Check-out]** when leaving.
3.  **Exception Handling:** If the system detects issues (e.g., *Outside office zone* or *Face suspect*):
    *   A warning box will appear.
    *   Enter a mandatory reason in the text area (e.g., "Working at client site").
    *   Click **[Gửi & Xác nhận]** to complete the action.

> **[IMAGE 1]:** *Screenshot of CheckInPanel.jsx showing the camera feed and the explanation input box.*

### 2.2 Attendance History & Personal Metrics
**Purpose:** Audit work logs and total credits.
1.  **View Logs:** Open the **Lịch sử chấm công** tab.
2.  **Filters:** Use the **Month Picker** or **Date Range** to filter records.
3.  **Summary Bar:** Review **Days Present**, **Total Credit**, **Deficit Credit**, and **Net Credit**.
4.  **Record Details:** Click any row to view photos taken during check-in/out and GPS locations on the map.

### 2.3 Attendance Rectification (Requests)
**Purpose:** Correct wrong timestamps or missing logs.
1.  In the **History Table**, click on the record that needs adjustment.
2.  The **Attendance Detail** drawer will open. Click **[Gửi đơn sửa]**.
3.  Fill in the **Proposed In/Out** times and provide a **Reason**.
4.  Click **[Gửi đơn]**. Track the status in the **Đơn của tôi** tab.

### 2.4 Shift & OT Registration
**Purpose:** Register extra shifts (OT) or CTV schedules.
1.  Navigate to the **Ca làm việc (CTV/OT)** tab.
2.  Click **[Đăng ký ca]**.
3.  **Multi-day registration:** Check the **"Đăng ký cho nhiều ngày"** box to select multiple dates for the same time frame.
4.  Select **Shift Type** (OT/CTV) and **OT Level** (100%, 150%, 300%).

---

## 3 FOR MANAGERS & HR

### 3.1 Management Dashboards
1.  **Summary Board:** View a monthly table of all employees with their total regular, OT, and CTV credits. Click an employee to see their full month detail.
2.  **Daily Table:** Monitor the office status for today. View who is **On Time**, **Late**, or **Missing**.

### 3.2 Request Approval
1.  Open the **Đơn chấm công** tab.
2.  Review pending requests from staff.
3.  Click **[Approve]** to automatically update the employee's attendance log or **[Reject]**.

### 3.3 Manual Adjustments
Managers can manually edit or delete any attendance record by opening the record detail and clicking the **[Sửa]** or **[Xóa]** button.

---

## 4 FOR ADMINS (SYSTEM CONFIGURATION)

### 4.1 Attendance Cycles
1.  Navigate to **Attendance Config** -> **Chu kỳ tính công**.
2.  Set the **Period Start Day** (e.g., 26th of the month) to define how monthly reports are cut.

### 4.2 System Policy & Geo-fencing
1.  Open the **Cấu hình hệ thống** tab.
2.  **Check-in/out Windows:** Define the allowed time ranges for morning and evening.
3.  **Late Cutoff:** Set the strict time after which employees are marked as "Late".
4.  **Google Maps Integration:** Paste a Google Maps URL; the system will auto-extract **Latitude** and **Longitude**.
5.  **Office Radius:** Set the allowed distance (in meters) for valid check-ins.
6.  **Face Sensitivity:** Set the **Face Threshold** (Default 0.6).

---

## 5 DATA DICTIONARY
| Field | Code Reference | Description |
| :--- | :--- | :--- |
| **Late Minutes** | `lateMinutes` | Minutes delayed compared to shift start. |
| **Work Credit** | `workCredit` | The value of the attendance (1.0 = Full day). |
| **Needs Review** | `needsReview` | Flagged if face suspect or out of zone. |
