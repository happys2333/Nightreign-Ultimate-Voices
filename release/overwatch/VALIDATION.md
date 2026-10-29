# 成品包校验 — 2026-10-29

| 变体 | ZIP 大小 | 文件数 | SHA-256 |
| --- | ---: | ---: | --- |
| Native | 36,859,931 bytes | 35 | `5babec25a1d1e3812f5ad537d531f1d386b3d91f07b9c771f4c31c50b4f561c8` |
| MMV-Addon | 38,309,930 bytes | 31 | `71cb708886fcd74fdfe6630a5ba11ae7d4f9abe8f0a5de97fa8bdc25306748b3` |

两包 ZIP CRC、内部 SHA256SUMS 和外部 `.zip.sha256` 均通过。分别包含 24 个游戏资源文件：十个角色声库、11 个本地媒体镜像、两个声音目录、一份动画包。十个 SBI 声库事件集合与实际 BNK 一致，11 个语音挂载点与媒体镜像核对通过。

MMV-Addon 的全部 24 个资源与现有已测 `dist/UltimateVoices-Overwatch` 逐字节一致。Native 与其相比，仅 `chr/c0000.anibnd.dcx` 不同；其余 23 个资源完全一致。

对实际 ZIP 解压输出独立读取 BND/TAE、移除四条新增事件和分组后，原输入逐字节恢复。Native 保留 538 个成员，MMV 保留 623 个成员，分别只修改三个 TAE。动画调用仍为 type-129，原声隔离与声音图未在此轮变更。

实际 ZIP 解压到包含空格的另一目录后，ME3 `profile show --file` 成功解析原生单人、原生无缝和“现有 MMV 配置副本 + 附加条目”三份配置。包内相对路径、无缝预设存档名称、依赖顺序核对通过，没有为了验证启动游戏。

不含私人路径/报告、存档、无缝 DLL、提取缓存、开发依赖或 SDK。MMV 包明确含指定 MMV 基底的派生动画，说明没有把它写成不含 MMV 资源或通用原生版本。

独立审查未发现需要修正的打包或说明问题。用户正在使用的包没有修改。正向实机反馈对应 MMV 版，Native 候选只完成本页所列离线验证。本轮没有公开上传。私有详细收据：`local/overwatch-release/final-validation.json`。
