/* Màn Tuyển dụng — điều phối tab (mẫu chuẩn: màn Nhân viên / Chấm công).
   Owner: Việt. API: /hocba-hrm/api/recruitment/* (đang chờ spec).
   Giai đoạn này mới dựng khung tab; nội dung từng tab nối API sau. */
import { useState, useEffect } from 'react';
import CvList from './CvList';
import JdLibrary from './JdLibrary';
import RequestTracking from './RequestTracking';
import Requests from './Requests';
import MailTemplates from './MailTemplates';
import InterviewSlots from './InterviewSlots';
import Offers from './Offers';
import MailLogs from './MailLogs';

/* Thứ tự tab bám theo luồng làm việc hằng ngày: ba màn xử lý ứng viên
   (CV → phỏng vấn → offer) trước, rồi tới màn theo dõi/quản trị đợt tuyển,
   cuối cùng là mail. */
const TABS = [
  ['cv',         'Danh sách CV'],
  ['interviews', 'Danh sách PV'],
  ['offers',     'Offer & Nhận việc'],
  ['jobs',       'Theo dõi tuyển dụng'],
  ['requests',   'Phiếu yêu cầu'],
  ['jd',         'Kho quản lý JD'],
  ['mails',      'Mail mẫu tuyển dụng'],
  ['maillog',    'Lịch sử gửi mail'],
];

const TAB_DESC = {
  cv:         'Tổng hợp & lọc CV ứng viên, kết quả lọc và trạng thái gọi điện.',
  interviews: 'Ứng viên đang ở bước phỏng vấn, trạng thái đã đến / không đến.',
  offers:     'Ứng viên ở bước Gửi Offer & Onboarding, nội dung offer và ngày nhận việc.',
  jobs:       'Theo dõi tiến độ từng phiếu yêu cầu: số lượng tuyển, đã tuyển, CV nộp vào, pass/fail, deadline.',
  requests:   'Phiếu yêu cầu tuyển dụng từ các bộ phận.',
  jd:         'Tra cứu nhanh JD theo vị trí · phòng ban · trạng thái.',
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
      ) : activeTab === 'jd' ? (
        <JdLibrary search={search} />
      ) : activeTab === 'jobs' ? (
        <RequestTracking search={search} />
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
