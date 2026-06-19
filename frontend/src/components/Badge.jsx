export default function Badge({ kind, children, dot }) {
  return (
    <span className={'badge badge-' + kind}>
      {dot && <span className="bdot"></span>}
      {children}
    </span>
  );
}
