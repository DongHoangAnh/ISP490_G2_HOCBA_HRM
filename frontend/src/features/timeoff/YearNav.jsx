/* Thanh chọn năm dùng chung cho các tab Nghỉ phép. Owner: Nhật Anh. */
import Icon from '../../components/Icon';

const THIS_YEAR = new Date().getFullYear();

/* disabled: khoá đổi năm khi caller đang có action bay (vd đang lưu ngày làm việc)
   — đổi năm giữa chừng sẽ ghi payload năm cũ vào cache năm mới. */
export default function YearNav({ year, onChange, disabled }) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button className="icon-btn" disabled={disabled} onClick={() => onChange(year - 1)}>
        <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
      <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
      <button className="icon-btn" disabled={disabled} onClick={() => onChange(year + 1)}><Icon name="chevR" size={16} /></button>
      <button className="btn btn-ghost btn-sm" disabled={disabled} onClick={() => onChange(THIS_YEAR)}>Năm nay</button>
    </div>
  );
}
