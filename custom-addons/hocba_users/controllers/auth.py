from odoo import http
from odoo.http import request


class AuthController(http.Controller):
    
    @http.route('/hocba/login', type='http', auth='public')
    def login(self, **kwargs):
        return request.render('hocba_users.login_template', {})
    
    @http.route('/hocba/do_login', type='http', auth='public', methods=['POST'], csrf=False)
    def do_login(self, email=None, password=None, **kwargs):
        if email and password:
            user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
            if user:
                hocba_user = request.env['hocba.user'].sudo().search([('user_id', '=', user.id)], limit=1)
                if hocba_user and hocba_user.is_active:
                    hocba_user.action_update_last_login()
                    request.session.authenticate(user.login, password)
                    return request.redirect('/web')
        
        return request.render('hocba_users.login_template', {'error': 'Invalid credentials'})
    
    @http.route('/hocba/logout', type='http', auth='user')
    def logout(self):
        request.session.logout()
        return request.redirect('/hocba/login')
