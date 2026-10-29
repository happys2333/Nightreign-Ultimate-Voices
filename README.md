# Nightreign Ultimate Voices

在《艾尔登法环 黑夜君临》中释放绝招时，播放该角色的自定义语音。支持十名角色，附中文测试播报。

本次更新只移除已定位的大招原喊声，保留蓄力、爆炸和命中音效。守护者、铁眼改为大招动作开始播报，学者改为收招时播报。具体事件、隔离范围和验证边界见 [喊声与时机说明](docs/voice-isolation.md)。

针对改时机后三名角色无声的反馈，已补齐新增声音的游戏索引，并把四条动画触发改为原生大招使用的完整 BySlot 一次性播放格式。2026-10-28 用户反馈当前修正版“目前测没啥问题”；详见 [触发兼容调查](docs/retimed-callout-trigger.md)。此反馈不扩展为全部联机与距离边界验收。

已加入用户指定的十角色本地 OW 导入组件，见 [OW 导入说明](docs/overwatch.md)。守护者使用末日铁拳敌方“毁天灭地！”，女爵使用禅雅塔友方“感受宁静”。针对无赖听不到播报的问题，已补充事件预备加载需要的本地媒体副本，并校准过轻的播报音量。独立引擎验证与实机反馈分开记录，详见 [验证记录](docs/verification.md)。旧的替换原声诊断包不能作为正式包使用。

Nexus 发布资料、可复制的中英文介绍和发布流程见 [发布准备](release/nexus/UPLOAD.zh-CN.md)。公开工具包不包含提取的游戏资源或预制声音包，需在目标电脑构建；本机 `dist/` 不应直接作为公共下载包。

2026-10-29 按用户要求另行整理了内置守望语音的 **Native 成品主包** 和 **MMV 成品附加包**，均无需下载者编译，见 [成品整理说明](release/overwatch/PREPARED.zh-CN.md)。本机正在使用的测试包保持不变；本轮只整理文件，尚未公开发布。

本模组生成本地 Wwise 角色声库及少量动画声音事件，通过游戏原生机制播放。**谁安装谁听见**：安装者使用自己的语音包听取本机收到的自身及队友绝招事件；没安装的队友继续听原有声音。无需语音传输或额外联机协议，也无需要求队友安装。

当前是 **1.3.3.0 本地测试版**。已验证原生/MMV 事件映射、声库格式及原音效保留；混装无缝联机、远距离事件可达性和全部角色游戏内边界仍需实测。详细状态见 [验证记录](docs/verification.md)，不能把静态声库验证理解为已完成双客户端联机验收。

## 本机直接使用

已经为本机的“地图扩容＋无缝联机”配置生成了独立启动包：

```text
dist/UltimateVoices/Launch.cmd
```

双击它启动。新的 `UltimateVoices.me3` 保留原来的无缝联机 DLL、地图/武器扩展和汉化，只在最后增加语音声库目录。原启动配置仍可照常使用。

生成包引用本机现有模组的绝对路径。**更换电脑或移动原模组后应在目标电脑重新构建**，不要直接复制这份本机配置。

## 自定义每个角色的语音

替换 `voices/` 中的同名 WAV，再重新构建。也可以在 `config/voices.json` 中给每个角色指定不同文件路径、`gain_db`、`normalize` 和 `enabled`。

| 配置键 / WAV 文件名 | 角色 |
| --- | --- |
| `wylder` | 追踪者 |
| `guardian` | 守护者 |
| `ironeye` | 铁眼 |
| `duchess` | 女爵 |
| `raider` | 无赖 |
| `revenant` | 复仇者 |
| `recluse` | 隐士 |
| `executor` | 执行者 |
| `scholar` | 学者 |
| `undertaker` | 送葬者 |

例如：

```json
{
  "gain_db": 0,
  "normalize": true,
  "characters": {
    "wylder": { "audio": "../voices/wylder.wav", "enabled": true, "gain_db": -3 },
    "guardian": { "enabled": false }
  }
}
```

相对路径以 **voices.json 所在文件夹** 为基准。未列出的角色关闭；`enabled: false` 保留原音效且无需提供文件。

- 音频要求：PCM 16-bit WAV，单/双声道，采样率不超过 48 kHz，时长大于 0 且不超过 8 秒。
- 不直接接收 MP3/OGG/浮点 WAV；用音频编辑器预先导出上述格式。
- 默认先在构建时校准音量，再应用 `gain_db`（默认 `0 dB`，范围 `-60` 至 `12 dB`）。校准以整段 RMS `-18 dBFS` 为目标，峰值不超过 `-1 dBFS`、提升最多 `24 dB`；峰值较突出的音频可能因限制而达不到目标。静音不变，左右声道使用同一增益。正的自定义增益仍可能使样本饱和。
- 设置全局或单角色 `normalize: false` 可保留源音量；单角色设置优先。原技能音效保留，已定位的大招原喊声由新播报替代。
- 全部播报新增媒体总量上限为 16 MiB；音频只在构建时转换，战斗中无需启动转码器。
- 中文测试语音由本机 Windows Microsoft Huihui 合成，不是角色正式配音。可运行 `scripts/Generate-TestVoices.ps1` 重新生成缺失样本；已有文件不会被覆盖。

## 从源码构建

需要 Windows、Steam 版游戏、Mod Engine 3、.NET 9 SDK（准备构建工具）和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。构建所需 Python 及依赖由 uv 管理，不需要安装 Wwise。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-AnimationTools.ps1
uv run python -m nuv inspect
uv run python -m nuv build --base-profile "D:\SteamLibrary\steamapps\common\ELDEN RING NIGHTREIGN\Game\启动地图扩容+无缝联机.me3"
uv run python -m nuv verify
```

也可以把原 `.me3` 文件拖到 `Build.cmd` 上。生成后双击 `dist/UltimateVoices/Launch.cmd`。

可选参数：

```powershell
uv run python -m nuv build --game-dir "D:\SteamLibrary\steamapps\common\ELDEN RING NIGHTREIGN\Game" --base-profile "D:\your-mods\coop.me3" --voices "D:\my-voices\voices.json" --output "D:\my-mods\UltimateVoices"
```

省略 `--base-profile` 会生成**离线单机**配置，不加载无缝联机。使用无缝联机时应指定你原来实际使用的配置。首版支持独立的本地 ME3 配置，遇到继承配置会明确拒绝；现有角色声库被其他音频模组修改时也会停止构建，不静默覆盖冲突。

构建器只选择性读取所需音频和动画资源，并核对游戏版本、原始角色声库和事件摘要。输出重新解析后检查所有原始音频媒体、非目标对象、事件原动作和未知数据块，成功后再交换输出目录。重复构建仅替换本工具拥有的完整输出；若该目录包含自己的文件或手动修改，会拒绝覆盖。

## 卸载

使用原来的 `.me3` 配置启动即可停用。要删除生成包：

```powershell
uv run python -m nuv uninstall
```

卸载仅处理拥有清单中的生成文件，不修改游戏归档、原模组、原配置或存档。输入音频 `voices/` 会保留。

## 性能和触发时机

游戏运行时增加的是原生 Wwise 一次性音频节点；四条新增动画事件也由游戏原生系统执行。本项目没有常驻进程、注入 DLL、内存轮询、截图识别或额外网络消息。PCM 转换、音量校准都在游戏启动前完成。本次中文样本增加 **2,689,832 bytes（约 2.57 MiB）** 媒体数据，含追踪者两个互斥释放分支。

每段媒体同时内嵌在声库，并以相同编号、相同字节放在本地 `mod/sd/wem/<前两位>/<编号>.wem`。这样兼容直接加载声库和按事件预备加载，不依赖队友文件。额外磁盘副本约 2.57 MiB；它不意味着战斗时额外转码或传输音频。没有帧时间实测数据时不声称零帧率影响。

守护者和铁眼在游戏接受输入并开始大招动作时播报，学者在收招时（约 3.3 秒）播报。追踪者仍按释放分支触发，其他角色按各自大招事件触发；取消边界仍待实际游戏验收。新语音使用 2D 播放以保持清晰，但前提仍是游戏在本机投递了该角色事件。远距离未加载的队友是否投递事件须由联机测试确认，原生声库不能凭空获得尚未同步到客户端的信息。

当前 11 个播报挂载点、原始动画/行为绑定和空中/蓄力分支证据见 [事件映射](docs/event-map.md)。

## 开发验证

```powershell
uv run python -m unittest discover -s tests -v
```

源代码使用 GPL-3.0。第三方格式资料和开发工具见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。仓库不包含提取的游戏声库；`local/`、`.tools/`、`dist/` 为本机构建缓存和输出，不进入版本控制。
