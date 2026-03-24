# 安全策略

## 支持的版本

| 版本 | 支持状态     |
|------|--------------|
| 最新 | ✅ 受支持    |
| 旧版 | ❌ 不再支持  |

## 报告安全漏洞

**请勿在公开 Issues 中披露安全漏洞。**

如发现与 API Key、密钥存储、敏感数据泄露等相关的安全问题时，请通过以下方式私密联系：

- **GitHub Security Advisories**：在仓库页面点击 **Security** → **Report a vulnerability**

我们会尽快评估并回复，感谢你的负责任披露。

## 安全建议

- **切勿**将 `.streamlit/secrets.toml` 或 `.env` 提交到版本控制
- 使用 Streamlit Community Cloud 时，仅通过 **App Settings → Secrets** 配置 API Key
- 定期更换 API Key，尤其是在可能泄露的情况下
