# 黑夜君临 × 守望中文大招播报 — Native Resources 0.1.0 Beta

此包内置十角色守望中文播报，提供游戏资源和 ME3 配置。原大招喊声隔离、守护者/铁眼起手播报、学者收招播报与此前成品相同。24 个游戏资源文件逐字节相同；本次仅简化安装包装，没有新增游戏进程或 DLL。

## 安装与启动

需要 Steam 黑夜君临文件版本 **1.3.3.0** 与另行安装的 [Mod Engine 3](https://github.com/garyttierney/me3/releases)。无需守望、Python、uv、Git 或 SDK。

1. 将整个 `UltimateVoices-Overwatch` 文件夹解压到游戏安装目录外，保持 `.me3` 与 `mod/` 在一起。
2. 启动 Steam，通过 ME3 打开 **`UltimateVoices.me3`**。安装了 ME3 文件关联时可直接双击；也可在本包目录打开终端执行：

```powershell
me3 launch -g nightreign -p ".\UltimateVoices.me3"
```

包内不提供 CMD/BAT/PowerShell 启动脚本。此配置使用离线单人模式，不加载无缝，不指定额外存档名。

## 已有无缝联机

将自己的完整 `SeamlessCoop` 文件夹放在 `.me3` 旁，确认 `SeamlessCoop/nrsc.dll` 存在，再通过 ME3 打开 **`UltimateVoices-Seamless.me3`**。此包不附无缝 DLL。也可执行：

```powershell
me3 launch -g nightreign -p ".\UltimateVoices-Seamless.me3"
```

内置配置使用默认 `NR0000.co2`。自定义存档扩展、其他模组或不同启动设置应沿用自己的原配置副本，在副本追加下列条目并调整路径：

```toml
[[packages]]
id = "nightreign-ultimate-voices"
path = "./UltimateVoices-Overwatch/mod"
```

不要通过普通官方匹配加载。此包是原生动画版；**MMV 用户选 MMV-Addon，二选一**。同一动画、声库、声音目录冲突需正确合并，不能删掉文件或改加载顺序来强行兼容。

## 播报、性能与验证

追踪者→安燃；守护者→末日铁拳“毁天灭地！”；铁眼→半藏；女爵→禅雅塔友方“感受宁静。”；无赖→莱因哈特；复仇者→安娜“你被强化了！快上！”；隐士→血律；执行者→温斯顿启动主咆哮；学者→黑影；送葬者→死怨。

守护者、铁眼在游戏接受大招并开始动作时播报，学者约 3.3 秒收招时播报。只移除已定位专用原喊声，保留蓄力、爆炸与命中音效。每台电脑使用自己的本地资源，不传音频，不强制队友安装；远处队友的原生事件覆盖与完整混装联机矩阵仍未验证。

游戏中无新增本项目 DLL、常驻进程、轮询、转码或网络协议。没有帧时间基准。MMV 版有正向本机实测反馈；Native 完成离线构建与独立动画恢复审计，未单独完成实机矩阵。此包装只减少脚本，不改变这些验证边界。

## 自定义与停用

单角色换音频、格式、音量、重建与恢复默认见 **CUSTOM-AUDIO.md（中英）**。可选构建工具与默认 WAV 见 [GitHub Release](https://github.com/happys2333/Nightreign-Ultimate-Voices/releases/tag/v0.1.0)，普通玩家不用下载。不要把自定义 WAV 直接放进 mod/sd/。

改用原配置或从自己的配置副本删去本包条目即可停用。素材归属见 CREDITS.txt，原创源码 GPL-3.0；不改变第三方素材的权利归属。
