# 本地守望先锋大招语音预设

按用户指定映射，从本机国服 OW `2.25.0.1.154504N`、zhCN 资源中提取。未从网页、视频或第三方语音合集下载音频。

## 角色选择

| 黑夜君临 | OW | 听者版本 | 选中原始音频 GUID |
| --- | --- | --- | --- |
| 追踪者 | 安燃（Anran） | 敌方，常规主动绝招 | `00000006AB26.0B2` |
| 铁眼 | 半藏（Hanzo） | 敌方 | `00000000A566.0B2` |
| 无赖 | 莱因哈特（Reinhardt，大锤） | 敌方 | `00000000A721.0B2` |
| 隐士 / 法师 | 血律（Doctrine） | 敌方 | `00000006D10F.0B2` |
| 复仇者 / 木偶 | 安娜（Ana） | 友方受强化者听到的“你被强化了！快上！” | `00000002B8CD.0B2` |
| 执行者 / 太刀 | 温斯顿（Winston） | 共用绝招启动咆哮主声层，敌方也听到 | `0000002A601B.03F` |
| 送葬者 / 修女 | 死怨（Shion） | 敌方 | `00000006C434.0B2` |
| 学者 | 黑影（Sombra） | 敌方 | `000000030559.0B2` |

用户写的“安然”“死苑”已按本机英雄列表对应为安燃、死怨。守护者、女爵未指定，所以这个预设不增加它们的播报；原有中文测试音频仍保留。

安娜按用户后续指定使用“你被强化了！快上！”，来自友方受强化者的听者条件：`m_DF647B95=0`、`m_EE144B9E=1`、原生 stimulus `000000000678.078`。模组将它作为复仇者大招播报播放给安装者，不再使用全队版“纳米激素已注入”。安燃使用常规主动大招，另一个重生触发版本未混入。

温斯顿不是一段有字幕的敌方专用台词。原生引用链 `gameplay entity 1C0 → statescript109 → effect211 → sound162C → Wwise event3386485218` 指向启动效果音；其主声音 `source148169123 / Sound512630930` 对应上述 `.03F`。该事件没有敌友切换，主声层为语言无关音频。这里提取主咆哮，未合成辅助变身音、随机音高、距离混响或动态总线处理；不能称为完整游戏混音的逐位复刻。

## 可重复执行的组件

工具准备一次：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Prepare-OverwatchTools.ps1
```

需要 Git、.NET 10 SDK 和 uv。此脚本只在项目 `.tools/` 下准备开源工具，不修改任何游戏文件。

```powershell
uv run python -m nuv ow-extract --overwatch-dir "D:\Overwatch"
uv run python -m nuv ow-import --build --base-profile "D:\SteamLibrary\steamapps\common\ELDEN RING NIGHTREIGN\Game\启动地图扩容+无缝联机.me3"
uv run python -m nuv verify "dist\UltimateVoices-Overwatch"
```

也可以把原无缝联机 `.me3` 配置拖到 `Build-Overwatch.cmd` 上；第二个参数可指定其他 OW 安装目录。该批处理沿用本机默认 `D:\Overwatch`。

输出：

- `local/overwatch/pinned/Pinned/`：八个原始 WEM，源文件字节摘要固定，不使用重新封装的 OGG 摘要作为源资源凭据。
- `local/overwatch/imported/<revision>/`：八个 PCM16 WAV、`voices.json` 和来源报告 `sources.json`。
- `dist/UltimateVoices-Overwatch/Launch.cmd`：独立 OW 测试包启动器，保留原无缝联机/地图/武器模组配置。

`ow-extract` 只选择性读取已审核的八个资源 GUID，`--online=false` 禁用游戏资源下载；本地工具还补上了上游的离线 keyring 开关。初次研究曾导出八英雄语音分组核对字幕/条件，日常组件不再遍历输出全部语音。

`ow-import` 在调用解码器前检查英雄、敌友听者、GUID、文件路径和原始 WEM SHA-256。解码失败、超过格式/时长预算或源数据变化均停止发布。成功导入使用不可变版本目录；重复导入验证后复用，不覆盖用户修改的 WAV。

## 开源工具和选择证据

- [OWLib/DataTool](https://github.com/overtools/OWLib)，固定提交 `546efa19516d7df7ba138802d221c73ad886df28`。
- 当前国服热修复适配使用 [TACTLib PR #40](https://github.com/overtools/TACTLib/pull/40) 的 `9b333b84211a4b95928e01be303b5ed27729c0aa`。它未合并上游；已对本机四份资源清单和八个音频实际读取验证。不是宣称官方发布版支持当前热修复。
- 项目自己的 DataTool 扩展 [NuvPinnedSfx.cs](../tools/owlib/NuvPinnedSfx.cs) 只接收明确的 `.0B2` / `.03F` GUID，以原始 WEM 输出。
- [vgmstream r2168](https://github.com/vgmstream/vgmstream/releases/tag/r2168)，Windows x64 发布包 SHA-256 `692d45070852a35c1fa42726aa3c9de528e44eec925d37d99b1074256b99a229`。

准备脚本核对源码提交、子模块干净状态、唯一离线补丁和本项目扩展摘要，拒绝把其他本地源码编辑冒称为固定版本。工具版本和摘要写入 `.tools/overwatch-tools.json`。

原始语音数据中的 `STUVoiceStimulus.m_DF647B95` 名称尚未被上游完全解析。通过半藏/黑影已知的敌方母语播报与对应友方台词校准，字段值 `0/1/2` 分别对应友方/敌方/自身；选中七段语音的字段和条件已逐条核对，没有仅凭目录排序选择。相关字段值、字幕及原始摘要保存在 [config/overwatch.json](../config/overwatch.json)。温斯顿使用单独的效果音引用链，未伪造语音听者字段。

本机研究缓存 `local/overwatch/selection-research/` 包含语音槽位、条件、温斯顿行为/效果/声库引用及审计说明；这些和实际游戏音频均不进入 Git。

## 验证边界

八个 WAV 均通过解码、格式、时长检查；八角色原生声库已生成并通过拥有清单校验。安娜最后按用户指定改为 `02B8CD`，原始 WEM SHA-256 为 `5cf2d0456c67c393aef86af5b34ae55d3ae87117b055cfc3206edafdd8e67bd5`，其他七段选择不变。新增媒体 `3,888,736 bytes`（约 3.71 MiB，含追踪者互斥分支的重复媒体），并提供同字节本地 WEM 副本；游戏运行期间不增加本项目进程、DLL、扫描或网络消息。

**无赖在上一版中文测试包中实测无播报，游戏内故障验收仍待进行。** 日志确认 `hero05.bnk` 已覆盖。后续使用同版号（135）Wwise 独立引擎证明原媒体和追加播放图可出声，并复现仅内嵌媒体在事件预备加载时失败、提供同编号本地 WEM 后成功。新版保留原声，额外输出这份本地副本；默认先校准至整段 RMS `-18 dBFS`、峰值上限 `-1 dBFS`，再应用用户增益（默认 `0 dB`）。可全局或单角色设置 `normalize: false`。

这些处理都在游戏启动前完成，不改变联机协议，也不增加游戏内扫描或转码。游戏实际使用的加载模式尚未直接采集，不能将离线修正描述为游戏内已通过。OW 包实机播放、混装无缝联机及远距离验证仍待进行；停止反复要求用户重启进行逐字段测试。
