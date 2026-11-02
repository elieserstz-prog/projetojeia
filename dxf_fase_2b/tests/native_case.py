"""Actual FreeCAD/Part fixtures. Run EACH case in its own compatible process."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--freecad-lib',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,args.freecad_lib)
    import FreeCAD as A
    import Part
    from jeia_dxf_freecad.collector import collect_document
    from jeia_dxf_freecad.contract import metadata
    d=A.newDocument('NativeFixture');o=d.addObject('Part::Feature','TestShape')
    try:
        name=args.case
        if name in ('line','placement','nested_placement'):o.Shape=Part.makeLine(A.Vector(0,0,0),A.Vector(10,0,0))
        elif name=='arc':o.Shape=Part.Arc(A.Vector(5,0,0),A.Vector(0,5,0),A.Vector(-5,0,0)).toShape()
        elif name=='circle':o.Shape=Part.makeCircle(5)
        elif name=='ellipse':o.Shape=Part.Ellipse(A.Vector(0,0,0),5,3).toShape()
        elif name=='bspline':
            c=Part.BSplineCurve();c.interpolate([A.Vector(0,0,0),A.Vector(5,3,0),A.Vector(10,0,0)]);o.Shape=c.toShape()
        elif name=='disk':o.Shape=Part.Face(Part.Wire(Part.makeCircle(5)))
        elif name in ('box','limits'):o.Shape=Part.makeBox(10,20,30)
        elif name=='cylinder':o.Shape=Part.makeCylinder(5,10)
        elif name=='empty':d.removeObject(o.Name);o=None
        else:raise ValueError('Unknown native case')
        if name=='placement':o.Placement=A.Placement(A.Vector(10,20,30),A.Rotation())
        if name=='nested_placement':
            parent=d.addObject('App::Part','Parent');parent.addObject(o)
            parent.Placement=A.Placement(A.Vector(10,0,0),A.Rotation())
            o.Placement=A.Placement(A.Vector(0,20,0),A.Rotation())
        d.recompute()
        def snapshot(obj):
            if obj is None:return None
            # BREP text can change location-table ordering after a native copy;
            # preservation is tested on document geometry, not text ordering.
            s=obj.Shape;m=obj.Placement.toMatrix()
            return {'placement':[getattr(m,'A'+str(i)+str(j)) for i in range(1,5) for j in range(1,5)],
                'vertices':[(v.Point.x,v.Point.y,v.Point.z) for v in s.Vertexes],
                'curves':[(e.Length,e.FirstParameter,e.LastParameter,
                    tuple(e.valueAt((e.FirstParameter+e.LastParameter)/2)),str(e.Orientation)) for e in s.Edges],
                'areas':[f.Area for f in s.Faces],'volume':s.Volume}
        before=snapshot(o)
        object_names=[x.Name for x in d.Objects]
        raw=(b'999\nSYNTHETIC_KERNEL_CASE:'+name.encode('ascii')+
             b'\n0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n')
        result=collect_document(d,metadata(raw,'SYNTHETIC_KERNEL_'+name+'.dxf'),A,synthetic=True,
            max_edges=2 if name=='limits' else 20000,max_faces=2 if name=='limits' else 10000)
        assert snapshot(o)==before,'Original object geometry/placement changed'
        assert [x.Name for x in d.Objects]==object_names,'Document object membership changed'
        shapes=[e['value'] for e in result['evidence'] if 'rawObjectBrep' in e['value']]
        payloads=[g['payload'] for g in result['geometries']]
        if name=='empty':assert any(x['code']=='NO_NATIVE_GEOMETRY' for x in result['diagnostics'])
        else:
            assert shapes and shapes[0]['globalBrep'] and shapes[0]['rawObjectBrep']
            restored=Part.Shape();restored.importBrepFromString(shapes[0]['globalBrep'])
            assert restored.isValid(),'BREP round-trip invalid'
        if name=='line':assert any(g['type']=='LINE' and g['end']==[10,0,0] for g in payloads)
        if name=='circle':assert any(g['type']=='CIRCLE' and g['radius']==5 for g in payloads)
        if name=='arc':assert any(g['type']=='ARC' for g in payloads)
        if name=='ellipse':assert any(g['type']=='ELLIPSE' for g in payloads)
        if name=='bspline':assert any(g['type']=='BSPLINE' for g in payloads)
        if name=='box':
            g=next(g for g in payloads if g['type']=='BREP_SUMMARY');assert g['faces']==6 and g['edges']==12 and abs(g['volume']['value']-6000)<1e-8
            assert len(shapes[0]['faces'])==6 and all(w['edges'] for f in shapes[0]['faces'] for w in f['wires'])
        if name=='disk':assert len(shapes[0]['faces'])==1 and abs(shapes[0]['faces'][0]['areaMm2']-25*3.141592653589793)<1e-7
        if name=='cylinder':assert any(f['type']=='Cylinder' for f in shapes[0]['faces'])
        if name=='placement':assert any(g['type']=='LINE' and g['start']==[10,20,30] for g in payloads)
        if name=='nested_placement':assert any(g['type']=='LINE' and g['start']==[10,20,0] for g in payloads)
        if name=='limits':
            assert len(shapes[0]['edges'])==2 and len(shapes[0]['faces'])==2
            assert any(x['code']=='TOPOLOGY_RESOURCE_LIMIT' for x in result['diagnostics'])
        args.output.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2),encoding='utf-8')
        print('NATIVE CASE PASS:',name)
    finally:A.closeDocument(d.Name)


if __name__=='__main__':main()
