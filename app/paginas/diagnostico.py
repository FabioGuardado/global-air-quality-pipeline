"""Página del capítulo: la lógica vive en capitulos/diagnostico.py."""

import contexto
from capitulos import diagnostico

c = contexto.actual()
diagnostico.render(c.df, c.df_contexto, c.df_total, c.f, c.t)
