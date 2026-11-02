"""Record actual native results; exits 1 if any required integration fails.

No expected-failure conversion and no dependency installation.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator,FormatChecker

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--api-python',required=True);p.add_argument('--freecad-lib',required=True)
    p.add_argument('--freecad-cmd',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--timeout',type=float,default=30)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    validator=Draft202012Validator(json.loads((ROOT/'jeia_dxf_freecad/schema.json').read_text()),format_checker=FormatChecker())
    result={'experimental':True,'integrationApproved':False,'nativeKernel':[],'dxfImports':[]}
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    cases=['line','arc','circle','ellipse','bspline','disk','box','cylinder','placement','nested_placement','limits','empty']
    for name in cases:
        output=args.output/('native_'+name+'.json')
        cmd=[args.api_python,str(ROOT/'tests/native_case.py'),name,'--freecad-lib',args.freecad_lib,'--output',str(output)]
        try:
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,env=env,timeout=args.timeout)
            error=None
            if r.returncode==0:
                try:validator.validate(json.loads(output.read_text(encoding='utf-8')))
                except Exception as exc:error=str(exc)
            passed=r.returncode==0 and output.is_file() and error is None
            record={'case':name,'status':'passed' if passed else 'failed','exitCode':r.returncode,'schemaError':error,
                    'stdoutTail':r.stdout[-4000:],'stderrTail':r.stderr[-4000:]}
        except subprocess.TimeoutExpired:
            record={'case':name,'status':'failed','exitCode':None,'error':'timeout'}
        result['nativeKernel'].append(record);print('KERNEL',name,record['status'],flush=True)
    fixtures=sorted((ROOT/'examples').glob('*.dxf'))
    routes=[('FreeCADCmd',fixtures[0]),*[('API Python',f) for f in fixtures]]
    for index,(route,fixture) in enumerate(routes,1):
        output=args.output/('dxf_'+str(index)+'.json')
        cmd=[sys.executable,'-m','jeia_dxf_freecad',str(fixture),'--output',str(output),'--timeout',str(args.timeout)]
        cmd+=['--freecad-cmd',args.freecad_cmd] if route=='FreeCADCmd' else ['--api-python',args.api_python,'--freecad-lib',args.freecad_lib]
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,env=env,timeout=args.timeout+10)
        packet=json.loads(output.read_text(encoding='utf-8')) if output.is_file() else None
        error=None
        if packet is not None:
            try:validator.validate(packet)
            except Exception as exc:error=str(exc)
        codes=[d['code'] for d in packet['diagnostics']] if packet else []
        passed=r.returncode==0 and packet is not None and error is None
        result['dxfImports'].append({'route':route,'fixture':fixture.name,'status':'passed' if passed else 'failed',
            'exitCode':r.returncode,'geometryCount':len(packet['geometries']) if packet else 0,
            'diagnosticCodes':codes,'schemaError':error,'stdoutTail':r.stdout[-2000:],'stderrTail':r.stderr[-2000:]})
        print('DXF',route,fixture.name,'passed' if passed else 'failed',flush=True)
    result['integrationApproved']=all(r['status']=='passed' for r in result['nativeKernel']+result['dxfImports'])
    result['note']='Kernel fixtures do not approve DXF import. Native environment failures remain failures, not skipped/expected-pass cases.'
    (args.output/'PROBE_RESULTADOS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('INTEGRATION APPROVED:',result['integrationApproved'])
    return 0 if result['integrationApproved'] else 1


if __name__=='__main__':raise SystemExit(main())
