# rosetta — Technical build brief

> Bespoke membership-management platform for The Tutors' Association (TTA), replacing **Wild Apricot**.
> Non-technical feature overview for staff/board: [`OVERVIEW.md`](./OVERVIEW.md). This document is the
> developer-facing brief: architecture, data model, scope with requirement traceability, and the build
> plan.

## 1. Context

TTA is a self-regulatory membership body for UK tutors and tuition businesses (~2,000 paying members + a
few hundred non-paying bundle members; ~200 events/year, mostly online; 4 full-time staff). It runs all
membership, events, billing and comms on **Wild Apricot**, which is dated, near-impossible to style (CSS
via FTP, 5-day support round-trips), blocks automation, and has a growth ceiling. TTA is evaluating
**Nucleus** (a configurable SaaS) in parallel; **rosetta is the in-house, bespoke alternative** — cheaper
to run, exactly fits the domain, owned by TC.

Sources: the planning-call transcript + recording (62 frames correlated), and the supplied "Membership
Platform — Requirements Document". **Note:** pages 1–8 of that PDF are TTA's RFP written *for Nucleus*, so
its delivery assumptions (Statamic CMS, "configured-not-customised" multi-tenant SaaS, no custom CSS —
TEC-03 / WEB-01 / PRT-10) describe *Nucleus's* model, **not ours**. We mine the **functional** requirements
(the `MEM/COM/EVT/PRT/WEB/COMM/ADM/TEC` IDs used below) and re-express them in our architecture.

## 2. Decisions locked in
- **Repo:** `tutorcruncher/rosetta` (private). **Name:** rosetta.
- **Tenancy:** true **single-tenant** (one company, TTA). No tenant `Organization`, **no**
  `request_query` / `query_for_pub_api` scoping, no per-org public-API-key machinery. Staff see everything.
- **Template:** `tc-fullstack-starter` is a **conventions/best-practice reference**, not a structure to
  copy — all models redone.
- **Build order:** **Members & onboarding first** (Section A). Everything else tracked as an issue, built
  after. September target ("base version") = Members → Payments → Events → Reports (+ Mailchimp sync).
- **Email:** **Mailchimp now** — sync members + segments via API and send all email there; in-platform
  email (ADM-01/02) is a later phase.
- **Public Find-a-Tutor directory / member hub:** **deferred** (admin backend only for now), even though
  the RFP marks the directory Must / "key value driver" (WEB-03/04). Board sign-off requested.
- **Compliance:** **tracking + dashboard now** (COM-01/03/04); tutor-check.co.uk API + auto-email /
  auto-suspend (COM-02) deferred to a fast-follow.
- **Configurability:** **code-first** — fields/levels/permissions in code; segments live in Mailchimp;
  event custom fields (e.g. dietary) supported as real per-event data. No runtime field/segment/permission
  builder.

## 3. How we build (template as conventions reference)

Backend **FastAPI · SQLModel · Celery · Postgres · Redis** (Python 3.12, `uv`, `ruff`, `ty`, `pytest`,
100% patch coverage). Frontend **React Router v7 (SSR) · React 19 · Tailwind v4 · Vite** (TypeScript,
`npm`, ESLint, Prettier, Jest 80/75/70/75, Playwright).

**Keep (best practice):** backend slice layout from `app/example_domain/` — `_Base`/`Table`/`Basic`/
`List`/`Detail` SQLModel split, `api/` router (CRUD + `ListFilter`/`ListOrder` + `OPTIONS` +
**paginate-then-fetch** to avoid N+1), `tasks.py` for Celery; register every model in `app/__init__.py`.
Auth `app/auth/` (`POST /auth/login` → JWT, `auth_user`, `Permission.is_admin/...`). Frontend feature
layout from `app/routes/items/` (loader/action, typed `app/data/api.ts`, `app/types/` snake_case mirrors,
`app/components/ui/`, `@theme` tokens, `APP_NAME`). Testing discipline (factories, role clients,
full-structure asserts, `count_queries`, `url_path_for()`, response var `r`).

**Drop (single-tenant):** `request_query`/`query_for_pub_api` scoping, the `Organization` tenant model,
per-org API keys / public `/api/v1`, and all starter example models. **Not** following the Nucleus RFP's
delivery model (Statamic, multi-tenant config SaaS, no-CSS member templates).

**First customisation:** `APP_NAME='rosetta'`; TTA brand (deep-red serif wordmark) in `@theme`; FastAPI
title / logfire service → `rosetta`; wire `AuthProvider` + `/auth/login` + `/users/me`; seed staff users.

## 4. Domain model (all fresh models)

**Build-now (Section A):**
1. **`User`** (admin/superadmin) — TTA staff. Member-login users come with the deferred member hub.
2. **`Member`** — named person holding/covered by a membership. Personal (name, email unique, phone,
   WhatsApp, address incl. **business address**, about, **tuition type**, **subject specialisms**,
   **tuition/qualification levels**, qualifications, **delivery mode** online/in-person/both, photo,
   `show_profile_publicly`); consents (Code of Practice, Contractual Rules, DBS Policy, Privacy Policy,
   level eligibility — bool + timestamp + version); additional (CPD Platform Username, referral source,
   admin bespoke-arrangement / notes); status & compliance (`verification_status` Processing/Verified,
   computed `compliance_rag`, safeguarding completion date); email prefs (Workflow / Event announcements /
   Email blasts → Mailchimp groups); `tags` m2m; links (`company_id?`, `Membership`, `DBS` 1:1).
3. **`DBS`** — **own object, 1:1 with `Member`, nullable** (field-heavy): certificate file(s), number,
   surname, DOB, Update-Service status, DBS date; "valid within 1 year" / on-update-service validity +
   grace window computed here (automation later). [COM-01]
4. **`Company`** — corporate member / affiliate partner / education agent / charity / franchise. Name (+
   trading name), category, billing, **`primary_member_id`** (FK to **one of its bundle members** = account
   holder; nullable but normally set), bundle seat allowance, notes. **Must have ≥1 bundle `Member`.** Holds
   corporate `Membership`; has many `Member`s. [MEM-03]
5. **`Product`** — purchasable thing. **Membership levels are Products**; store items (DBS admin, Compliance
   Pack, VAT Pack, conference recordings) are Products. name, `kind` (membership/store-item), description,
   **regular price + member price**, Stripe price ids (monthly + annual where relevant), eligibility,
   `public_can_apply`, allowed level-changes, bundle seat count, stock, tags, image, co-brand. Fixes WA's
   ~40-level mess: billing period & status are attributes of `Membership`, not separate levels; custom
   corporate bundles become Companies w/ a corporate membership; "Working with Corporate" = Member linked to
   a Company. Observed prices: Professional Tutor £9.50/mo or £95/yr; Working-with-Corporate £6.50/£65;
   Undergraduate £35/yr; Affiliate Partner £550/£360/£240/£120 yr; Corporate (Small) £24/mo or £240/yr;
   Launchpad £180/yr; DBS admin £30 (free for members). [MEM-02, COMM-01/02]
6. **`Membership`** — billable subscription on a `Member` (individual) or `Company` (corporate). `product`,
   `status` (active/processing/pending/lapsed/grace/suspended/archived), start date, renewal due date,
   `billing_period`, payment method (Stripe / bank transfer / GoCardless legacy / manual), Stripe customer +
   subscription id, `auto_renew`, renewal-date-last-changed, level-last-changed. **Two metrics:** paying
   members = count of Memberships (corporate = 1); named members = count of Members. [MEM-04]
7. **`Tag`** — staff-editable label, m2m with `Member`; replaces WA "Groups"; doubles as Mailchimp segments.
8. **`Reference`** — belongs to Member. Referee name + email, content, submitted date, confirmed date
   (email-verify), **`share_publicly`**. Replaces the Google Form.
9. **`AuditEntry`** — append-only log of membership/compliance status & level changes (who/what/when),
   surfaced as the member notes timeline. [COM-05]

**Later-section entities:** `Invoice` (+ line items; origins: member application/renewal/level-change/store
order/event ticket; VAT + `account` TTA/TFA flags; Stripe ids; export-only, no QuickBooks) · `DiscountCode`
(membership purchases, first-year-only, auto-renewal logic) · `Event`/`TicketType`/`EventRegistration`
(level-gated tickets, member/non-member pricing, VAT/account, **duplicate**, tags, waitlist, per-event
custom fields, back-end-only access link revealed post-registration, attendance) · `Contact` (non-members;
**open:** one `Person` table w/ discriminator vs separate) · `Poll`/election (members-only; with hub).

## 5. Scope & requirement traceability

| Area | Requirement IDs | Where |
|---|---|---|
| Members, profiles, levels, bundles, onboarding/approval, renewals, bulk ops | MEM-01..07, 2.4/2.5/2.6 | **A — now** |
| Compliance tracking + dashboard ("valid within 1yr", RAG, compliant/grace/out, audit log) | COM-01, COM-03 (model), COM-04, COM-05 | **A — now** |
| Payments, Stripe, store/products, member-vs-non-member pricing, invoices, VAT/TFA, discounts | COMM-01..04, 2.10/2.11 | **B — issue** |
| Events admin: tier-gated tickets, pricing, access links, reminders, attendance, waitlist | EVT-01..09, 2.1 | **C — issue** |
| Reporting: new members by tier, financials, churn/retention, MRR | 2.8, TEC-07 | **D — issue** |
| Email via Mailchimp (sync + segments); in-platform editor later | ADM-01/02, 2.9 | **E — issue** |
| Compliance automation (tutor-check.co.uk, auto-email, grace→auto-suspend, 14-day archive) | COM-02, COM-03 (automation) | **Deferred** |
| Member portal/hub (Home/DBS/CPD/Events/Discounts, resources, logos, helpline, self-service) | PRT-01..10, MEM-08/09 | **Deferred (CMS-ish)** |
| Public website + tutor/agency/partner directories, map, public discount list | WEB-01..09, 3.2 | **Deferred** |
| Voting / elections | 2.12, PRT-02 | **Deferred (with hub)** |
| Jobs board + multi-currency | 3.9 | **Deferred** |
| Store extras: IPP, VAT/Compliance pack fulfilment, conference paywall | COMM-02 | **Deferred** |
| Data migration from Wild Apricot (members, history, events, docs) | TEC-06 | **Migration epic** |

## 6. Module A — Members & onboarding (BUILD NOW)
- **Backend:** `app/members/` (Member, DBS 1:1, Reference, consents, Tag m2m, AuditEntry), `app/companies/`
  (Company + bundle + primary-member FK + ≥1-bundle rule), `app/products/` (membership Products),
  `app/memberships/` (Membership + lifecycle). CRUD + list filters (status, product, RAG, company, tag,
  search, new-in-7/30-days) + paginate-then-fetch w/ counts. Member-number generation. Staff-editable Tag
  CRUD + tag/untag (single + bulk). Bulk admin (delete/edit/email/status — MEM-07).
- **Compliance (tracking + dashboard):** "valid within 1 year" logic on DBS/references/safeguarding;
  computed `compliance_rag`; compliant / in-grace / out-of-compliance dashboard + saved view (COM-04);
  `AuditEntry` log (COM-05). Automation (tutor-check sync, auto-email, auto-suspend) deferred.
- **Public signup flow** (parameterised, not a CMS): choose membership Product → details → consents →
  Stripe payment → **Pending** → admin **Approve/Reject** queue (MEM-05). One flow replaces WA's ~12
  per-level pages. Post-approval: tier-specific confirmation + credentials via Mailchimp.
- **References:** hosted form per request; on submit + email-verify, auto-populate reference + date;
  `share_publicly`.
- **Frontend (admin):** Members list (RAG/status/level/tag filters, bulk actions); Member detail (tabs:
  Profile, Membership, DBS, References, Compliance, Notes/Audit); edit; approve/verify; tag management.
  Companies list/detail (bundle management). Products & Memberships admin.

## 7. Modules B–E + Migration (issues; build after A)
- **B · Payments/Stripe:** memberships (monthly/annual per-Product), store/one-off w/ member-vs-non-member
  pricing + fulfilment hooks, **discount codes** (first-year-only, auto-renewal), VAT + TTA/TFA tagging &
  routing + £90k member-ticket threshold tally, `Invoice` + member-downloadable + CSV export (no
  QuickBooks), renewal/lapse/grace lifecycle, DD/pay-by-bank + manual legacy. [COMM-01..04]
- **C · Events (admin):** tier-gated tickets enforced by platform not codes (EVT-01), tier pricing (EVT-02),
  free+paid (EVT-03), back-end-only access link post-registration (EVT-04), **duplicate**, tags + filters
  (EVT-05), online+in-person (EVT-06), confirmation+reminder emails via Mailchimp (EVT-07), waitlist
  (EVT-08), attendance (EVT-09). Follow-up session with Sam.
- **D · Reports:** new members by tier, financials, **churn & retention incl. lapsed-then-renewed**, MRR,
  paying-vs-named; charts + tables + date ranges. [2.8, TEC-07]
- **E · Mailchimp:** sync Members + segments/tags via API; trigger system + marketing email in Mailchimp;
  map the WA email set (application initiation, member activation, renewal reminders 1/2, renewal day,
  grace, lapsed, renewal pending/confirmed, recurring-renewal-failed, card-expiry) to Mailchimp journeys.
- **Migration:** members, membership history, event history (where feasible), documents + cleansing. WA
  renews **March** — migrate ahead. [TEC-06]

## 8. Where this diverges from the Nucleus RFP (deliberate)
- **Single-tenant bespoke**, not Nucleus's multi-tenant "configured-not-customised" shared codebase
  (TEC-03). **Code-first**, not no-code config (ADM-04, MEM-09, TEC-04/05). **Our stack** (FastAPI + RR7),
  not Statamic CMS for the public site (WEB-01). **Phased admin-first**, not "all Must at launch" — we
  deliberately defer the member hub, public directories, voting, jobs board and DBS automation that the RFP
  lists as Must. **Mailchimp retained** near-term, vs the RFP's intent to retire it (ADM-02). If the board
  wants the full member-hub + directory on day one, that materially changes scope (flag now).

## 9. GitHub issues
Labels: `epic`, `backend`, `frontend`, `infra`, `deferred`, `question`. Milestones: `M0 Scaffold`,
`M1 Members`, `Payments`, `Events`, `Reports`, `Phase 2`.

- **`[EPIC] M0 — Scaffold & conventions`:** repo from template; strip multi-tenancy + example models; config
  (title, logfire `rosetta`); `APP_NAME` + TTA `@theme`; wire auth + staff seed; deploy skeleton; CI green.
- **`[EPIC] M1 — Members & onboarding`** (master) + sub-issues: (1) Member model + admin CRUD; (2) DBS model
  1:1 + upload + validity; (3) Company + bundle + primary-member FK + ≥1-bundle; (4) Product + clean
  taxonomy + legacy-WA-level mapping + member/regular pricing; (5) Membership + lifecycle + paying-vs-named;
  (6) Tag + tag/untag (single+bulk) + migrate WA Groups; (7) Reference + hosted form + email-verify +
  share_publicly; (8) AuditEntry + member notes timeline; (9) Compliance tracking + RAG + dashboard/saved
  view; (10) Public signup flow + Approve/Reject queue; (11) Bulk admin ops; (12) Members admin UI + detail
  tabs + Companies/Products/Memberships admin.
- **Epic issues (after A):** Payments/Stripe · Events (admin) · Reports · Mailchimp integration · Wild
  Apricot data migration.
- **Deferred epics (`deferred`):** Member hub/portal · Public website + tutor/agency/partner directories +
  map · Voting/elections · Jobs board (multi-currency) · DBS automation (tutor-check.co.uk + auto-email +
  grace→auto-suspend + 14-day archive) · In-platform email (retire Mailchimp) · Discount-code engine +
  partner discounts · Store extras (IPP / VAT & Compliance packs / conference paywall) · Member self-service
  profile editing · Tier-split member experiences.
- **Open-question issues (`question`):** Contacts modelling (Person discriminator vs separate); events depth
  with Sam; finance/VAT with Stephen (TTA/TFA split, £90k threshold, abroad sponsorship); DBS automation with
  John (tutor-check.co.uk + his repo); board sign-off on deferring member-hub/directory.

## 10. Verification
- **Backend:** `make lint && make test-cov` (ruff + ty + pytest, 100% patch coverage; `count_queries` on
  list/report endpoints). CI runs `alembic upgrade head` on a fresh DB.
- **Frontend:** `npm run lint && npm test` (Jest 80/75/70/75) + `npm run test:e2e` (Playwright: signup →
  approve → member detail; compliance view).
- **Manual e2e:** run both servers; Tom self-signs-up as a test member (spare email; Julius approves). Stripe
  test mode for payments. Demo each module against the equivalent Wild Apricot screen.
