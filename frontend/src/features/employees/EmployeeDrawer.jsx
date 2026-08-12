/* Hồ sơ chi tiết nhân viên (drawer) — Owner: Tân.
   Khối dữ liệu trả theo quyền do BE quyết định (SPEC_HRM_SPA_API.md §3.2). */
import { useState, useEffect, Fragment } from 'react';
import { fetchEmployee, deleteDependent, verifyCert, deleteCert, fetchAccounts, deleteAsset } from '../../api/employees';
import { fetchCareer } from '../../api/career';
import { fetchEmployeeAllowances, saveEmployeeAllowance, deleteEmployeeAllowance } from '../../api/payroll';
import OnboardingStepsPanel from './OnboardingStepsPanel';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Avatar from '../../components/Avatar';
import Modal from '../../components/Modal';
import EmployeeForm from './EmployeeForm';
import DependentForm from './DependentForm';
import AssetForm from './AssetForm';
import CertForm from './CertForm';
import AccountForm from './AccountForm';
import { SalaryJourneyChart, CriteriaRadar } from './PromoCharts';
import { EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind, HB_CERT } from '../../utils/format';

export default function EmployeeDrawer({ emp, onClose, onChanged, isHr, isMgr,
  canEdit = isHr, canManageAccount = isHr, canSeeSalary = isMgr,
  initialTab = 'info', onOpenCareer }) {
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
        {det && tab === 'promo' && <PromoTab det={det} isMgr={isMgr}
          onOpenCareer={onOpenCareer && (() => { onOpenCareer(det.id); onClose(); })} />}
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
      {isMgr && <AllowanceSection empId={det.id} isMgr={isMgr} />}
    </div>
  );
}

/* ── Phụ cấp riêng (standalone CRUD, free-form name + amount) ── */
function AllowanceSection({ empId, isMgr }) {
  const [allowances, setAllowances] = useState([]);
  const [adding, setAdding] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ name: '', amount: '' });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchEmployeeAllowances(empId).then(setAllowances).catch(() => {});
  }, [empId]);

  const reload = () => fetchEmployeeAllowances(empId).then(setAllowances).catch(() => {});
  const resetForm = () => { setForm({ name: '', amount: '' }); setAdding(false); setEditId(null); };

  const handleSave = async () => {
    if (!form.name.trim() || busy) return;
    setBusy(true);
    try {
      await saveEmployeeAllowance({
        id: editId || undefined,
        employee_id: empId,
        name: form.name.trim(),
        amount: Number(form.amount) || 0,
      });
      resetForm();
      reload();
    } catch (e) { alert(e.message); }
    finally { setBusy(false); }
  };

  const handleDelete = async (a) => {
    if (!window.confirm(`Xoá phụ cấp "${a.name}"?`)) return;
    try { await deleteEmployeeAllowance(a.id); reload(); }
    catch (e) { alert(e.message); }
  };

  const fmtAmt = (v) => v ? Number(v).toLocaleString('vi-VN') + ' ₫' : '0 ₫';
  const inp = { border: '1px solid #d1d5db', borderRadius: 5, padding: '5px 10px', fontSize: 13 };

  return (
    <div style={{ marginTop: 22 }}>
      <div className="between" style={{ marginBottom: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
          💰 Phụ cấp riêng ({allowances.length})
        </div>
        {isMgr && !adding && !editId && (
          <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
            <Icon name="plus" size={13} />Thêm phụ cấp
          </button>
        )}
      </div>

      {allowances.length > 0 && (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead><tr>
              <th>Khoản phụ cấp</th><th style={{ textAlign: 'right' }}>Số tiền</th>
              {isMgr && <th style={{ width: 80 }}></th>}
            </tr></thead>
            <tbody>
              {allowances.map((a) => (
                editId === a.id ? (
                  <tr key={a.id} style={{ background: '#fefce8' }}>
                    <td>
                      <input type="text" style={{ ...inp, width: '100%' }}
                        value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                    </td>
                    <td>
                      <input type="number" style={{ ...inp, width: '100%', textAlign: 'right' }}
                        value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
                        autoFocus />
                    </td>
                    <td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>
                      <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={busy}>
                        {busy ? '...' : 'Lưu'}
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ marginLeft: 4 }}
                        onClick={resetForm}>Huỷ</button>
                    </td>
                  </tr>
                ) : (
                  <tr key={a.id}>
                    <td>{a.name}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{fmtAmt(a.amount)}</td>
                    {isMgr && (
                      <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                        <button className="icon-btn" title="Sửa" onClick={() => {
                          setEditId(a.id); setAdding(false);
                          setForm({ name: a.name, amount: a.amount });
                        }}><Icon name="edit" size={15} className="faint" /></button>
                        <button className="icon-btn" title="Xoá" onClick={() => handleDelete(a)}>
                          <Icon name="trash" size={15} className="faint" /></button>
                      </td>
                    )}
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      )}
      {allowances.length === 0 && !adding && (
        <div className="muted" style={{ fontSize: 12.5 }}>Chưa có phụ cấp riêng.</div>
      )}

      {adding && (
        <div style={{
          marginTop: 10, padding: '12px 16px', borderRadius: 8,
          background: '#f8fafc', border: '1px solid #e2e8f0',
        }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 180px' }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#374151' }}>Tên khoản</div>
              <input type="text" style={{ ...inp, width: '100%' }}
                value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="VD: PC Xăng xe, PC Di chuyển..." autoFocus />
            </div>
            <div style={{ flex: '0 0 150px' }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#374151' }}>Số tiền (₫)</div>
              <input type="number" style={{ ...inp, width: '100%' }}
                value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="0" />
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={busy || !form.name.trim()}>
                {busy ? 'Đang lưu...' : 'Thêm'}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={resetForm}>Huỷ</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* Tab Thử việc — quy trình bước động; giữ export ProbationTab để Profile
   self-service tái dùng (không truyền onUpdated = chỉ xem). */
export function ProbationTab({ det, isMgr, onUpdated }) {
  return <OnboardingStepsPanel det={det} isMgr={isMgr} onUpdated={onUpdated} />;
}

export function AssetsTab({ det, editable, onUpdated }) {
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(0);
  const canAct = editable && onUpdated;

  const remove = async (a) => {
    if (!window.confirm(`Gỡ tài sản ${a.code} khỏi hồ sơ ${det.name}?`)) return;
    setBusy(a.id);
    try { onUpdated(await deleteAsset(a.id)); }
    catch (e) { alert(e.message); }
    finally { setBusy(0); }
  };

  return (
    <div>
      {canAct && (
        <div className="between" style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>Tài sản đang giữ ({det.assets.length})</div>
          <button className="btn btn-soft btn-sm" onClick={() => setAdding(true)}>
            <Icon name="plus" size={13} />Cấp phát</button>
        </div>
      )}
      {!det.assets.length ? (
        <EmptyState>Chưa có tài sản cấp phát.</EmptyState>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead><tr><th>Mã tài sản</th><th>Loại</th><th>Ngày cấp</th><th>Tình trạng</th>{canAct && <th></th>}</tr></thead>
            <tbody>{det.assets.map((a) => (
              <tr key={a.id} style={{ cursor: 'default' }}>
                <td className="mono" style={{ fontWeight: 600 }}>{a.code}</td>
                <td>{a.type}</td>
                <td className="mono">{fmtDate(a.grant)}</td>
                <td>{a.conditionLabel || '—'}</td>
                {canAct && (
                  <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}>
                    <button className="btn btn-ghost btn-sm" title="Gỡ khỏi hồ sơ"
                      disabled={busy === a.id} onClick={() => remove(a)}>Gỡ</button>
                  </td>
                )}
              </tr>))}</tbody>
          </table>
        </div>
      )}
      {adding && (
        <AssetForm empId={det.id}
          onClose={() => setAdding(false)}
          onSaved={(d) => { setAdding(false); onUpdated(d); }} />
      )}
    </div>
  );
}

/* Tab Lộ trình trong hồ sơ NV — CHỈ ĐỌC từ 2026-08-12.
   Nhập liệu (chấm đánh giá + tạo thăng tiến) đã gộp về màn Đánh giá của
   hocba_reviews; ở đây chỉ còn kết quả và biểu đồ.
   Spec: docs/superpowers/specs/
   2026-08-12-gop-danh-gia-thang-tien-vao-reviews-design.md §4 */
export function PromoTab({ det, isMgr, onOpenCareer }) {
  const [career, setCareer] = useState(null);

  useEffect(() => {
    setCareer(null); // tránh nháy dữ liệu NV cũ khi đổi hồ sơ
    // MỘT nguồn duy nhất cho mọi vai trò: /career đã gác đúng phạm vi
    // (_emp_in_scope) và tự lọc phiếu chưa công bố với người tự xem.
    fetchCareer(det.id).then(setCareer).catch(() => setCareer(null));
  }, [det.id]);

  const evals = career?.evaluations || [];
  const latest = evals[evals.length - 1];
  const st = career?.stats;

  return (
    <div>
      {onOpenCareer && (
        <div style={{ marginBottom: 14 }}>
          <button className="btn btn-soft btn-sm" onClick={onOpenCareer}>
            <Icon name="trend" size={13} />Mở trang lộ trình đầy đủ</button>
        </div>
      )}
      {st && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
          <MetricCard label="Thâm niên (tháng)" value={st.tenureMonths ?? '—'} />
          <MetricCard label="Từ thăng tiến" value={st.monthsSincePromo ?? '—'} />
          <MetricCard label="Số đợt đánh giá" value={st.evalCount} />
          <MetricCard label="Điểm gần nhất"
            value={st.lastScore != null ? st.lastScore : '—'} />
        </div>
      )}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 320px' }}>
          <SectionTitle>Lộ trình chức vụ & lương</SectionTitle>
          <SalaryJourneyChart promotions={det.promotions} />
        </div>
        <div style={{ flex: '1 1 260px' }}>
          <SectionTitle>Radar tiêu chí (kỳ gần nhất)</SectionTitle>
          {/* Chỉ phiếu đánh giá định kỳ mới có tiêu chí — đợt cũ đã bỏ chi
              tiết theo bộ tiêu chí ngừng dùng. */}
          <CriteriaRadar lines={latest?.lines} />
        </div>
      </div>

      <div className="between" style={{ margin: '16px 0' }}>
        <div style={{ fontWeight: 700, fontSize: 13 }}>
          Lịch sử ({det.promotions.length} mốc · {evals.length} đợt đánh giá)
        </div>
      </div>

      {!det.promotions.length ? (
        <EmptyState>Chưa có lịch sử thăng tiến.</EmptyState>
      ) : (
        <PromoTimeline path={det.promotions} isMgr={isMgr} />
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
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{p.title || `${p.fromJob} → ${p.toJob}`}</span>
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
