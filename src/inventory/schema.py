"""
Modelos de datos para el inventario de la farmacia.

Define la estructura de un medicamento y del inventario completo,
basado en el archivo CSV de ejemplo proporcionado.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Medicamento(BaseModel):
    """
    Representa un medicamento o producto del inventario.
    """
    codigo: str = Field(..., alias="CÓDIGO", description="Código de barras o identificador")
    lote: Optional[str] = Field(None, alias="LOTE", description="Número de lote")
    caducidad: Optional[str] = Field(None, alias="CAD", description="Fecha de caducidad (mes/año)")
    producto: str = Field(..., alias="PRODUCTO", description="Nombre completo del producto")
    tipo_venta: str = Field(..., alias="QUE ES", description="Tipo de venta (LIBRE VENTA, RECETA, etc.)")
    marca: str = Field(..., alias="MARCA", description="Marca comercial")
    stock: int = Field(..., alias="STOCK", description="Cantidad disponible en inventario")
    stock_real: int = Field(..., alias="STOCK REAL", description="Cantidad real en almacén")
    precio_compra: float = Field(..., alias="PRECIO COMPRA", description="Precio de compra por unidad")
    precio_publico: float = Field(..., alias="PRECIO PÚBLICO", description="Precio de venta al público")
    precio_didi: Optional[float] = Field(None, alias="PRECIO DIDI", description="Precio para plataformas (opcional)")
    costo_real_por_vender: Optional[float] = Field(None, alias="COSTO REAL POR VENDER", description="Costo real por vender")
    vendidos_piezas: int = Field(0, alias="VENDIDOS PIEZAS", description="Unidades vendidas")
    agotado: Optional[str] = Field(None, alias="¿ESTÁ AGOTADO?", description="Indicador de agotado ('AGOTADO')")
    categoria: Optional[str] = Field(None, alias="CATEGORIA", description="Categoría del producto")
    resurtir: Optional[str] = Field(None, alias="RESURTIR", description="Indicador de resurtir ('RESURTIR' o 'NO RESURTIR')")

    # Configuración Pydantic V2
    model_config = ConfigDict(
        populate_by_name=True,   # permite usar 'codigo' en lugar de 'CÓDIGO'
        extra='ignore',
    )

    # Validadores
    @field_validator('precio_compra', 'precio_publico', 'precio_didi', 'costo_real_por_vender', mode='before')
    def parse_float(cls, v):
        if v is None or v == '':
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        cleaned = ''.join(c for c in str(v) if c.isdigit() or c == '.')
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    @field_validator('stock', 'stock_real', 'vendidos_piezas', mode='before')
    def parse_int(cls, v):
        if v is None or v == '':
            return 0
        if isinstance(v, int):
            return v
        cleaned = ''.join(c for c in str(v) if c.isdigit())
        return int(cleaned) if cleaned else 0

    @field_validator('agotado', mode='before')
    def normalize_agotado(cls, v):
        """Convierte cadena vacía a None."""
        if v == "":
            return None
        return v
    # Dentro de la clase Medicamento, agregar:

    @field_validator('codigo', 'lote', mode='before')
    def parse_to_str(cls, v):
        """Convierte a string (para códigos y lotes que vengan como int)."""
        if v is None:
            return None
        return str(v)


class Inventario(BaseModel):
    """
    Representa el inventario completo de la farmacia.

    Attributes:
        medicamentos: Lista de todos los medicamentos.
        ultima_actualizacion: Timestamp ISO de la última sincronización.
    """
    medicamentos: List[Medicamento] = Field(default_factory=list)
    ultima_actualizacion: Optional[str] = Field(None, description="Fecha/hora de última actualización en formato ISO")

    # Configuración Pydantic V2
    model_config = ConfigDict(extra='ignore')

    def buscar_por_nombre(self, nombre: str) -> List[Medicamento]:
        """Busca medicamentos por coincidencia parcial en nombre o marca."""
        nombre_lower = nombre.lower()
        return [
            m for m in self.medicamentos
            if nombre_lower in m.producto.lower()
            or nombre_lower in m.marca.lower()
        ]

    def buscar_por_codigo(self, codigo: str) -> Optional[Medicamento]:
        """Busca un medicamento por su código exacto."""
        for m in self.medicamentos:
            if m.codigo == codigo:
                return m
        return None

    def filtrar_por_categoria(self, categoria: str) -> List[Medicamento]:
        """Filtra medicamentos por categoría (case-insensitive)."""
        if not categoria:
            return []
        cat_lower = categoria.lower()
        return [m for m in self.medicamentos if m.categoria and m.categoria.lower() == cat_lower]
