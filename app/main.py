from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import config, derivados, productos, ventas
from . import services
from .calculos import ganancia_neta, precio_total
from .sheets import SheetsNotConfigured

app = FastAPI(title="Calculadora Calcas Pop", version="2.0.0")

origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "*").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(productos.router)
app.include_router(derivados.router)
app.include_router(ventas.router)
app.include_router(config.router)


@app.on_event("startup")
def startup() -> None:
    sub = 3000.0
    gan = ganancia_neta(sub, 50.0)
    tot = precio_total(sub, gan, 800.0, 200.0)
    assert abs(gan - 1500.0) < 1e-9 and abs(tot - 5500.0) < 1e-9
    try:
        services.ensure_defaults()
    except SheetsNotConfigured as exc:
        # Permite arrancar el proceso; /api/health avisará
        app.state.sheets_error = str(exc)
    else:
        app.state.sheets_error = None


@app.get("/api/health")
def health():
    err = getattr(app.state, "sheets_error", None)
    return {
        "ok": err is None,
        "app": "Calculadora Calcas Pop",
        "storage": "google_sheets",
        "sheets_error": err,
        "ejemplo": {"subtotal": 3000, "ganancia_neta": 1500, "precio_total": 5500},
    }
