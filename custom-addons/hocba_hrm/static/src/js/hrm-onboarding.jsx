/* ============================================================
   HOC BA HRM — Nhập việc (Onboarding)
   Quy trình Học Bá: Hội nhập (2 tuần) → đánh giá → cấp thiết bị
   → đào tạo chuyên môn → xét chính thức (2 tháng)
   ============================================================ */

function Onboarding({ search }) {
  const [items, setItems] = useState(ONBOARDING.map(o=>({...o, tasks:{...o.tasks}, equip:{...o.equip}})));
  const [sel, setSel] = useState(null);

  const update = (id, patch) => setItems(its=>its.map(o=>o.id===id?{...o,...patch}:o));

  const visible = items.filter(o=> !search || o.emp.name.toLowerCase().includes(search.toLowerCase()) || o.emp.code.toLowerCase().includes(search.toLowerCase()));

  const cIntro = items.filter(o=>o.phase==='intro').length;
  const cEval2w = items.filter(o=>o.phase==='eval2w').length;
  const cTrain = items.filter(o=>o.phase==='training').length;
  const cEval2m = items.filter(o=>o.phase==='eval2m').length;

  const selItem = sel ? items.find(o=>o.id===sel) : null;

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhận việc</h1>
          <p>Quy trình hội nhập Học Bá · thử việc 2 tuần → đánh giá cấp thiết bị → xét chính thức sau 2 tháng</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="file" size={16}/>Mẫu checklist</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Khởi tạo nhận việc</button>
        </div>
      </div>

      <div className="stat-grid">
        <MetricCard ico="users" col="var(--blue)" bg="var(--blue-bg)" val={cIntro} lbl="Đang hội nhập"/>
        <MetricCard ico="checkCircle" col="var(--gold-600)" bg="var(--gold-50)" val={cEval2w} lbl="Chờ đánh giá 2 tuần"/>
        <MetricCard ico="book" col="var(--teal)" bg="var(--teal-bg)" val={cTrain} lbl="Đào tạo chuyên môn"/>
        <MetricCard ico="award" col="var(--green)" bg="var(--green-bg)" val={cEval2m} lbl="Chờ xét chính thức"/>
      </div>

      {/* process legend */}
      <div className="card" style={{padding:'14px 20px',marginBottom:18}}>
        <div style={{display:'flex',alignItems:'center',gap:6,flexWrap:'wrap'}}>
          {ONB_PHASES.map((p,i)=>(
            <React.Fragment key={p.id}>
              <div style={{display:'flex',alignItems:'center',gap:9}}>
                <span style={{width:26,height:26,borderRadius:8,background:p.color+'1a',color:p.color,display:'grid',placeItems:'center',fontWeight:800,fontSize:12,flexShrink:0}}>{i+1}</span>
                <div>
                  <div style={{fontSize:12.5,fontWeight:700}}>{p.name}</div>
                  <div className="faint" style={{fontSize:11}}>{p.sub}</div>
                </div>
              </div>
              {i<ONB_PHASES.length-1 && <Icon name="chevR" size={16} className="faint" style={{margin:'0 6px'}}/>}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div style={{display:'flex',flexDirection:'column',gap:12}}>
        {visible.map(o=>{
          const phaseIdx = ONB_PHASES.findIndex(p=>p.id===o.phase);
          const introDone = ONB_TASKS.filter(t=>o.tasks[t.id]).length;
          return (
            <div key={o.id} className="card" style={{padding:'16px 20px',cursor:'pointer'}} onClick={()=>setSel(o.id)}>
              <div style={{display:'flex',alignItems:'center',gap:16}}>
                <Avatar emp={o.emp} size={46}/>
                <div style={{minWidth:200}}>
                  <div style={{fontWeight:700,fontSize:14}}>{o.emp.name}</div>
                  <div className="muted" style={{fontSize:12}}>{o.emp.code} · {o.emp.jobTitle} · {o.emp.depShort}</div>
                </div>
                <div style={{minWidth:130}}>
                  <div className="faint" style={{fontSize:10.5,fontWeight:700,textTransform:'uppercase',letterSpacing:'.4px'}}>Ngày thử việc</div>
                  <div style={{fontWeight:700,fontSize:14}}>Ngày {o.dayN} <span className="faint" style={{fontWeight:500,fontSize:11.5}}>· vào {fmtDate(o.startDate)}</span></div>
                </div>
                {/* milestone tracker */}
                <div style={{flex:1,display:'flex',alignItems:'center',minWidth:280}}>
                  {ONB_PHASES.map((p,i)=>{
                    const done = i<phaseIdx;
                    const cur = i===phaseIdx;
                    return (
                      <React.Fragment key={p.id}>
                        <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:5,flexShrink:0}}>
                          <div style={{width:26,height:26,borderRadius:'50%',display:'grid',placeItems:'center',fontWeight:700,fontSize:11,
                            background: done?p.color: cur?p.color:'#EEEAE4', color: (done||cur)?'#fff':'var(--faint)',
                            boxShadow: cur?'0 0 0 4px '+p.color+'2a':'none', transition:'all .2s'}}>
                            {done?'✓':i+1}
                          </div>
                          <span style={{fontSize:10,fontWeight:600,color:cur?'var(--ink)':'var(--faint)',whiteSpace:'nowrap'}}>{p.name}</span>
                        </div>
                        {i<ONB_PHASES.length-1 && <div style={{flex:1,height:2,background:done?p.color:'#EEEAE4',marginBottom:16,minWidth:14}}></div>}
                      </React.Fragment>
                    );
                  })}
                </div>
                <div style={{minWidth:90,textAlign:'right'}}>
                  {o.phase==='intro' && <Badge kind="blue" dot>Checklist {introDone}/{ONB_TASKS.length}</Badge>}
                  {o.phase==='eval2w' && <Badge kind="amber" dot>Cần đánh giá</Badge>}
                  {o.phase==='training' && <Badge kind="teal" dot>Đang đào tạo</Badge>}
                  {o.phase==='eval2m' && <Badge kind="green" dot>Xét chính thức</Badge>}
                </div>
                <Icon name="chevR" size={18} className="faint"/>
              </div>
            </div>
          );
        })}
      </div>

      {selItem && <OnboardingModal o={selItem} update={update} onClose={()=>setSel(null)}/>}
    </div>
  );
}

function OnboardingModal({ o, update, onClose }) {
  const toggleTask = (tid) => update(o.id, { tasks:{...o.tasks, [tid]:!o.tasks[tid]} });
  const toggleEquip = (eid) => update(o.id, { equip:{...o.equip, [eid]:!o.equip[eid]} });
  const passEval2w = (ok) => update(o.id, { eval2w: ok?'pass':'fail', phase: ok?'training':o.phase });
  const passEval2m = (ok) => update(o.id, { eval2m: ok?'pass':'fail' });

  const introDone = ONB_TASKS.every(t=>o.tasks[t.id]);
  const equipDone = ONB_EQUIP.every(t=>o.equip[t.id]);

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--blue-bg),#fff)'}}>
        <Avatar emp={o.emp} size={56}/>
        <div style={{flex:1}}>
          <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{o.emp.name}</h2>
          <div className="muted" style={{fontSize:13,marginTop:3}}>{o.emp.code} · {o.emp.jobTitle} · {o.emp.depName} · Vào làm {fmtDate(o.startDate)} (ngày {o.dayN})</div>
          <div style={{display:'flex',gap:14,marginTop:9,flexWrap:'wrap'}}>
            <span style={{fontSize:12.5}} className="muted">QL đào tạo: <b style={{color:'var(--ink-soft)'}}>{o.mentor}</b></span>
            <span style={{fontSize:12.5}} className="muted">Buddy: <b style={{color:'var(--ink-soft)'}}>{o.buddy}</b></span>
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'20px 24px',maxHeight:'60vh',overflowY:'auto'}}>

        {/* Mốc 1: Hội nhập */}
        <OnbSection num="1" color="#1D4ED8" title="Hội nhập (ngày 1 → tuần 2)" badge={introDone?'done':'doing'}>
          {ONB_TASKS.map(t=>(
            <CheckItem key={t.id} checked={o.tasks[t.id]} label={t.label} onToggle={()=>toggleTask(t.id)}/>
          ))}
        </OnbSection>

        {/* Gate 1: Đánh giá 2 tuần */}
        <div style={{margin:'18px 0',padding:'16px 18px',borderRadius:14,border:'1px solid '+(o.eval2w==='pass'?'#cdeacf':o.eval2w==='fail'?'var(--red-100)':'var(--gold-200)'),
          background:o.eval2w==='pass'?'var(--green-bg)':o.eval2w==='fail'?'var(--red-50)':'var(--gold-50)'}}>
          <div className="between">
            <div style={{display:'flex',alignItems:'center',gap:11}}>
              <div style={{width:34,height:34,borderRadius:10,background:'#fff',display:'grid',placeItems:'center',color:'var(--gold-600)'}}><Icon name="checkCircle" size={19}/></div>
              <div>
                <div style={{fontWeight:700,fontSize:13.5}}>Mốc đánh giá sau 2 tuần</div>
                <div className="muted" style={{fontSize:12}}>Đạt → cấp máy tính & vật dụng cơ bản · Không đạt → dừng thử việc</div>
              </div>
            </div>
            {o.eval2w==='pending'
              ? <div style={{display:'flex',gap:8}}><button className="btn btn-ghost btn-sm" onClick={()=>passEval2w(false)}>Không đạt</button><button className="btn btn-primary btn-sm" onClick={()=>passEval2w(true)} disabled={!introDone} style={!introDone?{opacity:.5,cursor:'not-allowed'}:null}><Icon name="check" size={14}/>Đạt</button></div>
              : <Badge kind={o.eval2w==='pass'?'green':'red'} dot>{o.eval2w==='pass'?'Đã đạt':'Không đạt'}</Badge>}
          </div>
          {o.eval2w==='pending' && !introDone && <div className="faint" style={{fontSize:11.5,marginTop:8}}>* Hoàn tất checklist hội nhập trước khi đánh giá.</div>}
        </div>

        {/* Cấp thiết bị — chỉ mở sau khi đạt */}
        {o.eval2w==='pass' && (
          <OnbSection num="2" color="#D9A400" title="Cấp máy tính & vật dụng" badge={equipDone?'done':'doing'}>
            {ONB_EQUIP.map(t=>(
              <CheckItem key={t.id} checked={o.equip[t.id]} label={t.label} onToggle={()=>toggleEquip(t.id)}/>
            ))}
          </OnbSection>
        )}

        {/* Mốc training */}
        {(o.eval2w==='pass') && (
          <OnbSection num="3" color="#0F766E" title="Đào tạo chuyên môn (tuần 2 → 2 tháng)" badge={o.phase==='eval2m'?'done':'doing'}>
            <div style={{display:'flex',alignItems:'center',gap:11,padding:'4px 2px'}}>
              <Icon name="book" size={18} className="muted"/>
              <span style={{fontSize:13}} className="muted">Do <b style={{color:'var(--ink)'}}>{o.mentor}</b> phụ trách đào tạo & theo dõi tiến độ chuyên môn.</span>
            </div>
          </OnbSection>
        )}

        {/* Gate 2: Xét chính thức */}
        {o.eval2w==='pass' && (
          <div style={{marginTop:18,padding:'16px 18px',borderRadius:14,border:'1px solid '+(o.eval2m==='pass'?'#cdeacf':o.eval2m==='fail'?'var(--red-100)':'var(--border-strong)'),
            background:o.eval2m==='pass'?'var(--green-bg)':o.eval2m==='fail'?'var(--red-50)':'var(--surface-2)'}}>
            <div className="between">
              <div style={{display:'flex',alignItems:'center',gap:11}}>
                <div style={{width:34,height:34,borderRadius:10,background:'#fff',display:'grid',placeItems:'center',color:'var(--green)'}}><Icon name="award" size={19}/></div>
                <div>
                  <div style={{fontWeight:700,fontSize:13.5}}>Mốc xét lên chính thức (sau 2 tháng)</div>
                  <div className="muted" style={{fontSize:12}}>Đạt → ký HĐ lao động chính thức · cập nhật trạng thái nhân sự</div>
                </div>
              </div>
              {o.dayN < 60 && o.eval2m==='pending'
                ? <Badge kind="gray">Còn {60-o.dayN} ngày</Badge>
                : o.eval2m==='pending'
                  ? <div style={{display:'flex',gap:8}}><button className="btn btn-ghost btn-sm" onClick={()=>passEval2m(false)}>Chưa đạt</button><button className="btn btn-gold btn-sm" onClick={()=>passEval2m(true)}><Icon name="check" size={14}/>Lên chính thức</button></div>
                  : <Badge kind={o.eval2m==='pass'?'green':'red'} dot>{o.eval2m==='pass'?'Đã lên chính thức':'Chưa đạt'}</Badge>}
            </div>
            {o.eval2m==='pass' && <div style={{marginTop:10,fontSize:12.5,color:'var(--green)',fontWeight:600,display:'flex',alignItems:'center',gap:7}}><Icon name="checkCircle" size={15}/>Đã tạo HĐ lao động chính thức · chuyển trạng thái sang “Chính thức”.</div>}
          </div>
        )}
      </div>
    </Modal>
  );
}

function OnbSection({ num, color, title, badge, children }) {
  return (
    <div style={{marginBottom:6}}>
      <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:10}}>
        <span style={{width:24,height:24,borderRadius:7,background:color+'1a',color:color,display:'grid',placeItems:'center',fontWeight:800,fontSize:12}}>{num}</span>
        <span style={{fontWeight:700,fontSize:14}}>{title}</span>
        {badge==='done' && <Badge kind="green" dot>Hoàn tất</Badge>}
        {badge==='doing' && <Badge kind="gray">Đang thực hiện</Badge>}
      </div>
      <div style={{display:'flex',flexDirection:'column',gap:2,paddingLeft:4}}>{children}</div>
    </div>
  );
}

function CheckItem({ checked, label, onToggle }) {
  return (
    <button onClick={onToggle} style={{display:'flex',alignItems:'center',gap:11,padding:'9px 8px',width:'100%',textAlign:'left',borderRadius:9,transition:'background .12s'}}
      onMouseEnter={e=>e.currentTarget.style.background='var(--surface-2)'}
      onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
      <span style={{width:21,height:21,borderRadius:7,flexShrink:0,display:'grid',placeItems:'center',transition:'all .15s',
        background:checked?'var(--green)':'#fff', border:'1.5px solid '+(checked?'var(--green)':'var(--border-strong)'), color:'#fff'}}>
        {checked && <Icon name="check" size={14} stroke={3}/>}
      </span>
      <span style={{fontSize:13,fontWeight:500,color:checked?'var(--muted)':'var(--ink)',textDecoration:checked?'line-through':'none'}}>{label}</span>
    </button>
  );
}

Object.assign(window, { Onboarding, OnboardingModal, OnbSection, CheckItem });
