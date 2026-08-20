/* Nhập hồ sơ nhân viên từ Excel — modal 2 bước. Owner: Việt.
   Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md

   Bước 1 chọn file → gọi preview (backend đọc-kiểm, KHÔNG ghi gì).
   Bước 2 xem trước → bấm Nhập mới gọi commit.
   Chia 2 bước vì file thật có 168 dòng dữ liệu bẩn: HR phải thấy trước chuyện
   gì sẽ xảy ra, thay vì nhập xong mới biết rồi đi xoá 112 hồ sơ.
   Khuôn bố cục bám WorkScheduleModal (luồng nhập lịch làm việc của Nhật Anh). */
import { useState } from 'react';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import Icon from '../../components/Icon';
import { previewEmployeeImport, commitEmployeeImport } from '../../api/employees';

const REASON_TXT = {
  code_exists: 'đã có hồ sơ mang mã này',
  cccd_exists: 'đã có hồ sơ mang CCCD này',
};

const MAX_ERR_SHOWN = 12;

const BOX_ERR = {
  padding: '10px 13px', background: 'var(--red-50)',
  border: '1px solid var(--red-100)', borderRadius: 10,
  color: 'var(--red-700)', fontSize: 12.5,
};
const BOX_WARN = {
  padding: '10px 13px', background: 'var(--surface-2)',
  border: '1px dashed var(--border-strong)', borderRadius: 10, fontSize: 12.5,
};

export default function ImportEmployeesModal({ onClose, onDone }) {
  const [file, setFile] = useState(null);
  const [prev, setPrev] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function doPreview(f, sheet) {
    if (!f) return;
    setBusy(true); setErr(null);
    try {
      setPrev(await previewEmployeeImport(f, sheet));
    } catch (e) {
      setErr(e.message || 'Không đọc được file.');
      setPrev(null);
    } finally { setBusy(false); }
  }

  async function doCommit() {
    setBusy(true); setErr(null);
    try {
      onDone(await commitEmployeeImport(prev.rows));
    } catch (e) {
      setErr(e.message || 'Không nhập được.');
      setBusy(false);
    }
  }

  const onPickFile = (e) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = '';          // chọn lại đúng file đó vẫn kích hoạt
    setFile(f || null);
    doPreview(f, null);
  };

  const s = prev && prev.summary;

  return (
    <Modal onClose={onClose} lg>
      <ModalHeader lg icon="upload" title="Nhập hồ sơ nhân viên từ Excel"
        sub="Hệ thống tự dò cột theo tên tiêu đề — không cần sửa file về mẫu riêng"
        onClose={onClose} />

      <div style={{ padding: '20px 24px', maxHeight: '62vh', overflowY: 'auto',
        display: 'flex', flexDirection: 'column', gap: 14 }}>

        {!prev && (
          <div style={{ ...BOX_WARN, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="muted">
              Chọn file .xlsx danh sách nhân sự (tối đa 10MB). Hệ thống đọc và
              kiểm trước, <b>chưa ghi gì</b> — bạn xem bảng kết quả rồi mới bấm Nhập.
            </div>
            <input type="file" accept=".xlsx" disabled={busy} onChange={onPickFile} />
          </div>
        )}

        {err && <div style={BOX_ERR}>{err}</div>}
        {busy && <div className="muted">Đang xử lý…</div>}

        {prev && (
          <>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <span className="muted">{prev.filename}</span>
              {prev.sheets && prev.sheets.length > 1 && (
                <select className="sel" value={prev.sheet} disabled={busy}
                  onChange={(e) => doPreview(file, e.target.value)}>
                  {prev.sheets.map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              )}
            </div>

            <div style={{ fontSize: 13.5 }}>
              <b>{s.ok}</b> hồ sơ sẽ nhập · <b>{s.skipped}</b> bỏ qua vì đã có ·{' '}
              <b>{s.error}</b> dòng lỗi phải sửa
              {s.needCompletion > 0 && (
                <> · <b>{s.needCompletion}</b> hồ sơ thiếu MST/BHXH, cần hoàn thiện sau</>
              )}
            </div>

            {prev.errors.length > 0 && (
              <div style={BOX_ERR}>
                <b>Dòng cần sửa trong file rồi tải lại:</b>
                <ul style={{ margin: '8px 0 0', paddingLeft: 18, display: 'flex',
                  flexDirection: 'column', gap: 3 }}>
                  {prev.errors.slice(0, MAX_ERR_SHOWN).map((e) => (
                    <li key={e.excelRow}>{e.message}</li>
                  ))}
                </ul>
                {prev.errors.length > MAX_ERR_SHOWN && (
                  <div style={{ marginTop: 6 }}>
                    … và {prev.errors.length - MAX_ERR_SHOWN} dòng nữa cùng loại.
                  </div>
                )}
              </div>
            )}

            <div className="tbl-wrap" style={{ maxHeight: 300 }}>
              <table className="tbl">
                <thead><tr>
                  <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Dòng</th>
                  <th>Họ và tên</th><th>Mã NV</th><th>Phòng ban</th>
                  <th>Chức danh</th><th>Ghi chú</th>
                </tr></thead>
                <tbody>
                  {prev.rows.map((r) => (
                    <tr key={`r${r.excelRow}`}>
                      <td>{r.excelRow}</td>
                      <td>{r.name}</td>
                      <td>{r.code}</td>
                      <td>{r.depName}</td>
                      <td>{r.jobName}</td>
                      <td className="muted" style={{ fontSize: 12.5 }}>
                        {r.missingOfficial.length > 0
                          && `Thiếu ${r.missingOfficial.join(', ')}. `}
                        {r.warnings.join(' ')}
                      </td>
                    </tr>
                  ))}
                  {prev.skipped.map((r) => (
                    <tr key={`s${r.excelRow}`} className="muted">
                      <td>{r.excelRow}</td>
                      <td>{r.name}</td>
                      <td>{r.code}</td>
                      <td colSpan={3}>Bỏ qua — {REASON_TXT[r.reason] || r.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {prev.unknownCols && prev.unknownCols.length > 0 && (
              <div className="muted" style={{ fontSize: 12.5 }}>
                Cột trong file không nhận diện được nên bỏ qua:{' '}
                {prev.unknownCols.join(', ')}
              </div>
            )}

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn btn-primary" onClick={doCommit}
                disabled={busy || !s.ok}>
                <Icon name="checkCircle" size={16} />
                {busy ? 'Đang nhập…' : `Nhập ${s.ok} hồ sơ`}
              </button>
              <button className="btn btn-ghost" disabled={busy}
                onClick={() => { setPrev(null); setFile(null); setErr(null); }}>
                Chọn file khác
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
