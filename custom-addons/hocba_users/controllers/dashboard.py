from odoo import http
from odoo.http import request


class DashboardController(http.Controller):
    
    @http.route('/hocba/dashboard', type='http', auth='user')
    def dashboard(self):
        hocba_user = request.env['hocba.user'].search(
            [('user_id', '=', request.uid)],
            limit=1
        )
        
        if not hocba_user:
            return request.redirect('/web')
        
        role_code = hocba_user.role_code
        
        context = {
            'hocba_user': hocba_user,
            'role_code': role_code,
        }
        
        if role_code == 'admin':
            return request.render('hocba_users.admin_dashboard', context)
        elif role_code == 'hr_manager':
            return request.render('hocba_users.hr_manager_dashboard', context)
        else:
            return request.render('hocba_users.employee_dashboard', context)
