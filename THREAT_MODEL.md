# Threat Model

Protected secret: a hidden capability/route class.

Audited transcript: the text/log boundary claimed by the auditor.

Omitted metadata: route_id values such as code_route, safety_route, expert_route.

Claim: post-processing soundness only applies when every training/inference input used by the artifact is inside the audited transcript boundary.
