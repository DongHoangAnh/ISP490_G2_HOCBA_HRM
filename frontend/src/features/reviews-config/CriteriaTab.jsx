/* Bảng câu hỏi đánh giá của MỘT nhóm (Giảng viên hoặc Nhân viên văn phòng).
   Owner: Việt.
   Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md */
import { Fragment, useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';

const inp = {
  width: '100%', padding: '7px 10px', borderRadius: 9,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const num = { ...inp, textAlign: 'right' };
const area = { ...inp, minHeight: 64, resize: 'vertical', lineHeight: 1.5 };

const th = {
  fontSize: 11, fontWeight: 700, color: 'var(--muted)',
  textTransform: 'uppercase', letterSpacing: '.3px', textAlign: 'left',
  padding: '8px 10px', whiteSpace: 'nowrap',
};

/* Câu hỏi trống để HR điền — trọng số 0 để không phá tổng 100 đang đúng. */
const blankRow = () => ({
  id: 0, code: '', name: '', weight: 0, maxScore: 5, autoSource: 'none',
  guideline: '', anchorTop: '', anchorMid: '', anchorLow: '', active: true,
});

function IconBtn({ name, title, onClick, disabled }) {
  return (
    <button type="button" className="btn btn-ghost" title={title}
      onClick={onClick} disabled={disabled}
      style={{ padding: '4px 7px', opacity: disabled ? 0.35 : 1 }}>
      <Icon name={name} size={15} />
    </button>
  );
}

export default function CriteriaTab({ rows, setRows, autoSources, maxScoreMin, maxScoreMax }) {
  const [openId, setOpenId] = useState(null);

  const patch = (idx, vals) => setRows(
    rows.map((r, i) => (i === idx ? { ...r, ...vals } : r)));

  const move = (idx, dir) => {
    const to = idx + dir;
    if (to < 0 || to >= rows.length) return;
    const next = rows.slice();
    [next[idx], next[to]] = [next[to], next[idx]];
    setRows(next);
  };

  const add = () => {
    const row = blankRow();
    // Khoá mở rộng cho câu hỏi mới (chưa có id): dùng vị trí trong danh sách.
    setRows([...rows, row]);
    setOpenId('new-' + rows.length);
  };

  const keyOf = (r, i) => (r.id ? 'id-' + r.id : 'new-' + i);

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
            <th style={{ ...th, width: 34 }}>#</th>
            <th style={th}>Câu hỏi đánh giá</th>
            <th style={{ ...th, width: 108, textAlign: 'right' }}>Trọng số (%)</th>
            <th style={{ ...th, width: 104, textAlign: 'right' }}>Điểm tối đa</th>
            <th style={{ ...th, width: 190 }}>Nguồn chấm</th>
            <th style={{ ...th, width: 132, textAlign: 'center' }}>Thao tác</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const k = keyOf(r, i);
            const open = openId === k;
            const auto = r.autoSource && r.autoSource !== 'none';
            return (
              <Fragment key={k}>
                <tr style={{
                  borderBottom: '1px solid var(--border)',
                  background: r.active ? '#fff' : 'var(--surface-2)',
                  opacity: r.active ? 1 : 0.65,
                }}>
                  <td style={{ padding: '8px 10px', color: 'var(--muted)', fontSize: 12.5 }}>{i + 1}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <input style={inp} value={r.name} placeholder="Tên câu hỏi…"
                      onChange={(e) => patch(i, { name: e.target.value })} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                      {r.code
                        ? <span className="faint" style={{ fontSize: 11 }}>{r.code}</span>
                        : <span className="faint" style={{ fontSize: 11 }}>mã tự sinh khi lưu</span>}
                      {!r.active && <Badge kind="gray">Đã tắt</Badge>}
                      <button type="button" className="btn btn-ghost"
                        style={{ padding: '2px 6px', fontSize: 12 }}
                        onClick={() => setOpenId(open ? null : k)}>
                        <Icon name={open ? 'chevD' : 'chevR'} size={13} />
                        {auto ? ' Hướng dẫn' : ' Hướng dẫn & mốc chấm'}
                      </button>
                    </div>
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <input type="number" min="0" max="100" step="0.5" style={num}
                      value={r.weight}
                      onChange={(e) => patch(i, { weight: Number(e.target.value || 0) })} />
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <input type="number" min={maxScoreMin} max={maxScoreMax} step="1"
                      style={num} value={r.maxScore}
                      onChange={(e) => patch(i, { maxScore: Number(e.target.value || 0) })} />
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <select style={inp} value={r.autoSource}
                      onChange={(e) => patch(i, { autoSource: e.target.value })}>
                      {autoSources.map((s) => (
                        <option key={s.key} value={s.key}>{s.label}</option>
                      ))}
                    </select>
                  </td>
                  <td style={{ padding: '8px 10px', textAlign: 'center', whiteSpace: 'nowrap' }}>
                    <IconBtn name="arrowUp" title="Lên trên"
                      onClick={() => move(i, -1)} disabled={i === 0} />
                    <IconBtn name="arrowDown" title="Xuống dưới"
                      onClick={() => move(i, 1)} disabled={i === rows.length - 1} />
                    <IconBtn name={r.active ? 'eye' : 'lock'}
                      title={r.active ? 'Tắt câu hỏi này' : 'Bật lại câu hỏi này'}
                      onClick={() => patch(i, { active: !r.active })} />
                  </td>
                </tr>
                {open && (
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <td />
                    <td colSpan={5} style={{ padding: '4px 10px 14px' }}>
                      <div style={{ display: 'grid', gap: 10 }}>
                        <label style={{ display: 'grid', gap: 4 }}>
                          <span style={th}>Hướng dẫn chấm</span>
                          <textarea style={area} value={r.guideline}
                            onChange={(e) => patch(i, { guideline: e.target.value })} />
                        </label>
                        {auto ? (
                          <div className="muted" style={{ fontSize: 12.5 }}>
                            Câu hỏi chấm tự động không cần mốc mô tả hành vi — thang
                            điểm của nó là bảng quy đổi ở tab Hướng dẫn cấu hình.
                          </div>
                        ) : (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                            {[
                              ['anchorTop', `Mốc cao nhất (${r.maxScore} điểm)`],
                              ['anchorMid', `Mốc giữa (${Math.max(1, Math.floor((r.maxScore + 1) / 2))} điểm)`],
                              ['anchorLow', 'Mốc thấp nhất (1 điểm)'],
                            ].map(([field, label]) => (
                              <label key={field} style={{ display: 'grid', gap: 4 }}>
                                <span style={th}>{label}</span>
                                <textarea style={area} value={r[field]}
                                  onChange={(e) => patch(i, { [field]: e.target.value })} />
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      <div style={{ padding: 12 }}>
        <button type="button" className="btn btn-ghost" onClick={add}>
          <Icon name="plus" size={15} className="mr-s" /> Thêm câu hỏi
        </button>
      </div>
    </div>
  );
}
