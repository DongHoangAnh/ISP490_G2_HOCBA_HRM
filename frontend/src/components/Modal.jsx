import { useEffect } from 'react';

export default function Modal({ children, onClose, lg }) {
  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onClose]);
  return (
    <div className="overlay" onClick={onClose}>
      <div className={'modal' + (lg ? ' modal-lg' : '')} onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
