# Design: a standalone app around this engine

*Status: design only. Nothing in this document is built. It exists so the decisions below — settled
in discussion — outlive the conversation that settled them.*

## What it is

A downloadable desktop app for people who cannot, and should not have to, drive a coding harness:
drop course material in, talk to an agent in a chat pane, review the cards it proposes, and get a
deck out. The engine is this repository, unchanged — the app is a shell that holds the method, runs
the checks, and turns the pipeline's stage gates into screens.

The app's reason to exist over "clone the repo and point an agent at it" is not convenience alone.
The **card preview is the feature**: every deck this method has produced was improved by an owner
looking at rendered cards and flagging what the pipeline missed. The app makes that loop
first-class — tap a card, flag it, and the flag routes as a finding — instead of something that
happens over screenshots.

## The agent: ACP first, API key as fallback

Most of the audience already pays for an agent subscription. The
[Agent Client Protocol](https://agentclientprotocol.com) is how an app taps it: the app is an ACP
*client*, and the user's own subscription-authenticated CLI (Claude Code through its ACP adapter,
Gemini CLI natively, Codex through an adapter — verify each at build time) is the agent server. The
app never touches credentials; auth lives in the vendor's CLI, and the tokens ride on the
subscription the user already pays for.

That ordering is decided by economics, not taste. A full lecture run is token-heavy — hours of
transcript, dozens of slide images, an audit pass — which is real per-lecture money on a metered
API key and bundled cost on a subscription. And for a non-technical user, obtaining an API key
(console account, billing details) is *more* friction than installing one CLI and signing in once.

The embedded-agent route (Claude Agent SDK, user-supplied API key) ships as the fallback tier for
users with neither, behind a cost estimate shown before every run.

Onboarding on the default path is exactly two steps: install the agent CLI, sign in. That is the
floor; the repo-clone-and-harness step this app deletes was the disqualifier.

## What the app owns, whichever agent is behind it

- **The method files, bundled unmodified.** They stay prose, they stay the single source of truth,
  and the app reads them from its bundle the way the skills read them now. Improving the method
  never means rebuilding the app; the app never edits the method.
- **The pipeline as screens.** Extract → inventory review → Organize → plan review → Cards → deck
  preview → audit → deliver. Each artifact (`inventory.md`, `plan.md`, `deck.json`) is written
  beside the user's course folder exactly as the harness writes it, so a run can resume and a
  power user can inspect.
- **The flag loop, with the standing rule enforced by the interface**: the writer ratifies
  nothing. A flagged card routes to a fresh adjudicator context that returns fix-or-approve; the
  writing context applies verbatim. In the harness this is discipline; in the app it is wiring.
- **The checks, ported.** `check_deck.py` and `render_review.py` are a few hundred lines of
  stdlib; they port to TypeScript and run on every stage the way the repo's hook fires on every
  `deck.json` write. The seven reference cards ship as the fixture set, and any check the app
  grows must pass them first — the repo's standing rule, inherited whole.

## The four hard edges, and the calls made on each

1. **File conversion.** No bundled LibreOffice. The model reads PDFs natively, so the app asks the
   user to export slides to PDF (one click in any slide software) and ingests that. Rasterised
   figures are read by vision, as the method already requires.
2. **Transcription.** v1 is bring-your-own-transcript — lecture platforms hand students one, and
   the method treats the transcript as emphasis, not anchor, so a rough one degrades gracefully.
   A bundled `whisper.cpp` tier can follow; the Mac-only Python tooling the repo uses today does
   not ship in a binary.
3. **Anki.** Default output is an **`.apkg` file** the user double-clicks — no add-on, no running
   Anki, works everywhere. If AnkiConnect is detected, the app offers the live tier: direct
   insert, tier tags, suspend/unsuspend, and in-place repair of existing decks (which `.apkg`
   export cannot do).
4. **Cost.** Shown, never hidden: an estimate before each run, an audit-depth selector, and a
   running meter on the API-key tier. On the ACP tier the cost is the subscription the user
   already has — which is the argument for that tier being the default.

## Shape of the build

Tauri (small binary, web UI) over Electron. One window: chat pane, file-drop, stage rail, preview
pane. State on disk in the user's course folders, none in the app. No server, no accounts, no
telemetry, no cloud storage — the app is as local as the repo it wraps.

Realistic effort: a few weeks to a credible MVP for one person working with an agent, then
maintenance forever — model behaviour drifts, agent CLIs version, Anki's format moves. The design
choice that keeps maintenance small is the first one above: everything that decides what a card
says lives in the bundled prose, not in the app's code.

## Non-goals

- No web version, no hosted service, no accounts.
- No card-authoring logic in app code — the line the repo already holds ("no code chooses what a
  card says") applies to the app verbatim.
- No editing of the method from inside the app. Method changes happen in this repository, with the
  discipline this repository imposes on them.

## Open questions, named so they are not settled by accident

- Codex's ACP support is adapter-based rather than first-party at the time of writing — verify
  before listing it on the tin.
- Windows and Linux: `.apkg` export and ACP both travel; the transcription tier and any AnkiConnect
  detection need per-platform testing.
- Media-heavy decks: `.apkg` bundles images fine, but the size estimate belongs in the preview.
- Whether the app's adjudicator context runs on the same agent session or a second one — the rule
  only requires a context that wrote none of the cards.
