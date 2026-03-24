# ClawMe Skill Maker 部署指南

本文档面向希望自托管或一键部署 ClawMe Skill Maker 的用户。

---

## 一、Streamlit Community Cloud（推荐，免费）

### 适用场景

- 快速 Demo、个人使用
- 无需服务器
- 免费额度通常够用

### 步骤

1. **Fork 本仓库**到你的 GitHub 账号
2. 打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登录
3. 点击 **New app**
4. 选择仓库 `gloweaseco-leo/clawme-skill-maker`，主文件填 `app.py`
5. 在 **Advanced settings → Secrets** 中添加（至少填一个你用到的模型）：

   ```toml
   DEEPSEEK_API_KEY = "sk-xxxxxxxx"
   # MOONSHOT_API_KEY = "sk-xxxxxxxx"
   # DASHSCOPE_API_KEY = "sk-xxxxxxxx"
   # ANTHROPIC_API_KEY = "sk-ant-xxxxxxxx"
   ```

6. 点击 **Deploy**，等待构建完成

### 注意事项

- 首次部署或更新后构建可能需要 2–5 分钟
- 免费版有资源与并发限制，长时间无访问会进入休眠
- 国内访问 Streamlit Cloud 可能较慢，可考虑自托管

---

## 二、Docker 自托管

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY .streamlit .streamlit

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 构建与运行

```bash
# 构建
docker build -t clawme-skill-maker .

# 运行（API Key 通过环境变量传入）
docker run -p 8501:8501 \
  -e DEEPSEEK_API_KEY="sk-xxx" \
  clawme-skill-maker
```

### Docker Compose

```yaml
services:
  clawme-skill-maker:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      # 按需添加其他 API Key
    restart: unless-stopped
```

---

## 三、Railway / Render / Fly.io

### Railway

1. 连接 GitHub 仓库
2. 选择本项目，Railway 会识别 Python 项目
3. 添加环境变量：`DEEPSEEK_API_KEY` 等
4. 设置启动命令：`streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. 部署

### Render

1. New → Web Service，连接仓库
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. 在 Environment 中添加 API Key 环境变量
5. 部署

### Fly.io

1. 安装 flyctl，在项目根目录执行：`fly launch`
2. 按提示完成初始化
3. `fly secrets set DEEPSEEK_API_KEY=sk-xxx`
4. `fly deploy`

---

## 四、传统 VPS（Ubuntu / Debian）

```bash
# 1. 安装依赖
sudo apt update && sudo apt install -y python3-pip python3-venv

# 2. 克隆项目
git clone https://github.com/gloweaseco-leo/clawme-skill-maker.git
cd clawme-skill-maker

# 3. 虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. 配置密钥
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
nano .streamlit/secrets.toml  # 填入 API Key

# 5. 后台运行（可用 screen / tmux 或 systemd）
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### 使用 systemd 常驻（可选）

创建 `/etc/systemd/system/clawme-skill-maker.service`：

```ini
[Unit]
Description=ClawMe Skill Maker
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/clawme-skill-maker
ExecStart=/path/to/clawme-skill-maker/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 五、环境变量对照表

| 变量名               | 说明           | 对应模型      |
|----------------------|----------------|---------------|
| `DEEPSEEK_API_KEY`   | DeepSeek       | deepseek-chat |
| `MOONSHOT_API_KEY`   | Kimi           | moonshot-v1-128k |
| `DASHSCOPE_API_KEY`  | 通义千问       | qwen-max      |
| `MINIMAX_API_KEY`    | MiniMax        | minimax-M2.1  |
| `ANTHROPIC_API_KEY`  | Claude         | claude-3-5-sonnet |

在云平台部署时，建议使用环境变量而非 `secrets.toml`，更安全、易管理。

---

## 六、健康检查

部署完成后，可访问：

- 应用首页应能正常加载
- 侧边栏可配置 API Key
- 输入需求后可进入澄清流程

若出现空白页，请检查终端/日志中的 `Script compilation error` 或依赖缺失。
