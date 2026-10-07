"""Bộ dữ liệu mô phỏng cho 3 kịch bản demo.

Tất cả dữ liệu này có is_simulated = True và chỉ được nạp khi người dùng chủ động
bấm nút, không tự nạp vào dữ liệu thật khi khởi động. Nhãn "Dữ liệu mô phỏng —
chưa xác nhận bởi Denso".
"""

from datetime import datetime, timezone

TZ = timezone(offset=__import__("datetime").timedelta(hours=7))


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


DEPARTMENTS = [
    {"code": "MAINT", "name": "Bảo trì"},
    {"code": "QC", "name": "Kiểm tra chất lượng"},
    {"code": "WH", "name": "Kho"},
    {"code": "PLAN", "name": "Kế hoạch sản xuất"},
    {"code": "DATA", "name": "IT/Data"},
]

LINES = [{"code": "LINE-01", "name": "Chuyền lắp ráp"}]

PROCESSES = [
    {"code": "ASSY-01", "name": "Lắp ráp"},
    {"code": "TEST-01", "name": "Kiểm tra"},
    {"code": "PACK-01", "name": "Đóng gói"},
]

MACHINES = [
    {"code": "M-01", "name": "Máy lắp ráp"},
    {"code": "M-02", "name": "Máy kiểm tra"},
]

MATERIALS = [
    {"code": "MAT-100", "name": "Linh kiện A", "unit": "pcs"},
    {"code": "MAT-200", "name": "Vật liệu B", "unit": "kg"},
]

PRODUCTS = [{"code": "PROD-001", "name": "Sản phẩm hoàn chỉnh"}]

ORDERS = [{"code": "ORD-001", "name": "Lệnh SX tháng 9", "status": "IN_PROGRESS"}]

LOTS = [{"code": "LOT-001", "name": "Lot 20260926"}]

SHIFTS = [{"code": "CA_1", "name": "Ca 1"}, {"code": "CA_2", "name": "Ca 2"}, {"code": "CA_3", "name": "Ca 3"}]


def build_edges(ids: dict) -> list[dict]:
    """ids: {(node_type, code): id}"""
    pid = lambda t, c: ids[(t, c)]
    edges = [
        # production_dependency
        ("line", "LINE-01", "process", "ASSY-01", "Chuyền có công đoạn"),
        ("line", "LINE-01", "process", "TEST-01", "Chuyền có công đoạn"),
        ("line", "LINE-01", "process", "PACK-01", "Chuyền có công đoạn"),
        ("machine", "M-01", "process", "ASSY-01", "Máy phục vụ công đoạn"),
        ("machine", "M-02", "process", "TEST-01", "Máy phục vụ công đoạn"),
        ("material", "MAT-100", "process", "ASSY-01", "Công đoạn phụ thuộc vật tư"),
        ("process", "ASSY-01", "process", "TEST-01", "Công đoạn trước cung cấp đầu ra"),
        ("process", "TEST-01", "process", "PACK-01", "Công đoạn trước cung cấp đầu ra"),
        ("process", "ASSY-01", "product", "PROD-001", "Công đoạn tạo ra sản phẩm"),
        ("process", "TEST-01", "product", "PROD-001", "Công đoạn xử lý sản phẩm"),
        ("process", "PACK-01", "product", "PROD-001", "Công đoạn xử lý sản phẩm"),
        ("order", "ORD-001", "product", "PROD-001", "Lệnh sản xuất cho sản phẩm"),
        ("lot", "LOT-001", "order", "ORD-001", "Lot thuộc lệnh sản xuất"),
        # department_responsibility
        ("department", "MAINT", "machine", "M-01", "Bộ phận chịu trách nhiệm"),
        ("department", "MAINT", "machine", "M-02", "Bộ phận chịu trách nhiệm"),
        ("department", "QC", "process", "TEST-01", "Bộ phận chịu trách nhiệm"),
    ]
    kind_map = {
        "line": "production_dependency",
        "machine": "production_dependency",
        "material": "production_dependency",
        "process": "production_dependency",
        "order": "production_dependency",
        "lot": "production_dependency",
        "department": "department_responsibility",
    }
    result = []
    for src_type, src_code, tgt_type, tgt_code, label in edges:
        result.append({
            "source_type": src_type, "source_id": pid(src_type, src_code),
            "target_type": tgt_type, "target_id": pid(tgt_type, tgt_code),
            "kind": kind_map[src_type], "label": label,
            "source_confirmation": "Demo", "is_simulated": True,
        })
    return result


DATA_SOURCES = [
    {"code": "MES", "name": "MES - Manufacturing Execution System",
     "source_type": "MES", "collection_method": "API", "confirmed": True},
    {"code": "APP", "name": "Ứng dụng nhập liệu sản lượng",
     "source_type": "APP", "collection_method": "manual", "confirmed": False},
]

DATASETS = [
    {"code": "machine_events", "name": "Sự kiện máy", "source_code": "MES",
     "dataset_type": "table", "collection_method": "PLC", "generation_unit": "per_event",
     "update_schedule": "realtime", "event_time_field": "event_time",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": True},
    {"code": "production_records", "name": "Sản lượng công đoạn", "source_code": "APP",
     "dataset_type": "table", "collection_method": "manual", "generation_unit": "per_lot",
     "update_schedule": "per_shift", "event_time_field": "production_date",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
]

DATASET_FIELDS = [
    {"dataset_code": "machine_events", "code": "machine_code", "name": "Mã máy",
     "data_type": "string", "is_key": True},
    {"dataset_code": "machine_events", "code": "event_time", "name": "Thời điểm sự kiện",
     "data_type": "timestamp", "is_key": False},
    {"dataset_code": "production_records", "code": "process_code", "name": "Mã công đoạn",
     "data_type": "string", "is_key": True},
    {"dataset_code": "production_records", "code": "lot_code", "name": "Mã lot",
     "data_type": "string", "is_key": False},
]

DATA_FLOWS = [
    {"code": "FLOW-01", "name": "Tổng hợp sản lượng", "from": "machine_events",
     "to": "production_records"},
]

# Ánh xạ trường -> đối tượng nghiệp vụ (data_mapping)
MAPPINGS = [
    ("machine_events", "machine_code", "machine", "M-01"),
    ("production_records", "process_code", "process", "ASSY-01"),
    ("production_records", "lot_code", "lot", "LOT-001"),
]

DOWNTIMES = [
    {"machine_code": "M-01", "start_time": "2026-09-26T08:00:00+07:00",
     "end_time": "2026-09-26T08:30:00+07:00", "reason": "Lỗi servo",
     "error_code": "E-101", "operator_name": "Demo"},
]

MACHINE_STATES = [
    {"machine_code": "M-01", "event_time": "2026-09-26T08:05:00+07:00",
     "state": "STOPPED", "error_code": "E-101"},
    {"machine_code": "M-02", "event_time": "2026-09-26T08:05:00+07:00",
     "state": "RUNNING"},
]

QC_RESULTS = [
    {"lot_code": "LOT-001", "product_code": "PROD-001", "process_code": "TEST-01",
     "check_time": "2026-09-26T10:00:00+07:00", "inspected_qty": 100,
     "defect_qty": 15, "defect_type": "Kích thước", "result": "FAIL"},
]

MATERIAL_STATUSES = [
    {"material_code": "MAT-100", "recorded_at": "2026-09-26T09:00:00+07:00",
     "available_qty": 30, "unit": "pcs", "scope": "Kho"},
]

INCIDENTS = [
    {"code": "INC-001", "title": "Máy lắp ráp dừng", "incident_type": "MACHINE_STOP",
     "source_object_type": "machine", "source_object_code": "M-01",
     "start_time": "2026-09-26T08:00:00+07:00", "end_time": "2026-09-26T08:30:00+07:00",
     "severity": "HIGH", "description": "Máy M-01 dừng đột ngột, mã lỗi E-101.",
     "status": "OPEN", "department_code": "MAINT"},
    {"code": "INC-002", "title": "Lot có tỷ lệ lỗi QC cao", "incident_type": "QUALITY",
     "source_object_type": "lot", "source_object_code": "LOT-001",
     "start_time": "2026-09-26T10:00:00+07:00", "severity": "HIGH",
     "description": "QC phát hiện 15/100 lỗi kích thước trong lot LOT-001.",
     "status": "OPEN", "department_code": "QC"},
    {"code": "INC-003", "title": "Thiếu vật tư linh kiện A", "incident_type": "MATERIAL_SHORTAGE",
     "source_object_type": "material", "source_object_code": "MAT-100",
     "start_time": "2026-09-26T09:00:00+07:00", "severity": "HIGH",
     "description": "Vật tư MAT-100 còn 30 pcs, thấp hơn ngưỡng.",
     "status": "OPEN", "department_code": "WH"},
]
