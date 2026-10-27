# Third-party references and local development tools

The project is GPL-3.0, as provided by LICENSE. Windows SAPI generated the included Chinese test clips using Microsoft Huihui Desktop on this machine.

- BHD5 archive format and selective extraction reference: [SoulsFormatsNEXT](https://github.com/soulsmods/SoulsFormatsNEXT) and [UXM Selective Unpack](https://github.com/Nordgaren/UXM-Selective-Unpack), Joseph Anderson, Nordgaren and contributors. The current SoulsFormatsNEXT checkout is GPL-3.0. Archive RSA public data was obtained from UXM `ArchiveKeys.cs`; these are public game-archive keys, not user credentials.
- Wwise bank structure reference and independent verification: [wwiser](https://github.com/bnnm/wwiser), bnnm and contributors, and [Yonder](https://github.com/ndahn/yonder), Nikolas Dahn. These developer tools are not linked into the runtime mod.
- Wwise PCM format reference and independent decoding: [vgmstream](https://github.com/vgmstream/vgmstream), contributors. Tools were used only for local verification.
- Independent bank decoding used the **MIT-licensed bnk2json build included in Yonder v2.0.4**. Its adjacent LICENSE-MIT states Copyright (c) 2024 Vincent Swarte. It is not bundled in the source or generated runtime mod; the current upstream rewwise licensing is not assumed to match this older binary.
- Native/MMV animation inspection used the local SoulsFormatsNEXT build, [DSAnimStudio's Nightreign TAE template](https://github.com/Meowmaritus/DSAnimStudio/blob/master/DSAnimStudioNETCore/Res/TAE.Template.ERNR.xml) and [HKLib 0.1.3-NR](https://github.com/The12thAvenger/HKLib/releases/tag/v0.1.3-NR). These development tools are not needed to build or play the mod.
- [cryptography](https://github.com/pyca/cryptography) supplies archive AES/RSA parsing during offline construction. [tomli-w](https://github.com/hukkin/tomli-w) writes generated ME3 TOML. See their distributed package licenses in the Python environment.
- [Mod Engine 3](https://github.com/garyttierney/me3) remains the user's separate mod loader. Existing Seamless Co-op and other mods remain separately installed and are not redistributed here.

Local extracted game resources, third-party binaries, inspector projects and independent verification dumps are excluded from Git. Generated hero banks are derived from the user's local installation.

The local OW importer uses [OWLib](https://github.com/overtools/OWLib) and [TACTLib](https://github.com/overtools/TACTLib), with exact source revisions and the unmerged build-support patch recorded in `docs/overwatch.md`. `scripts/Prepare-OverwatchTools.ps1` builds these locally with one explicit offline-keyring change and this project's pinned-audio extension. The vgmstream r2168 decoder is prepared separately and runs only before game startup. No Overwatch speech, SFX, game archives or extracted voice sets are committed or redistributed with this source repository; each user extracts from their own local installation.
