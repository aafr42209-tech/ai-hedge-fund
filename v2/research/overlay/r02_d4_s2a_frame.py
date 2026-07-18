"""Provider-free R02 D4-S2A successor frame construction and seal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from . import r02_d4_s2_frame as s2
from .artifacts import AppendOnlyArtifactStore
from .canonical import canonical_json_bytes, sha256_hex
from .contracts import SyntheticEpisode
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_frame import R02ChallengeScanRecord, R02FrameStratum

R02_D4_S2A_ATTEMPT_NAME = "R02_D4_S2A"
R02_D4_S2A_SCHEMA_VERSION = "r02-d4-s2a-frame-manifest-v1"
R02_D4_S2A_BASE_COMMIT = "17d9a382075d5008c79b42d52f2a8409947b4b04"
R02_D4_S2A_PREDECESSOR_ABORT_COMMIT = R02_D4_S2A_BASE_COMMIT
R02_D4_S2A_PREDECESSOR_ABORT_DIAGNOSTIC_SHA256 = (
    "6f404821a35096eafc1cba060d52faa9d3bf0652ddb49580e98d07bbfa455e35"
)
R02_D4_S2A_PREDECESSOR_ZERO_CALL_MANIFEST_SHA256 = (
    "d665fd6972c39197a62b2f94d7e160b11ceb26bc9c79daa1c528619edc4ea20e"
)
R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_RELATIVE = (
    ".research_artifacts/r02-d4-frame-0716a1b9c13a"
)
R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_TREE_SHA256 = (
    "2f15d7c9f0ff2e3e2314714a00384e110c45b0c468586c7f567aec0e7524d132"
)
R02_D4_S2A_BASE_BUILDER_SOURCE_SHA256 = (
    "178e9b5d943d2062517dfd5be746968e135b4a4bc1248092f17960b00e9786c3"
)
R02_D4_S2A_FRAME_ID = f"r02-d4-s2a-frame-{s2.R02_D4_S2_ROOT_SEED_HEX[:12]}"
R02_D4_S2A_ARTIFACT_ROOT_RELATIVE = f".research_artifacts/{R02_D4_S2A_FRAME_ID}"
R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS = 900
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_R02_D4_S2A_ARTIFACT_ROOT = ROOT / R02_D4_S2A_ARTIFACT_ROOT_RELATIVE


class R02D4S2AFrameError(RuntimeError):
    """Raised when the separately authorized S2A frame cannot seal exactly."""


class R02D4S2AChallengeScan(s2.R02D4S2ChallengeScan):
    schema_version: Literal["r02-d4-s2a-challenge-scan-v1"] = (
        "r02-d4-s2a-challenge-scan-v1"
    )
    frame_id: Literal[R02_D4_S2A_FRAME_ID] = R02_D4_S2A_FRAME_ID
    successor_attempt_name: Literal[R02_D4_S2A_ATTEMPT_NAME] = R02_D4_S2A_ATTEMPT_NAME
    predecessor_partial_root_reused: Literal[False] = False


class R02D4S2AFrameManifest(s2.R02D4S2FrameManifest):
    schema_version: Literal[R02_D4_S2A_SCHEMA_VERSION] = R02_D4_S2A_SCHEMA_VERSION
    frame_id: Literal[R02_D4_S2A_FRAME_ID] = R02_D4_S2A_FRAME_ID
    frame_build_base_commit: Literal[R02_D4_S2A_BASE_COMMIT] = R02_D4_S2A_BASE_COMMIT
    successor_attempt_name: Literal[R02_D4_S2A_ATTEMPT_NAME] = R02_D4_S2A_ATTEMPT_NAME
    predecessor_abort_commit: Literal[R02_D4_S2A_PREDECESSOR_ABORT_COMMIT] = (
        R02_D4_S2A_PREDECESSOR_ABORT_COMMIT
    )
    predecessor_abort_diagnostic_sha256: Literal[
        R02_D4_S2A_PREDECESSOR_ABORT_DIAGNOSTIC_SHA256
    ] = R02_D4_S2A_PREDECESSOR_ABORT_DIAGNOSTIC_SHA256
    predecessor_zero_call_manifest_sha256: Literal[
        R02_D4_S2A_PREDECESSOR_ZERO_CALL_MANIFEST_SHA256
    ] = R02_D4_S2A_PREDECESSOR_ZERO_CALL_MANIFEST_SHA256
    predecessor_partial_root_relative_path: Literal[
        R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_RELATIVE
    ] = R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_RELATIVE
    predecessor_partial_root_tree_sha256: Literal[
        R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_TREE_SHA256
    ] = R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_TREE_SHA256
    predecessor_partial_root_reused: Literal[False] = False
    base_frame_builder_source_sha256: Literal[
        R02_D4_S2A_BASE_BUILDER_SOURCE_SHA256
    ] = R02_D4_S2A_BASE_BUILDER_SOURCE_SHA256
    execution_timeout_seconds: Literal[R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS] = (
        R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS
    )
    in_generation_process_full_replay: Literal[False] = False


class R02D4S2AFrameSeal(s2.R02D4S2FrameSeal):
    schema_version: Literal["r02-d4-s2a-frame-seal-v1"] = (
        "r02-d4-s2a-frame-seal-v1"
    )
    frame_id: Literal[R02_D4_S2A_FRAME_ID] = R02_D4_S2A_FRAME_ID
    artifact_root_relative_path: Literal[R02_D4_S2A_ARTIFACT_ROOT_RELATIVE] = (
        R02_D4_S2A_ARTIFACT_ROOT_RELATIVE
    )
    successor_attempt_name: Literal[R02_D4_S2A_ATTEMPT_NAME] = R02_D4_S2A_ATTEMPT_NAME
    predecessor_partial_root_reused: Literal[False] = False
    execution_timeout_seconds: Literal[R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS] = (
        R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS
    )


@dataclass(frozen=True)
class R02D4S2AFrameBuild:
    representative_episodes: tuple[SyntheticEpisode, ...]
    challenge_episodes: tuple[SyntheticEpisode, ...]
    representative_classifications: tuple[R02ChallengeScanRecord, ...]
    challenge_scan: R02D4S2AChallengeScan


def frame_builder_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def base_builder_source_sha256() -> str:
    return sha256_hex(Path(s2.__file__).read_bytes())


def fixture_generator_source_sha256() -> str:
    return s2.fixture_generator_source_sha256()


def candidate_generator_source_sha256() -> str:
    return s2.candidate_generator_source_sha256()


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S2AFrameError(code)


def build_provider_free_frame() -> R02D4S2AFrameBuild:
    _require_equal(
        base_builder_source_sha256(),
        R02_D4_S2A_BASE_BUILDER_SOURCE_SHA256,
        "accepted S2 builder source drift",
    )
    base = s2.build_provider_free_frame()
    scan_payload = base.challenge_scan.model_dump(mode="python")
    scan_payload["schema_version"] = "r02-d4-s2a-challenge-scan-v1"
    scan_payload["frame_id"] = R02_D4_S2A_FRAME_ID
    scan_payload["successor_attempt_name"] = R02_D4_S2A_ATTEMPT_NAME
    scan_payload["predecessor_partial_root_reused"] = False
    scan = R02D4S2AChallengeScan.model_validate(scan_payload)
    return R02D4S2AFrameBuild(
        representative_episodes=base.representative_episodes,
        challenge_episodes=base.challenge_episodes,
        representative_classifications=base.representative_classifications,
        challenge_scan=scan,
    )


def persist_provider_free_frame(
    build: R02D4S2AFrameBuild,
    *,
    artifact_root: str | Path = DEFAULT_R02_D4_S2A_ARTIFACT_ROOT,
) -> tuple[R02D4S2AFrameManifest, R02D4S2AFrameSeal]:
    root = Path(artifact_root).resolve()
    if root != DEFAULT_R02_D4_S2A_ARTIFACT_ROOT.resolve():
        raise R02D4S2AFrameError("S2A artifact root is not the pinned successor root")
    if root == (ROOT / R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_RELATIVE).resolve():
        raise R02D4S2AFrameError("quarantined predecessor root reuse is forbidden")
    store = R02AppendOnlyArtifactStore(root)
    episodes = (*build.representative_episodes, *build.challenge_episodes)
    fixture_references = []
    for ordinal, episode in enumerate(episodes):
        stratum = "representative" if ordinal < s2.R02_D4_S2_REPRESENTATIVE_COUNT else "challenge"
        stratum_ordinal = (
            ordinal
            if stratum == "representative"
            else ordinal - s2.R02_D4_S2_REPRESENTATIVE_COUNT
        )
        fixture_references.append(
            store.write_json(f"fixtures/{stratum}/{stratum_ordinal:04d}.json", episode)
        )
    challenge_scan_reference = store.write_json("challenge_scan.json", build.challenge_scan)
    classifications = (
        *build.representative_classifications,
        *(record for record in build.challenge_scan.records if record.admitted),
    )
    cases = tuple(
        s2._build_case(
            ordinal=ordinal,
            episode=episode,
            classification=classification,
            reference=reference,
        )
        for ordinal, (episode, classification, reference) in enumerate(
            zip(episodes, classifications, fixture_references, strict=True)
        )
    )
    payload_references = (*fixture_references, challenge_scan_reference)
    representative = cases[: s2.R02_D4_S2_REPRESENTATIVE_COUNT]
    challenge = cases[s2.R02_D4_S2_REPRESENTATIVE_COUNT :]
    manifest = R02D4S2AFrameManifest(
        frame_builder_source_sha256=frame_builder_source_sha256(),
        challenge_scanned_count=len(build.challenge_scan.records),
        challenge_scan=challenge_scan_reference,
        representative_trigger_count=sum(case.triggered for case in representative),
        representative_eligible_count=sum(case.eligible_opportunity for case in representative),
        challenge_trigger_count=sum(case.triggered for case in challenge),
        challenge_eligible_count=sum(case.eligible_opportunity for case in challenge),
        total_eligible_count=sum(case.eligible_opportunity for case in cases),
        cases=cases,
        payload_tree_sha256=s2.tree_sha256(tuple(payload_references)),
    )
    manifest_reference = store.write_json("frame_manifest.json", manifest)
    full_tree_file_count, full_tree_sha256 = s2.filesystem_tree(store.root)
    seal = R02D4S2AFrameSeal(
        frame_manifest=manifest_reference,
        full_tree_file_count=full_tree_file_count,
        full_tree_sha256=full_tree_sha256,
    )
    return manifest, seal


def verify_persisted_frame(
    store: AppendOnlyArtifactStore,
    seal: R02D4S2AFrameSeal,
    *,
    reproduce: bool = True,
) -> R02D4S2AFrameManifest:
    manifest = R02D4S2AFrameManifest.model_validate_json(store.read_bytes(seal.frame_manifest))
    scan = R02D4S2AChallengeScan.model_validate_json(store.read_bytes(manifest.challenge_scan))
    admitted = tuple(record.source_index for record in scan.records if record.admitted)
    challenge_indexes = tuple(
        case.source_index
        for case in manifest.cases
        if case.stratum is R02FrameStratum.CHALLENGE_HEADROOM
    )
    _require_equal(admitted, challenge_indexes, "challenge admissions do not match cases")
    payload_references = tuple(case.fixture_artifact for case in manifest.cases) + (
        manifest.challenge_scan,
    )
    _require_equal(
        s2.tree_sha256(payload_references), manifest.payload_tree_sha256, "payload tree mismatch"
    )
    stored_episodes = tuple(
        SyntheticEpisode.model_validate_json(store.read_bytes(case.fixture_artifact))
        for case in manifest.cases
    )
    for case, episode in zip(manifest.cases, stored_episodes, strict=True):
        _require_equal(episode.public.case_id, case.fixture_id, "fixture ID mismatch")
        _require_equal(episode.content_sha256, case.fixture_content_sha256, "fixture content mismatch")
        _require_equal(
            s2.public_state_fingerprint(episode),
            case.public_state_fingerprint_sha256,
            "public-state fingerprint mismatch",
        )
    count, full_tree_sha256 = s2.filesystem_tree(store.root)
    _require_equal(count, seal.full_tree_file_count, "full-tree file count mismatch")
    _require_equal(full_tree_sha256, seal.full_tree_sha256, "full-tree hash mismatch")
    _require_equal(
        manifest.frame_builder_source_sha256,
        frame_builder_source_sha256(),
        "successor frame builder source drift",
    )
    _require_equal(
        manifest.base_frame_builder_source_sha256,
        base_builder_source_sha256(),
        "accepted S2 builder source drift",
    )
    _require_equal(
        manifest.fixture_generator_source_sha256,
        fixture_generator_source_sha256(),
        "fixture generator source drift",
    )
    _require_equal(
        manifest.candidate_generator_source_sha256,
        candidate_generator_source_sha256(),
        "candidate generator source drift",
    )
    if reproduce:
        regenerated = build_provider_free_frame()
        expected_episodes = (
            *regenerated.representative_episodes,
            *regenerated.challenge_episodes,
        )
        _require_equal(
            regenerated.challenge_scan,
            scan,
            "challenge scan is not byte-reproducible",
        )
        for observed, expected in zip(stored_episodes, expected_episodes, strict=True):
            _require_equal(
                canonical_json_bytes(observed),
                canonical_json_bytes(expected),
                "fixture is not byte-reproducible",
            )
    return manifest


def verify_intent(repo_root: Path, intent: Mapping[str, Any]) -> None:
    expected = {
        "status": "AUTHORIZED_PROVIDER_FREE_S2A_FRAME_GENERATION_AND_FROZEN_ADMISSION_SCAN",
        "successor_attempt_name": R02_D4_S2A_ATTEMPT_NAME,
        "frame_build_base_commit": R02_D4_S2A_BASE_COMMIT,
        "accepted_design_commit": s2.R02_D4_S2_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": s2.R02_D4_S2_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "resolved_seed_artifact_sha256": s2.R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256,
        "resolved_frame_seed_sha256": s2.R02_D4_S2_ROOT_SEED_HEX,
        "frame_id": R02_D4_S2A_FRAME_ID,
        "frame_root_relative": R02_D4_S2A_ARTIFACT_ROOT_RELATIVE,
        "representative_count": s2.R02_D4_S2_REPRESENTATIVE_COUNT,
        "challenge_count": s2.R02_D4_S2_CHALLENGE_COUNT,
        "challenge_scan_start_index": s2.R02_D4_S2_CHALLENGE_SCAN_START,
        "challenge_scan_limit": s2.R02_D4_S2_CHALLENGE_SCAN_LIMIT,
        "execution_timeout_seconds": R02_D4_S2A_EXECUTION_TIMEOUT_SECONDS,
        "in_generation_process_full_replay": False,
        "predecessor_abort_commit": R02_D4_S2A_PREDECESSOR_ABORT_COMMIT,
        "predecessor_partial_root_relative": R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_RELATIVE,
        "predecessor_partial_root_tree_sha256": R02_D4_S2A_PREDECESSOR_PARTIAL_ROOT_TREE_SHA256,
        "predecessor_partial_root_reused": False,
        "provider_calls": 0,
        "codex_exec_invocations": 0,
        "micro_pilot_executed": False,
        "live_execution": False,
        "retry_cap": 0,
        "replacement_cap": 0,
        "commit_created": False,
        "push_performed": False,
    }
    for field, value in expected.items():
        _require_equal(intent.get(field), value, f"intent field mismatch:{field}")
    source_pins = intent.get("source_pins")
    if not isinstance(source_pins, Mapping):
        raise R02D4S2AFrameError("intent source pins missing")
    _require_equal(
        source_pins.get("frame_builder_source_sha256"),
        frame_builder_source_sha256(),
        "intent successor builder source mismatch",
    )
    _require_equal(
        source_pins.get("base_frame_builder_source_sha256"),
        base_builder_source_sha256(),
        "intent base builder source mismatch",
    )
    _require_equal(
        source_pins.get("candidate_generator_source_sha256"),
        candidate_generator_source_sha256(),
        "intent candidate source mismatch",
    )
    _require_equal(
        source_pins.get("fixture_generator_source_sha256"),
        fixture_generator_source_sha256(),
        "intent fixture source mismatch",
    )
    _require_equal(
        sha256_hex((repo_root / "docs" / "r02-d4-s1-resolved-seed.json").read_bytes()),
        s2.R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256,
        "resolved seed artifact drift",
    )
    _require_equal(
        sha256_hex((repo_root / "docs" / "r02-d4-s2-abort-diagnostic.json").read_bytes()),
        R02_D4_S2A_PREDECESSOR_ABORT_DIAGNOSTIC_SHA256,
        "predecessor abort diagnostic drift",
    )
    _require_equal(
        sha256_hex((repo_root / "docs" / "r02-d4-s2-zero-call-manifest.json").read_bytes()),
        R02_D4_S2A_PREDECESSOR_ZERO_CALL_MANIFEST_SHA256,
        "predecessor zero-call manifest drift",
    )


def forbidden_capability_names() -> set[str]:
    return {
        "asyncio",
        "http",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "codex_exec_client",
        "r02_d3_live_orchestrator",
    }
