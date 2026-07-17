# R02 D2c provider-free frame and statistical-freeze authorization

Date: 2026-07-17

Status: `AUTHORIZED_PROVIDER_FREE_FREEZE_CANDIDATE_ONLY`

The user authorized the next provider-free unit after D2b review:

1. Generate and seal a new seed-derived frame with approximately 120
   representative and 40 headroom-positive challenge fixtures.
2. Verify the frozen 50-bps trigger on the new frame without readjusting it.
3. Propose `delta_min` with a practical utility-unit rationale.
4. Freeze the stratified estimand, bootstrap procedure, `N`, and `M_min` using
   provider-free simulation matching the registered estimator.
5. Calculate a provider token budget and attempt cap.
6. Produce an independent-review handoff.

## Explicit exclusions

- Provider calls and provider-backed clients.
- Live execution.
- Finalizing or running zero-call preflight.
- D3 or a micro-pilot.
- Changing the D1 trigger or candidate generator after observing the frame.
- Exposing oracle, headroom, hidden outcomes, stratum labels, canonical IDs, or
  permutation evidence to the selector.
- Editing or relabeling sealed R01 artifacts.

The frame seed is derived from immutable D1 identities and D2b commit `0f670bb`;
it is not selected by searching seed outcomes. The later type-only D2b review
follow-up `5dae53a` does not alter trigger, candidate, prompt, or scoring behavior
and therefore does not authorize regenerating the sealed frame.
