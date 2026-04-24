import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - allow runtime without model installed
    SentenceTransformer = None  # type: ignore

try:
    from openai import OpenAI  # Qwen via OpenAI-compatible API
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class EmbeddingModelSingleton:
    _instance_lock: threading.Lock = threading.Lock()
    _model: Optional[Any] = None

    @classmethod
    def get_model(cls) -> Optional[Any]:
        if cls._model is not None:
            return cls._model
        with cls._instance_lock:
            if cls._model is None and SentenceTransformer is not None:
                # Lightweight, widely available model
                cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model


class MCPToolRouter:
    def __init__(self, registry_path: Optional[str] = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.registry_path = (
            Path(registry_path)
            if registry_path
            else base_dir / "data" / "mcp_tools_registry.json"
        )
        self._tools: List[Dict[str, Any]] = []
        self._embeddings: Optional[List[List[float]]] = None
        self._embedder = EmbeddingModelSingleton.get_model()
        # Optional LLM client for CoT intent extraction (Qwen via DashScope compatible endpoint)
        self._llm: Optional[Any] = None
        self._llm_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("DASHSCOPE_COMPAT_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        if OpenAI is not None and api_key:
            try:
                self._llm = OpenAI(api_key=api_key, base_url=base_url)
            except Exception:
                self._llm = None
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            self._tools = []
            self._embeddings = None
            return
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Registry JSON must be a list of tool metadata")
        self._tools = data
        self._build_embeddings()

    def _tool_corpus_text(self, tool: Dict[str, Any]) -> str:
        parts: List[str] = []
        for key in ("name", "description"):
            val = tool.get(key)
            if isinstance(val, str):
                parts.append(val)
        for key in ("tags", "capabilities", "domains"):
            arr = tool.get(key, [])
            if isinstance(arr, list):
                parts.extend([str(x) for x in arr])
        examples = tool.get("examples", [])
        if isinstance(examples, list):
            for ex in examples:
                if isinstance(ex, dict):
                    inp = ex.get("input")
                    if isinstance(inp, dict):
                        parts.append(json.dumps(inp, ensure_ascii=False))
        return " \n ".join(parts)

    def _build_embeddings(self) -> None:
        if self._embedder is None:
            # No embedder available, skip precompute
            self._embeddings = None
            return
        corpus = [self._tool_corpus_text(t) for t in self._tools]
        if not corpus:
            self._embeddings = []
            return
        self._embeddings = self._embedder.encode(corpus, convert_to_numpy=False)  # type: ignore

    def _semantic_scores(self, query: str) -> List[Tuple[int, float]]:
        if self._embedder is None or not self._tools:
            # Fallback: simple keyword overlap score
            q_tokens = set(query.lower().split())
            scores: List[Tuple[int, float]] = []
            for i, t in enumerate(self._tools):
                text = self._tool_corpus_text(t).lower()
                score = sum(1.0 for tok in q_tokens if tok in text)
                scores.append((i, float(score)))
            return scores

        query_vec = self._embedder.encode([query], convert_to_numpy=False)[0]  # type: ignore
        # Cosine similarity without numpy dependency
        def cosine(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return (dot / (na * nb)) if na > 0 and nb > 0 else 0.0

        scores: List[Tuple[int, float]] = []
        assert self._embeddings is not None
        for i, emb in enumerate(self._embeddings):
            scores.append((i, cosine(query_vec, emb)))
        return scores

    def _llm_intent_filters(self, query: str) -> Dict[str, Any]:
        """Use CoT prompting to extract intent and structured filters.

        Returns keys: include_tags, include_domains, must_names, must_capabilities
        """
        if self._llm is None:
            return {}
        system = (
            "You are a tool routing planner. Extract high-level intent from the user's request, "
            "then propose concise filters to select tools: relevant tags, domains, must-have capabilities, "
            "and any likely tool name keywords. Respond in compact JSON with keys include_tags, include_domains, "
            "must_capabilities, must_names. Keep arrays short (<=5)."
        )
        user = (
            f"User request: {query}\n"
            "Output JSON only. Example: {\n"
            "  \"include_tags\":[\"weather\",\"transport\"],\n"
            "  \"include_domains\":[\"travel\"],\n"
            "  \"must_capabilities\":[\"get_forecast\",\"route_planning\"],\n"
            "  \"must_names\":[\"hotel\",\"flight\"]\n"
            "}"
        )
        try:
            resp = self._llm.chat.completions.create(  # type: ignore
                model=self._llm_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = resp.choices[0].message.content if resp and resp.choices else "{}"
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
        return {}

    def _apply_cot_prefilter(self, query: str) -> List[int]:
        """Use LLM-extracted filters to narrow down tool indices.
        If LLM unavailable or returns empty, fall back to all tools.
        """
        if not self._tools:
            return []
        filters = self._llm_intent_filters(query)
        if not filters:
            return list(range(len(self._tools)))
        include_tags = [str(x).lower() for x in filters.get("include_tags", []) or []]
        include_domains = [str(x).lower() for x in filters.get("include_domains", []) or []]
        must_caps = [str(x).lower() for x in filters.get("must_capabilities", []) or []]
        must_names = [str(x).lower() for x in filters.get("must_names", []) or []]

        def match(tool: Dict[str, Any]) -> bool:
            # tags/domains as soft includes (any match)
            if include_tags:
                tags = [str(x).lower() for x in tool.get("tags", [])]
                if not any(t in tags for t in include_tags):
                    return False
            if include_domains:
                domains = [str(x).lower() for x in tool.get("domains", [])]
                if not any(d in domains for d in include_domains):
                    return False
            # must capabilities: all required
            if must_caps:
                caps = [str(x).lower() for x in tool.get("capabilities", [])]
                for c in must_caps:
                    if c not in caps:
                        return False
            # name keywords: any match in name or description
            if must_names:
                name = str(tool.get("name", "")).lower()
                desc = str(tool.get("description", "")).lower()
                if not any((n in name) or (n in desc) for n in must_names):
                    return False
            return True

        indices: List[int] = []
        for i, t in enumerate(self._tools):
            if match(t):
                indices.append(i)
        # If filters are too restrictive, fallback to all tools to avoid empty set
        return indices if indices else list(range(len(self._tools)))

    def _apply_struct_filters(
        self,
        tools: List[Tuple[int, float]],
        include_tags: Optional[List[str]] = None,
        include_domains: Optional[List[str]] = None,
        safety_levels: Optional[List[str]] = None,
    ) -> List[Tuple[int, float]]:
        def ok(tool: Dict[str, Any]) -> bool:
            if include_tags:
                tags = [str(x).lower() for x in tool.get("tags", [])]
                if not any(t in tags for t in [x.lower() for x in include_tags]):
                    return False
            if include_domains:
                domains = [str(x).lower() for x in tool.get("domains", [])]
                if not any(d in domains for d in [x.lower() for x in include_domains]):
                    return False
            if safety_levels:
                if str(tool.get("safety_level", "low")).lower() not in [x.lower() for x in safety_levels]:
                    return False
            return True

        filtered: List[Tuple[int, float]] = []
        for idx, score in tools:
            t = self._tools[idx]
            if ok(t):
                filtered.append((idx, score))
        return filtered

    def select_top_k(
        self,
        query: str,
        k: int = 20,
        include_tags: Optional[List[str]] = None,
        include_domains: Optional[List[str]] = None,
        safety_levels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if not self._tools:
            return []
        # CoT intent narrowing to candidate indices
        candidate_indices = self._apply_cot_prefilter(query)
        # Compute scores only for candidates
        full_scores = self._semantic_scores(query)
        # Filter to candidates
        scores = [(idx, sc) for (idx, sc) in full_scores if idx in set(candidate_indices)]
        # Optional additional structured filtering
        scores = self._apply_struct_filters(scores, include_tags, include_domains, safety_levels)
        # Sort by score desc
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[: max(1, k)]
        result: List[Dict[str, Any]] = []
        for idx, score in top:
            tool = dict(self._tools[idx])
            tool["_score"] = float(score)
            result.append(tool)
        return result

    def diagnose_selection(
        self,
        query: str,
        k: int = 20,
        include_tags: Optional[List[str]] = None,
        include_domains: Optional[List[str]] = None,
        safety_levels: Optional[List[str]] = None,
        show_candidates: int = 30,
    ) -> Dict[str, Any]:
        """Return LLM filters, candidate tools after CoT prefilter, and final selection.

        Useful for debugging whether LLM-based filtering is narrowing to relevant tools
        before semantic ranking.
        """
        filters = self._llm_intent_filters(query)
        candidate_indices = self._apply_cot_prefilter(query)
        candidate_names = [self._tools[i].get("name") for i in candidate_indices[: max(1, show_candidates)]]
        selected = self.select_top_k(
            query=query,
            k=k,
            include_tags=include_tags,
            include_domains=include_domains,
            safety_levels=safety_levels,
        )
        return {
            "filters": filters,
            "candidate_count": len(candidate_indices),
            "candidate_preview": candidate_names,
            "selected": selected,
        }


