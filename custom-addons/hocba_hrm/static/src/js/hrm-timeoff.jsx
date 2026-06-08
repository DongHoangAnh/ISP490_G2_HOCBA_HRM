/* ============================================================
   HOC BA HRM — Nghỉ phép & Làm online (Time Off)
   Luồng duyệt rõ ràng: Nhân viên → Leader → HCNS
   ============================================================ */

// trạng thái → bước hiện tại (0=NV, 1=Leader, 2=HCNS, 3=xong)
function leaveStep(state){
  return state==='Chờ Leader'?1 : state==='Chờ HCNS'?2 : state==='Đã duyệt'?3 : state==='Từ chối'?-1 : 0;
}
// người duyệt theo từng bước
function leaveApprovers(r){
  const dep = DEPARTMENTS.find(d=>d.id===r.emp.dep);
  const leaderName = r.emp.isLeader ? 'Cao Vân Khánh (BĐH)' : dep.leader;
  return [
    { role:'Người tạo đơn', who:r.emp.name, sub:r.emp.jobTitle, icon:'user' },
    { role:'Quản lý trực tiếp', who:leaderName, sub:'Trưởng phòng '+dep.name, icon:'users' },
    { role:'Hành chính nhân sự', who:'Hoàng Thị Ngọc Anh', sub:'HCNS · HB.75', icon:'shield' },
  ];
}
// nhãn trạng thái "đang chờ ai"
function leaveStatusLabel(r){
  if (r.state==='Chờ Leader'){ const d=DEPARTMENTS.find(x=>x.id===r.emp.dep); return {txt:'Chờ '+(r.emp.isLeader?'BĐH':'TP '+d.short)+' duyệt', kind:'amber'}; }
  if (r.state==='Chờ HCNS') return {txt:'Chờ HCNS xác nhận', kind:'blue'};
  if (r.state==='Đã duyệt') return {txt:'Đã duyệt — hiệu lực', kind:'green'};
  if (r.state==='Từ chối') return {txt:'Đã từ chối', kind:'red'};
  return {txt:r.state, kind:'gray'};
}

function TimeOff({ search }) {
  const [tab, setTab] = useState('requests');
  const [reqs, setReqs] = useState(LEAVE_REQUESTS.map(r=>({...r})));
  const [typeF, setTypeF] = useState('all');
  const [stateF, setStateF] = useState('all');
  const [selId, setSelId] = useState(null);

  const advance = (id, action) => setReqs(rs=>rs.map(r=>{
    if (r.id!==id) return r;
    if (action==='reject') return {...r, state:'Từ chối'};
    if (r.state==='Chờ Leader') return {...r, state:'Chờ HCNS'};
    if (r.state==='Chờ HCNS') return {...r, state:'Đã duyệt'};
    return r;
  }));

  const visible = reqs.filter(r=>{
    if (typeF!=='all' && r.type!==typeF) return false;
    if (stateF!=='all' && r.state!==stateF) return false;
    if (search){ const q=search.toLowerCase(); if(!(r.emp.name.toLowerCase().includes(q)||r.emp.code.toLowerCase().includes(q))) return false; }
    return true;
  });

  const waitLeader = reqs.filter(r=>r.state==='Chờ Leader').length;
  const waitHCNS = reqs.filter(r=>r.state==='Chờ HCNS').length;
  const approved = reqs.filter(r=>r.state==='Đã duyệt').length;
  const wfh = reqs.filter(r=>r.type==='wfh').length;
  const sel = selId ? reqs.find(r=>r.id===selId) : null;

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nghỉ phép & Làm online</h1>
          <p>Quy trình duyệt 2 cấp: Nhân viên → Quản lý trực tiếp → Hành chính nhân sự (HCNS)</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Xuất dữ liệu</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Tạo đơn nghỉ</button>
        </div>
      </div>

      <div className="stat-grid">
        <MetricCard ico="users" col="var(--amber)" bg="var(--amber-bg)" val={waitLeader} lbl="Chờ Quản lý duyệt"/>
        <MetricCard ico="shield" col="var(--blue)" bg="var(--blue-bg)" val={waitHCNS} lbl="Chờ HCNS xác nhận"/>
        <MetricCard ico="checkCircle" col="var(--green)" bg="var(--green-bg)" val={approved} lbl="Đã duyệt hiệu lực"/>
        <MetricCard ico="home" col="var(--violet)" bg="var(--violet-bg)" val={wfh} lbl="Đơn làm online"/>
      </div>

      <div className="tabs">
        {[['requests',`Đơn xin nghỉ ${waitLeader+waitHCNS?`(${waitLeader+waitHCNS})`:''}`],['balance','Số dư phép'],['types','Loại nghỉ phép & quy định']].map(([id,l])=>(
          <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}</button>
        ))}
      </div>

      {tab==='requests' && (
        <>
          <div className="filterbar">
            {[['all','Tất cả'],['Chờ Leader','Chờ Quản lý'],['Chờ HCNS','Chờ HCNS'],['Đã duyệt','Đã duyệt'],['Từ chối','Từ chối']].map(([v,l])=>{
              const c = v==='all'?reqs.length:reqs.filter(r=>r.state===v).length;
              return <button key={v} className={'chip'+(stateF===v?' active':'')} onClick={()=>setStateF(v)}>{l} <span className="ct">{c}</span></button>;
            })}
            <select className="sel" value={typeF} onChange={e=>setTypeF(e.target.value)} style={{marginLeft:'auto'}}>
              <option value="all">Mọi loại nghỉ</option>
              {LEAVE_TYPES.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>

          <div style={{display:'flex',flexDirection:'column',gap:12}}>
            {visible.map(r=>{
              const lt = LEAVE_TYPES.find(t=>t.id===r.type);
              const step = leaveStep(r.state);
              const apprs = leaveApprovers(r);
              const sl = leaveStatusLabel(r);
              const isHalf = r.days==='0.5';
              return (
                <div key={r.id} className="card" style={{padding:'18px 20px',cursor:'pointer'}} onClick={()=>setSelId(r.id)}>
                  <div style={{display:'flex',alignItems:'center',gap:18}}>
                    {/* who + type */}
                    <Avatar emp={r.emp} size={46}/>
                    <div style={{minWidth:178}}>
                      <div style={{fontWeight:700,fontSize:14}}>{r.emp.name}</div>
                      <div className="muted" style={{fontSize:12}}>{r.emp.code} · {r.emp.depName}</div>
                    </div>

                    {/* scope */}
                    <div style={{minWidth:230,flex:1}}>
                      <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:5,flexWrap:'wrap'}}>
                        <span className="badge" style={{background:lt.color+'1a',color:lt.color}}><span className="bdot"></span>{lt.name}</span>
                        <span className="badge badge-gray">{isHalf?'Nửa ngày':r.days+' ngày'}</span>
                        {lt.deduct ? <span className="badge badge-amber" style={{fontSize:10.5}}>Trừ phép</span> : <span className="badge badge-gray" style={{fontSize:10.5}}>Không trừ</span>}
                      </div>
                      <div style={{fontSize:13,fontWeight:600,display:'flex',alignItems:'center',gap:7}}>
                        <Icon name="calendar" size={14} className="faint"/>
                        {fmtDate(r.from)}{!isHalf && Number(r.days)>1 ? ' → '+leaveEndDate(r.from, r.days) : ''}
                        <span className="faint" style={{fontWeight:500,fontSize:12,marginLeft:4}}>· gửi {fmtDate(r.submitted)}</span>
                      </div>
                    </div>

                    {/* approval chain — named */}
                    <div style={{minWidth:210,display:'flex',alignItems:'center',gap:0}}>
                      {apprs.map((a,i)=>{
                        const done = r.state!=='Từ chối' && i<step;
                        const cur = r.state!=='Từ chối' && i===step && step<3;
                        const rej = r.state==='Từ chối' && i===Math.max(1,step);
                        return (
                          <React.Fragment key={i}>
                            <div title={a.role+': '+a.who} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:3,flexShrink:0,width:62}}>
                              <div style={{width:30,height:30,borderRadius:'50%',display:'grid',placeItems:'center',
                                background: done?'var(--green)': cur?'var(--gold-500)': rej?'var(--red-600)':'#EEEAE4',
                                color:(done||cur||rej)?'#fff':'var(--faint)', boxShadow:cur?'0 0 0 4px var(--gold-50)':'none'}}>
                                {done?<Icon name="check" size={15}/>: rej?<Icon name="x" size={15}/>:<Icon name={a.icon} size={15}/>}
                              </div>
                              <span style={{fontSize:9.5,fontWeight:700,color:cur?'var(--ink)':'var(--faint)',whiteSpace:'nowrap'}}>{i===0?'NV':i===1?'Quản lý':'HCNS'}</span>
                            </div>
                            {i<2 && <div style={{flex:1,height:2,background:done?'var(--green)':'#EEEAE4',marginBottom:14,minWidth:8}}></div>}
                          </React.Fragment>
                        );
                      })}
                    </div>

                    {/* status + action */}
                    <div style={{minWidth:188,display:'flex',flexDirection:'column',alignItems:'flex-end',gap:8}}>
                      <Badge kind={sl.kind} dot>{sl.txt}</Badge>
                      {(r.state==='Chờ Leader'||r.state==='Chờ HCNS') ? (
                        <div style={{display:'flex',gap:7}} onClick={e=>e.stopPropagation()}>
                          <button className="btn btn-ghost btn-sm" onClick={()=>advance(r.id,'reject')}>Từ chối</button>
                          <button className="btn btn-primary btn-sm" onClick={()=>advance(r.id,'approve')}><Icon name="check" size={14}/>{r.state==='Chờ Leader'?'Duyệt':'Xác nhận'}</button>
                        </div>
                      ) : <span className="faint" style={{fontSize:11.5}}>Xem chi tiết →</span>}
                    </div>
                  </div>
                </div>
              );
            })}
            {visible.length===0 && <div className="card"><div className="empty">Không có đơn phù hợp.</div></div>}
          </div>
        </>
      )}

      {tab==='balance' && (
        <div className="card">
          <div className="card-head"><h3>Số dư nghỉ phép năm 2026</h3><span className="muted" style={{fontSize:12.5}}>{LEAVE_BALANCE.length} nhân sự chính thức · phép năm 12 ngày + phép tồn năm trước</span></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Nhân viên</th><th>Phòng ban</th><th className="tbl-num">Phép năm</th><th className="tbl-num">Phép tồn</th><th className="tbl-num">Đã dùng</th><th className="tbl-num">Còn lại</th><th style={{width:160}}>Sử dụng</th></tr></thead>
              <tbody>
                {LEAVE_BALANCE.map(b=>{
                  const total=b.year+b.carry; const pct=Math.round(b.used/total*100);
                  return (
                    <tr key={b.emp.id} style={{cursor:'default'}}>
                      <td><EmpCell emp={b.emp}/></td>
                      <td className="muted">{b.emp.depName}</td>
                      <td className="tbl-num mono">{b.year}</td>
                      <td className="tbl-num mono muted">{b.carry||'—'}</td>
                      <td className="tbl-num mono">{b.used}</td>
                      <td className="tbl-num mono" style={{fontWeight:700,color: b.remain<2?'var(--red-600)':'var(--green)'}}>{b.remain}</td>
                      <td><div className="bar"><span style={{width:pct+'%',background: pct>80?'var(--red-500)':'var(--green)'}}></span></div></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab==='types' && (
        <div className="card">
          <div className="card-head"><h3>Loại nghỉ phép & quy định duyệt</h3></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Loại nghỉ</th><th>Trừ phép năm</th><th>Cấp duyệt</th><th>Yêu cầu chứng từ</th><th>Ghi chú</th></tr></thead>
              <tbody>
                {LEAVE_TYPES.map(t=>{
                  const rule = {
                    annual:   {appr:'Quản lý → HCNS', doc:'Không', note:'Đăng ký trước tối thiểu 3 ngày'},
                    sick:     {appr:'Quản lý → HCNS', doc:'Giấy bác sĩ (nếu >1 ngày)', note:'Báo Quản lý ngay trong ngày'},
                    maternity:{appr:'HCNS', doc:'Giấy khám thai / sinh', note:'Theo luật BHXH 6 tháng'},
                    early:    {appr:'Quản lý', doc:'Không', note:'Duyệt nhanh trong ngày'},
                    wfh:      {appr:'Quản lý', doc:'Không', note:'No Validation · không trừ phép'},
                    unpaid:   {appr:'Quản lý → HCNS → BĐH', doc:'Đơn giải trình', note:'Trừ lương theo ngày'},
                  }[t.id] || {appr:'Quản lý → HCNS', doc:'—', note:'—'};
                  return (
                    <tr key={t.id} style={{cursor:'default'}}>
                      <td><span className="badge" style={{background:t.color+'1a',color:t.color}}><span className="bdot"></span>{t.name}</span></td>
                      <td><Badge kind={t.deduct?'amber':'gray'}>{t.deduct?'Có trừ':'Không trừ'}</Badge></td>
                      <td style={{fontWeight:600,fontSize:12.5}}>{rule.appr}</td>
                      <td className="muted">{rule.doc}</td>
                      <td className="muted">{rule.note}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sel && <LeaveDrawer r={sel} advance={advance} onClose={()=>setSelId(null)}/>}
    </div>
  );
}

function leaveEndDate(from, days){
  const d=new Date(from); d.setDate(d.getDate()+Math.ceil(Number(days))-1);
  return d.toISOString().slice(0,10).split('-').reverse().join('/');
}

function LeaveDrawer({ r, advance, onClose }) {
  const lt = LEAVE_TYPES.find(t=>t.id===r.type);
  const step = leaveStep(r.state);
  const apprs = leaveApprovers(r);
  const isHalf = r.days==='0.5';
  // mốc thời gian giả lập
  const subDate = fmtDate(r.submitted);
  const times = ['09:14 · '+subDate, step>1?'11:02 · '+subDate:'', step>2?'14:30 · '+subDate:''];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,'+lt.color+'14,#fff)'}}>
        <Avatar emp={r.emp} size={56}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',gap:10,alignItems:'center',flexWrap:'wrap'}}>
            <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{r.emp.name}</h2>
            <span className="badge" style={{background:lt.color+'1a',color:lt.color}}><span className="bdot"></span>{lt.name}</span>
          </div>
          <div className="muted" style={{fontSize:13,marginTop:3}}>{r.emp.code} · {r.emp.jobTitle} · {r.emp.depName}</div>
        </div>
        <Badge kind={leaveStatusLabel(r).kind} dot>{leaveStatusLabel(r).txt}</Badge>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>

      <div style={{padding:'22px 24px',maxHeight:'60vh',overflowY:'auto'}}>
        {/* scope */}
        <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--faint)',fontWeight:800,marginBottom:12}}>Phạm vi nghỉ</div>
        <div className="grid-3" style={{marginBottom:14}}>
          <MiniStat lbl="Từ ngày" val={fmtDate(r.from)} col="var(--ink)"/>
          <MiniStat lbl={isHalf?'Buổi':'Đến ngày'} val={isHalf?'Buổi chiều':leaveEndDate(r.from,r.days)} col="var(--ink)"/>
          <MiniStat lbl="Số ngày nghỉ" val={isHalf?'0,5 ngày':r.days+' ngày'} col={lt.color}/>
        </div>
        <div className="grid-2" style={{rowGap:14,marginBottom:20}}>
          <div className="kv"><div className="k">Loại nghỉ</div><div className="v">{lt.name}</div></div>
          <div className="kv"><div className="k">Trừ phép năm</div><div className="v">{lt.deduct?'Có — trừ vào quỹ phép':'Không trừ phép'}</div></div>
          <div className="kv" style={{gridColumn:'1 / -1'}}><div className="k">Lý do</div><div className="v" style={{fontWeight:500}}>"{r.reason}"</div></div>
          <div className="kv" style={{gridColumn:'1 / -1'}}><div className="k">Người bàn giao công việc</div><div className="v">{leaveApprovers(r)[1].who} (phụ trách thay)</div></div>
        </div>

        {/* approval chain — vertical, named */}
        <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--faint)',fontWeight:800,marginBottom:14}}>Luồng phê duyệt</div>
        <div style={{position:'relative'}}>
          {apprs.map((a,i)=>{
            const done = r.state!=='Từ chối' && i<step;
            const cur = r.state!=='Từ chối' && i===step && step<3;
            const rej = r.state==='Từ chối' && i===Math.max(1,step);
            const last = i===apprs.length-1;
            let stTxt = i===0 ? 'Đã gửi đơn' : done ? 'Đã duyệt' : cur ? 'Đang chờ xử lý' : rej ? 'Đã từ chối' : 'Chưa tới lượt';
            let stKind = i===0 ? 'green' : done ? 'green' : cur ? 'amber' : rej ? 'red' : 'gray';
            return (
              <div key={i} style={{display:'flex',gap:15,paddingBottom:last?0:18}}>
                <div style={{display:'flex',flexDirection:'column',alignItems:'center'}}>
                  <div style={{width:38,height:38,borderRadius:'50%',display:'grid',placeItems:'center',flexShrink:0,
                    background: done||i===0?'var(--green)': cur?'var(--gold-500)': rej?'var(--red-600)':'#EEEAE4',
                    color:(done||cur||rej||i===0)?'#fff':'var(--faint)'}}>
                    {(done||i===0)?<Icon name="check" size={18}/>: rej?<Icon name="x" size={18}/>:<Icon name={a.icon} size={17}/>}
                  </div>
                  {!last && <div style={{width:2,flex:1,minHeight:24,background:done?'var(--green)':'var(--border-strong)',marginTop:2}}></div>}
                </div>
                <div style={{flex:1,paddingBottom:4}}>
                  <div className="between">
                    <div>
                      <div style={{fontWeight:700,fontSize:13.5}}>{a.who}</div>
                      <div className="muted" style={{fontSize:12}}>{a.role} · {a.sub}</div>
                    </div>
                    <div style={{textAlign:'right'}}>
                      <Badge kind={stKind} dot>{stTxt}</Badge>
                      {times[i] && <div className="faint" style={{fontSize:11,marginTop:4}}>{times[i]}</div>}
                    </div>
                  </div>
                  {cur && (
                    <div style={{display:'flex',gap:8,marginTop:11}}>
                      <button className="btn btn-ghost btn-sm" onClick={()=>{advance(r.id,'reject');onClose();}}>Từ chối</button>
                      <button className="btn btn-primary btn-sm" onClick={()=>advance(r.id,'approve')}><Icon name="check" size={14}/>{i===1?'Duyệt (Quản lý)':'Xác nhận (HCNS)'}</button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}

Object.assign(window, { TimeOff, LeaveDrawer, leaveStep, leaveApprovers, leaveStatusLabel });
