/* Màn Bảng lương — điều phối tab.
   Owner: Hùng. API: /hocba-hrm/api/payroll/* */
import { useState } from 'react';
import BatchList from './BatchList';
import SaleRevenue from './SaleRevenue';
import BankFile from './BankFile';
import BhxhReport from './BhxhReport';
import EtaxReport from './EtaxReport';
import ConfigView from './ConfigView';
import SalaryHistory from './SalaryHistory';

const TABS = [
  ['batches', 'Bảng lương'],
  ['history', 'Lịch sử lương'],
  ['revenue', 'Doanh thu sale'],
  ['bank', 'Chuyển khoản'],
  ['bhxh', 'BHXH'],
  ['etax', 'Thuế TNCN'],
  ['config', 'Cấu hình'],
];

export default function Payroll({ search }) {
  const [tab, setTab] = useState(() => localStorage.getItem('hocba_payroll_tab') || 'batches');

  const select = (id) => { setTab(id); localStorage.setItem('hocba_payroll_tab', id); };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Bảng lương</h1>
          <p>Quản lý bảng lương, chuyển khoản, bảo hiểm &amp; thuế</p>
        </div>
      </div>

      <div className="tabs">
        {TABS.map(([id, l]) => (
          <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => select(id)}>{l}</button>
        ))}
      </div>

      {tab === 'batches' && <BatchList search={search} />}
      {tab === 'history' && <SalaryHistory />}
      {tab === 'revenue' && <SaleRevenue />}
      {tab === 'bank' && <BankFile />}
      {tab === 'bhxh' && <BhxhReport />}
      {tab === 'etax' && <EtaxReport />}
      {tab === 'config' && <ConfigView />}
    </div>
  );
}
