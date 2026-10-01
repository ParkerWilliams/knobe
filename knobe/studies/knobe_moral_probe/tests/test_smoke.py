def test_kmp_importable():
    import kmp
    assert kmp.__doc__.startswith("knobe_moral_probe")


def test_knobe_importable():
    from knobe.parsing import parse_rating
    assert parse_rating(" 7")[0] == 7
