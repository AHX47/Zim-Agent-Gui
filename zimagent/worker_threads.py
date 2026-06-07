"""
worker_threads.py
=================
QThread workers for background operations:
  – IndexWorker   : Iterates ZIM articles and indexes them via TurboRag
  – MCPWorker     : Runs the FastMCP server in a background thread
  – SearchWorker  : Runs a semantic query without blocking the UI
  – StatsWorker   : Periodic CPU/RAM sampling
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Indexing worker
# ─────────────────────────────────────────────────────────────

class IndexWorker(QThread):
    """Index a ZIM file with TurboRag.

    Signals
    -------
    progress(int, int, str)   : current article, total articles, message
    chunk_count(int)          : total chunks added so far
    finished(int)             : total chunks when done
    error(str)                : error message
    """

    progress   = pyqtSignal(int, int, str)   # (current, total, msg)
    chunk_count = pyqtSignal(int)
    finished_sig = pyqtSignal(int)
    error      = pyqtSignal(str)

    def __init__(
        self,
        zim_path: str,
        index_path: str,
        embed_model: str,
        max_articles: Optional[int] = None,
        chunk_size: int = 400,
        parent=None,
    ):
        super().__init__(parent)
        self.zim_path    = zim_path
        self.index_path  = index_path
        self.embed_model = embed_model
        self.max_articles = max_articles
        self.chunk_size  = chunk_size
        self._stop_flag  = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        try:
            self._do_index()
        except Exception as exc:
            logger.exception("IndexWorker error")
            self.error.emit(str(exc))

    def _do_index(self):
        from .zim_reader import ZimReader

        reader = ZimReader(self.zim_path)
        try:
            reader.open()
        except Exception as exc:
            self.error.emit(f"Cannot open ZIM: {exc}")
            return

        # Attempt to load TurboRag
        try:
            from turborag import TurboRag
            from turborag.config import TurboRagConfig, EmbedderConfig, LLMConfig, IndexConfig
            cfg = TurboRagConfig(
                embedder=EmbedderConfig(model_path=self.embed_model, dim=2048),
                llm=LLMConfig(model_path="", chat_template="none"),
                index=IndexConfig(
                    dim=2048,
                    bit_width=4,
                    index_path=self.index_path,
                    docstore_path=self.index_path.replace(".tvim", "_docs.db"),
                ),
                top_k=5,
            )
            rag = TurboRag(config=cfg, llm=None)
        except ImportError:
            # Fallback: mock rag for demo mode
            rag = _MockRag()

        total = reader.article_count or 9999
        chunks_total = 0
        count = 0

        for article in reader.iter_articles(max_articles=self.max_articles):
            if self._stop_flag:
                break
            self.progress.emit(count, total, article.title[:60])
            try:
                chunks = _chunk_text(article.text, self.chunk_size, 80)
                if not chunks:
                    continue
                metas = [
                    {"title": article.title, "path": article.path, "chunk": i}
                    for i in range(len(chunks))
                ]
                rag.add_documents(chunks, metas)
                chunks_total += len(chunks)
                self.chunk_count.emit(chunks_total)
            except Exception:
                pass
            count += 1

        try:
            rag.save()
        except Exception:
            pass

        reader.close()
        self.finished_sig.emit(chunks_total)


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i : i + size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


class _MockRag:
    """Stand-in when TurboRag is not installed."""
    def add_documents(self, docs, metas): pass
    def save(self): pass


# ─────────────────────────────────────────────────────────────
# MCP Server worker
# ─────────────────────────────────────────────────────────────

class MCPWorker(QThread):
    """Run the FastMCP server in a background thread.

    Signals
    -------
    started_sig(str)  : emitted when the server starts, with address
    stopped_sig()     : emitted after the server stops
    log_line(str)     : log messages from the server
    error(str)        : error string if startup fails
    """

    started_sig = pyqtSignal(str)
    stopped_sig = pyqtSignal()
    log_line    = pyqtSignal(str)
    error       = pyqtSignal(str)

    def __init__(
        self,
        zim_path: str,
        overlay_path: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 8002,
        transport: str = "sse",
        parent=None,
    ):
        super().__init__(parent)
        self.zim_path     = zim_path
        self.overlay_path = overlay_path
        self.host         = host
        self.port         = port
        self.transport    = transport
        self._server      = None
        self._stop_event  = threading.Event()

    def stop(self):
        self._stop_event.set()
        if self._server:
            try:
                self._server.should_exit = True
            except Exception:
                pass
        self.quit()

    def run(self):
        try:
            from .mcp_server import create_zim_mcp_server
        except ImportError as exc:
            self.error.emit(f"MCP server import failed: {exc}")
            return

        try:
            mcp = create_zim_mcp_server(self.zim_path, self.overlay_path)
            addr = f"{self.host}:{self.port}"
            self.log_line.emit(f"[MCP] Server starting on {self.transport.upper()} {addr}")
            self.started_sig.emit(addr)

            if self.transport == "sse":
                mcp.run(transport="sse", host=self.host, port=self.port)
            else:
                mcp.run(transport="stdio")
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.stopped_sig.emit()


# ─────────────────────────────────────────────────────────────
# Search worker
# ─────────────────────────────────────────────────────────────

class SearchWorker(QThread):
    """Run a semantic search query without blocking the UI.

    Signals
    -------
    results(list)  : list of result dicts {title, path, score, snippet}
    answer(str)    : LLM-generated answer
    error(str)     : error message
    """

    results = pyqtSignal(list)
    answer  = pyqtSignal(str)
    error   = pyqtSignal(str)

    def __init__(
        self,
        query: str,
        index_path: str,
        embed_model: str,
        llm_model: str,
        top_k: int = 5,
        parent=None,
    ):
        super().__init__(parent)
        self.query       = query
        self.index_path  = index_path
        self.embed_model = embed_model
        self.llm_model   = llm_model
        self.top_k       = top_k

    def run(self):
        try:
            self._do_search()
        except Exception as exc:
            logger.exception("SearchWorker error")
            self.error.emit(str(exc))

    def _do_search(self):
        try:
            from turborag import TurboRag
            from turborag.config import TurboRagConfig, EmbedderConfig, LLMConfig, IndexConfig
            cfg = TurboRagConfig(
                embedder=EmbedderConfig(model_path=self.embed_model, dim=2048),
                llm=LLMConfig(model_path=self.llm_model, chat_template="deepseek"),
                index=IndexConfig(
                    dim=2048, bit_width=4,
                    index_path=self.index_path,
                    docstore_path=self.index_path.replace(".tvim", "_docs.db"),
                ),
                top_k=self.top_k,
            )
            from turborag.llm import LLM
            llm = LLM.from_config(cfg.llm)
            rag = TurboRag(config=cfg, llm=llm)

            hits = rag.search(self.query, k=self.top_k)
            result_list = []
            for hit in hits:
                result_list.append({
                    "title": getattr(hit, "title", "Unknown"),
                    "path":  getattr(hit, "path",  "?"),
                    "score": float(getattr(hit, "score", 0.0)),
                    "snippet": str(getattr(hit, "text", ""))[:120],
                })
            self.results.emit(result_list)

            ans, _ = rag.ask(self.query, k=self.top_k)
            self.answer.emit(ans)
        except ImportError:
            # Demo mode — emit fake results
            time.sleep(0.6)
            self.results.emit([
                {"title": "Demo Result (TurboRag not loaded)",
                 "path": "A/demo", "score": 0.92, "snippet": self.query[:60]},
            ])
            self.answer.emit(
                "TurboRag is not installed or models not found.\n"
                "Install: pip install turborag-ahx47\n"
                "Place GGUF models in the models/ folder."
            )


# ─────────────────────────────────────────────────────────────
# System stats worker
# ─────────────────────────────────────────────────────────────

class StatsWorker(QThread):
    """Emits CPU + RAM usage every N seconds.

    Signals
    -------
    stats(float, float)  : cpu_percent, ram_gb
    """

    stats = pyqtSignal(float, float)

    def __init__(self, interval: float = 2.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self._running = True

    def stop(self):
        self._running = False
        self.quit()

    def run(self):
        while self._running:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().used / (1024 ** 3)
                self.stats.emit(cpu, ram)
            except ImportError:
                self.stats.emit(0.0, 0.0)
            time.sleep(self.interval)
