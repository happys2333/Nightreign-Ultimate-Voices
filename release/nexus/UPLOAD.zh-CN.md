# Nexus Mods 首发准备

整理日期：2026-10-28。建议发布 **Nightreign Ultimate Voices — Custom Callouts (Build Toolkit)**，版本 **0.1.0**，状态 **Beta**。当前项目版本也是 0.1.0。此材料只准备公开文件和页面，不代表已经向 Nexus 提交。

维护者可在 Git 源码仓库中运行 `uv run python release/nexus/package.py` 重新生成白名单 ZIP 和外部 SHA-256 文件。此打包脚本不进入公开工具 ZIP；下载者按 README 使用构建器，不需要重新发布打包流程。打包与异地解压验证结果见 [VALIDATION.md](VALIDATION.md)。

## 文件选择

上传 `dist/nexus/Nightreign-Ultimate-Voices-0.1.0-Build-Toolkit.zip` 作为 Main File，文件显示名称使用 `Nightreign Ultimate Voices - Build Toolkit (Beta)`。下载说明明确“源码构建工具，需要 Git、uv 和 .NET 9 SDK；不含任何游戏音频或预制游戏资源”。

不要上传本机的 `dist/UltimateVoices-Overwatch` 或 `dist/UltimateVoices`：前者含提取的 OW 音频，两者都含游戏派生声库和当前 MMV 合并动画，启动配置和报告还包含本机绝对路径。测试包的可运行不等于可直接作为公共下载包。

源码工具包不包括任何 `.bnk/.wem/.wav/.ogg/.dll/.exe/.anibnd.dcx`、现成 `.me3`、存档、研究缓存、虚拟环境或第三方模组。中文测试音频可让下载者用 Windows 本地生成；既有十角色映射保留在配置中。可选 OW 导入只附工具源码及选段元数据，实际支持的本地 OW 版本固定，详见包内 `OW-PRESET.md`。

这只是减少公开分发的第三方资源，不保证 Nexus 一定接受该工具，也不意味着本地提取或跨游戏使用自动获得权利人授权。

## 页面填写

1. 登录自己的 Nexus Mods 账号，进入 [Elden Ring Nightreign 游戏专区](https://www.nexusmods.com/games/eldenringnightreign)，从网站提供的上传/添加模组入口创建页面。先保存为草稿。
2. 名称填上述推荐英文名；版本 0.1.0。分类优先选择当前列表中的声音/音频类；没有时选择工具或 Miscellaneous，描述中明确 Build Toolkit。不要冒称即装声音包或 Vortex 安装器。
3. Short description 可填：`Build local custom ultimate voice callouts for all ten Nightfarers. Native playback, per-character WAV audio, and no teammate install requirement. Source toolkit; requires Git, uv and .NET 9 SDK.`
4. 英文介绍使用 `DESCRIPTION.en.bbcode.txt`；中文介绍见 `DESCRIPTION.zh-CN.bbcode.txt`。编辑器支持 BBCode，保存前查看实际预览。两份都说明不附 OW 语音，用户可以自行选择有权使用的音频。
5. Requirements：ME3、Git、uv、.NET 9 SDK 列为站外要求；Windows/游戏文件版本写进说明。Seamless Co-op 仅为可选联机要求，不把 MMV 设为必装，不宣称支持所有 MMV 版本。
6. 当前代码主要由 AI 生成，按规则标 **AI-Generated Content**；如果采用这里的 AI 起草页面介绍，也标 **AI Media**。不要仅标 AI Assisted 来淡化生成代码事实。其他功能标签以网站实际可选项为准。
7. 权限自定义说明采用下一节的文字，保持与 GPL-3.0 一致，不给代码加“禁止修改/再分发”等冲突限制。初版可先不加入 Donation Points；这是发布建议，不是已核实的强制要求。
8. 上传工具包 ZIP 为 Main File，填写真实更新记录。先等待网站的文件检查结果，不使用密码或嵌套 ZIP。若被隔离，按站内提示处理，不反复换包绕过检查。
9. 图片可用同目录的原创文字封面 `media/cover.png`，它只是功能标题卡。建议再附自己的实机截图、20–40 秒演示，重点展示守护者/铁眼起手和学者收招的播报。不要把标题卡写成实机截图。
10. 检查下载文件、说明、依赖、授权、标签、预览，再发布。未完成的页面维持草稿/隐藏，不发布没有功能文件的占位页。

用户当前只授权整理发布准备，不在本轮代替用户确认权利声明、登录账号或点击公开发布。

## 权限与制作说明，可直接复制

```text
Project source code is distributed under GPL-3.0; see LICENSE for its full terms. You may use, modify and redistribute the project code in accordance with that license. These permissions do not grant rights to Overwatch, Nightreign, other games, third-party libraries, or other mod authors' assets. No extracted game media or prebuilt game-derived banks/animations are included in this download.

Development used substantial AI-generated code under human-directed requirements, audio selection and local gameplay testing. The mod-page text was also AI-drafted and reviewed against the implementation. The download includes no cloned or AI-imitated character voices.
```

若以后想发“下载即用的 OW 语音版”，先取得可核验的素材再分发许可，再准备不包含其他模组内容、使用可迁移路径的安装包。署名、免费发布、“仅供学习”或已经购买/安装游戏都不等同于素材再分发许可；不要把现成声音包移到外链当替代上传。

## 已核对的官方依据

- [Nexus File Submission Guidelines](https://help.nexusmods.com/article/28-file-submission-guidelines)：版权内容需权利人许可；署名不能代替授权；外链也不能用于提供不允许托管的文件；功能、性能和兼容性声明应准确。还规定 AI-Generated Content / AI Media / AI Assisted 标签，以及公开页面需有功能文件。检查日期 2026-10-28，页面显示最后更新 2026-10-27。
- [Nexus 新上传表单公告](https://www.nexusmods.com/news/15491)：新版上传流程已启用，支持 BBCode 描述预览；不要照旧版教程寻找固定排列的全部按钮。
- [Nexus 文件隔离说明](https://help.nexusmods.com/article/117-why-has-my-mod-been-quarantined)：建议 ZIP/7z，避免嵌套压缩包和密码。
- [Blizzard Video Policy](https://www.blizzard.com/en-gb/legal/2068564f-f427-4c1c-8664-c107c90b34d5/blizzard-video-policy)：视频政策只应按其视频授权范围理解，不能当作在另一款游戏中分发原始语音的许可。网址若变动，请从 Blizzard Legal 的 Video Policy 入口访问。

上述是基于已读网站规则的发布建议，并非获得了 Nexus 或游戏权利人的审核批准。
