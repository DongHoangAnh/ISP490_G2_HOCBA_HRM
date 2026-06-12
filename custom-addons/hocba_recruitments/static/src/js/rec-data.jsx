/* ============================================================
   HỌC BÁ — Module Tuyển dụng / Dữ liệu
   ============================================================ */

/* ── Utility ── */
const fmtVND = (n) => n.toLocaleString('vi-VN');
const fmtDate = (s) => {
  if (!s) return '—';
  const [y, m, d] = s.split('-');
  return `${d}/${m}/${y}`;
};
const fmtDateShort = (s) => {
  if (!s) return '—';
  const [, m, d] = s.split('-');
  return `${d}/${m}`;
};

function removeAccents(str) {
  return str.normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D');
}
const AV = ['av-a','av-b','av-c','av-d','av-e','av-f'];
const initials = (name) => {
  const p = name.trim().split(/\s+/);
  return (p[p.length-2]?.[0] || '') + (p[p.length-1]?.[0] || '');
};
const avClass = (i) => AV[i % AV.length];

/* ── Seed data tĩnh ── */
const HO  = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Phan','Vũ','Đặng','Bùi','Đỗ','Hồ','Ngô','Dương','Lý'];
const DEM = ['Thị','Văn','Hồng','Quỳnh','Thu','Minh','Ngọc','Hải','Thanh','Tuấn','Diệu','Khánh'];
const TEN = ['Anh','Bình','Châu','Dung','Giang','Hà','Hằng','Hiếu','Hương','Khánh','Lan','Linh','Mai','Nam','Ngân','Nhung','Phúc','Quyên','Sơn','Tâm','Thảo','Trang','Trung','Tú','Vân','Duy'];

/* ── Pipeline stages ── */
const REC_STAGES = [
  { id:'new',    name:'Hồ sơ mới',  color:'#78716C', icon:'inbox',  desc:'Tiếp nhận hồ sơ ứng tuyển' },
  { id:'screen', name:'Lọc CV',     color:'#1D4ED8', icon:'filter', desc:'Lọc & đánh giá hồ sơ' },
  { id:'inter',  name:'Phỏng vấn',  color:'#D9A400', icon:'mic',    desc:'Phỏng vấn trực tiếp / online' },
  { id:'offer',  name:'Gửi Offer',  color:'#6D28D9', icon:'mail',   desc:'Gửi thư đề nghị & đàm phán' },
  { id:'hired',  name:'Nhận việc',  color:'#15803D', icon:'check',  desc:'Xác nhận & chuẩn bị onboarding' },
];

/* ── Vị trí tuyển dụng đang mở ── */
const REC_JOBS = [
  {
    id:'j1', title:'Tư vấn tuyển sinh', dept:'Kinh Doanh', deptColor:'#C8102E',
    headcount:5, filled:2, deadline:'2026-07-15', priority:'Cao',
    salary:'6.2M – 20M + COM', exp:'Không yêu cầu KN', type:'Offline',
    desc:'Tư vấn và chốt hợp đồng học viên tiếng Trung. Hoa hồng hấp dẫn.',
    tags:['Sales','Tư vấn','COM'],
  },
  {
    id:'j2', title:'Giáo viên tiếng Trung', dept:'R&D_SP', deptColor:'#0F766E',
    headcount:3, filled:1, deadline:'2026-07-01', priority:'Cao',
    salary:'9M – 14M', exp:'HSK5+', type:'Online / Offline',
    desc:'Giảng dạy tiếng Trung các cấp độ, chuẩn bị học liệu nội bộ.',
    tags:['Giảng dạy','HSK','R&D'],
  },
  {
    id:'j3', title:'Content Marketing', dept:'Marketing', deptColor:'#D9A400',
    headcount:2, filled:0, deadline:'2026-07-30', priority:'Trung bình',
    salary:'7M – 12M', exp:'1 năm KN', type:'Online',
    desc:'Sản xuất nội dung TikTok, Facebook, viết bài blog & email marketing.',
    tags:['Content','TikTok','SEO'],
  },
  {
    id:'j4', title:'Quản lý học viên', dept:'Vận Hành', deptColor:'#1D4ED8',
    headcount:1, filled:0, deadline:'2026-07-15', priority:'Cao',
    salary:'8M – 12M', exp:'1–2 năm KN', type:'Offline',
    desc:'Theo dõi tiến độ, hỗ trợ và chăm sóc học viên trong quá trình học.',
    tags:['CS','Vận hành','Học viên'],
  },
  {
    id:'j5', title:'Digital ADS', dept:'Marketing', deptColor:'#D9A400',
    headcount:1, filled:0, deadline:'2026-08-01', priority:'Trung bình',
    salary:'9M – 15M', exp:'2 năm KN', type:'Online',
    desc:'Lên kế hoạch & chạy quảng cáo Facebook Ads, Google Ads, TikTok Ads.',
    tags:['Facebook Ads','Google Ads','Performance'],
  },
  {
    id:'j6', title:'R&D học liệu', dept:'R&D_SP', deptColor:'#0F766E',
    headcount:2, filled:1, deadline:'2026-07-15', priority:'Thấp',
    salary:'8M – 13M', exp:'HSK4+', type:'Online',
    desc:'Nghiên cứu và phát triển tài liệu, giáo trình học tiếng Trung.',
    tags:['R&D','Học liệu','Tiếng Trung'],
  },
];

/* ── Sinh danh sách ứng viên (deterministic RNG) ── */
function genApplicants() {
  let rng = 20260609;
  const rand = () => { rng = (rng * 1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const pick = (a) => a[Math.floor(rand() * a.length)];

  const stageDist = [
    'new','new','new','new','new','new',    // 6 mới
    'screen','screen','screen','screen',     // 4 lọc CV
    'inter','inter','inter','inter','inter', // 5 phỏng vấn
    'offer','offer','offer',                 // 3 offer
    'hired','hired','hired',                 // 3 nhận việc
  ];

  const sources = ['Facebook','TopCV','Referral','Website','TikTok','TopCV','Facebook','Facebook'];
  const exps = ['Fresher','1 năm KN','2 năm KN','3 năm KN','HSK5','HSK6','Sinh viên','Fresher'];
  const positions = REC_JOBS.map(j => j.title);

  return stageDist.map((stage, i) => {
    const name = `${pick(HO)} ${pick(DEM)} ${pick(TEN)}`;
    const job = REC_JOBS[i % REC_JOBS.length];
    const hasInterview = stage === 'inter' || stage === 'offer' || stage === 'hired';
    const interviewDay = hasInterview ? (6 + Math.floor(rand() * 10)) : null;
    const interview = hasInterview
      ? `2026-06-${String(Math.min(interviewDay, 30)).padStart(2,'0')}`
      : null;
    return {
      id: 'UV' + String(i + 1).padStart(3, '0'),
      name, initials: initials(name), avatar: avClass(i + 2),
      pos: job.title, posId: job.id,
      stage,
      phone: '09' + String(Math.floor(rand() * 90000000) + 10000000),
      email: removeAccents(name).toLowerCase().replace(/\s+/g, '') + (i + 1) + '@gmail.com',
      exp: pick(exps),
      rating: Math.floor(rand() * 3) + 3,
      days: Math.floor(rand() * 18) + 1,
      source: pick(sources),
      interview,
      note: stage === 'hired' ? 'Đã xác nhận nhận việc' : stage === 'offer' ? 'Đang chờ phản hồi offer' : '',
    };
  });
}
const APPLICANTS = genApplicants();

/* ── Computed stats ── */
const REC_STATS = (() => {
  const byStage = {};
  REC_STAGES.forEach(s => { byStage[s.id] = APPLICANTS.filter(a => a.stage === s.id).length; });
  const hired = byStage.hired || 0;
  const offerReached = (byStage.offer || 0) + hired;
  const interviewsThisWeek = APPLICANTS.filter(a =>
    a.interview && a.interview >= '2026-06-09' && a.interview <= '2026-06-13'
  ).length;
  const todayInterviews = APPLICANTS.filter(a => a.interview === '2026-06-09').length;
  return {
    totalApplicants: APPLICANTS.length,
    openPositions: REC_JOBS.length,
    openSlots: REC_JOBS.reduce((s, j) => s + (j.headcount - j.filled), 0),
    byStage,
    hired, offerReached,
    offerAcceptRate: offerReached > 0 ? Math.round(hired / offerReached * 100) : 0,
    interviewsThisWeek, todayInterviews,
    avgDaysToHire: 21,
  };
})();

Object.assign(window, {
  REC_STAGES, REC_JOBS, APPLICANTS, REC_STATS,
  fmtVND, fmtDate, fmtDateShort, initials, avClass, removeAccents,
});
