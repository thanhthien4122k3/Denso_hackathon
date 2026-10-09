"""API kịch bản mô phỏng và trang khảo sát."""

from fastapi import APIRouter, Depends

from app.services.scenario_service import ScenarioService
from app.services.scenario_d3_service import ScenarioD3Service
from app.services.scenario_ambiguous_service import ScenarioAmbiguousService
from app.services.survey_service import SurveyService

scenarios_router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])
survey_router = APIRouter(prefix="/api/survey", tags=["survey"])


def get_scenario_service() -> ScenarioService:
    return ScenarioService()


def get_d3_service() -> ScenarioD3Service:
    return ScenarioD3Service()


def get_ambiguous_service() -> ScenarioAmbiguousService:
    return ScenarioAmbiguousService()


def get_survey_service() -> SurveyService:
    return SurveyService()


SCENARIO_INFO = [
    {
        "key": "S1", "title": "Kịch bản 1: Máy lắp ráp dừng",
        "incident_code": "INC-001",
        "expected": "Máy M-01 dừng -> lan truyền tới công đoạn ASSY-01 (trực tiếp) và TEST-01, PACK-01 (gián tiếp). Gợi ý việc cho Bảo trì và Kế hoạch.",
        "limits": "Thiếu dữ liệu tồn đệm nên không khẳng định công đoạn sau dừng ngay.",
    },
    {
        "key": "S2", "title": "Kịch bản 2: Lot có tỷ lệ lỗi QC cao",
        "incident_code": "INC-002",
        "expected": "QC FAIL trên LOT-001 -> đánh dấu phạm vi lot/order/sản phẩm có nguy cơ. Gợi ý QC kiểm tra và Kho truy xuất vật tư.",
        "limits": "Nguyên nhân vật tư chỉ là giả thuyết khi chưa xác minh.",
    },
    {
        "key": "S3", "title": "Kịch bản 3: Thiếu vật tư",
        "incident_code": "INC-003",
        "expected": "Vật tư MAT-100 dưới ngưỡng -> rủi ro cho công đoạn/lệnh liên quan. Gợi ý Kho và Kế hoạch xử lý.",
        "limits": "Ngưỡng thiếu vật tư là giá trị demo được cấu hình.",
    },
]


@scenarios_router.get("")
def list_scenarios():
    return {"success": True, "message": "OK", "data": SCENARIO_INFO}


@scenarios_router.get("/status")
def scenario_status(service: ScenarioService = Depends(get_scenario_service)):
    return {"success": True, "message": "OK",
            "data": {"loaded": service.is_loaded()}}


@scenarios_router.post("/load")
def load_demo(service: ScenarioService = Depends(get_scenario_service)):
    return {"success": True, "message": "OK", "data": service.load_demo()}


@scenarios_router.get("/d3/status")
def d3_status(service: ScenarioD3Service = Depends(get_d3_service)):
    return {"success": True, "message": "OK", "data": {"loaded": service.is_loaded()}}


@scenarios_router.post("/d3/load")
def load_d3(service: ScenarioD3Service = Depends(get_d3_service)):
    return {"success": True, "message": "OK", "data": service.load()}


@scenarios_router.get("/d3-ambiguous/status")
def ambiguous_status(service: ScenarioAmbiguousService = Depends(get_ambiguous_service)):
    return {"success": True, "message": "OK", "data": {"loaded": service.is_loaded()}}


@scenarios_router.post("/d3-ambiguous/load")
def load_ambiguous(service: ScenarioAmbiguousService = Depends(get_ambiguous_service)):
    return {"success": True, "message": "OK", "data": service.load()}


@survey_router.get("/groups")
def survey_groups(service: SurveyService = Depends(get_survey_service)):
    return {"success": True, "message": "OK", "data": service.groups()}


@survey_router.get("")
def survey_list(group: str | None = None, service: SurveyService = Depends(get_survey_service)):
    return {"success": True, "message": "OK", "data": service.list(group)}


@survey_router.post("", status_code=201)
def survey_create(payload: dict, service: SurveyService = Depends(get_survey_service)):
    return {"success": True, "message": "Đã lưu.", "data": service.create(payload)}


@survey_router.put("/{item_id}")
def survey_update(item_id: int, payload: dict, service: SurveyService = Depends(get_survey_service)):
    return {"success": True, "message": "Đã cập nhật.", "data": service.update(item_id, payload)}
