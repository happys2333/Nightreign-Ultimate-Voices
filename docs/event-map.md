# 原生绝招音效事件映射

本映射仅针对本机 **Nightreign 1.3.3.0**。`config/characters.json` 保存了十个角色声库的 SHA-256、11 个原生 Event 的编号与原始载荷摘要、原始 Action 编号与摘要，以及每个事件在原生和本机 MMV TAE 中的全部出现位置。追踪者的蓄满和提前释放使用两个互斥事件，其余角色各使用一个事件。

这是已完成的**静态资源验证**；尚未完成游戏内一次施放一次播报、远端队友、距离、混装无缝联机和中断边界验证。不能把下列静态计数理解为已经通过这些游戏测试。

## 事件与动作

所有选中事件都是 TAE 类型 `129 / Wwise_PlaySound_BySlot`，`SoundType=1`（角色音效）、`SoundIDOffsetType=-1`（不依赖当前武器偏移）。事件名为 `Play_c` 加九位十进制 SoundID。对小写 ASCII 名称计算 Wwise FNV-1（先乘 `16777619` 再异或字节，初始值 `2166136261`），得到的编号均已在对应角色声库的 HIRC Event 对象中实证匹配；没有用数值外形推测不存在的事件。

表中时间是 TAE 的局部秒数。`a900:600000` 表示 `a900.tae` 中动画 ID `600000`；TAE 文件内部 ID 为 `2900`，不能直接拿内部 ID 当动画文件前缀。

| 角色 | 声库 | 选中的原生事件 | 全部原生/MMV TAE 出现位置与开始时间 | 对应绝招状态 |
| --- | --- | --- | --- | --- |
| 追踪者 Wylder | `sd/hero01.bnk` | `Play_c000107105`；`Play_c000107106` | `107105`：`a900:600000/600100/600200/605000` 各 `3.000`；`a900:605200` 为 `0.133333`。`107106`：`a900:600005` 为 `1.966667` | `PileBunkerStart`、提前释放 `PileBunkerCancelEarly`、空中开始与落地 |
| 守护者 Guardian | `sd/hero02.bnk` | `Play_c000207103` | `a901:610000` 为 `2.933333`；`a901:615000` 为 `2.166667` | `DragoonJumpStart`、`AirDragoonJumpStart` |
| 铁眼 Ironeye | `sd/hero03.bnk` | `Play_c000307110` | `a902:620000` 为 `2.866667`；`a902:620005` 为 `0.033333` | `LongBowSnipeStart`、`LongBowSnipeCancelEarly` |
| 女爵 Duchess | `sd/hero04.bnk` | `Play_c000407100` | `a903:630000/635000` 各 `0.000` | `AllHideStart`、`AirAllHideStart`；落地续接 `630000` |
| 无赖 Raider | `sd/hero05.bnk` | `Play_c000508100` | `a904:640000` 为 `1.066667` | `RockWallAttackStart` |
| 复仇者 Revenant | `sd/hero06.bnk` | `Play_c000607102` | `a905:650000` 为 `1.266667` | `LivingDeadStart` |
| 隐士 Recluse | `sd/hero07.bnk` | `Play_c000707500` | `a906:660000` 为 `0.000` | `BloodMagicStart` |
| 执行者 Executor | `sd/hero08.bnk` | `Play_c000807501` | `a907:670000` 为 `0.000` | `DemonBeastStart`；变身待机 `670010` 不含选中事件 |
| 学者 Scholar | `sd/hero09.bnk` | `Play_c000907100` | `a908:680000` 为 `0.000` | `JointChainStart` |
| 送葬者 Undertaker | `sd/hero10.bnk` | `Play_c001007100` | `a909:690000/690010/695000/695010` 各 `0.000` | `BlinkStakeStart`、追加奖励分支、对应空中分支 |

这些事件实际位于 `hero01.bnk` 至 `hero10.bnk`，不在 `cs_main.bnk` 或 `cs_smain.bnk`。构建只覆盖对应角色声库。

## 证据链和分支边界

1. 从原始 `chr/c0000.behbnd.dcx` 以及当前 MMV 同名资源提取 `Behaviors/c0000.hkx`，使用 [HKLib 0.1.3-NR](https://github.com/The12thAvenger/HKLib/releases/tag/v0.1.3-NR) 解码。图中状态连接到 `CustomManualSelectorGenerator`，其 `animId`、`offsetType=11` 和下游 clip 明确指向上表动画。所有相关原生/MMV generator 对象编号和绑定都记录在配置的 `characters[].evidence` 中。例如原生 `PileBunkerStart` 经 `object2928` selector 连接 `object3973`（`animId=600000`）、`object3974/3975`（`animId=600100`）；无赖的 `RockWallAttackStart_CMSG` 是 `object2960`，`animId=640000`。
2. 读取原始及 MMV `chr/c0000.anibnd.dcx` 中的全部 TAE，分别扫描 **11,606** 和 **13,994** 个动画记录。11 个选中 SoundID 的全部出现位置、开始/结束时间及参数原始字节在两者之间完全一致。它们均只出现在上表的绝招动画族，普通攻击、职业技能、待机和就绪提示中没有发现这些 SoundID。
3. 每个扫描到的动画记录最多包含一个选中事件实例；追踪者 `107105` 和 `107106` 没有出现在同一动画记录中。并未叠加同一动作的蓄力声、发射声和后续声来触发多次播报。原始 Event Action 均保留。
4. 声库的 HIRC Event 编号、原始 Action 列表以及摘要已逐个验证。配置中的 `event_fingerprints` 是 **Event 载荷本身**的 SHA-256，摘要不包含 HIRC 类型、长度或对象编号外壳；Action 摘要同理。源声库摘要覆盖整个文件。

### 追踪者：提前释放与空中落地

`PileBunkerStart` 的释放音是 `107105`，提前释放动画 `600005` 改用 `107106`。`107100` 在两种动画开始就出现，属于准备阶段，因此没有用它作为触发点；`107107` 是各分支更晚的后续声，也没有重复叠加。

空中 `605000` 和落地 `605200` 均保留 `107105`，但不能把静态两行理解为一次施放必定触发两次。本机 MMV 的 `AirUltCommonFunction` 在落地且 `102060` 有效时转入 `AirPileBunkerLand`，否则转入普通落地；`145` 失效后则转入 `FallLoop`。原生/MMV `605000` 的 `102060` 仅在 `0–1.433333s`，`145` 仅在 `0–2s`；其 `107105` 在 `3s`。提前落地改走 `605200` 的 `0.133333s` 释放事件。这里已验证图和 TAE 结构，以及可读的当前 MMV 脚本控制流；原始游戏 HKS 是编译字节码，没有声称其文本反编译已经完成。

### 女爵：落地继续已有动作

`AirAllHideLand_CMSG` 复用 `630000`，其 clip 的 `startTime` 绑定 Havok 变量索引 `202`（`TimeActEditor_10`）。`635000` 的 TAE 类型 `605` 更新该变量，供落地继续已有动作阶段。该绑定在原生 `object3990 → object8161` 和 MMV 对应对象中一致，不能把它当作落地从零重新施放一轮绝招。`407100` 的 TAE 播放行为值为 `2`；模板对其语义仍标记为未知，实际是否在所有落地边界都只 Post 一次需要游戏实测。

### 守护者、铁眼与送葬者

守护者选中事件仅在起跳动作 `610000/615000` 出现；落地 `610010`、持盾循环 `610011`、结束 `610012`、空中循环 `615100` 都没有它。铁眼的普通/提前释放 `620000/620005` 分别含一个 `307110`。送葬者选中 `1007100` 只在普通/奖励/空中开始动画出现，抵达目标后 `BlinkStakeFinish` 的 `690001/690011` 和上下方向附加循环没有该事件。执行者选中声也不出现在变身待机循环中。

## 复核

本次本地证据缓存位于 `local/native-tae.json`、`local/mmv-tae.json`、`local/evidence_map/{native,mod}-behavior/`；均不随仓库分发。配置本身保存所选事件的完整位置和摘要，不包含原生声库或游戏脚本。

从相同资源重新生成两个 TAE JSON 后，可运行以下复核。它会检查整个动画集合，拒绝任一动画含两个触发点、普通动画新增复用、原生/MMV 位置变化、Event 指纹变化或原始 Action 列表变化。

```powershell
@'
import hashlib, json, struct
from pathlib import Path
from nuv.bank import Bank
from nuv.build import event_hash
m = json.loads(Path('config/characters.json').read_text(encoding='utf-8'))
selected = {int(n[6:]): n for n in m['event_metadata']}
for label in ('native', 'mmv'):
    rows = json.loads(Path(f'local/{label}-tae.json').read_text(encoding='utf-8'))
    found = {n: [] for n in m['event_metadata']}
    for a in rows:
        hits = 0
        for e in a['events']:
            if e['type'] not in (128,129,130,131,132,134): continue
            st, si = struct.unpack_from('<ii', bytes.fromhex(e['hex']))
            if st != 1 or si not in selected: continue
            hits += 1
            found[selected[si]].append((a['tae'], a['anim'], e['start'], e['end'], e['hex']))
        assert hits <= 1, (label, a['tae'], a['anim'])
    for n, actual in found.items():
        expected = [(u['tae_id'], u['animation_id'], u['start_seconds'], u['end_seconds'], u['parameters_hex'])
                    for u in m['event_metadata'][n]['native_and_mmv_tae_uses']]
        assert actual == expected, (label, n)
    print(label, len(rows), 'animation records: selected uses match')
for resource, digest in m['banks'].items():
    raw = (Path('local/game') / resource).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, resource
    b = Bank.parse(raw)
    for name, detail in m['event_metadata'].items():
        if detail['bank'] != resource: continue
        event = b.objects_by_id[event_hash(name)]
        assert hashlib.sha256(event.payload).hexdigest() == m['event_fingerprints'][name]
        assert list(b.event_actions(event.id)) == detail['original_action_ids']
print('11 Events / 10 banks: fingerprints and original actions match')
'@ | .venv\Scripts\python.exe -
```

本地开发时另保存了 `local/evidence_map/build_map.py` 和 `audit-summary.json`，用于复现生成过程；它们不是运行游戏所需的组件。TAE 参数名称依据本地 `.tools/TAE.Template.ERNR.xml`，行为文件解码依据 HKLib 的 Nightreign 版本；哈希和声库行为可对照 [Yonder 事件文档](https://ndahn.github.io/yonder/wwise/events/)。
