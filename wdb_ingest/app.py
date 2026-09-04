"""FastAPI app for the ingestion service — the write-side counterpart to ``wdb_api``.

Mirrors ``wdb_api.app``'s shape: ``create_app()`` with an injectable store (tests pass a temp SQLite),
sync endpoints (FastAPI threadpools them) except the upload which awaits the raw body. Role/identity
come from ``X-WDB-Role`` / ``X-WDB-User`` headers — a simple seam the gate enforces against, swappable
for real auth. Run it locally::

    uv run uvicorn wdb_ingest.app:app --port 8001
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import builder, config, service
from .gate import GateError
from .models import DraftedNote, Role, Submission
from .service import InvalidPlacement, NotFound
from .store import SqliteWorkflowStore, WorkflowStore


def _identity(request: Request) -> tuple[Role, str]:
    role = Role.CURATOR if request.headers.get("X-WDB-Role", "").lower() == "curator" else Role.CONTRIBUTOR
    user = request.headers.get("X-WDB-User") or role.value
    return role, user


def _dump(sub: Submission) -> dict:
    return sub.model_dump(by_alias=True)


class RejectBody(BaseModel):
    reason: str = ""


def create_app(store_factory: Callable[[], WorkflowStore] | None = None) -> FastAPI:
    app = FastAPI(
        title="WDB ingestion API",
        summary="Write-side workflow: submit → draft → two-stage gate → single-builder build handoff (local)",
    )
    store: WorkflowStore = (store_factory or (lambda: SqliteWorkflowStore(config.DB_PATH)))()

    @app.exception_handler(GateError)
    async def _gate_err(request: Request, exc: GateError):  # noqa: ANN202
        return JSONResponse(status_code=403 if exc.forbidden else 409, content={"error": str(exc)})

    @app.exception_handler(NotFound)
    async def _not_found(request: Request, exc: NotFound):  # noqa: ANN202
        return JSONResponse(status_code=404, content={"error": f"No such submission: {exc}"})

    @app.exception_handler(InvalidPlacement)
    async def _bad_placement(request: Request, exc: InvalidPlacement):  # noqa: ANN202
        # an unknown initiative or a path-bearing filename — refused before anything is staged
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "store": type(store).__name__, "root": str(config.WDB_ROOT)}

    @app.get("/submissions")
    def list_submissions(request: Request) -> list[dict]:
        role, user = _identity(request)
        return [_dump(s) for s in service.list_for_role(store, role, user)]

    @app.get("/submissions/{sub_id}")
    def get_submission(sub_id: str) -> dict:
        sub = store.get(sub_id)
        if not sub:
            raise NotFound(sub_id)
        return _dump(sub)

    @app.post("/submit")
    async def submit(request: Request, filename: str, format: str, initiative: str,
                     size_label: str = "", author: str = "", source_url: str = "") -> dict:
        _, user = _identity(request)
        body = await request.body()
        from .models import SubmissionInput

        inp = SubmissionInput(filename=filename, format=format, sizeLabel=size_label,
                              initiative=initiative, author=author, sourceUrl=source_url)
        return _dump(service.submit(store, inp, body, contributor=user))

    # ── contributor transitions ──
    @app.post("/submissions/{sub_id}/open-review")
    def open_review(sub_id: str, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.act(store, sub_id, "open_for_review", role, actor=user))

    @app.post("/submissions/{sub_id}/approve")
    def approve(sub_id: str, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.act(store, sub_id, "approve", role, actor=user))

    @app.post("/submissions/{sub_id}/resubmit")
    def resubmit(sub_id: str, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.act(store, sub_id, "resubmit", role, actor=user))

    @app.patch("/submissions/{sub_id}/draft")
    def edit_draft(sub_id: str, draft: DraftedNote, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.edit_draft(store, sub_id, draft, role, actor=user))

    # ── curator transitions ──
    @app.post("/submissions/{sub_id}/curator-approve")
    def curator_approve(sub_id: str, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.act(store, sub_id, "curator_approve", role, actor=user))

    @app.post("/submissions/{sub_id}/reject")
    def reject(sub_id: str, body: RejectBody, request: Request) -> dict:
        role, user = _identity(request)
        return _dump(service.act(store, sub_id, "reject", role, actor=user, reason=body.reason))

    # ── single-builder build (tracked handoff) — curator/maintainer only ──
    def _require_curator(request: Request) -> None:
        role, _ = _identity(request)
        if role != Role.CURATOR:
            raise GateError("Only the curator/maintainer can run the build.", forbidden=True)

    @app.post("/build")
    def build(request: Request) -> dict:
        _require_curator(request)
        return builder.start_build(store)

    @app.get("/build/status")
    def build_status(request: Request) -> dict:
        # Everyone may READ the status; only the curator's poll may publish (see builder.poll).
        role, _ = _identity(request)
        return builder.poll(store, promote=role == Role.CURATOR)

    @app.post("/build/confirm")
    def build_confirm(request: Request) -> dict:
        _require_curator(request)
        return builder.confirm(store)

    @app.post("/reset")
    def reset(request: Request) -> dict:
        """Wipe the workflow store (dev/test affordance) — curator only."""
        _require_curator(request)
        store.reset()
        return {"status": "reset"}

    return app


app = create_app()
