"""Kiểm thử query_loader và cấu trúc file YAML - không cần database."""

import pytest

from app.query_loader import (
    QueryConfigError,
    QueryLoader,
    get_database_queries,
    get_production_queries,
)


def test_database_queries_have_expected_keys():
    queries = get_database_queries()
    assert {
        "create_schema",
        "create_table",
        "index_production_date",
        "index_lot_code",
    } <= set(queries)


def test_production_queries_have_expected_keys():
    queries = get_production_queries()
    assert {
        "insert_record",
        "find_by_request_id",
        "find_by_id",
        "list_records",
        "count_records",
        "health_check",
    } <= set(queries)


def test_insert_uses_bound_placeholders():
    sql = get_production_queries()["insert_record"]["sql"]
    for field in (
        "request_id",
        "production_date",
        "shift",
        "line_code",
        "process_code",
        "product_code",
        "lot_code",
        "good_quantity",
        "defect_quantity",
        "operator_name",
        "note",
    ):
        assert f"%({field})s" in sql


def test_every_query_has_fetch_and_sql():
    for queries in (get_database_queries(), get_production_queries()):
        for name, spec in queries.items():
            assert spec["fetch"] in {"none", "one", "all"}
            assert isinstance(spec["sql"], str) and spec["sql"].strip()


def test_loader_rejects_bad_fetch(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "queries:\n  x:\n    description: d\n    fetch: many\n    sql: SELECT 1;\n",
        encoding="utf-8",
    )
    with pytest.raises(QueryConfigError):
        QueryLoader(path).load()


def test_loader_rejects_missing_sql(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("queries:\n  x:\n    description: d\n    fetch: one\n", encoding="utf-8")
    with pytest.raises(QueryConfigError):
        QueryLoader(path).load()


def test_loader_rejects_missing_queries_key(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("foo: bar\n", encoding="utf-8")
    with pytest.raises(QueryConfigError):
        QueryLoader(path).load()
