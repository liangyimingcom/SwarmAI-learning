---
inclusion: manual
---

# Pipeline Lessons (auto-cultivated)

> Each entry is dated. A lesson unreferenced for 90 days retires (Darwinian decay).

## run_6469c1bb · 实现一个 slugify 工具函数把任意字符串转为 URL slug · 2026-07-11
- ✅ Gate 2 fresh-context 子 agent 抓到 3 个 builder 盲点(长度上限/None/ß折叠)，全部收敛
- ⚠️ 首版 slugify 无长度上限——归为可复用 RP：纯函数产出无界字符串须设 cap
- 🚧 new gate proposed: RP-mc1: 字符串生成函数缺长度上限

## run_28c9f294 · 实现 pipeline/confidence_score.py：由 run 的门控通过数计算 1-12 交付信心分+分项拆解 · 2026-07-11
- ✅ Gate2 fresh子agent抓到 HIGH阈值下侧off-by-one + unresolved参数bool守卫不对称，均1轮收敛
- ⚠️ 首版含2处test-theater: test_ac4声称测clamp实为死代码, HIGH阈值只钉上侧——阈值须双侧钉死且mutation-proof
- 🚧 new gate proposed: RP-mc2: 阈值/分级判定测试须双侧边界钉死+mutation-proof, 防御性不可达代码勿伪称覆盖
