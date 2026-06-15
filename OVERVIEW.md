# rosetta — The Tutors' Association Membership Platform
## Plain-English feature brief (for approval)

*Prepared for Julius, Myra, Sam and the TTA board. This describes, in everyday language, what the new
system will do — and, just as importantly, what it won't do (yet). Please read it and tell us where it's
wrong or missing before we start building.*

---

### What this is

**rosetta** is a brand-new membership system, built specifically for TTA, to replace Wild Apricot. It
will be the place where staff manage members, take payments, run events and see the numbers — without the
things that make Wild Apricot painful (clunky screens, broken styling, hours of manual admin, and a
system that can't grow with us).

We're building it in stages. **The first version — targeted for September — covers the staff side
(managing members, taking payments, running events, reporting) *and* the member login area / member
hub** where members sign in to see their status, resources and events. The **public marketing website**
and the **public "Find a Tutor" directory** come later (explained at the end). We're starting with what
saves you the most time first.

**How to read this:** each feature says ✅ **what it will do** and 🚫 **what it won't do (for now)**. "For
now" means it's planned for a later stage, not that it's gone forever.

---

## Part 1 — What's in the first version

### 1. Member records & profiles
The core of the system: one clean, complete record per member.

✅ Will do:
- Hold everything you keep today — name, contact details, business address, WhatsApp, subjects taught,
  tuition type, qualifications, "how did you hear about us", and admin notes.
- Keep DBS details, references and safeguarding-course completion all in one place.
- Show a clear **verified / processing** status, and a **traffic-light (red / amber / green)** picture of
  how complete and compliant each member is, so you can see at a glance who needs chasing.
- Let you search and filter members (by status, type, tag, "joined in the last 7/30 days", etc.) and do
  things to lots of members at once (bulk email, bulk status change, bulk tagging).
- Keep a history/notes timeline on each member (e.g. "approved on…", "level changed by Julius on…") so
  there's always an audit trail.

🚫 Won't do (for now):
- Members won't appear in a public, searchable "Find a Tutor" directory yet — that's part of the public
  website, which comes later. (Members *can* log in and manage their own profile — see "Member login area
  & hub" below.)

### 2. Membership types & corporate / bundle members
A clean, simple set of membership types instead of Wild Apricot's ~40 overlapping, half-deleted ones.

✅ Will do:
- Support all the real membership types (Professional Tutor, Undergraduate, the Corporate sizes, Affiliate
  Partner, Education Agent, Charity, Launchpad, etc.), but tidied up.
- Treat "monthly vs annual" as simply a payment choice on one membership — **not** a separate type. No more
  duplicate levels.
- Properly model **corporate members with bundle members**: a company (e.g. Keystone) holds the membership
  and has several named tutors attached to it. One of those people is the **main contact**. A company
  always has at least one person attached.
- Count members two ways, cleanly: **paying members** (a corporate counts as one) and **named members**
  (every person counts) — so board numbers finally make sense.

🚫 Won't do (for now):
- Companies can't add or manage their own bundle members themselves yet — staff still add them (as today).
  Self-service for companies comes with the member area later.

### 3. Joining the association (onboarding) & approvals
One smooth sign-up flow instead of a dozen hand-built pages.

✅ Will do:
- A single online sign-up: choose your membership, fill in details, agree to the policies (Code of
  Practice, DBS Policy, etc.), and pay — all in one flow.
- New applications land in an **approval queue** for staff to **Approve or Reject**, exactly as you do now
  (so you keep oversight, e.g. for DBS).
- Send the welcome email and details once approved (sent through Mailchimp — see Emails).

🚫 Won't do (for now):
- The sign-up pages won't be a fully designed marketing website — they're functional, on-brand pages. The
  polished public website is a later stage.

### 4. References
Replaces the Google-Form-and-copy-paste routine.

✅ Will do:
- Send a referee a simple online form; when they complete and confirm it, the reference and its date land
  on the member's record **automatically** — no more manual date entry.
- Let the referee tick a box to allow the reference to be shown publicly (so members can point people to it
  later).

🚫 Won't do (for now):
- We still record both references and a human still glances at them — references aren't auto-judged.

### 5. Compliance & DBS (tracking + a clear dashboard)
This is one of the biggest time-savers and one of the strongest reasons to move.

✅ Will do:
- Track each member's DBS validity, Update-Service status, references and safeguarding completion, with the
  "valid within the last year" rule built in.
- Show a **live compliance dashboard**: who is fully compliant, who's in a grace period, and who's out of
  compliance — at any moment, without spreadsheets.
- Flag members who are missing important things, so you can chase them in a couple of clicks.

🚫 Won't do (in the first version):
- It won't yet *automatically* connect to the daily DBS-checking service (tutor-check.co.uk), send the
  out-of-compliance emails on its own, or auto-suspend after the 3-month grace period. That automation is
  the very next thing after launch — the first version gives you the visibility; the automation follows.

### 6. Tags & groups
✅ Will do: let staff create, rename and delete **tags** and apply them to members (e.g. Partner, Fellow,
Community Hub Leader, working groups), singly or in bulk. These double as the segments we send to
Mailchimp. 🚫 Won't do: tags don't yet drive what members see when logged in (member area is later).

### 7. Payments & membership fees
✅ Will do:
- Take card payments through **Stripe**, for both monthly and annual memberships, with automatic renewal
  and a 30-day heads-up before renewal.
- Handle one-off purchases (event tickets, DBS admin, packs) with **member vs non-member pricing**.
- Keep proper **invoices**, downloadable and exportable for the accountant, and handle the **TTA vs
  Tutoring-for-All / VAT** split by tagging each sale correctly.
- Still allow the handful of members who pay by bank transfer (and legacy GoCardless) to be managed.

🚫 Won't do (for now):
- No direct accounting-software integration (e.g. QuickBooks) — it's export-to-spreadsheet, as the
  accountant prefers. Discount codes and the more advanced incentive schemes come in this stage too but
  will be confirmed with you first.

### 8. The store
✅ Will do: sell products to members and non-members — DBS admin support, Compliance Pack, VAT Pack, etc. —
at the right price for each, with a paid/free/fulfilled status, and trigger the follow-up (e.g. send the
DBS next-steps PDF). 🚫 Won't do (for now): the International Partner Programme, conference-recording
paywall and similar specialist products come later.

### 9. Events
✅ Will do:
- Create events quickly, and **duplicate** a past event to make a new one (a big time-saver you asked for).
- Offer ticket types **restricted by membership** (members-only, specific tiers, or open to all) — enforced
  properly, not via discount-code workarounds — with different prices per type, and free for members where
  entitled.
- Keep the meeting link (Google Meet/Zoom) hidden until someone has registered.
- Send registration confirmations and reminders (through Mailchimp), and record **attendance**.
- Show events with counts and attendance at a glance; support online and in-person events, including the
  awards.

🚫 Won't do (for now):
- Waiting lists and automatic Google-Meet attendance-matching are "nice to have" and may come slightly
  later. The annual conference stays on Crowd Comm (out of scope). We'll have a dedicated session with Sam
  to get the events detail exactly right.

### 10. Reports
✅ Will do: clear charts and tables (not Wild Apricot's wall of colours) for new members by type, finances,
**churn and retention** — including the important "lapsed then renewed" case so we don't over-report losses
— monthly recurring revenue, and the paying-vs-named member counts. 🚫 Won't do (for now): fully custom,
build-your-own report designer — we'll build the reports you actually use.

### 11. Emails & Mailchimp
✅ Will do: keep using **Mailchimp** for writing and sending member emails (you already have everyone
there). rosetta will have a **proper, automatic Mailchimp connection**: the moment you add a member, change
their details, or tag them in rosetta, that change is sent straight to Mailchimp through its API — so your
audience and segments are always in sync, with no manual exports. 🚫 Won't do (for now): we're **not**
moving email *writing/sending* into rosetta yet (no in-app email editor) — you'll still compose and send in
Mailchimp, which you know and which looks good. Bringing email fully in-house is a possible later step.

### 12. Member login area & hub
The members' own logged-in area — the part members actually see when they sign in.

✅ Will do:
- Let members **log in** and see their **dashboard**: their membership status, compliance/DBS status and
  what they need to do, upcoming events, and quick links.
- Let members **view and update their own profile** (with admin approval where it matters).
- Surface the **resource library** (TTA Code of Practice, safeguarding/GDPR templates, marketing guide,
  etc.), membership **logos**, the **legal helpline** details, and the **partner discounts** list.
- Show **events** (browse + register) and **DBS / CPD** info pages, pulling live from the rest of rosetta.

🚫 Won't do (for now):
- It won't be a free-form, edit-any-page website builder (a full CMS). Staff manage the hub's content in a
  **structured way** — adding documents, links, logos and notices through the admin — rather than
  designing pages. *(This keeps to the "we're not building a CMS" decision while still giving members a
  proper, on-brand area. Tell us if you want fuller page-editing — that's a bigger build.)*
- Online **voting / board elections** and **company self-service** (a corporate managing its own bundle
  members) will follow shortly after, not necessarily on day one.

---

## Part 2 — What's deliberately NOT in the first version (and why)

These are real features we expect to build — just not first. Flagging them so there are no surprises.

- **Public "Find a Tutor" website & directory** — the searchable public listing of tutors (and the separate
  agency and partner directories, and the map view). *Why later:* it's a key value driver and we will build
  it, but it sits on top of clean member data — which the first version creates — and belongs with the
  public website stage. **This is the one deferral we'd specifically like the board to confirm.**
- **Automated DBS compliance** — the daily tutor-check.co.uk sync, automatic out-of-compliance emails, and
  automatic suspension after grace. *Why later:* the first version gives you the dashboard and visibility;
  the automation is the immediate next step.
- **Voting / board elections online** — *why later:* it lives in the member login area.
- **Jobs board** (with multiple currencies) — *why later:* a standalone area, lower urgency.
- **In-app email editor / retiring Mailchimp** — *why later:* Mailchimp works well today; revisit once the
  core is live.
- **Virtual exam centre, trade missions, International Partner Programme pages** — *why later:* separate
  initiatives, roughly six months out.
- **Moving your existing data across from Wild Apricot** — members, history, events and documents. This is a
  defined piece of work we'll schedule **before** the Wild Apricot renewal in March, so nothing is lost.

---

## Part 3 — Timeline & what we need from you

- **First version (staff side): targeted for September.** Built in order: members & onboarding → payments →
  events → reports.
- **Wild Apricot renews in March** — we'll plan the data move ahead of that.
- **What we need to start:** your approval of this brief, plus three short follow-ups — a session with
  **Sam** on events detail, a short call with **Stephen** on the VAT / TTA-vs-TFA money split, and the
  **board's nod** on deferring the public marketing website + "Find a Tutor" directory to a later stage
  (Part 2). *Note: adding the member login area & hub to the first version (good call) makes September
  tighter — we'll keep you posted on sequencing.*

*If anything here is wrong, missing, or in the wrong order, tell us now — it's much cheaper to change on
this page than later.*

---

*A separate technical document, [`BRIEF.md`](./BRIEF.md), covers the build detail for developers.*
