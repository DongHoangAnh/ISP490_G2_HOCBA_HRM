/* Danh sách chuyển khoản lương — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchTransferList } from '../../api/payroll';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import TblWrap from '../../components/TblWrap';
import * as XLSX from 'xlsx-js-style';

/* ── helpers ── */
const today = new Date();
const pad = (n) => String(n).padStart(2, '0');

/* Remove Vietnamese diacritics (for payment detail only) */
function removeDiacritics(text) {
  if (!text) return '';
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D');
}

export default function BankFile() {
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [exporting, setExporting] = useState(false);

  const load = () => {
    setErr(null);
    setData(null);
    fetchTransferList({ month, year })
      .then(setData)
      .catch((e) => setErr(e.message));
  };
  useEffect(load, [month, year]);

  /* ── Export eMB_BulkPayment Excel ── */
  const handleExport = () => {
    if (!data || data.employees.length === 0) return;
    setExporting(true);
    try {
      const emps = data.employees;
      const fmt = data.bank_formats.find((f) => f.code === 'MB') || data.bank_formats[0];
      const descTpl = (fmt && fmt.description_template) || `Hoc Ba thanh toan luong T${pad(month)}-${year}`;
      const desc = descTpl
        .replace('{month}', pad(month))
        .replace('{year}', String(year));

      buildAndDownloadExcel(emps, desc, month, year);
    } finally {
      setExporting(false);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải danh sách chuyển khoản..." />;

  const emps = data.employees;
  const totalNet = emps.reduce((s, e) => s + (e.net_amount || 0), 0);
  const missingBank = emps.filter((e) => !e.bank_account);

  return (
    <>
      {/* ── Filter bar ── */}
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>
          ))}
        </select>
        <select className="sel" value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[year - 1, year, year + 1].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        <div style={{ flex: 1 }} />
        {missingBank.length > 0 && (
          <span style={{ color: 'var(--orange-600)', fontSize: 13, marginRight: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Icon name="alert-triangle" size={14} />
            {missingBank.length} NV thiếu STK
          </span>
        )}
        <button
          className="btn btn-primary"
          onClick={handleExport}
          disabled={exporting || emps.length === 0}
        >
          <Icon name="download" size={16} />
          {exporting ? 'Đang xuất...' : 'Xuất Excel MB'}
        </button>
      </div>

      {/* ── Table ── */}
      <div className="card">
        {emps.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Chưa có dữ liệu lương tháng {month}/{year}.</EmptyState>
          </div>
        ) : (
          <TblWrap id="transfer-list">
            <table className="tbl">
              <thead>
                <tr>
                  <th style={{ width: 50 }}>STT</th>
                  <th style={{ width: 160 }}>Số tài khoản</th>
                  <th>Tên đơn vị thụ hưởng</th>
                  <th>Ngân hàng thụ hưởng</th>
                  <th style={{ width: 140, textAlign: 'right' }}>Số tiền (VNĐ)</th>
                  <th style={{ width: 80, textAlign: 'center' }}>TT</th>
                </tr>
              </thead>
              <tbody>
                {emps.map((e, i) => (
                  <tr key={e.employee_id} style={!e.bank_account ? { background: 'var(--orange-50, #fff7ed)' } : undefined}>
                    <td style={{ textAlign: 'center' }}>{i + 1}</td>
                    <td style={{ fontFamily: 'monospace' }}>
                      {e.bank_account || <span style={{ color: 'var(--orange-500)', fontSize: 12 }}>Chưa có</span>}
                    </td>
                    <td style={{ fontWeight: 600 }}>{e.name}</td>
                    <td>{e.bank_name || <span style={{ color: 'var(--gray-400)' }}>—</span>}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {(e.net_amount || 0).toLocaleString('vi-VN')}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {e.employee_confirm === 'confirmed'
                        ? <Icon name="check-circle" size={16} style={{ color: 'var(--green-600)' }} />
                        : <Icon name="clock" size={16} style={{ color: 'var(--gray-400)' }} />
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ fontWeight: 700 }}>
                  <td colSpan={4} style={{ textAlign: 'right' }}>Tổng cộng:</td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                    {totalNet.toLocaleString('vi-VN')}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </TblWrap>
        )}
      </div>
    </>
  );
}

/* ══════════════════════════════════════════════════════════════
   Build eMB_BulkPayment Excel — chuẩn format MB Bank
   ══════════════════════════════════════════════════════════════ */
function buildAndDownloadExcel(emps, paymentDetail, month, year) {
  const ws = {};
  const merges = [];

  const set = (r, c, v, s) => {
    const ref = XLSX.utils.encode_cell({ r, c });
    ws[ref] = { v, t: typeof v === 'number' ? 'n' : 's', s };
  };

  /* ── Styles ── */
  const thin = { style: 'thin', color: { rgb: '000000' } };
  const allBorders = { top: thin, bottom: thin, left: thin, right: thin };

  // Title style
  const titleStyle = {
    font: { bold: true, sz: 14, name: 'Times New Roman' },
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
  };

  // Header: dark green fill (#305496), white bold text — matching eMB template
  const hdrStyle = {
    font: { bold: true, sz: 10, name: 'Times New Roman', color: { rgb: 'FFFFFF' } },
    fill: { patternType: 'solid', fgColor: { rgb: '305496' } },
    border: allBorders,
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
  };

  // Data styles
  const bodyFont = { sz: 10, name: 'Times New Roman' };
  const dataStyle = {
    font: bodyFont, border: allBorders,
    alignment: { vertical: 'center' },
  };
  const dataCenterStyle = {
    font: bodyFont, border: allBorders,
    alignment: { horizontal: 'center', vertical: 'center' },
  };
  const numStyle = {
    font: bodyFont, border: allBorders,
    alignment: { horizontal: 'right', vertical: 'center' },
    numFmt: '#,##0',
  };

  let R = 0;

  /* ── Row 0: Title merged B1:F1 ── */
  set(R, 0, '', {}); // empty A1
  set(R, 1, 'DANH SÁCH GIAO DỊCH\n(LIST OF TRANSACTIONS)', titleStyle);
  // Fill merged cells so style applies
  for (let c = 2; c <= 5; c++) set(R, c, '', titleStyle);
  merges.push({ s: { r: R, c: 1 }, e: { r: R, c: 5 } });
  R++;

  /* ── Row 1: Column headers ── */
  const headers = [
    '\uFEFFSTT\n(Ord. No.)\n(1)',
    'Số tài khoản\n(Account No.)\n(2)',
    'Tên đơn vị thụ hưởng\n(Beneficiary Organization)\n(3)',
    'Ngân hàng thụ hưởng/Chi nhánh\n(Beneficiary Bank)\n(4)',
    'Số tiền\n(Amount)\n(5)',
    'Chi tiết thanh toán\n(Payment Detail)\n(6)',
  ];
  headers.forEach((h, c) => set(R, c, h, hdrStyle));
  const hdrRow = R;
  R++;

  /* ── Data rows (include ALL employees, even those missing bank info) ── */
  let stt = 1;
  emps.forEach((emp) => {
    set(R, 0, stt, dataCenterStyle);
    set(R, 1, emp.bank_account || '', dataStyle);
    set(R, 2, emp.name || '', dataStyle);                       // giữ dấu tiếng Việt
    set(R, 3, emp.bank_name || '', dataStyle);
    set(R, 4, emp.net_amount || 0, numStyle);
    set(R, 5, removeDiacritics(paymentDetail), dataStyle);       // bỏ dấu theo guideline MB
    R++;
    stt++;
  });

  /* ── Finalize worksheet ── */
  ws['!ref'] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: Math.max(R - 1, 1), c: 5 } });
  ws['!merges'] = merges;

  // Column widths
  ws['!cols'] = [
    { wch: 8 },   // A: STT
    { wch: 24 },  // B: Số tài khoản
    { wch: 32 },  // C: Tên thụ hưởng
    { wch: 58 },  // D: Ngân hàng thụ hưởng
    { wch: 18 },  // E: Số tiền
    { wch: 42 },  // F: Chi tiết thanh toán
  ];

  // Row heights
  ws['!rows'] = [];
  ws['!rows'][0] = { hpx: 40 };           // title row
  ws['!rows'][hdrRow] = { hpx: 52 };      // header row

  // Auto-filter on header row
  ws['!autofilter'] = {
    ref: XLSX.utils.encode_range(
      { r: hdrRow, c: 0 },
      { r: hdrRow, c: 5 },
    ),
  };

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'eMB_BulkPayment');
  XLSX.writeFile(wb, `eMB_BulkPayment_T${pad(month)}_${year}.xlsx`);
}
