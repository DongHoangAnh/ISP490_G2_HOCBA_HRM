/* Dashboard tổng hợp — [CHUNG], hoàn thiện ở Giai đoạn 4 khi API các
   domain sẵn sàng. Tạm thời điều hướng nhanh. */
import Icon from '../../components/Icon';

const TILES = [
  ['employees', 'Nhân viên', 'users', 'Hồ sơ, phòng ban, thử việc — dữ liệu thật'],
  ['attendance', 'Chấm công', 'clock', 'Chờ API — Hoàng Anh'],
  ['timeoff', 'Nghỉ phép', 'calendar', 'Chờ API — Nhật Anh'],
  ['payroll', 'Bảng lương', 'wallet', 'Chờ API — Hùng'],
  ['recruitment', 'Tuyển dụng', 'briefcase', 'Chờ API — Việt'],
];

export default function Dashboard({ setView }) {
  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Học Bá HRM</h1>
          <p>Frontend tách riêng, nối Odoo qua JSON API — docs/QUY_UOC_FRONTEND.md</p>
        </div>
      </div>
      <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))' }}>
        {TILES.map(([id, label, icon, sub]) => (
          <div key={id} className="card" style={{ padding: 20, cursor: 'pointer' }} onClick={() => setView(id)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 11, background: 'var(--red-50)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--red-600)' }}>
                <Icon name={icon} size={20} />
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 14.5 }}>{label}</div>
                <div className="muted" style={{ fontSize: 12 }}>{sub}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
