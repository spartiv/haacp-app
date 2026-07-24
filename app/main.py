from fastapi import FastAPI

from app.routers.v1 import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Polton HACCP API")
    app.include_router(api_router)
    return app


app = create_app()
