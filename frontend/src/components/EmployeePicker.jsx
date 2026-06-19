/* Chọn nhân viên — search dropdown + tạo mới. Owner: Hùng. */
import { useState, useEffect, useRef } from 'react';
import { fetchFormMeta } from '../api/employees';
import Icon from './Icon';
import EmployeeQuickForm from './EmployeeQuickForm';

export default function EmployeePicker({ value, onChange, disabled }) {
  const [employees, setEmployees] = useState([]);
  const [meta, setMeta] = useState(null);
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    fetchFormMeta().then((m) => {
      setMeta(m);
      setEmployees(m.employees || []);
    }).catch(() => {});
  }, []);

  /* close dropdown on outside click */
  useEffect(() => {
    const handler = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selected = value ? employees.find((e) => e.id === Number(value)) : null;

  const filtered = query
    ? employees.filter((e) => e.name.toLowerCase().includes(query.toLowerCase())).slice(0, 20)
    : employees.slice(0, 20);

  const handleSelect = (emp) => {
    onChange(emp.id, emp.name);
    setQuery('');
    setOpen(false);
  };

  const handleClear = () => {
    onChange('', '');
    setQuery('');
  };

  const handleCreated = (emp) => {
    setEmployees((prev) => [...prev, emp]);
    setCreating(false);
    handleSelect(emp);
  };

  const inp = {
    width: '100%', padding: '9px 12px', paddingLeft: 34, paddingRight: value ? 34 : 12,
    borderRadius: 8, border: '1px solid var(--border)', fontSize: 14,
    background: '#fff',
  };

  return (
    <>
      <div ref={wrapRef} style={{ position: 'relative' }}>
        {/* search icon */}
        <div style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)', pointerEvents: 'none' }}>
          <Icon name="search" size={15} />
        </div>

        {selected && !open ? (
          /* selected state */
          <div style={{
            ...inp, display: 'flex', alignItems: 'center', gap: 8, cursor: disabled ? 'default' : 'pointer',
            background: 'var(--gray-50)',
          }} onClick={() => !disabled && setOpen(true)}>
            <Icon name="user" size={15} />
            <span style={{ flex: 1, fontWeight: 600 }}>{selected.name}</span>
            {!disabled && (
              <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: 'var(--muted)' }}
                onClick={(e) => { e.stopPropagation(); handleClear(); }}>
                <Icon name="x" size={14} />
              </button>
            )}
          </div>
        ) : (
          /* search input */
          <input
            type="text"
            style={inp}
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            placeholder="Tìm nhân viên..."
            disabled={disabled}
          />
        )}

        {/* dropdown list */}
        {open && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
            background: '#fff', border: '1px solid var(--border)', borderRadius: 8,
            boxShadow: '0 4px 16px rgba(0,0,0,.12)', maxHeight: 260, overflowY: 'auto',
            marginTop: 4,
          }}>
            {filtered.length === 0 && (
              <div style={{ padding: '12px 14px', color: 'var(--muted)', fontSize: 13.5 }}>
                Không tìm thấy nhân viên
              </div>
            )}
            {filtered.map((emp) => (
              <div key={emp.id}
                style={{
                  padding: '9px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                  fontSize: 13.5, borderBottom: '1px solid var(--gray-100)',
                }}
                onMouseDown={() => handleSelect(emp)}
              >
                <Icon name="user" size={14} />
                <span style={{ fontWeight: 500 }}>{emp.name}</span>
                <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 'auto' }}>ID: {emp.id}</span>
              </div>
            ))}
            {/* create new */}
            <div
              style={{
                padding: '10px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                fontSize: 13.5, color: 'var(--red-600)', fontWeight: 600,
                borderTop: filtered.length > 0 ? '1px solid var(--border)' : 'none',
                background: 'var(--gray-50)',
              }}
              onMouseDown={() => { setOpen(false); setCreating(true); }}
            >
              <Icon name="plus" size={14} />
              Tạo nhân viên mới
            </div>
          </div>
        )}
      </div>

      {creating && meta && (
        <EmployeeQuickForm
          meta={meta}
          onClose={() => setCreating(false)}
          onCreated={handleCreated}
        />
      )}
    </>
  );
}
