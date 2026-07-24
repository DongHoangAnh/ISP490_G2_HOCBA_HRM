/* Trung tâm Cấu hình Time Off (chỉ Admin).
   Tab "Loại nghỉ" + "Chính sách" + "Ngày lễ" + "Tích lũy". */
import { useState } from 'react';
import LeaveTypesTab from './LeaveTypesTab';
import PoliciesTab from './PoliciesTab';
import HolidaysTab from './HolidaysTab';
import AccrualTab from './AccrualTab';

const TABS = [
  { id: 'types', label: 'Loại nghỉ' },
  { id: 'policies', label: 'Chính sách' },
  { id: 'holidays', label: 'Ngày lễ' },
  { id: 'accrual', label: 'Tích lũy' },
];

export default function TimeoffConfig() {
  const [tab, setTab] = useState('types');
  return (
    <div className="content fade-in">
      <div className="tabs">
        {TABS.map((t) => (
          <button key={t.id}
            className={'tab' + (tab === t.id ? ' active' : '')}
            disabled={t.disabled}
            title={t.disabled ? 'Sắp có' : ''}
            onClick={() => !t.disabled && setTab(t.id)}>
            {t.label}{t.disabled ? ' (sắp có)' : ''}
          </button>
        ))}
      </div>
      {tab === 'types' && <LeaveTypesTab />}
      {tab === 'policies' && <PoliciesTab />}
      {tab === 'holidays' && <HolidaysTab />}
      {tab === 'accrual' && <AccrualTab />}
    </div>
  );
}
