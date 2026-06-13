/* ============================================================
   Màn "Hồ sơ của tôi" (self-service) — mọi nhân viên xem hồ sơ
   CỦA CHÍNH MÌNH. Tái dùng các tab của EmployeeDrawer. Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchMe } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbStatusKind } from '../../utils/format';
import { InfoTab, ProbationTab, AssetsTab, PromoTab } from './EmployeeDrawer';

export default function Profile() {
  const [det, setDet] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState('info');

  const load = () => {
    setErr(null); setDet(null);
    fetchMe().then(setDet).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!det) return <LoadingState label="Đang tải hồ sơ của bạn…" />;

  if (det.hasEmployee === false) {
    return (
      <div className="content fade-in">
        <div className="card" style={{ padding: 36, textAlign: 'center' }}>
          <EmptyState>
            Tài khoản của bạn chưa được gắn với hồ sơ nhân viên nào.
            <br />Liên hệ phòng Nhân sự để được cập nhật.
          </EmptyState>
        </div>
      </div>
    );
  }

  const tabs = [
    ['info', 'Thông tin'],
    ['probation', 'Thử việc'],
    ['assets', `Tài sản (${det.assets.length})`],
    ['promo', `Thăng tiến (${det.promotions.length})`],
  ];

  return (
    <div className="content fade-in">
      {/* Header hồ sơ */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 16 }}>
        <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
          <Avatar emp={{ id: det.id, name: det.name, hasImg: det.hasImg }} size={64} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: '-.4px' }}>{det.name}</h2>
              <Badge kind={hbStatusKind(det.statusKey)} dot>{det.status}</Badge>
            </div>
            <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>{det.code} · {det.jobTitle} · {det.depName}</div>
            <div style={{ display: 'flex', gap: 14, marginTop: 10, flexWrap: 'wrap' }}>
              {det.email && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }} className="muted"><Icon name="mail" size={15} />{det.email}</span>}
              {det.phone && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5 }} className="muted"><Icon name="phone" size={15} />{det.phone}</span>}
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => window.open('/odoo/employees/' + det.id, '_blank')}>
            <Icon name="edit" size={15} />Sửa trong Odoo</button>
        </div>
        <div style={{ padding: '0 24px' }}>
          <div className="tabs" style={{ marginBottom: 0 }}>
            {tabs.map(([id, l]) => (
              <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => setTab(id)}>{l}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Nội dung tab — self-view nên xem đầy đủ (isHr=isMgr=true) */}
      <div className="card" style={{ padding: '22px 24px' }}>
        {tab === 'info' && <InfoTab det={det} isHr isMgr />}
        {tab === 'probation' && <ProbationTab det={det} />}
        {tab === 'assets' && <AssetsTab det={det} />}
        {tab === 'promo' && <PromoTab det={det} isMgr />}
      </div>
    </div>
  );
}
