# 发布包校验 / Release validation — 2026-11-01

| 变体 | ZIP 大小 | 文件数 | SHA-256 |
| --- | ---: | ---: | --- |
| Native | 36,864,015 bytes | 36 | `4497c6ed3c72bbec8c49b78b08392640da5de30afd041f4b8a4141b7e6e81627` |
| MMV-Addon | 38,313,996 bytes | 32 | `74b381dae99c4407e05acbb95b13c700919a7bb45a8e7b86359cd215fd4a983f` |
| Build-Toolkit | 131,762 bytes | 51 | `9a0c773775c6d224b9c7953c7c9e2110474bd3fd729d06be1f1d27ff3ddbb3b4` |
| Audio-Sources | 3,811,327 bytes | 14 | `7d4f91ad74f84e208c85538d3d5de286d51bf4ccb21de3487912e1637603d623` |

两包 ZIP CRC、内部 SHA256SUMS 和外部 `.zip.sha256` 均通过。分别包含 24 个游戏资源文件：十个角色声库、11 个本地媒体镜像、两个声音目录、一份动画包。十个 SBI 声库事件集合与实际 BNK 一致，11 个语音挂载点与媒体镜像核对通过。

MMV-Addon 的全部 24 个资源与现有已测 `dist/UltimateVoices-Overwatch` 逐字节一致。Native 与其相比，仅 `chr/c0000.anibnd.dcx` 不同；其余 23 个资源完全一致。

对实际 ZIP 解压输出独立读取 BND/TAE、移除四条新增事件和分组后，原输入逐字节恢复。Native 保留 538 个成员，MMV 保留 623 个成员，分别只修改三个 TAE。动画调用仍为 type-129，原声隔离与声音图未在此轮变更。

实际 ZIP 解压到包含空格的另一目录后，ME3 `profile show --file` 成功解析原生单人、原生无缝和“现有 MMV 配置副本 + 附加条目”三份配置。包内相对路径、无缝预设存档名称、依赖顺序核对通过，没有为了验证启动游戏。

不含私人路径/报告、存档、无缝 DLL、提取缓存、开发依赖或 SDK。MMV 包明确含指定 MMV 基底的派生动画，说明没有把它写成不含 MMV 资源或通用原生版本。

Audio Sources 十份默认 WAV 按实际配置转换后，与运行包 11 路 WEM 一致。另将 Build Toolkit 与 Audio Sources 解压到新目录，复制已核验的编译辅助工具，按教程执行离线 build/verify；生成的 24 个游戏资源与 Native 成品完全一致。此检查复用了已准备的辅助工具，没有重新联网安装 SDK。

功能基线通过 103 项测试（本次发布准备已重新运行）。本轮只调整文档和打包，游戏功能代码未改动。用户正在使用的包没有修改。正向实机反馈对应 MMV 版，Native 只完成本页所列离线验证；完整角色分支、混装联机距离及帧时间矩阵仍未完成。这些校验不表示文件已公开上传。

English: both runtime archives passed CRC, per-file hash, 11 media/route, catalog registration, independent animation restoration and relocated ME3 parsing checks. MMV matches the locally tested resources. A fresh toolkit/default-WAV extraction reproduced all 24 Native runtime resources using the prepared helper. No game was launched. Native has not completed a separate gameplay matrix.
