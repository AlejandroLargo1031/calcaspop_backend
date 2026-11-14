"""Cliente Google Sheets: reemplaza SQLite como almacenamiento."""

from __future__ import annotations

import json
import os
import threading
from functools import lru_cache
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = {
    "Productos": ["ID", "Nombre", "Precio", "CantidadUnidades", "ValorUnidad"],
    "Derivados": ["ID", "Nombre"],
    "ComposicionDerivados": ["IDDerivado", "IDProducto", "Nombre", "Cantidad"],
    "Ventas": [
        "ID",
        "Anio",
        "Mes",
        "ManoDeObra",
        "GastosOperativos",
        "Porcentaje",
        "SubtotalProductos",
        "GananciaNeta",
        "PrecioTotal",
        "Dia",
        "Cliente",
        "Origen",
        "MetodoPago",
    ],
    "DetalleVentas": [
        "IDVenta",
        "IDProducto",
        "Nombre",
        "ValorUnidad",
        "Cantidad",
        "Subtotal",
    ],
    "Config": ["Clave", "Valor"],
}

_lock = threading.Lock()


class SheetsNotConfigured(RuntimeError):
    pass


def _credentials_dict() -> dict:
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw:
        if raw.startswith("{"):
            return json.loads(raw)
        path = Path(raw)
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    file_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if file_env and Path(file_env).is_file():
        return json.loads(Path(file_env).read_text(encoding="utf-8"))
    local = Path(__file__).resolve().parent.parent / "credentials.json"
    if local.is_file():
        return json.loads(local.read_text(encoding="utf-8"))
    raise SheetsNotConfigured(
        "Faltan credenciales de Google. Define GOOGLE_SERVICE_ACCOUNT_JSON "
        "o coloca credentials.json en web/backend/."
    )


def spreadsheet_id() -> str:
    sid = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    if not sid:
        raise SheetsNotConfigured("Falta GOOGLE_SHEETS_ID (ID de la hoja de cálculo).")
    return sid


@lru_cache(maxsize=1)
def _client() -> gspread.Client:
    creds = Credentials.from_service_account_info(_credentials_dict(), scopes=SCOPES)
    return gspread.authorize(creds)


def open_book():
    return _client().open_by_key(spreadsheet_id())


def ensure_workbook() -> None:
    """Crea pestañas y encabezados si no existen. Rellena Config por defecto."""
    with _lock:
        book = open_book()
        existentes = {ws.title: ws for ws in book.worksheets()}
        for nombre, headers in HEADERS.items():
            if nombre not in existentes:
                ws = book.add_worksheet(title=nombre, rows=1000, cols=max(len(headers), 8))
                ws.update(range_name="A1", values=[headers])
            else:
                ws = existentes[nombre]
                actual = ws.row_values(1)
                if actual != headers:
                    # Solo escribe encabezados si la fila 1 está vacía
                    if not any(actual):
                        ws.update(range_name="A1", values=[headers])
        cfg = book.worksheet("Config")
        filas = cfg.get_all_records()
        claves = {str(r.get("Clave", "")).strip() for r in filas}
        defaults = {
            "ColorFondo": "#2d1b4e",
            "PorcentajeGanancia": "0",
            "RutaImagen": "",
            "PaletaColores": (
                '["#2d1b4e","#1b2a4e","#14352e","#4a1d2e","#3a2a12","#10233a",'
                '"#5a1f3d","#243015","#2a1640","#16333a","#402010","#1a1a2e"]'
            ),
        }
        for clave, valor in defaults.items():
            if clave not in claves:
                cfg.append_row([clave, valor], value_input_option="USER_ENTERED")


def worksheet(nombre: str):
    return open_book().worksheet(nombre)


def all_records(nombre: str) -> list[dict]:
    with _lock:
        return worksheet(nombre).get_all_records()


def next_id(nombre: str, campo: str = "ID") -> int:
    rows = all_records(nombre)
    max_id = 0
    for r in rows:
        try:
            max_id = max(max_id, int(r.get(campo) or 0))
        except (TypeError, ValueError):
            continue
    return max_id + 1


def append_row(nombre: str, values: list) -> None:
    with _lock:
        worksheet(nombre).append_row(values, value_input_option="USER_ENTERED")


def find_row_number(nombre: str, campo: str, valor) -> int | None:
    """Fila 1-indexada en la hoja (2 = primer dato)."""
    rows = all_records(nombre)
    for i, r in enumerate(rows):
        if str(r.get(campo, "")).strip() == str(valor).strip():
            return i + 2
    return None


def update_row(nombre: str, row_number: int, values: list) -> None:
    with _lock:
        ws = worksheet(nombre)
        end_col = chr(ord("A") + len(values) - 1)
        ws.update(
            range_name=f"A{row_number}:{end_col}{row_number}",
            values=[values],
            value_input_option="USER_ENTERED",
        )


def delete_row(nombre: str, row_number: int) -> None:
    with _lock:
        worksheet(nombre).delete_rows(row_number)


def delete_rows_where(nombre: str, campo: str, valor) -> int:
    """Borra de abajo hacia arriba. Devuelve cuántas filas borró."""
    with _lock:
        ws = worksheet(nombre)
        rows = ws.get_all_records()
        borradas = 0
        for i in range(len(rows) - 1, -1, -1):
            if str(rows[i].get(campo, "")).strip() == str(valor).strip():
                ws.delete_rows(i + 2)
                borradas += 1
        return borradas


def num(valor, default: float = 0.0) -> float:
    if valor is None or valor == "":
        return default
    if isinstance(valor, (int, float)):
        return float(valor)
    t = str(valor).strip().replace(" ", "").replace("$", "")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return default


def clear_client_cache() -> None:
    _client.cache_clear()
