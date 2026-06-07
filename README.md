# 🤖 ZimAgent Desktop

**Offline CRUD + Semantic Search for Wikipedia ZIM Archives**

A production-grade PyQt5 desktop application that lets you read, write, edit,
and semantically search any Kiwix `.zim` archive — with local LLM question
answering, animated pipeline visualisation, and a built-in MCP server for
Claude Desktop / LangChain integration.

> Fully offline. No internet connection required after initial model download.

---

## 📸 Screenshot
<img src=zim-agent-gui.png/>

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourname/zim-agent-gui
cd zim-agent-gui

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate.bat      # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Download a ZIM file

```bash
# Small Wikipedia excerpt for testing (~90 MB)
wget https://download.kiwix.org/zim/wikipedia/wikipedia_en_wp1_2023-11.zim \
     -O data/test.zim
```

### 3. Download GGUF Models (for RAG + LLM)

Place models in the `models/` folder:

| File | Purpose | Source |
|------|---------|--------|
| `embeddinggemma-300m-q4_k_m.gguf` | Sentence embeddings | HuggingFace |
| `qwen-0.5b-q4_k_m.gguf`           | Answer generation   | HuggingFace |

```bash
# Install TurboRag
pip install turborag-ahx47
```

### 4. Launch

```bash
python run_app.py
# or
python -m zimagent
```

---

## 📦 File Structure

```
zim-agent-gui/
├── zimagent/                    # Main Python package
│   ├── __init__.py
│   ├── __main__.py              # python -m zimagent
│   ├── main.py                  # App entry-point (QApplication)
│   ├── main_window.py           # Full PyQt5 UI (~600 lines)
│   ├── zim_reader.py            # ZIM article reading (libzim)
│   ├── zim_manager.py           # CRUD + SQLite overlay
│   ├── mcp_server.py            # FastMCP tool server
│   ├── indexer.py               # ZIM → TurboRag indexer
│   ├── agent.py                 # High-level ZimAgent orchestrator
│   ├── semantic_search.py       # TurboRag adapter
│   ├── worker_threads.py        # QThread workers (index, MCP, stats)
│   └── resources/
│       └── style.qss            # Dark cyberpunk QSS theme
│
├── models/                      # GGUF models (user-provided)
│   ├── embeddinggemma-300m-q4_k_m.gguf
│   └── qwen-0.5b-q4_k_m.gguf
│
├── data/                        # ZIM files + index
│
├── scripts/
│   ├── build_exe.bat            # Windows .exe via PyInstaller
│   ├── build_deb.sh             # Linux .deb package
│   └── DEBIAN/control
│
├── run_app.py                   # Standalone launcher
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🧩 Features

### Dashboard
- **ZIM Archive Input & CRUD** — open any `.zim`, see file size + article count
- **Pipeline Visualization** — animated dashed-arrow diagram:
  `ZIM Reader → Chunking → Gemma Embedding → TurboVec Index + SQLite FTS5`
- **Query & Results** — ask a question, see semantic results + LLM answer
- **MCP Server mini-panel** — one-click toggle with live status

### CRUD Operations
- Full article tree (namespaces A/, B/, …)
- HTML viewer (`QWebEngineView` or plain text fallback)
- Write new articles, edit existing, soft-delete with restore
- Every change stored in SQLite overlay (base ZIM untouched)
- Full action log

### Semantic Search
- Semantic search powered by TurboRag vector index
- Relevance bar for each result
- LLM-generated answer with source attribution
- Runs in background thread (UI never blocks)

### MCP Server
- Exposes 8 MCP tools to Claude Desktop / any MCP client
- SSE or stdio transport
- Configurable host + port
- Live server log

---

## ⚙️ Configuration

Open **⚙ Settings** in the sidebar to configure:
- Embedding model path
- LLM model path
- Vector index path

These are saved for the current session (persistent config coming in v1.1).

---

## 📦 Building Installers

### Windows .exe

```bat
pip install pyinstaller
scripts\build_exe.bat
# Output: dist\ZimAgent.exe
```

### Linux .deb

```bash
sudo apt install fakeroot dpkg-dev
bash scripts/build_deb.sh
# Output: zimagent_1.0.0_amd64.deb
sudo dpkg -i zimagent_1.0.0_amd64.deb
```

---

## 🔌 MCP Integration (Claude Desktop)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zimagent": {
      "command": "python",
      "args": ["-m", "zim_agent.mcp_server",
               "--zim", "/path/to/wikipedia.zim",
               "--transport", "stdio"]
    }
  }
}
```

Or start SSE server from the MCP Server tab and connect via:
`http://127.0.0.1:8002/sse`

---

## 📋 MCP Tools Reference

| Tool | Parameters | Description |
|------|-----------|-------------|
| `zim_read_article` | `path` | Read article by URL path |
| `zim_search` | `query, max_results` | Full-text + prefix search |
| `zim_write_article` | `path, title, html` | Create or replace article |
| `zim_edit_article` | `path, new_html, [new_title]` | Edit article content |
| `zim_delete_article` | `path` | Soft-delete article |
| `zim_restore_article` | `path` | Restore deleted article |
| `zim_list_modified` | — | List all overlay changes |
| `zim_stats` | — | Archive + index statistics |

---

## 🧱 Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt5` | GUI framework |
| `PyQtWebEngine` | HTML article rendering |
| `libzim` | ZIM file reading |
| `turborag-ahx47` | Semantic search + RAG |
| `fastmcp` | MCP server |
| `psutil` | CPU/RAM monitoring |

---

## 📄 License

MIT — see [LICENSE](LICENSE).
