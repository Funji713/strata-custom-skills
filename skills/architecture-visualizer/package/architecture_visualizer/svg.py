"""PowerPoint-friendly SVG renderer using simple native elements."""

from __future__ import annotations

from html import escape


def _path(points: list[list[float]]) -> str:
    if not points:
        return ""
    return "M " + " L ".join(f"{x:g} {y:g}" for x, y in points)


def _arrow(points: list[list[float]], size: float = 8) -> str:
    if len(points) < 2:
        return ""
    x2, y2 = points[-1]; x1, y1 = points[-2]
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        coords = [(x2, y2), (x2-direction*size, y2-size/2), (x2-direction*size, y2+size/2)]
    else:
        direction = 1 if y2 > y1 else -1
        coords = [(x2, y2), (x2-size/2, y2-direction*size), (x2+size/2, y2-direction*size)]
    return " ".join(f"{x:g},{y:g}" for x, y in coords)


def _longest_segment_midpoint(points: list[list[float]]) -> tuple[float, float]:
    segments = [(abs(x2-x1)+abs(y2-y1), (x1+x2)/2, (y1+y2)/2) for (x1,y1),(x2,y2) in zip(points, points[1:])]
    _, x, y = max(segments, default=(0, 0, 0))
    return x, y


def render_svg(render_ir: dict, layout: dict, theme: dict, profile: dict, *, portable: bool = False) -> str:
    width = layout["canvas"]["width"]; height = layout["canvas"]["height"]
    font_stack = "Arial, sans-serif" if portable else ", ".join(theme["typography"]["font_stack"])
    edge_colors = {"main": theme["edge"]["primary_color"], "data": "#0891B2", "api": "#4F46E5", "dependency": theme["edge"]["muted_color"], "optional": theme["edge"]["muted_color"], "bidirectional": theme["edge"]["primary_color"], "control": "#7C3AED", "feedback": "#DB2777"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc">',
        f'<title id="diagram-title">{escape(render_ir["diagram"]["title"])}</title>',
        f'<desc id="diagram-desc">{escape(render_ir["presentation"].get("key_message") or "Evidence-grounded architecture diagram")}</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{theme["background"]}"/>',
        f'<text x="{layout["title_box"]["x"]:g}" y="{layout["title_box"]["y"] + 38:g}" font-family="{escape(font_stack)}" font-size="{profile["font"]["slide_title_min_pt"]}" font-weight="600" fill="{theme["text"]["primary"]}">{escape(render_ir["diagram"]["title"])}</text>',
    ]
    subtitle = render_ir["diagram"].get("subtitle")
    if subtitle:
        lines.append(f'<text x="{layout["title_box"]["x"]:g}" y="{layout["title_box"]["y"] + 72:g}" font-family="{escape(font_stack)}" font-size="14" fill="{theme["text"]["secondary"]}">{escape(subtitle[:150])}</text>')
    for group in layout.get("groups", []):
        box = group["box"]
        lines.append(f'<rect x="{box["x"]:g}" y="{box["y"]:g}" width="{box["width"]:g}" height="{box["height"]:g}" rx="{theme["group"]["radius"]}" fill="{theme["group"]["fill"]}" stroke="{theme["group"]["border_color"]}" stroke-width="{theme["group"]["border_width"]}"/>')
        lines.append(f'<text x="{box["x"]+14:g}" y="{box["y"]+17:g}" font-family="{escape(font_stack)}" font-size="14" font-weight="600" fill="{theme["text"]["muted"]}">{escape(group["label"])}</text>')
    for edge in layout["edges"]:
        color = edge_colors[edge["type"]]
        dash = ' stroke-dasharray="7 6"' if edge["type"] in {"dependency", "optional"} else ""
        lines.append(f'<path d="{_path(edge["points"])}" fill="none" stroke="{color}" stroke-width="{max(float(profile["stroke"]["minimum_px"]), float(theme["edge"]["stroke_width"])):g}" stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        lines.append(f'<polygon points="{_arrow(edge["points"])}" fill="{color}"/>')
        if edge.get("label"):
            x, y = _longest_segment_midpoint(edge["points"])
            label = edge["label"][:28]
            lines.append(f'<rect x="{x-len(label)*3.4-5:g}" y="{y-13:g}" width="{len(label)*6.8+10:g}" height="18" rx="5" fill="{theme["background"]}"/>')
            lines.append(f'<text x="{x:g}" y="{y:g}" text-anchor="middle" font-family="{escape(font_stack)}" font-size="{profile["font"]["edge_label_min_pt"]}" fill="{theme["text"]["secondary"]}">{escape(label)}</text>')
    render_node_by_id = {node["id"]: node for node in render_ir["nodes"]}
    for item in layout["nodes"]:
        node = render_node_by_id[item["id"]]; box = item["box"]
        color = theme["semantic_colors"][node["category"]]
        border_width = theme["hero"]["border_width"] if node["visual_role"] == "hero" else theme["card"]["border_width"]
        lines.append(f'<g id="{escape(node["id"].replace("/", "-"))}">')
        lines.append(f'<rect x="{box["x"]:g}" y="{box["y"]:g}" width="{box["width"]:g}" height="{box["height"]:g}" rx="{theme["card"]["radius"]}" fill="{theme["surface"]}" stroke="{color}" stroke-width="{border_width}"/>')
        lines.append(f'<rect x="{box["x"]:g}" y="{box["y"]:g}" width="8" height="{box["height"]:g}" rx="4" fill="{color}"/>')
        text_x = box["x"] + 24; category_y = box["y"] + 24
        lines.append(f'<text x="{text_x:g}" y="{category_y:g}" font-family="{escape(font_stack)}" font-size="{item["font_sizes"]["category"]:g}" font-weight="600" fill="{color}">{escape(node["category"].upper())}</text>')
        title_y = category_y + 29
        lines.append(f'<text x="{text_x:g}" y="{title_y:g}" font-family="{escape(font_stack)}" font-size="{item["font_sizes"]["title"]:g}" font-weight="600" fill="{theme["text"]["primary"]}">')
        for line_index, text_line in enumerate(item["title_lines"]):
            dy = 0 if line_index == 0 else item["font_sizes"]["title"] * 1.15
            lines.append(f'<tspan x="{text_x:g}" dy="{dy:g}">{escape(text_line)}</tspan>')
        lines.append('</text>')
        if item["description_lines"]:
            desc_y = box["y"] + box["height"] - 21 - (len(item["description_lines"])-1)*item["font_sizes"]["description"]*1.15
            lines.append(f'<text x="{text_x:g}" y="{desc_y:g}" font-family="{escape(font_stack)}" font-size="{item["font_sizes"]["description"]:g}" fill="{theme["text"]["secondary"]}">')
            for line_index, text_line in enumerate(item["description_lines"]):
                dy = 0 if line_index == 0 else item["font_sizes"]["description"] * 1.15
                lines.append(f'<tspan x="{text_x:g}" dy="{dy:g}">{escape(text_line)}</tspan>')
            lines.append('</text>')
        lines.append('</g>')
    if layout.get("annotations"):
        note = layout["annotations"][0]["text"][:180]
        lines.append(f'<text x="{profile["safe_margin"]["left"]}" y="{height-profile["safe_margin"]["bottom"]+35}" font-family="{escape(font_stack)}" font-size="12" fill="{theme["text"]["muted"]}">{escape(note)}</text>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"
