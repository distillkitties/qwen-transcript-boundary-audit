# Qwen Transcript Boundary Audit

This artifact combines Lean proofs with real Qwen inference through MLX.

Lean proves the valid audit boundary:

```text
train : Transcript -> Student
```

Qwen demonstrates the failure mode:

```text
train : Transcript -> RouteMetadata -> Student
```

If route metadata is omitted from the audited transcript, a transcript-only audit can falsely pass.
