import React, { useState, useEffect } from 'react';
import { fetchSaleSalaryLevels, createSaleSalaryLevel, updateSaleSalaryLevel, deleteSaleSalaryLevel } from '../../api/payroll';
import Icon from '../../components/Icon';

export default function SaleLevelConfig() {
  const [levels, setLevels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const [form, setForm] = useState({
    levelCode: '',
    name: '',
    sequence: 10,
    kpiTarget: 1.0,
    baseWage: 7000000,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchSaleSalaryLevels();
      setLevels(res || []);
    } catch (err) {
      console.error('Error loading sale levels:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setForm({
        levelCode: item.levelCode || '',
        name: item.name || '',
        sequence: item.sequence || 10,
        kpiTarget: item.kpiTarget || 1.0,
        baseWage: item.baseWage || 7000000,
      });
    } else {
      setEditingItem(null);
      const nextSeq = (levels.length + 1) * 10;
      setForm({
        levelCode: `LEVEL_${levels.length + 1}`,
        name: `Level ${levels.length + 1} - Khởi đầu`,
        sequence: nextSeq,
        kpiTarget: 1.0 + levels.length * 0.5,
        baseWage: 7000000 + levels.length * 2000000,
      });
    }
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.levelCode) {
      alert('Vui lòng điền mã và tên Level!');
      return;
    }
    setSaving(true);
    try {
      if (editingItem) {
        await updateSaleSalaryLevel(editingItem.id, form);
      } else {
        await createSaleSalaryLevel(form);
      }
      setShowModal(false);
      loadData();
    } catch (err) {
      alert('Lỗi lưu Level: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Bạn có chắc chắn muốn xóa Level sale này không?')) return;
    try {
      await deleteSaleSalaryLevel(id);
      loadData();
    } catch (err) {
      alert('Lỗi xóa Level: ' + err.message);
    }
  };

  return (
    <div style={{ padding: '16px 0' }}>
      {/* Header Banner */}
      <div
        style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          padding: '16px 20px',
          borderRadius: 12,
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0f172a' }}>
            🎯 Cấu hình Bảng Lương Sale theo Level KPI
          </h4>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#64748b' }}>
            Áp dụng riêng cho <b>Nhân viên Sale chính thức</b>. Hệ thống tự động lấy điểm KPI tháng để áp mức Lương cơ bản tương ứng.
          </p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '9px 16px',
            borderRadius: 8,
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            color: '#fff',
            border: 'none',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
          }}
        >
          <Icon name="plus" size={16} /> Thêm Level mới
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: '#64748b', fontSize: 14 }}>
          🔄 Đang tải cấu hình Level Sale...
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                <th style={{ padding: '12px 16px', width: 60 }}>STT</th>
                <th style={{ padding: '12px 16px' }}>Mã Level</th>
                <th style={{ padding: '12px 16px' }}>Tên ngạch hiển thị</th>
                <th style={{ padding: '12px 16px' }}>Mốc KPI tối thiểu</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Lương cơ bản theo Level</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', width: 100 }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {levels.map((item, index) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 16px', color: '#64748b', fontWeight: 600 }}>{index + 1}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#2563eb', fontFamily: 'monospace' }}>{item.levelCode}</td>
                  <td style={{ padding: '14px 16px', fontWeight: 700, color: '#0f172a' }}>{item.name}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ padding: '4px 10px', borderRadius: 20, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', fontWeight: 700, fontSize: 12 }}>
                      ≥ {item.kpiTarget} KPI
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: '#059669', fontSize: 14, fontFamily: 'monospace' }}>
                    {Number(item.baseWage || 0).toLocaleString('vi-VN')} ₫
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 4 }}>
                      <button
                        onClick={() => handleOpenModal(item)}
                        style={{
                          border: '1px solid #cbd5e1',
                          background: '#fff',
                          color: '#475569',
                          borderRadius: 6,
                          padding: '5px 8px',
                          cursor: 'pointer',
                        }}
                        title="Chỉnh sửa"
                      >
                        <Icon name="edit" size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        style={{
                          border: '1px solid #fca5a5',
                          background: '#fef2f2',
                          color: '#dc2626',
                          borderRadius: 6,
                          padding: '5px 8px',
                          cursor: 'pointer',
                        }}
                        title="Xóa"
                      >
                        <Icon name="trash" size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', backdropFilter: 'blur(3px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
          <div style={{ background: '#fff', width: 440, borderRadius: 16, padding: 24, boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#0f172a' }}>
                {editingItem ? '✏️ Chỉnh sửa Level Sale' : '✨ Thêm mới Level Sale'}
              </h3>
              <button onClick={() => setShowModal(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', fontSize: 18 }}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>Mã Level <span style={{ color: '#dc2626' }}>*</span></label>
                <input
                  type="text"
                  value={form.levelCode}
                  onChange={(e) => setForm({ ...form, levelCode: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13.5, fontFamily: 'monospace', boxSizing: 'border-box' }}
                  placeholder="LEVEL_1"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>Tên ngạch hiển thị <span style={{ color: '#dc2626' }}>*</span></label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13.5, boxSizing: 'border-box' }}
                  placeholder="Level 1 - Khởi đầu"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>Mốc KPI tối thiểu</label>
                  <input
                    type="number"
                    step="0.1"
                    value={form.kpiTarget}
                    onChange={(e) => setForm({ ...form, kpiTarget: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13.5, boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>Lương cơ bản (VND)</label>
                  <input
                    type="number"
                    step="500000"
                    value={form.baseWage}
                    onChange={(e) => setForm({ ...form, baseWage: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13.5, fontFamily: 'monospace', fontWeight: 600, boxSizing: 'border-box' }}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
              <button
                onClick={() => setShowModal(false)}
                style={{ padding: '9px 16px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#fff', color: '#475569', fontWeight: 600, cursor: 'pointer' }}
              >
                Hủy
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{ padding: '9px 20px', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)', color: '#fff', fontWeight: 600, cursor: 'pointer', boxShadow: '0 2px 4px rgba(37,99,235,0.25)' }}
              >
                {saving ? '⏳ Đang lưu...' : 'Lưu Level'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
