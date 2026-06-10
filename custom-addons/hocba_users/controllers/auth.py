from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import request


class AuthController(http.Controller):

    @http.route('/hocba/login', type='http', auth='public')
    def login(self, **kwargs):
        return request.render('hocba_users.login_template', {})

    @http.route('/hocba/do_login', type='http', auth='public', methods=['POST'], csrf=False)
    def do_login(self, email=None, password=None, **kwargs):
        error = {'error': 'Invalid credentials'}
        if not email or not password:
            return request.render('hocba_users.login_template', error)

        user = request.env['res.users'].sudo().search(
            [('email', '=', email)], limit=1)
        if not user:
            return request.render('hocba_users.login_template', error)

        hocba_user = request.env['hocba.user'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        if not hocba_user or not hocba_user.is_active:
            return request.render('hocba_users.login_template', error)

        # Odoo 19: authenticate(env, credential_dict)
        try:
            request.session.authenticate(request.env, {
                'login': user.login,
                'password': password,
                'type': 'password',
            })
        except AccessDenied:
            return request.render('hocba_users.login_template', error)

        # Chỉ ghi last_login sau khi xác thực THÀNH CÔNG
        hocba_user.action_update_last_login()
        return request.redirect('/web')

    @http.route('/hocba/logout', type='http', auth='user')
    def logout(self):
        request.session.logout()
        return request.redirect('/hocba/login')
