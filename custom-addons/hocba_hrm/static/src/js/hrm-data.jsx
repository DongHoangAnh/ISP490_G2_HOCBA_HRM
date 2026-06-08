/* ============================================================
   HOC BA HRM — Mock data (rút từ tài liệu phân tích nội bộ)
   ============================================================ */

const AV = ['av-a','av-b','av-c','av-d','av-e','av-f'];
const initials = (name) => {
  const p = name.trim().split(/\s+/);
  return (p[p.length-2]?.[0] || '') + (p[p.length-1]?.[0] || '');
};
const avClass = (i) => AV[i % AV.length];
const fmtVND = (n) => n.toLocaleString('vi-VN');
const fmtM = (n) => (n/1e6).toLocaleString('vi-VN', {maximumFractionDigits: 1}) + 'tr';

/* ---- Phòng ban ---- */
const DEPARTMENTS = [
  { id:'kd',  name:'Kinh Doanh',   short:'KD',  leader:'Trần Thị Ngọc Ánh', fn:'Tư vấn tuyển sinh, chốt học viên', total:20, ct:10, tv:10, color:'#C8102E' },
  { id:'mkt', name:'Marketing',    short:'MKT', leader:'Nguyễn Trung Kiên',  fn:'Content, Ads, Social, thương hiệu', total:14, ct:10, tv:4,  color:'#D9A400' },
  { id:'rd',  name:'R&D_SP',       short:'R&D', leader:'Phan Quỳnh Giang',   fn:'Giáo viên, R&D, học liệu, Tester',  total:13, ct:7,  tv:6,  color:'#0F766E' },
  { id:'vh',  name:'Vận Hành',     short:'VH',  leader:'Cao Vân Khánh',      fn:'Quản lý học viên, lớp học',          total:4,  ct:2,  tv:2,  color:'#1D4ED8' },
  { id:'kt',  name:'Kế Toán',      short:'KT',  leader:'Nguyễn Thị Len',     fn:'Thu chi, quyết toán (online)',       total:2,  ct:1,  tv:1,  color:'#6D28D9' },
  { id:'ns',  name:'Nhân Sự',      short:'NS',  leader:'Hoàng Thị Ngọc Anh', fn:'HR, tuyển dụng, hành chính',         total:2,  ct:1,  tv:1,  color:'#BE185D' },
];

/* ---- Chức danh phổ biến (hr.job) ---- */
const JOBS = {
  tvts:'Tư vấn tuyển sinh', tbp:'Trưởng phòng', content:'Content Marketing',
  ads:'Digital ADS', gv:'Giáo viên tiếng Trung', rd:'R&D học liệu',
  tester:'Tester', qlhv:'Quản lý học viên', kt:'Kế toán', hcns:'HCNS',
  mentor:'Mentor học tập', design:'Designer',
};

/* ---- Sinh danh sách 53 nhân sự ---- */
const HO = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Phan','Vũ','Đặng','Bùi','Đỗ','Hồ','Ngô','Dương','Lý','Đinh','Cao','Trịnh','Mai'];
const DEM = ['Thị','Văn','Hồng','Quỳnh','Thu','Minh','Ngọc','Hải','Thanh','Tuấn','Diệu','Khánh','Gia','Bảo','Phương','Thùy'];
const TEN = ['Anh','Bình','Châu','Dung','Giang','Hà','Hằng','Hiếu','Hương','Khánh','Lan','Linh','Mai','Nam','Ngân','Nhung','Phúc','Quân','Quyên','Sơn','Tâm','Thảo','Trang','Trung','Tú','Vân','Việt','Yến','Duy','Hoa'];
const BANKS = ['Vietcombank','Techcombank','MB Bank','BIDV','ACB','VPBank','TPBank'];

function genEmployees() {
  let rng = 20260530;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const pick = (arr) => arr[Math.floor(rand()*arr.length)];

  // chia số lượng theo phòng ban (đúng tổng 53)
  const plan = [
    { dep:'kd', n:20, jobs:['tvts','tvts','tvts','tvts','tbp'] },
    { dep:'mkt', n:14, jobs:['content','ads','design','tbp'] },
    { dep:'rd', n:13, jobs:['gv','gv','rd','tester','tbp'] },
    { dep:'vh', n:4, jobs:['qlhv','mentor','tbp'] },
    { dep:'kt', n:2, jobs:['kt','tbp'] },
    { dep:'ns', n:2, jobs:['hcns','tbp'] },
  ];
  const leaders = {
    kd:'Trần Thị Ngọc Ánh', mkt:'Nguyễn Trung Kiên', rd:'Phan Quỳnh Giang',
    vh:'Cao Vân Khánh', kt:'Nguyễn Thị Len', ns:'Hoàng Thị Ngọc Anh',
  };
  const list = [];
  let idx = 1;
  for (const grp of plan) {
    const dep = DEPARTMENTS.find(d=>d.id===grp.dep);
    let ctLeft = dep.ct;
    for (let k=0;k<grp.n;k++){
      const isLeader = k===0;
      let name;
      if (isLeader) name = leaders[grp.dep];
      else name = `${pick(HO)} ${pick(DEM)} ${pick(TEN)}`;
      const jobKey = isLeader ? 'tbp' : pick(grp.jobs.filter(j=>j!=='tbp'));
      // trạng thái: ưu tiên CT cho leader & đầu danh sách
      let status;
      if (isLeader) { status='Chính thức'; ctLeft--; }
      else if (ctLeft>0 && rand()>0.35) { status='Chính thức'; ctLeft--; }
      else status='Thử việc';
      // hình thức
      let type;
      if (grp.dep==='kt') type='Online';
      else if (jobKey==='gv' || jobKey==='content' || jobKey==='design') type = rand()>0.5?'Online':'Offline';
      else if (rand()>0.78) type='CTV';
      else type='Offline';

      const code = 'HB.' + String(idx).padStart(2,'0');
      const startY = status==='Chính thức' ? pick([2022,2023,2023,2024,2024,2025]) : 2026;
      const startM = String(Math.floor(rand()*12)+1).padStart(2,'0');
      const startD = String(Math.floor(rand()*27)+1).padStart(2,'0');
      const bday = `${pick([1990,1992,1993,1995,1996,1997,1998,1999,2000,2001,2002])}-${String(Math.floor(rand()*12)+1).padStart(2,'0')}-${String(Math.floor(rand()*27)+1).padStart(2,'0')}`;
      const phone = '09' + String(Math.floor(rand()*90000000)+10000000);
      const baseWage = jobKey==='tbp' ? 14000000 + Math.floor(rand()*8)*1000000
        : jobKey==='gv' ? 9000000 + Math.floor(rand()*5)*1000000
        : jobKey==='tvts' ? 6200000 + Math.floor(rand()*4)*1000000
        : 7000000 + Math.floor(rand()*5)*1000000;
      const lvl = jobKey==='tvts' ? Math.floor(rand()*8) : null;

      list.push({
        id: code, code, name, dep:grp.dep, depName:dep.name, depShort:dep.short,
        job:jobKey, jobTitle: JOBS[jobKey], status, type,
        avatar: avClass(idx), initials: initials(name),
        start:`${startY}-${startM}-${startD}`, bday, phone,
        email: removeAccents(name).toLowerCase().replace(/\s+/g,'.') + '@hocba.edu.vn',
        bank: pick(BANKS), acct: String(Math.floor(rand()*9000000000)+1000000000),
        wage: baseWage, level: lvl, isLeader,
        cccd: String(Math.floor(rand()*9e11)+1e11),
      });
      idx++;
    }
  }
  return list;
}

function removeAccents(str){
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D');
}

const EMPLOYEES = genEmployees();

/* ---- KPI / COM level table (TVTS) ---- */
const KPI_LEVELS = [
  { lv:0,  hard:6200000,  target:50000000,  com:1.0, comGet:500000,   total:6700000 },
  { lv:1,  hard:6200000,  target:90000000,  com:1.5, comGet:1350000,  total:7550000 },
  { lv:2,  hard:7000000,  target:120000000, com:2.5, comGet:3000000,  total:10000000 },
  { lv:3,  hard:8000000,  target:160000000, com:3.0, comGet:4800000,  total:12800000 },
  { lv:5,  hard:9200000,  target:270000000, com:4.0, comGet:10800000, total:20000000 },
  { lv:7,  hard:11400000, target:420000000, com:4.7, comGet:19740000, total:31140000 },
  { lv:10, hard:15000000, target:720000000, com:5.2, comGet:37440000, total:52440000 },
];

/* ---- Chấm công hôm nay (29/05/2026) ---- */
function genAttendance() {
  let rng = 7777;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const offline = EMPLOYEES.filter(e=>e.type==='Offline');
  return offline.map(e=>{
    const r = rand();
    let status, checkIn, checkOut, late=0, type='Onsite';
    if (r < 0.62) { status='Đúng giờ'; checkIn=`0${8+Math.floor(rand()*1)}:${String(Math.floor(rand()*25)).padStart(2,'0')}`; checkOut='19:0'+Math.floor(rand()*6); }
    else if (r < 0.78) { status='Đi trễ'; const m=Math.floor(rand()*40)+5; late=m; checkIn=`09:${String(30+Math.floor(m/2)).padStart(2,'0')}`; checkOut='19:0'+Math.floor(rand()*6); }
    else if (r < 0.88) { status='Làm online'; type='Offsite'; checkIn='08:'+String(Math.floor(rand()*40)).padStart(2,'0'); checkOut='18:5'+Math.floor(rand()*9); }
    else if (r < 0.95) { status='Nghỉ phép'; checkIn='—'; checkOut='—'; type='—'; }
    else { status='Chưa chấm'; checkIn='—'; checkOut='—'; type='—'; }
    return { ...e, status, checkIn, checkOut, late, attType:type };
  });
}
const ATTENDANCE = genAttendance();

/* ---- Đơn quên chấm công chờ duyệt ---- */
const FORGOT_REQUESTS = EMPLOYEES.slice(8,13).map((e,i)=>({
  ...e, date:`2026-05-2${5-i}`, missType: i%2?'Quên check-out':'Quên check-in',
  proposed: i%2?'19:02':'08:24', reason:['Quên bấm app Lark khi về','App lỗi không check-in được','Họp ngoài VP buổi sáng','Đi gặp khách hàng','Mất mạng lúc tan ca'][i],
  state:'Chờ duyệt',
}));

/* ---- OT log ---- */
const OT_LOG = EMPLOYEES.filter(e=>e.type==='Offline').slice(0,6).map((e,i)=>({
  ...e, date:`2026-05-2${8-i}`, hours:[2,1.5,3,2,4,1][i],
  rate:[150,150,300,100,150,150][i], reason:['Chạy chiến dịch tuyển sinh','Soạn học liệu gấp','Trực lễ 30/4','Tổng kết tháng','Sự kiện khai giảng','Hỗ trợ chốt số'][i],
}));

/* ---- Tuyển dụng — pipeline ---- */
const REC_STAGES = [
  { id:'new',     name:'Hồ sơ mới',   color:'#78716C' },
  { id:'screen',  name:'Lọc CV',      color:'#1D4ED8' },
  { id:'inter',   name:'Phỏng vấn',   color:'#D9A400' },
  { id:'offer',   name:'Gửi Offer',   color:'#6D28D9' },
  { id:'hired',   name:'Nhận việc',   color:'#15803D' },
];
const REC_POSITIONS = ['Tư vấn tuyển sinh','Giáo viên tiếng Trung','Content Marketing','Quản lý học viên','Digital ADS','R&D học liệu'];

function genApplicants() {
  let rng = 31337;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const pick = (a)=>a[Math.floor(rand()*a.length)];
  const stageDist = ['new','new','new','new','new','screen','screen','screen','screen','inter','inter','inter','offer','offer','hired','hired'];
  const out = [];
  for (let i=0;i<22;i++){
    const name = `${pick(HO)} ${pick(DEM)} ${pick(TEN)}`;
    const stage = stageDist[i % stageDist.length];
    out.push({
      id:'AP'+String(i+1).padStart(3,'0'), name, initials:initials(name), avatar:avClass(i+3),
      pos: pick(REC_POSITIONS), stage,
      phone:'09'+String(Math.floor(rand()*90000000)+10000000),
      email: removeAccents(name).toLowerCase().replace(/\s+/g,'')+(i)+'@gmail.com',
      exp: pick(['Fresher','1 năm KN','2 năm KN','3 năm KN','HSK5','HSK6','Sinh viên']),
      rating: Math.floor(rand()*3)+3,
      days: Math.floor(rand()*14)+1,
      source: pick(['Facebook','TopCV','Referral','Website','TikTok']),
      interview: stage==='inter'||stage==='offer'||stage==='hired' ? `2026-06-0${Math.floor(rand()*9)+1}` : null,
    });
  }
  return out;
}
const APPLICANTS = genApplicants();

/* ---- Bảng lương tháng 05/2026 ---- */
function genPayroll() {
  let rng = 55555;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  return EMPLOYEES.map(e=>{
    const offline = e.type==='Offline';
    const wage = e.wage;
    const pcXang = offline ? 500000 : 0;
    const pcGui = offline ? 100000 : 0;
    const pcChucVu = e.isLeader ? 2000000 : 0;
    const pcTham = e.status==='Chính thức' ? (rand()>0.5?500000:300000) : 0;
    const htDienThoai = e.isLeader || e.job==='tvts' ? 300000 : 0;
    const htAnCa = offline ? 700000 : 0;
    const htTrangPhuc = offline ? 400000 : 0;
    const htDiLai = !offline ? 200000 : 0;
    // COM cho TVTS
    let com = 0, revenue = 0;
    if (e.job==='tvts' && e.level!=null){
      const lvRow = KPI_LEVELS.reduce((p,c)=> Math.abs(c.lv-e.level)<Math.abs(p.lv-e.level)?c:p, KPI_LEVELS[0]);
      revenue = Math.floor(lvRow.target * (0.7+rand()*0.6));
      com = Math.floor(revenue * lvRow.com/100);
    }
    const gross = wage + pcXang + pcGui + pcChucVu + pcTham + htDienThoai + htAnCa + htTrangPhuc + htDiLai + com;
    const bhxhBase = Math.min(Math.max(wage, 5100000), 7300000);
    const bhxh = Math.round(bhxhBase*0.08);
    const bhyt = Math.round(bhxhBase*0.015);
    const bhtn = Math.round(bhxhBase*0.01);
    const taxableBase = gross - bhxh - bhyt - bhtn - 11000000;
    let tax = 0;
    if (taxableBase>0){ tax = Math.round(taxableBase*0.1); }
    const net = gross - bhxh - bhyt - bhtn - tax;
    return {
      ...e, period:'05/2026', offline, wage,
      allow:{ pcXang, pcGui, pcChucVu, pcTham, htDienThoai, htAnCa, htTrangPhuc, htDiLai },
      com, revenue, gross, bhxh, bhyt, bhtn, tax, net,
      workDays: offline ? (22 - Math.floor(rand()*3)) : 22, standardDays:22,
      state: rand()>0.25 ? 'Đã duyệt' : 'Nháp',
    };
  });
}
const PAYROLL = genPayroll();

/* ---- Tổng hợp số liệu ---- */
const STATS = {
  total: 53, ct: 30, tv: 23, departments: 6,
  offline: 16, online: 20, ctv: 17,
  presentToday: ATTENDANCE.filter(a=>a.status==='Đúng giờ'||a.status==='Đi trễ').length,
  lateToday: ATTENDANCE.filter(a=>a.status==='Đi trễ').length,
  remoteToday: ATTENDANCE.filter(a=>a.status==='Làm online').length,
  pendingLeave: 7, openPositions: 6, applicants: APPLICANTS.length,
  payrollTotal: PAYROLL.reduce((s,p)=>s+p.net,0),
  contractsExpiring: 4,
};

/* ============================================================
   NGHỈ PHÉP & LÀM ONLINE
   ============================================================ */
const LEAVE_TYPES = [
  { id:'annual',    name:'Nghỉ phép năm',      color:'#15803D', kind:'green',  deduct:true  },
  { id:'sick',      name:'Nghỉ ốm',            color:'#B45309', kind:'amber',  deduct:true  },
  { id:'maternity', name:'Nghỉ thai sản',      color:'#BE185D', kind:'red',    deduct:false },
  { id:'early',     name:'Về sớm / Đi trễ',    color:'#1D4ED8', kind:'blue',   deduct:false },
  { id:'wfh',       name:'Làm online / WFH',   color:'#6D28D9', kind:'violet', deduct:false },
  { id:'unpaid',    name:'Nghỉ không lương',   color:'#78716C', kind:'gray',   deduct:false },
];
const LEAVE_STATES = ['Chờ Leader','Chờ HCNS','Đã duyệt','Từ chối'];

function genLeaveRequests() {
  let rng = 90909;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const pick = (a)=>a[Math.floor(rand()*a.length)];
  const reasons = {
    annual:['Về quê thăm gia đình','Du lịch cùng gia đình','Việc cá nhân','Nghỉ dưỡng sức'],
    sick:['Sốt cao, có giấy bác sĩ','Khám bệnh định kỳ','Đau dạ dày','Cảm cúm'],
    maternity:['Nghỉ thai sản 6 tháng theo quy định'],
    early:['Đón con đi học','Có việc gia đình buổi chiều','Khám sức khỏe'],
    wfh:['Làm online thứ 6 hàng tuần','Nhà có việc, xin làm từ xa','Chờ sửa nhà','Tiện chăm con nhỏ'],
    unpaid:['Việc gia đình dài ngày'],
  };
  const out = [];
  const pool = EMPLOYEES.slice(0, 30);
  // thai sản chỉ gán cho nữ (nhận diện qua đệm "Thị" hoặc tên nữ phổ biến)
  const isFemale = (e)=> /\bThị\b|Hồng|Quỳnh|Hương|Hằng|Nhung|Quyên|Thảo|Trang|Vân|Yến|Lan|Linh|Ngân|Mai|Diệu/.test(e.name);
  const femalePool = pool.filter(isFemale);
  for (let i=0;i<14;i++){
    const e = i<2 ? femalePool[i % femalePool.length] : pool[i % pool.length];
    const type = i<2?'maternity': pick(['annual','annual','sick','wfh','wfh','early','annual']);
    const d1 = 28 + Math.floor(rand()*8); // late may / early jun
    const fromM = d1>31?6:5; const fromD = d1>31?d1-31:d1;
    const days = type==='maternity'?'180': type==='wfh'?'1': type==='early'?'0.5': String(Math.floor(rand()*3)+1);
    let state;
    if (i<5) state='Chờ Leader';
    else if (i<7) state='Chờ HCNS';
    else if (i<12) state='Đã duyệt';
    else state='Từ chối';
    out.push({
      id:'LV'+String(i+1).padStart(3,'0'), emp:e, type,
      typeName: LEAVE_TYPES.find(t=>t.id===type).name,
      from:`2026-${String(fromM).padStart(2,'0')}-${String(fromD).padStart(2,'0')}`,
      days, reason: pick(reasons[type]), state,
      submitted:`2026-05-2${Math.floor(rand()*6)+1}`,
    });
  }
  return out;
}
const LEAVE_REQUESTS = genLeaveRequests();

function genLeaveBalance() {
  let rng = 24680;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  return EMPLOYEES.filter(e=>e.status==='Chính thức').slice(0,26).map(e=>{
    const year = 12;
    const carry = Math.floor(rand()*3);
    const total = year + carry;
    const used = Math.min(+(rand()*total).toFixed(1), total-0.5);
    return { emp:e, year, carry, used, remain:+(total-used).toFixed(1) };
  });
}
const LEAVE_BALANCE = genLeaveBalance();

/* ============================================================
   HỢP ĐỒNG LAO ĐỘNG
   ============================================================ */
const CONTRACT_TYPES = [
  { id:'trial', name:'HĐ thử việc 2 tháng',        short:'Thử việc', kind:'amber' },
  { id:'m6',    name:'HĐ lao động 6 tháng',         short:'6 tháng',  kind:'blue'  },
  { id:'m12',   name:'HĐ lao động 12 tháng',        short:'12 tháng', kind:'teal'  },
  { id:'perm',  name:'HĐ không xác định thời hạn',  short:'Vô thời hạn', kind:'green' },
];

function genContracts() {
  let rng = 13579;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const offline = EMPLOYEES.filter(e=>e.type==='Offline');
  const out = offline.map((e,i)=>{
    let typeId, signed, end, renewals;
    if (e.status==='Thử việc') {
      typeId='trial';
      signed = subMonths('2026-05-29', Math.floor(rand()*2)); // ký trong 0-1 tháng gần đây
      end = addMonths(signed, 2); renewals=0;
    } else {
      const r = rand();
      typeId = r<0.18?'perm': r<0.55?'m12':'m6';
      signed = e.start;
      const months = typeId==='perm'?null: typeId==='m12'?12:6;
      // current contract started after some renewals
      const startCur = subMonths('2026-05-29', Math.floor(rand()*8));
      end = typeId==='perm'? null : addMonths(startCur, months);
      renewals = typeId==='perm'?2: Math.floor(rand()*3)+1;
      signed = startCur;
    }
    // flag expiring within 45 days
    let daysLeft = null, expiring = false;
    if (end) { daysLeft = daysBetween('2026-05-29', end); expiring = daysLeft>=0 && daysLeft<=45; }
    return {
      id:'HD'+String(i+1).padStart(3,'0'), emp:e, typeId,
      typeName: CONTRACT_TYPES.find(t=>t.id===typeId).name,
      signed, end, renewals, daysLeft, expiring,
      bhxhBase: Math.min(Math.max(e.wage,5100000),7300000),
      state: e.status==='Thử việc'?'Thử việc':'Đang hiệu lực',
    };
  });
  return out;
}
function addMonths(s, m){ const d=new Date(s); d.setMonth(d.getMonth()+m); return d.toISOString().slice(0,10); }
function subMonths(s, m){ const d=new Date(s); d.setMonth(d.getMonth()-m); return d.toISOString().slice(0,10); }
function daysBetween(a,b){ return Math.round((new Date(b)-new Date(a))/86400000); }
const CONTRACTS = genContracts();

/* lịch sử lộ trình (salary versioning) cho 1 nhân viên mẫu */
function contractHistory(emp){
  const w = emp.wage;
  return [
    { date:'2024-03-01', type:'HĐ thử việc 2 tháng', job:emp.jobTitle, wage:Math.round(w*0.75), note:'Bắt đầu thử việc' },
    { date:'2024-05-01', type:'HĐ lao động 6 tháng', job:emp.jobTitle, wage:Math.round(w*0.85), note:'Ký chính thức' },
    { date:'2024-11-01', type:'HĐ lao động 12 tháng', job:emp.jobTitle, wage:Math.round(w*0.95), note:'Tái ký lần 1 · tăng lương' },
    { date:'2025-11-01', type:'HĐ lao động 12 tháng', job:emp.jobTitle, wage:w, note:'Tái ký lần 2 · điều chỉnh lương' },
  ];
}

/* ============================================================
   ĐÁNH GIÁ (APPRAISAL)
   ============================================================ */
const SKILLS = [
  { id:'pro',  name:'Chuyên môn' },
  { id:'comm', name:'Giao tiếp & tư vấn' },
  { id:'team', name:'Làm việc nhóm' },
  { id:'init', name:'Chủ động & trách nhiệm' },
  { id:'tool', name:'Sử dụng hệ thống' },
];
const APPRAISAL_PERIOD = 'Quý II/2026';

function genAppraisals() {
  let rng = 80808;
  const rand = () => { rng = (rng*1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  const pick = (a)=>a[Math.floor(rand()*a.length)];
  const goalBank = {
    tvts:['Đạt KPI doanh thu Quý II','Tăng tỉ lệ chốt lên 18%','Hoàn thành khóa kỹ năng tư vấn'],
    gv:['Hoàn thành bộ giáo án HSK4','Đạt điểm hài lòng học viên ≥ 4.5','Dự giờ & góp ý 5 buổi'],
    content:['Đạt 200k reach/tháng','Sản xuất 12 video/tháng','Tăng follow TikTok 15%'],
    default:['Hoàn thành đào tạo nội bộ','Cải tiến quy trình phòng ban','Nâng cấp 1 kỹ năng chuyên môn'],
  };
  const states = ['Chờ tự đánh giá','Chờ quản lý','Hoàn thành','Hoàn thành','Hoàn thành'];
  const pool = EMPLOYEES.filter(e=>e.status==='Chính thức').slice(0,18);
  return pool.map((e,i)=>{
    const state = i<3?'Chờ tự đánh giá': i<6?'Chờ quản lý':'Hoàn thành';
    const skills = {};
    SKILLS.forEach(s=>{ skills[s.id] = +(3 + rand()*2).toFixed(1); });
    const self = +(3.4 + rand()*1.4).toFixed(1);
    const mgr = +(3.2 + rand()*1.5).toFixed(1);
    const final = state==='Hoàn thành'? +((self+mgr)/2).toFixed(1) : null;
    const gb = goalBank[e.job] || goalBank.default;
    const goals = gb.slice(0,3).map((g,gi)=>({ text:g, progress: state==='Hoàn thành'? Math.floor(rand()*40)+60 : Math.floor(rand()*70)+10 }));
    return {
      id:'AP-'+e.code, emp:e, period:APPRAISAL_PERIOD, state,
      manager: DEPARTMENTS.find(d=>d.id===e.dep).leader,
      self, mgr, final, skills, goals,
    };
  });
}
const APPRAISALS = genAppraisals();

/* ============================================================
   NHẬP VIỆC (ONBOARDING) — quy trình đặc thù Học Bá
   Mốc 1: Hội nhập (ngày 1 → tuần 2)
   Mốc 2: Đánh giá 2 tuần → đạt thì cấp thiết bị
   Mốc 3: Xét lên chính thức sau 2 tháng
   ============================================================ */
const ONB_TASKS = [
  { id:'welcome', label:'Đón nhận ngày đầu & giới thiệu đội nhóm' },
  { id:'culture', label:'Đào tạo văn hóa công ty' },
  { id:'docs',    label:'Gửi tài liệu hội nhập (nội quy, handbook, quy trình)' },
  { id:'account', label:'Khởi tạo email & tài khoản hệ thống' },
  { id:'handover',label:'Bàn giao cho Quản lý đào tạo chuyên môn' },
];
const ONB_EQUIP = [
  { id:'laptop', label:'Cấp máy tính' },
  { id:'basics', label:'Cấp vật dụng cơ bản (bàn phím, chuột, tai nghe)' },
];
const ONB_PHASES = [
  { id:'intro',    name:'Hội nhập',           sub:'Ngày 1 → tuần 2',  color:'#1D4ED8' },
  { id:'eval2w',   name:'Đánh giá 2 tuần',    sub:'Gate cấp thiết bị', color:'#D9A400' },
  { id:'training', name:'Đào tạo chuyên môn', sub:'Tuần 2 → 2 tháng',  color:'#0F766E' },
  { id:'eval2m',   name:'Xét chính thức',     sub:'Sau 2 tháng',       color:'#15803D' },
];

function genOnboarding() {
  const today = new Date('2026-05-29');
  const mk = (daysAgo) => { const d=new Date(today); d.setDate(d.getDate()-daysAgo); return d.toISOString().slice(0,10); };
  const tv = EMPLOYEES.filter(e=>e.status==='Thử việc');
  // chọn 7 người với số ngày khác nhau để rải đều các mốc
  const setup = [
    { daysAgo:2  }, { daysAgo:6 }, { daysAgo:11 },
    { daysAgo:14 }, { daysAgo:27 }, { daysAgo:46 }, { daysAgo:61 },
  ];
  return setup.map((s,i)=>{
    const emp = tv[i % tv.length];
    const dayN = s.daysAgo;
    let phase, tasks={}, eval2w='pending', equip={}, eval2m='pending';
    ONB_TASKS.forEach(t=>tasks[t.id]=false);
    ONB_EQUIP.forEach(t=>equip[t.id]=false);
    if (dayN < 14) {
      phase='intro';
      // hoàn thành dần theo ngày
      const done = Math.min(ONB_TASKS.length, Math.floor(dayN/3)+1);
      ONB_TASKS.slice(0,done).forEach(t=>tasks[t.id]=true);
    } else if (dayN === 14) {
      phase='eval2w'; ONB_TASKS.forEach(t=>tasks[t.id]=true);
    } else if (dayN < 60) {
      phase='training'; ONB_TASKS.forEach(t=>tasks[t.id]=true);
      eval2w='pass'; ONB_EQUIP.forEach(t=>equip[t.id]=true);
    } else {
      phase='eval2m'; ONB_TASKS.forEach(t=>tasks[t.id]=true);
      eval2w='pass'; ONB_EQUIP.forEach(t=>equip[t.id]=true);
    }
    return {
      id:'ONB-'+emp.code, emp, startDate:mk(dayN), dayN, phase,
      tasks, eval2w, equip, eval2m,
      mentor: DEPARTMENTS.find(d=>d.id===emp.dep).leader,
      buddy: EMPLOYEES.find(x=>x.dep===emp.dep && x.status==='Chính thức' && x.id!==emp.id)?.name || '—',
    };
  });
}
const ONBOARDING = genOnboarding();

/* ============================================================
   HỒ SƠ CỦA TÔI (self-service) — dữ liệu thật từ file Lark
   Người đăng nhập: Hoàng Thị Ngọc Anh (HB.75)
   ============================================================ */
const MY_PROFILE = {
  code:'HB.75', name:'Hoàng Thị Ngọc Anh', initials:'NA', avatar:'av-f',
  lark:'Hoàng Thị Ngọc Anh',
  type:'Offline', status:'Chính thức',
  jobTitle:'Nhân viên hành chính nhân sự', jobGroup:'Hành chính nhân sự', posType:'Nhân viên',
  depName:'Phòng Nhân sự', depShort:'NS',
  trialDate:'2025-07-25', officialDate:'2025-09-24', tenureMonths:'8.2',
  gender:'Nữ', birth:'2002-06-08', age:24,
  birthplace:'Đại Đình, Tam Đảo, Vĩnh Phúc', nationality:'Việt Nam',
  cccd:'026302003949', cccdDate:'2021-08-12', cccdPlace:'Cục cảnh sát QLHC về TTXH',
  phone:'0356960580', emailPersonal:'anhhoangtdvp@gmail.com', emailCompany:null,
  addrPermanent:'Đại Đình, Tam Đảo, Vĩnh Phúc',
  addrCurrent:'234 Trường Chinh, Khương Thượng, Đống Đa, Hà Nội',
  marital:null, education:'Tốt nghiệp Đại học Kinh tế Quốc dân',
  family:null, emergencyName:null, emergencyPhone:'0977659939',
  bank:'Techcombank', acct:'1608062002',
  contract:'HĐ lao động 12 tháng', contractSchedule:'Đã ký',
  chineseStudy:null, chineseLevel:null,
  equipment:['Màn hình','Cây máy tính (CPU)','Bàn phím','Chuột','Lót bàn phím','Ghế làm việc','Bàn làm việc','Máy in'],
  // self-service nhanh
  netSalary:8_650_000, salaryPeriod:'05/2026',
  leaveYear:12, leaveUsed:3.5, leaveRemain:8.5,
  workDays:21, standardDays:22, lateThisMonth:1,
};

Object.assign(window, {
  DEPARTMENTS, EMPLOYEES, JOBS, KPI_LEVELS, ATTENDANCE, FORGOT_REQUESTS, OT_LOG,
  REC_STAGES, REC_POSITIONS, APPLICANTS, PAYROLL, STATS,
  LEAVE_TYPES, LEAVE_STATES, LEAVE_REQUESTS, LEAVE_BALANCE,
  CONTRACT_TYPES, CONTRACTS, contractHistory, addMonths, daysBetween,
  SKILLS, APPRAISAL_PERIOD, APPRAISALS,
  ONB_TASKS, ONB_EQUIP, ONB_PHASES, ONBOARDING,
  MY_PROFILE,
  fmtVND, fmtM, initials, avClass, removeAccents,
});
