"""Trạng thái tuyển của vị trí bám theo VÒNG ĐỜI PHIẾU — mở lại và hạ xuống.

Kho JD là kho dùng lại: đợt tuyển kết thúc thì vị trí về "Dừng tuyển" nhưng JD
vẫn nằm đó cho đợt sau (yêu cầu nghiệp vụ 2026-08-29).

  · Tạo phiếu (hoặc gắn phiếu) vào một vị trí đang Dừng tuyển ⇒ **mở lại Đang
    tuyển ngay**, không chờ duyệt — `_resume_job_recruiting()`.
  · Vị trí hết phiếu đang mở (đóng / từ chối / xoá) ⇒ **hạ về Dừng tuyển** và
    gỡ tin đăng — `_stop_jobs_without_open_request()`.

"Đợt còn mở" gồm cả **nháp / chờ duyệt**, không chỉ `recruiting`: phiếu vừa tạo
còn Nháp đã mở lại vị trí, nên nếu chỉ đếm phiếu `recruiting` thì chốt đợt cũ sẽ
dập tắt luôn đợt mới đang chờ duyệt.

Cả hai chiều đều KHÔNG đụng cờ đăng tin theo hướng bật: đăng tuyển là quyết định
của HR ở tab Theo dõi tuyển dụng (SPEC §3.3).
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestJobReuse(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dept = self.env['hr.department'].create({'name': 'Phòng (test reuse)'})
        self.job = self.env['hr.job'].create({
            'name': 'Vị trí (test reuse)', 'department_id': self.dept.id,
            'no_of_recruitment': 0, 'recruitment_status': 'stopped',
            'x_published': False,
        })

    def _request(self, job=None, qty=1):
        j = job or self.job
        return self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_id': j.id,
            'job_title': j.name, 'qty_expected': qty,
        })

    # ── Chiều MỞ LẠI ─────────────────────────────────────────────────────────

    def test_01_tao_phieu_chon_jd_dang_dung_thi_mo_lai(self):
        """Ngay khi tạo phiếu (còn Nháp) đã mở lại Đang tuyển."""
        req = self._request()
        self.assertEqual(req.state, 'draft')
        self.assertEqual(self.job.recruitment_status, 'recruiting')

    def test_02_mo_lai_nhung_khong_tu_dang_tin(self):
        """Đăng tuyển vẫn là quyết định của HR — không tự bật cờ publish."""
        self._request()
        self.assertFalse(self.job.x_published)

    def test_03_phieu_khong_gan_jd_thi_khong_sao(self):
        req = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_title': 'Vị trí gõ tay',
            'qty_expected': 1})
        self.assertFalse(req.job_id)
        self.assertEqual(self.job.recruitment_status, 'stopped')

    def test_04_doi_sang_jd_khac_dang_dung_cung_mo_lai(self):
        job2 = self.env['hr.job'].create({
            'name': 'Vị trí 2 (test reuse)', 'department_id': self.dept.id,
            'no_of_recruitment': 0, 'recruitment_status': 'stopped'})
        req = self._request()
        req.write({'job_id': job2.id})
        self.assertEqual(job2.recruitment_status, 'recruiting')

    def test_05_vong_doi_dong_roi_tai_su_dung(self):
        """Đóng phiếu cuối → JD dừng; mở phiếu mới trên JD đó → tuyển lại."""
        req = self._request(qty=2)
        req.action_submit()
        req.action_approve()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        req.action_close()
        self.assertEqual(self.job.recruitment_status, 'stopped',
                         'hết phiếu mở thì vị trí phải dừng')
        self._request(qty=1)
        self.assertEqual(self.job.recruitment_status, 'recruiting',
                         'JD phải dùng lại được cho đợt sau')

    def test_06_jd_dang_tuyen_san_thi_khong_ghi_thua(self):
        """Vị trí vốn đang tuyển: tạo phiếu không sinh thêm ghi chú chatter."""
        self.job.write({'recruitment_status': 'recruiting'})
        before = len(self.job.message_ids)
        self._request()
        self.assertEqual(len(self.job.message_ids), before)

    # ── Chiều HẠ XUỐNG: từ chối / xoá phiếu ──────────────────────────────────

    def test_07_tu_choi_phieu_thi_ha_ve_dung_tuyen(self):
        """Từ chối phiếu duy nhất ⇒ vị trí không được treo "Đang tuyển"."""
        req = self._request()
        req.action_submit()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        req.action_refuse()
        self.assertEqual(req.state, 'refused')
        self.assertEqual(self.job.recruitment_status, 'stopped')

    def test_08_xoa_phieu_thi_ha_ve_dung_tuyen(self):
        req = self._request()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        req.unlink()
        self.assertEqual(self.job.recruitment_status, 'stopped')

    def test_09_con_phieu_khac_dang_mo_thi_giu_dang_tuyen(self):
        """Còn phiếu ĐANG TUYỂN ⇒ từ chối phiếu kia không hạ trạng thái."""
        req_a = self._request()
        req_a.action_submit()
        req_a.action_approve()
        req_b = self._request()
        req_b.action_submit()
        req_b.action_refuse()
        self.assertEqual(self.job.recruitment_status, 'recruiting')

    def test_10_con_phieu_nhap_thi_van_giu_dang_tuyen(self):
        """Phiếu Nháp cũng là đợt còn mở — nó đã mở vị trí ngay lúc tạo."""
        req_a = self._request()
        req_a.action_submit()
        req_a.action_approve()
        req_nhap = self._request()          # đợt mới, còn Nháp
        req_a.action_close()
        self.assertEqual(req_nhap.state, 'draft')
        self.assertEqual(self.job.recruitment_status, 'recruiting',
                         'đóng đợt cũ không được dập tắt đợt đang soạn')

    def test_11_xoa_phieu_khong_gan_jd_khong_loi(self):
        req = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_title': 'Vị trí gõ tay',
            'qty_expected': 1})
        req.unlink()
        self.assertEqual(self.job.recruitment_status, 'stopped')
