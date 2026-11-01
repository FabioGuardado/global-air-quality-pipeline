"""Página del capítulo: la lógica vive en capitulos/recomendacion.py."""

import contexto
from capitulos import recomendacion

c = contexto.actual()
recomendacion.render(c.df, c.df_contexto, c.f, c.t)
