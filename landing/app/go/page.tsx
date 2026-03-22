"use client";

import { useEffect, useState } from "react";

const MVP_API_URL =
  process.env.NEXT_PUBLIC_MVP_API_URL ?? "https://tracker-gastos-api.onrender.com";

const POLL_MS = 2000;
/** Free Render can take 30–60s to wake; don’t cut off too early */
const MAX_WAIT_MS = 120000;

/**
 * Waits until the API responds on /health, then redirects.
 * Stays on Vercel during cold start so users don’t see Render’s “service waking up” screen.
 */
export default function GoPage() {
  const [error, setError] = useState(false);
  const [status, setStatus] = useState("Connecting…");

  useEffect(() => {
    if (!MVP_API_URL.startsWith("http")) {
      setError(true);
      return;
    }

    const base = MVP_API_URL.replace(/\/$/, "");
    const healthUrl = `${base}/health`;
    let cancelled = false;
    const started = Date.now();

    const tick = async () => {
      while (!cancelled && Date.now() - started < MAX_WAIT_MS) {
        try {
          const r = await fetch(healthUrl, {
            method: "GET",
            mode: "cors",
            cache: "no-store",
          });
          if (r.ok) {
            setStatus("Opening app…");
            window.location.assign(`${base}/`);
            return;
          }
        } catch {
          // still waking up or transient network
        }
        const elapsed = Math.round((Date.now() - started) / 1000);
        setStatus(`Starting the server… (${elapsed}s — free hosting can take up to ~1 min when idle)`);
        await new Promise((r) => setTimeout(r, POLL_MS));
      }
      if (!cancelled) {
        setError(true);
        setStatus("Timed out");
      }
    };

    void tick();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="container">
      <div className="panel" style={{ marginTop: 48, textAlign: "center" as const }}>
        <h1 className="h1" style={{ fontSize: 28 }}>
          Spend Tracker
        </h1>
        <p className="lead" style={{ marginTop: 16 }}>
          {status}
        </p>
        {error && (
          <p className="lead" style={{ color: "#b00020", marginTop: 12 }}>
            Could not reach the app in time. The server may still be waking up —{" "}
            <a href={`${MVP_API_URL.replace(/\/$/, "")}/`}>try opening it directly</a> or wait a minute and refresh.
            If this always fails, check <code>TG_CORS_ORIGINS</code> on Render includes this Vercel domain.
          </p>
        )}
        <p className="fineprint" style={{ marginTop: 24 }}>
          <a href={`${MVP_API_URL.replace(/\/$/, "")}/`}>Skip waiting and open the app</a> (you may see the host’s loading screen)
        </p>
      </div>
    </div>
  );
}
