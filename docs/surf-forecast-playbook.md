# surf-forecast 全引擎操作手册 —— 收官最终形态怎么用

> **一句话**：在 surf-forecast 上，5 个引擎共享同一套 DDD 知识层协同工作 ——
> **DDD 开局注入红线 → Pipeline 三门把关交付 → Eval 回归门守红线 → 自进化把复发错误锁成结构门 → Pollinate 产品牌正确公告**。
> 你只需一句"run pipeline for X"，其余是结构在替你把关。

---

## 0. 一分钟看懂：一个 surf-forecast 需求怎么流过全系统

```mermaid
flowchart TB
    REQ([需求: 给预报JSON加 gustRatio 阵风比字段]) --> DDD

    subgraph DDD["① DDD 知识层 (开局注入)"]
        direction LR
        d1["constraint: float→Decimal / ALB SG / api 401"]
        d2["model: wdeg[]数字契约"]
        d3["convention: GMT+8"]
    end

    DDD -->|EVALUATE/PLAN 注入红线| PIPE
    subgraph PIPE["② Pipeline 3 门 (代码强制)"]
        g0["★Gate0 现状对吗(skeptic)"] --> g1["★Gate1 方案sound(SSA)"] --> g2["★Gate2 对抗审查(security查ALB SG / operational查Decimal)"]
    end
    PIPE -->|CodeLens 爆炸半径| CI["get_impact score_wind → 上游31"]
    PIPE --> DELIV["push-ready 代码"]

    DELIV --> EVAL{{"③ Eval 红线回归门<br/>redlines.jsonl · 0 inversion"}}
    EVAL -->|绿| SHIP["合并"]
    EVAL -->|破红线| BLK["exit3 拦"]

    SHIP -->|REFLECT 写回| DDD
    SHIP -->|复发纠正| EVO["④ 自进化 L0→L3<br/>顽疾→结构门"]
    EVO -->|新结构门| PIPE
    SHIP -->|TECH.md更新| POLL["⑤ Pollinate<br/>产'新增gustRatio'准确公告<br/>5门品牌合规"]
```

---

## 1. 一次性安装（把系统接到 surf-forecast）

```bash
SF=/Users/yiming/Downloads/all_the_meshclaw/surf-forecast/surf-forecast-kiro-v2
PIPE=/Users/yiming/Downloads/all_the_meshclaw/SwarmAI-learning/pipeline

# (a) 全局装 skill，让任何会话能 "run pipeline for X"
cp -r /Users/yiming/Downloads/all_the_meshclaw/SwarmAI-learning/.kiro/skills/autonomous-pipeline ~/.kiro/skills/
# (b) 把引擎脚本放进 surf-forecast，产物落项目内
mkdir -p "$SF/pipeline"; cp "$PIPE"/*.py "$SF/pipeline/"
# (c) DDD 知识层已种(8条红线)：$SF/ddd/knowledge.jsonl  ✅
# (d) CodeLens 事实源：package liangyimingcom/surf-forecast (已索引)
# ⚠️ 必须用 set -a 让 CODELENS_TOKEN 导出到子进程(python)，否则 code_intel.py 报 "CODELENS_TOKEN not set":
set -a; source ~/.meshclaw/secrets/codelens.env; set +a    # secrets 文件里的 VAR= 没 export
```

**环境变量（每次开发前 export）：**
```bash
export DDD_STORE="$SF/ddd/knowledge.jsonl"                 # DDD/Pollinate 事实源
export PIPELINE_ARTIFACTS_ROOT="$SF/.pipeline-artifacts"   # run 产物落项目内
cd "$SF" && source .venv/bin/activate                      # same-runtime: 用 surf 自己的 venv
```

---

## 2. 端到端：给 gustRatio 加字段（真实走一遍）

### ①开局 DDD 注入（EVALUATE 就带着红线）
```bash
D="python3 pipeline/ddd.py"
$D inject --stage evaluate    # → 4 红线 constraint + wdeg model + DynamoDB decision
```
> float→Decimal 这条红线在 EVALUATE 就在眼前 —— 不靠记性。

### ②CodeLens 摸底 + 算爆炸半径（PLAN）
```bash
set -a; source ~/.meshclaw/secrets/codelens.env; set +a   # 导出 CODELENS_TOKEN 到 python 子进程
CI="python3 pipeline/code_intel.py"
$CI symbol --package liangyimingcom/surf-forecast --query build_context
$CI impact --package liangyimingcom/surf-forecast --symbol score_wind   # 上游31/下游4
$CI affected-tests --package liangyimingcom/surf-forecast --symbol score_wind
```

### ③Pipeline 三门交付（对我说 "run pipeline for 给预报JSON加gustRatio字段"）
- **Gate 0**:fresh skeptic 核"gustRatio 现在真不存在"
- **Gate 1**:SSA 核方案守红线（wdeg 数字契约、GMT+8）、API 无幻觉
- **Gate 2**:对抗子 agent 专家透镜 —— **security 查 ALB SG、operational 查写库有没有过 `_to_decimal`、api-contract 查 wdeg 契约没破**

### ④Eval 红线回归门（合并前）
```bash
python3 pipeline/eval_os.py --golden $SF/eval/redlines.jsonl --gate   # 破红线→exit3
```
（redlines.jsonl 见 `docs/eval-on-surf-forecast.md`：curl /api/spots 断言401、grep 无 0.0.0.0/0、find_callers _to_decimal…）

### ⑤REFLECT 复利写回 + 自进化
```bash
python3 pipeline/pipeline_cli.py run-cultivate --run-id <id>   # 教训→DDD(guideline/pitfall/constraint)
# 若"漏转Decimal"这类错跨多次复发：
python3 pipeline/self_evolution.py record --class skip-decimal --text "..." --session <s>
python3 pipeline/self_evolution.py act    # 复发到L3→生成结构门提案→加进pipeline_cli
```

### ⑥Pollinate 产公告（功能上线后）
```bash
P="python3 pipeline/pollinate.py"
$P plan --message "浪报新增阵风比 gustRatio" --channel social --complexity low
$P gate --message "..." --format poster --draft "阵风大不大，现在浪报直接告诉你..." --record
```
> Pollinate 的 Gate3 读**同一套 DDD** 当事实源 —— 不会声称不存在的能力。

---

## 3. 红线 → 各引擎护栏（surf-forecast 专属核对表）

| 红线 | DDD(注入) | Pipeline Gate2 专家 | Eval 回归门 |
|---|---|---|---|
| float→Decimal | constraint(全阶段注入) | operational | grep `find_callers _to_decimal` |
| ALB SG 禁 0.0.0.0/0 | constraint | security | `! grep 0.0.0.0/0 infra/` |
| /api/spots 全 401 | constraint | api-contract | `curl → 401` |
| wdeg 数字契约 | model | api-contract | JSON schema 断言 |
| GMT+8 日界 | convention | correctness | 时区边界 pytest |
| terraform 禁 -auto-approve | constraint | operational | `! grep auto-approve` |

**三层防护**:DDD 让红线**开局就在眼前**（判断层）· Pipeline Gate2 让 fresh 视角**逐条核**（对抗层）· Eval 回归门让破红线**exit3 拦发布**（验证层）。同一条红线，三道防线。

---

## 4. 原理：为什么比"直接写代码"稳

```mermaid
flowchart LR
    subgraph 直接写["靠记性 (moto测不到)"]
        a1["写put_item(float)"]-->a2["moto不校验Decimal"]-->a3["上线500💥"]
    end
    subgraph 全系统["靠结构 (漏不掉)"]
        b1["DDD开局注入Decimal红线"]-->b2["Gate2 operational逐条核"]-->b3["Eval回归门grep _to_decimal"]-->b4["复发→自进化锁成结构门"]
    end
```

- **判断不靠记性**:DDD 把红线注入到你做决策的那一刻。
- **盲点靠 fresh 视角**:Gate 2 的对抗子 agent 碰不到你的思路，专抓你看不见的（float→Decimal 这种）。
- **退化靠回归门**:Eval 0-inversion，破红线直接 exit3。
- **顽疾靠结构门**:同一类错复发到 L3，自进化把它锁成代码强制门，物理上不再发生。
- **知识会复利也会死**:REFLECT 写回 DDD，达尔文衰减淘汰过时知识，prompt 不膨胀。

---

## 5. 最快上手（3 步）

1. `export DDD_STORE=$SF/ddd/knowledge.jsonl && cd $SF && source .venv/bin/activate`
2. 对我说 **「run pipeline for <surf-forecast 需求>」** —— 我自动:DDD 注入红线 → CodeLens 摸底 → 三门把关 → 收敛 → REFLECT 写回。
3. 合并前跑 `eval_os.py --golden eval/redlines.jsonl --gate`；上线后 `pollinate.py` 产公告。

> 参考:`docs/pipeline-on-surf-forecast.md` · `docs/eval-on-surf-forecast.md` · `docs/ddd-on-surf-forecast.md` · `docs/LEARNINGS.md`。

---

## 6. 具体示例（照抄即可，带预期输出）

### Sample A — 最省事：对 agent 说一句话
在 surf-forecast 目录的 MeshClaw 会话里，你只打一句：
```
run pipeline for 给 /api/forecast 的预报 JSON 增加 gustRatio 阵风比字段
```
接下来 agent（我）会自动这样跑，你只在门口"拍板"：
```
① EVALUATE  → 读 DDD, 注入 4 红线 + wdeg 契约
            → spawn Gate0 skeptic: "gustRatio 现在真不存在吗?" → SUPPORTED ✅
② THINK     → 2 备选(加字段 vs 改scoring), 选加字段
③ PLAN      → CodeLens get_impact score_wind(上游31) + Gate1 SSA → SOUND ✅
④ BUILD     → TDD 写 gustRatio 计算 + 测试(含 float→Decimal 写库)
⑤⑥ REVIEW/TEST → 3层验证 + 118 pytest 基线无回归
⑦ DELIVER   → spawn Gate2 对抗: operational 查 _to_decimal ✅ / api-contract 查 wdeg 数字 ✅
            → push-ready
⑨ REFLECT   → 教训写回 DDD, learn_add
```
**你要做的只有**:在 Gate 0/1/2 三处看一眼裁决、DELIVER 时确认 push。其余结构替你把关。

### Sample B — 手动跑一遍（看得见每道门）
```bash
SF=/Users/yiming/Downloads/all_the_meshclaw/surf-forecast/surf-forecast-kiro-v2
export DDD_STORE="$SF/ddd/knowledge.jsonl" PIPELINE_ARTIFACTS_ROOT="$SF/.pipeline-artifacts"
cd "$SF"; PIPE="python3 pipeline/pipeline_cli.py"

# 1) 建 run(自动浮现 intel 注入建议)
$PIPE run-create --project surf-forecast --requirement "预报JSON加gustRatio字段" --profile full
# 输出: {"run_id":"run_xxxx","intel":{...},"evaluate_must_consider":"..."}

# 2) 先看 DDD 该阶段注入什么红线
python3 pipeline/ddd.py inject --stage evaluate
# 输出: 4 条 constraint(float→Decimal/ALB SG/api401/terraform) + 1 model(wdeg) + 1 decision

# 3) publish evaluate —— 若 understanding.claim 写成"我要加字段"(解决方案语言)会被 Gate0 拦:
$PIPE publish --run-id run_xxxx --stage evaluate --data '{"recommendation":"GO",...,"understanding":{"claim":"我要加 gustRatio",...}}'
# 输出(stderr): BLOCK: Understanding gate M1: claim contains solution language  ← 门在挡你
# 改成描述现状即可过:  "claim":"当前预报JSON无 gustRatio 字段"
```

### Sample C — 合并前守红线（Eval 回归门）
```bash
# 建 surf 的红线 golden set(一次性, 每条一个 shell 检查):
cat > "$SF/eval/redlines.jsonl" <<'JSONL'
{"id":"RL_spots401","check":"curl -s -o /dev/null -w '%{http_code}' localhost:8000/api/spots | grep -q 401","expect":"PASS"}
{"id":"RL_no_open_sg","check":"! grep -rn '0.0.0.0/0' infra/ terraform/ 2>/dev/null","expect":"PASS"}
{"id":"RL_decimal","check":"python3 -c \"import subprocess,sys; sys.exit(0 if '_to_decimal' in open('src/web/db.py').read() else 1)\"","expect":"PASS"}
JSONL
# 合并前跑(破任一红线 → exit3 拦住):
python3 pipeline/eval_os.py --golden "$SF/eval/redlines.jsonl" --gate
# 全绿 → exit 0 可合并; 某条红线破了 → "EVAL GATE: BLOCK" + exit3
```

### Sample D — 上线后产公告（Pollinate 5 门）
```bash
P="python3 pipeline/pollinate.py"
$P plan --message "浪报新增阵风比 gustRatio" --channel social --complexity low
# 输出: {"selected_tracks":["poster","shorts"]}

# ❌ 自吹稿 —— 被拦:
$P gate --message "gustRatio上线" --format poster --draft "我们激动地宣布业界领先的阵风比，最强算法从不出错"
# 输出(stderr): POLLINATE GATE: BLOCK — 2 failures [1_voice, 3_accuracy]

# ✅ 受众导向稿 —— 通过并记录:
$P gate --message "gustRatio上线" --format poster --draft "阵风忽大忽小毁了你的浪? 现在浪报直接告诉你的常冲浪点阵风比，出门前扫一眼。" --record
# 输出: {"push_ready": true}
```

> **对照记**:Sample A 是"日常用法"（说一句话）;B/C/D 是"想看清内部机制"时手动跑。红线只在 DDD 写一次（`$SF/ddd/knowledge.jsonl`），Pipeline/Eval/Pollinate 三处都读它。
