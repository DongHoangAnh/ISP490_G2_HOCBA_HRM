/* ============================================================
   HOC BA HRM — Hợp đồng lao động
   ============================================================ */

function Contracts({ search }) {
  const [typeF, setTypeF] = useState('all');
  const [onlyExp, setOnlyExp] = useState(false);
  const [sel, setSel] = useState(null);

  const visible = CONTRACTS.filter(c=>{
    if (typeF!=='all' && c.typeId!==typeF) return false;
    if (onlyExp && !c.expiring) return false;
    if (search){ const q=search.toLowerCase(); if(!(c.emp.name.toLowerCase().includes(q)||c.emp.code.toLowerCase().includes(q)||c.id.toLowerCase().includes(q))) return false; }
    return true;
  });

  const expiring = CONTRACTS.filter(c=>c.expiring).length;
  const trial = CONTRACTS.filter(c=>c.typeId==='trial').length;
  const perm = CONTRACTS.filter(c=>c.typeId==='perm').length;

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Hợp đồng lao động</h1>
          <p>{CONTRACTS.length} hợp đồng đang theo dõi · nhân sự offline · Odoo hr.contract</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Xuất danh sách</button>
          <button className="btn btn-primary"><Icon name="plus" size={16}/>Tạo hợp đồng</button>
        </div>
      </div>

      <div className="stat-grid">
        <MetricCard ico="file" col="var(--ink-soft)" bg="#F0EDE9" val={CONTRACTS.length} lbl="Tổng hợp đồng"/>
        <MetricCard ico="bell" col="var(--red-600)" bg="var(--red-50)" val={expiring} lbl="Sắp hết hạn (≤45 ngày)"/>
        <MetricCard ico="clock" col="var(--amber)" bg="var(--amber-bg)" val={trial} lbl="Đang thử việc"/>
        <MetricCard ico="checkCircle" col="var(--green)" bg="var(--green-bg)" val={perm} lbl="HĐ vô thời hạn"/>
      </div>

      {expiring>0 && (
        <div style={{display:'flex',alignItems:'center',gap:13,padding:'14px 18px',background:'var(--red-50)',border:'1px solid var(--red-100)',borderRadius:14,marginBottom:18}}>
          <div style={{width:38,height:38,borderRadius:11,background:'var(--red-600)',color:'#fff',display:'grid',placeItems:'center',flexShrink:0}}><Icon name="bell" size={19}/></div>
          <div style={{flex:1}}>
            <div style={{fontWeight:700,fontSize:13.5}}>{expiring} hợp đồng sắp hết hạn trong 45 ngày tới</div>
            <div className="muted" style={{fontSize:12.5}}>Cần lên kế hoạch phỏng vấn tái ký hoặc gia hạn trước khi hết hiệu lực.</div>
          </div>
          <button className={'chip'+(onlyExp?' active':'')} onClick={()=>setOnlyExp(v=>!v)}>{onlyExp?'Đang lọc':'Xem ngay'}</button>
        </div>
      )}

      <div className="filterbar">
        <button className={'chip'+(typeF==='all'?' active':'')} onClick={()=>{setTypeF('all');}}>Tất cả loại <span className="ct">{CONTRACTS.length}</span></button>
        {CONTRACT_TYPES.map(t=>{
          const c = CONTRACTS.filter(x=>x.typeId===t.id).length;
          return <button key={t.id} className={'chip'+(typeF===t.id?' active':'')} onClick={()=>setTypeF(t.id)}>{t.short} <span className="ct">{c}</span></button>;
        })}
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Mã HĐ</th><th>Loại hợp đồng</th><th>Ngày ký</th>
              <th>Ngày hết hạn</th><th className="tbl-num">Số lần ký</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {visible.map(c=>{
                const ct = CONTRACT_TYPES.find(t=>t.id===c.typeId);
                return (
                  <tr key={c.id} onClick={()=>setSel(c)}>
                    <td><EmpCell emp={c.emp}/></td>
                    <td className="mono muted">{c.id}</td>
                    <td><Badge kind={ct.kind}>{ct.short}</Badge></td>
                    <td className="mono muted">{fmtDate(c.signed)}</td>
                    <td className="mono">
                      {c.end ? (
                        <span style={{display:'inline-flex',alignItems:'center',gap:7}}>
                          {fmtDate(c.end)}
                          {c.expiring && <span className="badge badge-red" style={{fontSize:10.5}}>còn {c.daysLeft}d</span>}
                        </span>
                      ) : <span className="faint">Vô thời hạn</span>}
                    </td>
                    <td className="tbl-num mono">{c.renewals===0?'1':c.renewals+1}</td>
                    <td><Badge kind={c.state==='Thử việc'?'amber':'green'} dot>{c.state}</Badge></td>
                    <td><button className="icon-btn" onClick={e=>{e.stopPropagation();setSel(c);}}><Icon name="chevR" size={18} className="faint"/></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {visible.length===0 && <div className="empty">Không có hợp đồng phù hợp.</div>}
      </div>

      {sel && <ContractModal c={sel} onClose={()=>setSel(null)}/>}
    </div>
  );
}

function ContractModal({ c, onClose }) {
  const ct = CONTRACT_TYPES.find(t=>t.id===c.typeId);
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--teal-bg),#fff)'}}>
        <Avatar emp={c.emp} size={56}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',gap:10,alignItems:'center'}}>
            <h2 style={{margin:0,fontSize:20,fontWeight:800}}>{c.emp.name}</h2>
            <Badge kind={ct.kind}>{ct.name}</Badge>
          </div>
          <div className="muted" style={{fontSize:13,marginTop:3}}>{c.id} · {c.emp.code} · {c.emp.jobTitle} · {c.emp.depName}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'22px 24px',maxHeight:'58vh',overflowY:'auto'}}>
        <div className="grid-2" style={{rowGap:16,marginBottom:20}}>
          <div className="kv"><div className="k">Ngày ký hợp đồng</div><div className="v">{fmtDate(c.signed)}</div></div>
          <div className="kv"><div className="k">Ngày hết hạn</div><div className="v">{c.end?fmtDate(c.end):'Không xác định thời hạn'}</div></div>
          <div className="kv"><div className="k">Mức đóng BHXH</div><div className="v">{fmtVND(c.bhxhBase)} ₫</div></div>
          <div className="kv"><div className="k">Lương cơ bản hiện tại</div><div className="v">{fmtVND(c.emp.wage)} ₫</div></div>
        </div>

        {c.expiring && (
          <div style={{display:'flex',alignItems:'center',gap:11,padding:'12px 15px',background:'var(--red-50)',borderRadius:12,marginBottom:18,border:'1px solid var(--red-100)'}}>
            <Icon name="bell" size={18} />
            <div style={{fontSize:13,fontWeight:600,color:'var(--red-700)'}}>Hết hạn sau {c.daysLeft} ngày — đề xuất phỏng vấn tái ký theo quy trình.</div>
          </div>
        )}

        <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--faint)',fontWeight:800,marginBottom:14}}>Lộ trình thăng tiến & lịch sử lương</div>
        <SalaryJourney emp={c.emp}/>

        <div style={{display:'flex',gap:10,marginTop:24,justifyContent:'flex-end'}}>
          <button className="btn btn-ghost"><Icon name="file" size={16}/>Xem file HĐ</button>
          <button className="btn btn-ghost"><Icon name="logout" size={16}/>Khởi tạo thanh lý</button>
          <button className="btn btn-primary"><Icon name="edit" size={16}/>Tái ký hợp đồng</button>
        </div>
      </div>
    </Modal>
  );
}

Object.assign(window, { Contracts, ContractModal });
