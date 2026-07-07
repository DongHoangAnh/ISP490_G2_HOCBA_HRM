/* Header chuẩn cho modal: gradient đỏ + ô icon + tiêu đề + nút đóng.
   lg: cỡ lớn (icon-box 48, title 20). iconBg: đổi màu nền ô icon.
   children: node chèn cạnh title (vd Badge). Owner: Nhật Anh. */
import Icon from './Icon';

export default function ModalHeader({ icon, title, sub, onClose, lg, iconBg, children }) {
  const box = lg ? 48 : 44;
  return (
    <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
      <div style={{ width: box, height: box, borderRadius: 12, background: iconBg || 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
        <Icon name={icon} size={lg ? 22 : 20} />
      </div>
      <div style={{ flex: 1 }}>
        <h2 style={{
          margin: 0, fontSize: lg ? 20 : 18, fontWeight: 800,
          letterSpacing: lg ? '-.3px' : undefined,
          display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
        }}>{title}{children}</h2>
        {sub && <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>{sub}</div>}
      </div>
      <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
    </div>
  );
}
