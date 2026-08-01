import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

from .hocba_hr_request_type import RECIPIENT_SEL

_logger = logging.getLogger(__name__)

OPEN_STATES = ('new', 'in_progress')
ANON_LABEL = 'Người gửi (ẩn danh)'

# Mặc định 2 ngưỡng cấu hình (SPEC SVC §2.2). Sửa được ở màn Cấu hình P6 /
# Odoo backend mà KHÔNG sửa code — DB test có phòng < 5 NV nên lúc demo phải
# hạ min_anon_dept_size xuống cho khớp dữ liệu.
PARAM_MIN_ANON_DEPT = 'hocba_service.min_anon_dept_size'
PARAM_ANON_DAILY = 'hocba_service.anon_daily_limit'
DEFAULT_MIN_ANON_DEPT = 5
DEFAULT_ANON_DAILY = 3


class SvcError(ValidationError):
    """Vi phạm business rule của module dịch vụ, có mã lỗi để SPA hiện đúng
    thông điệp. Controller P2 map: except SvcError as e -> 400 + e.code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------
# Helper cấp module — test gọi trực tiếp (quy ước test của repo), controller P2
# import lại đúng những hàm này để không có 2 nguồn sự thật về phạm vi.
# ---------------------------------------------------------------------------

def _managed_department_ids(env, emp):
    """Phòng ban (gồm phòng con) mà emp làm trưởng phòng (manager_id).

    Bản sao cục bộ có chủ ý — hocba_timeoff cũng tự giữ một bản (controllers/
    main.py:109) thay vì import từ hocba_hrm, để không phải depends hocba_hrm.
    """
    if not emp:
        return []
    Dept = env['hr.department'].sudo()
    managed = Dept.search([('manager_id', '=', emp.id)])
    if not managed:
        return []
    result, frontier = set(managed.ids), managed
    while frontier:
        children = Dept.search([('parent_id', 'in', frontier.ids)])
        frontier = children.filtered(lambda d: d.id not in result)
        result.update(frontier.ids)
    return list(result)


def _svc_scope(env):
    """Vai trò + phạm vi xử lý đơn dịch vụ của user hiện tại.

    Lưu ý: Trưởng phòng KHÔNG có group riêng và KHÔNG có ACL trên
    hocba.hr.request ⇒ mọi truy cập của TP đi qua .sudo() sau khi lọc bằng
    _inbox_domain() (đúng convention _scope_for của hocba_timeoff).
    """
    user = env.user
    is_admin = user.has_group('base.group_system')
    is_hr_mgr = is_admin or user.has_group('hr.group_hr_manager')
    is_hr = is_hr_mgr or user.has_group('hr.group_hr_user')
    dept_ids = _managed_department_ids(env, user.employee_id)
    return {
        'isHr': is_hr,
        'isHrManager': is_hr_mgr,
        'isDeptManager': bool(dept_ids),
        'deptIds': dept_ids,
        'canHandle': is_hr or bool(dept_ids),
    }


def _inbox_domain(scope):
    """Domain hộp thư "cần xử lý" theo phạm vi.

    BR-SVC-13 — HR/HR Manager KHÔNG giám sát đơn của Trưởng phòng: đơn
    recipient_scope='manager' chỉ vào hộp thư của HR khi bản thân HR đó cũng là
    trưởng phòng của phòng đích (tức đọc với tư cách TP, không phải tư cách HR).
    BR-SVC-01/10 — đơn force_hr_only không bao giờ vào hộp thư TP.
    """
    mgr_part = ['&', '&',
                ('recipient_scope', 'in', ('manager', 'both')),
                ('target_department_id', 'in', scope['deptIds']),
                ('type_id.force_hr_only', '=', False)]
    if scope['isHr']:
        hr_part = [('recipient_scope', 'in', ('hr', 'both'))]
        if scope['deptIds']:
            return ['|'] + hr_part + mgr_part
        return hr_part
    if scope['deptIds']:
        return mgr_part
    return [('id', '=', 0)]


def _my_request_ids(env):
    """Id các đơn do user hiện tại gửi.

    Không thể viết ir.rule tĩnh cho người gửi vì danh tính nằm ở bảng
    hocba.hr.request.sender (bảng cố tình không cấp ACL). Vì vậy: pin uid TRƯỚC,
    sudo SAU — đúng gotcha "Self-service" của CLAUDE.md.
    """
    rows = env['hocba.hr.request.sender'].sudo().search(
        [('user_id', '=', env.user.id)])
    return rows.mapped('request_id').ids


def _param_int(env, key, default):
    raw = env['ir.config_parameter'].sudo().get_param(key)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


class HocbaHrRequest(models.Model):
    """Đơn yêu cầu dịch vụ nhân sự / góp ý (SPEC SVC §3.1).

    ⚠️ Model này CỐ TÌNH không có field người gửi. Danh tính nằm ở
    hocba.hr.request.sender (không ACL) — xem docstring model đó. Đừng thêm
    employee_id/user_id/sender_ids vào đây.
    """
    _name = 'hocba.hr.request'
    _description = 'Đơn yêu cầu dịch vụ nhân sự'
    _order = 'create_date desc, id desc'

    STATE_SEL = [
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('answered', 'Đã trả lời'),
        ('closed', 'Đã đóng'),
        ('cancelled', 'Người gửi đã rút'),
    ]
    PRIORITY_SEL = [('normal', 'Bình thường'), ('urgent', 'Gấp')]
    RATING_SEL = [(str(i), '%d ★' % i) for i in range(1, 6)]

    name = fields.Char(
        string='Mã đơn', readonly=True, copy=False, default='/', index=True)
    type_id = fields.Many2one(
        'hocba.hr.request.type', string='Loại yêu cầu',
        required=True, ondelete='restrict', index=True)
    subject = fields.Char(string='Tiêu đề', required=True)
    body = fields.Text(string='Nội dung', required=True)
    recipient_scope = fields.Selection(
        RECIPIENT_SEL, string='Gửi tới', required=True, default='hr', index=True)
    target_department_id = fields.Many2one(
        'hr.department', string='Phòng đích', index=True,
        help='Snapshot phòng lúc gửi — dùng để ĐỊNH TUYẾN tới trưởng phòng. '
             'Với đơn ẩn danh, serializer tuyệt đối không trả field này ra API '
             '(SPEC SVC §2.2.1).')
    is_anonymous = fields.Boolean(string='Ẩn danh', default=False, index=True)
    rating = fields.Selection(RATING_SEL, string='Điểm đánh giá')
    priority = fields.Selection(
        PRIORITY_SEL, string='Mức ưu tiên', default='normal', required=True)
    state = fields.Selection(
        STATE_SEL, string='Trạng thái', default='new', required=True, index=True)
    handler_id = fields.Many2one(
        'res.users', string='Người xử lý', readonly=True, index=True)
    claimed_at = fields.Datetime(string='Nhận xử lý lúc', readonly=True)
    answered_at = fields.Datetime(string='Trả lời lúc', readonly=True)
    closed_at = fields.Datetime(string='Đóng lúc', readonly=True)
    closed_reason = fields.Text(string='Lý do đóng')
    deadline = fields.Datetime(
        string='Hạn xử lý', compute='_compute_deadline', store=True)
    is_overdue = fields.Boolean(
        string='Quá hạn', compute='_compute_is_overdue',
        search='_search_is_overdue')
    message_ids = fields.One2many(
        'hocba.hr.request.message', 'request_id', string='Hội thoại')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'hocba_hr_request_attachment_rel',
        'request_id', 'attachment_id', string='Tệp đính kèm')

    # ---------------------------------------------------------------- compute

    @api.depends('type_id.sla_days', 'create_date')
    def _compute_deadline(self):
        for rec in self:
            base = rec.create_date or fields.Datetime.now()
            rec.deadline = base + timedelta(days=rec.type_id.sla_days or 0)

    @api.depends('state', 'deadline')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_overdue = bool(
                rec.state in OPEN_STATES and rec.deadline and rec.deadline < now)

    def _search_is_overdue(self, operator, value):
        if operator not in ('=', '!='):
            raise NotImplementedError(
                'is_overdue chỉ hỗ trợ toán tử = và !=')
        truthy = bool(value) if operator == '=' else not value
        now = fields.Datetime.now()
        if truthy:
            return [('state', 'in', OPEN_STATES), ('deadline', '<', now)]
        return ['|', ('state', 'not in', OPEN_STATES), ('deadline', '>=', now)]

    @api.depends('name', 'subject')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s' % (rec.name or '/', rec.subject or '')

    # ------------------------------------------------------- danh tính (sudo)

    def _as_system(self):
        """Recordset chạy dưới OdooBot — dùng cho MỌI ghi do NGƯỜI GỬI kích hoạt.

        ⚠️ Odoo 19: .sudo() chỉ bật cờ su, **env.uid không đổi** ⇒ create_uid /
        write_uid vẫn là nhân viên. Với đơn ẩn danh, một dòng write_uid = NV là
        đủ để suy ra ai gửi. Vì vậy lớp L2 (§4.2) phải là with_user(SUPERUSER_ID),
        không phải .sudo().

        Ngược lại, ghi do NGƯỜI XỬ LÝ kích hoạt vẫn dùng .sudo() để write_uid
        giữ được vết audit của handler (danh tính handler không cần bí mật).
        """
        return self.with_user(SUPERUSER_ID)

    def _sender_row(self):
        """Dòng danh tính người gửi. LUÔN sudo — bảng này không cấp ACL."""
        self.ensure_one()
        return self.env['hocba.hr.request.sender'].sudo().search(
            [('request_id', '=', self.id)], limit=1)

    def _is_sender(self):
        self.ensure_one()
        row = self._sender_row()
        return bool(row) and row.user_id.id == self.env.user.id

    def _can_handle(self):
        """User hiện tại có nằm trong phạm vi xử lý đơn này không."""
        self.ensure_one()
        scope = _svc_scope(self.env)
        if not scope['canHandle']:
            return False
        return bool(self.sudo().filtered_domain(_inbox_domain(scope)))

    # ------------------------------------------------- thông báo (SPEC §8.1)

    def _notif_sender_label(self):
        """Nhãn người gửi dùng TRONG NỘI DUNG THÔNG BÁO — cổng duy nhất.

        BR-SVC-11: title/body của đơn ẩn danh chỉ được chứa mã đơn + loại +
        tiêu đề. Mọi producer bắt buộc lấy tên người gửi qua đây, không đọc
        thẳng _sender_row().employee_id.name — quên một chỗ là rò một chỗ.
        """
        self.ensure_one()
        if self.sudo().is_anonymous:
            return ANON_LABEL
        return self._sender_row().employee_id.name or ANON_LABEL

    def _notif_ref(self):
        """Dòng nhận diện đơn, an toàn cho cả đơn ẩn danh."""
        self.ensure_one()
        rec = self.sudo()
        return '%s — %s (%s)' % (rec.name, rec.subject, rec.type_id.name)

    def _svc_notify(self, users, kind, level, title, body,
                    tab='mine', dedup_key=None):
        """Bắn hb.notification cho màn 'service'.

        ⚠️ with_user(SUPERUSER_ID) chứ không .sudo(): ir.rule của hb.notification
        cho người nhận đọc dòng của CHÍNH MÌNH ⇒ người xử lý đọc được cả
        create_uid của dòng đó. Với đơn ẩn danh, create_uid = NV là lộ danh tính
        y hệt lớp L2 trên bản ghi đơn (.sudo() không đổi env.uid — §10.1b).
        """
        self.ensure_one()
        if not users:
            return self.env['hb.notification']
        return self.env['hb.notification'].with_user(SUPERUSER_ID)._notify(
            users, category='service', kind=kind, level=level,
            title=title, body=body, target_view='service',
            target_ref=self.id, target_tab=tab, dedup_key=dedup_key)

    def _notif_handlers(self):
        """Người dùng có đơn này trong hộp thư — bám đúng _inbox_domain().

        Người gửi bị loại: HR tự gửi đơn cho HR thì không tự rung chuông mình.
        Ghi nhận lệch có chủ ý: user chỉ có base.group_system (không có group
        HR) vẫn ĐỌC được hộp thư nhưng không nhận chuông — sysadmin không phải
        người xử lý nghiệp vụ, ping họ mọi đơn là nhiễu.
        """
        self.ensure_one()
        rec = self.sudo()
        Users = self.env['res.users'].sudo()
        users = Users.browse()
        if rec.recipient_scope in ('hr', 'both'):
            grp = self.env.ref('hr.group_hr_user', raise_if_not_found=False)
            if grp:
                users |= Users.search([('all_group_ids', 'in', grp.id),
                                       ('active', '=', True)])
        if (rec.recipient_scope in ('manager', 'both')
                and not rec.type_id.force_hr_only):          # BR-SVC-01/10
            mgr_user = rec.target_department_id.manager_id.sudo().user_id
            if mgr_user:
                users |= mgr_user
        sender_user = self._sender_row().user_id
        if sender_user:
            users -= sender_user
        return users

    def _notif_sender_user(self):
        self.ensure_one()
        return self._sender_row().user_id

    # -------------------------------------------------------------- gửi đơn

    @api.model
    def _dept_headcount(self, dept):
        """Số NV đang làm việc của phòng (gồm phòng con) — cỡ "tập nghi vấn"
        của một đơn ẩn danh gửi trưởng phòng."""
        if not dept:
            return 0
        Dept = self.env['hr.department'].sudo()
        ids, frontier = {dept.id}, dept
        while frontier:
            children = Dept.search([('parent_id', 'in', frontier.ids)])
            frontier = children.filtered(lambda d: d.id not in ids)
            ids.update(frontier.ids)
        return self.env['hr.employee'].sudo().search_count([
            ('department_id', 'in', list(ids)),
            ('active', '=', True),
            ('x_employment_status', '!=', 'resigned'),
        ])

    @api.model
    def _anon_count_today(self):
        """Số đơn ẩn danh user hiện tại đã gửi trong NGÀY (theo tz của user)."""
        req_ids = _my_request_ids(self.env)
        if not req_ids:
            return 0
        reqs = self.sudo().search(
            [('id', 'in', req_ids), ('is_anonymous', '=', True)])
        today = fields.Date.context_today(self.env.user)
        return len(reqs.filtered(
            lambda r: r.create_date and fields.Datetime.context_timestamp(
                r, r.create_date).date() == today))

    @api.model
    def create_request(self, vals):
        """Tạo đơn từ phía người gửi — CHỐT toàn bộ BR gửi đơn.

        Đặt ở model (không ở controller) để P1 test được nghiệp vụ khi chưa có
        API; controller P2 chỉ parse JSON rồi gọi hàm này.
        """
        env = self.env
        user = env.user
        emp = user.sudo().employee_id
        if not emp:
            raise SvcError('no_employee', _(
                'Tài khoản chưa gắn hồ sơ nhân viên nên không gửi được đơn.'))

        req_type = env['hocba.hr.request.type'].sudo().browse(
            vals.get('type_id') or 0)
        if not req_type.exists() or not req_type.active:
            raise SvcError('type_invalid', _('Loại yêu cầu không hợp lệ.'))

        is_anonymous = bool(vals.get('is_anonymous'))
        if is_anonymous and not req_type.allow_anonymous:
            raise SvcError('anon_not_allowed', _(
                'Loại "%s" không cho gửi ẩn danh.', req_type.name))

        # --- Người nhận + phòng đích -------------------------------------
        scope = vals.get('recipient_scope') or req_type.default_recipient
        if req_type.force_hr_only:
            scope = 'hr'                                        # BR-SVC-01
        if scope not in dict(RECIPIENT_SEL):
            raise SvcError('scope_invalid', _('Người nhận không hợp lệ.'))

        Dept = env['hr.department'].sudo()
        dept = Dept.browse(vals['target_department_id']) \
            if vals.get('target_department_id') else emp.sudo().department_id
        if scope in ('manager', 'both'):
            if not dept or not dept.exists():
                raise SvcError('dept_required', _(
                    'Gửi trưởng phòng thì phải xác định được phòng đích.'))
            # Phòng chưa có TP thì _inbox_domain() không khớp hộp thư nào ⇒ đơn
            # mồ côi, không ai đọc. Chặn thẳng (kể cả scope 'both': im lặng hạ
            # về HR là đổi người đọc đơn sau lưng người gửi).
            if not dept.manager_id:
                raise SvcError('dept_no_manager', _(
                    'Phòng "%s" chưa có trưởng phòng nên không gửi được cho '
                    'trưởng phòng. Hãy gửi cho HR.', dept.name))
            # BR-SVC-04: người gửi chính là TP của phòng đích → chuyển về HR,
            # không ai tự gửi đơn cho chính mình xử lý.
            if dept.manager_id.id == emp.id:
                scope = 'hr'
        if scope == 'hr':
            dept = Dept.browse()

        # --- Luật ẩn danh (BR-SVC-02/03/12, SPEC §2.2.1) ------------------
        if is_anonymous:
            if scope == 'both':
                raise SvcError('anon_scope_both', _(
                    'Đơn ẩn danh phải chọn MỘT người nhận (HR hoặc Trưởng '
                    'phòng) — gửi cả hai sẽ để HR suy ra phòng ban của bạn.'))
            if scope == 'manager':
                min_size = _param_int(
                    env, PARAM_MIN_ANON_DEPT, DEFAULT_MIN_ANON_DEPT)
                if self._dept_headcount(dept) < min_size:
                    raise SvcError('anon_dept_too_small', _(
                        'Phòng "%(dept)s" có ít hơn %(n)s nhân viên nên gửi ẩn '
                        'danh cho trưởng phòng sẽ dễ bị suy ra bạn là ai. '
                        'Hãy gửi cho HR.',
                        dept=dept.name, n=min_size))
            limit = _param_int(env, PARAM_ANON_DAILY, DEFAULT_ANON_DAILY)
            if self._anon_count_today() >= limit:
                raise SvcError('anon_daily_limit', _(
                    'Bạn đã gửi %s đơn ẩn danh hôm nay — hãy gửi tiếp vào '
                    'ngày mai.', limit))

        # --- Đính kèm ------------------------------------------------------
        attachment_ids = list(vals.get('attachment_ids') or [])
        if attachment_ids and (is_anonymous or not req_type.allow_attachment):
            raise SvcError('attachment_not_allowed', _(
                'Đơn này không cho đính kèm tệp'
                + (' vì tệp đính kèm sẽ làm lộ người gửi ẩn danh.'
                   if is_anonymous else '.')))

        # --- Điểm đánh giá -------------------------------------------------
        rating = vals.get('rating')
        if rating and not req_type.has_rating:
            raise SvcError('rating_not_allowed', _(
                'Loại "%s" không có phần chấm điểm.', req_type.name))

        subject = (vals.get('subject') or '').strip()
        body = (vals.get('body') or '').strip()
        if not subject or not body:
            raise SvcError('content_required', _(
                'Tiêu đề và nội dung không được để trống.'))

        # with_user(SUPERUSER_ID): (a) NV thường không có ACL trên model này,
        # (b) để create_uid = OdooBot chứ không phải NV — lớp L2 (§4.2). Dùng
        # .sudo() ở đây là SAI: env.uid không đổi nên create_uid vẫn là NV.
        create_vals = {
            'name': env['ir.sequence'].sudo().next_by_code(
                'hocba.hr.request') or '/',
            'type_id': req_type.id,
            'subject': subject,
            'body': body,
            'recipient_scope': scope,
            'target_department_id': dept.id if dept else False,
            'is_anonymous': is_anonymous,
            'rating': rating or False,
            'priority': vals.get('priority') or 'normal',
        }
        if attachment_ids:
            create_vals['attachment_ids'] = [(6, 0, attachment_ids)]
        req = self.with_user(SUPERUSER_ID).create(create_vals)
        env['hocba.hr.request.sender'].with_user(SUPERUSER_ID).create({
            'request_id': req.id,
            'employee_id': emp.id,
            'user_id': user.id,
            'department_id': emp.sudo().department_id.id or False,
        })
        # Trả về recordset của CHÍNH user gửi (uid gốc + su) để _is_sender() /
        # serialize() phía sau xác định đúng vai trò — không trả recordset
        # OdooBot ra ngoài.
        out = self.sudo().browse(req.id)
        out._svc_notify(
            out._notif_handlers(), 'service_new', 'info',
            title=_('Yêu cầu dịch vụ mới'),
            body='%s · %s' % (out._notif_ref(), out._notif_sender_label()),
            tab='inbox')
        return out

    # ------------------------------------------------------- hội thoại

    def post_message(self, body, is_internal=False):
        """Gửi 1 tin nhắn lên đơn. Tự suy vai trò người viết theo phạm vi."""
        self.ensure_one()
        text = (body or '').strip()
        if not text:
            raise SvcError('content_required', _('Nội dung không được để trống.'))
        if self.sudo().state in ('closed', 'cancelled'):
            raise SvcError('bad_state', _('Đơn đã kết thúc, không gửi thêm được.'))

        if self._is_sender():
            role, internal = 'sender', False    # BR-SVC-07: NV không ghi nội bộ
        elif self._can_handle():
            role, internal = 'handler', bool(is_internal)
        else:
            raise AccessError(_('Bạn không có quyền trên đơn này.'))

        # SUPERUSER_ID chứ không .sudo(): create_uid của message người gửi cũng
        # là một đường rò danh tính (author_id đã lưu tường minh cho audit).
        msg = self.env['hocba.hr.request.message'].with_user(SUPERUSER_ID).create({
            'request_id': self.id,
            'author_role': role,
            'author_id': self.env.user.id,
            'body': text,
            'is_internal': internal,
        })
        # BR-SVC-06: người gửi trả lời tiếp đơn đã trả lời → mở lại hội thoại.
        # Ghi do người gửi kích hoạt ⇒ phải là SUPERUSER, nếu không write_uid
        # trên đơn ẩn danh sẽ chỉ đúng người gửi.
        if role == 'sender' and self.sudo().state == 'answered':
            self._as_system().write({'state': 'in_progress'})

        # BR-SVC-07: ghi chú nội bộ người gửi không đọc được ⇒ tuyệt đối không
        # rung chuông họ (tiêu đề thông báo cũng là nội dung bị rò).
        if not internal:
            if role == 'handler':
                self._svc_notify(
                    self._notif_sender_user(), 'service_reply', 'info',
                    title=_('Trả lời mới cho yêu cầu của bạn'),
                    body=self._notif_ref(), tab='mine')
            else:
                # Đơn đã có người nhận → chỉ báo người đó; chưa ai nhận → báo
                # cả hộp thư, nếu không phản hồi nằm im tới khi có người mở.
                targets = self.sudo().handler_id or self._notif_handlers()
                self._svc_notify(
                    targets, 'service_reply', 'info',
                    title=_('Người gửi vừa phản hồi'),
                    body='%s · %s' % (self._notif_ref(),
                                      self._notif_sender_label()),
                    tab='inbox')
        return msg

    # ------------------------------------------------------ vòng đời

    def _ensure_handler(self):
        """Chỉ người đã nhận đơn (hoặc HR Manager) mới chốt được đơn —
        BR-SVC-05, tránh 2 người xử lý chồng lên nhau."""
        self.ensure_one()
        if not self._can_handle():
            raise AccessError(_('Bạn không có quyền trên đơn này.'))
        scope = _svc_scope(self.env)
        handler = self.sudo().handler_id
        if handler and handler.id != self.env.user.id and not scope['isHrManager']:
            raise AccessError(_(
                'Đơn này do %s đang xử lý.', handler.name))

    def action_claim(self):
        for rec in self:
            if not rec._can_handle():
                raise AccessError(_('Bạn không có quyền trên đơn này.'))
            if rec.sudo().state != 'new':
                raise SvcError('bad_state', _('Đơn không còn ở trạng thái Mới.'))
            rec.sudo().write({
                'state': 'in_progress',
                'handler_id': rec.env.user.id,
                'claimed_at': fields.Datetime.now(),
            })
            rec._svc_notify(
                rec._notif_sender_user(), 'service_claimed', 'info',
                title=_('Yêu cầu của bạn đã có người xử lý'),
                body='%s · %s' % (rec._notif_ref(), rec.env.user.name),
                tab='mine')
        return True

    def action_answer(self):
        for rec in self:
            rec._ensure_handler()
            if rec.sudo().state != 'in_progress':
                raise SvcError('bad_state', _(
                    'Chỉ đơn đang xử lý mới chuyển sang Đã trả lời.'))
            replies = rec.sudo().message_ids.filtered(
                lambda m: m.author_role == 'handler' and not m.is_internal)
            if not replies:
                raise SvcError('no_handler_reply', _(
                    'Phải trả lời người gửi ít nhất 1 lần trước khi chốt '
                    '"Đã trả lời" (ghi chú nội bộ không tính).'))
            rec.sudo().write({
                'state': 'answered',
                'answered_at': fields.Datetime.now(),
            })
            rec._svc_notify(
                rec._notif_sender_user(), 'service_answered', 'success',
                title=_('Yêu cầu của bạn đã được trả lời'),
                body=rec._notif_ref(), tab='mine')
        return True

    def action_close(self, reason=None):
        for rec in self:
            if rec.sudo().state not in ('new', 'in_progress', 'answered'):
                raise SvcError('bad_state', _('Đơn đã kết thúc.'))
            by_sender = rec._is_sender()
            if not by_sender:
                rec._ensure_handler()
            vals = {
                'state': 'closed',
                'closed_at': fields.Datetime.now(),
                'closed_reason': (reason or '').strip() or False,
            }
            handler = rec.sudo().handler_id
            # Người gửi đóng đơn ⇒ ghi dưới OdooBot để write_uid không lộ họ.
            (rec._as_system() if by_sender else rec.sudo()).write(vals)
            # Báo BÊN CÒN LẠI: người gửi tự đóng thì báo người đang xử lý để họ
            # dừng việc, không báo ngược lại chính người vừa bấm.
            if by_sender:
                rec._svc_notify(
                    handler, 'service_closed', 'info',
                    title=_('Người gửi đã đóng yêu cầu'),
                    body='%s · %s' % (rec._notif_ref(),
                                      rec._notif_sender_label()),
                    tab='inbox')
            else:
                rec._svc_notify(
                    rec._notif_sender_user(), 'service_closed', 'info',
                    title=_('Yêu cầu của bạn đã đóng'),
                    body=rec._notif_ref(), tab='mine')
        return True

    def action_cancel(self):
        for rec in self:
            if not rec._is_sender():
                raise AccessError(_('Chỉ người gửi mới rút được đơn.'))
            if rec.sudo().state != 'new':
                raise SvcError('bad_state', _(
                    'Đơn đã có người xử lý nên không rút được nữa.'))
            rec._as_system().write({'state': 'cancelled'})
        return True

    # ------------------------------------------------------------- cron

    @api.model
    def _cron_overdue_reminder(self):
        """CRON-SVC-001 — nhắc đơn quá hạn SLA, chạy hằng ngày (SPEC §8.2).

        dedup_key='svc_overdue_<id>': _notify bỏ qua khi người nhận còn một
        dòng CHƯA ĐỌC cùng khoá ⇒ chạy 30 ngày liền vẫn 1 dòng, đọc rồi mà
        chưa xử lý thì hôm sau nhắc lại.
        """
        overdue = self.sudo().search([
            ('state', 'in', OPEN_STATES),
            ('deadline', '<', fields.Datetime.now()),
        ])
        sent = 0
        for rec in overdue:
            # Đã có người nhận → chỉ nhắc người đó; chưa ai nhận → nhắc cả hộp
            # thư, không thì đơn mồ côi không ai thấy là mình phải làm.
            targets = rec.handler_id or rec._notif_handlers()
            sent += len(rec._svc_notify(
                targets, 'service_overdue', 'warning',
                title=_('Yêu cầu dịch vụ quá hạn xử lý'),
                body='%s · %s · hạn %s' % (
                    rec._notif_ref(), rec._notif_sender_label(),
                    fields.Datetime.context_timestamp(
                        rec, rec.deadline).strftime('%d/%m/%Y')),
                tab='inbox', dedup_key='svc_overdue_%s' % rec.id))
        _logger.info('CRON-SVC-001: %d đơn quá hạn, gửi %d thông báo.',
                     len(overdue), sent)
        return True

    # ------------------------------------------------------- serializer

    def _serialize_message(self, msg, viewer_is_sender, is_anonymous):
        """Tên người viết theo BR-SVC-08: tin của người gửi trên đơn ẩn danh
        không bao giờ trả tên ra, kể cả khi chính người gửi xem (để payload
        người gửi và người xử lý không lệch nhau về mặt danh tính)."""
        if msg.author_role == 'sender' and is_anonymous:
            author = _('Bạn (ẩn danh)') if viewer_is_sender else ANON_LABEL
        elif msg.author_role == 'sender':
            author = msg.sudo().author_id.name or ''
        else:
            author = msg.sudo().author_id.name or _('Hệ thống')
        return {
            'id': msg.id,
            'authorRole': msg.author_role,
            'authorName': author,
            'body': msg.body,
            'isInternal': msg.is_internal,
            'createdAt': fields.Datetime.to_string(msg.create_date),
        }

    def serialize(self, viewer_is_sender=None, with_messages=False):
        """CHỐT CUỐI chống rò danh tính (SPEC §4.2 lớp L3).

        MỌI route của P2 phải đi qua hàm này — 3 nơi tự dựng payload là chắc
        chắn có một nơi quên ẩn tên.
        """
        self.ensure_one()
        rec = self.sudo()
        if viewer_is_sender is None:
            viewer_is_sender = self._is_sender()
        anon = rec.is_anonymous

        if anon:
            sender_name = _('Bạn (ẩn danh)') if viewer_is_sender else ANON_LABEL
            dept_name = None            # không bao giờ trả phòng của đơn ẩn danh
        else:
            row = self._sender_row()
            sender_name = row.employee_id.name or ''
            dept_name = row.department_id.name or None

        data = {
            'id': rec.id,
            'name': rec.name,
            'typeId': rec.type_id.id,
            'typeName': rec.type_id.name,
            'subject': rec.subject,
            'body': rec.body,
            'recipientScope': rec.recipient_scope,
            'isAnonymous': anon,
            'senderName': sender_name,
            'departmentName': dept_name,
            'state': rec.state,
            'stateLabel': dict(self.STATE_SEL).get(rec.state, rec.state),
            'priority': rec.priority,
            'rating': rec.rating or None,
            'handlerName': rec.handler_id.name or None,
            'deadline': fields.Datetime.to_string(rec.deadline),
            'isOverdue': rec.is_overdue,
            'createdAt': fields.Datetime.to_string(rec.create_date),
            'answeredAt': fields.Datetime.to_string(rec.answered_at),
            'closedAt': fields.Datetime.to_string(rec.closed_at),
            'closedReason': rec.closed_reason or None,
            'canReply': rec.state not in ('closed', 'cancelled'),
            # Đơn ẩn danh không bao giờ có đính kèm (BR-SVC-02) nên danh sách
            # này luôn rỗng ở đó — không phải đường rò.
            'attachments': [{
                'id': a.id,
                'name': a.name or 'tep',
                'mimetype': a.mimetype or '',
                'url': '/hocba-hrm/api/service/attachment/%d' % a.id,
            } for a in rec.attachment_ids],
        }
        if with_messages:
            msgs = rec.message_ids
            if viewer_is_sender:
                msgs = msgs.filtered(lambda m: not m.is_internal)  # BR-SVC-07
            data['messages'] = [
                self._serialize_message(m, viewer_is_sender, anon) for m in msgs]
        return data
