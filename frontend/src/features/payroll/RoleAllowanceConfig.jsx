import React, { useState, useEffect } from 'react';
import { fetchRoleAllowanceConfigs, createRoleAllowanceConfig, deleteRoleAllowanceConfig } from '../../api/payroll';
import Icon from '../../components/Icon';

export default function RoleAllowanceConfig() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const [form, setForm] = useState({
    name: '',
    allowanceType: 'position_allowance',
    amount: 1000000,
    notes: '',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchRoleAllowanceConfigs();
      setConfigs(res || []);
    } catch (err) {
      console.error('Error loading role allowance configs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async () => {
    if (!form.name || !form.amount) {
      alert('Vui lòng điền tên khoản thưởng/phụ cấp và số tiền!');
      return;
    }
    setSaving(true);
    try {
      await createRoleAllowanceConfig(form);
      setShowModal(false);
      setForm({ name: '', allowanceType: 'position_allowance', amount: 1000000, notes: '' });
      loadData();
    } catch (err) {
      alert('Lỗi lưu cấu hình: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Bạn có chắc chắn muốn xóa cấu hình phụ cấp này không?')) return;
    try {
      await deleteRoleAllowanceConfig(id);
      loadData();
    } catch (err) {
      alert('Lỗi xóa cấu hình: ' + err.message);
    }
  };

  return (
    <div style={{ padding: '16px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#111827' }}>
            🏛️ Cấu hình Thưởng & Phụ cấp cố định theo Chức vụ / Phòng ban
          </h4>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>
            Cấu hình 1 lần áp dụng tự động cho toàn bộ Nhân viên thuộc Chức vụ / Vị trí đó khi tính lương hàng tháng.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 8, background: '#2563eb', color: '#fff',
            border: 'none', fontWeight: 600, fontSize: 13, cursor: 'pointer',
          }}
        >
          <Icon name="plus" size={16} /> Thêm Cấu hình Phụ cấp
        </button>
      </div>

      {loading ? (
        <div style={{ padding: 20, textAlign: 'center', color: '#6b7280' }}>Đang tải cấu hình phụ cấp...</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: 8, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <thead>
            <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#374151' }}>
              <th style={{ padding: '10px 14px' }}>Tên khoản Phụ cấp / Thưởng</th>
              <th style={{ padding: '10px 14px' }}>Chức vụ áp dụng</th>
              <th style={{ padding: '10px 14px' }}>Phòng ban</th>
              <th style={{ padding: '10px 14px' }}>Loại khoản</th>
              <th style={{ padding: '10px 14px' }}>Số tiền (VND)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {configs.map((item) => (
              <tr key={item.id} style={{ borderBottom: '1px solid #f3f4f6', fontSize: 13 }}>
                <td style={{ padding: '12px 14px', fontWeight: 700, color: '#111827' }}>{item.name}</td>
                <td style={{ padding: '12px 14px', color: '#4b5563' }}>{item.jobName}</td>
                <td style={{ padding: '12px 14px', color: '#4b5563' }}>{item.departmentName}</td>
                <td style={{ padding: '12px 14px' }}>
                  <span style={{ padding: '3px 8px', borderRadius: 12, background: '#fef3c7', color: '#92400e', fontWeight: 600, fontSize: 12 }}>
                    {item.allowanceType === 'responsibility' ? 'Trách nhiệm' : item.allowanceType === 'holiday_bonus' ? 'Thưởng Lễ/Tết' : 'Phụ cấp Chức vụ'}
                  </span>
                </td>
                <td style={{ padding: '12px 14px', fontWeight: 700, color: '#059669' }}>
                  {item.amount ? item.amount.toLocaleString('vi-VN') : 0} đ
                </td>
                <td style={{ padding: '12px 14px', textAlign: 'right' }}>
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
              Thêm mới Thưởng / Phụ cấp theo Role
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Tên khoản Thưởng / Phụ cấp</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                  placeholder="VD: Phụ cấp Trách nhiệm Trưởng phòng"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Loại khoản</label>
                <select
                  value={form.allowanceType}
                  onChange={(e) => setForm({ ...form, allowanceType: e.target.value })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}
                >
                  <option value="position_allowance">Phụ cấp Chức vụ</option>
                  <option value="responsibility">Phụ cấp Trách nhiệm</option>
                  <option value="holiday_bonus">Thưởng Lễ / Tết</option>
                  <option value="other">Khác</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Số tiền (VND)</label>
                <input
                  type="number"
                  step="100000"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
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
                {saving ? 'Đang lưu...' : 'Lưu cấu hình'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
