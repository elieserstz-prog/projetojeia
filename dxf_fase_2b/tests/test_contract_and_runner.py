"""Unit/robustness tests. Native-process successes here are explicitly simulated."""
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from jeia_dxf_freecad import Options,extract,succeeded
from jeia_dxf_freecad.contract import Packet,metadata,number,state

ROOT=Path(__file__).resolve().parents[1]
DATA=b'0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1027\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nEOF\n'
SCHEMA=json.loads((ROOT/'jeia_dxf_freecad/schema.json').read_text())
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'input.dxf';self.path.write_bytes(DATA)
    def tearDown(self):self.temp.cleanup()
    def checked(self,r):
        VALIDATOR.validate(r);self.assertFalse(r['validation']['cncReleased'])
        self.assertEqual(r['validation']['semanticStatus'],'not_checked')
        self.assertTrue(all(x['status']=='blocked' for x in r['validation']['eligibility'] if x['consumer']!='visualization'))
        self.assertEqual(self.path.read_bytes(),DATA)
        return r
    def packet(self):return Packet(metadata(DATA,'input.dxf'),request_id='req-test',generation=3,revision=1)
    def simulated(self,mutation=None,exitcode=0):
        def run(cmd,**kwargs):
            env=kwargs['env'];req=json.loads(Path(env['JEIA_DXF2B_REQUEST']).read_text())
            snapshot=Path(req['input']);self.assertEqual(snapshot.read_bytes(),DATA);self.assertNotEqual(snapshot,self.path)
            p=Packet(metadata(snapshot.read_bytes(),snapshot.name),req['requestId'],req['generation'],req['revision'])
            p.geometry('Simulated.Edge1',{'type':'LINE','start':[0,0,0],'end':[1,0,0]})
            r=p.finish()
            if mutation:mutation(r,req,env)
            if exitcode==0:Path(env['JEIA_DXF2B_RESPONSE']).write_text(json.dumps(r))
            return SimpleNamespace(returncode=exitcode)
        return run
    def options(self,**kwargs):return Options(api_python=sys.executable,**kwargs)

    def test_schema_meta(self):Draft202012Validator.check_schema(SCHEMA)
    def test_metadata_hash(self):
        m=metadata(DATA,'input.dxf');self.assertEqual(m['sha256'],sha256(DATA).hexdigest());self.assertEqual(m['byteLength'],len(DATA))
    def test_metadata_mm(self):self.assertEqual(metadata(DATA,'x')['units']['mmPerDrawingUnit'],1)
    def test_unknown_units_no_fallback(self):
        d=DATA.replace(b'70\n4',b'70\n0');self.assertIsNone(metadata(d,'x')['units']['mmPerDrawingUnit'])
    def test_inch_header_not_applied_to_native_geometry(self):
        m=metadata(DATA.replace(b'70\n4',b'70\n1'),'x');p=Packet(m)
        p.geometry('Obj.Edge1',{'type':'LINE','start':[0,0,0],'end':[10,0,0]});r=p.finish()
        self.assertEqual(r['geometries'][0]['payload']['end'][0],10);self.assertEqual(m['units']['mmPerDrawingUnit'],25.4)
    def test_sources_do_not_fabricate_ezdxf(self):
        r=self.checked(self.packet().finish());self.assertFalse(any(s['kind']=='ezdxf' for s in r['sources']))
    def test_unmatched_geometry(self):
        p=self.packet();p.geometry('Obj.Edge1',{'type':'LINE','start':[0,0,0],'end':[1,0,0]});r=self.checked(p.finish())
        self.assertIsNone(r['geometries'][0]['entityId']);self.assertIsNone(r['geometries'][0]['occurrenceId'])
        self.assertEqual(r['entities'],[]);self.assertEqual(r['features'],[]);self.assertEqual(r['operations'],[])
    def test_synthetic_fixture_blocked(self):
        p=Packet(metadata(DATA,'fixture.dxf'),synthetic=True);r=self.checked(p.finish())
        self.assertIn('SYNTHETIC_DATA',{d['code'] for d in r['diagnostics']})
    def test_missing_executable(self):
        r=self.checked(extract(self.path,Options(freecad_cmd='/does/not/exist/freecad')))
        self.assertFalse(succeeded(r));self.assertIn('FREECAD_UNAVAILABLE',{d['code'] for d in r['diagnostics']})
    def test_simulated_response_identity(self):
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated()):r=self.checked(extract(self.path,self.options()))
        self.assertTrue(succeeded(r))
    def test_simulated_crash(self):
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(exitcode=-11)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r));self.assertEqual(r['geometries'],[])
        self.assertIn('NATIVE_PROCESS_FAILED',{d['code'] for d in r['diagnostics']})
    def test_simulated_timeout(self):
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=subprocess.TimeoutExpired('worker',1)):r=self.checked(extract(self.path,self.options()))
        self.assertIn('NATIVE_TIMEOUT',{d['code'] for d in r['diagnostics']})
    def test_simulated_missing_response(self):
        with patch('jeia_dxf_freecad.runner.subprocess.run',return_value=SimpleNamespace(returncode=0)):r=self.checked(extract(self.path,self.options()))
        self.assertIn('NATIVE_RESPONSE_MISSING',{d['code'] for d in r['diagnostics']})
    def test_simulated_wrong_hash(self):
        def change(r,*_):r['document']['sha256']='0'*64
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertIn('NATIVE_RESPONSE_INVALID',{d['code'] for d in r['diagnostics']})
    def test_simulated_wrong_generation(self):
        def change(r,*_):r['context']['selectionGeneration']+=1
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_wrong_request(self):
        def change(r,*_):r['context']['requestId']='other'
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_bad_source_hash(self):
        def change(r,*_):r['sources'][1]['inputSha256']='f'*64
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_snapshot_change(self):
        def change(r,req,_):Path(req['input']).write_bytes(b'changed')
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_cnc_permission_rejected(self):
        def change(r,*_):r['validation']['cncReleased']=True
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_material_permission_rejected(self):
        def change(r,*_):r['validation']['eligibility'][1]['status']='eligible'
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated(change)):r=self.checked(extract(self.path,self.options()))
        self.assertFalse(succeeded(r))
    def test_simulated_response_limit(self):
        with patch('jeia_dxf_freecad.runner.subprocess.run',side_effect=self.simulated()):r=self.checked(extract(self.path,self.options(max_response_bytes=10)))
        self.assertIn('NATIVE_RESPONSE_LIMIT',{d['code'] for d in r['diagnostics']})
    def test_input_limit(self):
        with self.assertRaisesRegex(ValueError,'Input limit'):extract(self.path,Options(max_input_bytes=10))
    def test_empty_input(self):
        self.path.write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'Empty input'):extract(self.path)
    def test_binary_input(self):
        self.path.write_bytes(b'AutoCAD Binary DXF\r\n\x1a\0');r=extract(self.path);VALIDATOR.validate(r)
        self.assertIn('BINARY_DXF_NOT_SUPPORTED',{d['code'] for d in r['diagnostics']})
    def test_invalid_options(self):
        for args in ({'timeout':0},{'timeout':float('nan')},{'max_edges':0},{'freecad_cmd':'x','api_python':'y'}):
            with self.assertRaises(ValueError):Options(**args)
    def test_invalid_selection_identity(self):
        for kwargs in ({'request_id':'with spaces'},{'generation':-1},{'generation':True},{'revision':0}):
            with self.assertRaises(ValueError):Packet(metadata(DATA,'x'),**kwargs)
    def test_nonfinite_number_rejected(self):
        for v in (math.nan,math.inf,-math.inf):
            with self.assertRaises(ValueError):number(v)
    def test_schema_required_generation(self):
        r=self.packet().finish();del r['context']['selectionGeneration']
        with self.assertRaises(ValidationError):VALIDATOR.validate(r)
    def test_no_existing_output_overwrite(self):
        output=Path(self.temp.name)/'out.json';output.write_text('preserve')
        r=subprocess.run([sys.executable,'-m','jeia_dxf_freecad',str(self.path),'--freecad-cmd','missing-freecad',
            '--output',str(output)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertEqual(output.read_text(),'preserve')
    def test_cli_cannot_overwrite_input(self):
        r=subprocess.run([sys.executable,'-m','jeia_dxf_freecad',str(self.path),'--output',str(self.path)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertEqual(self.path.read_bytes(),DATA)
    def test_schema_is_frozen(self):
        self.assertEqual(SCHEMA['$id'],'urn:jeia:dxf-tech:1.0');self.assertEqual(SCHEMA['properties']['version']['const'],'1.0')
    def test_simulated_unresolved_frame_preserves_brep_not_global_points(self):
        from jeia_dxf_freecad.collector import collect_document
        matrix=SimpleNamespace(**{'A'+str(i)+str(j):float(i==j) for i in range(1,5) for j in range(1,5)})
        placement=SimpleNamespace(toMatrix=lambda:matrix)
        shape=SimpleNamespace(isNull=lambda:False,Placement=placement,ShapeType='Edge',exportBrepToString=lambda:'SIMULATED_BREP')
        shape.copy=lambda:shape
        obj=SimpleNamespace(Name='Simulated',TypeId='Part::Feature',Shape=shape)
        app=SimpleNamespace(Version=lambda:['fixture','0','0'])
        r=self.checked(collect_document(SimpleNamespace(Objects=[obj]),metadata(DATA,'fixture.dxf'),app,synthetic=True))
        self.assertFalse(succeeded(r));self.assertEqual(r['geometries'][0]['payload']['type'],'UNSUPPORTED')
        self.assertEqual(r['evidence'][0]['value']['localBrep'],'SIMULATED_BREP')
        self.assertIn('GLOBAL_PLACEMENT_UNAVAILABLE',{d['code'] for d in r['diagnostics']})
    def test_simulated_curve_edge_coordinate_conflict_detected(self):
        from jeia_dxf_freecad.collector import curve_payload,GeometryConflict
        class V:
            def __init__(self,x):self.x=x;self.y=0;self.z=0
            def __sub__(self,other):return V(self.x-other.x)
            @property
            def Length(self):return abs(self.x)
        Circle=type('Circle',(),{})
        curve=Circle();curve.Center=V(0);curve.Axis=V(1);curve.Radius=5;curve.value=lambda t:V(5)
        edge=SimpleNamespace(Curve=curve,FirstParameter=0,LastParameter=math.tau,valueAt=lambda t:V(105))
        with self.assertRaises(GeometryConflict):curve_payload(edge)


if __name__=='__main__':unittest.main(verbosity=2)
