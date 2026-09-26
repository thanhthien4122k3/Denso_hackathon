"""Đăng ký loại node/cạnh của đồ thị hai lớp và kiểm tra quan hệ hợp lệ."""

BUSINESS_NODE_TYPES = {
    "department",
    "line",
    "process",
    "machine",
    "material",
    "product",
    "order",
    "lot",
    "shift",
}

SYSTEM_NODE_TYPES = {"source", "dataset", "field"}

NODE_TYPES = BUSINESS_NODE_TYPES | SYSTEM_NODE_TYPES

NODE_TABLES = {
    "department": "departments",
    "line": "production_lines",
    "process": "processes",
    "machine": "machines",
    "material": "materials",
    "product": "products",
    "order": "production_orders",
    "lot": "lots",
    "shift": "shifts",
    "source": "data_sources",
    "dataset": "datasets",
    "field": "dataset_fields",
}

NODE_LABELS = {
    "department": "Bộ phận",
    "line": "Chuyền",
    "process": "Công đoạn",
    "machine": "Máy",
    "material": "Vật tư",
    "product": "Sản phẩm",
    "order": "Lệnh sản xuất",
    "lot": "Lot",
    "shift": "Ca sản xuất",
    "source": "Hệ thống nguồn",
    "dataset": "Dataset",
    "field": "Trường dữ liệu",
}

EDGE_KINDS = {
    "production_dependency": "Phụ thuộc sản xuất",
    "data_flow": "Luồng dữ liệu",
    "data_mapping": "Ánh xạ dữ liệu–nghiệp vụ",
    "department_responsibility": "Trách nhiệm bộ phận",
}


class EdgeValidationError(ValueError):
    """Quan hệ không hợp lệ hoặc vi phạm quy tắc loại cạnh."""


def _valid_kind(source_type: str, target_type: str, kind: str) -> bool:
    if kind == "production_dependency":
        return source_type in BUSINESS_NODE_TYPES and target_type in BUSINESS_NODE_TYPES
    if kind == "data_flow":
        return source_type in {"source", "dataset"} and target_type in {"source", "dataset"}
    if kind == "data_mapping":
        return source_type in SYSTEM_NODE_TYPES and target_type in BUSINESS_NODE_TYPES
    if kind == "department_responsibility":
        return source_type == "department" and target_type in BUSINESS_NODE_TYPES
    return False


def validate_edge(source_type: str, target_type: str, kind: str) -> None:
    if source_type not in NODE_TYPES:
        raise EdgeValidationError(f"Loại node nguồn không hợp lệ: {source_type}.")
    if target_type not in NODE_TYPES:
        raise EdgeValidationError(f"Loại node đích không hợp lệ: {target_type}.")
    if kind not in EDGE_KINDS:
        raise EdgeValidationError(f"Loại cạnh không hợp lệ: {kind}.")
    if not _valid_kind(source_type, target_type, kind):
        raise EdgeValidationError(
            f"Không cho phép cạnh {kind} từ {source_type} -> {target_type}."
        )
