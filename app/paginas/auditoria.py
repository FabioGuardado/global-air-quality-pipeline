"""Página del anexo de auditoría: la lógica vive en capitulos/auditoria.py."""

import contexto
from capitulos import auditoria

auditoria.render(contexto.actual().t)
