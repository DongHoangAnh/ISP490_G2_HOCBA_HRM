import React, { useState, useEffect } from 'react';
import { fetchAttendanceConfig, saveAttendanceConfig } from '../../api/attendance';
import { LoadingState, ErrorState } from '../../components/states';
import Icon from '../../components/Icon';
import CycleTab from './CycleTab';
import PolicyTab from './PolicyTab';

const TABS = [
  { id: 'cycle', label: 'Chu kỳ tính công', icon: 'rotateCcw' },
  { id: 'policy', label: 'Cấu hình hệ thống', icon: 'settings' },
];

export default function AttendanceConfig() {
  const [tab, setTab] = useState(() => localStorage.getItem('attendance_config_tab') || 'cycle');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [history, setHistory] = useState([]);
  const [deletedIds, setDeletedIds] = useState([]);

  const loadConfig = () => {
    setLoading(true);
    fetchAttendanceConfig()
      .then((res) => {
        setData(res);
        setHistory(res.history || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadConfig();
  }, []);

  useEffect(() => {
    localStorage.setItem('attendance_config_tab', tab);
  }, [tab]);

  const handleSave = () => {
    setSaving(true);
    const payload = {
      ...data,
      history: history.map(h => ({
        id: h.id,
        applyFrom: h.applyFrom,
        periodStartDay: h.periodStartDay
      })),
      deleteHistoryIds: deletedIds
    };

    saveAttendanceConfig(payload)
      .then((res) => {
        setData(res);
        setHistory(res.history || []);
        setDeletedIds([]);
        setSaving(false);
        alert('Đã lưu cấu hình thành công!');
      })
      .catch((e) => {
        alert('Lỗi: ' + e.message);
        setSaving(false);
      });
  };

  if (loading && !data) return <LoadingState label="Đang tải cấu hình…" />;
  if (error) return <ErrorState message={error} onRetry={loadConfig} />;

  return (
    <div className="content fade-in" style={{ paddingBottom: 40 }}>
      <div className="page-head" style={{ marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--ink)' }}>Cấu hình Chấm công</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14 }}>Thiết lập chu kỳ, khung giờ và các quy tắc chấm công hệ thống</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ height: 42, padding: '0 20px' }}>
            <Icon name="checkCircle" size={18} className="mr-s" />
            {saving ? 'Đang lưu…' : 'Lưu cấu hình'}
          </button>
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: 24 }}>
        {TABS.map((t) => (
          <button key={t.id}
            className={'tab' + (tab === t.id ? ' active' : '')}
            onClick={() => setTab(t.id)}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name={t.icon} size={16} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {tab === 'cycle' && (
          <CycleTab data={data} setData={setData}
            history={history} setHistory={setHistory}
            deletedIds={deletedIds} setDeletedIds={setDeletedIds} />
        )}
        {tab === 'policy' && <PolicyTab data={data} setData={setData} />}
      </div>
    </div>
  );
}
