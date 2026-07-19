"""Provider-free verifier for the R02 overlay v2 preregistration drafts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "6774e846652afe81981928a1b2d9755c1a0d9221"
FIELD_REF_PATTERN = r"^/(public_context|candidates)(?:/(?:[^~/]|~0|~1)*)+$"

EXPECTED_DRAFT_FILES = (
    "docs/r02-overlay-v2-d3-d4-scope-annotation.md",
    "docs/r02-overlay-v2-deterministic-comparator-design.md",
    "docs/r02-overlay-v2-headroom-and-power-design.json",
    "docs/r02-overlay-v2-payload-schema-draft.json",
    "docs/r02-overlay-v2-preregistration-draft.json",
    "docs/r02-overlay-v2-preregistration-draft.md",
    "docs/r02-overlay-v2-preregistration-review-handoff.md",
    "docs/r02-overlay-v2-response-schema-draft.json",
    "docs/r02-overlay-v2-zero-call-manifest.json",
    "scripts/r02_overlay_v2_preregistration_verify.py",
)

SOURCE_PINS = {
    "docs/r02-d3-preregistration.json": "5e07d88e98e74f67a1377020ca8c19c6fada51756ebddd902706a1680eeb27d4",
    "docs/r02-d4-s3-statistical-freeze.json": "3538c09ffedd95f946a448ae298e04cad1cf933a99ff767b58472c4285c6b449",
    "docs/r02-d4-live-posthoc-independent-review.json": "efc668d817f2b344568ad549550d2dadaa8aa918c6180d5cb6ca753eabd80496",
    "docs/r02-d4-live-posthoc.json": "623b8888a90af34bf7f0be20cf45ff19691e8c1545de76d00534102643b71042",
    "docs/r02-overlay-v2-preregistration-design-handoff.md": "e889e954bc6841e5cccedcb212d48f401b78818bd3929dc6010989c35ac0baa8",
    "v2/research/overlay/baselines.py": "6f490aa3458856213c7cd6a859065d49d6383de00416ab523a52f2f4f5bc412f",
    "v2/research/overlay/r02_contracts.py": "64a099560432152da875843d6cddb4d08acd3a402198adb14a5aec65ef0dab05",
    "v2/research/overlay/r02_candidates.py": "29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e",
    "v2/research/overlay/r02_d4_design.py": "56cfb806c79baa768524c76c655907bc55934d421c0566740ee0f9c75e9ea4d6",
    "v2/research/overlay/r02_selector.py": "a90cc600ffc772c5fb4b1c964b5efc0a551de84a41eaa5c0a030b6d02b9b20f9",
    "v2/research/overlay/scoring.py": "c86b7ee61a0cc7a92557adda6826ab9f75e411f3bda9ec0219c5c1d6c96d8aff",
}

COMPONENT_PATHS = {
    "controlling_handoff_sha256": "docs/r02-overlay-v2-preregistration-design-handoff.md",
    "deterministic_comparator_design_sha256": "docs/r02-overlay-v2-deterministic-comparator-design.md",
    "headroom_and_power_design_sha256": "docs/r02-overlay-v2-headroom-and-power-design.json",
    "payload_schema_draft_sha256": "docs/r02-overlay-v2-payload-schema-draft.json",
    "response_schema_draft_sha256": "docs/r02-overlay-v2-response-schema-draft.json",
    "scope_annotation_sha256": "docs/r02-overlay-v2-d3-d4-scope-annotation.md",
}

JSON_PATHS = (
    "docs/r02-overlay-v2-headroom-and-power-design.json",
    "docs/r02-overlay-v2-payload-schema-draft.json",
    "docs/r02-overlay-v2-preregistration-draft.json",
    "docs/r02-overlay-v2-response-schema-draft.json",
    "docs/r02-overlay-v2-zero-call-manifest.json",
)


class DraftVerificationError(RuntimeError):
    pass


def sha256_file(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def require_canonical_blob(blob: bytes) -> dict[str, Any]:
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DraftVerificationError("invalid JSON bytes") from exc
    if not isinstance(value, dict):
        raise DraftVerificationError("JSON root is not an object")
    if blob != canonical_bytes(value):
        raise DraftVerificationError("noncanonical JSON bytes")
    return value


def load_canonical_json(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    try:
        return require_canonical_blob(path.read_bytes())
    except DraftVerificationError as exc:
        raise DraftVerificationError(f"invalid canonical JSON: {relative_path}") from exc


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def require_repository_state() -> None:
    head = git("rev-parse", "HEAD")
    status = tuple(line for line in git("status", "--porcelain").splitlines() if line)
    expected_untracked = tuple(f"?? {path}" for path in EXPECTED_DRAFT_FILES)
    if head == BASE_COMMIT and status == expected_untracked:
        return
    if status:
        raise DraftVerificationError("worktree is neither exact draft-untracked state nor clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    changed = tuple(
        line
        for line in git("diff", "--name-only", f"{BASE_COMMIT}..{head}").splitlines()
        if line
    )
    if changed != EXPECTED_DRAFT_FILES:
        raise DraftVerificationError("clean descendant does not contain exactly the draft files")


def require_local_schema_refs(schema: dict[str, Any]) -> None:
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        raise DraftVerificationError("schema lacks $defs")

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            reference = value.get("$ref")
            if reference is not None:
                if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
                    raise DraftVerificationError("schema contains nonlocal or invalid $ref")
                key = reference.removeprefix("#/$defs/")
                if key not in definitions:
                    raise DraftVerificationError(f"schema contains unresolved $ref: {reference}")
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(schema)


def verify_values(
    prereg: dict[str, Any],
    payload: dict[str, Any],
    response: dict[str, Any],
    design: dict[str, Any],
    zero: dict[str, Any],
) -> None:
    if prereg["base_commit"] != BASE_COMMIT:
        raise DraftVerificationError("base commit drift")
    authorization = prereg["authorization"]
    if authorization != {
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
        raise DraftVerificationError("draft authorization boundary drift")
    if prereg["status"] != (
        "TECHNICALLY_ACCEPTED_DRAFT_IMPLEMENTATION_NOT_AUTHORIZED_LIVE_NO_GO"
    ):
        raise DraftVerificationError("technical acceptance status drift")
    acceptance = prereg["technical_acceptance"]
    if acceptance != {
        "accepted": True,
        "accepted_date": "2026-07-19",
        "accepted_pre_promotion_review_handoff_sha256": (
            "b1782221e1463962b9179f0218ab4bac9971de867b349ce717598ff75d5ac52d"
        ),
        "authorized_actions": [
            "COMMIT_EXACT_TEN_DRAFT_FILES",
            "PUSH_EXACT_TEN_DRAFT_FILES",
        ],
        "blocking_findings_open": 0,
        "nonblocking_findings_closed": 3,
        "organizational_independence_established": False,
        "review_relationship": "SAME_SESSION_LINEAGE_TECHNICAL_VERIFICATION",
        "reviewer": "Claude (Fable 5)",
        "unauthorized_actions": [
            "IMPLEMENTATION",
            "FIXTURE_MATERIALIZATION",
            "PROVIDER_CALLS",
            "PILOT_LIVE",
            "CONFIRMATORY_LIVE",
            "RETRY",
            "REPLACEMENT",
            "RESUME",
        ],
    }:
        raise DraftVerificationError("technical acceptance record drift")
    if not prereg["information_parity"]["byte_identical_payload_required"]:
        raise DraftVerificationError("information parity is not required")
    population = prereg["candidate_population"]
    if population["trigger"] != "BASELINE_HAS_TRADE_AND_MAX_TRADED_EFFECTIVE_COST_BPS_GE_50":
        raise DraftVerificationError("candidate trigger drift")
    if population["trigger_change_authorized"] or population["generator_change_authorized"]:
        raise DraftVerificationError("candidate population mutation authorized")
    if population["nontrigger_full_frame_itt_e12"] != 0:
        raise DraftVerificationError("nontrigger ITT drift")
    excluded = set(prereg["information_parity"]["excluded_fields"])
    if not {"hidden.regime", "hidden.expected_returns_bps"}.issubset(excluded):
        raise DraftVerificationError("hidden oracle fields are not excluded")
    if payload["x_contract"]["information_parity"] != (
        "BYTE_IDENTICAL_PAYLOAD_FOR_DETERMINISTIC_SCORER_AND_LLM_V2"
    ):
        raise DraftVerificationError("payload information-parity contract drift")
    if response["x_contract"]["grounding_failure_endpoint"] != (
        "INVALID_OR_WRONG_SCOPE_FIELD_REFERENCE"
    ):
        raise DraftVerificationError("grounding endpoint drift")
    field_ref_items = response["$defs"]["reason"]["properties"]["field_refs"]["items"]
    if field_ref_items.get("maxLength") != 256 or field_ref_items.get("pattern") != FIELD_REF_PATTERN:
        raise DraftVerificationError("RFC 6901 field-reference contract drift")

    pilot = design["blinded_pilot"]
    if sum(pilot["initial_candidate_stratum_counts"].values()) != pilot[
        "initial_candidate_pilot_n"
    ]:
        raise DraftVerificationError("pilot stratum arithmetic drift")
    if sum(pilot["minimum_valid_settled_by_stratum"].values()) != pilot[
        "minimum_valid_settled_count"
    ]:
        raise DraftVerificationError("pilot valid-settled stratum arithmetic drift")
    budget = pilot["candidate_budget"]
    if budget["external_provider_call_cap"] != pilot["initial_candidate_pilot_n"]:
        raise DraftVerificationError("pilot call cap drift")
    if budget["per_attempt_token_reserve"] * budget["external_provider_call_cap"] != budget[
        "total_token_cap"
    ]:
        raise DraftVerificationError("pilot token budget arithmetic drift")
    if any(budget[key] != 0 for key in ("retry_count", "replacement_count", "resume_count")):
        raise DraftVerificationError("pilot repeat capability drift")
    if pilot["provider_calls_authorized"] or not pilot["utility_blind"]:
        raise DraftVerificationError("pilot authorization or blinding drift")
    confirmatory = design["confirmatory_design"]
    if confirmatory["minimum_representative_n"] + confirmatory[
        "minimum_challenge_n"
    ] != confirmatory["minimum_total_n"]:
        raise DraftVerificationError("confirmatory minimum sample arithmetic drift")
    if design["headroom_gate"]["provider_calls"] != 0:
        raise DraftVerificationError("headroom gate is not provider-free")
    sensitivity = design["power"]["sensitivity_grid"]
    if not sensitivity["grid_pruning_from_pilot_utility_forbidden"]:
        raise DraftVerificationError("pilot utility may prune the power grid")
    if sensitivity["go_no_go_rule"] != (
        "EVERY_INCLUDED_GRID_CELL_MUST_REACH_POWER_800000_PPM_WITH_REQUIRED_N_NO_GREATER_THAN_400_AND_THE_LEAST_POWERED_CELL_GOVERNS"
    ):
        raise DraftVerificationError("power sensitivity governing rule drift")
    included_cells = [
        (rate, mean)
        for rate in sensitivity["discordance_rate_ppm"]
        for mean in sensitivity["conditional_incremental_mean_e12"]
        if rate * mean // 1_000_000 >= 50_000_000
    ]
    if not included_cells or min(rate * mean // 1_000_000 for rate, mean in included_cells) != 50_000_000:
        raise DraftVerificationError("power sensitivity cell inclusion drift")
    operating = pilot["operating_characteristics"]
    if operating["no_go_probability_ppm"] != 828_676:
        raise DraftVerificationError("pilot no-go operating characteristic drift")
    if operating["two_stage_or_pilot_size_adaptation_authorized"]:
        raise DraftVerificationError("pilot adaptation capability drift")
    if zero["provider_calls"] != 0 or zero["live_runs"] != 0:
        raise DraftVerificationError("zero-call manifest drift")


def verify_component_pins(prereg: dict[str, Any]) -> None:
    for key, relative_path in COMPONENT_PATHS.items():
        if prereg["component_pins"].get(key) != sha256_file(relative_path):
            raise DraftVerificationError(f"component pin drift: {key}")


def verify_zero_manifest(zero: dict[str, Any]) -> None:
    for relative_path, expected_sha in zero["artifact_sha256"].items():
        if relative_path == "scripts/r02_overlay_v2_preregistration_verify.py":
            continue
        if sha256_file(relative_path) != expected_sha:
            raise DraftVerificationError(f"zero-call artifact pin drift: {relative_path}")
    if zero["source_sha256"] != SOURCE_PINS:
        raise DraftVerificationError("zero-call source pin map drift")
    if zero["status"] != (
        "DRAFTS_TECHNICALLY_ACCEPTED_PROVIDER_FREE_COMMIT_PUSH_AUTHORIZED"
    ):
        raise DraftVerificationError("zero-call acceptance status drift")
    if not zero["commit_authorized"] or not zero["push_authorized"]:
        raise DraftVerificationError("zero-call commit/push authorization drift")
    if zero["commit_created_at_manifest_seal"] or zero["push_performed_at_manifest_seal"]:
        raise DraftVerificationError("zero-call manifest seal timing drift")
    if zero["technical_acceptance"] != {
        "accepted": True,
        "accepted_pre_promotion_review_handoff_sha256": (
            "b1782221e1463962b9179f0218ab4bac9971de867b349ce717598ff75d5ac52d"
        ),
        "organizational_independence_established": False,
        "review_relationship": "SAME_SESSION_LINEAGE_TECHNICAL_VERIFICATION",
        "reviewer": "Claude (Fable 5)",
    }:
        raise DraftVerificationError("zero-call technical acceptance drift")


def assert_raises(expected: type[BaseException], function: Callable[[], Any]) -> None:
    try:
        function()
    except expected:
        return
    except Exception as exc:
        raise AssertionError(f"unexpected exception: {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"expected {expected.__name__}")


def negative_tests(
    prereg: dict[str, Any],
    payload: dict[str, Any],
    response: dict[str, Any],
    design: dict[str, Any],
    zero: dict[str, Any],
) -> int:
    assert_raises(
        DraftVerificationError,
        lambda: require_canonical_blob(canonical_bytes(prereg) + b"\n"),
    )
    bad_authorization = copy.deepcopy(prereg)
    bad_authorization["authorization"]["provider_calls"] = 1
    assert_raises(
        DraftVerificationError,
        lambda: verify_values(bad_authorization, payload, response, design, zero),
    )
    bad_hidden = copy.deepcopy(prereg)
    bad_hidden["information_parity"]["excluded_fields"].remove("hidden.regime")
    assert_raises(
        DraftVerificationError,
        lambda: verify_values(bad_hidden, payload, response, design, zero),
    )
    bad_ref = copy.deepcopy(payload)
    bad_ref["properties"]["candidates"]["items"]["$ref"] = "#/$defs/missing"
    assert_raises(DraftVerificationError, lambda: require_local_schema_refs(bad_ref))
    bad_pilot = copy.deepcopy(design)
    bad_pilot["blinded_pilot"]["initial_candidate_pilot_n"] += 1
    assert_raises(
        DraftVerificationError,
        lambda: verify_values(prereg, payload, response, bad_pilot, zero),
    )
    bad_pointer = copy.deepcopy(response)
    bad_pointer["$defs"]["reason"]["properties"]["field_refs"]["items"]["maxLength"] = 4096
    assert_raises(
        DraftVerificationError,
        lambda: verify_values(prereg, payload, bad_pointer, design, zero),
    )
    bad_grid = copy.deepcopy(design)
    bad_grid["power"]["sensitivity_grid"]["grid_pruning_from_pilot_utility_forbidden"] = False
    assert_raises(
        DraftVerificationError,
        lambda: verify_values(prereg, payload, response, bad_grid, zero),
    )
    return 7


def main() -> int:
    for relative_path, expected_sha in SOURCE_PINS.items():
        if sha256_file(relative_path) != expected_sha:
            raise DraftVerificationError(f"authoritative source pin drift: {relative_path}")
    require_repository_state()
    loaded = {path: load_canonical_json(path) for path in JSON_PATHS}
    prereg = loaded["docs/r02-overlay-v2-preregistration-draft.json"]
    payload = loaded["docs/r02-overlay-v2-payload-schema-draft.json"]
    response = loaded["docs/r02-overlay-v2-response-schema-draft.json"]
    design = loaded["docs/r02-overlay-v2-headroom-and-power-design.json"]
    zero = loaded["docs/r02-overlay-v2-zero-call-manifest.json"]
    require_local_schema_refs(payload)
    require_local_schema_refs(response)
    verify_component_pins(prereg)
    verify_values(prereg, payload, response, design, zero)
    verify_zero_manifest(zero)
    count = negative_tests(prereg, payload, response, design, zero)
    print(
        "PASS_R02_OVERLAY_V2_PROVIDER_FREE_PREREGISTRATION_DRAFT "
        f"negative_tests={count} provider_calls=0 live_runs=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
