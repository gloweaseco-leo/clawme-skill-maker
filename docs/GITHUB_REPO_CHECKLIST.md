# GitHub 开源仓库配置清单

> 作为 GitHub 运营总监，在上线 ClawMe Skill Maker 前请按此清单逐项检查。

---

## 一、仓库基础信息

在仓库 **Settings** 或 **About** 中配置：

| 项目 | 建议值 | 说明 |
|------|--------|------|
| **Description** | 用中文聊 3–5 句话，自动生成可导入 OpenClaw 的完整 Skill（V1） | 简洁描述，会出现在搜索和卡片上 |
| **Topics / Tags** | `openclaw`, `skill`, `streamlit`, `llm`, `clawme`, `ai` | 提高可发现性 |
| **Website** | 如有 Demo，填 Streamlit Cloud 地址 | 可选 |
| **Default branch** | `main` 或 `master` | 与 CI 分支一致 |

---

## 二、必须存在的文件

- [ ] **README.md** — 项目说明、快速开始、功能特性
- [ ] **LICENSE** — 本项目为 MIT
- [ ] **CONTRIBUTING.md** — 贡献指南
- [ ] **CODE_OF_CONDUCT.md** — 行为准则
- [ ] **SECURITY.md** — 安全策略（漏洞报告方式）
- [ ] **DEPLOYMENT.md** — 部署指南
- [ ] **.gitignore** — 排除 `secrets.toml`、`__pycache__`、`.env` 等

---

## 三、GitHub 功能启用

| 功能 | 建议 | 说明 |
|------|------|------|
| **Issues** | 启用 | 使用 YAML 模板（Bug / Feature Request） |
| **Discussions** | 建议启用 | 问答、想法交流，减轻 Issues 负担 |
| **Projects** | 可选 | 项目管理 |
| **Wiki** | 可选 | 深度文档 |
| **Sponsors** | 可选 | 若有赞助按钮，配置 FUNDING.yml |

---

## 四、分支与保护规则（可选）

- **main / master** 为默认分支
- 可设置：PR 需至少 1 人 Review、通过 CI 才能合并
- 保护规则路径：**Settings → Branches → Add rule**

---

## 五、GitHub Actions

- [ ] **CI 工作流**（`.github/workflows/ci.yml`）— 语法检查、依赖安装、导入测试
- [ ] **Dependabot**（`.github/dependabot.yml`）— 每月检查 pip 依赖更新

---

## 六、Issue / PR 模板

- [ ] **Bug 报告**：`.github/ISSUE_TEMPLATE/bug_report.yml`
- [ ] **功能建议**：`.github/ISSUE_TEMPLATE/feature_request.yml`
- [ ] **Issue 配置**：`.github/ISSUE_TEMPLATE/config.yml`（讨论链接等）
- [ ] **PR 模板**：`.github/PULL_REQUEST_TEMPLATE.md`

---

## 七、首次发布检查

1. **替换占位链接**  
   - 链接已使用 `gloweaseco-leo/clawme-skill-maker`，若需修改请全局替换  
   - 检查 CONTRIBUTING、CODE_OF_CONDUCT、SECURITY 中的链接

2. **敏感信息**  
   - 确认 `.streamlit/secrets.toml` 未被提交（应在 .gitignore 中）
   - 确认无硬编码 API Key

3. **README 中的快速开始**  
   - 克隆地址、部署步骤、API Key 配置说明是否准确

4. **Release（可选）**  
   - 创建首个 Release（如 v1.0.0），附上简要更新说明

---

## 八、上线后运营建议

- 在 X / 微博等平台发布开源公告，附仓库链接与 Demo 地址
- 定期查看 Issues、PR，及时回复
- 在 OpenClaw 社区或相关论坛分享，扩大曝光
- 收集用户反馈，迭代 README 与文档

---

## 九、文件结构总览

```
clawme-skill-maker/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── DEPLOYMENT.md
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── workflows/
│   │   └── ci.yml
│   └── dependabot.yml
└── docs/
    └── GITHUB_REPO_CHECKLIST.md  ← 本清单
```
