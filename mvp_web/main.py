from __future__ import annotations

import json
import mimetypes
import os
import threading
import time
from pathlib import Path

from fastapi import Cookie, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .executor import InProcessExecutor
from .pipeline_runner import validate_and_write_categorias_json
from .storage import cleanup_expired_sessions, delete_session, ensure_session, new_session_id, read_run_state, session_paths


SESSION_COOKIE = "tg_session"
TTL_SECONDS = int(os.environ.get("TG_TTL_SECONDS", "3600"))  # 1h default
MAX_BYTES = int(os.environ.get("TG_MAX_BYTES", str(25 * 1024 * 1024)))  # 25MB
MAX_FILES = int(os.environ.get("TG_MAX_FILES", "30"))
COOKIE_SECURE = os.environ.get("TG_COOKIE_SECURE", "0") == "1"
CLEANUP_INTERVAL_SECONDS = int(os.environ.get("TG_CLEANUP_INTERVAL_SECONDS", "600"))  # 10 min

app = FastAPI(title="Spend Tracker (MVP API)")
templates = Jinja2Templates(directory=str((Path(__file__).parent / "templates").resolve()))
executor = InProcessExecutor()


@app.get("/health")
def health():
    """Health check for Render / Railway / Fly / k8s."""
    return {"ok": True}


def _get_or_create_session_id(response: Response, session_id: str | None) -> str:
    if session_id:
        return session_id
    sid = new_session_id()
    # httpOnly cookie for privacy; sameSite Lax is ok for MVP
    response.set_cookie(
        key=SESSION_COOKIE,
        value=sid,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,  # set true behind HTTPS proxy in deploy
        max_age=TTL_SECONDS,
    )
    return sid


def _init_session_files(sp):
    # Copy example config into session config if missing
    root = Path(__file__).resolve().parent.parent
    ejemplo_cat = root / "config" / "categorias.ejemplo.json"
    ejemplo_obj = root / "config" / "objetivos.ejemplo.json"
    if not sp.categorias_path.exists():
        sp.categorias_path.write_text(ejemplo_cat.read_text(encoding="utf-8"), encoding="utf-8")
    if not sp.objetivos_path.exists():
        sp.objetivos_path.write_text(ejemplo_obj.read_text(encoding="utf-8"), encoding="utf-8")


@app.on_event("startup")
def _startup_cleanup():
    cleanup_expired_sessions(TTL_SECONDS)
    _start_cleanup_loop()


def _start_cleanup_loop():
    def loop():
        try:
            cleanup_expired_sessions(TTL_SECONDS)
        finally:
            t = threading.Timer(CLEANUP_INTERVAL_SECONDS, loop)
            t.daemon = True
            t.start()

    t = threading.Timer(CLEANUP_INTERVAL_SECONDS, loop)
    t.daemon = True
    t.start()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, response: Response, tg_session: str | None = Cookie(default=None)):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    _init_session_files(sp)
    files = sorted([p.name for p in sp.inputs.glob("*") if p.is_file()])
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "session_id_short": sid[:8],
            "files": files,
        },
        response=response,
    )


@app.post("/api/uploads")
async def upload_files(
    response: Response,
    tg_session: str | None = Cookie(default=None),
    files: list[UploadFile] = File(...),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    _init_session_files(sp)

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Too many files (max {MAX_FILES}).")

    total = 0
    saved = []
    for f in files:
        content = await f.read()
        total += len(content)
        if total > MAX_BYTES:
            raise HTTPException(status_code=400, detail="Session size limit exceeded.")
        name = Path(f.filename or "upload.bin").name
        out = sp.inputs / name
        out.write_bytes(content)
        saved.append(name)

    return {"ok": True, "saved": saved, "total_bytes": total}


@app.post("/api/process")
def process(
    response: Response,
    tg_session: str | None = Cookie(default=None),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    _init_session_files(sp)

    # Siempre inferido desde las fechas de los movimientos (no hay selector de período en la web).
    res = executor.submit(sp, None)
    return {"ok": True, "run_id": res.run_id}


@app.get("/api/runs/{run_id}")
def run_status(
    response: Response,
    run_id: str,
    tg_session: str | None = Cookie(default=None),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    state = read_run_state(sp, run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found.")
    return state


@app.get("/resultados/{run_id}", response_class=HTMLResponse)
def resultados_page(
    request: Request,
    response: Response,
    run_id: str,
    tg_session: str | None = Cookie(default=None),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    state = read_run_state(sp, run_id) or {"run_id": run_id, "status": "unknown"}
    return templates.TemplateResponse(
        "resultados.html",
        {"request": request, "run_id": run_id, "state": state},
        response=response,
    )


@app.get("/categorias", response_class=HTMLResponse)
def categorias_page(
    request: Request,
    response: Response,
    tg_session: str | None = Cookie(default=None),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    _init_session_files(sp)
    raw = sp.categorias_path.read_text(encoding="utf-8")
    return templates.TemplateResponse(
        "categorias.html",
        {"request": request, "raw_json": raw},
        response=response,
    )


@app.post("/categorias")
def save_categorias(
    request: Request,
    response: Response,
    tg_session: str | None = Cookie(default=None),
    raw_json: str = Form(...),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)
    ok, errors = validate_and_write_categorias_json(sp.categorias_path, raw_json)
    if not ok:
        return templates.TemplateResponse(
            "categorias.html",
            {"request": request, "raw_json": raw_json, "errors": errors},
            status_code=400,
            response=response,
        )
    return RedirectResponse(url="/categorias", status_code=303)


@app.get("/api/outputs/{periodo}/{name}")
def download_output(
    response: Response,
    periodo: str,
    name: str,
    tg_session: str | None = Cookie(default=None),
):
    sid = _get_or_create_session_id(response, tg_session)
    sp = ensure_session(sid)

    mapping = {
        "estandarizado": sp.outputs / "estandarizado" / f"estandarizado_{periodo}.xlsx",
        "categorizado": sp.outputs / "categorizado" / f"categorizado_{periodo}.xlsx",
        "metricas": sp.outputs / "metricas" / f"metricas_{periodo}.xlsx",
    }
    path = mapping.get(name)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path, media_type=media_type or "application/octet-stream", filename=path.name)


@app.post("/api/session/delete")
def delete_my_session(response: Response, tg_session: str | None = Cookie(default=None)):
    if tg_session:
        delete_session(tg_session)
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.post("/api/cleanup")
def manual_cleanup():
    # optional endpoint for ops; can be protected later
    deleted = cleanup_expired_sessions(TTL_SECONDS)
    return {"ok": True, "deleted": deleted}

