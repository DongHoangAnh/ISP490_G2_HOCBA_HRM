/* Drawer chấm điểm 1 phiếu đánh giá.
   Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
   Công thức hiển thị: docs/CONG_THUC_DANH_GIA.md */
import { useEffect, useState } from 'react';
import { fetchReview, saveReview, reviewAction } from '../../api/reviews';
import { fetchReviewPromotion } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import AnchorList from './AnchorList';
import PromotionForm from '../employees/PromotionForm';
import { GRADE_LABEL, GRADE_KIND, STATE_LABEL, STATE_KIND, AUTO_SOURCE_LABEL, gradeOf, unitLabel } from './util';

const inp = {
  padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', outline: 'none',
  fontFamily: 'inherit', width: '100%',
};

/* Thang chấm 0..max — nút tròn, không dùng select cho nhanh tay. */
function ScorePicker({ value, max, disabled, onPick }) {
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {Array.from({ length: max + 1 }, (_, n) => (
        <button key={n} type="button" disabled={disabled}
          onClick={() => onPick(n)}
          title={n === 0 ? 'Chưa chấm' : `${n} điểm`}
          style={{
            width: 30, height: 30, borderRadius: 8, fontSize: 13,
            fontWeight: value === n ? 800 : 500,
            cursor: disabled ? 'default' : 'pointer',
            border: '1px solid ' + (value === n ? 'var(--red-600)' : 'var(--border-strong)'),
            background: value === n ? 'var(--red-600)' : '#fff',
            color: value === n ? '#fff' : 'var(--muted)',
          }}>{n}</button>
      ))}
    </div>
  );
}

function Metrics({ m, group }) {
  const unit = unitLabel(group);
  const cells = [
    [`Tổng ${unit}`, m.totalUnits],
    ['Đạt chuẩn', m.okUnits],
    ['Tỷ lệ đúng giờ', `${m.punctualPct}%`],
    ['Số lần trễ', m.lateCount],
    ['Ngày nghỉ phép', m.leaveDays],
  ];
  if (group === 'teacher') {
    cells.push(['Chứng chỉ còn hạn', m.certValid]);
    if (m.certExpiring) cells.push(['Sắp hết hạn', m.certExpiring]);
    if (m.certExpired) cells.push(['Hết hạn', m.certExpired]);
  }
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(120px,1fr))',
      gap: 10, padding: 12, background: 'var(--surface-2)',
      border: '1px solid var(--border)', borderRadius: 11, marginBottom: 14,
    }}>
      {cells.map(([label, val]) => (
        <div key={label}>
          <div className="faint" style={{ fontSize: 11 }}>{label}</div>
          <div style={{ fontWeight: 700, fontSize: 15 }}>{val}</div>
        </div>
      ))}
    </div>
  );
}

export default function ReviewDrawer({ reviewId, canPromote, onClose, onSaved }) {
  const [d, setD] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  // Quyết định thăng tiến đã gắn với phiếu này (null = chưa gắn).
  const [promo, setPromo] = useState(null);
  const [promoting, setPromoting] = useState(false);

  useEffect(() => {
    fetchReview(reviewId).then(setD).catch((e) => setErr(e.message));
  }, [reviewId]);

  // Chỉ hỏi khi người dùng thật sự có quyền tạo — người khác không cần biết.
  const loadPromo = () => {
    if (!canPromote) return;
    fetchReviewPromotion(reviewId)
      .then((r) => setPromo(r.promotion)).catch(() => setPromo(null));
  };
  useEffect(loadPromo, [reviewId, canPromote]);

  if (err && !d) {
    return (
      <Modal onClose={onClose}>
        <ModalHeader icon="x" title="Không mở được phiếu" onClose={onClose} />
        <div style={{ padding: 24, fontSize: 13 }}>{err}</div>
      </Modal>
    );
  }
  if (!d) {
    return (
      <Modal onClose={onClose}>
        <ModalHeader icon="star" title="Đang tải phiếu đánh giá…" onClose={onClose} />
        <div style={{ padding: 24 }} className="muted">Vui lòng đợi…</div>
      </Modal>
    );
  }

  const editable = d.state === 'draft';
  /* Tổng điểm tính LẠI ở client để người chấm thấy đổi ngay khi bấm điểm —
     công thức trùng backend: Σ(score/max × weight) / Σweight × 100. */
  const wsum = d.lines.reduce((s, l) => s + (l.maxScore > 0 ? l.weight : 0), 0);
  const acc = d.lines.reduce(
    (s, l) => s + (l.maxScore > 0 ? (l.score / l.maxScore) * l.weight : 0), 0);
  const preview = wsum ? Math.round(acc / wsum * 1000) / 10 : 0;
  /* Phiếu đang chấm: xếp loại tính theo điểm vừa bấm cho khớp con số hiển thị.
     Phiếu đã chốt: dùng nguyên xếp loại backend đã đóng băng. */
  const shownGrade = editable ? gradeOf(preview) : d.grade;

  const setLine = (id, patch) => {
    setD((p) => ({
      ...p,
      lines: p.lines.map((l) => (l.id === id ? { ...l, ...patch } : l)),
    }));
    setDirty(true);
  };
  const setHead = (patch) => { setD((p) => ({ ...p, ...patch })); setDirty(true); };

  const save = async () => {
    setErr(null); setBusy(true);
    try {
      const fresh = await saveReview(d.id, {
        lines: d.lines.map((l) => ({ id: l.id, score: l.score, note: l.note })),
        selfNote: d.selfNote, managerNote: d.managerNote, hrNote: d.hrNote,
      });
      setD(fresh); setDirty(false); onSaved?.();
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); }
    finally { setBusy(false); }
  };

  const act = async (action) => {
    setErr(null); setBusy(true);
    try {
      if (dirty && action !== 'reset') {
        await saveReview(d.id, {
          lines: d.lines.map((l) => ({ id: l.id, score: l.score, note: l.note })),
          selfNote: d.selfNote, managerNote: d.managerNote, hrNote: d.hrNote,
        });
        setDirty(false);
      }
      const fresh = await reviewAction(d.id, action);
      setD(fresh); onSaved?.();
    } catch (e) { setErr(e.message || 'Thao tác thất bại.'); }
    finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <ModalHeader icon="star" onClose={onClose}
        title={d.empName}
        sub={`${d.periodLabel} · ${d.dateFrom} → ${d.dateTo}`
          + (d.department ? ` · ${d.department}` : '')}>
        <Badge kind={STATE_KIND[d.state]}>{STATE_LABEL[d.state]}</Badge>
      </ModalHeader>

      <div style={{ padding: '18px 24px', maxHeight: 'min(72vh, calc(100vh - 200px))', overflowY: 'auto' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14,
          padding: '12px 16px', background: 'var(--red-50)',
          border: '1px solid var(--red-100, var(--border))', borderRadius: 12,
        }}>
          <div>
            <div className="faint" style={{ fontSize: 11 }}>Tổng điểm (thang 100)</div>
            <div style={{ fontSize: 26, fontWeight: 800, lineHeight: 1.1 }}>{preview}</div>
          </div>
          <div>
            <div className="faint" style={{ fontSize: 11 }}>Xếp loại</div>
            <div style={{ marginTop: 3 }}>
              <Badge kind={GRADE_KIND[shownGrade] || 'gray'}>
                {GRADE_LABEL[shownGrade] || '—'}
              </Badge>
            </div>
          </div>
          {editable && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              style={{ marginLeft: 'auto' }} onClick={() => act('compute')}>
              <Icon name="rotateCcw" size={14} />Tính lại chỉ số</button>
          )}
        </div>

        <Metrics m={d.metrics} group={d.roleGroup} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {d.lines.map((l) => (
            <div key={l.id} className="card" style={{ padding: '11px 14px' }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ display: 'flex', gap: 7, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 13.5 }}>{l.name}</span>
                    <Badge kind="gray">{l.weight}%</Badge>
                    {l.isAuto && (
                      <Badge kind="teal">
                        Tự động · {AUTO_SOURCE_LABEL[l.autoSource] || ''}
                      </Badge>
                    )}
                    {l.isAuto && l.manualOverride && (
                      <Badge kind="amber">Quản lý sửa đè</Badge>
                    )}
                  </div>
                  {l.guideline && (
                    <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
                      {l.guideline}
                    </div>
                  )}
                  {l.isAuto && (
                    <div className="faint" style={{ fontSize: 11.5, marginTop: 3 }}>
                      Hệ thống đề xuất: {l.autoScore}/{l.maxScore}
                      {l.autoScore === 0 && ' (thiếu dữ liệu — cần chấm tay)'}
                    </div>
                  )}
                  {/* Mốc hành vi ngay tại chỗ bấm điểm — người chấm không phải
                      rời phiếu sang tab hướng dẫn để nhớ 4 khác 3 ở chỗ nào. */}
                  {l.anchors?.length > 0 && (
                    <details style={{ marginTop: 5 }}>
                      <summary style={{
                        cursor: 'pointer', fontSize: 12, fontWeight: 600,
                        color: 'var(--red-700, var(--ink))',
                      }}>Mốc chấm điểm</summary>
                      <div style={{ marginTop: 6 }}>
                        <AnchorList anchors={l.anchors} current={l.score} />
                      </div>
                    </details>
                  )}
                </div>
                <ScorePicker value={l.score} max={l.maxScore} disabled={!editable}
                  onPick={(n) => setLine(l.id, { score: n })} />
              </div>
              {editable && (
                <input style={{ ...inp, marginTop: 8 }} value={l.note || ''}
                  placeholder="Ghi chú cho tiêu chí này (không bắt buộc)"
                  onChange={(e) => setLine(l.id, { note: e.target.value })} />
              )}
              {!editable && l.note && (
                <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>{l.note}</div>
              )}
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Nhân viên tự đánh giá</span>
            <textarea style={{ ...inp, minHeight: 56, resize: 'vertical' }}
              disabled={!editable} value={d.selfNote || ''}
              onChange={(e) => setHead({ selfNote: e.target.value })} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>
              Nhận xét của quản lý * (bắt buộc trước khi chốt)
            </span>
            <textarea style={{ ...inp, minHeight: 64, resize: 'vertical' }}
              disabled={!editable} value={d.managerNote || ''}
              onChange={(e) => setHead({ managerNote: e.target.value })} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span className="faint" style={{ fontSize: 11 }}>Ý kiến HR</span>
            <textarea style={{ ...inp, minHeight: 48, resize: 'vertical' }}
              disabled={!editable} value={d.hrNote || ''}
              onChange={(e) => setHead({ hrNote: e.target.value })} />
          </label>
        </div>

        {/* Thăng tiến — nhập liệu gộp về đây từ 2026-08-12 (trước nằm trong
            hồ sơ NV). Chỉ mở khi phiếu ĐÃ CHỐT: phiếu là căn cứ của quyết
            định, gắn vào bản nháp thì căn cứ có thể đổi sau lưng. */}
        {canPromote && d.state !== 'draft' && (
          <div style={{
            marginTop: 16, padding: '12px 16px', borderRadius: 12,
            border: '1px solid var(--border)', background: 'var(--gold-50, #fdf8ec)',
            display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
          }}>
            <Icon name="arrowUp" size={16} />
            {promo ? (
              <div style={{ fontSize: 12.5 }}>
                Đã có quyết định thăng tiến từ phiếu này:{' '}
                <b>{promo.toJob || '—'}</b>
                {promo.date ? ` · hiệu lực ${promo.date}` : ''}
                {promo.decisionRef ? ` · ${promo.decisionRef}` : ''}
              </div>
            ) : (
              <>
                <div style={{ fontSize: 12.5, flex: 1, minWidth: 200 }}>
                  Kết quả kỳ này đủ căn cứ để điều chỉnh chức vụ hoặc mức lương?
                </div>
                <button className="btn btn-soft btn-sm" disabled={busy}
                  onClick={() => setPromoting(true)}>
                  <Icon name="arrowUp" size={14} />Tạo thăng tiến</button>
              </>
            )}
          </div>
        )}

        {err && <div style={{ marginTop: 12, fontSize: 12.5, color: 'var(--red-700)' }}>{err}</div>}

        <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          {d.state !== 'draft' && d.canPublish && (
            <button className="btn btn-ghost btn-sm" disabled={busy}
              style={{ marginRight: 'auto' }} onClick={() => act('reset')}>
              <Icon name="rotateCcw" size={14} />Mở lại phiếu</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Đóng</button>
          {editable && (
            <button className="btn btn-ghost btn-sm" disabled={busy || !dirty}
              onClick={save}>{busy ? 'Đang lưu…' : 'Lưu nháp'}</button>
          )}
          {editable && (
            <button className="btn btn-primary btn-sm" disabled={busy}
              onClick={() => act('confirm')}>
              <Icon name="check" size={14} />Chốt đánh giá</button>
          )}
          {d.state === 'confirmed' && d.canPublish && (
            <button className="btn btn-primary btn-sm" disabled={busy}
              onClick={() => act('publish')}>
              <Icon name="bell" size={14} />Công bố cho nhân viên</button>
          )}
        </div>
      </div>

      {promoting && (
        <PromotionForm
          /* payload phiếu chỉ có TÊN phòng ban, không có id → để trống, form
             mặc định "Giữ nguyên phòng ban". */
          det={{ id: d.empId, jobTitle: d.jobTitle || '', dep: '' }}
          reviewId={d.id}
          reasonHint={`Đánh giá ${d.periodLabel}${d.grade ? ` — xếp loại ${String(d.grade).toUpperCase()}` : ''}`}
          onClose={() => setPromoting(false)}
          onSaved={() => { setPromoting(false); loadPromo(); onSaved?.(); }} />
      )}
    </Modal>
  );
}
