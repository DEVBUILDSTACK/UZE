"""classify() — determinism, buckets, readiness, and the directive-4
structural guarantee (no LLM in the classifier's dependency set).

Pure unit tests: no database. The manifest is the Sprint 1 seed
(src/seed.py) validated through the GENERATED QuestionManifest —
the same shape the runtime classifies against.
"""

from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE_DIR = os.path.dirname(HERE)
SRC_DIR = os.path.join(COMPOSE_DIR, "src")
GEN_DIR = os.path.join(SRC_DIR, "generated")

from classify import classify  # noqa: E402
from questionmanifest_pydantic import QuestionManifest  # noqa: E402
from seed import SEED_MANIFEST  # noqa: E402


def seed_manifest() -> QuestionManifest:
    return QuestionManifest(
        key=SEED_MANIFEST["key"],
        version=SEED_MANIFEST["version"],
        title=SEED_MANIFEST["title"],
        questions=SEED_MANIFEST["questions"],
    )


def test_classify_is_deterministic():
    manifest = seed_manifest()
    answers = {"event.city": "Miami", "party.seats": 2, "stay.needed": True}
    first = classify(answers, manifest)
    second = classify(answers, manifest)
    assert first == second
    assert first.model_dump_json() == second.model_dump_json()
    # The answers dict's own ordering must not leak into the output.
    shuffled = dict(reversed(list(answers.items())))
    assert classify(shuffled, manifest) == first


def test_classify_buckets_and_branch():
    manifest = seed_manifest()
    result = classify({"stay.needed": False}, manifest)
    assert result.missing == ["event.city", "party.seats"]
    assert result.satisfied == ["stay.needed"]
    assert result.deferred == ["tickets.tier"]
    # The stay branch was never taken: both stay dates are not
    # applicable — neither missing nor deferred.
    assert result.notApplicable == ["stay.checkin", "stay.checkout"]
    assert result.moduleReadiness == {"STAY": "READY", "TICKETS": "NOT_READY"}
    assert result.modules == ["STAY", "TICKETS"]


def test_classify_validation_reasons_are_stable():
    manifest = seed_manifest()
    base = {"event.city": "Miami", "stay.needed": False}
    assert classify({**base, "party.seats": 0}, manifest).invalid == {
        "party.seats": "min"
    }
    assert classify({**base, "party.seats": 99}, manifest).invalid == {
        "party.seats": "max"
    }
    assert classify({**base, "party.seats": "two"}, manifest).invalid == {
        "party.seats": "type"
    }
    # bool is not an INT, whatever Python's isinstance says elsewhere.
    assert classify({**base, "party.seats": True}, manifest).invalid == {
        "party.seats": "type"
    }
    assert classify(
        {**base, "party.seats": 2, "tickets.tier": "gold"}, manifest
    ).invalid == {"tickets.tier": "enum"}
    assert classify(
        {"event.city": "", "party.seats": 2, "stay.needed": False}, manifest
    ).invalid == {"event.city": "minLength"}


def test_readiness_rule_optional_slot_blocks():
    """The filed readiness rule, literally: a gated slot that is
    unanswered and NOT deferrable blocks its module even when it is
    not required; a deferrable one does not."""
    manifest = QuestionManifest(
        key="test.readiness",
        version=1,
        title="Readiness probe",
        questions=[
            {
                "key": "dock.slip",
                "type": "STRING",
                "required": False,
                "deferrable": False,
                "moduleGate": "TRANSFER",
                "promptHuman": "Slip?",
                "promptAgent": "Ask slip.",
            },
            {
                "key": "dock.time",
                "type": "STRING",
                "required": False,
                "deferrable": True,
                "moduleGate": "TRANSFER",
                "promptHuman": "Time?",
                "promptAgent": "Ask time.",
            },
        ],
    )
    result = classify({}, manifest)
    assert result.optional == ["dock.slip"]
    assert result.deferred == ["dock.time"]
    assert result.moduleReadiness == {"TRANSFER": "NOT_READY"}
    answered = classify({"dock.slip": "B-12"}, manifest)
    assert answered.moduleReadiness == {"TRANSFER": "READY"}


def test_classify_module_has_no_llm_in_its_dependency_set():
    """Directive 4, proven structurally: import classify() in a clean
    interpreter and assert neither the suggest seam nor any LLM/HTTP
    client library entered sys.modules."""
    probe = (
        "import sys\n"
        "import classify\n"
        "banned = {'suggest', 'suggest_slots', 'openai', 'anthropic',"
        " 'litellm', 'httpx', 'requests', 'cohere', 'mistralai'}\n"
        "loaded = banned & set(sys.modules)\n"
        "assert not loaded, f'LLM-side modules loaded by classify: {loaded}'\n"
        "print('clean')\n"
    )
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([SRC_DIR, GEN_DIR]))
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert "clean" in proc.stdout
