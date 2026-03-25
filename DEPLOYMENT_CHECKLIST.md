# 🚀 Streamlit Cloud 部署检查清单

**完成时间：2024-03-24**
**状态：✅ Ready for Deployment**

---

## ✅ 安全检查

### 敏感信息保护

- [x] ✅ `.env` 文件在 `.gitignore` 中
- [x] ✅ 所有文档中的 API keys 已替换为占位符
- [x] ✅ 代码中无硬编码密钥
- [x] ✅ `.streamlit/secrets.toml` 在 `.gitignore` 中
- [x] ✅ 创建了 `.streamlit/secrets.toml.example` 模板
- [x] ✅ Git 历史中的大文件已清理（153 MB → 33.49 MB）

### 安全扫描结果

```bash
✅ 已扫描文件中的 API keys: 无真实密钥
✅ AWS credentials: 仅占位符
✅ Wiley token: 已替换为占位符
✅ OpenAI keys: 仅占位符
```

---

## ✅ 代码准备

### 必需文件

- [x] ✅ `app.py` - 主应用文件
- [x] ✅ `requirements.txt` - 生产依赖
- [x] ✅ `.streamlit/config.toml` - Streamlit 配置
- [x] ✅ `.streamlit/secrets.toml.example` - 密钥模板
- [x] ✅ `README.md` - 项目文档

### 模块文件

- [x] ✅ `modules/m1_query_gen.py` - Phase 1
- [x] ✅ `modules/m2_search_exec.py` - Phase 2
- [x] ✅ `modules/m3_screening.py` - Phase 3
- [x] ✅ `modules/m4_fulltext.py` - Phase 4
- [x] ✅ `utils/` - 工具函数

### 文档文件

- [x] ✅ `STREAMLIT_CLOUD_DEPLOYMENT.md` - 部署指南
- [x] ✅ `QUICK_START.md` - 快速开始
- [x] ✅ `DEPLOYMENT_GUIDE.md` - 完整部署选项
- [x] ✅ `FULLTEXT_USAGE_GUIDE.md` - 全文检索指南
- [x] ✅ `ENV_SETUP_GUIDE.md` - 环境配置

---

## ✅ Git 仓库

### 提交状态

```bash
✅ 最新 commit: 83b2abc "Add Streamlit Cloud deployment documentation"
✅ 推送到 GitHub: https://github.com/Ziqian-xia/Climate_Intervention_Atlas
✅ 分支: main
✅ 远程同步: 已完成
```

### 仓库统计

- **总文件数**: ~761 files
- **仓库大小**: 33.49 MB
- **提交数**: 3 commits
- **大文件**: 已清理

---

## ✅ 依赖配置

### requirements.txt 内容

```txt
✅ streamlit>=1.31.0
✅ anthropic>=0.18.0
✅ boto3>=1.26.0
✅ pandas>=2.0.0
✅ python-dotenv>=1.0.0
✅ requests>=2.31.0
✅ tqdm>=4.66.0
✅ colorlog>=6.8.0
✅ openai>=1.0.0
```

### 可选依赖

```txt
⚠️ playwright>=1.43.0 (已注释 - 用户可选)
⚠️ PyPDF2>=3.0.0 (已注释 - 用户可选)
⚠️ pymupdf>=1.23.0 (已注释 - 用户可选)
```

---

## 📋 Streamlit Cloud 部署步骤

### 1. 访问 Streamlit Cloud

- [ ] 打开 https://share.streamlit.io/
- [ ] 使用 GitHub 账号登录

### 2. 创建应用

- [ ] 点击 "New app"
- [ ] Repository: `Ziqian-xia/Climate_Intervention_Atlas`
- [ ] Branch: `main`
- [ ] Main file: `app.py`
- [ ] App URL: 自定义名称（如 `climate-slr-pipeline`）

### 3. 配置 Secrets

- [ ] 点击 "Advanced settings"
- [ ] 复制 `.streamlit/secrets.toml.example` 内容
- [ ] 粘贴到 Secrets 文本框
- [ ] 填入真实 API keys：

#### 必需的 Secrets

```toml
[llm]
provider = "bedrock"
aws_access_key_id = "YOUR_REAL_KEY"
aws_secret_access_key = "YOUR_REAL_SECRET"

[search]
openalex_mailto = "your@real-email.com"

[screening]
openai_api_key = "YOUR_REAL_OPENAI_KEY"
```

#### 可选的 Secrets

```toml
[search]
pubmed_api_key = "YOUR_PUBMED_KEY"
scopus_api_key = "YOUR_SCOPUS_KEY"

[fulltext]
wiley_tdm_client_token = "YOUR_WILEY_TOKEN"
elsevier_api_key = "YOUR_ELSEVIER_KEY"
```

### 4. 部署

- [ ] 点击 "Deploy!" 按钮
- [ ] 等待 2-5 分钟（首次部署）
- [ ] 检查日志确认无错误

### 5. 验证

- [ ] 访问应用 URL
- [ ] 测试 Phase 1（查询生成）
- [ ] 测试 Phase 2（搜索执行）
- [ ] 测试 Phase 3（摘要筛选）
- [ ] 测试 Phase 4（全文下载）

---

## 🔧 需要的 API Keys

### Phase 1: Query Generation（必需）

#### AWS Bedrock（推荐）

- [ ] AWS Access Key ID
- [ ] AWS Secret Access Key
- [ ] Region: `us-east-1`
- [ ] Model: `us.anthropic.claude-sonnet-4-6`

**获取地址**: https://aws.amazon.com/bedrock/

**或者**

#### Anthropic Direct API

- [ ] Anthropic API Key

**获取地址**: https://console.anthropic.com/

### Phase 2: Search（推荐）

#### OpenAlex（免费，推荐）

- [x] Email: 任何有效 email（必需）
- [ ] API Key: 可选

**获取地址**: https://openalex.org/

#### PubMed（免费，可选）

- [ ] API Key
- [ ] Email

**获取地址**: https://www.ncbi.nlm.nih.gov/account/

#### Scopus（可选）

- [ ] API Key
- [ ] Institutional Token

**获取地址**: https://dev.elsevier.com/

### Phase 3: Screening（必需）

#### OpenAI

- [ ] OpenAI API Key

**获取地址**: https://platform.openai.com/

### Phase 4: Full-Text（可选）

#### Wiley TDM

- [ ] Wiley TDM Token

**申请地址**: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

#### Elsevier

- [ ] Elsevier API Key
- [ ] Institutional Token

**获取地址**: https://dev.elsevier.com/

---

## 📊 预期资源使用

### Streamlit Cloud 资源

- **RAM**: ~500 MB - 1 GB（取决于使用）
- **CPU**: 单核，足够
- **存储**: ~100 MB（代码和依赖）

### API 费用估算

**轻度使用（每月）：**
- 10 次查询生成: ~$5-10
- 1000 篇文献搜索: 免费
- 500 篇摘要筛选: ~$10-20
- 50 篇全文下载: 免费
- **总计**: ~$15-30/月

**中度使用（每月）：**
- 50 次查询生成: ~$25-50
- 5000 篇文献搜索: 免费
- 2000 篇摘要筛选: ~$40-80
- 200 篇全文下载: 免费
- **总计**: ~$65-130/月

---

## 🎯 部署后测试

### 基本功能测试

- [ ] Phase 1: 输入示例 topic，生成查询
- [ ] Phase 2: 搜索 OpenAlex（max 100 results）
- [ ] Phase 3: 筛选 10 篇摘要
- [ ] Phase 4: 下载 2-3 篇全文

### 性能测试

- [ ] 查询生成时间 < 2 分钟
- [ ] 搜索执行时间 < 5 分钟（1000 results）
- [ ] 摘要筛选时间 < 10 分钟（100 abstracts）
- [ ] 全文下载时间 < 1 分钟/篇（API 方式）

### 用户体验测试

- [ ] 界面清晰易用
- [ ] 错误提示友好
- [ ] 下载功能正常
- [ ] 帮助文档可访问

---

## 🛡️ 安全检查

### 生产环境

- [x] ✅ 所有密钥通过 Secrets 管理
- [x] ✅ 代码中无硬编码密钥
- [x] ✅ `.env` 不在 Git 中
- [ ] 设置应用为私有（可选）
- [ ] 添加访问控制（可选）

### 数据隐私

- [x] ✅ 不保存用户输入的敏感数据
- [x] ✅ 临时文件自动清理
- [ ] 添加隐私政策（可选）
- [ ] 添加使用条款（可选）

---

## 📝 后续维护

### 定期任务

- [ ] 每月检查 API 使用量
- [ ] 每季度更新依赖包
- [ ] 每半年轮换 API keys
- [ ] 定期查看应用日志

### 监控指标

- [ ] 应用可用性 > 99%
- [ ] 平均响应时间 < 30 秒
- [ ] 错误率 < 1%
- [ ] 用户满意度

---

## 🎉 部署完成确认

### 最终检查

- [x] ✅ 代码已推送到 GitHub
- [x] ✅ 所有文档已创建
- [x] ✅ 安全检查已通过
- [x] ✅ 依赖已配置
- [ ] Streamlit Cloud 已部署
- [ ] 应用已测试
- [ ] 团队成员已邀请
- [ ] 文档已分享

### 应用信息

- **GitHub Repo**: https://github.com/Ziqian-xia/Climate_Intervention_Atlas
- **Streamlit App**: https://[your-app-name].streamlit.app (待创建)
- **文档**: 见 GitHub README.md
- **支持**: GitHub Issues

---

## 📞 获取帮助

### 部署问题

- 📖 [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md)
- 📖 [QUICK_START.md](QUICK_START.md)
- 🌐 [Streamlit Docs](https://docs.streamlit.io/)

### 技术问题

- 🐛 [GitHub Issues](https://github.com/Ziqian-xia/Climate_Intervention_Atlas/issues)
- 💬 [Streamlit Forum](https://discuss.streamlit.io/)

### 联系方式

- 📧 Email: your@email.com
- 🔗 GitHub: @Ziqian-xia

---

**状态更新**: 2024-03-24 23:45
**下一步**: 部署到 Streamlit Cloud 🚀
**预计时间**: 5-10 分钟

---

**✅ All Systems Go! Ready for Launch! 🚀**
