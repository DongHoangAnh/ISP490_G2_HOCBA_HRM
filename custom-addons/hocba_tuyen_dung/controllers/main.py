from odoo import http
from odoo.http import Response


class HocBaTuyenDung(http.Controller):

    @http.route('/hocba-tuyen-dung', auth='user', type='http', csrf=False)
    def recruitment_app(self, **kw):
        base = '/hocba_tuyen_dung/static/src'
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Tuyển dụng Học Bá — Hệ thống Quản lý Tuyển dụng</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{base}/css/rec-styles.css" />
</head>
<body>
<div id="root"></div>
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>
<script type="text/babel" src="{base}/js/rec-data.jsx"></script>
<script type="text/babel" src="{base}/js/rec-shell.jsx"></script>
<script type="text/babel" src="{base}/js/rec-dashboard.jsx"></script>
<script type="text/babel" src="{base}/js/rec-app.jsx"></script>
</body>
</html>"""
        return Response(html, content_type='text/html; charset=utf-8')
