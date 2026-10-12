#!/usr/bin/env python3
"""Validate a Feishu/Lark whiteboard export for dangling connectors.

Usage:
    lark-cli whiteboard +query --whiteboard-token <token> --output_as raw \
        --format json > board.json
    python scripts/lark_board_check.py board.json

The checker is deliberately geometry-only. It verifies the properties that
matter after an SVG has been converted into a native whiteboard:

* every connector endpoint lands on a shape edge or on another connector
  segment (T-junction), with a default tolerance of 1 px;
* all connector segments are horizontal or vertical;
* the board contains no embedded svg/image/picture/bitmap nodes.

Exit status is 0 when clean, 1 when any problem is found. Add ``--json`` for
machine-readable output.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Segment = Tuple[Point, Point]
Rect = Tuple[float, float, float, float]  # x0, y0, x1, y1

EMBEDDED_TYPES = {"svg", "image", "picture", "bitmap"}


@dataclass
class Node:
    raw: Dict[str, Any]
    node_type: str
    node_id: str
    x: float
    y: float
    width: float
    height: float

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


def _load_nodes(path: Path) -> List[Node]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if isinstance(data.get("data"), dict) and "nodes" in data["data"]:
            raw_nodes = data["data"]["nodes"]
        elif "nodes" in data:
            raw_nodes = data["nodes"]
        else:
            raise SystemExit("input JSON has no .data.nodes or .nodes array")
    elif isinstance(data, list):
        raw_nodes = data
    else:
        raise SystemExit("input JSON must be an object or an array")

    nodes: List[Node] = []
    for index, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            continue
        node_type = str(raw.get("type", ""))
        node_id = str(raw.get("id", "") or "node@%d" % index)
        nodes.append(
            Node(
                raw=raw,
                node_type=node_type,
                node_id=node_id,
                x=float(raw.get("x", 0.0) or 0.0),
                y=float(raw.get("y", 0.0) or 0.0),
                width=float(raw.get("width", 0.0) or 0.0),
                height=float(raw.get("height", 0.0) or 0.0),
            )
        )
    return nodes


def _connector_points(node: Node) -> Optional[List[Point]]:
    conn = node.raw.get("connector")
    if not isinstance(conn, dict):
        return None
    try:
        start = conn["start"]["position"]
        end = conn["end"]["position"]
    except (KeyError, TypeError):
        return None
    points: List[Point] = [(float(start["x"]), float(start["y"]))]
    # Feishu exports turning_points relative to the connector bbox origin,
    # not relative to the start point. Restore them with node.x / node.y.
    for tp in conn.get("turning_points") or []:
        if isinstance(tp, dict) and "x" in tp and "y" in tp:
            points.append((node.x + float(tp["x"]), node.y + float(tp["y"])))
    points.append((float(end["x"]), float(end["y"])))
    return points


def _segments(points: Sequence[Point]) -> Iterable[Segment]:
    for a, b in zip(points, points[1:]):
        yield a, b


def _dist_point_segment(p: Point, a: Point, b: Point) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    qx = ax + t * dx
    qy = ay + t * dy
    return math.hypot(px - qx, py - qy)


def _dist_point_rect_edge(p: Point, rect: Rect) -> float:
    x0, y0, x1, y1 = rect
    px, py = p
    # Distance to the nearest point on the four edges of the rectangle.
    return min(
        _dist_point_segment(p, (x0, y0), (x1, y0)),
        _dist_point_segment(p, (x1, y0), (x1, y1)),
        _dist_point_segment(p, (x1, y1), (x0, y1)),
        _dist_point_segment(p, (x0, y1), (x0, y0)),
    )


def _shape_rects(nodes: Sequence[Node], include_text_shapes: bool = False) -> List[Rect]:
    # Connectors normally attach to composite shapes or groups. Text nodes are
    # usually labels inside a box; counting them as attachment targets can hide
    # a real gap at the outer box edge.
    target_types = {"composite_shape", "group"}
    if include_text_shapes:
        target_types.add("text_shape")
    rects: List[Rect] = []
    for n in nodes:
        if n.node_type in target_types:
            if n.width > 0 and n.height > 0:
                rects.append(n.rect)
    return rects


def _connector_segments(nodes: Sequence[Node]) -> Dict[str, List[Segment]]:
    result: Dict[str, List[Segment]] = {}
    for n in nodes:
        if n.node_type != "connector":
            continue
        points = _connector_points(n)
        if points and len(points) >= 2:
            result[n.node_id] = list(_segments(points))
    return result


def _nearest_attachment_distance(
    p: Point,
    rects: Sequence[Rect],
    own_id: str,
    all_segments: Dict[str, List[Segment]],
) -> float:
    best = float("inf")
    for rect in rects:
        best = min(best, _dist_point_rect_edge(p, rect))
    for cid, segments in all_segments.items():
        if cid == own_id:
            continue
        for a, b in segments:
            best = min(best, _dist_point_segment(p, a, b))
    return best


def check(path: Path, tol: float = 1.0,
          include_text_shapes: bool = False) -> Dict[str, Any]:
    nodes = _load_nodes(path)
    rects = _shape_rects(nodes, include_text_shapes=include_text_shapes)
    all_segments = _connector_segments(nodes)
    problems: List[str] = []

    embedded = [
        n for n in nodes
        if n.node_type.lower() in EMBEDDED_TYPES or "svg_code" in n.raw
    ]
    for n in embedded:
        problems.append(
            "embedded non-editable node: id=%s type=%s" % (n.node_id, n.node_type)
        )

    endpoint_count = 0
    dangling = 0
    max_gap = 0.0
    non_orthogonal = 0

    for node in nodes:
        if node.node_type != "connector":
            continue
        points = _connector_points(node)
        if not points or len(points) < 2:
            problems.append("connector has no usable points: id=%s" % node.node_id)
            continue
        for seg_index, (a, b) in enumerate(_segments(points)):
            dx = abs(b[0] - a[0])
            dy = abs(b[1] - a[1])
            if dx > tol and dy > tol:
                non_orthogonal += 1
                problems.append(
                    "non-orthogonal segment: id=%s segment=%d (%g,%g)->(%g,%g)"
                    % (node.node_id, seg_index, a[0], a[1], b[0], b[1])
                )
        for end_name, p in (("start", points[0]), ("end", points[-1])):
            endpoint_count += 1
            gap = _nearest_attachment_distance(p, rects, node.node_id, all_segments)
            if gap > tol:
                dangling += 1
                max_gap = max(max_gap, gap)
                problems.append(
                    "dangling %s: id=%s at (%g,%g), nearest attachment %.3f px"
                    % (end_name, node.node_id, p[0], p[1], gap)
                )
            else:
                max_gap = max(max_gap, gap)

    summary = {
        "ok": not problems,
        "file": str(path),
        "tolerance_px": tol,
        "include_text_shapes": include_text_shapes,
        "nodes": len(nodes),
        "shapes": len(rects),
        "connectors": len(all_segments),
        "endpoints": endpoint_count,
        "dangling_endpoints": dangling,
        "max_endpoint_gap_px": round(max_gap, 3),
        "non_orthogonal_segments": non_orthogonal,
        "embedded_nodes": len(embedded),
        "problems": problems,
    }
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="raw whiteboard JSON export")
    parser.add_argument("--tol", type=float, default=1.0,
                        help="endpoint gap tolerance in px (default: 1.0)")
    parser.add_argument("--json", action="store_true",
                        help="print the full JSON summary only")
    parser.add_argument("--include-text-shapes", action="store_true",
                        help="also treat text nodes as attachment targets")
    args = parser.parse_args(argv)

    summary = check(args.json_file, tol=args.tol,
                    include_text_shapes=args.include_text_shapes)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            "Feishu board check: %s | nodes=%d connectors=%d endpoints=%d "
            "dangling=%d max_gap=%.3fpx non_orthogonal=%d embedded=%d"
            % (
                "clean" if summary["ok"] else "FAILED",
                summary["nodes"],
                summary["connectors"],
                summary["endpoints"],
                summary["dangling_endpoints"],
                summary["max_endpoint_gap_px"],
                summary["non_orthogonal_segments"],
                summary["embedded_nodes"],
            )
        )
        for problem in summary["problems"]:
            print("  ! " + problem)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
