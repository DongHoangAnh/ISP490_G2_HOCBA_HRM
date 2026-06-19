/* ============================================================
   Màn "Hồ sơ của tôi" (self-service) — mọi nhân viên xem hồ sơ
   CỦA CHÍNH MÌNH. Tái dùng các tab của EmployeeDrawer. Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchMe, updateMyPhoto } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbStatusKind } from '../../utils/format';
import { InfoTab, ProbationTab, AssetsTab, PromoTab } from './EmployeeDrawer';
import ProfileEditForm from './ProfileEditForm';

export default function Profile() {
  const [det, setDet] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState('info');
  const [editing, setEditing] = useState(false);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoBusy, setPhotoBusy] = useState(false);

  const load = () => {
    setErr(null); setDet(null);
    fetchMe().then(setDet).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  // Họp #2: nhân viên tự cập nhật ảnh đại diện của mình.
  const onPickPhoto = (ev) => {
    const file = ev.target.files && ev.target.files[0];
    ev.target.value = '';
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) { alert('Ảnh tối đa 8MB.'); return; }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result;
      setPhotoPreview(dataUrl);
      setPhotoBusy(true);
      updateMyPhoto(dataUrl)
        .then((d) => setDet(d))
        .catch((e) => { setPhotoPreview(null); alert(e.message || 'Tải ảnh thất bại.'); })
        .finally(() => setPhotoBusy(false));
    };
    reader.readAsDataURL(file);
  };

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
          <label title="Đổi ảnh đại diện"
            style={{ position: 'relative', width: 64, height: 64, flexShrink: 0, cursor: photoBusy ? 'wait' : 'pointer' }}>
            {photoPreview ? (
              <img src={photoPreview} alt=""
                style={{ width: 64, height: 64, borderRadius: '50%', objectFit: 'cover' }} />
            ) : (
              <Avatar emp={{ id: det.id, name: det.name, hasImg: det.hasImg }} size={64} />
            )}
            <span style={{ position: 'absolute', right: -2, bottom: -2, width: 22, height: 22,
              borderRadius: '50%', background: 'var(--red-600)', color: '#fff',
              display: 'grid', placeItems: 'center', border: '2px solid #fff' }}>
              <Icon name={photoBusy ? 'clock' : 'edit'} size={12} />
            </span>
            <input type="file" accept="image/*" onChange={onPickPhoto} disabled={photoBusy}
              style={{ display: 'none' }} />
          </label>
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
          <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
            <Icon name="edit" size={15} />Cập nhật thông tin</button>
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
        {tab === 'info' && <InfoTab det={det} isHr isMgr depEditable onUpdated={setDet} />}
        {tab === 'probation' && <ProbationTab det={det} />}
        {tab === 'assets' && <AssetsTab det={det} />}
        {tab === 'promo' && <PromoTab det={det} isMgr />}
      </div>

      {editing && (
        <ProfileEditForm det={det}
          onClose={() => setEditing(false)}
          onSaved={(d) => { setDet(d); setEditing(false); }} />
      )}
    </div>
  );
}
