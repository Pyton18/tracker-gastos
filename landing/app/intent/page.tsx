import Link from "next/link";

export default function IntentPage() {
  return (
    <div className="container">
      <div className="nav">
        <div className="brand">
          <div className="logo" />
          <div>Tracker de Gastos</div>
          <div className="pill">señal registrada</div>
        </div>
        <Link className="pill" href="/">
          Volver
        </Link>
      </div>

      <div className="panel" style={{ marginTop: 18 }}>
        <h1 className="h1" style={{ fontSize: 38 }}>
          Che, le estoy haciendo una mejora de último minuto.
        </h1>
        <p className="lead">
          Gracias por el click. En breve habilito el MVP para subir archivos y ver métricas desde la web.
        </p>

        <div className="ctaRow">
          <Link className="btn btnPrimary" href="/">
            Volver al inicio
          </Link>
        </div>

        <div className="footer">
          Para medir intención sin pedirte datos personales, este botón solo cuenta visitas a esta página.
        </div>
      </div>
    </div>
  );
}

