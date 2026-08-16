"""
Public Payslip Controller — token-based payslip view and confirmation.
Employees access their payslip via unique token link (no login required).
"""
import logging

from odoo import http, fields, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class PayrollPublicController(http.Controller):

    def _get_payslip_by_token(self, token):
        if not token:
            return None
        slip = request.env['hb.payslip'].sudo().search(
            [('x_access_token', '=', token)], limit=1,
        )
        return slip if slip.exists() else None

    @http.route('/payslip/view/<string:token>', type='http',
                auth='user', methods=['GET'], csrf=False)
    def view_payslip(self, token, **kw):
        slip = self._get_payslip_by_token(token)
        if not slip:
            return request.render('hocba_payroll.payslip_public_not_found')

        user = request.env.user
        user_email = (user.partner_id.email or user.login or '').strip().lower()
        emp_email = (slip.employee_id.work_email or '').strip().lower()

        # Strict matching: currently logged-in user MUST be the payslip employee
        is_owner = (slip.employee_id.user_id.id == user.id) or (emp_email and user_email == emp_email)

        if not is_owner:
            return request.render('hocba_payroll.payslip_unauthorized', {
                'employee_name': slip.employee_id.name,
                'employee_email': slip.employee_id.work_email or 'Chưa cập nhật',
                'user_name': user.name or user.login,
                'user_email': user_email,
                'token': token,
            })

        # Authorized owner! Redirect to the real SPA app (http://localhost:8069/hocba-hrm)
        return request.redirect(f'/hocba-hrm?payslip_id={slip.id}')

    @http.route('/payslip/view/<string:token>/confirm', type='http',
                auth='public', methods=['POST'], csrf=False)
    def confirm_payslip_public(self, token, **kw):
        slip = self._get_payslip_by_token(token)
        if not slip:
            return Response('Payslip not found.', status=404)

        now = fields.Datetime.now()
        if slip.x_confirm_deadline and now > slip.x_confirm_deadline:
            return request.redirect(f'/payslip/view/{token}?msg=expired')

        slip.sudo().write({
            'x_employee_confirm': 'confirmed',
            'x_auto_confirm': False,
            'x_confirmed_date': now,
        })
        slip.sudo().message_post(
            body=_('Nhân viên <b>%(name)s</b> đã <b>xác nhận (đồng ý)</b> phiếu lương.', name=slip.employee_id.name),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        return request.redirect(f'/payslip/view/{token}?msg=confirmed')

    @http.route('/payslip/view/<string:token>/reject', type='http',
                auth='public', methods=['POST'], csrf=False)
    def reject_payslip_public(self, token, **kw):
        slip = self._get_payslip_by_token(token)
        if not slip:
            return Response('Payslip not found.', status=404)

        now = fields.Datetime.now()
        if slip.x_confirm_deadline and now > slip.x_confirm_deadline:
            return request.redirect(f'/payslip/view/{token}?msg=expired')

        feedback = kw.get('feedback', '').strip()
        if not feedback:
            return request.redirect(f'/payslip/view/{token}?msg=feedback_required')

        slip.sudo().write({
            'x_employee_confirm': 'rejected',
            'x_auto_confirm': False,
            'x_employee_feedback': feedback,
            'x_confirmed_date': now,
        })
        slip.sudo().message_post(
            body=_(
                'Nhân viên <b>%(name)s</b> đã gửi <b>phản hồi / khiếu nại</b> phiếu lương. Lý do: %(fb)s',
                name=slip.employee_id.name, fb=feedback,
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        return request.redirect(f'/payslip/view/{token}?msg=rejected')
