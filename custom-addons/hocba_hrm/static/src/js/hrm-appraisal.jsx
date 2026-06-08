/* ============================================================
   HOC BA HRM — Đánh giá (Appraisal)
   ============================================================ */

function Appraisal({ search }) {
  const [tab, setTab] = useState('reviews');
  const [items, setItems] = useState(APPRAISALS.map(a=>({...a})));
  const [sel, setSel] = useState(null);

  const visible = items.filter(a=> !search || a.emp.name.toLowerCase().includes(search.toLowerCase()) || a.emp.code.toLowerCase().includes(search.toLowerCase()));

  const done = items.filter(a=>a.state==='Hoàn thành');
  const waitSelf = items.filter(a=>a.state==='Chờ tự đánh giá').length;
  const waitMgr = items.filter(a=>a.state==='Chờ quản lý').length;
  const avg = (done.reduce((s,a)=>s+a.final,0)/(done.length||1)).toFixed(1);

  // skills evolution: trung bình kỹ năng toàn công ty
  const skillAvg = SKILLS.map(s=>({
    ...s,
    val:+(items.reduce((sum,a)=>sum+a.skills[s.id],0)/items.length).toFixed(2),
  }));

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Đánh giá nhân sự</h1>
          <p>Chu kỳ {APPRAISAL_PERIOD} · self-assessment → quản lý đánh giá → chốt · theo dõi kỹ năng & mục tiêu</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Báo cáo Skills</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Mở chu kỳ đánh giá</button>
        </div>
      </div>

      <div className="stat-grid">
        <MetricCard ico="award" col="var(--green)" bg="var(--green-bg)" val={done.length} lbl="Đã hoàn thành"/>
        <MetricCard ico="edit" col="var(--amber)" bg="var(--amber-bg)" val={waitSelf} lbl="Chờ tự đánh giá"/>
        <MetricCard ico="users" col="var(--blue)" bg="var(--blue-bg)" val={waitMgr} lbl="Chờ quản lý duyệt"/>
        <MetricCard ico="star" col="var(--gold-600)" bg="var(--gold-50)" val={avg} lbl="Điểm TB toàn công ty"/>
      </div>

      <div className="tabs">
        {[['reviews','Phiếu đánh giá'],['skills','Tiến hóa kỹ năng']].map(([id,l])=>(
          <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}</button>
        ))}
      </div>

      {tab==='reviews' && (
        <div className="grid-3" style={{gridTemplateColumns:'repeat(auto-fill,minmax(310px,1fr))'}}>
          {visible.map(a=>(
            <div key={a.id} className="card" style={{padding:18,cursor:'pointer'}} onClick={()=>setSel(a)}>
              <div style={{display:'flex',gap:12,alignItems:'center',marginBottom:14}}>
                <Avatar emp={a.emp} size={44}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontWeight:700,fontSize:14}}>{a.emp.name}</div>
                  <div className="muted" style={{fontSize:12}}>{a.emp.jobTitle} · {a.emp.depShort}</div>
                </div>
                {a.final!=null
                  ? <div style={{textAlign:'center'}}><div style={{fontSize:22,fontWeight:800,color:'var(--gold-600)',lineHeight:1}}>{a.final}</div><div className="faint" style={{fontSize:10}}>/ 5.0</div></div>
                  : <Icon name="clock" size={20} className="faint"/>}
              </div>
              <div className="between" style={{marginBottom:10}}>
                <Badge kind={a.state==='Hoàn thành'?'green':a.state==='Chờ quản lý'?'blue':'amber'} dot>{a.state}</Badge>
                <span className="muted" style={{fontSize:11.5}}>QL: {a.manager.split(' ').slice(-2).join(' ')}</span>
              </div>
              {/* score compare bars */}
              <div style={{display:'flex',flexDirection:'column',gap:7}}>
                <ScoreRow label="Tự đánh giá" val={a.self} color="var(--blue)"/>
                <ScoreRow label="Quản lý" val={a.state==='Chờ tự đánh giá'||a.state==='Chờ quản lý'?null:a.mgr} color="var(--red-600)"/>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab==='skills' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-head"><h3>Năng lực trung bình toàn công ty</h3><span className="badge badge-gold" style={{marginLeft:'auto'}}>{APPRAISAL_PERIOD}</span></div>
            <div className="card-pad" style={{display:'flex',flexDirection:'column',gap:16}}>
              {skillAvg.map(s=>(
                <div key={s.id}>
                  <div className="between" style={{marginBottom:6}}>
                    <span style={{fontSize:13,fontWeight:600}}>{s.name}</span>
                    <span className="mono" style={{fontWeight:700,fontSize:13}}>{s.val} <span className="faint" style={{fontWeight:500}}>/5</span></span>
                  </div>
                  <div className="bar"><span style={{width:(s.val/5*100)+'%',background:'linear-gradient(90deg,var(--gold-500),var(--red-600))'}}></span></div>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-head"><h3>Xếp hạng nhân sự nổi bật</h3></div>
            <div style={{padding:'6px 10px'}}>
              {[...items].filter(a=>a.final!=null).sort((a,b)=>b.final-a.final).slice(0,7).map((a,i)=>(
                <div key={a.id} style={{display:'flex',alignItems:'center',gap:12,padding:'10px 8px'}}>
                  <div style={{width:24,height:24,borderRadius:8,display:'grid',placeItems:'center',fontWeight:800,fontSize:12,background:i<3?'var(--gold-50)':'var(--surface-2)',color:i<3?'var(--gold-600)':'var(--muted)'}}>{i+1}</div>
                  <Avatar emp={a.emp} size={34}/>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600,fontSize:13}}>{a.emp.name}</div>
                    <div className="muted" style={{fontSize:11.5}}>{a.emp.depName}</div>
                  </div>
                  <div className="mono" style={{fontWeight:800,fontSize:15,color:'var(--gold-600)'}}>{a.final}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {sel && <AppraisalModal a={sel} onClose={()=>setSel(null)}/>}
    </div>
  );
}

function ScoreRow({ label, val, color }) {
  return (
    <div style={{display:'flex',alignItems:'center',gap:9}}>
      <span className="muted" style={{fontSize:11.5,width:72,flexShrink:0}}>{label}</span>
      <div className="bar" style={{flex:1}}><span style={{width:(val?val/5*100:0)+'%',background:color}}></span></div>
      <span className="mono" style={{fontSize:12,fontWeight:700,width:30,textAlign:'right',color:val?'var(--ink)':'var(--faint)'}}>{val??'—'}</span>
    </div>
  );
}

function AppraisalModal({ a, onClose }) {
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--gold-50),#fff)'}}>
        <Avatar emp={a.emp} size={56}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',gap:10,alignItems:'center'}}>
            <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{a.emp.name}</h2>
            <Badge kind={a.state==='Hoàn thành'?'green':a.state==='Chờ quản lý'?'blue':'amber'} dot>{a.state}</Badge>
          </div>
          <div className="muted" style={{fontSize:13,marginTop:3}}>{a.emp.jobTitle} · {a.emp.depName} · {a.period} · QL: {a.manager}</div>
        </div>
        {a.final!=null && <div style={{textAlign:'center'}}><div style={{fontSize:30,fontWeight:800,color:'var(--gold-600)',lineHeight:1}}>{a.final}</div><div className="faint" style={{fontSize:11}}>điểm chốt</div></div>}
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'22px 24px',maxHeight:'58vh',overflowY:'auto'}}>
        <div className="grid-2" style={{gap:24}}>
          <div>
            <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--faint)',fontWeight:800,marginBottom:12}}>Đánh giá kỹ năng</div>
            <div style={{display:'flex',flexDirection:'column',gap:14}}>
              {SKILLS.map(s=>(
                <div key={s.id}>
                  <div className="between" style={{marginBottom:5}}>
                    <span style={{fontSize:12.5,fontWeight:600}}>{s.name}</span>
                    <span className="mono" style={{fontWeight:700,fontSize:12.5}}>{a.skills[s.id]}/5</span>
                  </div>
                  <div className="bar"><span style={{width:(a.skills[s.id]/5*100)+'%',background:'var(--teal)'}}></span></div>
                </div>
              ))}
            </div>
            <div style={{marginTop:18,padding:'14px 16px',borderRadius:12,background:'var(--surface-2)',border:'1px solid var(--border)'}}>
              <div style={{display:'flex',gap:20}}>
                <div><div className="faint" style={{fontSize:11,fontWeight:700,textTransform:'uppercase'}}>Tự đánh giá</div><div className="mono" style={{fontSize:20,fontWeight:800,color:'var(--blue)'}}>{a.self}</div></div>
                <div><div className="faint" style={{fontSize:11,fontWeight:700,textTransform:'uppercase'}}>Quản lý</div><div className="mono" style={{fontSize:20,fontWeight:800,color:'var(--red-600)'}}>{a.state==='Hoàn thành'?a.mgr:'—'}</div></div>
                <div><div className="faint" style={{fontSize:11,fontWeight:700,textTransform:'uppercase'}}>Điểm chốt</div><div className="mono" style={{fontSize:20,fontWeight:800,color:'var(--gold-600)'}}>{a.final??'—'}</div></div>
              </div>
            </div>
          </div>
          <div>
            <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--faint)',fontWeight:800,marginBottom:12}}>Mục tiêu (Goals)</div>
            <div style={{display:'flex',flexDirection:'column',gap:13}}>
              {a.goals.map((g,i)=>(
                <div key={i} style={{padding:'13px 15px',border:'1px solid var(--border)',borderRadius:12}}>
                  <div className="between" style={{marginBottom:8}}>
                    <span style={{fontSize:13,fontWeight:600,flex:1}}>{g.text}</span>
                    <span className="mono" style={{fontWeight:700,fontSize:12.5,color:g.progress>=80?'var(--green)':g.progress>=50?'var(--amber)':'var(--muted)'}}>{g.progress}%</span>
                  </div>
                  <div className="bar"><span style={{width:g.progress+'%',background:g.progress>=80?'var(--green)':g.progress>=50?'var(--gold-500)':'var(--blue)'}}></span></div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{display:'flex',gap:10,marginTop:24,justifyContent:'flex-end'}}>
          <button className="btn btn-ghost"><Icon name="mail" size={16}/>Nhắc nhở</button>
          {a.state!=='Hoàn thành'
            ? <button className="btn btn-primary"><Icon name="check" size={16}/>{a.state==='Chờ tự đánh giá'?'Gửi nhắc tự đánh giá':'Quản lý chấm điểm'}</button>
            : <button className="btn btn-gold"><Icon name="award" size={16}/>Xem phiếu chốt</button>}
        </div>
      </div>
    </Modal>
  );
}

Object.assign(window, { Appraisal, ScoreRow, AppraisalModal });
