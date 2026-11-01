"""Pipeline completo: CSV crudo → dataset procesado (y matriz escalada para modelado).

Uso por línea de comandos (desde la raíz del repo):

    python -m air_quality.pipeline [--entrada RUTA] [--salida RUTA]
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import config
from .bitacora import Bitacora
from .datos import cargar_crudo
from .derivadas import agregar_derivadas, agregar_ordinales
from .imputacion import aplicar_imputacion, columnas_con_nulos, plan_imputacion
from .limpieza import (agregar_variables_tiempo, agregar_viento_cat, eliminar_duplicados,
                       normalizar_claves)
from .transformacion import diagnostico_escalado, dummies_ciudad, escalar


@dataclass
class ResultadoPipeline:
    procesado: pd.DataFrame          # entregable: data/processed
    modelo: pd.DataFrame             # escalado + codificado, solo para auditoría/modelado
    final: pd.DataFrame              # todas las columnas intermedias
    plan_imputacion: pd.DataFrame
    diagnostico_escalado: pd.DataFrame
    bitacora: Bitacora = field(default_factory=Bitacora)


def construir_procesado(df_final, columnas=config.ENTREGABLE):
    cols = [c for c in columnas if c in df_final.columns]
    procesado = df_final[cols].sort_values(["City", "Date"]).reset_index(drop=True)
    # Las derivadas arrastran el ruido del float: se redondean a la precisión de las mediciones
    redondear = [c for c in config.REDONDEAR if c in procesado.columns]
    procesado[redondear] = procesado[redondear].round(3)
    return procesado


def ejecutar(df_raw):
    """Aplica las Fases I, III y IV en el mismo orden que el notebook."""
    bitacora = Bitacora()

    # Fase I: claves. Fase II deja creadas las variables de tiempo y viento_cat.
    df = normalizar_claves(df_raw, bitacora)
    df = agregar_variables_tiempo(df)
    df = agregar_viento_cat(df)

    # Fase III: duplicados → nulos
    df = eliminar_duplicados(df, bitacora=bitacora)
    plan = plan_imputacion(df, columnas_con_nulos(df))
    df = aplicar_imputacion(df, plan, bitacora)

    # Fase IV: derivadas → codificación → escalado
    df_final = agregar_ordinales(agregar_derivadas(df, bitacora=bitacora))
    dummies = dummies_ciudad(df_final)

    continuas = [c for c in config.CONTINUAS if c in df_final.columns]
    a_escalar = [c for c in continuas if c not in config.EXCLUIR_MODELO]
    diag = diagnostico_escalado(df_final, a_escalar)
    escalado = escalar(df_final, diag, bitacora)

    modelo = pd.concat([escalado,
                        df_final[config.CODIFICADAS].drop(columns=config.EXCLUIR_MODELO,
                                                          errors="ignore"),
                        dummies], axis=1)
    procesado = construir_procesado(df_final)

    n_ciudades = df_final["City"].nunique()
    bitacora.registrar("IV", "City", f"One-Hot con drop_first ({dummies.shape[1]} columnas)",
                       f"Nominal de {n_ciudades} categorías; Country se omite por ser "
                       "funcionalmente dependiente")
    bitacora.registrar("IV", ", ".join(config.EXCLUIR_MODELO), "Excluir de df_modelo",
                       "Multicolinealidad: combinación lineal exacta y duplicado de Wind Speed")

    return ResultadoPipeline(procesado=procesado, modelo=modelo, final=df_final,
                             plan_imputacion=plan, diagnostico_escalado=diag,
                             bitacora=bitacora)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entrada", type=Path, default=config.RAW_PATH)
    parser.add_argument("--salida", type=Path, default=config.PROCESSED_PATH)
    args = parser.parse_args(argv)

    resultado = ejecutar(cargar_crudo(args.entrada))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.procesado.to_csv(args.salida, index=False)
    # Solo ASCII: la consola de Windows (cp1252) no puede imprimir "→"
    print(f"Exportado: {args.salida} ({len(resultado.procesado):,} filas x "
          f"{resultado.procesado.shape[1]} columnas)")
    return resultado


if __name__ == "__main__":
    main()
