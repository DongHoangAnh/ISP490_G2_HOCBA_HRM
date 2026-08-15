/* <th> bấm được để sắp xếp — dùng với hook useSort. Owner: Tân.
   sk = khoá cột (trùng key trong accessors của useSort), sort = object hook trả về. */
export default function SortTh({ sk, sort, children, style, className, title }) {
  const active = sort.sortKey === sk;
  const arrow = active ? (sort.sortDir === 'asc' ? '▲' : '▼') : '⇅';
  return (
    <th className={className} title={title || 'Bấm để sắp xếp'}
      style={{ cursor: 'pointer', userSelect: 'none', ...style }}
      onClick={() => sort.toggle(sk)}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
        {children}
        <span style={{ fontSize: 9, lineHeight: 1, opacity: active ? 1 : 0.35,
                       color: active ? 'var(--red-600)' : 'inherit' }}>{arrow}</span>
      </span>
    </th>
  );
}
