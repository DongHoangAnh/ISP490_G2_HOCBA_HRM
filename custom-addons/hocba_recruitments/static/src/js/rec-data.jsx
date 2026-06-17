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

/* ── Vị trí tuyển dụng ── */
const REC_JOBS = [
  {
    id:'j1', title:'Tư vấn tuyển sinh', dept:'Kinh Doanh', deptColor:'#C8102E',
    status:'recruiting',
    headcount:null, filled:0, deadline:null, priority:'Cao',
    salary:null, exp:null, type:'Offline',
    desc:'Tư vấn và chốt hợp đồng học viên tiếng Trung.',
    tags:['Sales','Tư vấn'],
    jdLink:'https://docs.google.com/document/d/1ogsC-a1cR5-PUkttJ1MlkWeDu_eydbQl/edit',
    jdLabel:'Tư vấn tuyển sinh',
  },
  {
    id:'j2', title:'Giáo viên dạy tiếng Trung', dept:'R&D_SP', deptColor:'#0F766E',
    status:'recruiting',
    headcount:null, filled:0, deadline:null, priority:'Cao',
    salary:null, exp:'HSK5+', type:'Online / Offline',
    desc:'Giảng dạy tiếng Trung các cấp độ, chuẩn bị học liệu nội bộ.',
    tags:['Giảng dạy','HSK'],
    jdLink:'https://docs.google.com/document/d/1DB5HIdU5zA1KsSbCmw8JwAavBMoESZUaVoSWqVja0fM/edit?tab=t.0',
    jdLabel:'Giáo viên',
  },
  {
    id:'j3', title:'Chuyên viên R&D', dept:'R&D_SP', deptColor:'#0F766E',
    status:'recruiting',
    headcount:null, filled:0, deadline:null, priority:'Trung bình',
    salary:null, exp:null, type:'Online',
    desc:'Nghiên cứu và phát triển học liệu, giáo trình tiếng Trung.',
    tags:['R&D','Học liệu'],
    jdLink:'https://docs.google.com/document/d/1dnxGJS77C-ZVsG0RmmB-Kj9cjpXsuIi3cLiWGWPWybQ/edit?tab=t.0',
    jdLabel:'Chuyên viên R&D',
  },
  {
    id:'j4', title:'Trợ giảng', dept:'R&D_SP', deptColor:'#0F766E',
    status:'stopped',
    headcount:null, filled:0, deadline:null, priority:'Thấp',
    salary:null, exp:null, type:'Offline',
    desc:'Hỗ trợ giáo viên trong quá trình giảng dạy và quản lý lớp học.',
    tags:['Giảng dạy','Học thuật'],
    jdLink:'https://docs.google.com/document/d/1VYX4GcWvCz_77BC_uyuNOCMhFxN7vzPsPFIsFi_xBoM/edit?tab=t.0',
    jdLabel:'JD Nhân viên Học thuật - HocBaHSK',
  },
  {
    id:'j5', title:'Giáo vụ', dept:'Vận Hành', deptColor:'#1D4ED8',
    status:'stopped',
    headcount:null, filled:0, deadline:null, priority:'Thấp',
    salary:null, exp:null, type:'Offline',
    desc:'Quản lý và điều phối lịch học, lớp học và các hoạt động học thuật.',
    tags:['Vận hành','Giáo vụ'],
    jdLink:'https://docs.google.com/document/d/1_hb2L1eOeL2ZAe0Hi3CFofaWfcLEGPCQtlCLnQYw-PE/edit?usp=sharing',
    jdLabel:'Giáo vụ',
  },
  {
    id:'j6', title:'Quản lý học viên', dept:'Vận Hành', deptColor:'#1D4ED8',
    status:'recruiting',
    headcount:null, filled:0, deadline:null, priority:'Cao',
    salary:null, exp:null, type:'Offline',
    desc:'Theo dõi tiến độ, hỗ trợ và chăm sóc học viên trong quá trình học.',
    tags:['CS','Vận hành','Học viên'],
    jdLink:'https://docs.google.com/document/d/1QVojI-3Qg0EMQaCMuAVlTZRXmnntp3Kw/edit?tab=t.0',
    jdLabel:'Quản lý học viên',
  },
  {
    id:'j7', title:'Content Marketing', dept:'Marketing', deptColor:'#D9A400',
    status:'recruiting',
    headcount:null, filled:0, deadline:null, priority:'Trung bình',
    salary:null, exp:null, type:'Online',
    desc:'Sản xuất nội dung TikTok, Facebook, viết bài blog & email marketing.',
    tags:['Content','TikTok','SEO'],
    jdLink:'https://docs.google.com/document/d/1mNMLN8uRfzAU6QNbXpCpqvSeJi8AukYRykMxYTM4L-s/edit?tab=t.0',
    jdLabel:'Content Marketing',
  },
  {
    id:'j8', title:'Hành chính nhân sự', dept:'HCNS', deptColor:'#7C3AED',
    status:'stopped',
    headcount:null, filled:0, deadline:null, priority:'Thấp',
    salary:null, exp:null, type:'Offline',
    desc:'Quản lý hồ sơ nhân sự, hợp đồng lao động và các thủ tục hành chính.',
    tags:['HCNS','Hành chính'],
    jdLink:'https://docs.google.com/document/d/1Kx4uy4ZPW2ajRJRG6xxSpwrhnqyf0NFJsX_RUSLZFFM/edit?tab=t.0',
    jdLabel:'Hành chính nhân sự',
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
