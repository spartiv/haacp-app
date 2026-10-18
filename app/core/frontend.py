"""Serves the built web app (web/dist) from the API server: one service, one
origin, so the browser needs no CORS. Any path that isn't /api or a real file
gets index.html, letting the React router handle deep links on reload."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Vite fingerprints asset filenames, so they can be cached forever; index.html
# must always be revalidated or users would keep loading an old build.
_NO_CACHE = {"Cache-Control": "no-cache"}


def mount_frontend(app: FastAPI, dist_dir: Path) -> None:
    root = dist_dir.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise RuntimeError(f"Frontend build not found: {index} (run `npm run build` in web/)")

    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            # Unknown API route: keep the JSON error envelope, never return HTML.
            raise StarletteHTTPException(status_code=404)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(index, headers=_NO_CACHE)

    logger.info("Serving web app from %s", root)
