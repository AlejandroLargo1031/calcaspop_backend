from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cantidad_unidades: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    valor_unidad: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class Derivado(Base):
    __tablename__ = "derivados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    componentes: Mapped[list[ComposicionDerivado]] = relationship(
        "ComposicionDerivado",
        back_populates="derivado",
        cascade="all, delete-orphan",
    )


class ComposicionDerivado(Base):
    __tablename__ = "composicion_derivados"
    __table_args__ = (UniqueConstraint("derivado_id", "producto_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    derivado_id: Mapped[int] = mapped_column(ForeignKey("derivados.id", ondelete="CASCADE"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    derivado: Mapped[Derivado] = relationship("Derivado", back_populates="componentes")


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    dia: Mapped[int] = mapped_column(Integer, nullable=False)
    mano_de_obra: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gastos_operativos: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    porcentaje: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    subtotal_productos: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ganancia_neta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    precio_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cliente: Mapped[str] = mapped_column(String(200), nullable=False)
    origen: Mapped[str] = mapped_column(String(300), nullable=False, default="Individual")
    metodo_pago: Mapped[str] = mapped_column(String(40), nullable=False)

    detalles: Mapped[list[DetalleVenta]] = relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
    )


class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"))
    producto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    valor_unidad: Mapped[float] = mapped_column(Float, nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    venta: Mapped[Venta] = relationship("Venta", back_populates="detalles")


class Config(Base):
    __tablename__ = "config"

    clave: Mapped[str] = mapped_column(String(80), primary_key=True)
    valor: Mapped[str] = mapped_column(String(500), nullable=False, default="")
