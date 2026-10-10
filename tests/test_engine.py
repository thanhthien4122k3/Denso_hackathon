"""Kiểm thử engine phân tích tác động (thuần, không cần database)."""

from app.engine.impact_engine import evaluate_condition, select_hypotheses, traverse


def _edge(src_t, src_i, tgt_t, tgt_i, kind="production_dependency"):
    return {"source_type": src_t, "source_id": src_i,
            "target_type": tgt_t, "target_id": tgt_i, "kind": kind, "label": ""}


def test_traverse_direct_and_indirect():
    edges = [
        _edge("machine", 1, "process", 1),
        _edge("process", 1, "process", 2),
        _edge("process", 2, "product", 1),
    ]
    impacts = traverse(edges, "machine", 1, {"production_dependency"}, 5)
    by_type = {i["impact_type"] for i in impacts}
    assert "DIRECT" in by_type and "INDIRECT" in by_type
    nodes = {(i["node_type"], i["node_id"]) for i in impacts}
    assert ("process", 1) in nodes and ("process", 2) in nodes and ("product", 1) in nodes


def test_traverse_handles_cycle():
    edges = [
        _edge("process", 1, "process", 2),
        _edge("process", 2, "process", 3),
        _edge("process", 3, "process", 1),  # chu trình
    ]
    impacts = traverse(edges, "process", 1, {"production_dependency"}, 10)
    assert len(impacts) == 2  # process 2, 3; không lặp vô hạn


def test_traverse_no_duplicate_impacts():
    edges = [
        _edge("machine", 1, "process", 1),
        _edge("machine", 1, "process", 2),
        _edge("process", 1, "product", 1),
        _edge("process", 2, "product", 1),
    ]
    impacts = traverse(edges, "machine", 1, {"production_dependency"}, 5)
    products = [i for i in impacts if i["node_id"] == 1 and i["node_type"] == "product"]
    assert len(products) == 1  # không cộng lặp


def test_mapping_edge_does_not_become_impact_or_propagate():
    edges = [
        _edge("machine", 1, "process", 1),
        _edge("process", 1, "field", 9, "data_mapping"),
    ]
    impacts = traverse(edges, "machine", 1, {"production_dependency"}, 5)
    # Cạnh ánh xạ dữ liệu không lan truyền sự cố và không trở thành ảnh hưởng RISK.
    field_impacts = [i for i in impacts if i["node_type"] == "field"]
    assert field_impacts == []
    # Chỉ còn phụ thuộc sản xuất thực sự được lan truyền.
    assert {(i["node_type"], i["node_id"]) for i in impacts} == {("process", 1)}


def test_mapping_edge_does_not_propagate():
    edges = [
        _edge("machine", 1, "process", 1),
        _edge("process", 1, "dataset", 1, "data_mapping"),
        _edge("dataset", 1, "process", 3, "production_dependency"),
    ]
    impacts = traverse(edges, "machine", 1, {"production_dependency"}, 5)
    nodes = {(i["node_type"], i["node_id"]) for i in impacts}
    assert ("process", 3) not in nodes  # dataset không lan tiếp


def test_responsibility_edge_does_not_become_impact():
    edges = [
        _edge("machine", 1, "process", 1),
        _edge("department", 2, "process", 1, "department_responsibility"),
    ]
    impacts = traverse(edges, "machine", 1, {"production_dependency"}, 5)
    # Cạnh trách nhiệm bộ phận dùng để xác định bộ phận liên quan, không phải ảnh hưởng.
    assert all(i["node_type"] != "department" for i in impacts)


def test_evaluate_condition_operators():
    signals = {"has_error": True, "rate": 15.0, "state": "STOPPED"}
    assert evaluate_condition({"signal": "has_error", "op": "eq", "value": True}, signals)
    assert evaluate_condition({"signal": "rate", "op": "gt", "value": 10}, signals)
    assert evaluate_condition({"signal": "rate", "op": "lt", "value": 20}, signals)
    assert evaluate_condition({"signal": "state", "op": "in", "value": ["STOPPED", "RUNNING"]}, signals)
    assert evaluate_condition({"signal": "missing", "op": "exists"}, signals) is False
    assert evaluate_condition({"signal": "has_error", "op": "eq", "value": False}, signals) is False


def test_select_hypotheses():
    hypotheses = [
        {"id": "H1", "condition": {"signal": "has_error", "op": "eq", "value": True}, "content": "a"},
        {"id": "H2", "condition": {"signal": "low", "op": "eq", "value": True}, "content": "b"},
    ]
    selected = select_hypotheses(hypotheses, {"has_error": True, "low": False})
    assert [h["id"] for h in selected] == ["H1"]
