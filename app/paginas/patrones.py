"""Página del capítulo: la lógica vive en capitulos/patrones.py."""

import contexto
from capitulos import patrones

c = contexto.actual()
patrones.render(c.df, c.df_contexto, c.f, c.t)
