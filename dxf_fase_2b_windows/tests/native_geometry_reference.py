"""Optional developer probe; uses an already installed compatible FreeCAD Python.

This constructs shapes in memory, NOT a DXF import or Windows validation.
Run with --freecad-lib and --output using a compatible existing interpreter.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'approved_adapter'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freecad-lib', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, args.freecad_lib)
    import FreeCAD as app
    import Part
    from jeia_dxf_freecad.collector import collect_document
    from jeia_dxf_freecad.contract import metadata, vec
    from diagnostic.core import compare, read_json, write_json
    from diagnostic.native_worker import brep_audit
    expected = read_json(ROOT / 'expected.json')['cases'][0]
    doc = app.newDocument('DiagnosticReference')
    try:
        # Independent explicit construction using the geometry's defining points.
        edges = [Part.makeLine(app.Vector(0,0,0), app.Vector(10,0,0)),
                 Part.makeCircle(5, app.Vector(20,0,0), app.Vector(0,0,1), 350, 370),
                 Part.makeCircle(3, app.Vector(40,0,0)),
                 Part.Arc(app.Vector(0,20,0), app.Vector(5,15,0), app.Vector(10,20,0)).toShape(),
                 Part.Arc(app.Vector(10,20,0), app.Vector(15,25,0), app.Vector(20,20,0)).toShape(),
                 Part.makeLine(app.Vector(0,40,0), app.Vector(10,40,0)),
                 Part.makeLine(app.Vector(10,40,0), app.Vector(10,50,0)),
                 Part.makeLine(app.Vector(10,50,0), app.Vector(0,40,0))]
        midpoints = {}
        for i, edge in enumerate(edges):
            obj = doc.addObject('Part::Feature', 'Reference%d' % i); obj.Shape = edge
            midpoints[obj.Name + '.Edge1'] = vec(edge.valueAt((edge.FirstParameter+edge.LastParameter)/2))
        doc.recompute()
        raw = b'0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n'
        packet = collect_document(doc, metadata(raw, 'SYNTHETIC_REFERENCE.dxf'), app, synthetic=True)
        result = compare(packet, expected, midpoints)
        checks, _ = brep_audit(packet, Part)
        output = {'kind': 'native_in_memory_reference_NOT_DXF', 'freecadVersion': list(app.Version()),
                  'windowsValidationApproved': False, 'integrationApproved': False,
                  'comparison': result, 'brepChecks': checks}
        damaged = copy.deepcopy(packet)
        topology = next(e['value'] for e in damaged['evidence'] if 'globalBrep' in e['value'])
        topology['globalBrep'] = ''
        omitted_checks, _ = brep_audit(damaged, Part)
        assert any(c['status'] == 'failed' for c in omitted_checks), 'Missing BREP falsely accepted'
        topology['globalBrep'] = next(e['value']['globalBrep'] for e in packet['evidence'] if 'globalBrep' in e['value'])
        topology['counts']['edges'] += 1
        altered_checks, _ = brep_audit(damaged, Part)
        assert any(c['status'] == 'failed' for c in altered_checks), 'Changed BREP topology falsely accepted'
        output['negativeBrepChecks'] = {'missingBrepRejected': True, 'changedTopologyRejected': True}
        write_json(args.output, output)
        assert result['status'] == 'passed', result
        assert len(checks) == 16 and all(c['status'] == 'passed' for c in checks), checks
        print('PASS: 8 real kernel geometric references and 16 native BREP round-trips; NOT DXF/Windows approval')
    finally:
        app.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
