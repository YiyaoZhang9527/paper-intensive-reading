import pytest
from paper_intensive_reading.math_ladder import (
    path_for, layers_for_concept, describe_layer, ALL_LAYERS
)


class TestPathFor:
    def test_softmax_needs_probability(self):
        assert 4 in path_for("softmax")

    def test_attention_needs_matrix_and_probability(self):
        layers = path_for("attention")
        assert 5 in layers
        assert 4 in layers

    def test_simple_arithmetic(self):
        assert 0 in path_for("x + y")

    def test_rmsnorm_needs_matrix(self):
        assert 5 in path_for("rmsnorm")

    def test_unknown_concept_returns_layer_0(self):
        assert path_for("totally-unknown-xyz") == [0]

    def test_layer_order_ascending(self):
        layers = path_for("attention")
        assert layers == sorted(layers)


class TestLayersForConcept:
    def test_known_concept(self):
        assert 5 in layers_for_concept("matrix multiply")

    def test_case_insensitive(self):
        assert 4 in layers_for_concept("SoftMax")

    def test_strip_whitespace(self):
        assert 4 in layers_for_concept("  softmax  ")


class TestDescribeLayer:
    def test_describe_layer_0(self):
        desc = describe_layer(0)
        assert "算术" in desc or "加减" in desc

    def test_describe_layer_5(self):
        desc = describe_layer(5)
        assert "向量" in desc or "矩阵" in desc

    def test_invalid_layer(self):
        with pytest.raises(ValueError):
            describe_layer(99)


def test_all_layers_defined():
    assert len(ALL_LAYERS) == 8
    assert all(i in ALL_LAYERS for i in range(8))
