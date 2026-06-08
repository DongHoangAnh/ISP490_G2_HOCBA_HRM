/* ============================================================
   HOC BA HRM — Lộ trình thăng tiến (Salary versioning)
   Dựa trên Sheet 2.4: snapshot lương + chức danh theo tháng.
   Mỗi lần đổi lương/chức danh = 1 mốc.
   ============================================================ */

// các khoản lương theo đúng tên cột file Lark
function salaryComponents(emp, factor, withAllow) {
  const offline = emp.type==='Offline';
  const leader = emp.isLeader;
  return {
    'Lương cơ bản':       Math.round(emp.wage*factor/1e5)*1e5,
    'PC xăng xe':         withAllow && offline ? 500000 : 0,
    'PC gửi xe':          withAllow && offline ? 100000 : 0,
    'PC chức vụ':         withAllow && leader ? 2000000 : 0,
    'PC thâm niên':       withAllow && factor>=1 ? 500000 : (withAllow?300000:0),
    'Hỗ trợ điện thoại':  withAllow && (leader||emp.job==='tvts') ? 300000 : 0,
    'Hỗ trợ ăn ca':       withAllow && offline ? 700000 : 0,
    'Hỗ trợ trang phục':  withAllow && offline ? 400000 : 0,
    'Hỗ trợ đi lại':      withAllow && !offline ? 200000 : 0,
    'Lương KPI':          withAllow && emp.job==='tvts' ? Math.round(emp.wage*factor*0.4/1e5)*1e5 : 0,
  };
}
function compTotal(c){ return Object.values(c).reduce((a,b)=>a+b,0); }

function genSalaryPath(emp) {
  const startY = +emp.start.slice(0,4);
  const startM = +emp.start.slice(5,7);
  const mk = (y,m)=>`${y}-${String(m).padStart(2,'0')}-01`;
  const path = [];
  // Mốc 1: thử việc
  path.push({ date: emp.start, title: emp.jobTitle, status:'Thử việc',
    comp: salaryComponents(emp, 0.8, false), note:'Bắt đầu thử việc (lương 80%)' });

  if (emp.status==='Thử việc') {
    return path.map(p=>({...p, total:compTotal(p.comp)}));
  }

  // Mốc 2: lên chính thức (+2 tháng)
  let y=startY, m=startM+2; if(m>12){m-=12;y++;}
  path.push({ date: mk(y,m), title: emp.jobTitle, status:'Chính thức',
    comp: salaryComponents(emp, 0.9, true), note:'Ký HĐ chính thức · hưởng đủ phụ cấp' });

  // Mốc 3: tăng lương sau ~8 tháng
  m+=8; while(m>12){m-=12;y++;}
  if (y < 2026 || (y===2026 && m<=4)) {
    path.push({ date: mk(y,m), title: emp.jobTitle, status:'Chính thức',
      comp: salaryComponents(emp, 0.96, true), note:'Điều chỉnh lương theo kết quả' });
  }

  // Mốc 4: hiện tại (mức wage hiện tại) — có thể kèm thăng chức
  const promoted = emp.isLeader;
  path.push({ date:'2026-05-01', title: emp.jobTitle, status:'Chính thức',
    comp: salaryComponents(emp, 1, true),
    note: promoted ? 'Bổ nhiệm vị trí quản lý · mức hiện tại' : 'Mức lương hiện tại (T5/2026)' });

  return path.map(p=>({...p, total:compTotal(p.comp)}));
}

function SalaryJourney({ emp }) {
  const path = genSalaryPath(emp);
  const [openIdx, setOpenIdx] = useState(path.length-1);
  const totals = path.map(p=>p.total);
  const maxT = Math.max(...totals), minT = Math.min(...totals);
  const growth = totals[totals.length-1] - totals[0];
  const growthPct = Math.round(growth/totals[0]*100);

  // chart geometry
  const W=560, Hh=150, padX=20, padY=22;
  const n=path.length;
  const x=(i)=> n<=1?W/2: padX + i*(W-2*padX)/(n-1);
  const y=(v)=> padY + (Hh-2*padY) * (1 - (v-minT)/((maxT-minT)||1));
  const line = path.map((p,i)=>`${i===0?'M':'L'}${x(i).toFixed(1)},${y(p.total).toFixed(1)}`).join(' ');
  const area = `${line} L${x(n-1).toFixed(1)},${Hh-padY+8} L${x(0).toFixed(1)},${Hh-padY+8} Z`;

  return (
    <div>
      {/* summary */}
      <div className="grid-3" style={{marginBottom:16}}>
        <MiniStat lbl="Thu nhập khởi điểm" val={fmtVND(totals[0])+' ₫'} col="var(--muted)"/>
        <MiniStat lbl="Thu nhập hiện tại" val={fmtVND(totals[totals.length-1])+' ₫'} col="var(--green)"/>
        <MiniStat lbl="Tăng trưởng" val={'+'+growthPct+'%'} col="var(--gold-600)"/>
      </div>

      {/* chart */}
      <div className="card" style={{padding:'16px 18px',marginBottom:16}}>
        <div className="between" style={{marginBottom:6}}>
          <span style={{fontWeight:700,fontSize:13}}>Biểu đồ tổng thu nhập theo mốc</span>
          <span className="badge badge-gold">{n} mốc thay đổi</span>
        </div>
        <svg width="100%" viewBox={`0 0 ${W} ${Hh}`} style={{display:'block'}}>
          <defs>
            <linearGradient id="sjgrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--red-600)" stopOpacity="0.18"/>
              <stop offset="100%" stopColor="var(--red-600)" stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d={area} fill="url(#sjgrad)"/>
          <path d={line} fill="none" stroke="var(--red-600)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round"/>
          {path.map((p,i)=>(
            <g key={i} onClick={()=>setOpenIdx(i)} style={{cursor:'pointer'}}>
              <circle cx={x(i)} cy={y(p.total)} r={openIdx===i?6:4.5} fill="#fff" stroke="var(--red-600)" strokeWidth="2.5"/>
              <text x={x(i)} y={Hh-6} textAnchor="middle" fontSize="10.5" fill="var(--muted)" fontWeight="600">{fmtDateShort(p.date)}</text>
              <text x={x(i)} y={y(p.total)-12} textAnchor="middle" fontSize="10.5" fill="var(--ink)" fontWeight="700">{(p.total/1e6).toFixed(1)}tr</text>
            </g>
          ))}
        </svg>
      </div>

      {/* timeline */}
      <div style={{position:'relative',paddingLeft:8}}>
        {path.map((p,i)=>{
          const open=openIdx===i; const last=i===path.length-1;
          const prev = i>0 ? path[i-1].total : null;
          const delta = prev!=null ? p.total-prev : 0;
          return (
            <div key={i} style={{display:'flex',gap:16,paddingBottom:last?0:18,position:'relative'}}>
              <div style={{display:'flex',flexDirection:'column',alignItems:'center'}}>
                <div style={{width:14,height:14,borderRadius:'50%',background:last?'var(--red-600)':'var(--gold-500)',border:'3px solid #fff',boxShadow:'0 0 0 2px '+(last?'var(--red-100)':'var(--gold-200)'),zIndex:1}}></div>
                {!last && <div style={{width:2,flex:1,background:'var(--border-strong)',marginTop:2}}></div>}
              </div>
              <div style={{flex:1}}>
                <button onClick={()=>setOpenIdx(open?-1:i)} style={{width:'100%',textAlign:'left',background:'none',padding:0}}>
                  <div className="between">
                    <div style={{display:'flex',alignItems:'center',gap:9,flexWrap:'wrap'}}>
                      <span style={{fontWeight:700,fontSize:13.5}}>{p.title}</span>
                      <Badge kind={p.status==='Thử việc'?'amber':'green'}>{p.status}</Badge>
                      {delta>0 && <span className="badge badge-gold"><Icon name="arrowUp" size={11}/>+{fmtVND(delta)}</span>}
                    </div>
                    <span className="mono muted" style={{fontSize:12.5}}>{fmtDate(p.date)}</span>
                  </div>
                  <div style={{display:'flex',gap:12,alignItems:'center',marginTop:5}}>
                    <span className="mono" style={{fontWeight:800,fontSize:14,color:'var(--green)'}}>{fmtVND(p.total)} ₫</span>
                    <span className="faint" style={{fontSize:12}}>{p.note}</span>
                    <Icon name={open?'chevD':'chevR'} size={15} className="faint" style={{marginLeft:'auto'}}/>
                  </div>
                </button>
                {open && (
                  <div style={{marginTop:11,padding:'12px 14px',background:'var(--surface-2)',border:'1px solid var(--border)',borderRadius:11}}>
                    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'7px 18px'}}>
                      {Object.entries(p.comp).filter(([_,v])=>v>0).map(([k,v])=>(
                        <div key={k} style={{display:'flex',justifyContent:'space-between',fontSize:12.5}}>
                          <span className="muted">{k}</span>
                          <span className="mono" style={{fontWeight:600}}>{fmtVND(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function fmtDateShort(s){ const [y,m]=s.split('-'); return `T${+m}/${y.slice(2)}`; }

Object.assign(window, { SalaryJourney, genSalaryPath, salaryComponents });
