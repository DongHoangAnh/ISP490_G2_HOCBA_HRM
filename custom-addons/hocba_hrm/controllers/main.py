from odoo import http
from odoo.http import request, Response


class HocBaHRM(http.Controller):

    @http.route('/hocba-hrm', auth='user', type='http', csrf=False)
    def hrm_dashboard(self, **kw):
        base = '/hocba_hrm/static/src'
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Học Bá HRM — Hệ thống Quản lý Nhân sự</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{base}/css/hrm-styles.css" />
</head>
<body>
<div id="root"></div>
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>
<script type="text/babel" src="{base}/js/hrm-data.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-shell.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-journey.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-dashboard.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-employees.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-onboarding.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-attendance.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-timeoff.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-payroll.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-contracts.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-recruitment.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-appraisal.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-reports.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-profile.jsx"></script>
<script type="text/babel" src="{base}/js/hrm-app.jsx"></script>
</body>
</html>"""
        return Response(html, content_type='text/html; charset=utf-8')
