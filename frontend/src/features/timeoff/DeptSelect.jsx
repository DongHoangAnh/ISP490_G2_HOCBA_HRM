/* Dropdown lọc phòng ban dùng chung cho các tab Nghỉ phép. Owner: Nhật Anh. */
export default function DeptSelect({ value, onChange, departments, style }) {
  return (
    <select className="sel" style={style} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Mọi phòng ban</option>
      {(departments || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
    </select>
  );
}
