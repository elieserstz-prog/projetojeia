"""Executed only by the existing FreeCADCmd; no downloads or package installation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'approved_adapter'))
from diagnostic.core import close, isolation, read_json, write_json


def inspect_objects(doc):
    """Observe local shapes; emit global points only after a proven transform.

    Matches the approved collector's strict placement policy. A missing method
    is neither an identity placement nor a reason to abort the other objects.
    """
    inventory, midpoints = [], {}
    for obj in doc.Objects:
        item = {'name': obj.Name, 'label': obj.Label, 'typeId': obj.TypeId,
                'hasShape': hasattr(obj, 'Shape'), 'properties': list(obj.PropertiesList)}
        if hasattr(obj, 'Shape'):
            item['nullShape'] = obj.Shape.isNull()
            if not item['nullShape']:
                item['nativeShapeCounts'] = {'edges': len(obj.Shape.Edges), 'faces': len(obj.Shape.Faces),
                                             'vertices': len(obj.Shape.Vertexes), 'solids': len(obj.Shape.Solids)}
                # These facts precede the adapter and are explicitly LOCAL.
                item['nativeLocalEdges'] = [
                    {'index': i, 'curveType': type(edge.Curve).__name__, 'length': float(edge.Length),
                     'start': list(edge.valueAt(edge.FirstParameter)),
                     'end': list(edge.valueAt(edge.LastParameter))}
                    for i, edge in enumerate(obj.Shape.Edges, 1)]
                try:
                    get_global = getattr(obj, 'getGlobalPlacement', None)
                    if not callable(get_global):
                        raise AttributeError('getGlobalPlacement() not available on ' + obj.TypeId)
                    placement = get_global().multiply(obj.Placement.inverse()).multiply(obj.Shape.Placement)
                    shape = obj.Shape.copy()
                    shape.Placement = placement
                    object_points = {}
                    for index, edge in enumerate(shape.Edges, 1):
                        point = edge.valueAt((edge.FirstParameter + edge.LastParameter) / 2)
                        object_points[obj.Name + '.Edge' + str(index)] = [float(v) for v in point]
                    midpoints.update(object_points)
                    item['coordinateFrameStatus'] = 'global_known'
                except (AttributeError, RuntimeError, ValueError, TypeError) as exc:
                    item['coordinateFrameStatus'] = 'unresolved'
                    item['coordinateDiagnostic'] = type(exc).__name__ + ': ' + str(exc)
        for prop in ('Text', 'String', 'LabelText'):
            if prop in obj.PropertiesList:
                value = getattr(obj, prop)
                if isinstance(value, (str, list, tuple)):
                    item[prop] = value if isinstance(value, str) else [str(v) for v in value]
        inventory.append(item)
    return inventory, midpoints


def brep_audit(packet, part):
    checks, midpoints = [], {}
    for evidence in packet['evidence']:
        obj = evidence['value']
        if 'objectName' not in obj:
            continue
        kinds = ('localBrep',) if obj.get('coordinateFrameStatus') == 'unresolved' else (
            ('rawObjectBrep', 'globalBrep') if 'edges' in obj else ())
        for kind in kinds:
            text = obj.get(kind)
            item = {'object': obj['objectName'], 'kind': kind, 'status': 'failed'}
            try:
                if not text:
                    raise ValueError('BREP missing; omission is not a successful test')
                shape = part.Shape()
                shape.importBrepFromString(text)
                counts = {'edges': len(shape.Edges), 'faces': len(shape.Faces),
                          'vertices': len(shape.Vertexes), 'solids': len(shape.Solids)}
                item.update(valid=bool(shape.isValid()), counts=counts,
                            sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                            bytes=len(text.encode('utf-8')))
                if shape.isNull() or not shape.isValid() or ('counts' in obj and counts != obj['counts']):
                    raise ValueError('Invalid or changed BREP topology')
                if kind == 'localBrep':
                    item['coordinateFrameStatus'] = 'unresolved'
                    item['physicalCoordinatesApproved'] = False
                if kind == 'globalBrep':
                    for edge, recorded in zip(shape.Edges, obj['edges']):
                        if not close(edge.Length, recorded['lengthMm']):
                            raise ValueError('BREP edge length mismatch')
                item['status'] = 'passed'
            except Exception as exc:
                item['error'] = type(exc).__name__ + ': ' + str(exc)
            checks.append(item)
    return checks, midpoints


def collect(request):
    import FreeCAD as app
    import Part
    from jeia_dxf_freecad.collector import collect_document
    from jeia_dxf_freecad.contract import metadata
    iso = isolation(app, request['session'])
    if not iso['passed']:
        return {'workerError': 'FreeCAD configuration isolation not confirmed', 'isolation': iso}
    if request.get('mode') == 'polyline_probe':
        import Import
        from diagnostic.polyline_probe import run_probe
        result = run_probe(app, Import, request['input'], request['probeOutput'])
        result['isolation'] = iso
        return result
    doc = None
    old = app.ActiveDocument
    try:
        doc = app.newDocument('JEIA_DIAG_' + uuid.uuid4().hex)
        control = request.get('mode') == 'kernel_control'
        if control:
            raw = b'0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n'
            name = 'SYNTHETIC_KERNEL_CONTROL.dxf'
            doc.addObject('Part::Feature', 'ControlBox').Shape = Part.makeBox(10, 20, 30)
        else:
            import Import
            draft = Path(app.getResourceDir()) / 'Mod' / 'Draft'
            if draft.is_dir() and str(draft) not in sys.path:
                sys.path.append(str(draft))
            path = Path(request['input'])
            raw, name = path.read_bytes(), path.name
            if hashlib.sha256(raw).hexdigest() != request['inputSha256']:
                raise ValueError('Input differs from requested SHA-256')
            # Same entry point as the approved Fase 2B adapter. No legacy fallback.
            Import.readDXF(str(path), doc.Name, False)
        doc.recompute()
        inventory, midpoints = inspect_objects(doc)
        packet = collect_document(doc, metadata(raw, name), app, request_id=request['requestId'],
                                  generation=request['generation'], revision=request['revision'], synthetic=control,
                                  max_edges=20000, max_faces=10000, max_brep_bytes=16*1024*1024)
        packet['sources'][1]['options']['importer'] = 'synthetic kernel control' if control else 'Import.readDXF(ignore_errors=False)'
        if not control and path.read_bytes() != raw:
            raise ValueError('Input modified during import')
        checks, _ = brep_audit(packet, Part)
        result = {'packet': packet, 'objectInventory': inventory, 'edgeMidpoints': midpoints,
                  'brepChecks': checks, 'isolation': iso, 'freecadVersion': list(app.Version()),
                  'pythonVersion': sys.version, 'importer': packet['sources'][1]['options']['importer']}
        if control:
            summary = next(g['payload'] for g in packet['geometries'] if g['payload']['type'] == 'BREP_SUMMARY')
            result['kernelControlPassed'] = (summary['edges'] == 12 and summary['faces'] == 6
                                             and close(summary['volume']['value'], 6000)
                                             and bool(checks) and all(c['status'] == 'passed' for c in checks))
        return result
    except Exception as exc:
        # Preserve observations from a partially failed importer, but mark the
        # entire response as rejected so it cannot reach geometric comparison.
        result = {'workerError': type(exc).__name__ + ': ' + str(exc),
                  'workerTrace': traceback.format_exc(), 'partialImport': True,
                  'partialResultsAccepted': False, 'isolation': iso}
        if doc is not None:
            try:
                result['partialDocumentInventory'] = [
                    {'name': obj.Name, 'typeId': obj.TypeId, 'hasShape': hasattr(obj, 'Shape')}
                    for obj in doc.Objects]
                if 'raw' in locals():
                    result['rejectedPartialPacket'] = collect_document(
                        doc, metadata(raw, name), app, request_id=request['requestId'],
                        generation=request['generation'], revision=request['revision'],
                        synthetic=bool(request.get('mode') == 'kernel_control'))
            except Exception as inspection_error:
                result['partialInspectionError'] = str(inspection_error)
        return result
    finally:
        if doc is not None:
            app.closeDocument(doc.Name)
        if old is not None and app.getDocument(old.Name) is not None:
            app.setActiveDocument(old.Name)


def main():
    request = read_json(os.environ['JEIA_DIAG_REQUEST'])
    try:
        result = collect(request)
    except Exception as exc:
        result = {'workerError': type(exc).__name__ + ': ' + str(exc), 'workerTrace': traceback.format_exc()}
    write_json(os.environ['JEIA_DIAG_RESPONSE'], result)


if __name__ == '__main__':
    main()
