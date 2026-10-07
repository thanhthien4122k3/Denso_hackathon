"""Nghiệp vụ xác minh bối cảnh sản xuất của sự cố."""

from app.exceptions import NotFoundError, ValidationFailedError
from app.repositories.context_repository import ContextRepository
from app.repositories.incident_repository import IncidentRepository


class ContextVerificationService:
    def __init__(self, **repos):
        self.context = repos.get("context") or ContextRepository()
        self.incidents = repos.get("incidents") or IncidentRepository()

    def _candidate(self, op) -> dict:
        def _iso(v):
            return v.isoformat() if hasattr(v, "isoformat") else v

        return {
            "operation_id": op["id"],
            "machine_id": op["machine_id"],
            "machine_code": op.get("machine_code"),
            "process_id": op["process_id"],
            "process_code": op.get("process_code"),
            "lot_id": op["lot_id"],
            "lot_code": op.get("lot_code"),
            "order_code": op.get("order_code"),
            "started_at": _iso(op["started_at"]),
            "ended_at": _iso(op["ended_at"]),
            "source": op.get("source"),
            "status": op.get("status"),
        }

    def get_context(self, incident_id: int) -> dict:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise NotFoundError("Sự cố không tồn tại.")
        candidates = []
        status = "NOT_FOUND"
        if incident.get("source_object_type") == "machine" and incident.get("source_object_id") \
                and incident.get("start_time"):
            ops = self.context.active_operations(incident["source_object_id"], incident["start_time"])
            candidates = [self._candidate(o) for o in ops]
            verification = self.context.latest_verification(incident_id)
            if verification and verification.get("status") == "CONFIRMED":
                status = "CONFIRMED"
            elif len(candidates) == 1:
                status = "MATCHED"
            elif len(candidates) > 1:
                status = "AMBIGUOUS"
        verifications = self.context.list_verifications(incident_id)
        return {
            "status": status,
            "candidates": candidates,
            "verification": verifications[-1] if verifications else None,
            "history": verifications,
        }

    def verify(self, incident_id: int, operation_ids: list[int], reason: str,
               evidence: str | None, user: dict) -> dict:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise NotFoundError("Sự cố không tồn tại.")
        if incident.get("source_object_type") != "machine" or not incident.get("start_time"):
            raise ValidationFailedError("Sự cố không gắn máy/thời điểm để xác minh bối cảnh.")

        operation_ids = [int(x) for x in (operation_ids or [])]
        candidates = self.context.active_operations(incident["source_object_id"], incident["start_time"])
        candidate_ids = [o["id"] for o in candidates]

        # Kiểm tra tồn tại và phiên bản ứng viên: mọi id được chọn phải nằm trong
        # ứng viên hiện tại, nếu không thì dữ liệu đã thay đổi -> conflict.
        if not set(operation_ids).issubset(set(candidate_ids)):
            raise ValidationFailedError(
                "Bối cảnh đã thay đổi sau khi tải; vui lòng tải lại trước khi xác minh.")

        if not reason or not reason.strip():
            raise ValidationFailedError("Cần nhập lý do khi xác minh bối cảnh.")

        snapshot = [self._candidate(o) for o in candidates]
        return self.context.create_verification({
            "incident_id": incident_id,
            "operation_ids": operation_ids,
            "status": "CONFIRMED" if operation_ids else "UNRESOLVED",
            "decided_by": user["id"],
            "reason": reason.strip(),
            "evidence": (evidence or "").strip() or None,
            "candidate_snapshot": snapshot,
        })
