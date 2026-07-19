from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "69bdac5bbad9c41f3ae1bd769a83faa699ead950"

MODIFIED_FILES = {
    "docs/r02-overlay-v2-headroom-and-power-design.json",
    "docs/r02-overlay-v2-preregistration-draft.json",
    "docs/r02-overlay-v2-preregistration-review-handoff.md",
    "docs/r02-overlay-v2-zero-call-manifest.json",
}
NEW_FILES = {
    "docs/r02-overlay-v2-implementation-plan.json",
    "docs/r02-overlay-v2-implementation-plan.md",
    "docs/r02-overlay-v2-implementation-plan-review-handoff.md",
    "docs/r02-overlay-v2-implementation-plan-zero-call-manifest.json",
    "scripts/r02_overlay_v2_implementation_plan_verify.py",
}
EXPECTED_CHANGED_FILES = MODIFIED_FILES | NEW_FILES

PLAN_JSON = "docs/r02-overlay-v2-implementation-plan.json"
PLAN_MD = "docs/r02-overlay-v2-implementation-plan.md"
PLAN_REVIEW = "docs/r02-overlay-v2-implementation-plan-review-handoff.md"
PLAN_ZERO = "docs/r02-overlay-v2-implementation-plan-zero-call-manifest.json"
DESIGN_JSON = "docs/r02-overlay-v2-headroom-and-power-design.json"
PREREG_JSON = "docs/r02-overlay-v2-preregistration-draft.json"
OLD_ZERO = "docs/r02-overlay-v2-zero-call-manifest.json"

CANONICAL_JSON_PATHS = (
    DESIGN_JSON,
    PREREG_JSON,
    OLD_ZERO,
    PLAN_JSON,
    PLAN_ZERO,
)


class ImplementationPlanVerificationError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def load_canonical_json(relative_path: str) -> dict[str, Any]:
    blob = (ROOT / relative_path).read_bytes()
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImplementationPlanVerificationError(
            f"invalid JSON: {relative_path}"
        ) from exc
    if not isinstance(value, dict) or blob != canonical_bytes(value):
        raise ImplementationPlanVerificationError(
            f"noncanonical JSON: {relative_path}"
        )
    return value


def sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip()


def require_repository_state() -> None:
    head = git("rev-parse", "HEAD")
    status = {
        line[3:].replace("\\", "/"): line[:2]
        for line in git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line
    }
    expected_status = {
        **{path: " M" for path in MODIFIED_FILES},
        **{path: "??" for path in NEW_FILES},
    }
    if head == BASE_COMMIT and status == expected_status:
        return
    if status:
        raise ImplementationPlanVerificationError(
            "repository is neither exact plan-draft state nor clean"
        )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    changed = set(
        line
        for line in git(
            "diff", "--name-only", f"{BASE_COMMIT}..{head}"
        ).splitlines()
        if line
    )
    if changed != EXPECTED_CHANGED_FILES:
        raise ImplementationPlanVerificationError(
            "clean descendant does not contain exact plan change set"
        )


def require_authorization_boundary(plan: dict[str, Any]) -> None:
    if plan["authorization"] != {
        "commit": True,
        "confirmatory_live": False,
        "fixture_materialization": False,
        "implementation": False,
        "pilot_live": False,
        "provider_calls": 0,
        "push": True,
        "replacement": 0,
        "resume": 0,
        "retry": 0,
    }:
        raise ImplementationPlanVerificationError(
            "implementation-plan authorization drift"
        )
    if plan["information_boundary"]["provider_capability_absent"] is not True:
        raise ImplementationPlanVerificationError(
            "provider capability is not absent"
        )


def require_plan_values(
    plan: dict[str, Any],
    design: dict[str, Any],
    prereg: dict[str, Any],
) -> None:
    if plan["base_commit"] != BASE_COMMIT:
        raise ImplementationPlanVerificationError("plan base commit drift")
    if plan["status"] != (
        "TECHNICALLY_ACCEPTED_IMPLEMENTATION_PLAN_"
        "IMPLEMENTATION_NOT_AUTHORIZED_LIVE_NO_GO"
    ):
        raise ImplementationPlanVerificationError("plan status drift")
    if plan["technical_acceptance"] != {
        "accepted": True,
        "accepted_date": "2026-07-19",
        "accepted_pre_promotion_review_handoff_sha256": (
            "9d9440d8e0b53a3734b963657a6d9e33b9defd2d97cecf32879165c6e8a0b830"
        ),
        "authorized_actions": [
            "COMMIT_EXACT_NINE_PLAN_FILES",
            "PUSH_EXACT_NINE_PLAN_FILES",
        ],
        "blocking_findings_open": 0,
        "informational_findings": 2,
        "implementation_obligations": [
            "ADD_JSONSCHEMA_DEV_DEPENDENCY_FOR_I0_METASCHEMA_GATE",
            "INCLUDE_THIRTEEN_GATE_TO_TEST_TRACEABILITY_TABLE",
        ],
        "organizational_independence_established": False,
        "review_relationship": "SAME_SESSION_LINEAGE_TECHNICAL_VERIFICATION",
        "reviewer": "Claude (Fable 5)",
        "unauthorized_actions": [
            "IMPLEMENTATION_I0_TO_I5",
            "FIXTURE_MATERIALIZATION",
            "PROVIDER_CALLS",
            "PRIVATE_DATA_EXPORT",
            "PILOT_LIVE",
            "CONFIRMATORY_LIVE",
            "RETRY",
            "REPLACEMENT",
            "RESUME",
        ],
    }:
        raise ImplementationPlanVerificationError(
            "technical acceptance record drift"
        )
    normalization = plan["status_normalization"]
    if normalization != {
        "new_analysis_status": (
            "TECHNICALLY_ACCEPTED_PROVIDER_FREE_IMPLEMENTATION_PLANNING_INPUT"
        ),
        "prior_analysis_status": "DRAFT_PROVIDER_FREE_REVIEW_REQUIRED",
        "scientific_values_changed": False,
    }:
        raise ImplementationPlanVerificationError(
            "status normalization drift"
        )
    if design["analysis_status"] != normalization["new_analysis_status"]:
        raise ImplementationPlanVerificationError(
            "headroom analysis status not normalized"
        )
    if (
        prereg["component_pins"]["headroom_and_power_design_sha256"]
        != sha256_file(DESIGN_JSON)
    ):
        raise ImplementationPlanVerificationError(
            "preregistration headroom pin drift"
        )
    if len(plan["future_modules"]) != 8:
        raise ImplementationPlanVerificationError("future module count drift")
    if any("provider" in path or "transport" in path for path in plan["future_modules"]):
        raise ImplementationPlanVerificationError(
            "provider-capable future module declared"
        )
    if len(plan["ordered_phases"]) != 6:
        raise ImplementationPlanVerificationError("phase count drift")
    if len(plan["test_gates"]) != 13:
        raise ImplementationPlanVerificationError("test gate count drift")
    boundary = plan["information_boundary"]
    if not (
        boundary["byte_identical_payload_required"]
        and boundary["deterministic_extra_reads_forbidden"]
        and boundary["hidden_oracle_after_sealed_selection_only"]
    ):
        raise ImplementationPlanVerificationError(
            "information boundary weakened"
        )
    prohibited = set(boundary["prohibited_policy_fields"])
    if not {
        "fixture_id",
        "seed",
        "split_label",
        "hidden.regime",
        "hidden.expected_returns_bps",
        "oracle_score",
    }.issubset(prohibited):
        raise ImplementationPlanVerificationError(
            "forbidden policy fields missing"
        )


def require_status_only_normalization(
    design: dict[str, Any],
    prereg: dict[str, Any],
) -> None:
    base_design = json.loads(
        git("show", f"{BASE_COMMIT}:{DESIGN_JSON}")
    )
    if base_design.get("analysis_status") != (
        "DRAFT_PROVIDER_FREE_REVIEW_REQUIRED"
    ):
        raise ImplementationPlanVerificationError(
            "historical headroom status anchor drift"
        )
    current_design = copy.deepcopy(design)
    current_design["analysis_status"] = base_design["analysis_status"]
    if current_design != base_design:
        raise ImplementationPlanVerificationError(
            "headroom scientific values changed during status normalization"
        )

    base_prereg = json.loads(
        git("show", f"{BASE_COMMIT}:{PREREG_JSON}")
    )
    current_prereg = copy.deepcopy(prereg)
    current_prereg["component_pins"][
        "headroom_and_power_design_sha256"
    ] = base_prereg["component_pins"][
        "headroom_and_power_design_sha256"
    ]
    if current_prereg != base_prereg:
        raise ImplementationPlanVerificationError(
            "preregistration changed beyond the dependent headroom pin"
        )


def require_manifest_statuses(
    old_zero: dict[str, Any],
    plan_zero: dict[str, Any],
) -> None:
    if old_zero["status"] != (
        "PREREGISTRATION_TECHNICALLY_ACCEPTED_"
        "IMPLEMENTATION_PLAN_ACCEPTED_PROVIDER_FREE"
    ):
        raise ImplementationPlanVerificationError(
            "preregistration zero-call status drift"
        )
    if old_zero["implementation_plan"] != {
        "accepted": True,
        "accepted_pre_promotion_review_handoff_sha256": (
            "9d9440d8e0b53a3734b963657a6d9e33b9defd2d97cecf32879165c6e8a0b830"
        ),
        "base_commit": BASE_COMMIT,
        "commit_authorized": True,
        "drafting_authorized": True,
        "implementation_authorized": False,
        "organizational_independence_established": False,
        "provider_calls_authorized": 0,
        "push_authorized": True,
        "review_pending": False,
        "status_normalization_only_scientific_values_changed": False,
    }:
        raise ImplementationPlanVerificationError(
            "implementation-planning boundary drift"
        )
    if plan_zero["status"] != (
        "IMPLEMENTATION_PLAN_TECHNICALLY_ACCEPTED_PROVIDER_FREE_"
        "COMMIT_PUSH_AUTHORIZED"
    ):
        raise ImplementationPlanVerificationError(
            "implementation-plan zero-call status drift"
        )
    if not plan_zero["commit_authorized"] or not plan_zero["push_authorized"]:
        raise ImplementationPlanVerificationError(
            "plan commit or push capability drift"
        )
    if (
        plan_zero["commit_created_at_manifest_seal"]
        or plan_zero["push_performed_at_manifest_seal"]
    ):
        raise ImplementationPlanVerificationError(
            "plan zero-call seal timing drift"
        )
    if plan_zero["technical_acceptance"] != {
        "accepted": True,
        "accepted_pre_promotion_review_handoff_sha256": (
            "9d9440d8e0b53a3734b963657a6d9e33b9defd2d97cecf32879165c6e8a0b830"
        ),
        "blocking_findings_open": 0,
        "informational_findings": 2,
        "organizational_independence_established": False,
        "review_relationship": "SAME_SESSION_LINEAGE_TECHNICAL_VERIFICATION",
        "reviewer": "Claude (Fable 5)",
    }:
        raise ImplementationPlanVerificationError(
            "plan zero-call acceptance drift"
        )
    if len(plan_zero["negative_tests"]) != 7:
        raise ImplementationPlanVerificationError(
            "negative-test declaration drift"
        )


def require_manifest_pins(
    manifest: dict[str, Any],
    *,
    allow_review_absence: bool,
) -> None:
    for relative_path, expected_sha in manifest["artifact_sha256"].items():
        if allow_review_absence and relative_path == PLAN_REVIEW:
            continue
        if sha256_file(relative_path) != expected_sha:
            raise ImplementationPlanVerificationError(
                f"artifact pin drift: {relative_path}"
            )
    counters = (
        "provider_calls",
        "live_runs",
        "pilot_live_runs",
        "confirmatory_live_runs",
        "fixture_roots_materialized",
        "implementation_files_created",
        "codex_exec_invocations",
        "retry_count",
        "replacement_count",
        "resume_count",
    )
    if any(manifest[key] != 0 for key in counters):
        raise ImplementationPlanVerificationError(
            "zero-call counter drift"
        )


def require_review_pins(plan_zero: dict[str, Any]) -> None:
    review = (ROOT / PLAN_REVIEW).read_text(encoding="utf-8")
    required = {
        **plan_zero["artifact_sha256"],
        PLAN_ZERO: sha256_file(PLAN_ZERO),
    }
    for relative_path, expected_sha in required.items():
        if relative_path not in review or expected_sha not in review:
            raise ImplementationPlanVerificationError(
                f"review pin missing: {relative_path}"
            )


def assert_raises(
    expected: type[BaseException],
    function: Callable[[], Any],
) -> None:
    try:
        function()
    except expected:
        return
    except Exception as exc:
        raise AssertionError(
            f"unexpected exception: {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {expected.__name__}")


def negative_tests(
    plan: dict[str, Any],
    design: dict[str, Any],
    prereg: dict[str, Any],
    plan_zero: dict[str, Any],
) -> int:
    bad_auth = copy.deepcopy(plan)
    bad_auth["authorization"]["implementation"] = True
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_authorization_boundary(bad_auth),
    )
    bad_provider = copy.deepcopy(plan)
    bad_provider["information_boundary"]["provider_capability_absent"] = False
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_authorization_boundary(bad_provider),
    )
    bad_hidden = copy.deepcopy(plan)
    bad_hidden["information_boundary"]["prohibited_policy_fields"].remove(
        "hidden.expected_returns_bps"
    )
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_plan_values(bad_hidden, design, prereg),
    )
    bad_parity = copy.deepcopy(plan)
    bad_parity["information_boundary"]["byte_identical_payload_required"] = False
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_plan_values(bad_parity, design, prereg),
    )
    bad_module = copy.deepcopy(plan)
    bad_module["future_modules"][0] = (
        "v2/research/overlay/r02_v2_provider_transport.py"
    )
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_plan_values(bad_module, design, prereg),
    )
    bad_status = copy.deepcopy(design)
    bad_status["analysis_status"] = "DRAFT_PROVIDER_FREE_REVIEW_REQUIRED"
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_plan_values(plan, bad_status, prereg),
    )
    bad_zero = copy.deepcopy(plan_zero)
    bad_zero["provider_calls"] = 1
    assert_raises(
        ImplementationPlanVerificationError,
        lambda: require_manifest_pins(
            bad_zero,
            allow_review_absence=False,
        ),
    )
    return 7


def main() -> int:
    require_repository_state()
    loaded = {
        path: load_canonical_json(path)
        for path in CANONICAL_JSON_PATHS
    }
    design = loaded[DESIGN_JSON]
    prereg = loaded[PREREG_JSON]
    old_zero = loaded[OLD_ZERO]
    plan = loaded[PLAN_JSON]
    plan_zero = loaded[PLAN_ZERO]
    require_authorization_boundary(plan)
    require_plan_values(plan, design, prereg)
    require_status_only_normalization(design, prereg)
    require_manifest_statuses(old_zero, plan_zero)
    require_manifest_pins(old_zero, allow_review_absence=False)
    require_manifest_pins(plan_zero, allow_review_absence=False)
    require_review_pins(plan_zero)
    count = negative_tests(plan, design, prereg, plan_zero)
    print(
        "PASS_R02_OVERLAY_V2_PROVIDER_FREE_IMPLEMENTATION_PLAN "
        f"negative_tests={count} provider_calls=0 live_runs=0 "
        "implementation_files=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
