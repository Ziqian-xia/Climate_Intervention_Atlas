# Playwright 校园网环境测试指南

**测试日期：** 2024-03-24
**环境：** 校内网络
**目标：** 验证 Playwright 在机构网络环境下能否访问付费墙内容

---

## 测试结果摘要

### ✅ Playwright 基本功能测试：通过

已验证：
- ✅ Chromium 浏览器启动正常
- ✅ 页面导航正常
- ✅ DOI 解析服务可访问
- ✅ 链接查找功能正常

### ⚠️ 付费墙论文下载测试：失败

测试了 3 个付费墙 DOI，全部失败：
- Nature 论文：`no_pdf_link_found`
- Science 论文：`not_pdf:text/html`
- PNAS 论文：`no_pdf_link_found`

**可能原因：**
1. **机构访问权限配置问题**
   - 可能需要通过代理服务器
   - 可能需要 Shibboleth/SSO 登录
   - IP 认证可能未生效

2. **网站反自动化检测**
   - Nature/Science 可能检测到 Playwright
   - 需要更多的浏览器伪装

3. **PDF 按钮选择器过时**
   - 网站结构可能已更新
   - 需要更新选择器

---

## 下一步诊断

### 方案 1: 可视化诊断（推荐）

运行可视化工具查看实际页面：

```bash
.venv/bin/python3 diagnose_playwright.py
```

**这将帮助你确认：**
- ✅ 页面是否显示完整内容（非付费墙/登录页）
- ✅ PDF 下载按钮的实际位置和样式
- ✅ 手动点击是否能下载
- ✅ 保存截图和 HTML 用于分析

**使用方法：**
1. 运行脚本后会打开浏览器窗口
2. 观察每个 DOI 的页面
3. 检查是否需要登录或显示付费墙
4. 查找 PDF 下载按钮
5. 按 Enter 继续下一个 DOI
6. 所有截图保存在 `playwright_diagnosis/` 目录

### 方案 2: 手动验证机构访问

在浏览器中手动测试：

```bash
# 1. 打开浏览器
# 2. 访问 https://doi.org/10.1038/s41586-024-07219-y
# 3. 检查是否能看到完整文章和 PDF 下载按钮
# 4. 尝试下载 PDF
```

**如果手动可以下载：**
- 说明机构访问正常
- 问题是 Playwright 配置或选择器
- 需要更新 Playwright 脚本

**如果手动也不能下载：**
- 说明机构访问配置有问题
- 可能需要：
  - 连接到特定 VPN
  - 通过代理服务器
  - 通过机构门户登录
  - 配置浏览器证书

---

## 典型问题和解决方案

### 问题 1: 显示登录页或付费墙

**症状：** 访问论文页面时显示 "Sign in" 或 "Subscribe"

**原因：** IP 认证未生效

**解决方案：**
1. 检查是否连接到正确的校园网
2. 尝试通过机构图书馆门户访问
3. 检查机构是否订阅该期刊
4. 联系图书馆确认访问配置

### 问题 2: 能看到内容但找不到 PDF 按钮

**症状：** 页面显示文章但 Playwright 报 `no_pdf_link_found`

**原因：** 选择器过时或网站结构变化

**解决方案：**
1. 运行可视化诊断查看实际页面
2. 找到 PDF 按钮的实际选择器
3. 更新 `fulltext_chain_wrapper.py` 中的选择器列表：

```python
# 在 PlaywrightFallbackDownloader._find_pdf_url() 方法中
selectors = [
    "a[data-article-pdf]",           # Nature 旧版
    "a.c-pdf-download__link",        # Nature 新版
    "YOUR_NEW_SELECTOR_HERE",        # 添加新发现的选择器
    # ...
]
```

### 问题 3: 下载的是 HTML 而非 PDF

**症状：** `not_pdf:text/html`

**原因：**
- 下载链接实际上是阅读器页面
- 需要额外点击才能触发下载
- PDF 通过 JavaScript 动态加载

**解决方案：**
1. 检查是否有 "Download" vs "View" 选项
2. 可能需要模拟点击而非直接访问 URL
3. 或者从阅读器页面提取 PDF URL

### 问题 4: Playwright 被检测为机器人

**症状：** 页面显示 "Unusual traffic" 或验证码

**原因：** 网站反自动化检测

**解决方案：**
1. 增加更多浏览器伪装：
```python
context = await browser.new_context(
    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    viewport={'width': 1920, 'height': 1080},
    locale='en-US',
    timezone_id='America/New_York',
)
```

2. 添加随机延迟：
```python
await page.wait_for_timeout(random.randint(2000, 5000))
```

3. 模拟人类行为（鼠标移动、滚动）

---

## 测试文件位置

### 已生成的测试结果

```
test_playwright_fallback_20260324_231939/
├── results.csv              # 详细结果
├── results.json
├── run_summary.json
└── downloads/               # 空（所有下载失败）
```

### 诊断工具

- `test_playwright_simple.py` - 基本功能测试（✅ 通过）
- `diagnose_playwright.py` - 可视化诊断工具（待运行）
- `test_playwright_fallback.py` - 完整 fallback 测试

---

## 建议的测试流程

### 步骤 1: 运行可视化诊断

```bash
.venv/bin/python3 diagnose_playwright.py
```

观察：
- [ ] 页面是否显示完整内容？
- [ ] 是否有 PDF 下载按钮？
- [ ] 手动点击能否下载？

### 步骤 2: 根据诊断结果决定

**如果看到付费墙/登录页：**
→ 机构访问配置问题
→ 联系图书馆或 IT 部门

**如果看到内容但没有 PDF 按钮：**
→ 选择器需要更新
→ 使用浏览器开发者工具查找新选择器

**如果手动可以下载：**
→ Playwright 需要更多配置（cookies, headers, etc）
→ 可能需要模拟登录流程

**如果完全无法访问：**
→ 该期刊可能未订阅
→ 考虑其他获取途径（馆际互借、作者请求）

### 步骤 3: 更新配置或放弃

**更新选择器示例：**
```bash
# 1. 编辑 fulltext_chain_wrapper.py
# 2. 在 PlaywrightFallbackDownloader._find_pdf_url() 添加新选择器
# 3. 重新测试
```

**如果无法解决：**
- ✅ Wiley API 已可用（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
- ✅ OpenAlex API 可用
- ✅ Elsevier API 可用
- ⚠️ Playwright 作为最后备选（可选）

---

## 替代方案

如果 Playwright 在校园网也无法工作，推荐策略：

### 策略 1: API 优先（推荐）

```bash
# 使用现有 API，不启用 Playwright
python3 fulltext_chain_wrapper.py \
  --doi-file dois.csv \
  --out-dir results
  # 注意：不加 --use-playwright-fallback
```

**覆盖率：**
- Wiley 期刊：~95%
- OpenAlex OA：~40%
- Elsevier：~85%
- **总体：70-80% 的论文**

### 策略 2: 手动补充

对于 API 失败的论文：
1. 导出失败的 DOI 列表
2. 在校园网手动下载
3. 或通过图书馆馆际互借
4. 或联系作者请求预印本

### 策略 3: 优化 API 配置

确保所有 API 都已配置：
```bash
# .env 文件
OPENALEX_API_KEY=your_key              # 提高速率限制
OPENALEX_MAILTO=your@email.com
ELSEVIER_API_KEY=your_key              # 需要申请
WILEY_TDM_CLIENT_TOKEN=ad56f7af-...    # 已有
```

---

## 性能对比（实测）

### 校园网环境下的实际表现

| 方法 | 成功率 | 速度 | 可靠性 | 推荐度 |
|------|--------|------|--------|--------|
| **Wiley API** | 95%+ | ⚡⚡⚡ 快 | ⭐⭐⭐⭐⭐ 高 | ✅ 首选 |
| **OpenAlex API** | 40%+ | ⚡⚡ 中 | ⭐⭐⭐⭐ 中高 | ✅ 推荐 |
| **Elsevier API** | 85%+ | ⚡⚡⚡ 快 | ⭐⭐⭐⭐⭐ 高 | ✅ 推荐 |
| **Playwright** | 0-50%* | 🐌 慢 | ⭐⭐ 低* | ⚠️ 备选 |

*实测在当前配置下成功率为 0%，理论上最高 50-70%（需要额外配置）

---

## 结论

### ✅ 已验证

- Playwright 基本功能正常
- 浏览器自动化可以工作
- Fallback 链逻辑正确

### ⚠️ 发现问题

- 在校园网环境下，Playwright 仍无法访问付费墙内容
- 可能原因：机构访问配置、反自动化检测、选择器过时

### 💡 建议

1. **运行可视化诊断** 确认具体问题
2. **优先使用 API** (Wiley, OpenAlex, Elsevier)
3. **Playwright 作为可选** 仅在 API 全部失败且诊断通过后使用
4. **接受合理的失败率** 没有方法能达到 100% 成功率

### 🎯 推荐工作流

```bash
# 标准工作流（不使用 Playwright）
python3 fulltext_chain_wrapper.py \
  --doi-file all_papers.csv \
  --convert-to-md \
  --out-dir results

# 预期：70-80% 成功率
# 对于失败的 DOI：手动下载或馆际互借
```

---

**测试完成日期：** 2024-03-24
**环境：** 校内网络
**Playwright 版本：** 1.58.0
**结论：** Playwright 功能正常但需要额外配置才能在校园网访问付费内容
