"""JSON API màn Đánh giá nhân viên cho SPA Học Bá HRM.

Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
Công thức: docs/CONG_THUC_DANH_GIA.md
Quy ước: docs/QUY_UOC_FRONTEND.md (camelCase, ngày ISO, lỗi {error, message}).

Phân quyền (theo mô hình chung của hệ thống):
  - Admin / HR Manager / HR officer : mọi nhân viên, mọi thao tác.
  - Trưởng phòng : nhân viên phòng mình (gồm phòng con) — chấm & chốt.
  - Giáo vụ      : chỉ giáo viên.
  - Công bố kết quả : chỉ HR/Admin.
Kiểm phạm vi TRƯỚC rồi mới .sudo() (gotcha self-service của dự án).
"""
from odoo import fields, http, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from ..models.hb_performance_review import (
    GRADE_SEL, PERIOD_COUNT, PERIOD_MONTHS, PERIOD_TYPE_SEL,
)

# Diễn giải xếp loại cho tab Hướng dẫn (§2 docs/CONG_THUC_DANH_GIA.md).
GRADE_MEANING = {
    'a': 'Vượt mong đợi — xét thưởng, đề bạt, giao việc thử thách hơn.',
    'b': 'Hoàn thành tốt nhiệm vụ — duy trì, phát triển thêm thế mạnh.',
    'c': 'Hoàn thành ở mức đạt — chốt 1–2 điểm cải thiện cụ thể cho kỳ sau.',
    'd': 'Chưa đạt — lập kế hoạch cải thiện có mốc thời gian, tái đánh giá kỳ sau.',
}

# Quy đổi chuẩn chứng chỉ: mô tả đúng thứ tự if/elif của
# HbPerformanceReview._auto_score_for('cert'), gặp điều kiện đúng đầu tiên thì dừng.
CERT_RULES = [
    ('Không có chứng chỉ nào đã xác minh', 1, 'Chưa đạt chuẩn hồ sơ'),
    ('Có chứng chỉ đã hết hạn', 2, 'Phải gia hạn ngay'),
    ('Có chứng chỉ sắp hết hạn', 3, 'Nhắc giáo viên gia hạn'),
    ('Đúng 1 chứng chỉ còn hạn', 4, 'Đủ chuẩn tối thiểu'),
    ('Từ 2 chứng chỉ còn hạn trở lên', 5, 'Vượt chuẩn'),
]

# Ý nghĩa chung của từng mức trên thang chấm. Mức cao nhất / giữa / thấp nhất có
# mô tả hành vi riêng cho từng tiêu chí (anchor_*); hai mức xen giữa cố tình để
# trống mô tả vì chúng là "nằm giữa hai mốc", không phải một trạng thái riêng.
SCALE_MEANING = [
    ('top', 'Xuất sắc',
     'Vượt hẳn yêu cầu của vị trí, có việc cụ thể chứng minh được.'),
    ('between_high', 'Trên mong đợi',
     'Rõ ràng hơn mức đạt nhưng chưa tới mức xuất sắc — nằm giữa hai mốc.'),
    ('mid', 'Đạt yêu cầu',
     'Làm đúng những gì vị trí này cần. Đây là mốc chuẩn để so lên hoặc xuống.'),
    ('between_low', 'Dưới mong đợi',
     'Có thiếu sót thấy được nhưng chưa tới mức không đạt — nằm giữa hai mốc.'),
    ('low', 'Không đạt',
     'Chưa đáp ứng yêu cầu cơ bản, cần kế hoạch cải thiện có mốc thời gian.'),
    ('zero', 'Chưa chấm',
     'Không phải một mức đánh giá. Lưu ý: dòng để 0 vẫn được tính là 0 điểm '
     'trong công thức, nên đừng bỏ sót tiêu chí nào trước khi chốt.'),
]

# Điều kiện "đạt" của chỉ số đúng giờ, khác nhau giữa 2 nhóm (§4.1).
PUNCTUAL_RULE = {
    'teacher': {
        'unit': 'buổi dạy',
        'source': 'Chấm công theo buổi dạy (hocba.teaching.attendance)',
        'okWhen': 'Buổi được tính là đạt khi chấm công đúng cửa sổ giờ của buổi '
                  'học, đúng vị trí lớp và ảnh khuôn mặt không bị nghi ngờ.',
    },
    'office': {
        'unit': 'ngày công',
        'source': 'Chấm công theo ngày (hocba.attendance)',
        'okWhen': 'Ngày công được tính là đạt khi không đi trễ phút nào và '
                  'không về sớm phút nào.',
    },
}


def _d(v):
    return v.isoformat() if v else None


def _anchors(criteria):
    """3 mốc hành vi của tiêu chí, dạng [{score, text}] — rỗng nếu chấm tự động."""
    return [{'score': score, 'text': text}
            for score, text in criteria.anchor_levels()]


def _scale_rows(max_score):
    """Thang chấm của một tiêu chí kèm ý nghĩa từng mức.

    Mốc cao/giữa/thấp bám theo anchor_levels(); hai mức xen giữa chỉ xuất hiện
    khi thang đủ rộng để có chỗ cho chúng (thang 0–5 -> 4 và 2)."""
    mid = max(1, (max_score + 1) // 2)
    numbers = {
        'top': max_score,
        'between_high': (max_score + mid) // 2 if max_score - mid > 1 else None,
        'mid': mid,
        'between_low': (mid + 1) // 2 if mid - 1 > 1 else None,
        'low': 1 if max_score > 1 else None,
        'zero': 0,
    }
    return [{'key': key, 'score': numbers[key], 'label': label, 'desc': desc}
            for key, label, desc in SCALE_MEANING
            if numbers.get(key) is not None]


def _err(code, message=None, status=400):
    body = {'error': code}
    if message:
        body['message'] = message
    return request.make_json_response(body, status=status)


class HocBaReviews(http.Controller):

    # ------------------------------------------------------------------
    # Phân quyền
    # ------------------------------------------------------------------
    def _is_hr(self):
        u = request.env.user
        return (u.has_group('base.group_system')
                or u.has_group('hr.group_hr_manager')
                or u.has_group('hr.group_hr_user'))

    def _can_publish(self):
        u = request.env.user
        return (u.has_group('base.group_system')
                or u.has_group('hr.group_hr_manager'))

    def _is_giaovu(self):
        return request.env.user.has_group(
            'hocba_employees.group_hocba_giaovu')

    def _managed_department_ids(self):
        emp = request.env.user.employee_id
        if not emp:
            return []
        Dept = request.env['hr.department'].sudo()
        managed = Dept.search([('manager_id', '=', emp.id)])
        if not managed:
            return []
        result, frontier = set(managed.ids), managed
        while frontier:
            children = Dept.search([('parent_id', 'in', frontier.ids)])
            frontier = children.filtered(lambda d: d.id not in result)
            result.update(frontier.ids)
        return list(result)

    def _can_manage(self):
        return bool(self._is_hr() or self._is_giaovu()
                    or self._managed_department_ids())

    def _employee_domain(self):
        """Domain giới hạn nhân viên user được đánh giá.
        None = không có quyền; [] = toàn bộ."""
        if not self._can_manage():
            return None
        if self._is_hr():
            return []
        dom = []
        if self._is_giaovu():
            dom.append(('x_employee_type_id.code', '=', 'teacher'))
        depts = self._managed_department_ids()
        if depts and not self._is_giaovu():
            dom.append(('department_id', 'in', depts))
        return dom

    def _emp_in_scope(self, employee):
        dom = self._employee_domain()
        if dom is None:
            return False
        if not dom:
            return True
        return bool(request.env['hr.employee'].sudo().search_count(
            [('id', '=', employee.id)] + dom))

    # ------------------------------------------------------------------
    # Serialize
    # ------------------------------------------------------------------
    def _metrics(self, r):
        return {
            'totalUnits': r.metric_total_units,
            'okUnits': r.metric_ok_units,
            'punctualPct': round(r.metric_punctual_pct, 1),
            'lateCount': r.metric_late_count,
            'leaveDays': r.metric_leave_days,
            'certValid': r.metric_cert_valid,
            'certExpiring': r.metric_cert_expiring,
            'certExpired': r.metric_cert_expired,
            'computedOn': _d(r.metrics_computed_on),
        }

    def _review_row(self, r):
        """Dòng tóm tắt cho bảng danh sách."""
        e = r.employee_id
        return {
            'id': r.id,
            'empId': e.id,
            'empName': e.name,
            'empCode': e.x_employee_code or '',
            'department': e.department_id.name or '',
            'jobTitle': e.job_title or '',
            'roleGroup': r.role_group,
            'periodLabel': r.period_label,
            'totalScore': round(r.total_score, 1),
            'grade': r.grade or '',
            'state': r.state,
            'punctualPct': round(r.metric_punctual_pct, 1),
            'totalUnits': r.metric_total_units,
        }

    def _review_detail(self, r):
        d = self._review_row(r)
        d.update({
            'periodType': r.period_type,
            'periodYear': r.period_year,
            'periodIndex': r.period_index,
            'dateFrom': _d(r.date_from),
            'dateTo': _d(r.date_to),
            'selfNote': r.self_note or '',
            'managerNote': r.manager_note or '',
            'hrNote': r.hr_note or '',
            'evaluator': r.evaluator_id.name or '',
            'confirmedOn': _d(r.confirmed_on),
            'publishedOn': _d(r.published_on),
            'metrics': self._metrics(r),
            'canPublish': self._can_publish(),
            'lines': [{
                'id': l.id,
                'criteriaId': l.criteria_id.id,
                'name': l.criteria_id.name,
                'code': l.criteria_id.code,
                'guideline': l.criteria_id.guideline or '',
                # Mốc hành vi để người chấm đối chiếu ngay lúc bấm điểm.
                'anchors': _anchors(l.criteria_id),
                'weight': l.weight,
                'maxScore': l.max_score,
                'score': l.score,
                'autoScore': l.auto_score,
                'isAuto': l.is_auto,
                'autoSource': l.criteria_id.auto_source,
                'manualOverride': l.manual_override,
                'note': l.note or '',
            } for l in r.line_ids.sorted(lambda x: (x.sequence, x.id))],
        })
        return d

    # ------------------------------------------------------------------
    # GET danh sách theo nhóm + kỳ
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews', auth='user', type='http',
                methods=['GET'])
    def api_reviews(self, group='teacher', periodType='quarter',
                    year=None, index=None, **kw):
        emp_dom = self._employee_domain()
        if emp_dom is None:
            return _err('forbidden', status=403)
        env = request.env
        group = 'teacher' if group == 'teacher' else 'office'
        try:
            year = int(year) if year else fields.Date.today().year
            index = int(index) if index else 1
        except (TypeError, ValueError):
            return _err('bad_request', 'Kỳ đánh giá không hợp lệ.')

        dom = list(emp_dom) + [('active', '=', True)] \
            + env['hb.performance.review'].role_group_domain(group)
        employees = env['hr.employee'].sudo().search(dom, order='name')

        reviews = env['hb.performance.review'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('period_type', '=', periodType),
            ('period_year', '=', year),
            ('period_index', '=', index),
        ])
        by_emp = {r.employee_id.id: r for r in reviews}

        rows = []
        for e in employees:
            r = by_emp.get(e.id)
            if r:
                rows.append(self._review_row(r))
            else:
                rows.append({
                    'id': 0, 'empId': e.id, 'empName': e.name,
                    'empCode': e.x_employee_code or '',
                    'department': e.department_id.name or '',
                    'jobTitle': e.job_title or '',
                    'roleGroup': group, 'periodLabel': '', 'totalScore': 0,
                    'grade': '', 'state': 'none', 'punctualPct': 0,
                    'totalUnits': 0,
                })

        done = [r for r in rows if r['state'] in ('confirmed', 'published')]
        avg = round(sum(r['totalScore'] for r in done) / len(done), 1) \
            if done else 0
        criteria = env['hb.review.criteria'].sudo().search(
            [('role_group', '=', group)], order='sequence, id')
        return request.make_json_response({
            'canManage': True,
            'canPublish': self._can_publish(),
            'group': group,
            'periodType': periodType,
            'year': year,
            'index': index,
            'rows': rows,
            'criteria': [{
                'id': c.id, 'name': c.name, 'code': c.code,
                'weight': c.weight, 'maxScore': c.max_score,
                'autoSource': c.auto_source, 'guideline': c.guideline or '',
            } for c in criteria],
            'stats': {
                'employees': len(rows),
                'done': len(done),
                'pending': len(rows) - len(done),
                'avgScore': avg,
                # Đủ 4 bậc để SPA vẽ phân bố xếp loại (A/B/C/D), chỉ đếm trên
                # phiếu ĐÃ chấm — người chưa có phiếu không thuộc bậc nào.
                'gradeA': len([r for r in done if r['grade'] == 'a']),
                'gradeB': len([r for r in done if r['grade'] == 'b']),
                'gradeC': len([r for r in done if r['grade'] == 'c']),
                'gradeD': len([r for r in done if r['grade'] == 'd']),
            },
        })

    # ------------------------------------------------------------------
    # GET tài liệu hướng dẫn chấm điểm (tab "Hướng dẫn chấm điểm")
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews/guide', auth='user', type='http',
                methods=['GET'])
    def api_review_guide(self, **kw):
        """Toàn bộ số liệu để dựng tab hướng dẫn: ngưỡng xếp loại, bộ tiêu chí,
        bảng quy đổi chỉ số tự động, tham số cấu hình.

        Đọc thẳng từ ir.config_parameter + hằng số của model thay vì chép lại
        trong frontend — HR sửa trọng số/ngưỡng thì hướng dẫn đổi theo, không
        bao giờ lệch với điểm hệ thống thực sự chấm.
        """
        if not self._can_manage():
            return _err('forbidden', status=403)
        env = request.env
        ICP = env['ir.config_parameter'].sudo()
        ga = float(ICP.get_param('hocba_reviews.grade_a', 85))
        gb = float(ICP.get_param('hocba_reviews.grade_b', 70))
        gc = float(ICP.get_param('hocba_reviews.grade_c', 55))
        target = float(ICP.get_param(
            'hocba_reviews.teacher_sessions_target', 60))
        cert_days = int(float(ICP.get_param('hoc_ba.cert_alert_days', 60)))

        Review = env['hb.performance.review']
        grade_label = dict(GRADE_SEL)
        # Ngưỡng dưới của từng loại; ngưỡng trên = ngưỡng dưới của loại trên nó.
        bounds = [('a', ga, None), ('b', gb, ga), ('c', gc, gb), ('d', 0.0, gc)]

        crits = env['hb.review.criteria'].sudo().search(
            [], order='role_group, sequence, id')
        criteria = {'teacher': [], 'office': []}
        for c in crits:
            criteria.setdefault(c.role_group, []).append({
                'id': c.id, 'name': c.name, 'code': c.code,
                'weight': c.weight, 'maxScore': c.max_score,
                'autoSource': c.auto_source, 'guideline': c.guideline or '',
                'anchors': _anchors(c),
            })
        # Thang chung minh hoạ theo điểm tối đa phổ biến nhất của bộ tiêu chí.
        maxes = crits.mapped('max_score') or [5]
        common_max = max(set(maxes), key=maxes.count)

        return request.make_json_response({
            'canManage': True,
            'grades': [{
                'key': k,
                'label': grade_label.get(k, k.upper()),
                'min': lo,
                'max': hi,
                'meaning': GRADE_MEANING.get(k, ''),
            } for k, lo, hi in bounds],
            'criteria': criteria,
            'scale': _scale_rows(common_max),
            'scaleMax': common_max,
            'weightSum': {
                g: sum(c['weight'] for c in rows)
                for g, rows in criteria.items()
            },
            'autoTables': {
                # [(ngưỡng dưới %, điểm)] — giảm dần, khớp _bucket() của model.
                'punctuality': [{'min': t, 'score': s}
                                for t, s in Review.PCT_TABLE],
                'workload': [{'min': t, 'score': s}
                             for t, s in Review.WORKLOAD_TABLE],
                'cert': [{'when': w, 'score': s, 'note': n}
                         for w, s, n in CERT_RULES],
            },
            'punctualRule': PUNCTUAL_RULE,
            'periods': [{
                'type': t,
                'label': label,
                'months': PERIOD_MONTHS.get(t, 3),
                'count': PERIOD_COUNT.get(t, 4),
                'sessionTarget': target * (PERIOD_MONTHS.get(t, 3) / 3.0),
            } for t, label in PERIOD_TYPE_SEL],
            'params': {
                'teacherSessionsTarget': target,
                'certAlertDays': cert_days,
            },
        })

    # ------------------------------------------------------------------
    # GET chi tiết
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews/<int:review_id>', auth='user',
                type='http', methods=['GET'])
    def api_review_detail(self, review_id, **kw):
        r = request.env['hb.performance.review'].sudo().browse(review_id)
        if not r.exists():
            return _err('not_found', status=404)
        if not self._emp_in_scope(r.employee_id):
            return _err('forbidden', status=403)
        return request.make_json_response(self._review_detail(r))

    # ------------------------------------------------------------------
    # POST tạo phiếu cho 1 nhân viên
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_review_create(self, **kw):
        payload = request.get_json_data() or {}
        emp_id = int(payload.get('employeeId') or 0)
        emp = request.env['hr.employee'].sudo().browse(emp_id)
        if not emp.exists():
            return _err('not_found', 'Không tìm thấy nhân viên.', status=404)
        if not self._emp_in_scope(emp):
            return _err('forbidden', status=403)
        try:
            r = request.env['hb.performance.review'].sudo().create({
                'employee_id': emp.id,
                'period_type': payload.get('periodType') or 'quarter',
                'period_year': int(payload.get('year')
                                   or fields.Date.today().year),
                'period_index': int(payload.get('index') or 1),
            })
        except (UserError, ValidationError) as ex:
            request.env.cr.rollback()
            return _err('rejected', str(ex))
        except Exception:
            request.env.cr.rollback()
            return _err('rejected', 'Nhân viên đã có phiếu đánh giá cho kỳ này.')
        return request.make_json_response(self._review_detail(r))

    # ------------------------------------------------------------------
    # POST lưu điểm / nhận xét
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews/<int:review_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_review_save(self, review_id, **kw):
        r = request.env['hb.performance.review'].sudo().browse(review_id)
        if not r.exists():
            return _err('not_found', status=404)
        if not self._emp_in_scope(r.employee_id):
            return _err('forbidden', status=403)
        if r.state != 'draft':
            return _err('rejected', 'Phiếu đã chốt — cần HR mở lại trước khi sửa.')
        payload = request.get_json_data() or {}
        try:
            for item in payload.get('lines') or []:
                line = r.line_ids.filtered(lambda l: l.id == int(item.get('id') or 0))
                if not line:
                    continue
                vals = {}
                if 'score' in item:
                    score = float(item['score'] or 0)
                    vals['score'] = score
                    if line.is_auto and score != line.auto_score:
                        vals['manual_override'] = True
                if 'note' in item:
                    vals['note'] = item['note'] or False
                if vals:
                    line.write(vals)
            head = {}
            for key, field in (('selfNote', 'self_note'),
                               ('managerNote', 'manager_note'),
                               ('hrNote', 'hr_note')):
                if key in payload:
                    head[field] = payload[key] or False
            if head:
                r.write(head)
        except (UserError, ValidationError, AccessError) as ex:
            request.env.cr.rollback()
            return _err('rejected', str(ex))
        return request.make_json_response(self._review_detail(r))

    # ------------------------------------------------------------------
    # POST hành động: compute / confirm / publish / reset
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews/<int:review_id>/action', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_review_action(self, review_id, **kw):
        r = request.env['hb.performance.review'].sudo().browse(review_id)
        if not r.exists():
            return _err('not_found', status=404)
        if not self._emp_in_scope(r.employee_id):
            return _err('forbidden', status=403)
        action = (request.get_json_data() or {}).get('action')
        if action in ('publish', 'reset') and not self._can_publish():
            return _err('forbidden',
                        'Chỉ HR/Admin được công bố hoặc mở lại phiếu.', status=403)
        try:
            if action == 'compute':
                r.compute_metrics()
            elif action == 'confirm':
                r.action_confirm()
            elif action == 'publish':
                r.action_publish()
            elif action == 'reset':
                r.action_reset_draft()
            else:
                return _err('bad_request', 'Hành động không hợp lệ.')
        except (UserError, ValidationError, AccessError) as ex:
            request.env.cr.rollback()
            return _err('rejected', str(ex))
        return request.make_json_response(self._review_detail(r))

    # ------------------------------------------------------------------
    # POST mở đợt hàng loạt
    # ------------------------------------------------------------------
    @http.route('/hocba-hrm/api/reviews/bulk-open', auth='user', type='http',
                methods=['POST'], csrf=False)
    def api_review_bulk_open(self, **kw):
        if not self._is_hr():
            return _err('forbidden',
                        'Chỉ HR/Admin được mở đợt đánh giá.', status=403)
        payload = request.get_json_data() or {}
        group = 'teacher' if payload.get('group') == 'teacher' else 'office'
        try:
            result = request.env['hb.performance.review'].sudo().open_period(
                group,
                payload.get('periodType') or 'quarter',
                int(payload.get('year') or fields.Date.today().year),
                int(payload.get('index') or 1))
        except (UserError, ValidationError) as ex:
            request.env.cr.rollback()
            return _err('rejected', str(ex))
        return request.make_json_response({
            'created': result['created'], 'skipped': result['skipped'],
        })
