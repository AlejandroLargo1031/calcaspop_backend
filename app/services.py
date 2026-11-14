from __future__ import annotations

from calendar import monthrange

from fastapi import HTTPException

from . import calculos
from . import sheets


def dias_del_mes(anio: int, mes: int) -> int:
    return monthrange(anio, mes)[1]


def ensure_defaults() -> None:
    sheets.ensure_workbook()


PALETA_DEFAULT = [
    "#2d1b4e",
    "#1b2a4e",
    "#14352e",
    "#4a1d2e",
    "#3a2a12",
    "#10233a",
    "#5a1f3d",
    "#243015",
    "#2a1640",
    "#16333a",
    "#402010",
    "#1a1a2e",
]


def get_config_map() -> dict[str, str]:
    filas = sheets.all_records("Config")
    return {
        str(r.get("Clave", "")).strip(): str(r.get("Valor", "") if r.get("Valor") is not None else "")
        for r in filas
        if str(r.get("Clave", "")).strip()
    }


def get_paleta() -> list[str]:
    import json

    raw = get_config_map().get("PaletaColores", "")
    if not raw:
        return list(PALETA_DEFAULT)
    try:
        data = json.loads(raw)
        if isinstance(data, list) and data:
            return [str(c) for c in data if str(c).startswith("#")]
    except json.JSONDecodeError:
        pass
    return list(PALETA_DEFAULT)


def set_paleta(colores: list[str]) -> list[str]:
    import json

    limpios = []
    for c in colores:
        h = str(c).strip()
        if not h.startswith("#"):
            continue
        if len(h) in (4, 7):
            limpios.append(h.lower() if len(h) == 7 else h)
    if not limpios:
        limpios = list(PALETA_DEFAULT)
    set_config("PaletaColores", json.dumps(limpios))
    return limpios


def set_config(clave: str, valor: str) -> None:
    row = sheets.find_row_number("Config", "Clave", clave)
    if row is None:
        sheets.append_row("Config", [clave, valor])
    else:
        sheets.update_row("Config", row, [clave, valor])


def listar_productos() -> list[dict]:
    out = []
    for r in sheets.all_records("Productos"):
        try:
            pid = int(r.get("ID") or 0)
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        out.append(
            {
                "id": pid,
                "nombre": str(r.get("Nombre", "")),
                "precio": sheets.num(r.get("Precio")),
                "cantidad_unidades": sheets.num(r.get("CantidadUnidades")),
                "valor_unidad": sheets.num(r.get("ValorUnidad")),
            }
        )
    out.sort(key=lambda x: x["id"], reverse=True)
    return out


def obtener_producto(producto_id: int) -> dict | None:
    for p in listar_productos():
        if p["id"] == producto_id:
            return p
    return None


def guardar_producto(
    *,
    producto_id: int | None,
    nombre: str,
    precio: float,
    cantidad: float,
) -> dict:
    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(400, "Escribe el nombre del producto.")
    if precio <= 0 or cantidad <= 0:
        raise HTTPException(400, "Precio y cantidad deben ser mayores que cero.")
    valor = calculos.valor_unidad(precio, cantidad)

    if producto_id:
        row = sheets.find_row_number("Productos", "ID", producto_id)
        if row is None:
            raise HTTPException(404, "Producto no encontrado.")
        sheets.update_row(
            "Productos",
            row,
            [producto_id, nombre, precio, cantidad, valor],
        )
        pid = producto_id
    else:
        pid = sheets.next_id("Productos")
        sheets.append_row("Productos", [pid, nombre, precio, cantidad, valor])

    return {
        "id": pid,
        "nombre": nombre,
        "precio": precio,
        "cantidad_unidades": cantidad,
        "valor_unidad": valor,
    }


def eliminar_producto(producto_id: int) -> None:
    if obtener_producto(producto_id) is None:
        raise HTTPException(404, "Producto no encontrado.")
    for c in sheets.all_records("ComposicionDerivados"):
        if int(sheets.num(c.get("IDProducto"))) == producto_id:
            raise HTTPException(400, "Ese producto está en un derivado. Quítalo primero.")
    row = sheets.find_row_number("Productos", "ID", producto_id)
    if row:
        sheets.delete_row("Productos", row)


def texto_composicion(componentes: list[dict]) -> str:
    return ", ".join(c["nombre"] for c in componentes)


def listar_derivados() -> list[dict]:
    comps = sheets.all_records("ComposicionDerivados")
    out = []
    for r in sheets.all_records("Derivados"):
        try:
            did = int(r.get("ID") or 0)
        except (TypeError, ValueError):
            continue
        if did <= 0:
            continue
        componentes = []
        for c in comps:
            if int(sheets.num(c.get("IDDerivado"))) == did:
                componentes.append(
                    {
                        "producto_id": int(sheets.num(c.get("IDProducto"))),
                        "nombre": str(c.get("Nombre", "")),
                        "cantidad": sheets.num(c.get("Cantidad"), 1.0),
                    }
                )
        out.append(
            {
                "id": did,
                "nombre": str(r.get("Nombre", "")),
                "componentes": componentes,
                "productos_texto": texto_composicion(componentes),
            }
        )
    out.sort(key=lambda x: x["id"], reverse=True)
    return out


def obtener_derivado(derivado_id: int) -> dict | None:
    for d in listar_derivados():
        if d["id"] == derivado_id:
            return d
    return None


def guardar_derivado(
    *,
    derivado_id: int | None,
    nombre: str,
    componentes: list[dict],
) -> dict:
    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(400, "Escribe el nombre del derivado.")
    if not componentes:
        raise HTTPException(400, "Agrega al menos un producto al derivado.")

    vistos: set[int] = set()
    armados: list[tuple[dict, float]] = []
    for item in componentes:
        pid = int(item["producto_id"])
        if pid in vistos:
            raise HTTPException(400, "Hay productos repetidos en el derivado.")
        vistos.add(pid)
        prod = obtener_producto(pid)
        if not prod:
            raise HTTPException(404, f"No encontré el producto {pid}.")
        armados.append((prod, 1.0))

    if derivado_id:
        row = sheets.find_row_number("Derivados", "ID", derivado_id)
        if row is None:
            raise HTTPException(404, "Derivado no encontrado.")
        sheets.update_row("Derivados", row, [derivado_id, nombre])
        sheets.delete_rows_where("ComposicionDerivados", "IDDerivado", derivado_id)
        did = derivado_id
    else:
        did = sheets.next_id("Derivados")
        sheets.append_row("Derivados", [did, nombre])

    for prod, cant in armados:
        sheets.append_row(
            "ComposicionDerivados",
            [did, prod["id"], prod["nombre"], cant],
        )
    d = obtener_derivado(did)
    if not d:
        raise HTTPException(500, "No pude leer el derivado guardado.")
    return d


def eliminar_derivado(derivado_id: int) -> None:
    if obtener_derivado(derivado_id) is None:
        raise HTTPException(404, "Derivado no encontrado.")
    sheets.delete_rows_where("ComposicionDerivados", "IDDerivado", derivado_id)
    row = sheets.find_row_number("Derivados", "ID", derivado_id)
    if row:
        sheets.delete_row("Derivados", row)


def _agrupar_lineas(lineas: list[dict]) -> dict[int, float]:
    agrupado: dict[int, float] = {}
    for linea in lineas:
        pid = int(linea["producto_id"])
        cant = float(linea["cantidad"])
        if cant <= 0:
            raise HTTPException(400, "La cantidad debe ser mayor que cero.")
        agrupado[pid] = agrupado.get(pid, 0.0) + cant
    return agrupado


def validar_stock(lineas: list[dict]) -> dict[int, dict]:
    agrupado = _agrupar_lineas(lineas)
    productos: dict[int, dict] = {}
    for pid, cant in agrupado.items():
        prod = obtener_producto(pid)
        if not prod:
            raise HTTPException(404, f"No encontré el producto {pid}.")
        if cant > prod["cantidad_unidades"] + 1e-7:
            raise HTTPException(
                400,
                f"No hay suficientes unidades de {prod['nombre']}. "
                f"Disponibles: {calculos.texto_editable(prod['cantidad_unidades'])}.",
            )
        productos[pid] = prod
    return productos


def mover_inventario(prod: dict, cantidad: float, valor_u: float, *, devolver: bool) -> dict:
    if devolver:
        nueva_cant = prod["cantidad_unidades"] + cantidad
        nuevo_precio = prod["precio"] + (valor_u * cantidad)
    else:
        nueva_cant = prod["cantidad_unidades"] - cantidad
        nuevo_precio = prod["precio"] - (valor_u * cantidad)
        if abs(nueva_cant) < 1e-9:
            nueva_cant = 0.0
            nuevo_precio = 0.0
        if nuevo_precio < 0:
            nuevo_precio = 0.0
    if nueva_cant <= 0:
        actualizado = {
            **prod,
            "cantidad_unidades": 0.0,
            "precio": 0.0,
            "valor_unidad": 0.0,
        }
    else:
        actualizado = {
            **prod,
            "cantidad_unidades": nueva_cant,
            "precio": nuevo_precio,
            "valor_unidad": nuevo_precio / nueva_cant,
        }
    row = sheets.find_row_number("Productos", "ID", prod["id"])
    if row:
        sheets.update_row(
            "Productos",
            row,
            [
                actualizado["id"],
                actualizado["nombre"],
                actualizado["precio"],
                actualizado["cantidad_unidades"],
                actualizado["valor_unidad"],
            ],
        )
    return actualizado


def resumen_venta(detalles: list[dict]) -> str:
    partes = [
        f"{d['nombre']} x {calculos.texto_editable(d['cantidad'])}" for d in detalles
    ]
    texto = ", ".join(partes) if partes else "Venta"
    return texto if len(texto) <= 140 else texto[:137] + "..."


def _detalles_de_venta(venta_id: int) -> list[dict]:
    out = []
    for d in sheets.all_records("DetalleVentas"):
        if int(sheets.num(d.get("IDVenta"))) == venta_id:
            out.append(
                {
                    "producto_id": int(sheets.num(d.get("IDProducto"))),
                    "nombre": str(d.get("Nombre", "")),
                    "valor_unidad": sheets.num(d.get("ValorUnidad")),
                    "cantidad": sheets.num(d.get("Cantidad")),
                    "subtotal": sheets.num(d.get("Subtotal")),
                }
            )
    return out


def _venta_dict(r: dict) -> dict:
    vid = int(sheets.num(r.get("ID")))
    detalles = _detalles_de_venta(vid)
    return {
        "id": vid,
        "anio": int(sheets.num(r.get("Anio"))),
        "mes": int(sheets.num(r.get("Mes"))),
        "dia": int(sheets.num(r.get("Dia"))),
        "mano_de_obra": sheets.num(r.get("ManoDeObra")),
        "gastos_operativos": sheets.num(r.get("GastosOperativos")),
        "porcentaje": sheets.num(r.get("Porcentaje")),
        "subtotal_productos": sheets.num(r.get("SubtotalProductos")),
        "ganancia_neta": sheets.num(r.get("GananciaNeta")),
        "precio_total": sheets.num(r.get("PrecioTotal")),
        "cliente": str(r.get("Cliente", "")),
        "origen": str(r.get("Origen", "") or "Individual"),
        "metodo_pago": str(r.get("MetodoPago", "")),
        "resumen": resumen_venta(detalles),
        "detalles": detalles,
    }


def listar_ventas(anio: int, mes: int, dia: int) -> list[dict]:
    out = []
    for r in sheets.all_records("Ventas"):
        try:
            if (
                int(sheets.num(r.get("Anio"))) == anio
                and int(sheets.num(r.get("Mes"))) == mes
                and int(sheets.num(r.get("Dia"))) == dia
            ):
                out.append(_venta_dict(r))
        except (TypeError, ValueError):
            continue
    out.sort(key=lambda x: x["id"], reverse=True)
    return out


def obtener_venta(venta_id: int) -> dict | None:
    for r in sheets.all_records("Ventas"):
        if int(sheets.num(r.get("ID"))) == venta_id:
            return _venta_dict(r)
    return None


def guardar_venta(data) -> dict:
    if data.dia < 1 or data.dia > dias_del_mes(data.anio, data.mes):
        raise HTTPException(400, "Elige un día válido para ese mes.")

    lineas = [{"producto_id": l.producto_id, "cantidad": l.cantidad} for l in data.lineas]
    productos = validar_stock(lineas)

    subtotal = 0.0
    detalle_armado: list[tuple[dict, float, float, float]] = []
    for linea in data.lineas:
        prod = productos[linea.producto_id]
        valor_u = prod["valor_unidad"]
        sub = calculos.subtotal_linea(valor_u, linea.cantidad)
        subtotal += sub
        detalle_armado.append((prod, valor_u, linea.cantidad, sub))

    ganancia = calculos.ganancia_neta(subtotal, data.porcentaje)
    total = calculos.precio_total(
        subtotal, ganancia, data.mano_de_obra, data.gastos_operativos
    )

    vid = sheets.next_id("Ventas")
    sheets.append_row(
        "Ventas",
        [
            vid,
            data.anio,
            data.mes,
            data.mano_de_obra,
            data.gastos_operativos,
            data.porcentaje,
            subtotal,
            ganancia,
            total,
            data.dia,
            data.cliente,
            data.origen,
            data.metodo_pago,
        ],
    )

    for prod, valor_u, cant, sub in detalle_armado:
        sheets.append_row(
            "DetalleVentas",
            [vid, prod["id"], prod["nombre"], valor_u, cant, sub],
        )
        mover_inventario(prod, cant, valor_u, devolver=False)

    set_config("PorcentajeGanancia", str(data.porcentaje))
    venta = obtener_venta(vid)
    if not venta:
        raise HTTPException(500, "No pude leer la venta guardada.")
    return venta


def eliminar_venta(venta_id: int) -> None:
    venta = obtener_venta(venta_id)
    if not venta:
        raise HTTPException(404, "Venta no encontrada.")
    for d in venta["detalles"]:
        prod = obtener_producto(d["producto_id"])
        if prod:
            mover_inventario(prod, d["cantidad"], d["valor_unidad"], devolver=True)
    sheets.delete_rows_where("DetalleVentas", "IDVenta", venta_id)
    row = sheets.find_row_number("Ventas", "ID", venta_id)
    if row:
        sheets.delete_row("Ventas", row)


def actualizar_venta(venta_id: int, data) -> dict:
    """Devuelve stock de la venta anterior, aplica la nueva y recalcula totales."""
    venta = obtener_venta(venta_id)
    if not venta:
        raise HTTPException(404, "Venta no encontrada.")
    if data.dia < 1 or data.dia > dias_del_mes(data.anio, data.mes):
        raise HTTPException(400, "Elige un día válido para ese mes.")

    # Devolver inventario de la venta original antes de validar la nueva
    for d in venta["detalles"]:
        prod = obtener_producto(d["producto_id"])
        if prod:
            mover_inventario(prod, d["cantidad"], d["valor_unidad"], devolver=True)

    try:
        lineas = [{"producto_id": l.producto_id, "cantidad": l.cantidad} for l in data.lineas]
        productos = validar_stock(lineas)
    except Exception:
        for d in venta["detalles"]:
            prod = obtener_producto(d["producto_id"])
            if prod:
                mover_inventario(prod, d["cantidad"], d["valor_unidad"], devolver=False)
        raise

    subtotal = 0.0
    detalle_armado: list[tuple[dict, float, float, float]] = []
    for linea in data.lineas:
        prod = productos[linea.producto_id]
        valor_u = prod["valor_unidad"]
        sub = calculos.subtotal_linea(valor_u, linea.cantidad)
        subtotal += sub
        detalle_armado.append((prod, valor_u, linea.cantidad, sub))

    ganancia = calculos.ganancia_neta(subtotal, data.porcentaje)
    total = calculos.precio_total(
        subtotal, ganancia, data.mano_de_obra, data.gastos_operativos
    )

    row = sheets.find_row_number("Ventas", "ID", venta_id)
    if row is None:
        for d in venta["detalles"]:
            prod = obtener_producto(d["producto_id"])
            if prod:
                mover_inventario(prod, d["cantidad"], d["valor_unidad"], devolver=False)
        raise HTTPException(404, "Venta no encontrada.")

    sheets.update_row(
        "Ventas",
        row,
        [
            venta_id,
            data.anio,
            data.mes,
            data.mano_de_obra,
            data.gastos_operativos,
            data.porcentaje,
            subtotal,
            ganancia,
            total,
            data.dia,
            data.cliente,
            data.origen,
            data.metodo_pago,
        ],
    )
    sheets.delete_rows_where("DetalleVentas", "IDVenta", venta_id)
    for prod, valor_u, cant, sub in detalle_armado:
        sheets.append_row(
            "DetalleVentas",
            [venta_id, prod["id"], prod["nombre"], valor_u, cant, sub],
        )
        mover_inventario(prod, cant, valor_u, devolver=False)

    set_config("PorcentajeGanancia", str(data.porcentaje))
    actualizada = obtener_venta(venta_id)
    if not actualizada:
        raise HTTPException(500, "No pude leer la venta actualizada.")
    return actualizada


def utilidades(anio: int, mes: int, dia: int) -> dict:
    ventas = listar_ventas(anio, mes, dia)
    filas = []
    total_insumos = 0.0
    total_ganancia = 0.0
    for v in ventas:
        ganancia_total = v["ganancia_neta"] + v["mano_de_obra"]
        filas.append(
            {
                "id": v["id"],
                "cliente": v["cliente"],
                "origen": v["origen"],
                "referencia": v["resumen"],
                "mano_de_obra": v["mano_de_obra"],
                "ganancia_total": ganancia_total,
                "precio_insumos": v["subtotal_productos"],
            }
        )
        total_insumos += v["subtotal_productos"]
        total_ganancia += ganancia_total
    return {
        "filas": filas,
        "total_insumos": total_insumos,
        "total_ganancia": total_ganancia,
    }


def preview_totales(data) -> dict[str, float]:
    subtotal = 0.0
    for linea in data.lineas:
        prod = obtener_producto(linea.producto_id)
        if not prod:
            raise HTTPException(404, f"No encontré el producto {linea.producto_id}.")
        subtotal += calculos.subtotal_linea(prod["valor_unidad"], linea.cantidad)
    ganancia = calculos.ganancia_neta(subtotal, data.porcentaje)
    total = calculos.precio_total(
        subtotal, ganancia, data.mano_de_obra, data.gastos_operativos
    )
    return {
        "subtotal_productos": subtotal,
        "ganancia_neta": ganancia,
        "precio_total": total,
    }
