"""Página del capítulo: la lógica vive en capitulos/causa.py."""

import contexto
from capitulos import causa

c = contexto.actual()
causa.render(c.df, c.f, c.t)
