/* Thanh sắp xếp dùng chung cho các trang danh sách nghỉ phép.
   - fields: [{ key, label, type? }]  type ∈ 'text' | 'num' | 'date' (mặc định 'text').
   - sort:   { key, dir }  dir ∈ 'asc' | 'desc'.
   - onChange(nextSort).
   - departments / dept / onDeptChange (tùy chọn): khi chọn sắp xếp theo cột
     'department' và có danh sách phòng ban (role HR), ô bên cạnh đổi từ nút
     tăng/giảm thành dropdown lọc phòng ban.
   sortRows(rows, fields, sort) trả về mảng đã sắp xếp (không đổi mảng gốc). */
import Icon from '../../components/Icon';

export function sortRows(rows, fields, sort) {
  if (!sort || !sort.key) return rows;
  const f = fields.find((x) => x.key === sort.key);
  const type = f?.type || 'text';
  const dir = sort.dir === 'desc' ? -1 : 1;
  return [...rows].sort((a, b) => {
    const va = a[sort.key], vb = b[sort.key];
    let c;
    if (type === 'num') {
      c = (Number(va) || 0) - (Number(vb) || 0);
    } else if (type === 'date') {
      c = String(va || '').localeCompare(String(vb || ''));
    } else {
      c = String(va ?? '').localeCompare(String(vb ?? ''), 'vi', { sensitivity: 'base' });
    }
    return c * dir;
  });
}

export default function SortBar({ fields, sort, onChange, departments, dept, onDeptChange }) {
  const dir = sort.dir === 'desc' ? 'desc' : 'asc';
  // Role HR + đang sắp xếp theo phòng ban → ô bên cạnh thành dropdown lọc phòng ban.
  const deptMode = sort.key === 'department' && departments && departments.length > 0;
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <span className="muted" style={{ fontSize: 12.5, fontWeight: 600 }}>Sắp xếp</span>
      <select
        className="sel"
        style={{ padding: '7px 11px' }}
        value={sort.key}
        onChange={(e) => onChange({ key: e.target.value, dir })}
      >
        {fields.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
      </select>
      {deptMode ? (
        <select
          className="sel"
          style={{ padding: '7px 11px' }}
          value={dept || ''}
          onChange={(e) => onDeptChange && onDeptChange(e.target.value)}
        >
          <option value="">Mọi phòng ban</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      ) : (
        <button
          className="btn btn-ghost btn-sm"
          title={dir === 'asc' ? 'Tăng dần' : 'Giảm dần'}
          onClick={() => onChange({ key: sort.key, dir: dir === 'asc' ? 'desc' : 'asc' })}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}
        >
          <span style={{ display: 'inline-flex', transform: dir === 'asc' ? 'rotate(-90deg)' : 'rotate(90deg)' }}>
            <Icon name="chevR" size={14} />
          </span>
          {dir === 'asc' ? 'Tăng dần' : 'Giảm dần'}
        </button>
      )}
    </div>
  );
}
