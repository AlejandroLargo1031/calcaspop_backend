from fastapi import APIRouter, HTTPException

from ..schemas import DerivadoCreate, DerivadoOut, DerivadoUpdate
from .. import services

router = APIRouter(prefix="/api/derivados", tags=["derivados"])


@router.get("", response_model=list[DerivadoOut])
def listar():
    return services.listar_derivados()


@router.get("/{derivado_id}", response_model=DerivadoOut)
def obtener(derivado_id: int):
    d = services.obtener_derivado(derivado_id)
    if not d:
        raise HTTPException(404, "Derivado no encontrado.")
    return d


@router.post("", response_model=DerivadoOut)
def crear(data: DerivadoCreate):
    return services.guardar_derivado(
        derivado_id=None,
        nombre=data.nombre,
        componentes=[c.model_dump() for c in data.componentes],
    )


@router.put("/{derivado_id}", response_model=DerivadoOut)
def actualizar(derivado_id: int, data: DerivadoUpdate):
    return services.guardar_derivado(
        derivado_id=derivado_id,
        nombre=data.nombre,
        componentes=[c.model_dump() for c in data.componentes],
    )


@router.delete("/{derivado_id}")
def borrar(derivado_id: int):
    services.eliminar_derivado(derivado_id)
    return {"ok": True}
