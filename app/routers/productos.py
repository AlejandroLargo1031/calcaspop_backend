from fastapi import APIRouter, HTTPException

from ..schemas import ProductoCreate, ProductoOut, ProductoUpdate
from .. import services

router = APIRouter(prefix="/api/productos", tags=["productos"])


@router.get("", response_model=list[ProductoOut])
def listar():
    return services.listar_productos()


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener(producto_id: int):
    p = services.obtener_producto(producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado.")
    return p


@router.post("", response_model=ProductoOut)
def crear(data: ProductoCreate):
    return services.guardar_producto(
        producto_id=None,
        nombre=data.nombre,
        precio=data.precio,
        cantidad=data.cantidad_unidades,
    )


@router.put("/{producto_id}", response_model=ProductoOut)
def actualizar(producto_id: int, data: ProductoUpdate):
    return services.guardar_producto(
        producto_id=producto_id,
        nombre=data.nombre,
        precio=data.precio,
        cantidad=data.cantidad_unidades,
    )


@router.delete("/{producto_id}")
def borrar(producto_id: int):
    services.eliminar_producto(producto_id)
    return {"ok": True}
