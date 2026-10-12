"""Regression tests for scripts/lark_board_check.py."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lark_board_check as checker  # noqa: E402


def _write(payload):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                      encoding="utf-8")
    json.dump(payload, tmp)
    tmp.close()
    return Path(tmp.name)


class LarkBoardCheckTest(unittest.TestCase):
    def _summary(self, nodes):
        path = _write({"data": {"nodes": nodes}})
        try:
            return checker.check(path, tol=1.0)
        finally:
            path.unlink(missing_ok=True)

    def test_clean_board_has_zero_gaps_and_is_orthogonal(self):
        nodes = [
            {"id": "box", "type": "composite_shape", "x": 100, "y": 100,
             "width": 200, "height": 100},
            {"id": "c1", "type": "connector", "x": 100, "y": 150,
             "width": 200, "height": 0,
             "connector": {"shape": "straight",
                           "start": {"arrow_style": "none",
                                     "position": {"x": 100, "y": 150}},
                           "end": {"arrow_style": "triangle_arrow",
                                   "position": {"x": 300, "y": 150}},
                           "turning_points": []}},
        ]
        result = self._summary(nodes)
        self.assertTrue(result["ok"])
        self.assertEqual(result["dangling_endpoints"], 0)
        self.assertEqual(result["non_orthogonal_segments"], 0)
        self.assertEqual(result["embedded_nodes"], 0)

    def test_partial_trunk_and_short_arrow_are_reported(self):
        nodes = [
            {"id": "box", "type": "composite_shape", "x": 100, "y": 100,
             "width": 200, "height": 100},
            {"id": "trunk", "type": "connector", "x": 400, "y": 0,
             "width": 0, "height": 100,
             "connector": {"shape": "straight",
                           "start": {"arrow_style": "none",
                                     "position": {"x": 400, "y": 0}},
                           "end": {"arrow_style": "none",
                                   "position": {"x": 400, "y": 100}},
                           "turning_points": []}},
            {"id": "branch", "type": "connector", "x": 300, "y": 150,
             "width": 97, "height": 0,
             "connector": {"shape": "straight",
                           "start": {"arrow_style": "none",
                                     "position": {"x": 300, "y": 150}},
                           "end": {"arrow_style": "triangle_arrow",
                                   "position": {"x": 397, "y": 150}},
                           "turning_points": []}},
        ]
        result = self._summary(nodes)
        self.assertFalse(result["ok"])
        self.assertGreaterEqual(result["dangling_endpoints"], 2)
        self.assertGreater(result["max_endpoint_gap_px"], 1.0)

    def test_non_orthogonal_and_embedded_nodes_are_reported(self):
        nodes = [
            {"id": "box", "type": "composite_shape", "x": 100, "y": 100,
             "width": 200, "height": 100},
            {"id": "diag", "type": "connector", "x": 100, "y": 100,
             "width": 200, "height": 100,
             "connector": {"shape": "straight",
                           "start": {"arrow_style": "none",
                                     "position": {"x": 100, "y": 100}},
                           "end": {"arrow_style": "none",
                                   "position": {"x": 300, "y": 200}},
                           "turning_points": []}},
            {"id": "pic", "type": "svg", "x": 0, "y": 0,
             "width": 10, "height": 10},
        ]
        result = self._summary(nodes)
        self.assertFalse(result["ok"])
        self.assertEqual(result["non_orthogonal_segments"], 1)
        self.assertEqual(result["embedded_nodes"], 1)


if __name__ == "__main__":
    unittest.main()
