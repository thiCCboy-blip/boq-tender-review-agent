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
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv

from comparison import match_score, tokenize

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


class Embedder(ABC):
    """Caches text vectors on disk so repeated runs are free and reproducible.

    Caching also means a published result can be re-verified by a reviewer
    with no API access at all, which is why the cache is a real part of the
    evaluation design rather than an optimisation.
    """

    def __init__(self, model=None, cache_path=DEFAULT_CACHE_PATH):
        self.model = model or self.default_model()
        self.cache_path = Path(cache_path)
        self._cache = self._load_cache()

    @classmethod
    def default_model(cls):
        return DEFAULT_EMBEDDING_MODEL

    @abstractmethod
    def _fetch(self, texts):
        """Return {text: vector} for the given texts from the live backend."""

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

    def embed(self, texts):
        """Return {text: vector} for every input, requesting only cache misses."""
        missing = [text for text in dict.fromkeys(texts) if text not in self._cache]
        if missing:
            for text, vector in self._fetch(missing).items():
                self._cache[text] = [round(value, 5) for value in vector]
            self._save_cache()
        return {text: self._cache[text] for text in texts}


class OpenAIEmbedder(Embedder):
    """Embedding backend using the OpenAI embeddings API."""

    def __init__(self, model=None, api_key=None, cache_path=DEFAULT_CACHE_PATH):
        self._api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self._client = None
        super().__init__(model=model, cache_path=cache_path)

    @classmethod
    def default_model(cls):
        return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Use another embedding backend or a "
                    "populated data/embedding_cache.json from an earlier run."
                )
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def _fetch(self, texts):
        client = self._get_client()
        vectors = {}
        for start in range(0, len(texts), 256):
            batch = texts[start : start + 256]
            response = client.embeddings.create(model=self.model, input=batch)
            for text, item in zip(batch, sorted(response.data, key=lambda row: row.index)):
                vectors[text] = item.embedding
        return vectors


class TfidfEmbedder(Embedder):
    """Dependency-free lexical baseline using TF-IDF over a fixed corpus.

    Not semantic: it cannot relate "reinforcement" to "rebar". Its purpose is
    to separate two questions that a single baseline conflates. Comparing
    naive token overlap against TF-IDF shows how much of the gap is just
    better weighting, and comparing TF-IDF against a semantic model shows
    how much genuinely requires semantics.
    """

    def __init__(self, corpus=None, cache_path=DEFAULT_CACHE_PATH):
        self._corpus = list(corpus or [])
        super().__init__(cache_path=cache_path)

    @classmethod
    def default_model(cls):
        return "tfidf"

    def _fetch(self, texts):
        documents = self._corpus + texts
        document_frequency = {}
        for document in documents:
            for term in set(tokenize(document)):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        total = len(documents)

        # Vectors must share one vocabulary, otherwise cosine similarity would
        # compare unrelated terms that happen to sit at the same index.
        vocabulary = sorted({term for document in documents for term in tokenize(document)})

        vectors = {}
        for text in texts:
            counts = {}
            for term in tokenize(text):
                counts[term] = counts.get(term, 0) + 1
            vectors[text] = [
                self._weight(counts, term, document_frequency, total) if term in counts else 0.0
                for term in vocabulary
            ]
        return vectors

    @staticmethod
    def _weight(counts, term, document_frequency, total):
        inverse = math.log((1 + total) / (1 + document_frequency.get(term, 0))) + 1.0
        return counts[term] * inverse

    def embed(self, texts):
        # The cache is not reused across corpora, so a stale vector set cannot
        # silently produce a wrong score for a different fixture.
        self._cache = {}
        return super().embed(texts)


def build_tfidf_embedder(cases, cache_path=DEFAULT_CACHE_PATH):
    """Build a TF-IDF embedder whose corpus is every candidate in the fixture."""
    corpus = []
    for case in cases:
        corpus.extend(item["description"] for item in case["candidates"])
        corpus.append(case["query"])
    return TfidfEmbedder(corpus=corpus, cache_path=cache_path)


def rank_token_overlap(query, candidates):
    """Baseline lexical strategy. Reuses the score already in comparison.py."""
    scored = [(candidate["description"], match_score(query, candidate["description"])) for candidate in candidates]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def rank_by_vector(query, candidates, embedder):
    """Rank candidates by cosine similarity between cached text vectors."""
    vectors = embedder.embed([query] + [candidate["description"] for candidate in candidates])
    query_vector = vectors.get(query, [])
    scored = [
        (candidate["description"], cosine_similarity(query_vector, vectors.get(candidate["description"], [])))
        for candidate in candidates
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


# Semantic when the backend is an embedding model, lexical when it is TF-IDF.
# The harness reports which backend produced each row.
rank_embedding = rank_by_vector
rank_tfidf = rank_by_vector


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


VECTOR_RANKERS = {"embedding": rank_by_vector, "tfidf": rank_by_vector}


def get_ranker(method, embedder=None):
    """Return a ranker callable for a strategy name, or None if unavailable.

    Vector strategies return None without an embedder so the harness can
    report them as skipped instead of failing the whole run.
    """
    if method == "token_overlap":
        return rank_token_overlap
    if method in VECTOR_RANKERS:
        return None if embedder is None else (lambda q, c: VECTOR_RANKERS[method](q, c, embedder))
    if method in ("hybrid", "hybrid_tfidf"):
        return None if embedder is None else (lambda q, c: rank_hybrid(q, c, embedder))
    raise ValueError(f"Unknown retrieval method: {method}")


def build_embedder(method, cases, api_key=None, cache_path=DEFAULT_CACHE_PATH):
    """Construct the backend a strategy needs, or None when it is unavailable.

    Returning None rather than raising lets the harness report an unavailable
    strategy alongside the results that did run.
    """
    try:
        if method == "tfidf":
            return build_tfidf_embedder(cases, cache_path=cache_path)
        if method in ("embedding", "hybrid", "hybrid_tfidf"):
            return OpenAIEmbedder(api_key=api_key, cache_path=cache_path)
    except Exception:  # noqa: BLE001 - availability is the caller's decision
        return None
    return None
