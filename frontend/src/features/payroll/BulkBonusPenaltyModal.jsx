import React, { useState, useMemo } from 'react';
import { applyBulkBonusPenalty } from '../../api/payroll';
import Icon from '../../components/Icon';

export default function BulkBonusPenaltyModal({ batchId, employees, onClose, onSuccess }) {
  const [bonusAmount, setBonusAmount] = useState(0);
  const [bonusReason, setBonusReason] = useState('');
  const [penaltyAmount, setPenaltyAmount] = useState(0);
  const [penaltyReason, setPenaltyReason] = useState('');
  const [saving, setSaving] = useState(false);

  // Filters
  const [deptFilter, setDeptFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [checkedIds, setCheckedIds] = useState({});

  // Unique departments for filter dropdown
  const departments = useMemo(() => {
    const set = new Set();
    (employees || []).forEach((e) => {
      if (e.department_name) set.add(e.department_name);
    });
    return Array.from(set);
  }, [employees]);

  // Filtered employees list
  const filteredEmployees = useMemo(() => {
    return (employees || []).filter((e) => {
      if (deptFilter && e.department_name !== deptFilter) return false;
      if (statusFilter && e.employment_status !== statusFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const nameMatch = (e.name || '').toLowerCase().includes(q);
        const codeMatch = (e.employee_code || '').toLowerCase().includes(q);
        if (!nameMatch && !codeMatch) return false;
      }
      return true;
    });
  }, [employees, deptFilter, statusFilter, searchQuery]);

  // Handle select all / deselect all
  const handleToggleSelectAll = (e) => {
    const isChecked = e.target.checked;
    const next = {};
    if (isChecked) {
      filteredEmployees.forEach((emp) => {
        const slipId = emp.payslip_id || emp.id;
        next[slipId] = true;
      });
    }
    setCheckedIds(next);
  };

  const handleToggleOne = (slipId) => {
    setCheckedIds((prev) => ({
      ...prev,
      [slipId]: !prev[slipId],
    }));
  };

  const selectedPayslipIds = useMemo(() => {
    return Object.keys(checkedIds).filter((id) => checkedIds[id]).map(Number);
  }, [checkedIds]);

  const handleApply = async () => {
    if (bonusAmount <= 0 && penaltyAmount <= 0) {
      alert('Vui lòng nhập số tiền Thưởng (>0) hoặc Phạt (>0) để áp dụng!');
      return;
    }

    const targetIds = selectedPayslipIds.length > 0 ? selectedPayslipIds : filteredEmployees.map((e) => e.payslip_id || e.id);
    if (!targetIds.length) {
      alert('Không có nhân viên nào phù hợp để áp dụng!');
      return;
    }

    const targetMsg = selectedPayslipIds.length > 0
      ? `Bạn có XÁC NHẬN áp dụng Thưởng/Phạt cho ${selectedPayslipIds.length} nhân viên được chọn không?`
      : `Bạn có XÁC NHẬN áp dụng Thưởng/Phạt cho TẤT CẢ ${filteredEmployees.length} nhân viên theo bộ lọc không?`;

    if (!confirm(targetMsg)) return;

    setSaving(true);
    try {
      const res = await applyBulkBonusPenalty(batchId, {
        payslipIds: targetIds,
        bonusAmount: Number(bonusAmount),
        bonusReason,
        penaltyAmount: Number(penaltyAmount),
        penaltyReason,
      });

      alert(res.message || '🎉 Áp dụng thưởng/phạt thành công!');
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      alert('Lỗi áp dụng Thưởng/Phạt: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#fff', width: 720, maxHeight: '90vh', borderRadius: 14, display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)' }}>
        
        {/* Header */}
        <div style={{ padding: '16px 20px', background: '#1e293b', color: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
              Công cụ Thưởng & Phạt Hàng Loạt Theo Tháng
            </h3>
            <p style={{ margin: '4px 0 0', fontSize: 12, color: '#94a3b8' }}>
              Điền số tiền Thưởng/Phạt và tích chọn nhân viên cần áp dụng cho đợt lương này.
            </p>
          </div>
          <button onClick={onClose} style={{ border: 'none', background: 'transparent', color: '#94a3b8', cursor: 'pointer' }}>
            <Icon name="x" size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: 20, flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
          
          {/* Form Inputs: Bonus & Penalty */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, background: '#f8fafc', padding: 16, borderRadius: 10, border: '1px solid #e2e8f0' }}>
            
            {/* Bonus Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: 13, fontWeight: 700, color: '#059669', display: 'flex', alignItems: 'center', gap: 6 }}>
                Thưởng thêm (VND)
              </label>
              <input
                type="number"
                step="50000"
                value={bonusAmount}
                onChange={(e) => setBonusAmount(parseFloat(e.target.value) || 0)}
                placeholder="VD: 500,000"
                style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13, fontWeight: 700, color: '#047857' }}
              />
              <input
                type="text"
                value={bonusReason}
                onChange={(e) => setBonusReason(e.target.value)}
                placeholder="Lý do thưởng (VD: Thưởng hiệu suất Q3)"
                style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 12 }}
              />
            </div>

            {/* Penalty Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ fontSize: 13, fontWeight: 700, color: '#dc2626', display: 'flex', alignItems: 'center', gap: 6 }}>
                Phạt vi phạm (VND)
              </label>
              <input
                type="number"
                step="50000"
                value={penaltyAmount}
                onChange={(e) => setPenaltyAmount(parseFloat(e.target.value) || 0)}
                placeholder="VD: 200,000"
                style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13, fontWeight: 700, color: '#b91c1c' }}
              />
              <input
                type="text"
                value={penaltyReason}
                onChange={(e) => setPenaltyReason(e.target.value)}
                placeholder="Lý do phạt (VD: Đi trễ nhiều lần)"
                style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 12 }}
              />
            </div>
          </div>

          {/* Filters Bar */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="🔍 Tìm tên hoặc mã nhân viên..."
              style={{ flex: 1, padding: '7px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 12 }}
            />
            <select
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 12 }}
            >
              <option value="">Tất cả phòng ban</option>
              {departments.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* Table list of employees */}
          <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden', maxHeight: 260, overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569', fontWeight: 700 }}>
                  <th style={{ padding: '8px 12px', width: 40, textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      onChange={handleToggleSelectAll}
                      checked={filteredEmployees.length > 0 && selectedPayslipIds.length === filteredEmployees.length}
                    />
                  </th>
                  <th style={{ padding: '8px 12px' }}>Mã NV</th>
                  <th style={{ padding: '8px 12px' }}>Họ và tên</th>
                  <th style={{ padding: '8px 12px' }}>Phòng ban</th>
                  <th style={{ padding: '8px 12px' }}>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: 16, textAlign: 'center', color: '#94a3b8' }}>
                      Không tìm thấy nhân viên nào phù hợp bộ lọc.
                    </td>
                  </tr>
                ) : (
                  filteredEmployees.map((emp) => {
                    const slipId = emp.payslip_id || emp.id;
                    const isChecked = !!checkedIds[slipId];
                    return (
                      <tr key={slipId} style={{ borderBottom: '1px solid #f1f5f9', background: isChecked ? '#eff6ff' : '#fff' }}>
                        <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => handleToggleOne(slipId)}
                          />
                        </td>
                        <td style={{ padding: '8px 12px', fontWeight: 600, color: '#2563eb' }}>{emp.employee_code || `NV-${emp.id}`}</td>
                        <td style={{ padding: '8px 12px', fontWeight: 600, color: '#0f172a' }}>{emp.name}</td>
                        <td style={{ padding: '8px 12px', color: '#64748b' }}>{emp.department_name || '—'}</td>
                        <td style={{ padding: '8px 12px' }}>
                          <span style={{
                            padding: '2px 6px', borderRadius: 10, fontSize: 11, fontWeight: 600,
                            background: emp.employment_status === 'official' ? '#dcfce7' : '#fef3c7',
                            color: emp.employment_status === 'official' ? '#15803d' : '#b45309',
                          }}>
                            {emp.employment_status === 'official' ? 'Chính thức' : 'Thử việc'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

        </div>

        {/* Footer */}
        <div style={{ padding: '12px 20px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 13, color: '#64748b' }}>
            Đã chọn: <b style={{ color: '#2563eb' }}>{selectedPayslipIds.length > 0 ? selectedPayslipIds.length : `${filteredEmployees.length} (Tất cả theo bộ lọc)`}</b> nhân viên
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={onClose}
              style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              Hủy
            </button>
            <button
              onClick={handleApply}
              disabled={saving}
              style={{
                padding: '8px 18px', borderRadius: 8, border: 'none', background: '#2563eb', color: '#fff',
                fontSize: 13, fontWeight: 700, cursor: 'pointer', opacity: saving ? 0.7 : 1,
              }}
            >
              {saving ? 'Đang áp dụng...' : 'Áp Dụng Cho Nhân Viên'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
