"""Pipeline de limpieza y transformación del dataset global de calidad del aire."""

from .datos import cargar_crudo, cargar_procesado
from .pipeline import ResultadoPipeline, ejecutar

__all__ = ["cargar_crudo", "cargar_procesado", "ejecutar", "ResultadoPipeline"]
