"""Provider-free R02 D2c representative/challenge frame construction and seal."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from . import fixtures
from .artifacts import AppendOnlyArtifactStore
from .baselines import primary_deterministic
from .canonical import canonical_json_bytes, canonical_sha256, sha256_hex
from .contracts import ArtifactReference, GeneratorConfig, StrictModel, SyntheticEpisode
from .fixtures import generate_episode
from .oracle import solve_oracle
from .r02_audit import R02AppendOnlyArtifactStore
from .r02_candidates import prepare_provider_free_episode
from .r02_contracts import R02PreparationState, R02_FREEZE_SHA256
from .scoring import score_episode


R02_D1_MANIFEST_SHA256 = (
    "81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf"
)
R02_D2B_BASE_COMMIT = "0f670bb5fd1eccf9ecd6083d2f245311bf3ba34d"
R02_FRAME_SCHEMA_VERSION = "r02-d2c-frame-manifest-v1"
R02_FRAME_REPRESENTATIVE_COUNT = 120
R02_FRAME_CHALLENGE_COUNT = 40
R02_FRAME_CHALLENGE_SCAN_START = R02_FRAME_REPRESENTATIVE_COUNT
R02_FRAME_CHALLENGE_SCAN_LIMIT = 4_096
R02_FRAME_TARGET_WEIGHT_DENOMINATOR = 4
R02_FRAME_REPRESENTATIVE_WEIGHT_NUMERATOR = 3
R02_FRAME_CHALLENGE_WEIGHT_NUMERATOR = 1
R02_FRAME_ROOT_SEED_DERIVATION = (
    "sha256(canonical_json({domain,r02_d1_freeze_sha256,"
    "r02_d1_manifest_sha256,r02_d2b_base_commit}))"
)
R02_FRAME_ROOT_SEED_HEX = sha256_hex(
    canonical_json_bytes(
        {
            "domain": "r02-d2c-provider-free-frame-v1",
            "r02_d1_freeze_sha256": R02_FREEZE_SHA256,
            "r02_d1_manifest_sha256": R02_D1_MANIFEST_SHA256,
            "r02_d2b_base_commit": R02_D2B_BASE_COMMIT,
        }
    )
)
R02_FRAME_ID = f"r02-d2c-frame-{R02_FRAME_ROOT_SEED_HEX[:12]}"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_R02_FRAME_ARTIFACT_ROOT = ROOT / ".research_artifacts" / R02_FRAME_ID


class R02FrameError(RuntimeError):
    pass


class R02FrameStratum(StrEnum):
    REPRESENTATIVE = "REPRESENTATIVE"
    CHALLENGE_HEADROOM = "CHALLENGE_HEADROOM"


class R02ChallengeDisposition(StrEnum):
    NOT_TRIGGERED = "NOT_TRIGGERED"
    INELIGIBLE_CANDIDATE_COLLAPSE = "INELIGIBLE_CANDIDATE_COLLAPSE"
    NO_POSITIVE_CANDIDATE_HEADROOM = "NO_POSITIVE_CANDIDATE_HEADROOM"
    ADMITTED = "ADMITTED"


class R02ChallengeScanRecord(StrictModel):
    schema_version: Literal["r02-challenge-scan-record-v1"] = (
        "r02-challenge-scan-record-v1"
    )
    source_index: int = Field(ge=0)
    fixture_id: str
    fixture_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_state_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    regime: str
    triggered: bool
    candidate_count: int = Field(ge=0, le=4)
    eligible_opportunity: bool
    baseline_utility_e12: int
    best_candidate_utility_e12: int | None = None
    candidate_headroom_e12: int | None = Field(default=None, ge=0)
    best_candidate_canonical_id: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    disposition: R02ChallengeDisposition
    admitted: bool

    @model_validator(mode="after")
    def validate_classification(self) -> "R02ChallengeScanRecord":
        if self.admitted != (self.disposition is R02ChallengeDisposition.ADMITTED):
            raise ValueError("challenge admission and disposition disagree")
        if self.eligible_opportunity != (self.triggered and self.candidate_count >= 2):
            raise ValueError("challenge eligible-opportunity flag mismatch")
        scored = (
            self.best_candidate_utility_e12,
            self.candidate_headroom_e12,
            self.best_candidate_canonical_id,
        )
        if self.eligible_opportunity:
            if any(value is None for value in scored):
                raise ValueError("eligible challenge classification lacks candidate score")
            assert self.best_candidate_utility_e12 is not None
            assert self.candidate_headroom_e12 is not None
            if (
                self.candidate_headroom_e12
                != self.best_candidate_utility_e12 - self.baseline_utility_e12
            ):
                raise ValueError("challenge candidate headroom arithmetic mismatch")
            if self.admitted != (self.candidate_headroom_e12 > 0):
                raise ValueError("challenge admission must require strictly positive headroom")
        elif any(value is not None for value in scored):
            raise ValueError("ineligible challenge classification cannot contain candidate score")
        if not self.triggered and self.disposition is not R02ChallengeDisposition.NOT_TRIGGERED:
            raise ValueError("non-triggered challenge disposition mismatch")
        return self


class R02ChallengeScan(StrictModel):
    schema_version: Literal["r02-challenge-scan-v1"] = "r02-challenge-scan-v1"
    frame_id: str
    root_seed_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    scan_start_index: Literal[R02_FRAME_CHALLENGE_SCAN_START] = (
        R02_FRAME_CHALLENGE_SCAN_START
    )
    scan_limit: int = Field(ge=1)
    records: tuple[R02ChallengeScanRecord, ...] = Field(min_length=1)
    admitted_source_indexes: tuple[int, ...] = Field(min_length=1)
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False

    @model_validator(mode="after")
    def validate_scan(self) -> "R02ChallengeScan":
        indexes = tuple(record.source_index for record in self.records)
        if indexes != tuple(range(self.scan_start_index, self.scan_start_index + len(indexes))):
            raise ValueError("challenge scan indexes must be contiguous and ordered")
        if len(indexes) > self.scan_limit:
            raise ValueError("challenge scan exceeds its frozen limit")
        admitted = tuple(record.source_index for record in self.records if record.admitted)
        if admitted != self.admitted_source_indexes:
            raise ValueError("challenge admitted-index record mismatch")
        if self.records[-1].source_index != admitted[-1]:
            raise ValueError("challenge scan must stop at the final required admission")
        return self


class R02FrameCase(StrictModel):
    schema_version: Literal["r02-frame-case-v1"] = "r02-frame-case-v1"
    frame_ordinal: int = Field(ge=0)
    stratum: R02FrameStratum
    source_index: int = Field(ge=0)
    fixture_id: str
    fixture_seed_hex: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    public_state_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_artifact: ArtifactReference
    regime: str
    baseline_utility_e12: int
    oracle_utility_e12: int
    oracle_minus_baseline_e12: int = Field(ge=0)
    triggered: bool
    candidate_count: int = Field(ge=0, le=4)
    eligible_opportunity: bool
    candidate_headroom_e12: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_case(self) -> "R02FrameCase":
        if self.oracle_minus_baseline_e12 != self.oracle_utility_e12 - self.baseline_utility_e12:
            raise ValueError("frame oracle-minus-baseline arithmetic mismatch")
        if self.eligible_opportunity != (self.triggered and self.candidate_count >= 2):
            raise ValueError("frame eligible-opportunity flag mismatch")
        if self.eligible_opportunity != (self.candidate_headroom_e12 is not None):
            raise ValueError("frame candidate-headroom presence mismatch")
        if self.stratum is R02FrameStratum.CHALLENGE_HEADROOM:
            if not self.eligible_opportunity or not self.candidate_headroom_e12:
                raise ValueError("challenge frame case must have positive candidate headroom")
        return self


class R02FrameManifest(StrictModel):
    schema_version: Literal["r02-d2c-frame-manifest-v1"] = R02_FRAME_SCHEMA_VERSION
    status: Literal["PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"] = (
        "PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
    )
    frame_id: str
    base_commit: Literal[R02_D2B_BASE_COMMIT] = R02_D2B_BASE_COMMIT
    r02_d1_freeze_sha256: Literal[R02_FREEZE_SHA256] = R02_FREEZE_SHA256
    r02_d1_manifest_sha256: Literal[R02_D1_MANIFEST_SHA256] = R02_D1_MANIFEST_SHA256
    root_seed_hex: Literal[R02_FRAME_ROOT_SEED_HEX] = R02_FRAME_ROOT_SEED_HEX
    root_seed_derivation: Literal[R02_FRAME_ROOT_SEED_DERIVATION] = (
        R02_FRAME_ROOT_SEED_DERIVATION
    )
    generator_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fixture_generator_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frame_builder_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    representative_count: int = Field(ge=1)
    challenge_count: int = Field(ge=1)
    total_count: int = Field(ge=2)
    representative_target_weight_numerator: Literal[
        R02_FRAME_REPRESENTATIVE_WEIGHT_NUMERATOR
    ] = R02_FRAME_REPRESENTATIVE_WEIGHT_NUMERATOR
    challenge_target_weight_numerator: Literal[R02_FRAME_CHALLENGE_WEIGHT_NUMERATOR] = (
        R02_FRAME_CHALLENGE_WEIGHT_NUMERATOR
    )
    target_weight_denominator: Literal[R02_FRAME_TARGET_WEIGHT_DENOMINATOR] = (
        R02_FRAME_TARGET_WEIGHT_DENOMINATOR
    )
    challenge_scan_start_index: int = Field(ge=0)
    challenge_scan_limit: int = Field(ge=1)
    challenge_scanned_count: int = Field(ge=1)
    challenge_scan: ArtifactReference
    representative_trigger_count: int = Field(ge=0)
    representative_eligible_count: int = Field(ge=0)
    challenge_trigger_count: int = Field(ge=1)
    challenge_eligible_count: int = Field(ge=1)
    total_eligible_count: int = Field(ge=1)
    duplicate_policy: Literal["INVALID_FRAME_NO_SKIP"] = "INVALID_FRAME_NO_SKIP"
    near_duplicate_policy: Literal[
        "CANONICAL_PUBLIC_STATE_EXCLUDING_CASE_ID_AND_SEED_INVALID_FRAME_NO_SKIP"
    ] = "CANONICAL_PUBLIC_STATE_EXCLUDING_CASE_ID_AND_SEED_INVALID_FRAME_NO_SKIP"
    oracle_barrier: Literal[
        "CLASSIFICATION_AFTER_TRIGGER_AND_CANDIDATE_BYTES_SELECTOR_INACCESSIBLE"
    ] = "CLASSIFICATION_AFTER_TRIGGER_AND_CANDIDATE_BYTES_SELECTOR_INACCESSIBLE"
    cases: tuple[R02FrameCase, ...]
    payload_file_count: int = Field(ge=2)
    payload_tree_algorithm: Literal[
        "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    ] = "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    payload_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False
    trigger_threshold_bps: Literal[50] = 50
    trigger_recalibrated_after_frame: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "R02FrameManifest":
        if self.total_count != self.representative_count + self.challenge_count:
            raise ValueError("frame count arithmetic mismatch")
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
        uniqueness = (
            (case.fixture_id for case in self.cases),
            (case.source_index for case in self.cases),
            (case.fixture_content_sha256 for case in self.cases),
            (case.public_state_fingerprint_sha256 for case in self.cases),
            (case.fixture_artifact.relative_path for case in self.cases),
        )
        if any(len(set(values)) != self.total_count for values in uniqueness):
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


class R02FrameSeal(StrictModel):
    schema_version: Literal["r02-d2c-frame-seal-v1"] = "r02-d2c-frame-seal-v1"
    status: Literal["PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"] = (
        "PENDING_INDEPENDENT_REVIEW_AND_USER_ACCEPTANCE"
    )
    frame_id: str
    artifact_root_relative_path: str
    frame_manifest: ArtifactReference
    full_tree_file_count: int = Field(ge=3)
    full_tree_algorithm: Literal[
        "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    ] = "SHA256_SORTED_RELATIVE_PATH_NUL_SIZE_NUL_FILE_SHA256_NEWLINE"
    full_tree_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider_calls: Literal[0] = 0
    live_execution: Literal[False] = False


@dataclass(frozen=True)
class R02FrameBuild:
    representative_episodes: tuple[SyntheticEpisode, ...]
    challenge_episodes: tuple[SyntheticEpisode, ...]
    representative_classifications: tuple[R02ChallengeScanRecord, ...]
    challenge_scan: R02ChallengeScan


def _frame_builder_source_sha256() -> str:
    return sha256_hex(Path(__file__).read_bytes())


def _fixture_generator_source_sha256() -> str:
    return sha256_hex(Path(fixtures.__file__).read_bytes())


def _public_state_fingerprint(episode: SyntheticEpisode) -> str:
    public = episode.public.model_dump(mode="python")
    public.pop("case_id")
    public.pop("seed_hex")
    return canonical_sha256(public)


def _classify_episode(
    episode: SyntheticEpisode,
    *,
    source_index: int,
) -> R02ChallengeScanRecord:
    preparation = prepare_provider_free_episode(
        episode,
        experiment_id=R02_FRAME_ID,
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
            raise R02FrameError("triggered frame classification hit an integrity stop")
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
        raw_by_id = {}
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
        public_state_fingerprint_sha256=_public_state_fingerprint(episode),
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


def build_provider_free_frame(
    *,
    representative_count: int = R02_FRAME_REPRESENTATIVE_COUNT,
    challenge_count: int = R02_FRAME_CHALLENGE_COUNT,
    challenge_scan_limit: int = R02_FRAME_CHALLENGE_SCAN_LIMIT,
) -> R02FrameBuild:
    if representative_count <= 0 or challenge_count <= 0 or challenge_scan_limit <= 0:
        raise ValueError("frame counts and scan limit must be positive")
    config = GeneratorConfig()
    representative = tuple(
        generate_episode(config, R02_FRAME_ROOT_SEED_HEX, index)
        for index in range(representative_count)
    )
    representative_classifications = tuple(
        _classify_episode(episode, source_index=index)
        for index, episode in enumerate(representative)
    )
    seen_content = {episode.content_sha256 for episode in representative}
    seen_public = {_public_state_fingerprint(episode) for episode in representative}
    if len(seen_content) != representative_count or len(seen_public) != representative_count:
        raise R02FrameError("representative prefix contains duplicate or near-duplicate cases")

    challenge: list[SyntheticEpisode] = []
    scan_records: list[R02ChallengeScanRecord] = []
    scan_start = R02_FRAME_CHALLENGE_SCAN_START
    for source_index in range(scan_start, scan_start + challenge_scan_limit):
        episode = generate_episode(config, R02_FRAME_ROOT_SEED_HEX, source_index)
        fingerprint = _public_state_fingerprint(episode)
        if episode.content_sha256 in seen_content or fingerprint in seen_public:
            raise R02FrameError("challenge scan encountered a duplicate or near-duplicate case")
        classification = _classify_episode(episode, source_index=source_index)
        scan_records.append(classification)
        if classification.admitted:
            challenge.append(episode)
            seen_content.add(episode.content_sha256)
            seen_public.add(fingerprint)
            if len(challenge) == challenge_count:
                break
    if len(challenge) != challenge_count:
        raise R02FrameError("challenge scan limit exhausted before filling the frame")
    challenge_scan = R02ChallengeScan(
        frame_id=R02_FRAME_ID,
        root_seed_hex=R02_FRAME_ROOT_SEED_HEX,
        scan_start_index=scan_start,
        scan_limit=challenge_scan_limit,
        records=tuple(scan_records),
        admitted_source_indexes=tuple(
            record.source_index for record in scan_records if record.admitted
        ),
    )
    return R02FrameBuild(
        representative_episodes=representative,
        challenge_episodes=tuple(challenge),
        representative_classifications=representative_classifications,
        challenge_scan=challenge_scan,
    )


def _tree_sha256(references: tuple[ArtifactReference, ...]) -> str:
    records = "\n".join(
        f"{reference.relative_path}\0{reference.size_bytes}\0{reference.sha256}"
        for reference in sorted(references, key=lambda item: item.relative_path)
    )
    return sha256_hex(records.encode("utf-8"))


def _filesystem_tree(root: Path) -> tuple[int, str]:
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
    return len(references), _tree_sha256(tuple(references))


def persist_provider_free_frame(
    build: R02FrameBuild,
    *,
    artifact_root: str | Path = DEFAULT_R02_FRAME_ARTIFACT_ROOT,
) -> tuple[R02FrameManifest, R02FrameSeal]:
    store = R02AppendOnlyArtifactStore(artifact_root)
    fixture_references = []
    episodes = (*build.representative_episodes, *build.challenge_episodes)
    for ordinal, episode in enumerate(episodes):
        stratum = (
            "representative"
            if ordinal < len(build.representative_episodes)
            else "challenge"
        )
        stratum_ordinal = (
            ordinal
            if stratum == "representative"
            else ordinal - len(build.representative_episodes)
        )
        fixture_references.append(
            store.write_json(
                f"fixtures/{stratum}/{stratum_ordinal:04d}.json",
                episode,
            )
        )
    challenge_scan_reference = store.write_json(
        "challenge_scan.json",
        build.challenge_scan,
    )
    classifications = (
        *build.representative_classifications,
        *(
            record
            for record in build.challenge_scan.records
            if record.admitted
        ),
    )
    cases = []
    for ordinal, (episode, classification, reference) in enumerate(
        zip(episodes, classifications, fixture_references, strict=True)
    ):
        oracle = solve_oracle(episode)
        stratum = (
            R02FrameStratum.REPRESENTATIVE
            if ordinal < len(build.representative_episodes)
            else R02FrameStratum.CHALLENGE_HEADROOM
        )
        cases.append(
            R02FrameCase(
                frame_ordinal=ordinal,
                stratum=stratum,
                source_index=classification.source_index,
                fixture_id=episode.public.case_id,
                fixture_seed_hex=episode.public.seed_hex,
                fixture_content_sha256=episode.content_sha256,
                public_state_fingerprint_sha256=(
                    classification.public_state_fingerprint_sha256
                ),
                fixture_artifact=reference,
                regime=episode.hidden.regime,
                baseline_utility_e12=classification.baseline_utility_e12,
                oracle_utility_e12=oracle.score.utility_e12,
                oracle_minus_baseline_e12=(
                    oracle.score.utility_e12 - classification.baseline_utility_e12
                ),
                triggered=classification.triggered,
                candidate_count=classification.candidate_count,
                eligible_opportunity=classification.eligible_opportunity,
                candidate_headroom_e12=classification.candidate_headroom_e12,
            )
        )
    payload_references = (*fixture_references, challenge_scan_reference)
    representative = tuple(cases[: len(build.representative_episodes)])
    challenge = tuple(cases[len(build.representative_episodes) :])
    manifest = R02FrameManifest(
        frame_id=R02_FRAME_ID,
        generator_config_sha256=canonical_sha256(GeneratorConfig()),
        fixture_generator_source_sha256=_fixture_generator_source_sha256(),
        frame_builder_source_sha256=_frame_builder_source_sha256(),
        representative_count=len(representative),
        challenge_count=len(challenge),
        total_count=len(cases),
        challenge_scan_start_index=build.challenge_scan.scan_start_index,
        challenge_scan_limit=build.challenge_scan.scan_limit,
        challenge_scanned_count=len(build.challenge_scan.records),
        challenge_scan=challenge_scan_reference,
        representative_trigger_count=sum(case.triggered for case in representative),
        representative_eligible_count=sum(
            case.eligible_opportunity for case in representative
        ),
        challenge_trigger_count=sum(case.triggered for case in challenge),
        challenge_eligible_count=sum(case.eligible_opportunity for case in challenge),
        total_eligible_count=sum(case.eligible_opportunity for case in cases),
        cases=tuple(cases),
        payload_file_count=len(payload_references),
        payload_tree_sha256=_tree_sha256(tuple(payload_references)),
    )
    manifest_reference = store.write_json("frame_manifest.json", manifest)
    full_tree_file_count, full_tree_sha256 = _filesystem_tree(store.root)
    root_path = store.root.resolve()
    try:
        root_relative = root_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        root_relative = root_path.as_posix()
    seal = R02FrameSeal(
        frame_id=R02_FRAME_ID,
        artifact_root_relative_path=root_relative,
        frame_manifest=manifest_reference,
        full_tree_file_count=full_tree_file_count,
        full_tree_sha256=full_tree_sha256,
    )
    return manifest, seal


def verify_persisted_frame(
    store: AppendOnlyArtifactStore,
    seal: R02FrameSeal,
) -> R02FrameManifest:
    manifest = R02FrameManifest.model_validate_json(store.read_bytes(seal.frame_manifest))
    if manifest.frame_id != seal.frame_id:
        raise R02FrameError("frame seal identity mismatch")
    scan = R02ChallengeScan.model_validate_json(store.read_bytes(manifest.challenge_scan))
    admitted = tuple(record.source_index for record in scan.records if record.admitted)
    challenge_indexes = tuple(
        case.source_index
        for case in manifest.cases
        if case.stratum is R02FrameStratum.CHALLENGE_HEADROOM
    )
    if admitted != challenge_indexes:
        raise R02FrameError("challenge scan admissions do not match frame cases")
    payload_references = tuple(case.fixture_artifact for case in manifest.cases) + (
        manifest.challenge_scan,
    )
    if _tree_sha256(payload_references) != manifest.payload_tree_sha256:
        raise R02FrameError("frame payload tree mismatch")
    for case in manifest.cases:
        episode = SyntheticEpisode.model_validate_json(store.read_bytes(case.fixture_artifact))
        if episode.public.case_id != case.fixture_id:
            raise R02FrameError("frame fixture ID mismatch")
        if episode.content_sha256 != case.fixture_content_sha256:
            raise R02FrameError("frame fixture content identity mismatch")
        if _public_state_fingerprint(episode) != case.public_state_fingerprint_sha256:
            raise R02FrameError("frame public-state fingerprint mismatch")
    count, tree_sha256 = _filesystem_tree(store.root)
    if count != seal.full_tree_file_count or tree_sha256 != seal.full_tree_sha256:
        raise R02FrameError("frame full-tree seal mismatch")
    return manifest


def _write_new(path: Path, value: StrictModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical_json_bytes(value))
        handle.write(b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_R02_FRAME_ARTIFACT_ROOT)
    parser.add_argument("--seal-output", type=Path)
    parser.add_argument("--manifest-copy-output", type=Path)
    args = parser.parse_args(argv)
    build = build_provider_free_frame()
    manifest, seal = persist_provider_free_frame(build, artifact_root=args.artifact_root)
    verify_persisted_frame(R02AppendOnlyArtifactStore(args.artifact_root), seal)
    if args.seal_output is not None:
        _write_new(args.seal_output, seal)
    if args.manifest_copy_output is not None:
        _write_new(args.manifest_copy_output, manifest)
    print(canonical_json_bytes(seal).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
