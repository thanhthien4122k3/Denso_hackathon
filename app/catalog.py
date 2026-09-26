"""Định nghĩa danh mục nghiệp vụ và kiểm tra dữ liệu theo từng đối tượng."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    type: str = "str"  # str | int | bool
    required: bool = False
    max_length: int = 0


@dataclass(frozen=True)
class EntitySpec:
    key: str
    table: str
    label: str
    extra_fields: tuple[FieldSpec, ...] = ()
    fk: dict[str, str] = field(default_factory=dict)  # field -> (target_table)


# Các trường chung cho mọi danh mục.
_COMMON = (
    FieldSpec("code", "Mã", "str", True, 50),
    FieldSpec("name", "Tên", "str", True, 200),
    FieldSpec("description", "Mô tả", "str", False, 0),
)

CATALOG_ENTITIES: dict[str, EntitySpec] = {
    "department": EntitySpec("department", "departments", "Bộ phận"),
    "line": EntitySpec(
        "line",
        "production_lines",
        "Chuyền sản xuất",
        (),
        {"department_id": "department"},
    ),
    "process": EntitySpec(
        "process", "processes", "Công đoạn", (), {"line_id": "line"}
    ),
    "machine": EntitySpec(
        "machine",
        "machines",
        "Máy móc/thiết bị",
        (),
        {"department_id": "department"},
    ),
    "material": EntitySpec(
        "material",
        "materials",
        "Vật tư/linh kiện",
        (FieldSpec("unit", "Đơn vị tính", "str", False, 20),),
        {"department_id": "department"},
    ),
    "product": EntitySpec(
        "product", "products", "Sản phẩm", (), {"department_id": "department"}
    ),
    "order": EntitySpec(
        "order",
        "production_orders",
        "Lệnh sản xuất",
        (FieldSpec("status", "Trạng thái", "str", False, 30),),
        {"product_id": "product"},
    ),
    "lot": EntitySpec(
        "lot",
        "lots",
        "Lot",
        (),
        {"production_order_id": "order"},
    ),
    "shift": EntitySpec("shift", "shifts", "Ca sản xuất"),
}

CATALOG_KEYS = tuple(CATALOG_ENTITIES.keys())


def get_entity(key: str) -> EntitySpec:
    if key not in CATALOG_ENTITIES:
        raise KeyError(f"Danh mục không tồn tại: {key}")
    return CATALOG_ENTITIES[key]


def all_fields(spec: EntitySpec) -> dict[str, FieldSpec]:
    result = {f.name: f for f in _COMMON}
    result["active"] = FieldSpec("active", "Đang hoạt động", "bool", False, 0)
    result["is_simulated"] = FieldSpec("is_simulated", "Dữ liệu mô phỏng", "bool", False, 0)
    for f in spec.extra_fields:
        result[f.name] = f
    for fk_name in spec.fk:
        result[fk_name] = FieldSpec(fk_name, fk_name, "int", False, 0)
    return result
