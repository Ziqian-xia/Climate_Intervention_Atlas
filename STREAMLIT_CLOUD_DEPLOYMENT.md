# Streamlit Cloud 部署指南

**5 分钟内将 Auto-SLR Pipeline 部署到 Streamlit Cloud**

---

## ✅ 部署前检查清单

- [x] ✅ 代码已推送到 GitHub
- [x] ✅ `.streamlit/config.toml` 已创建
- [x] ✅ `.streamlit/secrets.toml.example` 已创建
- [x] ✅ `requirements.txt` 已创建
- [x] ✅ `README.md` 已创建
- [x] ✅ 所有 API keys 已从代码中移除
- [x] ✅ `.env` 文件在 `.gitignore` 中

---

## 🚀 部署步骤

### 步骤 1: 访问 Streamlit Cloud

1. 打开浏览器访问：https://share.streamlit.io/
2. 点击 **"Sign in with GitHub"**
3. 授权 Streamlit 访问您的 GitHub 账户

### 步骤 2: 创建新应用

1. 点击 **"New app"** 按钮
2. 填写应用信息：

   - **Repository**: `Ziqian-xia/Climate_Intervention_Atlas`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: `climate-slr-pipeline`（或自定义名称）

3. 点击 **"Advanced settings"**（可选）

### 步骤 3: 配置密钥（重要！）

1. 在 "Advanced settings" 中，找到 **"Secrets"** 部分
2. 复制 `.streamlit/secrets.toml.example` 的内容
3. 粘贴到 Secrets 文本框中
4. 填入您的真实 API keys：

```toml
# 示例配置（填入真实值）
[llm]
provider = "bedrock"
aws_region = "us-east-1"
aws_model_id = "us.anthropic.claude-sonnet-4-6"
aws_access_key_id = "AKIAXXXXXXXXXXXXXXXX"  # 填入真实值
aws_secret_access_key = "your_real_secret_key"  # 填入真实值

[search]
openalex_api_key = ""
openalex_mailto = "your@email.com"  # 填入真实值
pubmed_api_key = "your_real_key"  # 填入真实值
pubmed_email = "your@email.com"

[screening]
openai_api_key = "sk-your_real_openai_key"  # 填入真实值

[fulltext]
wiley_tdm_client_token = "your_real_wiley_token"  # 填入真实值
elsevier_api_key = "your_real_elsevier_key"  # 可选
```

### 步骤 4: 部署

1. 点击 **"Deploy!"** 按钮
2. 等待 2-5 分钟（首次部署会安装依赖）
3. 部署完成后，您的应用将在以下地址运行：
   - `https://climate-slr-pipeline.streamlit.app`

---

## 📋 获取 API Keys

### Phase 1: LLM Provider（查询生成）

#### AWS Bedrock（推荐）

1. 访问 [AWS Console](https://aws.amazon.com/)
2. 创建 IAM 用户：
   - 服务：IAM → 用户 → 创建用户
   - 权限：附加策略 `AmazonBedrockFullAccess`
3. 创建访问密钥：
   - 用户详情 → 安全凭证 → 创建访问密钥
   - 选择 "应用程序在 AWS 外部运行"
   - 保存 Access Key ID 和 Secret Access Key

4. 启用 Bedrock 模型：
   - 服务：Amazon Bedrock → Model access
   - 请求访问 Anthropic Claude models
   - 选择 Claude 3.5 Sonnet 或 4

#### Anthropic Direct API（备选）

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建账户
3. 导航到 Settings → API Keys
4. 创建新 API key
5. 保存密钥（格式：`sk-ant-...`）

### Phase 2: Search APIs（文献搜索）

#### OpenAlex（免费，推荐）

- **API Key**: 可选（留空即可使用免费层）
- **Email**: 必需（任何有效 email）
- 网址：https://openalex.org/

#### PubMed / NCBI（免费）

1. 访问 [NCBI](https://www.ncbi.nlm.nih.gov/account/)
2. 创建账户
3. 导航到 Account Settings → API Key Management
4. 创建 API key
5. 保存密钥

#### Scopus（需要机构访问）

1. 访问 [Elsevier Developer Portal](https://dev.elsevier.com/)
2. 使用机构账户登录
3. 创建应用并获取 API key
4. 保存 API key 和 Institutional Token（可选）

### Phase 3: Abstract Screening

#### OpenAI API

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 创建账户
3. 导航到 API Keys
4. 创建新密钥
5. 保存密钥（格式：`sk-proj-...`）

### Phase 4: Full-Text Retrieval（可选）

#### Wiley TDM API

1. 访问 [Wiley TDM](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)
2. 填写申请表单
3. 等待审批（通常 1-2 周）
4. 收到 token（格式：UUID）

#### Elsevier API

1. 与 Scopus API 相同
2. 使用相同的 API key

---

## 🔧 应用配置

### Python 版本

Streamlit Cloud 默认使用 Python 3.12，与我们的项目兼容。

### 资源限制

**免费版限制：**
- 1 GB RAM
- 1 CPU core
- 1 个私有应用

**如果遇到性能问题：**
- 减少并发搜索数量
- 减少 Phase 3 screening 线程数
- 考虑升级到 Streamlit Cloud Enterprise

### 更新应用

代码更新后自动部署：
1. 本地修改代码
2. Commit 并 push 到 GitHub
3. Streamlit Cloud 自动检测并重新部署（~2 分钟）

手动触发重新部署：
1. 访问应用仪表板
2. 点击 **"Reboot"** 按钮

---

## 🛡️ 安全建议

### 密钥管理

**✅ DO:**
- 使用 Streamlit Secrets 存储所有 API keys
- 定期轮换 API keys
- 为 Streamlit Cloud 创建专用 AWS IAM 用户
- 使用最小权限原则

**❌ DON'T:**
- 在代码中硬编码 API keys
- 提交 `.env` 或 `secrets.toml` 到 Git
- 在公共应用中暴露密钥
- 分享您的 Secrets 配置

### 访问控制

**设置为私有应用：**
1. 应用仪表板 → Settings
2. Sharing → 选择 "Private"
3. 添加允许访问的 email 地址

**或添加密码保护：**
- 在 `app.py` 中添加密码验证
- 使用 `st.secrets` 存储密码哈希

---

## 📊 监控和日志

### 查看日志

1. 应用仪表板 → Logs
2. 实时查看应用输出
3. 过滤错误和警告

### 性能监控

1. 应用仪表板 → Analytics
2. 查看：
   - 访问量
   - 响应时间
   - 错误率

---

## 🔍 故障排查

### 问题 1: 应用无法启动

**症状：** 部署失败或一直显示 "Preparing"

**可能原因：**
1. `requirements.txt` 中的包无法安装
2. Python 版本不兼容
3. 代码有语法错误

**解决方案：**
1. 检查 Logs 中的错误信息
2. 验证 `requirements.txt` 中的包名和版本
3. 本地测试：`pip install -r requirements.txt`

### 问题 2: API 调用失败

**症状：** 应用运行但功能失败

**可能原因：**
1. Secrets 未正确配置
2. API keys 无效或过期
3. API 配额已用完

**解决方案：**
1. 检查 Secrets 配置是否正确
2. 在本地测试 API keys
3. 查看 API 服务商的使用仪表板

### 问题 3: 应用很慢

**症状：** 响应时间长

**可能原因：**
1. 免费版资源限制
2. 大量数据处理
3. 并发用户过多

**解决方案：**
1. 优化代码（减少计算量）
2. 使用缓存（`@st.cache_data`）
3. 升级到付费计划

### 问题 4: 内存不足

**症状：** 应用崩溃或重启

**解决方案：**
1. 减少 Phase 2 的 `max_results`
2. 减少 Phase 3 的 `thread` 数量
3. 分批处理数据
4. 清理中间结果

---

## 🎯 优化建议

### 性能优化

```python
# 在 app.py 中添加缓存
import streamlit as st

@st.cache_data(ttl=3600)  # 缓存 1 小时
def generate_queries(topic, provider):
    # 查询生成逻辑
    pass

@st.cache_resource
def get_llm_provider(provider_type, config):
    # Provider 初始化
    pass
```

### 用户体验优化

1. **添加使用说明**
   ```python
   with st.expander("ℹ️ How to use this app"):
       st.markdown("""
       1. Configure your API keys in the sidebar
       2. Enter your research topic
       3. Generate queries
       4. Execute search
       """)
   ```

2. **添加示例数据**
   ```python
   if st.button("Load Example"):
       st.session_state.topic = "climate change adaptation..."
   ```

3. **添加进度提示**
   ```python
   with st.spinner("Generating queries..."):
       # 长时间操作
       pass
   ```

---

## 📱 分享应用

### 获取应用 URL

部署成功后，您的应用 URL 为：
- `https://[your-app-name].streamlit.app`

### 分享选项

1. **公开应用**
   - 任何人都可以访问
   - 适合演示和展示

2. **私有应用**
   - 只有邀请的用户可以访问
   - 适合内部使用

3. **密码保护**
   - 在代码中添加认证
   - 所有人可访问但需要密码

### 自定义域名（可选）

Streamlit Cloud Enterprise 支持自定义域名：
- `slr.your-domain.com`

---

## 💰 费用说明

### Streamlit Cloud 定价

**免费版：**
- ✅ 1 个私有应用
- ✅ 无限公开应用
- ✅ 1 GB RAM
- ✅ 社区支持

**Enterprise 版：**
- ✅ 无限私有应用
- ✅ 更多资源（RAM, CPU）
- ✅ 自定义域名
- ✅ SSO 集成
- ✅ 优先支持

### API 费用

**Phase 1: LLM Provider**
- AWS Bedrock Claude 3.5 Sonnet: ~$0.003 per 1K tokens
- Anthropic Direct: ~$0.003 per 1K tokens
- 预估：每次查询生成 ~$0.10-0.50

**Phase 2: Search**
- OpenAlex: 免费
- PubMed: 免费
- Scopus: 机构订阅

**Phase 3: Screening**
- OpenAI GPT-4: ~$0.01 per 1K tokens
- 预估：每 100 篇摘要 ~$2-5

**Phase 4: Full-Text**
- Wiley TDM: 免费（需申请）
- Elsevier: 机构订阅
- OpenAlex: 免费

**月度预算估算：**
- 轻度使用（10 queries/月）：~$20-30
- 中度使用（50 queries/月）：~$100-150
- 重度使用（200 queries/月）：~$400-600

---

## 🎉 部署完成！

### 验证部署

1. 访问您的应用 URL
2. 测试基本功能：
   - [ ] Phase 1: 生成查询
   - [ ] Phase 2: 执行搜索（小数据集）
   - [ ] Phase 3: 筛选摘要
   - [ ] Phase 4: 下载全文
3. 检查日志是否有错误

### 下一步

1. **添加团队成员**
   - 应用仪表板 → Settings → Sharing
   - 输入 email 地址邀请

2. **监控使用情况**
   - 定期检查 Analytics
   - 监控 API 配额

3. **获取用户反馈**
   - 添加反馈表单
   - 改进用户体验

4. **持续改进**
   - 修复 bugs
   - 添加新功能
   - 优化性能

---

## 📚 相关资源

### 文档

- [Streamlit Cloud 官方文档](https://docs.streamlit.io/streamlit-community-cloud)
- [App Settings 指南](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/app-settings)
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

### 本项目文档

- [README.md](README.md) - 项目概述
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 完整部署指南
- [FULLTEXT_USAGE_GUIDE.md](FULLTEXT_USAGE_GUIDE.md) - 全文检索使用
- [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) - 环境配置

### 支持

- [GitHub Issues](https://github.com/Ziqian-xia/Climate_Intervention_Atlas/issues)
- [Streamlit Forum](https://discuss.streamlit.io/)

---

**🎊 恭喜！您的 Auto-SLR Pipeline 现已上线！**

应用 URL: `https://[your-app-name].streamlit.app`
