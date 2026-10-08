"""Headless regression tests, without requiring the desktop image dependencies."""
import ast
import csv
import json
import math
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from chip_geometry import ChipGeometry, PRESETS

ROOT = Path(__file__).resolve().parents[1]


def load_class(filename, name, namespace, methods=None):
    tree = ast.parse((ROOT / filename).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    if methods is not None:
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in methods]
    module = ast.Module(body=[cls], type_ignores=[])
    exec(compile(module, filename, 'exec'), namespace)
    return namespace[name]


class Canvas:
    def __init__(self):
        self.polygons = []

    def delete(self, *args):
        self.polygons.clear()

    def create_image(self, *args, **kwargs):
        pass

    def create_polygon(self, points, **kwargs):
        self.polygons.append(points)


class Image:
    shape = (35, 35)

    def __getitem__(self, index):
        y, x = index
        # Captures are bright; only the gaps are dark.
        return 255 if (x < 10 or x >= 25) and (y < 10 or y >= 25) else 0


class GeometryTests(unittest.TestCase):
    def test_presets_and_boundaries(self):
        for size, (width, gap) in PRESETS.items():
            for n in [1, 50, 96]:
                with self.subTest(size=size, n=n):
                    g = ChipGeometry.preset(size)
                    span = n * width + (n - 1) * gap
                    capture, pitch = g.vectors([0, 0], [span, 0], n)
                    self.assertAlmostEqual(capture[0], width)
                    self.assertAlmostEqual(pitch[0], width + gap)
                    self.assertAlmostEqual((n-1)*pitch[0] + capture[0], span)

    def test_override_rotation_and_persistence(self):
        g = ChipGeometry(10, 12, 8)
        capture, pitch = g.vectors([3, 4], [63, 84], 3)
        self.assertAlmostEqual(capture[0], 60*12/52)
        self.assertAlmostEqual(pitch[1], 80*20/52)
        self.assertEqual(ChipGeometry.from_metadata(json.loads(json.dumps(g.metadata()))), g)
        self.assertEqual(ChipGeometry.from_metadata({}), ChipGeometry.preset(25))
        self.assertEqual(ChipGeometry.from_metadata({'chip_resolution':'10um'}), ChipGeometry.preset(10))
        for width, gap in [(0, 1), (-1, 1), (10, -1), (math.inf, 1), (10, math.nan)]:
            with self.assertRaises(ValueError):
                ChipGeometry(10, width, gap)

    def test_actual_drawing_and_csv_export(self):
        namespace = {'center': lambda *corners: tuple(sum(p[i] for p in corners)/4 for i in range(2)), 'csv': csv,
                     'json': json, 'os': os, 'mb': SimpleNamespace(showinfo=lambda *args: None)}
        gui_class = load_class('bsa_gui.py', 'Gui', namespace, ['grid', 'write_positions_file', 'update_pos'])
        gui = gui_class()
        gui.lmain = SimpleNamespace(winfo_exists=lambda: 0)
        gui.value_sheFrame = SimpleNamespace(set=lambda v: None)
        gui.my_canvas = Canvas()
        gui.chip_geometry = ChipGeometry.preset(10)
        gui.Rpoints = [0, 0, 35, 0, 35, 35, 0, 35]
        gui.num_chan = 2
        gui.factor = 1
        gui.tixel_width = .5
        gui.classification_active = False
        gui.coords = [[[] for _ in range(2)] for _ in range(2)]
        gui.tixel_status = [[1, 0], [0, 1]]
        gui.grid(None, 0, 'reg')
        self.assertEqual(gui.coords[0][0], [5, 5])
        self.assertEqual(gui.coords[1][1], [30, 30])
        regular = [list(p) for row in gui.coords for p in row]
        gui.crop_scale_factor = .5
        gui.current_quad_id = 0
        gui.match_tixel_quad = {0: [10, 20]}
        gui.grid(None, 0, 'quad')
        self.assertEqual([p for row in gui.coords for p in row], regular)
        gui.chip_geometry = ChipGeometry.preset(15)
        gui.grid(None, 0, 'reg')
        self.assertAlmostEqual(gui.coords[0][0][0], 35*7.5/40)
        self.assertTrue(all(len(p) == 2 for row in gui.coords for p in row))
        with tempfile.TemporaryDirectory() as folder:
            filename = str(Path(folder) / 'positions.csv')
            gui.write_positions_file(filename, ['a', 'b', 'c', 'd'], gui.coords, gui.tixel_status, 1)
            with open(filename) as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[0], ['a', '1', '0', '0', '7', '7'])
            Path(filename).rename(Path(folder) / 'tissue_positions_list.csv')
            (Path(folder) / 'metadata.json').write_text('{"run":"test"}')
            (Path(folder) / 'scalefactors_json.json').write_text('{"tissue_hires_scalef":0.5}')
            gui.folder_selected = folder
            gui.tissue_hires_scalef = .5
            gui.numTixels = 2
            gui.update_pos()
            saved = json.loads((Path(folder) / 'metadata.json').read_text())
            self.assertEqual(ChipGeometry.from_metadata(saved), gui.chip_geometry)
            scales = json.loads((Path(folder) / 'scalefactors_json.json').read_text())
            self.assertEqual(scales['spot_diameter_fullres'], gui.spot_dia / .5)

    def test_actual_classifier_excludes_gaps(self):
        namespace = {'math': math, 'ChipGeometry': ChipGeometry, 'cv2': SimpleNamespace(imread=lambda *args: Image(), IMREAD_UNCHANGED=-1)}
        tissue_class = load_class('tissue_grid.py', 'Tissue', namespace)
        tissue = tissue_class([0, 0, 35, 0, 35, 35, 0, 35], 1, 'unused', 2, ChipGeometry.preset(10))
        self.assertEqual(tissue.tixel_status, [[0, 0], [0, 0]])
        self.assertAlmostEqual(tissue.spot_dia, math.sqrt(200))


if __name__ == '__main__':
    unittest.main()
