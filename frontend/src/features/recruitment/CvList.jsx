/* Tab "Danh sách CV" — list + kanban (kéo-thả đổi stage), xem chi tiết, sửa,
   thêm CV thủ công. Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect, useRef } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fetchCvList, changeStage, updateApplicant } from '../../api/recruitment';
import { CV_RESULT_KIND, INTERVIEW_RESULT_KIND } from './util';
import ApplicantDrawer from './ApplicantDrawer';
import ApplicantForm from './ApplicantForm';

/* Chip lọc nhanh — sinh động từ nhãn Selection do BE trả về, bắc qua 2 trường:
   kết quả lọc CV (cvResult) và kết quả phỏng vấn (interviewResult).
   Thêm/bớt giá trị trong Selection ở Odoo là chip tự có, không phải sửa file này.
   Khoá giữ nguyên dạng cv_<key> / pv_<key> nên chip đang chọn không bị mất. */
const buildFilters = (cvLabels = {}, pvLabels = {}) => [
  ['all', 'Tất cả', null],
  ...Object.entries(cvLabels).map(
    ([k, l]) => [`cv_${k}`, `${l} CV`, (r) => r.cvResult === k]),
  ...Object.entries(pvLabels).map(
    ([k, l]) => [`pv_${k}`, `${l} PV`, (r) => r.interviewResult === k]),
];

/* Màu card kanban — lái theo KẾT QUẢ (lọc CV + phỏng vấn), KHÔNG theo tên bước
   (bước cấu hình được nên tên/thứ tự có thể đổi):
     xanh = đã Pass PV (giữ nguyên qua Offer/Nhận việc) ·
     đỏ   = không đi tiếp: Fail PV / Tiềm năng PV, HOẶC Fail CV ·
     vàng = chưa có kết quả (còn đang chạy). */
const CARD_TONE = {
  pass:      { bd: 'var(--green)',   bg: 'var(--green-bg)' },
  fail:      { bd: 'var(--red-600)', bg: 'var(--red-50)' },
  potential: { bd: 'var(--red-600)', bg: 'var(--red-50)' },
};
const TONE_PENDING = { bd: 'var(--amber)', bg: 'var(--amber-bg)' };

/* Kết quả PV xét trước vì nó là bước sau; chưa PV mà đã Fail CV thì cũng đỏ.
   Dữ liệu mâu thuẫn (Fail CV nhưng Pass PV) hiếm nhưng có thể xảy ra do sửa
   tay — khi đó ưu tiên PV, vì đó là phán quyết mới hơn. */
const cardTone = (r) => CARD_TONE[r.interviewResult]
  || (r.cvResult === 'fail' ? CARD_TONE.fail : TONE_PENDING);

/* Không có prop lọc theo bước. Bản cũ có `stageNames` lọc bằng TÊN bước nhưng
   không màn nào truyền vào — mà tên bước sửa được trên màn Cấu hình nên hễ ai
   dùng lại là hỏng đúng kiểu tab Offer trước đây. Cần lọc theo bước thì viết
   lại bằng MÃ bước (`r.stageRef`), xem OFFER_STAGE_REFS ở Offers.jsx. */
export default function CvList({ search, focus }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [cvFilter, setCvFilter] = useState('all');
  const [vmode, setVmode] = useState(() => localStorage.getItem('hocba_cv_vmode') || 'table');
  const [sel, setSel] = useState(null);       // applicant đang xem chi tiết
  const [creating, setCreating] = useState(false);
  const handledFocus = useRef(null);      // nonce thông báo đã xử lý

  const load = () => {
    setErr(null); setData(null);
    fetchCvList().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  /* Bấm thông báo "CV quá hạn xử lý" ở chuông → mở drawer đúng ứng viên.

     Tìm trong data.rows (toàn bộ) nên drawer luôn mở được, kể cả khi chip lọc
     đang giấu ứng viên đó. Vẫn reset chip về "Tất cả" để lúc ĐÓNG drawer ứng
     viên vừa được nhắc còn nằm trong danh sách — không thì vừa được nhắc xong
     đã mất dấu ngay.

     Phụ thuộc `data` vì thông báo có thể bấm lúc danh sách chưa tải xong; nhưng
     `data` còn đổi mỗi lần sửa 1 ô (applyRow) ⇒ chốt bằng ref theo nonce để
     mỗi lần bấm chuông chỉ mở drawer ĐÚNG MỘT LẦN, không tự bật lại. */
  useEffect(() => {
    if (!focus || !focus.requestId || !data) return;
    if (handledFocus.current === focus.nonce) return;
    const row = data.rows.find((r) => r.id === focus.requestId);
    if (!row) return;
    handledFocus.current = focus.nonce;
    setCvFilter('all');
    setSel(row);
  }, [focus, data]);

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
  const filters = buildFilters(cvResultLabels, interviewResultLabels);
  const matchCv = (r) => {
    const f = filters.find(([k]) => k === cvFilter);
    return !f || !f[2] || f[2](r);   // chip lạ (Selection đổi) → coi như Tất cả
  };
  const filtered = rows.filter((r) => matchSearch(r) && matchCv(r));

  return (
    <div>
      <div className="filterbar">
        {filters.map(([k, l, pred]) => (
          <button key={k} className={'chip' + (cvFilter === k ? ' active' : '')} onClick={() => setCvFilter(k)}>
            {l} <span className="ct">{pred ? rows.filter(pred).length : rows.length}</span></button>
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
        <TableView rows={filtered} resetKey={search + '|' + cvFilter}
          meta={meta} isRecruiter={isRecruiter} onOpen={setSel} onSaved={applyRow} />
      ) : (
        <KanbanView rows={filtered} stages={stages}
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

function TableView({ rows, resetKey, meta, isRecruiter, onOpen, onSaved }) {
  const [savingId, setSavingId] = useState(null);
  const { jobs = [], cvResultLabels = {}, interviewResultLabels = {} } = meta || {};
  // Phân trang chỉ ở chế độ Danh sách — Kanban cắt trang thì gãy luồng kéo-thả.
  const pg = usePaged(rows, [resetKey]);

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
            <th>Ứng viên</th><th>Vị trí</th>
            <th>Trạng thái CV</th><th>Kết quả PV</th><th>CV</th><th></th>
          </tr></thead>
          <tbody>
            {pg.rows.map((r) => {
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
      <Pagination {...pg} />
    </div>
  );
}

function KanbanView({ rows, stages, isRecruiter, onOpen, onMoved, onError }) {
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
    <>
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
              {col.map((r) => {
                const tone = cardTone(r);
                // Fail PV thì thôi giục — ứng viên đã dừng, quá hạn không còn nghĩa.
                const showSla = r.slaOverdue && r.interviewResult !== 'fail';
                return (
                <div key={r.id}
                  draggable={isRecruiter}
                  onDragStart={() => setDragId(r.id)}
                  onDragEnd={() => setDragId(null)}
                  onClick={() => onOpen(r)}
                  className="card"
                  style={{
                    padding: 11, cursor: isRecruiter ? 'grab' : 'pointer',
                    opacity: dragId === r.id ? 0.5 : 1,
                    background: tone.bg, borderLeft: '3px solid ' + tone.bd,
                  }}>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>{r.name || '—'}</div>
                  {showSla && (
                    <div style={{ marginTop: 8 }}>
                      <Badge kind="red" dot>Quá hạn {r.daysInStage - r.slaDays} ngày</Badge>
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
    <ColorLegend />
    </>
  );
}

/* Chú thích màu card — đặt dưới bảng Kanban. Lấy màu từ chính CARD_TONE /
   TONE_PENDING để chú thích không bao giờ lệch với card thật. */
const LEGEND = [
  [CARD_TONE.pass, 'Đã Pass PV', 'gồm cả các bước sau: Offer, Nhận việc, Đã tuyển'],
  [TONE_PENDING,   'Đang chạy', 'chưa có kết quả lọc CV / phỏng vấn'],
  [CARD_TONE.fail, 'Fail hoặc Tiềm năng PV, Fail CV', 'không đi tiếp lần này'],
];

function ColorLegend() {
  return (
    <div className="card" style={{ padding: '10px 12px', marginTop: 10 }}>
      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontWeight: 700, fontSize: 12 }}>Chú thích màu</span>
        {LEGEND.map(([tone, label, hint]) => (
          <span key={label} style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
            <span style={{
              width: 26, height: 15, borderRadius: 4, flexShrink: 0,
              background: tone.bg, borderLeft: '3px solid ' + tone.bd,
            }} />
            <span style={{ fontSize: 12 }}>{label}</span>
            <span className="muted" style={{ fontSize: 11.5 }}>· {hint}</span>
          </span>
        ))}
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <Badge kind="red" dot>Quá hạn N ngày</Badge>
          <span className="muted" style={{ fontSize: 11.5 }}>
            ứng viên nằm ở bước này lâu hơn hạn xử lý N ngày · không hiện với ứng viên Fail PV</span>
        </span>
      </div>
    </div>
  );
}
