/* Table wrapper with horizontal scroll — Owner: Hùng. */
export default function TblWrap({ id, children }) {
  return (
    <div id={id} style={{ overflowX: 'auto', width: '100%' }}>
      {children}
    </div>
  );
}
