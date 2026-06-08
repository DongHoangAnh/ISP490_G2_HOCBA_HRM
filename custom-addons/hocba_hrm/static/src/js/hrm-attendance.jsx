/* ============================================================
   HOC BA HRM — Chấm công (Attendance / OT / Quên chấm công)
   ============================================================ */

function Attendance({ search }) {
  const [tab, setTab] = useState('today');
  const [forgot, setForgot] = useState(FORGOT_REQUESTS.map(f=>({...f})));

  const approve = (id, ok) => setForgot(fs=>fs.map(f=>f.id===id?{...f,state:ok?'Đã duyệt':'Từ chối'}:f));

  const counts = {
    ok: ATTENDANCE.filter(a=>a.status==='Đúng giờ').length,
    late: ATTENDANCE.filter(a=>a.status==='Đi trễ').length,
    remote: ATTENDANCE.filter(a=>a.status==='Làm online').length,
    leave: ATTENDANCE.filter(a=>a.status==='Nghỉ phép').length,
    miss: ATTENDANCE.filter(a=>a.status==='Chưa chấm').length,
  };
  const pending = forgot.filter(f=>f.state==='Chờ duyệt').length;

  const att = ATTENDANCE.filter(a=> !search || a.name.toLowerCase().includes(search.toLowerCase()) || a.code.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Chấm công</h1>
          <p>Ca làm việc 08:00 – 19:00 · check-in 08:00 – 09:30 · đồng bộ từ Lark → Odoo</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="calendar" size={16}/>Thứ Sáu, 29/05/2026</button>
          <button className="btn btn-primary"><Icon name="download" size={16}/>Xuất bảng công</button>
        </div>
      </div>

      <div className="stat-grid" style={{gridTemplateColumns:'repeat(5,1fr)'}}>
        <MetricCard ico="checkCircle" col="var(--green)" bg="var(--green-bg)" val={counts.ok} lbl="Đúng giờ"/>
        <MetricCard ico="clock" col="var(--amber)" bg="var(--amber-bg)" val={counts.late} lbl="Đi trễ"/>
        <MetricCard ico="home" col="var(--blue)" bg="var(--blue-bg)" val={counts.remote} lbl="Làm online"/>
        <MetricCard ico="calendar" col="var(--violet)" bg="var(--violet-bg)" val={counts.leave} lbl="Nghỉ phép"/>
        <MetricCard ico="x" col="var(--red-600)" bg="var(--red-50)" val={counts.miss} lbl="Chưa chấm"/>
      </div>

      <div className="tabs">
        {[['today','Chấm công hôm nay'],['forgot',`Đơn quên chấm công ${pending?`(${pending})`:''}`],['ot','Tăng ca (OT)']].map(([id,l])=>(
          <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}</button>
        ))}
      </div>

      {tab==='today' && (
        <div className="card">
          <div className="card-head">
            <h3>Bảng chấm công · {att.length} nhân sự offline</h3>
            <div className="actions"><span className="badge badge-green"><span className="bdot"></span>Đang đồng bộ Lark</span></div>
          </div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Nhân viên</th><th>Phòng ban</th><th>Check-in</th><th>Check-out</th><th>Loại</th><th className="tbl-num">Đi trễ</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {att.map(a=>(
                  <tr key={a.id} style={{cursor:'default'}}>
                    <td><EmpCell emp={a}/></td>
                    <td className="muted">{a.depName}</td>
                    <td className="mono" style={{fontWeight:600}}>{a.checkIn}</td>
                    <td className="mono" style={{fontWeight:600}}>{a.checkOut}</td>
                    <td>{a.attType==='—'?<span className="faint">—</span>:<span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}}><Icon name={a.attType==='Onsite'?'pin':'home'} size={14} className="faint"/>{a.attType==='Onsite'?'Tại VP':'Từ xa'}</span>}</td>
                    <td className="tbl-num mono">{a.late>0?<span style={{color:'var(--amber)',fontWeight:600}}>+{a.late}'</span>:<span className="faint">—</span>}</td>
                    <td><Badge kind={statusBadge(a.status)} dot>{a.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab==='forgot' && (
        <div className="card">
          <div className="card-head">
            <h3>Đơn quên chấm công</h3>
            <span className="muted" style={{fontSize:12.5}}>Leader duyệt trước 12h ngày T+1</span>
            <div className="actions"><span className="badge badge-amber"><span className="bdot"></span>{pending} chờ duyệt</span></div>
          </div>
          <div style={{padding:'8px 10px'}}>
            {forgot.map(f=>(
              <div key={f.id} style={{display:'flex',alignItems:'center',gap:14,padding:'14px 12px',borderBottom:'1px solid var(--border)'}}>
                <Avatar emp={f} size={42}/>
                <div style={{minWidth:200}}>
                  <div style={{fontWeight:600,fontSize:13.5}}>{f.name}</div>
                  <div className="muted" style={{fontSize:12}}>{f.code} · {f.depName}</div>
                </div>
                <div style={{flex:1}}>
                  <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:3}}>
                    <Badge kind="red">{f.missType}</Badge>
                    <span className="mono" style={{fontWeight:600,fontSize:13}}>{fmtDate(f.date)} · {f.proposed}</span>
                  </div>
                  <div className="muted" style={{fontSize:12.5}}>“{f.reason}”</div>
                </div>
                {f.state==='Chờ duyệt' ? (
                  <div style={{display:'flex',gap:8}}>
                    <button className="btn btn-ghost btn-sm" onClick={()=>approve(f.id,false)}>Từ chối</button>
                    <button className="btn btn-primary btn-sm" onClick={()=>approve(f.id,true)}><Icon name="check" size={15}/>Duyệt</button>
                  </div>
                ) : <Badge kind={statusBadge(f.state)} dot>{f.state}</Badge>}
              </div>
            ))}
          </div>
        </div>
      )}

      {tab==='ot' && (
        <div className="card">
          <div className="card-head"><h3>Đăng ký tăng ca</h3><span className="muted" style={{fontSize:12.5}}>Hệ số 100% / 150% / 300% theo quy định</span></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Nhân viên</th><th>Ngày</th><th className="tbl-num">Số giờ</th><th>Hệ số</th><th>Lý do</th></tr></thead>
              <tbody>
                {OT_LOG.map(o=>(
                  <tr key={o.id} style={{cursor:'default'}}>
                    <td><EmpCell emp={o}/></td>
                    <td className="mono muted">{fmtDate(o.date)}</td>
                    <td className="tbl-num mono" style={{fontWeight:600}}>{o.hours} giờ</td>
                    <td><Badge kind={o.rate===300?'red':o.rate===150?'amber':'gray'}>{o.rate}%</Badge></td>
                    <td className="muted">{o.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ ico, col, bg, val, lbl }) {
  return (
    <div className="stat" style={{padding:'15px 16px'}}>
      <div style={{display:'flex',alignItems:'center',gap:11}}>
        <div style={{width:38,height:38,borderRadius:11,background:bg,color:col,display:'grid',placeItems:'center',flexShrink:0}}><Icon name={ico} size={19}/></div>
        <div>
          <div style={{fontSize:24,fontWeight:800,lineHeight:1,fontVariantNumeric:'tabular-nums'}}>{val}</div>
          <div className="stat-lbl" style={{marginTop:3}}>{lbl}</div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Attendance, MetricCard });
