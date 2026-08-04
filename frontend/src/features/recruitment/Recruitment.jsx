/* Màn Tuyển dụng — điều phối tab (mẫu chuẩn: màn Nhân viên / Chấm công).
   Owner: Việt. API: /hocba-hrm/api/recruitment/* (đang chờ spec).
   Giai đoạn này mới dựng khung tab; nội dung từng tab nối API sau. */
import { useState, useEffect } from 'react';
import CvList from './CvList';
import Jobs from './Jobs';
import Requests from './Requests';
import MailTemplates from './MailTemplates';
import InterviewSlots from './InterviewSlots';
import Offers from './Offers';
import MailLogs from './MailLogs';

const TABS = [
  ['cv',         'Danh sách CV'],
  ['jobs',       'Vị trí tuyển dụng / JD'],
  ['requests',   'Phiếu yêu cầu'],
  ['interviews', 'Danh sách PV'],
  ['offers',     'Offer & Nhận việc'],
  ['mails',      'Mail mẫu tuyển dụng'],
  ['maillog',    'Lịch sử gửi mail'],
];

const TAB_DESC = {
  cv:         'Tổng hợp & lọc CV ứng viên, kết quả lọc và trạng thái gọi điện.',
  jobs:       'Danh sách vị trí tuyển dụng và mô tả công việc (JD).',
  requests:   'Phiếu yêu cầu tuyển dụng từ các bộ phận.',
  interviews: 'Ứng viên đang ở bước phỏng vấn, trạng thái đã đến / không đến.',
  offers:     'Ứng viên ở bước Gửi Offer & Onboarding, nội dung offer và ngày nhận việc.',
  mails:      'Mẫu email dùng trong quy trình tuyển dụng.',
};

export default function Recruitment({ search, focus }) {
  const [tab, setTab] = useState(() => localStorage.getItem('hocba_rec_tab') || 'cv');

  const select = (id) => { setTab(id); localStorage.setItem('hocba_rec_tab', id); };

  /* Bấm thông báo ở chuông → về đúng tab rồi để màn con mở drawer:
     'cv' = CV quá hạn xử lý · 'requests' = phiếu yêu cầu chờ duyệt. */
  useEffect(() => {
    if (!focus) return;
    if (focus.targetTab === 'cv') select('cv');
    else if (focus.targetTab === 'requests') select('requests');
  }, [focus && focus.nonce]);
  const label = TABS.find(([id]) => id === tab)?.[1] || '';
  // Tab lưu trong localStorage có thể không còn (vd 'config' cũ) → về tab đầu.
  const activeTab = TABS.some(([id]) => id === tab) ? tab : 'cv';

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tuyển dụng</h1>
          <p>Quản lý quy trình tuyển dụng Học Bá · dữ liệu trực tiếp từ Odoo</p>
        </div>
      </div>

      <div className="tabs">
        {TABS.map(([id, l]) => (
          <button key={id} className={'tab' + (activeTab === id ? ' active' : '')} onClick={() => select(id)}>{l}</button>
        ))}
      </div>

      {activeTab === 'cv' ? (
        <CvList search={search} focus={focus} />
      ) : activeTab === 'jobs' ? (
        <Jobs search={search} />
      ) : activeTab === 'requests' ? (
        <Requests search={search} focus={focus} />
      ) : activeTab === 'interviews' ? (
        <InterviewSlots />
      ) : activeTab === 'offers' ? (
        <Offers search={search} />
      ) : activeTab === 'mails' ? (
        <MailTemplates search={search} />
      ) : activeTab === 'maillog' ? (
        <MailLogs search={search} />
      ) : (
        <div className="card" style={{ padding: 36, textAlign: 'center' }}>
          <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 8 }}>{label}</div>
          <p className="muted" style={{ margin: 0 }}>
            {TAB_DESC[tab]}
            <br />Đang chờ nối API <code>/hocba-hrm/api/recruitment/*</code>.
          </p>
        </div>
      )}
    </div>
  );
}
