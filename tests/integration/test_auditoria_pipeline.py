"""La auditoría debe contar exactamente lo mismo que registra el pipeline."""

import pytest

from air_quality import cargar_crudo, ejecutar
from air_quality.auditoria import auditar


@pytest.fixture(scope="module")
def auditoria_real():
    raw = cargar_crudo()
    resultado = ejecutar(raw)
    return auditar(raw, resultado), resultado


def test_cifras_coinciden_con_la_bitacora(auditoria_real):
    a, resultado = auditoria_real
    r = a.resumen
    acciones = resultado.bitacora.to_frame().set_index("columna")["accion"]
    assert acciones["todas"] == f"Eliminar {r['duplicados_exactos']} filas"
    assert acciones["City+Country+Date"] == f"Eliminar {r['duplicados_clave']} filas"
    assert r["filas_crudo"] - r["duplicados"] == r["filas_procesado"] == 5075
    assert r["decisiones"] == len(resultado.bitacora)


def test_nulos_imputados_coinciden_con_el_plan(auditoria_real):
    a, resultado = auditoria_real
    imputados = resultado.bitacora.to_frame().query("fase == 'III-nulos'")["accion"]
    total = sum(int(x.split("(")[1].split()[0]) for x in imputados)
    assert a.resumen["nulos_imputados"] == total
    assert a.resumen["nulos_procesado"] == 0


def test_embudo_termina_en_el_procesado(auditoria_real):
    a, _ = auditoria_real
    assert a.embudo["filas"].is_monotonic_decreasing
    assert a.embudo["filas"].iloc[-1] == a.resumen["filas_procesado"]


def test_solo_falla_la_coherencia_de_los_sensores(auditoria_real):
    a, _ = auditoria_real
    fallan = a.verificaciones.loc[~a.verificaciones["aprobado"], "control"].tolist()
    assert fallan == ["Coherencia física de los sensores"]
    assert a.distribuciones["intacta"].all()
