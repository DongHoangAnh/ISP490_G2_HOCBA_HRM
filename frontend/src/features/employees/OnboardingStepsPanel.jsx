/* Tab Thử việc theo QUY TRÌNH BƯỚC ĐỘNG (hb.onboarding.step) — thay 3 cổng
   + thử giảng cứng. Đọc det.onboarding (payload _onb_emp_item), mỗi thao tác
   trả item mới → merge lại det qua onUpdated. onUpdated vắng = chỉ xem
   (Profile self-service). Owner: Tân.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md */
import { useState } from 'react';
import {
  completeOnbStep, evaluateOnbStep, setOnbStepDue, assignOnbTemplate,
  fetchOnbTemplates, finalizeOnboarding,
} from '../../api/onboarding';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ConfirmModal from '../../components/ConfirmModal';
import { EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';

const TODAY = new Date().toISOString().slice(0, 10);

/* Trạng thái hiển thị 1 bước: [nhãn, kind badge, màu chấm] */
function stepBadge(s) {
  if (s.state === 'done') {
    if (s.result === 'fail') return ['Không đạt', 'red', 'var(--red-600)'];
    if (s.result === 'extend') return ['Gia hạn', 'amber', 'var(--gold-500)'];
    return ['Hoàn thành', 'green', 'var(--green)'];
  }
  if (s.state === 'skipped') return ['Bỏ qua', 'gray', 'var(--border-strong)'];
  if (s.state === 'open') {
    if (s.extendCount > 0) return ['Đang gia hạn', 'amber', 'var(--gold-500)'];
    return ['Đang chờ', 'blue', 'var(--red-600)'];
  }
  return ['Chưa tới lượt', 'gray', 'var(--border-strong)'];
}

const inp = {
  padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', outline: 'none',
  fontFamily: 'inherit',
};

/* yyyy-mm-dd + n ngày → yyyy-mm-dd. Dùng UTC để khỏi lệch 1 ngày khi máy ở
   múi giờ âm (new Date('2026-07-25') là mốc UTC, getDate() lại theo giờ máy). */
function addDays(iso, n) {
  if (!iso) return null;
  const d = new Date(iso + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/* Nội dung hộp xác nhận Gia hạn: nhập số ngày + xem trước hạn mới.
   Nói rõ số ngày này cộng vào CẢ các bước sau, vì đó mới là thứ làm "ngày kết
   thúc thử việc" ở màn Nhận việc lùi ra. */
function ExtendFields({ step, days, setDays }) {
  const n = Number(days);
  const valid = Number.isInteger(n) && n >= 1 && n <= 365;
  const newDue = valid ? addDays(step.dueDate, n) : null;
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <div>
        Gia hạn bước <b>{step.name}</b> — cộng thêm số ngày vào hạn của bước
        này <b>và mọi bước sau</b>.
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 12.5, fontWeight: 600 }}>Gia hạn thêm</span>
        <input type="number" min={1} max={365} value={days}
          onChange={(e) => setDays(e.target.value)}
          style={{ ...inp, width: 90 }} />
        <span style={{ fontSize: 12.5 }}>ngày</span>
      </label>
      {!valid && (
        <div style={{ fontSize: 12, color: 'var(--red-600)' }}>
          Nhập số nguyên từ 1 đến 365.
        </div>
      )}
      {valid && step.dueDate && (
        <div className="muted" style={{ fontSize: 12.5 }}>
          Hạn bước này: {fmtDate(step.dueDate)} → <b>{fmtDate(newDue)}</b>
        </div>
      )}
      {valid && !step.dueDate && (
        <div className="muted" style={{ fontSize: 12.5 }}>
          Bước này không đặt hạn nên hạn của nó giữ nguyên (không có gì để
          cộng); các bước sau vẫn lùi thêm {n} ngày.
        </div>
      )}
    </div>
  );
}

/* Khối hành động cho bước đang mở (canAct). ConfirmModal thay
   window.confirm (quy ước SPA từ đợt dọn timeoff). */
function StepActions({ step, onDone }) {
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [confirm, setConfirm] = useState(null); // 'extend' | 'fail' | null
  // Số ngày gia hạn — mặc định 14 (nửa tháng) chỉ là gợi ý cho đỡ gõ, HR sửa
  // được. Backend mới là chỗ chốt khoảng hợp lệ.
  const [days, setDays] = useState(14);
  const run = async (fn) => {
    setErr(null); setBusy(true);
    try { onDone(await fn()); } catch (e) {
      setErr(e.code === 'forbidden'
        ? 'Bạn không có quyền xử lý bước này.'
        : (e.message || 'Thao tác bị từ chối.'));
      throw e; // để ConfirmModal (nếu đang mở) hiện lỗi + giữ modal
    } finally { setBusy(false); }
  };
  const doEvaluate = (result) =>
    run(() => evaluateOnbStep(step.id, {
      result, note: note.trim(),
      ...(result === 'extend' ? { days: Number(days) } : {}),
    }));
  const evaluate = (result) => {
    setErr(null);
    if (result === 'fail' && !note.trim()) {
      setErr('Cần nhập nhận xét khi Không đạt.'); return;
    }
    if (result === 'pass') { doEvaluate('pass').catch(() => {}); return; }
    setConfirm(result);
  };
  return (
    <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px dashed var(--border)' }}>
      {step.stepType === 'evaluation' ? (
        <>
          <input value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="Nhận xét đánh giá (bắt buộc khi Không đạt)"
            style={{ ...inp, width: '100%', marginBottom: 8 }} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" disabled={busy}
              style={{ background: 'var(--green)', borderColor: 'var(--green)' }}
              onClick={() => evaluate('pass')}>
              <Icon name="checkCircle" size={14} />Đạt</button>
            <button className="btn btn-ghost btn-sm" disabled={busy}
              style={{ color: 'var(--gold-600)', borderColor: 'var(--gold-200)' }}
              onClick={() => evaluate('extend')}>
              <Icon name="clock" size={14} />Gia hạn</button>
            <button className="btn btn-ghost btn-sm" disabled={busy}
              style={{ color: 'var(--red-700)', borderColor: 'var(--red-100)' }}
              onClick={() => evaluate('fail')}>
              <Icon name="x" size={14} />Không đạt</button>
            {busy && <span className="muted" style={{ fontSize: 12, alignSelf: 'center' }}>Đang lưu…</span>}
          </div>
        </>
      ) : (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="Ghi chú (tuỳ chọn)" style={{ ...inp, flex: 1, minWidth: 180 }} />
          <button className="btn btn-primary btn-sm" disabled={busy}
            onClick={() => run(() => completeOnbStep(step.id, { note: note.trim() })).catch(() => {})}>
            <Icon name="checkCircle" size={14} />Hoàn thành</button>
          {busy && <span className="muted" style={{ fontSize: 12 }}>Đang lưu…</span>}
        </div>
      )}
      {err && <div style={{ marginTop: 7, fontSize: 12, color: 'var(--red-600)' }}>{err}</div>}
      {confirm && (
        <ConfirmModal
          title={confirm === 'fail' ? 'Xác nhận Không đạt' : 'Gia hạn thử việc'}
          message={confirm === 'fail'
            ? `Đánh dấu KHÔNG ĐẠT bước "${step.name}" sẽ chuyển nhân viên sang offboarding. Tiếp tục?`
            : <ExtendFields step={step} days={days} setDays={setDays} />}
          confirmLabel={confirm === 'fail' ? 'Không đạt' : 'Gia hạn'}
          onConfirm={() => doEvaluate(confirm).then(() => setConfirm(null))}
          onClose={() => setConfirm(null)} />
      )}
    </div>
  );
}

/* Sửa hạn 1 bước (chỉ HR Manager). */
function DueEditor({ step, onDone }) {
  const [open, setOpen] = useState(false);
  const [val, setVal] = useState(step.dueDate || '');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  if (!open) {
    return (
      <button type="button" title="Sửa hạn" onClick={() => setOpen(true)}
        style={{
          border: 'none', background: 'none', cursor: 'pointer', padding: 0,
          display: 'inline-flex', verticalAlign: 'middle', color: 'var(--faint)',
        }}>
        <Icon name="edit" size={13} />
      </button>
    );
  }
  const save = async () => {
    setBusy(true); setErr(null);
    try { onDone(await setOnbStepDue(step.id, val || null)); setOpen(false); }
    catch (e) { setErr(e.message || 'Không sửa được hạn.'); }
    finally { setBusy(false); }
  };
  return (
    <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      <input type="date" value={val} onChange={(e) => setVal(e.target.value)}
        style={{ ...inp, padding: '4px 8px', fontSize: 12 }} />
      <button className="btn btn-primary btn-sm" disabled={busy} onClick={save}>Lưu</button>
      <button className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>Huỷ</button>
      {err && <span style={{ fontSize: 11.5, color: 'var(--red-600)' }}>{err}</span>}
    </span>
  );
}

/* Đổi quy trình (chỉ HR Manager) — load template lazy khi bấm. */
function TemplatePicker({ empId, currentId, onDone }) {
  const [open, setOpen] = useState(false);
  const [tpls, setTpls] = useState(null);
  const [sel, setSel] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const start = async () => {
    setOpen(true); setErr(null);
    try {
      const d = await fetchOnbTemplates();
      setTpls(d.templates.filter((t) => t.active !== false));
    } catch (e) { setErr(e.message); }
  };
  const [confirming, setConfirming] = useState(false);
  const apply = async () => {
    try {
      onDone(await assignOnbTemplate(empId, Number(sel)));
      setConfirming(false); setOpen(false);
    } catch (e) {
      setConfirming(false);
      setErr(e.message || 'Không đổi được quy trình.');
      throw e;
    } finally { setBusy(false); }
  };
  if (!open) {
    return (
      <button className="btn btn-ghost btn-sm" onClick={start}>
        <Icon name="settings" size={14} />Đổi quy trình</button>
    );
  }
  return (
    <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      {!tpls && !err && <span className="muted" style={{ fontSize: 12 }}>Đang tải…</span>}
      {tpls && (
        <>
          <select value={sel} onChange={(e) => setSel(e.target.value)} style={{ ...inp, padding: '5px 8px', fontSize: 12.5 }}>
            <option value="">— Chọn quy trình —</option>
            {tpls.map((t) => (
              <option key={t.id} value={t.id} disabled={t.id === currentId}>
                {t.name}{t.id === currentId ? ' (hiện tại)' : ''}
              </option>
            ))}
          </select>
          <button className="btn btn-primary btn-sm" disabled={busy || !sel}
            onClick={() => setConfirming(true)}>Áp dụng</button>
        </>
      )}
      <button className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>Huỷ</button>
      {err && <span style={{ fontSize: 12, color: 'var(--red-600)' }}>{err}</span>}
      {confirming && (
        <ConfirmModal title="Đổi quy trình nhận việc"
          message="Đổi quy trình sẽ bỏ các bước CHƯA làm và nối bước của quy trình mới vào sau. Bước đã hoàn thành giữ lại làm lịch sử. Tiếp tục?"
          confirmLabel="Đổi quy trình"
          onConfirm={apply}
          onClose={() => setConfirming(false)} />
      )}
    </span>
  );
}

/* Chốt hoàn tất nhận việc → Chính thức. Chỉ hiện khi backend trả canFinalize
   (HR Manager + chuỗi đã xong, không bước nào Không đạt). Cần thiết vì quy
   trình không có bước "Đạt → lên chính thức" — như Thử việc Giáo viên — thì
   chạy hết chuỗi cũng không có gì chuyển trạng thái nhân sự. */
function FinalizeButton({ empId, onDone }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const run = async () => {
    setErr(null); setBusy(true);
    try { onDone(await finalizeOnboarding(empId)); } catch (e) {
      setErr(e.code === 'forbidden'
        ? 'Chỉ HR Manager được chuyển nhân viên lên Chính thức.'
        : (e.message || 'Thao tác bị từ chối.'));
      throw e; // giữ modal mở để người dùng đọc lỗi
    } finally { setBusy(false); }
  };
  return (
    <div style={{ marginTop: 14, padding: '12px 16px', background: 'var(--green-bg)', border: '1px solid var(--border)', borderRadius: 11 }}>
      <div className="between" style={{ flexWrap: 'wrap', gap: 8 }}>
        <div style={{ fontSize: 13 }}>
          <b>Đã xong toàn bộ bước nhận việc.</b>
          <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
            Quy trình này không có bước tự chuyển trạng thái — HR chốt để nhân
            viên lên Chính thức.
          </div>
        </div>
        <button className="btn btn-primary btn-sm" disabled={busy}
          style={{ background: 'var(--green)', borderColor: 'var(--green)' }}
          onClick={() => setConfirming(true)}>
          <Icon name="checkCircle" size={14} />Chuyển chính thức</button>
      </div>
      {err && <div style={{ fontSize: 12, color: 'var(--red-600)', marginTop: 6 }}>{err}</div>}
      {confirming && (
        <ConfirmModal title="Chuyển sang nhân viên chính thức"
          message="Nhân viên sẽ lên Chính thức kể từ hôm nay, kèm mốc thăng tiến và nhắc việc tạo hợp đồng chính thức. Tiếp tục?"
          confirmLabel="Chuyển chính thức"
          onConfirm={run}
          onClose={() => setConfirming(false)} />
      )}
    </div>
  );
}

export default function OnboardingStepsPanel({ det, isMgr, onUpdated }) {
  const onb = det.onboarding || { steps: [], progress: { done: 0, total: 0 } };
  const steps = onb.steps || [];
  // Thao tác trả item onboarding mới → merge vào det cho drawer/profile.
  // "Chuyển chính thức" (và bước Đánh giá có cờ Đạt → lên chính thức) đổi
  // TRẠNG THÁI nhân sự, nên phải nhấc trạng thái mới lên tầng det: nhét riêng
  // vào det.onboarding thì chip ở header drawer vẫn đọc det.statusKey cũ và
  // còn hiện "Thử việc".
  const patch = (resp) => onUpdated && onUpdated({
    ...det,
    ...(resp && resp.statusKey
      ? { status: resp.status, statusKey: resp.statusKey }
      : {}),
    onboarding: resp,
  });

  if (!steps.length) {
    return (
      <div>
        <EmptyState>
          Chưa có quy trình nhận việc cho nhân sự này. Kiểm tra <b>Ngày bắt đầu
          thử việc</b> và các trục phân loại (loại vị trí / hình thức làm việc /
          loại nhân sự) để hệ thống tự gán; hoặc HR Manager gán tay bên dưới.
        </EmptyState>
        {isMgr && onUpdated && (
          <div style={{ marginTop: 12, textAlign: 'center' }}>
            <TemplatePicker empId={det.id} currentId={onb.templateId} onDone={patch} />
          </div>
        )}
      </div>
    );
  }

  const pct = onb.progress.total
    ? Math.round((onb.progress.done / onb.progress.total) * 100) : 0;

  return (
    <div>
      {/* Header: quy trình + tiến độ */}
      <div className="card" style={{ padding: '14px 16px', marginBottom: 14 }}>
        <div className="between" style={{ flexWrap: 'wrap', gap: 8 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 13.5 }}>
              {onb.templateName || 'Quy trình nhận việc'}
            </div>
            <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
              {onb.progress.done}/{onb.progress.total} bước
              {onb.current ? ` · đang: ${onb.current.name}` : ''}
            </div>
          </div>
          {isMgr && onUpdated && (
            <TemplatePicker empId={det.id} currentId={onb.templateId} onDone={patch} />
          )}
        </div>
        <div style={{ height: 6, borderRadius: 4, background: 'var(--surface-2)', marginTop: 10, overflow: 'hidden' }}>
          <div style={{ width: `${pct}%`, height: '100%', borderRadius: 4, background: 'var(--green)' }} />
        </div>
      </div>

      {/* Timeline dọc các bước */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {steps.map((s, i) => {
          const [lbl, kind, color] = stepBadge(s);
          const overdue = s.state === 'open' && s.dueDate && s.dueDate < TODAY;
          return (
            <div key={s.id} className="card"
              style={{ padding: '12px 14px', opacity: s.state === 'skipped' ? 0.55 : 1 }}>
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{
                  width: 26, height: 26, borderRadius: '50%', background: color,
                  color: '#fff', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: 12, fontWeight: 800, flexShrink: 0, marginTop: 2,
                }}>
                  {s.state === 'done' && s.result !== 'fail' ? '✓'
                    : s.result === 'fail' ? '✗'
                      : s.state === 'skipped' ? '—'
                        : s.extendCount > 0 ? '↻' : i + 1}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="between" style={{ flexWrap: 'wrap', gap: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 13.5 }}>
                      {s.name}
                      <span className="faint" style={{ fontWeight: 500, fontSize: 11.5, marginLeft: 8 }}>
                        {s.stepType === 'evaluation' ? 'Đánh giá' : 'Việc cần làm'}
                        {s.extendCount > 0 ? ` · đã gia hạn ×${s.extendCount}` : ''}
                        {s.extendDays > 0 ? ` (+${s.extendDays} ngày)` : ''}
                      </span>
                      {s.isIndependent && (
                        <span style={{ marginLeft: 8 }}>
                          <Badge kind="teal">Không ràng buộc</Badge>
                        </span>
                      )}
                    </span>
                    <Badge kind={kind} dot>{lbl}</Badge>
                  </div>
                  <div className="muted" style={{ fontSize: 12, marginTop: 4, display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
                    {s.dueDate && s.state !== 'done' && s.state !== 'skipped' && (
                      <span className="mono" style={overdue ? { color: 'var(--red-600)' } : undefined}>
                        hạn {fmtDate(s.dueDate)}{overdue && ' ⚠'}
                        {isMgr && onUpdated && s.state === 'open' && (
                          <span style={{ marginLeft: 6 }}><DueEditor step={s} onDone={patch} /></span>
                        )}
                      </span>
                    )}
                    {s.doneDate && <span className="mono">{fmtDate(s.doneDate)}</span>}
                    {s.doneBy && <span>bởi {s.doneBy}</span>}
                  </div>
                  {s.note && <div className="faint" style={{ fontSize: 12, marginTop: 4 }}>{s.note}</div>}
                  {s.resultNote && (
                    <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>
                      <Icon name="edit" size={12} className="faint" /> {s.resultNote}
                    </div>
                  )}
                  {s.canAct && onUpdated && <StepActions step={s} onDone={patch} />}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {onb.canFinalize && onUpdated && (
        <FinalizeButton empId={det.id} onDone={patch} />
      )}

      {onb.officialDate && (
        <div style={{ marginTop: 14, padding: '12px 16px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 11, fontSize: 13 }}>
          Chính thức từ <b>{fmtDate(onb.officialDate)}</b>
        </div>
      )}
    </div>
  );
}
