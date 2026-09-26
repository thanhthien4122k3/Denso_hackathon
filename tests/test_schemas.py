"""Kiểm thử validate dữ liệu (Pydantic) - không cần database."""

import pytest
from pydantic import ValidationError

from app.schemas import ProductionRecordCreate
from tests.helpers import make_payload


def test_valid_payload():
    model = ProductionRecordCreate(**make_payload())
    assert model.good_quantity == 100
    assert model.defect_quantity == 3
    assert model.shift == "CA_1"


def test_trims_strings():
    model = ProductionRecordCreate(
        **make_payload(line_code="  LINE-01  ", operator_name="  Thanh Thiên  ")
    )
    assert model.line_code == "LINE-01"
    assert model.operator_name == "Thanh Thiên"


def test_note_whitespace_becomes_none():
    model = ProductionRecordCreate(**make_payload(note="   "))
    assert model.note is None


@pytest.mark.parametrize("field", ["good_quantity", "defect_quantity"])
def test_negative_quantity_rejected(field):
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(**{field: -1}))


@pytest.mark.parametrize("field", ["good_quantity", "defect_quantity"])
def test_decimal_quantity_rejected(field):
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(**{field: 1.5}))


@pytest.mark.parametrize("field", ["good_quantity", "defect_quantity"])
def test_boolean_quantity_rejected(field):
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(**{field: True}))


def test_total_zero_rejected():
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(good_quantity=0, defect_quantity=0))


def test_quantity_over_max_rejected():
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(good_quantity=1_000_000_001))


@pytest.mark.parametrize(
    "field", ["line_code", "process_code", "product_code", "lot_code", "operator_name"]
)
def test_required_string_blank_rejected(field):
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(**{field: ""}))


@pytest.mark.parametrize(
    "field", ["line_code", "process_code", "product_code", "lot_code", "operator_name"]
)
def test_required_string_whitespace_rejected(field):
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(**{field: "   "}))


def test_invalid_shift_rejected():
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(shift="CA_4"))


def test_note_too_long_rejected():
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(note="x" * 1001))


def test_line_code_too_long_rejected():
    with pytest.raises(ValidationError):
        ProductionRecordCreate(**make_payload(line_code="x" * 51))
