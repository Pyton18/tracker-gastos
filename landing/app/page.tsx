/** Live API (Render). Override in Vercel: NEXT_PUBLIC_MVP_API_URL */
const MVP_API_URL =
  process.env.NEXT_PUBLIC_MVP_API_URL ?? "https://tracker-gastos-api.onrender.com";

export default function Page() {
  return (
    <div className="container">
      <div className="nav">
        <div className="brand">
          <div className="logo" />
          <div>Spend Tracker</div>
          <div className="pill">free · private · 1h</div>
        </div>
        <div className="pill">Private beta</div>
      </div>

      <div className="hero">
        <div className="panel">
          <h1 className="h1">Upload your statements and see your metrics in 1 minute.</h1>
          <p className="lead">
            A simple way to consolidate monthly transactions (wallet / bank / card), auto‑categorize them with rules, and track
            budget progress. Your files are processed in an ephemeral session and deleted automatically.
          </p>

          <div className="ctaRow">
            <a className="btn btnPrimary" href={MVP_API_URL} target="_blank" rel="noopener noreferrer">
              Try it
            </a>
            <a className="btn btnGhost" href="https://github.com/Pyton18/tracker-gastos" target="_blank" rel="noreferrer">
              GitHub
            </a>
          </div>

          <div className="grid2">
            <div className="item">
              <p className="itemTitle">Privacy by default</p>
              <p className="itemText">No account required. 1‑hour retention. One click to delete everything instantly.</p>
            </div>
            <div className="item">
              <p className="itemTitle">Editable rules</p>
              <p className="itemText">Keywords and patterns per category. Adjust and re‑run in seconds.</p>
            </div>
          </div>
          <p className="fineprint">
            Currently supports: <strong>Mercado Pago</strong> statements and <strong>Santander</strong> account / Visa PDFs (Argentina).
            More sources coming.
          </p>
        </div>

        <div className="panel">
          <div className="mock">
            <div className="mockHeader">
              <div className="dotRow">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
              <div className="mockTitle">Preview</div>
            </div>
            <div className="simpleFlow" aria-hidden="true">
              <div className="fileIcon pdf">PDF</div>
              <div className="arrow">→</div>
              <div className="fileIcon xlsx">XLSX</div>
              <div className="arrow">→</div>
              <div className="factory" title="Process">
                🏭
              </div>
              <div className="arrow">→</div>
              <div className="bars">
                <div className="bar"><div /></div>
                <div className="bar bar2"><div /></div>
                <div className="bar bar3"><div /></div>
              </div>
            </div>
            <div className="kpiRow">
              <div className="kpi">
                <div className="kpiLabel">Monthly total</div>
                <div className="kpiValue">$ 1,757,310</div>
              </div>
              <div className="kpi">
                <div className="kpiLabel">Budget usage</div>
                <div className="kpiValue">76%</div>
              </div>
            </div>
            <div className="footer">Drag & drop your files, get a clear monthly view.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

