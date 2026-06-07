"""
semantic_search.py
==================
Thin wrapper around TurboRag for ZimAgent Desktop.

Handles graceful import failures so the app still launches
when TurboRag is not installed (demo / test mode).
"""

from __future__ import annotations

import logging
import os
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Lazy import guard
# ─────────────────────────────────────────────────────────────

def _try_import_turborag():
    try:
        from turborag import TurboRag
        from turborag.config import TurboRagConfig, EmbedderConfig, LLMConfig, IndexConfig
        from turborag.llm import LLM
        return TurboRag, TurboRagConfig, EmbedderConfig, LLMConfig, IndexConfig, LLM
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────
# SemanticSearch
# ─────────────────────────────────────────────────────────────

class SemanticSearch:
    """Manages a TurboRag index for ZIM article content.

    Parameters
    ----------
    index_path : str
        Path to the .tvim vector index file.
    embed_model : str
        Path to the GGUF embedding model.
    llm_model : str
        Path to the GGUF language model.
    embed_dim : int
        Embedding dimension (must match model output).
    top_k : int
        Default number of search results.
    """

    def __init__(
        self,
        index_path: str,
        embed_model: str,
        llm_model: str = "",
        embed_dim: int = 2048,
        top_k: int = 5,
    ) -> None:
        self.index_path  = index_path
        self.embed_model = embed_model
        self.llm_model   = llm_model
        self.embed_dim   = embed_dim
        self.top_k       = top_k
        self._rag        = None
        self._available  = False

        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _ensure_rag(self) -> Any:
        if self._rag is not None:
            return self._rag

        mods = _try_import_turborag()
        if mods is None:
            logger.warning("TurboRag not installed – running in demo mode")
            self._rag = _DemoRag()
            return self._rag

        TurboRag, TurboRagConfig, EmbedderConfig, LLMConfig, IndexConfig, LLM = mods

        cfg = TurboRagConfig(
            embedder=EmbedderConfig(
                model_path=self.embed_model,
                dim=self.embed_dim,
            ),
            llm=LLMConfig(
                model_path=self.llm_model,
                chat_template="deepseek",
            ),
            index=IndexConfig(
                dim=self.embed_dim,
                bit_width=4,
                index_path=self.index_path,
                docstore_path=self.index_path.replace(".tvim", "_docs.db"),
            ),
            top_k=self.top_k,
        )
        llm = LLM.from_config(cfg.llm) if self.llm_model else None
        self._rag = TurboRag(config=cfg, llm=llm)
        self._available = True
        logger.info("TurboRag initialised (index=%s)", self.index_path)
        return self._rag

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        return self._available

    def add_document(self, text: str, metadata: dict) -> None:
        self._ensure_rag().add_document(text, metadata)

    def add_documents(self, texts: List[str], metadatas: List[dict]) -> None:
        self._ensure_rag().add_documents(texts, metadatas)

    def save(self) -> None:
        try:
            self._ensure_rag().save()
        except Exception as exc:
            logger.warning("Save failed: %s", exc)

    def search(self, query: str, k: Optional[int] = None) -> List[dict]:
        """Return list of {title, path, score, snippet} dicts."""
        hits = self._ensure_rag().search(query, k=k or self.top_k)
        results = []
        for hit in hits:
            meta = getattr(hit, "metadata", {}) or {}
            results.append({
                "title":   meta.get("title",   getattr(hit, "title",   "?")),
                "path":    meta.get("path",    getattr(hit, "path",    "")),
                "score":   float(getattr(hit,  "score",  0.0)),
                "snippet": str(getattr(hit, "text", ""))[:120],
            })
        return results

    def ask(self, question: str, k: Optional[int] = None) -> tuple[str, list]:
        """Return (answer_str, source_list)."""
        try:
            ans, sources = self._ensure_rag().ask(question, k=k or self.top_k)
            return ans, sources
        except Exception as exc:
            return f"Error: {exc}", []

    def stats(self) -> dict:
        try:
            return self._ensure_rag().stats()
        except Exception:
            return {"index": self.index_path, "available": self._available}


# ─────────────────────────────────────────────────────────────
# Demo / fallback stub
# ─────────────────────────────────────────────────────────────

class _DemoRag:
    """Returned when TurboRag is not installed."""

    def add_document(self, *a, **kw): pass
    def add_documents(self, *a, **kw): pass
    def save(self): pass

    def search(self, query: str, k: int = 5):
        class Hit:
            title    = f"[Demo] {query}"
            path     = "A/demo"
            score    = 0.85
            text     = "TurboRag not installed – install with: pip install turborag-ahx47"
            metadata = {}
        return [Hit()]

    def ask(self, question: str, k: int = 5):
        return (
            "TurboRag is not installed.\n\n"
            "Install it with:\n"
            "    pip install turborag-ahx47\n\n"
            "Then place GGUF models in the models/ folder and re-index.",
            [],
        )

    def stats(self):
        return {"status": "demo_mode", "turborag": "not_installed"}
