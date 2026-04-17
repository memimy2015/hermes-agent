# 为 Hermes Agent 做贡献

感谢你为 Hermes Agent 做贡献！本指南涵盖你需要了解的一切：搭建开发环境、理解架构、决定要做什么，以及让你的 PR 顺利合并。

---

## 贡献优先级

我们按以下顺序重视贡献：

1. **Bug 修复** — 崩溃、错误行为、数据丢失。永远是最高优先级。
2. **跨平台兼容性** — Windows、macOS、不同的 Linux 发行版、不同的终端模拟器。我们希望 Hermes 在任何地方都能工作。
3. **安全加固** — Shell 注入、提示注入、路径穿越、权限提升。参见 [安全](#security-considerations)。
4. **性能与鲁棒性** — 重试逻辑、错误处理、优雅降级。
5. **新技能（Skill）** — 但只接受对大多数人都有用的技能。参见 [应该做成 Skill 还是 Tool？](#should-it-be-a-skill-or-a-tool)
6. **新工具（Tool）** — 很少需要。多数能力应该由 Skill 提供。详见下文。
7. **文档** — 修正、澄清、新示例。

---

<a id="should-it-be-a-skill-or-a-tool"></a>
## 应该做成 Skill 还是 Tool？

这是新贡献者最常见的问题。答案几乎总是 **Skill**。

### 适合做成 Skill 的情况

- 能力可以用“说明 + Shell 命令 + 现有工具”表达
- 包装一个外部 CLI 或 API，代理可以通过 `terminal` 或 `web_extract` 调用
- 不需要把自定义 Python 集成或 API Key 管理硬编码进代理本体
- 示例：arXiv 搜索、git 工作流、Docker 管理、PDF 处理、通过 CLI 工具发送邮件

### 适合做成 Tool 的情况

- 需要端到端集成 API Key、鉴权流程或由 agent harness 管理的多组件配置
- 需要必须每次都精确执行的自定义处理逻辑（而不是让 LLM “尽力而为”地解释）
- 处理二进制数据、流式传输或实时事件，无法通过终端通道完成
- 示例：浏览器自动化（Browserbase 会话管理）、TTS（音频编码 + 平台投递）、视觉分析（base64 图像处理）

### Skill 是否应该随包发布？

随包发布的技能（位于 `skills/`）会随每次 Hermes 安装一起提供。它们应当对 **大多数用户都普遍有用**：

- 文档处理、网页研究、常见开发工作流、系统管理
- 会被不同类型的人频繁使用

如果你的技能是官方且有用，但并非人人都需要（例如：付费服务集成、重量级依赖），请放在 **`optional-skills/`** —— 它会随仓库一起发布，但默认不启用。用户可以通过 `hermes skills browse`（标注为 “official”）发现它，并用 `hermes skills install` 安装（不会出现第三方警告，内置可信）。

如果你的技能更偏专用、社区贡献或小众，通常更适合放到 **Skills Hub** —— 把它上传到技能注册表，并在 [Nous Research Discord](https://discord.gg/NousResearch) 分享。用户可以用 `hermes skills install` 安装。

---

## 开发环境搭建

### 前置条件

| 需求 | 说明 |
|-------------|-------|
| **Git** | 支持 `--recurse-submodules` |
| **Python 3.11+** | 缺失时 uv 会安装 |
| **uv** | 快速 Python 包管理器（[安装](https://docs.astral.sh/uv/)） |
| **Node.js 18+** | 可选 — 浏览器工具与 WhatsApp bridge 需要 |

### 克隆与安装

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 使用 Python 3.11 创建 venv
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# 安装全部 extras（messaging、cron、CLI 菜单、开发工具）
uv pip install -e ".[all,dev]"

# 可选：RL 训练子模块
# git submodule update --init tinker-atropos && uv pip install -e "./tinker-atropos"

# 可选：浏览器工具
npm install
```

### 为开发配置

```bash
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env

# 至少添加一个 LLM provider 的 key：
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env
```

### 运行

```bash
# 建立全局访问的 symlink
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# 验证
hermes doctor
hermes chat -q "Hello"
```

### 运行测试

```bash
pytest tests/ -v
```

---

## 项目结构

```
hermes-agent/
├── run_agent.py              # AIAgent class — 核心对话循环、tool 分发、会话持久化
├── cli.py                    # HermesCLI class — 交互式 TUI、prompt_toolkit 集成
├── model_tools.py            # Tool 编排（tools/registry.py 之上的薄封装）
├── toolsets.py               # Tool 分组与预设（hermes-cli、hermes-telegram 等）
├── hermes_state.py           # SQLite 会话数据库（FTS5 全文检索）、会话标题
├── batch_runner.py           # 轨迹生成的并行批处理
│
├── agent/                    # Agent 内部实现（抽取出的模块）
│   ├── prompt_builder.py         # 系统提示构建（身份、技能、上下文文件、记忆）
│   ├── context_compressor.py     # 临近上下文上限时自动摘要
│   ├── auxiliary_client.py       # 辅助 OpenAI client（摘要、视觉）
│   ├── display.py                # KawaiiSpinner、tool 进度输出格式
│   ├── model_metadata.py         # 模型上下文长度、token 估算
│   └── trajectory.py             # 轨迹保存辅助
│
├── hermes_cli/               # CLI 命令实现
│   ├── main.py                   # 入口、参数解析、命令分发
│   ├── config.py                 # 配置管理、迁移、环境变量定义
│   ├── setup.py                  # 交互式配置向导
│   ├── auth.py                   # Provider 解析、OAuth、Nous Portal
│   ├── models.py                 # OpenRouter 模型选择列表
│   ├── banner.py                 # 欢迎横幅、ASCII art
│   ├── commands.py               # 中央 slash 命令注册表（CommandDef）、自动补全、gateway 辅助
│   ├── callbacks.py              # 交互式回调（澄清、sudo、审批）
│   ├── doctor.py                 # 诊断
│   ├── skills_hub.py             # Skills Hub CLI + /skills slash 命令
│   └── skin_engine.py            # 皮肤/主题引擎 — 数据驱动的 CLI 视觉自定义
│
├── tools/                    # Tool 实现（自注册）
│   ├── registry.py               # 中央 tool registry（schema、handler、dispatch）
│   ├── approval.py               # 危险命令检测 + 按会话审批
│   ├── terminal_tool.py          # 终端编排（sudo、env 生命周期、后端）
│   ├── file_operations.py        # read_file、write_file、search、patch 等
│   ├── web_tools.py              # web_search、web_extract（Parallel/Firecrawl + Gemini 摘要）
│   ├── vision_tools.py           # 通过多模态模型做图像分析
│   ├── delegate_tool.py          # 子代理创建与并行任务执行
│   ├── code_execution_tool.py    # 沙箱 Python（带 RPC tool 访问）
│   ├── session_search_tool.py    # 用 FTS5 + 摘要搜索历史对话
│   ├── cronjob_tools.py          # 定时任务管理
│   ├── skill_tools.py            # Skill 搜索、加载与管理
│   └── environments/             # 终端执行后端
│       ├── base.py                   # BaseEnvironment ABC
│       ├── local.py, docker.py, ssh.py, singularity.py, modal.py, daytona.py
│
├── gateway/                  # 消息网关
│   ├── run.py                    # GatewayRunner — 平台生命周期、消息路由、cron
│   ├── config.py                 # 平台配置解析
│   ├── session.py                # Session store、上下文提示、重置策略
│   └── platforms/                # 平台适配器
│       ├── telegram.py, discord_adapter.py, slack.py, whatsapp.py
│
├── scripts/                  # 安装器与 bridge 脚本
│   ├── install.sh                # Linux/macOS 安装器
│   ├── install.ps1               # Windows PowerShell 安装器
│   └── whatsapp-bridge/          # Node.js WhatsApp bridge（Baileys）
│
├── skills/                   # 随包技能（安装时复制到 ~/.hermes/skills/）
├── optional-skills/          # 官方可选技能（hub 可发现，默认不启用）
├── environments/             # RL 训练环境（Atropos 集成）
├── tests/                    # 测试套件
├── website/                  # 文档站点（hermes-agent.nousresearch.com）
│
├── cli-config.yaml.example   # 配置示例（复制到 ~/.hermes/config.yaml）
└── AGENTS.md                 # 面向 AI 编码助手的开发指南
```

### 用户配置（存放于 `~/.hermes/`）

| 路径 | 用途 |
|------|---------|
| `~/.hermes/config.yaml` | 设置（模型、终端、toolsets、压缩等） |
| `~/.hermes/.env` | API key 与密钥 |
| `~/.hermes/auth.json` | OAuth 凭据（Nous Portal） |
| `~/.hermes/skills/` | 所有启用的技能（随包 + hub 安装 + agent 创建） |
| `~/.hermes/memories/` | 持久化记忆（MEMORY.md、USER.md） |
| `~/.hermes/state.db` | SQLite 会话数据库 |
| `~/.hermes/sessions/` | JSON 会话日志 |
| `~/.hermes/cron/` | 定时任务数据 |
| `~/.hermes/whatsapp/session/` | WhatsApp bridge 凭据 |

---

## 架构概览

### 核心循环

```
用户消息 → AIAgent._run_agent_loop()
  ├── 构建系统提示（prompt_builder.py）
  ├── 构建 API kwargs（model、messages、tools、reasoning config）
  ├── 调用 LLM（OpenAI 兼容 API）
  ├── 如果响应中包含 tool_calls：
  │     ├── 通过 registry dispatch 执行每个 tool
  │     ├── 将 tool 结果加入对话
  │     └── 回到 LLM 调用
  ├── 如果是文本响应：
  │     ├── 将会话持久化到 DB
  │     └── 返回 final_response
  └── 临近 token 上限时进行上下文压缩
```

### 关键设计模式

- **自注册工具（self-registering tools）**：每个 tool 文件在 import 时调用 `registry.register()`。`model_tools.py` 通过导入所有 tool 模块触发发现流程。
- **Toolset 分组**：工具按 toolset（`web`、`terminal`、`file`、`browser` 等）分组，可针对不同平台启用/禁用。
- **会话持久化**：所有对话存入 SQLite（`hermes_state.py`），支持全文检索与唯一会话标题。JSON 日志写入 `~/.hermes/sessions/`。
- **临时注入（ephemeral injection）**：系统提示与预填消息在 API 调用时注入，从不持久化到数据库或日志。
- **Provider 抽象**：Agent 可对接任意 OpenAI 兼容 API。Provider 解析发生在初始化阶段（Nous Portal OAuth、OpenRouter API key 或自定义 endpoint）。
- **Provider 路由**：使用 OpenRouter 时，config.yaml 中的 `provider_routing` 控制 provider 选择（按吞吐/延迟/价格排序、允许/忽略特定 provider、数据保留策略）。它们作为 `extra_body.provider` 注入 API 请求。

---

## 代码风格

- **PEP 8**，但有实用例外（我们不严格限制行宽）
- **注释**：只在解释不明显的意图、取舍或 API 怪癖时使用。不要叙述代码在做什么 —— `# increment counter` 没有信息量
- **错误处理**：捕获具体异常。使用 `logger.warning()`/`logger.error()` 记录日志 —— 对于意外错误使用 `exc_info=True` 以便堆栈出现在日志中
- **跨平台**：不要假设 Unix。参见 [跨平台兼容性](#cross-platform-compatibility)

---

## 添加一个新 Tool

在写 tool 之前，先问自己： [是不是应该做成 Skill？](#should-it-be-a-skill-or-a-tool)

Tools 会在中央 registry 中自注册。每个 tool 文件把 schema、handler 和注册放在一起：

```python
"""my_tool — 对这个 tool 的简要描述。"""

import json
from tools.registry import registry


def my_tool(param1: str, param2: int = 10, **kwargs) -> str:
    """Handler。返回字符串结果（通常是 JSON）。"""
    result = do_work(param1, param2)
    return json.dumps(result)


MY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "这个 tool 做什么，以及 agent 何时应使用它。",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "param1 是什么"},
                "param2": {"type": "integer", "description": "param2 是什么", "default": 10},
            },
            "required": ["param1"],
        },
    },
}


def _check_requirements() -> bool:
    """如果该 tool 的依赖可用则返回 True。"""
    return True


registry.register(
    name="my_tool",
    toolset="my_toolset",
    schema=MY_TOOL_SCHEMA,
    handler=lambda args, **kw: my_tool(**args, **kw),
    check_fn=_check_requirements,
)
```

然后把 import 添加到 `model_tools.py` 的 `_modules` 列表里：

```python
_modules = [
    # ... existing modules ...
    "tools.my_tool",
]
```

如果这是一个新的 toolset，还需要把它加入 `toolsets.py` 和相关平台的 presets。

---

## 添加一个 Skill

随包技能位于 `skills/`，按类别组织。官方可选技能使用相同结构，位于 `optional-skills/`：

```
skills/
├── research/
│   └── arxiv/
│       ├── SKILL.md              # 必需：主说明
│       └── scripts/              # 可选：辅助脚本
│           └── search_arxiv.py
├── productivity/
│   └── ocr-and-documents/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── ...
```

### SKILL.md 格式

```markdown
---
name: my-skill
description: 简短描述（在 skill 搜索结果中展示）
version: 1.0.0
author: Your Name
license: MIT
platforms: [macos, linux]          # 可选 — 限制特定 OS 平台
                                   #   有效值：macos、linux、windows
                                   #   省略则在所有平台加载（默认）
required_environment_variables:    # 可选 — 安全的“加载时设置”元数据
  - name: MY_API_KEY
    prompt: API key
    help: 获取方式
    required_for: full functionality
prerequisites:                     # 可选：旧版运行时要求
  env_vars: [MY_API_KEY]           #   required env vars 的向后兼容别名
  commands: [curl, jq]             #   仅提示；不会隐藏该 skill
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    fallback_for_toolsets: [web]       # 可选 — 仅当 toolset 不可用时显示
    requires_toolsets: [terminal]      # 可选 — 仅当 toolset 可用时显示
---

# Skill 标题

简短介绍。

## 何时使用
触发条件 —— agent 什么时候应该加载该 skill？

## 快速参考
常用命令或 API 调用表格。

## 流程
agent 遵循的分步说明。

## 陷阱
已知失败模式与处理方式。

## 验证
agent 如何确认结果正确。
```

### 平台特定 Skill

Skill 可以通过 frontmatter 字段 `platforms` 声明其支持的 OS 平台。带该字段的技能会在不兼容的平台上自动从系统提示、`skills_list()` 和 slash 命令中隐藏。

```yaml
platforms: [macos]            # 仅 macOS（例如 iMessage、Apple Reminders）
platforms: [macos, linux]     # macOS 与 Linux
platforms: [windows]          # 仅 Windows
```

如果该字段省略或为空，skill 会在所有平台加载（向后兼容）。可参考 `skills/apple/` 中 macOS-only 的示例。

### 条件式 Skill 激活

Skill 可以声明条件，用于控制它们在系统提示中出现的时机，依据当前会话可用的 tools 与 toolsets。这个机制主要用于 **fallback skills** —— 只有在主要 tool 不可用时才展示的替代方案。

在 `metadata.hermes` 下支持四个字段：

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # 仅当这些 toolsets 不可用时显示
    requires_toolsets: [terminal]     # 仅当这些 toolsets 可用时显示
    fallback_for_tools: [web_search]  # 仅当这些 tools 不可用时显示
    requires_tools: [terminal]        # 仅当这些 tools 可用时显示
```

**语义：**
- `fallback_for_*`：该 skill 是备选方案。当列出的 tools/toolsets 可用时 **隐藏**，不可用时 **显示**。适用于高级工具的免费替代。
- `requires_*`：该 skill 需要某些 tools 才能工作。当列出的 tools/toolsets 不可用时 **隐藏**。适用于依赖特定能力的技能（例如必须有 terminal 才有意义的技能）。
- 如果两者都指定，则两类条件都必须满足该 skill 才会出现。
- 如果都未指定，则该 skill 始终显示（向后兼容）。

**示例：**

```yaml
# DuckDuckGo 搜索 — 当 Firecrawl（web toolset）不可用时显示
metadata:
  hermes:
    fallback_for_toolsets: [web]

# 智能家居技能 — 仅在 terminal 可用时有意义
metadata:
  hermes:
    requires_toolsets: [terminal]

# 本地浏览器 fallback — 当 Browserbase 不可用时显示
metadata:
  hermes:
    fallback_for_toolsets: [browser]
```

过滤发生在 `agent/prompt_builder.py` 的提示构建阶段。`build_skills_system_prompt()` 会从 agent 获取可用 tools 与 toolsets 集合，并使用 `_skill_should_show()` 评估每个技能的条件。

### Skill setup 元数据

Skill 可以通过 frontmatter 字段 `required_environment_variables` 声明安全的“加载时设置”元数据。缺失值不会影响 skill 的可发现性；当 skill 实际被加载时，会在 CLI 中触发安全提示。

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: 从 https://developers.google.com/tenor 获取 key
    required_for: full functionality
```

用户可以跳过设置并继续加载 skill。Hermes 只向模型暴露元数据（`stored_as`、`skipped`、`validated`），绝不会暴露 secret 的实际值。

旧字段 `prerequisites.env_vars` 仍受支持，并会被标准化成新表示。

```yaml
prerequisites:
  env_vars: [TENOR_API_KEY]       # required_environment_variables 的旧别名
  commands: [curl, jq]            # 仅提示：CLI 检查建议
```

Gateway 和消息会话从不在对话中收集 secrets；它们会指导用户在本地运行 `hermes setup` 或更新 `~/.hermes/.env`。

**何时声明 required environment variables：**
- 该 skill 使用应当安全采集的 API key 或 token，并希望在加载时提示设置
- 用户即便跳过设置 skill 仍可能有用，但会优雅降级

**何时声明 command prerequisites：**
- 该 skill 依赖某个可能未安装的 CLI 工具（例如 `himalaya`、`openhue`、`ddgs`）
- 把命令检查视为指导，而不是“发现阶段的隐藏条件”

可参考 `skills/gifs/gif-search/` 和 `skills/email/himalaya/` 的示例。

### Skill 编写指南

- **除非绝对必要，不要引入外部依赖。** 优先使用 Python 标准库、curl，以及现有 Hermes tools（`web_extract`、`terminal`、`read_file`）。
- **渐进式披露（progressive disclosure）。** 把最常用的工作流放在最前面。边缘情况与高级用法放在后面。
- **提供辅助脚本** 用于 XML/JSON 解析或复杂逻辑 —— 不要期待 LLM 每次都能在对话中临时写出解析器。
- **测试。** 运行 `hermes --toolsets skills -q "Use the X skill to do Y"`，并验证 agent 按指令正确执行。

---

## 添加皮肤 / 主题

Hermes 使用数据驱动的皮肤系统 —— 添加新皮肤无需改代码。

**方案 A：用户皮肤（YAML 文件）**

创建 `~/.hermes/skins/<name>.yaml`：

```yaml
name: mytheme
description: 主题的简短描述

colors:
  banner_border: "#HEX"     # 面板边框颜色
  banner_title: "#HEX"      # 面板标题颜色
  banner_accent: "#HEX"     # 分节标题颜色
  banner_dim: "#HEX"        # 弱化/暗色文本
  banner_text: "#HEX"       # 正文文本颜色
  response_border: "#HEX"   # 回复框边框

spinner:
  waiting_faces: ["(⚔)", "(⛨)"]
  thinking_faces: ["(⚔)", "(⌁)"]
  thinking_verbs: ["forging", "plotting"]
  wings:                     # 可选：左右装饰
    - ["⟪⚔", "⚔⟫"]

branding:
  agent_name: "My Agent"
  welcome: "Welcome message"
  response_label: " ⚔ Agent "
  prompt_symbol: "⚔ ❯ "

tool_prefix: "╎"             # tool 输出行前缀
```

所有字段都是可选的 —— 缺失值会继承默认皮肤。

**方案 B：内置皮肤**

把皮肤加入 `hermes_cli/skin_engine.py` 的 `_BUILTIN_SKINS` 字典。schema 与上面一致，但以 Python dict 表示。内置皮肤会随包发布，始终可用。

**启用方式：**
- CLI：`/skin mytheme` 或在 config.yaml 中设置 `display.skin: mytheme`
- 配置：`display: { skin: mytheme }`

完整 schema 与现有皮肤示例见 `hermes_cli/skin_engine.py`。

---

<a id="cross-platform-compatibility"></a>
## 跨平台兼容性

Hermes 运行在 Linux、macOS 和 Windows。编写涉及操作系统的代码时：

### 关键规则

1. **`termios` 和 `fcntl` 仅 Unix 可用。** 必须同时捕获 `ImportError` 和 `NotImplementedError`：
   ```python
   try:
       from simple_term_menu import TerminalMenu
       menu = TerminalMenu(options)
       idx = menu.show()
   except (ImportError, NotImplementedError):
       # 兜底：Windows 使用编号菜单
       for i, opt in enumerate(options):
           print(f"  {i+1}. {opt}")
       idx = int(input("Choice: ")) - 1
   ```

2. **文件编码。** Windows 可能用 `cp1252` 保存 `.env` 文件。要正确处理编码错误：
   ```python
   try:
       load_dotenv(env_path)
   except UnicodeDecodeError:
       load_dotenv(env_path, encoding="latin-1")
   ```

3. **进程管理。** `os.setsid()`、`os.killpg()` 以及 signal 处理在 Windows 上不同。要做平台判断：
   ```python
   import platform
   if platform.system() != "Windows":
       kwargs["preexec_fn"] = os.setsid
   ```

4. **路径分隔符。** 使用 `pathlib.Path`，不要用字符串拼接 `/`。

5. **安装器里的 shell 命令。** 如果修改了 `scripts/install.sh`，检查是否也需要在 `scripts/install.ps1` 做等价修改。

---

<a id="security-considerations"></a>
## 安全注意事项

Hermes 具备终端访问能力。安全至关重要。

### 现有防护

| 层级 | 实现 |
|-------|---------------|
| **Sudo 密码管道** | 使用 `shlex.quote()` 防止 shell 注入 |
| **危险命令检测** | `tools/approval.py` 中的正则模式 + 用户审批流程 |
| **Cron 提示注入** | `tools/cronjob_tools.py` 中的扫描器会阻止指令覆盖模式 |
| **写入拒绝列表** | 受保护路径（`~/.ssh/authorized_keys`、`/etc/shadow`）通过 `os.path.realpath()` 解析以防 symlink 绕过 |
| **Skills 防护** | hub 安装技能的安全扫描器（`tools/skills_guard.py`） |
| **代码执行沙箱** | `execute_code` 子进程运行时会从环境变量中移除 API keys |
| **容器加固** | Docker：丢弃全部 capabilities、禁止提权、PID 限制、容量受限的 tmpfs |

### 贡献安全敏感代码时

- **插入用户输入到 shell 命令时始终使用 `shlex.quote()`**
- **在基于路径的访问控制检查前用 `os.path.realpath()` 解析 symlink**
- **不要记录 secrets。** API keys、tokens 与密码绝不应出现在日志中
- **在 tool 执行周围捕获更宽的异常**，避免单点失败导致 agent loop 崩溃
- **若修改涉及文件路径、进程管理或 shell 命令**，请在所有平台上测试

如果你的 PR 影响安全，请在描述中明确指出。

---

## Pull Request 流程

### 分支命名

```
fix/description        # Bug 修复
feat/description       # 新功能
docs/description       # 文档
test/description       # 测试
refactor/description   # 重构
```

### 提交前检查

1. **运行测试**：`pytest tests/ -v`
2. **手动测试**：运行 `hermes` 并走一遍你改动的代码路径
3. **检查跨平台影响**：如果涉及文件 I/O、进程管理或终端处理，要考虑 Windows 和 macOS
4. **保持 PR 聚焦**：每个 PR 只做一个逻辑变更。不要把 bug 修复、重构、新功能混在一起

### PR 描述

请包含：
- **改了什么（What）** 以及 **为什么（Why）**
- **如何测试（How to test）**（bug 的复现步骤、功能的用法示例）
- **你测试过的平台（Platforms）**
- 关联相关 issue（如有）

### Commit message

我们使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>
```

| Type | 用途 |
|------|---------|
| `fix` | Bug 修复 |
| `feat` | 新功能 |
| `docs` | 文档 |
| `test` | 测试 |
| `refactor` | 重构（行为不变） |
| `chore` | 构建、CI、依赖更新 |

Scopes：`cli`、`gateway`、`tools`、`skills`、`agent`、`install`、`whatsapp`、`security` 等。

示例：
```
fix(cli): prevent crash in save_config_value when model is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
test(tools): add unit tests for file_operations
```

---

## 报告问题（Issues）

- 使用 [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)
- 请包含：操作系统、Python 版本、Hermes 版本（`hermes version`）、完整错误堆栈
- 请包含复现步骤
- 创建前先检查是否已有相同问题，避免重复
- 安全漏洞请私下报告

---

## 社区

- **Discord**：[discord.gg/NousResearch](https://discord.gg/NousResearch) — 提问、展示项目、分享技能
- **GitHub Discussions**：用于设计提案与架构讨论
- **Skills Hub**：把专用技能上传到注册表并与社区分享

---

## 许可证

提交贡献即表示你同意你的贡献将以 [MIT License](LICENSE) 进行许可。
