from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import products, search, uploads


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(products.router)
    app.include_router(search.router)
    app.include_router(uploads.router)

    @app.on_event("startup")
    async def startup() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

