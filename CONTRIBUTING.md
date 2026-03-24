# 参与贡献 ClawMe Skill Maker

感谢你对本项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

- 使用 [GitHub Issues](https://github.com/gloweaseco-leo/clawme-skill-maker/issues) 提交 Bug 报告
- 选择 **Bug Report** 模板，并尽可能填写完整信息
- 包含：复现步骤、预期行为、实际行为、环境信息

### 提出新功能

- 在 Issues 中选择 **Feature Request** 模板
- 清楚描述功能需求和使用场景
- 讨论通过后再提交 Pull Request

### 提交代码

1. **Fork** 本仓库到你自己的账号
2. **克隆**：`git clone https://github.com/gloweaseco-leo/clawme-skill-maker.git`  
   （若已 Fork，请将 `gloweaseco-leo` 改为你的 GitHub 用户名，以克隆你自己的 Fork）
3. **创建分支**：`git checkout -b feature/your-feature` 或 `fix/your-fix`
4. **编码**：遵循项目现有风格，确保代码可运行
5. **提交**：`git commit -m "feat: 简短描述"`
6. **推送**：`git push origin feature/your-feature`
7. **发起 PR**：在 GitHub 上创建 Pull Request，选择 PR 模板

### 提交信息规范

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `style:` 代码格式（不影响逻辑）
- `refactor:` 重构
- `chore:` 构建/工具变更

## 开发环境

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 编辑 secrets.toml 填入至少一个 API Key
streamlit run app.py
```

## 行为准则

请阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)，保持友好、尊重的沟通氛围。

## 许可证

贡献的代码默认采用与本项目相同的 MIT 许可证。
