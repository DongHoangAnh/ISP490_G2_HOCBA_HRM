/* ============================================================
   Màn Cấu hình nhận việc — admin (HR Manager) tạo/sửa template
   quy trình thử việc bước động. Owner: Tân.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
   ============================================================ */
import { useState } from 'react';
import useFetch from '../../hooks/useFetch';
import {
  fetchOnbTemplates, createOnbTemplate, updateOnbTemplate, assignPendingOnb,
} from '../../api/onboarding';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const POSITION_TYPES = [
  ['manager', 'Quản lý'], ['staff', 'Nhân viên'], ['ctv', 'CTV'],
  ['freelancer', 'Freelancer'], ['advisor', 'Cố vấn']];
const WORK_FORMS = [['any', 'Tất cả'], ['offline', 'Offline'], ['online', 'Online']];
const EMPTY_STEP = () => ({
  name: '', stepType: 'task', dueDays: 0,
  passCompletes: false, isExtension: false, autoAction: 'none', note: '',
});

const inp = {
  padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', outline: 'none',
  fontFamily: 'inherit',
};

/* Mô tả ngắn tiêu chí áp dụng của template (hiện trên card). */
function applyLabel(t, employeeTypes) {
  const parts = [];
  if (t.applyPositionTypes) {
    const map = Object.fromEntries(POSITION_TYPES);
    parts.push(t.applyPositionTypes.split(',').map((p) => map[p.trim()] || p.trim()).join('/'));
  }
  if (t.applyWorkForm && t.applyWorkForm !== 'any') parts.push(t.applyWorkForm);
  if (t.applyEmployeeTypeIds && t.applyEmployeeTypeIds.length) {
    const byId = Object.fromEntries((employeeTypes || []).map((e) => [e.id, e.name]));
    parts.push(t.applyEmployeeTypeIds.map((id) => byId[id] || id).join('/'));
  }
  return parts.length ? parts.join(' · ') : 'Mọi nhân sự';
}

/* Hai quy trình có thể cùng khớp 1 NV không (giao phạm vi ≠ rỗng)?
   Tiêu chí bỏ trống = khớp mọi giá trị → luôn giao trên trục đó. */
function scopeOverlaps(a, b) {
  const pos = (t) => (t.applyPositionTypes || '')
    .split(',').map((s) => s.trim()).filter(Boolean);
  const pA = pos(a); const pB = pos(b);
  if (pA.length && pB.length && !pA.some((v) => pB.includes(v))) return false;
  const wA = a.applyWorkForm || 'any'; const wB = b.applyWorkForm || 'any';
  if (wA !== 'any' && wB !== 'any' && wA !== wB) return false;
  const eA = a.applyEmployeeTypeIds || []; const eB = b.applyEmployeeTypeIds || [];
  if (eA.length && eB.length && !eA.some((v) => eB.includes(v))) return false;
  return true;
}

/* Drawer sửa/tạo template: form tiêu chí + bảng bước (thêm/xoá/di chuyển).
   others = các template active khác → cảnh báo trùng phạm vi + ai thắng. */
function TemplateEditor({ tpl, employeeTypes, others, onClose, onSaved }) {
  const isNew = !tpl.id;
  const [f, setF] = useState({
    name: tpl.name || '',
    sequence: tpl.sequence ?? 10,
    applyPositionTypes: (tpl.applyPositionTypes || '')
      .split(',').map((s) => s.trim()).filter(Boolean),
    applyWorkForm: tpl.applyWorkForm || 'any',
    applyEmployeeTypeIds: tpl.applyEmployeeTypeIds || [],
    steps: (tpl.steps || []).map((s) => ({ ...s })),
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const setStep = (i, k, v) => setF((p) => {
    const steps = p.steps.map((s, j) => (j === i ? { ...s, [k]: v } : s));
    return { ...p, steps };
  });
  const move = (i, d) => setF((p) => {
    const steps = [...p.steps];
    const j = i + d;
    if (j < 0 || j >= steps.length) return p;
    [steps[i], steps[j]] = [steps[j], steps[i]];
    return { ...p, steps };
  });
  const toggle = (list, v) =>
    list.includes(v) ? list.filter((x) => x !== v) : [...list, v];

  const save = async () => {
    setErr(null);
    if (!f.name.trim()) { setErr('Cần nhập tên quy trình.'); return; }
    if (!f.steps.length) { setErr('Quy trình phải có ít nhất 1 bước.'); return; }
    if (f.steps.some((s) => !s.name.trim())) { setErr('Mỗi bước cần có tên.'); return; }
    const payload = {
      name: f.name.trim(),
      sequence: Number(f.sequence) || 10,
      applyPositionTypes: f.applyPositionTypes.join(','),
      applyWorkForm: f.applyWorkForm,
      applyEmployeeTypeIds: f.applyEmployeeTypeIds,
      steps: f.steps.map((s) => ({
        name: s.name.trim(), stepType: s.stepType,
        dueDays: Number(s.dueDays) || 0,
        passCompletes: s.stepType === 'evaluation' && !!s.passCompletes,
        isExtension: s.stepType === 'evaluation' && !!s.isExtension,
        autoAction: s.stepType === 'task' ? (s.autoAction || 'none') : 'none',
        note: (s.note || '').trim(),
      })),
    };
    setBusy(true);
    try {
      const d = isNew ? await createOnbTemplate(payload)
        : await updateOnbTemplate(tpl.id, payload);
      onSaved(d);
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); }
    finally { setBusy(false); }
  };
  const [archiving, setArchiving] = useState(false);
  const archive = async () => {
    try { onSaved(await updateOnbTemplate(tpl.id, { active: false })); }
    catch (e) { setArchiving(false); setErr(e.message || 'Lưu trữ thất bại.'); throw e; }
  };
  const restore = async () => {
    setErr(null); setBusy(true);
    try { onSaved(await updateOnbTemplate(tpl.id, { active: true })); }
    catch (e) { setErr(e.message || 'Khôi phục thất bại.'); setBusy(false); }
  };

  // Cảnh báo sống: quy trình nào trùng đối tượng + với số ưu tiên hiện tại
  // thì bên nào thắng — trả lời tại chỗ "chọn số dựa vào đâu".
  const mySeq = Number(f.sequence) || 10;
  const clashes = (others || []).filter((t) => scopeOverlaps({
    applyPositionTypes: f.applyPositionTypes.join(','),
    applyWorkForm: f.applyWorkForm,
    applyEmployeeTypeIds: f.applyEmployeeTypeIds,
  }, t));

  return (
    <Modal onClose={onClose} lg>
      <ModalHeader icon="settings" lg onClose={onClose}
        title={isNew ? 'Thêm quy trình nhận việc' : `Sửa: ${tpl.name}`}
        sub="Sửa template chỉ ảnh hưởng nhân viên gán MỚI — NV đang chạy giữ nguyên lộ trình (snapshot)." />
      <div style={{ padding: '18px 24px', maxHeight: 'min(70vh, calc(100vh - 220px))', overflowY: 'auto' }}>
        <div className="grid-2" style={{ rowGap: 12, columnGap: 14, marginBottom: 14 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Tên quy trình *</span>
            <input style={inp} value={f.name} onChange={(e) => set('name', e.target.value)}
              placeholder="VD: Thử việc Nhân viên kinh doanh" />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Ưu tiên khi trùng (số nhỏ thắng)</span>
            <input type="number" style={inp} value={f.sequence}
              onChange={(e) => set('sequence', e.target.value)} />
            <span className="faint" style={{ fontSize: 11, lineHeight: 1.55 }}>
              Chỉ dùng đến khi 1 NV khớp nhiều quy trình cùng lúc — khi đó hệ
              thống lấy quy trình có số <b>nhỏ hơn</b>. Mẹo chọn: quy trình
              chuyên biệt (tiêu chí hẹp) đặt số nhỏ (1–5), quy trình chung
              đặt số lớn (10+). Không trùng ai thì số này không có tác dụng.
            </span>
          </label>
        </div>

        {clashes.length > 0 && (
          <div style={{ padding: '10px 14px', background: 'var(--gold-50)', border: '1px solid var(--gold-200)', borderRadius: 11, marginBottom: 14, fontSize: 12.5, display: 'grid', gap: 5 }}>
            <b style={{ fontSize: 12 }}>
              ⚠ Trùng đối tượng với {clashes.length} quy trình đang dùng — NV
              khớp cả hai sẽ theo bên có số ưu tiên nhỏ hơn:
            </b>
            {clashes.map((t) => {
              const win = mySeq < t.sequence ? 'this'
                : mySeq > t.sequence ? 'other' : 'tie';
              return (
                <div key={t.id}>
                  • <b>{t.name}</b> (ưu tiên {t.sequence}):{' '}
                  {win === 'this' && (
                    <>quy trình đang sửa <b>thắng</b> ({mySeq} &lt; {t.sequence})</>
                  )}
                  {win === 'other' && (
                    <>bên kia <b>thắng</b> ({t.sequence} &lt; {mySeq}) — muốn
                      quy trình này được chọn, đặt số nhỏ hơn {t.sequence}</>
                  )}
                  {win === 'tie' && (
                    <span style={{ color: 'var(--red-600)', fontWeight: 600 }}>
                      cùng số {mySeq} — kết quả khó đoán, nên đặt hai số khác nhau
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="card" style={{ padding: 14, marginBottom: 14 }}>
          <div style={{ fontWeight: 700, fontSize: 12.5, marginBottom: 10 }}>
            Tiêu chí gán tự động <span className="faint" style={{ fontWeight: 500 }}>(bỏ trống = khớp tất cả)</span>
          </div>
          <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', fontSize: 12.5 }}>
            <div>
              <div className="faint" style={{ fontSize: 11, marginBottom: 5 }}>Loại vị trí</div>
              {POSITION_TYPES.map(([v, l]) => (
                <label key={v} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 3 }}>
                  <input type="checkbox" checked={f.applyPositionTypes.includes(v)}
                    onChange={() => set('applyPositionTypes', toggle(f.applyPositionTypes, v))} />
                  {l}
                </label>
              ))}
            </div>
            <div>
              <div className="faint" style={{ fontSize: 11, marginBottom: 5 }}>Hình thức làm việc</div>
              <select style={inp} value={f.applyWorkForm}
                onChange={(e) => set('applyWorkForm', e.target.value)}>
                {WORK_FORMS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <div className="faint" style={{ fontSize: 11, marginBottom: 5 }}>Loại nhân sự</div>
              {(employeeTypes || []).map((t) => (
                <label key={t.id} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 3 }}>
                  <input type="checkbox" checked={f.applyEmployeeTypeIds.includes(t.id)}
                    onChange={() => set('applyEmployeeTypeIds', toggle(f.applyEmployeeTypeIds, t.id))} />
                  {t.name}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="between" style={{ marginBottom: 8 }}>
          <span style={{ fontWeight: 700, fontSize: 12.5 }}>Các bước ({f.steps.length})</span>
          <button className="btn btn-ghost btn-sm"
            onClick={() => set('steps', [...f.steps, EMPTY_STEP()])}>
            <Icon name="plus" size={14} />Thêm bước</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {f.steps.map((s, i) => (
            <div key={i} className="card" style={{ padding: 12 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="mono faint" style={{ width: 18, textAlign: 'center' }}>{i + 1}</span>
                <input style={{ ...inp, flex: 2, minWidth: 160 }} value={s.name}
                  placeholder="Tên bước *" onChange={(e) => setStep(i, 'name', e.target.value)} />
                <select style={{ ...inp, width: 130 }} value={s.stepType}
                  onChange={(e) => setStep(i, 'stepType', e.target.value)}>
                  <option value="task">Việc cần làm</option>
                  <option value="evaluation">Đánh giá</option>
                </select>
                <label className="faint" style={{ fontSize: 12, display: 'flex', gap: 5, alignItems: 'center' }}>
                  hạn +
                  <input type="number" min="0" style={{ ...inp, width: 64, padding: '5px 8px' }}
                    value={s.dueDays} onChange={(e) => setStep(i, 'dueDays', e.target.value)} />
                  ngày
                </label>
                <span style={{ marginLeft: 'auto', display: 'flex', gap: 2 }}>
                  <button className="icon-btn" title="Lên" onClick={() => move(i, -1)}>
                    <Icon name="arrowUp" size={15} className="faint" /></button>
                  <button className="icon-btn" title="Xuống" onClick={() => move(i, 1)}>
                    <Icon name="arrowDown" size={15} className="faint" /></button>
                  <button className="icon-btn" title="Xoá bước"
                    onClick={() => set('steps', f.steps.filter((_, j) => j !== i))}>
                    <Icon name="trash" size={15} className="faint" /></button>
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 8, flexWrap: 'wrap', fontSize: 12.5, alignItems: 'center' }}>
                {s.stepType === 'evaluation' ? (
                  <>
                    <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <input type="checkbox" checked={!!s.passCompletes}
                        onChange={(e) => setStep(i, 'passCompletes', e.target.checked)} />
                      Đạt → lên chính thức
                    </label>
                    <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <input type="checkbox" checked={!!s.isExtension}
                        onChange={(e) => setStep(i, 'isExtension', e.target.checked)} />
                      Bước gia hạn (chỉ mở khi bước trước "Gia hạn")
                    </label>
                  </>
                ) : (
                  <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    Automation:
                    <select style={{ ...inp, padding: '5px 8px' }} value={s.autoAction || 'none'}
                      onChange={(e) => setStep(i, 'autoAction', e.target.value)}>
                      <option value="none">Không</option>
                      <option value="grant_assets">Tự cấp tài sản mặc định</option>
                    </select>
                  </label>
                )}
                <input style={{ ...inp, flex: 1, minWidth: 180, padding: '5px 8px' }}
                  value={s.note || ''} placeholder="Hướng dẫn (tuỳ chọn)"
                  onChange={(e) => setStep(i, 'note', e.target.value)} />
              </div>
            </div>
          ))}
          {!f.steps.length && <EmptyState>Chưa có bước nào — bấm "Thêm bước".</EmptyState>}
        </div>

        {err && <div style={{ marginTop: 12, fontSize: 12.5, color: 'var(--red-600)' }}>{err}</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end' }}>
          {!isNew && tpl.active !== false && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              onClick={() => setArchiving(true)}
              style={{ marginRight: 'auto', color: 'var(--red-700)' }}>
              <Icon name="trash" size={14} />Lưu trữ</button>
          )}
          {!isNew && tpl.active === false && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              onClick={restore}
              style={{ marginRight: 'auto', color: 'var(--green)' }}>
              <Icon name="rotateCcw" size={14} />Khôi phục</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Huỷ</button>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={save}>
            {busy ? 'Đang lưu…' : 'Lưu quy trình'}</button>
        </div>
        {archiving && (
          <ConfirmModal title="Lưu trữ quy trình"
            message="NV đang chạy không bị ảnh hưởng (snapshot); quy trình sẽ không được gán mới. Tiếp tục?"
            confirmLabel="Lưu trữ"
            onConfirm={archive}
            onClose={() => setArchiving(false)} />
        )}
      </div>
    </Modal>
  );
}

export default function OnboardingConfig() {
  const { data, err, loading, reload } = useFetch(
    fetchOnbTemplates, [], 'onboarding:templates');
  const [editing, setEditing] = useState(null); // null | {} (mới) | template
  const [assigning, setAssigning] = useState(false);
  const [assignMsg, setAssignMsg] = useState(null);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <LoadingState label="Đang tải cấu hình nhận việc…" />;

  const templates = data.templates || [];
  const assignPending = async () => {
    setAssigning(true); setAssignMsg(null);
    try {
      const r = await assignPendingOnb();
      const parts = [`Đã gán quy trình cho ${r.assigned} nhân viên`];
      if (r.noMatch) parts.push(`${r.noMatch} không khớp quy trình nào`);
      if (r.noStart) parts.push(`${r.noStart} thiếu ngày bắt đầu thử việc`);
      setAssignMsg(parts.join(' · ') + '.');
    } catch (e) { setAssignMsg(e.message || 'Gán thất bại.'); }
    finally { setAssigning(false); }
  };
  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Cấu hình nhận việc</h1>
          <p>Định nghĩa các bước thử việc theo từng nhóm nhân sự — sửa template chỉ áp dụng cho nhân viên gán mới (snapshot)</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-ghost" disabled={assigning}
            title="Gán quy trình cho các NV thử việc chưa có bước (vd tạo trước khi có template phù hợp)"
            onClick={assignPending}>
            <Icon name="users" size={16} />
            {assigning ? 'Đang gán…' : 'Gán NV đang chờ'}</button>
          <button className="btn btn-primary" onClick={() => setEditing({})}>
            <Icon name="plus" size={16} />Thêm quy trình</button>
        </div>
      </div>
      {assignMsg && (
        <div style={{ marginBottom: 14, padding: '9px 13px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 12.5 }}>
          {assignMsg}
        </div>
      )}

      {!templates.length && <EmptyState>Chưa có quy trình nào.</EmptyState>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
        {templates.map((t) => (
          <div key={t.id} className="card" style={{ padding: 16, cursor: 'pointer', opacity: t.active === false ? 0.55 : 1 }}
            onClick={() => setEditing(t)}>
            <div className="between" style={{ marginBottom: 6 }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>{t.name}</span>
              <span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                <button type="button" title="Nhân bản thành quy trình mới"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditing({
                      name: `${t.name} (bản sao)`,
                      sequence: t.sequence,
                      applyPositionTypes: t.applyPositionTypes,
                      applyWorkForm: t.applyWorkForm,
                      applyEmployeeTypeIds: t.applyEmployeeTypeIds,
                      steps: t.steps.map(({ id, ...s }) => ({ ...s })),
                    });
                  }}
                  style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 2, display: 'inline-flex', color: 'var(--faint)' }}>
                  <Icon name="copy" size={14} />
                </button>
                {t.active === false
                  ? <Badge kind="gray">Đã lưu trữ</Badge>
                  : <Badge kind="green" dot>Đang dùng</Badge>}
              </span>
            </div>
            <div className="muted" style={{ fontSize: 12.5, marginBottom: 10 }}>
              Áp dụng: {applyLabel(t, data.employeeTypes)} · ưu tiên {t.sequence}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {t.steps.map((s, i) => (
                <div key={s.id || i} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12.5 }}>
                  <span className="mono faint" style={{ width: 16, textAlign: 'center' }}>{i + 1}</span>
                  <span style={{ flex: 1 }}>{s.name}</span>
                  <span className="faint" style={{ fontSize: 11 }}>
                    {s.stepType === 'evaluation' ? 'ĐG' : 'Việc'}
                    {s.dueDays ? ` · +${s.dueDays}ng` : ''}
                    {s.passCompletes ? ' · ✓chính thức' : ''}
                    {s.isExtension ? ' · ↻gia hạn' : ''}
                    {s.autoAction === 'grant_assets' ? ' · ⚙tài sản' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {editing !== null && (
        <TemplateEditor tpl={editing} employeeTypes={data.employeeTypes}
          others={templates.filter(
            (x) => x.active !== false && x.id !== editing.id)}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }} />
      )}
    </div>
  );
}
