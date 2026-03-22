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
            <a className="btn btnPrimary" href="/go">
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
            <strong>Argentina:</strong> works with <strong>Mercado Pago</strong> exports and <strong>Santander</strong> checking + Visa
            (XLSX or PDF). Download your latest movements and statements from each site, then upload them in the app—no other banks
            are supported yet.
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
            <div className="footer">Pick your exports, run the pipeline, download your monthly workbook.</div>
          </div>
        </div>
      </div>

      <section className="stepsSection" aria-labelledby="how-heading">
        <h2 id="how-heading" className="stepsTitle">
          How it works
        </h2>
        <ol className="stepList">
          <li>
            <span className="stepNum">1</span>
            <div>
              <p className="stepHead">Get your files</p>
              <p className="stepBody">
                From Santander: latest account movements and your Visa statement. From Mercado Pago: your account activity export.
                Use the formats the bank/wallet provides (XLSX or PDF).
              </p>
            </div>
          </li>
          <li>
            <span className="stepNum">2</span>
            <div>
              <p className="stepHead">Upload in the app</p>
              <p className="stepBody">
                Files upload as soon as you confirm in the file dialog. Then run the pipeline to merge and normalize everything.
              </p>
            </div>
          </li>
          <li>
            <span className="stepNum">3</span>
            <div>
              <p className="stepHead">Optional: category rules</p>
              <p className="stepBody">
                Edit JSON rules with <strong>keywords</strong> and <strong>regex</strong> patterns so transaction descriptions map to
                your categories (regex handles messy merchant strings). Re-run until you’re happy.
              </p>
            </div>
          </li>
          <li>
            <span className="stepNum">4</span>
            <div>
              <p className="stepHead">Download results</p>
              <p className="stepBody">
                Grab standardized, categorized, and metrics spreadsheets. Session data is deleted after an hour—save what you need.
              </p>
            </div>
          </li>
        </ol>
      </section>
    </div>
  );
}

