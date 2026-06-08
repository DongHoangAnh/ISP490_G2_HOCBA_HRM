/* ============================================================
   HOC BA HRM — App root
   ============================================================ */

function App() {
  const [view, setView] = useState(()=> localStorage.getItem('hocba_view') || 'dashboard');
  const [search, setSearch] = useState('');

  useEffect(()=>{ localStorage.setItem('hocba_view', view); setSearch(''); }, [view]);

  return (
    <div className="app">
      <Sidebar view={view} setView={setView} />
      <div className="main">
        <Topbar view={view} onSearch={setSearch} onProfile={()=>setView('profile')} />
        {view==='dashboard'   && <Dashboard setView={setView} />}
        {view==='employees'   && <Employees search={search} />}
        {view==='onboarding'  && <Onboarding search={search} />}
        {view==='attendance'  && <Attendance search={search} />}
        {view==='timeoff'     && <TimeOff search={search} />}
        {view==='payroll'     && <Payroll search={search} />}
        {view==='contracts'   && <Contracts search={search} />}
        {view==='recruitment' && <Recruitment search={search} />}
        {view==='appraisal'   && <Appraisal search={search} />}
        {view==='reports'     && <Reports />}
        {view==='profile'     && <Profile setView={setView} />}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
