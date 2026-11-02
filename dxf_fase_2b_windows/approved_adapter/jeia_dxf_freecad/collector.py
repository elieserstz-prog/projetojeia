"""Collect real FreeCAD shapes without modifying objects or JEIA application code.

FreeCAD is supplied by the caller inside its compatible Python runtime.
Native surface/topology information and full BREP live in contract evidence,
because frozen contract 1.0 has no analytic face/surface payload variant.
"""
import math
from .contract import Packet, number, vec, quantity, state


class GeometryConflict(ValueError):
    """Native curve attributes and located edge observations disagree."""


def placement_rows(p):
    m=p.toMatrix()
    return [[number(getattr(m,'A'+str(i)+str(j))) for j in range(1,5)] for i in range(1,5)]


def safe_attrs(obj,names):
    result={}
    for name in names:
        try:
            value=getattr(obj,name)
            if hasattr(value,'x') and hasattr(value,'y') and hasattr(value,'z'):result[name]=vec(value)
            elif isinstance(value,(float,int)):result[name]=number(value)
            elif isinstance(value,(str,bool)):result[name]=value
        except (AttributeError,TypeError,ValueError,RuntimeError):
            continue
    return result


def curve_payload(edge):
    c=edge.Curve;typ=type(c).__name__
    first,last=number(edge.FirstParameter),number(edge.LastParameter)
    a,b=edge.valueAt(first),edge.valueAt(last)
    if typ in ('Line','LineSegment'):
        return dict(type='LINE',start=vec(a),end=vec(b))
    if typ=='Circle':
        center,normal=c.Center,c.Axis
        if (c.value(first)-a).Length>1e-7 or (c.value(last)-b).Length>1e-7:
            raise GeometryConflict('Curve attributes and edge placement disagree; BREP retained')
        if edge.isClosed() and abs(abs(last-first)-math.tau)<1e-7:
            return dict(type='CIRCLE',center=vec(center),normal=vec(normal),radius=number(c.Radius))
        if not 0<abs(last-first)<=math.tau+1e-9:raise ValueError('Unsupported circle parameter interval')
        x=c.value(0)-center;x.normalize()
        return dict(type='ARC',center=vec(center),normal=vec(normal),xAxis=vec(x),radius=number(c.Radius),
            startRad=first,sweepRad=last-first)
    if typ=='Ellipse':
        if (c.value(first)-a).Length>1e-7:raise GeometryConflict('Ellipse placement mismatch')
        return dict(type='ELLIPSE',center=vec(c.Center),majorAxis=vec(c.value(0)-c.Center),
            minorAxis=vec(c.value(math.pi/2)-c.Center),startRad=first,sweepRad=last-first)
    if typ=='BSplineCurve':
        # Payload preserves the exact support curve; the trimmed edge domain
        # and orientation are separately preserved in its evidence/BREP.
        weights=[number(v) for v in c.getWeights()] if c.isRational() else None
        return dict(type='BSPLINE',degree=int(c.Degree),controlPoints=[vec(p) for p in c.getPoles()],
            knots=[number(v) for v in c.getKnots()],multiplicities=[int(v) for v in c.getMultiplicities()],
            weights=weights,periodic=bool(c.isPeriodic()),closed=bool(c.isClosed()))
    raise ValueError('Curve '+typ+' has no implemented analytic serializer; exact BREP retained when available')


def surface_info(face):
    s=face.Surface
    return dict(type=type(s).__name__,attributes=safe_attrs(s,('Center','Position','Axis','Radius','MajorRadius',
        'MinorRadius','SemiAngle','DegreeU','DegreeV')),parameterRange=[number(v) for v in face.ParameterRange],
        areaMm2=number(face.Area),centerOfMass=vec(face.CenterOfMass),orientation=str(face.Orientation),
        valid=bool(face.isValid()))


def collect_document(doc,meta,app,*,request_id=None,generation=0,revision=1,synthetic=False,
                     max_edges=20000,max_faces=10000,max_brep_bytes=16*1024*1024):
    """Read only. No document recompute, shape fusion or application changes."""
    for value in (max_edges,max_faces,max_brep_bytes):
        if type(value) is not int or value<=0:raise ValueError('Invalid collector limit')
    packet=Packet(meta,request_id,generation,revision,synthetic)
    packet.native_source.update(version='.'.join(map(str,app.Version()[:3])),
        options={'shapeCoordinates':'FreeCAD internal mm','sourceUnitConversionVerified':False,
                 'maxEdges':max_edges,'maxFaces':max_faces,'maxBrepBytes':max_brep_bytes},
        capabilities=['native_BREP','edge_curves','face_topology','source_object_metadata'],validation=state())
    objects=list(doc.Objects)
    count=0
    for obj in objects:
        if not hasattr(obj,'Shape'):
            packet.diag('OBJECT_WITHOUT_SHAPE','Native object has no Shape.','warning',details={'object':obj.Name,'type':obj.TypeId})
            continue
        source_shape=obj.Shape
        if source_shape.isNull():
            packet.diag('NULL_NATIVE_SHAPE','Object Shape is null.','warning',details={'object':obj.Name})
            continue
        count+=1
        shape=source_shape.copy()
        original_placement=placement_rows(source_shape.Placement)
        global_known=False
        try:
            # Shape.Placement already includes object placement. Replace its
            # parent frame contribution; do not multiply object placement twice.
            own=obj.Placement;globalp=obj.getGlobalPlacement()
            shape.Placement=globalp.multiply(own.inverse()).multiply(source_shape.Placement)
            global_known=True
        except (AttributeError,RuntimeError,ValueError,TypeError) as exc:
            packet.diag('GLOBAL_PLACEMENT_UNAVAILABLE','Only native shape coordinates preserved: '+str(exc),
                details={'object':obj.Name})
        if not global_known:
            # A local shape must not be falsely labelled as document WCS.
            gid=packet.geometry(obj.Name+'.UnresolvedFrame',dict(type='UNSUPPORTED',originalType=str(shape.ShapeType),
                reason='Object-to-document frame unresolved; exact local BREP retained separately'),'unsupported')
            local_brep=None
            try:
                candidate=source_shape.exportBrepToString()
                if len(candidate.encode('utf-8'))<=max_brep_bytes:local_brep=candidate
                else:packet.diag('BREP_RESOURCE_LIMIT','Local BREP exceeds explicit limit.',geometry=gid)
            except (RuntimeError,ValueError,AttributeError,TypeError) as exc:
                packet.diag('BREP_EXPORT_FAILED',str(exc),geometry=gid)
            packet.evidence(obj.Name+'.UnresolvedFrame',gid,dict(objectName=obj.Name,objectType=obj.TypeId,
                originalShapePlacement=original_placement,localBrep=local_brep,coordinateFrameStatus='unresolved'),
                'Local source preserved without fabricating global coordinates.')
            continue
        key=obj.Name
        edges=list(shape.Edges);faces=list(shape.Faces);solids=list(shape.Solids);bb=shape.BoundBox
        summary=dict(type='BREP_SUMMARY',solids=len(solids),faces=len(faces),edges=len(edges),valid=bool(shape.isValid()),
            bboxMin=[number(bb.XMin),number(bb.YMin),number(bb.ZMin)],bboxMax=[number(bb.XMax),number(bb.YMax),number(bb.ZMax)],
            volume=quantity(shape.Volume,'mm3') if solids else None)
        summary_id=packet.geometry(key+'.Shape',summary,'summary')
        properties=safe_attrs(obj,('Name','Label','TypeId','DxfHandle','DXFHandle','DxfLayer','DXFLayer','DxfEntityType'))
        linked=[child.Name for child in getattr(obj,'OutList',[]) if hasattr(child,'Shape')]
        native=dict(objectName=obj.Name,objectType=obj.TypeId,properties=properties,
            originalShapePlacement=original_placement,exportedShapePlacement=placement_rows(shape.Placement),
            globalPlacementKnown=global_known,shapeType=str(shape.ShapeType),aggregateOnly=bool(linked),
            shapeChildren=linked,counts={'vertices':len(shape.Vertexes),'edges':len(edges),'faces':len(faces),'solids':len(solids)},
            vertices=[vec(v.Point) for v in shape.Vertexes],edges=[],faces=[],rawObjectBrep=None,globalBrep=None)
        construction=obj.TypeId in ('App::Origin','App::Line','App::Plane','PartDesign::Plane','PartDesign::Line','PartDesign::Point')
        native['constructionReference']=construction
        if construction:packet.diag('NATIVE_CONSTRUCTION_REFERENCE','Native origin/datum helper retained as reference, not physical part geometry.',
            'warning',summary_id,{'nativeType':obj.TypeId})
        if linked:packet.diag('CONTAINER_AND_CHILD_GEOMETRY','Parent and child observations retained; never sum them as physical quantity.',
            geometry=summary_id,details={'shapeChildren':linked})
        try:
            raw=source_shape.exportBrepToString();global_brep=shape.exportBrepToString()
            if len(raw.encode('utf-8'))+len(global_brep.encode('utf-8'))>max_brep_bytes:
                packet.diag('BREP_RESOURCE_LIMIT','Exact BREP omitted because explicit limit was exceeded; no truncation presented as complete.',geometry=summary_id)
            else:
                native.update(rawObjectBrep=raw,globalBrep=global_brep)
        except (RuntimeError,ValueError,AttributeError,TypeError) as exc:
            packet.diag('BREP_EXPORT_FAILED',str(exc),geometry=summary_id)
        if len(edges)>max_edges or len(faces)>max_faces:
            packet.diag('TOPOLOGY_RESOURCE_LIMIT','Partial edge/face listing; counts and BREP remain explicit.',geometry=summary_id)
        for index,edge in enumerate(edges[:max_edges],1):
            edge_key=key+'.Edge'+str(index)
            try:
                payload=curve_payload(edge)
                gid=packet.geometry(edge_key+'.Curve',payload)
            except (AttributeError,ValueError,RuntimeError,TypeError,ArithmeticError) as exc:
                gid=packet.geometry(edge_key+'.Curve',dict(type='UNSUPPORTED',originalType=type(edge.Curve).__name__,reason=str(exc)),'unsupported')
                if isinstance(exc,GeometryConflict):
                    diagnostic=packet.diag('NATIVE_GEOMETRY_CONFLICT',str(exc),geometry=gid)
                    packet.data['geometries'][-1]['validation']=state('conflicting',str(exc),[diagnostic])
                else:packet.diag('CURVE_NOT_SERIALIZED',str(exc),geometry=gid)
            detail=dict(index=index,geometryId=gid,orientation=str(edge.Orientation),
                firstParameter=number(edge.FirstParameter),lastParameter=number(edge.LastParameter),lengthMm=number(edge.Length),
                closed=bool(edge.isClosed()),start=vec(edge.valueAt(edge.FirstParameter)),end=vec(edge.valueAt(edge.LastParameter)))
            native['edges'].append(detail)
            packet.evidence(edge_key,gid,detail,'Native edge domain, endpoints and orientation; analytic payload does not discard BREP topology.')
            if packet.data['geometries'][-1]['payload']['type']=='BSPLINE':
                packet.diag('BSPLINE_SUPPORT_AND_TRIM_SEPARATE','BSPLINE payload is support curve; edge trim domain is in evidence.','warning',gid)
        for index,face in enumerate(faces[:max_faces],1):
            try:
                detail=surface_info(face);detail['index']=index;detail['wires']=[]
                for wire in face.Wires:
                    refs=[]
                    for edge in wire.Edges:
                        matched=next((i for i,known in enumerate(edges,1) if edge.isSame(known)),None)
                        refs.append({'edgeIndex':matched,'orientation':str(edge.Orientation)})
                    detail['wires'].append({'closed':bool(wire.isClosed()),'edges':refs})
            except (AttributeError,ValueError,RuntimeError,TypeError,ArithmeticError) as exc:
                detail={'index':index,'surfaceMetadataUnavailable':str(exc)}
                packet.diag('FACE_METADATA_UNAVAILABLE','Face BREP retained, but metadata extraction failed: '+str(exc),geometry=summary_id)
            native['faces'].append(detail)
        packet.evidence(key+'.Topology',summary_id,native,
            'Exact original/global BREP plus native objects, vertices, edges, trimmed faces and adjacency; no DXF entity association fabricated.')
        packet.diag('FACE_SCHEMA_REPRESENTATION','Frozen 1.0 schema has no analytic face payload; exact BREP and face metadata retained in evidence.',
            'info',summary_id)
    if not count:packet.diag('NO_NATIVE_GEOMETRY','No non-null shapes collected; empty observations are not successful geometric recognition.')
    return packet.finish()
