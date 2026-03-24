# Query Variations功能说明

**实施时间**: 2026-03-23
**版本**: v1.0

---

## 功能概述 🎯

Query Variations功能允许系统自动生成5个不同的查询变体，对每个变体分别搜索，然后合并去重所有结果，以最大化文献覆盖率。

### 为什么需要这个功能？

根据稳定性测试分析，Phase 1的4-agent团队每次生成的查询都略有不同，即使使用相同的prompt。这是Claude AI的固有特性，导致：

- **相同prompt → 不同查询 → 不同结果数量**
- 例如：3次运行得到 381、1,313、97 条结果（OpenAlex）

**解决方案**：生成多个查询变体并合并，确保：
1. ✅ **最大化召回率** - 不同变体捕获不同的关键词组合
2. ✅ **去除重复** - 自动按DOI/PMID/EID去重
3. ✅ **可重复性** - 保存所有查询供后续重用

---

## 核心特性 ⭐

### 1. 自动生成5个查询变体

**默认配置**:
- ✅ **Enable Query Variations**: 默认开启
- ✅ **Number of Variations**: 5个
- ✅ **Auto-search all variations**: 默认开启

**工作流程**:
```
Phase 1: 生成5个查询变体
  ↓
  Variation 1: [keywords A, B, C, ...]
  Variation 2: [keywords A, D, E, ...]
  Variation 3: [keywords B, F, G, ...]
  Variation 4: [keywords C, H, I, ...]
  Variation 5: [keywords D, J, K, ...]
```

### 2. Phase 2自动搜索所有变体

**执行流程**:
```
For each database (OpenAlex, PubMed, Scopus):
  ├─ Search Variation 1
  ├─ Search Variation 2
  ├─ Search Variation 3
  ├─ Search Variation 4
  └─ Search Variation 5
```

**进度显示**:
- 显示总任务数：`数据库数 × 5`
- 例如：3个数据库 × 5个变体 = 15个搜索任务

### 3. 自动合并去重

**去重策略**:

| 数据库 | 去重字段 | 备用字段 |
|--------|---------|---------|
| **OpenAlex** | `openalex_id` | `doi` |
| **PubMed** | `pmid` | `doi` |
| **Scopus** | `eid` | `doi` |

**合并流程**:
```
Variation 1: 381 results
Variation 2: 1,313 results
Variation 3: 97 results
Variation 4: 542 results
Variation 5: 728 results
────────────────────────────
Total:       3,061 results (before dedup)
Duplicates:  -845 results (removed)
────────────────────────────
Final:       2,216 unique results ✅
```

### 4. 保存和加载查询

**保存功能**:
- 📥 **Save All Queries** 按钮
- 保存格式：JSON文件
- 包含内容：
  - 原始topic
  - 生成时间
  - 所有5个变体的完整信息（keywords, queries, reasoning）

**加载功能**:
- 📤 **Load Saved Queries** 文件上传
- 支持加载之前保存的查询
- 自动恢复所有变体和状态

---

## 用户界面变化 🖥️

### Phase 1: Query Generation

**新增提示**:
```
ℹ️ Query Variations Mode: 5 query variations will be generated.
   Each variation explores different keyword combinations.
```

**变体选择器**:
```
🔄 Query Variations
Generated 5 different query variations. Select one to view details:
[Dropdown: Variation #1, Variation #2, ..., Variation #5]
```

**保存/加载区域**:
```
💾 Save & Load Queries

[📥 Save All Queries]  [📤 Load Saved Queries]
```

### Phase 2: Metadata Search

**新增提示**:
```
📊 Query Variations Mode: 5 query variations will be searched for each database.
   Results will be automatically merged and deduplicated by DOI/PMID/EID.
```

**执行状态**:
```
🚀 Execute Search
Progress: ████████████████░░░░  12/15
Searching OPENALEX (Variation #3)...
```

**结果显示**:
```
📁 OPENALEX Results
✅ Status: merged_success

Variations Searched: 5
Total Retrieved:     3,061
Duplicates Removed:  845

ℹ️ Final Unique Results: 2,216 papers after deduplication
```

---

## 技术实现细节 🔧

### 1. 查询生成 (`modules/m1_query_gen.py`)

**`variation_seed` 参数**:
```python
team.generate_queries(topic, variation_seed=1)  # Variation 1
team.generate_queries(topic, variation_seed=2)  # Variation 2
# ...
```

每个`variation_seed`会影响：
- Pulse agent的关键词选择
- Formulator的Boolean结构
- Sentinel的验证结果
- Refiner的调整方向

### 2. 搜索执行 (`app.py`)

**嵌套循环搜索**:
```python
for var_idx in range(5):  # 5 variations
    for db in ["openalex", "pubmed", "scopus"]:
        query = get_query_for_variation(var_idx, db)
        result = execute_search(db, query)
        store_result(db, var_idx, result)
```

### 3. 合并去重 (`_merge_database_variations()`)

**步骤**:
1. 加载所有variation的CSV文件
2. 合并为单个DataFrame
3. 按ID列去重（`drop_duplicates`）
4. 保存合并后的CSV/JSONL
5. 生成统计summary

**关键代码**:
```python
def _merge_database_variations(db_name, variations, base_out_dir):
    # 1. Collect all DataFrames
    all_dfs = []
    for var in variations:
        df = pd.read_csv(var['output_files']['summary_csv'])
        df['source_variation'] = var['variation_idx']
        all_dfs.append(df)

    # 2. Merge
    merged_df = pd.concat(all_dfs, ignore_index=True)

    # 3. Deduplicate by ID
    id_column = {"openalex": "openalex_id", "pubmed": "pmid", "scopus": "eid"}[db_name]
    merged_df = merged_df.drop_duplicates(subset=[id_column], keep='first')

    # 4. Save
    merged_df.to_csv(f"{base_out_dir}/{db_name}/works_summary.csv")

    return {
        "results_count": len(merged_df),
        "duplicates_removed": before_count - len(merged_df),
        "num_variations": len(variations)
    }
```

---

## 文件结构 📂

### Phase 2输出目录结构

**多变体模式** (5 variations):
```
search_results_20260323_235959/
├── openalex/
│   ├── variation_1/
│   │   ├── works_summary.csv
│   │   ├── works_full.jsonl
│   │   └── run_summary.json
│   ├── variation_2/
│   ├── variation_3/
│   ├── variation_4/
│   ├── variation_5/
│   ├── works_summary.csv         ← 合并去重后的结果
│   ├── works_full.jsonl          ← 合并去重后的结果
│   └── run_summary.json          ← 包含合并统计信息
├── pubmed/
│   └── (同上结构)
└── scopus/
    └── (同上结构)
```

**单查询模式** (1 query):
```
search_results_20260323_235959/
├── openalex/
│   ├── works_summary.csv
│   ├── works_full.jsonl
│   └── run_summary.json
├── pubmed/
└── scopus/
```

### 保存的查询文件格式

**`queries_20260323_235959.json`**:
```json
{
  "topic": "I am interested in research papers on...",
  "generated_at": "2026-03-23T23:59:59",
  "num_variations": 5,
  "variations": [
    {
      "variation_seed": 1,
      "pulse_keywords": ["weather forecast", "heat warning", ...],
      "pulse_reasoning": "Expansion includes...",
      "queries": {
        "elsevier_query": "TITLE-ABS-KEY(...)",
        "pubmed_query": "(...)[Title/Abstract]",
        "openalex_query": "(...)"
      },
      "formulator_reasoning": "...",
      "sentinel_validation": "...",
      "refiner_notes": "..."
    },
    {
      "variation_seed": 2,
      ...
    },
    ...
  ]
}
```

---

## 使用场景 🎬

### 场景1: 最大化文献覆盖（推荐）

**目标**: 确保不遗漏任何相关文献

**步骤**:
1. ✅ 保持默认设置（5 variations, auto-search）
2. ✅ 点击 "🚀 Generate Queries"
3. ✅ 审查生成的5个变体（可选）
4. ✅ 点击 "🟢 Approve & Proceed to Phase 2"
5. ✅ 选择所有数据库（OpenAlex, PubMed, Scopus）
6. ✅ 点击 "🚀 Execute Search"
7. ✅ 等待15个搜索任务完成
8. ✅ 查看合并去重后的结果

**预期结果**:
- 更全面的文献覆盖
- 更高的召回率
- 自动去重保证质量

### 场景2: 保存查询供后续使用

**目标**: 记录确切的检索策略（系统性综述要求）

**步骤**:
1. ✅ 生成5个变体
2. ✅ 点击 "📥 Save All Queries"
3. ✅ 下载 `queries_YYYYMMDD_HHMMSS.json`
4. ✅ 执行搜索（或稍后执行）
5. ✅ 将JSON文件附在研究报告中

**用途**:
- 满足系统性综述的可重复性要求
- 记录完整的检索策略
- 与合作者分享查询

### 场景3: 加载之前保存的查询

**目标**: 重用之前生成的查询，确保完全可重复

**步骤**:
1. ✅ 点击 "📤 Load Saved Queries"
2. ✅ 上传之前保存的JSON文件
3. ✅ 系统自动恢复所有5个变体
4. ✅ 直接进入Phase 2搜索

**优势**:
- 完全可重复
- 无需重新生成查询
- 节省API调用成本

### 场景4: 单查询模式（不使用variations）

**目标**: 快速测试或已有明确查询

**步骤**:
1. ✅ 取消勾选 "Enable Query Variations"
2. ✅ 生成单个查询
3. ✅ 手动编辑调整
4. ✅ 执行搜索（只搜索1次）

**适用情况**:
- 已有经过验证的查询
- 快速pilot search
- 文献数量有限的领域

---

## 性能影响 ⚡

### API调用成本

| 模式 | Phase 1调用次数 | Phase 2调用次数 | 总成本估算 |
|------|---------------|---------------|-----------|
| **单查询** | 4 agents × 1 = 4 | 1 × 3 databases = 3 | $0.10-0.50 |
| **5 variations** | 4 agents × 5 = 20 | 5 × 3 databases = 15 | $0.50-2.50 |

**成本说明**:
- Phase 1 (Claude): ~$0.05-0.10 per query set
- Phase 2 (搜索APIs): 免费或已有API key

### 时间消耗

| 阶段 | 单查询 | 5 Variations | 增加时间 |
|------|--------|-------------|---------|
| **Phase 1** | ~40s | ~200s (3-4分钟) | +160s |
| **Phase 2** | ~30s | ~150s (2-3分钟) | +120s |
| **合并去重** | N/A | ~10s | +10s |
| **总计** | ~1-2分钟 | ~6-8分钟 | +5-6分钟 |

**优化建议**:
- ✅ 5 variations适合最终的系统性综述
- ⚠️ pilot search可以用1-2 variations
- ✅ 可以边生成边审查，时间感知更短

---

## 常见问题 ❓

### Q1: 为什么默认是5个variations而不是3个？

**A**: 根据稳定性测试，3次运行得到的结果数量跨度很大（97-1,313）。5个variations可以更好地覆盖这个范围，确保不遗漏重要文献。

### Q2: 去重逻辑是否会删除不同版本的论文？

**A**: 不会。去重只基于严格的ID匹配（DOI/PMID/EID）。如果同一论文在不同variation中被检索到（因为关键词不同），会被识别为重复并只保留一份。这正是我们想要的行为。

### Q3: 如果5个variations都返回很少结果怎么办？

**A**: 这可能说明：
1. 查询过于严格（考虑放宽条件）
2. 研究主题确实文献稀少（这是合理的）
3. 数据库选择不匹配（尝试其他数据库）

合并后的结果至少不会比单查询更少。

### Q4: 可以手动选择只搜索某几个variations吗？

**A**: 当前版本会自动搜索所有variations。如果只想搜索部分，可以：
1. 保存所有5个variations
2. 手动编辑JSON文件，只保留想要的variations
3. 重新加载

### Q5: 合并后的结果如何追溯到原始variation？

**A**: 每条记录都有 `source_variation` 列，标记它来自哪个variation。可以在CSV中筛选查看。

### Q6: 这个功能会影响Phase 3筛选吗？

**A**: 不会。Phase 3看到的是合并去重后的单一结果集，与单查询模式完全相同。

---

## 后续改进计划 🚀

### 短期（已实施）

- ✅ 生成5个查询变体
- ✅ 自动搜索所有变体
- ✅ 合并去重结果
- ✅ 保存/加载查询功能
- ✅ 显示合并统计信息

### 中期（2-4周）

- [ ] **智能variation数量**: 根据topic复杂度自动决定3-7个variations
- [ ] **Variation对比视图**: 并排显示所有variations的查询差异
- [ ] **部分搜索**: 允许选择只搜索某几个variations
- [ ] **Variation质量评分**: 预估每个variation的宽度（窄/中/宽）

### 长期（未来考虑）

- [ ] **Ensemble策略**: 自动选择"最佳"variation subset
- [ ] **增量variations**: 在现有结果上增加新variations
- [ ] **Variation模板**: 为常见研究类型提供预设variation策略
- [ ] **A/B测试**: 比较不同variation策略的效果

---

## 总结 🎯

**Query Variations功能解决了什么问题？**

1. ✅ **查询生成的非确定性** - 通过生成多个variations覆盖不同可能性
2. ✅ **结果数量的波动** - 合并后的结果更稳定、更全面
3. ✅ **可重复性** - 保存所有查询供后续重用
4. ✅ **文献召回率** - 最大化覆盖，不遗漏相关研究

**用户应该知道什么？**

- ✅ 默认会生成5个variations（可关闭）
- ✅ Phase 2会自动搜索所有variations（约6-8分钟）
- ✅ 结果会自动合并去重
- ✅ 可以保存查询供后续重用
- ✅ 最终结果比单查询更全面

**推荐使用方式**：

对于**正式的系统性综述**：
- ✅ 使用5 variations
- ✅ 搜索所有3个数据库
- ✅ 保存查询JSON
- ✅ 在方法部分报告完整的检索策略

对于**pilot search或探索性研究**：
- ⚠️ 可以使用1-2 variations
- ⚠️ 或关闭variations功能
- ⚠️ 但要注意可能遗漏文献

---

**实施完成！准备好测试！** 🎊
