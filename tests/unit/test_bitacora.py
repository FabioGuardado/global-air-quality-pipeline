from air_quality.bitacora import COLUMNAS, Bitacora, _registrar


def test_registrar_y_exportar():
    b = Bitacora()
    b.registrar("I", "City", "Normalizar", "motivo")
    df = b.to_frame()
    assert list(df.columns) == COLUMNAS
    assert df.iloc[0].tolist() == ["I", "City", "Normalizar", "motivo"]


def test_bitacora_vacia_tiene_columnas():
    assert list(Bitacora().to_frame().columns) == COLUMNAS


def test_registrar_opcional():
    _registrar(None, "I", "x", "y", "z")      # no falla sin bitácora
    b = Bitacora()
    _registrar(b, "I", "x", "y", "z")
    assert len(b) == 1
