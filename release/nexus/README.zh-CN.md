# Nightreign Ultimate Voices 0.1.0 — 本地构建测试版

为黑夜君临十名角色配置自己的大招播报语音。语音通过游戏原生声音事件播放；构建工具在进入游戏前退出。此下载是源码和本地构建工具包，需要以下开发工具，不是解压即用的预制声音包，也不是 Vortex 即装文件。

公开包不附守望先锋语音、黑夜君临原资源、MMV 资源、合并后的声库/动画或其他模组。准备自己的合法音频，在自己的电脑生成文件。

## 安装要求

- Windows x64、Steam 版黑夜君临，当前仅支持文件版本 **1.3.3.0**。
- [Mod Engine 3](https://github.com/garyttierney/me3/releases)，本机验证版本 0.11.0。
- [Git for Windows](https://git-scm.com/downloads/win)、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [.NET 9 SDK x64](https://dotnet.microsoft.com/en-us/download/dotnet/9.0)；仅安装 .NET Runtime 不够编译辅助工具。
- 首次准备工具需要联网下载开源源码和依赖；游戏资源从本机读取。游戏运行时本项目没有新增进程、DLL、轮询或网络协议。
- 无缝联机是可选依赖；有联机需求时使用自己已经可用的 Seamless Co-op / ME3 配置。不要用普通官方匹配启动本模组。

## 第一次构建

将整个工具包解压到自己选定的目录，避免放入游戏安装目录。在该目录打开终端，运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
```

在 `voices/` 放入自己的 PCM16 WAV，或使用下面的可选中文测试生成器。Windows 需要安装中文语音：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Generate-TestVoices.ps1
```

没有中文语音组件时可以直接提供自己的 WAV，无需使用测试生成器。十名角色的默认文件名如下；不使用的角色在 `config/voices.json` 中设 `enabled: false`。

| 文件名 | 角色 | 文件名 | 角色 |
| --- | --- | --- | --- |
| wylder.wav | 追踪者 | revenant.wav | 复仇者 |
| guardian.wav | 守护者 | recluse.wav | 隐士 |
| ironeye.wav | 铁眼 | executor.wav | 执行者 |
| duchess.wav | 女爵 | scholar.wav | 学者 |
| raider.wav | 无赖 | undertaker.wav | 送葬者 |

使用原本的无缝联机配置构建（替换示例路径为自己的原始配置）：

```powershell
uv run python -m nuv build --base-profile "C:\MyMods\original.me3"
uv run python -m nuv verify "dist\UltimateVoices"
```

也可以把原始 `.me3` 配置拖到 `Build.cmd`。如只需离线单人，省略 `--base-profile`：

```powershell
uv run python -m nuv build
```

完成后双击 **`dist/UltimateVoices/Launch.cmd`**。原配置不会被修改。生成目录会引用本机绝对路径，移动安装位置或换电脑后需重新构建。输出应保留在工具包目录下，不能放在游戏安装目录。

游戏未自动找到时，在 build 命令中添加 `--game-dir "C:\YourSteamLibrary\steamapps\common\ELDEN RING NIGHTREIGN\Game"`。选择原始配置，不选择已经生成的 Ultimate Voices 配置；当前不支持包含 `include/includes/profile` 继承的配置。

## 音频与触发

支持单/双声道 PCM16 WAV、采样率不超过 48 kHz、单段不超过 8 秒。默认在构建时校准音量。`gain_db` 范围 -60 到 12；可用 `normalize: false` 保留源音量。每次换音频需重新构建，不支持游戏内热切换。

守护者与铁眼在游戏接受输入、开始大招动作时播报；学者在约 3.3 秒收招时播报。其他角色随各自原生大招事件触发。只移除已定位的专用原喊声调用，蓄力、爆炸和命中音效保留。尚未承诺每种共享战斗喊声均可单独移除。

“谁安装谁听见”指每台电脑使用自己的本地资源；队友无需为此安装本工具，也不向未安装者发送音频。能听到的队友播报依赖该客户端收到游戏事件，远距离未加载角色的声音仍待验证。

## 兼容性与故障反馈

动画输入只接受已审核的原生 1.3.3.0 或本地验证的 MMVWeaponsMerge 文件摘要，不能把“MMV 兼容”理解成支持所有版本。遇到不受支持的版本或另一模组修改同一声库/动画/声音目录，会明确拒绝构建。不要靠覆盖顺序强行合并。

2026-10-28，本机测试者反馈当前 BySlot 修正版暂未发现问题；103 项自动化测试通过。尚无十角色全部分支、完整混装联机和远距离矩阵，也没有帧时间基准。

报告问题时附：游戏版本、ME3 版本、角色、单人/无缝联机、是否加载其他声音或动作模组、重现步骤、生成目录的 build-report.json、对应 ME3 日志。分享日志前删去自己的用户名、绝对路径等个人信息，不上传存档或整包游戏资源。

## 卸载与许可

改用原启动配置即可停用。要清理本工具拥有的输出，运行 `uv run python -m nuv uninstall "dist\UltimateVoices"`；自定义输入 WAV 保留。

项目代码按 `LICENSE` 中 GPL-3.0 发布。第三方工具见 `THIRD_PARTY_NOTICES.md`。这些许可不授予第三方游戏音频或其他模组资源的再分发权。代码开发大量使用生成式 AI，需求、声音选段与本机测试由用户指导；发布页文案也由 AI 起草。
