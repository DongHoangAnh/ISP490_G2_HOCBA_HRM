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
import { fetchWorkdays, addWorkdays, updateWorkday, deleteWorkday } from '../../api/timeoff';
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
  const [err, setErr] = useState(null);         // lỗi action (thêm/sửa/xoá)
  const [editing, setEditing] = useState(null); // { id, date, name } đang sửa
  const { data, err: loadErr, loading, setData } = useFetch(
    () => fetchWorkdays(year), [year], `timeoff:workdays:${year}`);

  useEffect(() => { setStaging([]); setEditing(null); }, [year]);

  const existing = new Set((data?.workDays || []).map((d) => d.date));
  // Ngày sớm nhất còn thao tác được = ngày mai (BE trả về; model chặn thật).
  // Ngày đã đến/đã qua bị khoá vì chấm công + lương của ngày đó đã tính theo
  // lịch này — xoá đi là sai dữ liệu.
  const minDate = data?.minDate || '';
  const inRange = (iso) => (!minDate || iso >= minDate)
    && Number(iso.slice(0, 4)) === year;

  const addToList = () => {
    setErr(null);
    if (!pick) return;
    if (Number(pick.slice(0, 4)) !== year) { setErr('Ngày phải thuộc năm ' + year + '.'); return; }
    if (minDate && pick < minDate) {
      setErr('Chỉ thêm được ngày chưa đến (từ ' + fmtDate(minDate) + ' trở đi). '
        + 'Ngày đã diễn ra thì chấm công và lương đã tính theo lịch lúc đó.');
      return;
    }
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

  const saveEdit = async () => {
    if (!editing) return;
    if (!inRange(editing.date)) {
      setErr(minDate && editing.date < minDate
        ? 'Chỉ chuyển được sang ngày chưa đến (từ ' + fmtDate(minDate) + ' trở đi).'
        : 'Ngày phải thuộc năm ' + year + '.');
      return;
    }
    setBusy(true); setErr(null);
    try {
      setData(await updateWorkday(editing.id, { date: editing.date, name: editing.name }, year));
      setEditing(null);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
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
            <input type="date" style={inp} value={pick} max={`${year}-12-31`}
              min={minDate && minDate > `${year}-01-01` ? minDate : `${year}-01-01`}
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

        <div className="muted" style={{ fontSize: 12 }}>
          Chỉ thêm / sửa / xoá được ngày <b>chưa đến</b>
          {minDate ? <> (từ {fmtDate(minDate)} trở đi)</> : null}. Ngày đã diễn ra
          bị khoá vì nhân viên đã chấm công và lương đã tính theo lịch đó.
        </div>

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
                    <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', border: '1px solid var(--border)', borderRadius: 9, flexWrap: 'wrap', opacity: d.locked ? 0.72 : 1 }}>
                      {editing?.id === d.id ? (
                        <>
                          <input type="date" style={{ ...inp, padding: '6px 9px' }} value={editing.date}
                            min={minDate && minDate > `${year}-01-01` ? minDate : `${year}-01-01`}
                            max={`${year}-12-31`}
                            onChange={(e) => setEditing((s) => ({ ...s, date: e.target.value }))} />
                          <input type="text" style={{ ...inp, padding: '6px 9px', flex: 1, minWidth: 120 }} value={editing.name}
                            placeholder="Ghi chú"
                            onChange={(e) => setEditing((s) => ({ ...s, name: e.target.value }))} />
                          <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }} disabled={busy} onClick={saveEdit}>
                            <Icon name="checkCircle" size={14} />Lưu</button>
                          <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => { setEditing(null); setErr(null); }}>Huỷ</button>
                        </>
                      ) : (
                        <>
                          <Badge kind={d.locked ? 'gray' : 'green'} dot>{dowOf(d.date)}</Badge>
                          <span className="mono" style={{ fontWeight: 600, fontSize: 13 }}>{fmtDate(d.date)}</span>
                          <span className="muted" style={{ fontSize: 12.5 }}>{d.name}</span>
                          {d.locked ? (
                            <span className="muted" style={{ marginLeft: 'auto', fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 5 }}
                              title="Ngày đã diễn ra — chấm công và lương đã tính theo lịch này nên không sửa/xoá được nữa.">
                              <Icon name="lock" size={13} />Đã diễn ra
                            </span>
                          ) : (
                            <>
                              <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} disabled={busy}
                                onClick={() => { setErr(null); setEditing({ id: d.id, date: d.date, name: d.name || '' }); }}>
                                <Icon name="edit" size={14} />Sửa</button>
                              <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => remove(d.id)}>
                                <Icon name="x" size={14} />Xoá</button>
                            </>
                          )}
                        </>
                      )}
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
