/* Dữ liệu mẫu cho 2 tab chưa có backend (Đơn quên chấm công, Tăng ca).
   Quy ước §7: có cờ USE_MOCK; xóa khi backend sẵn sàng. */
export const USE_MOCK = true;

export const FORGOT_REQUESTS = [
  { id: 1, name: 'Trần Thị B', code: 'GV002', depName: 'Tiếng Trung',
    missType: 'Quên check-out', date: '2026-06-11', proposed: '17:30',
    reason: 'Quên bấm khi ra về', state: 'Chờ duyệt' },
  { id: 2, name: 'Lê Văn C', code: 'NV010', depName: 'Hành chính',
    missType: 'Quên check-in', date: '2026-06-12', proposed: '08:10',
    reason: 'Điện thoại hết pin', state: 'Chờ duyệt' },
];

export const OT_LOG = [
  { id: 1, name: 'Phạm Thị D', code: 'GV005', depName: 'Luyện thi',
    date: '2026-06-10', hours: 2.5, rate: 150, reason: 'Dạy bù lớp tối' },
  { id: 2, name: 'Hoàng Văn E', code: 'NV021', depName: 'Marketing',
    date: '2026-06-08', hours: 3, rate: 100, reason: 'Chạy chiến dịch tuyển sinh' },
];
