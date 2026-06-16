Record a rosetta PR demo end-to-end as an animated **GIF**: best-guess generate a Playwright journey from the branch diff if one doesn't exist, drive it through the rosetta frontend with a **visible moving cursor** and **slow, readable pacing**, convert the recording to a GIF, and upload it straight into the PR description via the GitHub API — no browser drag-drop, no manual approvals. The full-quality webm is linked beside the GIF.

This is the rosetta-stack sibling of bobbin's `/pr-record-gif`. Use it for PRs that drive the rosetta frontend (`~/repos/rosetta/frontend`). The cursor is visible and moves to each target before clicking, and every beat holds long enough to read.

## Usage

```
/pr-record-gif [<name>]
```

- `<name>` — base filename. Defaults to the current rosetta branch, snake-cased (`m0/members-ui` → `m0_members_ui`).

## Output format (always a GIF)

Every demo is an animated flow. Record a single `.webm` at 1440×900, then convert it to a GIF for the PR. **We upload the GIF, not the webm:** a GIF embeds inline via `<img>` and autoplays/loops on GitHub, whereas a `<video src=…/raw/…>` renders blank for a private repo. The webm is kept and linked as a full-quality fallback.

## Preflight (run all, stop on first failure)

The journey drives the **real** frontend, which logs in against the **real** backend, so both must be up. **Never start the servers yourself** — tell the user to.

1. **Frontend up on :5001.** `curl -s -o /dev/null -w '%{http_code}' http://localhost:5001` → expect `200`.
2. **Backend up + healthy on :5000.** `curl -s http://localhost:5000/` → expect `{"status":"healthy"}`.
3. If either is down → **STOP** and tell the user to start the stack:
   - Postgres + Redis running (the backend needs both).
   - Backend: `cd ~/repos/rosetta/backend && make run-dev` (and `make seed` once, to create the dev admin).
   - Frontend: `cd ~/repos/rosetta/frontend && npm run dev`.

   Do not start them.
4. **PR exists for this branch.** `gh pr view <branch> --repo TheTutorsAssociation/rosetta --json url -q .url`. If not, stop and ask the user to open one first (the GIF is uploaded into the PR body).
5. **Frontend is serving this branch.** The dev server has HMR, so its working tree must be on the branch under test. If unsure, remind the user to check out the branch in `~/repos/rosetta/frontend` and restart `npm run dev`.

## File conventions

- **Journey (NOT committed):** `~/repos/pr-demos/rosetta/<name>.mjs`. A standalone Playwright script that imports the shared driver and records to `PR_DEMO_OUTPUT_DIR`. Auto-generated from the diff if missing.
- **Setup (committed, optional):** `~/repos/rosetta/backend/scripts/pr_setups/<name>.py`. Only if the demo needs DB rows the seed doesn't have. Most demos **mock** the API instead (see below), so this is usually unnecessary.
- **Driver (shared):** `~/repos/pr-demos/_lib/rosetta-driver.mjs` — handles chromium + video, the visible cursor, login as the seeded admin, and the cursor-moving navigation/click helpers.

## Steps

1. **Resolve `<name>`** from the current rosetta branch (kebab/slash → snake).
2. **Best-guess generate the journey if missing** (`git -C ~/repos/rosetta diff --stat main...HEAD` + targeted reads of the changed routes/components under `frontend/app/`). Only generate if `~/repos/pr-demos/rosetta/<name>.mjs` doesn't exist — never overwrite a hand-edited journey. Use the contract below: log in, navigate to the route(s) the diff touches, and drive a continuous flow with `moveAndClick` + captions. Tell the user briefly what got generated.
   - **Mock endpoints the running backend can't serve.** If the feature's backend isn't on the running branch yet (common when FE leads BE), mock its endpoints so the demo runs against realistic data. Use `mockJson(context, '**/path**', payload, { status })` for a static response, or **`mockCollection(context, '**/path**', { onCreate, createResponse })` for a stateful list** where the UI must reflect creates/deletes (GET list → POST create → list shows it → DELETE → gone) — the usual shape for a CRUD feature demo. rosetta list endpoints return a paginated `{ items, total, page, page_size }` envelope (the default in `mockCollection`); pass `paginated: false` for a bare-array endpoint. Login still goes through the real backend (`POST /auth/login` → JWT in `localStorage('token')`).
3. **Run the setup script if present:** `cd ~/repos/rosetta/backend && uv run python scripts/pr_setups/<name>.py`. Surface output; stop on error.
4. **Clear the output dir, then run the journey.** Stale `.webm`s from a failed attempt cause "which take is the good one?" ambiguity, so wipe first. Two plain commands:
   ```
   rm -f /tmp/pr_demo_out/*.webm
   PR_DEMO_OUTPUT_DIR=/tmp/pr_demo_out node ~/repos/pr-demos/rosetta/<name>.mjs
   ```
   If it exits non-zero, surface the error and stop. Common fixes: a changed selector (patch the journey), or a real (un-mocked) API 404 (add a `mockJson`/`mockCollection`).
5. **Move the webm:** `mv /tmp/pr_demo_out/*.webm ~/repos/pr-demos/rosetta/<name>.webm` (one file, since you cleared the dir).
6. **Convert the webm to a GIF** (two-pass palette for clean colour). The slow, cursor-led pacing makes clips long, and a GitHub-inline GIF balloons fast — so use **1000px / 10fps for short clips (≲45s), but start at `scale=800` / `fps=8` for anything longer**. Two separate commands (swap in `800`/`fps=8` as needed):
   ```
   ffmpeg -nostdin -loglevel error -y -i ~/repos/pr-demos/rosetta/<name>.webm -vf "fps=10,scale=1000:-1:flags=lanczos,palettegen=stats_mode=diff" /tmp/pr_demo_out/palette.png
   ffmpeg -nostdin -loglevel error -y -i ~/repos/pr-demos/rosetta/<name>.webm -i /tmp/pr_demo_out/palette.png -filter_complex "fps=10,scale=1000:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" ~/repos/pr-demos/rosetta/<name>.gif
   ```
   `ls -la` the GIF; if it's still over ~10 MB, drop further (`fps=6` / `scale=720`) and re-render.
7. **Verify the take before uploading.** Grab a frame and actually look at it, so a bad recording (cursor missing, a blocking modal caught mid-frame, wrong page) never reaches the PR:
   ```
   ffmpeg -nostdin -loglevel error -y -ss 8 -i ~/repos/pr-demos/rosetta/<name>.webm -frames:v 1 /tmp/pr_demo_out/frame.png
   ```
   Read `frame.png` (try a couple of timestamps); confirm the red cursor is visible and the flow looks right. Re-record if not.
8. **Upload both files to the PR via the GitHub API** — no browser. Pass the rosetta repo to the generalized helper:
   ```
   UPLOAD_REPO=TheTutorsAssociation/rosetta UPLOAD_REPO_PATH=~/repos/rosetta node ~/repos/pr-demos/_lib/upload-to-pr-api.mjs ~/repos/pr-demos/rosetta/<name>.gif <pr-number>
   UPLOAD_REPO=TheTutorsAssociation/rosetta UPLOAD_REPO_PATH=~/repos/rosetta node ~/repos/pr-demos/_lib/upload-to-pr-api.mjs ~/repos/pr-demos/rosetta/<name>.webm <pr-number>
   ```
   The helper pushes each file to the `pr-screenshots` branch on `TheTutorsAssociation/rosetta` and appends an embed. Then **fetch the body** (`gh pr view <pr> --repo TheTutorsAssociation/rosetta --json body -q .body`) and rewrite it into a single `## Demo` section, deleting the helper's leftover `#### Supporting Screenshots` blocks:
   ```
   ## Demo

   <one-line description of what the clip shows>

   <img src="https://github.com/TheTutorsAssociation/rosetta/raw/pr-screenshots/<name>.gif" width="900">

   <sub>Full-quality video: https://github.com/TheTutorsAssociation/rosetta/raw/pr-screenshots/<name>.webm</sub>
   ```
9. **Output:** the final file paths, the PR URL, and a one-line confirmation. Don't open the GIF in a viewer.

## Journey contract

Every journey imports the shared driver at `~/repos/pr-demos/_lib/rosetta-driver.mjs`. It handles browser/context + video, the visible cursor, login as the seeded dev admin (`admin@example.com` / `rosetta-dev-password` — override with `ADMIN_EMAIL` / `ADMIN_PASSWORD`), and cursor-moving navigation/click helpers.

Helpers (import from `'../_lib/rosetta-driver.mjs'`):

| Helper | What it does |
|---|---|
| `setupRecorder({ outputDir, viewport?, slowMo?, headless? })` | Launches chromium with `slowMo` (default 200) + `recordVideo`, injects the visible cursor. Returns `{ browser, context, page, consoleErrors }`. |
| `login(page, { email?, password? }?)` | Logs in via `/login` (button "Sign in"), waits out React hydration, and waits for the JWT to land in `localStorage('token')`. |
| `gotoPage(page, path, { waitMs? })` | `page.goto` + networkidle + hold (default 1500ms). |
| `moveTo(page, target)` | Tween the visible cursor to a selector/Locator's centre with `mouse.move(steps:28)`. |
| `moveAndClick(page, target, { waitMs? })` | `moveTo` then click — **use for every demo-relevant click** so the cursor's travel is recorded. |
| `fillField(page, target, value)` | Move to a field and type it character-by-character. |
| `mockJson(context, urlGlob, payload, { status?, method? })` | Mock a static backend JSON (or 204) response. |
| `mockCollection(context, urlGlob, { initial?, onCreate?, createResponse?, paginated?, pageSize? })` | Mock a **stateful** REST collection (GET list / POST append / DELETE by id → 204). Wraps GETs in rosetta's paginated envelope by default. |
| `caption(page, html, bg?)` | Top caption bar; update text/colour per beat (default bg is the TTA blue `#091697`). |
| `pause(page, ms)`, `log(msg)`, `ROSETTA_URL` | Helpers. |

Minimum template:

```js
import {
  setupRecorder, login, gotoPage, moveAndClick, fillField,
  caption, pause, teardown, mockJson, mockCollection,
} from '../_lib/rosetta-driver.mjs';

const recorder = await setupRecorder({ outputDir: process.env.PR_DEMO_OUTPUT_DIR });
const { page, context } = recorder;

try {
  // Mock any endpoints the running backend can't serve yet — static or stateful:
  // await mockJson(context, '**/members/**', { ... });
  // await mockCollection(context, '**/members**', { onCreate: (body) => ({ id: 1, ...body }) });

  await login(page);

  await caption(page, 'Intro — what this PR adds');
  await pause(page, 3000);

  await gotoPage(page, '/');
  // Drive a continuous flow with moveAndClick + captions; hold each beat 2.5–4s.
  await pause(page, 3500);
} finally {
  await teardown(recorder);
}
```

## Pacing & cursor (the point of this command)

- **Always** drive demo-relevant clicks with `moveAndClick` (never a bare `locator.click()`) so the red cursor visibly travels to the target first.
- Hold captions **2.5–4s** — long enough to read. `slowMo: 200` already slows each action; add explicit `pause()` between beats.
- Keep captions to one line, pinned to the top (GitHub's player controls cover the bottom). Highlight the element under discussion when it helps.

## Don'ts

- **Don't start the dev servers.** If a port is down, tell the user how to start the stack (preflight step 3).
- **Don't commit videos, GIFs, or journeys.** They live in `~/repos/pr-demos/rosetta/`. Optional `scripts/pr_setups/*.py` (if used) is committed to rosetta.
- **Don't regenerate an existing journey** — the user may have hand-edited it.
- **Don't open a browser to upload.** Use the gh API helper.
- **Don't ship a demo that doesn't show the change.** If you mock responses, make them realistic.
