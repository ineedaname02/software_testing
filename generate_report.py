"""
Builds test_report.html from results.csv (written by run_tests.py).
The report is one self-contained file (no external libraries) so it can be
uploaded as a GitHub Actions artifact and opened anywhere.

Optional env var: REPORT_PLATFORM (e.g. Ubuntu / Windows). Defaults to this OS.
"""
import csv
import os
import platform
from datetime import datetime
from html import escape
from pathlib import Path

BASE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(BASE / "results.csv", newline="", encoding="utf-8")))

total = len(rows)
passed = sum(r["status"] == "PASS" for r in rows)
failed = sum(r["status"] == "FAIL" for r in rows)
errors = sum(r["status"] == "ERROR" for r in rows)
times = [float(r["seconds"]) for r in rows]
total_time = sum(times)
slowest = max(times) if times else 1
rate = (passed / total * 100) if total else 0
plat = os.getenv("REPORT_PLATFORM") or platform.system()
when = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pct(n):
    return f"{(n / total * 100) if total else 0:.1f}%"


body_rows = ""
for r in rows:
    s = r["status"]
    width = float(r["seconds"]) / slowest * 100
    body_rows += (
        f"<tr><td>{escape(r['test_id'])}</td><td>{escape(r['description'])}</td>"
        f"<td class='n'>{escape(r['expected'])}</td><td class='n'>{escape(r['actual'] or '-')}</td>"
        f"<td><span class='tag {s.lower()}'>{s}</span></td>"
        f"<td><div class='bar'><i style='width:{width:.0f}%'></i></div></td>"
        f"<td class='n'>{r['seconds']}s</td></tr>\n"
    )

bad = [r for r in rows if r["status"] != "PASS"]
if bad:
    fail_html = "<ul>" + "".join(
        f"<li><b>{escape(r['test_id'])}</b> ({r['status']}): {escape(r['reason'])}</li>" for r in bad
    ) + "</ul>"
else:
    fail_html = "<p class='ok'>No failed test cases.</p>"

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Test Report - AI Gateway Dashboard ({escape(plat)})</title>
<style>
body{{font:15px/1.5 "Segoe UI",Arial,sans-serif;background:#eef3f4;color:#10222b;margin:0}}
header{{background:{'#0b5a54' if failed + errors == 0 else '#8a2a1f'};color:#fff;padding:22px 28px}}
header h1{{margin:0;font-size:24px}} header p{{margin:4px 0 0;opacity:.85}}
main{{max-width:980px;margin:0 auto;padding:20px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.card{{background:#fff;border:1px solid #d6e0e4;border-radius:10px;padding:14px 18px;flex:1;min-width:130px}}
.card b{{display:block;font-size:26px}} .card span{{color:#5b6f79;font-size:13px}}
section{{background:#fff;border:1px solid #d6e0e4;border-radius:10px;padding:18px;margin-bottom:18px}}
h2{{margin:0 0 12px;font-size:17px}}
.stack{{display:flex;height:22px;border-radius:6px;overflow:hidden;background:#e2e8f0}}
.stack div{{height:100%}} .g{{background:#059669}} .r{{background:#dc2626}} .a{{background:#d97706}}
.legend{{margin-top:8px;color:#5b6f79;font-size:13px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:8px 10px;border-bottom:1px solid #e2e8f0;text-align:left}}
th{{font-size:13px;color:#5b6f79}} .n{{text-align:right;font-variant-numeric:tabular-nums}}
.tag{{padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700;color:#fff}}
.tag.pass{{background:#059669}} .tag.fail{{background:#dc2626}} .tag.error{{background:#d97706}}
.bar{{background:#e2e8f0;border-radius:4px;height:10px;min-width:120px}} .bar i{{display:block;height:100%;background:#0f766e;border-radius:4px}}
.ok{{color:#059669;font-weight:600;margin:0}}
</style></head><body>
<header><h1>Test Report: LLM AI Gateway Dashboard</h1>
<p>Platform: {escape(plat)} | Generated: {when} | Result: {'ALL TESTS PASSED' if failed + errors == 0 else 'FAILURES FOUND'}</p></header>
<main>
<div class="cards">
<div class="card"><b>{total}</b><span>Total tests</span></div>
<div class="card"><b style="color:#059669">{passed}</b><span>Passed</span></div>
<div class="card"><b style="color:#dc2626">{failed}</b><span>Failed</span></div>
<div class="card"><b style="color:#d97706">{errors}</b><span>Errors</span></div>
<div class="card"><b>{rate:.0f}%</b><span>Pass rate</span></div>
<div class="card"><b>{total_time:.1f}s</b><span>Total time</span></div>
</div>
<section><h2>Outcome breakdown</h2>
<div class="stack"><div class="g" style="width:{pct(passed)}"></div><div class="r" style="width:{pct(failed)}"></div><div class="a" style="width:{pct(errors)}"></div></div>
<div class="legend">Green = passed, red = failed (wrong total), amber = error (timeout or missing element)</div></section>
<section><h2>Failed test cases</h2>{fail_html}</section>
<section><h2>All test cases and execution times</h2>
<table><tr><th>ID</th><th>Description</th><th class="n">Expected</th><th class="n">Actual</th><th>Status</th><th>Time</th><th class="n">Seconds</th></tr>
{body_rows}</table></section>
</main></body></html>"""

out = BASE / "test_report.html"
out.write_text(html, encoding="utf-8")
print(f"Report written to {out.name} ({passed}/{total} passed, {total_time:.1f}s total)")
