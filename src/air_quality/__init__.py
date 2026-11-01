"""Pipeline de limpieza y transformación del dataset global de calidad del aire."""

from .datos import cargar_crudo, cargar_procesado

__all__ = ["cargar_crudo", "cargar_procesado", "ejecutar", "ResultadoPipeline"]


def __getattr__(nombre):
    # Import diferido: evita cargar `pipeline` al ejecutar `python -m air_quality.pipeline`
    if nombre in ("ejecutar", "ResultadoPipeline"):
        from . import pipeline
        return getattr(pipeline, nombre)
    raise AttributeError(nombre)
