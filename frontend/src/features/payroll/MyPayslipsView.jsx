/* Phiếu lương cá nhân (self-service authenticated view) — mọi nhân viên xem & xác nhận phiếu lương của CHÍNH MÌNH trong ứng dụng SPA Học Bá HRM. */
import { useState, useEffect } from 'react';
import { fetchMyPayslips, employeeConfirmPayslip } from '../../api/payroll';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';

const CONFIRM_MAP = {
  pending:   { label: 'Chờ xác nhận', bg: '#fef3c7', color: '#92400e', icon: 'clock' },
  confirmed: { label: 'Đã xác nhận',  bg: '#dcfce7', color: '#166534', icon: 'checkCircle' },
  rejected:  { label: 'Phản hồi khiếu nại', bg: '#fee2e2', color: '#991b1b', icon: 'xCircle' },
};

const FEEDBACK_PRESETS = [
  'Sai số ngày công / giờ OT',
  'Thiếu tiền phụ cấp ăn trưa',
  'Tính sai khấu trừ BHXH/BHYT',
  'Chưa cộng thưởng kinh doanh',
];

export default function MyPayslipsView({ targetSlipId }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  // State bộ lọc 2 cấp
  const [selectedPeriod, setSelectedPeriod] = useState(null); // 'MM/YYYY'
  const [selectedSlipId, setSelectedSlipId] = useState(targetSlipId || null);

  // Tab phụ phía bên phải (Ngày công / Bảo hiểm & Thuế)
  const [activeRightTab, setActiveRightTab] = useState('work'); // 'work' | 'tax_ins'

  const [busy, setBusy] = useState(false);
  const [actionErr, setActionErr] = useState(null);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [feedback, setFeedback] = useState('');

  const load = () => {
    setErr(null);
    fetchMyPayslips()
      .then((d) => {
        setData(d);
      })
      .catch((e) => setErr(e.message));
  };

  useEffect(load, []);

  const slips = data?.payslips || [];
  const emp = data?.employee;

  // Lấy danh sách các Tháng/Năm duy nhất cho Lọc 1
  const periodOptions = (() => {
    const map = new Map();
    slips.forEach((s) => {
      const m = String(s.month || 1).padStart(2, '0');
      const y = s.year || 2026;
      const key = `${m}/${y}`;
      if (!map.has(key)) {
        map.set(key, { key, label: `Tháng ${m}/${y}`, month: s.month, year: s.year });
      }
    });
    return Array.from(map.values());
  })();

  // Tự động khởi tạo selectedPeriod và selectedSlipId khi có dữ liệu
  useEffect(() => {
    if (slips.length > 0) {
      let targetSlip = null;
      if (selectedSlipId) {
        targetSlip = slips.find((s) => s.id === Number(selectedSlipId));
      }
      if (!targetSlip && targetSlipId) {
        targetSlip = slips.find((s) => s.id === Number(targetSlipId));
      }
      if (!targetSlip) {
        targetSlip = slips[0];
      }

      const pKey = `${String(targetSlip.month || 1).padStart(2, '0')}/${targetSlip.year || 2026}`;
      if (!selectedPeriod || selectedPeriod !== pKey) {
        setSelectedPeriod(pKey);
      }
      if (selectedSlipId !== targetSlip.id) {
        setSelectedSlipId(targetSlip.id);
      }
    }
  }, [data]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phiếu lương của bạn…" />;

  if (!emp || slips.length === 0) {
    return (
      <div className="content fade-in">
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <EmptyState>Bạn chưa có phiếu lương nào được phát hành.</EmptyState>
        </div>
      </div>
    );
  }

  // Danh sách các phiếu lương thuộc Tháng/Năm đã chọn (Lọc 2)
  const slipsForPeriod = slips.filter((s) => {
    const key = `${String(s.month || 1).padStart(2, '0')}/${s.year || 2026}`;
    return key === selectedPeriod;
  });

  // Xác định phiếu lương active
  let activeSlip = slipsForPeriod.find((s) => s.id === Number(selectedSlipId));
  if (!activeSlip && slipsForPeriod.length > 0) {
    activeSlip = slipsForPeriod[0];
  }
  if (!activeSlip) {
    activeSlip = slips[0];
  }

  const cs = CONFIRM_MAP[activeSlip.employee_confirm] || CONFIRM_MAP.pending;

  // Đổi Lọc 1 (Tháng/Năm) -> tự động chọn phiếu lương đầu tiên trong tháng đó
  const handlePeriodChange = (newPeriod) => {
    setSelectedPeriod(newPeriod);
    const matched = slips.filter(
      (s) => `${String(s.month || 1).padStart(2, '0')}/${s.year || 2026}` === newPeriod
    );
    if (matched.length > 0) {
      setSelectedSlipId(matched[0].id);
    }
    setShowRejectForm(false);
    setActionErr(null);
  };

  const handleAction = async (actionType) => {
    if (actionType === 'reject' && !feedback.trim()) {
      setActionErr('Vui lòng nhập lý do từ chối / khiếu nại.');
      return;
    }
    setBusy(true); setActionErr(null);
    try {
      await employeeConfirmPayslip(activeSlip.id, actionType, feedback);
      setShowRejectForm(false);
      setFeedback('');
      load();
    } catch (e) {
      setActionErr(e.message || 'Thao tác thất bại');
    } finally {
      setBusy(false);
    }
  };

  // Classify lines into standard categories
  const lines = activeSlip.lines || [];
  const worked = activeSlip.worked_days || [];

  const earnings = [];
  const deductions = [];
  const employerContribs = [];
  const taxMetrics = [];

  lines.forEach((l) => {
    const code = (l.code || '').toLowerCase();
    const catCode = (l.category_code || '').toLowerCase();
    const name = (l.name || '').toLowerCase();

    if (catCode === 'thuc_lanh' || code === 'thuc_lanh' || code === 'net') {
      return; // Handled in hero financial summary
    }

    if (code.endsWith('_ct') || catCode.endsWith('_ct') || name.includes('(17.5%) ct') || name.includes('(3%) ct') || name.includes('(1%) ct')) {
      employerContribs.push(l);
    } else if (
      code.includes('tn_tinh_th') || code.includes('tn_truoc_th') || code.includes('tn_mien_th') ||
      code.includes('giam_tru') || code.includes('npt') || name.includes('tính thuế') || name.includes('giảm trừ') || name.includes('miễn thuế')
    ) {
      taxMetrics.push(l);
    } else if (
      code.endsWith('_nv') || code.startsWith('bhxh_') || code.startsWith('bhyt_') || code.startsWith('bhtn_') ||
      code.includes('thue_tncn') || code.includes('tam_ung') || name.includes('bhxh') || name.includes('bhyt') ||
      name.includes('bhtn') || name.includes('thuế') || name.includes('tạm ứng') || l.amount < 0
    ) {
      deductions.push(l);
    } else {
      earnings.push(l);
    }
  });

  const totalEarnings = earnings.reduce((sum, item) => sum + (item.amount || 0), 0);
  const totalDeductions = deductions.reduce((sum, item) => sum + Math.abs(item.amount || 0), 0);
  const totalEmployerContribs = employerContribs.reduce((sum, item) => sum + (item.amount || 0), 0);

  return (
    <div className="content fade-in" style={{ maxWidth: 1100, margin: '0 auto', paddingBottom: 24 }}>
      
      {/* ── HEADER TOOLBAR VỚI BỘ LỌC 2 CẤP ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: '#111827', letterSpacing: '-0.3px', display: 'flex', alignItems: 'center', gap: 8 }}>
            Phiếu Lương Cá Nhân
          </h2>
          <div style={{ fontSize: 12.5, color: '#6b7280', marginTop: 2 }}>
            Xem chi tiết thu nhập, khấu trừ & xác nhận phiếu lương hàng tháng
          </div>
        </div>

        {/* Cụm bộ lọc 2 cấp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          
          {/* LỌC 1: Chọn Tháng / Năm */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, background: '#fff',
            padding: '5px 12px', borderRadius: 10, border: '1px solid #d1d5db',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <Icon name="calendar" size={15} style={{ color: '#881337' }} />
            <span style={{ fontSize: 12.5, fontWeight: 700, color: '#374151' }}>Kỳ lương:</span>
            <select
              value={selectedPeriod || ''}
              onChange={(e) => handlePeriodChange(e.target.value)}
              style={{
                padding: '4px 8px', borderRadius: 6, border: '1px solid #9ca3af',
                fontSize: 13, fontWeight: 800, color: '#881337', background: '#fff', cursor: 'pointer', outline: 'none',
              }}
            >
              {periodOptions.map((p) => (
                <option key={p.key} value={p.key}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* LỌC 2: Chọn Mã phiếu lương (Slip) trong Tháng đã chọn */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, background: '#fff',
            padding: '5px 12px', borderRadius: 10, border: '1px solid #d1d5db',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <Icon name="fileText" size={15} style={{ color: '#0369a1' }} />
            <span style={{ fontSize: 12.5, fontWeight: 700, color: '#374151' }}>Đơn / Phiếu:</span>
            
            {slipsForPeriod.length > 1 ? (
              <select
                value={activeSlip.id}
                onChange={(e) => {
                  setSelectedSlipId(Number(e.target.value));
                  setShowRejectForm(false);
                  setActionErr(null);
                }}
                style={{
                  padding: '4px 8px', borderRadius: 6, border: '1px solid #38bdf8',
                  fontSize: 13, fontWeight: 800, color: '#0369a1', background: '#f0f9ff', cursor: 'pointer', outline: 'none',
                }}
              >
                {slipsForPeriod.map((s) => (
                  <option key={s.id} value={s.id}>
                    #{s.number} ({hbVND(s.net_amount)})
                  </option>
                ))}
              </select>
            ) : (
              <span style={{
                fontSize: 12.5, fontWeight: 800, color: '#0369a1', background: '#e0f2fe',
                padding: '3px 10px', borderRadius: 6, fontFamily: 'monospace',
              }}>
                #{activeSlip.number}
              </span>
            )}
          </div>

        </div>
      </div>

      {/* ── MAIN COMPACT CONTAINER ── */}
      <div style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 14,
        boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        overflow: 'hidden',
      }}>

        {/* 1. HERO SUMMARY BAR (COMPACT HEADER) */}
        <div style={{
          background: 'linear-gradient(135deg, #881337 0%, #9f1239 50%, #be123c 100%)',
          padding: '16px 24px',
          color: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 14,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                background: 'rgba(255, 255, 255, 0.18)', padding: '2px 8px', borderRadius: 12,
                fontSize: 11, fontWeight: 700, letterSpacing: '.4px', textTransform: 'uppercase',
              }}>
                Học Bá HRM Payroll
              </span>
              <span style={{ fontSize: 12, opacity: 0.85, fontFamily: 'monospace' }}>
                #{activeSlip.number}
              </span>
            </div>

            <h3 style={{ margin: '4px 0 2px', fontSize: 20, fontWeight: 800, color: '#ffffff' }}>
              Phiếu lương Tháng {activeSlip.month}/{activeSlip.year}
            </h3>

            <div style={{ fontSize: 13, opacity: 0.95, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontWeight: 700 }}>{emp.name}</span>
              {emp.code && <span style={{ opacity: 0.8, fontFamily: 'monospace' }}>({emp.code})</span>}
              <span style={{ opacity: 0.5 }}>•</span>
              <span>{emp.job_title || emp.department || 'Nhân viên'}</span>
            </div>
          </div>

          {/* Block Financial Metrics + Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            {/* Gross Summary Pill */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.12)', border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 10, padding: '8px 14px', textAlign: 'right', backdropFilter: 'blur(4px)',
            }}>
              <div style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '.5px', opacity: 0.8, fontWeight: 700 }}>
                Tổng thu nhập (Gross)
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#fff', fontVariantNumeric: 'tabular-nums' }}>
                {hbVND(activeSlip.gross_amount)}
              </div>
            </div>

            {/* Net Highlight Card */}
            <div style={{
              background: '#ecfdf5', border: '1.5px solid #a7f3d0',
              borderRadius: 10, padding: '8px 16px', textAlign: 'right', boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            }}>
              <div style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '.5px', color: '#15803d', fontWeight: 800 }}>
                Thực Lĩnh (Net)
              </div>
              <div style={{ fontSize: 20, fontWeight: 900, color: '#15803d', fontVariantNumeric: 'tabular-nums', marginTop: 1 }}>
                {hbVND(activeSlip.net_amount)}
              </div>
            </div>

            {/* Confirmation Status Badge */}
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', borderRadius: 20,
              fontSize: 12, fontWeight: 700,
              background: cs.bg, color: cs.color,
              boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
            }}>
              <Icon name={cs.icon} size={14} />
              {cs.label}
            </span>
          </div>
        </div>

        {/* 2. FEEDBACK DEADLINE RIBBON */}
        {(activeSlip.confirm_deadline || activeSlip.confirm_start_day) && (
          <div style={{
            padding: '8px 24px',
            background: activeSlip.is_expired ? '#fff5f5' : '#fffbeb',
            borderBottom: `1px solid ${activeSlip.is_expired ? '#fed7d7' : '#fef3c7'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            fontSize: 12.5, flexWrap: 'wrap', gap: 8,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Icon name={activeSlip.is_expired ? 'lock' : 'clock'} size={15} style={{ color: activeSlip.is_expired ? '#dc2626' : '#d97706' }} />
              <span>
                <b style={{ color: activeSlip.is_expired ? '#991b1b' : '#92400e' }}>
                  Thời hạn phản hồi:
                </b>{' '}
                <span style={{ color: '#374151' }}>
                  Từ ngày <b>{String(activeSlip.confirm_start_day || 5).padStart(2, '0')}</b> đến ngày <b>{String(activeSlip.confirm_end_day || 10).padStart(2, '0')}</b> hàng tháng
                  {activeSlip.confirm_deadline && !activeSlip.is_expired && (
                    <> (Hạn cuối <b style={{ color: '#111827' }}>{new Date(activeSlip.confirm_deadline).toLocaleString('vi-VN')}</b>)</>
                  )}
                </span>
              </span>
            </div>

            <span style={{
              fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 12,
              background: activeSlip.is_expired ? '#fee2e2' : '#fef08a',
              color: activeSlip.is_expired ? '#991b1b' : '#854d0e',
            }}>
              {activeSlip.is_expired ? '🔒 Đã khóa' : '⚡ Đang mở'}
            </span>
          </div>
        )}

        {/* 3. MAIN DASHBOARD SPLIT GRID (2-COLUMN COMPACT LAYOUT) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.15fr 0.85fr',
          gap: 16,
          padding: '16px 20px',
          background: '#f9fafb',
        }}>

          {/* ── CỘT TRÁI (57%): THU NHẬP & CÁC KHOẢN TRỪ ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            
            {/* Table 1: Earnings (Thu nhập & Phụ cấp) */}
            <div style={{
              background: '#fff', borderRadius: 10, border: '1px solid #bbf7d0',
              overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', background: '#f0fdf4', borderBottom: '1px solid #bbf7d0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#15803d', fontWeight: 800, fontSize: 13 }}>
                  <Icon name="arrowUp" size={15} />
                  <span>1. Thu nhập & Phụ cấp (Earnings)</span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 900, color: '#15803d', fontVariantNumeric: 'tabular-nums' }}>
                  {hbVND(totalEarnings)}
                </span>
              </div>

              <table className="tbl" style={{ margin: 0, fontSize: 12.5 }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th style={{ padding: '6px 12px' }}>Tên khoản lương / Thu nhập</th>
                    <th style={{ padding: '6px 12px', textAlign: 'right' }}>Số tiền (VND)</th>
                  </tr>
                </thead>
                <tbody>
                  {earnings.map((l) => (
                    <tr key={l.id}>
                      <td style={{ padding: '6px 12px', fontWeight: 600, color: '#111827' }}>{l.name}</td>
                      <td style={{ padding: '6px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#111827' }}>
                        {hbVND(l.amount)}
                      </td>
                    </tr>
                  ))}
                  {earnings.length === 0 && (
                    <tr>
                      <td colSpan={2} style={{ textAlign: 'center', color: '#9ca3af', padding: 8 }}>Không có khoản thu nhập riêng biệt</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Table 2: Deductions (Các khoản trừ lương) */}
            <div style={{
              background: '#fff', borderRadius: 10, border: '1px solid #fecdd3',
              overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', background: '#fff1f2', borderBottom: '1px solid #fecdd3',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#be123c', fontWeight: 800, fontSize: 13 }}>
                  <Icon name="arrowDown" size={15} />
                  <span>2. Khoản trừ vào lương (Deductions)</span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 900, color: '#be123c', fontVariantNumeric: 'tabular-nums' }}>
                  -{hbVND(totalDeductions)}
                </span>
              </div>

              <table className="tbl" style={{ margin: 0, fontSize: 12.5 }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th style={{ padding: '6px 12px' }}>Khoản trừ (BHXH, BHYT, BHTN, Thuế)</th>
                    <th style={{ padding: '6px 12px', textAlign: 'right' }}>Số tiền trừ (VND)</th>
                  </tr>
                </thead>
                <tbody>
                  {deductions.map((l) => (
                    <tr key={l.id}>
                      <td style={{ padding: '6px 12px', fontWeight: 500, color: '#374151' }}>{l.name}</td>
                      <td style={{ padding: '6px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#dc2626' }}>
                        -{hbVND(Math.abs(l.amount))}
                      </td>
                    </tr>
                  ))}
                  {deductions.length === 0 && (
                    <tr>
                      <td colSpan={2} style={{ textAlign: 'center', color: '#9ca3af', padding: 8 }}>Không có khoản trừ nào</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

          </div>

          {/* ── CỘT PHẢI (43%): CHI TIẾT TABBED & XÁC NHẬN BẢNG LƯƠNG ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            
            {/* Tab Container */}
            <div style={{
              background: '#fff', borderRadius: 10, border: '1px solid #e5e7eb',
              overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            }}>
              {/* Tab Selector Buttons */}
              <div style={{
                display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f8fafc',
              }}>
                <button
                  type="button"
                  onClick={() => setActiveRightTab('work')}
                  style={{
                    flex: 1, padding: '8px 12px', border: 'none', background: activeRightTab === 'work' ? '#fff' : 'transparent',
                    borderBottom: activeRightTab === 'work' ? '2.5px solid #881337' : '2.5px solid transparent',
                    fontWeight: activeRightTab === 'work' ? 800 : 600,
                    color: activeRightTab === 'work' ? '#881337' : '#6b7280',
                    fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  }}
                >
                  <Icon name="clock" size={14} />
                  <span>Ngày công & OT ({worked.length})</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveRightTab('tax_ins')}
                  style={{
                    flex: 1, padding: '8px 12px', border: 'none', background: activeRightTab === 'tax_ins' ? '#fff' : 'transparent',
                    borderBottom: activeRightTab === 'tax_ins' ? '2.5px solid #881337' : '2.5px solid transparent',
                    fontWeight: activeRightTab === 'tax_ins' ? 800 : 600,
                    color: activeRightTab === 'tax_ins' ? '#881337' : '#6b7280',
                    fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  }}
                >
                  <Icon name="building" size={14} />
                  <span>Bảo hiểm DN & Thuế</span>
                </button>
              </div>

              {/* Tab Content 1: Worked Days & OT */}
              {activeRightTab === 'work' && (
                <div style={{ padding: 0 }}>
                  <table className="tbl" style={{ margin: 0, fontSize: 12 }}>
                    <thead>
                      <tr style={{ background: '#f9fafb' }}>
                        <th style={{ padding: '6px 10px' }}>Loại công</th>
                        <th style={{ padding: '6px 10px', textAlign: 'right' }}>Công</th>
                        <th style={{ padding: '6px 10px', textAlign: 'right' }}>Giờ</th>
                        <th style={{ padding: '6px 10px', textAlign: 'right' }}>Thành tiền</th>
                      </tr>
                    </thead>
                    <tbody>
                      {worked.map((w) => (
                        <tr key={w.id}>
                          <td style={{ padding: '6px 10px', fontWeight: 600, color: '#374151' }}>{w.name}</td>
                          <td style={{ padding: '6px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{w.number_of_days}d</td>
                          <td style={{ padding: '6px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{w.number_of_hours}h</td>
                          <td style={{ padding: '6px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700 }}>
                            {hbVND(w.amount)}
                          </td>
                        </tr>
                      ))}
                      {worked.length === 0 && (
                        <tr>
                          <td colSpan={4} style={{ textAlign: 'center', color: '#9ca3af', padding: 12 }}>Không có chi tiết công riêng</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Tab Content 2: Employer Insurance & Tax Metrics */}
              {activeRightTab === 'tax_ins' && (
                <div style={{ padding: 0 }}>
                  {employerContribs.length > 0 && (
                    <div>
                      <div style={{ padding: '6px 10px', background: '#eff6ff', fontSize: 11.5, fontWeight: 700, color: '#1d4ed8', borderBottom: '1px solid #bfdbfe' }}>
                        Bảo hiểm Doanh nghiệp tài trợ ({hbVND(totalEmployerContribs)})
                      </div>
                      <table className="tbl" style={{ margin: 0, fontSize: 12 }}>
                        <tbody>
                          {employerContribs.map((l) => (
                            <tr key={l.id}>
                              <td style={{ padding: '5px 10px', color: '#374151' }}>{l.name}</td>
                              <td style={{ padding: '5px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#2563eb' }}>
                                {hbVND(l.amount)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {taxMetrics.length > 0 && (
                    <div style={{ borderTop: employerContribs.length > 0 ? '1px solid #e5e7eb' : 'none' }}>
                      <div style={{ padding: '6px 10px', background: '#f8fafc', fontSize: 11.5, fontWeight: 700, color: '#475569', borderBottom: '1px solid #e2e8f0' }}>
                        Chỉ số tính thuế TNCN
                      </div>
                      <table className="tbl" style={{ margin: 0, fontSize: 12 }}>
                        <tbody>
                          {taxMetrics.map((l) => (
                            <tr key={l.id}>
                              <td style={{ padding: '5px 10px', color: '#64748b' }}>{l.name}</td>
                              <td style={{ padding: '5px 10px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: '#334155' }}>
                                {hbVND(l.amount)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {employerContribs.length === 0 && taxMetrics.length === 0 && (
                    <div style={{ padding: 16, textAlign: 'center', color: '#9ca3af', fontSize: 12 }}>
                      Không có thông tin bảo hiểm DN hoặc thuế
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Khối Thao tác Xác nhận & Phản hồi khiếu nại (Action Box) */}
            <div style={{
              background: '#fff', borderRadius: 10, border: '1px solid #e5e7eb',
              padding: 14, boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            }}>
              {actionErr && (
                <div style={{
                  padding: '8px 12px', borderRadius: 6, background: '#fef2f2', border: '1px solid #fecaca',
                  color: '#dc2626', fontSize: 12, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  <Icon name="alertCircle" size={14} />
                  <span>{actionErr}</span>
                </div>
              )}

              {activeSlip.is_expired ? (
                <div style={{
                  padding: '10px 12px', borderRadius: 8, background: '#fff7ed', border: '1px solid #fed7aa',
                  color: '#c2410c', fontSize: 12, display: 'flex', alignItems: 'center', gap: 10,
                }}>
                  <Icon name="lock" size={18} style={{ color: '#ea580c', flexShrink: 0 }} />
                  <div>
                    <b style={{ color: '#9a3412', display: 'block', fontSize: 12.5 }}>🔒 Đã khóa phản hồi</b>
                    <span style={{ fontSize: 11.5, color: '#9a3412' }}>Đã hết hạn xác nhận phiếu lương tháng này.</span>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#111827', marginBottom: 2 }}>
                    Xác nhận số liệu phiếu lương
                  </div>
                  <div style={{ fontSize: 11.5, color: '#6b7280', marginBottom: 10 }}>
                    Vui lòng chọn <b>Xác nhận đồng ý</b> hoặc <b>Gửi khiếu nại</b>.
                  </div>

                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleAction('confirm')}
                      disabled={busy}
                      style={{
                        flex: 1,
                        background: activeSlip.employee_confirm === 'confirmed' ? '#15803d' : '#16a34a',
                        borderColor: '#16a34a',
                        padding: '7px 12px',
                        fontSize: 12.5,
                        fontWeight: 700,
                        borderRadius: 8,
                        boxShadow: '0 2px 4px rgba(22, 163, 74, 0.2)',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                      }}
                    >
                      <Icon name="check" size={14} />
                      {activeSlip.employee_confirm === 'confirmed' ? '✓ Đã đồng ý' : 'Xác nhận đồng ý'}
                    </button>

                    <button
                      className="btn btn-ghost"
                      onClick={() => setShowRejectForm(!showRejectForm)}
                      disabled={busy}
                      style={{
                        color: '#dc2626',
                        borderColor: '#fca5a5',
                        background: showRejectForm ? '#fee2e2' : '#fff',
                        padding: '7px 12px',
                        fontSize: 12.5,
                        fontWeight: 700,
                        borderRadius: 8,
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                      }}
                    >
                      <Icon name="xCircle" size={14} />
                      Khiếu nại
                    </button>
                  </div>

                  {/* Form khiếu nại nhanh */}
                  {showRejectForm && (
                    <div style={{
                      marginTop: 10, padding: 12, background: '#fff5f5',
                      border: '1px solid #fca5a5', borderRadius: 8,
                    }}>
                      <label style={{ fontSize: 12, fontWeight: 700, color: '#991b1b', display: 'block', marginBottom: 6 }}>
                        Lý do khiếu nại *
                      </label>

                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                        {FEEDBACK_PRESETS.map((preset) => (
                          <button
                            key={preset}
                            type="button"
                            onClick={() => setFeedback(preset)}
                            style={{
                              fontSize: 11, padding: '3px 8px', borderRadius: 12,
                              border: '1px solid #fca5a5', background: '#fff', color: '#b91c1c',
                              cursor: 'pointer', fontWeight: 600,
                            }}
                          >
                            + {preset}
                          </button>
                        ))}
                      </div>

                      <textarea
                        rows={2}
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="Mô tả nội dung cần làm rõ với phòng HR..."
                        style={{
                          width: '100%', padding: '6px 10px', borderRadius: 6,
                          border: '1px solid #d1d5db', fontSize: 12, outline: 'none',
                          boxSizing: 'border-box',
                        }}
                      />

                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => handleAction('reject')}
                          disabled={busy || !feedback.trim()}
                          style={{ background: '#dc2626', borderColor: '#dc2626', fontWeight: 700, padding: '5px 12px', fontSize: 12 }}
                        >
                          Gửi khiếu nại HR
                        </button>
                        <button
                          className="btn btn-sm btn-ghost"
                          onClick={() => { setShowRejectForm(false); setFeedback(''); }}
                          style={{ padding: '5px 12px', fontSize: 12 }}
                        >
                          Hủy
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
