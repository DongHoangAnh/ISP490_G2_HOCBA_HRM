"""Ô "Trình độ" của vị trí tuyển dụng (hr.job.x_teaching_level).

Field là Char (nhập tự do): HB_TEACHING_LEVELS chỉ là DANH SÁCH GỢI Ý cho SPA,
model nhận mọi chuỗi.

⚠️ KHÔNG có ràng buộc bắt buộc điền — và các test dưới đây khoá điều đó lại.
Ràng buộc cũ ("phòng Giảng viên / Trợ giảng bắt buộc điền trình độ") đã bỏ ngày
2026-08-07 vì đối chiếu file quy trình gốc của khách cho thấy cụm sheet 7.x
(tuyển dụng) không hề thu thập trình độ; lý do đầy đủ nằm trong
models/hr_job.py. Bộ test cũ vẫn xanh dù luật chết trên dữ liệu thật, vì nó tự
tạo một phòng ban tên 'Giảng viên' — phòng không tồn tại trong 6 phòng chuẩn.
Nên từ đây test chạy trên PHÒNG BAN SEED THẬT.
"""
from odoo.tests import TransactionCase, tagged

from odoo.addons.hocba_recruitments.models.hr_job import HB_TEACHING_LEVELS


@tagged('post_install', '-at_install')
class TestJobTeachingLevel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Phòng thật trong seed — nơi các vị trí giảng dạy đang nằm.
        cls.dep_van_hanh = cls.env.ref('hocba_employees.dept_van_hanh')
        cls.dep_san_pham = cls.env.ref('hocba_employees.dept_rd_sp')

    def _job(self, name, dep, level=''):
        return self.env['hr.job'].create({
            'name': name, 'department_id': dep.id, 'x_teaching_level': level,
        })

    # ── Danh sách gợi ý ──────────────────────────────────────────────────────

    def test_10_goi_y_du_cac_cap_hsk(self):
        """Gợi ý phải có đủ HSK1–6, cấp cao 7–9, HSKK và TOCFL."""
        for lv in ('HSK1', 'HSK2', 'HSK3', 'HSK4', 'HSK5', 'HSK6', 'HSK7-9'):
            self.assertIn(lv, HB_TEACHING_LEVELS)
        self.assertTrue(any(l.startswith('HSKK') for l in HB_TEACHING_LEVELS))
        self.assertTrue(any(l.startswith('TOCFL') for l in HB_TEACHING_LEVELS))

    def test_20_nhan_gia_tri_ngoai_danh_sach(self):
        """Trình độ lạ (không có trong gợi ý) vẫn lưu được — mục đích của Char."""
        j = self._job('GV chứng chỉ lạ (test)', self.dep_van_hanh,
                      'YCT4 + chứng chỉ nội bộ Học Bá')
        self.assertEqual(j.x_teaching_level, 'YCT4 + chứng chỉ nội bộ Học Bá')

    def test_30_cap_hsk_cao_hop_le(self):
        j = self._job('GV HSK cấp cao (test)', self.dep_van_hanh, 'HSK7-9')
        self.assertEqual(j.x_teaching_level, 'HSK7-9')

    # ── Không bắt buộc — chốt lại để không ai âm thầm thêm ràng buộc ─────────

    def test_40_de_trong_van_luu_duoc(self):
        """Vị trí giảng dạy để trống Trình độ vẫn lưu bình thường.

        Khách không thu thập trình độ ở khâu tuyển dụng: sheet "7.8 Danh sách
        vị trí JD" chỉ có Vị trí | Trạng thái | Số lượng | JD công việc.
        """
        j = self._job('Giáo viên tiếng Trung (test)', self.dep_van_hanh)
        self.assertFalse(j.x_teaching_level)

    def test_41_ghi_na_van_luu_duoc(self):
        """'N/A' từng bị chặn — giờ chỉ là một chuỗi như mọi chuỗi khác."""
        for val in ('na', 'N/A', ' n/a '):
            j = self._job('GV na %s (test)' % val, self.dep_van_hanh, val)
            self.assertEqual(j.x_teaching_level, val)

    def test_42_moi_phong_ban_deu_khong_bat_buoc(self):
        """Không phòng ban nào bắt buộc — kể cả phòng mô tả có chữ 'Giáo viên'.

        Phòng "Sản phẩm (R&D_SP)" ghi rõ chức năng "Giáo viên, R&D, học liệu,
        Tester", đúng phòng mà sheet 7.2 của khách xếp Giáo viên tiếng Trung
        vào. Nếu ai đó thêm lại luật so tên phòng, ca này sẽ đỏ.
        """
        for dep in (self.dep_van_hanh, self.dep_san_pham):
            j = self._job('Vị trí trống trình độ %s' % dep.id, dep)
            self.assertFalse(j.x_teaching_level)

    def test_43_khong_con_field_co_requires(self):
        """Field suy ra từ tên phòng ban đã bị gỡ hẳn, không chỉ vô hiệu hoá."""
        self.assertNotIn('x_requires_teaching_level', self.env['hr.job']._fields)
