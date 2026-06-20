/* Import lịch rảnh phỏng vấn theo tuần — Owner: Việt.
   Dán dữ liệu từ Excel/Google Sheets (hoặc upload .csv) → preview + kiểm tra →
   tạo hàng loạt slot cho 1 người phỏng vấn. Bổ sung cho nhập tay (SlotForm). */
import { useState, useMemo } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createInterviewSlots } from '../../api/recruitment';

const inp = {
  width: '100%', padding: '8px 10px', borderRadius: 9,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

const pad = (n) => String(n).padStart(2, '0');
const fmtHour = (h) => `${pad(Math.floor(h))}:${pad(Math.round((h % 1) * 60))}`;

/* Ngày: YYYY-MM-DD | DD/MM/YYYY | DD-MM-YYYY → trả 'YYYY-MM-DD' hoặc null */
function parseDate(raw) {
  const s = (raw || '').trim();
  let m;
  if ((m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) return `${m[1]}-${pad(m[2])}-${pad(m[3])}`;
  if ((m = s.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/))) return `${m[3]}-${pad(m[2])}-${pad(m[1])}`;
  return null;
}

/* Giờ: HH:MM | 9h | 9h30 | 9 | 9.5 → trả float (giờ) hoặc null */
function parseTime(raw) {
  const s = (raw || '').trim().toLowerCase().replace(/\s/g, '');
  let m;
  if ((m = s.match(/^(\d{1,2}):(\d{2})$/))) { const h = +m[1], mm = +m[2]; return h <= 24 && mm < 60 ? h + mm / 60 : null; }
  if ((m = s.match(/^(\d{1,2})h(\d{1,2})?$/))) { const h = +m[1], mm = m[2] ? +m[2] : 0; return h <= 24 && mm < 60 ? h + mm / 60 : null; }
  if (/^(\d{1,2})([.,]\d+)?$/.test(s)) { const v = parseFloat(s.replace(',', '.')); return v >= 0 && v <= 24 ? v : null; }
  return null;
}

function splitCols(line) {
  if (line.includes('\t')) return line.split('\t');
  if (line.includes(';')) return line.split(';');
  if (line.includes(',')) return line.split(',');
  return line.split(/\s+/);
}

function parseRows(text) {
  return text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
    .map((line, i) => {
      // Bỏ qua dòng tiêu đề nếu có.
      if (i === 0 && /(ngày|date|bắt đầu|start|giờ)/i.test(line)) return { skip: true };
      const cols = splitCols(line).map((c) => c.trim()).filter(Boolean);
      const [d, s, e] = cols;
      const date = parseDate(d);
      const startHour = parseTime(s);
      const endHour = parseTime(e);
      let error = null;
      if (cols.length < 3) error = 'Thiếu cột (cần: ngày, bắt đầu, kết thúc)';
      else if (!date) error = `Ngày không hợp lệ: "${d || ''}"`;
      else if (startHour == null) error = `Giờ bắt đầu không hợp lệ: "${s || ''}"`;
      else if (endHour == null) error = `Giờ kết thúc không hợp lệ: "${e || ''}"`;
      else if (endHour <= startHour) error = 'Giờ kết thúc phải sau giờ bắt đầu';
      return { raw: line, date, startHour, endHour, error };
    })
    .filter((r) => !r.skip);
}

const TEMPLATE = 'Ngày,Bắt đầu,Kết thúc\n2026-06-22,09:00,10:00\n2026-06-22,10:30,11:30\n2026-06-23,14:00,15:00';

export default function SlotImport({ interviewers, meId, onClose, onSaved }) {
  const [userId, setUserId] = useState(meId);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const rows = useMemo(() => parseRows(text), [text]);
  const valid = rows.filter((r) => !r.error);
  const invalid = rows.filter((r) => r.error);

  const onFile = (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => setText(String(reader.result || ''));
    reader.readAsText(f);
  };

  const downloadTemplate = () => {
    const blob = new Blob([TEMPLATE], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'mau-lich-ranh-pv.csv';
    a.click(); URL.revokeObjectURL(url);
  };

  const submit = async () => {
    if (valid.length === 0) { setErr('Chưa có dòng hợp lệ nào để import.'); return; }
    setBusy(true); setErr(null);
    try {
      await createInterviewSlots(Number(userId), valid.map((r) => ({
        date: r.date, startHour: r.startHour, endHour: r.endHour,
      })));
      onSaved();
    } catch (e) { setErr(e.message || 'Import thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="file" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>Import lịch rảnh theo tuần</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Dán từ Excel / Google Sheets hoặc tải file .csv</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px', maxHeight: '62vh', overflowY: 'auto' }}>
        <label style={{ display: 'block', marginBottom: 16 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', display: 'block', marginBottom: 5 }}>Người phỏng vấn</span>
          <select style={inp} value={userId} onChange={(e) => setUserId(e.target.value)}>
            {!interviewers.some((u) => u.id === meId) && <option value={meId}>Tôi</option>}
            {interviewers.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
        </label>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Dữ liệu lịch rảnh</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost btn-sm" onClick={downloadTemplate}><Icon name="file" size={14} />Tải mẫu CSV</button>
            <label className="btn btn-ghost btn-sm" style={{ cursor: 'pointer' }}>
              <Icon name="plus" size={14} />Chọn file .csv
              <input type="file" accept=".csv,text/csv,text/plain" style={{ display: 'none' }} onChange={onFile} />
            </label>
          </div>
        </div>
        <textarea
          value={text} onChange={(e) => setText(e.target.value)}
          placeholder={'Mỗi dòng: Ngày  Bắt đầu  Kết thúc\nVD:\n2026-06-22\t09:00\t10:00\n22/06/2026, 10h30, 11h30'}
          style={{ ...inp, minHeight: 120, resize: 'vertical', fontFamily: 'var(--mono, monospace)', fontSize: 12.5, whiteSpace: 'pre' }} />
        <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>
          Hỗ trợ ngày <b>YYYY-MM-DD</b> hoặc <b>DD/MM/YYYY</b>; giờ <b>HH:MM</b>, <b>9h30</b> hoặc <b>9.5</b>. Cột cách nhau bằng Tab, dấu phẩy hoặc chấm phẩy.
        </div>

        {rows.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div className="between" style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 12.5, fontWeight: 700 }}>Xem trước</span>
              <span style={{ fontSize: 12.5 }}>
                <span style={{ color: 'var(--green-700, #15803d)', fontWeight: 700 }}>{valid.length} hợp lệ</span>
                {invalid.length > 0 && <span style={{ color: 'var(--red-700)', fontWeight: 700, marginLeft: 10 }}>{invalid.length} lỗi</span>}
              </span>
            </div>
            <div className="tbl-wrap" style={{ border: '1px solid var(--border)', borderRadius: 10, maxHeight: 220, overflowY: 'auto' }}>
              <table className="tbl">
                <thead><tr><th>#</th><th>Ngày</th><th>Bắt đầu</th><th>Kết thúc</th><th>Trạng thái</th></tr></thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i} style={r.error ? { background: 'var(--red-50)' } : undefined}>
                      <td className="muted mono">{i + 1}</td>
                      <td className="mono">{r.date || <span className="muted">—</span>}</td>
                      <td className="mono">{r.startHour != null ? fmtHour(r.startHour) : <span className="muted">—</span>}</td>
                      <td className="mono">{r.endHour != null ? fmtHour(r.endHour) : <span className="muted">—</span>}</td>
                      <td style={{ fontSize: 12 }}>
                        {r.error
                          ? <span style={{ color: 'var(--red-700)' }}><Icon name="x" size={13} /> {r.error}</span>
                          : <span style={{ color: 'var(--green-700, #15803d)' }}><Icon name="check" size={13} /> OK</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || valid.length === 0}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang import…' : `Import ${valid.length} slot`}
        </button>
      </div>
    </Modal>
  );
}
