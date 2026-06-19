import { hbInitials, hbAvCls } from '../utils/format';

/* Avatar nhân viên: ảnh thật từ Odoo nếu có, fallback chữ cái đầu */
export default function Avatar({ emp, size = 34 }) {
  if (emp.hasImg) {
    return (
      <img src={`/web/image/hr.employee/${emp.id}/avatar_128`} alt=""
        style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
    );
  }
  return (
    <div className={'av ' + hbAvCls(emp.id)} style={{ width: size, height: size, fontSize: size * 0.36 }}>
      {hbInitials(emp.name)}
    </div>
  );
}
