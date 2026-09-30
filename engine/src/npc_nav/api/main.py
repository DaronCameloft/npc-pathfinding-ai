"""Aplicación FastAPI del motor.

    uvicorn npc_nav.api.main:app --reload

Variable de entorno CORS_ORIGINS: orígenes adicionales separados por coma
(por ejemplo, el dominio de Vercel). `http://localhost:5173` siempre está permitido.
"""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .. import __version__
from .rutas import router

ORIGENES_LOCALES = ['http://localhost:5173']


def origenes_permitidos() -> list[str]:
    extra = [origen.strip().rstrip('/')
             for origen in os.environ.get('CORS_ORIGINS', '').split(',') if origen.strip()]
    return ORIGENES_LOCALES + [origen for origen in extra if origen not in ORIGENES_LOCALES]


app = FastAPI(title='npc-nav', version=__version__,
              description='Motor de navegación de NPCs: BFS, Dijkstra, voraz y A*.')
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=origenes_permitidos(),
                   allow_methods=['GET', 'POST'], allow_headers=['*'])
app.include_router(router)


@app.exception_handler(ValueError)
def _error_de_dominio(_: Request, error: ValueError):
    """Extremos no transitables, caso fuera de rango o bloqueos inválidos."""
    return JSONResponse(status_code=422, content={'detail': str(error)})
