"""
Cliente para obtener datos de inventario desde Google Sheets.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import gspread
from google.oauth2.service_account import Credentials

from app.core.config import settings as default_settings
from .schema import Medicamento, Inventario

logger = logging.getLogger(__name__)


class InventoryClient:
    def __init__(
        self,
        settings = None,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None,
    ):
        self.settings = settings or default_settings
        self.credentials_path = credentials_path or self.settings.GOOGLE_APPLICATION_CREDENTIALS
        self.spreadsheet_id = spreadsheet_id or self.settings.SPREADSHEET_ID
        self.sheet_name = sheet_name

        if not self.credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS no está definido.")
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID no está definido.")

        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None

    def _get_client(self) -> gspread.Client:
        if self._client is None:
            scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            client = self._get_client()
            self._spreadsheet = client.open_by_key(self.spreadsheet_id)
        return self._spreadsheet

    def fetch_medicamentos(self) -> List[Medicamento]:
        """
        Obtiene los registros de la hoja y los convierte en objetos Medicamento.
        Normaliza los encabezados (recorta espacios) y maneja duplicados.
        """
        spreadsheet = self._get_spreadsheet()
        if self.sheet_name:
            worksheet = spreadsheet.worksheet(self.sheet_name)
        else:
            worksheet = spreadsheet.get_worksheet(0)

        rows = worksheet.get_all_values()
        if not rows:
            logger.warning("La hoja de inventario está vacía.")
            return []

        raw_headers = rows[0]
        clean_headers = []
        seen = {}
        for h in raw_headers:
            h = h.strip()  # ← Elimina espacios al inicio/final
            if h == "":
                # Para columnas sin encabezado, usar placeholder único
                h = f"col_{len(clean_headers)}"
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 1
            clean_headers.append(h)

        data_rows = rows[1:]
        medicamentos: List[Medicamento] = []
        errors = 0

        for idx, row in enumerate(data_rows, start=2):
            if all(cell == "" for cell in row):
                continue
            record = {}
            for col_idx, header in enumerate(clean_headers):
                value = row[col_idx] if col_idx < len(row) else ""
                record[header] = value
            try:
                medicamento = Medicamento(**record)
                medicamentos.append(medicamento)
            except Exception as e:
                errors += 1
                logger.error(f"Error al procesar fila {idx}: {e}")
                continue

        if errors:
            logger.warning(f"Se omitieron {errors} filas con errores de parseo.")
        return medicamentos

    def fetch_inventory(self) -> Inventario:
        medicamentos = self.fetch_medicamentos()
        now = datetime.now().isoformat()
        return Inventario(
            medicamentos=medicamentos,
            ultima_actualizacion=now,
        )

    def fetch_raw_values(self) -> List[List[str]]:
        """Obtiene todas las filas como listas de strings (incluye encabezados)."""
        spreadsheet = self._get_spreadsheet()
        if self.sheet_name:
            worksheet = spreadsheet.worksheet(self.sheet_name)
        else:
            worksheet = spreadsheet.get_worksheet(0)
        return worksheet.get_all_values()

    # fetch_as_dict se mantiene por compatibilidad, pero usa la misma lógica
    def fetch_as_dict(self) -> List[Dict[str, Any]]:
        """Devuelve los datos como lista de diccionarios (con encabezados normalizados)."""
        rows = self.fetch_raw_values()
        if not rows:
            return []
        headers = [h.strip() for h in rows[0]]
        # Manejar duplicados
        seen = {}
        for i, h in enumerate(headers):
            if h == "":
                h = f"col_{i}"
            if h in seen:
                seen[h] += 1
                headers[i] = f"{h}_{seen[h]}"
            else:
                seen[h] = 1
        data = []
        for row in rows[1:]:
            if all(cell == "" for cell in row):
                continue
            record = {}
            for i, header in enumerate(headers):
                record[header] = row[i] if i < len(row) else ""
            data.append(record)
        return data
