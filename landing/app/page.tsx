import Link from "next/link";

export default function Page() {
  return (
    <div className="container">
      <div className="nav">
        <div className="brand">
          <div className="logo" />
          <div>Tracker de Gastos</div>
          <div className="pill">gratis · privado · 1h</div>
        </div>
        <div className="pill">MVP en construcción</div>
      </div>

      <div className="hero">
        <div className="panel">
          <h1 className="h1">Subí tus extractos y mirá tus métricas en 1 minuto.</h1>
          <p className="lead">
            Una herramienta simple para juntar movimientos (Mercado Pago / banco / tarjeta), asignar categorías por reglas y
            calcular tu cumplimiento de presupuesto. Tus archivos se procesan en una sesión efímera y se eliminan automáticamente.
          </p>

          <div className="ctaRow">
            <Link className="btn btnPrimary" href="/intent">
              Quiero probarlo
            </Link>
            <a className="btn btnGhost" href="https://github.com/" target="_blank" rel="noreferrer">
              Ver el repo (pronto)
            </a>
          </div>

          <div className="grid2">
            <div className="item">
              <p className="itemTitle">Privacidad por defecto</p>
              <p className="itemText">Sesión sin cuenta. Retención 1 hora. Botón para borrar todo al instante.</p>
            </div>
            <div className="item">
              <p className="itemTitle">Reglas editables</p>
              <p className="itemText">Keywords y regex por categoría. Reprocesás y listo.</p>
            </div>
          </div>
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
            <div className="bar">
              <div />
            </div>
            <div className="kpiRow">
              <div className="kpi">
                <div className="kpiLabel">Total mes</div>
                <div className="kpiValue">$ 1.757.310</div>
              </div>
              <div className="kpi">
                <div className="kpiLabel">Cumplimiento</div>
                <div className="kpiValue">76%</div>
              </div>
            </div>
            <div className="footer">
              Esta es una maqueta para comunicar la idea. El MVP funcional corre aparte en backend Python.
            </div>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 18 }}>
        <h3 style={{ margin: 0 }}>¿Qué es “Quiero probarlo”?</h3>
        <p className="lead" style={{ marginTop: 10 }}>
          Hoy te va a aparecer un mensaje de “estoy haciendo una mejora de último minuto”. Ese click me ayuda a medir interés
          mientras termino de pulir la experiencia.
        </p>
      </div>
    </div>
  );
}

