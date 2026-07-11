# 附录 · 总学习心得：把 SwarmAI 13 引擎搬到 MeshClaw 学到了什么

> 这是把 [SwarmAI](https://github.com/xg-gh-25/SwarmAI) 的自进化 Agent OS 移植到 MeshClaw 的复盘。
> 不是"我实现了什么"的清单（那在 README 引擎表里），而是**做这件事真正想通的道理**。

---

## 1. 最核心的一条：门是结构，不是叮嘱

整个 SwarmAI 的赌注，一句话：**carefulness 不可规模化，gate 可以。**

移植过程亲身验证了这句话。我在跑真实需求时，**自己犯了两次典型错误，都被代码强制的门当场抓住**：
- 跑 wtf_gate 时我图快"先 build 后 evaluate"，Gate 0 的 fresh skeptic 观察到文件已存在，判 `ALREADY-SATISFIED`，CLI 直接 exit 3 拦住 —— 这正是它要防的"把已完成的当待办"的 no-op 框架错误。
- 跑 run-list 时我在 REVIEW 把"坏 json 不容错"当 known-gap 放行，Gate 2 的 fresh 对抗子 agent **把它升级成 HIGH**（一个坏文件拖垮整列表）。

关键洞察：**这两个错都是"我作为 builder 离代码太近看不见"的盲点**。不是我不小心 —— 是自省有结构性上限。fresh-context、只看 diff、零 builder 偏见的子 agent 才看得见。所以门不是形式主义，是把"看不见的盲点"变成"物理上过不去的墙"。

---

## 2. "测不到 = 没造" 是真的

建 Eval OS 时最震撼的一步:我故意把 Gate 0 的 M1 墙改瞎，Eval 立刻报 `inversion: GS001`、分数掉、回归门 exit 3。**没有 Eval，我这个改动会静默上线**——门失效了没人知道。

Agent 时代 `assert` 失效了（输出非确定、prompt 是源码却没 diff/review）。Eval + Golden Set + 回归门是 `assert` 的继任者。而且它的验收标准不是"95% 通过率"，是**"0 inversion"**——一个 critical case 裁决翻转就说明有根本性错误。二元，不统计。

配套的纪律：**mutation-proof**。测试必须能在"revert 被测行"时变红，否则就是 test-theater。我们每个引擎的边界测试都做了突变验证。

---

## 3. 复利闭环是"涌现"的，不是"编排"的

一开始我以为要精心编排 5 个引擎的调用顺序。做下去发现:**它们共享一个持久结构化知识层（DDD），复利就自然涌现了**：

- pipeline 跑完 → REFLECT 把教训按本体类型写进 DDD（guideline/pitfall/constraint）
- 下次 `run-create` → EVALUATE 开局**自动注入**这些教训（我实测到 RP-mc1→+mc2→+mc3 三次累积）
- 复发的纠正 → 自进化爬 L0→L3 → 升级成结构门 → 回到 pipeline
- constraint 红线 → 同时喂 Eval 回归门
- 同一套 DDD → Pollinate 产品牌正确内容

没有一个中央调度器编排这些。**共享知识层 + 双向读写 = 复利涌现**。这也是为什么 SwarmAI 说"抽掉任何一个引擎，闭环就不成立"。

---

## 4. 会遗忘的系统 > 只会记住的系统

DDD 的达尔文衰减（Ebbinghaus 遗忘 + Hebbian 强化）一开始觉得是花活，做完才懂:**只积累不淘汰是所有 memory 系统腐烂的根因**。dormant 的知识不再注入 → prompt 成本恒定（稳态 ~80 条），不随历史膨胀。而常用的知识靠 Hebbian 抗遗忘。衰减是 agent 所知之物的**自然选择**。

---

## 5. 什么该造，什么该接（架构判断）

13 引擎里我只真造了 5 个。另外 7 个（记忆/任务/上下文/自愈/多标签/Hook/技能通道）**映射到 MeshClaw 原生，没重造**。

判断标准很清晰：**SwarmAI 是独立桌面 App，必须自带平台底座；MeshClaw 本身就是那个底座。** 在 MeshClaw 上重造记忆库和调度器是重复造轮子。正确做法是把"引擎环"（判断/评估/知识/进化/内容）接到原生能力上。分清"引擎"和"底座"，是移植最重要的一次判断。

---

## 6. MeshClaw 原语到 SwarmAI 概念的映射，比想象中干净

| SwarmAI 要的 | MeshClaw 给的 | 惊喜程度 |
|---|---|---|
| fresh-context 对抗子 agent | `spawn_run` | 完美对应 |
| 过夜自主到 DoD | autonudge + cron | 已验证(LeagueApparel 7 cycles) |
| 代码智能/爆炸半径 | CodeLens MCP | 已接(surf-forecast) |
| DDD 知识层 | steering + memory + lessons | 概念同构 |
| 复利写回 | learn_add + 本项目 DDD | 现成 |

唯一要真造的，是那个把"门"写死在代码里的**状态机**（`pipeline_cli.py`）。其余是把 prompt 改写成 skill + 把 MeshClaw 原语接上线。

---

## 7. 踩的坑（诚实记录）

- **硬编码密钥**:我一开始把 CodeLens ServiceToken 写进 `code_intel.py` 默认值 —— 推 GitHub 前发现并清除，改从 env 读。**推公开仓库前必须全树扫密钥。**
- **私有仓库 CodeLens 索引 404**:CodeLens 只索引 public GitHub repo，私有会 404。转 public 才成功。
- **调参量纲**:DDD 的 Ebbinghaus stability 初值给成 1.0，分数瞬间触底没区分度 —— 改成天量纲(30)才有意义。
- **README 的"7 类本体" vs shipped 的"5 类"**:文档和实现有出入（Eval 的 5→6 维同理）。**以 shipped 源码为准**,我扩成 7 类并诚实标注。

---

## 8. 一句话总结

> **把一个"越用越聪明"的 Agent OS 搬到新运行时，真正难的不是写代码，是想清楚"哪些错误要用结构堵死、哪些知识要让它死、哪些底座不该重造"。SwarmAI 的价值不在 22 万行，在这几条判断。**

—— 移植过程本身就是这套方法论的最小可验证证据：人（你）定方向、在每道门拍板；AI（我）负责构建、被门挡住、收敛。`git log` 为证（PR #1–#5）。
