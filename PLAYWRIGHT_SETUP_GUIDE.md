# Playwright Browser Automation Setup Guide

**目的：** Playwright 用作全文检索的**最后备选方案**，当 API 方式（Wiley, Elsevier, OpenAlex）都失败时，通过浏览器自动化下载付费墙保护的论文。

**重要提示：** Playwright 相对较慢且不稳定，建议仅在必要时启用。

---

## 🚨 使用场景

### ✅ 适合使用 Playwright 的情况：

1. **付费墙内容** - API 无法访问，但机构有订阅
2. **罕见出版商** - 没有 API 支持
3. **紧急需求** - 少量论文需要立即获取

### ❌ 不适合使用 Playwright 的情况：

1. **大批量下载** - 非常慢（每篇论文 30-60秒）
2. **已有 API 访问** - API 方式更快更稳定
3. **自动化流水线** - 浏览器可能因页面变化而失败

---

## 📦 安装步骤

### 步骤 1: 安装 Playwright Python 包

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装 Playwright
pip install playwright>=1.43.0
```

### 步骤 2: 下载浏览器

```bash
# 安装 Chromium 浏览器（推荐）
python3 -m playwright install chromium

# 或安装所有浏览器（Chromium, Firefox, WebKit）
python3 -m playwright install
```

**预期输出：**
```
Downloading Chromium 123.0.6312.4 (playwright build v1091) - 141.6 Mb
Chromium 123.0.6312.4 (playwright build v1091) downloaded to ~/.cache/ms-playwright/chromium-1091
```

### 步骤 3: 验证安装

```bash
# 测试 Playwright 是否正常工作
python3 -c "from playwright.sync_api import sync_playwright; print('✅ Playwright installed successfully')"
```

**成功输出：**
```
✅ Playwright installed successfully
```

---

## 🧪 测试 Playwright

### 快速测试脚本

创建测试脚本：
```bash
cat > test_playwright_basic.py << 'EOF'
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(f"✅ Page title: {page.title()}")
    browser.close()
EOF

# 运行测试
python3 test_playwright_basic.py
```

**预期输出：**
```
✅ Page title: Example Domain
```

---

## 🔧 配置选项

### 在 Streamlit 应用中使用

**Phase 4 配置界面：**

```
☑️ Use Playwright Fallback
   └─ 启用浏览器自动化作为最后备选

配置选项：
- Headless Mode: 无头模式（默认：开启）
- Timeout: 60000ms（可在代码中调整）
```

**工作流程：**
```
1. 尝试 OpenAlex API
   ↓ 失败
2. 尝试 Wiley/Elsevier API
   ↓ 失败
3. 尝试 Playwright（如果启用）✅
   ↓ 成功或失败
4. 返回结果
```

---

## 📊 性能对比

| 方法 | 速度 | 成功率 | 稳定性 | 推荐度 |
|------|------|--------|--------|--------|
| **Wiley API** | ⚡⚡⚡ 5-10秒 | 95% | ⭐⭐⭐⭐⭐ | ✅ 首选 |
| **Elsevier API** | ⚡⚡⚡ 5-10秒 | 85% | ⭐⭐⭐⭐⭐ | ✅ 首选 |
| **OpenAlex API** | ⚡⚡ 10-15秒 | 40% | ⭐⭐⭐⭐ | ✅ 推荐 |
| **Playwright** | 🐌 30-60秒 | 50-70% | ⭐⭐⭐ | ⚠️ 备选 |

**时间成本示例：**
- 10篇论文（仅 API）：1-2 分钟
- 10篇论文（含 Playwright）：5-10 分钟

---

## 🎯 实际测试

### 测试脚本：完整工作流程

```bash
cat > test_playwright_fulltext.py << 'EOF'
#!/usr/bin/env python3
"""
Test Playwright integration with full-text retrieval chain.
Tests a DOI that typically requires Playwright fallback.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m4_fulltext import FullTextRetriever
import pandas as pd

print("=" * 80)
print("PLAYWRIGHT FALLBACK TEST")
print("=" * 80)
print()

# Test DOI that likely requires Playwright
# (Nature papers often behind paywall, good for testing)
test_doi = "10.1038/s41586-021-03114-8"  # Nature paper

print(f"Testing with DOI: {test_doi}")
print("This paper may be behind a paywall, perfect for testing Playwright fallback")
print()

# Create test DataFrame
test_data = {
    'doi': [test_doi],
    'title': ['Test Nature Paper'],
    'judgement': [True]
}
screening_df = pd.DataFrame(test_data)

# Configure with Playwright enabled
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
config = {
    'out_dir': f"test_playwright_{timestamp}",
    'convert_to_md': False,
    'use_playwright': True,  # ✅ Enable Playwright
    'max_retries': 2,
    'timeout': 60
}

print("Configuration:")
print(f"  Use Playwright: {config['use_playwright']} ✅")
print(f"  Output: {config['out_dir']}")
print()

# Check Playwright installation
print("=" * 80)
print("CHECKING PLAYWRIGHT")
print("=" * 80)

try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright package installed")

    # Test browser availability
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        print("✅ Chromium browser available")
        browser.close()
except ImportError:
    print("❌ Playwright not installed!")
    print()
    print("Install with:")
    print("  pip install playwright")
    print("  python3 -m playwright install chromium")
    sys.exit(1)
except Exception as e:
    print(f"❌ Playwright error: {e}")
    print()
    print("Install browser with:")
    print("  python3 -m playwright install chromium")
    sys.exit(1)

print()

# Initialize retriever
print("=" * 80)
print("RUNNING FULL-TEXT RETRIEVAL WITH PLAYWRIGHT")
print("=" * 80)
print()

try:
    retriever = FullTextRetriever(config)
    doi_list = retriever.prepare_doi_list(screening_df)

    print("Starting retrieval chain:")
    print("  1. OpenAlex (likely to fail - not OA)")
    print("  2. Wiley/Elsevier (will fail - Nature paper)")
    print("  3. Playwright (should attempt browser download)")
    print()

    result_summary = retriever.run_fulltext_chain(doi_list)

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Status: {result_summary.get('status', 'unknown')}")
    print(f"Success count: {result_summary.get('success', 0)}")
    print()

    # Parse detailed results
    results_df = retriever.parse_results(config['out_dir'])

    if len(results_df) > 0:
        for _, row in results_df.iterrows():
            print(f"DOI: {row.get('doi')}")
            print(f"Success: {row.get('success')}")
            print(f"Final source: {row.get('final_source', 'none')}")
            print(f"Final status: {row.get('final_status', 'unknown')}")
            print(f"OpenAlex status: {row.get('openalex_status', 'N/A')}")
            print(f"Playwright status: {row.get('playwright_status', 'N/A')}")

            if row.get('success'):
                print(f"✅ Downloaded to: {row.get('download_path')}")
                file_size = row.get('file_bytes', 0) / (1024 * 1024)
                print(f"   File size: {file_size:.2f} MB")
            else:
                print("❌ Download failed")
                if row.get('playwright_status'):
                    print(f"   Playwright error: {row.get('playwright_status')}")
            print()

    print(f"📁 Output directory: {config['out_dir']}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("Note: Playwright success depends on:")
print("  • Journal website structure (may change)")
print("  • Institutional access (must be logged in)")
print("  • Network connectivity")
print("  • Paywall bypass detection")
EOF

# Run test
python3 test_playwright_fulltext.py
```

---

## ⚠️ 重要注意事项

### 1. 速度影响

**启用 Playwright 会显著降低速度：**
```
Without Playwright: 10 papers in 2 minutes
With Playwright:    10 papers in 10 minutes (5× slower)
```

**建议：**
- 仅在必要时启用（小批量、罕见出版商）
- 大批量下载时禁用，手动处理失败的 DOI

---

### 2. 稳定性问题

**Playwright 可能因以下原因失败：**

❌ **网站结构变化**
```
# PDF 下载按钮位置改变
# 需要更新选择器
```

❌ **反爬虫检测**
```
# 某些网站会检测自动化工具
# 可能需要额外配置（代理、cookies）
```

❌ **登录要求**
```
# 某些机构需要 Shibboleth/SSO 登录
# Playwright 无法自动处理
```

---

### 3. 机构访问

**Playwright 使用你的 IP 地址：**

✅ **在校园网内：** 可能成功（通过 IP 认证）
❌ **在校外：** 大概率失败（需要 VPN）

**解决方案：**
- 在校园网环境运行
- 使用机构 VPN
- 配置代理（高级）

---

### 4. 法律和伦理

**使用 Playwright 时请遵守：**

✅ **合法场景：**
- 机构有订阅权限
- 用于学术研究
- 合理使用范围内

❌ **非法场景：**
- 绕过付费墙下载未订阅内容
- 大规模批量下载（可能违反 ToS）
- 分享或商用下载内容

---

## 🔧 高级配置

### 自定义 Playwright 设置

如需修改 Playwright 行为，编辑 `fulltext_chain_wrapper.py`：

```python
# 在 PlaywrightFallbackDownloader.__enter__ 方法中

# 当前配置：
self.browser = self.playwright.chromium.launch(
    headless=self.headless,  # 无头模式
    args=[
        "--disable-blink-features=AutomationControlled",  # 隐藏自动化特征
        "--no-sandbox"  # 沙箱模式
    ]
)

# 可添加的配置：
# 1. 启用代理
self.browser = self.playwright.chromium.launch(
    headless=True,
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)

# 2. 自定义用户代理
self.context = self.browser.new_context(
    user_agent="Custom User Agent String"
)

# 3. 设置 cookies（用于保持登录状态）
self.context.add_cookies([{
    "name": "session",
    "value": "your_session_cookie",
    "domain": ".example.com",
    "path": "/"
}])
```

---

## 📋 故障排查

### 问题 1: "ModuleNotFoundError: No module named 'playwright'"

**解决方案：**
```bash
pip install playwright
```

---

### 问题 2: "Executable doesn't exist"

**解决方案：**
```bash
# 下载浏览器
python3 -m playwright install chromium

# 或强制重新安装
python3 -m playwright install --force chromium
```

---

### 问题 3: Playwright 下载但文件不是 PDF

**诊断：**
```bash
# 检查下载的文件类型
file downloads/playwright/*.pdf

# 如果显示 HTML：
downloads/playwright/paper.pdf: HTML document, ASCII text

# 说明下载的是 HTML 页面而不是 PDF
```

**解决方案：**
- 网站结构可能已变化
- 需要更新 CSS 选择器（见高级配置）
- 或手动下载该论文

---

### 问题 4: "Timeout exceeded"

**解决方案：**
```python
# 增加超时时间
config = {
    'timeout': 120,  # 增加到 120 秒
    'use_playwright': True
}
```

---

## 📊 性能优化建议

### 策略 1: 混合使用

```python
# 1. 首先用 API 方式下载大批量
config_api_only = {
    'use_playwright': False,  # 禁用 Playwright
    'out_dir': 'batch1_api_only'
}
# 预期：90% 成功率，但快速

# 2. 然后用 Playwright 处理失败的少量 DOI
config_with_playwright = {
    'use_playwright': True,  # 启用 Playwright
    'out_dir': 'batch2_failed_retry'
}
# 预期：额外 30-50% 成功率，但慢
```

---

### 策略 2: 选择性启用

```python
# 根据出版商选择是否启用 Playwright

def should_use_playwright(doi):
    """判断是否需要 Playwright"""
    # Wiley 和 Elsevier 有 API，不需要
    if doi.startswith('10.1002/') or doi.startswith('10.1016/'):
        return False

    # Nature, Science, PNAS 等可能需要
    if any(x in doi for x in ['10.1038/', '10.1126/', '10.1073/']):
        return True

    return False
```

---

## ✅ 最佳实践总结

### DO ✅

1. **优先使用 API 方式**
   - Wiley TDM
   - Elsevier
   - OpenAlex

2. **Playwright 作为最后手段**
   - 小批量（<10 篇）
   - 罕见出版商
   - 紧急需求

3. **在校园网环境使用**
   - 机构 IP 认证
   - 或使用 VPN

4. **测试再使用**
   - 先测试 1-2 篇
   - 确认成功率
   - 再批量运行

---

### DON'T ❌

1. **不要用于大批量下载**
   - 非常慢
   - 容易被检测
   - 成功率不稳定

2. **不要完全依赖 Playwright**
   - 优先配置 API
   - Playwright 只是备选

3. **不要违反服务条款**
   - 遵守 robots.txt
   - 尊重速率限制
   - 仅用于合法用途

---

## 📚 相关文档

- **FULLTEXT_USAGE_GUIDE.md** - 全文检索完整指南
- **FULLTEXT_GUIDE.md** - 功能概述
- **WILEY_INTEGRATION_SUMMARY.md** - Wiley API 集成
- **ENV_SETUP_GUIDE.md** - 环境配置

---

## 🎯 快速决策树

```
需要下载论文？
  │
  ├─ 有 API 支持（Wiley/Elsevier）？
  │   └─ YES → ✅ 使用 API（快速、稳定）
  │
  ├─ 是开放获取（OA）？
  │   └─ YES → ✅ 使用 OpenAlex API
  │
  ├─ 少量论文（<10）且紧急？
  │   └─ YES → ⚠️ 可以尝试 Playwright
  │
  └─ 大批量（>10）且时间充裕？
      └─ ❌ 不建议 Playwright
          → 优先配置更多 API
          → 或手动下载
```

---

## 总结

**Playwright 状态：**
- ✅ 代码已实现（PlaywrightFallbackDownloader 类）
- ⚠️ 需要安装（pip install playwright + 浏览器下载）
- ⚠️ 建议仅作为备选方案使用

**推荐做法：**
1. 先配置好所有 API（Wiley, OpenAlex, Elsevier）
2. 用 API 方式下载大批量论文（快速稳定）
3. 仅在必要时启用 Playwright 处理失败的少量 DOI
4. 始终在测试环境验证后再投入生产

**安装命令（如果需要）：**
```bash
pip install playwright
python3 -m playwright install chromium
python3 test_playwright_basic.py  # 验证安装
```
