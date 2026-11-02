"""Specific regressions for reported Windows session e668d16bfe48."""
import copy
import importlib
import runpy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostic.native_worker import inspect_objects
from diagnostic.polyline_probe import legacy_polylines, variants
from diagnostic.assessment import assess_geometry
from diagnostic.core import read_json, compare

from test_diagnostic import packet


class Placement:
    def multiply(self, other):
        return other
    def inverse(self):
        return self


class Shape:
    Placement = Placement()
    Edges = []
    Faces = []
    Vertexes = []
    Solids = []
    def isNull(self):
        return False
    def copy(self):
        return copy.copy(self)


def obj(name='MissingPlacement'):
    return SimpleNamespace(Name=name, Label=name, TypeId='PartDesign::FeaturePython',
                           PropertiesList=[], Shape=Shape(), Placement=Placement())


class MissingGlobalPlacementTests(unittest.TestCase):
    def test_missing_method_preserves_inventory_without_global_points(self):
        item = obj()
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertEqual(points, {})
        self.assertEqual(inventory[0]['coordinateFrameStatus'], 'unresolved')
        self.assertIn('getGlobalPlacement', inventory[0]['coordinateDiagnostic'])
        self.assertEqual(inventory[0]['nativeShapeCounts']['edges'], 0)

    def test_known_shape_still_emits_global_midpoint(self):
        item = obj('Known')
        edge = SimpleNamespace(Curve=SimpleNamespace(), Length=10., FirstParameter=0., LastParameter=1.,
                               valueAt=lambda value: [10*value, 0., 0.])
        item.Shape = Shape(); item.Shape.Edges = [edge]
        item.getGlobalPlacement = lambda: Placement()
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertEqual(points, {'Known.Edge1': [5., 0., 0.]})
        self.assertEqual(inventory[0]['coordinateFrameStatus'], 'global_known')

    def test_missing_method_with_edges_keeps_local_inventory_only(self):
        item = obj()
        edge = SimpleNamespace(Curve=SimpleNamespace(), Length=10., FirstParameter=0., LastParameter=1.,
                               valueAt=lambda value: [10*value, 0., 0.])
        item.Shape = Shape(); item.Shape.Edges = [edge]
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertEqual(points, {})
        self.assertEqual(inventory[0]['nativeLocalEdges'][0]['end'], [10., 0., 0.])
        self.assertEqual(inventory[0]['coordinateFrameStatus'], 'unresolved')


    def test_noncallable_method_is_unresolved(self):
        item = obj(); item.getGlobalPlacement = None
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertEqual(inventory[0]['coordinateFrameStatus'], 'unresolved')
        self.assertEqual(points, {})

    def test_raising_method_does_not_abort_other_objects(self):
        item = obj()
        def bad(): raise RuntimeError('parent placement unavailable')
        item.getGlobalPlacement = bad
        other = obj('Known'); other.getGlobalPlacement = lambda: Placement()
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item, other]))
        self.assertEqual([i['coordinateFrameStatus'] for i in inventory], ['unresolved', 'global_known'])
        self.assertEqual(points, {})

    def test_missing_object_placement_never_uses_identity_fallback(self):
        item = obj(); del item.Placement
        item.getGlobalPlacement = lambda: Placement()
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertEqual(inventory[0]['coordinateFrameStatus'], 'unresolved')
        self.assertEqual(points, {})

    def test_null_shape_never_calls_global_placement(self):
        item = obj(); item.Shape = SimpleNamespace(isNull=lambda: True)
        inventory, points = inspect_objects(SimpleNamespace(Objects=[item]))
        self.assertTrue(inventory[0]['nullShape'])
        self.assertEqual(points, {})


class ClosedPolylineTests(unittest.TestCase):
    def setUp(self):
        self.raw = (ROOT / 'examples/01_geometrias_mm.dxf').read_bytes()
        self.poly, self.variants = variants(self.raw)

    def test_original_header_closed_and_three_distinct_vertices(self):
        self.assertEqual(self.poly['flags'] & 1, 1)
        self.assertEqual([v['point'] for v in self.poly['vertices']], [[0.,40.,0.],[10.,40.,0.],[10.,50.,0.]])
        self.assertTrue(all(v['flagsPresent'] and v['flags'] == 0 for v in self.poly['vertices']))

    def test_omitting_optional_vertex_flags_preserves_semantics(self):
        omitted = legacy_polylines(self.variants[1][1])[0]
        self.assertEqual(omitted['flags'], self.poly['flags'])
        self.assertEqual([v['point'] for v in omitted['vertices']], [v['point'] for v in self.poly['vertices']])
        self.assertTrue(all(v['flags'] == 0 and not v['flagsPresent'] for v in omitted['vertices']))

    def test_reproduces_shared_flags_overwrite_mechanism(self):
        # Model of the verified C++ aliasing, NOT execution of FreeCAD 1.1.4.
        def shared_flags(poly):
            flags = poly['flags']
            for vertex in poly['vertices']:
                if vertex['flagsPresent']:
                    flags = vertex['flags']
            return flags
        self.assertEqual(shared_flags(self.poly) & 1, 0)
        self.assertEqual(shared_flags(legacy_polylines(self.variants[1][1])[0]) & 1, 1)

    def test_missing_closing_edge_is_a_real_failure(self):
        oracle = read_json(ROOT / 'expected.json')['cases'][0]
        p, m = packet(0)
        p['evidence'].pop()  # the third and closing polyline edge
        result = compare(p, oracle, m)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(next(c for c in result['checks'] if c['id'] == 'polyline_closing')['status'], 'failed')

    def test_brep_validity_cannot_override_missing_closure(self):
        oracle = read_json(ROOT / 'expected.json')['cases'][0]
        p, m = packet(0); p['evidence'].pop()
        # Coordinate-complete comparison must retain the geometric failure.
        result = assess_geometry(p, oracle, m, [])
        self.assertEqual(result['status'], 'failed')

    def test_fixture_variants_never_change_original(self):
        self.assertEqual((ROOT / 'examples/01_geometrias_mm.dxf').read_bytes(), self.raw)
        self.assertEqual(len(self.variants), 5)
        self.assertEqual(self.variants[-1][2], 2)
        self.assertEqual(legacy_polylines(self.variants[-1][1])[0]['flags'], 0)


class PendingStateTests(unittest.TestCase):
    def test_case02_semantic_pending_preserved(self):
        p, m = packet(1)
        result = assess_geometry(p, read_json(ROOT / 'expected.json')['cases'][1], m, [])
        self.assertEqual(result['status'], 'pending')
        self.assertTrue(any(c['id'] == 'paper_and_annotations' and c['status'] == 'pending' for c in result['checks']))

    def test_case04_unit_pending_preserved(self):
        p = {'geometries': [{'id': 'a', 'payload': {'type': 'LINE'}}, {'id': 'b', 'payload': {'type': 'BSPLINE'}}],
             'evidence': [{'value': {'objectName': 'O', 'edges': [{'geometryId': 'a', 'index': 1}, {'geometryId': 'b', 'index': 2}]}}]}
        result = assess_geometry(p, read_json(ROOT / 'expected.json')['cases'][3], {}, [])
        self.assertEqual(result['status'], 'pending')
        self.assertTrue(any(c['id'] == 'physical_units' and c['status'] == 'pending' for c in result['checks']))

    def test_unresolved_frame_never_fabricates_global_approval(self):
        result = assess_geometry({}, read_json(ROOT / 'expected.json')['cases'][2], {},
                                 [{'name': 'Unknown', 'coordinateFrameStatus': 'unresolved'}])
        self.assertEqual(result['status'], 'pending')
        self.assertFalse(result['provisionalResultsAccepted'])
        self.assertEqual(result['knownFrameComparison']['status'], 'failed')
        self.assertEqual(result['checks'][0]['objects'], ['Unknown'])


class MacroRevisionTests(unittest.TestCase):
    def test_macro_loads_current_copy_without_reusing_cached_old_bootstrap(self):
        old = SimpleNamespace(main=lambda **kwargs: self.fail('Old diagnostic code reused'))
        real_import = importlib.import_module
        called = []
        before = set(sys.modules)
        def load_current(name, *args, **kwargs):
            module = real_import(name, *args, **kwargs)
            if name.startswith('_jeia_diag_launcher_') and name.endswith('.bootstrap'):
                self.assertEqual(module.ROOT, ROOT)
                return SimpleNamespace(main=lambda **kw: called.append(name))
            return module
        with patch.dict(sys.modules, {'diagnostic.bootstrap': old}), \
                patch.object(importlib, 'import_module', side_effect=load_current):
            runpy.run_path(str(ROOT / 'Executar_Diagnostico.FCMacro'))
            self.assertIs(sys.modules['diagnostic.bootstrap'], old)
        self.assertEqual(len(called), 1)
        self.assertFalse(any(n.startswith('_jeia_diag_launcher_') for n in set(sys.modules)-before))



if __name__ == '__main__':
    unittest.main()
