/* ============================================================
   HOC BA HRM — Tuyển dụng (Kanban pipeline)
   ============================================================ */

function Recruitment({ search }) {
  const [apps, setApps] = useState(APPLICANTS.map(a=>({...a})));
  const [pos, setPos] = useState('all');
  const [drag, setDrag] = useState(null);
  const [over, setOver] = useState(null);
  const [sel, setSel] = useState(null);

  const visible = apps.filter(a=>{
    if (pos!=='all' && a.pos!==pos) return false;
    if (search){ const q=search.toLowerCase(); if(!(a.name.toLowerCase().includes(q)||a.pos.toLowerCase().includes(q))) return false; }
    return true;
  });

  const moveTo = (id, stage) => setApps(as=>as.map(a=>a.id===id?{...a,stage}:a));

  const onDrop = (stageId) => {
    if (drag) moveTo(drag, stageId);
    setDrag(null); setOver(null);
  };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tuyển dụng</h1>
          <p>{REC_POSITIONS.length} vị trí đang tuyển · {apps.length} ứng viên · quy trình 10 bước Order → Onboarding</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="briefcase" size={16}/>Quản lý vị trí</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Thêm ứng viên</button>
        </div>
      </div>

      <div className="filterbar">
        <button className={'chip'+(pos==='all'?' active':'')} onClick={()=>setPos('all')}>Tất cả vị trí <span className="ct">{apps.length}</span></button>
        {REC_POSITIONS.map(p=>{
          const c = apps.filter(a=>a.pos===p).length;
          return <button key={p} className={'chip'+(pos===p?' active':'')} onClick={()=>setPos(p)}>{p} <span className="ct">{c}</span></button>;
        })}
      </div>

      <div className="kanban">
        {REC_STAGES.map(st=>{
          const items = visible.filter(a=>a.stage===st.id);
          return (
            <div key={st.id}
              className={'kcol'+(over===st.id?' dragover':'')}
              onDragOver={e=>{e.preventDefault();setOver(st.id);}}
              onDragLeave={()=>setOver(o=>o===st.id?null:o)}
              onDrop={()=>onDrop(st.id)}>
              <div className="kcol-head" style={{background:st.color+'12'}}>
                <span className="kdot" style={{background:st.color}}></span>
                <span className="kt">{st.name}</span>
                <span className="kc">{items.length}</span>
              </div>
              <div className="kcol-body">
                {items.map(a=>(
                  <div key={a.id}
                    className={'kcard'+(drag===a.id?' dragging':'')}
                    draggable
                    onDragStart={()=>setDrag(a.id)}
                    onDragEnd={()=>{setDrag(null);setOver(null);}}
                    onClick={()=>setSel(a)}>
                    <div style={{display:'flex',gap:10,alignItems:'center',marginBottom:9}}>
                      <Avatar emp={a} size={36}/>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{fontWeight:700,fontSize:13}}>{a.name}</div>
                        <div className="muted" style={{fontSize:11.5}}>{a.exp}</div>
                      </div>
                      <Stars n={a.rating}/>
                    </div>
                    <div style={{fontSize:12,color:'var(--ink-soft)',fontWeight:500,marginBottom:9}}>{a.pos}</div>
                    <div style={{display:'flex',alignItems:'center',gap:8,justifyContent:'space-between'}}>
                      <Badge kind="gray">{a.source}</Badge>
                      {a.interview
                        ? <span style={{fontSize:11,color:'var(--violet)',fontWeight:600,display:'inline-flex',alignItems:'center',gap:4}}><Icon name="calendar" size={13}/>{fmtDate(a.interview)}</span>
                        : <span className="faint" style={{fontSize:11}}>{a.days} ngày trước</span>}
                    </div>
                  </div>
                ))}
                {items.length===0 && <div style={{padding:'20px 8px',textAlign:'center',color:'var(--faint)',fontSize:12}}>Kéo ứng viên vào đây</div>}
              </div>
            </div>
          );
        })}
      </div>

      {sel && <ApplicantModal app={sel} onClose={()=>setSel(null)} onMove={(s)=>{moveTo(sel.id,s);setSel({...sel,stage:s});}}/>}
    </div>
  );
}

function Stars({ n }) {
  return (
    <div style={{display:'flex',gap:1}}>
      {[0,1,2,3,4].map(i=>(
        <svg key={i} width="12" height="12" viewBox="0 0 24 24"
          fill={i<n?'var(--gold-500)':'none'} stroke={i<n?'var(--gold-500)':'#D8D2C9'} strokeWidth="1.6" strokeLinejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2Z"/>
        </svg>
      ))}
    </div>
  );
}

function ApplicantModal({ app, onClose, onMove }) {
  const stIdx = REC_STAGES.findIndex(s=>s.id===app.stage);
  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--blue-bg),#fff)'}}>
        <Avatar emp={app} size={56}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',gap:10,alignItems:'center'}}>
            <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{app.name}</h2>
            <Stars n={app.rating}/>
          </div>
          <div className="muted" style={{fontSize:13,marginTop:3}}>Ứng tuyển: <b style={{color:'var(--ink-soft)'}}>{app.pos}</b> · {app.exp}</div>
          <div style={{display:'flex',gap:14,marginTop:9}}>
            <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="mail" size={15}/>{app.email}</span>
            <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="phone" size={15}/>{app.phone}</span>
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'22px 24px'}}>
        {/* Pipeline progress */}
        <div style={{display:'flex',alignItems:'center',marginBottom:22}}>
          {REC_STAGES.map((s,i)=>(
            <React.Fragment key={s.id}>
              <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:6,flex:'0 0 auto'}}>
                <div style={{width:30,height:30,borderRadius:'50%',display:'grid',placeItems:'center',background:i<=stIdx?s.color:'#EEEAE4',color:i<=stIdx?'#fff':'var(--faint)',fontWeight:700,fontSize:12,transition:'all .2s'}}>
                  {i<stIdx?<Icon name="check" size={15}/>:i+1}
                </div>
                <span style={{fontSize:10.5,fontWeight:600,color:i<=stIdx?'var(--ink)':'var(--faint)',whiteSpace:'nowrap'}}>{s.name}</span>
              </div>
              {i<REC_STAGES.length-1 && <div style={{flex:1,height:2,background:i<stIdx?REC_STAGES[i].color:'#EEEAE4',margin:'0 4px',marginBottom:18}}></div>}
            </React.Fragment>
          ))}
        </div>

        <div className="grid-2" style={{rowGap:16,marginBottom:20}}>
          <div className="kv"><div className="k">Mã ứng viên</div><div className="v">{app.id}</div></div>
          <div className="kv"><div className="k">Nguồn</div><div className="v">{app.source}</div></div>
          <div className="kv"><div className="k">Kinh nghiệm</div><div className="v">{app.exp}</div></div>
          <div className="kv"><div className="k">Lịch phỏng vấn</div><div className="v">{app.interview?fmtDate(app.interview):'Chưa xếp lịch'}</div></div>
        </div>

        <div className="divider"></div>
        <div style={{display:'flex',gap:10,alignItems:'center'}}>
          <span className="muted" style={{fontSize:12.5,fontWeight:600}}>Chuyển bước:</span>
          <select className="sel" value={app.stage} onChange={e=>onMove(e.target.value)} style={{flex:1}}>
            {REC_STAGES.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <button className="btn btn-ghost"><Icon name="mail" size={16}/>Gửi email</button>
          {stIdx>=3 && <button className="btn btn-primary"><Icon name="checkCircle" size={16}/>Tạo nhân viên</button>}
        </div>
      </div>
    </Modal>
  );
}

Object.assign(window, { Recruitment, Stars, ApplicantModal });
