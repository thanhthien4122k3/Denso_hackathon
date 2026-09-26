"""Nạp quy tắc nghiệp vụ từ YAML (tách riêng khỏi YAML chứa SQL).

Quy tắc dùng tập toán tử rõ ràng, không dùng eval.
"""

import yaml

from app.settings import RULES_YAML_PATH

ALLOWED_OPS = {"eq", "ne", "gt", "lt", "gte", "lte", "in", "exists"}

class RulesConfigError(ValueError):
    """File quy tắc không hợp lệ."""


_rules_cache: list | None = None
_version_cache: str = "unknown"


def _validate_rule(rule: dict) -> None:
    for required in ("id", "name", "incident_type"):
        if not rule.get(required):
            raise RulesConfigError(f"Quy tắc thiếu trường {required}.")
    for h in rule.get("hypotheses", []):
        cond = h.get("condition")
        if cond is None:
            raise RulesConfigError(f"Hypothesis {h.get('id')} thiếu condition.")
        op = cond.get("op", "eq")
        if op not in ALLOWED_OPS:
            raise RulesConfigError(f"Toán tử không hỗ trợ: {op}.")


def load_rules() -> tuple[list, str]:
    global _rules_cache, _version_cache
    if _rules_cache is not None:
        return _rules_cache, _version_cache

    try:
        with open(RULES_YAML_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError as exc:
        raise RulesConfigError(f"Không tìm thấy file quy tắc: {RULES_YAML_PATH}") from exc
    except yaml.YAMLError as exc:
        raise RulesConfigError(f"File quy tắc không hợp lệ: {exc}") from exc

    if not isinstance(raw, dict) or not isinstance(raw.get("rules"), list):
        raise RulesConfigError("File quy tắc phải có khóa 'rules' là một danh sách.")

    rules = raw["rules"]
    for rule in rules:
        _validate_rule(rule)

    _rules_cache = rules
    _version_cache = raw.get("version", "unknown")
    return _rules_cache, _version_cache


def matching_rules(rules: list, incident_type: str) -> list:
    return [r for r in rules if r.get("incident_type") == incident_type]
