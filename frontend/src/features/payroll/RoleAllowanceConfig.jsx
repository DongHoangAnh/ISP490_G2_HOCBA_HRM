import React, { useState, useEffect } from 'react';
import { fetchRoleAllowanceConfigs, createRoleAllowanceConfig, deleteRoleAllowanceConfig } from '../../api/payroll';
import { fetchFormMeta } from '../../api/employees';
import Icon from '../../components/Icon';

const TYPE_CONFIG = {
  position_allowance: { label: 'Phụ cấp Chức vụ', bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe', icon: 'shield' },
  responsibility: { label: 'Phụ cấp Trách nhiệm', bg: '#fff7ed', color: '#c2410c', border: '#fed7aa', icon: 'award' },
  holiday_bonus: { label: 'Thưởng Lễ / Tết', bg: '#ecfdf5', color: '#047857', border: '#a7f3d0', icon: 'gift' },
  other: { label: 'Khoản trợ cấp khác', bg: '#f3e8ff', color: '#6b21a8', border: '#e9d5ff', icon: 'tag' },
};

export default function RoleAllowanceConfig() {
  const [configs, setConfigs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const [form, setForm] = useState({
    id: null,
    name: '',
    jobId: '',
    departmentId: '',
    allowanceType: 'position_allowance',
    amount: 1000000,
    notes: '',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [cfgRes, metaRes] = await Promise.all([
        fetchRoleAllowanceConfigs(),
        fetchFormMeta().catch(() => ({ jobs: [], departments: [] })),
      ]);
      setConfigs(cfgRes || []);
      setJobs(metaRes?.jobs || []);
      setDepartments(metaRes?.departments || []);
    } catch (err) {
      console.error('Error loading role allowance configs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreateModal = () => {
    setEditingItem(null);
    setForm({
      id: null,
      name: '',
      jobId: '',
      departmentId: '',
      allowanceType: 'position_allowance',
      amount: 1000000,
      notes: '',
    });
    setShowModal(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setForm({
      id: item.id,
      name: item.name,
      jobId: item.jobId || '',
      departmentId: item.departmentId || '',
      allowanceType: item.allowanceType || 'position_allowance',
      amount: item.amount || 0,
      notes: item.notes || '',
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      alert('Vui lòng nhập Tên khoản Thưởng / Phụ cấp!');
      return;
    }
    if (form.amount <= 0) {
      alert('Số tiền phụ cấp phải lớn hơn 0!');
      return;
    }
    setSaving(true);
    try {
      await createRoleAllowanceConfig({
        id: form.id || undefined,
        name: form.name.trim(),
        jobId: form.jobId ? parseInt(form.jobId) : null,
        departmentId: form.departmentId ? parseInt(form.departmentId) : null,
        allowanceType: form.allowanceType,
        amount: parseFloat(form.amount) || 0,
        notes: form.notes.trim(),
      });
      setShowModal(false);
      loadData();
    } catch (err) {
      alert('Lỗi lưu cấu hình: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (item) => {
    if (!confirm(`Bạn có chắc chắn muốn xóa cấu hình phụ cấp "${item.name}" không?`)) return;
    try {
      await deleteRoleAllowanceConfig(item.id);
      loadData();
    } catch (err) {
      alert('Lỗi xóa cấu hình: ' + err.message);
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h4 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0f172a' }}>
              🏛️ Cấu hình Thưởng & Phụ cấp cố định theo Chức vụ / Phòng ban
            </h4>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: '#64748b' }}>
            Cấu hình 1 lần áp dụng tự động cho toàn bộ Nhân viên thuộc Chức vụ hoặc Phòng ban đó khi tính lương hàng tháng.
          </p>
        </div>
        <button
          onClick={openCreateModal}
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
            transition: 'all 0.2s',
          }}
        >
          <Icon name="plus" size={16} /> Thêm Cấu hình Phụ cấp
        </button>
      </div>

      {/* Main Table */}
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: '#64748b', fontSize: 14 }}>
          🔄 Đang tải danh sách cấu hình phụ cấp...
        </div>
      ) : configs.length === 0 ? (
        <div
          style={{
            padding: 48,
            textAlign: 'center',
            background: '#fff',
            borderRadius: 12,
            border: '1px border-dashed #cbd5e1',
            color: '#64748b',
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏛️</div>
          <div style={{ fontWeight: 600, fontSize: 15, color: '#1e293b' }}>Chưa có cấu hình Phụ cấp theo Role nào</div>
          <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 16px' }}>
            Bấm "Thêm Cấu hình Phụ cấp" để tự động gán phụ cấp chức vụ/phòng ban cho nhân viên.
          </p>
          <button
            onClick={openCreateModal}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              fontWeight: 600,
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            + Tạo cấu hình đầu tiên
          </button>
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                <th style={{ padding: '12px 16px' }}>Tên khoản Phụ cấp / Thưởng</th>
                <th style={{ padding: '12px 16px' }}>Chức vụ áp dụng</th>
                <th style={{ padding: '12px 16px' }}>Phòng ban áp dụng</th>
                <th style={{ padding: '12px 16px' }}>Loại khoản</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Số tiền (VND)</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', width: 100 }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((item) => {
                const typeInfo = TYPE_CONFIG[item.allowanceType] || TYPE_CONFIG.other;
                return (
                  <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9', transition: 'background 0.15s' }}>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 700, color: '#0f172a', fontSize: 13.5 }}>{item.name}</div>
                      {item.notes && (
                        <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{item.notes}</div>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {item.jobId ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: '#f1f5f9', color: '#334155', fontWeight: 600, fontSize: 12, border: '1px solid #e2e8f0' }}>
                          💼 {item.jobName}
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: '#f8fafc', color: '#64748b', fontWeight: 500, fontSize: 12 }}>
                          🌐 Tất cả chức vụ
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {item.departmentId ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: '#f1f5f9', color: '#334155', fontWeight: 600, fontSize: 12, border: '1px solid #e2e8f0' }}>
                          🏢 {item.departmentName}
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 10px', borderRadius: 6, background: '#f8fafc', color: '#64748b', fontWeight: 500, fontSize: 12 }}>
                          🌐 Tất cả phòng ban
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '4px 10px',
                          borderRadius: 20,
                          background: typeInfo.bg,
                          color: typeInfo.color,
                          border: `1px solid ${typeInfo.border}`,
                          fontWeight: 600,
                          fontSize: 12,
                        }}
                      >
                        {typeInfo.label}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: '#059669', fontSize: 14, fontFamily: 'monospace' }}>
                      +{Number(item.amount || 0).toLocaleString('vi-VN')} ₫
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 4 }}>
                        <button
                          onClick={() => openEditModal(item)}
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
                          onClick={() => handleDelete(item)}
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
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal CRUD */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.5)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            zIndex: 9999,
          }}
        >
          <div
            style={{
              background: '#fff',
              width: 500,
              maxWidth: '92vw',
              borderRadius: 16,
              padding: 24,
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              border: '1px solid #e2e8f0',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#0f172a' }}>
                {editingItem ? '✏️ Chỉnh sửa Cấu hình Phụ cấp' : '✨ Thêm mới Thưởng / Phụ cấp theo Role'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#64748b', fontSize: 18 }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Tên khoản */}
              <div>
                <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                  Tên khoản Thưởng / Phụ cấp <span style={{ color: '#dc2626' }}>*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 8,
                    border: '1px solid #cbd5e1',
                    fontSize: 13.5,
                    boxSizing: 'border-box',
                  }}
                  placeholder="VD: Phụ cấp Trách nhiệm Trưởng phòng, Thưởng Tết Kỹ thuật..."
                  autoFocus
                />
              </div>

              {/* Grid: Job Position & Department Selects */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {/* Select Chức vụ */}
                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                    Chức vụ áp dụng
                  </label>
                  <select
                    value={form.jobId}
                    onChange={(e) => setForm({ ...form, jobId: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid #cbd5e1',
                      fontSize: 13,
                      background: '#fff',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="">🌐 Tất cả chức vụ</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        💼 {j.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Select Phòng ban */}
                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                    Phòng ban áp dụng
                  </label>
                  <select
                    value={form.departmentId}
                    onChange={(e) => setForm({ ...form, departmentId: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid #cbd5e1',
                      fontSize: 13,
                      background: '#fff',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="">🌐 Tất cả phòng ban</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        🏢 {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Grid: Allowance Type & Amount */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                    Loại khoản
                  </label>
                  <select
                    value={form.allowanceType}
                    onChange={(e) => setForm({ ...form, allowanceType: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid #cbd5e1',
                      fontSize: 13,
                      background: '#fff',
                      boxSizing: 'border-box',
                    }}
                  >
                    <option value="position_allowance">Phụ cấp Chức vụ</option>
                    <option value="responsibility">Phụ cấp Trách nhiệm</option>
                    <option value="holiday_bonus">Thưởng Lễ / Tết</option>
                    <option value="other">Khoản trợ cấp khác</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                    Số tiền (VND) <span style={{ color: '#dc2626' }}>*</span>
                  </label>
                  <input
                    type="number"
                    step="100000"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid #cbd5e1',
                      fontSize: 13.5,
                      fontFamily: 'monospace',
                      fontWeight: 600,
                      boxSizing: 'border-box',
                    }}
                  />
                  <div style={{ fontSize: 11.5, color: '#059669', fontWeight: 600, marginTop: 4 }}>
                    💡 Số tiền: {Number(form.amount || 0).toLocaleString('vi-VN')} ₫
                  </div>
                </div>
              </div>

              {/* Ghi chú */}
              <div>
                <label style={{ display: 'block', fontSize: 12.5, fontWeight: 600, marginBottom: 5, color: '#334155' }}>
                  Ghi chú / Mô tả áp dụng
                </label>
                <input
                  type="text"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 8,
                    border: '1px solid #cbd5e1',
                    fontSize: 13,
                    boxSizing: 'border-box',
                  }}
                  placeholder="VD: Áp dụng cho các sếp từ Trưởng phòng trở lên..."
                />
              </div>
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  padding: '9px 16px',
                  borderRadius: 8,
                  border: '1px solid #cbd5e1',
                  background: '#fff',
                  color: '#475569',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Hủy
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  padding: '9px 20px',
                  borderRadius: 8,
                  border: 'none',
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 2px 4px rgba(37,99,235,0.25)',
                }}
              >
                {saving ? '⏳ Đang lưu...' : editingItem ? 'Lưu thay đổi' : 'Lưu cấu hình'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
