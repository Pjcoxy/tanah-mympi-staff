# Tanah Mympi — Housekeeping App (LIVE)

This is the **live** Tanah Mympi housekeeping app and the dedicated working folder for all
updates and maintenance. Launch Claude Code from here so every session is scoped to this project.
Resume past work with `claude --resume` (pick from the list) or `claude -c` (continue most recent).

> Note: a Firebase migration was once prototyped but **never adopted** and has been deleted.
> This Google Sheets version is the only one, and it's the one in production.

## What this is
A real-time housekeeping checklist app for a boutique resort. Staff complete a progressive room
sign-off form and flag action items; submissions are written to a Google Sheet via an Apps Script
web app. No build step — self-contained HTML files with vanilla JS/CSS plus a Chart.js dashboard.

## Hosting & URLs
- **GitHub repo:** https://github.com/Pjcoxy/tanah-mympi-staff (public)
- **Hosting:** GitHub Pages (branch `main`, root). Deploy = commit & push to `main`.
- **Staff app:** https://pjcoxy.github.io/tanah-mympi-staff/  (serves `index.html`)
- **Stats dashboard:** https://pjcoxy.github.io/tanah-mympi-staff/dashboard.html
- The repo is **public but kept out of search results** via `<meta name="robots" content="noindex">`
  in each HTML file and a root `robots.txt` (`Disallow: /`).
- `gh` CLI is installed and authenticated as `Pjcoxy`, so repo/Pages settings can be changed from
  the CLI (e.g. `gh repo edit`, `gh api .../pages`).

## Files
- `index.html` — the entire staff app (single file): config + UI + checklist + login + submit.
- `dashboard.html` — stats dashboard (Chart.js from CDN). Reads live data via `?action=records`.
- `apps-script/Code.gs` — version-controlled COPY of the Apps Script backend (see Backend below).
- `HOUSEKEEPING_APP_SUPPORT.md` — human support / as-built guide (the source).
- `HOUSEKEEPING_APP_SUPPORT.pdf` — shareable PDF, GENERATED from the `.md` (don't hand-edit).
- `docs/architecture.svg` — architecture diagram used in the support guide.
- `docs/build_support_pdf.py` — regenerates the PDF: `python docs/build_support_pdf.py`.
- `docs/screenshots/` — login.png / form.png / dashboard.png for the guide.
- `robots.txt` — blocks crawlers.

## Documentation model (keep these in sync on EVERY change)
Two docs, two audiences — update both in the same turn when the app changes:
1. **`CLAUDE.md`** (this file) — terse project/operator context for AI-assisted maintenance.
2. **`HOUSEKEEPING_APP_SUPPORT.md`** — standalone human guide (architecture, ops, troubleshooting).
   After editing it, regenerate the PDF: `python docs/build_support_pdf.py` (Markdown → styled HTML →
   Edge headless `--print-to-pdf`; missing screenshots become placeholders automatically). Commit the
   refreshed `.pdf` so a current shareable copy always exists in the repo. The old `.rtf` was deleted.

## Backend (Google Apps Script + Google Sheet)
- **Data Sheet** (`SHEET_ID` `19lrq6Sp7wY0q74mtZd0VDgLwj4QGu1Vf-LUEEMDzbPY`), still titled
  "Untitled spreadsheet". Two tabs:
  - `Staff` — A=Name, B=PIN (**plaintext**, despite the support doc claiming hashed), C=Active.
  - `Records` — `Type, Timestamp, Staff Member, Room, Service Type, Action Required, Notes, Device`.
    One combined log: `Type` is SUBMISSION / LOGIN / LOGIN_FAIL / RECALL. Timestamps are stored as
    text like `18 June 2026, 4:54 PM`.
- **Apps Script project** (standalone, NOT the spreadsheet's empty bound script):
  https://script.google.com/d/1F7ZbhlHNl_BI9W0_mOkN9hWfAHSKHNOO5w9Ul4LsvfZRsAs_wgpGWpAy/edit
  - `doGet` routes on `action`: `?action=records` → all Records rows (objects, never PINs);
    anything else (incl. the app's `?action=staff`) → active staff names.
  - `doPost` handles `login` / `submit` / `recall`.
- **The repo copy and the live project are NOT auto-synced.** After editing `apps-script/Code.gs`,
  paste it into the project and deploy a **New version** of the *existing* deployment
  (Deploy → Manage deployments → ✏️ → Version: New version) so the `/exec` URL stays the same.
- Endpoint URL lives in the front-end as `SHEETS_URL` (in `index.html` CONFIG and `dashboard.html`).
  If you ever create a *new* deployment instead of a new version, the `/exec` URL changes and must be
  updated in **both** files.

## Configuration (top of the `<script>` in `index.html`)
`const CONFIG = { SHEETS_URL, TIMEOUT_MINS, ROOMS }`
- `SHEETS_URL` — Apps Script deployment URL (the backend). Mirror in `dashboard.html`.
- `TIMEOUT_MINS` — inactivity session timeout (currently 20).
- `ROOMS` — room list: 101–105, 201–205, Villa 1–3, Suite A/B. Edit here to add/remove rooms.

## Form structure
Progressive disclosure: Step 1 Room → Step 2 Service Type → Step 3 Checklist → Action Items → Submit.
- Service types: `full` (Full Clean), `refresh`, `turndown`, `inspection`.
- Checklist items are `<div class="item" data-section="..." data-services="...">`. The
  `data-services` attribute (space-separated) controls which service types show that item.
  Sections: `bedroom`, `bathroom`, `minibar`, `final`.
- To add/change a checklist item: copy an existing `.item` div, set its `data-section` and the
  `data-services` list. `updateServiceItems()` handles show/hide on service-type change.
- After login a **gold "Logged in as NAME" banner** is pinned in the sticky header (shared-device
  safety), with a "Not you? Sign out" button. Set in `showForm()`.

## Dashboard notes (`dashboard.html`)
- Pulls `?action=records`, filters to `Type === 'SUBMISSION'`, and renders six charts:
  rooms/week + 4-week rolling average, per-staff totals, service-type mix, action flags,
  busiest day-of-week, busiest rooms. `render(records)` is global; `load()` fetches.
- `parseTs()` parses the timestamps; weeks bucket to the Monday start.
- Endpoint is **open** (anyone with the URL can load stats) — operational data only, no PINs.
- LIVE & verified (2026-06-29): `?action=records` returns the data and charts render.
- Note: the endpoint returns date cells as **ISO/UTC** strings (e.g. `...T08:54:00.000Z`), not the
  `18 June 2026, 4:54 PM` text format. `parseTs()` handles both via a `new Date()` fallback. Because
  ISO is UTC, the browser shows them in the viewer's local TZ — a late-night entry can shift to the
  adjacent day/week for far-away viewers. Pin to a fixed TZ (backend `formatTs`, or parse as a fixed
  offset in `parseTs`) only if exact day boundaries ever matter.

## Working notes for maintenance
- No package.json / no build. Edit the HTML directly; preview locally (a `.claude/launch.json`
  config named `housekeeping` serves this folder via `python -m http.server`).
- Chart.js dashboard renders fine but the preview screenshot tool times out on the 6 canvases —
  verify via `preview_eval` (check chart dimensions / data) rather than screenshots.
- If submissions break, first suspect the Apps Script deployment.
- Commit/push only when asked.

## Conventions
- Keep `index.html` a single-file app; match the existing dense inline HTML/CSS/JS style.
- `dashboard.html` JS is kept readable (analytical code) — that's intentional, not a mismatch.
- Don't change `SHEETS_URL` unless explicitly asked — it's the production backend link.

## Changelog
- **2026-06-29** — Renamed folder `app-testing` → `housekeeping`; deleted unused Firebase prototype.
  Made repo public + enabled GitHub Pages; added `noindex` + `robots.txt`. Renamed
  `housekeeping.html` → `index.html` for a clean Pages URL. Added "Logged in as" header banner.
  Added `dashboard.html` (Chart.js stats) and the `?action=records` backend endpoint; committed a
  repo copy of the backend at `apps-script/Code.gs`. Backend redeployed and dashboard verified live
  (records endpoint returning data). Rebuilt the human support guide
  (`HOUSEKEEPING_APP_SUPPORT.md` + generated `.pdf` + `docs/architecture.svg` + build script);
  deleted the stale `.rtf`. Screenshots still pending (preview tool couldn't capture the live pages).
