/* ============================================================
   Màn "Cấu hình tuyển dụng" (sidebar riêng, CHỈ Admin) — chỉnh quy trình
   stages (kéo-thả thứ tự, SLA từng bước, bước hired) + chế độ tự đóng tuyển.
   Owner: Việt. Pattern theo OnboardingConfig (kéo-thả + editor modal).
   Spec: docs/superpowers/specs/2026-07-23-recruitment-config-design.md
   ============================================================ */
import { useRef, useState } from 'react';
import useFetch from '../../hooks/useFetch';
import {
  fetchRecruitConfig, createRecruitStage, updateRecruitStage,
  deleteRecruitStage, reorderRecruitStages, saveRecruitSettings,
} from '../../api/recruitment';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const inp = {
  padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', outline: 'none',
  fontFamily: 'inherit',
};

/* Editor 1 bước: tên, người hỗ trợ, SLA, cờ hired, yêu cầu, tiêu chí. */
function StageEditor({ stage, onClose, onSaved }) {
  const isNew = !stage.id;
  const [f, setF] = useState({
    name: stage.name || '',
    supportPerson: stage.supportPerson || '',
    slaDays: stage.slaDays || 0,
    hiredStage: !!stage.hiredStage,
    requirements: stage.requirements || '',
    successCriteria: stage.successCriteria || '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const save = async () => {
    setErr(null);
    if (!f.name.trim()) { setErr('Cần nhập tên bước.'); return; }
    const payload = { ...f, name: f.name.trim(), slaDays: Number(f.slaDays) || 0 };
    setBusy(true);
    try {
      const d = isNew ? await createRecruitStage(payload)
        : await updateRecruitStage(stage.id, payload);
      onSaved(d);
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    try { await deleteRecruitStage(stage.id); onSaved(null); }
    catch (e) {
      setDeleting(false);
      setErr(e.message || 'Xoá thất bại.');
      throw e;
    }
  };
  const toggleHide = async () => {
    setErr(null); setBusy(true);
    try {
      await updateRecruitStage(stage.id, { active: stage.active === false });
      onSaved(null);
    } catch (e) {
      setErr(e.message || 'Thao tác thất bại.');
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader icon="settings" onClose={onClose}
        title={isNew ? 'Thêm bước quy trình' : `Sửa bước: ${stage.name}`}
        sub="Thay đổi áp dụng ngay cho kanban CV — ứng viên đang chạy giữ nguyên bước hiện tại." />
      <div style={{ padding: '18px 24px', maxHeight: 'min(70vh, calc(100vh - 220px))', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gap: 12 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Tên bước *</span>
            <input style={inp} value={f.name} onChange={(e) => set('name', e.target.value)}
              placeholder="VD: Phỏng vấn vòng 2" />
          </label>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 160 }}>
              <span className="faint" style={{ fontSize: 11 }}>Người hỗ trợ</span>
              <input style={inp} value={f.supportPerson}
                onChange={(e) => set('supportPerson', e.target.value)}
                placeholder="VD: BP tuyển dụng / TBP" />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, width: 130 }}>
              <span className="faint" style={{ fontSize: 11 }}>SLA (ngày) — 0 = không áp</span>
              <input type="number" min="0" style={inp} value={f.slaDays}
                onChange={(e) => set('slaDays', e.target.value)} />
            </label>
          </div>
          <label style={{ display: 'flex', gap: 7, alignItems: 'center', fontSize: 13 }}>
            <input type="checkbox" checked={f.hiredStage}
              onChange={(e) => set('hiredStage', e.target.checked)} />
            Bước "Đã tuyển" (hired) — ứng viên vào bước này được tính là nhận việc,
            trừ chỉ tiêu và kích hoạt tự đóng tuyển
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Yêu cầu / mô tả bước</span>
            <textarea style={{ ...inp, minHeight: 64, resize: 'vertical' }}
              value={f.requirements} onChange={(e) => set('requirements', e.target.value)} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Tiêu chí thành công</span>
            <textarea style={{ ...inp, minHeight: 64, resize: 'vertical' }}
              value={f.successCriteria} onChange={(e) => set('successCriteria', e.target.value)} />
          </label>
        </div>

        {err && <div style={{ marginTop: 12, fontSize: 12.5, color: 'var(--red-600)' }}>{err}</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end' }}>
          {!isNew && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              onClick={() => setDeleting(true)}
              style={{ marginRight: 'auto', color: 'var(--red-700)' }}>
              <Icon name="trash" size={14} />Xoá bước</button>
          )}
          {!isNew && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              onClick={toggleHide}
              title={stage.active === false
                ? 'Đưa bước trở lại kanban CV'
                : 'Ẩn khỏi kanban CV — không xoá dữ liệu, hiện lại được'}>
              <Icon name={stage.active === false ? 'eye' : 'eye-off'} size={14} />
              {stage.active === false ? 'Hiện lại' : 'Ẩn bước'}</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Huỷ</button>
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={save}>
            {busy ? 'Đang lưu…' : 'Lưu bước'}</button>
        </div>
        {deleting && (
          <ConfirmModal title="Xoá bước quy trình"
            message={stage.applicantCount
              ? `Bước này đang có ${stage.applicantCount} ứng viên (kể cả lưu trữ) — hệ thống sẽ từ chối xoá; hãy chuyển họ sang bước khác trước. Vẫn thử xoá?`
              : `Xoá bước "${stage.name}" khỏi quy trình? Hành động không hoàn tác được.`}
            confirmLabel="Xoá"
            onConfirm={remove}
            onClose={() => setDeleting(false)} />
        )}
      </div>
    </Modal>
  );
}

export default function RecruitmentConfig() {
  const { data, err, loading, reload } = useFetch(
    fetchRecruitConfig, [], 'recruitment:config');
  const [editing, setEditing] = useState(null); // null | {} (mới) | stage
  const [msg, setMsg] = useState(null);
  const [reordering, setReordering] = useState(false);
  const [savingMode, setSavingMode] = useState(false);
  const [dragIdx, setDragIdx] = useState(null);
  const [overIdx, setOverIdx] = useState(null);
  const dragDone = useRef(false); // chặn click mở editor ngay sau khi thả

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <LoadingState label="Đang tải cấu hình tuyển dụng…" />;

  const allStages = data.stages || [];
  const stages = allStages.filter((s) => s.active !== false);
  const hiddenStages = allStages.filter((s) => s.active === false);
  const noHired = !stages.some((s) => s.hiredStage);

  const doReorder = async (ids) => {
    setReordering(true);
    try { await reorderRecruitStages(ids); await reload(); }
    catch (e) { setMsg(e.message || 'Đổi thứ tự thất bại.'); }
    finally { setReordering(false); }
  };
  const moveStage = (i, d) => {
    const j = i + d;
    if (j < 0 || j >= stages.length) return;
    const ids = stages.map((s) => s.id);
    [ids[i], ids[j]] = [ids[j], ids[i]];
    doReorder(ids);
  };
  const dropOn = (i) => {
    if (dragIdx === null || dragIdx === i) return;
    const ids = stages.map((s) => s.id);
    const [moved] = ids.splice(dragIdx, 1);
    ids.splice(i, 0, moved);
    doReorder(ids);
  };
  const unhide = async (s) => {
    setMsg(null);
    try { await updateRecruitStage(s.id, { active: true }); await reload(); }
    catch (e) { setMsg(e.message || 'Hiện lại bước thất bại.'); }
  };
  const setMode = async (mode) => {
    if (mode === data.autoCloseMode) return;
    setSavingMode(true); setMsg(null);
    try { await saveRecruitSettings({ autoCloseMode: mode }); await reload(); }
    catch (e) { setMsg(e.message || 'Lưu cấu hình thất bại.'); }
    finally { setSavingMode(false); }
  };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Cấu hình tuyển dụng</h1>
          <p>Quy trình tuyển dụng dùng chung toàn hệ thống — chỉnh bước, SLA và
            chế độ tự đóng tuyển khi đủ chỉ tiêu</p>
        </div>
      </div>
      <div className="card" style={{ padding: 16, marginBottom: 16, maxWidth: 760 }}>
        <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 4 }}>
          Khi tuyển đủ chỉ tiêu (ứng viên vào bước hired đủ số lượng cần tuyển)
        </div>
        <p className="muted" style={{ fontSize: 12.5, margin: '0 0 10px' }}>
          Áp dụng toàn hệ thống, cho mọi vị trí đang đăng tuyển.
        </p>
        <div style={{ display: 'grid', gap: 7 }}>
          {Object.entries(data.autoCloseLabels).map(([mode, label]) => (
            <label key={mode}
              style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13, opacity: savingMode ? 0.6 : 1 }}>
              <input type="radio" name="autoCloseMode" disabled={savingMode}
                checked={data.autoCloseMode === mode} onChange={() => setMode(mode)} />
              {label}
            </label>
          ))}
        </div>
      </div>

      <div className="between" style={{ marginBottom: 10, maxWidth: 760 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 13.5 }}>
            Quy trình tuyển dụng ({stages.length} bước)
          </div>
          <p className="muted" style={{ fontSize: 12.5, margin: 0 }}>
            Kéo thẻ (hoặc bấm ▲▼) đổi thứ tự cột kanban; click thẻ để sửa/ẩn/xoá.
          </p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setEditing({})}>
          <Icon name="plus" size={15} />Thêm bước</button>
      </div>

      {noHired && (
        <div style={{ maxWidth: 760, padding: '10px 14px', background: 'var(--gold-50)', border: '1px solid var(--gold-200)', borderRadius: 11, marginBottom: 12, fontSize: 12.5 }}>
          ⚠ Chưa có bước nào đánh dấu <b>"Đã tuyển" (hired)</b> — thống kê đã tuyển
          và tự đóng tuyển sẽ không hoạt động. Hãy bật cờ hired cho bước cuối quy trình.
        </div>
      )}
      {msg && (
        <div style={{ maxWidth: 760, marginBottom: 12, padding: '9px 13px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 12.5 }}>
          {msg}
        </div>
      )}

      {!stages.length && <EmptyState>Chưa có bước nào — bấm "Thêm bước".</EmptyState>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 760 }}>
        {stages.map((s, i) => (
          <div key={s.id} className="card" draggable={!reordering}
            onDragStart={(e) => { e.dataTransfer.setData('text/plain', String(s.id)); setDragIdx(i); }}
            onDragOver={(e) => { e.preventDefault(); if (overIdx !== i) setOverIdx(i); }}
            onDrop={(e) => { e.preventDefault(); dropOn(i); dragDone.current = true; }}
            onDragEnd={() => {
              setDragIdx(null); setOverIdx(null);
              setTimeout(() => { dragDone.current = false; }, 0);
            }}
            onClick={() => { if (dragDone.current) return; setEditing(s); }}
            style={{
              padding: '11px 14px', cursor: 'pointer', display: 'flex', gap: 12,
              alignItems: 'center',
              outline: overIdx === i && dragIdx !== null && dragIdx !== i
                ? '2px dashed var(--red-600)' : 'none',
              opacity: dragIdx === i ? 0.5 : 1,
            }}>
            <div onClick={(e) => e.stopPropagation()}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, flexShrink: 0, cursor: 'grab' }}>
              <span className="mono" style={{ fontWeight: 800, fontSize: 14, color: 'var(--red-600)' }}>
                #{i + 1}
              </span>
              <span style={{ display: 'flex', gap: 0 }}>
                <button type="button" title="Đưa lên" disabled={reordering || i === 0}
                  onClick={() => moveStage(i, -1)}
                  style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 2, color: i === 0 ? 'var(--border-strong)' : 'var(--muted)' }}>
                  <Icon name="arrowUp" size={14} />
                </button>
                <button type="button" title="Đưa xuống" disabled={reordering || i === stages.length - 1}
                  onClick={() => moveStage(i, 1)}
                  style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 2, color: i === stages.length - 1 ? 'var(--border-strong)' : 'var(--muted)' }}>
                  <Icon name="arrowDown" size={14} />
                </button>
              </span>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 700, fontSize: 13.5 }}>{s.name}</span>
                {s.hiredStage && <Badge kind="green" dot>Đã tuyển</Badge>}
                {s.slaDays > 0 && <Badge kind="gold">SLA {s.slaDays} ngày</Badge>}
              </div>
              <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
                {s.supportPerson ? `Hỗ trợ: ${s.supportPerson} · ` : ''}
                {s.applicantCount} ứng viên đang ở bước này
              </div>
            </div>
          </div>
        ))}
      </div>

      {hiddenStages.length > 0 && (
        <div style={{ maxWidth: 760, marginTop: 22 }}>
          <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 2 }}>
            Bước đã ẩn ({hiddenStages.length})
          </div>
          <p className="muted" style={{ fontSize: 12.5, margin: '0 0 10px' }}>
            Không hiển thị trên kanban CV và form chọn bước — dữ liệu ứng viên cũ
            giữ nguyên; bấm "Hiện lại" để đưa về quy trình.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {hiddenStages.map((s) => (
              <div key={s.id} className="card"
                onClick={() => setEditing(s)}
                style={{
                  padding: '11px 14px', cursor: 'pointer', display: 'flex',
                  gap: 12, alignItems: 'center', opacity: 0.72,
                }}>
                <Icon name="eye-off" size={16} className="muted" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 13.5 }}>{s.name}</span>
                    <Badge kind="gray">Đã ẩn</Badge>
                    {s.hiredStage && <Badge kind="green" dot>Đã tuyển</Badge>}
                  </div>
                  <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
                    {s.applicantCount} ứng viên (kể cả lưu trữ) từng ở bước này
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm"
                  onClick={(e) => { e.stopPropagation(); unhide(s); }}>
                  <Icon name="eye" size={14} />Hiện lại</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {editing !== null && (
        <StageEditor stage={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }} />
      )}
    </div>
  );
}
