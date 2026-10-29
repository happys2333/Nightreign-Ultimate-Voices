# Nightreign × Overwatch Ultimate Voices — 0.1.0 Beta

Prebuilt Chinese Overwatch ultimate callouts for all ten Nightfarers. Requires Nightreign **1.3.3.0** and **Mod Engine 3**. No Overwatch installation, extraction, Python, Git, uv or SDK is required to use this download.

## Installation

This is the **Native animation** variant. Do not combine it with MMV or another player animation-bundle replacement. MMVWeaponsMerge users should choose the separate **MMV-Addon** variant; the two are mutually exclusive.

Install [ME3](https://github.com/garyttierney/me3/releases), start Steam, and extract the entire `UltimateVoices-Overwatch` folder outside the game installation. Use `Launch.cmd` or `UltimateVoices.me3` for offline solo. Keep the profile, launchers and mod directory together; paths are relative and the folder can be moved. The solo profile specifies no alternate save filename.

For Seamless Co-op, copy your own complete `SeamlessCoop` folder alongside the profiles so that `SeamlessCoop/nrsc.dll` exists, then use `Launch-Seamless.cmd`. No co-op DLL is bundled. This preset selects `NR0000.co2`, corresponding to default co2 settings. If you have a different save extension, additional mods, or custom launch settings, append this package to a copy of your own working offline/seamless profile instead:

```toml
[[packages]]
id = "nightreign-ultimate-voices"
path = "./UltimateVoices-Overwatch/mod"
```

Adjust the relative path from your profile's location. Do not use regular official matchmaking. Animation/sound replacements require a proper merge, not just a different loading order.

## Included mapping

Wylder → Anran (enemy); Guardian → Doomfist (enemy); Ironeye → Hanzo (enemy); Duchess → Zenyatta (friendly); Raider → Reinhardt (enemy); Recluse → Doctrine (enemy); Revenant → Ana (friendly recipient callout); Executor → Winston (shared primal activation main roar); Scholar → Sombra (enemy); Undertaker → Shion (enemy).

Guardian and Ironeye speak at accepted ultimate animation start. Scholar speaks at recovery, around 3.3 seconds. Audited dedicated original shouts are removed while charge, explosion and hit effects remain. Winston's clip is a shared roar, not enemy-exclusive spoken dialogue.

Each installed client uses its own resources. Teammates need not install the mod, and receive no transmitted voice files. Hearing remote/distant players depends on native events arriving at the client; the full distance/mixed-install matrix remains unverified.

## Status, conflicts and removal

The local positive gameplay feedback applies to the tested MMV variant. This native candidate uses identical audio/catalog files and trigger settings on the original animation base. Its offline build and animation-restoration checks passed; it has not been separately game-tested in this preparation.

Replaced resources include ten hero banks, added loose WEMs, two sound catalogs and c0000.anibnd.dcx. Do not remove the catalogs/animation to force compatibility: the retimed voices can become silent. There is no added project DLL, process, polling, runtime transcoding or network protocol; no frame-time benchmark or FPS improvement is claimed.

Use your original profile to disable the mod, or remove its package entry from your profile copy. Custom audio requires a separate source toolkit rebuild; there is no in-game import/hot-reload interface. See CREDITS.txt. This is a prepared candidate; no Nexus upload has been performed.
