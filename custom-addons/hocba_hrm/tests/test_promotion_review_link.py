"""Gắn bản ghi thăng tiến vào phiếu đánh giá của module hocba_reviews.

Spec: docs/superpowers/specs/
2026-08-12-gop-danh-gia-thang-tien-vao-reviews-design.md

Nhập liệu thăng tiến chuyển hẳn sang màn Đánh giá, nên phiếu là CĂN CỨ của
quyết định — ba ràng buộc dưới đây phải nằm ở server, không tin FE: sai
nhân viên, phiếu còn nháp, và tạo trùng.

Phiếu cũng đóng vai BẰNG CHỨNG đổi lương (_check_rules của
hr.promotion.history): trước đây SPA không có ô nhập x_evidence_url nên mọi
lần tạo thăng tiến CÓ đổi lương đều bị chặn — xem
test_thang_tien_doi_luong_khong_can_link_khi_da_gan_phieu.
"""
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM


@tagged('post_install', '-at_install')
class TestPromotionReviewLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()
        self.dept = self.env['hr.department'].create({'name': 'Link Dept'})
        self.job_old = self.env['hr.job'].create({'name': 'Link Job cu'})
        self.job_new = self.env['hr.job'].create({'name': 'Link Job moi'})
        self.emp = self.env['hr.employee'].create({
            'name': 'Link Emp', 'identification_id': '018000000001',
            'department_id': self.dept.id, 'job_id': self.job_old.id,
            'x_employment_status': 'parttime'})
        self.other = self.env['hr.employee'].create({
            'name': 'Link Other', 'identification_id': '018000000002',
            'department_id': self.dept.id, 'x_employment_status': 'parttime'})

    def _review(self, emp, state='confirmed'):
        """create() của phiếu tự sinh dòng chấm từ bộ tiêu chí của Việt."""
        rec = self.env['hb.performance.review'].create({
            'employee_id': emp.id, 'period_type': 'quarter',
            'period_year': 2026, 'period_index': 1})
        if state != 'draft':
            for line in rec.line_ids:
                line.score = line.max_score
            rec.manager_note = 'Hoàn thành tốt công việc trong kỳ.'
            rec.action_confirm()
        if state == 'published':
            rec.action_publish()
        return rec

    def _promo_vals(self, **kw):
        vals = {'employee_id': self.emp.id, 'x_change_type': 'promotion',
                'from_job_id': self.job_old.id, 'to_job_id': self.job_new.id,
                'date_effective': fields.Date.today(),
                'reason': 'Thăng tiến sau đánh giá'}
        vals.update(kw)
        return vals

    def _check(self, review, emp=None):
        return self.ctrl._promo_validate_review(
            self.env, (emp or self.emp).id, review.id)

    # --- 3 ràng buộc chặn ------------------------------------------------
    def test_phieu_con_nhap_bi_chan(self):
        rv = self._review(self.emp, state='draft')
        with self.assertRaises(ValidationError):
            self._check(rv)

    def test_phieu_cua_nhan_vien_khac_bi_chan(self):
        rv = self._review(self.other)
        with self.assertRaises(ValidationError):
            self._check(rv)

    def test_khong_gan_hai_thang_tien_vao_mot_phieu(self):
        rv = self._review(self.emp)
        self.env['hr.promotion.history'].create(
            self._promo_vals(review_id=rv.id))
        with self.assertRaises(ValidationError):
            self._check(rv)

    def test_phieu_khong_ton_tai_bi_chan(self):
        rv = self.env['hb.performance.review'].browse(999999999)
        with self.assertRaises(ValidationError):
            self.ctrl._promo_validate_review(self.env, self.emp.id, rv.id)

    # --- đường hợp lệ ----------------------------------------------------
    def test_phieu_da_chot_qua_duoc(self):
        rv = self._review(self.emp)
        self.assertEqual(self._check(rv).id, rv.id)

    def test_phieu_da_cong_bo_qua_duoc(self):
        rv = self._review(self.emp, state='published')
        self.assertEqual(self._check(rv).id, rv.id)

    def test_ghi_duoc_review_id_len_ban_ghi_thang_tien(self):
        rv = self._review(self.emp)
        promo = self.env['hr.promotion.history'].create(
            self._promo_vals(review_id=rv.id))
        self.assertEqual(promo.review_id.id, rv.id)

    def test_thang_tien_doi_luong_khong_can_link_khi_da_gan_phieu(self):
        """Trước đây: SPA không có ô x_evidence_url nên MỌI lần tạo thăng tiến
        có đổi lương đều bị ValidationError. Phiếu gắn kèm là bằng chứng."""
        rv = self._review(self.emp)
        promo = self.env['hr.promotion.history'].create(self._promo_vals(
            from_wage=10000000, to_wage=15000000, review_id=rv.id))
        self.assertEqual(promo.to_wage, 15000000)

    def test_doi_luong_khong_phieu_khong_link_van_bi_chan(self):
        """Ràng buộc bằng chứng của họp #2 vẫn còn nguyên cho đường tạo tay."""
        with self.assertRaises(ValidationError):
            self.env['hr.promotion.history'].create(self._promo_vals(
                from_wage=10000000, to_wage=15000000))
