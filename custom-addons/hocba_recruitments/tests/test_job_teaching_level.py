"""Ô "Trình độ" của vị trí tuyển dụng (hr.job.x_teaching_level).

Từ 19.0.2.6.0 field là Char (nhập tự do) thay vì Selection 4 lựa chọn cứng:
danh sách HB_TEACHING_LEVELS chỉ là GỢI Ý cho SPA, model nhận mọi chuỗi.
Ràng buộc còn lại: phòng Giảng viên / Trợ giảng bắt buộc điền trình độ thật.
"""
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.hocba_recruitments.models.hr_job import HB_TEACHING_LEVELS


@tagged('post_install', '-at_install')
class TestJobTeachingLevel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Dept = cls.env['hr.department']
        cls.dep_teach = Dept.create({'name': 'Giảng viên'})
        cls.dep_office = Dept.create({'name': 'Phòng Test Trình Độ'})

    def _job(self, name, dep, level):
        return self.env['hr.job'].create({
            'name': name, 'department_id': dep.id, 'x_teaching_level': level,
        })

    def test_10_goi_y_du_cac_cap_hsk(self):
        """Gợi ý phải có đủ HSK1–6, cấp cao 7–9, HSKK và TOCFL."""
        for lv in ('HSK1', 'HSK2', 'HSK3', 'HSK4', 'HSK5', 'HSK6', 'HSK7-9'):
            self.assertIn(lv, HB_TEACHING_LEVELS)
        self.assertTrue(any(l.startswith('HSKK') for l in HB_TEACHING_LEVELS))
        self.assertTrue(any(l.startswith('TOCFL') for l in HB_TEACHING_LEVELS))

    def test_20_nhan_gia_tri_ngoai_danh_sach(self):
        """Trình độ lạ (không có trong gợi ý) vẫn lưu được — đây là mục đích đổi Char."""
        j = self._job('GV chứng chỉ lạ', self.dep_teach, 'YCT4 + chứng chỉ nội bộ Học Bá')
        self.assertEqual(j.x_teaching_level, 'YCT4 + chứng chỉ nội bộ Học Bá')

    def test_30_cap_hsk_cao_hop_le(self):
        j = self._job('GV HSK cấp cao', self.dep_teach, 'HSK7-9')
        self.assertEqual(j.x_teaching_level, 'HSK7-9')

    def test_40_phong_giang_day_bo_trong_bi_chan(self):
        with self.assertRaises(ValidationError):
            self._job('GV thiếu trình độ', self.dep_teach, '')

    def test_41_phong_giang_day_ghi_na_bi_chan(self):
        """'na' / 'N/A' là cách viết cũ của "không yêu cầu" — vẫn phải chặn."""
        for val in ('na', 'N/A', ' n/a '):
            with self.assertRaises(ValidationError):
                self._job('GV na %s' % val, self.dep_teach, val)

    def test_50_phong_khac_khong_bat_buoc(self):
        j = self._job('NV văn phòng không cần trình độ', self.dep_office, '')
        self.assertFalse(j.x_teaching_level)
