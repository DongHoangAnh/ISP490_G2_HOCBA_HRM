import re
import unicodedata

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

ROLE_GROUP_SEL = [
    ('teacher', 'Giảng viên'),
    ('office', 'Nhân viên văn phòng'),
]

# Thang điểm mỗi câu hỏi: HR chọn trong khoảng này (màn Cấu hình đánh giá).
MAX_SCORE_MIN = 1
MAX_SCORE_MAX = 10

# Trường HR được sửa từ màn Cấu hình đánh giá. Không có 'code' và
# 'role_group': mã do hệ thống sinh, nhóm do tab đang mở quyết định.
CONFIG_FIELDS = (
    'name', 'weight', 'max_score', 'auto_source', 'guideline',
    'anchor_top', 'anchor_mid', 'anchor_low', 'active',
)

# Nguồn dữ liệu tự chấm. Công thức từng nguồn: docs/CONG_THUC_DANH_GIA.md §4.
AUTO_SOURCE_SEL = [
    ('none', 'Chấm tay'),
    ('punctuality', 'Tự động — chuyên cần & đúng giờ'),
    ('workload', 'Tự động — khối lượng giảng dạy'),
    ('cert', 'Tự động — chuẩn chứng chỉ'),
]

# Thang mô tả hành vi (BARS) cho các tiêu chí CHẤM TAY: {code: (cao, giữa, thấp)}.
# Người chấm neo vào 3 mốc này, mức 4 và 2 là khoảng giữa hai mốc liền kề — nhờ
# vậy hai quản lý khác nhau chấm cùng một nhân viên ra kết quả gần nhau.
# Tiêu chí tự động không cần mốc: thang của chúng là bảng quy đổi ở
# docs/CONG_THUC_DANH_GIA.md §4.
DEFAULT_ANCHORS = {
    # ---------------- Giảng viên ----------------
    't_quality': (
        'Giáo án luôn chuẩn bị trước, bài giảng bám mục tiêu buổi học; học viên '
        'phản hồi tốt và kết quả kiểm tra của lớp cao hơn mặt bằng; đồng nghiệp '
        'dự giờ để học hỏi cách dạy.',
        'Dạy đủ nội dung theo giáo trình, tiến độ bám khung chương trình; phản '
        'hồi học viên bình thường, không có khiếu nại đáng kể; kết quả lớp ngang '
        'mặt bằng chung.',
        'Thường xuyên không chuẩn bị giáo án, cháy giờ hoặc hụt nội dung; có '
        'khiếu nại lặp lại về cách truyền đạt; kết quả lớp thấp rõ so với mặt bằng.'),
    't_class': (
        'Sĩ số lớp giữ ổn định tới cuối khoá; chủ động phát hiện và kèm học viên '
        'yếu trước khi phụ huynh phản ánh; xử lý gọn tình huống trong lớp, phản '
        'hồi phụ huynh/học viên trong ngày.',
        'Nắm được tình hình lớp và trả lời khi được hỏi; tỷ lệ nghỉ/bỏ học ở mức '
        'bình thường; tình huống phát sinh có báo giáo vụ cùng xử lý.',
        'Không nắm sĩ số và học viên yếu; để phụ huynh phản ánh vượt cấp; tình '
        'huống trong lớp bỏ mặc hoặc xử lý làm căng thêm.'),
    't_teamwork': (
        'Báo cáo và nhập điểm đúng hạn không cần nhắc; chủ động nhận dạy thay khi '
        'trung tâm cần; đóng góp chuyên môn trong họp và chia sẻ tài liệu cho '
        'đồng nghiệp.',
        'Nộp báo cáo/điểm đúng hạn, thỉnh thoảng trễ ít và sửa ngay khi được '
        'nhắc; nhận dạy thay khi được phân công; dự họp đầy đủ.',
        'Thường xuyên trễ báo cáo/điểm dù đã nhắc nhiều lần; từ chối hỗ trợ khi '
        'trung tâm cần; vắng họp chuyên môn không lý do.'),
    # ---------------- Nhân viên văn phòng ----------------
    'o_result': (
        'Hoàn thành vượt mục tiêu thống nhất đầu kỳ, chất lượng không phải làm '
        'lại; còn gánh thêm phần việc ngoài phạm vi mà vẫn giữ được tiến độ.',
        'Hoàn thành đúng và đủ các mục tiêu chính, tiến độ cơ bản đúng hạn; có '
        'vài việc phải chỉnh sửa nhưng không ảnh hưởng bộ phận khác.',
        'Không hoàn thành phần lớn mục tiêu; công việc thường xuyên trễ hạn hoặc '
        'phải người khác làm lại.'),
    'o_attitude': (
        'Chủ động nhận việc khó và theo tới cùng; tự nhận lỗi và sửa ngay; tuân '
        'thủ nội quy ở mức làm chuẩn cho người mới nhìn vào.',
        'Làm đúng phần việc được giao, tuân thủ nội quy; gặp vướng thì báo cáo '
        'đúng lúc chứ không giấu.',
        'Né việc hoặc đùn đẩy trách nhiệm khi có sự cố; vi phạm nội quy lặp lại '
        'sau khi đã được nhắc.'),
    'o_teamwork': (
        'Chủ động hỗ trợ đồng nghiệp và bộ phận khác; bàn giao rõ tới mức người '
        'nhận không phải hỏi lại; giúp gỡ vướng giữa các bộ phận.',
        'Phối hợp khi được đề nghị; trao đổi đủ thông tin để việc chung chạy được.',
        'Giữ thông tin cho riêng mình hoặc bàn giao thiếu khiến bộ phận khác phải '
        'chờ; gây căng thẳng lặp lại khi làm việc nhóm.'),
    'o_initiative': (
        'Đề xuất được ít nhất một cải tiến áp dụng thật trong kỳ và thấy được '
        'kết quả; tự học nghiệp vụ mới rồi hướng dẫn lại đồng nghiệp.',
        'Có góp ý cải tiến khi được hỏi; tự xử lý được vấn đề quen thuộc mà không '
        'cần nhắc.',
        'Chỉ làm khi được giao từng bước; gặp vấn đề thì dừng chờ chỉ đạo dù đã '
        'có quy trình sẵn.'),
    'o_potential': (
        'Đã làm thử phần việc của vị trí cao hơn và làm được; sẵn sàng nhận vai '
        'trò lớn hơn trong 6 tháng tới.',
        'Vững vị trí hiện tại, cần bổ sung 1–2 kỹ năng nữa để lên vai trò cao hơn '
        'trong 12 tháng.',
        'Chưa vững việc hiện tại nên chưa đặt được vấn đề phát triển lên vai trò '
        'khác.'),
}


def seed_default_anchors(env):
    """Điền mô tả mức điểm mặc định cho tiêu chí còn TRỐNG.

    Chạy cả khi cài mới (post_init_hook) lẫn khi nâng cấp (migration). Chỉ ghi
    vào ô đang rỗng nên không đè lên nội dung HR đã sửa, và chạy lại nhiều lần
    không đổi kết quả.
    """
    Crit = env['hb.review.criteria'].sudo()
    filled = 0
    for code, (top, mid, low) in DEFAULT_ANCHORS.items():
        rec = Crit.with_context(active_test=False).search(
            [('code', '=', code)], limit=1)
        if not rec:
            continue
        vals = {}
        for field, text in (('anchor_top', top), ('anchor_mid', mid),
                            ('anchor_low', low)):
            if not rec[field]:
                vals[field] = text
        if vals:
            rec.write(vals)
            filled += 1
    return filled


class HbReviewCriteria(models.Model):
    """Tiêu chí đánh giá định kỳ, tách theo nhóm nhân sự.
    Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md"""
    _name = 'hb.review.criteria'
    _description = 'Tiêu chí đánh giá định kỳ'
    _order = 'role_group, sequence, id'

    name = fields.Char(string='Tiêu chí', required=True, translate=True)
    code = fields.Char(string='Mã', required=True)
    role_group = fields.Selection(
        ROLE_GROUP_SEL, string='Nhóm áp dụng', required=True, index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    weight = fields.Float(
        string='Trọng số (%)', required=True, default=10.0,
        help='Tổng trọng số của mỗi nhóm nên bằng 100.')
    max_score = fields.Integer(string='Điểm tối đa', default=5, required=True)
    auto_source = fields.Selection(
        AUTO_SOURCE_SEL, string='Nguồn chấm', default='none', required=True,
        help='Khác "Chấm tay" = hệ thống tính sẵn điểm đề xuất từ dữ liệu vận '
             'hành; quản lý vẫn sửa đè được.')
    guideline = fields.Text(string='Hướng dẫn chấm')
    # Ba mốc mô tả hành vi. Người chấm so nhân viên với mốc gần nhất rồi mới
    # chọn số; mức 4/2 là khoảng giữa. Bỏ trống với tiêu chí chấm tự động.
    anchor_top = fields.Text(
        string='Mốc điểm cao nhất',
        help='Hành vi quan sát được tương ứng với điểm tối đa.')
    anchor_mid = fields.Text(
        string='Mốc điểm giữa',
        help='Mức "đạt yêu cầu của vị trí" — chuẩn để so lên/xuống.')
    anchor_low = fields.Text(
        string='Mốc điểm thấp nhất',
        help='Hành vi tương ứng với 1 điểm — chưa đạt yêu cầu.')
    active = fields.Boolean(string='Hiệu lực', default=True)

    def anchor_levels(self):
        """[(điểm, mô tả)] của 3 mốc, tính theo thang riêng của tiêu chí.

        Thang 0–5 cho ra mốc 5/3/1. Thang khác vẫn ra 3 mốc cao/giữa/thấp đúng
        tỷ lệ, nên đổi max_score không làm hướng dẫn sai lệch.
        """
        self.ensure_one()
        mid = max(1, (self.max_score + 1) // 2)
        pairs = [(self.max_score, self.anchor_top), (mid, self.anchor_mid),
                 (1, self.anchor_low)]
        # Thang quá ngắn có thể làm 2 mốc trùng số điểm -> chỉ giữ mốc đầu.
        seen, out = set(), []
        for score, text in pairs:
            if not text or score in seen:
                continue
            seen.add(score)
            out.append((score, text))
        return out

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã tiêu chí phải duy nhất.',
    )

    @api.constrains('weight', 'max_score')
    def _check_ranges(self):
        for rec in self:
            if rec.weight < 0 or rec.weight > 100:
                raise ValidationError(_(
                    'Trọng số của "%s" phải trong khoảng 0–100.') % rec.name)
            if not MAX_SCORE_MIN <= rec.max_score <= MAX_SCORE_MAX:
                raise ValidationError(_(
                    'Điểm tối đa của "%(n)s" phải trong khoảng %(lo)s–%(hi)s.')
                    % {'n': rec.name, 'lo': MAX_SCORE_MIN, 'hi': MAX_SCORE_MAX})

    # ------------------------------------------------------------------
    # Màn Cấu hình đánh giá (HR sửa bộ câu hỏi)
    # Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md
    # ------------------------------------------------------------------
    @api.model
    def check_group_weight(self, role_group):
        """Tổng trọng số các câu hỏi ĐANG BẬT của nhóm phải bằng 100.

        Cố tình KHÔNG dùng @api.constrains: lúc cài module / nạp data XML các
        bản ghi vào từng cái một nên tổng chưa đủ 100, constraint sẽ làm hỏng
        install. Gọi method này sau khi đã áp cả lô trong cùng transaction.
        """
        total = sum(self.search(
            [('role_group', '=', role_group)]).mapped('weight'))
        if abs(total - 100.0) > 0.01:
            raise ValidationError(_(
                'Tổng trọng số nhóm "%(g)s" đang là %(t)s, phải bằng 100.') % {
                    'g': dict(ROLE_GROUP_SEL).get(role_group, role_group),
                    't': round(total, 2),
                })
        return True

    @api.model
    def _next_code(self, role_group, name):
        """Sinh mã duy nhất cho câu hỏi HR vừa thêm (HR không phải nhập mã)."""
        prefix = 't' if role_group == 'teacher' else 'o'
        ascii_name = unicodedata.normalize('NFD', name or '').encode(
            'ascii', 'ignore').decode()
        slug = re.sub(r'[^a-z0-9]+', '_', ascii_name.lower()).strip('_')[:16]
        base = '%s_%s' % (prefix, slug or 'q')
        Crit = self.with_context(active_test=False)
        code, i = base, 1
        while Crit.search_count([('code', '=', code)]):
            i += 1
            code = '%s_%s' % (base, i)
        return code

    @api.model
    def apply_group(self, role_group, rows):
        """Lưu CẢ BỘ câu hỏi của một nhóm trong một transaction.

        `rows` theo đúng thứ tự HR sắp trên màn hình; mỗi dòng có `id` (0 = câu
        hỏi mới) cùng các trường trong CONFIG_FIELDS. Câu hỏi không nằm trong
        payload thì giữ nguyên — payload thiếu không được phép âm thầm xoá bộ
        tiêu chí. Bỏ câu hỏi = gửi `active: False` (không xoá cứng, phiếu cũ
        còn phải tra được tên tiêu chí).
        """
        if role_group not in dict(ROLE_GROUP_SEL):
            raise ValidationError(_('Nhóm nhân sự không hợp lệ.'))
        Crit = self.with_context(active_test=False)
        sequence = 10
        for row in rows or []:
            vals = {k: row[k] for k in CONFIG_FIELDS if k in row}
            if 'name' in vals and not (vals['name'] or '').strip():
                raise ValidationError(_('Tên câu hỏi không được để trống.'))
            vals['sequence'] = sequence
            sequence += 10
            rec_id = int(row.get('id') or 0)
            if rec_id:
                rec = Crit.browse(rec_id)
                if not rec.exists() or rec.role_group != role_group:
                    raise ValidationError(_(
                        'Câu hỏi #%s không thuộc nhóm đang sửa.') % rec_id)
                rec.write(vals)
            else:
                vals['role_group'] = role_group
                vals.setdefault('name', _('Câu hỏi mới'))
                vals['code'] = self._next_code(role_group, vals['name'])
                Crit.create(vals)
        self.check_group_weight(role_group)
        return True
