"""合参编排测试——签名 token 来自 2026-07-09 接口门禁实测（勿改）。
每条测试都真实调起子系统 CLI，整文件耗时约 1 分钟属正常。"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from hecan_run import STATUSES  # noqa: E402

PY = sys.executable
SCRIPT = os.path.join(os.path.dirname(__file__), "hecan_run.py")

ABC = ["--year", "2000", "--month", "1", "--day", "1", "--hour", "12",
       "--lon", "-0.1278", "--lat", "51.5074", "--tz", "Europe/London",
       "--gender", "女"]
UNK = ["--year", "1988", "--month", "11", "--day", "5", "--hour", "unknown",
       "--lon", "151.21", "--lat", "-33.87", "--tz", "Australia/Sydney",
       "--gender", "女"]
XYZ_B = ["--b-year", "1995", "--b-month", "6", "--b-day", "15", "--b-hour", "8",
         "--b-minute", "30", "--b-lon", "2.3522", "--b-lat", "48.8566",
         "--b-tz", "Europe/Paris", "--b-gender", "男"]
REF = ["--date", "2026-07-09"]


def run_cli(*args, cwd=None):
    return subprocess.run([PY, SCRIPT, *args], capture_output=True,
                          text=True, cwd=cwd, timeout=600)


def run_json(*args):
    r = run_cli(*args, "--json")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_single_known_all_ok():
    out = run_json(*ABC, *REF)
    sys_ = out["系统"]
    assert {k: v["状态"] for k, v in sys_.items()} == {
        "natal": "ok", "八字": "ok", "紫微": "ok", "宿曜": "ok"}
    assert "Sun: sign=Capricorn" in sys_["natal"]["输出"]
    assert "日柱 戊午" in sys_["八字"]["输出"]
    assert "紫微(庙)" in sys_["紫微"]["输出"]
    assert "心宿" in sys_["宿曜"]["输出"]
    assert out["模式"] == "单人" and out["参考日期"] == "2026-07-09"


def test_single_unknown_hour_degrades():
    out = run_json(*UNK, *REF)
    sys_ = out["系统"]
    assert sys_["紫微"]["状态"] == "skipped" and "时辰" in sys_["紫微"]["原因"]
    assert sys_["紫微"]["输出"] is None
    assert sys_["natal"]["状态"] == "degraded" and "12:00" in sys_["natal"]["原因"]
    assert "time: 12:00" in sys_["natal"]["输出"]
    assert sys_["八字"]["状态"] == "ok" and "时辰不明" in sys_["八字"]["输出"]
    assert sys_["宿曜"]["状态"] == "ok" and "角宿" in sys_["宿曜"]["输出"]


def test_pair_three_axes():
    out = run_json(*ABC, *XYZ_B, *REF)
    sys_ = out["系统"]
    assert out["模式"] == "双人"
    assert sys_["natal"]["状态"] == "ok" and "# Synastry" in sys_["natal"]["输出"]
    assert sys_["八字"]["状态"] == "ok" and "五合化火" in sys_["八字"]["输出"]
    assert sys_["宿曜"]["状态"] == "ok" and "成（中距离" in sys_["宿曜"]["输出"]
    assert sys_["紫微"]["状态"] == "skipped" and "双人" in sys_["紫微"]["原因"]


def test_envelope_schema():
    out = run_json(*ABC, *REF)
    assert set(out) == {"模式", "参考日期", "系统", "可用性", "标注"}
    for name, entry in out["系统"].items():
        assert set(entry) == {"状态", "原因", "输出"}, name
        assert entry["状态"] in STATUSES, name
    assert len(out["可用性"]) == 4 and isinstance(out["标注"], list)


def test_partial_failure_not_fatal():
    bad_tz = [a if a != "Europe/London" else "Bad/Zone" for a in ABC]
    r = run_cli(*bad_tz, *REF, "--json")
    assert r.returncode == 0            # 宿曜不吃 tz，仍 ok → 非全灭
    out = json.loads(r.stdout)
    assert out["系统"]["宿曜"]["状态"] == "ok"
    assert out["系统"]["八字"]["状态"] == "error"
    assert out["系统"]["八字"]["原因"]


def test_all_error_exit_1():
    bad = [a for a in ABC]
    bad[bad.index("--month") + 1] = "13"   # --month 13 → 四系全部报错
    r = run_cli(*bad, *REF, "--json")
    assert r.returncode == 1


def test_partial_b_args_rejected():
    r = run_cli(*ABC, *REF, "--b-year", "1995")
    assert r.returncode != 0 and "错误" in r.stderr


def test_text_render_sections():
    r = run_cli(*ABC, *REF)
    assert r.returncode == 0
    for token in ["【natal · ok】", "【八字 · ok】", "【紫微 · ok】", "【宿曜 · ok】", "【标注】"]:
        assert token in r.stdout, token


def test_no_stray_files(tmp_path):
    r = run_cli(*ABC, *REF, "--json", cwd=str(tmp_path))
    assert r.returncode == 0
    assert list(tmp_path.iterdir()) == []   # chart.py 默认 --out 落盘已被覆盖


def test_pair_one_unknown_hour_degrades():
    out = run_json(*UNK, *XYZ_B, *REF)
    sys_ = out["系统"]
    assert out["模式"] == "双人"
    assert sys_["natal"]["状态"] == "degraded" and "12:00" in sys_["natal"]["原因"]
    assert sys_["八字"]["状态"] == "ok"      # bazi_match 自吸收 unknown（甲方三柱）
    assert sys_["宿曜"]["状态"] == "ok"
    assert sys_["紫微"]["状态"] == "skipped"


def test_all_active_error_exit_1_with_skipped_ziwei():
    bad = [a for a in UNK]
    bad[bad.index("--month") + 1] = "13"     # 三个 active 体系全报错；紫微 skipped 不挡全灭判定
    r = run_cli(*bad, *REF, "--json")
    assert r.returncode == 1


def test_malformed_hour_rejected():
    bad = [a if a != "12" else "bogus" for a in ABC]
    r = run_cli(*bad, *REF)
    assert r.returncode != 0 and "错误" in r.stderr
