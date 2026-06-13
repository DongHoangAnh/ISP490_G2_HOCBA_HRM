from datetime import timedelta

from odoo import http, fields
from odoo.http import request, Response
from odoo.tools import file_open

# 13/06/2026: SPA là frontend chính thức (FE/BE tách riêng qua API).
# Dev:   cd frontend && npm run dev   (Vite :5173, proxy API về Odoo)
# Build: cd frontend && npm run build → static/spa/, route này serve bản build.
# (quy ước: docs/QUY_UOC_FRONTEND.md)
SPA_ENABLED = True


# Bảng màu gán cho phòng ban theo thứ tự id (SPA filter chips)
DEP_PALETTE = ['#C8102E', '#D9A400', '#0F766E', '#1D4ED8', '#6D28D9',
               '#BE185D', '#B45309', '#334155']


def _d(v):
    """date/datetime → chuỗi ISO (None-safe)."""
    return v.isoformat() if v else None


class HocBaHRM(http.Controller):

    @http.route('/hocba-hrm', auth='user', type='http', csrf=False)
    def hrm_dashboard(self, **kw):
        if not SPA_ENABLED:
            return request.redirect('/odoo')
        try:
            with file_open('hocba_hrm/static/spa/index.html', 'r') as f:
                html = f.read()
        except (FileNotFoundError, OSError):
            html = ('<h3 style="font-family:sans-serif">SPA chưa được build.</h3>'
                    '<p style="font-family:sans-serif">Chạy: <code>cd frontend &amp;&amp; '
                    'npm install &amp;&amp; npm run build</code> rồi tải lại trang '
                    '(xem docs/QUY_UOC_FRONTEND.md §8).</p>')
        return Response(html, content_type='text/html; charset=utf-8')

    # ------------------------------------------------------------------
    # JSON API cho SPA — dữ liệu thật từ hocba_employees.
    # Trường nhạy cảm chỉ trả khi user thuộc nhóm HR tương ứng:
    #   hr.group_hr_user    → CCCD, ngày sinh, pháp lý cơ bản, NPT, chứng chỉ
    #   hr.group_hr_manager → MST TNCN, BHXH, lương (wage / from_wage / to_wage)
    # ------------------------------------------------------------------

    def _hr_flags(self):
        user = request.env.user
        return (user.has_group('hr.group_hr_user'),
                user.has_group('hr.group_hr_manager'))

    def _labels(self):
        env = request.env
        Emp = env['hr.employee']

        def sel(model, fname):
            return dict(model._fields[fname]._description_selection(env))

        return {
            'status': sel(Emp, 'x_employment_status'),
            'work_form': sel(Emp, 'x_work_form'),
            'position': sel(Emp, 'x_position_type'),
            'asset_state': sel(env['hr.employee.asset'], 'state'),
            'relationship': sel(env['hr.employee.dependent'], 'relationship'),
        }

    def _emp_base(self, e, labels, is_mgr):
        status_key = e.x_employment_status or ''
        etype = ('CTV' if status_key == 'ctv'
                 else labels['work_form'].get(e.x_work_form, '—'))
        data = {
            'id': e.id,
            'code': e.x_employee_code or '—',
            'name': e.name,
            'dep': e.department_id.id or 0,
            'depName': e.department_id.name or 'Chưa gán',
            'jobTitle': e.job_id.name or '—',
            'status': labels['status'].get(status_key, '—'),
            'statusKey': status_key,
            'type': etype,
            'posType': labels['position'].get(e.x_position_type, ''),
            'posTypeKey': e.x_position_type or '',
            'start': _d(e.x_probation_start) or _d(e.create_date and e.create_date.date()),
            'email': e.work_email or '',
            'phone': e.work_phone or '',
            'hasImg': bool(e.image_1920),
        }
        if is_mgr:
            v = e.version_id
            data['wage'] = (v.wage if v and 'wage' in v._fields else 0) or 0
        return data

    @http.route('/hocba-hrm/api/employees', auth='user', type='http', methods=['GET'])
    def api_employees(self, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        labels = self._labels()
        emps = request.env['hr.employee'].sudo().search([], order='x_employee_code, id')

        deps = {}
        for i, d in enumerate(emps.mapped('department_id').sorted('id')):
            deps[d.id] = {'id': d.id, 'name': d.name, 'total': 0,
                          'official': 0, 'probation': 0,
                          'color': DEP_PALETTE[i % len(DEP_PALETTE)]}
        rows = []
        for e in emps:
            rows.append(self._emp_base(e, labels, is_mgr))
            dd = deps.get(e.department_id.id)
            if dd:
                dd['total'] += 1
                if e.x_employment_status == 'official':
                    dd['official'] += 1
                elif e.x_employment_status == 'probation':
                    dd['probation'] += 1

        return request.make_json_response({
            'isHr': is_hr,
            'isHrManager': is_mgr,
            'departments': list(deps.values()),
            'employees': rows,
        })

    @http.route('/hocba-hrm/api/employee/<int:emp_id>', auth='user',
                type='http', methods=['GET'])
    def api_employee_detail(self, emp_id, **kw):
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, is_mgr = self._hr_flags()
        labels = self._labels()
        e = request.env['hr.employee'].sudo().browse(emp_id)
        if not e.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)

        data = self._emp_base(e, labels, is_mgr)

        # --- Pháp lý (F-002) + NPT (F-003): chỉ HR ---
        if is_hr:
            data.update({
                'bday': _d(e.birthday),
                'cccd': e.identification_id or '',
                'idIssue': _d(e.x_id_date_issue),
                'idPlace': e.x_id_place_issue or '',
                'hi': e.x_health_insurance_no or '',
                'hiPlace': e.x_health_care_place or '',
                'permanentAddr': ', '.join(p for p in (
                    e.x_permanent_street, e.x_permanent_ward,
                    e.x_permanent_state_id.name) if p),
                'currentAddr': ('Giống thường trú' if e.x_current_same_as_permanent
                                else ', '.join(p for p in (
                                    e.x_current_street, e.x_current_ward,
                                    e.x_current_state_id.name) if p)),
                'dependents': [{
                    'name': dp.name,
                    'relationship': labels['relationship'].get(dp.relationship, ''),
                    'birthday': _d(dp.birthday),
                    'from': _d(dp.date_start),
                    'to': _d(dp.date_end),
                } for dp in e.x_dependent_ids],
            })
        if is_mgr:
            data.update({
                'pit': e.x_pit_code or '',
                'si': e.x_social_insurance_no or '',
            })

        # --- Thử việc 2 cổng (F-004/005) — Nhóm B ---
        data['probation'] = {
            'isGroupB': (e.x_position_type in ('staff', 'manager')
                         and e.x_work_form == 'offline'),
            'start': _d(e.x_probation_start),
            'd2wDue': _d(e.x_eval_2w_due),
            'd2wResult': e.x_eval_2w_result or 'draft',
            'd2wDate': _d(e.x_eval_2w_date),
            'd2wNote': e.x_eval_2w_note or '',
            'equipDate': _d(e.x_equip_grant_date),
            'd2mDue': _d(e.x_eval_2m_due),
            'd2mResult': e.x_eval_2m_result or 'draft',
            'd2mDate': _d(e.x_eval_2m_date),
            'd2mNote': e.x_eval_2m_note or '',
            'officialDate': _d(e.x_official_date),
            'officialMonths': round(e.x_official_months or 0, 1),
        }

        # --- Thử giảng (F-008) — Nhóm A ---
        if (e.x_work_form == 'online'
                or e.x_employment_status in ('parttime', 'ctv', 'advisor')):
            data['trial'] = {
                'date': _d(e.x_trial_lesson_date),
                'class': e.x_trial_lesson_class or '',
                'scoreMethod': e.x_trial_score_method or 0,
                'scoreContent': e.x_trial_score_content or 0,
                'result': e.x_trial_lesson_result or 'draft',
                'note': e.x_trial_lesson_note or '',
            }

        # --- Tài sản (F-006) ---
        data['assets'] = [{
            'id': a.id,
            'type': a.asset_type_id.name or '',
            'code': a.asset_code or '',
            'grant': _d(a.grant_date),
            'state': a.state,
            'stateLabel': labels['asset_state'].get(a.state, a.state),
            'returnDate': _d(a.return_date),
        } for a in e.x_asset_ids.sorted('grant_date')]

        # --- Thăng tiến (F-007) ---
        promotions = []
        for p in e.x_promotion_ids.sorted('date_effective'):
            item = {
                'date': _d(p.date_effective),
                'fromJob': p.from_job_id.name or '—',
                'toJob': p.to_job_id.name or '—',
                'dept': p.to_department_id.name or '',
                'ref': p.decision_ref or '',
                'reason': p.reason or '',
            }
            if is_mgr:
                item.update({'fromWage': p.from_wage or 0,
                             'toWage': p.to_wage or 0})
            promotions.append(item)
        data['promotions'] = promotions

        # --- Chứng chỉ (F-008/009): chỉ HR ---
        if is_hr:
            data['certs'] = [{
                'skill': s.skill_id.name or '',
                'level': s.skill_level_id.name or '',
                'date': _d(s.x_cert_date),
                'expiry': _d(s.x_cert_expiry),
                'status': s.x_cert_status or 'none',
                'verified': s.x_cert_verified,
            } for s in e.employee_skill_ids
                if s.x_cert_date or s.x_cert_expiry]

        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/employees/cert-alerts', auth='user',
                type='http', methods=['GET'])
    def api_cert_alerts(self, **kw):
        """F-009: chứng chỉ sắp/đã hết hạn — widget cảnh báo dashboard.
        Cert là dữ liệu HR → non-HR nhận danh sách rỗng (không phải 403) để
        dashboard tự ẩn widget."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        is_hr, _ = self._hr_flags()
        if not is_hr:
            return request.make_json_response({'isHr': False, 'alerts': []})

        # Khớp đúng tập cảnh báo của CRON F-009 (_cron_cert_expiry_alerts):
        # chỉ cert ĐÃ XÁC MINH + nhân viên active; search trên x_cert_expiry
        # (stored) vì x_cert_status là computed non-stored, không search được.
        days = int(request.env['ir.config_parameter'].sudo().get_param(
            'hoc_ba.cert_alert_days', '60'))
        today = fields.Date.today()
        skills = request.env['hr.employee.skill'].sudo().search([
            ('x_cert_verified', '=', True),
            ('employee_id.active', '=', True),
            ('x_cert_expiry', '!=', False),
            ('x_cert_expiry', '<=', today + timedelta(days=days)),
        ])
        alerts = []
        for s in skills:
            e = s.employee_id
            alerts.append({
                'empId': e.id,
                'empName': e.name,
                'empCode': e.x_employee_code or '—',
                'dep': e.department_id.name or 'Chưa gán',
                'hasImg': bool(e.image_1920),
                'skill': s.skill_id.name or '',
                'level': s.skill_level_id.name or '',
                'expiry': _d(s.x_cert_expiry),
                'status': 'expired' if s.x_cert_expiry < today else 'expiring',
            })
        # sắp xếp: hết hạn trước, rồi theo ngày hết hạn gần nhất
        alerts.sort(key=lambda a: (a['status'] != 'expired', a['expiry'] or '9999'))
        return request.make_json_response({'isHr': True, 'alerts': alerts})
