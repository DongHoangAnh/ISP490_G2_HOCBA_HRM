import React from 'react';
import Icon from '../../components/Icon';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, children, hint }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
      {hint && <span style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{hint}</span>}
    </label>
  );
}

export default function PolicyTab({ data, setData }) {
  const update = (field, val) => {
    setData({ ...data, [field]: val });
  };

  const handleUrlChange = (val) => {
    update('officeMapUrl', val);

    // Regex 1: Định dạng @lat,lng (phổ biến nhất trên browser)
    // Regex 2: Định dạng q=lat,lng (thường có trong link chia sẻ)
    const regex1 = /@(-?\d+\.\d+),(-?\d+\.\d+)/;
    const regex2 = /q=(-?\d+\.\d+),(-?\d+\.\d+)/;

    const match = val.match(regex1) || val.match(regex2);

    if (match) {
      setData(prev => ({
        ...prev,
        officeMapUrl: val,
        officeLat: parseFloat(match[1]),
        officeLng: parseFloat(match[2])
      }));
    }
  };

  const isShortLink = data.officeMapUrl && data.officeMapUrl.includes('maps.app.goo.gl') && !data.officeMapUrl.match(/@|-?\d+\.\d+,-?\d+\.\d+/);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      <div className="card">
        <div className="card-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)', padding: '12px 16px' }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', marginRight: 12 }}>
            <Icon name="clock" size={16} />
          </div>
          <div className="t" style={{ fontSize: 15, fontWeight: 700 }}>Khung giờ & Chốt công</div>
        </div>
        <div className="card-body" style={{ padding: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <Field label="Vào từ (giờ)">
              <input type="number" step="0.5" style={inp} value={data.morningStart} onChange={e => update('morningStart', e.target.value)} />
            </Field>
            <Field label="Đến (giờ)">
              <input type="number" step="0.5" style={inp} value={data.morningEnd} onChange={e => update('morningEnd', e.target.value)} />
            </Field>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <Field label="Ra từ (giờ)">
              <input type="number" step="0.5" style={inp} value={data.eveningStart} onChange={e => update('eveningStart', e.target.value)} />
            </Field>
            <Field label="Đến (giờ)">
              <input type="number" step="0.5" style={inp} value={data.eveningEnd} onChange={e => update('eveningEnd', e.target.value)} />
            </Field>
          </div>
          <div className="divider" style={{ margin: '20px 0' }}></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Field label="Mốc đi trễ (giờ)" hint="VD: 9.5 = 09:30">
              <input type="number" step="0.1" style={inp} value={data.lateCutoff} onChange={e => update('lateCutoff', e.target.value)} />
            </Field>
            <Field label="Số ngày vi phạm miễn trừ">
              <input type="number" style={inp} value={data.violationFreeDays} onChange={e => update('violationFreeDays', e.target.value)} />
            </Field>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)', padding: '12px 16px' }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', marginRight: 12 }}>
            <Icon name="map" size={16} />
          </div>
          <div className="t" style={{ fontSize: 15, fontWeight: 700 }}>Địa điểm & Nhận diện</div>
        </div>
        <div className="card-body" style={{ padding: 20 }}>
          <div className="mb-m">
            <Field label="Link vị trí Google Maps" hint="Dùng link đầy đủ trên browser để tự nhận diện tọa độ">
              <input type="text" style={{ ...inp, borderColor: isShortLink ? 'var(--gold-500)' : 'var(--border-strong)' }}
                value={data.officeMapUrl || ''}
                placeholder="https://www.google.com/maps/..."
                onChange={e => handleUrlChange(e.target.value)} />
            </Field>
            {isShortLink && (
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--gold-700)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Icon name="alertTriangle" size={14} />
                Link rút gọn không chứa tọa độ. Vui lòng dùng link đầy đủ hoặc nhập tay Lat/Lng bên dưới.
              </div>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 12 }}>
            <Field label="Vĩ độ (Lat)">
              <input type="number" style={inp} value={data.officeLat} onChange={e => update('officeLat', e.target.value)} />
            </Field>
            <Field label="Kinh độ (Lng)">
              <input type="number" style={inp} value={data.officeLng} onChange={e => update('officeLng', e.target.value)} />
            </Field>
          </div>
          <Field label="Bán kính cho phép (m)">
            <input type="number" style={inp} value={data.officeRadiusM} onChange={e => update('officeRadiusM', e.target.value)} />
          </Field>

          <div className="divider" style={{ margin: '20px 0' }}></div>

          <Field label="Ngưỡng so khớp mặt" hint="Thấp = khắt khe hơn. Mặc định 0.6.">
            <input type="number" step="0.01" style={inp} value={data.faceThreshold} onChange={e => update('faceThreshold', e.target.value)} />
          </Field>

          <div style={{ marginTop: 20, padding: 12, borderRadius: 10, background: 'var(--blue-50)', border: '1px solid var(--blue-100)', color: 'var(--blue-700)', fontSize: 12.5 }}>
            <Icon name="info" size={14} style={{ marginRight: 6 }} />
            Tọa độ được dùng để giới hạn phạm vi điểm danh qua ứng dụng di động.
          </div>
        </div>
      </div>
    </div>
  );
}
