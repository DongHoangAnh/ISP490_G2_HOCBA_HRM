/* Chuyển khoản lương — 2 màn: danh sách file + chi tiết. Owner: Hùng. */
import { useState, useEffect, useCallback } from 'react';
import { fetchTransferList, fetchBankFiles, fetchBankFormats, createTransferFile } from '../../api/payroll';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import TblWrap from '../../components/TblWrap';
import * as XLSX from 'xlsx-js-style';

/* ── helpers ── */
const today = new Date();
const pad = (n) => String(n).padStart(2, '0');

function removeDiacritics(text) {
  if (!text) return '';
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D');
}

/** Deduplicate bank formats by code — keep first occurrence. */
function deduplicateBanks(list) {
  const seen = new Set();
  return (list || []).filter((b) => {
    const code = (b.code || '').toUpperCase();
    if (!code || seen.has(code)) return false;
    seen.add(code);
    return true;
  });
}

/* ══════════════════════════════════════════════════════════
   Main component — switches between list & detail
   ══════════════════════════════════════════════════════════ */
export default function BankFile() {
  const [view, setView] = useState('list');
  const [selectedFile, setSelectedFile] = useState(null);

  if (view === 'detail' && selectedFile) {
    return <TransferDetail file={selectedFile} onBack={() => { setView('list'); setSelectedFile(null); }} />;
  }
  return <FileList onSelect={(f) => { setSelectedFile(f); setView('detail'); }} />;
}

/* ══════════════════════════════════════════════════════════
   Screen 1: Danh sách file chuyển khoản
   ══════════════════════════════════════════════════════════ */
function FileList({ onSelect }) {
  const [files, setFiles] = useState(null);
  const [err, setErr] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [exportingId, setExportingId] = useState(null);

  const loadFiles = useCallback(() => {
    setErr(null);
    setFiles(null);
    fetchBankFiles({}).then(setFiles).catch((e) => setErr(e.message));
  }, []);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  /* Export Excel for a file row */
  const handleExportRow = async (file) => {
    setExportingId(file.id);
    try {
      const params = { month: file.batch_month, year: file.batch_year };
      if (file.bank_codes && file.bank_codes !== 'ALL') {
        params.bank_codes = file.bank_codes;
      }
      const data = await fetchTransferList(params);
      if (!data || data.employees.length === 0) {
        alert('Không có dữ liệu để xuất.');
        return;
      }
      const desc = `Hoc Ba thanh toan luong T${pad(file.batch_month)}-${file.batch_year}`;
      buildAndDownloadExcel(data.employees, desc, file.batch_month, file.batch_year);
    } catch (e) {
      alert(e.message || 'Lỗi xuất Excel');
    } finally {
      setExportingId(null);
    }
  };

  if (err) return <ErrorState message={err} onRetry={loadFiles} />;

  return (
    <>
      {/* ── Toolbar ── */}
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <div style={{ fontWeight: 600, fontSize: 15 }}>Danh sách file chuyển khoản</div>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setShowModal(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '6px 14px', borderRadius: 6, border: 'none',
            background: '#2563eb', color: '#fff', fontSize: 13,
            fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          <Icon name="plus" size={14} />
          Tạo file chuyển khoản
        </button>
      </div>

      {/* ── File list ── */}
      <div className="card">
        {!files ? (
          <LoadingState label="Đang tải danh sách file..." />
        ) : files.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <EmptyState>Chưa có file chuyển khoản nào.</EmptyState>
          </div>
        ) : (
          <TblWrap id="bank-file-list">
            <table className="tbl">
              <thead>
                <tr>
                  <th style={{ width: 50 }}>STT</th>
                  <th>Tên file</th>
                  <th style={{ width: 100, textAlign: 'center' }}>Tháng</th>
                  <th style={{ width: 130 }}>Ngân hàng</th>
                  <th style={{ width: 70, textAlign: 'center' }}>Số NV</th>
                  <th style={{ width: 140, textAlign: 'right' }}>Tổng tiền (VNĐ)</th>
                  <th style={{ width: 130 }}>Ngày tạo</th>
                  <th style={{ width: 100 }}>Người tạo</th>
                  <th style={{ width: 90, textAlign: 'center' }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f, i) => (
                  <tr key={f.id}>
                    <td style={{ textAlign: 'center' }}>{i + 1}</td>
                    <td>
                      <button
                        onClick={() => onSelect(f)}
                        style={{
                          background: 'none', border: 'none', padding: 0,
                          color: '#2563eb', cursor: 'pointer', fontWeight: 600,
                          fontSize: 13, textDecoration: 'underline',
                        }}
                      >
                        {f.name}
                      </button>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {f.batch_month && f.batch_year ? `${pad(f.batch_month)}/${f.batch_year}` : '—'}
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11.5, padding: '2px 8px', borderRadius: 10,
                        background: '#f3f4f6', color: '#374151',
                      }}>
                        {f.bank_codes === 'ALL' ? 'Tất cả' : (f.bank_codes || f.bank_code || '—')}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>{f.record_count}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {(f.total_amount || 0).toLocaleString('vi-VN')}
                    </td>
                    <td style={{ fontSize: 12, color: '#6b7280' }}>
                      {f.generated_at ? new Date(f.generated_at).toLocaleDateString('vi-VN') : '—'}
                    </td>
                    <td style={{ fontSize: 12 }}>{f.generated_by || '—'}</td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => handleExportRow(f)}
                        disabled={exportingId === f.id}
                        title="Xuất Excel"
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 3,
                          padding: '3px 8px', borderRadius: 4, border: '1px solid #d1d5db',
                          background: '#fff', color: '#059669', fontSize: 12,
                          cursor: exportingId === f.id ? 'not-allowed' : 'pointer',
                          opacity: exportingId === f.id ? 0.5 : 1,
                        }}
                      >
                        <Icon name="download" size={13} />
                        Excel
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TblWrap>
        )}
      </div>

      {/* ── Create modal ── */}
      {showModal && (
        <CreateFileModal
          onClose={() => setShowModal(false)}
          onCreated={() => { setShowModal(false); loadFiles(); }}
        />
      )}
    </>
  );
}

/* ══════════════════════════════════════════════════════════
   Modal: Tạo file chuyển khoản
   ══════════════════════════════════════════════════════════ */
const fieldLabel = { fontSize: 13, fontWeight: 500, color: '#374151', display: 'block', marginBottom: 6 };
const fieldSelect = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14, background: '#fff', boxSizing: 'border-box' };

function CreateFileModal({ onClose, onCreated }) {
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year, setYear] = useState(today.getFullYear());
  const [banks, setBanks] = useState([]);
  const [selCodes, setSelCodes] = useState([]);
  const [creating, setCreating] = useState(false);
  const [bankOpen, setBankOpen] = useState(false);

  useEffect(() => {
    fetchBankFormats().then((list) => setBanks(deduplicateBanks(list))).catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (creating) return;
    setCreating(true);
    try {
      await createTransferFile(month, year, selCodes);
      onCreated();
    } catch (e) {
      alert(e.message || 'Lỗi tạo file');
    } finally {
      setCreating(false);
    }
  };

  const bankLabel = selCodes.length === 0
    ? 'Tất cả ngân hàng'
    : selCodes.length <= 3
      ? selCodes.join(', ')
      : `${selCodes.length} ngân hàng đã chọn`;

  return (
    <Modal onClose={onClose} maxWidth={480}>
      <div style={{
        display: 'flex', flexDirection: 'column',
        width: '100%', maxHeight: '88vh',
      }}>
        {/* Header */}
        <div style={{
          padding: '22px 28px 16px', borderBottom: '1px solid #e5e7eb',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>Tạo file chuyển khoản</h3>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>Sinh file thanh toán cho ngân hàng</p>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            padding: 4, color: '#9ca3af', lineHeight: 1,
          }}>
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 28px', flex: 1, overflow: 'hidden' }}>
          {/* Tháng */}
          <div style={{ marginBottom: 16 }}>
            <span style={fieldLabel}>Tháng</span>
            <select className="sel" style={fieldSelect} value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>
              ))}
            </select>
          </div>

          {/* Năm */}
          <div style={{ marginBottom: 16 }}>
            <span style={fieldLabel}>Năm</span>
            <select className="sel" style={fieldSelect} value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[year - 1, year, year + 1].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Ngân hàng */}
          <div>
            <span style={fieldLabel}>
              Ngân hàng
              {selCodes.length > 0 && (
                <span style={{ fontWeight: 400, color: '#2563eb', marginLeft: 6, fontSize: 12 }}>
                  ({selCodes.length} đã chọn)
                </span>
              )}
            </span>
            {/* Trigger — looks like a select */}
            <div
              onClick={() => setBankOpen(!bankOpen)}
              style={{
                ...fieldSelect,
                cursor: 'pointer', display: 'flex', alignItems: 'center',
                justifyContent: 'space-between',
                borderBottomLeftRadius: bankOpen ? 0 : 8,
                borderBottomRightRadius: bankOpen ? 0 : 8,
                borderColor: bankOpen ? '#2563eb' : '#d1d5db',
              }}
            >
              <span style={{ color: selCodes.length === 0 ? '#9ca3af' : '#111827' }}>
                {bankLabel}
              </span>
              <Icon name={bankOpen ? 'chevron-up' : 'chevron-down'} size={16} style={{ color: '#9ca3af', flexShrink: 0 }} />
            </div>
            {/* Expandable bank list */}
            {bankOpen && (
              <BankPickerPanel banks={banks} selected={selCodes} onChange={setSelCodes} />
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 28px', borderTop: '1px solid #e5e7eb',
          display: 'flex', justifyContent: 'flex-end', gap: 10,
        }}>
          <button onClick={onClose} style={{
            padding: '8px 20px', borderRadius: 8, border: '1px solid #d1d5db',
            background: '#fff', color: '#374151', fontSize: 14, cursor: 'pointer',
          }}>
            Huỷ
          </button>
          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              padding: '8px 20px', borderRadius: 8, border: 'none',
              background: '#2563eb', color: '#fff', fontSize: 14, fontWeight: 600,
              cursor: creating ? 'not-allowed' : 'pointer',
              opacity: creating ? 0.6 : 1,
            }}
          >
            {creating ? 'Đang tạo...' : 'Tạo file'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/* ══════════════════════════════════════════════════════════
   Expandable bank picker panel (shows below the trigger)
   ══════════════════════════════════════════════════════════ */
function BankPickerPanel({ banks, selected, onChange }) {
  const [search, setSearch] = useState('');

  const filtered = banks.filter((b) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (b.code || '').toLowerCase().includes(q) || (b.name || '').toLowerCase().includes(q);
  });

  const toggle = (code) => {
    onChange(selected.includes(code) ? selected.filter((c) => c !== code) : [...selected, code]);
  };
  const toggleAll = () => {
    const allCodes = banks.map((b) => b.code);
    onChange(selected.length === banks.length ? [] : allCodes);
  };

  return (
    <div style={{
      border: '1px solid #2563eb', borderTop: 'none',
      borderBottomLeftRadius: 8, borderBottomRightRadius: 8,
      overflow: 'hidden', background: '#fafafa',
    }}>
      {/* Search */}
      <div style={{ padding: '8px 10px', background: '#fff', borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ position: 'relative' }}>
          <Icon name="search" size={14} style={{
            position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)',
            color: '#9ca3af', pointerEvents: 'none',
          }} />
          <input
            type="text"
            placeholder="Tìm theo mã hoặc tên..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%', padding: '7px 10px 7px 30px', borderRadius: 6,
              border: '1px solid #e5e7eb', fontSize: 13, outline: 'none',
              boxSizing: 'border-box', background: '#f9fafb',
            }}
          />
        </div>
      </div>

      {/* Select all row */}
      <label style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '8px 12px', cursor: 'pointer', fontSize: 13,
        borderBottom: '1px solid #e5e7eb', fontWeight: 600, color: '#374151',
        background: '#fff',
      }}>
        <input
          type="checkbox"
          checked={selected.length === banks.length && banks.length > 0}
          onChange={toggleAll}
          style={{ width: 16, height: 16, accentColor: '#2563eb', flexShrink: 0, cursor: 'pointer' }}
        />
        Chọn tất cả
        <span style={{ fontWeight: 400, color: '#9ca3af', marginLeft: 'auto', fontSize: 12 }}>
          {banks.length} ngân hàng
        </span>
      </label>

      {/* Scrollable list */}
      <div style={{ overflow: 'auto', maxHeight: 'min(36vh, 320px)', scrollbarWidth: 'thin' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
            Không tìm thấy ngân hàng nào
          </div>
        ) : (
          filtered.map((b) => {
            const active = selected.includes(b.code);
            return (
              <label
                key={b.code}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '7px 12px', cursor: 'pointer', fontSize: 13,
                  background: active ? '#eff6ff' : '#fff',
                  borderBottom: '1px solid #f3f4f6',
                }}
              >
                <input
                  type="checkbox"
                  checked={active}
                  onChange={() => toggle(b.code)}
                  style={{ width: 16, height: 16, accentColor: '#2563eb', flexShrink: 0, cursor: 'pointer' }}
                />
                <span style={{
                  display: 'inline-block', minWidth: 56, padding: '1px 6px',
                  borderRadius: 4, fontSize: 12, fontWeight: 700, textAlign: 'center',
                  background: active ? '#dbeafe' : '#f3f4f6',
                  color: active ? '#1d4ed8' : '#374151',
                  flexShrink: 0, fontFamily: 'monospace', letterSpacing: '.3px',
                }}>
                  {b.code}
                </span>
                <span style={{
                  color: '#6b7280', fontSize: 12.5,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
                }}>
                  {b.name}
                </span>
              </label>
            );
          })
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   Screen 2: Chi tiết file — danh sách chuyển khoản
   ══════════════════════════════════════════════════════════ */
function TransferDetail({ file, onBack }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(() => {
    setErr(null);
    setData(null);
    fetchTransferList({ file_id: file.id })
      .then(setData)
      .catch((e) => setErr(e.message));
  }, [file.id]);

  useEffect(load, [load]);

  const handleExport = () => {
    if (!data || data.employees.length === 0) return;
    setExporting(true);
    try {
      const m = data.month || file.batch_month;
      const y = data.year || file.batch_year;
      const desc = `Hoc Ba thanh toan luong T${pad(m)}-${y}`;
      buildAndDownloadExcel(data.employees, desc, m, y);
    } finally {
      setExporting(false);
    }
  };

  const emps = data?.employees || [];
  const totalNet = emps.reduce((s, e) => s + (e.net_amount || 0), 0);
  const missingBank = emps.filter((e) => !e.bank_account);

  return (
    <>
      {/* ── Header bar ── */}
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <button
          onClick={onBack}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '5px 12px', borderRadius: 6,
            border: '1px solid #d1d5db', background: '#fff',
            color: '#374151', fontSize: 13, cursor: 'pointer',
          }}
        >
          <Icon name="arrow-left" size={14} />
          Quay lại
        </button>

        <div style={{ fontWeight: 600, fontSize: 14, marginLeft: 10 }}>
          {file.name}
        </div>

        <span style={{ fontSize: 12, color: '#6b7280', marginLeft: 8 }}>
          {file.batch_month && file.batch_year
            ? `Tháng ${pad(file.batch_month)}/${file.batch_year}`
            : ''}
          {file.bank_codes ? ` — NH: ${file.bank_codes === 'ALL' ? 'Tất cả' : file.bank_codes}` : ''}
        </span>

        <div style={{ flex: 1 }} />

        {missingBank.length > 0 && (
          <span style={{ color: 'var(--orange-600)', fontSize: 13, marginRight: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Icon name="alert-triangle" size={14} />
            {missingBank.length} NV thiếu STK
          </span>
        )}

        <button
          onClick={handleExport}
          disabled={exporting || emps.length === 0}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '5px 12px', borderRadius: 6, border: 'none',
            background: '#059669', color: '#fff', fontSize: 13,
            fontWeight: 600, cursor: exporting || emps.length === 0 ? 'not-allowed' : 'pointer',
            opacity: exporting || emps.length === 0 ? 0.5 : 1,
          }}
        >
          <Icon name="download" size={14} />
          {exporting ? 'Đang xuất...' : 'Xuất Excel'}
        </button>
      </div>

      {/* ── Table ── */}
      <div className="card">
        {err ? (
          <ErrorState message={err} onRetry={load} />
        ) : !data ? (
          <LoadingState label="Đang tải danh sách chuyển khoản..." />
        ) : emps.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Không có dữ liệu chuyển khoản cho file này.</EmptyState>
          </div>
        ) : (
          <TblWrap id="transfer-detail">
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

/* ══════════════════════════════════════════════════════════
   Build eMB_BulkPayment Excel — chuẩn format MB Bank
   ══════════════════════════════════════════════════════════ */
function buildAndDownloadExcel(emps, paymentDetail, month, year) {
  const ws = {};
  const merges = [];

  const set = (r, c, v, s) => {
    const ref = XLSX.utils.encode_cell({ r, c });
    ws[ref] = { v, t: typeof v === 'number' ? 'n' : 's', s };
  };

  const thin = { style: 'thin', color: { rgb: '000000' } };
  const allBorders = { top: thin, bottom: thin, left: thin, right: thin };

  const titleStyle = {
    font: { bold: true, sz: 14, name: 'Times New Roman' },
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
  };
  const hdrStyle = {
    font: { bold: true, sz: 10, name: 'Times New Roman', color: { rgb: 'FFFFFF' } },
    fill: { patternType: 'solid', fgColor: { rgb: '305496' } },
    border: allBorders,
    alignment: { horizontal: 'center', vertical: 'center', wrapText: true },
  };
  const bodyFont = { sz: 10, name: 'Times New Roman' };
  const dataStyle = { font: bodyFont, border: allBorders, alignment: { vertical: 'center' } };
  const dataCenterStyle = { font: bodyFont, border: allBorders, alignment: { horizontal: 'center', vertical: 'center' } };
  const numStyle = { font: bodyFont, border: allBorders, alignment: { horizontal: 'right', vertical: 'center' }, numFmt: '#,##0' };

  let R = 0;

  set(R, 0, '', {});
  set(R, 1, 'DANH SÁCH GIAO DỊCH\n(LIST OF TRANSACTIONS)', titleStyle);
  for (let c = 2; c <= 5; c++) set(R, c, '', titleStyle);
  merges.push({ s: { r: R, c: 1 }, e: { r: R, c: 5 } });
  R++;

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

  let stt = 1;
  emps.forEach((emp) => {
    set(R, 0, stt, dataCenterStyle);
    set(R, 1, emp.bank_account || '', dataStyle);
    set(R, 2, emp.name || '', dataStyle);
    set(R, 3, emp.bank_name || '', dataStyle);
    set(R, 4, emp.net_amount || 0, numStyle);
    set(R, 5, removeDiacritics(paymentDetail), dataStyle);
    R++; stt++;
  });

  ws['!ref'] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: Math.max(R - 1, 1), c: 5 } });
  ws['!merges'] = merges;
  ws['!cols'] = [{ wch: 8 }, { wch: 24 }, { wch: 32 }, { wch: 58 }, { wch: 18 }, { wch: 42 }];
  ws['!rows'] = [];
  ws['!rows'][0] = { hpx: 40 };
  ws['!rows'][hdrRow] = { hpx: 52 };
  ws['!autofilter'] = { ref: XLSX.utils.encode_range({ r: hdrRow, c: 0 }, { r: hdrRow, c: 5 }) };

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'eMB_BulkPayment');
  XLSX.writeFile(wb, `eMB_BulkPayment_T${pad(month)}_${year}.xlsx`);
}
