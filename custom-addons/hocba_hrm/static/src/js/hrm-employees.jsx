/* ============================================================
   HOC BA HRM — Nhân viên (danh sách + hồ sơ chi tiết)
   ============================================================ */

function Employees({ search }) {
  const [dep, setDep] = useState('all');
  const [status, setStatus] = useState('all');
  const [type, setType] = useState('all');
  const [sel, setSel] = useState(null);
  const [vmode, setVmode] = useState('table');

  const filtered = useMemo(()=> EMPLOYEES.filter(e=>{
    if (dep!=='all' && e.dep!==dep) return false;
    if (status!=='all' && e.status!==status) return false;
    if (type!=='all' && e.type!==type) return false;
    if (search){ const q=search.toLowerCase();
      if (!(e.name.toLowerCase().includes(q)||e.code.toLowerCase().includes(q)||e.jobTitle.toLowerCase().includes(q)||e.depName.toLowerCase().includes(q))) return false; }
    return true;
  }), [dep,status,type,search]);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhân viên</h1>
          <p>{EMPLOYEES.length} nhân sự · 6 phòng ban · cập nhật T5/2026</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Import / Export</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Thêm nhân viên</button>
        </div>
      </div>

      {/* Filter chips theo phòng ban */}
      <div className="filterbar">
        <button className={'chip'+(dep==='all'?' active':'')} onClick={()=>setDep('all')}>Tất cả <span className="ct">{EMPLOYEES.length}</span></button>
        {DEPARTMENTS.map(d=>(
          <button key={d.id} className={'chip'+(dep===d.id?' active':'')} onClick={()=>setDep(d.id)}>{d.name} <span className="ct">{d.total}</span></button>
        ))}
        <div style={{marginLeft:'auto',display:'flex',gap:9,alignItems:'center'}}>
          <select className="sel" value={status} onChange={e=>setStatus(e.target.value)}>
            <option value="all">Mọi trạng thái</option>
            <option>Chính thức</option><option>Thử việc</option>
          </select>
          <select className="sel" value={type} onChange={e=>setType(e.target.value)}>
            <option value="all">Mọi hình thức</option>
            <option>Offline</option><option>Online</option><option>CTV</option>
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
                <th>Trạng thái</th><th>Ngày vào</th><th className="tbl-num">Lương CB</th><th></th>
              </tr></thead>
              <tbody>
                {filtered.map(e=>(
                  <tr key={e.id} onClick={()=>setSel(e)}>
                    <td><EmpCell emp={e}/></td>
                    <td><span style={{display:'inline-flex',alignItems:'center',gap:7}}><span style={{width:8,height:8,borderRadius:3,background:DEPARTMENTS.find(d=>d.id===e.dep).color}}></span>{e.depName}</span></td>
                    <td>{e.jobTitle}{e.level!=null && <span className="badge badge-gold" style={{marginLeft:6}}>Lv {e.level}</span>}</td>
                    <td><Badge kind={typeBadge(e.type)}>{e.type}</Badge></td>
                    <td><Badge kind={statusBadge(e.status)} dot>{e.status}</Badge></td>
                    <td className="muted mono">{fmtDate(e.start)}</td>
                    <td className="tbl-num mono" style={{fontWeight:600}}>{fmtVND(e.wage)}</td>
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
                <Avatar emp={e} size={48}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontWeight:700,fontSize:14}}>{e.name}</div>
                  <div className="muted" style={{fontSize:12}}>{e.code} · {e.jobTitle}</div>
                </div>
              </div>
              <div className="divider" style={{margin:'14px 0'}}></div>
              <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
                <Badge kind={statusBadge(e.status)} dot>{e.status}</Badge>
                <Badge kind={typeBadge(e.type)}>{e.type}</Badge>
                <Badge kind="gray">{e.depShort}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      {sel && <EmployeeDrawer emp={sel} onClose={()=>setSel(null)}/>}
    </div>
  );
}

function EmployeeDrawer({ emp, onClose }) {
  const [tab, setTab] = useState('info');
  const dep = DEPARTMENTS.find(d=>d.id===emp.dep);
  const pay = PAYROLL.find(p=>p.id===emp.id);
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--red-50),#fff)'}}>
        <Avatar emp={emp} size={62}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <h2 style={{margin:0,fontSize:21,fontWeight:800,letterSpacing:'-.4px'}}>{emp.name}</h2>
            <Badge kind={statusBadge(emp.status)} dot>{emp.status}</Badge>
          </div>
          <div className="muted" style={{fontSize:13.5,marginTop:3}}>{emp.code} · {emp.jobTitle} · {dep.name}</div>
          <div style={{display:'flex',gap:14,marginTop:10}}>
            <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="mail" size={15}/>{emp.email}</span>
            <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="phone" size={15}/>{emp.phone}</span>
          </div>
        </div>
        <div className="modal-x" style={{display:'flex',gap:8}}>
          <button className="btn btn-ghost btn-sm"><Icon name="edit" size={15}/>Sửa</button>
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
        </div>
      </div>

      <div style={{padding:'0 24px'}}>
        <div className="tabs" style={{marginBottom:0}}>
          {[['info','Thông tin'],['contract','Hợp đồng & Lương'],['journey','Lộ trình thăng tiến'],['equip','Tài sản'],['attend','Chấm công']].map(([id,l])=>(
            <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{padding:'22px 24px',maxHeight:'52vh',overflowY:'auto'}}>
        {tab==='info' && (
          <div className="grid-2" style={{rowGap:20}}>
            {[
              ['Mã nhân viên',emp.code],['Họ và tên',emp.name],
              ['Ngày sinh',fmtDate(emp.bday)],['CCCD',emp.cccd],
              ['Phòng ban',dep.name],['Chức danh',emp.jobTitle],
              ['Hình thức',emp.type],['Ngày vào làm',fmtDate(emp.start)],
              ['Email công ty',emp.email],['Điện thoại',emp.phone],
              ['Ngân hàng',emp.bank],['Số tài khoản',emp.acct],
            ].map(([k,v],i)=>(
              <div className="kv" key={i}><div className="k">{k}</div><div className="v">{v}</div></div>
            ))}
          </div>
        )}
        {tab==='contract' && pay && (
          <div>
            <div className="grid-3" style={{marginBottom:18}}>
              <MiniStat lbl="Lương cơ bản" val={fmtVND(emp.wage)+' ₫'} col="var(--ink)"/>
              <MiniStat lbl="Tổng thu nhập T5" val={fmtVND(pay.gross)+' ₫'} col="var(--blue)"/>
              <MiniStat lbl="Thực lãnh T5" val={fmtVND(pay.net)+' ₫'} col="var(--green)"/>
            </div>
            <div className="card" style={{padding:0}}>
              <div className="card-head"><h3 style={{fontSize:13.5}}>Loại hợp đồng</h3><span className="badge badge-blue" style={{marginLeft:'auto'}}>{emp.status==='Thử việc'?'HĐ thử việc 2 tháng':'HĐ lao động 12 tháng'}</span></div>
              <div className="card-pad grid-2" style={{rowGap:16}}>
                <div className="kv"><div className="k">Ngày ký</div><div className="v">{fmtDate(emp.start)}</div></div>
                <div className="kv"><div className="k">Ngày hết hạn</div><div className="v">{emp.status==='Thử việc'?'—':addYear(emp.start)}</div></div>
                <div className="kv"><div className="k">Mức đóng BHXH</div><div className="v">{fmtVND(Math.min(Math.max(emp.wage,5100000),7300000))} ₫</div></div>
                <div className="kv"><div className="k">Số lần ký</div><div className="v">{emp.status==='Thử việc'?'1':'2'}</div></div>
              </div>
            </div>
            {emp.level!=null && (
              <div style={{marginTop:14,padding:'13px 16px',background:'var(--gold-50)',borderRadius:12,border:'1px solid var(--gold-200)',display:'flex',alignItems:'center',gap:12}}>
                <Icon name="target" size={22} className="" />
                <div><div style={{fontWeight:700,fontSize:13}}>Vị trí TVTS — Level {emp.level}</div><div className="muted" style={{fontSize:12}}>COM {KPI_LEVELS.reduce((p,c)=>Math.abs(c.lv-emp.level)<Math.abs(p.lv-emp.level)?c:p).com}% · áp dụng bảng KPI Level 0–10</div></div>
              </div>
            )}
          </div>
        )}
        {tab==='journey' && <SalaryJourney emp={emp}/>}
        {tab==='equip' && (
          <div>
            <p className="muted" style={{marginTop:0,fontSize:13}}>Tài sản công ty cấp phát {emp.type==='Offline'?'(nhân sự tại văn phòng)':'(làm việc từ xa)'}:</p>
            <div className="grid-3">
              {(emp.type==='Offline'
                ? ['Màn hình','CPU','Bàn phím','Chuột','Tai nghe','Ghế công thái học']
                : ['Laptop cá nhân','Tài khoản phần mềm']).map((it,i)=>(
                <div key={i} style={{padding:'14px 16px',border:'1px solid var(--border)',borderRadius:11,display:'flex',alignItems:'center',gap:10}}>
                  <span style={{width:8,height:8,borderRadius:'50%',background:'var(--green)'}}></span>
                  <span style={{fontSize:13,fontWeight:500}}>{it}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {tab==='attend' && (
          <div>
            <div className="grid-3" style={{marginBottom:16}}>
              <MiniStat lbl="Công chuẩn T5" val="22 ngày" col="var(--ink)"/>
              <MiniStat lbl="Công thực tế" val={(pay?pay.workDays:22)+' ngày'} col="var(--green)"/>
              <MiniStat lbl="Phép còn lại" val="8.5 ngày" col="var(--blue)"/>
            </div>
            <div className="card" style={{padding:0}}>
              <table className="tbl"><thead><tr><th>Ngày</th><th>Check-in</th><th>Check-out</th><th>Trạng thái</th></tr></thead>
                <tbody>{['28/05 · Thứ 5','27/05 · Thứ 4','26/05 · Thứ 3','25/05 · Thứ 2','23/05 · Thứ 7'].map((d,i)=>(
                  <tr key={i} style={{cursor:'default'}}><td className="mono">{d}</td><td className="mono">{['08:12','08:45','09:02','08:21','08:33'][i]}</td><td className="mono">{['19:03','19:10','18:58','19:05','12:30'][i]}</td><td><Badge kind={['green','green','amber','green','blue'][i]} dot>{['Đúng giờ','Đúng giờ','Đi trễ','Đúng giờ','Nửa ngày'][i]}</Badge></td></tr>
                ))}</tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Modal>
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

function fmtDate(s){ if(!s||s==='—')return '—'; const [y,m,d]=s.split('-'); return `${d}/${m}/${y}`; }
function addYear(s){ const [y,m,d]=s.split('-'); return `${d}/${m}/${+y+1}`; }

Object.assign(window, { Employees, EmployeeDrawer, MiniStat, fmtDate });
