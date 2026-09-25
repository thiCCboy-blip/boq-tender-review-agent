import json
import math

import pytest

from retrieval import (
    Embedder,
    OpenAIEmbedder,
    TfidfEmbedder,
    build_embedder,
    build_tfidf_embedder,
    cosine_similarity,
    get_ranker,
    rank_by_vector,
    rank_hybrid,
    rank_token_overlap,
    reciprocal_rank_fusion,
)


def make_candidates(descriptions):
    return [{"description": description, "unit": "m3"} for description in descriptions]


def test_cosine_similarity_identical_vectors():
    assert math.isclose(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_cosine_similarity_handles_mismatched_lengths():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0


def test_cosine_similarity_handles_zero_vector():
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_rank_token_overlap_prefers_shared_tokens():
    ranking = rank_token_overlap("concrete work", make_candidates(["carpentry", "concrete work items"]))

    assert ranking[0][0] == "concrete work items"


def test_rank_token_overlap_returns_every_candidate():
    candidates = make_candidates(["alpha", "beta", "gamma"])
    ranking = rank_token_overlap("alpha", candidates)

    assert len(ranking) == len(candidates)


class FakeEmbedder:
    """Stands in for the API so fusion logic is testable without a key.

    Unmapped text returns a zero vector, mirroring how a cache miss degrades
    to a zero-similarity score rather than raising.
    """

    def __init__(self, vectors):
        self.vectors = vectors

    def embed(self, texts):
        return {text: self.vectors.get(text, [0.0]) for text in texts}


def test_rank_by_vector_ranks_by_similarity():
    embedder = FakeEmbedder(
        {
            "query": [1.0, 0.0],
            "far": [0.0, 1.0],
            "near": [0.9, 0.1],
        }
    )
    ranking = rank_by_vector("query", make_candidates(["far", "near"]), embedder)

    assert ranking[0][0] == "near"


def test_rank_by_vector_tolerates_missing_vector():
    embedder = FakeEmbedder({"query": [1.0, 0.0]})
    ranking = rank_by_vector("query", make_candidates(["unmapped"]), embedder)

    assert ranking == [("unmapped", 0.0)]


def test_reciprocal_rank_fusion_rewards_agreement():
    fused = reciprocal_rank_fusion(
        [
            [("a", 0.9), ("b", 0.8), ("c", 0.7)],
            [("a", 0.85), ("b", 0.6), ("c", 0.4)],
        ]
    )
    scores = dict(fused)

    assert set(scores) == {"a", "b", "c"}
    assert scores["a"] > scores["b"] > scores["c"]


def test_reciprocal_rank_fusion_ties_on_mirrored_ranks():
    """RRF scores by position, so mirrored orderings tie exactly.

    Worth pinning because it bounds the method: fusion can promote an item the
    two rankers agree on, but it cannot break a tie where each ranker simply
    swapped two items.
    """
    fused = reciprocal_rank_fusion(
        [
            [("x", 0.9), ("a", 0.5), ("b", 0.4)],
            [("a", 0.9), ("x", 0.5), ("b", 0.4)],
        ]
    )
    scores = dict(fused)

    assert scores["a"] == scores["x"]
    assert scores["a"] > scores["b"]


def test_reciprocal_rank_fusion_promotes_shared_first_place():
    fused = reciprocal_rank_fusion(
        [
            [("a", 0.9), ("x", 0.5), ("b", 0.4)],
            [("a", 0.8), ("y", 0.5), ("b", 0.4)],
        ]
    )

    assert fused[0][0] == "a"


def test_reciprocal_rank_fusion_ignores_incomparable_score_scales():
    fused = reciprocal_rank_fusion(
        [
            [("a", 0.9), ("b", 0.1)],
            [("b", 0.9), ("a", 0.1)],
        ],
        k=1,
    )

    assert len(fused) == 2
    assert dict(fused)["a"] == pytest.approx(0.5 + 1 / 3, rel=1e-9)


def test_rank_hybrid_returns_all_candidates_once():
    embedder = FakeEmbedder(
        {
            "query": [1.0, 0.0],
            "alpha": [0.0, 1.0],
            "beta": [1.0, 0.0],
        }
    )
    ranking = rank_hybrid("query", make_candidates(["alpha", "beta"]), embedder)

    assert sorted(description for description, _score in ranking) == ["alpha", "beta"]


def test_get_ranker_returns_callable_for_lexical():
    assert callable(get_ranker("token_overlap"))


def test_get_ranker_returns_none_without_embedder():
    assert get_ranker("embedding") is None
    assert get_ranker("tfidf") is None
    assert get_ranker("hybrid") is None


def test_get_ranker_tfidf_uses_vector_ranker():
    embedder = FakeEmbedder({"query": [1.0, 0.0], "alpha": [1.0, 0.0]})
    ranker = get_ranker("tfidf", embedder)

    assert ranker("query", make_candidates(["alpha"])) == [("alpha", pytest.approx(1.0))]


def test_get_ranker_rejects_unknown_method():
    try:
        get_ranker("telepathy")
    except ValueError as error:
        assert "Unknown retrieval method" in str(error)
    else:
        raise AssertionError("Expected an unknown method to fail")


def test_openai_embedder_missing_key_raises_clear_error(tmp_path):
    embedder = OpenAIEmbedder(api_key="", cache_path=tmp_path / "missing.json")

    try:
        embedder.embed(["uncached text"])
    except RuntimeError as error:
        assert "OPENAI_API_KEY" in str(error)
    else:
        raise AssertionError("Expected a missing API key to fail")


def test_openai_embedder_explicit_empty_key_overrides_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-be-used")
    embedder = OpenAIEmbedder(api_key="", cache_path=tmp_path / "cache.json")

    try:
        embedder.embed(["text"])
    except RuntimeError as error:
        assert "OPENAI_API_KEY" in str(error)
    else:
        raise AssertionError("An explicit empty key must not fall back to the environment")


def test_tfidf_embedder_shares_one_vocabulary(tmp_path):
    embedder = TfidfEmbedder(corpus=["reinforcement steel", "rebar fixing"], cache_path=tmp_path / "c.json")
    vectors = embedder.embed(["reinforcement steel", "rebar fixing", "roof covering"])

    lengths = {len(vector) for vector in vectors.values()}
    assert len(lengths) == 1


def test_tfidf_embedder_ranks_shared_terms_above_unrelated(tmp_path):
    embedder = TfidfEmbedder(
        corpus=["concrete work to foundations", "roof covering to flat roof", "masonry work"],
        cache_path=tmp_path / "c.json",
    )
    texts = ["concrete work", "concrete work to foundations", "roof covering to flat roof"]
    vectors = embedder.embed(texts)
    query = vectors["concrete work"]

    assert cosine_similarity(query, vectors["concrete work to foundations"]) > cosine_similarity(
        query, vectors["roof covering to flat roof"]
    )


def test_tfidf_embedder_ignores_stale_cache(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"roof covering": [1.0, 0.0]}), encoding="utf-8")
    embedder = TfidfEmbedder(corpus=["roof covering", "concrete work"], cache_path=cache_path)
    vectors = embedder.embed(["roof covering"])

    assert len(vectors["roof covering"]) > 2


def test_build_tfidf_embedder_covers_every_candidate():
    cases = [
        {
            "query": "q1",
            "candidates": [{"description": "a"}, {"description": "b"}],
        },
        {
            "query": "q2",
            "candidates": [{"description": "c"}],
        },
    ]
    embedder = build_tfidf_embedder(cases, cache_path="data/test_cache.json")
    vectors = embedder.embed(["a", "b", "c", "q1", "q2"])

    assert len(vectors) == 5


def test_build_embedder_returns_tfidf_backend_without_credentials():
    embedder = build_embedder("tfidf", [], api_key="")

    assert isinstance(embedder, TfidfEmbedder)


def test_build_embedder_returns_none_for_unknown_strategy():
    assert build_embedder("telepathy", []) is None


def test_embedder_is_abstract():
    with pytest.raises(TypeError):
        Embedder()
