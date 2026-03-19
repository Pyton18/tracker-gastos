import Link from "next/link";

export default function IntentPage() {
  return (
    <div className="container">
      <div className="nav">
        <div className="brand">
          <div className="logo" />
          <div>Spend Tracker</div>
          <div className="pill">private beta</div>
        </div>
        <Link className="pill" href="/">
          Back
        </Link>
      </div>

      <div className="panel" style={{ marginTop: 18 }}>
        <h1 className="h1" style={{ fontSize: 38 }}>
          Oops — we're making a last‑minute improvement.
        </h1>
        <p className="lead">
          Please check back shortly.
        </p>

        <div className="ctaRow">
          <Link className="btn btnPrimary" href="/">
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}

