/* Trung tâm Cấu hình Time Off (chỉ Admin). Phase 1: tab "Loại nghỉ".
   Các tab Chính sách / Ngày lễ / Tích lũy sẽ bổ sung ở phase sau. */
import { useState } from 'react';
import LeaveTypesTab from './LeaveTypesTab';

const TABS = [
  { id: 'types', label: 'Loại nghỉ' },
  { id: 'policies', label: 'Chính sách', disabled: true },
  { id: 'holidays', label: 'Ngày lễ', disabled: true },
  { id: 'accrual', label: 'Tích lũy', disabled: true },
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
    </div>
  );
}
