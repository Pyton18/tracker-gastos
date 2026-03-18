from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .pipeline_runner import new_run_id, run_pipeline_for_session
from .storage import SessionPaths, write_run_state


@dataclass(frozen=True)
class SubmitResult:
    run_id: str


class InProcessExecutor:
    """
    Ejecuta el pipeline en un thread dentro del mismo proceso.
    Diseñado para poder reemplazarse por un QueueExecutor (worker) a futuro.
    """

    def __init__(self):
        self._lock = threading.Lock()

    def submit(self, sp: SessionPaths, periodo: str) -> SubmitResult:
        run_id = new_run_id()
        state = {
            "run_id": run_id,
            "periodo": periodo,
            "status": "queued",
            "created_at": int(time.time()),
        }
        write_run_state(sp, run_id, state)

        t = threading.Thread(target=self._run, args=(sp, run_id, periodo), daemon=True)
        t.start()
        return SubmitResult(run_id=run_id)

    def _run(self, sp: SessionPaths, run_id: str, periodo: str) -> None:
        state = {
            "run_id": run_id,
            "periodo": periodo,
            "status": "running",
            "started_at": int(time.time()),
        }
        write_run_state(sp, run_id, state)
        try:
            summary = run_pipeline_for_session(
                periodo=periodo,
                inputs_dir=sp.inputs,
                outputs_dir=sp.outputs,
                categorias_path=sp.categorias_path,
                objetivos_path=sp.objetivos_path,
            )
            state.update(
                {
                    "status": "done",
                    "finished_at": int(time.time()),
                    "summary": summary,
                }
            )
            write_run_state(sp, run_id, state)
        except Exception as e:
            state.update(
                {
                    "status": "error",
                    "finished_at": int(time.time()),
                    "error": str(e),
                }
            )
            write_run_state(sp, run_id, state)

