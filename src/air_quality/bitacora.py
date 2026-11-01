"""Bitácora de decisiones de limpieza y transformación."""

import pandas as pd

COLUMNAS = ["fase", "columna", "accion", "justificacion"]


class Bitacora:
    """Registro ordenado de cada decisión tomada sobre los datos."""

    def __init__(self):
        self.decisiones = []

    def registrar(self, fase, columna, accion, justificacion):
        self.decisiones.append({"fase": fase, "columna": columna,
                                "accion": accion, "justificacion": justificacion})

    def to_frame(self):
        return pd.DataFrame(self.decisiones, columns=COLUMNAS)

    def __len__(self):
        return len(self.decisiones)


def _registrar(bitacora, *args):
    """Registra solo si se pasó una bitácora (las funciones la aceptan como opcional)."""
    if bitacora is not None:
        bitacora.registrar(*args)
