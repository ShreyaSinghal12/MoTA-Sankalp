export default function Section({ n, title, hint, children, right }) {
  return (
    <section className="section">
      <header className="section-head">
        <div>
          {n !== undefined && <span className="section-n">{String(n).padStart(2, "0")}</span>}
          <h2>{title}</h2>
          {hint && <p className="hint">{hint}</p>}
        </div>
        {right}
      </header>
      <div className="section-body">{children}</div>
    </section>
  );
}
