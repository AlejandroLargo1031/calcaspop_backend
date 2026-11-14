"""Fórmulas equivalentes a ModCalculos.bas."""

from __future__ import annotations


def try_numero(texto: str | None) -> float | None:
    if texto is None:
        return 0.0
    t = str(texto).strip().replace(" ", "").replace("\xa0", "").replace("$", "").replace("%", "")
    if not t:
        return 0.0
    signo = 1.0
    if t[0] == "-":
        signo = -1.0
        t = t[1:]
    elif t[0] == "+":
        t = t[1:]
    if not t:
        return None
    canon = _canon_numero(t)
    if canon is None:
        return None
    try:
        return signo * float(canon)
    except ValueError:
        return None


def valor_unidad(precio: float, cantidad_unidades: float) -> float:
    if cantidad_unidades == 0:
        raise ValueError("La cantidad de unidades debe ser mayor que cero.")
    return precio / cantidad_unidades


def subtotal_linea(valor_de_unidad: float, cantidad: float) -> float:
    return valor_de_unidad * cantidad


def ganancia_neta(subtotal_productos: float, porcentaje: float) -> float:
    return subtotal_productos * porcentaje / 100.0


def precio_total(
    subtotal_productos: float,
    ganancia: float,
    mano_de_obra: float,
    gastos_operativos: float,
) -> float:
    return subtotal_productos + ganancia + mano_de_obra + gastos_operativos


def texto_moneda(valor: float) -> str:
    return f"{valor:,.2f}"


def texto_editable(valor: float) -> str:
    if valor == int(valor):
        return str(int(valor))
    return f"{valor:.2f}".rstrip("0").rstrip(".")


def _canon_numero(t: str) -> str | None:
    coma = t.rfind(",")
    punto = t.rfind(".")
    if coma > 0 and punto > 0:
        if coma > punto:
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif coma > 0:
        t = _un_separador(t, ",")
    elif punto > 0:
        t = _un_separador(t, ".")
    return t if _es_canon(t) else None


def _un_separador(t: str, sep: str) -> str:
    if t.count(sep) > 1:
        return t.replace(sep, "")
    partes = t.split(sep)
    if len(partes) == 2:
        izquierda, derecha = partes
        if (
            len(derecha) == 3
            and izquierda
            and izquierda != "0"
            and izquierda.isdigit()
            and derecha.isdigit()
        ):
            return izquierda + derecha
    return t.replace(",", ".") if sep == "," else t


def _es_canon(t: str) -> bool:
    if not t:
        return False
    visto_punto = False
    for i, c in enumerate(t):
        if c == ".":
            if visto_punto or i == len(t) - 1:
                return False
            visto_punto = True
        elif not c.isdigit():
            return False
    return True
