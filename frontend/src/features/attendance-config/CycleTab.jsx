import React from 'react';
import Icon from '../../components/Icon';
import TblWrap from '../../components/TblWrap';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

export default function CycleTab({ data, setData, history, setHistory, deletedIds, setDeletedIds }) {
  const addHistory = () => {
    const newItem = {
      applyFrom: new Date().toISOString().split('T')[0],
      periodStartDay: 1
    };
    setHistory([newItem, ...history]);
  };

  const removeHistory = (index) => {
    const item = history[index];
    if (item.id) {
      setDeletedIds([...deletedIds, item.id]);
    }
    const newHistory = [...history];
    newHistory.splice(index, 1);
    setHistory(newHistory);
  };

  const updateHistory = (index, field, value) => {
    const newHistory = [...history];
    newHistory[index] = { ...newHistory[index], [field]: value };
    setHistory(newHistory);
  };

  return (
    <div className="card">
      <div className="card-body" style={{ padding: '24px' }}>
        <div style={{ maxWidth: 400 }}>
          <Field label="Ngày bắt đầu mặc định (mọi tháng)">
            <input type="number" min="1" max="31" style={inp}
              value={data.periodStartDay}
              onChange={(e) => setData({ ...data, periodStartDay: e.target.value })}
            />
          </Field>
          <p className="hint mt-s" style={{ fontSize: 12, color: 'var(--muted)' }}>
            Chu kỳ tính công sẽ bắt đầu từ ngày này và kết thúc vào trước ngày này của tháng kế tiếp.
          </p>
        </div>

        <div className="divider" style={{ margin: '24px 0' }}></div>

        <div className="flex-row items-center mb-m">
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
              Ngoại lệ & Lịch sử đổi chu kỳ
            </span>
          </div>
          <button className="btn btn-sm" onClick={addHistory}>
            <Icon name="plus" size={14} className="mr-s" />
            Thêm mốc áp dụng
          </button>
        </div>

        <TblWrap>
          <table className="tbl">
            <thead>
              <tr>
                <th>Áp dụng từ ngày</th>
                <th>Ngày bắt đầu chu kỳ</th>
                <th width="50"></th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, idx) => (
                <tr key={idx}>
                  <td>
                    <input type="date" style={{ ...inp, padding: '6px 10px' }}
                      value={h.applyFrom}
                      onChange={(e) => updateHistory(idx, 'applyFrom', e.target.value)}
                    />
                  </td>
                  <td>
                    <input type="number" min="1" max="31" style={{ ...inp, padding: '6px 10px' }}
                      value={h.periodStartDay}
                      onChange={(e) => updateHistory(idx, 'periodStartDay', e.target.value)}
                    />
                  </td>
                  <td className="text-right">
                    <button className="icon-btn text-danger" onClick={() => removeHistory(idx)}>
                      <Icon name="trash" size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan="3" className="text-center text-muted pad-v">Chưa có mốc lịch sử nào.</td>
                </tr>
              )}
            </tbody>
          </table>
        </TblWrap>
      </div>
    </div>
  );
}
