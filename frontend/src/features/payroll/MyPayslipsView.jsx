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
  const [selectedSlipId, setSelectedSlipId] = useState(targetSlipId || null);
  const [busy, setBusy] = useState(false);
  const [actionErr, setActionErr] = useState(null);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [feedback, setFeedback] = useState('');

  const load = () => {
    setErr(null);
    fetchMyPayslips()
      .then((d) => {
        setData(d);
        if (d.payslips?.length > 0 && !selectedSlipId) {
          setSelectedSlipId(d.payslips[0].id);
        }
      })
      .catch((e) => setErr(e.message));
  };

  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phiếu lương của bạn…" />;

  const slips = data.payslips || [];
  const emp = data.employee;

  if (!emp || slips.length === 0) {
    return (
      <div className="content fade-in">
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <EmptyState>Bạn chưa có phiếu lương nào được phát hành.</EmptyState>
        </div>
      </div>
    );
  }

  const activeSlip = slips.find((s) => s.id === Number(selectedSlipId)) || slips[0];
  const cs = CONFIRM_MAP[activeSlip.employee_confirm] || CONFIRM_MAP.pending;

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
    <div className="content fade-in" style={{ maxWidth: 880, margin: '0 auto', paddingBottom: 40 }}>
      {/* Selector kỳ lương */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: '#111827', letterSpacing: '-0.3px' }}>
            Phiếu Lương Cá Nhân
          </h2>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>
            Xem bảng kê chi tiết thu nhập & xác nhận phiếu lương
          </div>
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#fff', padding: '6px 14px', borderRadius: 10, border: '1px solid #e5e7eb', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
          <Icon name="calendar" size={16} style={{ color: '#881337' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>Chọn kỳ lương:</span>
          <select
            value={activeSlip.id}
            onChange={(e) => { setSelectedSlipId(Number(e.target.value)); setShowRejectForm(false); setActionErr(null); }}
            style={{
              padding: '4px 8px', borderRadius: 6, border: '1px solid #d1d5db',
              fontSize: 13, fontWeight: 700, color: '#881337', background: '#fff', cursor: 'pointer', outline: 'none',
            }}
          >
            {slips.map((s) => (
              <option key={s.id} value={s.id}>
                Tháng {s.month}/{s.year} ({s.number})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Payslip Card */}
      <div style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 16,
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
        overflow: 'hidden',
      }}>

        {/* 1. Header Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #881337 0%, #9f1239 50%, #be123c 100%)',
          padding: '28px 32px',
          color: '#fff',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'flex-start',
          position: 'relative',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{
                background: 'rgba(255, 255, 255, 0.15)',
                padding: '4px 10px',
                borderRadius: 20,
                fontSize: 11.5,
                fontWeight: 700,
                letterSpacing: '.5px',
                textTransform: 'uppercase',
                backdropFilter: 'blur(4px)',
              }}>
                Học Bá HRM Payroll
              </span>
              <span style={{ fontSize: 12, opacity: 0.8, fontFamily: 'monospace' }}>
                #{activeSlip.number}
              </span>
            </div>

            <h3 style={{ margin: '10px 0 4px', fontSize: 24, fontWeight: 800, letterSpacing: '-.5px', color: '#ffffff' }}>
              Phiếu lương Tháng {activeSlip.month}/{activeSlip.year}
            </h3>

            <div style={{ fontSize: 14.5, opacity: 0.95, display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
              <span style={{ fontWeight: 700 }}>{emp.name}</span>
              {emp.code && <span style={{ opacity: 0.75, fontFamily: 'monospace' }}>({emp.code})</span>}
              <span style={{ opacity: 0.5 }}>•</span>
              <span>{emp.job_title || emp.department || 'Nhân viên'}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              padding: '7px 16px', borderRadius: 30,
              fontSize: 13, fontWeight: 700,
              background: cs.bg, color: cs.color,
              boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
            }}>
              <Icon name={cs.icon} size={15} />
              {cs.label}
            </span>
          </div>
        </div>

        {/* 2. Feedback Window Deadline Notification */}
        {activeSlip.confirm_deadline && (
          <div style={{
            padding: '12px 32px',
            background: activeSlip.is_expired ? '#fff5f5' : '#fffbeb',
            borderBottom: `1px solid ${activeSlip.is_expired ? '#fed7d7' : '#fef3c7'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            fontSize: 13, flexWrap: 'wrap', gap: 10,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: activeSlip.is_expired ? '#fee2e2' : '#fef3c7',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: activeSlip.is_expired ? '#dc2626' : '#d97706',
              }}>
                <Icon name={activeSlip.is_expired ? 'xCircle' : 'clock'} size={16} />
              </div>
              <div>
                <b style={{ color: activeSlip.is_expired ? '#991b1b' : '#92400e' }}>
                  Thời hạn phản hồi phiếu lương:
                </b>{' '}
                <span style={{ color: '#4b5563' }}>
                  Đến <b style={{ color: '#111827' }}>{new Date(activeSlip.confirm_deadline).toLocaleString('vi-VN')}</b>
                </span>
              </div>
            </div>

            <span style={{
              fontSize: 11.5, fontWeight: 700, padding: '3px 10px', borderRadius: 20,
              background: activeSlip.is_expired ? '#fee2e2' : '#fef08a',
              color: activeSlip.is_expired ? '#991b1b' : '#854d0e',
            }}>
              {activeSlip.is_expired ? '⏰ Đã hết thời hạn' : '⚡ Đang mở phản hồi'}
            </span>
          </div>
        )}

        {/* 3. Hero Financial Summary Bar */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          borderBottom: '1px solid #e5e7eb', background: '#fafafb',
        }}>
          <div style={{ padding: '20px 32px', borderRight: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#6b7280' }}>
              <Icon name="wallet" size={16} style={{ color: '#4b5563' }} />
              <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '.6px', fontWeight: 700 }}>
                Tổng Thu Nhập (Gross)
              </span>
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#111827', marginTop: 6, fontVariantNumeric: 'tabular-nums' }}>
              {hbVND(activeSlip.gross_amount)}
            </div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
              Tổng thu nhập trước khi trừ bảo hiểm & thuế
            </div>
          </div>

          <div style={{
            padding: '20px 32px',
            background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
            position: 'relative',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#15803d' }}>
              <Icon name="checkCircle" size={17} style={{ color: '#16a34a' }} />
              <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '.6px', fontWeight: 800 }}>
                Thực Lĩnh Chuyển Khoản (Net)
              </span>
            </div>
            <div style={{ fontSize: 26, fontWeight: 900, color: '#15803d', marginTop: 4, fontVariantNumeric: 'tabular-nums' }}>
              {hbVND(activeSlip.net_amount)}
            </div>
            <div style={{ fontSize: 12, color: '#166534', marginTop: 4, fontWeight: 600 }}>
              Số tiền thực tế nhận về tài khoản ngân hàng
            </div>
          </div>
        </div>

        {/* 4. Categorized Breakdown Tables */}
        <div style={{ padding: '28px 32px' }}>

          {/* Group 1: Earnings (Thu nhập & Phụ cấp) */}
          <div style={{ marginBottom: 24 }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderRadius: '8px 8px 0 0',
              background: '#f0fdf4', border: '1px solid #bbf7d0', borderBottom: 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#15803d', fontWeight: 700, fontSize: 14 }}>
                <Icon name="arrowUp" size={16} />
                <span>1. Thu nhập & Phụ cấp (Earnings)</span>
              </div>
              <span style={{ fontSize: 13, fontWeight: 800, color: '#15803d' }}>
                {hbVND(totalEarnings)}
              </span>
            </div>

            <table className="tbl" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0, border: '1px solid #bbf7d0' }}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  <th>Tên khoản lương / Thu nhập</th>
                  <th style={{ textAlign: 'right' }}>Số tiền (VND)</th>
                </tr>
              </thead>
              <tbody>
                {earnings.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600, color: '#111827' }}>{l.name}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#111827' }}>
                      {hbVND(l.amount)}
                    </td>
                  </tr>
                ))}
                {earnings.length === 0 && (
                  <tr>
                    <td colSpan={2} style={{ textAlign: 'center', color: '#9ca3af', padding: 12 }}>Không có dòng thu nhập riêng biệt</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Group 2: Deductions (Các khoản trừ lương) */}
          <div style={{ marginBottom: 24 }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderRadius: '8px 8px 0 0',
              background: '#fff1f2', border: '1px solid #fecdd3', borderBottom: 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#be123c', fontWeight: 700, fontSize: 14 }}>
                <Icon name="arrowDown" size={16} />
                <span>2. Các khoản trừ vào lương (Employee Deductions)</span>
              </div>
              <span style={{ fontSize: 13, fontWeight: 800, color: '#be123c' }}>
                -{hbVND(totalDeductions)}
              </span>
            </div>

            <table className="tbl" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0, border: '1px solid #fecdd3' }}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  <th>Khoản trừ (BHXH, BHYT, BHTN, Thuế TNCN)</th>
                  <th style={{ textAlign: 'right' }}>Số tiền trừ (VND)</th>
                </tr>
              </thead>
              <tbody>
                {deductions.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 500, color: '#374151' }}>{l.name}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700, color: '#dc2626' }}>
                      -{hbVND(Math.abs(l.amount))}
                    </td>
                  </tr>
                ))}
                {deductions.length === 0 && (
                  <tr>
                    <td colSpan={2} style={{ textAlign: 'center', color: '#9ca3af', padding: 12 }}>Không có khoản trừ nào</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Group 3: Employer Contributions (Bảo hiểm Công ty đóng tài trợ) */}
          {employerContribs.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 14px', borderRadius: '8px 8px 0 0',
                background: '#eff6ff', border: '1px solid #bfdbfe', borderBottom: 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#1d4ed8', fontWeight: 700, fontSize: 14 }}>
                  <Icon name="building" size={16} />
                  <span>3. Bảo hiểm Công ty đóng tài trợ (Employer Contributions — Không trừ vào lương)</span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#1d4ed8' }}>
                  {hbVND(totalEmployerContribs)}
                </span>
              </div>

              <table className="tbl" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0, border: '1px solid #bfdbfe' }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th>Khoản bảo hiểm doanh nghiệp chi trả (BHXH 17.5%, BHYT 3%, BHTN 1%)</th>
                    <th style={{ textAlign: 'right' }}>Số tiền (VND)</th>
                  </tr>
                </thead>
                <tbody>
                  {employerContribs.map((l) => (
                    <tr key={l.id}>
                      <td style={{ fontWeight: 500, color: '#374151' }}>
                        {l.name}
                        <span style={{ marginLeft: 8, fontSize: 11, background: '#dbeafe', color: '#1e40af', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>
                          DN tài trợ
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: '#2563eb' }}>
                        {hbVND(l.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Group 4: Tax Calculation Metrics */}
          {taxMetrics.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '10px 14px', borderRadius: '8px 8px 0 0',
                background: '#f8fafc', border: '1px solid #e2e8f0', borderBottom: 'none',
                color: '#475569', fontWeight: 700, fontSize: 14,
              }}>
                <Icon name="calculator" size={16} />
                <span>4. Căn cứ & Chỉ số tính thuế TNCN</span>
              </div>

              <table className="tbl" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0, border: '1px solid #e2e8f0' }}>
                <tbody>
                  {taxMetrics.map((l) => (
                    <tr key={l.id}>
                      <td style={{ fontWeight: 500, color: '#64748b' }}>{l.name}</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: '#475569' }}>
                        {hbVND(l.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Worked Days Section */}
          {worked.length > 0 && (
            <div style={{ marginTop: 28 }}>
              <h4 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 800, color: '#111827', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Icon name="clock" size={17} style={{ color: '#881337' }} />
                <span>Chi tiết Ngày công & Giờ làm việc</span>
              </h4>

              <table className="tbl" style={{ border: '1px solid #e5e7eb' }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th>Loại ngày công</th>
                    <th style={{ textAlign: 'right' }}>Số ngày</th>
                    <th style={{ textAlign: 'right' }}>Số giờ</th>
                    <th style={{ textAlign: 'right' }}>Thành tiền (VND)</th>
                  </tr>
                </thead>
                <tbody>
                  {worked.map((w) => (
                    <tr key={w.id}>
                      <td style={{ fontWeight: 600, color: '#374151' }}>{w.name}</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{w.number_of_days} ngày</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{w.number_of_hours}h</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 700 }} className="mono">
                        {hbVND(w.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 5. Employee Action Footer Box */}
        <div style={{
          padding: '24px 32px',
          borderTop: '1px solid #e5e7eb',
          background: '#f9fafb',
        }}>
          {actionErr && (
            <div style={{
              padding: '12px 16px', borderRadius: 8, background: '#fef2f2', border: '1px solid #fecaca',
              color: '#dc2626', fontSize: 13, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <Icon name="alertCircle" size={16} />
              <span>{actionErr}</span>
            </div>
          )}

          {activeSlip.is_expired ? (
            <div style={{
              padding: '14px 18px', borderRadius: 10, background: '#fff7ed', border: '1px solid #ffedd5',
              color: '#c2410c', fontSize: 13.5, display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <Icon name="clock" size={18} style={{ color: '#ea580c' }} />
              <div>
                <b>Hết thời hạn phản hồi:</b> Thời hạn phản hồi phiếu lương đã kết thúc. Nếu có thắc mắc về số liệu, vui lòng liên hệ phòng Nhân sự (HR).
              </div>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: 14.5, fontWeight: 700, color: '#111827' }}>
                    Xác nhận số liệu phiếu lương
                  </h4>
                  <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>
                    Vui lòng kiểm tra kỹ các khoản lương. Bạn có thể bấm <b>Xác nhận đồng ý</b> hoặc gửi <b>Phản hồi khiếu nại</b>.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleAction('confirm')}
                    disabled={busy}
                    style={{
                      background: activeSlip.employee_confirm === 'confirmed' ? '#15803d' : '#16a34a',
                      borderColor: '#16a34a',
                      padding: '9px 18px',
                      fontSize: 13.5,
                      fontWeight: 700,
                      borderRadius: 10,
                      boxShadow: '0 2px 6px rgba(22, 163, 74, 0.25)',
                      display: 'inline-flex', alignItems: 'center', gap: 8,
                    }}
                  >
                    <Icon name="check" size={16} />
                    {activeSlip.employee_confirm === 'confirmed' ? '✓ Đã đồng ý (Xác nhận lại)' : 'Xác nhận đồng ý'}
                  </button>

                  <button
                    className="btn btn-ghost"
                    onClick={() => setShowRejectForm(!showRejectForm)}
                    disabled={busy}
                    style={{
                      color: '#dc2626',
                      borderColor: '#fca5a5',
                      background: showRejectForm ? '#fee2e2' : '#fff',
                      padding: '9px 18px',
                      fontSize: 13.5,
                      fontWeight: 700,
                      borderRadius: 10,
                      display: 'inline-flex', alignItems: 'center', gap: 8,
                    }}
                  >
                    <Icon name="xCircle" size={16} />
                    Phản hồi khiếu nại
                  </button>
                </div>
              </div>

              {/* Interactive Reject / Feedback Form */}
              {showRejectForm && (
                <div style={{
                  marginTop: 18, padding: 20, background: '#fff',
                  border: '1px solid #fecaca', borderRadius: 12,
                  boxShadow: '0 4px 12px rgba(220, 38, 38, 0.08)',
                }}>
                  <label style={{ fontSize: 13.5, fontWeight: 700, color: '#991b1b', display: 'block', marginBottom: 8 }}>
                    Nội dung khiếu nại / lý do thắc mắc *
                  </label>

                  {/* Preset Helper Chips */}
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                    {FEEDBACK_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setFeedback(preset)}
                        style={{
                          fontSize: 12, padding: '4px 10px', borderRadius: 16,
                          border: '1px solid #fca5a5', background: '#fff5f5', color: '#b91c1c',
                          cursor: 'pointer', fontWeight: 600, transition: 'all .15s ease',
                        }}
                      >
                        + {preset}
                      </button>
                    ))}
                  </div>

                  <textarea
                    rows={3}
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Mô tả chi tiết nội dung bạn cần phòng HR làm rõ..."
                    style={{
                      width: '100%', padding: '10px 14px', borderRadius: 8,
                      border: '1px solid #d1d5db', fontSize: 13.5, outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />

                  <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleAction('reject')}
                      disabled={busy || !feedback.trim()}
                      style={{ background: '#dc2626', borderColor: '#dc2626', fontWeight: 700, padding: '8px 16px' }}
                    >
                      Gửi khiếu nại đến HR
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => { setShowRejectForm(false); setFeedback(''); }}
                      style={{ padding: '8px 16px' }}
                    >
                      Hủy bỏ
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

