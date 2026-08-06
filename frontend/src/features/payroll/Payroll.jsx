/* Màn Bảng lương — điều phối tab.
   Owner: Hùng. API: /hocba-hrm/api/payroll/* */
import { useState } from 'react';
import BatchList from './BatchList';
import BankFile from './BankFile';
import ConfigView from './ConfigView';
import SalaryHistory from './SalaryHistory';

const TABS = [
  ['batches', 'Kỳ tính lương'],
  ['history', 'Lịch sử lương'],
  ['bank', 'File chi lương Bank'],
  ['config', 'Cấu hình lương'],
];

export default function Payroll({ search }) {
  const [tab, setTab] = useState(() => localStorage.getItem('hocba_payroll_tab') || 'batches');

  const select = (id) => { setTab(id); localStorage.setItem('hocba_payroll_tab', id); };

  return (
    <div className="content fade-in" style={{
      display: 'flex', flexDirection: 'column',
      height: 'calc(100vh - var(--topbar-h, 64px))',
      paddingTop: 10, paddingBottom: 0, overflow: 'hidden',
    }}>
      <div className="tabs" style={{ marginTop: 0, marginBottom: 10, flexShrink: 0 }}>
        {TABS.map(([id, l]) => (
          <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => select(id)}>{l}</button>
        ))}
      </div>

      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: (tab === 'batches' || tab === 'history') ? 'hidden' : 'auto' }}>
        {tab === 'batches' && <BatchList search={search} />}
        {tab === 'history' && <SalaryHistory />}
        {tab === 'bank' && <BankFile />}
        {tab === 'config' && <ConfigView />}
      </div>
    </div>
  );
}
