/* Hồ sơ chi tiết nhân viên (drawer) — Owner: Tân.
   Khối dữ liệu trả theo quyền do BE quyết định (SPEC_HRM_SPA_API.md §3.2). */
import { useState, useEffect, Fragment } from 'react';
import { fetchEmployee, postGate } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Avatar from '../../components/Avatar';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind, HB_RESULT, HB_CERT } from '../../utils/format';

export default function EmployeeDrawer({ emp, onClose, isHr, isMgr, initialTab = 'info' }) {
  const [tab, setTab] = useState(initialTab);
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  useEffect(() => {
    fetchEmployee(emp.id).then(setDet).catch((e) => setDerr(e.message));
  }, [emp.id]);

  const tabs = [
    ['info', 'Thông tin'],
    ['probation', 'Thử việc'],
    ['assets', det ? `Tài sản (${det.assets.length})` : 'Tài sản'],
    ['promo', det ? `Thăng tiến (${det.promotions.length})` : 'Thăng tiến'],
  ];

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
          <button className="btn btn-ghost btn-sm" onClick={() => window.open('/odoo/employees/' + emp.id, '_blank')}>
            <Icon name="edit" size={15} />Sửa trong Odoo</button>
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

      <div style={{ padding: '22px 24px', maxHeight: '52vh', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được hồ sơ ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải hồ sơ…</EmptyState>}
        {det && tab === 'info' && <InfoTab det={det} isHr={isHr} isMgr={isMgr} />}
        {det && tab === 'probation' && <ProbationTab det={det} isMgr={isMgr} onUpdated={setDet} />}
        {det && tab === 'assets' && <AssetsTab det={det} />}
        {det && tab === 'promo' && <PromoTab det={det} isMgr={isMgr} />}
      </div>
    </Modal>
  );
}

export function InfoTab({ det, isHr, isMgr }) {
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
  if (isMgr) rows.push(['MST TNCN', det.pit || '—'], ['Số sổ BHXH', det.si || '—']);
  return (
    <div>
      <div className="grid-2" style={{ rowGap: 20 }}>
        {rows.map(([k, v], i) => (
          <div className="kv" key={i}><div className="k">{k}</div><div className="v">{v || '—'}</div></div>
        ))}
      </div>
      {isHr && det.dependents && det.dependents.length > 0 && (
        <div style={{ marginTop: 22 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Người phụ thuộc ({det.dependents.length})</div>
          <div className="card" style={{ padding: 0 }}>
            <table className="tbl"><thead><tr><th>Họ tên</th><th>Quan hệ</th><th>Ngày sinh</th><th>Giảm trừ từ</th><th>Đến</th></tr></thead>
              <tbody>{det.dependents.map((d, i) => (
                <tr key={i} style={{ cursor: 'default' }}>
                  <td>{d.name}</td><td>{d.relationship}</td>
                  <td className="mono">{fmtDate(d.birthday)}</td>
                  <td className="mono">{fmtDate(d.from)}</td>
                  <td className="mono">{d.to ? fmtDate(d.to) : '—'}</td>
                </tr>))}</tbody>
            </table>
          </div>
        </div>
      )}
      {isHr && det.certs && det.certs.length > 0 && (
        <div style={{ marginTop: 22 }}>
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Chứng chỉ ({det.certs.length})</div>
          <div className="card" style={{ padding: 0 }}>
            <table className="tbl"><thead><tr><th>Kỹ năng</th><th>Cấp độ</th><th>Ngày cấp</th><th>Hết hạn</th><th>Trạng thái</th><th>Xác minh</th></tr></thead>
              <tbody>{det.certs.map((c, i) => {
                const [lbl, kind] = HB_CERT[c.status] || HB_CERT.none;
                return (
                  <tr key={i} style={{ cursor: 'default' }}>
                    <td>{c.skill}</td><td>{c.level}</td>
                    <td className="mono">{fmtDate(c.date)}</td>
                    <td className="mono">{c.expiry ? fmtDate(c.expiry) : '—'}</td>
                    <td><Badge kind={kind} dot>{lbl}</Badge></td>
                    <td>{c.verified ? <Badge kind="green">Đã xác minh</Badge> : <Badge kind="gray">Chưa</Badge>}</td>
                  </tr>);
              })}</tbody>
            </table>
          </div>
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
  const submit = async (result) => {
    if (result === 'fail' && !window.confirm(
      'Đánh dấu KHÔNG ĐẠT sẽ chuyển nhân viên sang offboarding (không gia hạn). Tiếp tục?')) return;
    setBusy(true); setErr(null);
    try {
      const det = await postGate(empId, { gate, result });
      onUpdated(det);
    } catch (e) {
      setErr(e.status === 403 ? 'Không có quyền hoặc thao tác bị từ chối (kiểm tra điều kiện cổng).' : e.message);
    } finally { setBusy(false); }
  };
  return (
    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px dashed var(--border)' }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--faint)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 7 }}>
        Đánh giá cổng
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-primary btn-sm" disabled={busy}
          style={{ background: 'var(--green)', borderColor: 'var(--green)' }}
          onClick={() => submit('pass')}>
          <Icon name="checkCircle" size={14} />Đạt
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

/* Timeline thử việc 5 điểm (Nhóm B) + thử giảng (Nhóm A) */
export function ProbationTab({ det, isMgr, onUpdated }) {
  const p = det.probation || {};
  const steps = [
    ['Thử việc', p.start ? 'done' : 'pending', fmtDate(p.start)],
    ['ĐG tuần-2', p.d2wResult === 'pass' ? 'done' : p.d2wResult === 'fail' ? 'fail' : 'pending',
      p.d2wDate ? fmtDate(p.d2wDate) : (p.d2wDue ? 'hạn ' + fmtDate(p.d2wDue) : '')],
    ['Cấp thiết bị', p.equipDate ? 'done' : 'pending', p.equipDate ? fmtDate(p.equipDate) : ''],
    ['ĐG tháng-2', p.d2mResult === 'pass' ? 'done' : p.d2mResult === 'fail' ? 'fail' : 'pending',
      p.d2mDate ? fmtDate(p.d2mDate) : (p.d2mDue ? 'hạn ' + fmtDate(p.d2mDue) : '')],
    ['Chính thức', p.officialDate ? 'done' : 'pending', p.officialDate ? fmtDate(p.officialDate) : ''],
  ];
  const col = (s) => s === 'done' ? 'var(--green)' : s === 'fail' ? 'var(--red-600)' : 'var(--border-strong)';
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
                      {st === 'done' ? '✓' : st === 'fail' ? '✗' : i + 1}
                    </div>
                    <div style={{ fontSize: 11.5, fontWeight: 700, marginTop: 6, textAlign: 'center' }}>{lbl}</div>
                    {sub && <div className="faint" style={{ fontSize: 10.5, marginTop: 2, textAlign: 'center' }}>{sub}</div>}
                  </div>
                </Fragment>
              ))}
            </div>
          </div>
          <div className="grid-2">
            <div className="card" style={{ padding: 16 }}>
              <div className="between" style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>Cổng tuần-2 · cấp thiết bị</span>
                <Badge kind={HB_RESULT[p.d2wResult][1]} dot>{HB_RESULT[p.d2wResult][0]}</Badge>
              </div>
              <div className="kv" style={{ marginBottom: 8 }}><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2wDue)}</div></div>
              <div className="kv" style={{ marginBottom: 8 }}><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2wDate)}</div></div>
              <div className="kv"><div className="k">Ghi chú</div><div className="v">{p.d2wNote || '—'}</div></div>
              {isMgr && onUpdated && p.d2wResult === 'draft' && (
                <GateAction empId={det.id} gate="2w" onUpdated={onUpdated} />
              )}
            </div>
            <div className="card" style={{ padding: 16 }}>
              <div className="between" style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>Cổng tháng-2 · lên chính thức</span>
                <Badge kind={HB_RESULT[p.d2mResult][1]} dot>{HB_RESULT[p.d2mResult][0]}</Badge>
              </div>
              <div className="kv" style={{ marginBottom: 8 }}><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2mDue)}</div></div>
              <div className="kv" style={{ marginBottom: 8 }}><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2mDate)}</div></div>
              <div className="kv"><div className="k">Ghi chú</div><div className="v">{p.d2mNote || '—'}</div></div>
              {isMgr && onUpdated && p.d2wResult === 'pass' && p.d2mResult === 'draft' && (
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
        <EmptyState>Nhân sự này không thuộc luồng thử việc 2 cổng (Nhóm B).</EmptyState>
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
          </div>
        </div>
      )}
    </div>
  );
}

export function AssetsTab({ det }) {
  if (!det.assets.length) return <EmptyState>Chưa có tài sản cấp phát.</EmptyState>;
  const kind = (s) => s === 'assigned' ? 'green' : s === 'transferred' ? 'blue' : 'gray';
  return (
    <div className="card" style={{ padding: 0 }}>
      <table className="tbl">
        <thead><tr><th>Mã tài sản</th><th>Loại</th><th>Ngày cấp</th><th>Trạng thái</th><th>Ngày thu hồi</th></tr></thead>
        <tbody>{det.assets.map((a) => (
          <tr key={a.id} style={{ cursor: 'default' }}>
            <td className="mono" style={{ fontWeight: 600 }}>{a.code}</td>
            <td>{a.type}</td>
            <td className="mono">{fmtDate(a.grant)}</td>
            <td><Badge kind={kind(a.state)} dot>{a.stateLabel}</Badge></td>
            <td className="mono">{a.returnDate ? fmtDate(a.returnDate) : '—'}</td>
          </tr>))}</tbody>
      </table>
    </div>
  );
}

export function PromoTab({ det, isMgr }) {
  if (!det.promotions.length) return <EmptyState>Chưa có lịch sử thăng tiến.</EmptyState>;
  const path = det.promotions;
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
