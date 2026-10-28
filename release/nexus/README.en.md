# Nightreign Ultimate Voices 0.1.0 — Local Build Toolkit (Beta)

Assign your own ultimate callouts to all ten Nightfarers. Native animation and Wwise events play the audio. The builder exits before gameplay. This download contains source and build scripts; it requires development tools and is not a prebuilt sound pack or a Vortex one-click installation.

No extracted Overwatch audio, original Nightreign assets, MMV assets, merged banks/animations, or other mods are included. Supply audio you are entitled to use and build on your own computer.

## Requirements

- Windows x64 and Steam Nightreign **file version 1.3.3.0**.
- [Mod Engine 3](https://github.com/garyttierney/me3/releases); tested locally with 0.11.0.
- [Git](https://git-scm.com/downloads/win), [uv](https://docs.astral.sh/uv/getting-started/installation/), and [.NET 9 SDK x64](https://dotnet.microsoft.com/en-us/download/dotnet/9.0). The SDK is required, not just the runtime.
- Internet access for initial source/dependency preparation. Game resources are read locally.
- Seamless Co-op is optional. For co-op, use your own working offline/seamless ME3 profile. Do not use regular official matchmaking with the mod.

## Build and launch

Extract the toolkit outside the game installation. Open a terminal in the extracted folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
```

Put PCM16 WAV files in `voices/`, named `wylder.wav`, `guardian.wav`, `ironeye.wav`, `duchess.wav`, `raider.wav`, `revenant.wav`, `recluse.wav`, `executor.wav`, `scholar.wav`, and `undertaker.wav`. Disable unused characters with `enabled: false` in `config/voices.json`. Relative audio paths are resolved from that configuration file.

Optional Chinese test clips can be generated locally with the script below. This requires an installed Chinese Windows speech voice. You can supply your own audio instead.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Generate-TestVoices.ps1
```

Build using your original working ME3 profile; replace the example path with your own:

```powershell
uv run python -m nuv build --base-profile "C:\MyMods\original.me3"
uv run python -m nuv verify "dist\UltimateVoices"
```

Alternatively, drag that original `.me3` file onto `Build.cmd`. For offline solo, omit `--base-profile`. Launch **`dist/UltimateVoices/Launch.cmd`** after building. If automatic game discovery fails, add `--game-dir` pointing to your Nightreign `Game` directory.

The builder preserves the original profile. Generated profiles use absolute local paths: rebuild after moving the toolkit, other mods, or changing computers. Output must remain outside the game installation. Choose your original profile, not a generated Ultimate Voices profile. Profile inheritance via `include`, `includes`, or `profile` is currently unsupported.

## Audio and behavior

Use mono/stereo 16-bit PCM WAV, up to 48 kHz and 8 seconds. Normalization occurs before gameplay. `gain_db` accepts -60 through 12; `normalize: false` preserves source levels. Rebuild after changing audio; no in-game hot reload is provided.

Guardian and Ironeye callouts start when the accepted ultimate animation starts. Scholar speaks at the recovery boundary, around 3.3 seconds. Other callouts follow their native ultimate events. Audited dedicated native shouts are removed while charge, explosion, and hit effects remain. Shared combat voices are not globally muted.

Each installation uses its own local audio. Teammates do not need to install the toolkit and receive no transmitted voice files. Hearing a teammate's callout depends on that client receiving the relevant native event; unloaded/distant players remain an unverified boundary.

## Compatibility and status

The builder accepts only approved hashes for native 1.3.3.0 or the locally tested MMVWeaponsMerge animation bundle. This is not blanket compatibility with every MMV version or animation mod. Modified banks, animation inputs, or sound catalogs outside the approved inputs are rejected. Do not force a merge by overwriting files.

On 28 October 2026, the local tester reported no issues observed with the current BySlot revision. The functional code passed 103 automated tests. A complete ten-character branch matrix, mixed-install co-op/distance matrix, and frame-time benchmark have not been completed. No additional project process, DLL, polling loop, transcoder, or network protocol runs during gameplay.

For bug reports include game/ME3 versions, character, solo/seamless setup, conflicting audio/animation mods, reproduction steps, `build-report.json`, and the corresponding ME3 log. Remove private usernames and paths before sharing. Do not upload saves or extracted game archives.

## Removal and license

Launch your original profile to disable the mod. `uv run python -m nuv uninstall "dist\UltimateVoices"` removes only the tool-owned generated output and preserves input WAV files.

Project code is GPL-3.0; see `LICENSE` and `THIRD_PARTY_NOTICES.md`. This does not grant redistribution rights to third-party game audio or other mods. Development used substantial AI-generated code under human-directed requirements, clip selection, and local testing. Publication text was also AI-drafted.
