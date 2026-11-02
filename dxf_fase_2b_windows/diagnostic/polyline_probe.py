"""Read-only differential probe of the existing importer, not a polyline repair.

Only synthetic diagnostic files are generated inside the new session. The four
approved examples, the installed importer and JEIA are never modified.
"""
from hashlib import sha256
from pathlib import Path
import traceback

from .core import close


def records(raw):
    lines = raw.decode('utf-8').splitlines()
    if len(lines) % 2:
        raise ValueError('Incomplete DXF group pair')
    return [(int(lines[i].strip()), lines[i+1].strip()) for i in range(0, len(lines), 2)]


def legacy_polylines(raw):
    pairs = records(raw)
    results, current, vertex = [], None, None
    for code, value in pairs:
        if code == 0:
            if vertex is not None and current is not None:
                current['vertices'].append(vertex)
                vertex = None
            if value == 'POLYLINE':
                current = {'handle': None, 'flags': 0, 'vertices': []}
            elif value == 'VERTEX' and current is not None:
                vertex = {'flags': 0, 'flagsPresent': False, 'point': [0., 0., 0.]}
            elif value == 'SEQEND' and current is not None:
                results.append(current); current = None
        elif current is not None:
            if vertex is not None:
                if code == 70:
                    vertex.update(flags=int(value), flagsPresent=True)
                elif code in (10, 20, 30):
                    vertex['point'][(10, 20, 30).index(code)] = float(value)
            elif code == 70:
                current['flags'] = int(value)
            elif code == 5:
                current['handle'] = value
    return results


def variants(raw):
    """Extract the known three-vertex synthetic fixture; never rewrite the input."""
    polylines = legacy_polylines(raw)
    if len(polylines) != 1:
        raise ValueError('Probe requires exactly one legacy synthetic POLYLINE')
    poly = polylines[0]
    points = [v['point'] for v in poly['vertices']]
    if len(points) != 3 or not poly['flags'] & 1:
        raise ValueError('Probe requires the approved closed three-vertex POLYLINE')
    header = [(0, 'SECTION'), (2, 'HEADER'), (9, '$ACADVER'), (1, 'AC1024'),
              (9, '$INSUNITS'), (70, '4'), (0, 'ENDSEC'),
              (0, 'SECTION'), (2, 'ENTITIES')]
    tail = [(0, 'ENDSEC'), (0, 'EOF')]
    def encode(body):
        return ''.join(str(c) + '\n' + str(v) + '\n' for c, v in header + body + tail).encode('ascii')
    def legacy(include_flags, closed=True, repeat_first=False):
        body = [(0, 'POLYLINE'), (100, 'AcDbEntity'), (8, '0'), (100, 'AcDb2dPolyline'),
                (66, '1'), (10, 0), (20, 0), (30, 0), (70, '1' if closed else '0')]
        for p in points + ([points[0]] if repeat_first else []):
            body.extend([(0, 'VERTEX'), (100, 'AcDbEntity'), (8, '0'), (100, 'AcDbVertex'),
                         (100, 'AcDb2dVertex'), (10, p[0]), (20, p[1]), (30, p[2])])
            if include_flags:
                body.append((70, '0'))
        return encode(body + [(0, 'SEQEND'), (100, 'AcDbEntity'), (8, '0')])
    lw = [(0, 'LWPOLYLINE'), (100, 'AcDbEntity'), (8, '0'), (100, 'AcDbPolyline'), (90, '3'), (70, '1')]
    for p in points:
        lw.extend([(10, p[0]), (20, p[1])])
    return poly, [
        ('legacy_vertex70_zero', legacy(True), 3),
        ('legacy_vertex70_omitted', legacy(False), 3),
        ('lwpolyline_closed', encode(lw), 3),
        ('legacy_explicit_endpoint', legacy(True, repeat_first=True), 3),
        ('legacy_open_control', legacy(True, closed=False), 2)]


def inspect_native(doc, closing_start, closing_end):
    """Local evidence, before adapter. No inference of WCS or piece semantics."""
    objects = []
    for obj in doc.Objects:
        if not hasattr(obj, 'Shape') or obj.Shape.isNull():
            continue
        edges = []
        for edge in obj.Shape.Edges:
            a, b = list(edge.valueAt(edge.FirstParameter)), list(edge.valueAt(edge.LastParameter))
            edges.append({'startLocal': a, 'endLocal': b, 'length': float(edge.Length),
                          'closingLandmark': ((close(a, closing_start) and close(b, closing_end))
                                              or (close(a, closing_end) and close(b, closing_start)))})
        objects.append({'name': obj.Name, 'typeId': obj.TypeId, 'edges': edges,
                        'edgeCountBeforeAdapter': len(obj.Shape.Edges),
                        'shapeBrepSha256': sha256(obj.Shape.exportBrepToString().encode()).hexdigest()})
    return {'objects': objects, 'edgeCountBeforeAdapter': sum(o['edgeCountBeforeAdapter'] for o in objects),
            'closingLandmarkPresentBeforeAdapter': any(e['closingLandmark'] for o in objects for e in o['edges']),
            'coordinateFrame': 'native_local_only', 'countsMeaning': 'observations, not physical quantities'}


def run_probe(app, importer, input_path, output_dir):
    """Run only inside an already verified isolated FreeCADCmd profile."""
    from jeia_dxf_freecad.collector import collect_document
    from jeia_dxf_freecad.contract import metadata
    raw = Path(input_path).read_bytes()
    poly, cases = variants(raw)
    cases = [('approved_original_full', raw, 8)] + cases
    output = Path(output_dir); output.mkdir()
    settings = app.ParamGet('User parameter:BaseApp/Preferences/Mod/Draft')
    report = {'kind': 'isolated_polyline_differential_probe', 'freecadVersion': list(app.Version()),
              'inputSha256': sha256(raw).hexdigest(), 'originalPolyline': poly, 'trials': [],
              'windowsValidationApproved': False, 'integrationApproved': False,
              'warning': 'Synthetic variants only. No generated variant repairs or replaces approved DXFs.'}
    # One session-local settings group. Modes have version-specific semantics;
    # retain actual importer statistics instead of assuming support from SetInt.
    profiles = [('isolated_defaults', None), ('mode0_no_layers', 0), ('mode1_no_layers', 1),
                ('mode2_no_layers', 2), ('mode3_no_layers', 3)]
    for label, mode in profiles:
        if mode is not None:
            settings.SetBool('dxfUseDraftVisGroups', False)
            settings.SetInt('DxfImportMode', mode)
        for name, content, count in cases:
            path = output / (label + '__' + name + '.dxf')
            path.write_bytes(content)
            trial = {'profile': label, 'variant': name, 'inputSha256': sha256(content).hexdigest(),
                     'expectedEdges': count, 'requestedMode': mode, 'status': 'failed'}
            doc = None
            try:
                doc = app.newDocument('JEIA_POLYLINE_PROBE')
                stats = importer.readDXF(str(path), doc.Name, False)
                doc.recompute()
                before = inspect_native(doc, poly['vertices'][-1]['point'], poly['vertices'][0]['point'])
                trial['beforeAdapter'] = before
                trial['importStatistics'] = stats if isinstance(stats, (dict, list, str, int, float, bool, type(None))) else str(stats)
                packet = collect_document(doc, metadata(content, path.name), app, synthetic=True)
                observations = [e['value'] for e in packet['evidence'] if 'counts' in e['value']]
                trial['afterAdapterEdgeCounts'] = {v['objectName']: v['counts']['edges'] for v in observations}
                trial['unresolvedAdapterObjects'] = [e['value']['objectName'] for e in packet['evidence']
                    if e['value'].get('coordinateFrameStatus') == 'unresolved']
                trial['status'] = 'passed' if before['edgeCountBeforeAdapter'] == count else 'failed'
                if count in (3, 8) and not before['closingLandmarkPresentBeforeAdapter']:
                    trial['status'] = 'failed'
                after = inspect_native(doc, poly['vertices'][-1]['point'], poly['vertices'][0]['point'])
                # Kernel copies may reorder the BREP location table without
                # changing geometry; compare native edge observations instead.
                for facts in (before, after):
                    for observed in facts['objects']:
                        observed.pop('shapeBrepSha256', None)
                if after != before:
                    raise RuntimeError('Collector changed native shape observations')
                trial['collectorReadOnlyVerified'] = True
            except Exception as exc:
                trial.update(status='failed', error=type(exc).__name__ + ': ' + str(exc), trace=traceback.format_exc())
            finally:
                if doc is not None:
                    app.closeDocument(doc.Name)
            report['trials'].append(trial)
            # Save progress even if a later native trial crashes or times out.
            from .core import write_json
            write_json(output / (label + '__' + name + '.json'), trial)
    if Path(input_path).read_bytes() != raw:
        raise RuntimeError('Original example changed')
    report['sourceUnchanged'] = True
    return report
