# Reproduce

```bash
lake build
bash scripts/audit.sh
source .venv/bin/activate
python experiments/qwen_boundary_audit.py --model mlx-community/Qwen2.5-0.5B-Instruct-4bit --n-cases 120
python experiments/make_report.py
```

Expected headline result:
- Lean build succeeds.
- Lean audit has no forbidden proof tokens.
- At least one metadata condition improves recovery over transcript-only.
- HTML report appears at `results/publishable_artifacts/index.html`.
