/* ============================================================
   Màn "Yêu cầu dịch vụ nhân sự" — nhân viên gửi yêu cầu/góp ý (kể cả ẩn danh)
   tới HR hoặc trưởng phòng; HR/TP xử lý. Owner: Nhật Anh.
   Spec: docs/superpowers/specs/2026-07-26-hr-service-request-design.md §7
   ============================================================ */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState } from '../../components/states';
import { fetchMeta } from '../../api/service';
import RequestForm from './RequestForm';
import MyRequestsPanel from './MyRequestsPanel';
import InboxPanel from './InboxPanel';
import StatsPanel from './StatsPanel';

export default function Service({ search, focus }) {
  const [meta, setMeta] = useState(null);
  const [err, setErr] = useState(null);
  const [tab, setTab] = useState(null);
  const [creating, setCreating] = useState(false);
  const [reload, setReload] = useState(0);   // ép MyRequestsPanel tải lại sau khi gửi

  const load = () => {
    setErr(null); setMeta(null);
    fetchMeta().then(setMeta).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  /* Thông báo ở chuông mang theo targetTab ('mine' | 'inbox' — spec §8.1): với
     người vừa gửi vừa xử lý (Trưởng phòng) phải nhảy đúng tab, không thì đơn mở
     ra ở sai vai trò (người gửi thấy "Rút đơn" thay vì "Nhận xử lý"). */
  useEffect(() => {
    if (!focus || !focus.targetTab) return;
    if (focus.targetTab === 'inbox') setTab('inbox');
    else if (focus.targetTab === 'mine') setTab('me');
  }, [focus]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!meta) return <LoadingState label="Đang tải yêu cầu dịch vụ…" />;

  /* Tab hiện theo dữ liệu, không theo vai trò đoán ở FE:
     canSend  = tài khoản có gắn hồ sơ nhân viên (tài khoản vai trò thuần thì không);
     canHandle = HR / HR Manager / Trưởng phòng. */
  const tabs = [];
  if (meta.canSend) tabs.push(['me', 'Đơn của tôi']);
  if (meta.canHandle) tabs.push(['inbox', 'Cần xử lý'], ['stats', 'Thống kê']);
  const activeTab = tab || (tabs.length ? tabs[0][0] : null);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Yêu cầu dịch vụ nhân sự</h1>
        </div>
        <div className="actions">
          {meta.canSend && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Gửi yêu cầu
            </button>
          )}
        </div>
      </div>

      {tabs.length > 1 && (
        <div className="tabs">
          {tabs.map(([id, l]) => (
            <button key={id} className={'tab' + (activeTab === id ? ' active' : '')}
              onClick={() => setTab(id)}>{l}</button>
          ))}
        </div>
      )}

      {!tabs.length && (
        <div className="card" style={{ padding: 28, textAlign: 'center' }}>
          <div className="muted" style={{ fontSize: 13.5 }}>
            Tài khoản của bạn chưa gắn hồ sơ nhân viên nên chưa gửi được yêu cầu.
            Liên hệ HR để được gắn hồ sơ.
          </div>
        </div>
      )}

      {activeTab === 'me' && (
        <MyRequestsPanel key={reload} search={search} focus={focus} />
      )}

      {activeTab === 'inbox' && (
        <InboxPanel meta={meta} search={search} focus={focus} />
      )}

      {activeTab === 'stats' && <StatsPanel />}

      {creating && (
        <RequestForm meta={meta}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            setTab('me');
            setReload((n) => n + 1);
            // Số đơn ẩn danh còn lại trong ngày nằm ở meta ⇒ phải lấy lại,
            // nếu không form lần sau vẫn báo hạn mức cũ.
            fetchMeta().then(setMeta).catch(() => {});
          }} />
      )}
    </div>
  );
}
