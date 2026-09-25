"""Pluggable retrieval strategies for matching BOQ rows to extracted tender items.

The original system matched descriptions with a token-overlap score. That score
is explainable and cheap, but it cannot see past wording: "Reinforcement steel"
and "Rebar supply and fixing" share almost no tokens while describing the same
work. This module keeps the original strategy available and adds semantic and
hybrid strategies so the choice can be made on measured evidence instead of
assumption.

Every strategy ranks the same candidate list and returns the same shape, so the
evaluation harness treats them interchangeably.
"""

import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv

from comparison import match_score

load_dotenv()

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CACHE_PATH = Path("data/embedding_cache.json")
DEFAULT_FUSION_K = 60


def cosine_similarity(left, right):
    """Cosine similarity between two vectors of equal length."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


class Embedder:
    """Embeds text with the OpenAI embeddings API and caches vectors on disk.

    Caching keeps repeated evaluation runs free and makes a published result
    reproducible by a reviewer who has no API key. Rounding keeps the cache
    small without changing which candidate ranks first.
    """

    def __init__(self, model=None, api_key=None, cache_path=DEFAULT_CACHE_PATH):
        self.model = model or os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.cache_path = Path(cache_path)
        self._cache = self._load_cache()
        self._client = None

    def _load_cache(self):
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as file:
            json.dump(self._cache, file)

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Embedding strategies need an API key, "
                    "or a populated data/embedding_cache.json from an earlier run."
                )
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def embed(self, texts):
        """Return {text: vector} for every input, requesting only cache misses."""
        missing = [text for text in dict.fromkeys(texts) if text not in self._cache]
        if missing:
            client = self._get_client()
            for start in range(0, len(missing), 256):
                batch = missing[start : start + 256]
                response = client.embeddings.create(model=self.model, input=batch)
                ordered = sorted(response.data, key=lambda item: item.index)
                for text, item in zip(batch, ordered):
                    self._cache[text] = [round(value, 5) for value in item.embedding]
            self._save_cache()
        return {text: self._cache[text] for text in texts}


def rank_token_overlap(query, candidates):
    """Baseline lexical strategy. Reuses the score already in comparison.py."""
    scored = [(candidate["description"], match_score(query, candidate["description"])) for candidate in candidates]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def rank_embedding(query, candidates, embedder):
    """Semantic strategy. Purely lexical scorer replaced by vector similarity."""
    vectors = embedder.embed([query] + [candidate["description"] for candidate in candidates])
    query_vector = vectors.get(query, [])
    scored = [
        (candidate["description"], cosine_similarity(query_vector, vectors.get(candidate["description"], [])))
        for candidate in candidates
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def reciprocal_rank_fusion(rankings, k=DEFAULT_FUSION_K):
    """Fuse ranked lists into one ranking using reciprocal rank fusion.

    RRF combines rankings by position rather than by score, so a lexical score
    and a cosine similarity can be merged without putting them on a comparable
    scale or tuning a weight between them. This is the standard fusion approach
    for hybrid retrieval.
    """
    fused = {}
    for ranking in rankings:
        for rank, (key, _score) in enumerate(ranking, start=1):
            fused[key] = fused.get(key, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda pair: pair[1], reverse=True)


def rank_hybrid(query, candidates, embedder, k=DEFAULT_FUSION_K):
    """Fuse the lexical and semantic rankings rather than blending their scores."""
    return reciprocal_rank_fusion(
        [rank_token_overlap(query, candidates), rank_embedding(query, candidates, embedder)],
        k=k,
    )


def get_ranker(method, embedder=None):
    """Return a ranker callable for a strategy name, or None if unavailable.

    Embedding strategies return None without an embedder so the harness can
    report them as skipped instead of failing the whole run.
    """
    if method == "token_overlap":
        return rank_token_overlap
    if method == "embedding":
        return None if embedder is None else (lambda q, c: rank_embedding(q, c, embedder))
    if method == "hybrid":
        return None if embedder is None else (lambda q, c: rank_hybrid(q, c, embedder))
    raise ValueError(f"Unknown retrieval method: {method}")


def embedder_available(api_key=None, cache_path=DEFAULT_CACHE_PATH):
    """True when embeddings can run, either from an API key or a warm cache."""
    if api_key or os.getenv("OPENAI_API_KEY"):
        return True
    return Path(cache_path).exists()
