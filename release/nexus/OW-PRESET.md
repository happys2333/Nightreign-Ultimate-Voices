# Optional local OW preset — advanced workflow

The public toolkit contains no Overwatch audio. The generic custom-WAV workflow does not require Overwatch. This optional importer uses local resources only; it is not a source of redistribution permission, and it is not a promise that every current Overwatch release works.

The audited manifest is pinned to **zhCN build 2.25.0.1.154504N** and original WEM hashes. Other builds or changed resources are rejected. Users must review applicable game terms and use audio they are entitled to use. Do not upload extracted clips or generated banks to Nexus without the required permission.

## Audited selection

| Nightfarer | Preset |
| --- | --- |
| Wylder | Anran, enemy ultimate |
| Guardian | Doomfist, enemy “毁天灭地！” |
| Ironeye | Hanzo, enemy ultimate |
| Duchess | Zenyatta, friendly “感受宁静。” |
| Raider | Reinhardt, enemy ultimate |
| Revenant | Ana, recipient-friendly “你被强化了！快上！” |
| Recluse | Doctrine, enemy ultimate |
| Executor | Winston, shared primal activation main roar |
| Scholar | Sombra, enemy ultimate |
| Undertaker | Shion, enemy ultimate |

Winston is a shared roar layer, not an enemy-exclusive spoken line. Doomfist is not advertised as a skin-exclusive recording. The manifest in config/overwatch.json pins the original GUIDs and bytes.

## Advanced setup

In addition to the standard toolkit requirements, install the **.NET 10 SDK** for DataTool. Keep the .NET 9 runtime/SDK required by the animation helper. In the toolkit folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-OverwatchTools.ps1
uv run python -m nuv ow-extract --overwatch-dir "C:\YourOverwatchInstallation"
uv run python -m nuv ow-import --build --base-profile "C:\MyMods\original.me3"
uv run python -m nuv verify "dist\UltimateVoices-Overwatch"
```

Replace both example paths. For offline solo, omit --base-profile. Launch dist/UltimateVoices-Overwatch/Launch.cmd only after a successful build. The importer writes owned local version directories and refuses changed input instead of guessing new clips.

Preparation fetches pinned open-source tools and the decoder; it does not download game media. Extraction uses --online=false and an offline-keyring change. Source revisions are pinned in scripts/Prepare-OverwatchTools.ps1: OWLib 546efa19516d7df7ba138802d221c73ad886df28 and TACTLib 9b333b84211a4b95928e01be303b5ed27729c0aa (an unmerged upstream PR at preparation time). These are advanced, version-specific requirements.
