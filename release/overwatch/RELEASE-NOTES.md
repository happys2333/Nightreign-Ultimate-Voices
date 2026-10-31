# Nightreign × Overwatch Ultimate Voices 0.1.0 Beta

[Nexus Mods / N 网下载](https://www.nexusmods.com/eldenringnightreign/mods/960) · [中文 README](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/README.md) · [English README](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/README.en.md)

Nexus status / N 网状态 (2026-11-01): Native and Build Toolkit are automatically quarantined pending moderator review; MMV and Audio Sources are downloadable. The same original artifacts and checksums are published here. / Native 与构建工具被自动隔离，待平台人工复核；MMV 与默认 WAV 可下载。[详细状态 / Details](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/release/overwatch/PUBLICATION.md)。

十角色守望中文大招播报，保留蓄力、爆炸和命中音效。守护者、铁眼起手播报，学者收招播报。采用游戏原生事件和本地声库；谁安装谁使用本机的声音，无需强制队友安装。

## 中文

适用 Windows Steam 黑夜君临**文件版本 1.3.3.0**，需另装 [Mod Engine 3](https://github.com/garyttierney/me3/releases)。成品玩家无需守望安装、Git、Python 或 SDK。

| 下载 | 用途 |
| --- | --- |
| `Nightreign-Overwatch-Voices-0.1.0-Native.zip` | 原生动画环境；内附离线/无缝启动配置。 |
| `Nightreign-Overwatch-Voices-0.1.0-MMV-Addon.zip` | 指定 MMVWeaponsMerge 基底；追加到自己已可用的配置。 |
| `Nightreign-Ultimate-Voices-0.1.0-Build-Toolkit.zip` | 可选自定义语音构建工具，另需 Git、uv、.NET 9 SDK。 |
| `Nightreign-Overwatch-Voices-0.1.0-Audio-Sources.zip` | 可选十角色默认 WAV，方便只替换一个角色并保留其余默认。 |

**Native 与 MMV 二选一。** MMV 附加包要求未应用本语音补丁的 `chr/c0000.anibnd.dcx` SHA-256 为 `0eafca3631ddbbf3b2ec67edb49068bdc4ebcf5e4d48b2b1720a0a1c2921be69`。包含此基底上修改的动画，仍需原 MMV 其余资源，不兼容任意 MMV 版本。无缝 DLL 需自备；请阅读压缩包内说明并用离线/无缝配置启动。

[安装与角色映射](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/README.md) · [替换音频、调整音量、恢复默认（中英）](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/docs/CUSTOM-AUDIO.md)

音频格式：PCM16 WAV，单/双声道，≤48 kHz，≤8 秒。替换对应角色 WAV 后重新构建，不支持游戏中热切换。每份 ZIP 附 `.sha256`，包内另有文件摘要。GitHub 自动生成的 Source code ZIP 是源码快照；直接游玩请选上表成品文件。

## English

Chinese Overwatch ultimate callouts for all ten Nightfarers, retaining charge, explosion and hit effects. Guardian/Ironeye speak at accepted animation start; Scholar at recovery. Native local resources play the audio; teammates do not have to install the mod and no voice files are transmitted.

Requires Windows Steam Nightreign **file version 1.3.3.0** and [ME3](https://github.com/garyttierney/me3/releases). Prebuilt users do not need Overwatch, extraction tools, Git, Python or an SDK.

- **Native.zip:** stock player animation base; offline and seamless profiles included. Supply your own Seamless Co-op folder/DLL if needed.
- **MMV-Addon.zip:** append to your existing supported MMV profile; exact unpatched animation input SHA-256 shown above. Contains a patched animation derived from that base and requires the rest of MMV separately. Not every MMV version is supported.
- **Build-Toolkit.zip:** optional source/build tooling for customization; requires Git, uv and the .NET 9 SDK.
- **Audio-Sources.zip:** optional ten default editable WAVs. Copy `voices/` into the toolkit root, then replace only the desired file and rebuild.

Choose **Native OR MMV**, not both. Use offline or your existing seamless profile. Read the packaged instructions before installing. GitHub's automatically generated Source code archives are source snapshots, not the prebuilt mod.

[English installation](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/README.en.md) · [Custom audio guide](https://github.com/happys2333/Nightreign-Ultimate-Voices/blob/main/docs/CUSTOM-AUDIO.md)

## Validation and credits / 验证与致谢

Functional baseline passed 103 automated tests. Final packages passed ZIP/file hash checks, 11 voice-route/media checks, sound catalog registration, independent animation restoration audits and relocated ME3 profile parsing. MMV resources match the locally tested pack; the tester reported no issues observed. Native passed offline checks but has not had a separate full gameplay matrix. Full character branches, mixed-install co-op/distance and frame-time benchmarks remain incomplete. No new project DLL, resident process, polling, runtime transcoding or network protocol.

功能基线通过 103 项自动化测试；最终包完成资源摘要、11 路声音、目录登记、独立动画恢复审计和移动目录配置解析。MMV 资源与本机已测包一致；Native 尚未独立完成实机矩阵。角色全分支、混装联机距离和帧时间基准仍待验证。

Overwatch recordings: Blizzard Entertainment and the respective rights holders/performers. Nightreign assets: FromSoftware / Bandai Namco. MMV animation base: MMVWeaponsMerge contributors. Original source code is GPL-3.0; code licensing does not change third-party media ownership. Substantial AI-generated code and AI-drafted instructions, with human-directed requirements, clip selection and testing. Full credits are included in each archive.
