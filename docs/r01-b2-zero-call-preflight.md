# R01 Phase B2 zero-call preflight

Status: `BLOCKED_PENDING_D2`

Observation date: `2026-07-14` (Asia/Seoul)

Provider calls made: `0`

D2 cross-review package: `docs/r01-d2-decision-package.md`.

Evaluation fixtures generated: `0`

## Trust anchors

- Code commit: `fe521fefcaf25475a7bd92c8626f6eccd6ca3033`
- Research contract SHA-256: `3a2f2dab0acd4c6a274f660f3dd69b3dea0f60d1de263e1034e653a7e03028bc`
- B3 readiness implementation parent commit: `1b0ef0e`
- Provider-free freeze SHA-256: `86096c395922d179d4d047b2c7934a221a376c948e5d7d9b5c7e41c332b630f2`
- Provider-free regime-gap summary SHA-256: `0e6e8945f93779a77ffc7687d63062c010efd3aee3d6c8062551e54108fbf886`
- Exact-tag Codex source feature proof SHA-256: `1de5d131356deb6dec8186eb07795e47717d4960937b9142689a5e9cc3554f91`
- Source tag/commit: `rust-v0.144.1` / `44918ea10c0f99151c6710411b4322c2f5c96bea`
- D2 decision package SHA-256: `b240fde00ae335f7ced09113332c60cefacafe6a4223114bf680a8d427dcab82`
- Freeze root-seed label: `r01-phase-b-development-fixtures-v1`
- Freeze fixture count: `40`
- Root-seed and fixture-count match: `true`
- Final prompt SHA-256: `TBD_D2`

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
- Exact selected model: `TBD_D2`
- User-visible reasoning effort: `TBD_D2`
- User-visible service tier: `TBD_D2`
- Provider-managed model availability and routing: not frozen and not queried by this zero-call preflight.
- Transport model-echo availability: `UNESTABLISHED_ZERO_CALL`; absence is an explicit D2 limitation, while any observed mismatch is a `STOP_PHASE` condition.
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
  `SOURCE_ESTABLISHED_REMOVED_NOOP_PENDING_D2_ACCEPTANCE`. Exact tagged source
  explicitly ignores all four config keys and has no behavior consumer outside
  the feature registry, removed-key guards, and tests. The stage label alone was
  not used as evidence.
- Command-spec SHA-256: absent until D2 approves or rejects the exact four-entry
  non-tool allowlist.
- Gate result: `BLOCKED_PENDING_D2`; prompt wording cannot override it.

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
- `enable_request_compression`, `remote_compaction_v2`, and `fast_mode`: baseline `true`, post-disable `false`.
- Secrets in argv, prompt, config, artifacts, or logs: none observed; secret-bearing config keys and recognizable secret-bearing values are rejected by the command-spec validator.

## Budget and D2 blockers

- Development attempt cap: `200`.
- Development attempts spent: `0`.
- Development attempts remaining: `200`.
- Development token cap: `TBD_D2`.
- Per-attempt token reserve: `TBD_D2`.
- USD cap: `TBD_D2`; ChatGPT subscription use does not authorize overage or API billing.
- High-transaction-cost stratum: `6/7` zero oracle-hold gaps; treatment remains `TBD_D2_ACCEPT_UNCHANGED_OR_RESTART_PROVIDER_FREE`.
- Transport disposition policy: `FROZEN_PRE_D2`. Parser-originated `STOP_PHASE` always dominates timeout/nonzero wrapping; retry wrappers retain the original code and disposition; a complete transport with timeout or nonzero process status is `STOP_PHASE`, never hold.

D2 must resolve all items below before any B3 acquisition:

1. Accept the exact-tag source proof and approve exactly the four residual
   removed/no-op entries, or reject it and stop Option A.
2. Freeze the exact model string, reasoning effort, service tier, and provider-managed setting declarations.
3. Accept model-echo absence as a possible transport identity limitation, subject to mismatch stopping the phase.
4. Freeze the development token cap, per-attempt reserve, USD cap, and no-overage rule.
5. Accept the unchanged high-cost stratum and its prospective power cost, or restart from a newly amended provider-free contract and freeze.
