# Qwen Transcript Boundary Audit

## Executive verdict

- Lean build: PASS
- Forbidden-token audit: PASS
- Real Qwen model: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`
- Cases: 120
- Fixed audit budget: 30
- Transcript-only successes: 25
- Best metadata condition: route_id_only
- Best metadata-condition successes: 34
- Best metadata-condition lift: +9
- Best metadata-condition CI: {'mean_lift': 0.075, 'ci95_low': 0, 'ci95_high': 0.15}

## Interpretation

Lean certifies the transcript-only post-processing boundary. The Qwen experiment demonstrates that if route metadata outside the audited transcript is made available, at least one metadata condition can exceed the transcript-only boundary.

## Scope

This is a finite transcript-boundary audit, not a full Shannon/Gaussian/rate-distortion formalization.
