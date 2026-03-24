import io
import json
import os
import re
import time
import zipfile

import litellm
import streamlit as st
import streamlit.components.v1 as components

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(
    page_title="ClawMe Skill Maker",
    page_icon="🦞",
    layout="centered",
    initial_sidebar_state="expanded",
)

MODEL_CONFIG: dict[str, dict] = {
    "deepseek-chat": {
        "litellm": "deepseek/deepseek-chat",
        "secret":  "DEEPSEEK_API_KEY",
        "env":     "DEEPSEEK_API_KEY",
        "label":   "DeepSeek Chat",
        "hint":    "推荐国内用户，去 deepseek.com 免费注册",
    },
    "moonshot-v1-128k": {
        "litellm": "moonshot/moonshot-v1-128k",
        "secret":  "MOONSHOT_API_KEY",
        "env":     "MOONSHOT_API_KEY",
        "label":   "Kimi（Moonshot）",
        "hint":    "platform.moonshot.cn 注册",
    },
    "qwen-max": {
        "litellm": "dashscope/qwen-max",
        "secret":  "DASHSCOPE_API_KEY",
        "env":     "DASHSCOPE_API_KEY",
        "label":   "通义千问 Max",
        "hint":    "dashscope.aliyuncs.com（阿里云）",
    },
    "minimax-M2.1": {
        "litellm": "minimax/MiniMax-M2.1",
        "secret":  "MINIMAX_API_KEY",
        "env":     "MINIMAX_API_KEY",
        "label":   "MiniMax M2.1",
        "hint":    "platform.minimax.io 注册",
    },
    "claude-3-5-sonnet-20241022": {
        "litellm": "anthropic/claude-3-5-sonnet-20241022",
        "secret":  "ANTHROPIC_API_KEY",
        "env":     "ANTHROPIC_API_KEY",
        "label":   "Claude 3.5 Sonnet",
        "hint":    "console.anthropic.com",
    },
}
MODEL_KEYS = list(MODEL_CONFIG.keys())

# 快捷提示词标签，降低小白冷启动门槛
PROMPT_CHIPS: list[tuple[str, str]] = [
    ("🌞 每日早报助手", "每天早上汇总新闻、天气、待办，生成个人早报，推送到 Obsidian 或飞书"),
    ("📅 会议纪要整理", "把语音/文字会议记录自动整理成结构化纪要：议题、结论、待办，写入 Notion 或本地 md"),
    ("🔍 本地文档检索", "根据关键词搜索本地 Markdown/文档库，返回相关内容摘要和原文链接"),
    ("📺 B站动态 → Obsidian", "每天把关注的 B 站 UP 主动态总结成 Obsidian 笔记，按 UP 主分文件夹"),
]

CLARIFY_QUESTIONS = [
    ("q1", "这个 Skill **最核心的一件事**是什么？请用『动词 + 具体对象』描述（例如：总结 B 站 UP 主动态）"),
    ("q2", "你希望主要用哪个**大模型**跑这个 Skill？\n（Claude 3.5/3.7、GPT-4o、DeepSeek、Kimi、通义千问、其他）"),
    ("q3", "这个 Skill 需要用到哪些**能力/工具**？\n（例如：浏览器、本地文件读写、Obsidian 写入、微信发消息、发邮件等，用逗号分隔）"),
    ("q4", "**触发方式**？\n（手动触发 / 每天定时 / 收到消息时自动跑 / 其他）"),
]

META_PROMPT = """\
你现在是 OpenClaw 顶级 Skill 架构师，必须严格遵循最小权限原则（Principle of Least Privilege）。

用户需求：{user_original_input}
澄清信息：
- 核心动作：{core_action}
- 目标模型：{target_model}
- 所需工具/能力：{tools_list}
- 触发方式：{trigger_mode}

要求：
1. 全程用中文
2. YAML Front-matter 必须完整规范，且必须包含以下字段（缺少时自动补齐）：
   - name, description, version: "1.0.0", author: "ClawMe Skill Maker"
   - icon: 🦞 与 emoji: 🦞（二者保持一致）
   - user-invocable: true
   - homepage: https://github.com/gloweaseco-leo/clawme-skill-maker
   - generated_by: ClawMe Skill Maker v1
   - triggers, permissions 等
3. 每一步操作都明确写"调用哪个 Tool""预期输入输出""失败处理"
4. 前置条件里只列真正需要的 Tool（绝不多给权限）
5. 写 3–5 条常见边界 case 和错误处理
6. 最后加"使用示例"（2–3 个自然语言触发句）

请直接输出完整的 SKILL.md 内容（从 --- 开始，到结尾），不要任何废话。"""


def slugify_skill_name(raw: str) -> str:
    s = (raw or "").strip().lower().replace(" ", "-")
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "my-skill")[:80]


def compute_risk_level(permissions: dict) -> tuple[str, str]:
    p = permissions or {}
    exec_ = bool(p.get("exec"))
    fw = bool(p.get("file_write"))
    msg = bool(p.get("message"))
    em = bool(p.get("email"))
    net = bool(p.get("network"))

    score = 0
    if exec_:
        score += 5
    if fw:
        score += 2
    if msg:
        score += 2
    if em:
        score += 2
    if net:
        score += 1

    if exec_ or score >= 5:
        return ("高", "包含执行系统命令或多项敏感能力，请仔细核对。")
    if score >= 2:
        return ("中", "涉及写入、外发或网络访问，请确认符合预期。")
    return ("低", "权限范围相对克制，仍建议快速过一眼。")


PERM_FRIENDLY: list[tuple[str, str]] = [
    ("network",    "访问互联网（调用外部 API、网页等）"),
    ("file_read",  "读取本地文件"),
    ("file_write", "写入或修改本地文件"),
    ("exec",       "执行系统命令（风险较高，请谨慎）"),
    ("message",    "发送消息（微信/飞书/邮件等）"),
    ("email",      "发送邮件"),
]


def init_state() -> None:
    defaults: dict = {
        "stage":           "welcome",
        "messages":        [],
        "answers":         {},
        "original_input":  "",
        "skill_json":      None,
        "skill_md":        "",
        "confirm_checked": False,
        "skill_history":   [],
        "api_key_error":   None,  # 当 API Key 无效时，存对应 secret 名便于高亮
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


def test_api_key(model_key: str) -> tuple[bool, str | None]:
    """测试当前模型 API Key 是否有效。返回 (成功, 错误信息)。"""
    if not inject_api_key(model_key):
        return False, "未找到 API Key，请先在下方输入"
    try:
        litellm.completion(
            model=MODEL_CONFIG[model_key]["litellm"],
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        return True, None
    except Exception as e:
        return False, str(e)


def inject_api_key(model_key: str) -> str | None:
    cfg = MODEL_CONFIG[model_key]
    key: str | None = None
    # 1. st.secrets（兼容原有部署）
    try:
        val = st.secrets[cfg["secret"]]
        key = str(val).strip() if val else None
    except Exception:
        key = None
    # 2. UI 输入（session_state）
    if not key:
        ui_val = st.session_state.get(f"ui_key_{cfg['secret']}", "")
        if isinstance(ui_val, str) and ui_val.strip():
            key = ui_val.strip()
    # 3. 环境变量
    if not key:
        key = os.getenv(cfg["env"])
    if key:
        os.environ[cfg["env"]] = key
    return key


def current_question_index() -> int:
    for i, (k, _) in enumerate(CLARIFY_QUESTIONS):
        if k not in st.session_state.answers:
            return i
    return len(CLARIFY_QUESTIONS)


def append_and_show(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


def push_skill_history(slug: str, display_name: str, preview: str, skill_md: str = "", skill_json: dict | None = None) -> None:
    hist = list(st.session_state.skill_history)
    hist.insert(0, {
        "slug": slug,
        "name": display_name[:80],
        "preview": preview[:200],
        "skill_md": skill_md,
        "skill_json": skill_json or {},
        "ts": int(time.time()),
    })
    st.session_state.skill_history = hist[:5]


def build_install_sh(slug: str) -> str:
    return f"""#!/usr/bin/env bash
# ClawMe Skill Maker 自动生成 — 安装到全局 ~/.openclaw/skills/
# 适用于 macOS / Linux。Windows 用户请解压后手动将本文件夹复制到 %USERPROFILE%\\.openclaw\\skills\\
set -euo pipefail
SKILL_NAME="{slug}"
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
TARGET_DIR="${{HOME}}/.openclaw/skills/${{SKILL_NAME}}"

mkdir -p "${{TARGET_DIR}}"
cp "${{SCRIPT_DIR}}/SKILL.md" "${{TARGET_DIR}}/"
echo "✅ Skill 已安装到 ~/.openclaw/skills/${{SKILL_NAME}}"
echo "请在 OpenClaw 对话框输入：刷新技能列表"
"""


def build_install_bat(slug: str) -> str:
    return f"""@echo off
setlocal
set SKILL_NAME={slug}
set "SCRIPT_DIR=%~dp0"
set "TARGET_DIR=%USERPROFILE%\\.openclaw\\skills\\%SKILL_NAME%"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
copy /Y "%SCRIPT_DIR%SKILL.md" "%TARGET_DIR%\\" >nul
echo Skill 已安装到 %TARGET_DIR%
echo 请在 OpenClaw 中输入：刷新技能列表
pause
"""


def build_readme_txt(slug: str, display_name: str) -> str:
    return f"""ClawMe Skill Maker 自动生成
技能目录名（slug）: {slug}
展示名称: {display_name}

安装方式：
  • macOS / Linux：在本文件夹内执行
      chmod +x install.sh
      ./install.sh
  • Windows：双击 install.bat（或在本目录打开 CMD 后运行 install.bat）

安装目标：用户主目录下的 .openclaw/skills/{slug}/
（与 OpenClaw 全局技能目录一致）

由 ClawMe 品牌驱动 — https://github.com/gloweaseco-leo/clawme-skill-maker
"""


def build_zip(slug: str, skill_md: str, display_name: str) -> bytes:
    prefix = f"{slug}/"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(prefix + "SKILL.md", skill_md)
        zf.writestr(prefix + "install.sh", build_install_sh(slug))
        zf.writestr(prefix + "install.bat", build_install_bat(slug))
        zf.writestr(prefix + "README.txt", build_readme_txt(slug, display_name))
    buf.seek(0)
    return buf.read()


def copy_import_command_bash(slug: str) -> str:
    return (
        f'mkdir -p ~/.openclaw/skills/{slug} && '
        f'cp "$(pwd)/SKILL.md" ~/.openclaw/skills/{slug}/'
    )


def copy_import_command_win(slug: str) -> str:
    return (
        f'mkdir "%USERPROFILE%\\.openclaw\\skills\\{slug}" 2>nul & '
        f'copy /Y SKILL.md "%USERPROFILE%\\.openclaw\\skills\\{slug}\\"'
    )


def render_copy_import_buttons(slug: str) -> None:
    bash_cmd = copy_import_command_bash(slug)
    win_cmd = copy_import_command_win(slug)
    st.markdown("##### 一键复制导入命令（解压进入技能文件夹后，在终端粘贴执行）")
    c1, c2 = st.columns(2)
    jb = json.dumps(bash_cmd)
    jw = json.dumps(win_cmd)
    with c1:
        components.html(
            f"""
<div style="font-family:sans-serif;">
  <button id="cpb" type="button" style="padding:0.6rem 1rem;font-size:1rem;width:100%;cursor:pointer;border-radius:8px;border:1px solid #444;background:#262730;color:#fafafa;">复制 Bash 命令（macOS / Linux）</button>
  <script>
    document.getElementById("cpb").onclick = function() {{
      navigator.clipboard.writeText({jb});
      this.innerText = "已复制 ✓";
    }};
  </script>
</div>
""",
            height=70,
        )
    with c2:
        components.html(
            f"""
<div style="font-family:sans-serif;">
  <button id="cpw" type="button" style="padding:0.6rem 1rem;font-size:1rem;width:100%;cursor:pointer;border-radius:8px;border:1px solid #444;background:#262730;color:#fafafa;">复制 CMD 命令（Windows）</button>
  <script>
    document.getElementById("cpw").onclick = function() {{
      navigator.clipboard.writeText({jw});
      this.innerText = "已复制 ✓";
    }};
  </script>
</div>
""",
            height=70,
        )
    st.caption("若浏览器拦截剪贴板，请从下方代码块手动复制。")
    st.code(bash_cmd, language="bash")
    st.code(win_cmd, language="batch")


def render_copy_full_md_hint() -> None:
    """整段 SKILL.md 可能很长，不嵌入 iframe，避免页面白屏；用预览区 st.code 自带复制。"""
    st.caption("复制全部：在下方「预览」代码块右上角使用复制图标。")


with st.sidebar:
    st.markdown(
        '<p style="font-size:1.5rem;font-weight:700;margin:0.4rem 0 0.1rem 0;line-height:1.3">'
        "🦞 ClawMe Skill Maker</p>",
        unsafe_allow_html=True,
    )
    st.caption("用 3–5 句话，一键生成可导入 OpenClaw 的你专属 Skill")
    with st.expander("查看产品说明", expanded=False):
        st.markdown(
            "用任意语言描述需求，自动生成带权限说明的 `SKILL.md`，"
            "并支持一键打包下载，快速导入 OpenClaw。"
        )
    st.divider()

    st.markdown("")

    with st.container(border=True):
        st.markdown("### 🤖 模型配置")
        st.selectbox(
            "选择模型",
            options=MODEL_KEYS,
            format_func=lambda k: MODEL_CONFIG[k]["label"],
            index=0,
            key="selected_model",
            help="选择生成 SKILL.md 的模型，并填写对应 API Key",
        )
        st.caption("默认推荐 DeepSeek Chat（上手快）；你也可以选择 Kimi/通义千问等模型")

        with st.expander("配置 API Keys 🔑", expanded=bool(st.session_state.get("api_key_error"))):
            st.caption(
                "Key 仅保存到本次会话；长期使用建议配置到 Streamlit Secrets。"
            )
            _sm = st.session_state.get("selected_model", MODEL_KEYS[0])
            if st.button("🧪 测试当前模型 Key", key="test_api_key_btn", use_container_width=True):
                with st.spinner("测试中…"):
                    ok, err = test_api_key(_sm)
                    st.session_state["api_key_test_result"] = ("ok", None) if ok else ("err", err)
                    st.session_state["api_key_test_model"] = _sm
                st.rerun()
            if "api_key_test_result" in st.session_state and st.session_state.get("api_key_test_model") == _sm:
                ok, err = st.session_state["api_key_test_result"]
                if ok:
                    st.success("✅ Key 有效")
                else:
                    st.error(f"❌ {err}")
            st.divider()
            for mk, mcfg in MODEL_CONFIG.items():
                secret = mcfg["secret"]
                hint = mcfg.get("hint", "")
                ui_key = f"ui_key_{secret}"
                is_err = st.session_state.get("api_key_error") == secret
                has_key = bool(str(st.session_state.get(ui_key, "")).strip())
                label = f"{mcfg['label']}  ✅" if has_key else mcfg["label"]
                st.text_input(
                    label,
                    key=ui_key,
                    type="password",
                    placeholder="输入 API Key",
                    help="⚠️ 该 Key 无效或已过期，请检查后重试" if is_err else hint,
                )
                if is_err:
                    st.caption("⚠️ 该 Key 无效或已过期，请检查后重试")

    st.markdown("")

    with st.container(border=True):
        st.markdown("### 🔗 链接与信息")
        st.markdown("📦 [GitHub Repo](https://github.com/gloweaseco-leo/clawme-skill-maker)")
        st.caption("由 ClawMe 品牌驱动")
        st.caption("主题切换：右上角 ⚙️ Settings")

    st.markdown("")

    with st.container(border=True):
        st.markdown("### ⚠️ 安全提醒")
        st.warning(
            "导入前请人工审核权限清单，确保每项权限都符合真实需求。"
        )
        st.markdown("[查看项目说明](https://github.com/gloweaseco-leo/clawme-skill-maker)")

    if st.session_state.skill_history:
        st.markdown("")
        with st.container(border=True):
            with st.expander("📜 最近 5 次生成", expanded=False):
                for i, item in enumerate(st.session_state.skill_history):
                    st.markdown(f"**{i + 1}. `{item['slug']}`** — {item['name'][:40]}")
                    st.caption((item.get("preview", "")[:120].replace("\n", " ") + "…") if len(item.get("preview", "")) > 120 else item.get("preview", ""))
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("查看", key=f"hist_view_{i}", use_container_width=True):
                            st.session_state.stage = "done"
                            st.session_state.skill_json = item.get("skill_json") or {}
                            st.session_state.skill_md = item.get("skill_md", "")
                            st.session_state.md_edit = item.get("skill_md", "")
                            st.rerun()
                    with c2:
                        _md = item.get("skill_md", "")
                        _zip = build_zip(item["slug"], _md, item.get("name", item["slug"])) if _md else b""
                        st.download_button(
                            "下载",
                            data=_zip,
                            file_name=f"{item['slug']}.zip",
                            mime="application/zip",
                            key=f"hist_dl_{i}",
                            use_container_width=True,
                            disabled=not _md,
                        )
                    with c3:
                        if st.button("基于此优化", key=f"hist_opt_{i}", use_container_width=True):
                            sk = item.get("skill_json") or {}
                            st.session_state.skill_json = sk
                            st.session_state.answers = {
                                "q1": str(sk.get("core_action", "")),
                                "q2": str(sk.get("target_model", "")),
                                "q3": str(sk.get("tools", "")),
                                "q4": str(sk.get("trigger", "")),
                            }
                            st.session_state.original_input = str(sk.get("description", "")) or f"基于 {item.get('name', '')} 优化"
                            st.session_state.stage = "confirm"
                            st.session_state.confirm_checked = False
                            st.session_state.messages = []
                            st.rerun()

    st.markdown("")
    if st.button("🔄 新需求（重置）", use_container_width=True):
        preserved: dict = {"selected_model": st.session_state.get("selected_model", MODEL_KEYS[0])}
        for k in list(st.session_state.keys()):
            if k.startswith("ui_key_"):
                preserved[k] = st.session_state[k]
            else:
                del st.session_state[k]
        for k, v in preserved.items():
            st.session_state[k] = v
        st.rerun()

selected_model: str = st.session_state.get("selected_model", MODEL_KEYS[0])
current_key = inject_api_key(selected_model)

if not current_key:
    cfg = MODEL_CONFIG[selected_model]
    st.session_state["api_key_error"] = cfg["secret"]
    st.error(
        f"❌ 未找到 `{cfg['label']}` 的 API Key。\n\n"
        "**请在左侧「配置 API Keys」中展开并输入对应 Key 后重试。**\n\n"
        f"若使用 secrets 部署，可在 `.streamlit/secrets.toml` 添加：\n"
        f"```toml\n{cfg['secret']} = \"your-key-here\"\n```"
    )
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.stage == "welcome" and not st.session_state.messages:
    welcome = (
        "你好！我是 **ClawMe Skill Maker** 🦞\n\n"
        "请告诉我你想要什么 Skill，例如：\n\n"
        "> 每天早上把 B 站关注的 UP 主动态总结成 Obsidian 笔记\n\n"
        "请开始描述你的想法 👇"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    with st.chat_message("assistant"):
        st.markdown(welcome)


def render_confirm_card() -> None:
    skill = st.session_state.skill_json or {}
    permissions = skill.get("permissions", {})
    risk, risk_note = compute_risk_level(permissions)

    st.markdown("---")
    st.subheader("🔐 权限确认")

    with st.expander("查看权限与技能摘要", expanded=True):
        risk_icon = {"低": "🟢", "中": "🟡", "高": "🔴"}.get(risk, "⚪")
        st.markdown(f"**风险等级：** {risk_icon} **{risk}** — {risk_note}")
        st.markdown("请逐项确认该 Skill 所需权限：")

        for perm_key, friendly in PERM_FRIENDLY:
            on = bool(permissions.get(perm_key, False))
            st.markdown(f"{'✅' if on else '⬜'} {friendly}")

        extras = skill.get("permissions_extra", "")
        if extras:
            st.markdown(f"**其他说明：** {extras}")

        st.markdown("---")
        st.markdown(f"**技能名称：** `{skill.get('name', '未命名')}`")
        st.markdown(f"**描述：** {skill.get('description', '')}")
        st.markdown(f"**核心动作：** {skill.get('core_action', '')}")
        st.markdown(f"**触发方式：** {skill.get('trigger', '')}")
        st.markdown(f"**所需工具：** {skill.get('tools', '')}")

    checked = st.checkbox(
        "我已阅读并确认以上权限清单，同意生成该 Skill",
        value=st.session_state.confirm_checked,
        key="perm_checkbox",
    )
    st.session_state.confirm_checked = checked

    col_ok, col_back = st.columns(2)
    with col_ok:
        if st.button("✅ 确认生成 Skill", disabled=not checked, use_container_width=True, type="primary"):
            st.session_state.stage = "generating"
            st.session_state.pop("generate_error", None)
            st.rerun()
    with col_back:
        if st.button("↩️ 返回修改", use_container_width=True):
            st.session_state.answers.pop("q4", None)
            st.session_state.stage = "q4"
            st.session_state.skill_json = None
            st.session_state.confirm_checked = False
            st.session_state.pop("generate_error", None)
            st.rerun()


def structurize_skill() -> dict:
    model_key = st.session_state.get("selected_model", MODEL_KEYS[0])
    inject_api_key(model_key)
    answers = st.session_state.answers

    prompt = f"""你是 JSON 生成器，根据以下信息生成技能结构 JSON，只输出 JSON，不要任何解释。

用户原始需求：{st.session_state.original_input}
核心动作：{answers.get('q1', '')}
目标模型：{answers.get('q2', '')}
所需工具/能力：{answers.get('q3', '')}
触发方式：{answers.get('q4', '')}

输出格式：
{{
  "name": "skill-slug-用连字符",
  "description": "一句话描述这个技能做什么",
  "core_action": "动词+对象",
  "target_model": "模型名",
  "tools": "工具列表",
  "trigger": "触发方式",
  "permissions": {{
    "network": true,
    "file_read": false,
    "file_write": false,
    "exec": false,
    "message": false,
    "email": false
  }},
  "permissions_extra": ""
}}"""

    response = litellm.completion(
        model=MODEL_CONFIG[model_key]["litellm"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    raw = response.choices[0].message.content.strip()
    match = re.search(r"\{[\s\S]+\}", raw)
    if match:
        return json.loads(match.group())
    return json.loads(raw)


def generate_skill_md() -> str:
    model_key = st.session_state.get("selected_model", MODEL_KEYS[0])
    inject_api_key(model_key)
    skill = st.session_state.skill_json or {}
    answers = st.session_state.answers

    prompt = META_PROMPT.format(
        user_original_input=st.session_state.original_input,
        core_action=answers.get("q1", skill.get("core_action", "")),
        target_model=answers.get("q2", skill.get("target_model", "")),
        tools_list=answers.get("q3", skill.get("tools", "")),
        trigger_mode=answers.get("q4", skill.get("trigger", "")),
    )

    response = litellm.completion(
        model=MODEL_CONFIG[model_key]["litellm"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def render_done() -> None:
    """技能预览卡片：顶部名称+简介，中间权限清单，底部主操作，源码折叠。"""
    skill = st.session_state.skill_json or {}
    raw_name = str(skill.get("name", "my-skill"))
    slug = slugify_skill_name(raw_name)
    display_name = raw_name if raw_name else slug
    description = str(skill.get("description", "")) or f"OpenClaw 技能：{display_name}"
    zip_bytes = build_zip(slug, st.session_state.skill_md, display_name)
    bash_cmd = copy_import_command_bash(slug)
    win_cmd = copy_import_command_win(slug)
    permissions = skill.get("permissions", {})

    st.balloons()

    # ── 技能预览卡片：顶部 ──
    with st.container(border=True):
        st.markdown(f"## {display_name}")
        st.caption(description)
    st.markdown("")

    # ── 权限清单（醒目展示） ──
    st.markdown("#### 权限清单")
    perm_lines = []
    for perm_key, friendly in PERM_FRIENDLY:
        on = bool(permissions.get(perm_key, False))
        perm_lines.append(f"{'✅' if on else '❌'} {friendly}")
    st.markdown("  \n".join(perm_lines))
    risk, risk_note = compute_risk_level(permissions)
    risk_icon = {"低": "🟢", "中": "🟡", "高": "🔴"}.get(risk, "⚪")
    st.caption(f"{risk_icon} 风险等级：{risk} — {risk_note}")
    st.markdown("")

    # ── 主操作按钮（硕大、醒目） ──
    dl_col, copy_col = st.columns(2)
    with dl_col:
        st.download_button(
            label="⬇️ 下载 .zip（含 SKILL.md + 安装脚本）",
            data=zip_bytes,
            file_name=f"{slug}.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
            key="done_dl_zip",
        )
    with copy_col:
        copy_choice = st.radio(
            "复制导入命令",
            ["Bash (macOS/Linux)", "CMD (Windows)"],
            key="copy_cmd_choice",
            label_visibility="collapsed",
            horizontal=True,
        )
        cmd = bash_cmd if "Bash" in copy_choice else win_cmd
        components.html(
            f"""
<div>
  <button id="cpcmd" type="button" style="padding:0.6rem 1.2rem;font-size:1rem;width:100%;cursor:pointer;border-radius:8px;border:1px solid #444;background:#262730;color:#fafafa;">📋 复制拉取命令</button>
  <script>
    document.getElementById("cpcmd").onclick = function() {{
      navigator.clipboard.writeText({json.dumps(cmd)});
      this.innerText = "已复制 ✓";
    }};
  </script>
</div>
""",
            height=55,
        )

    st.markdown("---")

    # ── 继续编辑（可选） ──
    with st.expander("✏️ 修改后重新下载", expanded=False):
        edited = st.text_area(
            "可直接修改下方内容，修改后下载会使用最新内容",
            height=200,
            key="md_edit",
            label_visibility="collapsed",
        )
        st.session_state.skill_md = edited
        md_bytes = st.session_state.skill_md.encode("utf-8")
        st.download_button("⬇️ 下载 SKILL.md（仅文件）", data=md_bytes, file_name="SKILL.md", mime="text/markdown", key="done_dl_md")

    # ── 查看底层源码（折叠） ──
    with st.expander("📄 查看底层源码", expanded=False):
        st.code(st.session_state.skill_md, language="markdown")

    with st.expander("🚀 30 秒导入教程"):
        st.markdown(f"""
**全局目录（推荐）**  
OpenClaw 会读取用户目录下的 `~/.openclaw/skills/`。本应用生成的 `install.sh` / `install.bat` 会把 `SKILL.md` 复制到该路径下的 `{slug}/`。

**方式一：脚本安装（推荐）**
1. 解压 `{slug}.zip`，进入 `{slug}/` 文件夹。
2. **macOS / Linux**：在终端执行 `chmod +x install.sh` 后执行 `./install.sh`（也可在终端中打开该目录再运行）。
3. **Windows**：双击 `install.bat`，或在 CMD 中进入该目录后运行 `install.bat`。
4. 在 OpenClaw 里说：**「刷新技能列表」**。

**方式二：手动复制**  
将解压后的 `{slug}/` 整个文件夹复制到 `~/.openclaw/skills/`（Windows 对应 `%USERPROFILE%\\.openclaw\\skills\\`）。

**工作区局部目录**  
若使用 OpenClaw 的 workspace 局部技能目录 `./skills/`，可将同一文件夹复制到项目下的 `skills/`。

**验证**  
在 OpenClaw 里说 **「列出所有 Skill」**，能看到 `{slug}` 即表示安装成功 ✅
""")


stage = st.session_state.stage

if stage == "confirm":
    if st.session_state.get("generate_error"):
        st.error(
            f"❌ 生成失败：{st.session_state['generate_error']}\n\n"
            "请在左侧「配置 API Keys」中检查对应 Key 是否正确，或点击下方重试。"
        )
        if st.button("🔄 重试生成", type="primary", key="retry_generate"):
            st.session_state.pop("generate_error", None)
            st.session_state.stage = "generating"
            st.rerun()
        st.markdown("---")
    render_confirm_card()

elif stage == "structurize_failed":
    err = st.session_state.get("structurize_error", "未知错误")
    st.error(f"❌ 结构化分析失败：{err}\n\n请在左侧「配置 API Keys」中检查对应 Key，或点击重试。")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重试", type="primary", key="retry_structurize"):
            try:
                st.session_state.skill_json = structurize_skill()
                st.session_state.stage = "confirm"
                st.session_state.pop("structurize_error", None)
                st.session_state.pop("api_key_error", None)
                append_and_show("assistant", "✅ 信息收集完毕！请在下方确认该 Skill 所需权限，然后点击「确认生成」。")
            except Exception as e:
                st.session_state.structurize_error = str(e)
                err_lower = str(e).lower()
                if any(x in err_lower for x in ("401", "authentication", "invalid api", "api_key", "invalid key")):
                    st.session_state["api_key_error"] = MODEL_CONFIG[selected_model]["secret"]
            st.rerun()
    with col2:
        if st.button("↩️ 返回修改", key="back_from_structurize"):
            st.session_state.stage = "q4"
            st.session_state.pop("structurize_error", None)
            st.session_state.skill_json = None
            st.rerun()

elif stage == "generating":
    model_label = MODEL_CONFIG[selected_model]["label"]
    with st.spinner(f"⏳ {model_label} 正在生成 SKILL.md，大约需要 10–20 秒……"):
        try:
            skill_md = generate_skill_md()
            st.session_state.skill_md = skill_md
            st.session_state.md_edit = skill_md
            sj = st.session_state.skill_json or {}
            raw_n = str(sj.get("name", "my-skill"))
            s_slug = slugify_skill_name(raw_n)
            push_skill_history(s_slug, raw_n, skill_md, skill_md, sj)
            st.session_state.stage = "done"
            st.session_state.pop("api_key_error", None)
            append_and_show("assistant", "✅ 已生成完毕！请查看下方结果。")
        except Exception as e:
            st.session_state.generate_error = str(e)
            st.session_state.stage = "confirm"
            err_lower = str(e).lower()
            if any(x in err_lower for x in ("401", "authentication", "invalid api", "api_key", "invalid key")):
                st.session_state["api_key_error"] = MODEL_CONFIG[selected_model]["secret"]
    st.rerun()

elif stage == "done":
    render_done()

# 对话阶段：chat_input 固定在底部，避免与其它阶段混排导致布局异常
if stage in ("welcome", "q1", "q2", "q3", "q4"):
    # 快捷提示词标签（仅 welcome 阶段展示，降低小白冷启动门槛）
    if stage == "welcome":
        st.caption("💡 点击下方标签快速开始，或直接输入你的想法")
        c1, c2 = st.columns(2)
        for i, (label, preset) in enumerate(PROMPT_CHIPS):
            col = c1 if i % 2 == 0 else c2
            with col:
                if st.button(label, key=f"chip_{i}", use_container_width=True):
                    st.session_state["chip_submit"] = preset
                    st.rerun()

    user_input: str | None = st.session_state.pop("chip_submit", None) or st.chat_input(
        "输入想法，按 Enter 一键生成可导入的 .md 文件",
        key="main_chat",
    )

    if user_input:
        append_and_show("user", user_input)
        cur = st.session_state.stage

        if cur == "welcome":
            st.session_state.original_input = user_input
            st.session_state.stage = "q1"
            q_text = CLARIFY_QUESTIONS[0][1]
            append_and_show("assistant", f"好的！让我进一步了解你的需求。\n\n**问题 1/4：** {q_text}")

        elif cur in ("q1", "q2", "q3", "q4"):
            st.session_state.answers[cur] = user_input
            q_idx = current_question_index()

            if q_idx < len(CLARIFY_QUESTIONS):
                next_key, next_q = CLARIFY_QUESTIONS[q_idx]
                st.session_state.stage = next_key
                append_and_show("assistant", f"**问题 {q_idx + 1}/4：** {next_q}")
            else:
                st.session_state.stage = "confirm"
                with st.spinner("🔍 正在分析需求，生成权限清单……"):
                    try:
                        st.session_state.skill_json = structurize_skill()
                        st.session_state.pop("api_key_error", None)
                        append_and_show(
                            "assistant",
                            "✅ 信息收集完毕！请在下方确认该 Skill 所需权限，然后点击「确认生成」。",
                        )
                    except Exception as e:
                        st.session_state.structurize_error = str(e)
                        st.session_state.stage = "structurize_failed"
                        err_lower = str(e).lower()
                        if any(x in err_lower for x in ("401", "authentication", "invalid api", "api_key", "invalid key")):
                            st.session_state["api_key_error"] = MODEL_CONFIG[selected_model]["secret"]

        st.rerun()
