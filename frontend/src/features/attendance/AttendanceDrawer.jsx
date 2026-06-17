/* Chi tiết 1 bản ghi chấm công (read-only): ảnh, bản đồ, cờ review. */
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { fmtDate } from '../../utils/format';
import { fmtTime, attStatus, fmtCredit } from './util';

export default function AttendanceDrawer({ rec, onClose }) {
  const [stLabel, stKind] = attStatus(rec.statusKey);
  const img = (field) => `/web/image/hocba.attendance/${rec.id}/${field}`;
  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>{rec.name}</h2>
            <Badge kind={stKind} dot>{stLabel}</Badge>
            {rec.needsReview && <Badge kind="amber" dot>Cần xem lại</Badge>}
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 3 }}>
            {rec.code} · {rec.depName} · {fmtDate(rec.date)}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        <div className="grid-2" style={{ rowGap: 16 }}>
          <div className="kv"><div className="k">Check-in</div><div className="v mono">{fmtTime(rec.checkIn)}{rec.lateMinutes > 0 && <span style={{ color: 'var(--amber)' }}> (+{rec.lateMinutes}')</span>}</div></div>
          <div className="kv"><div className="k">Check-out</div><div className="v mono">{fmtTime(rec.checkOut)}</div></div>
          <div className="kv"><div className="k">Giờ công</div><div className="v mono">{rec.workingHours} giờ</div></div>
          <div className="kv"><div className="k">Ngày công</div><div className="v mono" style={{ fontWeight: 600 }}>{fmtCredit(rec.workCredit)}</div></div>
          <div className="kv"><div className="k">Giờ ra mong đợi</div><div className="v mono">{fmtTime(rec.expectedCheckOut)}</div></div>
          <div className="kv"><div className="k">Về sớm</div><div className="v mono">{rec.earlyLeaveMinutes > 0 ? `${rec.earlyLeaveMinutes}'` : '—'}</div></div>
          <div className="kv"><div className="k">Phút thiếu</div><div className="v mono">{rec.missingMinutes > 0 ? `${rec.missingMinutes}'` : '—'}</div></div>
          <div className="kv"><div className="k">Cờ kiểm tra</div><div className="v" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {rec.faceSuspect && <Badge kind="red">Khuôn mặt nghi ngờ</Badge>}
            {rec.outOfZone && <Badge kind="red">Ngoài vùng VP</Badge>}
            {rec.outOfWindow && <Badge kind="amber">Ngoài khung giờ</Badge>}
            {!rec.faceSuspect && !rec.outOfZone && !rec.outOfWindow && <span className="faint">Không có</span>}
          </div></div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginTop: 20, flexWrap: 'wrap' }}>
          {rec.hasImg && (
            <figure style={{ margin: 0 }}>
              <img src={img('check_in_photo')} alt="check-in" style={{ width: 200, borderRadius: 10, display: 'block' }} />
              <figcaption className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Ảnh check-in {rec.checkInMapUrl && <a href={rec.checkInMapUrl} target="_blank" rel="noreferrer"><Icon name="pin" size={13} /> bản đồ</a>}
              </figcaption>
            </figure>
          )}
          {rec.hasCheckOutImg && (
            <figure style={{ margin: 0 }}>
              <img src={img('check_out_photo')} alt="check-out" style={{ width: 200, borderRadius: 10, display: 'block' }} />
              <figcaption className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                Ảnh check-out {rec.checkOutMapUrl && <a href={rec.checkOutMapUrl} target="_blank" rel="noreferrer"><Icon name="pin" size={13} /> bản đồ</a>}
              </figcaption>
            </figure>
          )}
        </div>
      </div>
    </Modal>
  );
}
