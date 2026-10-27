# Build-time TAE patcher

Prepare the pinned SoulsFormatsNEXT checkout and publish the helper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
```

The script publishes `.tools/tae-patcher/Nuv.TaePatcher.dll` and writes
`.tools/animation-tools.json`. It clones the pinned library only when missing;
an existing checkout must have the expected remote, revision, and clean source.
It never resets a checkout. The helper requires a .NET 9 runtime. Preparation
uses the installed `dotnet` SDK.

```text
dotnet .tools/tae-patcher/Nuv.TaePatcher.dll --input INPUT --output OUTPUT --plan PLAN.json --game-dir GAME --report REPORT.json
```

All five arguments are required. OUTPUT and REPORT must have existing parent
directories and must not exist. Use normal local-drive paths: symlinks,
junctions, UNC/device paths, alternate data streams, short-name aliases, and
paths with trailing dots/spaces are rejected. Neither output may be inside GAME.
GAME is read only; its existing Oodle DLL is used only for build-time DCX work.

The plan has exactly these fields:

```json
{
  "schema_version": 1,
  "source_sha256": "64 hexadecimal characters identifying the complete input",
  "operations": [
    {
      "tae_id": 2901,
      "animation_id": 610000,
      "sound_id": 900207000,
      "start_seconds": 0,
      "end_seconds": 0.03333333333333333
    }
  ]
}
```

Each operation appends one type-129 `Wwise_PlaySound_BySlot` event with SoundType 1 and an independent
type-128 group. IDs must be positive int32 values; times must be finite and
within 0–120 seconds, with positive duration at TAE float precision. The helper
accepts 1–64 operations, at most 1 MiB of JSON, and at most 256 MiB of input.
Duplicate operations, missing/duplicate targets, and requested SoundIDs already
present on sound rows 128–134 anywhere in the binder are rejected. Unknown or
duplicate JSON fields are rejected. The caller owns its approved source-hash
whitelist and canonical animation/sound mapping.

No output is staged until the complete patch and audits succeed in memory.
The source binder and target TAEs must first roundtrip byte-identically. The
patched binder is read back and checked for unchanged binder headers, member
metadata, and unrelated member bytes. Every original TAE header, animation,
event, flag, group, and group membership is compared. Removing the additions
must reproduce each original TAE byte-identically.

SoulsFormats exposes alignment padding as part of an event's parameter byte
array. An added 24-byte event header can add eight trailing zero bytes to the
first original event's parameter storage. The audit permits only an eight-byte
zero alignment difference at that position; it restores the original storage
length before structural and byte-restoration checks. These cases appear in
`alignment_padding_adjustments`. The inserted sound payload is exactly 32 bytes,
matching the native ultimate one-shot rows: SoundType 1, the registered SoundID,
DummyPolyID and SlotID -1, PlaybackBehaviorType 0 (finish playback after the
event window), and SoundIDOffsetType -1 (no weapon/hero sound ID adjustment).
The remaining bytes match native one-shot settings. GroupType remains 128,
as in the game's type-129 rows. Report times reflect the actual float32 values
written to TAE. See [trigger compatibility investigation](../../docs/retimed-callout-trigger.md)
for the evidence and outstanding game-side acceptance.

Success returns 0 and prints `TAE_PATCH_OK ...`. Refusal returns 2 and prints one
bounded diagnostic, `TAE_PATCH_ERROR CODE: explanation`, with no stack trace.
The success report contains schema/source/output hashes and sizes, member and
insertion counts, audit booleans, written operations, changed-member hashes,
and alignment adjustments. Output and report are staged beside their final
paths and moved without replacement; errors do not overwrite existing files.

The metadata lists SHA-256 hashes of the helper/library DLLs and the two helper
source files. `helper_source_sha256` hashes a UTF-8 manifest of sorted
`repo-relative-path:lowercase-sha256\n` lines. Only build tooling uses these DLLs;
the generated mod package does not need the helper, SoulsFormats, or a runtime
hook.

Run the tests after preparation:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p test_tae_helper.py -v
```

Set `NUV_TAE_REAL_SOURCE` to the approved MMV binder and `NUV_TAE_GAME_DIR` to
the game directory to include the read-only real-source test. All test outputs
stay under `local/timing-update/helper-tests`; the independent audit removes
the inserted rows/groups and verifies restoration of the original bytes.
