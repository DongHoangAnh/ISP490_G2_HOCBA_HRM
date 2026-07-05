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
                auth='public', methods=['GET'], csrf=False)
    def view_payslip(self, token, **kw):
        slip = self._get_payslip_by_token(token)
        if not slip:
            return request.render('hocba_payroll.payslip_public_not_found')

        lines = slip.line_ids.sorted('sequence')
        month = slip.date_from.strftime('%m') if slip.date_from else ''
        year = slip.date_from.strftime('%Y') if slip.date_from else ''

        return request.render('hocba_payroll.payslip_public_view', {
            'slip': slip,
            'employee': slip.employee_id,
            'lines': lines,
            'month': month,
            'year': year,
            'gross': slip.gross_amount,
            'net': slip.net_amount,
            'token': token,
        })

    @http.route('/payslip/view/<string:token>/confirm', type='http',
                auth='public', methods=['POST'], csrf=False)
    def confirm_payslip_public(self, token, **kw):
        slip = self._get_payslip_by_token(token)
        if not slip:
            return Response('Payslip not found.', status=404)

        if slip.x_employee_confirm == 'confirmed':
            return request.redirect(f'/payslip/view/{token}?msg=already_actioned')

        slip.sudo().write({
            'x_employee_confirm': 'confirmed',
            'x_confirmed_date': fields.Datetime.now(),
        })
        slip.sudo().message_post(
            body=_('Nhân viên <b>%(name)s</b> đã <b>xác nhận</b> phiếu lương.', name=slip.employee_id.name),
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

        if slip.x_employee_confirm == 'confirmed':
            return request.redirect(f'/payslip/view/{token}?msg=already_actioned')

        feedback = kw.get('feedback', '').strip()
        if not feedback:
            return request.redirect(f'/payslip/view/{token}?msg=feedback_required')

        slip.sudo().write({
            'x_employee_confirm': 'rejected',
            'x_employee_feedback': feedback,
            'x_confirmed_date': fields.Datetime.now(),
        })
        slip.sudo().message_post(
            body=_(
                'Nhân viên <b>%(name)s</b> đã <b>từ chối</b> phiếu lương. Lý do: %(fb)s',
                name=slip.employee_id.name, fb=feedback,
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        return request.redirect(f'/payslip/view/{token}?msg=rejected')
