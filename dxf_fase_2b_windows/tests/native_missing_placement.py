"""Real Part shape in a wrapper without getGlobalPlacement, not a Windows run."""
import argparse
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'approved_adapter'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freecad-lib', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); sys.path.insert(0, args.freecad_lib)
    import FreeCAD as app
    import Part
    from jeia_dxf_freecad.collector import collect_document
    from jeia_dxf_freecad.contract import metadata
    from diagnostic.native_worker import inspect_objects, brep_audit
    from diagnostic.core import write_json
    local_shape = Part.makeLine(app.Vector(10,20,30), app.Vector(20,20,30))
    obj = SimpleNamespace(Name='NativeWrapper', Label='Local only', TypeId='Part::FeaturePython',
                          Shape=local_shape, PropertiesList=[], Placement=app.Placement())
    doc = SimpleNamespace(Objects=[obj])
    inventory, points = inspect_objects(doc)
    assert points == {} and inventory[0]['coordinateFrameStatus'] == 'unresolved'
    raw = b'0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n'
    packet = collect_document(doc, metadata(raw, 'SYNTHETIC_UNRESOLVED.dxf'), app, synthetic=True)
    assert all(g['payload']['type'] == 'UNSUPPORTED' for g in packet['geometries'])
    evidence = next(e['value'] for e in packet['evidence'] if 'localBrep' in e['value'])
    assert evidence['localBrep'] and 'globalBrep' not in evidence
    checks, _ = brep_audit(packet, Part)
    assert len(checks) == 1 and checks[0]['status'] == 'passed' and checks[0]['kind'] == 'localBrep'
    assert checks[0]['physicalCoordinatesApproved'] is False
    assert list(local_shape.Vertexes[0].Point) == [10.,20.,30.]
    write_json(args.output, {'kind': 'real_kernel_missing_method_wrapper_NOT_WINDOWS',
                            'freecadVersion': list(app.Version()), 'inventory': inventory,
                            'globalMidpoints': points, 'packet': packet, 'brepChecks': checks,
                            'integrationApproved': False, 'windowsValidationApproved': False})
    print('PASS: native local BREP retained; no global coordinates invented; no AttributeError')


if __name__ == '__main__':
    main()
