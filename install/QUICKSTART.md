# 新 MeshClaw 环境 · 快速使用指南（Quickstart）

> 目标：在**另一台电脑的新 MeshClaw 环境**里，一键导入 SwarmAI 13 引擎移植，自检无误后立即上手。

---

## 0. 前置条件

| 必需 | 说明 |
|------|------|
| **Python 3.10+** | 全部引擎纯标准库，**无需 pip install** |
| **git** | 克隆仓库 |
| MeshClaw dashboard | （可选）想用「run pipeline for X」自然语言触发才需要；纯 CLI 用法不需要 |
| CodeLens token | （可选）只有用爆炸半径 `code_intel.py` 才需要，见 §4 |

---

## 1. 一键导入（30 秒）

```bash
git clone https://github.com/liangyimingcom/SwarmAI-learning.git
cd SwarmAI-learning
bash install/install.sh
```

安装脚本会：
1. 校验 python3；
2. 把 `autonomous-pipeline` skill 装到 `~/.kiro/skills/`（让任何 MeshClaw 会话能触发）；
3. 跑 `install/selfcheck.sh` 自检全部 5 个引擎。

看到 **`SELFCHECK: PASS ✅` + `🎉 install OK`** 即导入成功。

> 自定义 skill 目录：`KIRO_SKILLS_DIR=/path/to/skills bash install/install.sh`

---

## 2. 验证无误（自检做了什么）

`selfcheck.sh` 在临时隔离目录里跑，不碰任何真实状态，逐引擎验证：

| 检查 | 通过标准 |
|------|----------|
| 9 模块编译 | 全部 compile |
| #4 Pipeline | Gate 0 拦截"解决方案语言"claim（exit 3）|
| #13 Eval OS | Golden Set 10/10、回归门 0 inversion |
| #3 DDD | 本体阶段注入 + 达尔文衰减 |
| #6 自进化 | record/assess |
| #5 Pollinate | Gate1 拦自吹稿 |
| 工具 | wtf_gate/confidence_score/run-list 退出码正确 |

随时可单独重跑：`bash install/selfcheck.sh`

---

## 3. 立即上手（两种用法）

### 用法 A · 自然语言触发（最省事）
在 MeshClaw 会话里直接说：
```
run pipeline for <你的需求>
```
agent 会自动走 9 阶段 3 门（EVALUATE→…→REFLECT），在 Gate 0/1/2 处 spawn 对抗子 agent，你只在门口拍板。

### 用法 B · 直接驱动 CLI（看得见每道门）
```bash
PIPE="python3 pipeline/pipeline_cli.py"
$PIPE run-create --project demo --requirement "实现一个 X" --profile full   # 记下 run_id
# 每阶段: publish(门在此跑) -> advance
$PIPE run-list                       # 一览所有 run
$PIPE run-cultivate --run-id <id>    # REFLECT 复利写回
$PIPE run-report   --run-id <id>     # 生成 REPORT.md
```

### 其它引擎
```bash
python3 pipeline/eval_os.py --gate              # #13 回归门(0 inversion 才 exit0)
python3 pipeline/ddd.py inject --stage build    # #3 该阶段注入哪些本体
python3 pipeline/self_evolution.py audit        # #6 纠正 L0-L3 阶梯
python3 pipeline/pollinate.py tracks            # #5 11 内容轨道
```

---

## 4. 用在某个项目（如把红线接进去）

```bash
PROJ=/path/to/your-project
export DDD_STORE="$PROJ/ddd/knowledge.jsonl"                 # DDD/Pollinate 事实源(落项目内)
export PIPELINE_ARTIFACTS_ROOT="$PROJ/.pipeline-artifacts"   # run 产物落项目内
# 种红线为 constraint 本体(会在 EVALUATE/PLAN/REVIEW/DELIVER 全程注入):
python3 pipeline/ddd.py add --type constraint --text "你的红线" --source 红线
# 合并前跑项目红线回归门(command 型 golden set, 见 docs/eval-on-surf-forecast.md):
python3 pipeline/eval_os.py --golden "$PROJ/eval/redlines.jsonl" --cwd "$PROJ" --gate
```

**（可选）CodeLens 爆炸半径**：需要一个 CodeLens 服务 token。注意 secrets 文件里的 `VAR=` 没 export，子进程收不到，必须用 `set -a`：
```bash
set -a; source ~/.meshclaw/secrets/codelens.env; set +a
python3 pipeline/code_intel.py impact --package <owner/repo> --symbol <fn>
```
> 本仓库**不打包任何 token/密钥**。没有 token 时 `code_intel.py` 会友好报错，其余引擎照常工作。

---

## 5. 深入

- 全景与引擎表：`README.md` / `README.zh-CN.md`
- 一次真实 run 全程复盘：`docs/walkthrough-run-list.md`
- 在具体项目端到端用（surf-forecast 为例，含 4 个可复制示例）：`docs/surf-forecast-playbook.md`
- 各引擎原理：`docs/{eval-os,ddd-engine,self-evolution,pollinate-engine}.md`
- 编排运行手册：`.kiro/skills/autonomous-pipeline/INSTRUCTIONS.md`

---

## 6. 卸载

```bash
rm -rf ~/.kiro/skills/autonomous-pipeline     # 移除 skill
# 引擎脚本就在克隆的仓库里, 删仓库目录即可; 不写任何全局状态(除上面这个 skill)
```
