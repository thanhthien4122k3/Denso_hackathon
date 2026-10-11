"""Bộ dữ liệu mô phỏng DEMO-D3-01 (tổng hợp để kiểm thử, không phải dữ liệu DENSO).

Toàn bộ dữ liệu có is_simulated=True và scenario_id="DEMO-D3-01".
Mọi thời gian dùng múi giờ +07:00, ngày 2026-10-06 (trừ sự cố cũ 2026-10-03).
"""

from datetime import datetime

SCENARIO_ID = "DEMO-D3-01"


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


# Thời điểm chạy kịch bản chính (Bước 2/3).
T0 = "2026-10-06T10:00:00+07:00"

# Danh mục dùng chung cho DEMO-D3-01.
DEPARTMENTS = [
    {"code": "PROD", "name": "Sản xuất"},
    {"code": "MAINT", "name": "Bảo trì"},
    {"code": "QC", "name": "Chất lượng"},
    {"code": "PLAN", "name": "Kế hoạch"},
    {"code": "WH", "name": "Kho"},
    {"code": "DATA", "name": "IT/Data"},
]

LINES = [{"code": "LINE-01", "name": "Chuyền demo 01"}]

PROCESSES = [
    {"code": "P10", "name": "Gia công"},
    {"code": "P20", "name": "Kiểm tra"},
    {"code": "P30", "name": "Đóng gói"},
]

MACHINES = [
    {"code": "M10", "name": "Máy gia công", "process": "P10"},
    {"code": "M20", "name": "Máy kiểm tra", "process": "P20"},
    {"code": "M30", "name": "Máy đóng gói", "process": "P30"},
]

MATERIALS = [
    {"code": "MAT-100", "name": "Phôi", "unit": "pcs"},
    {"code": "MAT-200", "name": "Bao bì", "unit": "pcs"},
]

PRODUCTS = [{"code": "SP-A", "name": "Sản phẩm A"}]

ORDERS = [
    {"code": "PO-001", "name": "Lệnh sản xuất SP-A", "status": "IN_PROGRESS",
     "product_code": "SP-A", "plan_qty": 1000,
     "plan_start": "2026-10-06T08:00:00+07:00", "plan_end": "2026-10-06T16:00:00+07:00"},
]

LOTS = [
    {"code": "LOT-A", "name": "Lô A", "order_code": "PO-001", "qty": 400},
    {"code": "LOT-B", "name": "Lô B", "order_code": "PO-001", "qty": 600},
]

# Quan hệ (source_type, source_code, target_type, target_code, kind, label).
# Hiệu lực từ 2026-10-01T00:00+07.
EDGES = [
    ("machine", "M10", "process", "P10", "production_dependency", "Máy phục vụ công đoạn"),
    ("machine", "M20", "process", "P20", "production_dependency", "Máy phục vụ công đoạn"),
    ("machine", "M30", "process", "P30", "production_dependency", "Máy phục vụ công đoạn"),
    ("process", "P10", "process", "P20", "production_dependency", "Cung cấp bán thành phẩm"),
    ("process", "P20", "process", "P30", "production_dependency", "Cung cấp sản phẩm đã kiểm tra"),
    ("department", "MAINT", "machine", "M10", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "MAINT", "machine", "M20", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "MAINT", "machine", "M30", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "QC", "process", "P20", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "PROD", "line", "LINE-01", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "PLAN", "order", "PO-001", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "DATA", "line", "LINE-01", "department_responsibility", "Bộ phận chịu trách nhiệm dữ liệu"),
    # Vật tư cung cấp cho công đoạn; kho chịu trách nhiệm.
    ("material", "MAT-100", "process", "P10", "production_dependency", "Cung cấp phôi"),
    ("material", "MAT-200", "process", "P30", "production_dependency", "Cung cấp bao bì"),
    ("department", "WH", "material", "MAT-100", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    ("department", "WH", "material", "MAT-200", "department_responsibility", "Bộ phận chịu trách nhiệm"),
    # Chuyền gồm các công đoạn.
    ("line", "LINE-01", "process", "P10", "production_dependency", "Chuyền gồm công đoạn"),
    ("line", "LINE-01", "process", "P20", "production_dependency", "Chuyền gồm công đoạn"),
    ("line", "LINE-01", "process", "P30", "production_dependency", "Chuyền gồm công đoạn"),
    # Lô thuộc lệnh; lệnh sản xuất sản phẩm.
    ("lot", "LOT-A", "order", "PO-001", "production_dependency", "Lô thuộc lệnh"),
    ("lot", "LOT-B", "order", "PO-001", "production_dependency", "Lô thuộc lệnh"),
    ("order", "PO-001", "product", "SP-A", "production_dependency", "Lệnh sản xuất sản phẩm"),
]

EDGE_VALID_FROM = "2026-10-01T00:00:00+07:00"

# Lịch sử thực hiện (production_operations).
OPERATIONS = [
    {"lot_code": "LOT-A", "process_code": "P10", "machine_code": "M10",
     "started_at": "2026-10-06T08:00:00+07:00", "ended_at": "2026-10-06T09:50:00+07:00",
     "status": "COMPLETED"},
    {"lot_code": "LOT-A", "process_code": "P20", "machine_code": "M20",
     "started_at": "2026-10-06T09:30:00+07:00", "ended_at": None,
     "status": "IN_PROGRESS"},
    {"lot_code": "LOT-B", "process_code": "P10", "machine_code": "M10",
     "started_at": "2026-10-06T09:50:00+07:00", "ended_at": None,
     "status": "IN_PROGRESS"},
]

# Vận hành nền.
MACHINE_STATES = [
    {"machine_code": "M10", "event_time": "2026-10-06T09:50:00+07:00", "state": "RUNNING"},
    {"machine_code": "M20", "event_time": "2026-10-06T09:30:00+07:00", "state": "RUNNING"},
]

BUFFER_SNAPSHOTS = [
    {"upstream_process_code": "P10", "downstream_process_code": "P20",
     "product_code": "SP-A", "lot_code": "LOT-A", "available_qty": 60, "unit": "pcs",
     "recorded_at": "2026-10-06T10:00:00+07:00", "source": "Demo", "confirmed": True},
]

CAPACITY_PROFILES = [
    {"process_code": "P20", "machine_code": None, "product_code": None,
     "rate_per_minute": 10, "unit": "pcs/min", "valid_from": "2026-10-06T00:00:00+07:00",
     "source_confirmation": "Demo", "note": "Tốc độ tiêu thụ công đoạn P20"},
    {"process_code": "P10", "machine_code": "M10", "product_code": "SP-A",
     "rate_per_minute": 12, "unit": "pcs/min", "valid_from": "2026-10-06T00:00:00+07:00",
     "source_confirmation": "Demo", "note": "Công suất tham chiếu M10/P10/SP-A"},
]

# Các giả định demo (để tính toán ước tính, không phải dữ liệu thật).
ASSUMPTIONS = [
    "Không bổ sung hàng vào buffer sau 10:00.",
    "P20 duy trì 10 pcs/phút, không nghỉ trong khoảng xét.",
    "Không có nguồn thay thế trong tình huống.",
    "Các tham số chỉ phục vụ mô phỏng.",
]

# Lớp logic hệ thống và mapping.
DATA_SOURCES = [
    {"code": "APP-DEMO", "name": "Ứng dụng nhập liệu demo", "source_type": "APP",
     "collection_method": "manual", "confirmed": False},
]

DATASETS = [
    {"code": "machine_states", "name": "Trạng thái máy", "dataset_type": "table",
     "collection_method": "manual", "generation_unit": "per_event",
     "update_schedule": "realtime", "event_time_field": "event_time",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
    {"code": "production_operations", "name": "Bối cảnh sản xuất", "dataset_type": "table",
     "collection_method": "manual", "generation_unit": "per_lot",
     "update_schedule": "per_shift", "event_time_field": "started_at",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
    {"code": "buffer_snapshots", "name": "Hàng đệm", "dataset_type": "table",
     "collection_method": "manual", "generation_unit": "per_event",
     "update_schedule": "per_shift", "event_time_field": "recorded_at",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
    {"code": "qc_results", "name": "Kết quả QC", "dataset_type": "table",
     "collection_method": "manual", "generation_unit": "per_lot",
     "update_schedule": "per_shift", "event_time_field": "check_time",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
    {"code": "production_records", "name": "Sản lượng", "dataset_type": "table",
     "collection_method": "manual", "generation_unit": "per_pcs",
     "update_schedule": "per_shift", "event_time_field": "production_date",
     "timezone": "Asia/Ho_Chi_Minh", "confirmed": False},
]

DATASET_FIELDS = [
    {"dataset_code": "machine_states", "code": "machine_code", "name": "Mã máy",
     "data_type": "string", "is_key": True},
    {"dataset_code": "machine_states", "code": "event_time", "name": "Thời điểm sự kiện",
     "data_type": "timestamp", "is_key": False},
    {"dataset_code": "machine_states", "code": "state", "name": "Trạng thái",
     "data_type": "string", "is_key": False},
    {"dataset_code": "machine_states", "code": "error_code", "name": "Mã lỗi",
     "data_type": "string", "is_key": False},
    {"dataset_code": "production_records", "code": "quantity", "name": "Số lượng đạt",
     "data_type": "integer", "is_key": False},
]

# Luồng dữ liệu (lớp hệ thống): source -> dataset, dataset -> dataset.
DATA_FLOW_EDGES = [
    ("source", "APP-DEMO", "dataset", "machine_states", "data_flow", "Nguồn cấp trạng thái máy"),
    ("source", "APP-DEMO", "dataset", "production_operations", "data_flow", "Nguồn cấp bối cảnh sản xuất"),
    ("source", "APP-DEMO", "dataset", "buffer_snapshots", "data_flow", "Nguồn cấp hàng đệm"),
    ("source", "APP-DEMO", "dataset", "qc_results", "data_flow", "Nguồn cấp kết quả QC"),
    ("source", "APP-DEMO", "dataset", "production_records", "data_flow", "Nguồn cấp sản lượng"),
    ("dataset", "machine_states", "dataset", "production_operations", "data_flow", "Trạng thái máy nối bối cảnh sản xuất"),
]

# Ánh xạ dữ liệu -> nghiệp vụ (data_mapping). source_ref của field là "dataset.field".
DATA_MAPPING_EDGES = [
    ("field", "machine_states.machine_code", "machine", "M10", "data_mapping", "Mã máy ánh xạ tới máy"),
    ("field", "machine_states.event_time", "machine", "M10", "data_mapping", "Thời điểm sự kiện ánh xạ tới máy"),
    ("field", "machine_states.state", "machine", "M10", "data_mapping", "Trạng thái ánh xạ tới máy"),
    ("field", "machine_states.error_code", "machine", "M10", "data_mapping", "Mã lỗi ánh xạ tới máy"),
    ("field", "production_records.quantity", "process", "P10", "data_mapping", "Số lượng ánh xạ tới công đoạn"),
    ("dataset", "machine_states", "machine", "M10", "data_mapping", "Dataset trạng thái máy ánh xạ tới máy"),
    ("dataset", "production_records", "process", "P20", "data_mapping", "Dataset sản lượng ánh xạ tới công đoạn"),
]

# Mapping mã nguồn -> mã chuẩn (chỉ trong nguồn APP-DEMO).
MAPPINGS = [
    {"source_code": "APP-DEMO", "object_type": "machine", "source_code_value": "CNC-01", "target_code": "M10"},
    {"source_code": "APP-DEMO", "object_type": "lot", "source_code_value": "BATCH-B", "target_code": "LOT-B"},
]

# Mẫu nhập sai mã để kiểm tra trường hợp chưa ánh xạ.
UNMAPPED_INGESTION = {
    "request_id": None,  # sinh uuid4 khi nạp
    "event_time": "2026-10-06T10:01:00+07:00",
    "payload": {"machine_code": "CNC-UNKNOWN", "state": "STOPPED"},
    "status": "NEEDS_MAPPING",
    "error": "Không tìm thấy ánh xạ cho mã máy 'CNC-UNKNOWN' trong nguồn APP-DEMO.",
}

# Sự cố cũ để kiểm tra tái sử dụng kinh nghiệm (2026-10-03).
HISTORIC_INCIDENT = {
    "code": "INC-HIST-001",
    "title": "Máy M10 dừng - lỗi cấp phôi",
    "incident_type": "MACHINE_STOP",
    "source_object_type": "machine",
    "source_object_code": "M10",
    "start_time": "2026-10-03T14:00:00+07:00",
    "end_time": "2026-10-03T14:20:00+07:00",
    "severity": "HIGH",
    "description": "Máy dừng, báo lỗi bộ phận cấp phôi.",
    "status": "RESOLVED",
    "department_code": "MAINT",
    "recovered_at": "2026-10-03T14:20:00+07:00",
    "recovered_by": "demo-supervisor",
    "closed_at": "2026-10-03T15:00:00+07:00",
    "closed_by": "demo-supervisor",
    "resolution_summary": "Bảo trì kiểm tra và căn chỉnh theo hướng dẫn demo.",
    "root_cause_status": "CONFIRMED",
    "error_code": "E-DEMO-01",
}

HISTORIC_DOWNTIME = {
    "machine_code": "M10",
    "start_time": "2026-10-03T14:00:00+07:00",
    "end_time": "2026-10-03T14:20:00+07:00",
    "reason": "Lỗi bộ phận cấp phôi",
    "error_code": "E-DEMO-01",
    "operator_name": "demo-supervisor",
}

HISTORIC_RECOVERY_STATE = {
    "machine_code": "M10",
    "event_time": "2026-10-03T14:20:00+07:00",
    "state": "RUNNING",
}

HISTORIC_CAUSE = {
    "content": "Cảm biến phát hiện phôi bị lệch vị trí.",
    "kind": "CONFIRMED",
    "evidence": "Phiếu kiểm tra và trạng thái RUNNING sau xử lý (mô phỏng).",
    "confirmed_by": "demo-supervisor",
}

HISTORIC_EXPERIENCE = {
    "incident_type": "MACHINE_STOP",
    "error_code": "E-DEMO-01",
    "symptom": "Máy dừng, màn hình báo lỗi bộ phận cấp phôi.",
    "root_cause": "Cảm biến phát hiện phôi bị lệch vị trí.",
    "actions": "Bảo trì kiểm tra và căn chỉnh theo hướng dẫn demo.",
    "result": "Máy chạy lại sau xử lý.",
    "approved_by": "demo-supervisor",
}

# Tài khoản demo (tự sinh mật khẩu khi nạp; chưa phải danh tính xác thực).
USERS = [
    {"username": "demo-recorder", "display_name": "Người ghi nhận (demo)", "roles": ["OPERATOR"]},
    {"username": "demo-handler", "display_name": "Người xử lý (demo)", "roles": ["HANDLER"]},
    {"username": "demo-coordinator", "display_name": "Người điều phối (demo)", "roles": ["COORDINATOR"]},
    {"username": "demo-admin", "display_name": "Quản trị (demo)", "roles": ["ADMIN"]},
]
