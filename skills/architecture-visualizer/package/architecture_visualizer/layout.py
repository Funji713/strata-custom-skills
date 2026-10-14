"""Deterministic grid layout and orthogonal edge routing for Render IR."""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from .errors import LAYOUT_FAILURE, VisualizerError


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float: return self.x
    @property
    def right(self) -> float: return self.x + self.width
    @property
    def top(self) -> float: return self.y
    @property
    def bottom(self) -> float: return self.y + self.height
    @property
    def cx(self) -> float: return self.x + self.width / 2
    @property
    def cy(self) -> float: return self.y + self.height / 2


def _wrap(text: str | None, max_chars: int, max_lines: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    consumed = " ".join(lines)
    if len(consumed) < len(text) and lines:
        lines[-1] = (lines[-1][:max(1, max_chars - 1)] + "…")
    return lines


def _serpentine_position(index: int, columns: int) -> tuple[int, int]:
    row, offset = divmod(index, columns)
    column = offset if row % 2 == 0 else columns - 1 - offset
    return row, column


def layout_render_ir(render_ir: dict, profile: dict) -> dict:
    canvas = profile["canvas"]; margin = profile["safe_margin"]
    width, height = float(canvas["width"]), float(canvas["height"])
    nodes = render_ir.get("nodes", [])
    if not nodes:
        raise VisualizerError(LAYOUT_FAILURE, "Cannot lay out an empty Render IR")
    order = render_ir["presentation"].get("presentation_order", [])
    node_by_id = {node["id"]: node for node in nodes}
    ordered_ids = [node_id for node_id in order if node_id in node_by_id]
    ordered_ids.extend(sorted(set(node_by_id) - set(ordered_ids)))
    columns = min(5, max(1, math.ceil(math.sqrt(len(nodes) * 1.6))))
    rows = math.ceil(len(nodes) / columns)
    left, right = float(margin["left"]), width - float(margin["right"])
    top, bottom = max(float(margin["top"]) + 105, 215.0), height - float(margin["bottom"]) - 45
    cell_w, cell_h = (right - left) / columns, (bottom - top) / rows
    node_w = min(270.0, cell_w - 38.0)
    node_h = min(132.0, cell_h - 34.0)
    if node_w < 175 or node_h < 96:
        raise VisualizerError(LAYOUT_FAILURE, f"{len(nodes)} nodes exceed the ppt-16x9 density envelope")
    positioned: dict[str, dict] = {}
    grid: dict[str, tuple[int, int]] = {}
    for index, node_id in enumerate(ordered_ids):
        row, column = _serpentine_position(index, columns)
        x = left + column * cell_w + (cell_w - node_w) / 2
        y = top + row * cell_h + (cell_h - node_h) / 2
        box = Box(round(x, 2), round(y, 2), round(node_w, 2), round(node_h, 2))
        node = node_by_id[node_id]
        positioned[node_id] = {
            "id": node_id, "box": asdict(box), "category_lines": [node["category"].upper()],
            "title_lines": _wrap(node["label"], max(10, int(node_w / 11.0)), 2),
            "description_lines": _wrap(node.get("description"), max(14, int(node_w / 7.0)), 2),
            "font_sizes": {"category": float(profile["font"]["section_label_min_pt"]), "title": float(profile["font"]["node_title_min_pt"]), "description": float(profile["font"]["node_description_min_pt"])},
        }
        grid[node_id] = (row, column)

    routed: list[dict] = []
    for edge_index, edge in enumerate(render_ir["edges"]):
        if edge["from"] not in positioned or edge["to"] not in positioned:
            raise VisualizerError(LAYOUT_FAILURE, f"Invalid edge endpoint: {edge['id']}")
        source = Box(**positioned[edge["from"]]["box"]); target = Box(**positioned[edge["to"]]["box"])
        source_grid, target_grid = grid[edge["from"]], grid[edge["to"]]
        if source_grid == target_grid:
            points = [(source.right, source.cy), (source.right + 26, source.cy), (source.right + 26, source.top - 22), (source.cx, source.top - 22), (source.cx, source.top)]
        elif source_grid[0] == target_grid[0] and abs(source_grid[1] - target_grid[1]) == 1:
            if source.cx < target.cx:
                points = [(source.right, source.cy), (target.left, target.cy)]
            else:
                points = [(source.left, source.cy), (target.right, target.cy)]
        elif source_grid[0] == target_grid[0]:
            channel_y = min(source.top, target.top) - 17 - (edge_index % 3) * 9
            points = [(source.cx, source.top), (source.cx, channel_y), (target.cx, channel_y), (target.cx, target.top)]
        else:
            source_channel = source.bottom + max(8.0, (cell_h - source.height) / 2)
            target_channel = target.top - max(8.0, (cell_h - target.height) / 2)
            outer_x = right + 12 + (edge_index % 4) * 20
            outer_x = min(width - 10, outer_x)
            points = [(source.cx, source.bottom), (source.cx, source_channel), (outer_x, source_channel), (outer_x, target_channel), (target.cx, target_channel), (target.cx, target.top)]
        routed.append({**edge, "points": [[round(x, 2), round(y, 2)] for x, y in points]})

    group_layout: list[dict] = []
    for group in render_ir.get("groups", []):
        member_boxes = [Box(**positioned[item]["box"]) for item in group["members"] if item in positioned]
        if not member_boxes:
            continue
        pad = 16.0
        box = Box(min(b.left for b in member_boxes)-pad, min(b.top for b in member_boxes)-pad-18, max(b.right for b in member_boxes)-min(b.left for b in member_boxes)+2*pad, max(b.bottom for b in member_boxes)-min(b.top for b in member_boxes)+2*pad+18)
        group_layout.append({**group, "box": asdict(box)})
    return {
        "canvas": {"width": int(width), "height": int(height)}, "safe_margin": margin,
        "title_box": {"x": left, "y": float(margin["top"]), "width": right-left, "height": 82.0},
        "nodes": [positioned[node_id] for node_id in ordered_ids], "groups": group_layout, "edges": routed,
        "annotations": render_ir.get("annotations", []), "layout_engine": "deterministic-serpentine-grid-v1",
    }
