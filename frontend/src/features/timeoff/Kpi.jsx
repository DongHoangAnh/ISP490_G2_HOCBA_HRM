/* Thẻ KPI dùng chung cho các tab Nghỉ phép (Tổng quan, Đã duyệt, Giám sát
   duyệt đơn, Sức khỏe NV, Quỹ phép, Tổng hợp). Owner: Nhật Anh. */
export default function Kpi({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 18px' }}>
      <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px', color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="muted" style={{ fontSize: 11.5 }}>{sub}</div>}
    </div>
  );
}
