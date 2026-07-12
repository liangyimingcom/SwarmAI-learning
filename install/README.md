# install/ — 一键导入到新 MeshClaw 环境

把 SwarmAI 13 引擎移植装到**另一台电脑的新 MeshClaw 环境**。

## 一键导入

```bash
git clone https://github.com/liangyimingcom/SwarmAI-learning.git
cd SwarmAI-learning
bash install/install.sh          # 装 skill + 自检 5 引擎
```

看到 `SELFCHECK: PASS ✅` 即成功。然后读 [`QUICKSTART.md`](QUICKSTART.md) 上手。

## 本目录文件

| 文件 | 作用 |
|------|------|
| [`install.sh`](install.sh) | 一键安装：装 `autonomous-pipeline` skill 到 `~/.kiro/skills/` + 跑自检 |
| [`selfcheck.sh`](selfcheck.sh) | 隔离环境自检全部 5 引擎（可单独重跑：`bash install/selfcheck.sh`）|
| [`QUICKSTART.md`](QUICKSTART.md) | 新环境快速使用指南（用法 A 自然语言触发 / 用法 B CLI / 接项目 / CodeLens / 卸载）|

## 设计要点

- **纯标准库**：所有引擎只用 Python 3.10+ 标准库，**无需 pip install / 无外部依赖**。
- **不打包密钥**：仓库内无任何 token；CodeLens token 需新环境自备（可选功能）。
- **不写全局状态**：除把 skill 拷到 `~/.kiro/skills/` 外，引擎脚本在克隆目录内原地运行，产物默认落 `pipeline/.artifacts/`（可用 `PIPELINE_ARTIFACTS_ROOT` 改到目标项目内）。
- **幂等**：重复跑 `install.sh` 会覆盖旧 skill 副本，安全。
