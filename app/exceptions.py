"""Ngoại lệ nghiệp vụ dùng chung trong ứng dụng."""


class DatabaseUnavailableError(Exception):
    """Không kết nối được PostgreSQL."""


class DuplicateRequestError(Exception):
    """Vi phạm unique constraint trên request_id."""


class RecordConflictError(Exception):
    """Cùng request_id nhưng nội dung đã chuẩn hóa khác nhau."""


class ConflictError(Exception):
    """Xung đột trạng thái nghiệp vụ (ví dụ: thao tác trên hồ sơ đã đóng)."""


class DuplicateCodeError(Exception):
    """Mã nghiệp vụ đã tồn tại."""


class NotFoundError(Exception):
    """Không tìm thấy đối tượng tham chiếu."""


class ValidationFailedError(ValueError):
    """Dữ liệu gửi lên không hợp lệ (trả 422)."""
