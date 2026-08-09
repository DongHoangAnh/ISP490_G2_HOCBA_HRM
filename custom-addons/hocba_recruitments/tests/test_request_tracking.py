"""Tab "Theo dõi tuyển dụng" — số liệu tiến độ theo từng phiếu yêu cầu.

Bảng cơ bản (GET /recruitment/jobs → data['requests']): vị trí · phòng ban ·
trạng thái · số lượng tuyển · đã tuyển · deadline (Ngày cần onboard).
Xổ dòng chi tiết: đã nộp CV · hoàn thiện thử việc · fail CV · fail PV.
Bấm vào một con số → GET /recruitment/request/<id>/applicants?group=... trả
danh sách ứng viên + thông tin JD cho popup.

Quy ước đếm (xem _request_stats): ứng viên gắn thẳng vào đợt tuyển qua
hr.applicant.hb_request_id, tính cả hồ sơ đã lưu trữ (active_test=False) vì hồ sơ
hay bị lưu trữ sau khi nhận việc. "Đã tuyển" = ứng viên ở stage hired_stage
(Bàn giao nhân sự) — NV lên Chính thức thì
hr_employee._hb_advance_applicant_to_handover() đẩy tới đây.
"""
from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestRequestTracking(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Dept = cls.env['hr.department']
        cls.dept_a = Dept.create({'name': 'Phòng A (test tracking)'})
        cls.dept_b = Dept.create({'name': 'Phòng B (test tracking)'})

        Users = cls.env['res.users']
        cls.user_hr = Users.create({
            'name': 'HR (test tracking)',
            'login': 'test_track_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.user_mgr = Users.create({
            'name': 'TBP phòng A (test tracking)',
            'login': 'test_track_mgr', 'password': PWD,
        })
        cls.emp_mgr = cls.env['hr.employee'].create({
            'name': 'TBP phòng A (test tracking)',
            'user_id': cls.user_mgr.id,
            'department_id': cls.dept_a.id,
        })
        cls.dept_a.manager_id = cls.emp_mgr

        Stage = cls.env['hr.recruitment.stage']
        cls.stage_new = Stage.search([('hired_stage', '=', False)], limit=1)
        cls.stage_hired = Stage.search([('hired_stage', '=', True)], limit=1)

        # no_of_recruitment=0 để chỉ tiêu đến thuần từ phiếu; qty=5 đủ rộng để
        # 1 ứng viên hired KHÔNG kích hoạt tự đóng phiếu (_hb_auto_close_if_filled).
        cls.job_a = cls.env['hr.job'].create({
            'name': 'Giáo viên tiếng Trung (test tracking)',
            'department_id': cls.dept_a.id,
            'no_of_recruitment': 0,
        })
        cls.req_a = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept_a.id,
            'job_id': cls.job_a.id,
            'job_title': cls.job_a.name,
            'qty_expected': 5,
            'level': 'junior',
            'expected_start_date': '2026-09-15',
            'salary_from': 12000000,
            'salary_to': 18000000,
            'language_requirement': 'HSK5',
        })
        cls.req_a.action_submit()
        cls.req_a.action_approve()

        # Phiếu phòng B — dùng cho ca phân quyền.
        cls.job_b = cls.env['hr.job'].create({
            'name': 'Kế toán (test tracking)',
            'department_id': cls.dept_b.id,
            'no_of_recruitment': 0,
        })
        cls.req_b = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept_b.id,
            'job_id': cls.job_b.id,
            'job_title': cls.job_b.name,
            'qty_expected': 1,
        })
        cls.req_b.action_submit()
        cls.req_b.action_approve()

        # Phiếu chưa gắn JD — không có ứng viên nào quy về được.
        cls.req_nojd = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept_a.id,
            'job_title': 'Vị trí chưa có JD (test tracking)',
            'qty_expected': 2,
        })
        cls.req_nojd.action_submit()
        cls.req_nojd.action_approve()

        Applicant = cls.env['hr.applicant']

        def uv(name, **vals):
            return Applicant.create(dict(
                {'partner_name': name, 'job_id': cls.job_a.id,
                 'stage_id': cls.stage_new.id}, **vals))

        # 5 CV: 1 đã qua thử việc · 1 fail CV · 1 fail PV · 1 fail cả hai · 1 đang xử lý
        cls.uv_hired = uv('UV Đạt thử việc')
        cls.uv_hired.write({'stage_id': cls.stage_hired.id})
        cls.uv_fail_cv = uv('UV Fail CV', cv_filter_result='fail')
        cls.uv_fail_pv = uv('UV Fail PV', interview_result='fail')
        cls.uv_fail_both = uv('UV Fail cả hai',
                              cv_filter_result='fail', interview_result='fail')
        cls.uv_running = uv('UV Đang xử lý')

    # ── helper ───────────────────────────────────────────────────────────────

    def _get(self, path, login=None, expect=200):
        self.authenticate(login or 'test_track_hr', PWD)
        res = self.url_open('%s/%s' % (BASE, path))
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def _row(self, req, login=None):
        rows = self._get('jobs', login)['requests']
        found = [r for r in rows if r['id'] == req.id]
        self.assertTrue(found, 'phiếu %s phải có trong danh sách' % req.name)
        return found[0]

    # ── Bảng cơ bản ──────────────────────────────────────────────────────────

    def test_01_basic_columns(self):
        """Vị trí · phòng ban · trạng thái · SL tuyển · đã tuyển · deadline."""
        r = self._row(self.req_a)
        self.assertEqual(r['jobTitle'], self.job_a.name)
        self.assertEqual(r['depName'], self.dept_a.name)
        self.assertEqual(r['state'], 'recruiting')
        self.assertTrue(r['stateLabel'], 'phải có nhãn trạng thái để hiện badge')
        self.assertEqual(r['qty'], 5)
        self.assertEqual(r['hired'], 1)
        self.assertEqual(r['deadline'], '2026-09-15',
                         'Deadline lấy từ Ngày cần onboard')

    def test_02_detail_counters(self):
        """Xổ chi tiết: nộp CV · hoàn thiện thử việc · fail CV · fail PV."""
        r = self._row(self.req_a)
        self.assertEqual(r['cvCount'], 5)
        self.assertEqual(r['hired'], 1)
        # "UV Fail cả hai" được tính ở CẢ hai cột — đây là 2 chỉ số độc lập
        # (rớt ở khâu lọc CV vs rớt ở khâu phỏng vấn), không phải phân loại loại trừ.
        self.assertEqual(r['failCv'], 2)
        self.assertEqual(r['failPv'], 2)

    def test_03_request_without_jd_counts_zero(self):
        """Phiếu chưa gắn JD: mọi con số = 0, không nổ lỗi."""
        r = self._row(self.req_nojd)
        self.assertEqual(
            (r['cvCount'], r['hired'], r['failCv'], r['failPv']), (0, 0, 0, 0))
        self.assertEqual(r['qty'], 2)

    def test_04_counters_do_not_leak_between_jobs(self):
        """Phiếu phòng B (JD khác) không ăn ké số của phòng A."""
        r = self._row(self.req_b)
        self.assertEqual(r['cvCount'], 0)
        self.assertEqual(r['hired'], 0)

    # ── Gắn CV vào đợt tuyển (hb_request_id) ─────────────────────────────────

    def test_05_new_cv_auto_joins_open_request(self):
        """CV mới của JD đang có phiếu tuyển → tự gắn vào phiếu đó."""
        a = self.env['hr.applicant'].create({
            'partner_name': 'UV tự gắn đợt', 'job_id': self.job_a.id})
        self.assertEqual(a.hb_request_id, self.req_a)

    def test_06_no_open_request_leaves_blank(self):
        """Vị trí không có phiếu nào đang tuyển → để trống, không gắn phiếu đã đóng."""
        job = self.env['hr.job'].create({
            'name': 'Vị trí không có đợt (test tracking)',
            'department_id': self.dept_a.id, 'no_of_recruitment': 0})
        closed = self.env['hb.recruitment.request'].create({
            'department_id': self.dept_a.id, 'job_id': job.id,
            'job_title': job.name, 'qty_expected': 1})
        closed.action_submit()
        closed.action_approve()
        closed.action_close()
        a = self.env['hr.applicant'].create({
            'partner_name': 'UV không đợt', 'job_id': job.id})
        self.assertFalse(a.hb_request_id,
                         'không được gắn bừa vào đợt đã chốt')

    def test_07_manual_choice_not_overwritten(self):
        """HR gán tay rồi đổi vị trí → máy không đạp lên lựa chọn của người."""
        a = self.env['hr.applicant'].create({
            'partner_name': 'UV gán tay', 'job_id': self.job_b.id,
            'hb_request_id': self.req_b.id})
        a.write({'job_id': self.job_a.id})
        self.assertEqual(a.hb_request_id, self.req_b)

    def test_08_two_batches_same_job_have_separate_books(self):
        """Hai đợt tuyển cùng một vị trí KHÔNG dùng chung số (lỗi gốc của bản cũ).

        Đóng đợt 1, mở đợt 2 trên cùng JD: CV cũ vẫn thuộc đợt 1, CV mới thuộc
        đợt 2 — trước đây cả hai đợt đều bắc cầu qua job_id nên ra cùng bộ số.
        """
        before = self._row(self.req_a)['cvCount']
        self.req_a.action_close()
        req2 = self.env['hb.recruitment.request'].create({
            'department_id': self.dept_a.id, 'job_id': self.job_a.id,
            'job_title': self.job_a.name, 'qty_expected': 3})
        req2.action_submit()
        req2.action_approve()
        self.env['hr.applicant'].create({
            'partner_name': 'UV đợt hai', 'job_id': self.job_a.id})

        rows = {r['id']: r for r in self._get('jobs')['requests']}
        self.assertEqual(rows[req2.id]['cvCount'], 1,
                         'đợt 2 chỉ đếm CV nộp sau khi mở đợt')
        self.assertEqual(before, 5, 'đợt 1 vẫn giữ nguyên 5 CV của mình')
        self.assertEqual(rows[self.req_a.id]['cvCount'], 5,
                         'đợt 1 đã đóng vẫn giữ đúng sổ của mình')
        # Đợt 2 không thừa hưởng kết quả fail của đợt 1
        self.assertEqual(rows[req2.id]['failCv'], 0)
        self.assertEqual(rows[req2.id]['failPv'], 0)

    def test_09_cv_form_lists_only_open_requests(self):
        """Ô "Đợt tuyển" ở form CV chỉ liệt kê phiếu đang tuyển, theo phạm vi."""
        codes = {q['code'] for q in self._get('cv')['requests']}
        self.assertIn(self.req_a.name, codes)
        mgr_codes = {q['code'] for q in self._get('cv', 'test_track_mgr')['requests']}
        self.assertIn(self.req_a.name, mgr_codes)
        self.assertNotIn(self.req_b.name, mgr_codes, 'phiếu phòng B ngoài phạm vi')

    # ── Popup danh sách ứng viên ─────────────────────────────────────────────

    def test_10_group_cv_lists_every_applicant(self):
        data = self._get('request/%s/applicants?group=cv' % self.req_a.id)
        self.assertEqual(data['group'], 'cv')
        self.assertEqual(len(data['rows']), 5)
        self.assertIn('UV Đạt thử việc', {r['name'] for r in data['rows']})

    def test_11_group_hired_lists_only_passed(self):
        data = self._get('request/%s/applicants?group=hired' % self.req_a.id)
        self.assertEqual([r['name'] for r in data['rows']], ['UV Đạt thử việc'])

    def test_12_group_fail_cv_and_fail_pv(self):
        cv = self._get('request/%s/applicants?group=fail_cv' % self.req_a.id)
        pv = self._get('request/%s/applicants?group=fail_pv' % self.req_a.id)
        self.assertEqual({r['name'] for r in cv['rows']},
                         {'UV Fail CV', 'UV Fail cả hai'})
        self.assertEqual({r['name'] for r in pv['rows']},
                         {'UV Fail PV', 'UV Fail cả hai'})

    def test_13_jd_block_for_popup(self):
        """Popup hiện kèm thông tin phiếu + JD để đối chiếu."""
        jd = self._get('request/%s/applicants?group=cv' % self.req_a.id)['jd']
        self.assertEqual(jd['jobTitle'], self.job_a.name)
        self.assertEqual(jd['depName'], self.dept_a.name)
        self.assertEqual(jd['qty'], 5)
        self.assertEqual(jd['deadline'], '2026-09-15')
        self.assertEqual(jd['code'], self.req_a.name)
        self.assertTrue(jd['levelLabel'])
        self.assertEqual(jd['languageRequirement'], 'HSK5')
        self.assertIn('12.000.000', jd['salary'])

    def test_14_bad_group_rejected(self):
        self._get('request/%s/applicants?group=banana' % self.req_a.id, expect=400)

    def test_15_missing_request_404(self):
        self._get('request/999999999/applicants', expect=404)

    # ── Tuyển đủ chỉ tiêu & nút Đăng tuyển/Ngừng đăng phản chiếu ra 2 tab ────
    # Model đã có test_auto_close.py; ở đây soi ĐÚNG THỨ 2 TAB NHÌN THẤY, vì tab
    # Kho JD đọc hr.job.recruitment_status còn tab Theo dõi đọc state của PHIẾU.

    def _tabs(self, login=None):
        d = self._get('jobs', login)
        return ({r['id']: r for r in d['rows']},        # tab Kho quản lý JD
                {q['id']: q for q in d['requests']})    # tab Theo dõi tuyển dụng

    def test_30_filled_quota_stops_job_and_closes_request(self):
        """Tuyển đủ → Kho JD chuyển "Dừng tuyển"; phiếu đóng nên rời tab Theo dõi."""
        job = self.env['hr.job'].create({
            'name': 'Vị trí đủ chỉ tiêu (test tracking)',
            'department_id': self.dept_a.id, 'no_of_recruitment': 0,
            'recruitment_status': 'recruiting', 'x_published': True})
        req = self.env['hb.recruitment.request'].create({
            'department_id': self.dept_a.id, 'job_id': job.id,
            'job_title': job.name, 'qty_expected': 1})
        req.action_submit()
        req.action_approve()

        jobs, reqs = self._tabs()
        self.assertEqual(jobs[job.id]['status'], 'recruiting')
        self.assertIn(req.id, reqs, 'đang tuyển thì phải nằm trên tab Theo dõi')

        a = self.env['hr.applicant'].create({
            'partner_name': 'UV lấp chỗ', 'job_id': job.id})
        a.write({'stage_id': self.stage_hired.id})

        self.assertEqual(job.recruitment_status, 'stopped')
        self.assertEqual(req.state, 'closed')
        jobs, reqs = self._tabs()
        self.assertEqual(jobs[job.id]['status'], 'stopped',
                         'tab Kho JD phải hiện Dừng tuyển')
        self.assertFalse(jobs[job.id]['published'], 'phải tự ngừng đăng')
        # Phiếu đã đóng vẫn Ở LẠI tab Theo dõi để người dùng thấy nó chuyển
        # trạng thái, thay vì biến mất đúng lúc đáng chú ý nhất.
        self.assertIn(req.id, reqs, 'phiếu đã đóng phải còn trên tab Theo dõi')
        self.assertEqual(reqs[req.id]['state'], 'closed')
        self.assertEqual(reqs[req.id]['jobStatus'], 'stopped')

    def test_31_publish_toggle_flips_recruitment_status(self):
        """Nút Ngừng đăng / Đăng tuyển đổi luôn Đang tuyển ↔ Dừng tuyển."""
        self.authenticate('test_track_hr', PWD)
        url = '%s/job/%s' % (BASE, self.job_a.id)

        det = self.url_open(url, data='{"published": true}',
                            headers={'Content-Type': 'application/json'}).json()
        self.assertTrue(det['published'])
        self.assertEqual(det['status'], 'recruiting')

        det = self.url_open(url, data='{"published": false}',
                            headers={'Content-Type': 'application/json'}).json()
        self.assertFalse(det['published'])
        self.assertEqual(det['status'], 'stopped')

    def test_32_publish_toggle_shows_on_tracking_tab(self):
        """Ngừng đăng: tab Theo dõi thấy jobStatus='stopped' nhưng phiếu VẪN MỞ.

        Hai khái niệm khác nhau và SPA ghép lại thành cột "Trạng thái":
        phiếu đóng > JD dừng tuyển > đang tuyển. Ngừng đăng chỉ tắt tin, bật lại
        được; đóng phiếu mới là chốt đợt.
        """
        self.authenticate('test_track_hr', PWD)
        url = '%s/job/%s' % (BASE, self.job_a.id)
        hdr = {'Content-Type': 'application/json'}

        self.url_open(url, data='{"published": false}', headers=hdr)
        self.assertEqual(self.job_a.recruitment_status, 'stopped')
        self.assertEqual(self.req_a.state, 'recruiting', 'không được đóng phiếu')
        _, reqs = self._tabs()
        self.assertEqual(reqs[self.req_a.id]['state'], 'recruiting')
        self.assertEqual(reqs[self.req_a.id]['jobStatus'], 'stopped')
        self.assertFalse(reqs[self.req_a.id]['published'])

        # Đăng lại → về Đang tuyển
        self.url_open(url, data='{"published": true}', headers=hdr)
        _, reqs = self._tabs()
        self.assertEqual(reqs[self.req_a.id]['jobStatus'], 'recruiting')
        self.assertTrue(reqs[self.req_a.id]['published'])

    def test_33_draft_and_refused_stay_off_tracking_tab(self):
        """Phiếu nháp / chờ duyệt / từ chối chưa vào guồng tuyển → không lên tab."""
        draft = self.env['hb.recruitment.request'].create({
            'department_id': self.dept_a.id, 'job_id': self.job_a.id,
            'job_title': self.job_a.name, 'qty_expected': 1})
        refused = self.env['hb.recruitment.request'].create({
            'department_id': self.dept_a.id, 'job_id': self.job_a.id,
            'job_title': self.job_a.name, 'qty_expected': 1})
        refused.action_submit()
        refused.action_refuse()
        _, reqs = self._tabs()
        self.assertNotIn(draft.id, reqs)
        self.assertNotIn(refused.id, reqs)

    # ── Phân quyền ───────────────────────────────────────────────────────────

    def test_20_manager_blocked_on_other_department(self):
        """Trưởng phòng A mở phiếu phòng B → 403."""
        self._get('request/%s/applicants' % self.req_b.id,
                  login='test_track_mgr', expect=403)

    def test_21_manager_allowed_on_own_department(self):
        data = self._get('request/%s/applicants' % self.req_a.id,
                         login='test_track_mgr')
        self.assertEqual(len(data['rows']), 5)

    def test_22_manager_list_scoped(self):
        """Danh sách phiếu của TBP A không có phiếu phòng B."""
        rows = self._get('jobs', 'test_track_mgr')['requests']
        ids = {r['id'] for r in rows}
        self.assertIn(self.req_a.id, ids)
        self.assertNotIn(self.req_b.id, ids)
