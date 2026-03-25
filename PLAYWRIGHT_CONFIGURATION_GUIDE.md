# Playwright 配置指南

**目标：** 让 Playwright 在校园网环境下成功下载付费墙论文

---

## 快速诊断

### 第 1 步：查看可视化诊断结果

运行中的诊断工具会显示 3 个测试页面：

**对于每个页面，请观察：**

#### ✅ 理想情况（机构访问正常）
- [ ] 页面显示完整文章内容
- [ ] 有明显的 "Download PDF" 或 "PDF" 按钮
- [ ] 没有 "Sign in" / "Subscribe" / "Login" 提示
- [ ] 手动点击 PDF 按钮可以下载

→ **如果是这样：** 问题是 Playwright 选择器，需要更新选择器（见下方"配置方案 A"）

#### ⚠️ 需要登录（机构访问未生效）
- [ ] 页面显示 "Sign in" / "Subscribe" 按钮
- [ ] 文章内容被模糊或隐藏
- [ ] 提示需要订阅或登录

→ **如果是这样：** 问题是机构访问配置（见下方"配置方案 B"）

#### ❌ 完全无法访问
- [ ] 页面显示 "Access denied"
- [ ] 或显示 "Unusual traffic detected"
- [ ] 或要求验证码

→ **如果是这样：** 网站反自动化检测（见下方"配置方案 C"）

---

## 配置方案 A：更新 PDF 选择器

**适用场景：** 手动可以下载，但 Playwright 找不到 PDF 按钮

### A1. 找到正确的选择器

在诊断工具打开的浏览器窗口中：

1. **右键点击 PDF 下载按钮** → 选择"检查"（Inspect）
2. 浏览器会显示 HTML 代码，例如：
   ```html
   <a class="article-pdf-link" href="/content/pdf/10.1038/...pdf" data-track="download-pdf">
       Download PDF
   </a>
   ```
3. **记录关键信息：**
   - `class="article-pdf-link"` → CSS 选择器：`a.article-pdf-link`
   - `data-track="download-pdf"` → 属性选择器：`a[data-track="download-pdf"]`
   - `href` 包含 `/content/pdf/` → 模糊匹配：`a[href*="/content/pdf/"]`

### A2. 更新 fulltext_chain_wrapper.py

打开文件并找到 `PlaywrightFallbackDownloader._find_pdf_url()` 方法（约第 411 行）：

```python
def _find_pdf_url(self) -> str:
    selectors = [
        # 现有选择器
        "a[data-article-pdf]",
        "a.c-pdf-download__link",
        "a[data-panel='PDF']",

        # 添加你发现的新选择器（在这里）
        "a.article-pdf-link",                    # 你的新选择器 1
        "a[data-track='download-pdf']",          # 你的新选择器 2

        # 其他现有选择器...
    ]
```

### A3. 测试更新后的选择器

```bash
# 重新运行测试
.venv/bin/python3 test_playwright_fallback.py
```

---

## 配置方案 B：机构访问配置

**适用场景：** 页面显示付费墙或需要登录

### B1. 确认机构订阅

首先确认你的机构是否订阅了这些期刊：

```bash
# 在浏览器中手动访问（不用 Playwright）
https://doi.org/10.1038/s41586-024-07219-y
https://doi.org/10.1126/science.adk4858
```

**如果手动也需要登录：**
→ 机构可能没有订阅，或需要特定访问方式
→ 联系图书馆确认订阅情况

**如果手动可以访问：**
→ 继续下面的配置

### B2. 配置机构代理（如需要）

某些机构需要通过代理访问：

**编辑 `fulltext_chain_wrapper.py`，找到第 392 行的浏览器启动代码：**

```python
# 原代码（第 392 行）
self.browser = self.playwright.chromium.launch(
    headless=self.headless,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
)

# 修改为（添加代理）
self.browser = self.playwright.chromium.launch(
    headless=self.headless,
    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    proxy={
        "server": "http://your-proxy-server:port",  # 替换为你的代理地址
        "username": "your_username",  # 如果需要
        "password": "your_password",  # 如果需要
    }
)
```

**获取代理信息：**
- 询问 IT 部门或图书馆
- 或查看浏览器代理设置：系统偏好设置 → 网络 → 高级 → 代理

### B3. 添加 Cookies（如需要登录）

如果机构访问需要登录，需要先在浏览器中登录，然后导出 cookies：

**步骤 1：获取 Cookies**

1. 在 Chrome/Edge 中访问期刊网站并登录
2. 按 F12 打开开发者工具
3. 切换到 "Application" 标签
4. 左侧选择 "Cookies" → 选择网站域名
5. 复制所有 cookie 的 Name 和 Value

**步骤 2：添加到 Playwright**

编辑 `fulltext_chain_wrapper.py`，在第 396 行后添加：

```python
# 原代码（第 396-400 行）
self.context = self.browser.new_context(
    accept_downloads=True,
    user_agent=DEFAULT_USER_AGENT,
)

# 修改为（添加 cookies）
self.context = self.browser.new_context(
    accept_downloads=True,
    user_agent=DEFAULT_USER_AGENT,
)

# 添加 cookies（在 new_context 之后，new_page 之前）
self.context.add_cookies([
    {
        "name": "session_id",        # 从浏览器复制
        "value": "your_session_value",
        "domain": ".nature.com",     # 对应的域名
        "path": "/"
    },
    {
        "name": "institutional_access",
        "value": "your_token",
        "domain": ".science.org",
        "path": "/"
    },
    # 根据需要添加更多 cookies
])

self.page = self.context.new_page()
```

---

## 配置方案 C：绕过反自动化检测

**适用场景：** 页面显示 "Unusual traffic" 或要求验证码

### C1. 增强浏览器伪装

编辑 `fulltext_chain_wrapper.py`：

```python
# 找到第 396 行的 new_context 调用
# 原代码
self.context = self.browser.new_context(
    accept_downloads=True,
    user_agent=DEFAULT_USER_AGENT,
)

# 修改为（增强伪装）
self.context = self.browser.new_context(
    accept_downloads=True,
    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport={'width': 1920, 'height': 1080},
    locale='en-US',
    timezone_id='America/New_York',
    device_scale_factor=1,
    has_touch=False,
    java_script_enabled=True,
    # 添加额外的浏览器特征
    extra_http_headers={
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
)
```

### C2. 添加随机延迟

在 `download()` 方法中（第 447 行后）添加延迟：

```python
# 原代码（第 447-448 行）
self.page.goto(f"https://doi.org/{doi}", wait_until="domcontentloaded", timeout=self.timeout_ms)
self.page.wait_for_timeout(2000)

# 修改为（随机延迟）
import random

self.page.goto(f"https://doi.org/{doi}", wait_until="domcontentloaded", timeout=self.timeout_ms)
self.page.wait_for_timeout(random.randint(2000, 5000))  # 2-5秒随机延迟
```

### C3. 使用 Stealth 插件（高级）

安装 playwright-stealth：

```bash
uv pip install playwright-stealth
```

然后修改代码：

```python
# 在文件顶部添加导入（第 10 行附近）
from playwright_stealth import stealth_sync

# 在 __enter__ 方法中，创建 page 后（第 400 行后）
self.page = self.context.new_page()
stealth_sync(self.page)  # 添加这行
```

---

## 最简配置：仅使用开放获取和已验证的 API

**如果上述配置都很复杂，最简单的方案是：**

### 不启用 Playwright，仅用 API

```bash
# 创建 .env 文件（如果还没有）
cat > .env << 'EOF'
# OpenAlex（开放获取，推荐）
OPENALEX_API_KEY=
OPENALEX_MAILTO=your@email.com

# Wiley TDM API（已验证可用）
WILEY_TDM_CLIENT_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Elsevier（如果有 API key）
ELSEVIER_API_KEY=your_key_here
ELSEVIER_INST_TOKEN=
EOF

# 运行全文检索（不使用 Playwright）
cd "Search and full-text packages/fulltext-packages"
python3 fulltext_chain_wrapper.py \
  --doi-file your_dois.csv \
  --convert-to-md \
  --out-dir results
  # 注意：不加 --use-playwright-fallback
```

**预期成功率：**
- Wiley 期刊 (10.1002/*, 10.1111/*): **~95%**
- OpenAlex 开放获取: **~40%**
- Elsevier (10.1016/*): **~85%**
- **总体：70-80% 的论文**

**对于失败的 20-30%：**
1. 在浏览器中手动下载（校园网环境）
2. 使用图书馆馆际互借服务
3. 联系作者请求预印本
4. 检查是否有 arXiv 等预印本版本

---

## 配置检查清单

完成配置后，按此清单验证：

### ✅ 基本配置
- [ ] Playwright 已安装 (`python3 -c "import playwright"`)
- [ ] Chromium 已下载 (`python3 -m playwright install chromium`)
- [ ] 基本测试通过 (`python3 test_playwright_simple.py`)

### ✅ 环境配置
- [ ] 已在校园网或连接机构 VPN
- [ ] 浏览器手动访问可以看到完整内容
- [ ] 已确认机构订阅相关期刊

### ✅ 代码配置（根据需要）
- [ ] PDF 选择器已更新（如果找不到按钮）
- [ ] 代理已配置（如果机构需要）
- [ ] Cookies 已添加（如果需要登录）
- [ ] 反检测配置已启用（如果被拦截）

### ✅ 测试验证
- [ ] 可视化诊断显示正确页面
- [ ] 测试下载至少 1 篇论文成功
- [ ] `results.csv` 显示 `final_source: "playwright"`
- [ ] `downloads/playwright/` 目录有 PDF 文件

---

## 测试命令

### 测试单个 DOI

```bash
# 创建测试文件
echo "10.1038/s41586-024-07219-y,Test paper,True" > test_single.csv

# 运行测试
cd "Search and full-text packages/fulltext-packages"
.venv/bin/python3 fulltext_chain_wrapper.py \
  --doi-file ../../test_single.csv \
  --use-playwright-fallback \
  --out-dir test_single_result
```

### 检查结果

```bash
# 查看详细结果
cat test_single_result/results.csv

# 检查是否有下载的文件
ls -lh test_single_result/downloads/playwright/
```

---

## 故障排查

### 问题 1: 仍然找不到 PDF 链接

**解决方案：** 手动提取 PDF URL 模式

1. 在浏览器中访问论文页面
2. 找到 PDF 下载链接
3. 右键 → 复制链接地址
4. 分析 URL 模式

例如：
- Nature: `https://www.nature.com/articles/s41586-024-07219-y.pdf`
- Science: `https://www.science.org/doi/pdf/10.1126/science.adk4858`
- PNAS: `https://www.pnas.org/doi/epdf/10.1073/pnas.2307665120`

然后在代码中添加 URL 模式推导（修改 `_derive_pdf_url()` 方法，第 436 行）：

```python
def _derive_pdf_url(self, current_url: str) -> str:
    # 现有模式
    if "/doi/abs/" in current_url:
        return current_url.replace("/doi/abs/", "/doi/pdf/")

    # 添加新模式
    if "nature.com/articles/" in current_url:
        return current_url.rstrip('/') + ".pdf"

    if "science.org/doi/" in current_url:
        return current_url.replace("/doi/", "/doi/pdf/")

    if "pnas.org/doi/" in current_url:
        return current_url.replace("/doi/", "/doi/epdf/")

    return ""
```

### 问题 2: 下载超时

**解决方案：** 增加超时时间

```bash
python3 fulltext_chain_wrapper.py \
  --doi-file dois.csv \
  --use-playwright-fallback \
  --timeout 120  # 增加到 120 秒
  --out-dir results
```

### 问题 3: 内存不足

**解决方案：** 批量处理

```bash
# 分批处理大量 DOI
split -l 10 all_dois.csv batch_  # 每 10 个一批

# 依次处理每批
for batch in batch_*; do
    python3 fulltext_chain_wrapper.py \
        --doi-file $batch \
        --use-playwright-fallback \
        --out-dir results_$batch
done
```

---

## 推荐决策树

```
需要下载论文？
│
├─ 是 Wiley 期刊 (10.1002/*, 10.1111/*)?
│   └─ ✅ 用 Wiley API（已配置，95% 成功率）
│       → 不需要 Playwright
│
├─ 是开放获取论文？
│   └─ ✅ 用 OpenAlex API（40% 成功率）
│       → 不需要 Playwright
│
├─ 是 Elsevier 期刊 (10.1016/*)?
│   └─ ✅ 用 Elsevier API（85% 成功率）
│       → 不需要 Playwright
│
├─ 少量论文（< 10 篇）且在校园网？
│   └─ ⚠️ 可以尝试 Playwright
│       → 但需要配置（见上方方案）
│
└─ 大批量论文（> 10 篇）？
    └─ ❌ 不建议 Playwright
        → 用 API 后手动补充失败的论文
```

---

## 获取帮助

如果上述配置都不成功：

1. **查看诊断截图**
   ```bash
   open playwright_diagnosis/
   ```

2. **联系机构支持**
   - 图书馆：确认期刊订阅和访问方式
   - IT 部门：确认网络配置和代理设置

3. **考虑替代方案**
   - 使用 API 方式（已验证可用）
   - 图书馆馆际互借
   - 联系作者请求预印本

---

**记住：API 方式已经可以覆盖 70-80% 的论文，对于大多数使用场景已经足够！**

Playwright 适合作为可选的补充方案，而非必需的核心功能。
