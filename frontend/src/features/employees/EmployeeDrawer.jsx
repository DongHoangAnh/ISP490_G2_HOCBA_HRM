/* Hồ sơ chi tiết nhân viên (drawer) — Owner: Tân.
   Khối dữ liệu trả theo quyền do BE quyết định (SPEC_HRM_SPA_API.md §3.2). */
import { useState, useEffect, Fragment } from 'react';
import { fetchEmployee, postGate, postTrial, deleteDependent, verifyCert, deleteCert, fetchAccounts, fetchEvaluations } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Avatar from '../../components/Avatar';
import Modal from '../../components/Modal';
import EmployeeForm from './EmployeeForm';
import DependentForm from './DependentForm';
import AssetForm from './AssetForm';
import PromotionForm from './PromotionForm';
import CertForm from './CertForm';
import AccountForm from './AccountForm';
import EvaluationForm from './EvaluationForm';
import { SalaryJourneyChart, CriteriaRadar } from './PromoCharts';
import { EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind, HB_RESULT, HB_CERT } from '../../utils/format';

export default function EmployeeDrawer({ emp, onClose, onChanged, isHr, isMgr,
  canEdit = isHr, canManageAccount = isHr, canSeeSalary = isMgr, initialTab = 'info' }) {
  const [tab, setTab] = useState(initialTab);
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [editing, setEditing] = useState(false);
  useEffect(() => {
    fetchEmployee(emp.id).then(setDet).catch((e) => setDerr(e.message));
  }, [emp.id]);
  // Cập nhật det do một thao tác SỬA (khác lần fetch đầu) → đánh dấu để
  // danh sách ngoài refresh ngầm khi đóng drawer.
  const update = (d) => { setDet(d); onChanged && onChanged(); };

  const tabs = [
    ['info', 'Thông tin'],
    ['probation', 'Thử việc'],
    ['assets', det ? `Tài sản (${det.assets.length})` : 'Tài sản'],
    ['promo', det ? `Thăng tiến (${det.promotions.length})` : 'Thăng tiến'],
  ];
  if (canManageAccount) tabs.push(['account', 'Tài khoản']);

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <Avatar emp={emp} size={62} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{emp.name}</h2>
            <Badge kind={hbStatusKind((det || emp).statusKey)} dot>{(det || emp).status}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{emp.code} · {emp.jobTitle} · {emp.depName}</div>
          <div style={{ display: 'flex', gap: 14, marginTop: 10 }}>
            {emp.email && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }} className="muted"><Icon name="mail" size={15} />{emp.email}</span>}
            {emp.phone && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }} className="muted"><Icon name="phone" size={15} />{emp.phone}</span>}
          </div>
        </div>
        <div className="modal-x" style={{ display: 'flex', gap: 8 }}>
          {canEdit && det && (
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
              <Icon name="edit" size={15} />Chỉnh sửa</button>
          )}
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
        </div>
      </div>

      <div style={{ padding: '0 24px' }}>
        <div className="tabs" style={{ marginBottom: 0 }}>
          {tabs.map(([id, l]) => (
            <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => setTab(id)}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: 'min(72vh, calc(100vh - 210px))', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được hồ sơ ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải hồ sơ…</EmptyState>}
        {det && tab === 'info' && <InfoTab det={det} isHr={canEdit} isMgr={canSeeSalary} editable={canEdit} onUpdated={update} />}
        {det && tab === 'probation' && <ProbationTab det={det} isHr={canEdit} isMgr={isMgr} onUpdated={update} />}
        {det && tab === 'assets' && <AssetsTab det={det} editable={canEdit} onUpdated={update} />}
        {det && tab === 'promo' && <PromoTab det={det} isMgr={isMgr} editable={isMgr} onUpdated={update} />}
        {det && tab === 'account' && canManageAccount && <AccountTab det={det} emp={emp} onUpdated={update} />}
      </div>

      {editing && det && (
        <EmployeeForm emp={det} isMgr={isMgr}
          onClose={() => setEditing(false)}
          onSaved={(newDet) => { update(newDet); setEditing(false); }} />
      )}
    </Modal>
  );
}

export function InfoTab({ det, isHr, isMgr, editable, depEditable = editable, onUpdated }) {
  const [depForm, setDepForm] = useState(null); // null | 'new' | <dependent>
  const [certForm, setCertForm] = useState(null); // null | 'new' | <cert>
  const delDep = async (d) => {
    if (!window.confirm(`Xoá người phụ thuộc "${d.name}"?`)) return;
    try { onUpdated && onUpdated(await deleteDependent(d.id)); }
    catch (e) { alert(e.message); }
  };
  const toggleVerify = async (c) => {
    try { onUpdated && onUpdated(await verifyCert(c.id, !c.verified)); }
    catch (e) { alert(e.message); }
  };
  const delCert = async (c) => {
    if (!window.confirm(`Xoá chứng chỉ "${c.skill}"?`)) return;
    try { onUpdated && onUpdated(await deleteCert(c.id)); }
    catch (e) { alert(e.message); }
  };
  const rows = [
    ['Mã nhân sự', det.code], ['Họ và tên', det.name],
    ['Phòng ban', det.depName], ['Chức danh', det.jobTitle],
    ['Loại vị trí', det.posType || '—'], ['Hình thức', det.type],
    ['Tình trạng', det.status], ['Ngày vào làm', fmtDate(det.start)],
    ['Email công ty', det.email || '—'], ['Điện thoại', det.phone || '—'],
  ];
  if (isHr) rows.push(
    ['Ngày sinh', fmtDate(det.bday)],
    ['CCCD', det.cccd || '—'],
    ['Ngày cấp CCCD', fmtDate(det.idIssue)], ['Nơi cấp', det.idPlace || '—'],
    ['Số thẻ BHYT', det.hi || '—'], ['Nơi KCB ban đầu', det.hiPlace || '—'],
    ['Địa chỉ thường trú', det.permanentAddr || '—'], ['Địa chỉ tạm trú', det.currentAddr || '—'],
  );
  if (isMgr) rows.push(
    ['Lương cơ bản', det.wage ? `${hbVND(det.wage)} ₫` : '—'],
    ['MST TNCN', det.pit || '—'], ['Số sổ BHXH', det.si || '—'],
    ['Ngân hàng nhận lương', det.bankName || det.bankCode || '—'],
    ['Số tài khoản nhận lương', det.bankAccountNo || '—'],
  );
  return (
    <div>
      <div className="grid-2" style={{ rowGap: 20 }}>
        {rows.map(([k, v], i) => (
          <div className="kv" key={i}><div className="k">{k}</div><div className="v">{v || '—'}</div></div>
        ))}
      </div>
      {isHr && (det.dependents?.length > 0 || depEditable) && (
        <div style={{ marginTop: 22 }}>
          <div className="between" style={{ marginBottom: 8 }}>
            <div style={{ fontWeight: 700, fontSize: 13 }}>Người phụ thuộc ({det.dependents?.length || 0})</div>
            {depEditable && (
              <button className="btn btn-soft btn-sm" onClick={() => setDepForm('new')}>
                <Icon name="plus" size={13} />Thêm NPT</button>
            )}
          </div>
          {det.dependents?.length > 0 ? (
            <div className="card" style={{ padding: 0 }}>
              <table className="tbl"><thead><tr><th>Họ tên</th><th>Quan hệ</th><th>Ngày sinh</th><th>Giảm trừ từ</th><th>Đến</th>{depEditable && <th></th>}</tr></thead>
                <tbody>{det.dependents.map((d) => (
                  <tr key={d.id} style={{ cursor: 'default' }}>
                    <td>{d.name}</td><td>{d.relationship}</td>
                    <td className="mono">{fmtDate(d.birthday)}</td>
                    <td className="mono">{fmtDate(d.from)}</td>
                    <td className="mono">{d.to ? fmtDate(d.to) : '—'}</td>
                    {depEditable && (
                      <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                        <button className="icon-btn" title="Sửa" onClick={() => setDepForm(d)}><Icon name="edit" size={15} className="faint" /></button>
                        <button className="icon-btn" title="Xoá" onClick={() => delDep(d)}><Icon name="trash" size={15} className="faint" /></button>
                      </td>
                    )}
                  </tr>))}</tbody>
              </table>
            </div>
          ) : (
            <div className="muted" style={{ fontSize: 12.5 }}>Chưa có người phụ thuộc.</div>
          )}
          {depForm && (
            <DependentForm empId={det.id} dep={depForm === 'new' ? null : depForm}
              onClose={() => setDepForm(null)}
              onSaved={(d) => { setDepForm(null); onUpdated && onUpdated(d); }} />
          )}
        </div>
      )}
      {isHr && (det.certs?.length > 0 || editable) && (
        <div style={{ marginTop: 22 }}>
          <div className="between" style={{ marginBottom: 8 }}>
            <div style={{ fontWeight: 700, fontSize: 13 }}>Chứng chỉ ({det.certs?.length || 0})</div>
            {editable && (
              <button className="btn btn-soft btn-sm" onClick={() => setCertForm('new')}>
                <Icon name="plus" size={13} />Thêm chứng chỉ</button>
            )}
          </div>
          {det.certs?.length > 0 ? (
            <div className="card" style={{ padding: 0 }}>
              <table className="tbl"><thead><tr><th>Kỹ năng</th><th>Cấp độ</th><th>Ngày cấp</th><th>Hết hạn</th><th>Trạng thái</th><th>Xác minh</th>{editable && <th></th>}</tr></thead>
                <tbody>{det.certs.map((c) => {
                  const [lbl, kind] = HB_CERT[c.status] || HB_CERT.none;
                  return (
                    <tr key={c.id} style={{ cursor: 'default' }}>
                      <td>{c.skill}</td><td>{c.level}</td>
                      <td className="mono">{fmtDate(c.date)}</td>
                      <td className="mono">{c.expiry ? fmtDate(c.expiry) : '—'}</td>
                      <td><Badge kind={kind} dot>{lbl}</Badge></td>
                      <td>
                        {editable ? (
                          <button className="btn btn-ghost btn-sm" title="Bật/tắt xác minh" onClick={() => toggleVerify(c)}>
                            {c.verified ? <Badge kind="green">Đã xác minh</Badge> : <Badge kind="gray">Chưa · xác minh?</Badge>}
                          </button>
                        ) : (c.verified ? <Badge kind="green">Đã xác minh</Badge> : <Badge kind="gray">Chưa</Badge>)}
                      </td>
                      {editable && (
                        <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                          <button className="icon-btn" title="Sửa" onClick={() => setCertForm(c)}><Icon name="edit" size={15} className="faint" /></button>
                          <button className="icon-btn" title="Xoá" onClick={() => delCert(c)}><Icon name="trash" size={15} className="faint" /></button>
                        </td>
                      )}
                    </tr>);
                })}</tbody>
              </table>
            </div>
          ) : (
            <div className="muted" style={{ fontSize: 12.5 }}>Chưa có chứng chỉ.</div>
          )}
          {certForm && (
            <CertForm empId={det.id} cert={certForm === 'new' ? null : certForm}
              onClose={() => setCertForm(null)}
              onSaved={(d) => { setCertForm(null); onUpdated && onUpdated(d); }} />
          )}
        </div>
      )}
    </div>
  );
}

/* Nút đánh giá 1 cổng (chỉ HR Manager). Gọi API → BE chạy automation
   (cấp thiết bị / lên chính thức / offboarding) → trả hồ sơ mới. */
function GateAction({ empId, gate, onUpdated }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [note, setNote] = useState('');
  const submit = async (result) => {
    setErr(null);
    if ((result === 'pass' || result === 'fail') && !note.trim()) {
      setErr('Cần nhập ghi chú đánh giá khi Đạt hoặc Không đạt.'); return;
    }
    if (result === 'fail' && !window.confirm(
      'Đánh dấu KHÔNG ĐẠT sẽ chuyển nhân viên sang offboarding. Tiếp tục?')) return;
    if (result === 'extend' && !window.confirm(
      'Gia hạn sẽ kéo dài thử việc và hẹn tái đánh giá. Tiếp tục?')) return;
    setBusy(true);
    try {
      const det = await postGate(empId, { gate, result, note: note.trim() });
      onUpdated(det);
    } catch (e) {
      // 'forbidden' = thiếu quyền; còn lại hiện lý do thật từ server (sai
      // trình tự / thiếu ngày thử việc / BR-010…).
      setErr(e.code === 'forbidden'
        ? 'Bạn không có quyền duyệt nhân viên này.'
        : (e.message || 'Thao tác bị từ chối.'));
    } finally { setBusy(false); }
  };
  return (
    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px dashed var(--border)' }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 7 }}>
        Đánh giá cổng
      </div>
      <input
        value={note} onChange={(e) => setNote(e.target.value)}
        placeholder="Ghi chú đánh giá (bắt buộc khi Đạt / Không đạt)"
        style={{ width: '100%', marginBottom: 9, padding: '7px 10px', borderRadius: 9,
          border: '1px solid var(--border-strong)', background: '#fff', fontSize: 13,
          color: 'var(--ink)', outline: 'none', fontFamily: 'inherit' }} />
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button className="btn btn-primary btn-sm" disabled={busy}
          style={{ background: 'var(--green)', borderColor: 'var(--green)' }}
          onClick={() => submit('pass')}>
          <Icon name="checkCircle" size={14} />Đạt
        </button>
        <button className="btn btn-ghost btn-sm" disabled={busy}
          style={{ color: 'var(--gold-600)', borderColor: 'var(--gold-200)' }}
          onClick={() => submit('extend')}>
          <Icon name="clock" size={14} />Gia hạn
        </button>
        <button className="btn btn-ghost btn-sm" disabled={busy}
          style={{ color: 'var(--red-700)', borderColor: 'var(--red-100)' }}
          onClick={() => submit('fail')}>
          <Icon name="x" size={14} />Không đạt
        </button>
        {busy && <span className="muted" style={{ fontSize: 12, alignSelf: 'center' }}>Đang lưu…</span>}
      </div>
      {err && <div style={{ marginTop: 7, fontSize: 12, color: 'var(--red-600)' }}>{err}</div>}
    </div>
  );
}

/* Form chấm thử giảng (F-008) — HR nhập ngày/lớp/2 điểm/nhận xét rồi
   chốt Đạt / Không đạt. Model áp ràng buộc (điểm 1–10, fail cần nhận xét). */
function TrialAction({ empId, onUpdated }) {
  const tinp = {
    padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
    background: '#fff', fontSize: 13, color: 'var(--ink)', outline: 'none',
    fontFamily: 'inherit', width: '100%',
  };
  const [f, setF] = useState({
    date: new Date().toISOString().slice(0, 10), cls: '', scoreMethod: '', scoreContent: '', note: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));
  const submit = async (result) => {
    setErr(null);
    if (result === 'fail' && !f.note.trim()) { setErr('Cần nhập nhận xét khi Không đạt.'); return; }
    for (const s of [f.scoreMethod, f.scoreContent]) {
      if (s !== '' && (Number(s) < 1 || Number(s) > 10)) { setErr('Điểm phải trong thang 1–10.'); return; }
    }
    setBusy(true);
    try { onUpdated(await postTrial(empId, { ...f, result })); }
    catch (e) { setErr(e.code === 'forbidden' ? 'Không có quyền chấm thử giảng.' : (e.message || 'Thao tác bị từ chối.')); }
    finally { setBusy(false); }
  };
  return (
    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px dashed var(--border)' }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 9 }}>
        Chấm thử giảng
      </div>
      <div className="grid-2" style={{ rowGap: 10, columnGap: 12, marginBottom: 10 }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span className="faint" style={{ fontSize: 11 }}>Ngày thử giảng</span>
          <input type="date" style={tinp} value={f.date} onChange={set('date')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span className="faint" style={{ fontSize: 11 }}>Lớp</span>
          <input style={tinp} value={f.cls} onChange={set('cls')} placeholder="VD: HSK3-T2" /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span className="faint" style={{ fontSize: 11 }}>Điểm phương pháp (1–10)</span>
          <input type="number" min="1" max="10" step="0.1" style={tinp} value={f.scoreMethod} onChange={set('scoreMethod')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span className="faint" style={{ fontSize: 11 }}>Điểm chuyên môn (1–10)</span>
          <input type="number" min="1" max="10" step="0.1" style={tinp} value={f.scoreContent} onChange={set('scoreContent')} /></label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, gridColumn: '1 / -1' }}>
          <span className="faint" style={{ fontSize: 11 }}>Nhận xét (bắt buộc nếu Không đạt)</span>
          <input style={tinp} value={f.note} onChange={set('note')} /></label>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-primary btn-sm" disabled={busy}
          style={{ background: 'var(--green)', borderColor: 'var(--green)' }}
          onClick={() => submit('pass')}><Icon name="checkCircle" size={14} />Đạt</button>
        <button className="btn btn-ghost btn-sm" disabled={busy}
          style={{ color: 'var(--red-700)', borderColor: 'var(--red-100)' }}
          onClick={() => submit('fail')}><Icon name="x" size={14} />Không đạt</button>
        {busy && <span className="muted" style={{ fontSize: 12, alignSelf: 'center' }}>Đang lưu…</span>}
      </div>
      {err && <div style={{ marginTop: 7, fontSize: 12, color: 'var(--red-600)' }}>{err}</div>}
    </div>
  );
}

/* Timeline thử việc 5 điểm (Nhóm B) + thử giảng (Nhóm A) */
export function ProbationTab({ det, isHr, isMgr, onUpdated }) {
  const p = det.probation || {};
  const gst = (r) => r === 'pass' ? 'done' : r === 'fail' ? 'fail' : r === 'extend' ? 'extend' : 'pending';
  const gsub = (date, due) => date ? fmtDate(date) : (due ? 'hạn ' + fmtDate(due) : '');
  const steps = [
    ['Thử việc', p.start ? 'done' : 'pending', fmtDate(p.start)],
    ['ĐG tuần-2', gst(p.d2wResult), gsub(p.d2wDate, p.d2wDue)],
    ['Cấp thiết bị', p.equipDate ? 'done' : 'pending', p.equipDate ? fmtDate(p.equipDate) : ''],
    ['ĐG tháng-1', gst(p.d1mResult), gsub(p.d1mDate, p.d1mDue)],
    ['ĐG tháng-2', gst(p.d2mResult), gsub(p.d2mDate, p.d2mDue)],
    ['Chính thức', p.officialDate ? 'done' : 'pending', p.officialDate ? fmtDate(p.officialDate) : ''],
  ];
  const col = (s) => s === 'done' ? 'var(--green)' : s === 'fail' ? 'var(--red-600)'
    : s === 'extend' ? 'var(--gold-500)' : 'var(--border-strong)';
  return (
    <div>
      {p.isGroupB ? (
        <div>
          <div className="card" style={{ padding: '20px 18px 14px', marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start' }}>
              {steps.map(([lbl, st, sub], i) => (
                <Fragment key={i}>
                  {i > 0 && <div style={{ flex: 1, height: 3, background: col(st), margin: '7px 4px 0', borderRadius: 2, minWidth: 18 }}></div>}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 86 }}>
                    <div style={{ width: 17, height: 17, borderRadius: '50%', background: col(st),
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 10, fontWeight: 800 }}>
                      {st === 'done' ? '✓' : st === 'fail' ? '✗' : st === 'extend' ? '↻' : i + 1}
                    </div>
                    <div style={{ fontSize: 11.5, fontWeight: 700, marginTop: 6, textAlign: 'center' }}>{lbl}</div>
                    {sub && <div className="faint" style={{ fontSize: 10.5, marginTop: 2, textAlign: 'center' }}>{sub}</div>}
                  </div>
                </Fragment>
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="card" style={{ padding: 16 }}>
              <div className="between" style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>Cổng tuần-2 · cấp thiết bị</span>
                <Badge kind={HB_RESULT[p.d2wResult][1]} dot>{HB_RESULT[p.d2wResult][0]}</Badge>
              </div>
              <div className="grid-2">
                <div className="kv"><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2wDue)}</div></div>
                <div className="kv"><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2wDate)}</div></div>
              </div>
              <div className="kv" style={{ marginTop: 8 }}><div className="k">Ghi chú</div><div className="v">{p.d2wNote || '—'}</div></div>
              {p.canEval && onUpdated && p.d2wResult === 'draft' && (
                <GateAction empId={det.id} gate="2w" onUpdated={onUpdated} />
              )}
            </div>
            <div className="card" style={{ padding: 16 }}>
              <div className="between" style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>Cổng tháng-1 · có thể lên chính thức sớm</span>
                <Badge kind={HB_RESULT[p.d1mResult][1]} dot>{HB_RESULT[p.d1mResult][0]}</Badge>
              </div>
              <div className="grid-2">
                <div className="kv"><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d1mDue)}</div></div>
                <div className="kv"><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d1mDate)}</div></div>
              </div>
              <div className="kv" style={{ marginTop: 8 }}><div className="k">Ghi chú</div><div className="v">{p.d1mNote || '—'}</div></div>
              {p.d2wResult !== 'pass' ? (
                <div className="faint" style={{ fontSize: 11.5, marginTop: 10 }}>Mở sau khi cổng tuần-2 Đạt.</div>
              ) : p.canEval && onUpdated && p.d1mResult === 'draft' && (
                <GateAction empId={det.id} gate="1m" onUpdated={onUpdated} />
              )}
            </div>
            <div className="card" style={{ padding: 16 }}>
              <div className="between" style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>Cổng tháng-2 · lên chính thức</span>
                <Badge kind={HB_RESULT[p.d2mResult][1]} dot>{HB_RESULT[p.d2mResult][0]}</Badge>
              </div>
              <div className="grid-2">
                <div className="kv"><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2mDue)}</div></div>
                <div className="kv"><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2mDate)}</div></div>
              </div>
              <div className="kv" style={{ marginTop: 8 }}><div className="k">Ghi chú</div><div className="v">{p.d2mNote || '—'}</div></div>
              {p.d1mResult !== 'extend' ? (
                <div className="faint" style={{ fontSize: 11.5, marginTop: 10 }}>Chỉ mở khi cổng tháng-1 "Gia hạn".</div>
              ) : p.canEval && onUpdated && p.d2mResult === 'draft' && (
                <GateAction empId={det.id} gate="2m" onUpdated={onUpdated} />
              )}
            </div>
          </div>
          {p.officialDate && (
            <div style={{ marginTop: 14, padding: '12px 16px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 11, fontSize: 13 }}>
              Chính thức từ <b>{fmtDate(p.officialDate)}</b> · {p.officialMonths} tháng
            </div>
          )}
        </div>
      ) : !det.trial ? (
        <EmptyState>Chưa xác định được luồng đánh giá cho nhân sự này. Hãy đặt
          {' '}<b>Hình thức làm việc</b> (Online → thử giảng / Offline → thử việc 2 cổng)
          {' '}và <b>Loại vị trí</b> trong hồ sơ; hoặc gán <b>Loại nhân sự = Giáo viên</b>
          {' '}để dùng luồng thử giảng.</EmptyState>
      ) : null}

      {det.trial && (
        <div style={{ marginTop: p.isGroupB ? 18 : 0 }}>
          <div className="card" style={{ padding: 16 }}>
            <div className="between" style={{ marginBottom: 12 }}>
              <span style={{ fontWeight: 700, fontSize: 13 }}>Đánh giá thử giảng (Nhóm A — giảng viên)</span>
              <Badge kind={HB_RESULT[det.trial.result][1]} dot>{HB_RESULT[det.trial.result][0]}</Badge>
            </div>
            <div className="grid-2" style={{ rowGap: 14 }}>
              <div className="kv"><div className="k">Ngày thử giảng</div><div className="v mono">{fmtDate(det.trial.date)}</div></div>
              <div className="kv"><div className="k">Lớp</div><div className="v">{det.trial.class || '—'}</div></div>
              <div className="kv"><div className="k">Điểm phương pháp</div><div className="v mono">{det.trial.scoreMethod || '—'} / 10</div></div>
              <div className="kv"><div className="k">Điểm chuyên môn</div><div className="v mono">{det.trial.scoreContent || '—'} / 10</div></div>
            </div>
            {det.trial.note && <div style={{ marginTop: 12, fontSize: 12.5 }} className="muted">{det.trial.note}</div>}
            {det.trial.canEval && onUpdated && det.trial.result === 'draft' && (
              <TrialAction empId={det.id} onUpdated={onUpdated} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function AssetsTab({ det, editable, onUpdated }) {
  // form = null | { mode:'new' } | { mode:'return'|'transfer', asset }
  const [form, setForm] = useState(null);
  const kind = (s) => s === 'assigned' ? 'green' : s === 'transferred' ? 'blue' : 'gray';
  const canAct = editable && onUpdated;
  return (
    <div>
      {canAct && (
        <div className="between" style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>Tài sản cấp phát ({det.assets.length})</div>
          <button className="btn btn-soft btn-sm" onClick={() => setForm({ mode: 'new' })}>
            <Icon name="plus" size={13} />Cấp phát</button>
        </div>
      )}
      {!det.assets.length ? (
        <EmptyState>Chưa có tài sản cấp phát.</EmptyState>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead><tr><th>Mã tài sản</th><th>Loại</th><th>Ngày cấp</th><th>Trạng thái</th><th>Ngày thu hồi</th>{canAct && <th></th>}</tr></thead>
            <tbody>{det.assets.map((a) => (
              <tr key={a.id} style={{ cursor: 'default' }}>
                <td className="mono" style={{ fontWeight: 600 }}>{a.code}</td>
                <td>{a.type}</td>
                <td className="mono">{fmtDate(a.grant)}</td>
                <td><Badge kind={kind(a.state)} dot>{a.stateLabel}</Badge></td>
                <td className="mono">{a.returnDate ? fmtDate(a.returnDate) : '—'}</td>
                {canAct && (
                  <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                    {a.state === 'assigned' ? (
                      <>
                        <button className="btn btn-ghost btn-sm" title="Thu hồi" onClick={() => setForm({ mode: 'return', asset: a })}>Thu hồi</button>
                        <button className="btn btn-ghost btn-sm" title="Chuyển giao" style={{ marginLeft: 6 }} onClick={() => setForm({ mode: 'transfer', asset: a })}>Chuyển</button>
                      </>
                    ) : <span className="faint" style={{ fontSize: 12 }}>—</span>}
                  </td>
                )}
              </tr>))}</tbody>
          </table>
        </div>
      )}
      {form && (
        <AssetForm empId={det.id} mode={form.mode} asset={form.asset}
          onClose={() => setForm(null)}
          onSaved={(d) => { setForm(null); onUpdated(d); }} />
      )}
    </div>
  );
}

export function PromoTab({ det, isMgr, editable, onUpdated }) {
  const [adding, setAdding] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evalData, setEvalData] = useState(null);
  const canAct = editable && onUpdated;

  useEffect(() => {
    setEvalData(null); // tránh nháy dữ liệu NV cũ khi đổi hồ sơ
    if (canAct) fetchEvaluations(det.id).then(setEvalData).catch(() => setEvalData(null));
  }, [det.id, canAct]);

  const latest = evalData?.evaluations?.[evalData.evaluations.length - 1];
  const am = evalData?.autoMetrics;

  return (
    <div>
      {am && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
          <MetricCard label="Thâm niên (tháng)" value={am.tenureMonths} />
          <MetricCard label="Từ thăng tiến" value={am.monthsSincePromo ?? '—'} />
          <MetricCard label="Chấm công 3T" value={am.attendance ? `${am.attendance.days} ngày` : 'Chưa có'} />
          <MetricCard label="Kết luận gần nhất" value={latest ? `${latest.totalScore}%` : '—'} />
        </div>
      )}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 320px' }}>
          <SectionTitle>Lộ trình chức vụ & lương</SectionTitle>
          <SalaryJourneyChart promotions={det.promotions} />
        </div>
        <div style={{ flex: '1 1 260px' }}>
          <SectionTitle>Radar tiêu chí (đợt gần nhất)</SectionTitle>
          <CriteriaRadar lines={latest?.lines} />
        </div>
      </div>

      {canAct && (
        <div className="between" style={{ margin: '16px 0' }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>
            Lịch sử ({det.promotions.length} mốc · {evalData?.evaluations?.length || 0} đợt đánh giá)
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-soft btn-sm" disabled={!evalData}
              onClick={() => setEvaluating(true)}>
              <Icon name="checkCircle" size={13} />Đánh giá mới</button>
            {isMgr && (
              <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
                <Icon name="arrowUp" size={13} />Tạo thăng tiến</button>
            )}
          </div>
        </div>
      )}

      {!det.promotions.length ? (
        <EmptyState>Chưa có lịch sử thăng tiến.</EmptyState>
      ) : (
        <PromoTimeline path={det.promotions} isMgr={isMgr} />
      )}

      {adding && (
        <PromotionForm det={det} evaluationId={latest?.id}
          onClose={() => setAdding(false)}
          onSaved={(d) => { setAdding(false); onUpdated(d); }} />
      )}
      {evaluating && evalData && (
        <EvaluationForm empId={det.id} criteria={evalData.criteria}
          onClose={() => setEvaluating(false)}
          onSaved={(d) => { setEvaluating(false); setEvalData(d); }} />
      )}
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div style={{ flex: '1 1 110px', background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 12px', textAlign: 'center' }}>
      <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--red-700)' }}>{value}</div>
      <div style={{ fontSize: 10.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</div>
    </div>
  );
}

function SectionTitle({ children }) {
  return <div style={{ fontWeight: 700, fontSize: 12.5, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 6 }}>{children}</div>;
}

function PromoTimeline({ path, isMgr }) {
  return (
    <div style={{ position: 'relative', paddingLeft: 8 }}>
      {path.map((p, i) => {
        const last = i === path.length - 1;
        const delta = isMgr && p.toWage > p.fromWage ? p.toWage - p.fromWage : 0;
        return (
          <div key={i} style={{ display: 'flex', gap: 16, paddingBottom: last ? 0 : 18, position: 'relative' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ width: 14, height: 14, borderRadius: '50%', background: last ? 'var(--red-600)' : 'var(--gold-500)',
                border: '3px solid #fff', boxShadow: '0 0 0 2px ' + (last ? 'var(--red-100)' : 'var(--gold-200)'), zIndex: 1 }}></div>
              {!last && <div style={{ width: 2, flex: 1, background: 'var(--border-strong)', marginTop: 2 }}></div>}
            </div>
            <div style={{ flex: 1 }}>
              <div className="between">
                <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{p.fromJob} → {p.toJob}</span>
                  {p.dept && <Badge kind="gray">{p.dept}</Badge>}
                  {delta > 0 && <span className="badge badge-gold"><Icon name="arrowUp" size={11} />+{hbVND(delta)}</span>}
                </div>
                <span className="mono muted" style={{ fontSize: 12.5 }}>{fmtDate(p.date)}</span>
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 5, flexWrap: 'wrap' }}>
                {isMgr && p.toWage > 0 && <span className="mono" style={{ fontWeight: 800, fontSize: 13.5, color: 'var(--green)' }}>{hbVND(p.toWage)} ₫</span>}
                {p.ref && <span className="faint" style={{ fontSize: 12 }}>QĐ: {p.ref}</span>}
                {p.reason && <span className="faint" style={{ fontSize: 12 }}>{p.reason}</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* Tab tài khoản đăng nhập — chỉ HR/Admin (det.account chỉ có khi BE trả cho HR).
   Cho tạo tài khoản mới hoặc cấp lại mật khẩu qua AccountForm. */
function AccountTab({ det, emp, onUpdated }) {
  const acc = det.account || { hasAccount: false };
  const [mode, setMode] = useState(null); // null | 'create' | 'reset'
  const [depts, setDepts] = useState([]);
  useEffect(() => {
    fetchAccounts().then((d) => setDepts(d.departments || [])).catch(() => {});
  }, []);
  const done = (accountPayload) => { onUpdated({ ...det, account: accountPayload }); setMode(null); };
  return (
    <div>
      {acc.hasAccount ? (
        <div className="card" style={{ padding: 16 }}>
          <div className="kv"><div className="k">Đăng nhập</div><div className="v">{acc.login}</div></div>
          <div className="kv" style={{ marginTop: 8 }}>
            <div className="k">Trạng thái</div>
            <div className="v"><Badge kind={acc.active ? 'green' : 'gray'} dot>{acc.active ? 'Hoạt động' : 'Khóa'}</Badge></div>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 14 }} onClick={() => setMode('reset')}>
            <Icon name="rotateCcw" size={14} />Cấp lại mật khẩu</button>
        </div>
      ) : (
        <div className="card" style={{ padding: 16 }}>
          <div className="muted" style={{ fontSize: 12.5 }}>Nhân viên chưa có tài khoản đăng nhập.</div>
          <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }} onClick={() => setMode('create')}>
            <Icon name="shield" size={14} />Tạo tài khoản</button>
        </div>
      )}
      {mode && (
        <AccountForm emp={emp} mode={mode} departments={depts}
          onClose={() => setMode(null)} onDone={done} />
      )}
    </div>
  );
}
