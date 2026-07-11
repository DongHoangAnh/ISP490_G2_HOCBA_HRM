/* Form chấm đợt đánh giá thăng tiến — chỉ người quản lý. Owner: Tân. */
import { useState, useMemo } from 'react';
import { saveEvaluation } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';

const TODAY = new Date().toISOString().slice(0, 10);
const VERDICTS = [
  ['qualified', 'Đủ điều kiện'], ['consider', 'Cân nhắc'], ['not_yet', 'Chưa đủ'],
];

function autoVerdict(pct) {
  if (pct >= 80) return 'qualified';
  if (pct >= 60) return 'consider';
  return 'not_yet';
}

export default function EvaluationForm({ empId, criteria, onClose, onSaved }) {
  const [date, setDate] = useState(TODAY);
  const [scores, setScores] = useState(() =>
    Object.fromEntries(criteria.map((c) => [c.id, 0])));
  const [notes, setNotes] = useState({});
  const [verdictFinal, setVerdictFinal] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const pct = useMemo(() => {
    const wsum = criteria.reduce((s, c) => s + c.weight, 0);
    if (!wsum) return 0;
    const acc = criteria.reduce(
      (s, c) => s + (scores[c.id] / c.maxScore) * c.weight, 0);
    return Math.round((acc / wsum) * 1000) / 10;
  }, [scores, criteria]);

  const submit = async (confirm) => {
    setErr(null);
    if (confirm && !verdictFinal) { setErr('Chọn kết luận trước khi xác nhận.'); return; }
    setBusy(true);
    try {
      const data = await saveEvaluation({
        employeeId: empId, date, verdictFinal, note, confirm,
        lines: criteria.map((c) => ({
          criteriaId: c.id, score: scores[c.id], note: notes[c.id] || '' })),
      });
      onSaved(data);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head">
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Đợt đánh giá thăng tiến</h2>
          <div className="muted" style={{ fontSize: 12.5 }}>Chấm theo tiêu chí · gợi ý theo ngưỡng</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '18px 24px' }}>
        <label style={{ fontSize: 12, fontWeight: 700 }}>Ngày đánh giá&nbsp;
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
        <div style={{ marginTop: 14 }}>
          {criteria.map((c) => (
            <div key={c.id} style={{ marginBottom: 12 }}>
              <div className="between">
                <span style={{ fontWeight: 600, fontSize: 13 }}>{c.name} <span className="muted">· w{c.weight}</span></span>
                <span style={{ fontWeight: 700 }}>{scores[c.id]}/{c.maxScore}</span>
              </div>
              <input type="range" min="0" max={c.maxScore} step="1"
                value={scores[c.id]} style={{ width: '100%' }}
                onChange={(e) => setScores((p) => ({ ...p, [c.id]: Number(e.target.value) }))} />
            </div>
          ))}
        </div>
        <div className="between" style={{ marginTop: 8, padding: '10px 0', borderTop: '1px solid var(--border)' }}>
          <span style={{ fontWeight: 700 }}>Tổng điểm</span>
          <span style={{ fontWeight: 800, fontSize: 20, color: 'var(--red-700)' }}>{pct}% · {VERDICTS.find((v) => v[0] === autoVerdict(pct))[1]}</span>
        </div>
        <label style={{ display: 'block', marginTop: 10, fontSize: 12, fontWeight: 700 }}>Kết luận
          <select value={verdictFinal} onChange={(e) => setVerdictFinal(e.target.value)} style={{ width: '100%' }}>
            <option value="">— Chọn —</option>
            {VERDICTS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </label>
        <label style={{ display: 'block', marginTop: 10, fontSize: 12, fontWeight: 700 }}>Nhận xét
          <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} style={{ width: '100%' }} />
        </label>
        {err && <div style={{ marginTop: 12, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-soft" onClick={() => submit(false)} disabled={busy}>Lưu nháp</button>
        <button className="btn btn-primary" onClick={() => submit(true)} disabled={busy}>
          <Icon name="checkCircle" size={16} />Xác nhận</button>
      </div>
    </Modal>
  );
}
