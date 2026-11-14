from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ProductoBase(BaseModel):
    nombre: str
    precio: float = Field(gt=0)
    cantidad_unidades: float = Field(gt=0)


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(ProductoBase):
    pass


class ProductoOut(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad_unidades: float
    valor_unidad: float

    model_config = {"from_attributes": True}


class ComponenteIn(BaseModel):
    producto_id: int
    cantidad: float = 1.0


class ComponenteOut(BaseModel):
    producto_id: int
    nombre: str
    cantidad: float

    model_config = {"from_attributes": True}


class DerivadoCreate(BaseModel):
    nombre: str
    componentes: list[ComponenteIn] = Field(min_length=1)


class DerivadoUpdate(DerivadoCreate):
    pass


class DerivadoOut(BaseModel):
    id: int
    nombre: str
    componentes: list[ComponenteOut] = []
    productos_texto: str = ""

    model_config = {"from_attributes": True}


class LineaVentaIn(BaseModel):
    producto_id: int
    cantidad: float = Field(gt=0)


class VentaCreate(BaseModel):
    anio: int = Field(ge=2000)
    mes: int = Field(ge=1, le=12)
    dia: int = Field(ge=1, le=31)
    mano_de_obra: float = Field(ge=0)
    gastos_operativos: float = Field(ge=0)
    porcentaje: float = Field(ge=0)
    cliente: str
    origen: str = "Individual"
    metodo_pago: str
    lineas: list[LineaVentaIn] = Field(min_length=1)

    @field_validator("cliente")
    @classmethod
    def cliente_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Escribe el nombre del cliente.")
        return v

    @field_validator("metodo_pago")
    @classmethod
    def metodo_valido(cls, v: str) -> str:
        t = v.strip().lower()
        if t == "transferencia":
            return "Transferencia"
        if t == "efectivo":
            return "Efectivo"
        raise ValueError("Elige el método de pago: transferencia o efectivo.")

    @field_validator("origen")
    @classmethod
    def origen_default(cls, v: str) -> str:
        v = v.strip()
        return v or "Individual"


class DetalleVentaOut(BaseModel):
    producto_id: int
    nombre: str
    valor_unidad: float
    cantidad: float
    subtotal: float

    model_config = {"from_attributes": True}


class VentaOut(BaseModel):
    id: int
    anio: int
    mes: int
    dia: int
    mano_de_obra: float
    gastos_operativos: float
    porcentaje: float
    subtotal_productos: float
    ganancia_neta: float
    precio_total: float
    cliente: str
    origen: str
    metodo_pago: str
    resumen: str = ""
    detalles: list[DetalleVentaOut] = []

    model_config = {"from_attributes": True}


class UtilidadFila(BaseModel):
    id: int
    cliente: str
    origen: str
    referencia: str
    mano_de_obra: float
    ganancia_total: float
    precio_insumos: float


class UtilidadesOut(BaseModel):
    filas: list[UtilidadFila]
    total_insumos: float
    total_ganancia: float


class PreviewIn(BaseModel):
    lineas: list[LineaVentaIn] = []
    porcentaje: float = 0
    mano_de_obra: float = 0
    gastos_operativos: float = 0


class PreviewOut(BaseModel):
    subtotal_productos: float
    ganancia_neta: float
    precio_total: float


class ConfigOut(BaseModel):
    color_fondo: str = "#2d1b4e"
    porcentaje_ganancia: float = 0
    imagen_url: str | None = None
    paleta_colores: list[str] = []


class ConfigUpdate(BaseModel):
    color_fondo: str | None = None
    porcentaje_ganancia: float | None = None
    paleta_colores: list[str] | None = None


class PorcentajeUpdate(BaseModel):
    porcentaje: float = Field(ge=0)
