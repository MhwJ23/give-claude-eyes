# Give Claude Eyes 👀（给 Claude 装一双眼睛）

**给 Claude Code 里任何"没有视觉能力的模型"装上眼睛。**

如果你接进 Claude Code 的模型没有视觉（比如 DeepSeek 等纯文本模型），那它**看不了
图片**——无论你是粘贴、拖拽还是附件，都一样。这个工具补上这块短板：把图片发给
**你自己选择的任意 OpenAI 兼容视觉模型**，拿回客观描述，让你的模型先"看见"、再
"推理"。

> 🌍 适用于 **Claude Code 的 CLI、桌面 App、IDE 插件（VS Code / JetBrains）、网页版**，
> 覆盖 **Windows / macOS / Linux**。自带 API Key 即可使用，仓库**不含任何 Key**。

---

## 工作原理

```
  你的 Claude Code（纯文本模型）
        │    "我看不了图" → 调用识图工具
        ▼
  Give Claude Eyes
        │    把图片 + 指令用标准 OpenAI 兼容接口发出去
        ▼
  你的视觉模型（OpenAI / 豆包 / DeepSeek-VL / Kimi / 任意兼容端点）
        │    只返回客观事实（OCR、物体、数量、颜色、检测框…）
        ▼
  你的 Claude Code 模型基于这些事实继续推理
```

视觉模型只负责**提取**（眼睛），你的模型只负责**推理**（大脑），两者互不越界。

---

## 环境要求

- **Python 3.8+**（零第三方依赖，纯标准库）。
- 任意 OpenAI 兼容视觉模型的 **API Key**（OpenAI、火山方舟/豆包、DeepSeek-VL、Kimi、
  Moonshot、OpenRouter、各类中转站……）。需要三个值：`base_url`、`model`、`api_key`。

---

## 安装

两种方式完全独立，任选其一。

### 方式 A —— 手动安装

1. 克隆或下载本仓库。
2. 复制 `config.example.json` 为 `config.json`：
   ```bash
   cp config.example.json config.json
   ```
3. 打开 `config.json`，把占位符替换成你自己的值：
   ```json
   {
     "base_url": "https://api.openai.com/v1",
     "api_key": "sk-...",
     "model": "gpt-4o"
   }
   ```

> `config.json` 已写入 `.gitignore`，绝不会被提交。

### 方式 B —— 让 Claude Code 自己安装

把下面这段话丢给 Claude Code（任意界面），然后按提示给出你的 `base_url`、`model`、
`api_key`：

```
请从以下仓库安装 "Give Claude Eyes" 工具：<REPO_URL>

1. 克隆仓库。
2. 运行下面的命令生成配置：
   python setup.py --base-url <我的 base_url> --model <我的 model> --api-key <我的 api_key>
   （我会把这三个值告诉你。）
3. （可选）启用自动/手动模式提醒：添加 SessionStart hook（见"4) 识图模式"下的
   "SessionStart hook"小节），并把 commands/*.md 复制到 ~/.claude/commands/。
```

`setup.py` 支持**交互式**（自己跑 `python setup.py`）或**非交互式**（传上面三个参数，
Claude Code 代跑时就用这种方式）。

---

## 使用方法

### 1) 让模型学会用它（一次性设置）

把下面这段加进你项目的 `CLAUDE.md`（或全局 `~/.claude/CLAUDE.md`）：

```markdown
你没有视觉能力。当用户给你一张图（路径、附件或截图）时，不要声称你能看见。
请调用识图工具：

- 已接 MCP：vision_describe <路径>  或  vision_batch <文件夹>
- CLI 兜底：python vision.py <路径>

拿到描述后由你自己完成推理。
```

### 2) CLI（命令行）

```bash
# 单张图片，完整客观描述
python vision.py photo.png

# 单张图片，提取特定内容
python vision.py photo.png "提取图中所有文字"

# 批量识别文件夹
python vision.py images/ "判断每张图是否有裂缝" --ext .jpg,.png

# 批量 → 结构化 JSON → 存盘
python vision.py images/ "每张图输出JSON：主色和形状" --json --out results.json
```

CLI 选项：

| 选项 | 作用 | 默认值 |
|---|---|---|
| `--ext` | 批量时匹配的扩展名，逗号分隔 | `.png,.jpg,.jpeg,.webp,.gif,.bmp` |
| `--max-batch N` | 批量时最多处理 N 张（0=不限） | `0` |
| `--json` | 输出 JSON 数组（`file` + `data`/`content`） | 关闭 |
| `--out FILE` | 结果写入文件 | 打印到屏幕 |

### 3) MCP（Claude Code 里的原生工具）

以 stdio 服务器方式接入。在 Claude Code 里运行 `/mcp`，或在项目根放一个 `.mcp.json`：

```json
{
  "mcpServers": {
    "give-claude-eyes": {
      "command": "python",
      "args": ["/绝对路径/give-claude-eyes/mcp_server.py"]
    }
  }
}
```

> macOS/Linux 上如果 `python` 不在 PATH，请改用 `"python3"`。

接入后得到两个工具：`vision_describe`（单张）和 `vision_batch`（文件夹）。

### 4) 识图模式：自动 / 手动

控制"何时调用识图工具"：

- **自动**（默认）——图片相关时主动调用。
- **手动**——仅在你明确要求时才调用。

随时可切，两种方式：

- 斜杠命令 `/vision-auto`、`/vision-manual`（装好 `commands/` 后可用），或直接说
  **"自动"** / **"手动"**。
- **启动器**（仅终端）：启动 Claude Code 前用上下箭头选模式，写入 `mode.txt`。

```bash
# Windows
ccstart.bat

# macOS（可双击）
./ccstart.command

# Linux / macOS 终端
./ccstart.sh
```

> `.bat` 启动器用 `python`；`.command` 和 `.sh` 启动器用 `python3`（macOS 默认只带
> `python3`、不带 `python`）。如果你的解释器命名不同，请自行调整。

#### SessionStart hook（可选）

想在每次会话开始时看到当前识图模式，就加一个 SessionStart hook 运行 `hook.py`
（它会读取 `mode.txt` 并打印当前模式）。写入 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"/绝对路径/give-claude-eyes/hook.py\""
          }
        ]
      }
    ]
  }
}
```

> macOS/Linux 上如果 `python` 不在 PATH，请改用 `python3`。`mode.txt` 缺失时
> `hook.py` 默认按 `auto` 处理（启动器会自动创建该文件）。

---

## 配置

`config.json`（或环境变量，环境变量优先）：

| 配置字段 | 环境变量 | 含义 |
|---|---|---|
| `base_url` | `VISION_BASE_URL` | OpenAI 兼容端点，如 `https://api.openai.com/v1` |
| `model` | `VISION_MODEL` | 模型 ID，如 `gpt-4o`、`doubao-seed-2-1-pro-260628` |
| `api_key` | `VISION_API_KEY` | 你的 API Key |

---

## 安全

- `config.json` 明文存放你的真实 API Key，**只在你本机**。已被 git 忽略——不要提交、
  不要外泄。
- 仓库本身**不内置任何 Key**。

## 许可证

[MIT](LICENSE)
