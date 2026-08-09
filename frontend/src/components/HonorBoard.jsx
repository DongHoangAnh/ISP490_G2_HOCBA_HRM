/* ============================================================
   Bảng vinh danh — khung trên cùng của dashboard chung.
   Khách (họp 2026-08-07, 10:33): "hiển thị lên dashboard chung của tất cả
   mọi người… người ta vào đấy, người ta sẽ nhìn thấy cái đấy đầu tiên.
   Mình sẽ có một cái khung ở trên cùng kiểu vinh danh".
   Đặt ở CẢ Dashboard (vai trò quản lý) lẫn Hồ sơ của tôi (nhân viên
   thường không thấy Dashboard — đó mới là màn đầu tiên của họ).
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import {
  fetchHonorBoard, createHonorEntry, archiveHonorEntry,
} from '../api/career';
import { fetchEmployees } from '../api/employees';
import Icon from './Icon';
import Avatar from './Avatar';
import Badge from './Badge';
import Modal from './Modal';
import ModalHeader from './ModalHeader';
import ConfirmModal from './ConfirmModal';

const CATEGORY_KIND = {
  promotion: 'gold', achievement: 'green', tenure: 'blue', other: 'gray',
};

const inp = {
  padding: '7px 10px', borderRadius: 8, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', fontFamily: 'inherit',
  width: '100%',
};

export default function HonorBoard() {
  const [board, setBoard] = useState(null);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(null);

  useEffect(() => {
    // Lỗi ở đây chỉ ẩn khung, không được làm hỏng cả trang chủ.
    fetchHonorBoard().then(setBoard).catch(() => setBoard(null));
  }, []);

  if (!board) return null;
  const empty = board.entries.length === 0 && board.ranking.length === 0;
  // Bảng trống với nhân viên thường = một ô chết ngay đầu trang → ẩn hẳn.
  if (empty && !board.canManage) return null;
  // Với HR thì vẫn phải có lối thêm, nhưng không được ngốn nguyên khung cao
  // ở chỗ đắt nhất của trang — thu về một dải mỏng.
  if (empty) {
    return (
      <div className="card" style={{
        marginBottom: 16, padding: '10px 16px',
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        background: 'linear-gradient(120deg, var(--red-50), #fff 60%)',
      }}>
        <Icon name="award" size={16} />
        <b style={{ fontSize: 13 }}>Bảng vinh danh</b>
        <span className="sub">{board.periodLabel}</span>
        <span className="muted" style={{ fontSize: 12.5, flex: 1 }}>
          Kỳ này chưa vinh danh ai — bổ nhiệm chức vụ mới sẽ tự lên bảng.
        </span>
        <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
          <Icon name="plus" size={13} />Thêm vinh danh</button>
        {adding && (
          <HonorForm onClose={() => setAdding(false)}
            onSaved={(b) => { setBoard(b); setAdding(false); }} />
        )}
      </div>
    );
  }

  // Lỗi ném ra để ConfirmModal tự hiện — nó quản lý busy/err của chính nó.
  const doRemove = async () => {
    setBoard(await archiveHonorEntry(removing.id));
    setRemoving(null);
  };

  return (
    <div className="card" style={{
      marginBottom: 16,
      background: 'linear-gradient(120deg, var(--red-50), #fff 60%)',
    }}>
      <div className="card-head">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Icon name="award" size={18} />Bảng vinh danh
        </h3>
        <span className="sub">
          {board.periodLabel}
          {!board.isCurrent && ' · kỳ gần nhất có dữ liệu'}
        </span>
        {board.canManage && (
          <div className="actions">
            <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
              <Icon name="plus" size={13} />Thêm vinh danh</button>
          </div>
        )}
      </div>

      <div style={{
        padding: '14px 16px 18px', display: 'grid', gap: 16,
        gridTemplateColumns: board.ranking.length ? '2fr 1fr' : '1fr',
      }}>
        <div>
          {board.entries.length === 0 ? (
            <div className="empty">
              Kỳ này chưa vinh danh ai. Bổ nhiệm chức vụ mới sẽ tự lên bảng.
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {board.entries.map((h) => (
                <div key={h.id} style={{
                  flex: '1 1 260px', minWidth: 240, background: '#fff',
                  border: '1px solid var(--border)', borderRadius: 12,
                  padding: '12px 14px', display: 'flex', gap: 12,
                  position: 'relative',
                }}>
                  <Avatar emp={{ id: h.empId, name: h.empName, hasImg: h.hasImg }} size={44} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 700, fontSize: 13.5 }}>{h.empName}</span>
                      {h.rank > 0 && <Badge kind="gold">Hạng {h.rank}</Badge>}
                    </div>
                    <div style={{ fontSize: 13, marginTop: 3, fontWeight: 600, color: 'var(--red-700)' }}>
                      {h.title}
                    </div>
                    <div className="faint" style={{ fontSize: 12, marginTop: 3 }}>
                      {h.dep || '—'} · {h.categoryLabel}
                    </div>
                    {h.description && (
                      <div className="muted" style={{ fontSize: 12, marginTop: 5 }}>{h.description}</div>
                    )}
                  </div>
                  {board.canManage && (
                    <button className="icon-btn" title="Gỡ khỏi bảng"
                      style={{ position: 'absolute', top: 6, right: 6 }}
                      onClick={() => setRemoving(h)}>
                      <Icon name="x" size={15} className="faint" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {board.ranking.length > 0 && (
          <div>
            <div style={{
              fontWeight: 700, fontSize: 12, color: 'var(--muted)',
              textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 8,
            }}>
              Đánh giá xuất sắc trong kỳ
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {board.ranking.map((r, i) => (
                <div key={r.empId} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  background: '#fff', border: '1px solid var(--border)',
                  borderRadius: 10, padding: '8px 12px',
                }}>
                  <span style={{ fontWeight: 800, fontSize: 15, color: 'var(--gold-600, #a8760a)', width: 18 }}>
                    {i + 1}
                  </span>
                  <Avatar emp={{ id: r.empId, name: r.empName, hasImg: r.hasImg }} size={30} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 12.5, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.empName}
                    </div>
                    <div className="faint" style={{ fontSize: 11 }}>{r.dep || '—'}</div>
                  </div>
                  {/* Điểm chỉ hiện với vai trò quản lý — vinh danh là nêu tên,
                      không phải công bố bảng điểm cá nhân cho toàn công ty. */}
                  {r.score != null && (
                    <span className="mono" style={{ fontWeight: 700, fontSize: 12.5 }}>{r.score}%</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {adding && (
        <HonorForm onClose={() => setAdding(false)}
          onSaved={(b) => { setBoard(b); setAdding(false); }} />
      )}
      {removing && (
        <ConfirmModal icon="award"
          title="Gỡ khỏi bảng vinh danh"
          message={`Gỡ "${removing.title}" của ${removing.empName} khỏi bảng? Bản ghi vẫn được lưu lại.`}
          confirmLabel="Gỡ"
          onConfirm={doRemove} onClose={() => setRemoving(null)} />
      )}
    </div>
  );
}

/* Form thêm vinh danh — modal nhỏ ngay trong khung, không đẻ thêm màn hình. */
function HonorForm({ onClose, onSaved }) {
  const [people, setPeople] = useState([]);
  const [form, setForm] = useState({
    employeeId: '', title: '', category: 'achievement',
    description: '', rank: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    fetchEmployees().then((d) => setPeople(d.employees || [])).catch(() => {});
  }, []);

  const save = async () => {
    setErr(null); setBusy(true);
    try {
      onSaved(await createHonorEntry({
        employeeId: Number(form.employeeId) || 0,
        title: form.title.trim(),
        category: form.category,
        description: form.description.trim(),
        rank: Number(form.rank) || 0,
      }));
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  const ok = form.employeeId && form.title.trim();
  return (
    <Modal onClose={onClose}>
      <ModalHeader icon="award" title="Thêm vinh danh" onClose={onClose} />
      <div style={{ padding: '18px 22px', display: 'grid', gap: 14 }}>
        <Field label="Nhân viên">
          <select style={inp} value={form.employeeId}
            onChange={(e) => setForm({ ...form, employeeId: e.target.value })}>
            <option value="">— Chọn nhân viên —</option>
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code ? `${p.code} · ` : ''}{p.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Danh hiệu">
          <input style={inp} value={form.title} autoFocus
            placeholder="VD: Nhân viên xuất sắc tháng"
            onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
          <Field label="Nhóm">
            <select style={inp} value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option value="achievement">Thành tích</option>
              <option value="promotion">Bổ nhiệm / Thăng chức</option>
              <option value="tenure">Kỷ niệm gắn bó</option>
              <option value="other">Khác</option>
            </select>
          </Field>
          <Field label="Hạng (0 = không xếp)">
            <input style={inp} type="number" min="0" value={form.rank}
              onChange={(e) => setForm({ ...form, rank: e.target.value })} />
          </Field>
        </div>
        <Field label="Mô tả">
          <textarea style={{ ...inp, minHeight: 70, resize: 'vertical' }}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        {err && <div className="muted" style={{ color: 'var(--red-600)', fontSize: 12.5 }}>{err}</div>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn btn-ghost" onClick={onClose}>Huỷ</button>
          <button className="btn btn-primary" disabled={!ok || busy} onClick={save}>
            {busy ? 'Đang lưu…' : 'Vinh danh'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 5, color: '#374151' }}>{label}</div>
      {children}
    </div>
  );
}
