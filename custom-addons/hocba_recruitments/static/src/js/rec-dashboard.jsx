/* ============================================================
   HỌC BÁ — Module Tuyển dụng / Dashboard
   ============================================================ */

/* ══════════════════════════════════════════════════════════════
   Dashboard chính
   ══════════════════════════════════════════════════════════════ */
function RecDashboard({ setView }) {
  const S = REC_STATS;
  const stageMap = {};
  REC_STAGES.forEach(s => { stageMap[s.id] = s; });

  const upcomingInterviews = APPLICANTS
    .filter(a => a.interview)
    .sort((a, b) => a.interview.localeCompare(b.interview));

  const recentApps = [...APPLICANTS]
    .sort((a, b) => a.days - b.days)
    .slice(0, 6);

  const kpis = [
    {
      icon: 'briefcase', color: 'var(--red-600)', bg: 'var(--red-50)',
      val: S.openPositions, label: 'Vị trí đang tuyển',
      sub: `${S.openSlots} suất còn trống`,
      trend: '+2 so với T5', up: true,
    },
    {
      icon: 'users', color: 'var(--blue)', bg: 'var(--blue-bg)',
      val: S.totalApplicants, label: 'Tổng ứng viên',
      sub: `${S.byStage.new || 0} hồ sơ mới`,
      trend: '+5 tuần này', up: true,
    },
    {
      icon: 'calendar', color: 'var(--violet)', bg: 'var(--violet-bg)',
      val: upcomingInterviews.length, label: 'Lịch phỏng vấn',
      sub: `${S.todayInterviews} phỏng vấn hôm nay`,
    },
    {
      icon: 'target', color: 'var(--green)', bg: 'var(--green-bg)',
      val: S.offerAcceptRate + '%', label: 'Tỷ lệ nhận offer',
      sub: `${S.hired}/${S.offerReached} đã chốt`,
    },
  ];

  return (
    <div className="content fade-in">
      {/* ── Page Header ── */}
      <div className="page-head">
        <div>
          <h1>Dashboard Tuyển dụng</h1>
          <p>
            Quy trình 5 bước · {S.totalApplicants} ứng viên · {S.openPositions} vị trí mở ·
            Cập nhật: Thứ Hai, 09/06/2026
          </p>
        </div>
        <div className="actions">
          <button className="btn btn-ghost" onClick={() => setView('jobs')}>
            <Icon name="building" size={15}/> Quản lý vị trí
          </button>
          <button className="btn btn-ghost" onClick={() => setView('kanban')}>
            <Icon name="briefcase" size={15}/> Xem Kanban
          </button>
          <button className="btn btn-primary" onClick={() => setView('kanban')}>
            <Icon name="plus" size={15}/> Thêm ứng viên
          </button>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="stat-grid">
        {kpis.map((k, i) => (
          <div key={i} className="stat" style={{ cursor: 'pointer' }}>
            <div className="stat-ico" style={{ background: k.bg, color: k.color }}>
              <Icon name={k.icon} size={22}/>
            </div>
            <div className="stat-val">{k.val}</div>
            <div className="stat-lbl">{k.label}</div>
            {k.trend && (
              <div className={'stat-trend ' + (k.up ? 'trend-up' : 'trend-down')}>
                <Icon name="arrowUp" size={13}/>{k.trend}
              </div>
            )}
            {k.sub && (
              <div className="stat-trend" style={{ color: 'var(--muted)' }}>{k.sub}</div>
            )}
          </div>
        ))}
      </div>

      {/* ── Row 2: Pipeline + Tasks ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.65fr 1fr', gap: 16, marginBottom: 16 }}>
        <PipelineSummary stageMap={stageMap} setView={setView}/>
        <TaskPanel setView={setView}/>
      </div>

      {/* ── Row 3: Position Breakdown + Source Chart ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <PositionBreakdown setView={setView}/>
        <SourceBreakdown/>
      </div>

      {/* ── Row 4: Open Jobs ── */}
      <OpenJobsCard setView={setView}/>

      {/* ── Row 5: Interviews + Recent Applicants ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr', gap: 16, marginTop: 16 }}>
        <UpcomingInterviewsCard interviews={upcomingInterviews} stageMap={stageMap}/>
        <RecentApplicantsCard apps={recentApps} stageMap={stageMap} setView={setView}/>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Pipeline Summary
   ══════════════════════════════════════════════════════════════ */
function PipelineSummary({ stageMap, setView }) {
  const total = APPLICANTS.length || 1;
  const byStage = REC_STATS.byStage;

  return (
    <div className="card">
      <div className="card-head">
        <h3>Pipeline tuyển dụng</h3>
        <Badge kind="blue">{total} ứng viên</Badge>
        <div className="actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setView('kanban')}>
            Xem Kanban <Icon name="chevR" size={14}/>
          </button>
        </div>
      </div>

      <div className="card-pad" style={{ paddingBottom: 14 }}>
        {/* Stage rows */}
        {REC_STAGES.map((st, i) => {
          const count = byStage[st.id] || 0;
          const pct = Math.round(count / total * 100);
          const prevCount = i === 0 ? total : (byStage[REC_STAGES[i - 1].id] || 0);
          const convRate = prevCount > 0 ? Math.round(count / prevCount * 100) : 0;

          return (
            <div key={st.id} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {/* Stage badge */}
                <div style={{
                  width: 34, height: 34, borderRadius: 9, flexShrink: 0,
                  background: st.color + '18', color: st.color,
                  display: 'grid', placeItems: 'center', fontWeight: 800, fontSize: 12,
                }}>
                  {i + 1}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 700, fontSize: 13 }}>{st.name}</span>
                      {i > 0 && convRate > 0 && (
                        <span style={{
                          fontSize: 10.5, color: 'var(--muted)', fontWeight: 600,
                          background: 'var(--surface-2)', borderRadius: 6, padding: '2px 7px',
                          border: '1px solid var(--border)',
                        }}>
                          {convRate}% từ bước trước
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 11.5, color: 'var(--faint)' }}>{pct}%</span>
                      <span style={{ fontWeight: 800, fontSize: 16, color: st.color }}>{count}</span>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="bar">
                    <span style={{ width: pct + '%', background: st.color }}></span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* Mini funnel summary */}
        <div className="funnel-row">
          {REC_STAGES.map((st, i) => (
            <React.Fragment key={st.id}>
              <div className="funnel-step">
                <div className="fs-val" style={{ color: st.color }}>
                  {byStage[st.id] || 0}
                </div>
                <div className="fs-lbl">{st.name}</div>
              </div>
              {i < REC_STAGES.length - 1 && (
                <div className="funnel-arrow">
                  <Icon name="arrowR" size={14}/>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Task Panel — việc cần xử lý
   ══════════════════════════════════════════════════════════════ */
function TaskPanel({ setView }) {
  const S = REC_STATS;
  const todayInterviews = APPLICANTS.filter(a => a.interview === '2026-06-09');

  const tasks = [
    {
      icon: 'inbox', color: 'var(--blue)', bg: 'var(--blue-bg)',
      label: `${S.byStage.new || 0} CV chờ lọc`,
      sub: 'Xử lý trước 12h hôm nay',
      urgent: (S.byStage.new || 0) >= 4,
      action: () => setView('kanban'),
    },
    {
      icon: 'calendar', color: 'var(--violet)', bg: 'var(--violet-bg)',
      label: `${todayInterviews.length} phỏng vấn hôm nay`,
      sub: todayInterviews.length > 0
        ? `Gần nhất: ${todayInterviews[0]?.name}`
        : 'Không có lịch hôm nay',
      urgent: todayInterviews.length > 0,
      action: () => setView('interviews'),
    },
    {
      icon: 'mail', color: 'var(--amber)', bg: 'var(--amber-bg)',
      label: `${S.byStage.inter || 0} ứng viên chờ gửi offer`,
      sub: 'Đã hoàn thành vòng phỏng vấn',
      action: () => setView('kanban'),
    },
    {
      icon: 'checkCircle', color: 'var(--green)', bg: 'var(--green-bg)',
      label: `${S.byStage.hired || 0} ứng viên sắp onboarding`,
      sub: 'Chuyển sang quy trình nhập việc',
      action: () => setView('kanban'),
    },
  ];

  const urgentCount = tasks.filter(t => t.urgent).length;

  return (
    <div className="card">
      <div className="card-head">
        <h3>Việc cần xử lý</h3>
        {urgentCount > 0
          ? <Badge kind="red" dot>{urgentCount} cần chú ý</Badge>
          : <Badge kind="green" dot>Ổn định</Badge>
        }
      </div>
      <div style={{ padding: '8px 10px' }}>
        {tasks.map((t, i) => (
          <button key={i} onClick={t.action}
            style={{
              display: 'flex', gap: 12, padding: '12px 10px', width: '100%',
              textAlign: 'left', borderRadius: 11, alignItems: 'flex-start',
              background: t.urgent ? 'var(--red-50)' : 'transparent',
              transition: 'background .12s', marginBottom: 2,
              border: t.urgent ? '1px solid var(--red-100)' : '1px solid transparent',
            }}
            onMouseEnter={e => { if (!t.urgent) e.currentTarget.style.background = 'var(--surface-2)'; }}
            onMouseLeave={e => { if (!t.urgent) e.currentTarget.style.background = 'transparent'; }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: t.bg, color: t.color,
              display: 'grid', placeItems: 'center', flexShrink: 0,
            }}>
              <Icon name={t.icon} size={18}/>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.35,
                color: t.urgent ? 'var(--red-700)' : 'var(--ink)' }}>
                {t.label}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>{t.sub}</div>
            </div>
            <Icon name="chevR" size={15} className="faint" style={{ marginTop: 2 }}/>
          </button>
        ))}
      </div>

      {/* KPI nhanh ở cuối */}
      <div style={{
        borderTop: '1px solid var(--border)', margin: '0 12px',
        padding: '12px 10px 14px',
        display: 'flex', gap: 0,
      }}>
        {[
          { label: 'Thời gian tuyển TB', val: REC_STATS.avgDaysToHire + ' ngày', color: 'var(--ink)' },
          { label: 'Tỷ lệ offer', val: REC_STATS.offerAcceptRate + '%', color: 'var(--green)' },
        ].map((m, i) => (
          <div key={i} style={{
            flex: 1, textAlign: 'center',
            borderRight: i === 0 ? '1px solid var(--border)' : 'none',
          }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: m.color }}>{m.val}</div>
            <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 3 }}>{m.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Position Breakdown — ứng viên theo vị trí
   ══════════════════════════════════════════════════════════════ */
function PositionBreakdown({ setView }) {
  const posData = REC_JOBS.map(j => {
    const apps = APPLICANTS.filter(a => a.posId === j.id);
    return {
      title: j.title, dept: j.dept, deptColor: j.deptColor,
      total: apps.length,
      screen: apps.filter(a => a.stage === 'screen').length,
      inter:  apps.filter(a => a.stage === 'inter').length,
      offer:  apps.filter(a => a.stage === 'offer').length,
      hired:  apps.filter(a => a.stage === 'hired').length,
      new:    apps.filter(a => a.stage === 'new').length,
    };
  }).sort((a, b) => b.total - a.total);

  const max = Math.max(...posData.map(p => p.total), 1);

  return (
    <div className="card">
      <div className="card-head">
        <h3>Ứng viên theo vị trí</h3>
        <Badge kind="gray">{REC_JOBS.length} vị trí</Badge>
        <div className="actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setView('jobs')}>
            Chi tiết <Icon name="chevR" size={14}/>
          </button>
        </div>
      </div>
      <div className="card-pad" style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        {posData.map((p, i) => (
          <div key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'flex-end' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{p.title}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 1 }}>{p.dept}</div>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', fontSize: 11 }}>
                {p.inter > 0 && (
                  <span style={{ color: 'var(--amber)', fontWeight: 700 }}>
                    <Icon name="mic" size={10}/> {p.inter} PV
                  </span>
                )}
                {p.hired > 0 && (
                  <span style={{ color: 'var(--green)', fontWeight: 700 }}>
                    <Icon name="check" size={10}/> {p.hired}
                  </span>
                )}
                <span style={{ fontWeight: 800, fontSize: 14 }}>{p.total}</span>
              </div>
            </div>
            {/* Stacked bar */}
            <div className="bar" style={{ height: 8 }}>
              <span style={{
                width: (p.total / max * 100) + '%',
                background: `linear-gradient(90deg, ${p.deptColor} 0%, ${p.deptColor}99 100%)`,
              }}></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Source Breakdown — nguồn tuyển dụng
   ══════════════════════════════════════════════════════════════ */
function SourceBreakdown() {
  const counts = {};
  APPLICANTS.forEach(a => { counts[a.source] = (counts[a.source] || 0) + 1; });

  const colors = {
    Facebook: '#1877F2', TopCV: '#15803D', Referral: '#D9A400',
    Website: '#C8102E', TikTok: '#010101',
  };

  const data = Object.entries(counts)
    .map(([label, val]) => ({ label, val, color: colors[label] || '#78716C' }))
    .sort((a, b) => b.val - a.val);

  return (
    <div className="card">
      <div className="card-head">
        <h3>Nguồn ứng viên</h3>
        <Badge kind="gray">{data.length} kênh</Badge>
      </div>
      <div className="card-pad">
        <Donut data={data} total={APPLICANTS.length} label="ứng viên"/>

        <div style={{ marginTop: 18, borderTop: '1px solid var(--border)', paddingTop: 14 }}>
          <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: 10 }}>
            Kênh hiệu quả nhất
          </div>
          {data.slice(0, 3).map((d, i) => {
            const hired = APPLICANTS.filter(a => a.source === d.label && a.stage === 'hired').length;
            const rate = d.val > 0 ? Math.round(hired / d.val * 100) : 0;
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '6px 0', borderBottom: i < 2 ? '1px solid var(--border)' : 'none',
              }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: d.color, flexShrink: 0 }}></span>
                <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>{d.label}</span>
                <span style={{ fontSize: 11.5, color: 'var(--muted)' }}>{d.val} UV</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                  background: hired > 0 ? 'var(--green-bg)' : 'var(--surface-2)',
                  color: hired > 0 ? 'var(--green)' : 'var(--faint)',
                }}>
                  {rate}% hired
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Open Jobs — vị trí đang tuyển
   ══════════════════════════════════════════════════════════════ */
function OpenJobsCard({ setView }) {
  const priorityColor = { 'Cao': 'red', 'Trung bình': 'amber', 'Thấp': 'blue' };

  return (
    <div className="card">
      <div className="card-head">
        <h3>Vị trí đang tuyển</h3>
        <Badge kind="gray">{REC_JOBS.length} vị trí</Badge>
        <div className="actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setView('jobs')}>
            Quản lý vị trí <Icon name="chevR" size={14}/>
          </button>
        </div>
      </div>
      <div style={{ padding: '14px 16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {REC_JOBS.map(j => {
            const filled = j.filled;
            const open = j.headcount - filled;
            const pct = Math.round(filled / j.headcount * 100);
            const daysLeft = Math.round(
              (new Date(j.deadline) - new Date('2026-06-09')) / 86400000
            );

            return (
              <div key={j.id} className="job-card">
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                  <Badge kind={priorityColor[j.priority] || 'gray'}>{j.priority}</Badge>
                  <span style={{
                    fontSize: 11, color: daysLeft <= 10 ? 'var(--red-600)' : 'var(--muted)',
                    fontWeight: 600,
                  }}>
                    <Icon name="calendar" size={11}/> {daysLeft}d còn lại
                  </span>
                </div>

                {/* Title + dept */}
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 14, fontWeight: 800, lineHeight: 1.2, marginBottom: 3 }}>
                    {j.title}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 7, height: 7, borderRadius: 2, background: j.deptColor, flexShrink: 0 }}></span>
                    {j.dept} · {j.type}
                  </div>
                </div>

                {/* Salary */}
                <div style={{ fontSize: 12, color: 'var(--green)', fontWeight: 700, marginBottom: 10 }}>
                  {j.salary}
                </div>

                {/* Fill progress */}
                <div style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, marginBottom: 5 }}>
                    <span className="muted">Đã tuyển: <b style={{ color: 'var(--ink)' }}>{filled}/{j.headcount}</b></span>
                    <span style={{ color: open > 0 ? 'var(--red-600)' : 'var(--green)', fontWeight: 700 }}>
                      {open > 0 ? `Còn ${open} suất` : 'Đã đủ'}
                    </span>
                  </div>
                  <div className="bar" style={{ height: 6 }}>
                    <span style={{
                      width: pct + '%',
                      background: open === 0 ? 'var(--green)' : j.deptColor,
                    }}></span>
                  </div>
                </div>

                {/* Tags */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {j.tags.map(tag => (
                    <span key={tag} style={{
                      fontSize: 10.5, background: 'var(--surface-2)', color: 'var(--ink-soft)',
                      border: '1px solid var(--border)', borderRadius: 5, padding: '2px 7px', fontWeight: 600,
                    }}>{tag}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Upcoming Interviews — lịch phỏng vấn sắp tới
   ══════════════════════════════════════════════════════════════ */
function UpcomingInterviewsCard({ interviews, stageMap }) {
  const today = '2026-06-09';

  return (
    <div className="card">
      <div className="card-head">
        <h3>Lịch phỏng vấn sắp tới</h3>
        <Badge kind="violet" dot>{interviews.length} lịch</Badge>
        <div className="actions">
          <button className="btn btn-ghost btn-sm">
            <Icon name="calendar" size={13}/> Thêm lịch
          </button>
        </div>
      </div>

      {interviews.length === 0 ? (
        <div style={{ padding: '30px 20px', textAlign: 'center', color: 'var(--faint)' }}>
          <Icon name="calendar" size={32}/>
          <div style={{ marginTop: 10, fontSize: 13 }}>Chưa có lịch phỏng vấn nào</div>
        </div>
      ) : (
        <div style={{ padding: '8px 12px' }}>
          {interviews.slice(0, 7).map((a, i) => {
            const st = stageMap[a.stage];
            const isToday = a.interview === today;
            const [, mon, day] = a.interview.split('-');

            return (
              <div key={a.id} style={{
                display: 'flex', gap: 12, padding: '10px 10px',
                borderRadius: 10, alignItems: 'center', marginBottom: 2,
                background: isToday ? 'var(--violet-bg)' : 'transparent',
                border: isToday ? '1px solid var(--violet-bg)' : '1px solid transparent',
                transition: 'background .12s',
              }}
              onMouseEnter={e => { if (!isToday) e.currentTarget.style.background = 'var(--surface-2)'; }}
              onMouseLeave={e => { if (!isToday) e.currentTarget.style.background = 'transparent'; }}>
                {/* Date badge */}
                <div style={{
                  width: 44, textAlign: 'center', flexShrink: 0,
                  background: isToday ? 'var(--violet)' : 'var(--surface-2)',
                  borderRadius: 10, padding: '6px 0',
                  border: '1px solid ' + (isToday ? 'var(--violet)' : 'var(--border)'),
                }}>
                  <div style={{
                    fontSize: 17, fontWeight: 800, lineHeight: 1,
                    color: isToday ? '#fff' : 'var(--ink)',
                  }}>{day}</div>
                  <div style={{
                    fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase',
                    color: isToday ? 'rgba(255,255,255,.8)' : 'var(--muted)',
                  }}>T{parseInt(mon)}</div>
                  {isToday && (
                    <div style={{ fontSize: 8, color: 'rgba(255,255,255,.8)', fontWeight: 700 }}>
                      HÔM NAY
                    </div>
                  )}
                </div>

                {/* Avatar */}
                <Avatar emp={a} size={36}/>

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: isToday ? 'var(--violet)' : 'var(--ink)' }}>
                    {a.name}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 1 }}>{a.pos}</div>
                </div>

                {/* Stage badge */}
                <div style={{
                  fontSize: 11, fontWeight: 700,
                  color: st?.color || 'var(--muted)',
                  background: (st?.color || '#78716C') + '18',
                  borderRadius: 6, padding: '3px 8px', whiteSpace: 'nowrap',
                }}>
                  {st?.name}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   Recent Applicants — ứng viên mới nhất
   ══════════════════════════════════════════════════════════════ */
function RecentApplicantsCard({ apps, stageMap, setView }) {
  return (
    <div className="card">
      <div className="card-head">
        <h3>Ứng viên mới nhất</h3>
        <div className="actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setView('applicants')}>
            Xem tất cả <Icon name="chevR" size={14}/>
          </button>
        </div>
      </div>

      <div style={{ padding: '6px 12px' }}>
        {apps.map((a, i) => {
          const st = stageMap[a.stage];
          return (
            <div key={a.id} style={{
              display: 'flex', gap: 12, padding: '11px 10px',
              alignItems: 'center', borderRadius: 10, marginBottom: 2,
              transition: 'background .12s', cursor: 'pointer',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              {/* Avatar */}
              <Avatar emp={a} size={40}/>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>{a.name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 1 }}>
                  {a.pos} · {a.exp}
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 4, alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--faint)', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                    <Icon name="clock" size={10}/> {a.days} ngày trước
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--faint)' }}>·</span>
                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>{a.source}</span>
                </div>
              </div>

              {/* Stage + rating */}
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{
                  fontSize: 11, fontWeight: 700,
                  color: st?.color || 'var(--muted)',
                  background: (st?.color || '#78716C') + '18',
                  borderRadius: 6, padding: '3px 8px',
                  marginBottom: 5, whiteSpace: 'nowrap',
                }}>
                  {st?.name}
                </div>
                <Stars n={a.rating} size={11}/>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, {
  RecDashboard, PipelineSummary, TaskPanel,
  PositionBreakdown, SourceBreakdown, OpenJobsCard,
  UpcomingInterviewsCard, RecentApplicantsCard,
});
