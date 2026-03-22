# Deploy the MVP backend (FastAPI)

The web UI + API live in `mvp_web/`. Deploy this **separately** from the Vercel landing (`landing/`).

## What you get

- Upload statements → run pipeline → download XLSX + metrics
- Ephemeral sessions (default **1h**), storage under `TG_STORAGE_ROOT`
- Health check: `GET /health`

## Environment variables

| Variable | Default | Notes |
|----------|---------|--------|
| `PORT` | `8000` | Set automatically on Render / Railway / Fly |
| `TG_TTL_SECONDS` | `3600` | Session TTL (1 hour) |
| `TG_MAX_BYTES` | `25MB` | Max upload size per session |
| `TG_MAX_FILES` | `30` | Max files per session |
| `TG_COOKIE_SECURE` | `0` | Set to **`1`** in production (HTTPS) |
| `TG_STORAGE_ROOT` | `./storage` locally; **`/tmp/tg-storage` in Docker** | Must be **writable**. Avoid `/data/...` unless you know the host allows writes there (some platforms mount `/data` read-only). |
| `TG_CORS_ORIGINS` | _(empty)_ | Comma-separated origins allowed to call the API from the browser (e.g. `https://tracker-gastos.vercel.app`). **Required** for the Vercel `/go` page to poll `/health` before redirect; without it, the wait screen cannot verify the server is up. |

## Option A — Docker (Fly.io, Railway, any host)

```bash
docker build -t spend-tracker-api .
docker run -p 8000:8000 \
  -e TG_COOKIE_SECURE=1 \
  spend-tracker-api
```

Open `http://localhost:8000/`.

## Option B — Render (Web Service)

1. New **Web Service** → connect repo `tracker-gastos`.
2. **Root directory**: leave empty (repo root) **or** set if you only deploy this service from monorepo.
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `uvicorn mvp_web.main:app --host 0.0.0.0 --port $PORT`
5. **Environment**:
   - `TG_COOKIE_SECURE` = `1`
   - `TG_CORS_ORIGINS` = `https://tracker-gastos.vercel.app` (your real Vercel URL; comma-separate preview domains if needed)
   - Optional: leave `TG_STORAGE_ROOT` unset to use the image default (`/tmp/tg-storage`), or set any **writable** path.

6. Health check path: `/health`

## Option C — Railway

1. New project → Deploy from GitHub → select repo.
2. **Start command**: `uvicorn mvp_web.main:app --host 0.0.0.0 --port $PORT`
3. Add env vars as above (`TG_COOKIE_SECURE=1`).

## Landing (Vercel) + API (different domain)

Cookies are **per domain**. The MVP UI is served by the API itself at `/`.

- **Simplest**: share the **API URL** as “the app” (e.g. `https://tracker-gastos-api.onrender.com`).
- **If you keep the marketing site on Vercel**: change the “Try it” button to `https://YOUR-API-HOST/` (full URL). First visit sets the session cookie on the API domain.

Cross-origin embedding (iframe) is **not** supported for this cookie model; use a normal link.

## Free tier limits

Python + pandas + PDF parsing can be **slow** or hit **memory** limits on small free tiers. If builds fail, upgrade the instance or switch to a paid small box.
