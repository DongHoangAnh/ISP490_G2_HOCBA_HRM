/* Tab "Danh sách PV" — lịch rảnh phỏng vấn theo tuần. Owner: Việt.
   HR/BP tạo slot rảnh; xem lịch PV theo ngày/giờ. Spec §5e. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchInterviewSlots, deleteInterviewSlot, bookInterviewSlot, unbookInterviewSlot, fetchCvList, updateApplicant, fetchMailTemplates } from '../../api/recruitment';
import { ATTENDANCE_KIND, INTERVIEW_RESULT_KIND } from './util';
import Modal from '../../components/Modal';
import SlotForm from './SlotForm';
import SlotImport from './SlotImport';
import MailSendModal from './MailSendModal';

const INTERVIEW_STAGE = 'Phỏng vấn';

const DOW = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const mondayOf = (d) => { const x = new Date(d); const w = (x.getDay() + 6) % 7; return addDays(x, -w); };
const ddmm = (s) => { const [, m, dd] = s.split('-'); return `${dd}/${m}`; };

export default function InterviewSlots() {
  const [anchor, setAnchor] = useState(() => new Date());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(null); // null | defaultDate
  const [importing, setImporting] = useState(false);
  const [booking, setBooking] = useState(null); // null | slot đang đặt UV
  const [cv, setCv] = useState(null); // danh sách CV (để lọc ứng viên đang phỏng vấn)
  const [tmpls, setTmpls] = useState(null); // mail mẫu (cho nút Gửi mail)

  const weekStart = mondayOf(anchor);
  const weekDates = Array.from({ length: 7 }, (_, i) => ymd(addDays(weekStart, i)));
  const todayYmd = ymd(new Date());

  const load = () => {
    setErr(null); setData(null);
    fetchInterviewSlots(weekDates[0], weekDates[6]).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [weekDates[0]]);

  // Danh sách ứng viên đang ở bước Phỏng vấn — tải 1 lần, độc lập với tuần.
  useEffect(() => { fetchCvList().then(setCv).catch(() => setCv({ rows: [], attendanceLabels: {} })); }, []);
  useEffect(() => { fetchMailTemplates().then(setTmpls).catch(() => setTmpls({ rows: [] })); }, []);

  const removeSlot = async (id) => {
    if (!window.confirm('Xoá slot lịch rảnh này?')) return;
    try { await deleteInterviewSlot(id); load(); } catch (e) { alert(e.message); }
  };

  // Đặt slot lại về Rảnh; lịch PV đã ghi trên hồ sơ ứng viên vẫn giữ nguyên.
  const unbookSlot = async (id) => {
    if (!window.confirm('Hủy đặt slot này (trả về Rảnh)?')) return;
    try { await unbookInterviewSlot(id); load(); fetchCvList().then(setCv).catch(() => {}); }
    catch (e) { alert(e.message); }
  };

  // Sau khi đặt UV: refresh cả lịch (slot → Đã đặt) lẫn danh sách CV (ngày/giờ PV mới).
  const afterBook = () => { setBooking(null); load(); fetchCvList().then(setCv).catch(() => {}); };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải lịch phỏng vấn…" />;

  const { rows, canManage, interviewers, meId } = data;
  const total = rows.length;
  const booked = rows.filter((r) => r.state === 'booked').length;

  return (
    <div>
      <div className="filterbar" style={{ alignItems: 'center' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => setAnchor(addDays(weekStart, -7))}>
          <Icon name="chevR" size={15} className="faint" style={{ transform: 'rotate(180deg)' }} />Tuần trước</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setAnchor(new Date())}>Tuần này</button>
        <button className="btn btn-ghost btn-sm" onClick={() => setAnchor(addDays(weekStart, 7))}>
          Tuần sau<Icon name="chevR" size={15} className="faint" /></button>
        <span style={{ fontWeight: 700, fontSize: 13.5, marginLeft: 6 }}>
          {ddmm(weekDates[0])} – {ddmm(weekDates[6])}/{weekDates[6].split('-')[0]}</span>
        <span className="muted" style={{ fontSize: 12.5, marginLeft: 8 }}>{total} slot · {booked} đã đặt</span>
        {canManage && (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 9 }}>
            <button className="btn btn-soft" onClick={() => setImporting(true)}>
              <Icon name="file" size={16} />Import lịch tuần</button>
            <button className="btn btn-primary" onClick={() => setCreating(todayYmd)}>
              <Icon name="plus" size={16} />Thêm lịch rảnh PV</button>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 8 }}>
        {weekDates.map((dstr, i) => {
          const daySlots = rows.filter((r) => r.date === dstr).sort((a, b) => a.startTime.localeCompare(b.startTime));
          const isToday = dstr === todayYmd;
          return (
            <div key={dstr} style={{ background: 'var(--surface-2)', border: '1px solid ' + (isToday ? 'var(--red-600)' : 'var(--border)'), borderRadius: 12, padding: 8, minHeight: 120 }}>
              <div className="between" style={{ marginBottom: 8, padding: '2px 2px' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 12.5 }}>{DOW[i]}</div>
                  <div className="muted" style={{ fontSize: 11 }}>{ddmm(dstr)}</div>
                </div>
                {canManage && (
                  <button className="icon-btn" title="Thêm slot ngày này" onClick={() => setCreating(dstr)}>
                    <Icon name="plus" size={15} className="faint" /></button>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {daySlots.length === 0 && <div className="muted" style={{ fontSize: 11, textAlign: 'center', padding: '8px 0' }}>—</div>}
                {daySlots.map((s) => (
                  <div key={s.id} className="card" style={{ padding: 8 }}>
                    <div className="between">
                      <span className="mono" style={{ fontWeight: 700, fontSize: 12 }}>{s.startTime}–{s.endTime}</span>
                      <Badge kind={s.state === 'booked' ? 'blue' : 'green'}>{s.state === 'booked' ? 'Đã đặt' : 'Rảnh'}</Badge>
                    </div>
                    <div className="muted" style={{ fontSize: 11.5, marginTop: 3 }}>{s.interviewer}</div>
                    {s.applicant && <div style={{ fontSize: 11.5, marginTop: 2, fontWeight: 600 }}>UV: {s.applicant}</div>}
                    {canManage && (
                      <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                        {s.state === 'booked' ? (
                          <button className="btn btn-ghost btn-sm" style={{ padding: '2px 7px', fontSize: 11 }} onClick={() => unbookSlot(s.id)}>
                            <Icon name="x" size={12} />Hủy đặt</button>
                        ) : (
                          <>
                            <button className="btn btn-soft btn-sm" style={{ padding: '2px 7px', fontSize: 11 }} onClick={() => setBooking(s)}>
                              <Icon name="user" size={12} />Đặt UV</button>
                            <button className="icon-btn" title="Xoá" onClick={() => removeSlot(s.id)}>
                              <Icon name="trash" size={14} className="faint" /></button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <InterviewApplicants cv={cv} setCv={setCv} templates={(tmpls && tmpls.rows) || []} />

      {creating && (
        <SlotForm interviewers={interviewers} meId={meId} weekDates={weekDates} defaultDate={creating}
          onClose={() => setCreating(null)}
          onSaved={() => { setCreating(null); load(); }} />
      )}
      {importing && (
        <SlotImport interviewers={interviewers} meId={meId}
          onClose={() => setImporting(false)}
          onSaved={() => { setImporting(false); load(); }} />
      )}
      {booking && (
        <SlotBookModal slot={booking} candidates={(cv && cv.rows) || []}
          onClose={() => setBooking(null)} onBooked={afterBook} />
      )}
    </div>
  );
}

/* Modal chọn ứng viên để đặt vào 1 slot rảnh. Đặt xong: slot -> Đã đặt và lịch PV
   (ngày/giờ/người PV) tự điền lên hồ sơ ứng viên. */
function SlotBookModal({ slot, candidates, onClose, onBooked }) {
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const list = candidates.filter((c) => {
    if (!q) return true;
    const s = q.toLowerCase();
    return [c.name, c.phone, c.email, c.jobName].some((v) => (v || '').toLowerCase().includes(s));
  });

  const book = async (aid) => {
    setBusy(true); setErr(null);
    try { await bookInterviewSlot(slot.id, aid); onBooked(); }
    catch (e) { setErr(e.message || 'Không đặt được lịch.'); setBusy(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="calendar" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Đặt lịch phỏng vấn</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {ddmm(slot.date)}/{slot.date.split('-')[0]} · {slot.startTime}–{slot.endTime} · {slot.interviewer}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '16px 22px' }}>
        <input type="text" autoFocus placeholder="Tìm ứng viên theo tên / SĐT / email / vị trí…"
          value={q} onChange={(e) => setQ(e.target.value)}
          style={{ width: '100%', padding: '8px 11px', borderRadius: 9, border: '1px solid var(--border-strong)', fontSize: 13, outline: 'none', boxSizing: 'border-box' }} />
        {err && <div style={{ color: 'var(--red-600)', fontSize: 12.5, marginTop: 8 }}>{err}</div>}
        <div style={{ marginTop: 12, maxHeight: '46vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {list.length === 0 && <EmptyState>Không có ứng viên phù hợp.</EmptyState>}
          {list.map((c) => (
            <div key={c.id} className="card between" style={{ padding: '9px 12px', alignItems: 'center' }}>
              <div style={{ minWidth: 0 }}>
                <div className="nm" style={{ fontWeight: 600 }}>{c.name || '—'}</div>
                <div className="id muted" style={{ fontSize: 12 }}>
                  {[c.jobName, c.phone, c.stage].filter(Boolean).join(' · ') || '—'}</div>
              </div>
              <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => book(c.id)}>Chọn</button>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  );
}

/* Danh sách ứng viên đang ở trạng thái "Phỏng vấn" (Sheet 7.1 bước 6).
   Recruiter chỉnh trực tiếp Ngày/Giờ/Người PV/Có mặt + gửi mail tại bảng. */
function InterviewApplicants({ cv, setCv, templates }) {
  const [savingId, setSavingId] = useState(null);
  const [mailFor, setMailFor] = useState(null);
  const isRecruiter = cv?.isRecruiter;

  // Lưu 1 trường rồi cập nhật dòng vào state (không refetch).
  const saveField = async (id, patch) => {
    setSavingId(id);
    try {
      const det = await updateApplicant(id, patch);
      setCv((p) => ({ ...p, rows: p.rows.map((r) => (r.id === id ? det : r)) }));
    } catch (e) {
      alert(e.message || 'Không lưu được thay đổi.');
    } finally {
      setSavingId(null);
    }
  };

  const cell = {
    padding: '6px 9px', borderRadius: 8, border: '1px solid var(--border-strong)',
    background: '#fff', fontSize: 12.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
  };

  return (
    <div style={{ marginTop: 22 }}>
      <div className="between" style={{ marginBottom: 10 }}>
        <h2 style={{ fontSize: 15.5, fontWeight: 800, margin: 0 }}>Ứng viên đang phỏng vấn</h2>
        {cv && (
          <span className="muted" style={{ fontSize: 12.5 }}>
            {cv.rows.filter((r) => r.stage === INTERVIEW_STAGE).length} ứng viên
          </span>
        )}
      </div>

      {!cv ? (
        <LoadingState label="Đang tải danh sách ứng viên…" />
      ) : (() => {
        const rows = cv.rows
          .filter((r) => r.stage === INTERVIEW_STAGE)
          .sort((a, b) => (b.interviewDate || '').localeCompare(a.interviewDate || ''));
        if (rows.length === 0)
          return <EmptyState>Chưa có ứng viên nào ở bước phỏng vấn.</EmptyState>;
        const attLabels = cv.attendanceLabels || {};
        const resLabels = cv.interviewResultLabels || {};
        const jobs = cv.jobs || [];
        return (
          <div className="card">
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr>
                  <th>Họ tên ứng viên</th><th>Vị trí ứng tuyển</th><th>Ngày PV</th><th>Giờ</th>
                  <th>Người PV</th><th>Tham gia PV</th><th>Kết quả PV</th><th></th>
                </tr></thead>
                <tbody>
                  {rows.map((r) => {
                    const busy = savingId === r.id;
                    return (
                    <tr key={r.id}>
                      <td>
                        <div className="nm">{r.name || '—'}</div>
                        <div className="id">{[r.phone, r.email].filter(Boolean).join(' · ') || '—'}</div>
                      </td>
                      <td>
                        {isRecruiter ? (
                          <select value={r.jobId || ''} disabled={busy}
                            onChange={(e) => saveField(r.id, { jobId: e.target.value })}
                            style={{ ...cell, width: 170, opacity: busy ? 0.6 : 1 }}>
                            <option value="">— Chưa gán —</option>
                            {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
                          </select>
                        ) : (r.jobName || '—')}
                      </td>
                      <td>
                        {isRecruiter ? (
                          <input type="date" value={r.interviewDate ? r.interviewDate.slice(0, 10) : ''}
                            disabled={busy} onChange={(e) => saveField(r.id, { interviewDate: e.target.value || '' })}
                            style={{ ...cell, width: 150, opacity: busy ? 0.6 : 1 }} />
                        ) : (
                          <span className="muted mono">{r.interviewDate ? fmtDate(r.interviewDate) : '—'}</span>
                        )}
                      </td>
                      <td>
                        {isRecruiter ? (
                          <input type="text" defaultValue={r.interviewTime || ''} placeholder="VD: 10h30"
                            disabled={busy}
                            onBlur={(e) => { if ((e.target.value || '') !== (r.interviewTime || '')) saveField(r.id, { interviewTime: e.target.value }); }}
                            style={{ ...cell, width: 90, opacity: busy ? 0.6 : 1 }} />
                        ) : (
                          <span className="muted mono">{r.interviewTime || '—'}</span>
                        )}
                      </td>
                      <td>
                        {isRecruiter ? (
                          <input type="text" defaultValue={r.interviewer || ''} placeholder="VD: DungLt"
                            disabled={busy}
                            onBlur={(e) => { if ((e.target.value || '') !== (r.interviewer || '')) saveField(r.id, { interviewer: e.target.value }); }}
                            style={{ ...cell, width: 130, opacity: busy ? 0.6 : 1 }} />
                        ) : (
                          <span className="muted">{r.interviewer || '—'}</span>
                        )}
                      </td>
                      <td>
                        {isRecruiter ? (
                          <select value={r.attendanceStatus || ''} disabled={busy}
                            onChange={(e) => saveField(r.id, { attendanceStatus: e.target.value })}
                            style={{ ...cell, width: 120, opacity: busy ? 0.6 : 1 }}>
                            <option value="">— Chưa ghi nhận —</option>
                            {Object.entries(attLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                          </select>
                        ) : (r.attendanceStatus
                          ? <Badge kind={ATTENDANCE_KIND[r.attendanceStatus] || 'gray'}>{attLabels[r.attendanceStatus] || r.attendanceStatus}</Badge>
                          : <span className="muted">—</span>)}
                      </td>
                      <td>
                        {isRecruiter ? (
                          <select value={r.interviewResult || ''} disabled={busy}
                            onChange={(e) => saveField(r.id, { interviewResult: e.target.value })}
                            style={{ ...cell, width: 120, opacity: busy ? 0.6 : 1 }}>
                            <option value="">— Chưa có —</option>
                            {Object.entries(resLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                          </select>
                        ) : (r.interviewResult
                          ? <Badge kind={INTERVIEW_RESULT_KIND[r.interviewResult] || 'gray'}>{resLabels[r.interviewResult] || r.interviewResult}</Badge>
                          : <span className="muted">—</span>)}
                      </td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button className="btn btn-primary btn-sm" onClick={() => setMailFor(r)}>
                          <Icon name="mail" size={14} />Gửi mail</button>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })()}

      {mailFor && (
        <MailSendModal applicant={mailFor} templates={templates} onClose={() => setMailFor(null)} />
      )}
    </div>
  );
}
