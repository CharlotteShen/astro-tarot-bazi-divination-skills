import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
pytest.importorskip("kerykeion")

from wheel import build_wheel  # noqa: E402

BIRTH_A = {
    "name": "A", "year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0,
    "lat": 31.23, "lon": 121.47, "tz": "Asia/Shanghai", "city": "Shanghai",
    "house_system": "Placidus",
}
BIRTH_B = {
    "name": "B", "year": 1988, "month": 3, "day": 2, "hour": 9, "minute": 15,
    "lat": 39.90, "lon": 116.41, "tz": "Asia/Shanghai", "city": "Beijing",
    "house_system": "Placidus",
}


def _valid_svg(s):
    return isinstance(s, str) and len(s) > 1000 and "<svg" in s and "</svg>" in s


def test_natal_returns_svg_string():
    assert _valid_svg(build_wheel("natal", BIRTH_A))


def test_synastry_two_subjects():
    assert _valid_svg(build_wheel("synastry", BIRTH_A, BIRTH_B))


def test_composite_renders():
    assert _valid_svg(build_wheel("composite", BIRTH_A, BIRTH_B))


def test_davison_renders():
    assert _valid_svg(build_wheel("davison", BIRTH_A, BIRTH_B))


def test_marks_canonical_renders():
    assert _valid_svg(build_wheel("marks", BIRTH_A, BIRTH_B, who="A"))
    assert _valid_svg(build_wheel("marks", BIRTH_A, BIRTH_B, who="B"))


def test_theme_and_lang_passthrough():
    assert _valid_svg(build_wheel("natal", BIRTH_A, theme="dark"))
    assert _valid_svg(build_wheel("natal", BIRTH_A, lang="CN"))


def test_missing_second_person_raises():
    for t in ("synastry", "composite", "davison", "marks"):
        with pytest.raises(ValueError):
            build_wheel(t, BIRTH_A)


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        build_wheel("transit", BIRTH_A)


from wheel import render_to_file, main  # noqa: E402


def test_writes_file_to_out_dir(tmp_path):
    path = render_to_file("natal", BIRTH_A, out_dir=str(tmp_path))
    assert path.endswith(".svg")
    assert os.path.exists(path) and os.path.getsize(path) > 1000
    assert os.path.basename(path) == "natal-a-light.svg"


def test_filename_slugs_two_person_and_lang(tmp_path):
    path = render_to_file("synastry", BIRTH_A, BIRTH_B, theme="dark", lang="CN",
                          out_dir=str(tmp_path))
    assert os.path.basename(path) == "synastry-a-b-dark-cn.svg"


def test_marks_filename_includes_who(tmp_path):
    path = render_to_file("marks", BIRTH_A, BIRTH_B, who="B", out_dir=str(tmp_path))
    assert os.path.basename(path) == "marks-b-a-b-light.svg"


def test_cli_natal_writes(tmp_path, capsys):
    rc = main(["--type", "natal", "--date", "1990-06-15", "--time", "12:00",
               "--lat", "31.23", "--lon", "121.47", "--tz", "Asia/Shanghai",
               "--city", "Shanghai", "--name", "A", "--out-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.endswith(".svg") and os.path.exists(out)


def test_cli_synastry_missing_person_b_errors(tmp_path, capsys):
    rc = main(["--type", "synastry", "--date", "1990-06-15", "--time", "12:00",
               "--lat", "31.23", "--lon", "121.47", "--tz", "Asia/Shanghai",
               "--out-dir", str(tmp_path)])
    assert rc == 1
    assert "person B" in capsys.readouterr().err


def test_invalid_who_raises():
    with pytest.raises(ValueError):
        build_wheel("marks", BIRTH_A, BIRTH_B, who="X")


def test_davison_honors_house_system():
    # A bad house system must now surface as an error on the derived davison chart,
    # proving the user's house_system is threaded through (not silently forced to Placidus).
    bad_a = dict(BIRTH_A, house_system="NotARealSystem")
    with pytest.raises(ValueError):
        build_wheel("davison", bad_a, BIRTH_B)
