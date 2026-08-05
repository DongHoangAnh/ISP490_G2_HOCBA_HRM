"""Slot phỏng vấn xếp được NHIỀU ứng viên cùng khung giờ.

`hb.interview.slot.applicant_ids` là many2many; `state` suy ra từ danh sách đó
(có ứng viên = Đã đặt) nên không còn nguồn sự thật thứ hai để lệch.
"""
from datetime import datetime, timedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInterviewSlotMulti(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create(
            {'name': 'Vị trí Test Slot PV', 'no_of_recruitment': 2})
        start = datetime(2026, 9, 1, 2, 0)  # 09:00 giờ VN
        cls.slot = cls.env['hb.interview.slot'].create({
            'start_datetime': start,
            'stop_datetime': start + timedelta(hours=1),
            'user_id': cls.env.user.id,
        })

    def _applicant(self, name):
        return self.env['hr.applicant'].create(
            {'partner_name': name, 'job_id': self.job.id})

    def test_10_slot_moi_con_trong(self):
        self.assertEqual(self.slot.state, 'available')
        self.assertEqual(self.slot.applicant_count, 0)

    def test_20_xep_nhieu_ung_vien_cung_slot(self):
        a1, a2, a3 = (self._applicant('UV %s' % i) for i in (1, 2, 3))
        for a in (a1, a2, a3):
            self.slot.write({'applicant_ids': [(4, a.id)]})
        self.assertEqual(self.slot.applicant_count, 3)
        self.assertEqual(self.slot.state, 'booked')
        self.assertEqual(set(self.slot.applicant_ids.ids), {a1.id, a2.id, a3.id})

    def test_30_go_tung_ung_vien(self):
        """Gỡ 1 người: slot vẫn Đã đặt; gỡ nốt người cuối mới về Còn trống."""
        a1, a2 = self._applicant('UV gỡ 1'), self._applicant('UV gỡ 2')
        self.slot.write({'applicant_ids': [(6, 0, [a1.id, a2.id])]})

        self.slot.write({'applicant_ids': [(3, a1.id)]})
        self.assertEqual(self.slot.state, 'booked')
        self.assertEqual(self.slot.applicant_ids, a2)

        self.slot.write({'applicant_ids': [(3, a2.id)]})
        self.assertEqual(self.slot.state, 'available')
        self.assertEqual(self.slot.applicant_count, 0)

    def test_40_action_mark_available_go_het(self):
        a1, a2 = self._applicant('UV hết 1'), self._applicant('UV hết 2')
        self.slot.write({'applicant_ids': [(6, 0, [a1.id, a2.id])]})
        self.slot.action_mark_available()
        self.assertEqual(self.slot.state, 'available')
        self.assertFalse(self.slot.applicant_ids)

    def test_50_mot_ung_vien_nhieu_slot(self):
        """Ứng viên có thể nằm ở nhiều slot (PV vòng 1 / vòng 2) — m2m 2 chiều."""
        a = self._applicant('UV hai vòng')
        slot2 = self.env['hb.interview.slot'].create({
            'start_datetime': datetime(2026, 9, 2, 2, 0),
            'stop_datetime': datetime(2026, 9, 2, 3, 0),
            'user_id': self.env.user.id,
        })
        self.slot.write({'applicant_ids': [(4, a.id)]})
        slot2.write({'applicant_ids': [(4, a.id)]})
        self.assertEqual(self.slot.state, 'booked')
        self.assertEqual(slot2.state, 'booked')
