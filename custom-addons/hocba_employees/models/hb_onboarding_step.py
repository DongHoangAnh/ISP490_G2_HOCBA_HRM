from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

# Trần cho một lần gia hạn. Không phải luật nghiệp vụ, chỉ là chặn gõ nhầm:
# nhập 3650 vì thừa số 0 thì hạn nhảy 10 năm mà không ai nhận ra ngay.
MAX_EXTEND_DAYS = 365

STATE_SEL = [
    ('waiting', 'Chưa tới lượt'),
    ('open', 'Đang chờ'),
    ('done', 'Hoàn thành'),
    ('skipped', 'Bỏ qua'),
]
RESULT_SEL = [('pass', 'Đạt'), ('extend', 'Gia hạn'), ('fail', 'Không đạt')]


class HbOnboardingStep(models.Model):
    """Bước nhận việc/thử việc trên TỪNG nhân viên — snapshot từ template
    lúc gán (sửa template sau không ảnh hưởng NV đang chạy).
    Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md"""
    _name = 'hb.onboarding.step'
    _description = 'Bước nhận việc/thử việc của nhân viên (instance snapshot)'
    _order = 'sequence, id'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên', required=True,
        ondelete='cascade', index=True)
    template_id = fields.Many2one(
        'hb.onboarding.template', string='Từ template', ondelete='set null')
    # --- snapshot từ template.step (không đọc lại template) ---
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Tên bước', required=True)
    step_type = fields.Selection(
        [('task', 'Việc cần làm'), ('evaluation', 'Đánh giá')],
        string='Loại bước', default='task', required=True)
    pass_completes = fields.Boolean(string='Đạt → lên chính thức')
    is_extension = fields.Boolean(string='Bước gia hạn')
    # Bước ngoài chuỗi: mở ngay lúc gán, điều hướng chuỗi không đụng tới.
    is_independent = fields.Boolean(string='Không ràng buộc thứ tự')
    auto_action = fields.Selection(
        [('none', 'Không'), ('grant_assets', 'Tự cấp tài sản mặc định')],
        string='Automation', default='none', required=True)
    note = fields.Text(string='Hướng dẫn')
    # --- runtime ---
    due_date = fields.Date(string='Hạn')
    state = fields.Selection(
        STATE_SEL, string='Trạng thái', default='waiting',
        required=True, index=True)
    result = fields.Selection(RESULT_SEL, string='Kết quả')
    extend_count = fields.Integer(string='Số lần gia hạn tại chỗ', default=0)
    extend_days_total = fields.Integer(
        string='Tổng ngày đã gia hạn', default=0,
        help='Cộng dồn số ngày HR đã gia hạn tại bước này. Số ngày đó đã được '
             'cộng thẳng vào Hạn của bước này và mọi bước sau nó.')
    done_date = fields.Date(string='Ngày hoàn thành')
    done_by_id = fields.Many2one('res.users', string='Người thực hiện')
    result_note = fields.Text(string='Nhận xét')

    @api.constrains('step_type', 'is_independent', 'auto_action')
    def _check_independent_flags(self):
        """Phản chiếu _check_step_flags của bước mẫu lên bản snapshot.

        Snapshot không đi qua template khi ghi, mà ir.model.access cho
        hr.group_hr_user quyền write thẳng model này — thiếu ràng buộc ở đây
        thì mọi bất biến của spec §5.1 vá được bằng một lệnh write."""
        for step in self:
            if step.is_independent and step.step_type != 'task':
                raise ValidationError(_(
                    'Cờ "Không ràng buộc thứ tự" chỉ dùng cho bước Việc '
                    'cần làm — các bước Đánh giá phải chạy tuần tự.'))
            if step.is_independent and step.auto_action != 'none':
                raise ValidationError(_(
                    'Bước "không ràng buộc thứ tự" mở ngay từ đầu nên không '
                    'được đặt Automation — nếu không nó sẽ tự chạy ngày đầu.'))

    # ------------------------------------------------------------------
    # Điều hướng chuỗi
    # ------------------------------------------------------------------
    def _chain(self):
        """Toàn bộ bước của NV, đúng thứ tự. sudo: user thường/QL không đọc
        được field ngoài whitelist public profile của hr.employee (Odoo 19);
        quyền thao tác đã gác ở _check_can_act."""
        self.ensure_one()
        return self.employee_id.sudo().x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def _next_waiting(self):
        """Bước 'waiting' trong CHUỖI đứng sau self gần nhất (rỗng nếu hết).

        Bước is_independent nằm ngoài chuỗi: không bao giờ được mở hay bỏ
        qua bởi điều hướng — HR làm nó lúc nào cũng được."""
        self.ensure_one()
        if self.is_independent:
            return self.browse()
        chain = [s for s in self._chain() if not s.is_independent]
        idx = chain.index(self)
        for step in chain[idx + 1:]:
            if step.state == 'waiting':
                return step
        return self.browse()

    def _skip_auto(self):
        """NV bật x_skip_auto_trigger → ghi kết quả nhưng bỏ side-effect."""
        return self.employee_id.sudo().x_skip_auto_trigger

    # ------------------------------------------------------------------
    # Máy trạng thái
    # ------------------------------------------------------------------
    def _open(self):
        """Mở bước; task có auto_action → chạy automation rồi tự done."""
        self.ensure_one()
        self.sudo().write({'state': 'open'})
        if self.step_type == 'task' and self.auto_action == 'grant_assets':
            if not self._skip_auto():
                self.employee_id.sudo()._hocba_grant_default_assets()
            self.sudo().write({
                'state': 'done',
                'done_date': fields.Date.context_today(self),
                'done_by_id': self.env.user.id,
            })
            self._advance()

    def _advance(self):
        """Sau khi self done/skipped: mở bước kế; skip bước gia hạn nếu self
        không Gia hạn; hết chuỗi mà chưa official → chuông HR chờ quyết định."""
        self.ensure_one()
        if self.is_independent:
            # Bước ngoài chuỗi: xong thì thôi, không mở bước nào và KHÔNG
            # được coi là "hết chuỗi" (nếu không sẽ bắn chuông hoàn tất sai).
            return
        nxt = self._next_waiting()
        if not nxt:
            emp = self.employee_id.sudo()
            if (emp.x_employment_status == 'probation'
                    and not self._skip_auto()):
                emp._hocba_notify_probation(
                    'onboarding_chain_done', 'info',
                    _('Hoàn tất quy trình nhận việc: %s') % emp.name,
                    body=_('Mọi bước đã xong — chờ HR quyết định trạng '
                           'thái nhân sự.'),
                    dedup_key='onb_chain_done:%s' % emp.id)
            return
        if nxt.is_extension and self.result != 'extend':
            nxt.sudo().write({'state': 'skipped'})
            nxt._advance()
        else:
            nxt._open()

    def _ensure_open(self, want_type):
        self.ensure_one()
        if self.state != 'open' or self.step_type != want_type:
            raise ValidationError(_(
                'Bước "%s" không ở trạng thái xử lý được.') % self.name)

    def _check_can_act(self):
        """HR Manager / quản lý trực tiếp / trưởng phòng ban NV; bước task cho
        thêm Giáo vụ với giáo viên. Sau check, thao tác ghi chạy sudo."""
        self.ensure_one()
        if self.env.su:
            return
        user = self.env.user
        emp = self.employee_id.sudo()
        if user.has_group('hr.group_hr_manager'):
            return
        if emp.parent_id and emp.parent_id.user_id == user:
            return
        if emp._hocba_user_manages_dept(user):
            return
        if (self.step_type == 'task'
                and user.has_group('hocba_employees.group_hocba_giaovu')
                and emp.x_employee_type_id.code == 'teacher'):
            return
        raise AccessError(_(
            'Bạn không có quyền xử lý bước nhận việc của nhân viên này.'))

    def action_complete(self, note=None):
        """Hoàn thành bước task (tay)."""
        self.ensure_one()
        self._check_can_act()
        self._ensure_open('task')
        uid = self.env.user.id
        vals = {'state': 'done',
                'done_date': fields.Date.context_today(self),
                'done_by_id': uid}
        if note:
            vals['result_note'] = note
        self.sudo().write(vals)
        self.employee_id.sudo().message_post(body=_(
            '✅ Bước nhận việc "%s" hoàn thành.') % self.name)
        self._advance()

    @staticmethod
    def _clean_extend_days(value):
        """Số ngày gia hạn HR nhập → int hợp lệ, hoặc ValidationError."""
        try:
            days = int(value)
        except (TypeError, ValueError):
            raise ValidationError(_('Cần nhập số ngày gia hạn.'))
        if not 1 <= days <= MAX_EXTEND_DAYS:
            raise ValidationError(_(
                'Số ngày gia hạn phải từ 1 đến %s.') % MAX_EXTEND_DAYS)
        return days

    def _shift_later_dues(self, days):
        """Dời hạn của mọi bước SAU bước này trong chuỗi, thêm `days` ngày.

        Chỉ đụng bước chưa xong: bước đã done/skipped là lịch sử, sửa hạn của
        nó là viết lại quá khứ. Bước ĐỘC LẬP nằm ngoài chuỗi (vd cấp thiết bị
        làm việc) nên KHÔNG dời — gia hạn một kỳ đánh giá không có lý do gì
        làm chậm việc cấp máy cho người ta. Bước không có hạn thì vẫn không có
        hạn: cộng ngày vào "không hạn" là bịa ra một cái hạn chưa ai đặt."""
        self.ensure_one()
        chain = [s for s in self._chain() if not s.is_independent]
        if self not in chain:
            return
        for step in chain[chain.index(self) + 1:]:
            if step.state in ('waiting', 'open') and step.due_date:
                step.sudo().due_date = step.due_date + timedelta(days=days)

    def action_evaluate(self, result, note=None, eval_date=None,
                        extend_days=None):
        """Ghi kết quả bước evaluation: pass / extend / fail.

        - pass + pass_completes → lên Chính thức, skip bước còn lại.
        - pass thường → mở bước kế (bước gia hạn kế tiếp bị skip).
        - extend: BẮT BUỘC kèm extend_days. Số ngày đó cộng vào hạn của bước
          này (nếu nó còn mở) và hạn của mọi bước sau — nhờ vậy "ngày kết thúc
          thử việc" ở màn Nhận việc (suy ra từ hạn muộn nhất) mới thực sự lùi
          ra. Trước 2026-08-27 gia hạn KHÔNG đụng ngày nào: bấm gia hạn 2 lần
          rồi vẫn lên chính thức đúng ngày cũ.
          Bước kế là is_extension → done + mở bước đó (cổng tháng-1 cũ);
          không thì giữ open + extend_count++ (tái đánh giá — cổng
          tuần-2/tháng-2 cũ).
        - fail → skip bước còn lại + khởi động offboarding (hành vi cũ)."""
        self.ensure_one()
        self._check_can_act()
        self._ensure_open('evaluation')
        if result not in ('pass', 'extend', 'fail'):
            raise ValidationError(_('Kết quả không hợp lệ.'))
        if result == 'fail' and not (note or '').strip():
            raise ValidationError(_(
                'Cần nhập nhận xét khi kết quả Không đạt.'))
        today = fields.Date.context_today(self)
        uid = self.env.user.id
        done_vals = {'done_date': eval_date or today, 'done_by_id': uid}
        if note:
            done_vals['result_note'] = note
        emp = self.employee_id.sudo()

        if result == 'extend':
            days = self._clean_extend_days(extend_days)
            nxt = self._next_waiting()
            stays_open = not (nxt and nxt.is_extension)
            # Dời hạn TRƯỚC khi đổi trạng thái: _advance() có thể mở bước kế,
            # và bước đó phải mở ra với hạn ĐÃ cộng thêm, không phải hạn cũ.
            if stays_open and self.due_date:
                self.sudo().due_date = self.due_date + timedelta(days=days)
            self._shift_later_dues(days)
            vals = dict(done_vals,
                        extend_days_total=self.extend_days_total + days)
            if stays_open:
                # hành vi cổng 2w/2m cũ: giữ open, hẹn tái đánh giá
                self.sudo().write(dict(vals,
                                       extend_count=self.extend_count + 1))
            else:
                # hành vi cổng tháng-1 cũ: done + mở bước gia hạn
                self.sudo().write(dict(vals, state='done', result='extend'))
                self._advance()
            if not self._skip_auto():
                emp._hocba_notify_probation(
                    'probation_extend', 'warning',
                    _('Gia hạn thử việc: %s') % emp.name,
                    body=_('Bước "%s" gia hạn thêm %s ngày.')
                         % (self.name, days),
                    include_employee=True)
            han_moi = (_(' — hạn mới %s') % self.due_date
                       if stays_open and self.due_date else '')
            emp.sudo().message_post(body=_(
                '⏳ Bước "%s" GIA HẠN +%s ngày%s. Hạn các bước sau cũng lùi '
                'thêm %s ngày.') % (self.name, days, han_moi, days))
            return

        self.sudo().write(dict(done_vals, state='done', result=result))
        if result == 'fail':
            self._chain().filtered(
                lambda s: s.state in ('waiting', 'open')
                and not s.is_independent).sudo().write({'state': 'skipped'})
            if not self._skip_auto():
                emp._hocba_start_offboarding(self.name)
            return
        # result == 'pass'
        if self.pass_completes and not self._skip_auto():
            # Đối xứng với nhánh fail: bước độc lập không bao giờ bị điều
            # hướng chuỗi chạm tới. Thực tế bước độc lập luôn ở 'open' (mở
            # ngay lúc gán) nên clause này hiếm khi chạy — giữ để trạng thái
            # 'waiting' do migration/gán lại quy trình sinh ra vẫn an toàn.
            self._chain().filtered(
                lambda s: s.state == 'waiting'
                and not s.is_independent).sudo().write({'state': 'skipped'})
            emp._hocba_make_official(self.name)
            return
        emp.sudo().message_post(body=_('✅ Bước "%s" ĐẠT.') % self.name)
        self._advance()
