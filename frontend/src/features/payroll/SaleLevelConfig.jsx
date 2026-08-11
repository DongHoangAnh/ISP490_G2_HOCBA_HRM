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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#111827' }}>
            🎯 Cấu hình Bảng Lương Sale theo Level KPI
          </h4>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>
            Chỉ áp dụng cho <b>Nhân viên Sale chính thức</b>. Cuối tháng tự động đối chiếu điểm KPI đạt được để áp mức Lương cơ bản tương ứng.
          </p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 8, background: '#2563eb', color: '#fff',
            border: 'none', fontWeight: 600, fontSize: 13, cursor: 'pointer',
          }}
        >
          <Icon name="plus" size={16} /> Thêm Level mới
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 20, textAlign: 'center', color: '#6b7280' }}>Đang tải cấu hình Level Sale...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 8, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <thead>
            <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#374151' }}>
              <th style={{ padding: '10px 14px', width: 60 }}>STT</th>
              <th style={{ padding: '10px 14px' }}>Mã Level</th>
              <th style={{ padding: '10px 14px' }}>Tên hiển thị</th>
              <th style={{ padding: '10px 14px' }}>Chỉ số KPI tối thiểu</th>
              <th style={{ padding: '10px 14px' }}>Lương cơ bản (VND)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {levels.map((item, index) => (
              <tr key={item.id} style={{ borderBottom: '1px solid #f3f4f6', fontSize: 13 }}>
                <td style={{ padding: '12px 14px', color: '#6b7280', fontWeight: 600 }}>{index + 1}</td>
                <td style={{ padding: '12px 14px', fontWeight: 700, color: '#2563eb' }}>{item.levelCode}</td>
                <td style={{ padding: '12px 14px', fontWeight: 600, color: '#111827' }}>{item.name}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span style={{ padding: '3px 8px', borderRadius: 12, background: '#eff6ff', color: '#1d4ed8', fontWeight: 700, fontSize: 12 }}>
                    ≥ {item.kpiTarget} KPI
                  </span>
                </td>
                <td style={{ padding: '12px 14px', fontWeight: 700, color: '#059669' }}>
                  {item.baseWage ? item.baseWage.toLocaleString('vi-VN') : 0} đ
                </td>
                <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                  <button
                    onClick={() => handleOpenModal(item)}
                    style={{ border: 'none', background: 'transparent', color: '#2563eb', cursor: 'pointer', padding: 4, marginRight: 8 }}
                    title="Chỉnh sửa"
                  >
                    <Icon name="edit" size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    style={{ border: 'none', background: 'transparent', color: '#dc2626', cursor: 'pointer', padding: 4 }}
                    title="Xóa"
                  >
                    <Icon name="trash2" size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: '#fff', width: 440, borderRadius: 12, padding: 20, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 700 }}>
              {editingItem ? 'Chỉnh sửa Level Sale' : 'Thêm mới Level Sale'}
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Mã Level</label>
                <input
                  type="text"
                  value={form.levelCode}
                  onChange={(e) => setForm({ ...form, levelCode: e.target.value })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                  placeholder="LEVEL_1"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Tên hiển thị</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                  placeholder="Level 1 - Khởi đầu"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Chỉ số KPI tối thiểu</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.kpiTarget}
                  onChange={(e) => setForm({ ...form, kpiTarget: parseFloat(e.target.value) || 0 })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Lương cơ bản theo Level (VND)</label>
                <input
                  type="number"
                  step="500000"
                  value={form.baseWage}
                  onChange={(e) => setForm({ ...form, baseWage: parseFloat(e.target.value) || 0 })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button
                onClick={() => setShowModal(false)}
                style={{ padding: '8px 14px', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer' }}
              >
                Hủy
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{ padding: '8px 14px', borderRadius: 6, border: 'none', background: '#2563eb', color: '#fff', fontWeight: 600, cursor: 'pointer' }}
              >
                {saving ? 'Đang lưu...' : 'Lưu Level'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
