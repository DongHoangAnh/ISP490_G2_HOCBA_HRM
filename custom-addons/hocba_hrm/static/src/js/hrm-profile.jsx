/* ============================================================
   HOC BA HRM — Hồ sơ của tôi (Employee self-service)
   ============================================================ */

function Profile({ setView }) {
  const p = MY_PROFILE;
  const leavePct = Math.round(p.leaveUsed / p.leaveYear * 100);

  const shortcuts = [
    { ico:'calendar', col:'var(--violet)', bg:'var(--violet-bg)', t:'Xin nghỉ phép', s:'Tạo đơn nghỉ', act:()=>setView('timeoff') },
    { ico:'home', col:'var(--blue)', bg:'var(--blue-bg)', t:'Đăng ký làm online', s:'WFH / remote', act:()=>setView('timeoff') },
    { ico:'wallet', col:'var(--green)', bg:'var(--green-bg)', t:'Xem phiếu lương', s:'Kỳ '+p.salaryPeriod, act:()=>setView('payroll') },
    { ico:'clock', col:'var(--amber)', bg:'var(--amber-bg)', t:'Báo quên chấm công', s:'Bổ sung công', act:()=>setView('attendance') },
  ];

  return (
    <div className="content fade-in">
      {/* HERO */}
      <div className="card" style={{overflow:'hidden',marginBottom:16,padding:0}}>
        <div style={{height:92,background:'linear-gradient(110deg,#5C0A17,#C8102E 58%,#D9A400)',position:'relative'}}>
          <div style={{position:'absolute',inset:0,background:'radial-gradient(500px 160px at 88% -20%, rgba(255,255,255,.18), transparent)'}}></div>
        </div>
        <div style={{padding:'0 26px 20px',marginTop:-42,display:'flex',gap:20,alignItems:'flex-end',flexWrap:'wrap'}}>
          <div className={'av '+p.avatar} style={{width:88,height:88,fontSize:30,boxShadow:'0 0 0 4px #fff, var(--shadow)'}}>{p.initials}</div>
          <div style={{flex:1,minWidth:240,paddingBottom:2}}>
            <div style={{display:'flex',alignItems:'center',gap:11,flexWrap:'wrap'}}>
              <h1 style={{margin:0,fontSize:23,fontWeight:800,letterSpacing:'-.5px'}}>{p.name}</h1>
              <Badge kind="green" dot>{p.status}</Badge>
            </div>
            <div className="muted" style={{fontSize:13.5,marginTop:4}}>{p.code} · {p.jobTitle} · {p.depName}</div>
            <div style={{display:'flex',gap:16,marginTop:11,flexWrap:'wrap'}}>
              <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="mail" size={15}/>{p.emailPersonal}</span>
              <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="phone" size={15}/>{p.phone}</span>
              <span style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:12.5}} className="muted"><Icon name="clock" size={15}/>Thâm niên {p.tenureMonths} tháng</span>
            </div>
          </div>
          <div style={{display:'flex',gap:10,paddingBottom:4}}>
            <button className="btn btn-ghost"><Icon name="shield" size={16}/>Đổi mật khẩu</button>
            <button className="btn btn-primary"><Icon name="edit" size={16}/>Đề nghị cập nhật</button>
          </div>
        </div>
      </div>

      {/* SELF-SERVICE QUICK STATS */}
      <div className="stat-grid">
        <div className="stat">
          <div className="stat-ico" style={{background:'var(--green-bg)',color:'var(--green)'}}><Icon name="wallet" size={21}/></div>
          <div className="stat-val" style={{fontSize:23}}>{fmtVND(p.netSalary)} <span style={{fontSize:13,color:'var(--faint)',fontWeight:600}}>₫</span></div>
          <div className="stat-lbl">Thực lãnh kỳ {p.salaryPeriod}</div>
        </div>
        <div className="stat">
          <div className="stat-ico" style={{background:'var(--blue-bg)',color:'var(--blue)'}}><Icon name="calendar" size={21}/></div>
          <div className="stat-val" style={{fontSize:23}}>{p.leaveRemain} <span style={{fontSize:13,color:'var(--faint)',fontWeight:600}}>ngày</span></div>
          <div className="stat-lbl">Phép năm còn lại</div>
          <div className="bar" style={{marginTop:9}}><span style={{width:leavePct+'%',background:'var(--blue)'}}></span></div>
        </div>
        <div className="stat">
          <div className="stat-ico" style={{background:'var(--gold-50)',color:'var(--gold-600)'}}><Icon name="clock" size={21}/></div>
          <div className="stat-val" style={{fontSize:23}}>{p.workDays}<span style={{fontSize:14,color:'var(--faint)',fontWeight:600}}>/{p.standardDays}</span></div>
          <div className="stat-lbl">Công tháng này · {p.lateThisMonth} lần đi trễ</div>
        </div>
        <div className="stat">
          <div className="stat-ico" style={{background:'var(--red-50)',color:'var(--red-600)'}}><Icon name="file" size={21}/></div>
          <div className="stat-val" style={{fontSize:23}}>{p.contract.includes('12')?'12 tháng':p.contract}</div>
          <div className="stat-lbl">Hợp đồng · {p.contractSchedule}</div>
        </div>
      </div>

      {/* SHORTCUTS */}
      <div className="grid-2" style={{gridTemplateColumns:'repeat(4,1fr)',marginBottom:18}}>
        {shortcuts.map((s,i)=>(
          <button key={i} className="card" onClick={s.act} style={{padding:16,display:'flex',alignItems:'center',gap:13,textAlign:'left',transition:'border-color .14s, transform .14s'}}
            onMouseEnter={e=>{e.currentTarget.style.borderColor='var(--border-strong)';e.currentTarget.style.transform='translateY(-1px)';}}
            onMouseLeave={e=>{e.currentTarget.style.borderColor='var(--border)';e.currentTarget.style.transform='none';}}>
            <div style={{width:40,height:40,borderRadius:11,background:s.bg,color:s.col,display:'grid',placeItems:'center',flexShrink:0}}><Icon name={s.ico} size={20}/></div>
            <div style={{flex:1}}>
              <div style={{fontWeight:700,fontSize:13.5}}>{s.t}</div>
              <div className="muted" style={{fontSize:11.5}}>{s.s}</div>
            </div>
            <Icon name="chevR" size={16} className="faint"/>
          </button>
        ))}
      </div>

      {/* INFO SECTIONS */}
      <div className="grid-2" style={{alignItems:'start'}}>
        <InfoCard icon="idcard" color="var(--red-600)" title="Thông tin định danh">
          <Field label="Mã nhân viên" value={p.code}/>
          <Field label="Họ và tên" value={p.name}/>
          <Field label="Giới tính" value={p.gender}/>
          <Field label="Ngày sinh" value={fmtDate(p.birth)+' · '+p.age+' tuổi'}/>
          <Field label="Nơi sinh" value={p.birthplace} full/>
          <Field label="Quốc tịch" value={p.nationality}/>
          <Field label="Số CCCD" value={p.cccd}/>
          <Field label="Ngày cấp" value={fmtDate(p.cccdDate)}/>
          <Field label="Nơi cấp" value={p.cccdPlace}/>
        </InfoCard>

        <InfoCard icon="phone" color="var(--blue)" title="Thông tin liên hệ">
          <Field label="Số điện thoại" value={p.phone}/>
          <Field label="Tài khoản Lark" value={p.lark}/>
          <Field label="Email cá nhân" value={p.emailPersonal} full/>
          <Field label="Email công ty" value={p.emailCompany} full/>
          <Field label="Địa chỉ thường trú" value={p.addrPermanent} full/>
          <Field label="Địa chỉ hiện tại" value={p.addrCurrent} full/>
        </InfoCard>

        <InfoCard icon="briefcase" color="var(--teal)" title="Công việc & hợp đồng">
          <Field label="Chức danh" value={p.jobTitle} full/>
          <Field label="Loại vị trí" value={p.posType}/>
          <Field label="Phòng ban" value={p.depName}/>
          <Field label="Hình thức" value={p.type}/>
          <Field label="Số tháng làm việc" value={p.tenureMonths+' tháng'}/>
          <Field label="Ngày thử việc" value={fmtDate(p.trialDate)}/>
          <Field label="Ngày chính thức" value={fmtDate(p.officialDate)}/>
          <Field label="Hợp đồng" value={p.contract}/>
          <Field label="Lịch ký HĐ" value={p.contractSchedule}/>
        </InfoCard>

        <InfoCard icon="users" color="var(--violet)" title="Gia đình & liên hệ khẩn cấp">
          <Field label="Tình trạng hôn nhân" value={p.marital}/>
          <Field label="SĐT người thân" value={p.emergencyPhone}/>
          <Field label="Người liên hệ khẩn cấp" value={p.emergencyName} full/>
          <Field label="Thông tin gia đình" value={p.family} full/>
        </InfoCard>

        <InfoCard icon="graduation" color="var(--gold-600)" title="Học vấn & ngôn ngữ">
          <Field label="Trình độ học vấn" value={p.education} full/>
          <Field label="Học tiếng Trung" value={p.chineseStudy}/>
          <Field label="Trình độ tiếng Trung" value={p.chineseLevel}/>
        </InfoCard>

        <InfoCard icon="wallet" color="var(--green)" title="Tài khoản ngân hàng">
          <Field label="Ngân hàng" value={p.bank}/>
          <Field label="Số tài khoản" value={p.acct}/>
        </InfoCard>
      </div>

      {/* EQUIPMENT */}
      <div className="card" style={{marginTop:16}}>
        <div className="card-head">
          <div style={{width:32,height:32,borderRadius:9,background:'#F0EDE9',color:'var(--ink-soft)',display:'grid',placeItems:'center'}}><Icon name="grid" size={17}/></div>
          <h3>Tài sản được cấp phát</h3>
          <span className="badge badge-gray" style={{marginLeft:'auto'}}>{p.equipment.length} thiết bị</span>
        </div>
        <div className="card-pad">
          <div style={{display:'flex',gap:10,flexWrap:'wrap'}}>
            {p.equipment.map((it,i)=>(
              <span key={i} style={{display:'inline-flex',alignItems:'center',gap:8,padding:'8px 14px',border:'1px solid var(--border)',borderRadius:10,fontSize:13,fontWeight:500,background:'var(--surface-2)'}}>
                <span style={{width:7,height:7,borderRadius:'50%',background:'var(--green)'}}></span>{it}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div style={{textAlign:'center',marginTop:22,color:'var(--faint)',fontSize:12}}>
        Thông tin được đồng bộ từ hệ thống nhân sự · cần chỉnh sửa? Gửi đề nghị cập nhật để HCNS duyệt.
      </div>
    </div>
  );
}

function InfoCard({ icon, color, title, children }) {
  return (
    <div className="card">
      <div className="card-head">
        <div style={{width:32,height:32,borderRadius:9,background:color+'1a',color:color,display:'grid',placeItems:'center'}}><Icon name={icon} size={17}/></div>
        <h3>{title}</h3>
      </div>
      <div className="card-pad">
        <div className="grid-2" style={{rowGap:17,columnGap:18}}>{children}</div>
      </div>
    </div>
  );
}

function Field({ label, value, full }) {
  const empty = value==null || value==='' || value==='null';
  return (
    <div className="kv" style={full?{gridColumn:'1 / -1'}:null}>
      <div className="k">{label}</div>
      <div className="v" style={empty?{color:'var(--faint)',fontWeight:500,fontStyle:'italic'}:{textWrap:'pretty'}}>{empty?'Chưa cập nhật':value}</div>
    </div>
  );
}

Object.assign(window, { Profile, InfoCard, Field });
