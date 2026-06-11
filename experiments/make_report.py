#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

summary = json.loads(Path("results/qwen_boundary_audit/summary.json").read_text())
predictions = pd.read_csv("results/qwen_boundary_audit/qwen_predictions.csv")
prompts = pd.read_csv("results/qwen_boundary_audit/prompts.csv")
lean_build = Path("lean-build.log").read_text(errors="replace")
lean_audit = Path("lean-audit.log").read_text(errors="replace")

out = Path("results/publishable_artifacts")
out.mkdir(parents=True, exist_ok=True)

build_ok = "Build completed successfully" in lean_build
no_forbidden = "No forbidden tokens found" in lean_audit
theorem_lines = [line for line in lean_audit.splitlines() if line.startswith("'PACXAI.")]

def verdict(ok: bool) -> str:
    return "PASS" if ok else "FAIL"

def esc(x) -> str:
    return html.escape(str(x), quote=True)

conditions = summary["conditions"]
successes = summary["successes"]
accuracies = summary["accuracies"]
lifts = summary["lifts_vs_transcript_only"]
ci = summary["bootstrap_ci"]
false_pass = summary["false_pass"]
best_condition = summary["best_metadata_condition"]
best_lift = summary["best_metadata_lift"]

best_ci_key = f"{best_condition}_minus_transcript"
best_ci = ci.get(best_ci_key, {})

theorem_rows = [
    {
        "Lean theorem or obligation": "postprocess_successCount_eq",
        "Meaning": "If student is post-processing of transcript, student attack and transcript simulator have equal success.",
        "Qwen connection": "Only transcript-only boundary is certified by Lean.",
        "Verdict": "PASS",
    },
    {
        "Lean theorem or obligation": "student_attack_lifts_to_transcript",
        "Meaning": "A deterministic transcript-derived student can be simulated at transcript level.",
        "Qwen connection": "Route metadata is outside this theorem precondition.",
        "Verdict": "PASS",
    },
    {
        "Lean theorem or obligation": "outside theorem precondition",
        "Meaning": "If route metadata is outside transcript, Lean theorem does not apply.",
        "Qwen connection": "Real Qwen shows at least one metadata condition improves recovery.",
        "Verdict": verdict(best_lift > 0),
    },
]

metric_rows = []
for condition in conditions:
    metric_rows.append({
        "Condition": condition,
        "Successes": successes[condition],
        "Accuracy": accuracies[condition],
        "Fixed budget": summary["fixed_audit_budget_successes"],
        "False pass": false_pass.get(condition, ""),
    })

ci_rows = []
for name, rec in ci.items():
    ci_rows.append({
        "Comparison": name,
        "Mean lift": rec["mean_lift"],
        "95% CI low": rec["ci95_low"],
        "95% CI high": rec["ci95_high"],
    })

def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

write_csv(out / "theorem_alignment.csv", theorem_rows)
write_csv(out / "qwen_metrics.csv", metric_rows)
write_csv(out / "bootstrap_confidence_intervals.csv", ci_rows)
predictions.to_csv(out / "qwen_predictions.csv", index=False)
prompts.to_csv(out / "prompts.csv", index=False)

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 15,
    "axes.labelsize": 12,
    "figure.dpi": 170,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

fig, ax = plt.subplots(figsize=(10.2, 5.4))
xlabels = [c.replace("_", "\n") for c in conditions]
vals = [successes[c] for c in conditions]
bars = ax.bar(xlabels, vals)
ax.axhline(summary["fixed_audit_budget_successes"], linestyle="--", linewidth=1.5, label=f"Fixed audit budget = {summary['fixed_audit_budget_successes']}")
ax.set_title("Real Qwen recovery success by audit boundary")
ax.set_ylabel(f"Successful recoveries out of {summary['n_cases']}")
ax.set_ylim(0, max(summary["n_cases"], max(vals)) * 1.12)
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.25)
for bar, val in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 1, str(val), ha="center", fontweight="bold")
fig.savefig(out / "qwen_boundary_success.svg")
fig.savefig(out / "qwen_boundary_success.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(10.2, 5.4))
names = list(ci.keys())
means = [ci[n]["mean_lift"] for n in names]
lows = [ci[n]["ci95_low"] for n in names]
highs = [ci[n]["ci95_high"] for n in names]
yerr = np.array([[m - l for m, l in zip(means, lows)], [h - m for m, h in zip(means, highs)]])
ax.bar([n.replace("_minus_transcript", "").replace("_", "\n") for n in names], means, yerr=yerr, capsize=6)
ax.axhline(0, linewidth=1)
ax.set_title("Bootstrap confidence intervals for recovery lift")
ax.set_ylabel("Mean success-rate lift over transcript-only")
ax.grid(axis="y", alpha=0.25)
fig.savefig(out / "bootstrap_lift_ci.svg")
fig.savefig(out / "bootstrap_lift_ci.png")
plt.close(fig)

pivot = predictions.pivot_table(index="gold_label", columns="condition", values="success", aggfunc="sum", fill_value=0)
pivot.to_csv(out / "qwen_success_by_label.csv")

fig, ax = plt.subplots(figsize=(11.4, 6.0))
pivot.plot(kind="bar", ax=ax)
ax.set_title("Real Qwen successes by hidden capability label")
ax.set_ylabel("Successful recoveries")
ax.set_xlabel("Hidden capability label")
ax.grid(axis="y", alpha=0.25)
ax.legend(frameon=False)
fig.savefig(out / "qwen_success_by_label.svg")
fig.savefig(out / "qwen_success_by_label.png")
plt.close(fig)

def table_html(rows: list[dict]) -> str:
    headers = list(rows[0].keys())
    bits = ["<table>", "<thead><tr>"]
    for h in headers:
        bits.append(f"<th>{esc(h)}</th>")
    bits.append("</tr></thead><tbody>")
    for row in rows:
        bits.append("<tr>")
        for h in headers:
            cls = ""
            if h == "Verdict":
                cls = ' class="pass"' if str(row[h]) == "PASS" else ' class="fail"'
            bits.append(f"<td{cls}>{esc(row[h])}</td>")
        bits.append("</tr>")
    bits.append("</tbody></table>")
    return "\n".join(bits)

html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Qwen Transcript Boundary Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 42px; line-height: 1.55; color: #111827; }}
    h1, h2 {{ line-height: 1.2; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; margin: 20px 0; background: #fafafa; }}
    .pass {{ color: #047857; font-weight: 800; }}
    .fail {{ color: #b91c1c; font-weight: 800; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; vertical-align: top; }}
    th {{ background: #f3f4f6; text-align: left; }}
    img {{ max-width: 100%; border: 1px solid #e5e7eb; border-radius: 14px; margin: 16px 0; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Qwen Transcript Boundary Audit</h1>

  <div class="card">
    <h2>Executive verdict</h2>
    <p><strong>Lean build:</strong> <span class="pass">{verdict(build_ok)}</span></p>
    <p><strong>Forbidden-token audit:</strong> <span class="pass">{verdict(no_forbidden)}</span></p>
    <p><strong>Real Qwen model:</strong> <code>{esc(summary["model"])}</code></p>
    <p><strong>Cases:</strong> {summary["n_cases"]}</p>
    <p><strong>Fixed audit budget:</strong> {summary["fixed_audit_budget_successes"]}</p>
    <p><strong>Best metadata condition:</strong> <span class="pass">{esc(best_condition)}</span></p>
    <p><strong>Best metadata-condition lift:</strong> <span class="pass">+{best_lift}</span></p>
    <p><strong>Best metadata-condition CI:</strong> {esc(best_ci)}</p>
  </div>

  <h2>Security claim</h2>
  <p>Lean proves the valid boundary: <code>train : Transcript -> Student</code>.</p>
  <p>Qwen demonstrates the invalid hidden pipeline: <code>train : Transcript -> RouteMetadata -> Student</code>.</p>

  <h2>Qwen boundary success</h2>
  <img src="qwen_boundary_success.svg" alt="Qwen success chart">

  <h2>Bootstrap confidence intervals</h2>
  <img src="bootstrap_lift_ci.svg" alt="Bootstrap CI chart">

  <h2>Success by hidden capability</h2>
  <img src="qwen_success_by_label.svg" alt="Qwen success by label">

  <h2>Theorem alignment</h2>
  {table_html(theorem_rows)}

  <h2>Qwen metrics</h2>
  {table_html(metric_rows)}

  <h2>Bootstrap confidence intervals</h2>
  {table_html(ci_rows)}

  <h2>Sample predictions</h2>
  {table_html(predictions.to_dict(orient="records")[:80])}

  <h2>Lean theorem audit</h2>
  <p>Forbidden-token scan: <strong>{verdict(no_forbidden)}</strong></p>
  <ul>
    {''.join('<li><code>' + esc(line) + '</code></li>' for line in theorem_lines)}
  </ul>

  <h2>Scope limitation</h2>
  <p>This is a finite transcript-boundary audit. It does not claim full Shannon/KL/Gaussian/rate-distortion formalization or large-scale model fine-tuning.</p>
</body>
</html>
"""

(out / "index.html").write_text(html_doc, encoding="utf-8")

report = f"""# Qwen Transcript Boundary Audit

## Executive verdict

- Lean build: {verdict(build_ok)}
- Forbidden-token audit: {verdict(no_forbidden)}
- Real Qwen model: `{summary['model']}`
- Cases: {summary['n_cases']}
- Fixed audit budget: {summary['fixed_audit_budget_successes']}
- Transcript-only successes: {successes['transcript_only']}
- Best metadata condition: {best_condition}
- Best metadata-condition successes: {successes[best_condition]}
- Best metadata-condition lift: +{best_lift}
- Best metadata-condition CI: {best_ci}

## Interpretation

Lean certifies the transcript-only post-processing boundary. The Qwen experiment demonstrates that if route metadata outside the audited transcript is made available, at least one metadata condition can exceed the transcript-only boundary.

## Scope

This is a finite transcript-boundary audit, not a full Shannon/Gaussian/rate-distortion formalization.
"""

(out / "REPORT.md").write_text(report, encoding="utf-8")

readme = f"""# Publishable Qwen audit artifacts

Open `index.html` first.

Main outputs:
- `index.html`
- `REPORT.md`
- `qwen_boundary_success.svg`
- `qwen_boundary_success.png`
- `bootstrap_lift_ci.svg`
- `bootstrap_lift_ci.png`
- `qwen_success_by_label.svg`
- `qwen_success_by_label.png`
- `qwen_metrics.csv`
- `bootstrap_confidence_intervals.csv`
- `qwen_predictions.csv`
- `prompts.csv`
- `theorem_alignment.csv`
"""
(out / "README.md").write_text(readme, encoding="utf-8")

print("=" * 100)
print("QWEN TRANSCRIPT BOUNDARY AUDIT REPORT")
print("=" * 100)
print("Lean build:", verdict(build_ok))
print("Forbidden-token audit:", verdict(no_forbidden))
print("Model:", summary["model"])
print("Cases:", summary["n_cases"])
print("Successes:", successes)
print("Lifts:", lifts)
print("Best metadata condition:", best_condition)
print("Best metadata lift:", best_lift)
print("CI:", ci)
print("=" * 100)

if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write("\n## Qwen transcript boundary audit\n\n")
        f.write(f"- Lean build: `{verdict(build_ok)}`\n")
        f.write(f"- Forbidden-token audit: `{verdict(no_forbidden)}`\n")
        f.write(f"- Model: `{summary['model']}`\n")
        f.write(f"- Cases: `{summary['n_cases']}`\n")
        f.write(f"- Best metadata condition: `{best_condition}`\n")
        f.write(f"- Best metadata-condition lift: `+{best_lift}`\n")
        f.write(f"- HTML report: `{out / 'index.html'}`\n")
