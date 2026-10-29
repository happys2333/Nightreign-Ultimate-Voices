# 守望成品包整理结果

2026-10-29。本轮只整理成品候选，保留现有音频及玩法行为，没有上传或操作 Nexus 账号。之前的 Build Toolkit 继续保留，属于开发者/自定义音频的可选下载，不作为此次成品安装的前置条件。

## 两个互斥成品

| 文件 | 用途 | 安装依赖 |
| --- | --- | --- |
| `dist/nexus/Nightreign-Overwatch-Voices-0.1.0-Native.zip` | 原生玩家动画环境的成品主包，附离线及无缝启动配置 | 游戏 1.3.3.0、ME3；无缝模式另用自己的 Seamless Co-op |
| `dist/nexus/Nightreign-Overwatch-Voices-0.1.0-MMV-Addon.zip` | 当前已测 MMV 版本的成品附加包，追加到原有 ME3 配置 | 指定摘要的 MMV、现有 ME3/联机配置 |

两个包都已经包含选定的十角色守望中文语音，无需守望安装、Python、uv、Git、编译器或 SDK。MMV 附加包的 24 个游戏资源文件与现有已测成品逐字节一致。原生包与其相比只有动画基底不同，其余 23 个游戏资源文件完全相同。

ZIP、资源字节、异地相对路径配置和动画恢复的校验结果见 [VALIDATION.md](VALIDATION.md)。

原生包不包含 MMV 动画；MMV 附加包包含在指定 MMV 基底上合并的动画文件，必须搭配对应 MMV 安装。二者均不附无缝 DLL、其他 MMV 资源、汉化、存档、个人启动配置、提取缓存或开发工具。

## 便携性和使用范围

原生包采用 `./mod` 及 `./SeamlessCoop/nrsc.dll` 相对路径，启动器通过自身目录定位 `.me3`，整个文件夹可以移动。无缝预设使用默认 `NR0000.co2`；自定义存档或其他模组用户按 README 集成到自己的配置副本。

MMV 附加包不伪造通用启动器，直接提供追加条目并保留用户自己的原联机、汉化、存档和其他模组设置。要求的原始 MMV 动画 SHA-256：

`0eafca3631ddbbf3b2ec67edb49068bdc4ebcf5e4d48b2b1720a0a1c2921be69`

## 后续在 N 网的文件安排

建议页面名 `Nightreign x Overwatch Ultimate Voices - Chinese Callouts`，版本 `0.1.0 Beta`，标题和摘要明确这是预制中文语音。文件可安排为 Native 主文件、MMV-Addon 可选文件、Build Toolkit 开发工具可选文件；Native/MMV 二选一。不要使用此前写着“无音频工具包”的介绍或封面描述这两个成品。

依赖只列游戏/ME3，MMV 及 Seamless Co-op 按相应下载项注明。素材来源写入包内 `CREDITS.txt`，页面制作说明和 AI 标签保留真实信息。页面和素材发布事宜按用户要求放到后续步骤处理，不在本轮代替用户作最终提交。

## 维护者重新打包

保留已完成构建的拥有清单，执行：

```powershell
uv run python release/overwatch/package.py --variant Native --built local/overwatch-release/native-built
uv run python release/overwatch/package.py --variant MMV-Addon --built dist/UltimateVoices-Overwatch
```

脚本核对原生/MMV 输入摘要、十角色声库、媒体、声音登记和 type-129 动画事件，只收集拥有清单中的 24 个 `mod/` 资源，重新附上干净的说明与相对路径模板。原始 `build-report.json`、绝对路径 `.me3` 和提取报告不进入成品 ZIP。每包附内部 SHA256SUMS 与外部 `.zip.sha256`。
