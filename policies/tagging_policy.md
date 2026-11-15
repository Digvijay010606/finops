# Cloud Tagging Governance Policy v1.0
**Purpose:** Make every dollar of cloud spend attributable to an owner, environment and team so it can be allocated, optimised and alerted on.

## 1. Mandatory tags (enforced at creation)
| Tag key | Allowed values | Example | Why |
|---|---|---|---|
| `env` | prod, staging, dev, sandbox | prod | Separates production from waste-prone environments |
| `team` | platform, data, web, ml (extend via change request) | data | Chargeback / showback |
| `owner` | valid company email | asha@example.com | Who to contact about spend or cleanup |
| `cost-center` | finance code | CC-1042 | Ties to budget lines |

## 2. Optional tags
`project`, `app`, `ttl` (expiry date for temporary resources), `data-classification`.

## 3. Rules
1. Tag keys are lowercase, hyphenated; values come from the allowed list. No free-text `env`.
2. Resources missing a mandatory tag get a 7-day grace period, then are flagged to the platform team; after 14 days non-prod untagged resources are stopped (never deleted automatically).
3. A resource with **no `team` and no `owner`** is *orphaned*; it is reviewed weekly and removed or assigned within 10 working days.
4. Enforce with AWS Tag Policies + SCP (deny create without tags) + IaC modules that require tag inputs.
5. Target KPI: >= 95% of spend carries all mandatory tags. Reported weekly from `audit_untagged.py`.

## 4. Roles
FinOps owns the policy; platform enforces; team leads fix findings; finance consumes the reports.
