"""Provider-free R02 D4-S2 exact-replication frame construction and seal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import Field, model_validator

from . import fixtures, r02_candidates
from .artifacts import AppendOnlyArtifactStore
from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import ArtifactReference, GeneratorConfig, StrictModel, SyntheticEpisode
from .fixtures import generate_episode
from .oracle import solve_oracle
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_candidates import prepare_provider_free_episode
from .r02_contracts import R02PreparationState, R02_FREEZE_SHA256
from .r02_frame import (
    R02ChallengeDisposition,
    R02ChallengeScanRecord,
    R02FrameCase,
    R02FrameStratum,
)
from .scoring import score_episode

R02_D4_S2_SCHEMA_VERSION = "r02-d4-s2-frame-manifest-v1"
R02_D4_S2_BASE_COMMIT = "a563fb4e6e83a51662fa41c166eeb3fa5f1a52f0"
R02_D4_S2_ACCEPTED_DESIGN_COMMIT = "d9f984866c8775153d9c1ac1aea9b49fc9647635"
R02_D4_S2_ACCEPTED_DESIGN_MANIFEST_SHA256 = (
    "784f47a8fa19a679f1048269810604a9164081a1676ffe4c04ccb4d959e0a900"
)
R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256 = (
    "a05f3b2da66dfda6ba3369effa1734f8c760e6c1735db80306b07f51a8abeef5"
)
R02_D4_S2_ROOT_SEED_HEX = (
    "0716a1b9c13aec596b29776f48b3d8d1fc0a9afacc1c5010bd2cf2a9629d0621"
)
R02_D4_S2_FRAME_ID = f"r02-d4-frame-{R02_D4_S2_ROOT_SEED_HEX[:12]}"
R02_D4_S2_REPRESENTATIVE_COUNT = 150
R02_D4_S2_CHALLENGE_COUNT = 50
R02_D4_S2_TOTAL_COUNT = 200
R02_D4_S2_CHALLENGE_SCAN_START = R02_D4_S2_REPRESENTATIVE_COUNT
R02_D4_S2_CHALLENGE_SCAN_LIMIT = 4_096
R02_D4_S2_TARGET_WEIGHT_DENOMINATOR = 4
R02_D4_S2_REPRESENTATIVE_WEIGHT_NUMERATOR = 3
R02_D4_S2_CHALLENGE_WEIGHT_NUMERATOR = 1
R02_D4_S2_GENERATOR_CONFIG_SHA256 = (
    "e6598cca07c846650f7d7c157c16a6d77aefd4a94966c6624288239b5ae04ccf"
)
R02_D4_S2_CANDIDATE_GENERATOR_SOURCE_SHA256 = (
    "29c13547230d1729d8b9cec637ccb13335fbcae52c1360e63718359d993a320e"
)
R02_D4_S2_FIXTURE_GENERATOR_SOURCE_SHA256 = (
    "732ca6ff358590edd856ba68bcb6cefb612246da9d81b97aa08d12db786eabfe"
)
R02_D4_S2_R02_D1_MANIFEST_SHA256 = (
    "81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf"
)
R02_D4_S2_ARTIFACT_ROOT_RELATIVE = (
    f".research_artifacts/{R02_D4_S2_FRAME_ID}"
)
R02_D4_S2_PAYLOAD_FILE_COUNT = R02_D4_S2_TOTAL_COUNT + 1
R02_D4_S2_FULL_TREE_FILE_COUNT = R02_D4_S2_PAYLOAD_FILE_COUNT + 1
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_R02_D4_S2_ARTIFACT_ROOT = ROOT / R02_D4_S2_ARTIFACT_ROOT_RELATIVE


class R02D4S2FrameError(RuntimeError):
    """Raised when the one accepted S2 frame cannot be sealed exactly."""


class R02D4S2ChallengeScan(StrictModel):
    schema_version: Literal["r02-d4-s2-challenge-scan-v1"] = (
        "r02-d4-s2-challenge-scan-v1"
    )
    frame_id: Literal[R02_D4_S2_FRAME_ID] = R02_D4_S2_FRAME_ID
    root_seed_hex: Literal[R02_D4_S2_ROOT_SEED_HEX] = R02_D4_S2_ROOT_SEED_HEX
    scan_start_index: Literal[R02_D4_S2_CHALLENGE_SCAN_START] = (
        R02_D4_S2_CHALLENGE_SCAN_START
    )
    scan_limit: Literal[R02_D4_S2_CHALLENGE_SCAN_LIMIT] = (
        R02_D4_S2_CHALLENGE_SCAN_LIMIT
    )
    records: tuple[R02ChallengeScanRecord, ...] = Field(min_length=50)
    admitted_source_indexes: tuple[int, ...] = Field(min_length=50, max_length=50)
    admission_rule: Literal[
        "TRIGGER_TRUE_AND_AT_LEAST_TWO_DEDUPLICATED_CANDIDATES_AND_POSITIVE_HEADROOM"
    ] = "TRIGGER_TRUE_AND_AT_LEAST_TWO_DEDUPLICATED_CANDIDATES_AND_POSITIVE_HEADROOM"
    outcome_shopping_fields_used: Literal[False] = False
    provider_calls: Literal[0] = 0
    frame_scan: Literal[True] = True
    live_execution: Literal[False] = False

    @model_validator(mode="after")
    def validate_scan(self) -> "R02D4S2ChallengeScan":
        indexes = tuple(record.source_index for record in self.records)
        expected = tuple(range(self.scan_start_index, self.scan_start_index + len(indexes)))
        if indexes != expected:
            raise ValueError("challenge scan indexes must be contiguous and ordered")
        if len(indexes) > self.scan_limit:
            raise ValueError("challenge scan exceeds the frozen limit")
        admitted = tuple(record.source_index for record in self.records if record.admitted)
        if admitted != self.admitted_source_indexes:
            raise ValueError("challenge admitted-index record mismatch")
        if len(admitted) != R02_D4_S2_CHALLENGE_COUNT:
            raise ValueError("challenge scan must admit exactly 50 fixtures")
        if self.records[-1].source_index != admitted[-1]:
            raise ValueError("challenge scan must stop at the final required admission")
        return self


class R02D4S2FrameManifest(StrictModel):
    schema_version: Literal[R02_D4_S2_SCHEMA_VERSION] = R02_D4_S2_SCHEMA_VERSION
    status: Literal["PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"] = (
        "PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
    )
    frame_id: Literal[R02_D4_S2_FRAME_ID] = R02_D4_S2_FRAME_ID
    frame_build_base_commit: Literal[R02_D4_S2_BASE_COMMIT] = R02_D4_S2_BASE_COMMIT
    accepted_design_commit: Literal[R02_D4_S2_ACCEPTED_DESIGN_COMMIT] = (
        R02_D4_S2_ACCEPTED_DESIGN_COMMIT
    )
    accepted_design_manifest_sha256: Literal[
        R02_D4_S2_ACCEPTED_DESIGN_MANIFEST_SHA256
    ] = R02_D4_S2_ACCEPTED_DESIGN_MANIFEST_SHA256
    resolved_seed_artifact_sha256: Literal[
        R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256
    ] = R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256
    r02_d1_freeze_sha256: Literal[R02_FREEZE_SHA256] = R02_FREEZE_SHA256
    r02_d1_manifest_sha256: Literal[R02_D4_S2_R02_D1_MANIFEST_SHA256] = (
        R02_D4_S2_R02_D1_MANIFEST_SHA256
    )
    root_seed_hex: Literal[R02_D4_S2_ROOT_SEED_HEX] = R02_D4_S2_ROOT_SEED_HEX
    root_seed_derivation: Literal["COPIED_FROM_ACCEPTED_S1_RESOLVED_SEED_ARTIFACT"] = (
        "COPIED_FROM_ACCEPTED_S1_RESOLVED_SEED_ARTIFACT"
    )
    generator_config_sha256: Literal[R02_D4_S2_GENERATOR_CONFIG_SHA256] = (
        R02_D4_S2_GENERATOR_CONFIG_SHA256
    )
    candidate_generator_source_sha256: Literal[
        R02_D4_S2_CANDIDATE_GENERATOR_SOURCE_SHA256
    ] = R02_D4_S2_CANDIDATE_GENERATOR_SOURCE_SHA256
    fixture_generator_source_sha256: Literal[
        R02_D4_S2_FIXTURE_GENERATOR_SOURCE_SHA256
    ] = R02_D4_S2_FIXTURE_GENERATOR_SOURCE_SHA256
    frame_builder_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    representative_count: Literal[R02_D4_S2_REPRESENTATIVE_COUNT] = (
        R02_D4_S2_REPRESENTATIVE_COUNT
    )
    challenge_count: Literal[R02_D4_S2_CHALLENGE_COUNT] = R02_D4_S2_CHALLENGE_COUNT
    total_count: Literal[R02_D4_S2_TOTAL_COUNT] = R02_D4_S2_TOTAL_COUNT
    representative_target_weight_numerator: Literal[
        R02_D4_S2_REPRESENTATIVE_WEIGHT_NUMERATOR
    ] = R02_D4_S2_REPRESENTATIVE_WEIGHT_NUMERATOR
    challenge_target_weight_numerator: Literal[
        R02_D4_S2_CHALLENGE_WEIGHT_NUMERATOR
    ] = R02_D4_S2_CHALLENGE_WEIGHT_NUMERATOR
    target_weight_denominator: Literal[R02_D4_S2_TARGET_WEIGHT_DENOMINATOR] = (
        R02_D4_S2_TARGET_WEIGHT_DENOMINATOR
    )
    challenge_scan_start_index: Literal[R02_D4_S2_CHALLENGE_SCAN_START] = (
        R02_D4_S2_CHALLENGE_SCAN_START
    )
    challenge_scan_limit: Literal[R02_D4_S2_CHALLENGE_SCAN_LIMIT] = (
        R02_D4_S2_CHALLENGE_SCAN_LIMIT
    )
    challenge_scanned_count: int = Field(ge=50, le=R02_D4_S2_CHALLENGE_SCAN_LIMIT)
    challenge_scan: ArtifactReference
    representative_trigger_count: int = Field(ge=0, le=R02_D4_S2_REPRESENTATIVE_COUNT)
    representative_eligible_count: int = Field(ge=0, le=R02_D4_S2_REPRESENTATIVE_COUNT)
    challenge_trigger_count: Literal[R02_D4_S2_CHALLENGE_COUNT] = (
        R02_D4_S2_CHALLENGE_COUNT
    )
    challenge_eligible_count: Literal[R02_D4_S2_CHALLENGE_COUNT] = (
        R02_D4_S2_CHALLENGE_COUNT
    )
    total_eligible_count: int = Field(ge=R02_D4_S2_CHALLENGE_COUNT, le=R02_D4_S2_TOTAL_COUNT)
    duplicate_policy: Literal["INVALID_FRAME_NO_SKIP"] = "INVALID_FRAME_NO_SKIP"
    near_duplicate_policy: Literal[
        "CANONICAL_PUBLIC_STATE_EXCLUDING_CASE_ID_AND_SEED_INVALID_FRAME_NO_SKIP"
    ] = "CANONICAL_PUBLIC_STATE_EXCLUDING_CASE_ID_AND_SEED_INVALID_FRAME_NO_SKIP"
    oracle_barrier: Literal[
        "CLASSIFICATION_AFTER_TRIGGER_AND_CANDIDATE_BYTES_SELECTOR_INACCESSIBLE"
    ] = "CLASSIFICATION_AFTER_TRIGGER_AND_CANDIDATE_BYTES_SELECTOR_INACCESSIBLE"
    cases: tuple[R02FrameCase, ...] = Field(min_length=200, max_length=200)
    payload_file_count: Literal[R02_D4_S2_PAYLOAD_FILE_COUNT] = (
        R02_D4_S2_PAYLOAD_FILE_COUNT
    )
    payload_tree_algorithm: Literal[
        "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    ] = "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    payload_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frame_generation_count: Literal[1] = 1
    scan_execution_count: Literal[1] = 1
    retry_count: Literal[0] = 0
    replacement_count: Literal[0] = 0
    provider_calls: Literal[0] = 0
    codex_exec_invocations: Literal[0] = 0
    frame_generation: Literal[True] = True
    frame_scan: Literal[True] = True
    micro_pilot_executed: Literal[False] = False
    live_execution: Literal[False] = False
    trigger_threshold_bps: Literal[50] = 50
    trigger_recalibrated_after_frame: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "R02D4S2FrameManifest":
        if len(self.cases) != self.total_count:
            raise ValueError("frame case count mismatch")
        if tuple(case.frame_ordinal for case in self.cases) != tuple(range(self.total_count)):
            raise ValueError("frame ordinals must be contiguous")
        expected_strata = (
            *(R02FrameStratum.REPRESENTATIVE for _ in range(self.representative_count)),
            *(R02FrameStratum.CHALLENGE_HEADROOM for _ in range(self.challenge_count)),
        )
        if tuple(case.stratum for case in self.cases) != expected_strata:
            raise ValueError("frame stratum order mismatch")
        identities = (
            (case.fixture_id for case in self.cases),
            (case.source_index for case in self.cases),
            (case.fixture_content_sha256 for case in self.cases),
            (case.public_state_fingerprint_sha256 for case in self.cases),
            (case.fixture_artifact.relative_path for case in self.cases),
        )
        if any(len(set(values)) != self.total_count for values in identities):
            raise ValueError("frame contains a duplicate or near-duplicate identity")
        representative = self.cases[: self.representative_count]
        challenge = self.cases[self.representative_count :]
        if tuple(case.source_index for case in representative) != tuple(
            range(self.representative_count)
        ):
            raise ValueError("representative frame must be the unconditional seed prefix")
        if self.representative_trigger_count != sum(case.triggered for case in representative):
            raise ValueError("representative trigger count mismatch")
        if self.representative_eligible_count != sum(
            case.eligible_opportunity for case in representative
        ):
            raise ValueError("representative eligible count mismatch")
        if self.challenge_trigger_count != sum(case.triggered for case in challenge):
            raise ValueError("challenge trigger count mismatch")
        if self.challenge_eligible_count != sum(case.eligible_opportunity for case in challenge):
            raise ValueError("challenge eligible count mismatch")
        if self.total_eligible_count != (
            self.representative_eligible_count + self.challenge_eligible_count
        ):
            raise ValueError("total eligible count mismatch")
        if self.payload_file_count != self.total_count + 1:
            raise ValueError("frame payload must contain fixtures plus challenge scan")
        return self


class R02D4S2FrameSeal(StrictModel):
    schema_version: Literal["r02-d4-s2-frame-seal-v1"] = "r02-d4-s2-frame-seal-v1"
    status: Literal["PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"] = (
        "PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
    )
    frame_id: Literal[R02_D4_S2_FRAME_ID] = R02_D4_S2_FRAME_ID
    artifact_root_relative_path: Literal[R02_D4_S2_ARTIFACT_ROOT_RELATIVE] = (
        R02_D4_S2_ARTIFACT_ROOT_RELATIVE
    )
    frame_manifest: ArtifactReference
    full_tree_file_count: Literal[R02_D4_S2_FULL_TREE_FILE_COUNT] = (
        R02_D4_S2_FULL_TREE_FILE_COUNT
    )
    full_tree_algorithm: Literal[
        "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    ] = "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    full_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frame_generation_count: Literal[1] = 1
    scan_execution_count: Literal[1] = 1
    retry_count: Literal[0] = 0
    replacement_count: Literal[0] = 0
    provider_calls: Literal[0] = 0
    codex_exec_invocations: Literal[0] = 0
    frame_generation: Literal[True] = True
    frame_scan: Literal[True] = True
    live_execution: Literal[False] = False


@dataclass(frozen=True)
class R02D4S2FrameBuild:
    representative_episodes: tuple[SyntheticEpisode, ...]
    challenge_episodes: tuple[SyntheticEpisode, ...]
    representative_classifications: tuple[R02ChallengeScanRecord, ...]
    challenge_scan: R02D4S2ChallengeScan


def frame_builder_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def fixture_generator_source_sha256() -> str:
    return sha256_hex(Path(fixtures.__file__).read_bytes())


def candidate_generator_source_sha256() -> str:
    return sha256_hex(Path(r02_candidates.__file__).read_bytes())


def public_state_fingerprint(episode: SyntheticEpisode) -> str:
    public = episode.public.model_dump(mode="python")
    public.pop("case_id")
    public.pop("seed_hex")
    return canonical_sha256(public)


def classify_episode(episode: SyntheticEpisode, *, source_index: int) -> R02ChallengeScanRecord:
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=R02_D4_S2_FRAME_ID,
        replicate_id=0,
        provider_attempt_count=0,
    )
    baseline = primary_deterministic(episode)
    triggered = preparation.eligibility.trigger.triggered
    candidate_count = (
        len(preparation.candidate_set.candidates)
        if preparation.candidate_set is not None
        else 0
    )
    eligible = triggered and candidate_count >= 2
    if triggered and preparation.state is R02PreparationState.NO_CALL_TERMINAL:
        if candidate_count != 1:
            raise R02D4S2FrameError("triggered frame classification hit an integrity stop")
    if not triggered:
        disposition = R02ChallengeDisposition.NOT_TRIGGERED
        best_utility = None
        headroom = None
        best_candidate_id = None
    elif not eligible:
        disposition = R02ChallengeDisposition.INELIGIBLE_CANDIDATE_COLLAPSE
        best_utility = None
        headroom = None
        best_candidate_id = None
    else:
        assert preparation.candidate_set is not None
        raw_by_id: dict[str, Any] = {}
        for raw in preparation.candidate_set.raw_candidates:
            raw_by_id.setdefault(raw.canonical_candidate_id, raw)
        scored = tuple(
            (
                score_episode(
                    episode,
                    raw_by_id[candidate.canonical_candidate_id].validation_report,
                ).utility_e12,
                candidate.canonical_candidate_id,
            )
            for candidate in preparation.candidate_set.candidates
        )
        best_utility, best_candidate_id = max(scored, key=lambda item: (item[0], item[1]))
        headroom = best_utility - baseline.score.utility_e12
        disposition = (
            R02ChallengeDisposition.ADMITTED
            if headroom > 0
            else R02ChallengeDisposition.NO_POSITIVE_CANDIDATE_HEADROOM
        )
    return R02ChallengeScanRecord(
        source_index=source_index,
        fixture_id=episode.public.case_id,
        fixture_content_sha256=episode.content_sha256,
        public_state_fingerprint_sha256=public_state_fingerprint(episode),
        regime=episode.hidden.regime,
        triggered=triggered,
        candidate_count=candidate_count,
        eligible_opportunity=eligible,
        baseline_utility_e12=baseline.score.utility_e12,
        best_candidate_utility_e12=best_utility,
        candidate_headroom_e12=headroom,
        best_candidate_canonical_id=best_candidate_id,
        disposition=disposition,
        admitted=disposition is R02ChallengeDisposition.ADMITTED,
    )


def build_provider_free_frame() -> R02D4S2FrameBuild:
    config = GeneratorConfig()
    representative = tuple(
        generate_episode(config, R02_D4_S2_ROOT_SEED_HEX, index)
        for index in range(R02_D4_S2_REPRESENTATIVE_COUNT)
    )
    representative_classifications = tuple(
        classify_episode(episode, source_index=index)
        for index, episode in enumerate(representative)
    )
    seen_content = {episode.content_sha256 for episode in representative}
    seen_public = {public_state_fingerprint(episode) for episode in representative}
    if len(seen_content) != R02_D4_S2_REPRESENTATIVE_COUNT or len(seen_public) != (
        R02_D4_S2_REPRESENTATIVE_COUNT
    ):
        raise R02D4S2FrameError("representative prefix contains duplicate identities")
    challenge: list[SyntheticEpisode] = []
    scan_records: list[R02ChallengeScanRecord] = []
    for source_index in range(
        R02_D4_S2_CHALLENGE_SCAN_START,
        R02_D4_S2_CHALLENGE_SCAN_START + R02_D4_S2_CHALLENGE_SCAN_LIMIT,
    ):
        episode = generate_episode(config, R02_D4_S2_ROOT_SEED_HEX, source_index)
        fingerprint = public_state_fingerprint(episode)
        if episode.content_sha256 in seen_content or fingerprint in seen_public:
            raise R02D4S2FrameError("challenge scan encountered a duplicate identity")
        classification = classify_episode(episode, source_index=source_index)
        scan_records.append(classification)
        if classification.admitted:
            challenge.append(episode)
            seen_content.add(episode.content_sha256)
            seen_public.add(fingerprint)
            if len(challenge) == R02_D4_S2_CHALLENGE_COUNT:
                break
    if len(challenge) != R02_D4_S2_CHALLENGE_COUNT:
        raise R02D4S2FrameError("challenge scan limit exhausted before filling the frame")
    scan = R02D4S2ChallengeScan(
        records=tuple(scan_records),
        admitted_source_indexes=tuple(
            record.source_index for record in scan_records if record.admitted
        ),
    )
    return R02D4S2FrameBuild(
        representative_episodes=representative,
        challenge_episodes=tuple(challenge),
        representative_classifications=representative_classifications,
        challenge_scan=scan,
    )


def tree_sha256(references: tuple[ArtifactReference, ...]) -> str:
    records = "\n".join(
        f"{reference.relative_path}\0{reference.size_bytes}\0{reference.sha256}"
        for reference in sorted(references, key=lambda item: item.relative_path)
    )
    return sha256_hex(records.encode("utf-8"))


def filesystem_tree(root: Path) -> tuple[int, str]:
    references = []
    for path in sorted(value for value in root.rglob("*") if value.is_file()):
        payload = path.read_bytes()
        references.append(
            ArtifactReference(
                relative_path=path.relative_to(root).as_posix(),
                sha256=sha256_hex(payload),
                size_bytes=len(payload),
            )
        )
    return len(references), tree_sha256(tuple(references))


def _build_case(
    *,
    ordinal: int,
    episode: SyntheticEpisode,
    classification: R02ChallengeScanRecord,
    reference: ArtifactReference,
) -> R02FrameCase:
    oracle = solve_oracle(episode)
    stratum = (
        R02FrameStratum.REPRESENTATIVE
        if ordinal < R02_D4_S2_REPRESENTATIVE_COUNT
        else R02FrameStratum.CHALLENGE_HEADROOM
    )
    return R02FrameCase(
        frame_ordinal=ordinal,
        stratum=stratum,
        source_index=classification.source_index,
        fixture_id=episode.public.case_id,
        fixture_seed_hex=episode.public.seed_hex,
        fixture_content_sha256=episode.content_sha256,
        public_state_fingerprint_sha256=classification.public_state_fingerprint_sha256,
        fixture_artifact=reference,
        regime=episode.hidden.regime,
        baseline_utility_e12=classification.baseline_utility_e12,
        oracle_utility_e12=oracle.score.utility_e12,
        oracle_minus_baseline_e12=oracle.score.utility_e12 - classification.baseline_utility_e12,
        triggered=classification.triggered,
        candidate_count=classification.candidate_count,
        eligible_opportunity=classification.eligible_opportunity,
        candidate_headroom_e12=classification.candidate_headroom_e12,
    )


def persist_provider_free_frame(
    build: R02D4S2FrameBuild,
    *,
    artifact_root: str | Path = DEFAULT_R02_D4_S2_ARTIFACT_ROOT,
) -> tuple[R02D4S2FrameManifest, R02D4S2FrameSeal]:
    store = R02AppendOnlyArtifactStore(artifact_root)
    episodes = (*build.representative_episodes, *build.challenge_episodes)
    fixture_references = []
    for ordinal, episode in enumerate(episodes):
        stratum = "representative" if ordinal < R02_D4_S2_REPRESENTATIVE_COUNT else "challenge"
        stratum_ordinal = (
            ordinal
            if stratum == "representative"
            else ordinal - R02_D4_S2_REPRESENTATIVE_COUNT
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
        _build_case(
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
    representative = cases[:R02_D4_S2_REPRESENTATIVE_COUNT]
    challenge = cases[R02_D4_S2_REPRESENTATIVE_COUNT:]
    manifest = R02D4S2FrameManifest(
        frame_builder_source_sha256=frame_builder_source_sha256(),
        challenge_scanned_count=len(build.challenge_scan.records),
        challenge_scan=challenge_scan_reference,
        representative_trigger_count=sum(case.triggered for case in representative),
        representative_eligible_count=sum(case.eligible_opportunity for case in representative),
        challenge_trigger_count=sum(case.triggered for case in challenge),
        challenge_eligible_count=sum(case.eligible_opportunity for case in challenge),
        total_eligible_count=sum(case.eligible_opportunity for case in cases),
        cases=cases,
        payload_tree_sha256=tree_sha256(tuple(payload_references)),
    )
    manifest_reference = store.write_json("frame_manifest.json", manifest)
    full_tree_file_count, full_tree_sha256 = filesystem_tree(store.root)
    seal = R02D4S2FrameSeal(
        frame_manifest=manifest_reference,
        full_tree_file_count=full_tree_file_count,
        full_tree_sha256=full_tree_sha256,
    )
    return manifest, seal


def _require_equal(actual: object, expected: object, code: str) -> None:
    if actual != expected:
        raise R02D4S2FrameError(code)


def verify_persisted_frame(
    store: AppendOnlyArtifactStore,
    seal: R02D4S2FrameSeal,
    *,
    reproduce: bool = True,
) -> R02D4S2FrameManifest:
    manifest = R02D4S2FrameManifest.model_validate_json(store.read_bytes(seal.frame_manifest))
    scan = R02D4S2ChallengeScan.model_validate_json(store.read_bytes(manifest.challenge_scan))
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
        tree_sha256(payload_references), manifest.payload_tree_sha256, "payload tree mismatch"
    )
    stored_episodes = tuple(
        SyntheticEpisode.model_validate_json(store.read_bytes(case.fixture_artifact))
        for case in manifest.cases
    )
    for case, episode in zip(manifest.cases, stored_episodes, strict=True):
        _require_equal(episode.public.case_id, case.fixture_id, "fixture ID mismatch")
        _require_equal(episode.content_sha256, case.fixture_content_sha256, "fixture content mismatch")
        _require_equal(
            public_state_fingerprint(episode),
            case.public_state_fingerprint_sha256,
            "public-state fingerprint mismatch",
        )
    count, full_tree_sha256 = filesystem_tree(store.root)
    _require_equal(count, seal.full_tree_file_count, "full-tree file count mismatch")
    _require_equal(full_tree_sha256, seal.full_tree_sha256, "full-tree hash mismatch")
    _require_equal(
        manifest.frame_builder_source_sha256,
        frame_builder_source_sha256(),
        "frame builder source drift",
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
        "status": "AUTHORIZED_PROVIDER_FREE_FRAME_GENERATION_AND_FROZEN_ADMISSION_SCAN",
        "frame_build_base_commit": R02_D4_S2_BASE_COMMIT,
        "accepted_design_commit": R02_D4_S2_ACCEPTED_DESIGN_COMMIT,
        "accepted_design_manifest_sha256": R02_D4_S2_ACCEPTED_DESIGN_MANIFEST_SHA256,
        "resolved_seed_artifact_sha256": R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256,
        "resolved_frame_seed_sha256": R02_D4_S2_ROOT_SEED_HEX,
        "frame_id": R02_D4_S2_FRAME_ID,
        "representative_count": R02_D4_S2_REPRESENTATIVE_COUNT,
        "challenge_count": R02_D4_S2_CHALLENGE_COUNT,
        "challenge_scan_start_index": R02_D4_S2_CHALLENGE_SCAN_START,
        "challenge_scan_limit": R02_D4_S2_CHALLENGE_SCAN_LIMIT,
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
        raise R02D4S2FrameError("intent source pins missing")
    _require_equal(
        source_pins.get("frame_builder_source_sha256"),
        frame_builder_source_sha256(),
        "intent frame builder source mismatch",
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
    resolved_path = repo_root / "docs" / "r02-d4-s1-resolved-seed.json"
    _require_equal(
        sha256_hex(resolved_path.read_bytes()),
        R02_D4_S2_RESOLVED_SEED_ARTIFACT_SHA256,
        "resolved seed artifact drift",
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
        "r02_d3_live_selector_adapter",
    }
