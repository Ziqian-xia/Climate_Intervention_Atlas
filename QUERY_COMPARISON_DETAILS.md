# 三次运行的查询详细对比

**测试时间**: 2026-03-23 23:28-23:30
**相同输入**: "I am interested in research papers on the impacts of weather forecasts interventions on the temperature–health relationship..."

---

## Run 1 - OpenAlex Query (381 results)

### Pulse扩展的关键词 (36个)

```
weather forecast, weather forecasting, meteorological forecast, temperature forecast, heat forecast,
cooling center, cooling centre, cooling shelter, heat shelter, heat refuge, cooling intervention, heat intervention,
temperature-mortality, temperature-health, heat-mortality, heat-health, extreme heat, heatwave, heat wave,
randomized, randomised, quasi-experimental, natural experiment, controlled trial, causal inference, intervention study,
experimental design, plausibly exogenous, random assignment, treatment assignment,
mortality, morbidity, health outcomes, emergency department, hospitalization, hospitalisation
```

### Refiner最终查询

```
("weather forecast" OR "meteorological forecast" OR "temperature forecast" OR "heat forecast"
OR "forecast-based" OR "early warning" OR "heat warning" OR "temperature prediction" OR "weather prediction")

AND

("cooling center" OR "cooling centre" OR "cooling shelter" OR "heat shelter" OR "heat refuge"
OR "cooling intervention" OR "heat intervention" OR "public cooling" OR "community cooling"
OR "heat relief" OR "cooling service" OR "heat mitigation" OR "cooling program" OR "cooling programme")

AND

("temperature-mortality" OR "temperature-health" OR "heat-mortality" OR "heat-health"
OR "extreme heat" OR "heatwave" OR "heat wave" OR "thermal stress" OR "heat exposure" OR "temperature exposure")

AND

("randomized" OR "randomised" OR "quasi-experimental" OR "natural experiment" OR "controlled trial"
OR "causal inference" OR "intervention study" OR "experimental design" OR "plausibly exogenous"
OR "difference-in-difference" OR "regression discontinuity" OR "instrumental variable")

AND

("mortality" OR "morbidity" OR "health outcomes" OR "emergency department" OR "hospitalization"
OR "hospital admission" OR "emergency visit" OR "healthcare utilization" OR "healthcare utilisation")
```

**关键特征**:
- ✅ 包含 `"forecast-based"`, `"early warning"`, `"heat warning"`
- ✅ 包含 `"weather prediction"`, `"temperature prediction"`
- ✅ 添加了 `"public cooling"`, `"community cooling"`, `"heat relief"`
- ✅ 包含 `"difference-in-difference"`, `"regression discontinuity"`, `"instrumental variable"`

**查询长度**: 1190 chars
**结果数量**: **381**

---

## Run 2 - OpenAlex Query (1,313 results)

### Pulse扩展的关键词 (25个)

```
weather forecast, weather forecasting, meteorological forecast, temperature forecast, heat forecast,
early warning system, heat warning, cooling center, cooling centre, cooling shelter, heat refuge,
temperature-health, heat-health, extreme heat, heatwave, heat wave,
randomized controlled trial, quasi-experimental, natural experiment, causal inference, experimental design,
mortality, morbidity, health outcomes, hospitalization
```

**与Run 1的差异**:
- ❌ **少了11个关键词**（25 vs 36）
- ✅ 直接包含 `"early warning system"` (而非 "early warning")
- ❌ 缺少 `"heat shelter"`, `"cooling intervention"`, `"heat intervention"`
- ❌ 缺少 `"random assignment"`, `"treatment assignment"`
- ❌ 缺少 `"emergency department"`, `"hospital admission"`

### Refiner最终查询

```
("weather forecast" OR "meteorological forecast" OR "temperature forecast" OR "heat forecast"
OR "early warning system" OR "heat warning" OR "cooling center" OR "cooling centre"
OR "cooling shelter" OR "heat refuge")

AND

("temperature-health" OR "heat-health" OR "extreme heat" OR "heatwave" OR "heat wave")

AND

("randomized controlled trial" OR "quasi-experimental" OR "natural experiment" OR "causal inference"
OR "experimental design" OR "intervention study" OR "difference-in-differences" OR "regression discontinuity")

AND

("mortality" OR "morbidity" OR "health outcomes" OR "hospitalization")
```

**关键特征**:
- ⚠️  **查询结构只有4组AND** (Run 1有5组)
- ⚠️  **cooling相关术语混入了forecast组** (结构不同)
- ✅ 使用通配符 `"forecast*"` (在PubMed查询中)
- ✅ 包含 `"difference-in-differences"` (复数形式)
- ❌ 缺少很多同义词

**查询长度**: 1167 chars
**结果数量**: **1,313** (最多！)

**为什么返回最多**:
- 查询更简洁，限制条件更少
- 某些术语的组合方式产生了更宽的匹配

---

## Run 3 - OpenAlex Query (97 results)

### Pulse扩展的关键词 (40个)

```
weather forecast, weather prediction, meteorological forecast, temperature forecast, heat forecast,
forecast-based intervention, early warning system, heat warning, heat alert,
cooling center, cooling centre, cooling shelter, heat shelter, heat refuge, refuge center,
cooling intervention, heat intervention, heat mitigation, heat adaptation,
temperature-health, temperature-mortality, heat-health, heat-mortality, extreme heat, heatwave, heat wave,
randomized controlled trial, randomised controlled trial, quasi-experimental, natural experiment,
causal inference, causal analysis, intervention study, experimental design, plausibly exogenous,
difference-in-differences, instrumental variable, regression discontinuity,
mortality, morbidity, health outcomes, hospitalization
```

**与Run 1/2的差异**:
- ✅ **最多关键词**（40个）
- ✅ 包含 `"weather prediction"` (Run 1也有，Run 2没有)
- ✅ 包含 `"forecast-based intervention"` (更具体)
- ✅ 包含 `"heat alert"` (新增)
- ✅ 包含 `"refuge center"`, `"heat mitigation"`, `"heat adaptation"` (新增)
- ✅ 包含 `"causal analysis"` (新增)

### Refiner最终查询

```
("weather forecast" OR "weather prediction" OR "meteorological forecast" OR "temperature forecast"
OR "heat forecast" OR "early warning system" OR "heat warning" OR "heat alert")

AND

("cooling center" OR "cooling centre" OR "cooling shelter" OR "heat shelter" OR "heat refuge"
OR "refuge center" OR "cooling intervention" OR "heat intervention" OR "heat mitigation" OR "heat adaptation")

AND

("temperature-health" OR "temperature-mortality" OR "heat-health" OR "heat-mortality"
OR "extreme heat" OR "heatwave" OR "heat wave")

AND

("randomized controlled trial" OR "randomised controlled trial" OR "quasi-experimental"
OR "natural experiment" OR "causal inference" OR "causal analysis" OR "intervention study"
OR "experimental design" OR "plausibly exogenous" OR "difference-in-differences" OR "instrumental variable"
OR "regression discontinuity")

AND

("mortality" OR "morbidity" OR "health outcomes" OR "hospitalization")
```

**关键特征**:
- ✅ **最规范的5组AND结构**
- ✅ 关键词最丰富
- ✅ 包含 `"heat alert"` (可能过于具体)
- ✅ 包含 `"causal analysis"` (更学术)
- ❌ **但返回最少结果** (97)

**查询长度**: 1146 chars
**结果数量**: **97** (最少！)

**为什么返回最少**:
- 虽然关键词最多，但某些术语组合可能过于严格
- `"heat alert"` 这样的术语可能很少在文献中使用
- `"forecast-based intervention"` 可能过于具体

---

## 关键差异分析

### 1. 结构差异

| Run | AND组数 | 结构类型 | 结果 |
|-----|--------|---------|------|
| Run 1 | 5组 | ✅ 标准五概念 | 381 |
| Run 2 | 4组 | ⚠️ 简化结构 | 1,313 |
| Run 3 | 5组 | ✅ 标准五概念 | 97 |

**Run 2的结构异常**是导致其返回最多结果的原因之一。

### 2. 关键术语对比

| 术语类别 | Run 1 | Run 2 | Run 3 | 影响 |
|---------|-------|-------|-------|------|
| **Weather Forecast** ||||
| "weather prediction" | ✅ | ❌ | ✅ | 中等 |
| "forecast-based" | ✅ | ❌ | ❌ | 中等 |
| "forecast-based intervention" | ❌ | ❌ | ✅ | 高（过于具体） |
| "heat alert" | ❌ | ❌ | ✅ | 高（罕见术语） |
| **Cooling Interventions** ||||
| "public cooling" | ✅ | ❌ | ❌ | 低 |
| "community cooling" | ✅ | ❌ | ❌ | 低 |
| "heat relief" | ✅ | ❌ | ❌ | 低 |
| "heat mitigation" | ✅ | ❌ | ✅ | 中等 |
| "heat adaptation" | ❌ | ❌ | ✅ | 中等 |
| "refuge center" | ❌ | ❌ | ✅ | 低（罕见） |
| **Causal Methods** ||||
| "difference-in-difference" | ✅ | ❌ | ❌ | 低 |
| "difference-in-differences" | ❌ | ✅ | ✅ | 低 |
| "instrumental variable" | ✅ | ❌ | ✅ | 低 |
| "regression discontinuity" | ✅ | ✅ | ✅ | 低 |
| "causal analysis" | ❌ | ❌ | ✅ | 低 |
| **Health Outcomes** ||||
| "hospital admission" | ✅ | ❌ | ❌ | 低 |
| "emergency visit" | ✅ | ❌ | ❌ | 低 |
| "healthcare utilization" | ✅ | ❌ | ❌ | 低 |

### 3. 通配符使用对比

| 数据库 | Run 1 | Run 2 | Run 3 |
|-------|-------|-------|-------|
| **PubMed** | ❌ 不使用通配符 | ✅ 使用 `forecast*`, `heatwave*` | ❌ 不使用通配符 |

**Run 2在PubMed中使用通配符**，这可能解释了为什么它返回9条结果而其他两次返回0条。

### 4. 查询宽度评估

| Run | 宽度评估 | 原因 | 结果 |
|-----|---------|------|------|
| **Run 1** | 中等-宽 | 丰富的同义词，标准结构 | 381 |
| **Run 2** | **最宽** | 简化结构，关键词少但通用，使用通配符 | **1,313** |
| **Run 3** | **最窄** | 关键词多但某些过于具体（"heat alert", "forecast-based intervention"） | **97** |

---

## 为什么同样的prompt产生如此不同的结果？

### Pulse Agent的选择分支

**Run 1**:
- 选择 `"forecast-based"`, `"early warning"` (分开)
- 选择 `"weather prediction"`, `"temperature prediction"` (都选)

**Run 2**:
- 选择 `"early warning system"` (组合在一起)
- **没有**选择 `"weather prediction"`
- 关键词总数更少（25 vs 36）

**Run 3**:
- 选择 `"forecast-based intervention"` (更具体的组合)
- 选择 `"heat alert"` (罕见术语)
- 选择 `"causal analysis"` (学术术语)
- 关键词总数最多（40）

### Formulator Agent的结构决策

**Run 1**: 标准5组AND结构
**Run 2**: **异常的4组AND结构** - cooling terms混入forecast组
**Run 3**: 标准5组AND结构

### Refiner Agent的调整方向

**Run 1**: 添加了 `"public cooling"`, `"community cooling"`, `"heat relief"`
**Run 2**: 保持简洁，使用通配符
**Run 3**: 添加了 `"heat alert"`, `"refuge center"`, `"causal analysis"`

---

## 哪个查询是"最好的"？

### 按目标评估

| 目标 | 最佳查询 | 原因 |
|-----|---------|------|
| **最大召回率** | Run 2 (1,313) | 查询最宽松 |
| **精确度** | Run 3 (97) | 查询最严格 |
| **平衡** | Run 1 (381) | 中等宽度，标准结构 |

### 推荐策略

对于系统性综述：

1. **探索阶段**: 使用类似Run 2的查询（宽松，高召回率）
2. **精细筛选**: 在Phase 3使用Claude进行严格筛选
3. **或者**: 生成多个variation并合并结果

对于文献数量有限的主题：

1. **使用最宽的查询** (Run 2类型)
2. **手动审查所有结果**

对于高度成熟的研究领域：

1. **使用更严格的查询** (Run 3类型)
2. **聚焦于最相关的研究**

---

## 结论

### 三次运行的本质差异

1. **Pulse选择不同的关键词集** → 导致查询内容不同
2. **Formulator采用不同的结构** (特别是Run 2的4组vs 5组) → 导致查询宽度不同
3. **Refiner的调整方向不同** → 细微调整放大差异

### 关键insight

**Run 2返回最多不是因为它"更好"，而是因为**:
- 查询结构更简单（4组vs 5组）
- 某些限制条件缺失
- 在PubMed使用了通配符

**Run 3返回最少不是因为它"更差"，而是因为**:
- 包含了罕见/具体的术语（"heat alert", "forecast-based intervention"）
- 这些术语虽然准确，但在文献中出现频率低

### 用户应该知道什么

1. ✅ **每次运行Phase 1都会生成略微不同的查询** - 这是AI的正常行为
2. ✅ **结果数量差异来自查询差异，不是搜索引擎的问题**
3. ✅ **没有"唯一正确"的查询** - 不同策略适合不同目标
4. ✅ **建议生成2-3个查询变体，然后选择或合并**

---

## 推荐工作流程

### 步骤1: 生成多个变体
```
运行Phase 1三次 → 得到3个不同的查询策略
```

### 步骤2: 比较宽度
```
Run 1: 381 results  (中等)
Run 2: 1,313 results (宽松)
Run 3: 97 results    (严格)
```

### 步骤3: 选择策略
```
如果研究主题文献稀少 → 选择Run 2
如果研究主题文献丰富 → 选择Run 1或Run 3
如果不确定 → 选择Run 1 (平衡)
```

### 步骤4: 执行并筛选
```
Phase 2: 执行选定的查询
Phase 3: Claude严格筛选
→ 最终得到高质量、高相关性的文献集
```
