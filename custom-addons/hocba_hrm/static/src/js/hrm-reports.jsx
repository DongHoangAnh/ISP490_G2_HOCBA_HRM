/* ============================================================
   HOC BA HRM — Báo cáo nhân sự (Analytics)
   ============================================================ */

function Reports() {
  // payroll theo phòng ban
  const payByDep = DEPARTMENTS.map(d=>({
    label:d.short, color:d.color,
    val: PAYROLL.filter(p=>p.dep===d.id).reduce((s,p)=>s+p.net,0),
  }));
  const maxPay = Math.max(...payByDep.map(d=>d.val));

  // headcount theo phòng ban (CT vs TV stacked)
  const head = DEPARTMENTS.map(d=>({ ...d }));

  // biến động nhân sự 6 tháng
  const trend = [
    { m:'T12', hire:3, leave:2 }, { m:'T1', hire:5, leave:1 }, { m:'T2', hire:2, leave:3 },
    { m:'T3', hire:6, leave:2 }, { m:'T4', hire:4, leave:1 }, { m:'T5', hire:5, leave:2 },
  ];
  const maxTrend = Math.max(...trend.flatMap(t=>[t.hire,t.leave]));

  const attToday = {
    ok: ATTENDANCE.filter(a=>a.status==='Đúng giờ').length,
    late: ATTENDANCE.filter(a=>a.status==='Đi trễ').length,
    remote: ATTENDANCE.filter(a=>a.status==='Làm online').length,
    leave: ATTENDANCE.filter(a=>a.status==='Nghỉ phép').length,
  };
  const totalNet = PAYROLL.reduce((s,p)=>s+p.net,0);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Báo cáo nhân sự</h1>
          <p>Dashboard thời gian thực · tháng 5/2026 · dữ liệu liên thông từ các module</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="calendar" size={16}/>Tháng 05/2026</button>
          <button className="btn btn-primary"><Icon name="download" size={16}/>Xuất Excel / PDF</button>
        </div>
      </div>

      {/* KPI row */}
      <div className="stat-grid">
        <MetricCard ico="users" col="var(--red-600)" bg="var(--red-50)" val={STATS.total} lbl="Tổng nhân sự"/>
        <MetricCard ico="trend" col="var(--green)" bg="var(--green-bg)" val="+5" lbl="Tuyển mới T5"/>
        <MetricCard ico="logout" col="var(--amber)" bg="var(--amber-bg)" val="2" lbl="Nghỉ việc T5"/>
        <MetricCard ico="coins" col="var(--gold-600)" bg="var(--gold-50)" val={fmtM(totalNet)} lbl="Quỹ lương thực chi"/>
      </div>

      <div className="grid-2" style={{marginBottom:16}}>
        {/* Headcount theo phòng ban */}
        <div className="card">
          <div className="card-head"><h3>Cơ cấu nhân sự theo phòng ban</h3><span className="muted" style={{fontSize:12,marginLeft:'auto'}}>Chính thức · Thử việc</span></div>
          <div className="card-pad" style={{display:'flex',flexDirection:'column',gap:14}}>
            {head.map(d=>{
              const max = Math.max(...head.map(x=>x.total));
              return (
                <div key={d.id} style={{display:'flex',alignItems:'center',gap:12}}>
                  <span style={{width:40,fontSize:12,fontWeight:700,color:d.color,flexShrink:0}}>{d.short}</span>
                  <div style={{flex:1,display:'flex',height:24,borderRadius:7,overflow:'hidden',background:'#EEEAE4'}}>
                    <div style={{width:(d.ct/max*100)+'%',background:d.color,display:'flex',alignItems:'center',paddingLeft:7,color:'#fff',fontSize:11,fontWeight:700}}>{d.ct}</div>
                    <div style={{width:(d.tv/max*100)+'%',background:d.color+'66',display:'flex',alignItems:'center',paddingLeft:6,color:'#fff',fontSize:11,fontWeight:700}}>{d.tv||''}</div>
                  </div>
                  <span style={{width:28,textAlign:'right',fontWeight:700,fontSize:13}}>{d.total}</span>
                </div>
              );
            })}
            <div style={{display:'flex',gap:18,marginTop:4,fontSize:11.5}}>
              <span style={{display:'inline-flex',alignItems:'center',gap:6}}><span style={{width:11,height:11,borderRadius:3,background:'var(--red-600)'}}></span>Chính thức (30)</span>
              <span style={{display:'inline-flex',alignItems:'center',gap:6}}><span style={{width:11,height:11,borderRadius:3,background:'#C8102E66'}}></span>Thử việc (23)</span>
            </div>
          </div>
        </div>

        {/* Quỹ lương theo phòng ban */}
        <div className="card">
          <div className="card-head"><h3>Quỹ lương thực chi theo phòng ban</h3></div>
          <div className="card-pad" style={{display:'flex',flexDirection:'column',gap:13}}>
            {payByDep.map(d=>(
              <div key={d.label} style={{display:'flex',alignItems:'center',gap:12}}>
                <span style={{width:40,fontSize:12,fontWeight:700,color:d.color,flexShrink:0}}>{d.label}</span>
                <div className="bar" style={{flex:1,height:14}}><span style={{width:(d.val/maxPay*100)+'%',background:d.color}}></span></div>
                <span className="mono" style={{width:64,textAlign:'right',fontWeight:700,fontSize:12.5}}>{fmtM(d.val)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Biến động nhân sự */}
        <div className="card">
          <div className="card-head"><h3>Biến động nhân sự 6 tháng</h3></div>
          <div className="card-pad">
            <div style={{display:'flex',alignItems:'flex-end',gap:18,height:180,padding:'8px 4px 0'}}>
              {trend.map(t=>(
                <div key={t.m} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',gap:7,height:'100%',justifyContent:'flex-end'}}>
                  <div style={{display:'flex',gap:5,alignItems:'flex-end',height:'100%',width:'100%',justifyContent:'center'}}>
                    <div title={'Tuyển: '+t.hire} style={{width:14,height:(t.hire/maxTrend*100)+'%',background:'var(--green)',borderRadius:'4px 4px 0 0',transition:'height .3s'}}></div>
                    <div title={'Nghỉ: '+t.leave} style={{width:14,height:(t.leave/maxTrend*100)+'%',background:'var(--red-500)',borderRadius:'4px 4px 0 0',transition:'height .3s'}}></div>
                  </div>
                  <span className="muted" style={{fontSize:11,fontWeight:600}}>{t.m}</span>
                </div>
              ))}
            </div>
            <div style={{display:'flex',gap:18,marginTop:10,fontSize:11.5,justifyContent:'center'}}>
              <span style={{display:'inline-flex',alignItems:'center',gap:6}}><span style={{width:11,height:11,borderRadius:3,background:'var(--green)'}}></span>Tuyển mới</span>
              <span style={{display:'inline-flex',alignItems:'center',gap:6}}><span style={{width:11,height:11,borderRadius:3,background:'var(--red-500)'}}></span>Nghỉ việc</span>
            </div>
          </div>
        </div>

        {/* Tổng hợp chấm công hôm nay */}
        <div className="card">
          <div className="card-head"><h3>Tổng hợp chấm công hôm nay</h3><span className="badge badge-green" style={{marginLeft:'auto'}}><span className="bdot"></span>Trực tiếp</span></div>
          <div className="card-pad">
            <Donut total={ATTENDANCE.length} data={[
              {label:'Đúng giờ', val:attToday.ok, color:'#15803D'},
              {label:'Đi trễ', val:attToday.late, color:'#D9A400'},
              {label:'Làm online', val:attToday.remote, color:'#1D4ED8'},
              {label:'Nghỉ phép', val:attToday.leave||1, color:'#6D28D9'},
            ]}/>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Reports });
