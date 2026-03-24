# 用户研究主题的数据库表现分析

**研究主题**: "weather forecast interventions on cooling centers and temperature-health relationship with causal research designs"

**核心关键词**: weather forecast, cooling centers, temperature, health, causal, quasi-experimental

---

## 数据库搜索结果对比

### 测试1: 完整主题搜索

**查询**: "weather forecast cooling centers temperature health"

| 数据库 | 查询方式 | 结果数量 | 说明 |
|--------|---------|---------|------|
| **OpenAlex** | `abstract.search` | **19** | 摘要中包含这些词 |
| **PubMed** | OR逻辑 `[Title/Abstract]` | 313 | 任何一个词组出现 |
| **Scopus** | OR逻辑 `TITLE-ABS-KEY` | 142,574 | 任何一个词出现（太宽） |

**问题**: 不同的查询逻辑导致结果差异巨大

---

## 关键发现：Cooling Centers是小众研究领域

### "Cooling Centers"单独搜索

| 数据库 | 查询 | 结果 |
|--------|------|------|
| **Scopus** | `TITLE-ABS-KEY("cooling centers" OR "cooling center" OR "heat relief center")` | **188** |
| **PubMed** | `"cooling centers"[Title/Abstract] OR "cooling center"[Title/Abstract]` | **56** |
| **OpenAlex** | 推测（基于19条包含更多词的结果） | ~50-100 |

**结论**: "Cooling centers"本身就是**非常小众**的研究主题！

### 进一步细化搜索

| 查询策略 | Scopus | PubMed | 说明 |
|---------|--------|--------|------|
| **所有词都要有 (AND)** | **1** | 未测试 | 太严格 |
| **Cooling centers + health** | 未测试 | **14** | 更合理 |
| **Weather/heat + intervention + health** | 未测试 | **10** | 相关但不同角度 |

---

## 为什么结果这么少？

### 1. 研究主题的特殊性

**你的研究关注的是**:
- ❌ **不是**: 一般性的气候变化与健康
- ❌ **不是**: 温度与健康的相关性研究
- ✅ **是**: 特定的公共卫生**干预措施**（cooling centers）
- ✅ **是**: 天气预报系统的**干预效果**
- ✅ **是**: **因果研究设计**（实验/准实验）

### 2. 为什么文献少？

1. **Cooling centers不常见**:
   - 主要在北美（美国、加拿大）
   - 欧洲较少使用
   - 发展中国家几乎没有

2. **因果研究设计难**:
   - 需要随机/准随机分配
   - Cooling centers是公共设施，难以随机化
   - 大多数研究是观察性的

3. **交叉学科**:
   - 涉及气象学（weather forecast）
   - 公共卫生（health outcomes）
   - 城市规划（cooling centers location）
   - 因果推断方法（quasi-experimental）

4. **相对较新的研究领域**:
   - Cooling centers作为热浪应对策略
   - 近10-15年才逐渐受到关注

---

## 真实的文献数量估计

基于测试结果，**合理的预期**：

### 核心相关文献（直接相关）

| 范围 | 估计数量 |
|------|---------|
| **Cooling centers + health outcomes** | 50-100篇 |
| **其中有因果设计的** | 10-30篇 |
| **结合weather forecast干预的** | 5-20篇 |

### 扩展相关文献（间接相关）

| 范围 | 估计数量 |
|------|---------|
| **Heat warning systems + health** | 100-300篇 |
| **Extreme heat interventions** | 300-500篇 |
| **Temperature-health with causal designs** | 500-1000篇 |

---

## 为什么OpenAlex只有19条？

### OpenAlex的搜索逻辑

OpenAlex使用 `abstract.search`，要求：
- 所有关键词都在**同一个摘要**中出现
- 类似于AND逻辑

**查询**: "weather forecast cooling centers temperature health"

**意味着摘要必须包含**:
- ✅ "weather" 或 "forecast"
- ✅ "cooling" 或 "centers"
- ✅ "temperature"
- ✅ "health"

**结果**: 19篇论文的摘要同时提到了这些概念

---

## 建议的搜索策略

### 策略1: 核心搜索（严格，精确）

**适用场景**: 找最直接相关的核心文献

**建议查询**:
- **OpenAlex**: `abstract.search:cooling centers health` → 预期10-50条
- **PubMed**: `("cooling center"[Title/Abstract] OR "cooling shelter"[Title/Abstract]) AND "health"[Title/Abstract]` → 预期10-20条
- **Scopus**: `TITLE-ABS-KEY("cooling center" OR "cooling shelter") AND TITLE-ABS-KEY("health")` → 预期20-100条

### 策略2: 扩展搜索（宽松，覆盖面广）

**适用场景**: 找所有可能相关的文献

**建议查询**:
- **OpenAlex**: `abstract.search:heat warning intervention health` → 预期100-500条
- **PubMed**: `("heat warning"[Title/Abstract] OR "extreme heat"[Title/Abstract]) AND "intervention"[Title/Abstract] AND "health"[Title/Abstract]` → 预期100-300条
- **Scopus**: `TITLE-ABS-KEY(("heat wave" OR "extreme heat") AND ("intervention" OR "adaptation") AND "health")` → 预期500-2000条

### 策略3: 多阶段搜索（推荐）

**第一阶段**: 核心搜索
- 聚焦于 "cooling centers" + "health"
- 预期: 50-100篇核心文献

**第二阶段**: 相关概念搜索
- "heat warning systems"
- "extreme heat interventions"
- "heat action plans"
- 预期: 再增加200-500篇

**第三阶段**: 因果设计筛选（Phase 3）
- 使用Claude筛选出有因果设计的论文
- 预期: 最终保留50-200篇

---

## Phase 1 Agent生成的查询是什么？

建议检查：
1. **Phase 1生成的实际查询字符串是什么？**
2. **是否包含了同义词？**
   - Cooling centers = cooling shelters = heat relief centers = respite centers
   - Weather forecast = heat warning = heat alert = early warning system
3. **Boolean逻辑是什么？**
   - AND vs OR
   - 括号分组

---

## 三个数据库的合理预期

### 如果使用合理的查询策略

**核心主题**: Cooling centers + health + interventions

| 数据库 | 预期结果数量 | 原因 |
|--------|-------------|------|
| **OpenAlex** | **100-500** | 全学科，包含政策、规划等 |
| **Scopus** | **50-200** | 覆盖STM+社科，但不如OpenAlex全 |
| **PubMed** | **20-100** | 仅生物医学，最窄 |

**排序**: OpenAlex > Scopus > PubMed ✅ （符合预期）

### 如果扩展到相关主题

**扩展主题**: Heat interventions + health + causal designs

| 数据库 | 预期结果数量 |
|--------|-------------|
| **OpenAlex** | **1,000-5,000** |
| **Scopus** | **500-2,000** |
| **PubMed** | **300-1,000** |

---

## 实际操作建议

### 短期（立即可做）

1. **检查Phase 1生成的查询**
   - 确保包含同义词
   - 确保Boolean逻辑合理（不要太严格的AND）

2. **调整查询广度**
   - 如果结果太少（<100），扩大到 "heat interventions"
   - 如果结果太多（>5000），聚焦于 "cooling centers"

3. **利用Phase 3 Claude筛选**
   - 即使Phase 2返回1000-2000篇
   - Claude可以筛选出真正有因果设计的

### 中期（后续优化）

1. **多概念搜索**
   - 分别搜索 "cooling centers", "heat warning", "heat action plans"
   - Phase 2合并结果
   - Phase 3统一筛选

2. **灵活的查询生成**
   - 让Phase 1 Agent根据主题专业性调整查询宽度
   - 非常专业的主题 → 使用更宽泛的同义词
   - 常见主题 → 可以更精确

3. **数据库特定优化**
   - OpenAlex: 专注于跨学科视角
   - PubMed: 专注于健康结果
   - Scopus: 平衡学科覆盖

---

## 总结

### 当前状态

✅ **OpenAlex: 19条**
- 这是合理的
- 搜索逻辑：摘要中同时包含所有关键词
- 对于如此专业的主题，这个数量是正常的

⚠️ **需要注意的问题**:
- "Cooling centers"本身就是小众研究领域（全球只有100-200篇相关文献）
- 加上"因果设计"要求，核心文献可能只有10-50篇
- 这不是数据库问题，而是研究领域的现实

### 建议

1. **扩大Phase 1的查询范围**
   - 包含更多同义词
   - 包含相关概念（heat warning systems, heat action plans）

2. **依靠Phase 3 Claude筛选**
   - Phase 2可以返回500-2000篇相关文献
   - Phase 3筛选出真正符合因果设计要求的

3. **预期最终结果**
   - Phase 2: 500-2000篇（扩展搜索）
   - Phase 3: 50-200篇（Claude筛选后）
   - Phase 4: 30-100篇（获取全文后）
   - Phase 5: 20-50篇（最终分析）

**关键**: 你的研究主题非常专业，小样本量是正常的。质量比数量更重要！
