/* Tab "Vị trí tuyển dụng / JD" — lưới + bảng, xem chi tiết JD, sửa, thêm.
   Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchJobs, updateJob } from '../../api/recruitment';
import JobDrawer from './JobDrawer';
import JobForm from './JobForm';

export default function Jobs({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [status, setStatus] = useState('all');
  const [dep, setDep] = useState('all');
  const [vmode, setVmode] = useState(() => localStorage.getItem('hocba_job_vmode') || 'dept');
  const [sel, setSel] = useState(null);
  const [creating, setCreating] = useState(false);

  const load = () => { setErr(null); setData(null); fetchJobs().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  const setView = (m) => { setVmode(m); localStorage.setItem('hocba_job_vmode', m); };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải vị trí tuyển dụng…" />;

  const { rows, requests = [], statusLabels, teachingLevels, departments, isRecruiter } = data;
  const meta = { statusLabels, teachingLevels, departments };

  const applyRow = (det) => setData((p) => {
    const exists = p.rows.some((r) => r.id === det.id);
    const rows = exists ? p.rows.map((r) => (r.id === det.id ? { ...r, ...det } : r)) : [det, ...p.rows];
    // Đồng bộ trạng thái published xuống danh sách phiếu (view phòng ban).
    const requests = (p.requests || []).map((q) => (q.jobId === det.id ? { ...q, published: det.published } : q));
    return { ...p, rows, requests };
  });

  // Mở JD gắn với 1 vị trí (phiếu) trong view phòng ban.
  const openJob = (jobId) => { const r = data.rows.find((x) => x.id === jobId); if (r) setSel(r); };

  // Bật/tắt đăng tuyển ngay tại dòng vị trí (không cần mở JD).
  const togglePublish = async (jobId, next) => {
    try { applyRow(await updateJob(jobId, { published: next })); }
    catch (e) { alert(e.message || 'Không đổi được trạng thái đăng tuyển.'); }
  };

  const filtered = rows.filter((r) => {
    if (status !== 'all' && r.status !== status) return false;
    if (dep !== 'all' && r.depId !== dep) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((r.name || '').toLowerCase().includes(q) || (r.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  });

  // Vị trí đang tuyển = phiếu yêu cầu (state recruiting). Lọc theo phòng ban + tìm kiếm.
  const filteredRequests = requests.filter((r) => {
    if (dep !== 'all' && r.depId !== dep) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((r.jobTitle || '').toLowerCase().includes(q) || (r.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  });

  // Nhóm theo phòng ban: hiện mọi phòng ban; khi đang tìm kiếm thì chỉ giữ phòng ban
  // có vị trí khớp (hoặc tên phòng ban khớp).
  const deptGroups = departments
    .filter((d) => dep === 'all' || d.id === dep)
    .map((d) => ({ id: d.id, name: d.name, reqs: filteredRequests.filter((r) => r.depId === d.id) }))
    .filter((g) => (search ? g.reqs.length > 0 || g.name.toLowerCase().includes(search.toLowerCase()) : true));

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (status === 'all' ? ' active' : '')} onClick={() => setStatus('all')}>
          Tất cả <span className="ct">{rows.length}</span></button>
        {Object.entries(statusLabels).map(([k, l]) => (
          <button key={k} className={'chip' + (status === k ? ' active' : '')} onClick={() => setStatus(k)}>
            {l} <span className="ct">{rows.filter((r) => r.status === k).length}</span></button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={dep} onChange={(e) => setDep(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
            <option value="all">Mọi phòng ban</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          {isRecruiter && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm vị trí</button>
          )}
          <div className="seg">
            <button className={vmode === 'dept' ? 'active' : ''} onClick={() => setView('dept')}>Phòng ban</button>
            <button className={vmode === 'grid' ? 'active' : ''} onClick={() => setView('grid')}>Thẻ</button>
            <button className={vmode === 'table' ? 'active' : ''} onClick={() => setView('table')}>Bảng</button>
          </div>
        </div>
      </div>

      {vmode === 'dept' ? (
        <DepartmentView groups={deptGroups} isRecruiter={isRecruiter} onOpenJob={openJob} onTogglePublish={togglePublish} />
      ) : vmode === 'grid' ? (
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))' }}>
          {filtered.map((r) => (
            <div key={r.id} className="card" style={{ padding: 18, cursor: 'pointer' }} onClick={() => setSel(r)}>
              <div className="between">
                <div style={{ fontWeight: 800, fontSize: 14.5 }}>{r.name}</div>
                {r.published && <Badge kind="teal">PUBLISHED</Badge>}
              </div>
              <div className="muted" style={{ fontSize: 12.5, marginTop: 3 }}>{r.depName}</div>
              <div className="divider" style={{ margin: '13px 0' }}></div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                <Badge kind={r.status === 'recruiting' ? 'green' : 'gray'} dot>{statusLabels[r.status]}</Badge>
                <Badge kind="gray">Cần {r.expected}</Badge>
                <Badge kind="blue">{r.applications} đơn</Badge>
              </div>
              {r.jdLink && <div className="muted" style={{ fontSize: 12, marginTop: 10, display: 'inline-flex', alignItems: 'center', gap: 6 }}><Icon name="file" size={14} />Có JD đính kèm</div>}
            </div>
          ))}
          {filtered.length === 0 && <EmptyState>Không tìm thấy vị trí phù hợp.</EmptyState>}
        </div>
      ) : (
        <div className="card">
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Vị trí</th><th>Phòng ban</th><th>Trạng thái</th>
                <th className="tbl-num">Cần tuyển</th><th className="tbl-num">Đơn</th>
                <th>Đăng tuyển</th><th></th>
              </tr></thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id} onClick={() => setSel(r)}>
                    <td><div className="nm">{r.name}</div></td>
                    <td className="muted">{r.depName}</td>
                    <td><Badge kind={r.status === 'recruiting' ? 'green' : 'gray'} dot>{statusLabels[r.status]}</Badge></td>
                    <td className="tbl-num mono">{r.expected}</td>
                    <td className="tbl-num mono">{r.applications}</td>
                    <td>{r.published ? <Badge kind="teal">PUBLISHED</Badge> : <span className="muted">—</span>}</td>
                    <td><button className="icon-btn" onClick={(e) => { e.stopPropagation(); setSel(r); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && <EmptyState>Không tìm thấy vị trí phù hợp.</EmptyState>}
        </div>
      )}

      {sel && (
        <JobDrawer job={sel} meta={meta} isRecruiter={isRecruiter}
          onClose={() => setSel(null)} onChanged={applyRow} />
      )}
      {creating && (
        <JobForm job={null} meta={meta}
          onClose={() => setCreating(false)}
          onSaved={(det) => { setCreating(false); applyRow(det); }} />
      )}
    </div>
  );
}

/* View theo phòng ban (nguồn: phiếu yêu cầu tuyển dụng đang tuyển).
   Thu gọn: tổng vị trí + trạng thái. Bung ra: từng vị trí với Cần / Đã / Còn thiếu. */
function DepartmentView({ groups, isRecruiter, onOpenJob, onTogglePublish }) {
  const [open, setOpen] = useState({}); // depId -> bool
  const [busyJob, setBusyJob] = useState(null);
  const doToggle = async (jobId, next) => {
    setBusyJob(jobId);
    try { await onTogglePublish(jobId, next); } finally { setBusyJob(null); }
  };

  if (!groups.length) return <EmptyState>Không tìm thấy phòng ban phù hợp.</EmptyState>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {groups.map((g) => {
        const posCount = g.reqs.length;
        const need = g.reqs.reduce((s, q) => s + (q.qty || 0), 0);
        const hired = g.reqs.reduce((s, q) => s + (q.hired || 0), 0);
        const missing = Math.max(0, need - hired);
        const isRecruiting = posCount > 0;
        const isOpen = !!open[g.id];
        return (
          <div key={g.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="between" style={{ padding: '15px 18px', cursor: isRecruiting ? 'pointer' : 'default' }}
              onClick={isRecruiting ? () => setOpen((p) => ({ ...p, [g.id]: !p[g.id] })) : undefined}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <Icon name="chevR" size={18} className="faint"
                  style={{ transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform .12s', opacity: isRecruiting ? 1 : 0.25 }} />
                <div>
                  <div style={{ fontWeight: 800, fontSize: 15 }}>{g.name}</div>
                  <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                    Tổng {posCount} vị trí đang tuyển</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', alignItems: 'center' }}>
                <Badge kind={isRecruiting ? 'green' : 'gray'} dot>{isRecruiting ? 'Đang tuyển' : 'Dừng tuyển'}</Badge>
                {isRecruiting && <>
                  <Badge kind="gray">Cần tuyển {need}</Badge>
                  <Badge kind="green">Đã tuyển {hired}</Badge>
                  <Badge kind={missing > 0 ? 'amber' : 'teal'}>Còn thiếu {missing}</Badge>
                </>}
              </div>
            </div>

            {isOpen && (
              <div className="tbl-wrap" style={{ borderTop: '1px solid var(--border)' }}>
                <table className="tbl">
                  <thead><tr>
                    <th>Vị trí</th><th>Phiếu YC</th>
                    <th className="tbl-num">Cần tuyển</th><th className="tbl-num">Đã tuyển</th>
                    <th className="tbl-num">Còn thiếu</th><th>Đăng tuyển</th>
                  </tr></thead>
                  <tbody>
                    {g.reqs.map((q) => {
                      const miss = Math.max(0, (q.qty || 0) - (q.hired || 0));
                      const hasJD = !!q.jobId;
                      return (
                        <tr key={q.id}>
                          <td>
                            <div className="nm" style={hasJD ? { cursor: 'pointer', color: 'var(--red-700)' } : undefined}
                              onClick={hasJD ? () => onOpenJob(q.jobId) : undefined}
                              title={hasJD ? 'Mở JD' : undefined}>
                              {q.jobTitle}
                              {q.levelLabel && <span className="muted" style={{ fontWeight: 400 }}> · {q.levelLabel}</span>}</div>
                            {q.jobName && <div className="id">JD: {q.jobName}</div>}
                          </td>
                          <td className="muted mono">{q.code}</td>
                          <td className="tbl-num mono">{q.qty || 0}</td>
                          <td className="tbl-num mono">{q.hired || 0}</td>
                          <td className="tbl-num mono" style={{ fontWeight: miss > 0 ? 700 : 400, color: miss > 0 ? 'var(--amber-700, #b45309)' : 'inherit' }}>{miss}</td>
                          <td>
                            {!hasJD ? (
                              <span className="muted" title="Phiếu chưa gắn JD nên chưa đăng được">Chưa có JD</span>
                            ) : isRecruiter ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                {q.published && <Badge kind="teal">PUBLISHED</Badge>}
                                <button className="btn btn-ghost btn-sm" disabled={busyJob === q.jobId}
                                  onClick={() => doToggle(q.jobId, !q.published)}>
                                  <Icon name={q.published ? 'x' : 'check'} size={14} />
                                  {q.published ? 'Ngừng đăng' : 'Đăng tuyển'}</button>
                              </div>
                            ) : (
                              q.published ? <Badge kind="teal">PUBLISHED</Badge> : <span className="muted">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
