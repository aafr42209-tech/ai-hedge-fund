"""Provider-free Codex feature and isolation gates for R01 Phase B2."""

from __future__ import annotations

from pathlib import Path

from .contracts import (
    CodexFeatureCatalogEntry,
    CodexFeatureGate,
    codex_feature_catalog_definition_sha256,
    codex_feature_catalog_snapshot_sha256,
    codex_pilot_sandbox_identity_sha256,
)

PINNED_CODEX_FEATURE_CATALOG_COUNT = 92


def parse_codex_feature_catalog(
    raw: bytes,
    *,
    expected_count: int = PINNED_CODEX_FEATURE_CATALOG_COUNT,
) -> tuple[CodexFeatureCatalogEntry, ...]:
    """Parse every `codex features list` row without fixed-width assumptions."""

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("feature catalog is not valid UTF-8") from exc
    lines = text.rstrip("\r\n").splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ValueError("feature catalog contains no rows or an empty row")
    entries: list[CodexFeatureCatalogEntry] = []
    for line_number, line in enumerate(lines, start=1):
        tokens = line.split()
        if len(tokens) < 3 or tokens[-1] not in {"true", "false"}:
            raise ValueError(f"unparsed feature catalog row {line_number}")
        entries.append(
            CodexFeatureCatalogEntry(
                name=tokens[0],
                stage=" ".join(tokens[1:-1]),
                enabled=tokens[-1] == "true",
            )
        )
    if len(entries) != expected_count:
        raise ValueError(f"feature catalog row count {len(entries)} != pinned {expected_count}")
    ordered = tuple(sorted(entries, key=lambda entry: entry.name))
    if len({entry.name for entry in ordered}) != len(ordered):
        raise ValueError("feature catalog contains duplicate names")
    return ordered


def build_codex_feature_gate(
    baseline_catalog: tuple[CodexFeatureCatalogEntry, ...],
    post_disable_catalog: tuple[CodexFeatureCatalogEntry, ...],
    *,
    active_feature_allowlist: tuple[str, ...],
    expected_feature_catalog_sha256: str,
) -> CodexFeatureGate:
    """Bind one complete catalog and reject any post-disable feature escape."""

    baseline = tuple(sorted(baseline_catalog, key=lambda entry: entry.name))
    post_disable = tuple(sorted(post_disable_catalog, key=lambda entry: entry.name))
    actual_catalog_sha256 = codex_feature_catalog_snapshot_sha256(baseline)
    if actual_catalog_sha256 != expected_feature_catalog_sha256:
        raise RuntimeError("feature catalog differs from the external trust anchor")
    catalog_definition_sha256 = codex_feature_catalog_definition_sha256(baseline)
    if catalog_definition_sha256 != codex_feature_catalog_definition_sha256(post_disable):
        raise RuntimeError("post-disable feature catalog definition drifted")
    allowlist = tuple(sorted(set(active_feature_allowlist)))
    if len(allowlist) != len(active_feature_allowlist):
        raise ValueError("active feature allowlist contains duplicates")
    catalog_names = tuple(entry.name for entry in baseline)
    if not set(allowlist).issubset(catalog_names):
        raise ValueError("active feature allowlist contains an unknown feature")
    disabled = tuple(sorted(set(catalog_names) - set(allowlist)))
    post_true = tuple(entry.name for entry in post_disable if entry.enabled)
    return CodexFeatureGate(
        feature_catalog=baseline,
        feature_catalog_sha256=actual_catalog_sha256,
        feature_catalog_definition_sha256=catalog_definition_sha256,
        baseline_effective_true_features=tuple(entry.name for entry in baseline if entry.enabled),
        active_feature_allowlist=allowlist,
        disabled_features=disabled,
        post_disable_effective_true_features=post_true,
    )


def pilot_sandbox_identity_sha256(working_directory: str) -> str:
    """Validate one empty out-of-repository sandbox and return its identity."""

    directory = Path(working_directory)
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("pilot sandbox must be an existing absolute directory")
    if directory.is_symlink():
        raise ValueError("pilot sandbox cannot be a symbolic link")
    resolved = directory.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    if resolved == repository_root or repository_root in resolved.parents:
        raise ValueError("pilot sandbox must be outside the repository tree")
    entries = tuple(sorted(path.name for path in resolved.iterdir()))
    if entries:
        raise ValueError("pilot sandbox must be empty before every launch")
    return codex_pilot_sandbox_identity_sha256(str(resolved))
