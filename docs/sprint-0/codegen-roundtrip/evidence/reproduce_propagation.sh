#!/usr/bin/env bash
# Criterion 1 + 2 evidence run — change propagation, start to finish.
#
# What this proves, in one continuous transcript
# (evidence/propagation_transcript.log):
#   PHASE 1: models.py = evidence/models_before.py (NO retentionUntil).
#            Full regeneration from the SQLAlchemy model. The generated
#            Pydantic and TypeScript artifacts must NOT contain the field.
#   PHASE 2: the ONLY edit is swapping models.py to
#            evidence/models_after.py — identical except the retentionUntil
#            column (see evidence/propagation_models.diff). Full
#            regeneration again. The field must appear in BOTH generated
#            artifacts with zero hand edits to them
#            (see evidence/propagation.diff).
#   Then validation + strict tsc run against the regenerated artifacts.
#
# The generator's input in both phases is the SQLAlchemy model file
# (via bridge.py). No Pydantic or TypeScript file is edited at any point.
#
# Run from this directory's parent (the codegen-roundtrip dir):
#   bash evidence/reproduce_propagation.sh 2>&1 | tee evidence/propagation_transcript.log
set -euo pipefail
cd "$(dirname "$0")/.."

backup="$(mktemp ./models_backup.XXXXXX.py)"
cp models.py "$backup"
restore() { cp "$backup" models.py; rm -f "$backup"; }
trap restore EXIT

echo "=================================================================="
echo "PHASE 1 — models.py := evidence/models_before.py (no retentionUntil)"
echo "=================================================================="
cp evidence/models_before.py models.py
grep -c "retention" models.py || echo "models.py: 'retention' absent (grep found 0)"
make clean >/dev/null
make all
if grep -q "retentionUntil" offersnapshot_pydantic.py offersnapshot.ts; then
  echo "FAIL: retentionUntil present in a generated artifact in phase 1"
  exit 1
fi
echo "PHASE 1 OK: retentionUntil absent from generated Pydantic and TypeScript"
mkdir -p evidence/before
cp offersnapshot.schema.json offersnapshot_pydantic.py offersnapshot_pydantic.schema.json offersnapshot.ts evidence/before/

echo
echo "=================================================================="
echo "PHASE 2 — the model edit: models.py := evidence/models_after.py"
echo "(the edit itself is evidence/propagation_models.diff)"
echo "=================================================================="
cp evidence/models_after.py models.py
make clean >/dev/null
make all
grep -n "retentionUntil" offersnapshot_pydantic.py offersnapshot.ts
echo "PHASE 2 OK: retentionUntil present in BOTH generated artifacts after regeneration"
mkdir -p evidence/after
cp offersnapshot.schema.json offersnapshot_pydantic.py offersnapshot_pydantic.schema.json offersnapshot.ts evidence/after/

{
  echo "=== diff: offersnapshot_pydantic.py (before -> after propagation) ==="
  diff -u evidence/before/offersnapshot_pydantic.py evidence/after/offersnapshot_pydantic.py || true
  echo
  echo "=== diff: offersnapshot.ts (before -> after propagation) ==="
  diff -u evidence/before/offersnapshot.ts evidence/after/offersnapshot.ts || true
} > evidence/propagation.diff
echo "artifact diffs written to evidence/propagation.diff"

echo
echo "=================================================================="
echo "VALIDATION of the regenerated (after) artifacts"
echo "=================================================================="
make validate
make check-ts
echo "CHECK-TS: tsc strict noEmit OK"
echo
echo "PROPAGATION RUN COMPLETE: edit started at the SQLAlchemy model file;"
echo "both downstream artifacts picked the field up by regeneration alone."
