# 查询稳健性分析总结报告

**日期**: 2026-03-25
**配置**: 20个query variations，仅OpenAlex数据库，下载全部结果（DOI only）

---

## 🎯 核心发现

### 1. 极高的查询变异性

**统计数据**:
- **变异系数 (CV)**: 378.6% ⚠️ **极高！**
- **最小结果**: 9篇论文
- **最大结果**: 87,884篇论文
- **极值比**: 9,765:1（最大是最小的9,765倍！）
- **平均值**: 5,148篇
- **中位数**: 499篇
- **标准差**: 19,492

**结论**: 当前的prompt和4-agent系统产生的查询**极不稳定**，不同variation之间的结果数量差异巨大。

---

## 📊 术语敏感性分析

### TOP 10 扩大结果的术语 (EXPANDING - 应避免单独使用)

这些通用方法学术语会导致结果暴增，因为它们适用于所有学科的因果推断研究：

| 术语 | 增加结果数 | 百分比变化 |
|------|-----------|-----------|
| discontinuity threshold | +87,089 | +10,968% |
| event study design | +87,089 | +10,968% |
| fixed effects | +87,089 | +10,968% |
| endogeneity | +87,089 | +10,968% |
| parallel trends | +87,089 | +10,968% |
| matching estimator | +87,089 | +10,968% |
| identification strategy | +87,089 | +10,968% |
| diff-in-diff | +87,089 | +10,968% |
| exogenous variation | +87,089 | +10,968% |
| treatment effect | +22,247 | +3,183% |

**问题**: 这些术语在**没有健康/热浪干预约束**的情况下会检索到经济学、教育学、环境科学等所有领域的因果推断论文。

### TOP 10 精准化结果的术语 (RESTRICTING - 核心术语)

这些具体的健康干预术语能有效限定研究范围：

| 术语 | 减少结果数 | 百分比变化 |
|------|-----------|-----------|
| excess mortality | -43,891 | -98.3% |
| heat action plan | -28,637 | -97.1% |
| heat-related mortality | -18,049 | -96.6% |
| heat warning system | -11,046 | -93.8% |
| heat-related death | -11,003 | -93.6% |
| heat alert system | -8,304 | -93.5% |
| cardiovascular mortality | -7,656 | -93.2% |
| heat early warning | -7,347 | -90.8% |
| heat stroke | -6,710 | -85.7% |
| cooling center | -6,687 | -93.5% |

**优势**: 这些术语精准定位到目标研究领域（热浪健康干预）。

---

## 🔍 问题诊断

### Variation 2的异常（87,884篇）

**Query内容**:
```
("causal inference" OR "quasi-experimental" OR "natural experiment" OR "exogenous variation")
AND ("difference-in-differences" OR "diff-in-diff" OR ...)
AND ("policy evaluation" OR "program evaluation" OR ...)
```

**问题**:
- **缺少健康干预术语**：query中完全没有"heat warning", "heat mortality", "cooling center"等关键词
- **仅包含方法学术语**：只有因果推断方法，没有研究对象的限定
- **结果**: 检索到**所有学科**的因果推断研究（经济学、教育、环境等），而非特定于热浪健康干预

### Variation 8的极端精确（9篇）

可能的原因：
- 过多的AND操作符
- 术语组合过于具体
- 限制条件过严

---

## 💡 核心问题

### 1. Agent系统的不稳定性

4个Agent（Pulse → Formulator → Sentinel → Refiner）在以下方面表现不稳定：

**Pulse Agent (关键词扩展)**:
- ✅ 能够生成多样的同义词
- ❌ 不同variation之间的关键词选择差异过大
- ❌ 有时会**丢失核心概念**（如Variation 2缺少所有健康干预术语）

**Formulator Agent (布尔查询构建)**:
- ✅ 能够生成语法正确的Boolean查询
- ❌ **概念分组不一致**：有些variation将3个概念（干预+结果+方法）都包含，有些只包含1-2个
- ❌ 逻辑结构不稳定

**Sentinel Agent (质量控制)**:
- ❌ **未能检测到缺失的核心概念**（应该发现Variation 2缺少健康术语）
- ❌ 质量检查标准不够严格

**Refiner Agent (最终修订)**:
- ❌ **未能修复关键缺陷**（应该补充缺失的健康干预术语）

### 2. 根本原因

**Prompt结构问题**:
当前的研究问题描述虽然清晰，但LLM在keyword expansion阶段容易：
1. 过度关注某一个概念（如方法学）而忽略其他概念（干预、结果）
2. 不同variation之间的关键词平衡性差异大
3. 缺乏**强制性约束**确保所有核心概念都被包含

---

## 📋 推荐解决方案

### 方案 1: 修改Prompt结构（短期，快速）

在研究问题中**明确标记三个必需概念**：

```markdown
MANDATORY CONCEPTS (ALL must be included in every query):

1. **INTERVENTION** (at least 3 terms required):
   - Heat warning systems
   - Heat-health action plans
   - Cooling center programs
   - Public health advisories
   - Temperature forecast-based interventions

2. **OUTCOME** (at least 3 terms required):
   - Temperature-related mortality
   - Heat-related morbidity
   - Cardiovascular impacts
   - Respiratory impacts
   - Emergency department visits

3. **STUDY DESIGN** (at least 2 terms required):
   - Randomized controlled trials
   - Quasi-experimental designs
   - Natural experiments
   - Causal inference methods
```

### 方案 2: 增强Sentinel Agent检查（中期）

修改Sentinel Agent的检查规则：
1. **必须检查每个concept group的coverage**
2. **如果任何group缺失或覆盖不足 → 标记为CRITICAL ERROR**
3. **强制Refiner补充缺失的terms**

### 方案 3: 混合策略（推荐）

**预定义核心术语 + LLM扩展**:
1. **手动定义"最小必需术语集"**（每个概念3-5个核心术语）
2. Pulse Agent负责**扩展同义词和变体**
3. Sentinel检查确保**核心术语集100%出现**
4. 允许变化的部分是**同义词选择和逻辑结构优化**

这种方式既保持了variation的多样性，又避免了核心概念缺失的灾难性错误。

---

## 🎯 最佳Query选择建议

基于当前20个variations的分析，推荐使用的variations：

### 推荐 Top 3:
1. **Variation 1** (219篇) - 平衡的三概念query，结果数量合理
2. **Variation 4** (511篇) - 较宽但仍在控制范围内
3. **Variation 10** (2,475篇) - 如果需要更高召回率

### 不推荐:
- **Variation 2** (87,884篇) - 过于宽泛，缺少健康干预约束
- **Variation 8** (9篇) - 过于严格，可能遗漏相关研究

### 折中方案:
可以考虑**ensemble approach**：
- 使用3-5个variation的**并集**
- 选择结果数量在200-1,500之间的variations
- 去重后送入Phase 3 (Claude筛选)

---

## 📈 统计数据详细表

### 所有20个Variations的结果分布

| Variation | Meta Count | 评价 |
|-----------|-----------|------|
| 1 | 219 | ✅ 优秀 |
| 2 | 87,884 | ❌ 过宽 |
| 3 | 3,267 | ⚠️ 较宽 |
| 4 | 511 | ✅ 良好 |
| 5 | 678 | ✅ 良好 |
| 6 | 189 | ✅ 优秀 |
| 7 | 59 | ⚠️ 较窄 |
| 8 | 9 | ❌ 过窄 |
| 9 | 218 | ✅ 优秀 |
| 10 | 2,475 | ⚠️ 较宽 |
| 11 | 385 | ✅ 良好 |
| 12 | 487 | ✅ 良好 |
| 13 | 1,659 | ✅ 良好 |
| 14 | 578 | ✅ 良好 |
| 15 | 1,021 | ✅ 良好 |
| 16 | 280 | ✅ 优秀 |
| 17 | 1,177 | ✅ 良好 |
| 18 | 312 | ✅ 优秀 |
| 19 | 1,418 | ✅ 良好 |
| 20 | 145 | ✅ 优秀 |

**建议的"黄金区间"**: 150-1,500篇论文

---

## 🚀 下一步行动

### 立即行动:
1. ✅ **已完成**: 敏感性分析揭示了问题根源
2. ⭐ **选择最佳query**: 使用Variation 1或4-5个优秀variations的并集
3. 🔧 **修复Prompt**: 增加"MANDATORY CONCEPTS"约束

### 中期优化:
1. 重新运行20-variation测试（使用改进的prompt）
2. 比较改进前后的CV值（目标：降至<50%）
3. 验证所有variations都包含三个核心概念

### 长期改进:
1. 开发Sentinel Agent的自动化检查规则
2. 创建"核心术语库"作为质量基准
3. 实施ensemble query策略的自动化pipeline

---

## 📄 附件

详细分析文件保存在:
```
robustness_test_results_20260325_194108/analysis/openalex/
├── result_statistics.json      # 统计摘要
├── term_frequency.csv          # 术语频率矩阵
├── query_features.csv          # Query特征
├── correlations.csv            # 特征相关性
└── impact_rankings.csv         # 术语影响排名（完整版）
```

---

**分析完成**: 2026-03-25
**总结**: 当前系统变异性过高(CV=378.6%)，主要由于LLM keyword expansion的不稳定性。建议采用混合策略：预定义核心术语 + LLM灵活扩展。
