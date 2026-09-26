"""Nghiệp vụ thông tin khảo sát cần xác nhận (9 nhóm)."""

from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.task_repository import SurveyRepository

SURVEY_GROUPS = {
    "G1": "Quy trình và quan hệ phụ thuộc",
    "G2": "Ảnh hưởng khi xảy ra sự cố",
    "G3": "Dữ liệu vận hành đang thu thập",
    "G4": "Nơi phát sinh và phương thức thu thập",
    "G5": "Hệ thống lưu trữ và khóa liên kết",
    "G6": "Tần suất phát sinh/cập nhật",
    "G7": "Cách xác định nguyên nhân và quy tắc xử lý",
    "G8": "Bộ phận nhận việc và hành động",
    "G9": "Ba tình huống thực tế",
}

DEFAULT_QUESTIONS = {
    "G1": ["Chuỗi công đoạn và chiều phụ thuộc thực tế giữa các công đoạn là gì?",
           "Có công đoạn nào phân nhánh, hội tụ hoặc phụ thuộc có điều kiện không?"],
    "G2": ["Khi một công đoạn dừng, công đoạn nào bị ảnh hưởng trực tiếp/gián tiếp?",
           "Có tồn kho đệm hay tuyến thay thế để giảm lan truyền không?"],
    "G3": ["Những loại dữ liệu vận hành nào đang được thu thập (trạng thái máy, QC, vật tư...)?",
           "Dữ liệu sản lượng được ghi theo đơn vị gì (pcs, lot, sự kiện)?"],
    "G4": ["Dữ liệu phát sinh ở đâu và thu thập bằng cách nào (cảm biến, PLC, barcode, nhập tay)?"],
    "G5": ["Dữ liệu lưu ở hệ thống nào và khóa liên kết (machine_code, lot_code, order_code) là gì?"],
    "G6": ["Tần suất phát sinh và cập nhật dữ liệu (realtime, theo ca, hằng ngày, batch) là gì?"],
    "G7": ["Hiện nhà máy xác định nguyên nhân và có quy tắc xử lý sự cố nào không?"],
    "G8": ["Bộ phận nào nhận việc và hành động chuẩn khi xảy ra từng loại sự cố?"],
    "G9": ["Mô tả ba tình huống sự cố thực tế gần đây để đối chiếu với kịch bản demo."],
}


class SurveyService:
    def __init__(self, repository: SurveyRepository | None = None):
        self.repository = repository or SurveyRepository()

    def ensure_seeded(self):
        existing = self.repository.list()
        existing_groups = {item["group_code"] for item in existing}
        for group, questions in DEFAULT_QUESTIONS.items():
            if group in existing_groups:
                continue
            for question in questions:
                self.repository.create({"group_code": group, "question": question})

    def list(self, group_code=None):
        self.ensure_seeded()
        return self.repository.list(group_code)

    def groups(self):
        return [{"code": c, "name": n} for c, n in SURVEY_GROUPS.items()]

    def _clean(self, data):
        if not isinstance(data, dict):
            raise ValidationFailedError("Dữ liệu phải là đối tượng JSON.")
        cleaned = {}
        for name, value in data.items():
            if name in ("group_code", "question", "answer", "provided_by", "status", "note"):
                if name == "status" and value not in ("UNCONFIRMED", "CONFIRMED"):
                    raise ValidationFailedError("status phải là UNCONFIRMED hoặc CONFIRMED.")
                if value is None:
                    continue
                cleaned[name] = (value.strip() if isinstance(value, str) else value)
        return cleaned

    def create(self, data):
        cleaned = self._clean(data)
        if not cleaned.get("group_code") or not cleaned.get("question"):
            raise ValidationFailedError("group_code và question là bắt buộc.")
        cleaned.setdefault("status", "UNCONFIRMED")
        return self.repository.create(cleaned)

    def update(self, item_id, data):
        if self.repository.get(item_id) is None:
            raise NotFoundError("Mục khảo sát không tồn tại.")
        return self.repository.update(item_id, self._clean(data))
