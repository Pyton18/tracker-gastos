from __future__ import annotations

import json
import os
import secrets
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionPaths:
    root: Path
    inputs: Path
    outputs: Path
    config: Path
    runs: Path

    @property
    def categorias_path(self) -> Path:
        return self.config / "categorias.json"

    @property
    def objetivos_path(self) -> Path:
        return self.config / "objetivos.json"


def get_storage_root() -> Path:
    # overrideable via env for deploys
    return Path(os.environ.get("TG_STORAGE_ROOT", "storage")).resolve()


def new_session_id() -> str:
    # 32 bytes -> 64 hex chars
    return secrets.token_hex(32)


def session_paths(session_id: str) -> SessionPaths:
    base = get_storage_root() / "sessions" / session_id
    return SessionPaths(
        root=base,
        inputs=base / "inputs",
        outputs=base / "outputs",
        config=base / "config",
        runs=base / "runs",
    )


def ensure_session(session_id: str) -> SessionPaths:
    sp = session_paths(session_id)
    sp.inputs.mkdir(parents=True, exist_ok=True)
    sp.outputs.mkdir(parents=True, exist_ok=True)
    sp.config.mkdir(parents=True, exist_ok=True)
    sp.runs.mkdir(parents=True, exist_ok=True)
    meta_path = sp.root / "meta.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps({"created_at": int(time.time())}, ensure_ascii=False), encoding="utf-8")
    return sp


def delete_session(session_id: str) -> None:
    sp = session_paths(session_id)
    if sp.root.exists():
        shutil.rmtree(sp.root, ignore_errors=True)


def cleanup_expired_sessions(ttl_seconds: int) -> int:
    root = get_storage_root() / "sessions"
    if not root.exists():
        return 0
    now = int(time.time())
    deleted = 0
    for d in root.iterdir():
        if not d.is_dir():
            continue
        meta = d / "meta.json"
        created_at = None
        try:
            if meta.exists():
                created_at = json.loads(meta.read_text(encoding="utf-8")).get("created_at")
        except Exception:
            created_at = None
        if created_at is None:
            # if corrupt, delete proactively
            shutil.rmtree(d, ignore_errors=True)
            deleted += 1
            continue
        if now - int(created_at) > ttl_seconds:
            shutil.rmtree(d, ignore_errors=True)
            deleted += 1
    return deleted


def write_run_state(sp: SessionPaths, run_id: str, state: dict) -> None:
    path = sp.runs / f"{run_id}.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_run_state(sp: SessionPaths, run_id: str) -> dict | None:
    path = sp.runs / f"{run_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

