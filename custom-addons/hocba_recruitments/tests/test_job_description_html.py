"""Mô tả công việc (JD) không được lòi thẻ HTML ra cho người đọc.

`hr.job.description` là field **Html** (ORM sanitize lúc ghi). Trang tuyển dụng
công khai lại `escape()` giá trị đó trước khi nhúng ⇒ ứng viên/giáo viên mở
/jobs đọc được đúng chữ `<p>…</p>` thay vì nội dung. Ngược lại, ô "Mô tả công
việc (JD)" trên SPA là textarea text thuần: lưu thẳng text vào field Html thì
mọi xuống dòng biến mất lúc render.

Quy ước chốt 2026-08-29:
  · DB luôn giữ HTML — text thuần từ SPA được `plaintext2html` hoá lúc lưu.
  · Nhúng ra trang công khai thì giữ nguyên thẻ thật, chỉ escape phần text thuần.
  · Form SPA luôn hiện text thuần (JobForm dùng htmlToText), không bao giờ lòi thẻ.
"""
from odoo.tests import TransactionCase, tagged

from odoo.addons.hocba_recruitments.controllers.main import HocBaTuyenDung


@tagged('post_install', '-at_install')
class TestJobDescriptionHtml(TransactionCase):
    """Hai hàm thuần payload/chuỗi nên gọi thẳng, không cần dựng HTTP."""

    # ── Lưu: text thuần → HTML ───────────────────────────────────────────────

    def test_01_text_thuan_thanh_html_khi_luu(self):
        vals = HocBaTuyenDung()._job_vals({'description': 'Dòng 1\nDòng 2'})
        self.assertEqual(vals['description'], '<p>Dòng 1<br/>Dòng 2</p>')

    def test_02_html_san_thi_giu_nguyen(self):
        html = '<p>Dạy lớp HSK1-3</p><ul><li>Soạn giáo án</li></ul>'
        vals = HocBaTuyenDung()._job_vals({'description': html})
        self.assertEqual(vals['description'], html)

    def test_03_de_trong_thi_khong_boc_the(self):
        self.assertFalse(HocBaTuyenDung()._job_vals({'description': ''})['description'])

    def test_04_khong_gui_thi_khong_dung_toi(self):
        self.assertNotIn('description', HocBaTuyenDung()._job_vals({'name': 'X'}))

    # ── Nhúng ra trang công khai ─────────────────────────────────────────────

    def test_10_the_that_khong_bi_escape(self):
        out = str(HocBaTuyenDung()._as_html('<p>Dạy lớp HSK1-3</p>'))
        self.assertIn('<p>Dạy lớp HSK1-3</p>', out)
        self.assertNotIn('&lt;p&gt;', out, 'không được in thẻ ra cho người đọc')

    def test_11_text_thuan_giu_xuong_dong(self):
        out = str(HocBaTuyenDung()._as_html('Dòng 1\nDòng 2'))
        self.assertIn('<br/>', out)
        self.assertIn('Dòng 1', out)

    def test_12_text_thuan_van_duoc_escape(self):
        """"Lương < 10 triệu & thưởng" không phải thẻ ⇒ vẫn phải escape."""
        out = str(HocBaTuyenDung()._as_html('Lương < 10 triệu & thưởng'))
        self.assertIn('&lt;', out)
        self.assertIn('&amp;', out)
