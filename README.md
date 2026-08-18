# Give Claude Eyes 👀

**Give eyes to any text-only model in Claude Code.**

If the model behind your Claude Code has no vision (DeepSeek, and many other
text-only LLMs), it cannot see images — no matter whether you paste, drag, or attach
them. This tool bridges that gap: it sends images to **any OpenAI-compatible vision
model you choose** and returns an objective description, so your model can *see* and
then *reason* over the result.

> 🌍 Works in **Claude Code CLI, desktop app, IDE extensions (VS Code / JetBrains),
> and the web app** — on **Windows, macOS, and Linux**. Bring your own API key; no key
> is bundled.

---

## How it works

```
  Your Claude Code (a text-only model)
        │   "I can't see images" → calls the vision tool
        ▼
  Give Claude Eyes
        │   sends image + instruction over a standard OpenAI-compatible API
        ▼
  Your vision model (OpenAI / 豆包 / DeepSeek-VL / Kimi / any compatible endpoint)
        │   returns objective facts only (OCR, objects, counts, colors, boxes…)
        ▼
  Your Claude Code model reasons over those facts
```

The vision model only **extracts** (eyes). Your model only **reasons** (brain). They
never overlap.

---

## Requirements

- **Python 3.8+** (no third-party packages — pure standard library).
- A **vision model API key** from any OpenAI-compatible provider
  (OpenAI, Volcano Ark / 豆包, DeepSeek-VL, Kimi, Moonshot, OpenRouter, a proxy, …).
  You need three values: `base_url`, `model`, and `api_key`.

---

## Install

There are two independent ways. Pick one.

### Way A — Manual install

1. Clone or download this repository.
2. Copy `config.example.json` to `config.json`:
   ```bash
   cp config.example.json config.json
   ```
3. Open `config.json` and replace the placeholders with your own values:
   ```json
   {
     "base_url": "https://api.openai.com/v1",
     "api_key": "sk-...",
     "model": "gpt-4o"
   }
   ```

> `config.json` is listed in `.gitignore` — it will never be committed.

### Way B — Let Claude Code install itself

Paste this into Claude Code (any surface), then answer its questions with your own
`base_url`, `model`, and `api_key`:

```
Please install the "Give Claude Eyes" tool from this repository: <REPO_URL>

1. Clone the repo.
2. Generate the config by running:
   python setup.py --base-url <my base_url> --model <my model> --api-key <my api_key>
   (I will give you these three values.)
3. (Optional) Enable the auto/manual mode reminder: add the SessionStart hook
   (see "SessionStart hook" under "4) Vision mode"), and copy the commands/*.md
   files into ~/.claude/commands/.
```

`setup.py` works **interactively** (run `python setup.py` yourself) or
**non-interactively** (pass the three flags above, which is how Claude Code drives it).

---

## Usage

### 1) Teach your model to use it (one-time)

Add this to your project's `CLAUDE.md` (or your global `~/.claude/CLAUDE.md`):

```markdown
You do not have vision. When the user gives you an image (a path, an attachment,
or a screenshot), do NOT claim you can see it. Instead call the vision tool:

- MCP (if set up): vision_describe <path>  or  vision_batch <folder>
- CLI fallback:   python vision.py <path>

Then reason over the returned description yourself.
```

### 2) CLI (command line)

```bash
# single image, full objective description
python vision.py photo.png

# single image, extract something specific
python vision.py photo.png "OCR all the text"

# batch over a folder
python vision.py images/ "Does each image contain a crack?" --ext .jpg,.png

# batch → structured JSON → file
python vision.py images/ "output JSON: main color and shape" --json --out results.json
```

CLI options:

| Option | Meaning | Default |
|---|---|---|
| `--ext` | comma-separated extensions in batch mode | `.png,.jpg,.jpeg,.webp,.gif,.bmp` |
| `--max-batch N` | max images in batch mode (0 = unlimited) | `0` |
| `--json` | output a JSON array (`file` + `data`/`content`) | off |
| `--out FILE` | write results to a file | stdout |

### 3) MCP (native tool inside Claude Code)

Configure it as a stdio server. Either run `/mcp` in Claude Code, or add a
`.mcp.json` to your project root:

```json
{
  "mcpServers": {
    "give-claude-eyes": {
      "command": "python",
      "args": ["/absolute/path/to/give-claude-eyes/mcp_server.py"]
    }
  }
}
```

> On macOS/Linux, use `"python3"` if `python` is not on your PATH.

Two tools become available: `vision_describe` (single image) and `vision_batch`
(folder).

### 4) Vision mode: auto / manual

Control *when* the vision tool is called:

- **auto** (default) — call it yourself whenever an image is relevant.
- **manual** — only call it when the user explicitly asks.

Switch at any time, in two ways:

- Slash commands: `/vision-auto` and `/vision-manual` (after installing the
  `commands/` files), or just say **"auto"** / **"manual"**.
- The **launcher** (terminal only): an up/down arrow menu that writes `mode.txt`
  before starting Claude Code.

```bash
# Windows
ccstart.bat

# macOS (double-clickable)
./ccstart.command

# Linux / macOS terminal
./ccstart.sh
```

> The `.bat` launcher uses `python`; the `.command` and `.sh` launchers use
> `python3` (macOS ships `python3`, not `python`). Adjust if your interpreter is
> named differently.

#### SessionStart hook (optional)

To see the current vision mode at the start of every session, add a SessionStart
hook that runs `hook.py` (it reads `mode.txt` and prints the mode). In
`~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"/absolute/path/to/give-claude-eyes/hook.py\""
          }
        ]
      }
    ]
  }
}
```

> Use `python3` on macOS/Linux if `python` is not on your PATH. `hook.py` defaults
> to `auto` when `mode.txt` is missing (the launcher creates it automatically).

---

## Configuration

`config.json` (or environment variables, which take precedence):

| Config field | Env var | Meaning |
|---|---|---|
| `base_url` | `VISION_BASE_URL` | OpenAI-compatible endpoint, e.g. `https://api.openai.com/v1` |
| `model` | `VISION_MODEL` | model id, e.g. `gpt-4o`, `doubao-seed-2-1-pro-260628` |
| `api_key` | `VISION_API_KEY` | your API key |

---

## Security

- `config.json` holds your real API key in plain text **on your machine only**.
  It is git-ignored — never commit it, and never share it.
- The repository ships **no key of any kind**.

## License

[MIT](LICENSE)
