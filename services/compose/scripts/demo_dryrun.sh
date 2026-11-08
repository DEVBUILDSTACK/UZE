#!/usr/bin/env bash
# Integrated demo dry run — Sprint 1.5 step-4 rehearsal.
#
# Walks DEMO-SCRIPT.md beat by beat against the real stack (compose
# API with the NEAR chain gate OPEN + the Next.js human surface +
# the migrated demo database), asserting what each beat must show
# in the system's current honest state:
#   - agent bid carries inference status "unavailable" until the
#     NEARAI_API_KEY lands (never a fabricated attestation);
#   - settle rests at SELECTED + "signed" until the payer address
#     is funded (fully built + MPC-signed, broadcast held);
#   - the pulse comparable count moves only when a settle lands;
#   - Beat 7 exercises the evidence gate end to end: the Track A
#     webhook enters at INPUT_VALIDATED, the mock Effatha adapter
#     returns PROVIDER_PROPOSAL_RECEIVED, the referral rests at
#     FARMER_APPROVAL_PENDING, and only an explicit entity consent
#     record advances it to SERVICE_AUTHORIZED.
# When funding + key arrive, the same walk shows SETTLED and the
# attested analysis with no script changes.
#
#   bash scripts/demo_dryrun.sh
set -u
cd "$(dirname "$0")/.."
VENV=~/workspace/tools/composevenv/bin/python
export COMPOSE_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55433/uzemarkets-compose
export PYTHONPATH=src:src/generated
export AGTECH_WEBHOOK_SECRET=demo-webhook-secret

cleanup() {
  [ -f /tmp/demo-api.pid ] && kill "$(cat /tmp/demo-api.pid)" 2>/dev/null
  [ -f /tmp/demo-web.pid ] && kill "$(cat /tmp/demo-web.pid)" 2>/dev/null
  # npm/next children can outlive their launcher — clear the ports.
  fuser -k 3000/tcp 8100/tcp 2>/dev/null
}
trap cleanup EXIT
# Clear any stale listeners from earlier runs before binding ours.
fuser -k 3000/tcp 8100/tcp 2>/dev/null; sleep 1

echo "== reset + migrate + seed micro-regions =="
$VENV - <<'PY'
import sys
sys.path.insert(0, "scripts")
from metering_dryrun import reset_db
reset_db()
import json
import db, models
fixture = json.load(open("scripts/fixtures/sprint15_demo.json"))
s = db.session()
for row in fixture["microRegions"]:
    s.add(models.MicroRegion(id=row["id"], label=row["label"],
                             metro=row["metro"], region=row["region"]))
s.commit(); s.close()
print("regions seeded")
PY

COMPOSE_NEAR_CHAIN=1 $VENV -m uvicorn app:app --port 8100 >/tmp/demo-api.log 2>&1 &
echo $! > /tmp/demo-api.pid
(cd ../.. && cd apps/uze-web && NEXT_PUBLIC_BASE_URL=http://localhost:3000 npm run start >/tmp/demo-web.log 2>&1) &
echo $! > /tmp/demo-web.pid
for i in $(seq 1 30); do
  curl -s -o /dev/null http://127.0.0.1:8100/health && curl -s -o /dev/null http://localhost:3000/ && break
  sleep 1
done

API=http://127.0.0.1:8100/api/v1
WEB=http://localhost:3000

echo "== Beat 1: micro-regions index renders =="
curl -s $WEB/micro-regions | grep -q "Miami — Brickell" && echo "OK  regions page lists Brickell"

echo "== Beat 2: spec posted (Track H, radius) — page + JSON-LD =="
SPEC_JSON=$(curl -s -X POST $API/specs -H 'Content-Type: application/json' -d @scripts/fixtures/demo-spec.json)
SPEC_ID=$(echo "$SPEC_JSON" | jq -r .id)
echo "spec $SPEC_ID chain: $(echo "$SPEC_JSON" | jq -c .chain)"
curl -s $WEB/specs/$SPEC_ID | sed 's/<!-- -->//g' > /tmp/demo-spec-page.html
for s in "Aloft" "340 doors" '"@type":"Demand"' "H — Hospitality" "Radius 37.5 mi"; do
  grep -q "$s" /tmp/demo-spec-page.html && echo "OK  spec page: $s" || echo "MISS spec page: $s"
done
curl -s $API/specs/$SPEC_ID | jq -e '.assetSubclass == "H" and .targetArea.type == "Radius"' >/dev/null && echo "OK  agent JSON carries HIADR fields"

echo "== Beat 3: bids — human vs agent, inference state honest =="
curl -s -X POST $API/bids -H 'Content-Type: application/json' -d "$(jq --arg id "$SPEC_ID" '. + {intentId: $id}' scripts/fixtures/demo-bid-human.json)" >/dev/null
AGENT_BID=$(curl -s -X POST $API/bids -H 'Content-Type: application/json' -d "$(jq --arg id "$SPEC_ID" '. + {intentId: $id}' scripts/fixtures/demo-bid-agent.json)")
AGENT_BID_ID=$(echo "$AGENT_BID" | jq -r .id)
echo "agent bid inference: $(echo "$AGENT_BID" | jq -c .payload.inference)"
curl -s $API/specs/$SPEC_ID/bids | jq -e 'length == 2' >/dev/null && echo "OK  two bids on the spec"

echo "== Beat 4-5: settle — rests SELECTED + signed until funded =="
SETTLE=$(curl -s -X POST $API/settle -H 'Content-Type: application/json' -d "{\"intentId\": \"$SPEC_ID\", \"bidId\": \"$AGENT_BID_ID\"}")
echo "settle: spec=$(echo "$SETTLE" | jq -r .spec.status) match=$(echo "$SETTLE" | jq -r .match.state) settlement=$(echo "$SETTLE" | jq -c .settlement)"

echo "== Beat 6: pulse — Dataset JSON on the API and in the page =="
curl -s $API/micro-regions/miami-brickell/pulse | jq -c '{type: .["@type"], measured: .variableMeasured, action: .agent_action}'
curl -s $WEB/micro-regions/miami-brickell | sed 's/<!-- -->//g' > /tmp/demo-region-page.html
for s in '"@type":"Dataset"' '"agent_action":"POST /api/v1/specs to initiate underwriting"' "Pulse — the Content Desk dataset" "Specs posted"; do
  grep -q "$s" /tmp/demo-region-page.html && echo "OK  region page: $s" || echo "MISS region page: $s"
done

echo "== talent page =="
curl -s $WEB/talent/recon.uzemarkets-talent.testnet | grep -q "4,200 USDC" && echo "OK  agent talent page renders its bid"

echo "== Beat 7: evidence gate — Track A approval (webhook → mock proposal → consent) =="
GATE_HOOK=$(curl -s -X POST $API/webhooks/agriculture/intent -H 'Content-Type: application/json' -H "X-Webhook-Secret: $AGTECH_WEBHOOK_SECRET" -H 'Idempotency-Key: demo-gate-001' -d '{"schema_version":"1.0","track":"A","transaction_type":"agtech_referral","crop_type":"CORN","production_purpose":"SILAGE","provider_preference":"EFFATHA","country_code":"PY","macro_driver":"fiat_collapse","polygon":{"type":"Polygon","coordinates":[[[-57.6,-25.3],[-57.5,-25.3],[-57.5,-25.2],[-57.6,-25.3]]]}}')
REFERRAL_ID=$(echo "$GATE_HOOK" | jq -r .id)
echo "webhook: state=$(echo "$GATE_HOOK" | jq -r .state) referral=$REFERRAL_ID macroDistressExit=$(echo "$GATE_HOOK" | jq -r .macroDistressExit)"
ENTITY_ID=$(jq -r .entityId scripts/fixtures/demo-spec.json)
REFERRAL_ID="$REFERRAL_ID" ENTITY_ID="$ENTITY_ID" $VENV - <<'PY' > /tmp/demo-gate.log 2>&1
import os
import db, models
from agtech_workflow import (
    authorize_service,
    check_provider_eligibility,
    complete_spatial_assessment,
    request_provider_proposal,
    request_spatial_assessment,
)

s = db.session()
ref = s.query(models.AgReferral).filter_by(id=os.environ["REFERRAL_ID"]).one()
assert ref.state is models.AgReferralState.INPUT_VALIDATED, ref.state

assessment = request_spatial_assessment(s, ref)
s.commit()
print(f"spatial: state={ref.state.value} assessment={assessment.status} (mock adapter, pending)")

complete_spatial_assessment(
    s, ref, assessment,
    registry_matches=[{"registry": "CAR", "matchId": "mock-car-demo"}],
    confidence_score=0.81,
    actor="demo:spatial-reviewer",
)
s.commit()
print(f"spatial completed: state={ref.state.value} ownership_established={assessment.ownership_established}")

eligibility = check_provider_eligibility(s, ref)
s.commit()
print(f"eligibility: adapter_status={eligibility.status} state={ref.state.value}")

proposal = request_provider_proposal(s, ref)
s.commit()
print(f"proposal: status={proposal.status} state={ref.state.value} execution_authorized={proposal.execution_authorized}")
assert proposal.status == "PROVIDER_PROPOSAL_RECEIVED"
assert ref.state is models.AgReferralState.FARMER_APPROVAL_PENDING, ref.state

consent = f"consent:{os.environ['ENTITY_ID']}:farmer-approval-demo-001"
authorize_service(s, ref, actor="demo:farmer-entity", consent_record_id=consent)
s.commit()
print(f"consent: record={consent} -> state={ref.state.value}")
assert ref.state is models.AgReferralState.SERVICE_AUTHORIZED, ref.state
s.close()
print("GATE_OK")
PY
cat /tmp/demo-gate.log
grep -q GATE_OK /tmp/demo-gate.log && echo "OK  approval gate: PROVIDER_PROPOSAL_RECEIVED → FARMER_APPROVAL_PENDING → entity consent → SERVICE_AUTHORIZED" || echo "MISS approval gate (see /tmp/demo-gate.log)"

echo "DEMO DRY RUN COMPLETE — outcomes as printed (current honest state)."
