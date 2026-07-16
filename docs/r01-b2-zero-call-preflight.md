# R01 Phase B2 zero-call preflight

Status: `D2_APPROVED_B3_PREFLIGHT_IMPLEMENTED_REVIEW_PENDING`

Observation date: `2026-07-14`; D2 approval recorded `2026-07-16` (Asia/Seoul)

Provider calls made: `0`

D2 cross-review package: `docs/r01-d2-decision-package.md`.

Evaluation fixtures generated: `0`

## Trust anchors

- Code commit: `fe521fefcaf25475a7bd92c8626f6eccd6ca3033`
- Research contract SHA-256: `f1e46e11397ab1dd41cc1bda3c2f2c20720201733bb2d2e6a192d6cf241c69f3`
- B3 readiness implementation base commit: `bdc0827`
- Provider-free freeze SHA-256: `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`
- Provider-free regime-gap summary SHA-256: `0e6e8945f93779a77ffc7687d63062c010efd3aee3d6c8062551e54108fbf886`
- Exact-tag Codex source feature proof SHA-256: `1de5d131356deb6dec8186eb07795e47717d4960937b9142689a5e9cc3554f91`
- Source tag/commit: `rust-v0.144.1` / `44918ea10c0f99151c6710411b4322c2f5c96bea`
- D2 decision package SHA-256: `bf9597c14460fdebf104fd7ff10789256857f07a3a2d44c086d0afa527099d8e`
- D2 user approval record SHA-256: `95e55764963cc86e18e6e66348956bcde84082e3f0da28faf1c60145eb4e150c`
- Zero-cost account attestation SHA-256: `94ca690340273e02da7de19e0c1ea5efc8793547f2a87822dc40eb5b630b9746`
- Freeze root-seed label: `r01-phase-b-development-fixtures-v1`
- Freeze fixture count: `40`
- Root-seed and fixture-count match: `true`
- Final prompt SHA-256: `TBD_D3_AFTER_B3_CANDIDATE_REVIEW`

## Local Codex identity

- CLI version: `codex-cli 0.144.1`
- Authentication mode: `ChatGPT`; no credential was recorded.
- Launcher: `%USERPROFILE%/AppData/Roaming/npm/codex.ps1`
- Launcher SHA-256: `0c149db80ed0bf442c810146b0ad0163b74982fe4542d673f56c354d7b8229cb`
- Package manifest: `%USERPROFILE%/AppData/Roaming/npm/node_modules/@openai/codex/package.json`
- Package-manifest SHA-256: `e9756b0cb1e3a6f678ac9848365b6f3a22f11cede8348b883c2c05cb9c31705b`
- Resolved native executable: `%USERPROFILE%/AppData/Roaming/npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe`
- Native-executable SHA-256: `cbacbb9726262ef558b4af0438a1b2a5bba9076132401d947b5b4d2bf92ab0e4`
- Installed package dependency lock: absent.
- Exact selected model: `gpt-5.6-sol`
- User-visible reasoning effort: `high`
- User-visible service tier: provider default
- Provider-managed model availability and routing: not frozen and not queried by this zero-call preflight.
- Transport model-echo availability: `UNESTABLISHED_ZERO_CALL`; absence is an approved D2 identity limitation, while any observed mismatch is a `STOP_PHASE` condition.
- Global-flag placement check: the zero-call command `codex --disable shell_tool exec --help` exited successfully and returned the pinned `codex exec` help surface.
- Every provider-free subprocess command has a fixed `30`-second timeout; expiry fails the preflight closed.

## Reproduction artifacts

- Reproducer: `scripts/r01_b2_preflight.py`; it permits only version, login-status, feature-list, all-feature-disable feature-list, and global-disable `exec --help` commands. It contains no provider acquisition command.
- Canonical capture summary: `docs/r01-b2-zero-call-capture.json`, SHA-256 `409ee28ca3dc83aa69b6bacaefcd957c2c7641780af852f63ab8feb290c55242`.
- Baseline catalog preimage: `docs/r01-b2-codex-features-baseline.raw.b64`, artifact SHA-256 `339b7ba47c67851dde94e3c1d8247a8374399bb34330b2d0a61edf2f44f4452b`; base64 decoding yields the exact 92-row stdout bytes with SHA-256 `d3d16f7d0639ce0b8fdce02078b0af7f2b8e9cc1476aa55e91b3ce83c1768afa`.
- Post-disable catalog preimage: `docs/r01-b2-codex-features-post-disable.raw.b64`, artifact SHA-256 `31e5af5a9e7bd19f163c995b3dbc7f0055052db7d231b06221d22356535982a2`; decoded stdout SHA-256 `662c755fa3e6d3edc2b0f9cd616e4bf17517c654c3d930c0159f9f1c41a6d2fa`.
- Global-flag help preimage: `docs/r01-b2-codex-global-disable-help.raw.b64`, artifact SHA-256 `049104832fb82b7c76534e1ba35f9cb0614e8d3df532f01cbaf803c7a9f34095`; decoded stdout SHA-256 `9f86f0115238ddde2514587e5f95b0ab0aa6b89495e5912878d49ad26038aa19`.
- Every raw artifact is reversible base64 of exact captured bytes with no trailing artifact newline. Regeneration uses exclusive creation and therefore cannot overwrite this observation.

## Feature-catalog result

- Strictly parsed rows: `92`; unparsed rows: `0`.
- Stage counts: removed `30`, stable `29`, under development `27`, experimental `3`, deprecated `3`.
- Baseline effective-true count: `35`.
- Full snapshot SHA-256: `14b554bd29e409dd348878c18ad8b0820a1165772039bb839b538dca03956aad`.
- Name/stage definition SHA-256: `aa86f33bf40be81c79fdcbc6254b8162bf9d081b5ff1a7634f669223fea1d530`.
- Desired active feature allowlist: empty.
- Generated disable set: all `92` catalog names below.
- Post-disable definition hash: unchanged.
- Post-disable effective-false count: `88`.
- Post-disable effective-true count: `4`.
- Residual effective-true entries: `resize_all_images`, `terminal_resize_reflow`, `tool_search_always_defer_mcp_tools`, `tui_app_server`.
- Residual runtime inertness:
  `SOURCE_ESTABLISHED_REMOVED_NOOP_D2_ACCEPTED`. Exact tagged source
  explicitly ignores all four config keys and has no behavior consumer outside
  the feature registry, removed-key guards, and tests. The stage label alone was
  not used as evidence.
- Six command-spec SHA-256 values: generated only by the one-shot B3 preflight
  after the implementation commit; the provider-free generator is implemented
  and covered by the overlay regression suite.
- Gate result: `D2_APPROVED_NOOP_ALLOWLIST`; provider execution remains blocked
  until the generated B3 preflight hash and implementation commit pass external
  review.

`baseline` is the effective value before generated disables.

| name | stage | baseline |
|---|---|---:|
| apply_patch_freeform | removed | false |
| apply_patch_streaming_events | under development | false |
| apps | stable | true |
| apps_mcp_path_override | removed | false |
| artifact | under development | false |
| auth_elicitation | stable | true |
| browser_use | stable | true |
| browser_use_external | stable | true |
| browser_use_full_cdp_access | stable | true |
| chronicle | under development | false |
| code_mode | under development | false |
| code_mode_host | stable | true |
| code_mode_only | under development | false |
| codex_git_commit | removed | false |
| collaboration_modes | removed | true |
| computer_use | stable | true |
| concurrent_reasoning_summaries | under development | false |
| current_time_reminder | under development | false |
| default_mode_request_user_input | under development | false |
| deferred_executor | under development | false |
| elevated_windows_sandbox | removed | false |
| enable_fanout | under development | false |
| enable_mcp_apps | under development | false |
| enable_request_compression | stable | true |
| exec_permission_approvals | under development | false |
| experimental_windows_sandbox | removed | false |
| external_migration | removed | false |
| fast_mode | stable | true |
| goals | stable | true |
| guardian_approval | stable | true |
| hooks | stable | true |
| image_detail_original | removed | false |
| image_generation | stable | true |
| in_app_browser | stable | true |
| item_ids | under development | false |
| js_repl | removed | false |
| js_repl_tools_only | removed | false |
| local_thread_store_compression | under development | false |
| memories | experimental | false |
| mentions_v2 | stable | true |
| multi_agent | stable | true |
| multi_agent_mode | removed | false |
| multi_agent_v2 | under development | false |
| network_proxy | experimental | false |
| non_prefixed_mcp_tool_names | under development | false |
| personality | stable | true |
| plugin_hooks | removed | false |
| plugin_sharing | stable | true |
| plugins | stable | true |
| prevent_idle_sleep | experimental | false |
| realtime_conversation | under development | false |
| remote_compaction_v2 | stable | true |
| remote_control | removed | false |
| remote_models | removed | false |
| remote_plugin | stable | true |
| request_permissions_tool | under development | false |
| request_rule | removed | false |
| resize_all_images | removed | true |
| respect_system_proxy | under development | false |
| responses_websockets | removed | false |
| responses_websockets_v2 | removed | false |
| rollout_budget | under development | false |
| runtime_metrics | under development | false |
| search_tool | removed | false |
| secret_auth_storage | stable | true |
| shell_snapshot | stable | true |
| shell_tool | stable | true |
| shell_zsh_fork | under development | false |
| skill_env_var_dependency_prompt | removed | false |
| skill_mcp_dependency_install | stable | true |
| sqlite | removed | true |
| standalone_web_search | under development | false |
| steer | removed | true |
| terminal_resize_reflow | removed | true |
| terminal_visualization_instructions | under development | false |
| token_budget | under development | false |
| tool_call_mcp_elicitation | stable | true |
| tool_search | removed | false |
| tool_search_always_defer_mcp_tools | removed | true |
| tool_suggest | stable | true |
| tui_app_server | removed | true |
| unavailable_dummy_tools | removed | false |
| undo | removed | false |
| unified_exec | stable | false |
| unified_exec_zsh_fork | under development | false |
| use_agent_identity | under development | false |
| use_legacy_landlock | deprecated | false |
| use_linux_sandbox_bwrap | removed | false |
| web_search_cached | deprecated | false |
| web_search_request | deprecated | false |
| workspace_dependencies | stable | true |
| workspace_owner_usage_nudge | removed | false |

## Isolation and surface removal

- Pilot sandbox: `%LOCALAPPDATA%/Temp/r01-codex-pilot-sandbox-c916696`.
- Pilot-sandbox identity SHA-256: `234601e39170d4dd121da8ebbeb0f99657c56e1ca7ab69f5d2ff531d1d5c812d`.
- Absolute, outside repository, non-symlink, empty at check: `true`.
- B2 runner exceptions: OS/subprocess launch errors are retryable; phase-stop and unexpected programming errors are preserved, not reclassified.
- Shell, exec, browser, app, plugin, MCP, external-context, workspace-dependency, personality, request-compression, remote-compaction, and fast-mode feature disables were generated from the complete catalog.
- Runtime removal proof: exact-tag source proof is available in
  `docs/r01-b2-codex-source-feature-proof.json`; D2 acceptance is still pending,
  so no acquisition command may be built.
- Source-proof limitation: package version `0.144.1` attributes the prebuilt npm
  binary to `rust-v0.144.1`, but no reproducible build cryptographically proves
  binary-to-commit identity. Any package/binary/source drift invalidates the
  four-entry no-op conclusion.
- `enable_request_compression`, `remote_compaction_v2`, and `fast_mode`: baseline `true`, post-disable `false`.
- Secrets in argv, prompt, config, artifacts, or logs: none observed; secret-bearing config keys and recognizable secret-bearing values are rejected by the command-spec validator.

## Budget and post-D2 execution blockers

- Development attempt cap: `200`.
- Development attempts spent: `0`.
- Development attempts remaining: `200`.
- Development token cap: `6400000`.
- Per-attempt token reserve: `32000`.
- USD cap: `0`; ChatGPT subscription use does not authorize purchased-credit
  drawdown, automatic top-up, shared-credit use, overage, or API billing.
- High-transaction-cost stratum: `6/7` zero oracle-hold gaps; D2 treatment is
  `ACCEPT_UNCHANGED_AND_CARRY_POWER_COST`.
- Transport disposition policy: `FROZEN_PRE_D2`. Parser-originated `STOP_PHASE` always dominates timeout/nonzero wrapping; retry wrappers retain the original code and disposition; a complete transport with timeout or nonzero process status is `STOP_PHASE`, never hold.
- Retry budget policy: attempt-1 `nonzero_exit_without_complete_response` is
  `STOP_PHASE`; other transport failures may advance once to attempt 2; the
  second consecutive `RETRY_TRANSPORT` is converted to `STOP_PHASE` before a
  third call; the global `200`-attempt cap is checked before every call.

D2 resolved all six decision items above on 2026-07-16. The zero-cost account
state is attested; live command construction, deterministic six-case anchor
selection, reservation/actual-usage accounting, bounded retries, and failed-
attempt transport replay are implemented. The complete provider-free suite is
`121 passed`; compile, Black, isort, and `git diff --check` also pass.

No provider call is authorized until the implementation is committed and the
one-shot B3 preflight generates exact command-spec, anchor-manifest, executable,
account, feature, timeout, and token-cap hashes for external review. A changed
account state, executable, sandbox, feature catalog, command spec, or preflight
hash stops the phase.
