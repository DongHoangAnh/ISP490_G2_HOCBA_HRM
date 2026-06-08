/* ============================================================
   HOC BA HRM — Bảng lương / Payroll Run
   Quy trình: Tạo kỳ lương → Tính lương → Duyệt → Chuyển khoản
   ============================================================ */

const RUN_STAGES = [
  { id:'draft',    name:'Kỳ lương (Nháp)',  sub:'Tạo kỳ tính lương',   icon:'calendar', color:'#78716C' },
  { id:'computed', name:'Tính lương',        sub:'Sinh phiếu lương',     icon:'coins',    color:'#1D4ED8' },
  { id:'approved', name:'Duyệt',             sub:'Phê duyệt bảng lương', icon:'checkCircle', color:'#B45309' },
  { id:'paid',     name:'Chuyển khoản',      sub:'Thanh toán qua NH',    icon:'wallet',   color:'#15803D' },
];
const runIdx = (s)=> RUN_STAGES.findIndex(x=>x.id===s);
// trạng thái phiếu lương theo state của kỳ
const payslipState = (run)=> ({draft:'Nháp', computed:'Đã tính', approved:'Đã duyệt', paid:'Đã chi trả'}[run]);

function Payroll({ search }) {
  const [tab, setTab] = useState('payslip');
  const [scope, setScope] = useState('all');
  const [onlyPending, setOnlyPending] = useState(false);
  const [sel, setSel] = useState(null);
  const [run, setRun] = useState(()=> localStorage.getItem('hocba_payrun') || 'computed');
  const [approvals, setApprovals] = useState({}); // id -> 'approved' | 'held'
  const [showPay, setShowPay] = useState(false);
  useEffect(()=>{ localStorage.setItem('hocba_payrun', run); }, [run]);

  // duyệt / tạm giữ từng người
  const setOne = (id, st) => setApprovals(a=>({...a, [id]: a[id]===st ? undefined : st}));
  const approveAllPending = () => setApprovals(a=>{ const n={...a}; PAYROLL.forEach(p=>{ if(!n[p.id]) n[p.id]='approved'; }); return n; });

  const approvedCount = PAYROLL.filter(p=>approvals[p.id]==='approved').length;
  const heldCount = PAYROLL.filter(p=>approvals[p.id]==='held').length;
  const pendingCount = PAYROLL.length - approvedCount - heldCount;

  // trạng thái từng phiếu theo kỳ + duyệt cá nhân
  const rowStatus = (p) => {
    if (run==='paid') return approvals[p.id]==='held' ? 'Tạm giữ' : 'Đã chi trả';
    if (run==='approved') return approvals[p.id]==='held' ? 'Tạm giữ' : 'Đã duyệt';
    if (run==='computed') return approvals[p.id]==='approved' ? 'Đã duyệt' : approvals[p.id]==='held' ? 'Tạm giữ' : 'Chờ duyệt';
    return 'Nháp';
  };
  const STATUS_KIND = {'Nháp':'gray','Chờ duyệt':'amber','Đã duyệt':'green','Tạm giữ':'gray','Đã chi trả':'teal'};

  // danh sách được chi trả (loại người tạm giữ)
  const payList = PAYROLL.filter(p=>approvals[p.id]!=='held');

  const rows = useMemo(()=> PAYROLL.filter(p=>{
    if (scope==='offline' && !p.offline) return false;
    if (scope==='online' && p.offline) return false;
    if (onlyPending && run==='computed' && approvals[p.id]) return false;
    if (search){ const q=search.toLowerCase(); if(!(p.name.toLowerCase().includes(q)||p.code.toLowerCase().includes(q))) return false; }
    return true;
  }), [scope,search,onlyPending,run,approvals]);

  const totals = PAYROLL.reduce((s,p)=>({gross:s.gross+p.gross,net:s.net+p.net,deduct:s.deduct+(p.bhxh+p.bhyt+p.bhtn+p.tax),com:s.com+p.com}),{gross:0,net:0,deduct:0,com:0});
  const payTotal = payList.reduce((s,p)=>s+p.net,0);
  const idx = runIdx(run);

  const primaryAction = () => {
    if (run==='draft') setRun('computed');
    else if (run==='computed'){ if (pendingCount>0) approveAllPending(); else setRun('approved'); }
    else if (run==='approved') setShowPay(true);
  };
  const primaryLabel = run==='draft' ? 'Tính lương'
    : run==='computed' ? (pendingCount>0 ? `Duyệt tất cả · còn ${pendingCount}` : 'Chốt bảng lương')
    : run==='approved' ? 'Chuyển khoản thanh toán'
    : 'Đã thanh toán';
  const primaryIcon = {draft:'coins', computed: pendingCount>0?'check':'checkCircle', approved:'wallet', paid:'check'}[run];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Bảng lương</h1>
          <p>Kỳ lương tháng 05/2026 · {PAYROLL.length} nhân sự · chu kỳ chi trả ngày 05 hàng tháng</p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost"><Icon name="calendar" size={16}/>Kỳ 05/2026</button>
          {run==='paid'
            ? <button className="btn btn-ghost" onClick={()=>setRun('draft')}><Icon name="plus" size={16}/>Tạo kỳ lương mới</button>
            : <button className={'btn '+(run==='approved'?'btn-gold':'btn-primary')} onClick={primaryAction}><Icon name={primaryIcon} size={16}/>{primaryLabel}</button>}
        </div>
      </div>

      {/* PAYROLL RUN STEPPER */}
      <div className="card" style={{padding:'18px 22px',marginBottom:18}}>
        <div style={{display:'flex',alignItems:'center'}}>
          {RUN_STAGES.map((st,i)=>{
            const done = i<idx, cur = i===idx;
            return (
              <React.Fragment key={st.id}>
                <div style={{display:'flex',alignItems:'center',gap:12,flexShrink:0}}>
                  <div style={{width:44,height:44,borderRadius:13,display:'grid',placeItems:'center',flexShrink:0,
                    background: done?'var(--green)': cur?st.color:'#EEEAE4', color:(done||cur)?'#fff':'var(--faint)',
                    boxShadow: cur?'0 6px 16px -4px '+st.color+'88':'none', transition:'all .25s'}}>
                    {done?<Icon name="check" size={22}/>:<Icon name={st.icon} size={21}/>}
                  </div>
                  <div>
                    <div style={{fontSize:13.5,fontWeight:700,color:(done||cur)?'var(--ink)':'var(--faint)'}}>{st.name}</div>
                    <div className="faint" style={{fontSize:11.5}}>{st.sub}</div>
                  </div>
                </div>
                {i<RUN_STAGES.length-1 && (
                  <div style={{flex:1,height:3,borderRadius:3,margin:'0 14px',background: i<idx?'var(--green)':'#EEEAE4',transition:'background .25s'}}></div>
                )}
              </React.Fragment>
            );
          })}
        </div>
        {/* contextual hint */}
        <div style={{marginTop:14,paddingTop:14,borderTop:'1px solid var(--border)',display:'flex',alignItems:'center',gap:10}}>
          <Icon name={run==='paid'?'checkCircle':'bell'} size={17} className="" style={{color:run==='paid'?'var(--green)':'var(--amber)'}}/>
          <span style={{fontSize:13,fontWeight:500,color:'var(--ink-soft)'}}>
            {run==='draft' && 'Kỳ lương đã tạo. Nhấn “Tính lương” để sinh phiếu lương cho toàn bộ nhân sự dựa trên công, phụ cấp và COM/KPI.'}
            {run==='computed' && <>Đã sinh <b>{PAYROLL.length} phiếu lương</b>. Duyệt <b>từng người</b> bên dưới (hoặc “Duyệt tất cả”). {pendingCount>0?<>Còn <b>{pendingCount}</b> phiếu chờ duyệt{heldCount>0?<>, <b>{heldCount}</b> tạm giữ</>:''}.</>:<>Tất cả đã xử lý — nhấn <b>“Chốt bảng lương”</b>.</>}</>}
            {run==='approved' && <>Bảng lương đã duyệt ({approvedCount?approvedCount:PAYROLL.length-heldCount} phiếu{heldCount>0?<>, {heldCount} tạm giữ</>:''}). Nhấn <b>“Chuyển khoản thanh toán”</b> để tạo lệnh chi trả.</>}
            {run==='paid' && <>Đã chi trả <b>{fmtVND(payTotal)} ₫</b> cho {payList.length} nhân sự ngày 05/06/2026. Phiếu lương đã gửi tới từng người.</>}
          </span>
          <Badge kind={{draft:'gray',computed:'blue',approved:'amber',paid:'green'}[run]} dot>{RUN_STAGES[idx].name}</Badge>
        </div>
      </div>

      <div className="stat-grid">
        <BigMoney lbl="Tổng quỹ lương (gross)" val={totals.gross} col="var(--ink)" ico="coins" bg="#F0EDE9" icol="var(--ink-soft)"/>
        <BigMoney lbl="Tổng thực lãnh (net)" val={totals.net} col="var(--green)" ico="wallet" bg="var(--green-bg)" icol="var(--green)"/>
        <BigMoney lbl="Khấu trừ (BH + thuế)" val={totals.deduct} col="var(--red-600)" ico="arrowDown" bg="var(--red-50)" icol="var(--red-600)"/>
        <BigMoney lbl="Hoa hồng COM (TVTS)" val={totals.com} col="var(--gold-600)" ico="trend" bg="var(--gold-50)" icol="var(--gold-600)"/>
      </div>

      <div className="tabs">
        {[['payslip','Phiếu lương'],['kpi','Bảng KPI & COM (Level 0–10)'],['payment','Chuyển khoản']].map(([id,l])=>(
          <button key={id} className={'tab'+(tab===id?' active':'')} onClick={()=>setTab(id)}>{l}{id==='payment'&&run==='paid'?' ✓':''}</button>
        ))}
      </div>

      {tab==='payslip' && (
        <>
          <div className="filterbar">
            <div className="seg">
              <button className={scope==='all'?'active':''} onClick={()=>setScope('all')}>Tất cả</button>
              <button className={scope==='offline'?'active':''} onClick={()=>setScope('offline')}>Offline (VP)</button>
              <button className={scope==='online'?'active':''} onClick={()=>setScope('online')}>Online / CTV</button>
            </div>
            {run==='computed' && <button className={'chip'+(onlyPending?' active':'')} onClick={()=>setOnlyPending(v=>!v)}>Chỉ chưa duyệt <span className="ct">{pendingCount}</span></button>}
            <span className="muted" style={{fontSize:12.5,marginLeft:'auto'}}>{rows.length} phiếu lương</span>
          </div>

          {/* thanh tiến độ duyệt — chỉ khi đang ở bước Tính lương */}
          {run==='computed' && (
            <div className="card" style={{padding:'14px 18px',marginBottom:14,display:'flex',alignItems:'center',gap:16,flexWrap:'wrap'}}>
              <div style={{flex:1,minWidth:220}}>
                <div className="between" style={{marginBottom:7}}>
                  <span style={{fontSize:13,fontWeight:600}}>Tiến độ duyệt phiếu lương</span>
                  <span className="mono" style={{fontSize:12.5,fontWeight:700}}>{approvedCount}/{PAYROLL.length} đã duyệt{heldCount>0?` · ${heldCount} giữ`:''}</span>
                </div>
                <div className="bar" style={{height:8}}>
                  <span style={{width:(approvedCount/PAYROLL.length*100)+'%',background:'var(--green)'}}></span>
                </div>
              </div>
              {pendingCount>0
                ? <button className="btn btn-primary btn-sm" onClick={approveAllPending}><Icon name="check" size={14}/>Duyệt tất cả ({pendingCount})</button>
                : <span className="badge badge-green" style={{padding:'7px 12px'}}><Icon name="checkCircle" size={14}/>Đã duyệt xong — sẵn sàng chốt</span>}
            </div>
          )}

          <div className="card">
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr>
                  <th>Nhân viên</th><th>Cấu trúc</th><th className="tbl-num">Lương CB</th>
                  <th className="tbl-num">Phụ cấp</th><th className="tbl-num">COM/KPI</th>
                  <th className="tbl-num">Khấu trừ</th><th className="tbl-num">Thực lãnh</th><th>Trạng thái</th>
                  {run==='computed' && <th style={{width:150}}>Duyệt</th>}
                </tr></thead>
                <tbody>
                  {rows.map(p=>{
                    const allowSum = Object.values(p.allow).reduce((a,b)=>a+b,0);
                    const deduct = p.bhxh+p.bhyt+p.bhtn+p.tax;
                    const ps = rowStatus(p);
                    const ap = approvals[p.id];
                    return (
                      <tr key={p.id} onClick={()=>setSel(p)}>
                        <td><EmpCell emp={p}/></td>
                        <td><Badge kind={p.offline?'teal':'blue'}>{p.offline?'Offline Staff':'Online/CTV'}</Badge></td>
                        <td className="tbl-num mono">{fmtVND(p.wage)}</td>
                        <td className="tbl-num mono muted">{allowSum?fmtVND(allowSum):'—'}</td>
                        <td className="tbl-num mono">{p.com?<span style={{color:'var(--gold-600)',fontWeight:600}}>{fmtVND(p.com)}</span>:<span className="faint">—</span>}</td>
                        <td className="tbl-num mono" style={{color:'var(--red-600)'}}>-{fmtVND(deduct)}</td>
                        <td className="tbl-num mono" style={{fontWeight:700}}>{fmtVND(p.net)}</td>
                        <td><Badge kind={STATUS_KIND[ps]||'gray'} dot>{ps}</Badge></td>
                        {run==='computed' && (
                          <td onClick={e=>e.stopPropagation()}>
                            {ap==='approved'
                              ? <button className="btn btn-soft btn-sm" onClick={()=>setOne(p.id,'approved')} title="Bỏ duyệt"><Icon name="check" size={13}/>Đã duyệt</button>
                              : ap==='held'
                                ? <button className="btn btn-ghost btn-sm" onClick={()=>setOne(p.id,'held')} title="Bỏ tạm giữ">Tạm giữ</button>
                                : <div style={{display:'flex',gap:6}}>
                                    <button className="btn btn-ghost btn-sm" onClick={()=>setOne(p.id,'held')} title="Tạm giữ phiếu này">Giữ</button>
                                    <button className="btn btn-primary btn-sm" onClick={()=>setOne(p.id,'approved')}><Icon name="check" size={13}/>Duyệt</button>
                                  </div>}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {tab==='kpi' && <KpiTable/>}

      {tab==='payment' && <PaymentBatch run={run} payList={payList} payTotal={payTotal} onPay={()=>setShowPay(true)}/>}

      {sel && <PayslipModal pay={sel} run={run} status={rowStatus(sel)} approval={approvals[sel.id]}
        onApprove={run==='computed'?()=>{setOne(sel.id,'approved');}:null}
        onHold={run==='computed'?()=>{setOne(sel.id,'held');}:null}
        onClose={()=>setSel(null)}/>}
      {showPay && <PaymentConfirm payList={payList} payTotal={payTotal} onClose={()=>setShowPay(false)} onConfirm={()=>{setRun('paid');setShowPay(false);setTab('payment');}}/>}
    </div>
  );
}

function BigMoney({ lbl, val, col, ico, bg, icol }) {
  return (
    <div className="stat">
      <div className="stat-ico" style={{background:bg,color:icol}}><Icon name={ico} size={21}/></div>
      <div className="stat-val" style={{fontSize:24,color:col}}>{fmtVND(val)} <span style={{fontSize:14,color:'var(--faint)',fontWeight:600}}>₫</span></div>
      <div className="stat-lbl">{lbl}</div>
    </div>
  );
}

/* ---------- Chuyển khoản: gom theo ngân hàng ---------- */
function PaymentBatch({ run, payList, payTotal, onPay }) {
  const banks = useMemo(()=>{
    const g = {};
    payList.forEach(p=>{ (g[p.bank] = g[p.bank] || {bank:p.bank, rows:[], total:0}); g[p.bank].rows.push(p); g[p.bank].total += p.net; });
    return Object.values(g).sort((a,b)=>b.total-a.total);
  }, [payList]);

  if (run!=='approved' && run!=='paid') {
    return (
      <div className="card"><div className="empty">
        <Icon name="wallet" size={34} className="faint"/>
        <div style={{marginTop:12,fontWeight:600,color:'var(--ink-soft)'}}>Chưa thể chuyển khoản</div>
        <div style={{fontSize:13,marginTop:4}}>Cần <b>duyệt bảng lương</b> trước khi tạo lệnh chi trả qua ngân hàng.</div>
      </div></div>
    );
  }

  return (
    <div>
      <div className="card" style={{marginBottom:16,padding:'16px 20px',display:'flex',alignItems:'center',gap:16,flexWrap:'wrap'}}>
        <div style={{width:44,height:44,borderRadius:12,background:run==='paid'?'var(--green-bg)':'var(--gold-50)',color:run==='paid'?'var(--green)':'var(--gold-600)',display:'grid',placeItems:'center'}}><Icon name={run==='paid'?'checkCircle':'wallet'} size={22}/></div>
        <div style={{flex:1,minWidth:200}}>
          <div style={{fontWeight:700,fontSize:15}}>Lệnh chi trả lương kỳ 05/2026</div>
          <div className="muted" style={{fontSize:12.5}}>{payList.length} nhân sự · {banks.length} ngân hàng thụ hưởng · {run==='paid'?'đã chuyển khoản 05/06/2026':'chờ tạo lệnh chuyển khoản'}</div>
        </div>
        <div style={{textAlign:'right'}}>
          <div className="faint" style={{fontSize:11,fontWeight:700,textTransform:'uppercase'}}>Tổng chi trả</div>
          <div className="mono" style={{fontSize:22,fontWeight:800,color:'var(--green)'}}>{fmtVND(payTotal)} ₫</div>
        </div>
        {run==='paid'
          ? <button className="btn btn-ghost"><Icon name="download" size={16}/>Tải UNC / sao kê</button>
          : <button className="btn btn-gold" onClick={onPay}><Icon name="wallet" size={16}/>Tạo lệnh chuyển khoản</button>}
      </div>

      <div style={{display:'flex',flexDirection:'column',gap:14}}>
        {banks.map(b=>(
          <div key={b.bank} className="card">
            <div className="card-head">
              <div style={{width:32,height:32,borderRadius:9,background:'var(--blue-bg)',color:'var(--blue)',display:'grid',placeItems:'center'}}><Icon name="building" size={17}/></div>
              <h3>{b.bank}</h3>
              <span className="badge badge-gray">{b.rows.length} tài khoản</span>
              <div className="actions">
                <span className="mono" style={{fontWeight:800,fontSize:14}}>{fmtVND(b.total)} ₫</span>
                {run==='paid' && <Badge kind="green" dot>Đã chuyển</Badge>}
              </div>
            </div>
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr><th>Người thụ hưởng</th><th>Số tài khoản</th><th>Nội dung CK</th><th className="tbl-num">Số tiền</th><th>Trạng thái</th></tr></thead>
                <tbody>
                  {b.rows.map(p=>(
                    <tr key={p.id} style={{cursor:'default'}}>
                      <td><EmpCell emp={p}/></td>
                      <td className="mono" style={{fontWeight:600}}>{p.acct}</td>
                      <td className="muted" style={{fontSize:12.5}}>HOCBA LUONG T05 {p.code}</td>
                      <td className="tbl-num mono" style={{fontWeight:700}}>{fmtVND(p.net)}</td>
                      <td>{run==='paid'?<Badge kind="green" dot>Đã chuyển</Badge>:<Badge kind="amber" dot>Chờ chuyển</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Modal xác nhận chuyển khoản ---------- */
function PaymentConfirm({ payList, payTotal, onClose, onConfirm }) {
  const banks = {};
  payList.forEach(p=>{ banks[p.bank]=(banks[p.bank]||0)+1; });
  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--green-bg),#fff)'}}>
        <div style={{width:48,height:48,borderRadius:13,background:'var(--green)',color:'#fff',display:'grid',placeItems:'center'}}><Icon name="wallet" size={24}/></div>
        <div style={{flex:1}}>
          <h2 style={{margin:0,fontSize:19,fontWeight:800}}>Xác nhận chuyển khoản lương</h2>
          <div className="muted" style={{fontSize:13,marginTop:3}}>Kỳ lương 05/2026 · tài khoản chi: Học Bá Education — Techcombank</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'22px 24px'}}>
        <div className="grid-2" style={{rowGap:16,marginBottom:18}}>
          <div className="kv"><div className="k">Số nhân sự được chi</div><div className="v">{payList.length} người</div></div>
          <div className="kv"><div className="k">Số ngân hàng thụ hưởng</div><div className="v">{Object.keys(banks).length} ngân hàng</div></div>
          <div className="kv"><div className="k">Hình thức</div><div className="v">Chuyển khoản theo lô (UNC)</div></div>
          <div className="kv"><div className="k">Ngày giá trị</div><div className="v">05/06/2026</div></div>
        </div>
        <div style={{padding:'16px 18px',borderRadius:14,background:'linear-gradient(120deg,var(--green-bg),#fff)',border:'1px solid #cdeacf',marginBottom:18}}>
          <div style={{fontSize:12,color:'var(--green)',fontWeight:700,textTransform:'uppercase',letterSpacing:'.5px'}}>Tổng tiền chuyển khoản</div>
          <div className="mono" style={{fontSize:30,fontWeight:800,color:'var(--green)',marginTop:2}}>{fmtVND(payTotal)} ₫</div>
        </div>
        <div style={{display:'flex',gap:10,justifyContent:'flex-end'}}>
          <button className="btn btn-ghost" onClick={onClose}>Huỷ</button>
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Xuất file ngân hàng</button>
          <button className="btn" style={{background:'var(--green)',color:'#fff'}} onClick={onConfirm}><Icon name="check" size={16}/>Xác nhận đã chuyển</button>
        </div>
      </div>
    </Modal>
  );
}

function KpiTable() {
  return (
    <div className="card">
      <div className="card-head">
        <h3>Bảng Level KPI & COM — vị trí Tư vấn tuyển sinh (TVTS)</h3>
        <div className="actions"><span className="badge badge-gold">Cấu trúc đặc thù · custom salary rule</span></div>
      </div>
      <div className="card-pad" style={{paddingBottom:8}}>
        <p className="muted" style={{margin:'0 0 16px',fontSize:13}}>Mỗi level xác định lương cứng, KPI target và % hoa hồng. COM được tính tự động: <b style={{color:'var(--ink)'}}>COM = Doanh thu × %COM</b>, nhập doanh thu thực tế vào payslip input hàng tháng.</p>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr><th>Level</th><th className="tbl-num">Lương cứng</th><th className="tbl-num">KPI Target</th><th className="tbl-num">% COM</th><th className="tbl-num">COM (nếu đạt)</th><th className="tbl-num">Tổng thu nhập</th><th></th></tr></thead>
            <tbody>
              {KPI_LEVELS.map(l=>(
                <tr key={l.lv} style={{cursor:'default'}}>
                  <td><span className="badge badge-gold" style={{fontSize:13,fontWeight:800,minWidth:34,justifyContent:'center'}}>Lv {l.lv}</span></td>
                  <td className="tbl-num mono">{fmtVND(l.hard)}</td>
                  <td className="tbl-num mono muted">{fmtVND(l.target)}</td>
                  <td className="tbl-num"><b style={{color:'var(--red-600)'}}>{l.com}%</b></td>
                  <td className="tbl-num mono" style={{color:'var(--gold-600)',fontWeight:600}}>{fmtVND(l.comGet)}</td>
                  <td className="tbl-num mono" style={{fontWeight:700}}>{fmtVND(l.total)}</td>
                  <td style={{width:120}}><div className="bar" style={{minWidth:90}}><span style={{width:(l.total/52440000*100)+'%',background:'linear-gradient(90deg,var(--gold-500),var(--red-600))'}}></span></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function PayslipModal({ pay, run, status, approval, onApprove, onHold, onClose }) {
  const allow = [
    ['PC xăng xe',pay.allow.pcXang],['PC gửi xe',pay.allow.pcGui],['PC chức vụ',pay.allow.pcChucVu],
    ['PC thâm niên',pay.allow.pcTham],['Hỗ trợ điện thoại',pay.allow.htDienThoai],['Hỗ trợ ăn ca',pay.allow.htAnCa],
    ['Hỗ trợ trang phục',pay.allow.htTrangPhuc],['Hỗ trợ đi lại',pay.allow.htDiLai],
  ].filter(([_,v])=>v>0);
  const ps = status || pay.state;
  const Row = ({label,val,sign,strong,note}) => (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'9px 0',borderBottom:'1px dashed var(--border)'}}>
      <span style={{fontSize:13,fontWeight:strong?700:500,color:strong?'var(--ink)':'var(--ink-soft)'}}>{label}{note&&<span className="faint" style={{fontWeight:500,marginLeft:6,fontSize:11.5}}>{note}</span>}</span>
      <span className="mono" style={{fontSize:13.5,fontWeight:strong?800:600,color:sign==='-'?'var(--red-600)':sign==='+'?'var(--green)':'var(--ink)'}}>{sign==='-'?'-':''}{fmtVND(val)} ₫</span>
    </div>
  );
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{background:'linear-gradient(120deg,var(--gold-50),#fff)'}}>
        <Avatar emp={pay} size={56}/>
        <div style={{flex:1}}>
          <h2 style={{margin:0,fontSize:20,fontWeight:800}}>Phiếu lương · {pay.name}</h2>
          <div className="muted" style={{fontSize:13,marginTop:3}}>{pay.code} · {pay.jobTitle} · Kỳ lương {pay.period} · STK {pay.bank} {pay.acct}</div>
        </div>
        <Badge kind={{'Nháp':'gray','Chờ duyệt':'amber','Đã tính':'blue','Đã duyệt':'green','Tạm giữ':'gray','Đã chi trả':'teal'}[ps]||'gray'} dot>{ps}</Badge>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20}/></button>
      </div>
      <div style={{padding:'20px 24px',maxHeight:'58vh',overflowY:'auto'}}>
        <div className="grid-2" style={{gap:22}}>
          <div>
            <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--green)',fontWeight:800,marginBottom:4}}>Thu nhập</div>
            <Row label="Lương cơ bản" val={pay.wage} note={`${pay.workDays}/${pay.standardDays} công`}/>
            {allow.map(([k,v],i)=><Row key={i} label={k} val={v}/>)}
            {pay.com>0 && <Row label="Hoa hồng COM" val={pay.com} sign="+" note={`DT ${fmtM(pay.revenue)}`}/>}
            <Row label="Tổng thu nhập (gross)" val={pay.gross} strong/>
          </div>
          <div>
            <div style={{fontSize:11,textTransform:'uppercase',letterSpacing:'.5px',color:'var(--red-600)',fontWeight:800,marginBottom:4}}>Khấu trừ</div>
            <Row label="BHXH" val={pay.bhxh} sign="-" note="8%"/>
            <Row label="BHYT" val={pay.bhyt} sign="-" note="1.5%"/>
            <Row label="BHTN" val={pay.bhtn} sign="-" note="1%"/>
            <Row label="Thuế TNCN" val={pay.tax} sign="-" note="sau giảm trừ 11tr"/>
            <Row label="Tổng khấu trừ" val={pay.bhxh+pay.bhyt+pay.bhtn+pay.tax} sign="-" strong/>
            <div style={{marginTop:18,padding:'16px 18px',borderRadius:14,background:'linear-gradient(120deg,var(--green-bg),#fff)',border:'1px solid #cdeacf'}}>
              <div style={{fontSize:12,color:'var(--green)',fontWeight:700,textTransform:'uppercase',letterSpacing:'.5px'}}>Thực lãnh (NET)</div>
              <div className="mono" style={{fontSize:28,fontWeight:800,color:'var(--green)',marginTop:2}}>{fmtVND(pay.net)} ₫</div>
            </div>
          </div>
        </div>
        <div style={{display:'flex',gap:10,marginTop:22,justifyContent:'flex-end',alignItems:'center'}}>
          <button className="btn btn-ghost"><Icon name="mail" size={16}/>Gửi phiếu lương</button>
          <button className="btn btn-ghost"><Icon name="download" size={16}/>Tải PDF</button>
          {onApprove && (approval==='approved'
            ? <span className="badge badge-green" style={{padding:'9px 14px'}}><Icon name="checkCircle" size={15}/>Phiếu đã duyệt</span>
            : <>
                {onHold && approval!=='held' && <button className="btn btn-ghost" onClick={()=>{onHold();onClose();}}>Tạm giữ</button>}
                <button className="btn btn-primary" onClick={()=>{onApprove();onClose();}}><Icon name="check" size={16}/>Duyệt phiếu này</button>
              </>)}
        </div>
      </div>
    </Modal>
  );
}

Object.assign(window, { Payroll, BigMoney, KpiTable, PayslipModal, PaymentBatch, PaymentConfirm });
