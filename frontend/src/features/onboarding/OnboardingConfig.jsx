/* ============================================================
   Màn Cấu hình nhận việc — admin (HR Manager) tạo/sửa template
   quy trình thử việc bước động. Owner: Tân.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
   ============================================================ */
import { useState } from 'react';
import useFetch from '../../hooks/useFetch';
import {
  fetchOnbTemplates, createOnbTemplate, updateOnbTemplate,
} from '../../api/onboarding';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
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

/* Drawer sửa/tạo template: form tiêu chí + bảng bước (thêm/xoá/di chuyển). */
function TemplateEditor({ tpl, employeeTypes, onClose, onSaved }) {
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
  const archive = async () => {
    if (!window.confirm('Lưu trữ quy trình này? NV đang chạy không bị ảnh hưởng (snapshot); quy trình sẽ không được gán mới.')) return;
    setBusy(true);
    try { onSaved(await updateOnbTemplate(tpl.id, { active: false })); }
    catch (e) { setErr(e.message || 'Lưu trữ thất bại.'); setBusy(false); }
  };

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
            <span className="faint" style={{ fontSize: 11 }}>Ưu tiên (khớp nhiều → số nhỏ thắng)</span>
            <input type="number" style={inp} value={f.sequence}
              onChange={(e) => set('sequence', e.target.value)} />
          </label>
        </div>

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
            <button className="btn btn-ghost btn-sm" disabled={busy} onClick={archive}
              style={{ marginRight: 'auto', color: 'var(--red-700)' }}>
              <Icon name="trash" size={14} />Lưu trữ</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Huỷ</button>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={save}>
            {busy ? 'Đang lưu…' : 'Lưu quy trình'}</button>
        </div>
      </div>
    </Modal>
  );
}

export default function OnboardingConfig() {
  const { data, err, loading, reload } = useFetch(
    fetchOnbTemplates, [], 'onboarding:templates');
  const [editing, setEditing] = useState(null); // null | {} (mới) | template

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <LoadingState label="Đang tải cấu hình nhận việc…" />;

  const templates = data.templates || [];
  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Cấu hình nhận việc</h1>
          <p>Định nghĩa các bước thử việc theo từng nhóm nhân sự — sửa template chỉ áp dụng cho nhân viên gán mới (snapshot)</p>
        </div>
        <button className="btn btn-primary" onClick={() => setEditing({})}>
          <Icon name="plus" size={16} />Thêm quy trình</button>
      </div>

      {!templates.length && <EmptyState>Chưa có quy trình nào.</EmptyState>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
        {templates.map((t) => (
          <div key={t.id} className="card" style={{ padding: 16, cursor: 'pointer', opacity: t.active === false ? 0.55 : 1 }}
            onClick={() => setEditing(t)}>
            <div className="between" style={{ marginBottom: 6 }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>{t.name}</span>
              {t.active === false
                ? <Badge kind="gray">Đã lưu trữ</Badge>
                : <Badge kind="green" dot>Đang dùng</Badge>}
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
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }} />
      )}
    </div>
  );
}
