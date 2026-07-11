/* Nút "Sao chép link" trang tuyển dụng công khai (/jobs/detail/...) —
   cho nhân viên tiếp thị copy link đi rải/truyền thông. Owner: Việt. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import { publicJobUrl, copyText } from './util';

export default function CopyLinkBtn({ url, label = 'Sao chép link' }) {
  const [done, setDone] = useState(false);
  if (!url) return null;
  const full = publicJobUrl(url);
  const doCopy = async (e) => {
    e.stopPropagation();
    if (await copyText(full)) {
      setDone(true);
      setTimeout(() => setDone(false), 1600);
    } else {
      window.prompt('Không tự sao chép được — copy thủ công link dưới đây:', full);
    }
  };
  return (
    <button className="btn btn-ghost btn-sm" onClick={doCopy} title={full}>
      <Icon name={done ? 'check' : 'link'} size={14} />
      {done ? 'Đã chép!' : label}
    </button>
  );
}
