"use client";

import { useEffect, useState } from "react";

const MVP_API_URL =
  process.env.NEXT_PUBLIC_MVP_API_URL ?? "https://tracker-gastos-api.onrender.com";

/**
 * Intermediate page so Vercel Web Analytics records a pageview on /go
 * before sending the user to the live API (Render).
 * In the dashboard, filter by path /go to approximate "Try it" intent.
 */
export default function GoPage() {
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!MVP_API_URL.startsWith("http")) {
      setError(true);
      return;
    }
    window.location.assign(MVP_API_URL);
  }, []);

  return (
    <div className="container">
      <div className="panel" style={{ marginTop: 48, textAlign: "center" as const }}>
        <h1 className="h1" style={{ fontSize: 28 }}>
          Opening the app…
        </h1>
        <p className="lead">You’ll be redirected to the live tool in a moment.</p>
        {error && (
          <p className="lead" style={{ color: "#b00020" }}>
            Invalid app URL. Set <code>NEXT_PUBLIC_MVP_API_URL</code> in Vercel.
          </p>
        )}
        <p className="fineprint" style={{ marginTop: 24 }}>
          <a href={MVP_API_URL}>Click here if nothing happens</a>
        </p>
      </div>
    </div>
  );
}
