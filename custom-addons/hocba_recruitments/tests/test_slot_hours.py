"""Khung giờ phỏng vấn cấu hình được.

Spec: docs/superpowers/specs/2026-08-11-interview-hours-config-design.md

Trước bản này khung giờ khai lịch rảnh cứng 09:00–17:00 bước 30 phút, lại cứng ở
HAI nơi độc lập (Selection của wizard Odoo + hằng số JS của SPA). Trung tâm dạy
buổi tối nên trưởng bộ phận không khai nổi slot sau 17:00.

Nay ba tham số ir.config_parameter quyết định danh sách giờ, backend là nguồn sự
thật duy nhất; controller kiểm giờ khai mới nằm trong khung.
"""
from odoo.tests import HttpCase, TransactionCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'
P_OPEN = 'hocba_recruitments.slot_hour_open'
P_CLOSE = 'hocba_recruitments.slot_hour_close'
P_STEP = 'hocba_recruitments.slot_step_minutes'


@tagged('post_install', '-at_install')
class TestSlotHours(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ICP = self.env['ir.config_parameter'].sudo()
        self.Slot = self.env['hb.interview.slot']

    def _set(self, open_h=None, close_h=None, step=None):
        if open_h is not None:
            self.ICP.set_param(P_OPEN, str(open_h))
        if close_h is not None:
            self.ICP.set_param(P_CLOSE, str(close_h))
        if step is not None:
            self.ICP.set_param(P_STEP, str(step))

    def test_01_default_hours(self):
        """Chưa cấu hình gì ⇒ giữ nguyên hành vi cũ: 09:00–17:00 mỗi 30 phút."""
        for key in (P_OPEN, P_CLOSE, P_STEP):
            self.ICP.set_param(key, '')
        opts = self.Slot._hb_hour_slots()
        self.assertEqual(len(opts), 17)
        self.assertEqual(opts[0], (9.0, '09:00'))
        self.assertEqual(opts[-1], (17.0, '17:00'))

    def test_02_custom_range_and_step(self):
        """Trung tâm dạy tối: 08:00–20:00 mỗi 60 phút."""
        self._set(8.0, 20.0, 60)
        opts = self.Slot._hb_hour_slots()
        self.assertEqual(len(opts), 13)
        self.assertEqual(opts[0], (8.0, '08:00'))
        self.assertEqual(opts[-1], (20.0, '20:00'))

    def test_03_step_15(self):
        self._set(9.0, 10.0, 15)
        opts = self.Slot._hb_hour_slots()
        self.assertEqual([o[1] for o in opts],
                         ['09:00', '09:15', '09:30', '09:45', '10:00'])
        self.assertEqual(opts[1][0], 9.25)

    def test_04_wizard_selection_follows_config(self):
        """Selection phải là callable — đổi cấu hình là đổi ngay, không cần
        restart Odoo (module load một lần, hằng số thì đóng băng theo)."""
        self._set(8.0, 20.0, 60)
        line = self.env['hb.interview.slot.wizard.line']
        starts = dict(line.fields_get(['start_hour'])['start_hour']['selection'])
        self.assertIn('8.0', starts)
        self.assertNotIn('17.5', starts)

    def test_10_existing_slot_survives_narrowing(self):
        """Slot 18:00 đã khai từ trước, sau đó thu khung về 17:00 ⇒ vẫn đọc được.
        Slot lưu datetime chứ không lưu mã giờ nên thu khung không phá dữ liệu."""
        self._set(8.0, 20.0, 60)
        slot = self.Slot.create({
            'start_datetime': '2026-09-01 11:00:00',   # 18:00 giờ VN
            'stop_datetime': '2026-09-01 12:00:00',
            'user_id': self.env.user.id,
        })
        self._set(9.0, 17.0, 30)
        slot.invalidate_recordset()
        self.assertTrue(slot.exists())
        self.assertEqual(str(slot.start_datetime), '2026-09-01 11:00:00')


@tagged('post_install', '-at_install')
class TestSlotHoursApi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env['ir.config_parameter'].sudo()
        cls.user_admin = cls.env['res.users'].create({
            'name': 'Admin (test slot hours)',
            'login': 'test_slothours_admin', 'password': PWD,
            'group_ids': [(4, cls.env.ref('base.group_system').id),
                          (4, cls.env.ref('hr_recruitment.group_hr_recruitment_manager').id)],
        })
        # Trưởng phòng: khai được slot nhưng KHÔNG được sửa cấu hình.
        cls.user_manager = cls.env['res.users'].create({
            'name': 'TBP (test slot hours)',
            'login': 'test_slothours_tbp', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr_recruitment.group_hr_recruitment_user').id)],
        })

    def _post(self, url, payload, login, expect):
        self.authenticate(login, PWD)
        res = self.url_open(url, data=payload,
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def _make_slot(self, start, end, login='test_slothours_admin', expect=200):
        import json
        return self._post(
            '%s/interview-slots' % BASE,
            json.dumps({'slots': [
                {'date': '2026-09-01', 'startHour': start, 'endHour': end}]}),
            login, expect)

    def _save_cfg(self, payload, login='test_slothours_admin', expect=200):
        import json
        return self._post('%s/config/slot-hours' % BASE,
                          json.dumps(payload), login, expect)

    def test_05_create_slot_outside_range_rejected(self):
        self.ICP.set_param('hocba_recruitments.slot_hour_close', '17.0')
        body = self._make_slot(18.0, 19.0, expect=400)
        self.assertEqual(body['error'], 'rejected')

    def test_06_create_slot_inside_range_ok(self):
        self.ICP.set_param('hocba_recruitments.slot_hour_open', '8.0')
        self.ICP.set_param('hocba_recruitments.slot_hour_close', '20.0')
        body = self._make_slot(18.0, 19.0)
        self.assertEqual(body['created'], 1)

    def test_07_save_config_invalid_order(self):
        self._save_cfg({'open': 18.0, 'close': 9.0, 'stepMinutes': 30},
                       expect=400)

    def test_08_save_config_bad_step(self):
        self._save_cfg({'open': 9.0, 'close': 17.0, 'stepMinutes': 45},
                       expect=400)

    def test_09_config_requires_permission(self):
        self._save_cfg({'open': 8.0, 'close': 20.0, 'stepMinutes': 60},
                       login='test_slothours_tbp', expect=403)

    def test_11_config_roundtrip(self):
        self._save_cfg({'open': 7.5, 'close': 21.0, 'stepMinutes': 15})
        self.authenticate('test_slothours_admin', PWD)
        cfg = self.url_open('%s/config' % BASE).json()['slotHours']
        self.assertEqual((cfg['open'], cfg['close'], cfg['stepMinutes']),
                         (7.5, 21.0, 15))
        self.assertEqual(cfg['options'][0], [7.5, '07:30'])
