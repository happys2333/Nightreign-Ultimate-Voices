# Nightreign × Overwatch Ultimate Voices — Native Resources 0.1.0 Beta

Prebuilt Chinese ultimate callouts for all ten Nightfarers. This packaging revision provides the same **24 game resources**, byte for byte, with two ME3 profiles and instructions. Dedicated original shout isolation and the Guardian/Ironeye/Scholar timing are unchanged.

## Install and launch

Requires Windows Steam Nightreign **file version 1.3.3.0** and separately installed [Mod Engine 3](https://github.com/garyttierney/me3/releases). Ordinary players need no Overwatch installation, Python, uv, Git or SDK.

1. Extract the whole `UltimateVoices-Overwatch` folder outside the game installation. Keep `.me3` and `mod/` together.
2. Start Steam and open **`UltimateVoices.me3`** using ME3. Double-click works when ME3 file associations are installed. Alternatively, open a terminal in the extracted folder:

```powershell
me3 launch -g nightreign -p ".\UltimateVoices.me3"
```

No CMD/BAT/PowerShell launcher scripts are included. The solo profile disables official online play, loads no co-op DLL and specifies no alternate save filename.

## Seamless Co-op or an existing profile

Supply your complete `SeamlessCoop` folder beside the profiles, verify `SeamlessCoop/nrsc.dll` exists, then open **`UltimateVoices-Seamless.me3`** using ME3, or run:

```powershell
me3 launch -g nightreign -p ".\UltimateVoices-Seamless.me3"
```

No co-op DLL is bundled. The preset uses default `NR0000.co2`. If you use a custom save extension, other mods or different launch settings, append this block to a **copy of your original working profile** and adjust its relative path:

```toml
[[packages]]
id = "nightreign-ultimate-voices"
path = "./UltimateVoices-Overwatch/mod"
```

Use offline or your working seamless setup. **Native and MMV-Addon are mutually exclusive.** Choose MMV-Addon for the specifically supported existing MMV base. Conflicting animation/bank/catalog replacements need merging; removing required files or changing load order cannot resolve them.

## Voices and validation

Wylder → Anran; Guardian → Doomfist; Ironeye → Hanzo; Duchess → Zenyatta (friendly); Raider → Reinhardt; Revenant → Ana (friendly recipient); Recluse → Doctrine; Executor → Winston (shared primal activation roar); Scholar → Sombra; Undertaker → Shion. Other selected clips use enemy ultimate lines.

Guardian/Ironeye speak at accepted action start; Scholar at recovery around 3.3 seconds. Charge, explosion and hit effects remain. Each installed client uses its own local resources; teammates need not install it and receive no audio files. The full mixed-install/distance matrix is unverified.

No additional project DLL, resident process, polling, runtime transcoder or network protocol. No frame-time benchmark is claimed. Positive local gameplay feedback applies to MMV; Native passed offline build and independent animation restoration checks, without a separate full gameplay matrix. Removing launcher scripts does not change these limits.

## Customize and remove

Read **CUSTOM-AUDIO.md** for per-role WAV names, formats, volume, rebuilding and restoration. Optional Build Toolkit and default Audio Sources remain on the [GitHub release](https://github.com/happys2333/Nightreign-Ultimate-Voices/releases/tag/v0.1.0). Do not place raw WAVs directly in mod/sd/.

Use the original profile or remove this package entry to disable it. Credits are in CREDITS.txt. Original source code is GPL-3.0; third-party game media retains its respective ownership.
