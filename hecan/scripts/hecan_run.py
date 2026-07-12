#!/usr/bin/env python3
"""中西合参编排脚本——调起四个既有排盘 CLI，打包原生输出为一个信封。零新计算。

单人:  python hecan_run.py --year 2000 --month 1 --day 1 --hour 12 --lon -0.1278 \
         --lat 51.5074 --tz Europe/London --gender 女 [--date YYYY-MM-DD] [--json]
双人:  加 --b-* 同构。时辰不明用 --hour unknown（紫微跳过、natal 以 12:00 降级、八字三柱自降级）。
真实生辰仅经参数进内存；写文件型子 CLI（chart.py/synastry.py）经临时文件即读即删。
"""
import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
TIMEOUT = 120
STATUSES = {"ok", "degraded", "skipped", "error"}

NOTES = [
    "合参为编排层：各系输出为其排盘脚本原文，解读按 hecan-method.md（含反多重宿命红线）。",
    "多系共振加深的是主题分量，不是宿命确定性；体系间不互为证据，只互为镜子。",
    "缺席/降级体系如实标注，不以其他体系推补。",
]


def _run(cmd, stdin_text=None):
    """跑子进程 → (状态, 原因, 输出)。非零退出 → error + stderr 摘要，不抛异常。"""
    try:
        r = subprocess.run(cmd, input=stdin_text, capture_output=True,
                           encoding="utf-8", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return "error", "子进程超时", None
    if r.returncode != 0:
        return "error", (r.stderr or "").strip()[-200:] or "子进程失败", None
    return "ok", None, r.stdout


def _run_to_file(cmd, stdin_text=None):
    """写文件型 CLI（chart.py/synastry.py）：--out 指向临时文件，即读即删。"""
    with tempfile.NamedTemporaryFile("r", suffix=".md", delete=False) as tf:
        path = tf.name
    try:
        status, reason, _ = _run(cmd + ["--out", path], stdin_text)
        if status != "ok":
            return status, reason, None
        return "ok", None, Path(path).read_text(encoding="utf-8")
    finally:
        Path(path).unlink(missing_ok=True)


def _unknown(p):
    return str(p["hour"]) == "unknown"


def _natal_single(p):
    t = "12:00" if _unknown(p) else f"{int(p['hour']):02d}:{int(p['minute']):02d}"
    cmd = [PY, str(ROOT / "natal-astrology/scripts/chart.py"),
           "--name", p["label"],
           "--date", f"{p['year']:04d}-{p['month']:02d}-{p['day']:02d}",
           "--time", t, "--lat", str(p["lat"]), "--lon", str(p["lon"]),
           "--tz", p["tz"]]
    status, reason, out = _run_to_file(cmd)
    if status == "ok" and _unknown(p):
        return "degraded", "时辰未知：以 12:00 计，宫位/上升/月亮不可用", out
    return status, reason, out


def _bazi_single(p, ref):
    cmd = [PY, str(ROOT / "bazi/scripts/bazi_chart.py"),
           "--year", str(p["year"]), "--month", str(p["month"]),
           "--day", str(p["day"]), "--hour", str(p["hour"]),
           "--minute", str(p["minute"]), "--lon", str(p["lon"]),
           "--lat", str(p["lat"]), "--tz", p["tz"],
           "--gender", p["gender"], "--date", ref]
    return _run(cmd)


def _ziwei_single(p, ref):
    if _unknown(p):
        return "skipped", "时辰未知：紫微排盘必需时辰", None
    cmd = [PY, str(ROOT / "ziwei/scripts/ziwei_chart.py"),
           "--year", str(p["year"]), "--month", str(p["month"]),
           "--day", str(p["day"]), "--hour", str(p["hour"]),
           "--minute", str(p["minute"]), "--lon", str(p["lon"]),
           "--lat", str(p["lat"]), "--tz", p["tz"],
           "--gender", p["gender"], "--date", ref]
    return _run(cmd)


def _xiuyao(p, ref, b=None):
    cmd = [PY, str(ROOT / "xiuyao/scripts/xiuyao_chart.py"),
           "--year", str(p["year"]), "--month", str(p["month"]),
           "--day", str(p["day"]), "--label", p["label"], "--date", ref]
    if b is not None:
        cmd += ["--b-year", str(b["year"]), "--b-month", str(b["month"]),
                "--b-day", str(b["day"]), "--b-label", b["label"]]
    return _run(cmd)


def _natal_pair(a, b):
    def birth(p):
        return {"name": p["label"], "year": p["year"], "month": p["month"],
                "day": p["day"], "hour": 12 if _unknown(p) else int(p["hour"]),
                "minute": 0 if _unknown(p) else int(p["minute"]),
                "lon": p["lon"], "lat": p["lat"], "tz": p["tz"]}
    payload = json.dumps({"birth_a": birth(a), "birth_b": birth(b),
                          "relationship_type": "romantic"})
    status, reason, out = _run_to_file(
        [PY, str(ROOT / "natal-astrology/scripts/synastry.py")], payload)
    unknowns = [p["label"] for p in (a, b) if _unknown(p)]
    if status == "ok" and unknowns:
        return ("degraded",
                f"时辰未知（{'、'.join(unknowns)}）：以 12:00 计，宫位重叠/上升相关不可用",
                out)
    return status, reason, out


def _bazi_pair(a, b, ref):
    cmd = [PY, str(ROOT / "bazi/scripts/bazi_match.py"), "--date", ref]
    for pre, p in (("--a", a), ("--b", b)):
        cmd += [f"{pre}-year", str(p["year"]), f"{pre}-month", str(p["month"]),
                f"{pre}-day", str(p["day"]), f"{pre}-hour", str(p["hour"]),
                f"{pre}-minute", str(p["minute"]), f"{pre}-lon", str(p["lon"]),
                f"{pre}-lat", str(p["lat"]), f"{pre}-tz", p["tz"],
                f"{pre}-gender", p["gender"], f"{pre}-label", p["label"]]
    return _run(cmd)


def build_envelope(a, b, ref):
    systems = {}
    if b is None:
        systems["natal"] = _natal_single(a)
        systems["八字"] = _bazi_single(a, ref)
        systems["紫微"] = _ziwei_single(a, ref)
        systems["宿曜"] = _xiuyao(a, ref)
    else:
        systems["natal"] = _natal_pair(a, b)
        systems["八字"] = _bazi_pair(a, b, ref)
        systems["紫微"] = ("skipped", "体系无双人模式", None)
        systems["宿曜"] = _xiuyao(a, ref, b)
    env = {"模式": "单人" if b is None else "双人", "参考日期": ref,
           "系统": {k: {"状态": s, "原因": r, "输出": o}
                    for k, (s, r, o) in systems.items()},
           "可用性": [f"{k}: {s}" for k, (s, r, o) in systems.items()],
           "标注": NOTES}
    active = [s for s, _, _ in systems.values() if s != "skipped"]
    all_error = bool(active) and all(s == "error" for s in active)
    return env, all_error


def render(env):
    lines = [f"# 中西合参（{env['模式']}）　参考日期 {env['参考日期']}", ""]
    lines.append("【可用性】" + "；".join(env["可用性"]))
    for name, entry in env["系统"].items():
        head = f"【{name} · {entry['状态']}】"
        if entry["原因"]:
            head += f"（{entry['原因']}）"
        lines += ["", head, entry["输出"].rstrip() if entry["输出"] else "（无输出）"]
    lines += ["", "【标注】" + " ".join(f"{i}) {n}" for i, n in enumerate(NOTES, 1))]
    return "\n".join(lines)


def _add_person_args(p, pre=""):
    d = f"--{pre}" if pre else "--"
    p.add_argument(f"{d}year", type=int)
    p.add_argument(f"{d}month", type=int)
    p.add_argument(f"{d}day", type=int)
    p.add_argument(f"{d}hour")                    # 整数或 unknown
    p.add_argument(f"{d}minute", type=int, default=0)
    p.add_argument(f"{d}lon", type=float)
    p.add_argument(f"{d}lat", type=float)
    p.add_argument(f"{d}tz")
    p.add_argument(f"{d}gender", choices=["男", "女"])
    p.add_argument(f"{d}label", default="乙方" if pre else "甲方")


def main(argv=None):
    p = argparse.ArgumentParser(description="中西合参编排（零新计算，信封打包）")
    _add_person_args(p)
    _add_person_args(p, "b-")
    p.add_argument("--date", default=_date.today().isoformat())
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    core = ["year", "month", "day", "hour", "lon", "lat", "tz", "gender"]
    if any(getattr(args, k) is None for k in core):
        print("错误：单人参数 --year/--month/--day/--hour/--lon/--lat/--tz/--gender 必须齐全",
              file=sys.stderr)
        return 1
    b_vals = [getattr(args, f"b_{k}") for k in core]
    if any(v is not None for v in b_vals) and any(v is None for v in b_vals):
        print("错误：--b-* 参数必须同时提供（year/month/day/hour/lon/lat/tz/gender）",
              file=sys.stderr)
        return 1

    def _hour_ok(h):
        if str(h) == "unknown":
            return True
        try:
            return 0 <= int(h) <= 23
        except (TypeError, ValueError):
            return False

    if not _hour_ok(args.hour) or (b_vals[0] is not None and not _hour_ok(args.b_hour)):
        print("错误：--hour/--b-hour 须为 0–23 的整数或 unknown", file=sys.stderr)
        return 1

    person = {k: getattr(args, k) for k in core + ["minute", "label"]}
    b = None
    if b_vals[0] is not None:
        b = {k: getattr(args, f"b_{k}") for k in core}
        b["minute"] = args.b_minute
        b["label"] = args.b_label

    env, all_error = build_envelope(person, b, args.date)
    print(json.dumps(env, ensure_ascii=False, indent=2) if args.json else render(env))
    return 1 if all_error else 0


if __name__ == "__main__":
    sys.exit(main())
