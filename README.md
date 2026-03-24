# ClawMe Skill Maker 🦞✨

> 用中文聊 3–5 句话，自动生成可导入 OpenClaw 的完整 Skill（V1）

由 **ClawMe** 驱动

---

## 功能特性

- 🗣️ **中文对话生成**：无需了解 Skill 格式，聊天即可生成
- 🔐 **权限确认卡片**：遵循最小权限原则，生成前可视化确认所有权限
- 📦 **一键打包下载**：生成 `.zip`（`SKILL.md`、`install.sh`、`install.bat`、`README.txt`），安装到 `~/.openclaw/skills/`
- 🔄 **多轮澄清引导**：结构化问 4 个问题，确保生成质量

## 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/gloweaseco-leo/clawme-skill-maker.git
cd clawme-skill-maker

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（按需填写你使用的模型对应的 Key）
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 .streamlit/secrets.toml，填入对应 API Key

# 4. 启动
streamlit run app.py
```

### 部署到 Streamlit Community Cloud（免费）

1. Fork 本仓库到你的 GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)，连接 GitHub 仓库
3. 在 **App Settings → Secrets** 添加：
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-xxxxxxxx"
   ```
4. 点击 Deploy

## 项目结构

```
clawme-skill-maker/
├── app.py                        # 主应用（唯一入口）
├── requirements.txt              # 依赖：streamlit / litellm / python-dotenv
├── .gitignore
├── .streamlit/
│   ├── secrets.toml.example      # API Key 示例（提交 GitHub）
│   └── config.toml               # 主题配置
└── README.md
```

## 使用流程

```
1. 描述你的需求（任意中文）
        ↓
2. 回答 4 个澄清问题（核心动作 / 目标模型 / 所需能力 / 触发方式）
        ↓
3. 确认权限清单
        ↓
4. 下载 .zip，运行 install.sh，在 OpenClaw 说"刷新技能列表"
```

## 技术栈

- **Python 3.10+**
- **Streamlit** — UI 框架
- **LiteLLM** — 统一多模型调用（DeepSeek / Kimi / 通义千问 / Claude）

## 故障排除

- **页面空白**：多半是 `app.py` 语法错误导致脚本未编译。请查看运行 `streamlit` 的终端是否出现 `Script compilation error`，修复后**重启** Streamlit；并尝试强制刷新浏览器（Ctrl+F5）。
- **远程访问异常**：勿在 `.streamlit/config.toml` 中设置 `enableCORS=false`，会与 XSRF 保护冲突。

## 相关文档

- [部署指南](DEPLOYMENT.md) — Streamlit Cloud、Docker、Railway 等部署方式
- [贡献指南](CONTRIBUTING.md) — 如何参与贡献
- [安全策略](SECURITY.md) — 漏洞报告方式
- [更新日志](CHANGELOG.md) — 版本变更记录

### 维护者：一键发布

```powershell
# Windows PowerShell
.\scripts\release.ps1 1.0.0
```

```bash
# Bash / Git Bash / WSL
./scripts/release.sh 1.0.0
```

推送 tag 后，GitHub Actions 自动构建 Release 并上传 source/dist 发布包。

## License

MIT © ClawMe
