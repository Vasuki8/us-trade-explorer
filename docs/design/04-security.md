# Threat model and security acceptance criteria

This is a design-time model of the proposed system, not a vulnerability scan or a claim about deployed controls. Assets are data integrity, source credentials, deployment authority, the domain, source provenance, visitor privacy, future private research and subscription entitlements. Main adversaries are malicious contributors, compromised data/dependencies, credential thieves, abusive visitors and future users attempting to access another user's resources.

The trust boundaries and stores are shown in the architecture diagram. Official data is authoritative statistical input but is still untrusted bytes. GitHub permission to propose a change is not permission to access secrets or publish it. Public pages and private paid work must remain different security domains.

## Prioritized threats and tests

P0 means required before the relevant feature is exposed; P1 means required before routine commercial operation. Each control has an observable failure test.

| Priority / threat | Boundary and impact | Control | Acceptance test |
|---|---|---|---|
| P0 source poisoning, schema drift or partial responses | Source → ingestion → public numbers | Strict schema/type/size/relationship contracts, completeness inventory, independent reconciliation, quarantine | Truncated JSON, 200-with-empty-body, missing country partition, duplicate key and changed variable each prevent promotion |
| P0 malicious description or URL | Source/query → rendered HTML | Framework escaping, textContent, no raw HTML; URL scheme/host allowlists; safe JSON serialization including script-closing text | XSS payloads in title, table, chart tooltip and search display remain inert with no network side effect |
| P0 CSV formula injection | Source → download → spreadsheet | Numeric typing; text neutralization after leading whitespace/control inspection; CSV quoting | Formula, tab/CR prefix, multiline quote and malicious country-name fixtures stay text in spreadsheet imports |
| P0 SSRF and credential leakage | Fetcher → network/logs | Fixed HTTPS source hosts/ports/paths, validate redirects or disable them; no arbitrary URL input; bounded downloads; redact query keys | Reject localhost, metadata IPs, alternate schemes, cross-host redirect and compression bomb; fake credential canary absent from errors/artifacts |
| P0 untrusted PR steals secrets | Contributor → CI privileged context | PRs only run unprivileged checks; no production secrets, OIDC role or trusted cache; never checkout PR code in pull_request_target | Fork and same-repository PR cannot obtain source key, deployment role or writable shared cache |
| P0 compromised dependency/Action | Package/Action → CI | Exact lockfiles; pin Actions to full commit SHA, images to digests; review lifecycle scripts; security updates through PRs | Policy rejects floating Actions and changed unreviewed locks; secrets never exist in dependency-install/build jobs |
| P0 unauthorized publication or manifest rewrite | CI → production | Protected main; CODEOWNERS for workflows/source registry; scoped environment and branch-bound OIDC; verify candidate provenance independently | PR-origin/foreign-repo OIDC subject denied; wrong build digest denied; ingestion role cannot activate/delete production |
| P0 mixed release or concurrent promotion | Storage → visitor | Immutable objects, complete inventory, serialized promotion and release-pinned fetches | Kill upload/build and race two promotions; old site remains usable and no comparison combines releases |
| P0 raw/private bucket exposure | Object stores → internet | Separate buckets, public-access block, least-privilege OAC/IAM, no directory listing routes | Anonymous, CDN and preview requests to raw/log/private-report objects fail; public exports contain only allowlisted fields |
| P1 account/domain takeover | Administrator → control plane | Passkeys/MFA, individual accounts, registrar lock, recovery contacts, minimal admin role | Restore using documented recovery; removed admin loses active access; no shared root credentials |
| P1 stale data falsely presented as current | Scheduler/source → visitor trust | Official-calendar checks, independent monitor and visible dates/staleness states | Stop schedules and simulate source delay; monitor alerts and UI distinguishes the two conditions |
| P1 abuse and cost escalation | Visitor → CDN/storage | Static cache, bounded files, budgets/alarms, sensible rate controls, bot monitoring | Load a staged abuse pattern; downloads stay bounded and alarm fires without blocking normal crawlers |
| P0 unsafe ad integration | Sponsor/vendor → visitor | Locally hosted reviewed creatives initially; no arbitrary sponsor scripts; consent gate before any later SDK | Launch network audit contains only declared requests; reject sponsor HTML/script/pixel |
| Future P0 cross-user access | User → API/database/reports | Membership and role authorization on every resource and operation; tenant-scoped SQL; RLS as defense in depth | User B cannot read/update/delete/export user A's resources using valid IDs or signed-link endpoints |
| Future P0 session/CSRF abuse | Browser → account API | Secure HttpOnly host-only cookies, rotation, CSRF tokens and Origin checks for unsafe requests | Cross-site POST denied; session fixation fails; logout/deletion revokes sessions; GET never mutates |
| Future P0 fake/duplicate/out-of-order billing | Processor → API → entitlement | Signature verification on raw body, replay bounds, unique provider event ID, transactional processing and reconciliation | Tampered webhook denied; 20 duplicates have one effect; old events cannot restore expired rights |
| Future P0 paid-output exposure | API/build/CDN/queue → report | Separate private store; no public build access; authorization for both report creation and download; short-lived signed URLs | Logged-out/expired/wrong-tenant request fails; source maps, search index and build tarballs contain no private content |

## CI and administrative design

Set workflow permissions to read-only or none by default. Grant `contents: read` only when needed; grant `id-token: write` only to a trusted deployment/archive job whose AWS trust policy binds the exact repository and environment. OIDC supplies short-lived credentials, not a reason to trust arbitrary workflow code. Checkout disables credential persistence. No broad personal access token in builds.

The ingestion job receives only the Census key and tightly scoped staging-write authority if required. A separate publisher receives only publication permissions. The historical archive writer cannot delete accepted data. Production activation is limited to protected main or an approved immutable release, and cannot consume arbitrary workflow_run artifacts from an untrusted PR. A private repository reduces public exposure; it does not make collaborator code inherently safe.

Never log complete request URLs containing the Census key. Disable HTTP debug dumps, sanitize exception objects and scan files before uploading evidence. Masking is a fallback; already emitted secrets must be rotated even if a log is later removed. Avoid real credentials in tests; use marked canaries. No browser `PUBLIC_*`/`VITE_*` variable contains secrets. Do not store API keys in GitHub release descriptions or source links.

Use an individual owner account and a documented recovery contact. If there is initially only one administrator, record that separation-of-duties cannot yet be achieved; enforce automated gates and add a second reviewer when available. Root/cloud-owner credentials are break-glass only. Rotate Census and remaining long-lived tokens after suspected exposure, staff departure or scope changes, and on a proposed 90-day operational review cycle. Validate new credentials before revoking old ones; never extend overlap indefinitely.

Lock Python and JavaScript dependencies and record an SBOM/licence inventory per build. Keep third-party code out of the data parsing path where unnecessary. Dependency updates receive ordinary review and relevant regression tests, not automatic production promotion solely because a scanner is green.

## Browser and host security

HTTPS-only with HTTP redirect; modern TLS. Start HSTS with a short validated period, then increase after checking every relevant subdomain; do not preload or apply includeSubDomains blindly. Use `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, a restrictive Permissions-Policy, and CSP with `default-src 'self'`, `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`, narrow form/connect/image destinations and hashed scripts where necessary. No blanket unsafe-eval/unsafe-inline relaxation for advertisements.

Validate CSP against Astro-generated output before enforcing it. Security headers must cover HTML, errors and downloads as appropriate, verified by actual HTTP responses. Use correct MIME types and Content-Disposition for downloads. Restrict preview access and prevent indexing; do not store production secrets in a preview environment. CloudFront header policy availability is a reason for choosing pay-as-you-go configuration over an incompatible low-cost flat-rate tier.

No accounts means no app session cookies in the MVP. Hosting/CDN security features can nevertheless set cookies or make extra requests; inspect the selected configuration and list any such behavior in the inventory. Disabling visitor analytics does not mean no personal data is processed.

## Future authorization and billing

Prefer an established OIDC identity service using authorization-code flow with PKCE, state and nonce. Keep tokens server-side; use an opaque session ID in a Secure, HttpOnly, host-only cookie, SameSite=Lax where suitable. Set idle/absolute expiration, session rotation, verified recovery and rate limits. Admin accounts require phishing-resistant MFA. Rate-limit signup, login, resets, report generation and exports; avoid account enumeration.

All APIs authorize subject, workspace membership, role and current entitlement. Never accept a browser-provided owner/price/plan as authoritative. Private responses are `Cache-Control: private, no-store`; CDN caching is bypassed. Public and private service roles, build pipelines and buckets remain separate. A hidden button, guessed URL, static JSON asset or noindex tag is not access control.

Hosted checkout and billing portal reduce card-data handling. The operator retains payment/customer IDs and necessary invoice records, never card numbers or CVV. The processor's availability in India, international recurring payments, RBI mandates, supported currencies, tax responsibilities and customer countries must be verified before selection. A hosted flow still has PCI responsibilities to establish with the provider.

Billing state is persisted independently of client UI. Store processor event ID, payload hash, accepted timestamp and processing state in a unique transaction. Verify signature and timestamp using raw bytes; enqueue only after durable receipt. A worker obtains authoritative subscription state and reconciles out-of-order notifications. Scheduled reconciliation catches missed events. Checkout creation is idempotent, and entitlement updates and audit records commit together. [Stripe webhook guidance](https://docs.stripe.com/webhooks) is a reference pattern, not a selected-provider commitment.

| Internal state | Proposed entitlement |
|---|---|
| Pending/incomplete | No paid access; checkout-return page can poll authenticated confirmation |
| Active and paid | Feature set in server-owned plan mapping until paid-through date |
| Past due | Proposed three-day grace for existing workspaces, visible payment warning; no expensive new report jobs; local/legal policy reviewed before launch |
| Cancel scheduled | Paid access to effective end unless immediate refund/withdrawal requires earlier termination; no further renewal |
| Unpaid/expired/cancelled | No paid jobs; read-only export window according to published retention policy |
| Refunded/disputed | Apply reviewed refund/dispute policy; manual review when needed; never silently recreate active entitlement |

Alert workers deduplicate `(rule_id, release_id, trigger_version)`, check entitlement at scheduling and execution, and recheck subscription/email status before sending. Report downloads authorize current access; signed links expire quickly and are scoped to one object. Revisions generate distinct correction events rather than repeating a claimed new-period alert. A cancelled user must not continue receiving paid scheduled work because a queue was already populated.

## Incident and recovery procedure

1. Operator triages the signal, preserves sanitized evidence and records detection time. Freeze promotion if integrity or secrets may be affected; keep the known-good public release available where safe.
2. Revoke affected credentials/sessions, stop unsafe integrations, isolate candidates and assess which assets/users were touched. Do not delete audit evidence during containment.
3. Restore verified artifacts and configuration from independent backups. Re-run hashes, statistical checks, secret scans and access tests. Publish a correction record for changed public facts.
4. Legal lead evaluates notifications by jurisdiction. India's CERT-In directions include short reporting timelines for specified incidents; EU and other regimes have their own triggers. The incident playbook records clocks and responsible contacts in advance, not after a breach.
5. Verify recovery and monitor recurrence; document root cause, actual impact, affected releases and preventative changes. Practice one failed-release and one credential-exposure tabletop before launch and quarterly restore tests thereafter.

India logging/reporting scope and exact log types must be reviewed against the [CERT-In directions and FAQs](https://www.cert-in.org.in/Directions70B.jsp). The design initially provisions 180-day restricted logs in India and a reachable incident contact; this is not a claim that storage alone satisfies the directions.
