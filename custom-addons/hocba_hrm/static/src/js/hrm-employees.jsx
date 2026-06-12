/* ============================================================
   HOC BA HRM — Nhân viên (dữ liệu THẬT từ hocba_employees
   qua /hocba-hrm/api/*; các màn khác vẫn chạy mock)
   ============================================================ */

const HB_AV = ['av-a','av-b','av-c','av-d','av-e','av-f'];
function hbInitials(name){
  const p = (name||'').trim().split(/\s+/);
  return ((p[p.length-2]?.[0]||'') + (p[p.length-1]?.[0]||'')).toUpperCase();
}
function hbAvCls(id){ return HB_AV[(id||0) % HB_AV.length]; }
function hbVND(n){ return (n||0).toLocaleString('vi-VN'); }
function fmtDate(s){ if(!s||s==='—')return '—'; const [y,m,d]=s.split('-'); return `${d}/${m}/${y}`; }
function hbStatusKind(key){
  return ({ probation:'amber', official:'green', intern:'blue', parttime:'violet',
    ctv:'violet', advisor:'teal', exiting:'red', resigned:'gray' })[key] || 'gray';
}
function hbTypeKind(t){ return ({Offline:'teal',Online:'blue',CTV:'violet'})[t]||'gray'; }
const HB_RESULT = { draft:['Chưa đánh giá','gray'], pass:['Đạt','green'], fail:['Không đạt','red'] };
const HB_CERT = { valid:['Còn hạn','green'], expiring:['Sắp hết hạn','amber'], expired:['Hết hạn','red'], none:['—','gray'] };

function hbGet(url){
  return fetch(url, {credentials:'same-origin'}).then(r=>{
    if(!r.ok) throw new Error('HTTP '+r.status);
    return r.json();
  });
}

function HbAvatar({ emp, size=34 }){
  if (emp.hasImg) return (
    <img src={`/web/image/hr.employee/${emp.id}/avatar_128`} alt=""
      style={{width:size,height:size,borderRadius:'50%',objectFit:'cover',flexShrink:0}}/>
  );
  return <div className={'av '+hbAvCls(emp.id)} style={{width:size,height:size,fontSize:size*0.36}}>{hbInitials(emp.name)}</div>;
}

/* ---------------- Danh sách ---------------- */
function Employees({ search }) {
  const [data, setData] = React.useState(null);
  const [err, setErr]   = React.useState(null);
  const [dep, setDep]       = React.useState('all');
  const [status, setStatus] = React.useState('all');
  const [type, setType]     = React.useState('all');
  const [sel, setSel]       = React.useState(null);
  const [vmode, setVmode]   = React.useState('table');

  const load = () => { setErr(null); setData(null);
    hbGet('/hocba-hrm/api/employees').then(setData).catch(e=>setErr(e.message)); };
  React.useEffect(load, []);

  if (err) return (
    <div className="content fade-in">
      <div className="empty">Không tải được dữ liệu nhân sự ({err}).{' '}
        <button className="btn btn-ghost" onClick={load}>Thử lại</button></div>
    </div>
  );
  if (!data) return <div className="content fade-in"><div className="empty">Đang tải dữ liệu nhân sự…</div></div>;

  const emps = data.employees, deps = data.departments;
  const statusOptions = [...new Map(emps.map(e=>[e.statusKey, e.status])).entries()];
  const typeOptions = [...new Set(emps.map(e=>e.type))].filter(t=>t&&t!=='—');

  const filtered = emps.filter(e=>{
    if (dep!=='all' && e.dep!==dep) return false;
    if (status!=='all' && e.statusKey!==status) return false;
    if (type!=='all' && e.type!==type) return false;
    if (search){ const q=search.toLowerCase();
      if (!((e.name||'').toLowerCase().includes(q)||(e.code||'').toLowerCase().includes(q)
        ||(e.jobTitle||'').toLowerCase().includes(q)||(e.depName||'').toLowerCase().includes(q))) return false; }
    return true;
  });

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhân viên</h1>
          <p>{emps.length} nhân sự · {deps.length} phòng ban · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost" onClick={()=>window.open('/odoo/employees','_blank')}>
            <Icon name="settings" size={16}/>Mở Odoo backend</button>
          <button className="btn btn-primary" onClick={()=>window.open('/odoo/employees/new','_blank')}>
            <Icon name="plus" size={16}/>Thêm nhân viên</button>
        </div>
      </div>

      {/* Filter chips theo phòng ban (số liệu thật) */}
      <div className="filterbar">
        <button className={'chip'+(dep==='all'?' active':'')} onClick={()=>setDep('all')}>
          Tất cả <span className="ct">{emps.length}</span></button>
        {deps.map(d=>(
          <button key={d.id} className={'chip'+(dep===d.id?' active':'')} onClick={()=>setDep(d.id)}>
            {d.name} <span className="ct">{d.total}</span></button>
        ))}
        <div style={{marginLeft:'auto',display:'flex',gap:9,alignItems:'center'}}>
          <select className="sel" value={status} onChange={e=>setStatus(e.target.value)}>
            <option value="all">Mọi trạng thái</option>
            {statusOptions.map(([k,l])=><option key={k} value={k}>{l}</option>)}
          </select>
          <select className="sel" value={type} onChange={e=>setType(e.target.value)}>
            <option value="all">Mọi hình thức</option>
            {typeOptions.map(t=><option key={t}>{t}</option>)}
          </select>
          <div className="seg">
            <button className={vmode==='table'?'active':''} onClick={()=>setVmode('table')}>Bảng</button>
            <button className={vmode==='grid'?'active':''} onClick={()=>setVmode('grid')}>Thẻ</button>
          </div>
        </div>
      </div>

      {vmode==='table' ? (
        <div className="card">
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Nhân viên</th><th>Phòng ban</th><th>Chức danh</th><th>Hình thức</th>
                <th>Trạng thái</th><th>Ngày vào</th>
                {data.isHrManager && <th className="tbl-num">Lương CB</th>}
                <th></th>
              </tr></thead>
              <tbody>
                {filtered.map(e=>(
                  <tr key={e.id} onClick={()=>setSel(e)}>
                    <td>
                      <div className="cell-emp">
                        <HbAvatar emp={e}/>
                        <div>
                          <div className="nm">{e.name}</div>
                          <div className="id">{e.code} · {e.jobTitle}</div>
                        </div>
                      </div>
                    </td>
                    <td><span style={{display:'inline-flex',alignItems:'center',gap:7}}>
                      <span style={{width:8,height:8,borderRadius:3,background:(deps.find(d=>d.id===e.dep)||{}).color||'var(--border-strong)'}}></span>
                      {e.depName}</span></td>
                    <td>{e.jobTitle}{e.posType && <span className="badge badge-gray" style={{marginLeft:6}}>{e.posType}</span>}</td>
                    <td><Badge kind={hbTypeKind(e.type)}>{e.type}</Badge></td>
                    <td><Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge></td>
                    <td className="muted mono">{fmtDate(e.start)}</td>
                    {data.isHrManager && <td className="tbl-num mono" style={{fontWeight:600}}>{e.wage?hbVND(e.wage):'—'}</td>}
                    <td><button className="icon-btn" onClick={ev=>{ev.stopPropagation();setSel(e);}}><Icon name="chevR" size={18} className="faint"/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length===0 && <div className="empty">Không tìm thấy nhân viên phù hợp.</div>}
        </div>
      ) : (
        <div className="grid-3" style={{gridTemplateColumns:'repeat(auto-fill,minmax(260px,1fr))'}}>
          {filtered.map(e=>(
            <div key={e.id} className="card" style={{padding:18,cursor:'pointer'}} onClick={()=>setSel(e)}>
              <div style={{display:'flex',gap:13,alignItems:'center'}}>
                <HbAvatar emp={e} size={48}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontWeight:700,fontSize:14}}>{e.name}</div>
                  <div className="muted" style={{fontSize:12}}>{e.code} · {e.jobTitle}</div>
                </div>
              </div>
              <div className="divider" style={{margin:'14px 0'}}></div>
              <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
                <Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge>
                <Badge kind={hbTypeKind(e.type)}>{e.type}</Badge>
                <Badge kind="gray">{e.depName}</Badge>
              </div>
            </div>
          ))}
          {filtered.length===0 && <div className="empty">Không tìm thấy nhân viên phù hợp.</div>}
        </div>
      )}

      {sel && <EmployeeDrawer emp={sel} onClose={()=>setSel(null)} isHr={data.isHr} isMgr={data.isHrManager}/>}
    </div>
  );
}

/* ---------------- Hồ sơ chi tiết ---------------- */
function EmployeeDrawer({ emp, onClose, isHr, isMgr }) {
  const [tab, setTab] = React.useState('info');
  const [det, setDet] = React.useState(null);
  const [derr, setDerr] = React.useState(null);
  React.useEffect(()=>{
    hbGet('/hocba-hrm/api/employee/'+emp.id).then(setDet).catch(e=>setDerr(e.message));
  }, [emp.id]);

  const tabs = [
    ['info','Thông tin'],
    ['probation','Thử việc'],
    ['assets', det ? `Tài sản (${det.assets.length})` : 'Tài sản'],
    ['promo', det ? `Thăng tiến (${det.promotions.length})` : 'Thăng tiến'],
  ];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--red-50),#fff)'}}>
        <HbAvatar emp={emp} size={62}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <h2 style={{margin:0,fontSize:21,fontWeight:800,letterSpacing:'-.4px'}}>{emp.name}</h2>
            <Badge kind={hbStatusKind(emp.statusKey)} dot>{emp.status}</Badge>
          </div>
          <div className="muted" style={{fontSize:13.5,marginTop:3}}>{emp.code} · {emp.jobTitle} · {emp.depName}</div>
          <div style={{display:'flex',gap:14,marginTop:10}}>
            {emp.email && <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="mail" size={15}/>{emp.email}</span>}
            {emp.phone && <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="phone" size={15}/>{emp.phone}</span>}
          </div>
        </div>
        <div className="modal-x" style={{display:'flex',gap:8}}>
          <button className="btn btn-ghost btn-sm" onClick={()=>window.open('/odoo/employees/'+emp.id,'_blank')}>
            <Icon name="edit" size={15}/>Sửa trong Odoo</button>
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
        </div>
      </div>

      <div style={{padding:'0 24px'}}>
        <div className="tabs" style={{marginBottom:0}}>
          {tabs.map(([id,l])=>(
            <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{padding:'22px 24px',maxHeight:'52vh',overflowY:'auto'}}>
        {derr && <div className="empty">Không tải được hồ sơ ({derr}).</div>}
        {!det && !derr && <div className="empty">Đang tải hồ sơ…</div>}
        {det && tab==='info'      && <HbInfoTab det={det} isHr={isHr} isMgr={isMgr}/>}
        {det && tab==='probation' && <HbProbationTab det={det}/>}
        {det && tab==='assets'    && <HbAssetsTab det={det}/>}
        {det && tab==='promo'     && <HbPromoTab det={det} isMgr={isMgr}/>}
      </div>
    </Modal>
  );
}

function HbInfoTab({ det, isHr, isMgr }) {
  const rows = [
    ['Mã nhân sự', det.code], ['Họ và tên', det.name],
    ['Phòng ban', det.depName], ['Chức danh', det.jobTitle],
    ['Loại vị trí', det.posType||'—'], ['Hình thức', det.type],
    ['Tình trạng', det.status], ['Ngày vào làm', fmtDate(det.start)],
    ['Email công ty', det.email||'—'], ['Điện thoại', det.phone||'—'],
  ];
  if (isHr) rows.push(
    ['Ngày sinh', fmtDate(det.bday)],
    ['CCCD', det.cccd||'—'],
    ['Ngày cấp CCCD', fmtDate(det.idIssue)], ['Nơi cấp', det.idPlace||'—'],
    ['Số thẻ BHYT', det.hi||'—'], ['Nơi KCB ban đầu', det.hiPlace||'—'],
    ['Địa chỉ thường trú', det.permanentAddr||'—'], ['Địa chỉ tạm trú', det.currentAddr||'—'],
  );
  if (isMgr) rows.push(['MST TNCN', det.pit||'—'], ['Số sổ BHXH', det.si||'—']);
  return (
    <div>
      <div className="grid-2" style={{rowGap:20}}>
        {rows.map(([k,v],i)=>(
          <div className="kv" key={i}><div className="k">{k}</div><div className="v">{v||'—'}</div></div>
        ))}
      </div>
      {isHr && det.dependents && det.dependents.length>0 && (
        <div style={{marginTop:22}}>
          <div style={{fontWeight:700,fontSize:13,marginBottom:8}}>Người phụ thuộc ({det.dependents.length})</div>
          <div className="card" style={{padding:0}}>
            <table className="tbl"><thead><tr><th>Họ tên</th><th>Quan hệ</th><th>Ngày sinh</th><th>Giảm trừ từ</th><th>Đến</th></tr></thead>
              <tbody>{det.dependents.map((d,i)=>(
                <tr key={i} style={{cursor:'default'}}>
                  <td>{d.name}</td><td>{d.relationship}</td>
                  <td className="mono">{fmtDate(d.birthday)}</td>
                  <td className="mono">{fmtDate(d.from)}</td>
                  <td className="mono">{d.to?fmtDate(d.to):'—'}</td>
                </tr>))}</tbody>
            </table>
          </div>
        </div>
      )}
      {isHr && det.certs && det.certs.length>0 && (
        <div style={{marginTop:22}}>
          <div style={{fontWeight:700,fontSize:13,marginBottom:8}}>Chứng chỉ ({det.certs.length})</div>
          <div className="card" style={{padding:0}}>
            <table className="tbl"><thead><tr><th>Kỹ năng</th><th>Cấp độ</th><th>Ngày cấp</th><th>Hết hạn</th><th>Trạng thái</th><th>Xác minh</th></tr></thead>
              <tbody>{det.certs.map((c,i)=>{
                const [lbl,kind] = HB_CERT[c.status]||HB_CERT.none;
                return (
                <tr key={i} style={{cursor:'default'}}>
                  <td>{c.skill}</td><td>{c.level}</td>
                  <td className="mono">{fmtDate(c.date)}</td>
                  <td className="mono">{c.expiry?fmtDate(c.expiry):'—'}</td>
                  <td><Badge kind={kind} dot>{lbl}</Badge></td>
                  <td>{c.verified?<Badge kind="green">Đã xác minh</Badge>:<Badge kind="gray">Chưa</Badge>}</td>
                </tr>);})}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* Timeline thử việc 5 điểm (Nhóm B) + thử giảng (Nhóm A) */
function HbProbationTab({ det }) {
  const p = det.probation || {};
  const steps = [
    ['Thử việc', p.start?'done':'pending', fmtDate(p.start)],
    ['ĐG tuần-2', p.d2wResult==='pass'?'done':p.d2wResult==='fail'?'fail':'pending',
      p.d2wDate?fmtDate(p.d2wDate):(p.d2wDue?'hạn '+fmtDate(p.d2wDue):'')],
    ['Cấp thiết bị', p.equipDate?'done':'pending', p.equipDate?fmtDate(p.equipDate):''],
    ['ĐG tháng-2', p.d2mResult==='pass'?'done':p.d2mResult==='fail'?'fail':'pending',
      p.d2mDate?fmtDate(p.d2mDate):(p.d2mDue?'hạn '+fmtDate(p.d2mDue):'')],
    ['Chính thức', p.officialDate?'done':'pending', p.officialDate?fmtDate(p.officialDate):''],
  ];
  const col = s => s==='done'?'var(--green)':s==='fail'?'var(--red-600)':'var(--border-strong)';
  return (
    <div>
      {p.isGroupB ? (
        <div>
          <div className="card" style={{padding:'20px 18px 14px',marginBottom:18}}>
            <div style={{display:'flex',alignItems:'flex-start'}}>
              {steps.map(([lbl,st,sub],i)=>(
                <React.Fragment key={i}>
                  {i>0 && <div style={{flex:1,height:3,background:col(st),margin:'7px 4px 0',borderRadius:2,minWidth:18}}></div>}
                  <div style={{display:'flex',flexDirection:'column',alignItems:'center',width:86}}>
                    <div style={{width:17,height:17,borderRadius:'50%',background:col(st),
                      display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontSize:10,fontWeight:800}}>
                      {st==='done'?'✓':st==='fail'?'✗':i+1}
                    </div>
                    <div style={{fontSize:11.5,fontWeight:700,marginTop:6,textAlign:'center'}}>{lbl}</div>
                    {sub && <div className="faint" style={{fontSize:10.5,marginTop:2,textAlign:'center'}}>{sub}</div>}
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>
          <div className="grid-2">
            <div className="card" style={{padding:16}}>
              <div className="between" style={{marginBottom:10}}>
                <span style={{fontWeight:700,fontSize:13}}>Cổng tuần-2 · cấp thiết bị</span>
                <Badge kind={HB_RESULT[p.d2wResult][1]} dot>{HB_RESULT[p.d2wResult][0]}</Badge>
              </div>
              <div className="kv" style={{marginBottom:8}}><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2wDue)}</div></div>
              <div className="kv" style={{marginBottom:8}}><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2wDate)}</div></div>
              <div className="kv"><div className="k">Ghi chú</div><div className="v">{p.d2wNote||'—'}</div></div>
            </div>
            <div className="card" style={{padding:16}}>
              <div className="between" style={{marginBottom:10}}>
                <span style={{fontWeight:700,fontSize:13}}>Cổng tháng-2 · lên chính thức</span>
                <Badge kind={HB_RESULT[p.d2mResult][1]} dot>{HB_RESULT[p.d2mResult][0]}</Badge>
              </div>
              <div className="kv" style={{marginBottom:8}}><div className="k">Hạn đánh giá</div><div className="v mono">{fmtDate(p.d2mDue)}</div></div>
              <div className="kv" style={{marginBottom:8}}><div className="k">Ngày đánh giá</div><div className="v mono">{fmtDate(p.d2mDate)}</div></div>
              <div className="kv"><div className="k">Ghi chú</div><div className="v">{p.d2mNote||'—'}</div></div>
            </div>
          </div>
          {p.officialDate && (
            <div style={{marginTop:14,padding:'12px 16px',background:'var(--surface-2)',border:'1px solid var(--border)',borderRadius:11,fontSize:13}}>
              Chính thức từ <b>{fmtDate(p.officialDate)}</b> · {p.officialMonths} tháng
            </div>
          )}
        </div>
      ) : !det.trial ? (
        <div className="empty">Nhân sự này không thuộc luồng thử việc 2 cổng (Nhóm B).</div>
      ) : null}

      {det.trial && (
        <div style={{marginTop:p.isGroupB?18:0}}>
          <div className="card" style={{padding:16}}>
            <div className="between" style={{marginBottom:12}}>
              <span style={{fontWeight:700,fontSize:13}}>Đánh giá thử giảng (Nhóm A — giảng viên)</span>
              <Badge kind={HB_RESULT[det.trial.result][1]} dot>{HB_RESULT[det.trial.result][0]}</Badge>
            </div>
            <div className="grid-2" style={{rowGap:14}}>
              <div className="kv"><div className="k">Ngày thử giảng</div><div className="v mono">{fmtDate(det.trial.date)}</div></div>
              <div className="kv"><div className="k">Lớp</div><div className="v">{det.trial.class||'—'}</div></div>
              <div className="kv"><div className="k">Điểm phương pháp</div><div className="v mono">{det.trial.scoreMethod||'—'} / 10</div></div>
              <div className="kv"><div className="k">Điểm chuyên môn</div><div className="v mono">{det.trial.scoreContent||'—'} / 10</div></div>
            </div>
            {det.trial.note && <div style={{marginTop:12,fontSize:12.5}} className="muted">{det.trial.note}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

function HbAssetsTab({ det }) {
  if (!det.assets.length) return <div className="empty">Chưa có tài sản cấp phát.</div>;
  const kind = s => s==='assigned'?'green':s==='transferred'?'blue':'gray';
  return (
    <div className="card" style={{padding:0}}>
      <table className="tbl">
        <thead><tr><th>Mã tài sản</th><th>Loại</th><th>Ngày cấp</th><th>Trạng thái</th><th>Ngày thu hồi</th></tr></thead>
        <tbody>{det.assets.map(a=>(
          <tr key={a.id} style={{cursor:'default'}}>
            <td className="mono" style={{fontWeight:600}}>{a.code}</td>
            <td>{a.type}</td>
            <td className="mono">{fmtDate(a.grant)}</td>
            <td><Badge kind={kind(a.state)} dot>{a.stateLabel}</Badge></td>
            <td className="mono">{a.returnDate?fmtDate(a.returnDate):'—'}</td>
          </tr>))}</tbody>
      </table>
    </div>
  );
}

function HbPromoTab({ det, isMgr }) {
  if (!det.promotions.length) return <div className="empty">Chưa có lịch sử thăng tiến.</div>;
  const path = det.promotions;
  return (
    <div style={{position:'relative',paddingLeft:8}}>
      {path.map((p,i)=>{
        const last = i===path.length-1;
        const delta = isMgr && p.toWage>p.fromWage ? p.toWage-p.fromWage : 0;
        return (
          <div key={i} style={{display:'flex',gap:16,paddingBottom:last?0:18,position:'relative'}}>
            <div style={{display:'flex',flexDirection:'column',alignItems:'center'}}>
              <div style={{width:14,height:14,borderRadius:'50%',background:last?'var(--red-600)':'var(--gold-500)',
                border:'3px solid #fff',boxShadow:'0 0 0 2px '+(last?'var(--red-100)':'var(--gold-200)'),zIndex:1}}></div>
              {!last && <div style={{width:2,flex:1,background:'var(--border-strong)',marginTop:2}}></div>}
            </div>
            <div style={{flex:1}}>
              <div className="between">
                <div style={{display:'flex',alignItems:'center',gap:9,flexWrap:'wrap'}}>
                  <span style={{fontWeight:700,fontSize:13.5}}>{p.fromJob} → {p.toJob}</span>
                  {p.dept && <Badge kind="gray">{p.dept}</Badge>}
                  {delta>0 && <span className="badge badge-gold"><Icon name="arrowUp" size={11}/>+{hbVND(delta)}</span>}
                </div>
                <span className="mono muted" style={{fontSize:12.5}}>{fmtDate(p.date)}</span>
              </div>
              <div style={{display:'flex',gap:12,alignItems:'center',marginTop:5,flexWrap:'wrap'}}>
                {isMgr && p.toWage>0 && <span className="mono" style={{fontWeight:800,fontSize:13.5,color:'var(--green)'}}>{hbVND(p.toWage)} ₫</span>}
                {p.ref && <span className="faint" style={{fontSize:12}}>QĐ: {p.ref}</span>}
                {p.reason && <span className="faint" style={{fontSize:12}}>{p.reason}</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function MiniStat({ lbl, val, col }) {
  return (
    <div style={{padding:'13px 15px',border:'1px solid var(--border)',borderRadius:12,background:'var(--surface-2)'}}>
      <div className="k" style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.4px',color:'var(--faint)',fontWeight:700}}>{lbl}</div>
      <div style={{fontSize:18,fontWeight:800,color:col,marginTop:4,fontVariantNumeric:'tabular-nums'}}>{val}</div>
    </div>
  );
}

Object.assign(window, { Employees, EmployeeDrawer, MiniStat, fmtDate });
