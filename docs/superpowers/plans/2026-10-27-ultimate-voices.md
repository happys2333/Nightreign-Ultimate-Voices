# Ultimate Voices Implementation Plan

> **For agentic workers:** Use executing-plans to implement sequentially in this session. Steps use checkbox syntax for tracking.

**Goal:** Deliver an offline builder and local native-event audio mod for Nightreign, with ten configurable character clips and Chinese test voices.

**Architecture:** Resolve original game resources and installed ME3 overrides before patching existing one-shot ultimate events. Preserve original soundbank objects, append bounded PCM voice media and actions, and generate an isolated profile. No runtime worker, DLL or network messages.

**Tech Stack:** Windows, Python 3.12+, unittest, cryptography (archive AES), .NET/SoulsFormats for read-only animation inspection when needed, Wwise bank inspection tools.

---

## Execution status (2026-10-27)

Tasks 1–4 implemented. Actual events reside in `sd/hero01.bnk` through `hero10.bnk`; no shared cs_main override is needed. All 38 automated tests pass, the ten-bank local build and owned-package verification pass, and independent spec/code reviews pass. ME3 launched the generated profile and loaded the existing save into Roundtable Hold.

Task 5 has completed static/independent-format, preservation, CLI, startup and review checks. Actual ultimate playback, two-client mixed-install co-op, distance behavior and FPS comparison remain open. Automated keyboard input was not reliably accepted by the game; a manual training-ground playback check has been requested. See `docs/verification.md` for the acceptance matrix; no pending game checks are represented as passed.

## Task 1: Establish resource evidence

- [ ] Inspect the local sound archive headers and relevant player animation/FXR files using read-only extraction into `local/`.
- [ ] Record exact local game version and source SHA-256 hashes, and record ultimate-only sound events for all ten roles in `config/characters.json` with animation/FXR evidence.
- [ ] Confirm which soundbanks contain each event and which installed mod supplies the effective source. Never substitute guessed event IDs.

## Task 2: Binary soundbank and audio code

Files: `nuv/bank.py`, `nuv/audio.py`, `tests/test_bank.py`, `tests/test_audio.py`.

- [ ] Write failing tests for retaining unknown chunks, truncated bank rejection, original-action preservation, duplicate IDs, and PCM format/duration limits. Run `uv run python -m unittest discover -s tests -v` and observe missing-feature failures.
- [ ] Implement strict chunk/HIRC/DIDX parsing, append-only sound/action/event edits and PCM media generation. Use `struct.unpack_from('<I', data, offset)` only after checking boundaries; reject unsupported BKHD versions explicitly.
- [ ] Re-run the same tests and inspect the resulting bank using an independent Wwise parser.

## Task 3: Archive and profile integration

Files: `nuv/archive.py`, `nuv/profile.py`, `nuv/build.py`, `tests/test_archive.py`, `tests/test_profile.py`, `tests/test_build.py`.

- [ ] Write failing tests for path containment, hashed resource lookup, AES ranges, inherited profile-relative paths, preserved native order, invalid input and transactional builds.
- [ ] Implement selective extraction, active override resolution and a builder that verifies source/event identity before modifying copies. Generate a new ME3 profile using absolute resolved existing paths and an additional package loaded after existing packages.
- [ ] Run `uv run python -m unittest discover -s tests -v`. Verify the original profile and game archive hashes remain unchanged.

## Task 4: Usable audio workflow

Files: `nuv/__main__.py`, `config/voices.json`, `scripts/Generate-TestVoices.ps1`, `Build.cmd`, `README.md`, `pyproject.toml`.

- [ ] Write a CLI integration test before wiring commands for inspection, build and validation.
- [ ] Provide per-character WAV input, gain control and disabling, with Chinese Windows SAPI samples generated before game startup. Use `uv run python -m nuv --help` to check discoverability.
- [ ] Build against the actual local game and the user's existing seamless/MMV profile into `dist/UltimateVoices/` and provide an independent launch profile.

## Task 5: Verify and document limits

Files: `docs/verification.md`, `docs/event-map.md`.

- [ ] Run unit and CLI integration tests, independent bank roundtrip validation, all ten real-event checks, and verify generated audio duration and size budget.
- [ ] If game interaction is available, test actual cast playback; record remote mixed-install and distance tests only if actually exercised with a second client.
- [ ] Document exact commands, generated output path, rollback steps, runtime resource footprint and any unresolved game-level verification. Do not claim unperformed co-op or performance tests passed.
