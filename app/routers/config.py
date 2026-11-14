from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..schemas import ConfigOut, ConfigUpdate, PorcentajeUpdate
from .. import services

router = APIRouter(prefix="/api/config", tags=["config"])

ALLOWED = {".jpg", ".jpeg", ".png", ".bmp"}
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _config_out() -> ConfigOut:
    cfg = services.get_config_map()
    imagen = cfg.get("RutaImagen", "")
    imagen_url = None
    if imagen:
        path = Path(imagen)
        if path.is_file():
            imagen_url = f"/api/config/imagen?v={path.stat().st_mtime_ns}"
        elif imagen.startswith("http"):
            imagen_url = imagen
    try:
        porcentaje = float(cfg.get("PorcentajeGanancia", "0") or 0)
    except ValueError:
        porcentaje = 0.0
    if porcentaje < 0:
        porcentaje = 0.0
    return ConfigOut(
        color_fondo=cfg.get("ColorFondo", "#2d1b4e") or "#2d1b4e",
        porcentaje_ganancia=porcentaje,
        imagen_url=imagen_url,
        paleta_colores=services.get_paleta(),
    )


@router.get("", response_model=ConfigOut)
def obtener():
    return _config_out()


@router.put("", response_model=ConfigOut)
def actualizar(data: ConfigUpdate):
    if data.color_fondo is not None:
        services.set_config("ColorFondo", data.color_fondo.strip() or "#2d1b4e")
    if data.porcentaje_ganancia is not None:
        if data.porcentaje_ganancia < 0:
            raise HTTPException(400, "El porcentaje no puede ser negativo.")
        services.set_config("PorcentajeGanancia", str(data.porcentaje_ganancia))
    if data.paleta_colores is not None:
        services.set_paleta(data.paleta_colores)
    return _config_out()


@router.put("/porcentaje", response_model=ConfigOut)
def guardar_porcentaje(data: PorcentajeUpdate):
    services.set_config("PorcentajeGanancia", str(data.porcentaje))
    return _config_out()


@router.get("/imagen")
def servir_imagen():
    cfg = services.get_config_map()
    ruta = cfg.get("RutaImagen", "")
    if ruta.startswith("http"):
        raise HTTPException(302, detail=ruta)
    path = Path(ruta) if ruta else None
    if path and path.is_file():
        return FileResponse(path)
    candidatos = [
        Path(__file__).resolve().parents[3] / "imagenes" / "inicio.jpeg",
        Path(__file__).resolve().parents[3] / "logo.jpeg",
        UPLOADS_DIR / "inicio.jpeg",
    ]
    for c in candidatos:
        if c.is_file():
            return FileResponse(c)
    raise HTTPException(404, "No hay imagen.")


@router.post("/imagen", response_model=ConfigOut)
async def subir_imagen(file: UploadFile = File(...)):
    nombre = file.filename or "inicio.jpg"
    ext = Path(nombre).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, "Solo jpg, jpeg, png o bmp.")
    destino = UPLOADS_DIR / f"inicio{ext}"
    contenido = await file.read()
    if len(contenido) > 8_000_000:
        raise HTTPException(400, "La imagen pesa más de 8 MB.")
    destino.write_bytes(contenido)
    for viejo in UPLOADS_DIR.glob("inicio.*"):
        if viejo != destino:
            viejo.unlink(missing_ok=True)
    services.set_config("RutaImagen", str(destino))
    return _config_out()


@router.delete("/imagen", response_model=ConfigOut)
def quitar_imagen():
    for viejo in UPLOADS_DIR.glob("inicio.*"):
        viejo.unlink(missing_ok=True)
    services.set_config("RutaImagen", "")
    return _config_out()
