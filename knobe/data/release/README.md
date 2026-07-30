# data/release/

Releases in this directory are **append-only history**. Once a release
directory (`vX.Y/`) is written and its `manifest.json` committed, nothing
inside it may ever be edited or deleted — not by hand, not by a script, not
by a coding agent. If a mistake is found, cut a new release; do not amend
an old one.

Every downstream artifact (results, activation caches, probes, patch
results, analysis outputs) records the release string it was computed
from, and H200 jobs refuse to run if a manifest hash check fails. Treating
this directory as mutable would silently invalidate that provenance chain.

See master spec `01_MASTER_SPEC.md` §3.10 and §7.1 for the manifest schema
and the binding ground rule.
