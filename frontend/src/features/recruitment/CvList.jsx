/* Tab "Danh sách CV" — list + kanban (kéo-thả đổi stage), xem chi tiết, sửa,
   thêm CV thủ công. Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchCvList, changeStage, updateApplicant } from '../../api/recruitment';
import { CV_RESULT_KIND, CALL_STATUS_KIND, INTERVIEW_RESULT_KIND } from './util';
import ApplicantDrawer from './ApplicantDrawer';
import ApplicantForm from './ApplicantForm';

export default function CvList({ search, stageNames }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [cvFilter, setCvFilter] = useState('all');
  const [vmode, setVmode] = useState(() => localStorage.getItem('hocba_cv_vmode') || 'table');
  const [sel, setSel] = useState(null);       // applicant đang xem chi tiết
  const [creating, setCreating] = useState(false);

  const load = () => {
    setErr(null); setData(null);
    fetchCvList().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const setView = (m) => { setVmode(m); localStorage.setItem('hocba_cv_vmode', m); };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải danh sách CV…" />;

  const { rows, cvResultLabels, callStatusLabels, attendanceLabels, interviewResultLabels, stages, jobs, isRecruiter } = data;
  const meta = { stages, jobs, cvResultLabels, callStatusLabels, attendanceLabels, interviewResultLabels };

  // Cập nhật 1 dòng vào state (sau khi tạo/sửa/đổi stage) — không cần refetch.
  const applyRow = (det) => setData((p) => {
    const exists = p.rows.some((r) => r.id === det.id);
    return { ...p, rows: exists ? p.rows.map((r) => (r.id === det.id ? det : r)) : [det, ...p.rows] };
  });


  const matchSearch = (r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return [r.name, r.phone, r.email, r.jobName, r.ctv]
      .some((v) => (v || '').toLowerCase().includes(q));
  };
  const matchCv = (r) => cvFilter === 'all' || (r.cvResult || 'none') === cvFilter;
  // Tập theo stage (tab PV/Offer) — dùng cho cả chip đếm lẫn bảng/kanban.
  const stageRows = stageNames ? rows.filter((r) => stageNames.includes(r.stage)) : rows;
  const filtered = stageRows.filter((r) => matchSearch(r) && matchCv(r));

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (cvFilter === 'all' ? ' active' : '')} onClick={() => setCvFilter('all')}>
          Tất cả <span className="ct">{stageRows.length}</span></button>
        {Object.entries(cvResultLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (cvFilter === k ? ' active' : '')} onClick={() => setCvFilter(k)}>
            {l} <span className="ct">{stageRows.filter((r) => r.cvResult === k).length}</span></button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          {isRecruiter && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm CV</button>
          )}
          <div className="seg">
            <button className={vmode === 'table' ? 'active' : ''} onClick={() => setView('table')}>Danh sách</button>
            <button className={vmode === 'kanban' ? 'active' : ''} onClick={() => setView('kanban')}>Kanban</button>
          </div>
        </div>
      </div>

      {vmode === 'table' ? (
        <TableView rows={filtered} meta={meta} isRecruiter={isRecruiter} onOpen={setSel} onSaved={applyRow} />
      ) : (
        <KanbanView rows={filtered} stages={stages} labels={{ cvResultLabels, callStatusLabels }}
          isRecruiter={isRecruiter} onOpen={setSel} onMoved={applyRow} onError={load} />
      )}

      {sel && (
        <ApplicantDrawer app={sel} meta={meta} isRecruiter={isRecruiter}
          onClose={() => setSel(null)} onChanged={applyRow} />
      )}
      {creating && (
        <ApplicantForm app={null} meta={meta}
          onClose={() => setCreating(false)}
          onSaved={(det) => { setCreating(false); applyRow(det); }} />
      )}
    </div>
  );
}

function ResultBadge({ k, label }) {
  return k ? <Badge kind={CV_RESULT_KIND[k] || 'gray'}>{label}</Badge> : <span className="muted">—</span>;
}
function CallBadge({ k, label }) {
  return k ? <Badge kind={CALL_STATUS_KIND[k] || 'gray'}>{label}</Badge> : <span className="muted">—</span>;
}
function InterviewBadge({ k, label }) {
  return k ? <Badge kind={INTERVIEW_RESULT_KIND[k] || 'gray'}>{label}</Badge>
    : <span className="muted">—</span>;
}

function CvFileCell({ row }) {
  // Ưu tiên file PDF thật đã upload; nếu chưa có thì xét cvLink (URL hoặc tên file).
  if (row.cvFileUrl) {
    return (
      <a href={row.cvFileUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
        style={{ color: 'var(--red-700)', fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}
        title={row.cvFileName}>
        <Icon name="file" size={14} />Xem PDF</a>
    );
  }
  if (row.cvLink && /^https?:\/\//i.test(row.cvLink)) {
    return (
      <a href={row.cvLink} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}
        style={{ color: 'var(--red-700)', fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <Icon name="file" size={14} />{row.cvLink.toLowerCase().endsWith('.pdf') ? 'Xem PDF' : 'Xem CV'}</a>
    );
  }
  if (row.cvLink) {
    return <span className="muted" style={{ fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }} title={row.cvLink}>
      <Icon name="file" size={14} className="faint" />{row.cvLink}</span>;
  }
  return <span className="muted">—</span>;
}

/* Ô nhập inline (giống InterviewApplicants / Offers) — sửa trực tiếp ngoài bảng. */
const cellStyle = {
  padding: '6px 9px', borderRadius: 8, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 12.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function TableView({ rows, meta, isRecruiter, onOpen, onSaved }) {
  const [savingId, setSavingId] = useState(null);
  const { jobs = [], cvResultLabels = {}, interviewResultLabels = {} } = meta || {};

  // Lưu 1 trường rồi cập nhật dòng vào state (không refetch).
  const saveField = async (id, patch) => {
    setSavingId(id);
    try {
      onSaved(await updateApplicant(id, patch));
    } catch (e) {
      alert(e.message || 'Không lưu được thay đổi.');
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="card">
      <div className="tbl-wrap tbl-scroll">
        <table className="tbl">
          <thead><tr>
            <th>Ứng viên</th><th>Vị trí</th><th>Ngày nhận</th><th>CTV</th>
            <th>Lọc CV</th><th>Kết quả PV</th><th>Link CV / File PDF</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => {
              const busy = savingId === r.id;
              const op = busy ? 0.6 : 1;
              return (
              <tr key={r.id}>
                <td>
                  <div className="nm">{r.name || '—'}</div>
                  <div className="id">{[r.phone, r.email].filter(Boolean).join(' · ') || '—'}</div>
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  {isRecruiter ? (
                    <select value={r.jobId || ''} disabled={busy}
                      onChange={(e) => saveField(r.id, { jobId: e.target.value })}
                      style={{ ...cellStyle, width: 170, opacity: op }}>
                      <option value="">— Chưa gán —</option>
                      {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
                    </select>
                  ) : (r.jobName || '—')}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  {isRecruiter ? (
                    <input type="date" value={r.dateReceived ? r.dateReceived.slice(0, 10) : ''}
                      disabled={busy} onChange={(e) => saveField(r.id, { dateReceived: e.target.value || '' })}
                      style={{ ...cellStyle, width: 140, opacity: op }} />
                  ) : (<span className="muted mono">{r.dateReceived ? fmtDate(r.dateReceived) : '—'}</span>)}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  {isRecruiter ? (
                    <input type="text" defaultValue={r.ctv || ''} placeholder="Tên CTV" disabled={busy}
                      onBlur={(e) => { if ((e.target.value || '') !== (r.ctv || '')) saveField(r.id, { ctv: e.target.value }); }}
                      style={{ ...cellStyle, width: 120, opacity: op }} />
                  ) : (r.ctv || <span className="muted">—</span>)}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  {isRecruiter ? (
                    <select value={r.cvResult || ''} disabled={busy}
                      onChange={(e) => saveField(r.id, { cvResult: e.target.value })}
                      style={{ ...cellStyle, width: 130, opacity: op }}>
                      <option value="">— Chưa lọc —</option>
                      {Object.entries(cvResultLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  ) : (<ResultBadge k={r.cvResult} label={cvResultLabels[r.cvResult]} />)}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  {isRecruiter ? (
                    <select value={r.interviewResult || ''} disabled={busy}
                      onChange={(e) => saveField(r.id, { interviewResult: e.target.value })}
                      style={{ ...cellStyle, width: 130, opacity: op }}>
                      <option value="">— Chưa PV —</option>
                      {Object.entries(interviewResultLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  ) : (<InterviewBadge k={r.interviewResult}
                    label={interviewResultLabels[r.interviewResult]} />)}
                </td>
                <td><CvFileCell row={r} /></td>
                <td><button className="icon-btn" title="Xem hồ sơ" onClick={(e) => { e.stopPropagation(); onOpen(r); }}>
                  <Icon name="chevR" size={18} className="faint" /></button></td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <EmptyState>Không tìm thấy CV phù hợp.</EmptyState>}
    </div>
  );
}

function KanbanView({ rows, stages, labels, isRecruiter, onOpen, onMoved, onError }) {
  const [dragId, setDragId] = useState(null);
  const [overStage, setOverStage] = useState(null);

  const drop = async (stageId) => {
    setOverStage(null);
    const id = dragId; setDragId(null);
    if (!id) return;
    const row = rows.find((r) => r.id === id);
    if (!row || row.stageId === stageId) return;
    const stage = stages.find((s) => s.id === stageId);
    onMoved({ ...row, stageId, stage: stage ? stage.name : row.stage }); // optimistic
    try {
      const det = await changeStage(id, stageId);
      onMoved(det);
    } catch (e) {
      onError();
    }
  };

  return (
    <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8 }}>
      {stages.map((s) => {
        const col = rows.filter((r) => r.stageId === s.id);
        const isOver = overStage === s.id;
        return (
          <div key={s.id}
            onDragOver={isRecruiter ? (e) => { e.preventDefault(); setOverStage(s.id); } : undefined}
            onDragLeave={() => setOverStage((p) => (p === s.id ? null : p))}
            onDrop={isRecruiter ? () => drop(s.id) : undefined}
            style={{
              minWidth: 248, width: 248, flexShrink: 0, background: 'var(--surface-2)',
              border: '1px solid ' + (isOver ? 'var(--red-600)' : 'var(--border)'),
              borderRadius: 12, padding: 10, transition: 'border-color .12s',
            }}>
            <div className="between" style={{ marginBottom: 8, padding: '2px 4px' }}>
              <span style={{ fontWeight: 700, fontSize: 12.5 }}>{s.name}</span>
              <span className="badge badge-gray">{col.length}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minHeight: 40 }}>
              {col.map((r) => (
                <div key={r.id}
                  draggable={isRecruiter}
                  onDragStart={() => setDragId(r.id)}
                  onDragEnd={() => setDragId(null)}
                  onClick={() => onOpen(r)}
                  className="card"
                  style={{ padding: 11, cursor: isRecruiter ? 'grab' : 'pointer', opacity: dragId === r.id ? 0.5 : 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>{r.name || '—'}</div>
                  <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>{r.jobName || 'Chưa gán vị trí'}</div>
                  {r.phone && <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>{r.phone}</div>}
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginTop: 8 }}>
                    {r.slaOverdue && (
                      <Badge kind="red" dot>
                        Trễ SLA +{r.daysInStage - r.slaDays}ng
                      </Badge>
                    )}
                    {r.cvResult && <Badge kind={CV_RESULT_KIND[r.cvResult] || 'gray'}>{labels.cvResultLabels[r.cvResult]}</Badge>}
                    {r.callStatus && <Badge kind={CALL_STATUS_KIND[r.callStatus] || 'gray'}>{labels.callStatusLabels[r.callStatus]}</Badge>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
