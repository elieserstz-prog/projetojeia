"""Independent ezdxf adapter for JEIA_DXF_TECH 1.0.

Extraction only: no physical feature inference, operations, CAD integration,
network access, package installation, source-file changes or automatic repair.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
import uuid

import ezdxf
from ezdxf import transform, units
from ezdxf.filemanagement import dxf_stream_info
from ezdxf.lldxf.types import cast_tag_value
from ezdxf.math import Matrix44, Vec3
from jsonschema import Draft202012Validator, FormatChecker


class AdapterError(ValueError):
    """Invalid/unsupported input or an unsafe extraction prerequisite."""


@dataclass(frozen=True)
class Options:
    request_id: str | None = None
    selection_generation: int = 0
    analysis_revision: int = 1
    max_bytes: int = 64 * 1024 * 1024
    max_entities: int = 100_000
    max_occurrences: int = 100_000
    max_depth: int = 32

    def __post_init__(self):
        if self.request_id is not None and (not isinstance(self.request_id,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9._:/@+\-]{0,255}',self.request_id)):
            raise AdapterError('Invalid request_id')
        for name in ('max_bytes', 'max_entities', 'max_occurrences', 'max_depth', 'analysis_revision'):
            v = getattr(self, name)
            if type(v) is not int or v <= 0:
                raise AdapterError(name + ' must be a positive integer')
        if type(self.selection_generation) is not int or self.selection_generation < 0:
            raise AdapterError('selection_generation must be a nonnegative integer')


def state(value='extracted', reason=None, diagnostics=()):
    return dict(state=value, evidenceIds=[], diagnosticIds=list(diagnostics), reason=reason)


def quantity(value=None, unit='unknown', reason=None):
    return dict(value=value, unit=unit, validation=state('extracted' if value is not None else 'unknown', reason))


def plain(value):
    """JSON-safe existing attributes, without silently replacing nonfinite numbers."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AdapterError('Nonfinite numeric attribute')
        return value
    if isinstance(value, bytes):
        return {'binaryHex': value.hex()}
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, Vec3)):
        return [plain(v) for v in value]
    try:
        return [plain(v) for v in value]
    except TypeError as exc:
        raise AdapterError('Unsupported attribute serialization: ' + type(value).__name__) from exc


def vector(p):
    return plain(list(Vec3(p)))


def identity():
    return [[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]]


def mul(left, right):
    return [[sum(left[i][k] * right[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def apply(m, p):
    return Vec3(*(sum(m[i][j] * p[j] for j in range(3)) + m[i][3] for i in range(3)))


def from_native(m):
    """ezdxf uses row vectors. Contract uses column vectors."""
    o = m.transform(Vec3())
    axes = [m.transform(Vec3(*p)) - o for p in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]
    return [[axes[j][i] for j in range(3)] + [o[i]] for i in range(3)] + [[0., 0., 0., 1.]]


def to_native(m):
    return Matrix44([m[j][i] for i in range(4) for j in range(4)])


def determinant(m):
    a, b, c = [r[:3] for r in m[:3]]
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


@lru_cache(maxsize=1)
def _validator():
    schema = json.loads(Path(__file__).with_name('schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_structure(package):
    """Structural contract validation only; not the full semantic validator."""
    _validator().validate(package)
    json.dumps(package, allow_nan=False)


def raw_records(text):
    """Preserve original value lines and repeated group codes by source handle."""
    rows = text.splitlines()
    if len(rows) % 2:
        raise AdapterError('Unpaired DXF group/value lines')
    records, record = [], []
    for i in range(0, len(rows), 2):
        try:
            code = int(rows[i].strip())
        except ValueError as exc:
            raise AdapterError('Invalid DXF group code at line ' + str(i+1)) from exc
        if code == 0 and record:
            records.append(record)
            record = []
        try:
            decoded=plain(cast_tag_value(code,rows[i+1]))
        except (ValueError,TypeError) as exc:
            raise AdapterError('Invalid DXF value at line '+str(i+2)) from exc
        record.append({'code': code, 'rawValue': rows[i+1], 'decodedValue': decoded})
    if record:
        records.append(record)
    by_handle, missing = {}, []
    for ordinal, tags in enumerate(records):
        first = next((t['rawValue'].strip() for t in tags if t['code'] == 0), '')
        handles = [t['rawValue'].strip().upper() for t in tags if t['code'] in (5, 105)]
        # HEADER $HANDSEED is not an entity handle. Never map a synthesized
        # library helper to a SECTION record just because the seed matches.
        if handles and first not in ('SECTION','ENDSEC','EOF','TABLE','ENDTAB'):
            h = handles[0]
            if h in by_handle:
                raise AdapterError('Duplicate source handle: ' + h)
            by_handle[h] = (ordinal, tags)
        else:
            missing.append((ordinal, first, tags))
    return by_handle, missing


class _Extraction:
    def __init__(self, data, filename, options):
        self.options = options
        self.hash = sha256(data).hexdigest()
        if data.startswith(b'AutoCAD Binary DXF'):
            raise AdapterError('Binary DXF is not supported in Fase 2A; no implicit text conversion')
        try:
            info = dxf_stream_info(io.StringIO(data.decode('latin1')))
            self.encoding = info.encoding
            text = data.decode(self.encoding, errors='strict')
            self.raw, self.no_handle = raw_records(text)
            if not any(typ=='EOF' for _,typ,_ in self.no_handle):
                raise AdapterError('Missing DXF EOF marker')
            self.doc = ezdxf.read(io.StringIO(text))
        except AdapterError:
            raise
        except (UnicodeError, LookupError, ezdxf.DXFError, ValueError, StopIteration) as exc:
            raise AdapterError('DXF decoding/parsing failed: ' + str(exc)) from exc
        if len(self.doc.entitydb) > options.max_entities:
            raise AdapterError('Entity resource limit exceeded before extraction')
        self.package = {name: [] for name, prop in _validator().schema['properties'].items() if prop.get('type') == 'array'}
        self.package.update(contract='JEIA_DXF_TECH', version='1.0', context=dict(
            requestId=options.request_id or 'req-' + uuid.uuid4().hex,
            selectionGeneration=options.selection_generation, analysisRevision=options.analysis_revision,
            purpose='production_analysis', producer='experimental-ezdxf-adapter-0.1.0',
            createdAt=datetime.now(timezone.utc).isoformat()), validation=dict(stage='extracted',
            schemaStatus='not_checked', semanticStatus='not_checked', eligibility=[], cncReleased=False))
        self.eids, self.entities, self.rawframes, self.layers, self.blocks = {}, {}, {}, {}, {}
        self.entity_records, self.raw_gids = {}, {}
        self.frame_units, self.space_frames, self.space_factors, self.style_ids = {}, {}, {}, {}
        self.limit_reported = False
        self.factor = None
        self.model_units = int(self.doc.header.get('$INSUNITS', 0))
        # Exact DXF/industrial factors; avoid the rounded reciprocal factors
        # used by some library conversion tables (notably international inch).
        self.factor = {1:25.4,2:304.8,3:1609344.,4:1.,5:10.,6:1000.,7:1e6,
            8:0.0000254,9:0.0254,10:914.4,11:1e-7,12:1e-6,13:0.001,
            14:100.,15:1e4,16:1e5,17:1e12,21:1200000/3937,
            22:100000/3937,23:3600000/3937,24:6336000000/3937}.get(self.model_units)
        self.package['document'] = dict(id=self.id('document'), fileName=filename, sha256=self.hash,
            byteLength=len(data), dxfVersion=self.doc.dxfversion, encoding=self.encoding,
            units=dict(rawInsunits=self.model_units, rawMeasurement=self.doc.header.get('$MEASUREMENT'),
                resolvedUnit=units.unit_name(self.model_units) if self.factor else None,
                mmPerDrawingUnit=self.factor, resolutionMethod='header' if self.factor else 'unknown',
                validation=state('extracted' if self.factor else 'unknown', 'Read from DXF header; no physical scale inferred')),
            rawHeader={str(k): plain(self.doc.header[k]) for k in self.doc.header.varnames()}, validation=state())
        for kind, version in [('dxf_original', self.doc.dxfversion), ('ezdxf', ezdxf.__version__), ('rule_engine', '0.1.0')]:
            self.package['sources'].append(dict(id=self.id('source', kind), kind=kind, version=version,
                inputSha256=self.hash, options={'maxBytes':options.max_bytes,'maxEntities':options.max_entities,
                    'maxDepth': options.max_depth, 'maxOccurrences': options.max_occurrences,
                    'automaticRepair': False, 'experimental': True}, capabilities=['ascii_dxf_extraction_only'], validation=state()))
        self.diag('EXTRACTION_ONLY', 'No physical part/feature/operation inference or JEIA integration in Fase 2A.')
        self.diag('FREECAD_NOT_RUN', 'Only ezdxf was executed; FreeCAD observations and reconciliation are not fabricated.', 'info')
        if self.factor is None:
            self.diag('UNITS_UNRESOLVED', 'No conversion factor 1 fallback for absent or unsupported INSUNITS.')

    def id(self, kind, *keys):
        return kind + '-' + sha256(json.dumps([self.hash, kind, *keys], ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()[:32]

    def diag(self, code, message, severity='blocker', targets=None, details=None):
        id = self.id('diagnostic', code, len(self.package['diagnostics']))
        self.package['diagnostics'].append(dict(id=id, code=code, severity=severity,
            targets=targets or [dict(kind='document', id=self.package['document']['id'])], message=message,
            details=plain(details), blocksConsumers=[] if severity == 'info' else ['material', 'process', 'cost'],
            status='open', evidenceIds=[]))
        return id

    def frame(self, key, kind, unit, space=None):
        id = self.id('frame', key)
        if id not in self.frame_units:
            self.frame_units[id] = unit
            self.package['frames'].append(dict(id=id, kind=kind, unit=unit, spaceId=space, description=key))
        return id

    def transform_record(self, key, src, dst, matrix, kind, components=()):
        id = self.id('transform', key)
        self.package['transforms'].append(dict(id=id, fromFrameId=src, toFrameId=dst, matrix=plain(matrix),
            kind=kind, componentTransformIds=list(components), validation=state()))
        return id

    def ocs_matrix(self, e):
        typ = e.dxftype()
        if typ not in ('CIRCLE', 'ARC', 'LWPOLYLINE', 'TEXT', 'ATTRIB', 'ATTDEF') and not (typ == 'POLYLINE' and e.is_2d_polyline):
            return identity(), False
        o = e.ocs()
        return [[o.ux[i], o.uy[i], o.uz[i], 0.] for i in range(3)] + [[0., 0., 0., 1.]], True

    def register(self, e, owner, owner_frame):
        key = id(e)
        if key in self.eids:
            return self.eids[key]
        h = str(e.dxf.get('handle', '')).upper()
        record = self.raw.get(h)
        if record is None:
            matches = [(i, tags) for i, typ, tags in self.no_handle if typ == e.dxftype()]
            if len(matches) == 1:
                record = matches[0]
            else:
                raise AdapterError('Cannot unambiguously map original raw record for ' + e.dxftype())
            h = None
            self.diag('HANDLE_MISSING', 'Identity uses original raw-record ordinal, not geometry.')
        ordinal, tags = record
        eid = self.id('entity', owner, h or ordinal)
        self.eids[key], self.entities[eid] = eid, e
        self.layers.setdefault(e.dxf.get('layer', '0'), self.id('layer', e.dxf.get('layer', '0')))
        _, ocs = self.ocs_matrix(e)
        fr = self.frame(eid, 'entity_ocs', self.frame_units[owner_frame]) if ocs else owner_frame
        self.rawframes[eid] = fr
        record=dict(id=eid, dxfType=e.dxftype(),
            origin=dict(sourceId=self.id('source', 'dxf_original'), handle=h, ownerHandle=e.dxf.get('owner'),
                ordinal=ordinal, identityMethod='dxf_handle' if h else 'owner_and_ordinal'),
            owner=owner, layerId=self.layers[e.dxf.get('layer', '0')], linetype=e.dxf.get('linetype', 'BYLAYER'),
            rawFrameId=fr, geometryIds=[], rawGroups=tags, validation=state())
        self.entity_records[eid]=record
        self.package['entities'].append(record)
        if e.dxftype() == 'POLYLINE':
            for child in e.vertices:
                self.register(child, dict(kind='entity', id=eid), owner_frame)
            if e.seqend is not None and e.seqend.dxf.get('handle','').upper() in self.raw:
                self.register(e.seqend, dict(kind='entity', id=eid), owner_frame)
        if e.dxftype() == 'INSERT':
            for child in e.attribs:
                self.register(child, dict(kind='entity', id=eid), owner_frame)
            # ezdxf creates virtual SEQEND helpers even for INSERT without
            # attributes. Do not fabricate source records for those helpers.
            if e.seqend is not None and e.seqend.dxf.get('handle','').upper() in self.raw:
                self.register(e.seqend, dict(kind='entity', id=eid), owner_frame)
        return eid

    def raw_geometry(self, e):
        t = e.dxftype()
        if t == 'LINE':
            a, b = Vec3(e.dxf.start), Vec3(e.dxf.end)
            if a == b:
                raise AdapterError('Degenerate zero-length LINE')
            return dict(type='LINE', start=vector(a), end=vector(b))
        if t == 'POINT':
            return dict(type='POINT', point=vector(e.dxf.location))
        if t in ('CIRCLE', 'ARC'):
            if e.dxf.radius <= 0:
                raise AdapterError('Invalid radius')
            v = dict(type=t, center=vector(e.dxf.center), normal=[0, 0, 1], radius=float(e.dxf.radius))
            if t == 'ARC':
                sweep = math.radians((e.dxf.end_angle-e.dxf.start_angle) % 360)
                if sweep == 0:
                    raise AdapterError('Degenerate ARC; not silently converted to CIRCLE')
                v.update(xAxis=[1, 0, 0], startRad=math.radians(e.dxf.start_angle), sweepRad=sweep)
            return v
        if t in ('LWPOLYLINE', 'POLYLINE'):
            if t == 'LWPOLYLINE':
                pts = [dict(point=[float(x), float(y), 0.], bulge=float(b), startWidth=float(sw), endWidth=float(ew))
                       for x, y, sw, ew, b in e.get_points('xyseb')]
                width = float(e.dxf.get('const_width', 0))
                if width:
                    for pt in pts:
                        pt.update(startWidth=width, endWidth=width)
                elevation, three = float(e.dxf.elevation), False
            else:
                if not (e.is_2d_polyline or e.is_3d_polyline):
                    raise AdapterError('POLYLINE mesh/polyface not supported')
                three = bool(e.is_3d_polyline)
                pts = [dict(point=vector(v.dxf.location) if three else [v.dxf.location.x, v.dxf.location.y, 0.],
                    bulge=float(v.dxf.get('bulge', 0)), startWidth=float(v.dxf.get('start_width', e.dxf.get('default_start_width',0))),
                    endWidth=float(v.dxf.get('end_width', e.dxf.get('default_end_width',0)))) for v in e.vertices]
                elevation = 0. if three else float(e.dxf.elevation.z)
            if len(pts) < 2:
                raise AdapterError('Polyline has fewer than two vertices')
            return dict(type='POLYLINE', vertices=pts, closed=bool(e.closed if t == 'LWPOLYLINE' else e.is_closed),
                normal=[0, 0, 1], elevation=elevation, is3d=three)
        if t == 'ELLIPSE':
            major = Vec3(e.dxf.major_axis)
            normal = Vec3(e.dxf.extrusion).normalize()
            minor = normal.cross(major).normalize(major.magnitude * e.dxf.ratio)
            sweep = (e.dxf.end_param-e.dxf.start_param) % math.tau
            return dict(type='ELLIPSE', center=vector(e.dxf.center), majorAxis=vector(major),
                minorAxis=vector(minor), startRad=float(e.dxf.start_param), sweepRad=sweep or math.tau)
        raise AdapterError('Geometry type not supported in Fase 2A: ' + t)

    def world_payload(self, e):
        p = self.raw_geometry(e)
        if e.dxftype() in ('CIRCLE', 'ARC'):
            ocs = e.ocs()
            p.update(center=vector(ocs.to_wcs(e.dxf.center)), normal=vector(ocs.uz))
            if e.dxftype() == 'ARC':
                p['xAxis'] = vector(ocs.ux)
        return p

    def geometry(self, eid, oid, frame, payload, suffix, derived=(), applied=()):
        id = self.id('geometry', eid, oid, suffix)
        self.package['geometries'].append(dict(id=id, sourceId=self.id('source', 'ezdxf'), entityId=eid,
            occurrenceId=oid, sourceObjectKey=None, frameId=frame, payload=plain(payload),
            approximation='unsupported' if payload['type'] == 'UNSUPPORTED' else 'analytic',
            derivedFromGeometryIds=list(derived), appliedTransformIds=list(applied),
            validation=state('unsupported',payload.get('reason')) if payload['type']=='UNSUPPORTED' else state()))
        self.entity_records[eid]['geometryIds'].append(id)
        if oid is None:
            self.raw_gids[eid]=id
        return id

    def canonical(self, e, eid, oid, raw_gid, world, dest, applied):
        nm = to_native(world)
        if e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
            pieces = list(e.virtual_entities())
            points = list(e.vertices_in_wcs() if e.dxftype() == 'LWPOLYLINE' else e.points_in_wcs())
            if not pieces:
                raise AdapterError('No supported polyline segments')
            expected=len(points) if (e.closed if e.dxftype()=='LWPOLYLINE' else e.is_closed) else len(points)-1
            if len(pieces)!=expected:
                raise AdapterError('Degenerate/unsupported polyline segment; endpoint correspondence not guessed')
            segments = []
            for i, piece in enumerate(pieces):
                log, clones = transform.copies([piece], nm)
                if len(log) or len(clones) != 1:
                    raise AdapterError('Segment transform failed: ' + str(list(log)))
                c = clones[0]
                payload = self.world_payload(c)
                gid = self.geometry(eid, oid, dest, payload, 'segment-'+str(i), [raw_gid], applied)
                expected = nm.transform(Vec3(points[i]))
                if c.dxftype() == 'LINE':
                    first, last = Vec3(c.dxf.start), Vec3(c.dxf.end)
                else:
                    first, last = Vec3(c.start_point), Vec3(c.end_point)
                segments.append(dict(geometryId=gid, reversed=(last-expected).magnitude < (first-expected).magnitude))
            return self.geometry(eid, oid, dest, dict(type='COMPOSITE_CURVE', segments=segments,
                closed=bool(e.closed if e.dxftype() == 'LWPOLYLINE' else e.is_closed)), 'canonical', [raw_gid], applied)
        log, clones = transform.copies([e], nm)
        if len(log) or len(clones) != 1:
            raise AdapterError('Entity transform failed: ' + str(list(log)))
        return self.geometry(eid, oid, dest, self.world_payload(clones[0]), 'canonical', [raw_gid], applied)

    def emit(self, e, space, parent, instance_path=(), inherited_layer='0', inherited_linetype='CONTINUOUS', inherited_visible=True):
        if len(self.package['occurrences']) >= self.options.max_occurrences:
            if not self.limit_reported:
                self.diag('OCCURRENCE_LIMIT_REACHED', 'Partial extraction: occurrence limit reached; coverage incomplete.')
                self.limit_reported = True
            return
        eid = self.eids[id(e)]
        oid = self.id('occurrence', eid, space, instance_path)
        fr, sf = self.rawframes[eid], self.space_frames[space]
        ocs, _ = self.ocs_matrix(e)
        full = mul(parent, ocs)
        tid = self.transform_record(oid, fr, sf, full, 'occurrence_to_space')
        layer_name = e.dxf.get('layer', '0')
        effective_layer = inherited_layer if layer_name == '0' else layer_name
        lt = e.dxf.get('linetype', 'BYLAYER')
        if lt == 'BYBLOCK':
            lt = inherited_linetype
        if lt == 'BYLAYER':
            try:
                lt = self.doc.layers.get(effective_layer).dxf.linetype
            except ezdxf.DXFTableEntryError:
                lt = None
        try:
            layer_obj=self.doc.layers.get(effective_layer)
            hidden=layer_obj.is_off() or layer_obj.is_frozen() or e.dxf.get('invisible',0)
            visible=False if hidden or inherited_visible is False else (None if inherited_visible is None else True)
        except ezdxf.DXFTableEntryError:
            visible=None
        occurrence = dict(id=oid, entityId=eid, spaceId=space, instancePath=list(instance_path), transformToSpaceId=tid,
            effectiveLayerId=self.layers[effective_layer], effectiveLinetype=lt, effectiveVisible=visible,
            canonicalGeometryId=None, validation=state())
        self.package['occurrences'].append(occurrence)
        self.package['classifications'].append(dict(id=self.id('classification', oid), targets=[dict(kind='occurrence', id=oid)],
            candidates=[dict(**{'class': 'unknown'}, evidenceIds=[], score=None)], selectedClass=None,
            inclusion='pending', decisionId=None, validation=state('unknown', 'Fase 2A does not classify physical meaning.')))
        typ = e.dxftype()
        if typ in ('INSERT', 'DIMENSION', 'ARC_DIMENSION', 'VIEWPORT', 'TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF', 'SEQEND', 'VERTEX'):
            pass
        else:
            try:
                payload = self.raw_geometry(e)
                raw_gid = self.raw_gids.get(eid) or self.geometry(eid, None, fr, payload, 'original')
                if payload['type']=='POLYLINE' and any(v['startWidth'] or v['endWidth'] for v in payload['vertices']):
                    self.diag('POLYLINE_WIDTH_NOT_MODELED','Widths preserved in raw polyline; canonical composite represents its centerline only.','warning',[dict(kind='occurrence',id=oid)])
                if e.dxf.hasattr('thickness') and e.dxf.thickness:
                    self.diag('THICKNESS_NOT_MODELED','DXF thickness preserved in raw groups; no surface/solid extrusion performed.','warning',[dict(kind='occurrence',id=oid)])
                factor = self.space_factors[space]
                if factor is not None:
                    unit_matrix = identity()
                    for i in range(3):
                        unit_matrix[i][i] = factor
                    dest = self.frame('mm:'+space, 'document_wcs' if self.space_kind(space) == 'model' else 'paper', 'mm', space)
                    ut = self.transform_record('units:'+oid, sf, dest, unit_matrix, 'unit_conversion')
                    occurrence['canonicalGeometryId'] = self.canonical(e, eid, oid, raw_gid, mul(unit_matrix, parent), dest, [tid, ut])
            except (AdapterError, ezdxf.DXFError, ValueError, ZeroDivisionError, ArithmeticError) as exc:
                self.diag('GEOMETRY_UNSUPPORTED', str(exc), targets=[dict(kind='occurrence', id=oid)])
                if eid not in self.raw_gids:
                    self.geometry(eid, None, fr, dict(type='UNSUPPORTED', originalType=typ, reason=str(exc)), 'unsupported')
        if typ in ('TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF'):
            raw = e.text if typ == 'MTEXT' else e.dxf.text
            anchor = vector(e.dxf.insert) if e.dxf.hasattr('insert') else None
            self.package['annotations'].append(dict(id=self.id('annotation', oid), entityId=eid, occurrenceId=oid,
                kind={'TEXT':'text','MTEXT':'mtext','ATTRIB':'attribute','ATTDEF':'attribute_definition'}[typ],
                rawText=raw, plainText=e.plain_text(), anchor=anchor, frameId=fr,
                associatedOccurrenceIds=[], interpretation=None, validation=state()))
            if typ == 'ATTDEF':
                self.diag('ATTRIBUTE_DEFINITION_ONLY', 'ATTDEF is a default definition, not a confirmed instance value.', 'info', [dict(kind='occurrence', id=oid)])
        if typ in ('DIMENSION', 'ARC_DIMENSION'):
            self.dimension(e, eid, oid, fr, space, parent)
        if typ == 'VIEWPORT':
            self.viewport(e, eid, space)
        if typ == 'INSERT':
            self.expand(e, eid, oid, space, parent, instance_path, effective_layer, lt, visible)

    def space_kind(self, id):
        return next(s['kind'] for s in self.package['spaces'] if s['id'] == id)

    def expand(self, e, eid, oid, space, parent, path, layer, lt, visible):
        name = e.dxf.name
        block_key=next((k for k in self.blocks if k.casefold()==name.casefold()),None)
        if block_key is None:
            self.diag('BLOCK_MISSING', 'Block definition not found: ' + name, targets=[dict(kind='occurrence', id=oid)])
            return
        definition, bf, block = self.blocks[block_key]
        if int(block.block.dxf.flags) & 12:
            self.diag('XREF_NOT_RESOLVED', 'External block not fetched: ' + name, targets=[dict(kind='occurrence', id=oid)])
            return
        ancestors = {i['definitionId'] for i in self.package['blockInstances'] if i['id'] in path}
        if definition in ancestors or len(path) >= self.options.max_depth:
            self.diag('BLOCK_RECURSION_OR_DEPTH_LIMIT', 'Block expansion stopped with incomplete coverage.', targets=[dict(kind='occurrence', id=oid)])
            return
        rows, cols = int(e.dxf.row_count), int(e.dxf.column_count)
        if rows < 1 or cols < 1:
            self.diag('INVALID_ARRAY_COUNT', 'Invalid MINSERT cell count.', targets=[dict(kind='occurrence', id=oid)])
            return
        seen = set()
        for r in range(rows):
            for c in range(cols):
                if self.limit_reported:
                    return
                if len(self.package['blockInstances']) >= self.options.max_occurrences:
                    self.diag('INSTANCE_LIMIT_REACHED', 'Partial extraction: block instance limit reached.')
                    self.limit_reported = True
                    return
                clone = e.copy()
                delta = Vec3(c*e.dxf.column_spacing, r*e.dxf.row_spacing, 0).rotate_deg(e.dxf.rotation)
                if tuple(delta) in seen:
                    self.diag('COINCIDENT_ARRAY_CELLS', 'Coincident cells preserved as distinct occurrences, not physical quantity.')
                seen.add(tuple(delta))
                clone.dxf.insert = e.dxf.insert + delta
                local = from_native(clone.matrix44())
                if determinant(local) == 0:
                    self.diag('SINGULAR_BLOCK_TRANSFORM', 'Block scale is singular; no canonical geometry.', targets=[dict(kind='occurrence', id=oid)])
                    continue
                iid = self.id('instance', eid, space, path, r, c)
                # Parent frame is the entity's containing coordinate system.
                containing = self.rawframes[eid]
                tid = self.transform_record(iid, bf, containing, local, 'block_instance')
                self.package['blockInstances'].append(dict(id=iid, insertEntityId=eid, definitionId=definition,
                    parentInstanceId=path[-1] if path else None, spaceId=space, row=r, column=c,
                    insertPoint=vector(e.dxf.insert), scale=[e.dxf.xscale,e.dxf.yscale,e.dxf.zscale],
                    rotationRad=math.radians(e.dxf.rotation), extrusion=vector(e.dxf.extrusion),
                    rowSpacing=float(e.dxf.row_spacing), columnSpacing=float(e.dxf.column_spacing),
                    transformId=tid, validation=state()))
                world = mul(parent, local)
                for child in block:
                    self.emit(child, space, world, (*path, iid), layer, lt, visible)
                # Attached attributes are already placed in the parent space.
                attr_parent = identity()
                offset = e.ocs().to_wcs(delta)
                for i in range(3):
                    attr_parent[i][3] = offset[i]
                for attrib in e.attribs:
                    self.emit(attrib, space, mul(parent, attr_parent), (*path, iid), layer, lt, visible)

    def dimension(self, e, eid, oid, fr, space, parent):
        kinds = {0:'linear',1:'aligned',2:'angular',3:'diameter',4:'radius',5:'angular',6:'ordinate',8:'arc_length'}
        kind = kinds.get(e.dimtype, 'unknown')
        did = self.id('dimension', oid)
        style_name = e.dxf.get('dimstyle', 'Standard')
        styleid = self.style_ids.get(style_name)
        overrides, resolved = {}, {}
        try:
            override = e.override()
            overrides = plain(override.dimstyle_attribs)
            resolved = plain(self.doc.dimstyles.get(style_name).dxf.all_existing_dxf_attribs())
            resolved.update(overrides)
        except (ezdxf.DXFError, AttributeError, ValueError) as exc:
            self.diag('DIMSTYLE_UNRESOLVED', str(exc), targets=[dict(kind='entity', id=eid)])
        rawvalue = e.dxf.get('actual_measurement')
        rawq = quantity(float(rawvalue) if rawvalue is not None else None,
            'unknown' if kind == 'angular' else ('drawing_unit' if self.space_kind(space) == 'model' else 'paper_unit'))
        computed = quantity(reason='No trustworthy scalar measurement available')
        try:
            measurement = e.get_measurement()
            # Instance scaling of nominal/geometry dimensions is intentionally not inferred.
            if parent != identity():
                raise AdapterError('Dimension inside transformed block requires separate scale interpretation')
            if isinstance(measurement, (int, float)):
                if kind == 'angular':
                    computed = quantity(math.radians(float(measurement)), 'rad')
                elif self.space_factors[space] is not None:
                    computed = quantity(float(measurement)*self.space_factors[space], 'mm')
            else:
                self.diag('ORDINATE_VECTOR_PRESERVED', 'Ordinate measurement retained as vector evidence; scalar axis not inferred.', 'warning', [dict(kind='entity', id=eid)], {'rawMeasurementVector': vector(measurement)})
        except (AdapterError, ezdxf.DXFError, ValueError, TypeError, AttributeError, ZeroDivisionError) as exc:
            self.diag('DIMENSION_MEASUREMENT_UNRESOLVED', str(exc), 'warning', [dict(kind='entity', id=eid)])
        if kind == 'angular' and rawvalue is not None:
            self.diag('RAW_ANGLE_UNIT_UNRESOLVED', 'Raw group 42 is preserved without assuming its angular convention.', 'warning', [dict(kind='entity', id=eid)])
        points = [vector(e.dxf.get(key)) for key in ('defpoint','defpoint2','defpoint3','defpoint4','defpoint5') if e.dxf.hasattr(key)]
        toleranceids = []
        if resolved.get('dimtol') or resolved.get('dimlim'):
            tid = self.id('tolerance', oid)
            toleranceids = [tid]
            attrs = {k:v for k,v in resolved.items() if k in ('dimtol','dimlim','dimtp','dimtm','dimlfac','dimalt','dimtfac','dimtdec')}
            self.package['tolerances'].append(dict(id=tid, targetDimensionIds=[did], targetFeatureIds=[], kind='unknown',
                interpretation='unparsed', lower=None, upper=None, rawText=json.dumps(attrs,ensure_ascii=False),
                standardReference=None, datumAnnotationIds=[], validation=state('extracted','Style values retained; physical tolerance interpretation deferred')))
            self.diag('TOLERANCE_INTERPRETATION_PENDING', 'Tolerance style/overrides preserved without fabricating physical limits.', 'warning', [dict(kind='dimension', id=did)])
        self.package['dimensions'].append(dict(id=did, entityId=eid, occurrenceId=oid, kind=kind, styleId=styleid,
            rawMeasurement=rawq, computedMeasurement=computed, displayMeasurement=quantity(reason='Nominal display not resolved in Fase 2A'),
            rawText=e.dxf.get('text',''), displayText=None, rawOverrides=overrides, resolvedStyle=resolved,
            definitionPoints=points, pointFrameId=fr, associatedOccurrenceIds=[], toleranceIds=toleranceids, validation=state()))

    def viewport(self, e, eid, space):
        if self.space_kind(space) != 'paper':
            self.diag('VIEWPORT_IN_MODEL', 'VIEWPORT outside Paper Space preserved without mapping.', 'warning')
            return
        model = next(s['id'] for s in self.package['spaces'] if s['kind'] == 'model')
        vid = self.id('viewport', eid)
        self.package['viewports'].append(dict(id=vid, entityId=eid, modelSpaceId=model, paperFrameId=self.space_frames[space],
            viewCenter=vector(e.dxf.view_center_point), viewTarget=vector(e.dxf.view_target_point),
            viewDirection=vector(e.dxf.view_direction_vector), twistRad=math.radians(e.dxf.view_twist_angle),
            paperCenter=vector(e.dxf.center), paperHeight=quantity(float(e.dxf.height),'paper_unit'),
            modelViewHeight=quantity(float(e.dxf.view_height),'drawing_unit'),
            projection='perspective' if int(e.dxf.get('flags',0)) & 1 else 'orthographic',
            modelToPaperTransformId=None, projectionMatrix=None, clipBoundaryOccurrenceIds=[], validation=state()))
        next(s for s in self.package['spaces'] if s['id'] == space)['viewportIds'].append(vid)
        # Frozen contract 1.0 Target has no viewport discriminator: reference
        # its DXF entity, preserving the viewport ID in diagnostic details.
        self.diag('VIEWPORT_MAPPING_PENDING', 'Camera/layout preserved; clipping and projection mapping not implemented in Fase 2A.', 'warning', [dict(kind='entity', id=eid)], {'viewportId':vid})

    def run(self):
        for l in self.doc.layers:
            name = l.dxf.name
            lid = self.id('layer', name)
            self.layers[name] = lid
            self.package['layers'].append(dict(id=lid, name=name, color=plain(l.dxf.get('true_color', l.dxf.color)),
                linetype=l.dxf.linetype, lineweight=l.dxf.get('lineweight'), visible=not l.is_off(), frozen=l.is_frozen(),
                locked=l.is_locked(), plotEnabled=bool(l.dxf.get('plot', 1)), rawAttributes=plain(l.dxf.all_existing_dxf_attribs())))
        layouts = list(self.doc.layouts)
        layout_blocks = {l.block_record_name for l in layouts}
        for layout in layouts:
            sid = self.id('space', layout.name)
            model = layout.name == 'Model'
            fr = self.frame(layout.name, 'document_wcs' if model else 'paper','drawing_unit' if model else 'paper_unit',sid)
            paper_code = int(layout.dxf.get('plot_paper_units',2)) if not model else None
            paper_unit = {0:'inch',1:'mm'}.get(paper_code,'unknown')
            self.space_frames[sid] = fr
            self.space_factors[sid] = self.factor if model else {'inch':25.4,'mm':1.}.get(paper_unit)
            self.package['spaces'].append(dict(id=sid,kind='model' if model else 'paper',name=layout.name,
                frameId=fr,paperUnit='not_applicable' if model else paper_unit,viewportIds=[],validation=state()))
            if not model and self.space_factors[sid] is None:
                self.diag('PAPER_UNITS_UNRESOLVED', 'Paper units unknown; not replaced with Model units.', 'warning', [dict(kind='space',id=sid)])
        for style in self.doc.dimstyles:
            id = self.id('dimension-style',style.dxf.name)
            self.style_ids[style.dxf.name]=id
            self.package['dimensionStyles'].append(dict(id=id,name=style.dxf.name,rawAttributes=plain(style.dxf.all_existing_dxf_attribs()),validation=state()))
        for block in self.doc.blocks:
            if block.name in layout_blocks:
                continue
            bid = self.id('block',block.name)
            bf = self.frame('block:'+block.name,'block_definition','drawing_unit')
            self.blocks[block.name]=(bid,bf,block)
        for name,(bid,bf,block) in self.blocks.items():
            entities=[self.register(e,dict(kind='block_definition',id=bid),bf) for e in block]
            self.package['blockDefinitions'].append(dict(id=bid,name=name,basePoint=vector(block.block.dxf.base_point),
                frameId=bf,declaredInsunits=block.block_record.dxf.get('units'),entityIds=entities,
                externalReference=block.block.dxf.get('xref_path') or None,validation=state()))
        for layout in layouts:
            sid=self.id('space',layout.name)
            for e in layout:
                self.register(e,dict(kind='space',id=sid),self.space_frames[sid])
        # Missing table entries are retained as unknown layers, never inherited from an unrelated layer.
        recorded={x['id'] for x in self.package['layers']}
        for name,id in self.layers.items():
            if id not in recorded:
                self.package['layers'].append(dict(id=id,name=name,color=None,linetype=None,lineweight=None,visible=None,
                    frozen=None,locked=None,plotEnabled=None,rawAttributes={}))
                self.diag('LAYER_TABLE_ENTRY_MISSING','Layer referenced but absent from table: '+name,'warning')
        for layout in layouts:
            sid=self.id('space',layout.name)
            for e in layout:
                self.emit(e,sid,identity())
        # Definition-only geometries remain available even for unreferenced blocks.
        for eid,e in list(self.entities.items()):
            if e.dxftype() in ('LINE','ARC','CIRCLE','ELLIPSE','LWPOLYLINE','POLYLINE','POINT') and eid not in self.raw_gids:
                try:
                    self.geometry(eid,None,self.rawframes[eid],self.raw_geometry(e),'definition-only')
                except (AdapterError,ValueError,ezdxf.DXFError,ZeroDivisionError) as exc:
                    self.diag('DEFINITION_GEOMETRY_UNSUPPORTED',str(exc),'warning',[dict(kind='entity',id=eid)])
        for consumer in ('visualization','material','process','cost'):
            self.package['validation']['eligibility'].append(dict(scope=dict(kind='document',id=self.package['document']['id']),
                consumer=consumer,status='not_assessed' if consumer=='visualization' else 'blocked',
                blockingDiagnosticIds=[] if consumer=='visualization' else [d['id'] for d in self.package['diagnostics'] if consumer in d['blocksConsumers']],
                requiredDecisionIds=[],reason='Experimental extraction only; no physical recognition or operational integration.'))
        self.package['validation']['schemaStatus']='valid'
        validate_structure(self.package)
        return self.package


def extract(path, options=None):
    """Read once, preserve source bytes, return an extraction-only contract."""
    options = options or Options()
    path = Path(path)
    if path.suffix.lower() != '.dxf':
        raise AdapterError('Expected .dxf input')
    with path.open('rb') as source:
        data = source.read(options.max_bytes+1)
    if len(data) > options.max_bytes:
        raise AdapterError('Input size limit exceeded')
    if not data:
        raise AdapterError('Empty DXF input')
    return _Extraction(data,path.name,options).run()
