/* Modal "Thêm lịch làm việc" (chỉ HR/Admin).
   Công ty làm Thứ 2–Thứ 6; HR thêm các ngày Thứ 7 (hoặc ngày khác) đi làm.
   Owner: Nhật Anh. */
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ModalHeader from '../../components/ModalHeader';
import { LoadingState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchWorkdays, addWorkdays, deleteWorkday } from '../../api/timeoff';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';

const DOW = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];

const inp = {
  padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

const dowOf = (iso) => { const [y, m, d] = iso.split('-').map(Number); return DOW[new Date(y, m - 1, d).getDay()]; };

export default function WorkScheduleModal({ onClose }) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [staging, setStaging] = useState([]);   // các ngày chờ lưu
  const [pick, setPick] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);         // lỗi action (thêm/xoá)
  const { data, err: loadErr, loading, setData } = useFetch(
    () => fetchWorkdays(year), [year], `timeoff:workdays:${year}`);

  useEffect(() => { setStaging([]); }, [year]);

  const existing = new Set((data?.workDays || []).map((d) => d.date));

  const addToList = () => {
    setErr(null);
    if (!pick) return;
    if (Number(pick.slice(0, 4)) !== year) { setErr('Ngày phải thuộc năm ' + year + '.'); return; }
    if (existing.has(pick) || staging.includes(pick)) { setErr('Ngày này đã có trong lịch.'); return; }
    setStaging((s) => [...s, pick].sort());
    setPick('');
  };

  const save = async () => {
    if (!staging.length) return;
    setBusy(true); setErr(null);
    try {
      const res = await addWorkdays(staging, note.trim(), year);
      setData(res); setStaging([]); setNote('');
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  const remove = async (id) => {
    setBusy(true); setErr(null);
    try { setData(await deleteWorkday(id, year)); }
    catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="calendar" title="Thêm lịch làm việc"
        sub="Công ty làm Thứ 2 – Thứ 6 · thêm các ngày Thứ 7 đi làm" onClose={onClose} />

      <div style={{ padding: '20px 24px', maxHeight: '62vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Năm */}
        <YearNav year={year} onChange={setYear} disabled={busy} />

        {/* Thêm ngày */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Ngày đi làm</span>
            <input type="date" style={inp} value={pick} min={`${year}-01-01`} max={`${year}-12-31`}
              onChange={(e) => setPick(e.target.value)} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 140 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Ghi chú</span>
            <input type="text" style={inp} value={note} placeholder="VD: Làm bù"
              onChange={(e) => setNote(e.target.value)} />
          </label>
          <button className="btn btn-ghost" onClick={addToList} disabled={!pick}>
            <Icon name="plus" size={16} />Thêm vào danh sách</button>
        </div>

        {pick && dowOf(pick) !== 'Thứ 7' && (
          <div className="muted" style={{ fontSize: 12 }}>Lưu ý: {dowOf(pick)} không phải Thứ 7.</div>
        )}

        {/* Danh sách chờ lưu */}
        {staging.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>Chờ lưu ({staging.length})</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {staging.map((d) => (
                <span key={d} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 10px', borderRadius: 999, background: 'var(--surface-2)', fontSize: 12.5 }}>
                  {dowOf(d)} · {fmtDate(d)}
                  <button className="icon-btn" style={{ width: 18, height: 18 }} onClick={() => setStaging((s) => s.filter((x) => x !== d))}>
                    <Icon name="x" size={13} /></button>
                </span>
              ))}
            </div>
            <div>
              <button className="btn btn-primary" onClick={save} disabled={busy}>
                <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : `Lưu ${staging.length} ngày`}</button>
            </div>
          </div>
        )}

        {(err || loadErr) && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err || loadErr}</div>
        )}

        {/* Danh sách ngày đã có */}
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', marginBottom: 8 }}>Ngày đi làm trong năm {year}</div>
          {loading || !data ? <LoadingState label="Đang tải…" /> : (
            data.workDays.length === 0
              ? <div className="muted" style={{ fontSize: 13 }}>Chưa có ngày đi làm thêm nào.</div>
              : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {data.workDays.map((d) => (
                    <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', border: '1px solid var(--border)', borderRadius: 9 }}>
                      <Badge kind="green" dot>{dowOf(d.date)}</Badge>
                      <span className="mono" style={{ fontWeight: 600, fontSize: 13 }}>{fmtDate(d.date)}</span>
                      <span className="muted" style={{ fontSize: 12.5 }}>{d.name}</span>
                      <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} disabled={busy} onClick={() => remove(d.id)}>
                        <Icon name="x" size={14} />Xoá</button>
                    </div>
                  ))}
                </div>
              )
          )}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
