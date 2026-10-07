"""Engine phân tích tác động theo đồ thị và quy tắc (không dùng ML).

Duyệt đồ thị có visited set để tránh lặp vô hạn khi có chu trình. Không cộng lặp
ảnh hưởng: mỗi node chỉ ghi nhận một lần theo mức ảnh hưởng mạnh nhất.
"""

from collections import defaultdict, deque


def build_adjacency(edges: list[dict]) -> dict:
    adj = defaultdict(list)
    for edge in edges:
        adj[(edge["source_type"], edge["source_id"])].append(edge)
    return adj


def traverse(
    edges: list[dict],
    source_type: str,
    source_id: int,
    propagate_kinds: set,
    max_depth: int,
) -> list[dict]:
    adj = build_adjacency(edges)
    visited = {(source_type, source_id)}
    impacts: dict[tuple, dict] = {}

    queue = deque()
    queue.append((source_type, source_id, 0, []))
    while queue:
        node_type, node_id, depth, path = queue.popleft()
        if depth >= max_depth:
            continue
        for edge in adj.get((node_type, node_id), []):
            if edge["kind"] not in propagate_kinds:
                continue
            ntype, nid = edge["target_type"], edge["target_id"]
            if (ntype, nid) in visited:
                continue
            visited.add((ntype, nid))
            step = _step(node_type, node_id, edge)
            new_path = path + [step]
            depth_kind = "DIRECT" if depth == 0 else "INDIRECT"
            impacts[(ntype, nid)] = {
                "node_type": ntype,
                "node_id": nid,
                "impact_type": depth_kind,
                "relation_depth": depth_kind,
                "evidence_status": "POTENTIAL",
                "path": new_path,
                "edge_kind": edge["kind"],
            }
            queue.append((ntype, nid, depth + 1, new_path))

    # Rủi ro tiềm năng: cạnh không truyền tác động (ánh xạ, trách nhiệm bộ phận...)
    nodes_to_check = [(source_type, source_id)] + [
        (impact["node_type"], impact["node_id"]) for impact in impacts.values()
    ]
    for node_type, node_id in nodes_to_check:
        for edge in adj.get((node_type, node_id), []):
            if edge["kind"] in propagate_kinds:
                continue
            ntype, nid = edge["target_type"], edge["target_id"]
            if (ntype, nid) in impacts or (ntype, nid) == (source_type, source_id):
                continue
            step = _step(node_type, node_id, edge)
            base_path = impacts.get((node_type, node_id), {}).get("path", [])
            impacts[(ntype, nid)] = {
                "node_type": ntype,
                "node_id": nid,
                "impact_type": "RISK",
                "relation_depth": None,
                "evidence_status": "POTENTIAL",
                "path": base_path + [step],
                "edge_kind": edge["kind"],
            }

    return list(impacts.values())


def _step(from_type: str, from_id: int, edge: dict) -> dict:
    return {
        "from_type": from_type,
        "from_id": from_id,
        "to_type": edge["target_type"],
        "to_id": edge["target_id"],
        "kind": edge["kind"],
        "label": edge.get("label") or "",
    }


def evaluate_condition(condition: dict, signals: dict) -> bool:
    signal = condition.get("signal")
    op = condition.get("op", "eq")
    value = condition.get("value")
    if signal not in signals:
        return False
    actual = signals[signal]
    if op == "exists":
        return actual is not None
    if op == "eq":
        return actual == value
    if op == "ne":
        return actual != value
    if op == "gt":
        return actual is not None and actual > value
    if op == "lt":
        return actual is not None and actual < value
    if op == "gte":
        return actual is not None and actual >= value
    if op == "lte":
        return actual is not None and actual <= value
    if op == "in":
        return actual in value
    return False


def select_hypotheses(hypotheses: list[dict], signals: dict) -> list[dict]:
    selected = []
    for hyp in hypotheses:
        if evaluate_condition(hyp.get("condition", {}), signals):
            selected.append(hyp)
    return selected


def match_past_incidents(current: dict, past: list[dict]) -> list[dict]:
    """Tìm sự cố cũ tương tự theo tiêu chí đơn giản, có giải thích tiêu chí khớp.

    current: {incident_type, source_object_type, source_object_id, ...}
    past: danh sách sự cố cũ {id, code, incident_type, machine_id, error_code, ...}
    Trả về danh sách {incident_id, code, matched_criteria: [..]}.
    """
    matches = []
    for p in past:
        criteria = []
        if current.get("incident_type") and p.get("incident_type") == current["incident_type"]:
            criteria.append("cùng loại sự cố")
        if (current.get("source_object_type") == "machine"
                and p.get("machine_id") and p["machine_id"] == current.get("source_object_id")):
            criteria.append("cùng máy")
        cur_code = (current.get("error_code") or "").strip()
        if cur_code and p.get("error_code") and p["error_code"] == cur_code:
            criteria.append("cùng mã lỗi")
        if criteria:
            matches.append({
                "incident_id": p.get("id"),
                "code": p.get("code"),
                "matched_criteria": criteria,
            })
    return matches
