/* ============================================================
   HOC BA HRM — Dashboard
   ============================================================ */

function Dashboard({ setView }) {
  const present = STATS.presentToday;
  const presentPct = Math.round(present / STATS.offline * 100);

  const statCards = [
    { ico:'users', col:'var(--red-600)', bg:'var(--red-50)', val:STATS.total, lbl:'Tổng nhân sự', trend:'+5 so với T4', up:true },
    { ico:'checkCircle', col:'var(--green)', bg:'var(--green-bg)', val:STATS.ct, lbl:'Chính thức', sub:`${STATS.tv} đang thử việc` },
    { ico:'clock', col:'var(--blue)', bg:'var(--blue-bg)', val:present+'/'+STATS.offline, lbl:'Có mặt hôm nay', sub:`${STATS.lateToday} đi trễ · ${STATS.remoteToday} online` },
    { ico:'briefcase', col:'var(--violet)', bg:'var(--violet-bg)', val:STATS.openPositions, lbl:'Vị trí đang tuyển', sub:`${STATS.applicants} ứng viên` },
  ];

  const maxDep = Math.max(...DEPARTMENTS.map(d=>d.total));

  // sinh nhật & việc cần làm
  const tasks = [
    { ico:'checkCircle', col:'var(--amber)', bg:'var(--amber-bg)', t:'5 đơn quên chấm công chờ duyệt', s:'Hạn duyệt trước 12h hôm nay', act:()=>setView('attendance') },
    { ico:'calendar', col:'var(--violet)', bg:'var(--violet-bg)', t:'7 đơn xin nghỉ phép & làm online', s:'2 đơn cần HCNS xác nhận', act:()=>setView('timeoff') },
    { ico:'file', col:'var(--red-600)', bg:'var(--red-50)', t:'4 hợp đồng sắp hết hạn', s:'Trong vòng 45 ngày tới · cần tái ký', act:()=>setView('contracts') },
    { ico:'wallet', col:'var(--green)', bg:'var(--green-bg)', t:'Bảng lương T5/2026 đang chờ chốt', s:'40/53 payslip đã duyệt', act:()=>setView('payroll') },
  ];

  const recent = [
    { e:EMPLOYEES[2], a:'check-in lúc 08:12', tag:'Chấm công', c:'green', time:'2 phút trước' },
    { e:EMPLOYEES[14], a:'gửi đơn xin nghỉ phép năm', tag:'Nghỉ phép', c:'violet', time:'18 phút trước' },
    { e:EMPLOYEES[7], a:'được duyệt offer — nhận việc 01/06', tag:'Tuyển dụng', c:'blue', time:'1 giờ trước' },
    { e:EMPLOYEES[21], a:'cập nhật tài khoản ngân hàng', tag:'Hồ sơ', c:'gray', time:'3 giờ trước' },
    { e:EMPLOYEES[5], a:'đăng ký làm online thứ 6', tag:'Làm online', c:'blue', time:'Hôm qua' },
  ];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Xin chào, chị Ngọc Anh 👋</h1>
          <p>Tổng quan nhân sự Học Bá Education · Thứ Sáu, 29/05/2026</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Xuất báo cáo</button>
          <button className="btn btn-primary" onClick={()=>setView('employees')}><Icon name="plus" size={16}/>Thêm nhân viên</button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="stat-grid">
        {statCards.map((s,i)=>(
          <div className="stat" key={i}>
            <div className="stat-ico" style={{background:s.bg,color:s.col}}><Icon name={s.ico} size={22}/></div>
            <div className="stat-val">{s.val}</div>
            <div className="stat-lbl">{s.lbl}</div>
            {s.trend && <div className={'stat-trend '+(s.up?'trend-up':'trend-down')}><Icon name="arrowUp" size={13}/>{s.trend}</div>}
            {s.sub && <div className="stat-trend muted" style={{color:'var(--muted)'}}>{s.sub}</div>}
          </div>
        ))}
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1.55fr 1fr',gap:16,marginBottom:16}}>
        {/* Phòng ban */}
        <div className="card">
          <div className="card-head">
            <h3>Cơ cấu phòng ban</h3>
            <span className="badge badge-gray">6 phòng ban</span>
            <div className="actions"><button className="btn btn-ghost btn-sm" onClick={()=>setView('employees')}>Xem tất cả<Icon name="chevR" size={14}/></button></div>
          </div>
          <div className="card-pad" style={{display:'flex',flexDirection:'column',gap:15}}>
            {DEPARTMENTS.map(d=>(
              <div key={d.id} style={{display:'flex',alignItems:'center',gap:14}}>
                <div style={{width:40,height:40,borderRadius:11,background:d.color+'1a',color:d.color,display:'grid',placeItems:'center',fontWeight:800,fontSize:13,flexShrink:0}}>{d.short}</div>
                <div style={{flex:1,minWidth:0}}>
                  <div className="between" style={{marginBottom:6}}>
                    <div>
                      <span style={{fontWeight:700,fontSize:13.5}}>{d.name}</span>
                      <span className="muted" style={{fontSize:12,marginLeft:8}}>TBP: {d.leader}</span>
                    </div>
                    <div style={{fontSize:13,fontWeight:700}}>{d.total} <span className="faint" style={{fontWeight:500,fontSize:11.5}}>người</span></div>
                  </div>
                  <div className="bar"><span style={{width:(d.total/maxDep*100)+'%',background:d.color}}></span></div>
                  <div style={{display:'flex',gap:12,marginTop:6,fontSize:11.5}}>
                    <span className="muted">Chính thức: <b style={{color:'var(--green)'}}>{d.ct}</b></span>
                    <span className="muted">Thử việc: <b style={{color:'var(--amber)'}}>{d.tv}</b></span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Việc cần làm */}
        <div className="card">
          <div className="card-head">
            <h3>Việc cần xử lý</h3>
            <span className="badge badge-red" style={{marginLeft:'auto'}}><span className="bdot"></span>4 mục</span>
          </div>
          <div style={{padding:'8px 10px'}}>
            {tasks.map((t,i)=>(
              <button key={i} onClick={t.act} style={{display:'flex',gap:12,padding:'12px 10px',width:'100%',textAlign:'left',borderRadius:11,alignItems:'flex-start',transition:'background .12s',cursor:t.act?'pointer':'default'}}
                onMouseEnter={e=>e.currentTarget.style.background='var(--surface-2)'}
                onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                <div style={{width:36,height:36,borderRadius:10,background:t.bg,color:t.col,display:'grid',placeItems:'center',flexShrink:0}}><Icon name={t.ico} size={18}/></div>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,lineHeight:1.35}}>{t.t}</div>
                  <div className="muted" style={{fontSize:11.5,marginTop:2}}>{t.s}</div>
                </div>
                {t.act && <Icon name="chevR" size={16} className="faint" />}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1.55fr',gap:16}}>
        {/* Phân loại hình thức */}
        <div className="card">
          <div className="card-head"><h3>Hình thức làm việc</h3></div>
          <div className="card-pad">
            <Donut data={[
              {label:'Offline (VP)', val:STATS.offline, color:'#C8102E'},
              {label:'Online / Remote', val:STATS.online, color:'#1D4ED8'},
              {label:'CTV theo đầu việc', val:STATS.ctv, color:'#D9A400'},
            ]} total={STATS.total}/>
          </div>
        </div>

        {/* Hoạt động gần đây */}
        <div className="card">
          <div className="card-head">
            <h3>Hoạt động gần đây</h3>
            <div className="actions"><span className="badge badge-green"><span className="bdot"></span>Trực tiếp</span></div>
          </div>
          <div style={{padding:'6px 8px'}}>
            {recent.map((r,i)=>(
              <div key={i} style={{display:'flex',gap:12,padding:'11px 12px',alignItems:'center'}}>
                <Avatar emp={r.e} size={36}/>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,lineHeight:1.4}}><b>{r.e.name}</b> <span className="muted">{r.a}</span></div>
                  <div style={{fontSize:11,color:'var(--faint)',marginTop:1}}>{r.time}</div>
                </div>
                <Badge kind={r.c}>{r.tag}</Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* Donut chart (pure SVG arcs) */
function Donut({ data, total }) {
  const sum = data.reduce((s,d)=>s+d.val,0);
  let acc = 0;
  const R = 58, C = 2*Math.PI*R;
  return (
    <div style={{display:'flex',alignItems:'center',gap:22}}>
      <svg width="150" height="150" viewBox="0 0 150 150" style={{flexShrink:0}}>
        <circle cx="75" cy="75" r={R} fill="none" stroke="#EEEAE4" strokeWidth="16"/>
        {data.map((d,i)=>{
          const frac = d.val/sum;
          const dash = frac*C;
          const el = <circle key={i} cx="75" cy="75" r={R} fill="none" stroke={d.color} strokeWidth="16"
            strokeDasharray={`${dash} ${C-dash}`} strokeDashoffset={-acc*C} transform="rotate(-90 75 75)" strokeLinecap="butt"/>;
          acc += frac; return el;
        })}
        <text x="75" y="71" textAnchor="middle" fontSize="30" fontWeight="800" fill="var(--ink)">{total}</text>
        <text x="75" y="90" textAnchor="middle" fontSize="11" fill="var(--muted)" fontWeight="600">nhân sự</text>
      </svg>
      <div style={{flex:1,display:'flex',flexDirection:'column',gap:12}}>
        {data.map((d,i)=>(
          <div key={i} style={{display:'flex',alignItems:'center',gap:10}}>
            <span style={{width:11,height:11,borderRadius:3,background:d.color,flexShrink:0}}></span>
            <span style={{fontSize:12.5,fontWeight:500,flex:1}}>{d.label}</span>
            <span style={{fontSize:13.5,fontWeight:700}}>{d.val}</span>
            <span className="faint" style={{fontSize:11.5,width:34,textAlign:'right'}}>{Math.round(d.val/sum*100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { Dashboard, Donut });
