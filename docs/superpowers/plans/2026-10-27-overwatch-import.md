# Local Overwatch Voice Import Implementation Plan

> **For agentic workers:** Use subagent-driven-development for independent tool compatibility investigation and requesting-code-review for integration. Execute dependent import/build steps sequentially.

**Goal:** Extract the user's eight specified ultimate callouts from local Overwatch and provide repeatable offline import into the existing Nightreign builder.

**Architecture:** DataTool reads local CASC without online payload fallback; an auditable manifest pins exactly selected local hero/side audio GUIDs and SHA-256. A Python importer validates the manifest and calls a decoder with structured arguments, then publishes a dedicated OW voice preset for the original native bank builder.

**Tech Stack:** OWLib/DataTool, .NET10, Python unittest, vgmstream, existing nuv PCM/Wwise builder.

---

## Execution status

All extraction/import implementation steps are complete. Original WEM is used for byte-stable source pinning (rather than re-encapsulated OGG). The own DataTool extension reads only the eight audited `.0B2`/`.03F` GUIDs; two fresh extraction directories match all eight SHA-256 values. Eight WAVs and eight Nightreign banks are generated;45 tests, package integrity, and independent import review pass. Tool source provenance checks were strengthened after review.

The earlier Raider no-playback report is a separate unresolved game-level blocker. Native layer/PCM diagnostic has been generated and a manual result requested. New Wwise internal IDs now use the documented30-bit domain, but no game-root-cause or playback-success claim is made from that correction. Do not mark total gameplay/co-op acceptance complete until actual testing passes.

- [ ] Establish working154504 DataTool and record exact source/provenance; run `list-heroes --json` and verify all eight hero IDs.
- [ ] Extract those hero voice sets with zhCN speech/text, skin/type grouping and subtitle sidecars. Inspect `Ultimate` audio/criteria and choose each requested enemy/friendly variant; record exact resource GUIDs and hashes.
- [ ] Write failing `tests/test_overwatch.py` for manifest hero/side identity, containment, source integrity, tool failure and atomic imported output; run `uv run python -m unittest discover -s tests -p test_overwatch.py -v`.
- [ ] Implement `nuv/overwatch.py`, static `config/overwatch.json`, and `ow-extract` / `ow-import` CLI commands. Decode selected audio to PCM16 and validate with the existing `pcm_wem` function before publishing a generated config.
- [ ] Run the importer against real local extraction, build eight selected Nightreign banks using the user's seamless/MMV profile into `dist/UltimateVoices-Overwatch`, verify preservation and resource budget, and run all tests.
- [ ] Review source changes, document reproduction commands and remaining gameplay/co-op acceptance limits, and commit code/manifest without game audio.
