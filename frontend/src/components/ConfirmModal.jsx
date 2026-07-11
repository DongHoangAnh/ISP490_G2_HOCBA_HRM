/* Modal xác nhận dùng chung — thay window.confirm/alert. onConfirm trả
   Promise; lỗi hiện ngay trong modal, thành công thì phía gọi tự đóng.
   Owner: Nhật Anh. */
import { useState } from 'react';
import Modal from './Modal';
import ModalHeader from './ModalHeader';

export default function ConfirmModal({ title, message, confirmLabel = 'Xác nhận', icon = 'alertCircle', onConfirm, onClose }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const run = () => {
    setBusy(true); setErr(null);
    // .then(onConfirm) thay vì resolve(onConfirm()): throw đồng bộ cũng thành rejection.
    Promise.resolve().then(onConfirm).catch((e) => { setErr(e.message); setBusy(false); });
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader icon={icon} title={title} onClose={onClose} />
      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <div style={{ fontSize: 13.5, color: 'var(--ink)' }}>{message}</div>
        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? 'Đang xử lý…' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
