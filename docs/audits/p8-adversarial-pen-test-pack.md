# P8 Adversarial Pen-Test Pack

**Date:** 2026-06-23  
**Scope:** P0 policy deny-by-default regression scenarios  
**Status:** Automated in CI via `tests/test_adversarial_policy.py`

## Scenarios

| ID | Attack vector | Expected outcome | Test |
| --- | --- | --- | --- |
| AP-01 | Unknown adapter injection | `DENY_UNKNOWN_ADAPTER` | `test_adversarial_unknown_adapter_injection` |
| AP-02 | Scope hopping to unauthorized target | `DENY_TARGET_OUT_OF_SCOPE` | `test_adversarial_scope_hopping` |
| AP-03 | Credential smuggling in URL target | `TargetParseError` | `test_adversarial_credential_smuggling_in_url` |
| AP-04 | Extra manifest arguments (e.g. shell flags) | `DENY_UNKNOWN_ARGUMENT` | `test_adversarial_extra_arguments_blocked` |
| AP-05 | Network transport without ROE consent | `DENY_NETWORK_TRANSPORT` | `test_adversarial_network_transport_denied_without_roe` |
| AP-06 | Expired engagement replay | `DENY_EXPIRED_ENGAGEMENT` | `test_adversarial_expired_engagement_replay` |
| AP-07 | Tampered job envelope signature | `DENY_BAD_SIGNATURE` | `test_adversarial_tampered_job_signature` |
| AP-08 | Valid simulator path (control) | `ALLOW` | `test_adversarial_valid_path_still_allows_simulator_only` |

## Manual follow-ups (P9)

- Fuzz `parse_target` with malformed Unicode and IDN homoglyphs.
- Attempt plugin manifest schema downgrade attacks.
- Verify MCP stdio server rejects execution-shaped tool names.

## Evidence

Run: `python -m pytest tests/test_adversarial_policy.py -v`