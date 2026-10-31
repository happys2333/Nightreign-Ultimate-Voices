# 自定义大招播报 / Custom ultimate audio

成品版已内置默认守望语音。此教程用于替换某个角色的播报，不需要修改大招触发时机。**替换后需在进入游戏前重新构建**，不支持运行中热切换。

## 中文

### 1. 准备构建工具和默认音频

从 [v0.1.0 下载页](https://github.com/happys2333/Nightreign-Ultimate-Voices/releases/tag/v0.1.0)下载 **Build-Toolkit.zip** 和 **Audio-Sources.zip**。前者是构建代码，后者是十个默认守望 WAV。

解压工具包，将 Audio Sources 中的 `voices/` 文件夹复制到**工具包根目录**，与 `config/`、`nuv/`、`Build.cmd` 同级。默认 `config/voices.json` 已按下表引用这些文件。保留一份 Audio Sources ZIP，之后可以恢复原音频。

只替换一个角色时，把该同名 WAV 换成自己的文件，其他九个保留默认音频。不要把 WAV 直接放入已编译成品的 `mod/sd/`，游戏不会按这些角色文件名自动读取它们。

| WAV 文件 | 角色 | WAV 文件 | 角色 |
| --- | --- | --- | --- |
| wylder.wav | 追踪者 | revenant.wav | 复仇者 |
| guardian.wav | 守护者 | recluse.wav | 隐士 |
| ironeye.wav | 铁眼 | executor.wav | 执行者 |
| duchess.wav | 女爵 | scholar.wav | 学者 |
| raider.wav | 无赖 | undertaker.wav | 送葬者 |

### 2. 导出正确格式

使用音频编辑器把片段裁剪到 **8 秒以内**，导出为 **16-bit PCM WAV**，单/双声道、采样率不超过 **48 kHz**。MP3/OGG 改后缀不算转换，浮点 WAV 也不适用。建议剪掉多余开头静音，避免听起来延迟。

### 3. 安装一次性构建依赖

需要 Windows、[Git](https://git-scm.com/downloads/win)、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [.NET 9 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/9.0)。打开工具包目录的终端，执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
```

首次会下载、编译开源动画辅助工具。使用这里提供的默认 WAV 时，不需要守望安装或额外的 .NET 10 / DataTool 提取流程。

### 4. 设置音量和开关

编辑 `config/voices.json`。例如复仇者一项可设为：

```json
"revenant": {
  "audio": "../voices/revenant.wav",
  "enabled": true,
  "gain_db": -3,
  "normalize": true
}
```

保留原 JSON 中其他角色项、逗号和外层结构。`gain_db` 范围为 -60 至 12；负数变小声，正数变大声。默认 `normalize: true` 在构建时校准响度；设为 `false` 保留源音量。`enabled: false` 让该角色不应用语音/原喊声隔离/时机补丁。相对路径以配置文件所在目录为基准。

### 5. 重新构建并使用

退出游戏后，将自己的**原始**离线/无缝联机 `.me3` 配置拖到 `Build.cmd`，或者执行（将示例路径换成自己的）：

```powershell
uv run python -m nuv build --base-profile "C:\MyMods\original.me3"
uv run python -m nuv verify "dist\UltimateVoices"
```

离线单人可省略 `--base-profile`。MMV 用户必须传入包含自己 MMV 的原始配置，构建器才会读取、校验对应动作基底；不要传入已经加过本语音包的配置。游戏目录未自动发现时可添加 `--game-dir "C:\YourSteamLibrary\steamapps\common\ELDEN RING NIGHTREIGN\Game"`。

成功后使用**新生成的** `dist/UltimateVoices/Launch.cmd`。此输出取代此前的语音安装，不要同时加载下载成品和自己构建的版本。若版本或动画摘要不支持，按错误信息处理，不要强行覆盖。

### 6. 恢复默认 / 排查

- 恢复该角色：从 Audio Sources ZIP 取回同名 WAV，再构建一次；或直接停用自定义包，重新使用下载的成品包。
- 音量不合适：先调整 `gain_db`，重新构建。播放器里的原文件变化不会实时传到游戏。
- 没声音：确认 PCM16 WAV 格式、`enabled`、音频路径，以及启动的是新生成的 `.me3`；确认没有另一份语音包或动作/声音目录覆盖冲突。
- 缺少默认中文测试音频：只有使用 Windows 测试合成语音才需要运行 `scripts/Generate-TestVoices.ps1`；想保留 OW 默认时不要用它替代 Audio Sources。

## English

### 1. Keep default voices while replacing one character

Download **Build-Toolkit.zip** and **Audio-Sources.zip** from the [release](https://github.com/happys2333/Nightreign-Ultimate-Voices/releases/tag/v0.1.0). Copy Audio Sources' `voices/` into the toolkit root, alongside `config/`, `nuv/` and `Build.cmd`. Replace only the desired WAV; retain the other nine default Overwatch clips. Keep the original Audio Sources ZIP for restoration.

Names are `wylder.wav`, `guardian.wav`, `ironeye.wav`, `duchess.wav`, `raider.wav`, `revenant.wav`, `recluse.wav`, `executor.wav`, `scholar.wav` and `undertaker.wav`. The runtime game does not read these names directly from `mod/sd/`; rebuild the banks after editing.

### 2. Format and dependencies

Export **16-bit PCM WAV**, mono/stereo, at most **48 kHz** and **8 seconds**. Renaming an MP3 extension does not convert it. Float WAV is unsupported. Trim excess leading silence if you want an immediate-sounding callout.

Only customization needs Windows, Git, uv and the .NET 9 SDK. In the toolkit directory run the preparation command shown above. It downloads/builds the pinned animation helper. With the provided Audio Sources, no Overwatch installation, DataTool or .NET 10 extraction setup is required.

### 3. Configure, rebuild and restore

`config/voices.json` supports per-character `audio`, `enabled`, `gain_db` (-60 to 12) and `normalize`. Negative gain is quieter. `normalize: true` calibrates loudness before gameplay; false retains source levels. `enabled: false` skips that character's voice, vocal-isolation and timing changes. Relative paths start from the configuration directory. Preserve the surrounding valid JSON and the other characters.

Close the game, drag your **original** offline/seamless ME3 profile onto `Build.cmd`, or run the build/verify commands above using your own path. MMV users must pass the original MMV profile so the builder reads its animation base. Do not pass an already modified Ultimate Voices profile. Unsupported versions/hashes are rejected.

Launch the newly generated `dist/UltimateVoices/Launch.cmd`. Use that output instead of the previous voice pack, not alongside it. Changes are not hot-reloaded during gameplay.

To restore a character, recover its WAV from Audio Sources and rebuild; to restore the whole preset, disable your custom output and return to the downloaded prebuilt pack. For silence, check PCM16 format, file path, enabled state, selected launch profile, and conflicting sound/animation resources. Windows test-speech generation is optional and is not needed to preserve Overwatch defaults.
