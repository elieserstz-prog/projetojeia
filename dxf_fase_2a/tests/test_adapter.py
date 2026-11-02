"""Real ezdxf + schema regressions, with synthetic DXF files in temporary folders."""
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import ezdxf
from ezdxf.math import Vec3
from jsonschema import ValidationError
from jeia_dxf_tech import AdapterError, Options, extract, validate_structure
from jeia_dxf_tech.adapter import apply, from_native, to_native


ROOT=Path(__file__).resolve().parents[1]


def geometries(r,typ=None):
    return [g for g in r['geometries'] if g['occurrenceId'] and (typ is None or g['payload']['type']==typ)]


def codes(r):return {d['code'] for d in r['diagnostics']}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'teste.dxf'
        self.d=ezdxf.new('R2010');self.d.units=4
        self.m=self.d.modelspace()

    def tearDown(self):self.temp.cleanup()

    def read(self,options=None):
        self.d.saveas(self.path)
        before=self.path.read_bytes()
        r=extract(self.path,options)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(r['document']['sha256'],sha256(before).hexdigest())
        self.assertEqual(r['document']['byteLength'],len(before))
        validate_structure(r)
        self.assertFalse(r['validation']['cncReleased'])
        self.assertEqual(r['validation']['semanticStatus'],'not_checked')
        self.assertTrue(all(e['status']=='blocked' for e in r['validation']['eligibility'] if e['consumer']!='visualization'))
        self.assertEqual(r['features'],[]);self.assertEqual(r['operations'],[])
        return r

    def test_line_coordinates(self):
        self.m.add_line((1,2,3),(11,2,3));r=self.read();p=geometries(r,'LINE')[0]['payload']
        self.assertEqual(p['start'],[1,2,3]);self.assertEqual(p['end'],[11,2,3])

    def test_arc_crossing_zero(self):
        self.m.add_arc((0,0),5,350,10);p=geometries(self.read(),'ARC')[0]['payload']
        self.assertAlmostEqual(p['sweepRad'],math.radians(20));self.assertEqual(p['radius'],5)

    def test_circle_ocs(self):
        self.m.add_circle((2,3,4),1,dxfattribs={'extrusion':(0,1,0)})
        p=geometries(self.read(),'CIRCLE')[0]['payload']
        self.assertEqual(p['center'],[-2,4,3]);self.assertEqual(p['normal'],[0,1,0])

    def test_inches(self):
        self.d.units=1;self.m.add_line((0,0),(10,0));r=self.read()
        self.assertEqual(geometries(r,'LINE')[0]['payload']['end'][0],254)

    def test_kilometers(self):
        self.d.units=7;self.m.add_line((0,0),(1,0))
        self.assertEqual(geometries(self.read(),'LINE')[0]['payload']['end'][0],1000000)

    def test_unitless(self):
        self.d.units=0;self.m.add_line((0,0),(10,0));r=self.read()
        self.assertIn('UNITS_UNRESOLVED',codes(r));self.assertIsNone(r['document']['units']['mmPerDrawingUnit'])
        self.assertTrue(all(o['canonicalGeometryId'] is None for o in r['occurrences']))
        self.assertTrue(any(g['payload']['type']=='LINE' for g in r['geometries']))

    def test_astronomical_units_blocked(self):
        self.d.units=18;self.m.add_circle((0,0),1);r=self.read()
        self.assertIn('UNITS_UNRESOLVED',codes(r));self.assertEqual(geometries(r),[])

    def test_sparse_bulge_attaches_to_correct_vertex(self):
        self.m.add_lwpolyline([(0,0,0),(10,0,1),(10,10,0)],format='xyb');r=self.read()
        self.assertEqual(len(geometries(r,'LINE')),1);self.assertEqual(len(geometries(r,'ARC')),1)
        p=geometries(r,'ARC')[0]['payload'];self.assertEqual(p['radius'],5)
        self.assertAlmostEqual(p['center'][0],10);self.assertAlmostEqual(p['center'][1],5)

    def test_negative_bulge_orientation(self):
        self.m.add_lwpolyline([(0,0,-1),(10,0,0)],format='xyb');r=self.read()
        p=geometries(r,'COMPOSITE_CURVE')[0]['payload']
        self.assertTrue(p['segments'][0]['reversed'])

    def test_closed_curved_wire(self):
        self.m.add_lwpolyline([(0,0,1),(10,0,1)],format='xyb',close=True);r=self.read()
        self.assertTrue(geometries(r,'COMPOSITE_CURVE')[0]['payload']['closed'])
        self.assertEqual(len(geometries(r,'ARC')),2)

    def test_major_bulge(self):
        self.m.add_lwpolyline([(0,0,2),(10,0,0)],format='xyb');r=self.read()
        self.assertGreater(geometries(r,'ARC')[0]['payload']['sweepRad'],math.pi)

    def test_polyline_elevation_once(self):
        self.m.add_lwpolyline([(0,0),(10,0)],dxfattribs={'elevation':4,'extrusion':(0,1,0)})
        p=geometries(self.read(),'LINE')[0]['payload']
        self.assertEqual(p['start'],[0,4,0]);self.assertEqual(p['end'],[-10,4,0])

    def test_classic_polyline_preserves_vertex_handles(self):
        self.m.add_polyline2d([(0,0),(10,0),(10,10)],close=True);r=self.read()
        self.assertEqual(sum(e['dxfType']=='VERTEX' for e in r['entities']),3)
        self.assertEqual(len(geometries(r,'LINE')),3)

    def test_polyline3d_preserves_z(self):
        self.m.add_polyline3d([(0,0,1),(1,2,3)]);r=self.read()
        self.assertEqual(geometries(r,'LINE')[0]['payload']['end'],[1,2,3])

    def test_model_and_paper_separate(self):
        self.m.add_line((0,0),(10,0));paper=self.d.layouts.new('FOLHA');paper.dxf.plot_paper_units=1
        paper.add_line((1000,1000),(1100,1000));r=self.read()
        spaces={s['id']:s['kind'] for s in r['spaces']}
        self.assertEqual({spaces[o['spaceId']] for o in r['occurrences']},{'model','paper'})
        self.assertEqual(r['views'],[])

    def test_paper_does_not_inherit_model_inches(self):
        self.d.units=1;p=self.d.layouts.new('MM');p.dxf.plot_paper_units=1;p.add_line((0,0),(10,0))
        r=self.read();self.assertEqual(geometries(r,'LINE')[0]['payload']['end'][0],10)

    def test_title_text_and_attributes(self):
        b=self.d.blocks.new('CARIMBO');b.add_attdef('REV',(2,3),text='00')
        self.m.add_blockref('CARIMBO',(100,200)).add_auto_attribs({'REV':'01'});r=self.read()
        vals=[a for a in r['annotations'] if a['kind']=='attribute'];self.assertEqual(len(vals),1)
        self.assertEqual(vals[0]['rawText'],'01');self.assertEqual(vals[0]['anchor'],[102,203,0])
        e=next(e for e in r['entities'] if e['id']==vals[0]['entityId']);self.assertEqual(e['owner']['kind'],'entity')
        self.assertTrue(all(c['inclusion']=='pending' for c in r['classifications']))

    def test_layer_zero_and_byblock_inheritance(self):
        self.d.layers.new('PECA',dxfattribs={'linetype':'DASHED'});b=self.d.blocks.new('B')
        b.add_line((0,0),(1,0),dxfattribs={'layer':'0','linetype':'BYBLOCK'})
        self.m.add_blockref('B',(0,0),dxfattribs={'layer':'PECA','linetype':'CENTER'});r=self.read()
        e=next(e for e in r['entities'] if e['dxfType']=='LINE');o=next(o for o in r['occurrences'] if o['entityId']==e['id'])
        self.assertNotEqual(e['layerId'],o['effectiveLayerId']);self.assertEqual(o['effectiveLinetype'],'CENTER')

    def test_frozen_layer_visibility(self):
        l=self.d.layers.new('MOLDURA');l.freeze();self.m.add_circle((0,0),5,dxfattribs={'layer':'MOLDURA'})
        r=self.read();self.assertFalse(r['occurrences'][0]['effectiveVisible'])
        self.assertEqual(r['classifications'][0]['inclusion'],'pending')

    def test_nonuniform_rotated_block(self):
        b=self.d.blocks.new('B',base_point=(1,0));b.add_circle((0,0),1)
        self.m.add_blockref('B',(10,20),dxfattribs={'xscale':2,'yscale':1,'rotation':90});r=self.read()
        p=geometries(r,'ELLIPSE')[0]['payload'];self.assertAlmostEqual(p['center'][0],10);self.assertAlmostEqual(p['center'][1],18)
        self.assertAlmostEqual(Vec3(p['majorAxis']).magnitude,2);self.assertAlmostEqual(Vec3(p['minorAxis']).magnitude,1)

    def test_nonuniform_bulge_converts_to_ellipse(self):
        b=self.d.blocks.new('B');b.add_lwpolyline([(0,0,1),(10,0,0)],format='xyb')
        self.m.add_blockref('B',(0,0),dxfattribs={'xscale':2,'yscale':1})
        r=self.read();self.assertEqual(len(geometries(r,'ELLIPSE')),1);self.assertEqual(len(geometries(r,'ARC')),0)

    def test_mirrored_arc_endpoints(self):
        b=self.d.blocks.new('B');b.add_arc((0,0),5,0,90)
        self.m.add_blockref('B',(0,0),dxfattribs={'xscale':-1});r=self.read();p=geometries(r,'ARC')[0]['payload']
        n=Vec3(p['normal']);x=Vec3(p['xAxis']);y=n.cross(x);center=Vec3(p['center'])
        start=center+p['radius']*(x*math.cos(p['startRad'])+y*math.sin(p['startRad']))
        self.assertLess((start-Vec3(-5,0,0)).magnitude,1e-8)

    def test_minsert_grid_not_scaled(self):
        b=self.d.blocks.new('B',base_point=(1,0));b.add_circle((0,0),1)
        self.m.add_blockref('B',(10,20),dxfattribs={'xscale':2,'yscale':1,'rotation':90}).grid(size=(1,2),spacing=(0,5))
        r=self.read();p=geometries(r,'ELLIPSE');self.assertEqual(len(p),2)
        self.assertAlmostEqual(p[1]['payload']['center'][1]-p[0]['payload']['center'][1],5)
        self.assertNotEqual(p[0]['occurrenceId'],p[1]['occurrenceId'])

    def test_coincident_cells_preserved(self):
        b=self.d.blocks.new('B');b.add_circle((0,0),1)
        e=self.m.add_blockref('B',(0,0));e.dxf.column_count=2;e.dxf.column_spacing=0
        r=self.read();self.assertEqual(len(geometries(r,'CIRCLE')),2);self.assertIn('COINCIDENT_ARRAY_CELLS',codes(r))

    def test_nested_blocks(self):
        b=self.d.blocks.new('B');b.add_line((1,0),(2,0));a=self.d.blocks.new('A')
        a.add_blockref('B',(10,0),dxfattribs={'xscale':2,'yscale':2})
        self.m.add_blockref('A',(100,0));r=self.read();p=geometries(r,'LINE')[0]
        self.assertEqual(p['payload']['start'],[112,0,0]);self.assertEqual(len(next(o for o in r['occurrences'] if o['id']==p['occurrenceId'])['instancePath']),2)

    def test_cycle_is_diagnosed(self):
        a=self.d.blocks.new('A');a.add_blockref('A',(0,0));self.m.add_blockref('A',(0,0));r=self.read()
        self.assertIn('BLOCK_RECURSION_OR_DEPTH_LIMIT',codes(r))

    def test_missing_block(self):
        self.m.add_blockref('MISSING',(0,0));self.assertIn('BLOCK_MISSING',codes(self.read()))

    def test_dimension_computed_without_group42(self):
        e=self.m.add_linear_dim(base=(0,-5),p1=(0,0),p2=(80,0)).dimension
        e.dxf.discard('actual_measurement');r=self.read();dim=r['dimensions'][0]
        self.assertIsNone(dim['rawMeasurement']['value']);self.assertEqual(dim['computedMeasurement']['value'],80)
        self.assertIsNone(dim['displayMeasurement']['value'])

    def test_dimension_style_override_preserved(self):
        self.m.add_linear_dim(base=(0,-5),p1=(0,0),p2=(10,0),override={'dimlfac':2,'dimtol':1,'dimtp':0.1,'dimtm':0.05}).render()
        r=self.read();dim=r['dimensions'][0];self.assertEqual(dim['computedMeasurement']['value'],10)
        self.assertEqual(dim['resolvedStyle']['dimlfac'],2);self.assertEqual(len(r['tolerances']),1)
        self.assertIsNone(r['tolerances'][0]['upper'])

    def test_dimensions_inside_blocks_preserved(self):
        b=self.d.blocks.new('B');b.add_linear_dim(base=(0,-2),p1=(0,0),p2=(10,0))
        self.m.add_blockref('B',(100,0));r=self.read();self.assertEqual(len(r['dimensions']),1)
        self.assertIsNone(r['dimensions'][0]['computedMeasurement']['value'])
        self.assertIn('DIMENSION_MEASUREMENT_UNRESOLVED',codes(r))

    def test_paper_dimension_preserved(self):
        p=self.d.layouts.new('FOLHA');p.dxf.plot_paper_units=1;p.add_linear_dim(base=(0,-2),p1=(0,0),p2=(50,0))
        r=self.read();self.assertEqual(r['dimensions'][0]['computedMeasurement']['value'],50)

    def test_501_dimensions_not_truncated(self):
        for i in range(501):self.m.add_linear_dim(base=(0,-2),p1=(0,0),p2=(i+1,0))
        self.assertEqual(len(self.read()['dimensions']),501)

    def test_viewport_camera_retained_without_mapping(self):
        p=self.d.layouts.new('FOLHA');p.dxf.plot_paper_units=1
        p.add_viewport(center=(100,100),size=(80,60),view_center_point=(20,30),view_height=200)
        r=self.read();v=r['viewports'][0];self.assertEqual(v['viewCenter'],[20,30,0])
        self.assertEqual(v['paperHeight']['value'],60);self.assertIsNone(v['modelToPaperTransformId'])
        self.assertIn('VIEWPORT_MAPPING_PENDING',codes(r))

    def test_unsupported_spline_is_explicit(self):
        self.m.add_spline([(0,0),(1,2),(2,0)]);r=self.read()
        self.assertIn('GEOMETRY_UNSUPPORTED',codes(r));self.assertTrue(any(g['payload']['type']=='UNSUPPORTED' for g in r['geometries']))

    def test_raw_groups_keep_spaces_and_codes(self):
        self.m.add_text('  material: aço  ');r=self.read();e=next(e for e in r['entities'] if e['dxfType']=='TEXT')
        self.assertTrue(any(t['code']==1 and t['rawValue']=='  material: aço  ' for t in e['rawGroups']))

    def test_legacy_encoding(self):
        self.d=ezdxf.new('R2000');self.d.units=4;self.d.modelspace().add_text('revisão ç')
        r=self.read();self.assertIn('revisão ç',[a['rawText'] for a in r['annotations']])

    def test_identity_stable_across_requests(self):
        self.m.add_circle((0,0),5);self.d.saveas(self.path)
        a=extract(self.path,Options(request_id='request-a'));b=extract(self.path,Options(request_id='request-b',selection_generation=2))
        self.assertEqual(a['entities'],b['entities']);self.assertEqual(a['occurrences'],b['occurrences'])
        self.assertNotEqual(a['context']['requestId'],b['context']['requestId'])

    def test_same_name_different_bytes_different_identity(self):
        self.m.add_line((0,0),(1,0));a=self.read();self.m.add_circle((0,0),2);b=self.read()
        self.assertNotEqual(a['document']['sha256'],b['document']['sha256']);self.assertNotEqual(a['entities'][0]['id'],b['entities'][0]['id'])

    def test_no_freecad_observations_fabricated(self):
        self.m.add_circle((0,0),5);r=self.read()
        self.assertFalse(any(s['kind']=='freecad' for s in r['sources']));self.assertEqual(r['reconciliations'],[])
        self.assertIn('FREECAD_NOT_RUN',codes(r))

    def test_occurrence_limit_is_explicit(self):
        for i in range(5):self.m.add_line((i,0),(i,1))
        r=self.read(Options(max_occurrences=2));self.assertEqual(len(r['occurrences']),2)
        self.assertIn('OCCURRENCE_LIMIT_REACHED',codes(r))

    def test_depth_limit_is_explicit(self):
        a=self.d.blocks.new('A');b=self.d.blocks.new('B');b.add_line((0,0),(1,0));a.add_blockref('B',(0,0));self.m.add_blockref('A',(0,0))
        self.assertIn('BLOCK_RECURSION_OR_DEPTH_LIMIT',codes(self.read(Options(max_depth=1))))

    def test_entity_limit_fails(self):
        self.m.add_line((0,0),(1,0));self.d.saveas(self.path)
        with self.assertRaisesRegex(AdapterError,'Entity resource limit'):extract(self.path,Options(max_entities=1))

    def test_size_limit_fails(self):
        self.m.add_line((0,0),(1,0));self.d.saveas(self.path)
        with self.assertRaisesRegex(AdapterError,'size limit'):extract(self.path,Options(max_bytes=10))

    def test_binary_dxf_rejected(self):
        self.path.write_bytes(b'AutoCAD Binary DXF\r\n\x1a\0')
        with self.assertRaisesRegex(AdapterError,'Binary DXF'):extract(self.path)

    def test_invalid_and_empty_inputs(self):
        for raw in (b'',b'not a dxf',b'0\nSECTION\n2\nENTITIES\n0\nENDSEC\n'):
            self.path.write_bytes(raw)
            with self.assertRaises(AdapterError):extract(self.path)

    def test_duplicate_handles_rejected(self):
        e1=self.m.add_line((0,0),(1,0));e2=self.m.add_line((0,1),(1,1));self.d.saveas(self.path)
        rows=self.path.read_text().splitlines()
        for i in range(0,len(rows)-1,2):
            if rows[i].strip()=='5' and rows[i+1].strip()==e2.dxf.handle:rows[i+1]=e1.dxf.handle
        self.path.write_text('\n'.join(rows)+'\n')
        with self.assertRaisesRegex(AdapterError,'Duplicate source handle'):extract(self.path)

    def test_degenerate_line_is_diagnosed(self):
        self.m.add_line((0,0),(0,0));self.assertIn('GEOMETRY_UNSUPPORTED',codes(self.read()))

    def test_schema_required_generation(self):
        self.m.add_line((0,0),(1,0));r=self.read();del r['context']['selectionGeneration']
        with self.assertRaises(ValidationError):validate_structure(r)

    def test_schema_unknown_field_rejected(self):
        self.m.add_line((0,0),(1,0));r=self.read();r['unapprovedIntegration']=True
        with self.assertRaises(ValidationError):validate_structure(r)

    def test_invalid_options(self):
        for kwargs in [{'selection_generation':-1},{'selection_generation':True},{'max_depth':0},{'request_id':'has spaces'},{'request_id':42}]:
            with self.assertRaises(AdapterError):Options(**kwargs)

    def test_matrix_convention_roundtrip(self):
        from ezdxf.math import Matrix44
        m=Matrix44.chain(Matrix44.scale(2,1,1),Matrix44.z_rotate(math.pi/2),Matrix44.translate(10,20,0))
        a=from_native(m);p=Vec3(1,2,3)
        self.assertLess((apply(a,p)-m.transform(p)).magnitude,1e-9)
        self.assertLess((to_native(a).transform(p)-m.transform(p)).magnitude,1e-9)

    def test_raw_record_type_matches_entity(self):
        b=self.d.blocks.new('B');b.add_line((0,0),(1,0));self.m.add_blockref('B',(0,0))
        self.m.add_polyline2d([(0,0),(2,0)])
        r=self.read()
        for e in r['entities']:
            self.assertEqual(next(t['rawValue'].strip() for t in e['rawGroups'] if t['code']==0),e['dxfType'])

    def test_block_name_case_insensitive(self):
        b=self.d.blocks.new('BLOCK');b.add_line((0,0),(1,0));self.m.add_blockref('block',(0,0))
        self.assertEqual(len(geometries(self.read(),'LINE')),1)

    def test_widths_and_thickness_not_silently_dropped(self):
        self.m.add_lwpolyline([(0,0),(10,0)],dxfattribs={'const_width':2,'thickness':3})
        r=self.read();self.assertIn('POLYLINE_WIDTH_NOT_MODELED',codes(r));self.assertIn('THICKNESS_NOT_MODELED',codes(r))
        raw=next(g for g in r['geometries'] if g['payload']['type']=='POLYLINE')['payload']
        self.assertEqual(raw['vertices'][0]['startWidth'],2)

    def test_degenerate_polyline_not_given_guessed_orientation(self):
        self.m.add_lwpolyline([(0,0),(0,0),(10,0)]);r=self.read()
        self.assertIn('GEOMETRY_UNSUPPORTED',codes(r));self.assertEqual(geometries(r,'COMPOSITE_CURVE'),[])

    def test_decoded_numeric_groups_preserve_original_text(self):
        self.m.add_line((1.25,0),(2.5,0));r=self.read();e=r['entities'][0]
        tag=next(t for t in e['rawGroups'] if t['code']==10)
        self.assertEqual(tag['decodedValue'],1.25);self.assertIsInstance(tag['rawValue'],str)

    def test_parent_visibility_propagates(self):
        self.d.layers.new('HIDDEN_PARENT').off();b=self.d.blocks.new('B');b.add_line((0,0),(1,0))
        self.m.add_blockref('B',(0,0),dxfattribs={'layer':'HIDDEN_PARENT'})
        r=self.read();self.assertTrue(all(o['effectiveVisible'] is False for o in r['occurrences']))

    def test_ids_and_basic_references(self):
        b=self.d.blocks.new('B');b.add_circle((0,0),5);self.m.add_blockref('B',(10,20))
        r=self.read();ids=[]
        for k,value in r.items():
            if isinstance(value,list):ids.extend(v['id'] for v in value if isinstance(v,dict) and 'id' in v)
        self.assertEqual(len(ids),len(set(ids)));registry=set(ids)|{r['document']['id']}
        for o in r['occurrences']:
            for k in ('entityId','spaceId','transformToSpaceId','effectiveLayerId'):self.assertIn(o[k],registry)
            if o['canonicalGeometryId']:self.assertIn(o['canonicalGeometryId'],registry)
        for t in r['transforms']:self.assertIn(t['fromFrameId'],registry);self.assertIn(t['toFrameId'],registry)

    def test_examples_are_extracted(self):
        paths=list((ROOT/'examples').glob('*.dxf'));self.assertEqual(len(paths),4)
        for p in paths:
            before=p.read_bytes();r=extract(p);validate_structure(r);self.assertEqual(before,p.read_bytes())

    def test_cli_json_and_no_overwrite(self):
        self.m.add_line((0,0),(1,0));self.d.saveas(self.path);output=Path(self.temp.name)/'out.json'
        cmd=[sys.executable,'-m','jeia_dxf_tech',str(self.path),'--output',str(output)]
        env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'}
        r=subprocess.run(cmd,capture_output=True,text=True,env=env);self.assertEqual(r.returncode,0,r.stderr)
        validate_structure(json.loads(output.read_text(encoding='utf-8')));before=output.read_bytes()
        r=subprocess.run(cmd,capture_output=True,text=True,env=env);self.assertEqual(r.returncode,2);self.assertEqual(output.read_bytes(),before)

    def test_cli_input_cannot_be_output(self):
        self.m.add_line((0,0),(1,0));self.d.saveas(self.path);before=self.path.read_bytes()
        env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'}
        r=subprocess.run([sys.executable,'-m','jeia_dxf_tech',str(self.path),'--output',str(self.path)],env=env,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertEqual(self.path.read_bytes(),before)


if __name__=='__main__':unittest.main(verbosity=2)
