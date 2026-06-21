/* Quản lý file chuyển khoản — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchBankFiles, fetchBatches, fetchBankFormats, generateBankFile, markBankFileUploaded, markBankFileConfirmed, fetchEmployeePayroll } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import BankFileForm from './BankFileForm';
import TblWrap from '../../components/TblWrap';
import * as XLSX from 'xlsx';

const FILE_STATE = {
  draft: ['Đã tạo', 'gray'],
  generated: ['Đã tạo', 'gray'],
  uploaded: ['Đã tải lên', 'blue'],
  confirmed: ['Đã xác nhận', 'green'],
};
const fileState = (k) => FILE_STATE[k] || ['?', 'gray'];

/* ── helpers for Excel formatting ── */
const fmtVND = (n) => typeof n === 'number' ? n : 0;

const thin = { style: 'thin', color: { rgb: '000000' } };
const allBorders = { top: thin, bottom: thin, left: thin, right: thin };

const hdrFill = { patternType: 'solid', fgColor: { rgb: 'DAEEF3' } };
const hdrFont = { bold: true, sz: 10, name: 'Times New Roman' };
const bodyFont = { sz: 10, name: 'Times New Roman' };
const boldFont = { bold: true, sz: 10, name: 'Times New Roman' };
const titleFont = { bold: true, sz: 13, name: 'Times New Roman' };
const companyFont = { bold: true, sz: 11, name: 'Times New Roman' };

export default function BankFile() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [batchId, setBatchId] = useState('');
  const [batches, setBatches] = useState([]);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null);
  const [exporting, setExporting] = useState(null);

  useEffect(() => { fetchBatches().then(setBatches).catch(() => {}); }, []);

  const load = () => {
    setErr(null); setData(null);
    const params = {};
    if (batchId) params.batch_id = batchId;
    fetchBankFiles(params).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [batchId]);

  const doAction = async (id, fn, label) => {
    setBusy(id);
    try {
      await fn(id);
      load();
    } catch (e) {
      alert(`${label} thất bại: ${e.message}`);
    } finally {
      setBusy(null);
    }
  };

  /* ── export Excel per bank file row ── */
  const handleExportExcel = async (f) => {
    setExporting(f.id);
    try {
      const month = f.batch_month;
      const year = f.batch_year;
      if (!month || !year) { alert('Không xác định được tháng/năm của đợt lương.'); return; }
      const res = await fetchEmployeePayroll({ month, year });
      const cols = res.columns || [];
      const emps = res.employees || [];
      if (emps.length === 0) { alert('Không có dữ liệu để xuất.'); return; }

      buildAndDownloadExcel(emps, cols, month, year, f.bank_name || f.format_name || '');
    } catch (e) {
      alert('Lỗi xuất Excel: ' + e.message);
    } finally {
      setExporting(null);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải danh sách file..." />;

  return (
    <>
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={batchId} onChange={(e) => setBatchId(e.target.value)}>
          <option value="">Tất cả đợt lương</option>
          {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={16} />Tạo file CK
        </button>
      </div>

      <div className="card">
        {data.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Chưa có file chuyển khoản.</EmptyState>
          </div>
        ) : (
          <TblWrap id="bank-file">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Đợt lương</th>
                  <th>Ngân hàng</th>
                  <th>Ngày tạo</th>
                  <th>Trạng thái</th>
                  <th style={{ width: 240 }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {data.map((f) => {
                  const [sl, sk] = fileState(f.state);
                  return (
                    <tr key={f.id}>
                      <td style={{ fontWeight: 600 }}>{f.batch_name || `Batch #${f.batch_id}`}</td>
                      <td>{f.format_name || f.bank_name || '—'}</td>
                      <td>{fmtDate(f.generated_at?.split(' ')[0])}</td>
                      <td><Badge kind={sk}>{sl}</Badge></td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          {(f.state === 'draft' || f.state === 'generated') && (
                            <button className="btn btn-ghost btn-sm"
                              onClick={() => doAction(f.id, markBankFileUploaded, 'Đánh dấu tải lên')}
                              disabled={busy === f.id}>
                              <Icon name="upload" size={14} />Tải lên
                            </button>
                          )}
                          {f.state === 'uploaded' && (
                            <button className="btn btn-ghost btn-sm"
                              onClick={() => doAction(f.id, markBankFileConfirmed, 'Xác nhận')}
                              disabled={busy === f.id}>
                              <Icon name="check" size={14} />Xác nhận
                            </button>
                          )}
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => handleExportExcel(f)}
                            disabled={exporting === f.id}>
                            <Icon name="download" size={14} />
                            {exporting === f.id ? 'Đang xuất...' : 'Xuất Excel'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </TblWrap>
        )}
      </div>

      {creating && (
        <BankFileForm
          batches={batches}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }}
        />
      )}
    </>
  );
}

/* ══════════════════════════════════════════════════════════════
   Build Excel matching the exact salary sheet format
   ══════════════════════════════════════════════════════════════ */
function buildAndDownloadExcel(emps, cols, month, year, bankName) {
  const ws = {};
  const merges = [];
  let R = 0; // current row (0-indexed)

  const set = (r, c, v, s) => {
    const ref = XLSX.utils.encode_cell({ r, c });
    ws[ref] = { v, t: typeof v === 'number' ? 'n' : 's', s };
  };

  const totalCols = 5 + cols.length; // STT + Mã NV + Họ tên + Chức vụ + Phòng ban + salary cols

  /* ── Row 0: Company name ── */
  set(R, 0, 'CÔNG TY ...............', { font: companyFont });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 4 } });
  R++;

  /* ── Row 1: Address ── */
  set(R, 0, 'Địa chỉ: ............................', { font: bodyFont });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 4 } });
  R++;

  /* ── Row 2: MST ── */
  set(R, 0, 'MST: ............................', { font: bodyFont });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 4 } });
  R++;

  /* ── Row 3: blank ── */
  R++;

  /* ── Row 4: Title ── */
  const titleText = `BẢNG LƯƠNG THÁNG ${String(month).padStart(2, '0')}/${year}`;
  set(R, 0, titleText, { font: titleFont, alignment: { horizontal: 'center' } });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: totalCols - 1 } });
  R++;

  /* ── Row 5: blank ── */
  R++;

  /* ── Row 6: Header row ── */
  const hdrStyle = { font: hdrFont, fill: hdrFill, border: allBorders, alignment: { horizontal: 'center', vertical: 'center', wrapText: true } };
  const headers = ['STT', 'Mã NV', 'Họ Và Tên', 'Chức Vụ', 'Phòng Ban', ...cols.map((c) => c.name)];
  headers.forEach((h, c) => set(R, c, h, hdrStyle));
  const hdrRow = R;
  R++;

  /* ── Data rows ── */
  const dataStyle = { font: bodyFont, border: allBorders, alignment: { vertical: 'center' } };
  const dataStyleNum = { font: bodyFont, border: allBorders, alignment: { vertical: 'center' }, numFmt: '#,##0' };
  const dataStyleName = { font: { ...bodyFont, bold: false }, border: allBorders, alignment: { vertical: 'center' } };

  emps.forEach((emp, idx) => {
    set(R, 0, idx + 1, { ...dataStyle, alignment: { horizontal: 'center', vertical: 'center' } });
    set(R, 1, emp.code || '', dataStyle);
    set(R, 2, emp.name || '', dataStyleName);
    set(R, 3, emp.job_title || '', dataStyle);
    set(R, 4, emp.department || '', dataStyle);
    cols.forEach((c, ci) => {
      const val = emp.amounts[c.code];
      set(R, 5 + ci, fmtVND(val), dataStyleNum);
    });
    R++;
  });

  /* ── Footer: Tổng row ── */
  const totalStyle = { font: boldFont, border: allBorders, alignment: { vertical: 'center' } };
  const totalStyleNum = { font: boldFont, border: allBorders, alignment: { vertical: 'center' }, numFmt: '#,##0' };
  set(R, 0, '', totalStyle);
  set(R, 1, '', totalStyle);
  set(R, 2, 'Tổng cộng', { ...totalStyle, alignment: { horizontal: 'center', vertical: 'center' } });
  set(R, 3, '', totalStyle);
  set(R, 4, '', totalStyle);
  cols.forEach((c, ci) => {
    const sum = emps.reduce((s, e) => s + fmtVND(e.amounts[c.code]), 0);
    set(R, 5 + ci, sum, totalStyleNum);
  });
  R++;

  /* ── blank row ── */
  R++;

  /* ── Payment info rows ── */
  set(R, 0, `Trả qua ${bankName || 'Ngân hàng'}`, { font: boldFont });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 4 } });
  R++;
  set(R, 0, 'Trả tiền mặt', { font: boldFont });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 4 } });
  R++;

  /* ── blank row ── */
  R++;

  /* ── Signature row ── */
  const sigStyle = { font: boldFont, alignment: { horizontal: 'center' } };
  const sigSubStyle = { font: { ...bodyFont, italic: true }, alignment: { horizontal: 'center' } };

  // Distribute 3 signature blocks across the columns
  const sigCol1 = 1;
  const sigCol2 = Math.floor(totalCols / 2);
  const sigCol3 = totalCols - 3;

  set(R, sigCol1, 'Lập Biểu', sigStyle);
  set(R, sigCol2, 'Kế Toán Trưởng', sigStyle);
  set(R, sigCol3, 'Giám Đốc', sigStyle);
  R++;
  set(R, sigCol1, '(Ký, ghi rõ họ tên)', sigSubStyle);
  set(R, sigCol2, '(Ký, ghi rõ họ tên)', sigSubStyle);
  set(R, sigCol3, '(Ký, ghi rõ họ tên)', sigSubStyle);

  /* ── Finalize worksheet ── */
  ws['!ref'] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: R, c: totalCols - 1 } });
  ws['!merges'] = merges;

  // Column widths
  ws['!cols'] = headers.map((_, i) => {
    if (i === 0) return { wch: 5 };    // STT
    if (i === 1) return { wch: 10 };   // Mã NV
    if (i === 2) return { wch: 24 };   // Họ tên
    if (i === 3) return { wch: 16 };   // Chức vụ
    if (i === 4) return { wch: 16 };   // Phòng ban
    return { wch: 15 };                // salary cols
  });

  // Row heights for header
  ws['!rows'] = [];
  ws['!rows'][hdrRow] = { hpx: 36 };

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, `BL T${String(month).padStart(2, '0')}-${year}`);
  XLSX.writeFile(wb, `Bang_luong_T${String(month).padStart(2, '0')}_${year}.xlsx`);
}
