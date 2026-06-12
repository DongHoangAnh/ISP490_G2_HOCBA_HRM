/* ============================================================
   HỌC BÁ — Module Tuyển dụng / App Entry Point
   ============================================================ */

const DEPT_OPTIONS = [
  { label: 'Kinh Doanh', color: '#C8102E' },
  { label: 'R&D_SP',     color: '#0F766E' },
  { label: 'Marketing',  color: '#D9A400' },
  { label: 'Vận Hành',   color: '#1D4ED8' },
  { label: 'HCNS',       color: '#6D28D9' },
  { label: 'Kế Toán',    color: '#D97706' },
];

const PRIORITY_OPTIONS = ['Cao', 'Trung bình', 'Thấp'];
const TYPE_OPTIONS     = ['Offline', 'Online', 'Online / Offline'];
const PRIORITY_COLOR   = { 'Cao': 'red', 'Trung bình': 'amber', 'Thấp': 'blue' };

/* ── Shared input style ── */
const INP = {
  width: '100%', padding: '9px 12px',
  border: '1px solid var(--border)', borderRadius: 9,
  fontSize: 13.5, fontFamily: 'inherit',
  background: 'var(--surface)', color: 'var(--ink)',
  outline: 'none', boxSizing: 'border-box',
};

function FormField({ label, full, children }) {
  return (
    <div style={full ? { gridColumn: '1 / -1' } : {}}>
      <label style={{
        fontSize: 11.5, fontWeight: 700, color: 'var(--muted)',
        display: 'block', marginBottom: 6,
        textTransform: 'uppercase', letterSpacing: '.35px',
      }}>{label}</label>
      {children}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Job Form Modal — dùng cho cả Create và Edit
   ══════════════════════════════════════════════════════════════ */
function JobFormModal({ job, onSave, onClose }) {
  const isEdit = !!job;

  const [form, setForm] = useState({
    title:     job?.title     || '',
    dept:      job?.dept      || DEPT_OPTIONS[0].label,
    deptColor: job?.deptColor || DEPT_OPTIONS[0].color,
    headcount: job?.headcount != null ? job.headcount : 1,
    filled:    job?.filled    != null ? job.filled    : 0,
    deadline:  job?.deadline  || '',
    priority:  job?.priority  || 'Cao',
    salary:    job?.salary    || '',
    exp:       job?.exp       || '',
    type:      job?.type      || 'Offline',
    desc:      job?.desc      || '',
    tags:      job?.tags      ? job.tags.join(', ') : '',
  });

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  function handleDeptChange(label) {
    const d = DEPT_OPTIONS.find(d => d.label === label);
    setForm(f => ({ ...f, dept: label, deptColor: d?.color || '#78716C' }));
  }

  function handleSave() {
    if (!form.title.trim() || !form.deadline) return;
    const tags = form.tags.split(',').map(t => t.trim()).filter(Boolean);
    onSave({ ...form, headcount: Number(form.headcount) || 1, filled: Number(form.filled) || 0, tags });
  }

  return (
    <Modal onClose={onClose} lg>
      {/* Header */}
      <div style={{
        padding: '20px 24px 16px', borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: 17, fontWeight: 800 }}>
            {isEdit ? 'Chỉnh sửa vị trí tuyển dụng' : 'Tạo vị trí tuyển dụng mới'}
          </div>
          {isEdit && (
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>ID: {job.id}</div>
          )}
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={18}/></button>
      </div>

      {/* Body */}
      <div style={{
        padding: '20px 24px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px 20px',
        maxHeight: '65vh', overflowY: 'auto',
      }}>
        <FormField label="Tên vị trí *" full>
          <input style={INP} placeholder="VD: Chuyên viên tuyển sinh"
            value={form.title} onChange={e => set('title', e.target.value)}/>
        </FormField>

        <FormField label="Phòng ban">
          <select style={INP} value={form.dept} onChange={e => handleDeptChange(e.target.value)}>
            {DEPT_OPTIONS.map(d => <option key={d.label} value={d.label}>{d.label}</option>)}
          </select>
        </FormField>

        <FormField label="Hình thức làm việc">
          <select style={INP} value={form.type} onChange={e => set('type', e.target.value)}>
            {TYPE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </FormField>

        <FormField label="Số lượng cần tuyển">
          <input style={INP} type="number" min={1} value={form.headcount}
            onChange={e => set('headcount', e.target.value)}/>
        </FormField>

        <FormField label="Đã tuyển được">
          <input style={INP} type="number" min={0} value={form.filled}
            onChange={e => set('filled', e.target.value)}/>
        </FormField>

        <FormField label="Deadline *">
          <input style={INP} type="date" value={form.deadline}
            onChange={e => set('deadline', e.target.value)}/>
        </FormField>

        <FormField label="Mức độ ưu tiên">
          <select style={INP} value={form.priority} onChange={e => set('priority', e.target.value)}>
            {PRIORITY_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </FormField>

        <FormField label="Mức lương">
          <input style={INP} placeholder="VD: 8M – 15M" value={form.salary}
            onChange={e => set('salary', e.target.value)}/>
        </FormField>

        <FormField label="Yêu cầu kinh nghiệm">
          <input style={INP} placeholder="VD: 1–2 năm KN" value={form.exp}
            onChange={e => set('exp', e.target.value)}/>
        </FormField>

        <FormField label="Mô tả vị trí" full>
          <textarea style={{ ...INP, height: 80, resize: 'vertical' }}
            placeholder="Mô tả ngắn về vị trí và yêu cầu công việc..."
            value={form.desc} onChange={e => set('desc', e.target.value)}/>
        </FormField>

        <FormField label={<>Tags <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>(phân cách bằng dấu phẩy)</span></>} full>
          <input style={INP} placeholder="VD: Sales, Tư vấn, COM"
            value={form.tags} onChange={e => set('tags', e.target.value)}/>
        </FormField>
      </div>

      {/* Footer */}
      <div style={{
        padding: '14px 24px', borderTop: '1px solid var(--border)',
        display: 'flex', justifyContent: 'flex-end', gap: 10,
      }}>
        <button className="btn btn-ghost" onClick={onClose}>Hủy</button>
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={!form.title.trim() || !form.deadline}
          style={{ opacity: (!form.title.trim() || !form.deadline) ? .5 : 1 }}
        >
          <Icon name={isEdit ? 'edit' : 'plus'} size={15}/>
          {isEdit ? 'Lưu thay đổi' : 'Tạo vị trí'}
        </button>
      </div>
    </Modal>
  );
}

/* ══════════════════════════════════════════════════════════════
   Jobs View — danh sách + create + edit
   ══════════════════════════════════════════════════════════════ */
function RecJobsView({ jobs, setJobs, setView }) {
  const [modal, setModal] = useState(null); // null | 'create' | <job object>
  let nextId = jobs.length + 1;

  function handleSave(formData) {
    if (modal === 'create') {
      const newJob = { ...formData, id: 'j' + (nextId++) };
      setJobs(prev => [...prev, newJob]);
    } else {
      setJobs(prev => prev.map(j => j.id === modal.id ? { ...modal, ...formData } : j));
    }
    setModal(null);
  }

  const openSlots = jobs.reduce((s, j) => s + Math.max(0, j.headcount - j.filled), 0);

  return (
    <div className="content fade-in">
      {/* Page header */}
      <div className="page-head">
        <div>
          <h1>Vị trí tuyển dụng</h1>
          <p>{jobs.length} vị trí đang mở · {openSlots} suất còn trống</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost" onClick={() => setView('dashboard')}>
            <Icon name="chevL" size={15}/> Dashboard
          </button>
          <button className="btn btn-primary" onClick={() => setModal('create')}>
            <Icon name="plus" size={15}/> Tạo vị trí mới
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="card-head">
          <h3>Danh sách vị trí</h3>
          <Badge kind="gray">{jobs.length} vị trí</Badge>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Vị trí', 'Phòng ban', 'Ưu tiên', 'Chỉ tiêu', 'Lương', 'Deadline', 'Hình thức', ''].map(h => (
                  <th key={h} style={{
                    padding: '11px 16px', textAlign: 'left',
                    fontWeight: 700, fontSize: 11.5, color: 'var(--muted)',
                    textTransform: 'uppercase', letterSpacing: '.3px',
                    background: 'var(--surface-2)', whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: '56px 20px', textAlign: 'center', color: 'var(--faint)' }}>
                    <Icon name="building" size={36}/>
                    <div style={{ marginTop: 12, fontSize: 14, fontWeight: 600 }}>
                      Chưa có vị trí nào
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--faint)', marginTop: 4 }}>
                      Click "Tạo vị trí mới" để bắt đầu
                    </div>
                  </td>
                </tr>
              ) : jobs.map(j => {
                const open = j.headcount - j.filled;
                const pct  = j.headcount > 0 ? Math.round(j.filled / j.headcount * 100) : 0;
                const daysLeft = Math.round((new Date(j.deadline) - new Date('2026-06-09')) / 86400000);

                return (
                  <tr key={j.id}
                    style={{ borderBottom: '1px solid var(--border)', transition: 'background .1s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-2)'}
                    onMouseLeave={e => e.currentTarget.style.background = ''}>

                    {/* Tên vị trí */}
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 700, color: 'var(--ink)', fontSize: 13.5 }}>{j.title}</div>
                      {j.exp && <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>{j.exp}</div>}
                    </td>

                    {/* Phòng ban */}
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 8, height: 8, borderRadius: 2, background: j.deptColor, flexShrink: 0 }}></span>
                        <span style={{ fontWeight: 600 }}>{j.dept}</span>
                      </div>
                    </td>

                    {/* Ưu tiên */}
                    <td style={{ padding: '14px 16px' }}>
                      <Badge kind={PRIORITY_COLOR[j.priority] || 'gray'}>{j.priority}</Badge>
                    </td>

                    {/* Chỉ tiêu */}
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 700 }}>{j.filled}/{j.headcount}</div>
                      <div style={{ width: 72, marginTop: 5 }}>
                        <div className="bar" style={{ height: 5 }}>
                          <span style={{ width: pct + '%', background: open === 0 ? 'var(--green)' : j.deptColor }}></span>
                        </div>
                      </div>
                      <div style={{
                        fontSize: 11, fontWeight: 700, marginTop: 3,
                        color: open > 0 ? 'var(--red-600)' : 'var(--green)',
                      }}>
                        {open > 0 ? `Còn ${open} suất` : 'Đủ người'}
                      </div>
                    </td>

                    {/* Lương */}
                    <td style={{ padding: '14px 16px', color: 'var(--green)', fontWeight: 700 }}>
                      {j.salary || '—'}
                    </td>

                    {/* Deadline */}
                    <td style={{ padding: '14px 16px', whiteSpace: 'nowrap' }}>
                      <div style={{ fontWeight: 600 }}>{fmtDate(j.deadline)}</div>
                      <div style={{
                        fontSize: 11.5, fontWeight: 600, marginTop: 2,
                        color: daysLeft < 0 ? 'var(--muted)' : daysLeft <= 10 ? 'var(--red-600)' : 'var(--muted)',
                      }}>
                        {daysLeft > 0 ? `Còn ${daysLeft} ngày` : daysLeft === 0 ? 'Hôm nay' : 'Đã hết hạn'}
                      </div>
                    </td>

                    {/* Hình thức */}
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        fontSize: 12, background: 'var(--surface-2)',
                        border: '1px solid var(--border)', borderRadius: 6,
                        padding: '3px 9px', fontWeight: 600,
                      }}>{j.type}</span>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: '14px 16px', whiteSpace: 'nowrap' }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => setModal(j)}>
                        <Icon name="edit" size={13}/> Sửa
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal create / edit */}
      {modal && (
        <JobFormModal
          job={modal === 'create' ? null : modal}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   App root
   ══════════════════════════════════════════════════════════════ */
const LS_JOBS_KEY = 'hocba_rec_jobs';

function loadJobs() {
  try {
    const raw = localStorage.getItem(LS_JOBS_KEY);
    return raw ? JSON.parse(raw) : REC_JOBS;
  } catch {
    return REC_JOBS;
  }
}

function saveJobs(jobs) {
  try { localStorage.setItem(LS_JOBS_KEY, JSON.stringify(jobs)); } catch {}
}

function RecApp() {
  const [view, setView] = useState('dashboard');
  const [search, setSearch] = useState('');
  const [jobs, setJobsState] = useState(loadJobs);

  function setJobs(next) {
    const updated = typeof next === 'function' ? next(jobs) : next;
    setJobsState(updated);
    saveJobs(updated);
  }

  function renderView() {
    switch (view) {
      case 'dashboard':  return <RecDashboard setView={setView}/>;
      case 'kanban':     return <RecKanbanPlaceholder setView={setView}/>;
      case 'jobs':       return <RecJobsView jobs={jobs} setJobs={setJobs} setView={setView}/>;
      case 'applicants': return <RecApplicantsPlaceholder setView={setView}/>;
      case 'interviews': return <RecInterviewsPlaceholder setView={setView}/>;
      default:           return <RecDashboard setView={setView}/>;
    }
  }

  return (
    <div className="app">
      <RecSidebar view={view} setView={setView}/>
      <div className="main">
        <RecTopbar view={view} onSearch={setSearch}/>
        {renderView()}
      </div>
    </div>
  );
}

/* ── Placeholder views ── */
function PlaceholderView({ icon, title, desc, actions }) {
  return (
    <div className="content fade-in">
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: '80px 20px', textAlign: 'center',
      }}>
        <div style={{
          width: 72, height: 72, borderRadius: 20,
          background: 'var(--red-50)', color: 'var(--red-600)',
          display: 'grid', placeItems: 'center', marginBottom: 20,
        }}>
          <Icon name={icon} size={34}/>
        </div>
        <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 800 }}>{title}</h2>
        <p style={{ margin: '0 0 24px', color: 'var(--muted)', fontSize: 14, maxWidth: 400 }}>{desc}</p>
        {actions && <div style={{ display: 'flex', gap: 10 }}>{actions}</div>}
        <div style={{
          marginTop: 32, padding: '12px 22px', borderRadius: 10,
          background: 'var(--gold-50)', border: '1px solid var(--gold-200)',
          fontSize: 12.5, color: 'var(--gold-600)', fontWeight: 600,
        }}>
          Tính năng này sẽ được phát triển trong phiên bản tiếp theo
        </div>
      </div>
    </div>
  );
}

function RecKanbanPlaceholder({ setView }) {
  return (
    <PlaceholderView icon="briefcase" title="Pipeline Kanban"
      desc="Kéo thả ứng viên qua các bước tuyển dụng. Trực quan, tức thì, dễ quản lý."
      actions={[
        <button key="1" className="btn btn-ghost" onClick={() => setView('dashboard')}>
          <Icon name="chevL" size={15}/> Về Dashboard
        </button>,
        <button key="2" className="btn btn-primary">
          <Icon name="plus" size={15}/> Thêm ứng viên
        </button>,
      ]}
    />
  );
}

function RecApplicantsPlaceholder({ setView }) {
  return (
    <PlaceholderView icon="users" title="Danh sách ứng viên"
      desc="Tìm kiếm, lọc và quản lý toàn bộ ứng viên theo vị trí, giai đoạn, nguồn."
      actions={[
        <button key="1" className="btn btn-ghost" onClick={() => setView('dashboard')}>
          <Icon name="chevL" size={15}/> Về Dashboard
        </button>,
      ]}
    />
  );
}

function RecInterviewsPlaceholder({ setView }) {
  return (
    <PlaceholderView icon="calendar" title="Lịch phỏng vấn"
      desc="Xem và đặt lịch phỏng vấn. Tích hợp Google Calendar và nhắc nhở tự động."
      actions={[
        <button key="1" className="btn btn-ghost" onClick={() => setView('dashboard')}>
          <Icon name="chevL" size={15}/> Về Dashboard
        </button>,
        <button key="2" className="btn btn-primary">
          <Icon name="plus" size={15}/> Đặt lịch phỏng vấn
        </button>,
      ]}
    />
  );
}

/* ── Mount ── */
ReactDOM.createRoot(document.getElementById('root')).render(<RecApp/>);
