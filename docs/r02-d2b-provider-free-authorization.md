# R02 D2b provider-free authorization

Date: 2026-07-17

Status: `AUTHORIZED_PROVIDER_FREE_IMPLEMENTATION_ONLY`

Base commit: `7f9a998a32bf6835fd5ef6b14ebc79d674727128`

R02 D1 freeze SHA-256:
`2d5961806b5051ff56c874b8b05933df014136bacb98717c4846f2b48f645778`

R02 D1 manifest SHA-256:
`81026cdd1ab83fe7f0cea30951cf8cb1351dca6150d9aaecbfa696d932bbdeaf`

## Authorized implementation

1. Assemble a selector prompt from the frozen selector-safe payload only. Strictly
   parse `selected_candidate_id`, integer `confidence`, and enumerated
   `reason_codes`. Invalid responses must take a typed baseline-fallback path.
   Prompt wording may be implemented but remains a draft pending separate review.
2. Deterministically revalidate the selected candidate at the acceptance gate.
   A failed revalidation must take the baseline-fallback path.
3. Execute and score triggered scripted episodes, record paired utility delta
   against the deterministic baseline, and bind attempt and token accounting to
   the R02 identity.
4. Extend the append-only graph and replay verification with selector request,
   response, transport, fallback, execution, and score evidence.
5. Use scripted clients only and preserve all sealed R01 artifacts.

## Explicitly not authorized

- Provider calls or a provider-backed client.
- Live execution.
- A new fixture frame.
- Freezing `delta_min`, bootstrap rules, sample size, trigger minimum, or budget.
- Finalizing zero-call preflight.
- Freezing the selector prompt wording.
- Editing or relabeling any sealed R01 artifact.
