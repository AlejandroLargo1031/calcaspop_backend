from fastapi import APIRouter, HTTPException

from ..schemas import PreviewIn, PreviewOut, UtilidadesOut, VentaCreate, VentaOut
from .. import services

router = APIRouter(prefix="/api", tags=["ventas"])


@router.get("/ventas", response_model=list[VentaOut])
def listar(anio: int, mes: int, dia: int):
    return services.listar_ventas(anio, mes, dia)


@router.get("/ventas/{venta_id}", response_model=VentaOut)
def obtener(venta_id: int):
    v = services.obtener_venta(venta_id)
    if not v:
        raise HTTPException(404, "Venta no encontrada.")
    return v


@router.post("/ventas", response_model=VentaOut)
def crear(data: VentaCreate):
    return services.guardar_venta(data)


@router.put("/ventas/{venta_id}", response_model=VentaOut)
def actualizar(venta_id: int, data: VentaCreate):
    return services.actualizar_venta(venta_id, data)


@router.delete("/ventas/{venta_id}")
def borrar(venta_id: int):
    services.eliminar_venta(venta_id)
    return {"ok": True}


@router.get("/utilidades", response_model=UtilidadesOut)
def utilidades(anio: int, mes: int, dia: int):
    return services.utilidades(anio, mes, dia)


@router.post("/calculos/preview", response_model=PreviewOut)
def preview(data: PreviewIn):
    return services.preview_totales(data)


@router.get("/calendario/dias")
def dias(anio: int, mes: int):
    return {"dias": services.dias_del_mes(anio, mes)}
