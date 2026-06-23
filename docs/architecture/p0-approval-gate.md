# P0 Human Approval Gate

## Purpose

The P0 approval gate requires an explicit human approval artifact before the runner can issue a signed simulator job envelope.

## Boundary

The UI may request and display an approval, but it is not trusted. `RunnerSimulator` independently validates the approval artifact after policy allows the request and before creating a job envelope.

## Approval States

- `requested`: approval artifact exists but cannot authorize a job.
- `approved`: approval is eligible for runner validation until expiration.
- `denied`: request was rejected by a human reviewer.
- `expired`: approval timed out before runner validation.

## Binding Requirements

Approvals are bound to:

- tenant ID;
- client ID;
- engagement ID;
- adapter ID;
- normalized target;
- expiration time.

Any mismatch fails closed with a stable denial reason.

## P0 Limitation

The current desktop path uses a local modal dialog as the human decision point. Multi-approver policy, durable reviewer identity, delegated approval, and production audit review are future work.
