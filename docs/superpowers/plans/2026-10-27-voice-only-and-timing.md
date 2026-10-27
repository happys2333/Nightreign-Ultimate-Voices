# Voice-only and timing implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove only proven native ultimate vocalizations and deliver exact animation-driven start/end OW callouts without runtime polling.

**Architecture:** Preserve all native audio events. Add dedicated voice-only Wwise events for the three timing changes and four whitelisted TAE rows in the effective animation binder. Investigate vocal triggers independently; do not mute mixed FX or material dialogue.

**Tech Stack:** Python 3.12+, SoulsFormatsNEXT/net9.0 build-time helper, native Wwise 135, ME3.

### 1. Evidence and source safety

- [x] Record native/MMV animation branches, accepted-start and Scholar completion boundaries.
- [x] Verify native/MMV Binder and target TAE no-op round trips are byte identical.
- [x] Exclude complete original event removal and SoundType15 removal as unsafe.
- [x] Identify a proven voice-only trigger/field and scope it to ultimate actions.

### 2. Build-time animation helper

- [x] Add `tools/tae` helper with bounded JSON operations, exact source digest and animation fingerprint checks, dedicated event groups, and no game-directory output.
- [x] Test malformed/stale plans before implementation; add real Binder regression and compare every unmodified member/event/header/group after writing.
- [x] Add pinned SoulsFormats preparation and metadata; run helper only before packaging.

### 3. Voice event and Python integration

- [x] Test creation of a dedicated routed voice event while retaining every original HIRC object and media.
- [x] Implement new-event creation with explicit template routing and atomic collision/budget handling.
- [x] Resolve the effective animation source from ME3 packages, loose game assets or selective native Data3 extraction.
- [x] Integrate four TAE insertions only for enabled/retimed roles; package the output atomically.

### 4. Native vocal isolation

- [x] Apply only audited voice-only changes, preserving charge/impact and unrelated playback.
- [x] Add regression evidence showing both vocal suppression and effect preservation; record any actual limit without claiming an unverified result.

### 5. Delivery

- [x] Rebuild current ten-role OW package and Chinese test package as appropriate.
- [x] Run targeted tests, full unit suite, Binder difference audit and real independent Wwise captures.
- [x] Review specification and implementation, update README/event map/verification records, and commit.
- [x] Keep actual game/co-op acceptance separate and do not launch the game repeatedly.

Verification: 95 tests passed including real MMV input; 32 independent Wwise OW/vocal captures passed; final OW and Chinese packages each own 25 verified files. Native fallback extraction plus four-row patch also passed (538 members). Actual game/co-op acceptance remains pending; no game restart was requested.
