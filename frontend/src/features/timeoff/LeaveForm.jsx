/* Form tạo đơn nghỉ (modal). Owner: Nhật Anh. Spec §3.3 + §8 + nghỉ-theo-buổi (GV).
   - Nhân viên thường: form nghỉ theo KHOẢNG NGÀY (RangeLeaveBody).
   - Giáo viên: mặc định nghỉ theo BUỔI dạy (SessionLeaveBody) + lối phụ nghỉ dài ngày. */
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { createRequest, fetchTeachingConflicts, fetchMyTeachingSessions } from '../../api/timeoff';

const ALLOWED_MIME = ['application/pdf', 'image/jpeg', 'image/png'];
const MAX_SIZE = 5 * 1024 * 1024;

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

/* File → base64 (bỏ tiền tố data:...;base64,). */
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(',')[1] || '');
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

export default function LeaveForm({ leaveTypes, isTeacher, onClose, onSaved }) {
  // GV mặc định nghỉ theo buổi; 'range' là lối phụ nghỉ dài ngày.
  const [mode, setMode] = useState(isTeacher ? 'sessions' : 'range');

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="calendar" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>Tạo đơn nghỉ</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isTeacher && mode === 'sessions'
              ? 'Chọn buổi dạy bạn muốn nghỉ — xử lý lớp cho từng buổi'
              : 'Gửi đơn xin nghỉ để quản lý phê duyệt'}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {isTeacher && (
        <div style={{ display: 'flex', gap: 8, padding: '14px 24px 0' }}>
          {[['sessions', 'Nghỉ buổi dạy'], ['range', 'Nghỉ dài ngày']].map(([v, l]) => (
            <button key={v} type="button" onClick={() => setMode(v)}
              style={{
                flex: 1, padding: '9px 12px', borderRadius: 10, fontSize: 13, fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
                border: '1px solid ' + (mode === v ? 'var(--red-600)' : 'var(--border-strong)'),
                background: mode === v ? 'var(--red-50)' : '#fff',
                color: mode === v ? 'var(--red-700)' : 'var(--ink)',
              }}>{l}</button>
          ))}
        </div>
      )}

      {mode === 'sessions'
        ? <SessionLeaveBody onClose={onClose} onSaved={onSaved} />
        : <RangeLeaveBody leaveTypes={leaveTypes} isTeacher={isTeacher} onClose={onClose} onSaved={onSaved} />}
    </Modal>
  );
}

/* ============================================================
   Chế độ A — Nghỉ theo BUỔI dạy (giáo viên). Chọn buổi → xử lý từng buổi.
   ============================================================ */
function SessionLeaveBody({ onClose, onSaved }) {
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [subs, setSubs] = useState([]);
  const [sel, setSel] = useState({});   // { [sessionId]: {checked, type, substituteId} }
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    fetchMyTeachingSessions()
      .then((d) => { if (alive) { setSessions(d.sessions || []); setSubs(d.substitutes || []); } })
      .catch((e) => { if (alive) setErr(e.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const patch = (sid, p) => setSel((m) => ({ ...m, [sid]: { ...m[sid], ...p } }));

  const chosen = sessions.filter((s) => sel[s.sessionId]?.checked);
  const valid = chosen.length > 0 && chosen.every((s) => {
    const r = sel[s.sessionId];
    return r.type && (r.type !== 'substitute' || r.substituteId);
  });

  // Nhóm buổi theo ngày để hiển thị.
  const byDate = [];
  sessions.forEach((s) => {
    let g = byDate.find((x) => x.date === s.date);
    if (!g) { g = { date: s.date, rows: [] }; byDate.push(g); }
    g.rows.push(s);
  });

  const submit = async () => {
    setErr(null);
    if (!valid) { setErr('Hãy chọn ít nhất 1 buổi và xử lý đầy đủ từng buổi.'); return; }
    const resolutions = chosen.map((s) => {
      const r = sel[s.sessionId];
      return {
        sessionId: s.sessionId, type: r.type,
        substituteId: r.type === 'substitute' ? Number(r.substituteId) : undefined,
      };
    });
    setBusy(true);
    try {
      const payload = await createRequest({ scope: 'sessions', reason: reason.trim(), resolutions });
      onSaved(payload);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <>
      <div style={{ padding: '18px 24px', maxHeight: '54vh', overflowY: 'auto', display: 'grid', gap: 12 }}>
        {loading ? (
          <LoadingState label="Đang tải lịch dạy sắp tới…" />
        ) : sessions.length === 0 ? (
          <div style={{ padding: '14px', textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
            Không có buổi dạy nào sắp tới (4 tuần tới). Không cần xin nghỉ buổi dạy.
          </div>
        ) : (
          <>
            <div className="muted" style={{ fontSize: 12.5 }}>
              Tick buổi bạn muốn nghỉ, rồi chọn <b>Cả lớp nghỉ</b> hoặc <b>Đổi GV dạy thay</b> cho từng buổi.
            </div>
            {byDate.map((g) => (
              <div key={g.date} style={{ display: 'grid', gap: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
                  {fmtDate(g.date)}
                </div>
                {g.rows.map((s) => {
                  const r = sel[s.sessionId] || {};
                  return (
                    <div key={s.sessionId} style={{ border: '1px solid ' + (r.checked ? 'var(--red-600)' : 'var(--border-strong)'), borderRadius: 10, padding: 11, display: 'grid', gap: 8 }}>
                      <label style={{ display: 'flex', gap: 9, alignItems: 'center', cursor: 'pointer' }}>
                        <input type="checkbox" checked={!!r.checked}
                          onChange={() => patch(s.sessionId, { checked: !r.checked })} />
                        <span style={{ fontWeight: 700, fontSize: 13.5 }}>
                          {s.className || '(Lớp chưa đặt tên)'}
                          <span className="muted" style={{ fontWeight: 500, fontSize: 12.5 }}>
                            {' · '}{s.startTime}–{s.endTime}
                          </span>
                        </span>
                      </label>
                      {r.checked && (
                        <div style={{ display: 'grid', gap: 8, paddingLeft: 26 }}>
                          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {[['class_off', 'Cả lớp cùng nghỉ'], ['substitute', 'Đổi GV dạy thay']].map(([v, l]) => (
                              <button key={v} type="button" onClick={() => patch(s.sessionId, { type: v })}
                                style={{
                                  flex: 1, minWidth: 140, padding: '7px 11px', borderRadius: 9, fontSize: 12.5, fontWeight: 600,
                                  cursor: 'pointer', fontFamily: 'inherit',
                                  border: '1px solid ' + (r.type === v ? 'var(--red-600)' : 'var(--border-strong)'),
                                  background: r.type === v ? 'var(--red-50)' : '#fff',
                                  color: r.type === v ? 'var(--red-700)' : 'var(--ink)',
                                }}>{l}</button>
                            ))}
                          </div>
                          {r.type === 'substitute' && (
                            <select style={inp} value={r.substituteId || ''}
                              onChange={(e) => patch(s.sessionId, { substituteId: e.target.value })}>
                              <option value="">— Chọn giáo viên dạy thay —</option>
                              {subs.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                            </select>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}

            <Field label="Lý do" full>
              <textarea style={{ ...inp, resize: 'vertical' }} rows={2} value={reason}
                onChange={(e) => setReason(e.target.value)} placeholder="Nhập lý do nghỉ…" />
            </Field>
          </>
        )}

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <span className="muted" style={{ fontSize: 12.5 }}>
          {chosen.length > 0 ? `Đã chọn ${chosen.length} buổi` : 'Chưa chọn buổi nào'}
        </span>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button className="btn btn-primary" onClick={submit} disabled={busy || !valid}>
            <Icon name="checkCircle" size={16} />{busy ? 'Đang gửi…' : 'Gửi đơn'}</button>
        </div>
      </div>
    </>
  );
}

/* ============================================================
   Chế độ B — Nghỉ theo KHOẢNG NGÀY (nhân viên thường / GV nghỉ dài ngày).
   ============================================================ */
function RangeLeaveBody({ leaveTypes, isTeacher, onClose, onSaved }) {
  const [typeId, setTypeId] = useState(leaveTypes[0]?.id || '');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [span, setSpan] = useState('day'); // 'day' | 'am' | 'pm'
  const [reason, setReason] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  // Xử lý buổi dạy trùng (chỉ giáo viên). res: { [sessionId]: {type, substituteId} }
  const [conflicts, setConflicts] = useState([]);
  const [subs, setSubs] = useState([]);
  const [res, setRes] = useState({});
  const [checking, setChecking] = useState(false);

  const type = leaveTypes.find((t) => t.id === Number(typeId));
  const needDoc = !!type?.supportDocument;
  const allowHalf = type?.requestUnit === 'half_day';
  const isHalf = allowHalf && span !== 'day';
  const dateFrom = from;
  const dateTo = isHalf ? from : to;
  const rangeReady = !!from && (isHalf || (!!to && to >= from));

  useEffect(() => {
    if (!isTeacher || !rangeReady) { setConflicts([]); setSubs([]); setRes({}); return undefined; }
    let alive = true;
    setChecking(true);
    fetchTeachingConflicts(dateFrom, dateTo)
      .then((d) => {
        if (!alive) return;
        setConflicts(d.conflicts || []);
        setSubs(d.substitutes || []);
        setRes({});
      })
      .catch(() => { if (alive) { setConflicts([]); setSubs([]); } })
      .finally(() => { if (alive) setChecking(false); });
    return () => { alive = false; };
  }, [isTeacher, rangeReady, dateFrom, dateTo]);

  const setResolution = (sid, patch) => setRes((m) => ({ ...m, [sid]: { ...m[sid], ...patch } }));

  const allResolved = conflicts.every((c) => {
    const r = res[c.sessionId];
    if (!r || !r.type) return false;
    if (r.type === 'substitute' && !r.substituteId) return false;
    return true;
  });
  const blockSubmit = conflicts.length > 0 && !allResolved;

  const submit = async () => {
    setErr(null);
    if (!typeId || !from) { setErr('Vui lòng chọn loại nghỉ và ngày bắt đầu.'); return; }
    if (!isHalf && !to) { setErr('Vui lòng chọn khoảng ngày.'); return; }
    if (!isHalf && to < from) { setErr('Ngày kết thúc phải sau ngày bắt đầu.'); return; }
    if (blockSubmit) { setErr('Vui lòng xử lý tất cả buổi dạy bị trùng trước khi gửi đơn.'); return; }

    let attachment = null;
    if (file) {
      if (!ALLOWED_MIME.includes(file.type)) { setErr('Chứng từ chỉ chấp nhận PDF, JPG, PNG.'); return; }
      if (file.size > MAX_SIZE) { setErr('Chứng từ tối đa 5 MB.'); return; }
      attachment = { filename: file.name, mimetype: file.type, data: await fileToBase64(file) };
    }

    const resolutions = conflicts.map((c) => {
      const r = res[c.sessionId];
      return {
        sessionId: c.sessionId, type: r.type,
        substituteId: r.type === 'substitute' ? Number(r.substituteId) : undefined,
      };
    });

    setBusy(true);
    try {
      const payload = await createRequest({
        leaveTypeId: Number(typeId), dateFrom: from,
        dateTo: isHalf ? from : to,
        period: isHalf ? span : undefined,
        reason: reason.trim(), attachment,
        resolutions: resolutions.length ? resolutions : undefined,
      });
      onSaved(payload);
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <>
      <div style={{ padding: '18px 24px', maxHeight: '54vh', overflowY: 'auto', display: 'grid', gap: 14 }}>
        <Field label="Loại nghỉ *" full>
          <select style={inp} value={typeId}
            onChange={(e) => { setTypeId(e.target.value); setSpan('day'); }}>
            {leaveTypes.map((t) => (
              <option key={t.id} value={t.id}>{t.name}{t.isEmergency ? ' (khẩn cấp)' : ''}</option>
            ))}
          </select>
          {type && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 7 }}>
              <Badge kind={type.unpaid ? 'gray' : 'green'} dot>
                {type.unpaid ? 'Không lương' : 'Có lương'}
              </Badge>
              <span className="muted" style={{ fontSize: 12 }}>
                {type.unpaid
                  ? 'Những ngày nghỉ loại này sẽ bị trừ lương.'
                  : type.requiresAllocation
                    ? 'Có lương · trừ vào quỹ phép năm.'
                    : 'Có lương · không trừ quỹ phép năm.'}
              </span>
            </div>
          )}
        </Field>

        {allowHalf && (
          <Field label="Thời lượng" full>
            <div style={{ display: 'flex', gap: 8 }}>
              {[['day', 'Cả ngày'], ['am', 'Sáng'], ['pm', 'Chiều']].map(([v, l]) => (
                <button key={v} type="button" onClick={() => setSpan(v)}
                  style={{
                    flex: 1, padding: '9px 12px', borderRadius: 10, fontSize: 13, fontWeight: 600,
                    cursor: 'pointer', fontFamily: 'inherit',
                    border: '1px solid ' + (span === v ? 'var(--red-600)' : 'var(--border-strong)'),
                    background: span === v ? 'var(--red-50)' : '#fff',
                    color: span === v ? 'var(--red-700)' : 'var(--ink)',
                  }}>{l}</button>
              ))}
            </div>
            {isHalf && (
              <span className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Nghỉ nửa ngày {span === 'am' ? '(buổi sáng)' : '(buổi chiều)'} — chỉ trừ 0,5 ngày.
              </span>
            )}
          </Field>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: isHalf ? '1fr' : '1fr 1fr', gap: 14 }}>
          <Field label={isHalf ? 'Ngày nghỉ *' : 'Từ ngày *'}>
            <input type="date" style={inp} value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
          {!isHalf && (
            <Field label="Đến ngày *">
              <input type="date" style={inp} value={to} onChange={(e) => setTo(e.target.value)} /></Field>
          )}
        </div>

        {isTeacher && rangeReady && (
          <ConflictStep checking={checking} conflicts={conflicts} subs={subs}
            res={res} onSet={setResolution} />
        )}

        <Field label="Lý do" full>
          <textarea style={{ ...inp, resize: 'vertical' }} rows={3} value={reason}
            onChange={(e) => setReason(e.target.value)} placeholder="Nhập lý do nghỉ…" /></Field>

        {needDoc && (
          <Field label="Chứng từ y tế (PDF/JPG/PNG, ≤ 5 MB)" full>
            <input type="file" style={inp} accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setFile(e.target.files[0] || null)} />
            <span className="muted" style={{ fontSize: 12, marginTop: 4 }}>
              Đơn nghỉ ốm cần chứng từ để được duyệt (BR-011).</span>
          </Field>
        )}

        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || blockSubmit}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang gửi…' : 'Gửi đơn'}</button>
      </div>
    </>
  );
}

/* Danh sách buổi dạy trùng (chế độ nghỉ dài ngày) + radio xử lý từng buổi. */
function ConflictStep({ checking, conflicts, subs, res, onSet }) {
  if (checking) {
    return (
      <div style={{ padding: '10px 13px', background: 'var(--surface-2,#f8f9fa)', borderRadius: 10, fontSize: 12.5, color: 'var(--muted)' }}>
        Đang kiểm tra lịch dạy trùng kỳ nghỉ…
      </div>
    );
  }
  if (conflicts.length === 0) {
    return (
      <div style={{ padding: '10px 13px', background: 'var(--green-50,#ecfdf5)', border: '1px solid var(--green-100,#d1fae5)', borderRadius: 10, fontSize: 12.5, color: 'var(--green-700,#047857)' }}>
        ✓ Không có buổi dạy nào trùng kỳ nghỉ này.
      </div>
    );
  }
  return (
    <div style={{ gridColumn: '1 / -1', display: 'grid', gap: 10 }}>
      <div style={{ padding: '10px 13px', background: 'var(--amber-50,#fffbeb)', border: '1px solid var(--amber-100,#fef3c7)', borderRadius: 10, fontSize: 12.5, color: 'var(--amber-700,#b45309)' }}>
        ⚠ Bạn có <b>{conflicts.length}</b> buổi dạy trùng kỳ nghỉ. Hãy chọn cách xử lý cho từng buổi —
        đơn chỉ gửi được khi đã xử lý hết.
      </div>
      {conflicts.map((c) => {
        const r = res[c.sessionId] || {};
        return (
          <div key={c.sessionId} style={{ border: '1px solid var(--border-strong)', borderRadius: 10, padding: 12, display: 'grid', gap: 8 }}>
            <div style={{ fontWeight: 700, fontSize: 13.5 }}>
              {c.className || '(Lớp chưa đặt tên)'}
              <span className="muted" style={{ fontWeight: 500, fontSize: 12.5 }}>
                {' · '}{fmtDate(c.date)} · {c.startTime}–{c.endTime}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {[['class_off', 'Cả lớp cùng nghỉ'], ['substitute', 'Đổi GV dạy thay']].map(([v, l]) => (
                <button key={v} type="button" onClick={() => onSet(c.sessionId, { type: v })}
                  style={{
                    flex: 1, minWidth: 140, padding: '8px 12px', borderRadius: 9, fontSize: 12.5, fontWeight: 600,
                    cursor: 'pointer', fontFamily: 'inherit',
                    border: '1px solid ' + (r.type === v ? 'var(--red-600)' : 'var(--border-strong)'),
                    background: r.type === v ? 'var(--red-50)' : '#fff',
                    color: r.type === v ? 'var(--red-700)' : 'var(--ink)',
                  }}>{l}</button>
              ))}
            </div>
            {r.type === 'substitute' && (
              <select style={inp} value={r.substituteId || ''}
                onChange={(e) => onSet(c.sessionId, { substituteId: e.target.value })}>
                <option value="">— Chọn giáo viên dạy thay —</option>
                {subs.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            )}
          </div>
        );
      })}
    </div>
  );
}
